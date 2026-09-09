"""Optional GitHub documentary-PR controller. Explicit network access, never PR execution."""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import quote, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

from .git_snapshot import GitSnapshot, git, commit
from .memory.models import canonical, FRAMEWORK
from .workspace import MemoryInputError


def prepare(repository, info, pull, branch, project, framework_commit):
    """API documents must come from authenticated same-host requests by the controller."""
    if (info["full_name"] != repository or pull["base"]["repo"]["full_name"] != repository
            or pull["state"] != "open" or pull.get("draft")
            or pull["base"]["ref"] != info["default_branch"] or branch["name"] != info["default_branch"]
            or branch.get("protected") is not True or branch["commit"]["sha"] != pull["base"]["sha"]):
        raise MemoryInputError("PR is not against the current protected default branch")
    before = GitSnapshot.open(project, pull["base"]["sha"])
    after = GitSnapshot.open(project, pull["head"]["sha"])
    # This example has no code/evidence collector. Never silently interpret code as docs.
    for path in before.changed(after):
        if Path(path).suffix not in (".md", ".yaml", ".yml") and path != ".framework/contribution-policy.json":
            raise MemoryInputError("the supplied GitHub example is documentary-only")
    text = pull["title"] + "\n" + (pull.get("body") or "")
    if len(text.encode("utf-8")) > 1_000_000:
        raise MemoryInputError("PR metadata exceeds the bound")
    control = dict(schema="framework-memory/contribution-input/v1", framework_commit=framework_commit,
                   author=pull["user"]["login"],
                   documents=dict(repository=info["html_url"], root=str(Path(project).resolve()),
                                  commit=before.revision, approved_tip=before.revision, proposed=after.revision),
                   repositories={}, receipts=[], selected_tests=[])
    return control, text


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward authorization to a redirected host.


def endpoint(value):
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment):
        raise MemoryInputError("CI API/server endpoint must be an explicit HTTPS origin/path")
    return value.rstrip("/")


def fetch_head(project, server, repository, number, token):
    """Only the base repository's pull ref; no URLs or ref names taken from PR text."""
    url = server + "/" + repository + ".git"
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k not in ("GITHUB_TOKEN", "GH_TOKEN")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0",
               GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0=f"http.{url}.extraheader",
               GIT_CONFIG_VALUE_0="AUTHORIZATION: basic " + base64.b64encode(("x-access-token:" + token).encode()).decode())
    command = ["git", "-c", "core.fsmonitor=false", "-c", f"core.hooksPath={os.devnull}",
               "-c", "protocol.file.allow=never", "-c", "protocol.ext.allow=never",
               "-C", str(project), "fetch", "--no-tags", "--no-recurse-submodules",
               url, f"+refs/pull/{number}/head:refs/framework/contribution-head"]
    result = subprocess.run(command, env=env, capture_output=True, timeout=60)
    if result.returncode:
        raise MemoryInputError("PR Git objects could not be fetched")
    return git(project, "rev-parse", "refs/framework/contribution-head").decode().strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--pr-number", required=True, type=int)
    args = parser.parse_args()
    try:
        repository = os.environ["GITHUB_REPOSITORY"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or args.pr_number <= 0:
            raise MemoryInputError("invalid repository or PR number")
        api_url, server = endpoint(os.environ["GITHUB_API_URL"]), endpoint(os.environ["GITHUB_SERVER_URL"])
        token = os.environ["GITHUB_TOKEN"]
        opener = build_opener(NoRedirect())

        def get(path):
            request = Request(api_url + path, headers={"Authorization": "Bearer " + token,
                       "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2026-03-10"})
            with opener.open(request, timeout=20) as response:
                raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise MemoryInputError("CI response exceeds the bound")
            return json.loads(raw)

        info = get("/repos/" + repository)
        if (os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch"
                or os.environ.get("GITHUB_REF") != "refs/heads/" + info["default_branch"]):
            raise MemoryInputError("run this controller explicitly from the trusted default branch")
        pull = get(f"/repos/{repository}/pulls/{args.pr_number}")
        branch = get(f"/repos/{repository}/branches/" + quote(info["default_branch"], safe=""))
        # Establish identity/default/protection before fetching any proposed objects.
        if (info["full_name"] != repository or pull["base"]["repo"]["full_name"] != repository
                or pull["base"]["ref"] != info["default_branch"] or not branch.get("protected")):
            raise MemoryInputError("unapproved PR base")
        fetched = fetch_head(args.project, server, repository, args.pr_number, token)
        if fetched != pull["head"]["sha"]:
            raise MemoryInputError("PR changed during capture; rerun against its new head")
        pin = git(FRAMEWORK, "rev-parse", "HEAD").decode().strip()
        commit(FRAMEWORK, pin)
        control, text = prepare(repository, info, pull, branch, args.project, pin)
        with tempfile.TemporaryDirectory(prefix="framework-contribution-") as temporary:
            directory = Path(temporary)
            (directory / "input.json").write_bytes(canonical(control))
            (directory / "pr.txt").write_text(text, encoding="utf-8", newline="\n")
            # No hosting token, PYTHONPATH or other job secrets reach the verifier.
            environment = {k: v for k, v in os.environ.items()
                           if k in ("PATH", "SYSTEMROOT", "LANG", "LC_ALL", "TMP", "TEMP")}
            result = subprocess.run([sys.executable, "-I", "-B",
                                    str(FRAMEWORK / "skills/audit/scripts/validate.py"),
                                    "--profile", "strict-contribution", "--trust-input", str(directory / "input.json"),
                                    "--pr-text-file", str(directory / "pr.txt"), "--json"],
                                   env=environment, capture_output=True, timeout=300)
            sys.stdout.buffer.write(result.stdout)
            return result.returncode
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        print('{"profile":"strict-contribution","gate":"unavailable","authorization":"not-verified"}')
        return 2
