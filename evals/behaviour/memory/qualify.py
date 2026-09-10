#!/usr/bin/env python3
"""Opt-in, synthetic-only comprehension capture. Never grades its own answers.

Prepare copies/context with `--output ABSENT_DIR`; add `--execute` to call the
already authenticated Codex CLI sequentially. No install, model override, release,
product adoption or real repository input. The frozen cases remain unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import time

import yaml

ROOT = Path(__file__).resolve().parents[3]
CASES = Path(__file__).with_name("cases.yaml")
OVERLAYS = ROOT / "tests/fixtures/memory/phase2-metadata.yaml"
DISABLED = ("apps", "plugins", "hooks", "memories", "multi_agent", "multi_agent_v2",
            "browser_use", "computer_use", "image_generation", "shell_snapshot",
            "skill_search", "skill_mcp_dependency_install")
FRAMEWORK_FILES = ("memory.py", "FRAMEWORK.md", "src", "schemas", "references",
                   "skills", "templates", "providers.lock.json", "constraints.txt", "requirements.txt")
INSTRUCTIONS = """Read-only analysis of this synthetic workspace. Do not approve or implement
anything, create artifacts, access the network, install tools, or delegate work.
Start with AGENTS.md and the authoritative sources it names. A precomputed context
pack is at _meta/memory/evaluation/context.json; the documentary graph is beside it.
These are navigation/provenance aids, not proof of understanding or authorization.
Read the relevant original sources and available code. Graph absence is not proof
of no impact. If you use a tool, stay inside this project or the adjacent framework
runtime; never inspect the evaluator, answer keys, sibling trials or account files.
Report conclusions, evidence (exact paths/sections and what you actually read),
uncertainties and missing evidence. Do not claim execution or measurement you did
not perform. Give your answer as text; the evaluator, not you, saves it.

Question:
"""


def canonical(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def inventory(root):
    """Include removals, links, modes and Git internals; never follow a link."""
    result = {}
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in sorted([*dirs, *files]):
            path = Path(parent) / name
            info = path.lstat()
            relative = path.relative_to(root).as_posix()
            row = {"mode": stat.S_IMODE(info.st_mode)}
            if path.is_symlink():
                row.update(kind="symlink", target=os.readlink(path))
            elif path.is_file():
                row.update(kind="file", sha256=digest(path.read_bytes()))
            elif path.is_dir():
                row.update(kind="directory")
            else:
                row.update(kind="special")
            result[relative] = row
    return result


def differences(before, after):
    return [{"path": key, "change": "added" if key not in before else
             "deleted" if key not in after else "modified"}
            for key in sorted(before.keys() | after.keys()) if before.get(key) != after.get(key)]


def input_changes(project, project_before, framework, framework_before):
    return [dict(row, scope=scope) for scope, rows in (
        ("project", differences(project_before, inventory(project))),
        ("framework", differences(framework_before, inventory(framework)))) for row in rows]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(output, selected, enola=None):
    if not output.is_absolute() or output.exists():
        raise ValueError("output must be an absent absolute directory; never reuse a run")
    output.mkdir(parents=True)
    generator = load_module("qualification_fixtures", ROOT / "evals/fixtures/generators/memory.py")
    generator.build(output / "frozen")
    runtime = load_module("qualification_runtime", ROOT / "memory.py")
    import importlib
    capture = importlib.import_module(runtime._name + ".snapshots").capture
    graph_module = importlib.import_module(runtime._name + ".memory.graph")
    context_module = importlib.import_module(runtime._name + ".memory.context")
    code_module = importlib.import_module(runtime._name + ".memory.code_graph")
    provider_module = importlib.import_module(runtime._name + ".memory.providers.enola")
    overlays = yaml.safe_load(OVERLAYS.read_text())
    framework = output / "framework"
    framework.mkdir()
    # Runtime/rules only: never expose tests, cases, reports, Git history or evaluator.
    for relative in FRAMEWORK_FILES:
        source, target = ROOT / relative, framework / relative
        if source.is_dir():
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copyfile(source, target)
    for case in selected:
        project = output / "trials" / case["name"] / "project"
        shutil.copytree(output / "frozen" / case["fixture"], project)
        for relative, fields in overlays.get(case["fixture"], {}).items():
            path = project / relative
            _, front, body = path.read_text().split("---", 2)
            meta = yaml.safe_load(front)
            meta.update(fields)
            path.write_text("---\n" + yaml.safe_dump(meta, sort_keys=False) + "---" + body)
        bindings = {"repository:product:alpha:api": "code/alpha-api",
                    "repository:product:beta:worker": "code/beta-worker",
                    "repository:platform:rules": "code/shared-rules"}
        path = project / ".framework-memory/local.yaml"
        path.parent.mkdir()
        path.write_text(yaml.safe_dump({"checkouts": bindings}))
        snapshot = capture(project)
        graph = graph_module.build(snapshot)
        code = None
        if enola is not None:
            observed = code_module.build_code(snapshot, graph, provider_module.EnolaProvider(enola))
            observed.publish()
            code = {"graph": observed.graph, "inputs": observed.inputs}
        pack = context_module.compose(snapshot, graph, goal=case["prompt"], mode="analysis",
                                       reconsider=True, skill="audit", budget=250000,
                                       framework_root=framework, code=code)
        support = project / "_meta/memory/evaluation"
        save(support / "context.json", pack)
        save(support / "documents.json", graph)
        prompt = INSTRUCTIONS + case["prompt"] + "\n"
        trial = project.parent
        (trial / "prompt.txt").write_text(prompt)
        save(trial / "before.json", inventory(project))
        print("prepared", case["name"], flush=True)
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                            check=True, capture_output=True, text=True).stdout.strip()
    save(output / "manifest.json", {
        "schema": "framework/memory-qualification/v1", "framework_commit": commit,
        "runner_sha256": digest(Path(__file__).read_bytes()), "cases_sha256": digest(CASES.read_bytes()),
        "overlay_sha256": digest(OVERLAYS.read_bytes()), "cases": [c["name"] for c in selected],
        "framework_files": inventory(framework), "synthetic_only": True,
        "mode": "precomputed-memory-assisted-comprehension-not-skill-routing",
        "grading": "independent-review-required", "enola_requested": enola is not None,
        "model_override": None, "configuration": "ignore-user-config; saved authentication",
        "limitations": ["One sample per case; no reliability or improvement claim",
                        "Tool delivery and self-reported reading do not attest understanding"],
    })


def settings(project, framework, helper=None):
    filesystem = {":minimal": "read", str(project): "read", str(framework): "read"}
    if helper is not None:
        if not helper.is_file():
            raise ValueError("sandbox helper must be an existing executable file")
        filesystem[str(helper.resolve())] = "read"
    return ["approval_policy=\"never\"", "default_permissions=\"memory-eval\"",
            "permissions.memory-eval.filesystem=" + "{" + ",".join(
                json.dumps(k) + "=" + json.dumps(v) for k, v in filesystem.items()) + "}",
            "permissions.memory-eval.network.enabled=false", "web_search=\"disabled\"",
            "shell_environment_policy.ignore_default_excludes=false",
            "shell_environment_policy.experimental_use_profile=false"]


def replay(source, output, selected):
    """New attempt on EXACT prepared bytes, not on a silently regenerated framework."""
    if not output.is_absolute() or output.exists():
        raise ValueError("replay output must be an absent absolute directory")
    manifest_bytes = (source / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest["cases_sha256"] != digest(CASES.read_bytes()):
        raise ValueError("frozen case contract changed; cannot replay")
    framework_files = inventory(source / "framework")
    if framework_files != manifest["framework_files"]:
        raise ValueError("prepared framework changed; cannot replay")
    if any(r["kind"] in ("symlink", "special") for r in framework_files.values()):
        raise ValueError("links or special files are not replayable")
    projects = {}
    for case in selected:
        trial = source / "trials" / case["name"]
        before = json.loads((trial / "before.json").read_text())
        if inventory(trial / "project") != before or any(
                row["kind"] in ("symlink", "special") for row in before.values()):
            raise ValueError("prepared project changed; cannot replay")
        if (trial / "prompt.txt").read_text() != INSTRUCTIONS + case["prompt"] + "\n":
            raise ValueError("prepared prompt changed; cannot replay")
        projects[case["name"]] = trial
    output.mkdir(parents=True)
    shutil.copytree(source / "framework", output / "framework")
    for name, trial in projects.items():
        target = output / "trials" / name
        shutil.copytree(trial / "project", target / "project")
        for relative in ("prompt.txt", "before.json"):
            shutil.copyfile(trial / relative, target / relative)
    manifest.update(cases=[c["name"] for c in selected], replay_of_manifest_sha256=digest(manifest_bytes),
                    execution_runner_sha256=digest(Path(__file__).read_bytes()))
    save(output / "manifest.json", manifest)


def options(config):
    return [part for setting in config for part in ("-c", setting)]


def capture_process(command, *, cwd, output, prefix, timeout, stdin=None):
    """Keep complete streams even on timeout; kill the Linux process group, not just wrapper."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", GIT_OPTIONAL_LOCKS="0")
    env.pop("CLAUDECODE", None)
    start = time.monotonic()
    with (output / (prefix + ".stdout")).open("wb") as stdout, \
            (output / (prefix + ".stderr")).open("wb") as stderr:
        try:
            process = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.PIPE,
                                       stdout=stdout, stderr=stderr, start_new_session=True)
        except OSError as error:
            return {"status": "unavailable", "reason": type(error).__name__, "exit_code": None}
        try:
            process.communicate(stdin, timeout=timeout)
            status = "completed" if process.returncode == 0 else "unavailable"
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            status = "timeout"
        except BaseException:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise
    return {"status": status, "exit_code": process.returncode,
            "elapsed_seconds": round(time.monotonic() - start, 3)}


def preflight(codex, project, framework, trial, helper=None):
    # A canary outside permitted roots is not an answer key or an account file.
    canary = trial / "canary.txt"
    canary.write_text("Synthetic sandbox canary.\n")
    probe = """import json, pathlib, socket, sys
project, forbidden = map(pathlib.Path, sys.argv[1:])
result = {'read': (project / 'AGENTS.md').is_file()}
for name, action in [('write', lambda: (project / '.probe-write').write_text('probe')),
                     ('outside_read', lambda: forbidden.read_bytes()),
                     ('network', lambda: socket.socket().connect(('127.0.0.1', 9)))]:
    try:
        action()
        result[name] = 'allowed'
    except OSError as error:
        # bwrap hides an existing, host-verified canary as ENOENT instead of EACCES.
        denied = error.errno in (1, 13, 30) or (name == 'outside_read' and error.errno == 2)
        result[name] = 'denied' if denied else 'unproven'
print(json.dumps(result))
"""
    command = [codex, "sandbox", *options(settings(project, framework, helper)),
               "-P", "memory-eval", "-C", str(project), "--", "/usr/bin/python3", "-B", "-c",
               probe, str(project), str(canary)]
    result = capture_process(command, cwd=project, output=trial, prefix="preflight", timeout=30)
    try:
        observed = json.loads((trial / "preflight.stdout").read_text())
    except (ValueError, OSError):
        observed = {}
    result["observed"] = observed
    result["status"] = "passed" if result["status"] == "completed" and observed == {
        "read": True, "write": "denied", "outside_read": "denied", "network": "denied"
    } else "unavailable"
    save(trial / "preflight.json", result)
    return result


def usable_result(process, stdout, answer, changes):
    """Only capture validity is mechanical. Never infer semantic success from phrases."""
    if changes:
        return {"status": "critical-failure", "reason": "unauthorized-write", "changes": changes}
    if process["status"] != "completed":
        return {"status": "unavailable", "reason": process["status"]}
    try:
        events = [json.loads(line) for line in stdout.splitlines() if line.strip()]
        if not all(isinstance(e, dict) for e in events):
            raise ValueError("invalid event shape")
    except ValueError:
        return {"status": "unavailable", "reason": "invalid-event-stream"}
    if not answer.strip() or not any(e.get("type") == "turn.completed" for e in events) or any(
            e.get("type") in ("error", "turn.failed") for e in events):
        return {"status": "unavailable", "reason": "incomplete-model-turn"}
    return {"status": "pending-review", "reason": "answer-and-completed-turn-captured"}


def run(output, selected, codex, timeout, helper=None):
    if sys.platform != "linux":
        raise ValueError("This explicit adapter requires Linux/WSL; no weaker sandbox fallback")
    version = subprocess.run([codex, "--version"], capture_output=True, text=True, timeout=30, check=True)
    (output / "cli-version.txt").write_text(version.stdout)
    framework = output / "framework"
    framework_before = json.loads((output / "manifest.json").read_text())["framework_files"]
    summary = []
    for case in selected:
        trial = output / "trials" / case["name"]
        project = trial / "project"
        before = json.loads((trial / "before.json").read_text())
        changed = input_changes(project, before, framework, framework_before)
        checked = preflight(codex, project, framework, trial, helper) if not changed else {
            "status": "unavailable"}
        changed = input_changes(project, before, framework, framework_before)
        if changed:
            result = {"status": "critical-failure", "reason": "unauthorized-write", "changes": changed}
        elif checked["status"] != "passed":
            result = {"status": "unavailable", "reason": "sandbox-preflight-not-proven"}
        else:
            command = [codex, "exec", "--ignore-user-config", "--ephemeral", "--json",
                       "--skip-git-repo-check", "-C", str(project),
                       *options(settings(project, framework, helper)),
                       *[p for f in DISABLED for p in ("--disable", f)],
                       "-o", str(trial / "answer.md"), "-"]
            save(trial / "command.json", command)
            process = capture_process(command, cwd=project, output=trial, prefix="events",
                                      timeout=timeout, stdin=(trial / "prompt.txt").read_bytes())
            answer = (trial / "answer.md").read_text() if (trial / "answer.md").exists() else ""
            result = usable_result(process, (trial / "events.stdout").read_text(), answer,
                                   input_changes(project, before, framework, framework_before))
            result["process"] = process
        result["case"] = case["name"]
        save(trial / "result.json", result)
        summary.append(result)
        save(output / "results.json", {"results": summary, "grading": "not-performed",
             "not_run": [c["name"] for c in selected if c["name"] not in {r["case"] for r in summary}]})
        print(case["name"], result["status"], result["reason"], flush=True)
        if result["status"] in ("unavailable", "critical-failure"):
            # Don't turn a global outage into fourteen supposed model failures.
            break
    return 2 if any(r["status"] != "pending-review" for r in summary) else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", action="append", help="exact frozen case name; default all")
    parser.add_argument("--enola", type=Path, help="already installed, pinned provider; never downloaded")
    parser.add_argument("--execute", action="store_true", help="explicitly call the authenticated model")
    parser.add_argument("--from-prepared", type=Path, help="new attempt on unchanged, hashed prepared inputs")
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--sandbox-helper", type=Path,
                        help="exact native Codex executable if installed outside minimal runtime paths")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    cases = yaml.safe_load(CASES.read_text())["cases"]
    if args.case and set(args.case) - {c["name"] for c in cases}:
        parser.error("unknown case; expected an exact frozen case name")
    selected = [c for c in cases if not args.case or c["name"] in args.case]
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    if args.from_prepared:
        if args.enola:
            parser.error("replay cannot invoke a provider or regenerate inputs")
        replay(args.from_prepared, args.output, selected)
    else:
        prepare(args.output, selected, args.enola)
    return run(args.output, selected, args.codex, args.timeout, args.sandbox_helper) if args.execute else 0


if __name__ == "__main__":
    raise SystemExit(main())
