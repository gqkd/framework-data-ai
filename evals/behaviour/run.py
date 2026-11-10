#!/usr/bin/env python3
"""Does a skill do the right thing once it fires, on repositories built to tell it apart.

    python evals/behaviour/run.py release             # every case, one at a time
    python evals/behaviour/run.py release --case D    # one of them
    python evals/behaviour/run.py release --baseline  # the same, with no framework at all
    python evals/behaviour/run.py contribute --plugin-dir .  # with the plugin of this tree

Triggering asks whether the skill answers. This asks whether the answer is right, which
for a gate is the half that matters: one that fires reliably and says yes to everything is
worse than no gate, because somebody is now relying on it.

One sentence per skill, the same for all of its cases, so what the model gets right or
wrong comes from the repository rather than from how the question was put. Where the
repository is the constant instead, a case carries its own `prompt` and its own `name`:
`requirement` is one project and many statements to file, which is the shape of the
question inverted.

NO TOOL IS DENIED, DELIBERATELY. The release gate has to recompute a hash and recover a
frozen plan with `git show`; without a shell it cannot do what it is told, and the run
would fail for a reason that has nothing to do with the skill. Writes are allowed for the
same reason: `-p` denies them by default, and the first run of this graded judgement only,
because the skill reached the right verdict and then printed a manifest it could not save.
Half of what these skills do is produce artifacts, and an unwritten one cannot be wrong.
The fixture is copied first.

WHAT SITS BESIDE THE PROJECT, FOR A CASE THAT NEEDS IT. A case, or its file, may name in
`beside` what the build put next to the fixture -- `contribute/team` has its remote at
`../remote.git` and the exchange at `../_scambio` --, and each is copied next to the copy under
its own name, so that a push lands in the copy's remote and a delivery is read from the copy's
exchange. For such a case what the run did to git is printed too, as what changed between
before and after: the branches, the remote-tracking ones, the claim, reservation and delegation
tags, the worktrees beside the project, the refs of each bare repository beside it -- its
remote, a code repository's remote -- and the files of every other folder beside it -- the
exchange, a code repository, its `.git/` included. A skill that works on branches leaves most
of what it did there, and a list of the files in the checkout would read as "nothing written":
so for every local branch the run made or moved, the files it changes against the main line
before the run are printed as well, with git's letter, before the copy is deleted. Such a run is
also given `--add-dir` on the folder that holds the copy and what sits beside it, where a skill
makes a thread's worktree, so that it writes there as a person would.

A CASE FILE MAY ASK FOR THE BASH SANDBOX OFF. Under the sandbox, `contribute` hands `open`,
`list`, every push and the steps of `join` to the person as lines to paste, because its text
says so, not because a command failed: `--add-dir` does not change that, and a run would stop at
its first command, short of what the case expects -- `outside` too, which names nothing beside
it and may begin with a fetch. So a case file may set `without_sandbox: true`, inherited by its
cases as `beside` is, and a case may say otherwise for itself; `contribute`'s sets it. The
header of every case says what the settings `claude -p` reads declare of the sandbox, and where
they declare it on, a case so marked is not run, in either arm, and the runner says why: in the
baseline arm, so that the two arms differ in the framework alone. What the files declare, and
not whether the sandbox could start, which a run has no one to ask. What a skill does under the
sandbox is measured by the version that tries it on a machine.

A CODE SESSION A SKILL LAUNCHES IS STOOD IN FOR, from 4.13.0. A documentation session launches
the code session with `exchange.py code --launch`, on the person's yes, and a run has the
interpreter granted: a skill that does not stop at "launch?" would start a real code session,
on the person's subscription, inside the measurement. Every run gets `FRAMEWORK_DATA_AI_CLAUDE`
pointed at a fake `claude` in a folder of its own, outside the one the run is opened to, where a
skill looks for code repositories, which `exchange.py` launches in place of the one
on the `PATH` -- not the `PATH` itself, which the shell of a run takes again from the person's
profile -- and which records its arguments and does nothing else; the runner itself calls the
`claude` it always did. What it recorded is printed as a code session launched -- for a case
that stops at "launch?", nothing --: after what the run did on git, for a case that names
something beside its fixture, and on a line "beside it" of its own, git unread, for one that
names nothing; and after a timeout too, when the copy is removed unread.

GRADING IS BY HAND, AND THE CASE COUNT IS WHY. A keyword match on "go" and "block" scores
the laundering fixture correct for saying the word while missing that 0.812 under a 0.85
threshold is the entire point of it. What the run said, what it wrote, and whether the
repository still validates are printed, and read. That does not scale, and at six cases it
does not have to.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
VALIDATE = HERE.parents[1] / "skills" / "audit" / "scripts" / "validate.py"
FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)


# THE SAME GUARD THE TRIGGER RUNNER HAS, AND IT IS HERE BECAUSE IT WAS MISSING. A batch of
# six skills ran into a session limit and printed "skills invoked: none" for every case after
# it -- which reads exactly like six descriptions that stopped working, on the day six
# descriptions had just been changed. The sibling runner has refused to score that shape
# since the first time it happened; this one printed it as a result.
#
# Grading here is by hand, so the guard does not need to score anything: it needs to say, at
# the top of the case, that what follows is not a measurement.
# And a run with no login: the baseline arm points `CLAUDE_CONFIG_DIR` at an empty folder, and
# where the login is a subscription's, kept in the configuration folder, every one of its runs
# answered "Not logged in · Please run /login" and was printed as seven results (2026-11-04).
UNUSABLE = re.compile(r"session limit|usage limit|rate limit|credit balance|"
                      r"upgrade to increase|Claude AI usage limit|"
                      r"Not logged in|Please run /login", re.I)


def inspect(fixture: Path, cwd: Path) -> tuple[list[str], str]:
    """What the run left behind, and whether the repository still validates.

    A verdict is half the job. `release` also produces an `RLM` and a `REL`, and the
    failure worth catching is a manifest written while the gate was blocking: the words
    say rework and the artifacts say shipped, and the artifacts are what the next person
    reads at four in the morning.
    """
    before = {p.relative_to(fixture) for p in fixture.rglob("*")
              if p.is_file() and ".git/" not in str(p)}
    after = {p.relative_to(cwd) for p in cwd.rglob("*")
             if p.is_file() and ".git/" not in str(p)}
    changed = sorted(str(p) for p in (after - before))
    for p in sorted(after & before):
        if (fixture / p).read_bytes() != (cwd / p).read_bytes():
            changed.append(f"{p} (modified)")

    # The front matter of anything new, because for some of these the verdict *is* the
    # front matter: an `ICG` says what it decided in `routing`, and reading that back is
    # the difference between "it wrote a document" and "it wrote the right one".
    for rel in sorted(str(p) for p in (after - before)):
        if not rel.endswith((".md", ".yaml", ".yml")):
            continue
        m = FRONT.match((cwd / rel).read_text(encoding="utf-8", errors="replace"))
        if m:
            changed.append(f"\n--- {rel}\n" + m.group(1))

    try:
        r = subprocess.run([sys.executable, str(VALIDATE), "--root", str(cwd), "--json"],
                           capture_output=True, text=True, timeout=120)
        d = json.loads(r.stdout)
        verdict = (f"{d['errors']} errors, {d['warnings']} warnings: "
                   + (", ".join(sorted({f['code'] for f in d['findings']})) or "clean"))
    except Exception as e:
        verdict = f"the validator did not complete: {e}"
    return changed, verdict


def lay_out(fixture: Path, beside: list[str], tmp: Path) -> Path:
    """The copy the run happens in: the fixture as `project`, and what the case names in
    `beside`, found next to the fixture, copied next to it under the same names."""
    cwd = tmp / "project"
    shutil.copytree(fixture, cwd)
    for name in beside:
        src = fixture.parent / name
        if not src.exists():
            raise FileNotFoundError(f"{src}: named in `beside`, and the build did not write it")
        shutil.copytree(src, tmp / name)
    return cwd


def git_state(tmp: Path, cwd: Path, beside: list[str]) -> set[str]:
    """What git and the exchange hold, one line per fact, paths relative to the copy: the refs
    of the project -- branches, remote-tracking branches, tags with the subject of their
    message --, its worktrees, the refs of each bare repository named in `beside` and the
    files of every other folder named there."""
    def git(where: Path, *args: str) -> list[str]:
        r = subprocess.run(["git", "-C", str(where), *args], capture_output=True, text=True)
        return r.stdout.splitlines() if r.returncode == 0 else [f"git {args[0]} failed: "
                                                                 f"{r.stderr.strip()}"]
    out = {f"project {line}" for line in git(
        cwd, "for-each-ref", "--format=%(refname) %(objectname:short) %(contents:subject)",
        "refs/heads", "refs/remotes", "refs/tags")}
    # git prints a worktree by its real path: a temporary folder behind a link (`/var` on macOS)
    # is compared resolved.
    real = tmp.resolve()
    for line in git(cwd, "worktree", "list", "--porcelain"):
        if line.startswith("worktree "):
            path = Path(line[len("worktree "):])
            out.add(f"worktree {path.relative_to(real) if path.is_relative_to(real) else path}")
    for name in beside:
        where = tmp / name
        if (where / "HEAD").is_file() and (where / "objects").is_dir():
            out |= {f"{name} {line}" for line in git(
                where, "for-each-ref", "--format=%(refname) %(objectname:short)")}
        elif where.is_dir():
            out |= {f"{name} {p.relative_to(where).as_posix()}"
                    for p in where.rglob("*") if p.is_file()}
    return out


def branch_changes(cwd: Path, base: str, before: set[str], after: set[str]) -> list[str]:
    """What each local branch the run made or moved changes against `base`, the commit the
    copy stood on before it, one file per line with git's letter: `<branch>: M <path>`. The
    work of a thread is on its branch and in its worktree, never in the copy, and the refs
    alone do not say whether a living document was rewritten there."""
    def heads(state: set[str]) -> dict[str, str]:
        return {line.split()[1]: line.split()[2] for line in state
                if line.startswith("project refs/heads/") and len(line.split()) > 2}
    old, new = heads(before), heads(after)
    out = []
    for ref in sorted(r for r in new if new[r] != old.get(r)):
        name = ref[len("refs/heads/"):]
        r = subprocess.run(["git", "-C", str(cwd), "diff", "--name-status", "--no-renames",
                            f"{base}...{ref}"], capture_output=True, text=True)
        if r.returncode:
            out.append(f"{name}: git diff failed: {r.stderr.strip()}")
            continue
        files = [" ".join(line.split("\t")) for line in r.stdout.splitlines() if line]
        out += [f"{name}: {f}" for f in files] or [f"{name}: no file"]
    return out


def sandbox_declared(project: Path, baseline: bool) -> str:
    """Whether the settings files `claude -p` reads in `project` turn the Bash sandbox on, read
    in their order of precedence: the managed ones, the project's local and shared ones, the
    person's -- which the baseline arm does not load. What the files say, not what the session
    could start: `/sandbox` says that, and a run has no one to type it."""
    managed = {"darwin": Path("/Library/Application Support/ClaudeCode"),
               "win32": Path("C:/Program Files/ClaudeCode")}.get(sys.platform,
                                                                 Path("/etc/claude-code"))
    files = [managed / "managed-settings.json", project / ".claude" / "settings.local.json",
             project / ".claude" / "settings.json"]
    if not baseline:
        config = os.environ.get("CLAUDE_CONFIG_DIR")
        files.append((Path(config) if config else Path.home() / ".claude") / "settings.json")
    for f in files:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        sandbox = d.get("sandbox") if isinstance(d, dict) else None
        if isinstance(sandbox, dict) and "enabled" in sandbox:
            return f"{'on' if sandbox['enabled'] else 'off'}, by {f}"
    return "off, declared by no settings file"


# The `claude` `exchange.py code` launches where the environment names one (`CLAUDE_VAR` there).
CLAUDE_VAR = "FRAMEWORK_DATA_AI_CLAUDE"


def stand_in_claude(tmp: Path) -> tuple[Path, Path]:
    """A fake `claude` in `tmp`, a folder of its own outside the one the run is opened to, and
    the file where it records each call, its arguments as one JSON list per line: a code session
    a skill launches starts nothing, and the run does not find the fake among its folders."""
    fake, launched = tmp / "claude", tmp / "calls.jsonl"
    fake.write_text(f"#!{sys.executable}\nimport json, sys\n"
                    f"with open({str(launched)!r}, 'a', encoding='utf-8') as f:\n"
                    "    f.write(json.dumps(sys.argv[1:]) + '\\n')\n", encoding="utf-8")
    fake.chmod(0o755)
    return fake, launched


def launches(launched: Path) -> list[str]:
    """What the fake recorded, a call per line, its arguments quoted, newlines taken out, and
    each over 60 characters cut -- the prompt, and a long path too."""
    out = []
    for line in launched.read_text(encoding="utf-8").splitlines() if launched.is_file() else []:
        args = [a.replace("\n", " ") for a in json.loads(line)]
        out.append("claude " + shlex.join(a if len(a) <= 60 else a[:57] + "..." for a in args))
    return out


def run_one(fixture: Path, prompt: str, timeout: int, baseline: bool = False,
            beside: list[str] | None = None, plugin_dir: Path | None = None
            ) -> tuple[str, list[str], list[str], str, list[str], list[str]]:
    """Return the closing text, the skills invoked, what was written, the validator, what
    changed in git and beside the project -- for a case that names something `beside` it --
    followed by each code session the fake recorded as launched -- for every case, and after a
    timeout those alone --, and the files each branch made or moved changes, for a case that
    names something `beside` it, which also gets `--add-dir` on the folder of the copy.
    `plugin_dir`, absolute, is passed to `claude --plugin-dir`: the skills, agents and hooks of
    that checkout in place of the plugin installed. The fixture and the validator stay those of
    the tree this runner is in."""
    beside = list(beside or [])
    tmp = Path(tempfile.mkdtemp(prefix="rel-"))
    cwd = lay_out(fixture, beside, tmp)
    before = git_state(tmp, cwd, beside) if beside else set()
    base = subprocess.run(["git", "-C", str(cwd), "rev-parse", "HEAD"], capture_output=True,
                          text=True).stdout.strip() if beside else ""
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    # THE ARM THAT ANSWERS THE QUESTION THIS DIRECTORY CANNOT ANSWER WITHOUT IT. Every score
    # here says the skill did something; none of them says it did better than the same model
    # with no framework at all, which is the question that decides whether any of this earns
    # its tokens. `CLAUDE_CONFIG_DIR` at an empty directory loads no plugins and no skills
    # directory, per process: the fixture, the prompt and the tools are identical, and the
    # only difference is whether the six descriptions exist.
    if baseline:
        env["CLAUDE_CONFIG_DIR"] = str(Path(tmp) / "no-config")
        (Path(tmp) / "no-config").mkdir(parents=True, exist_ok=True)
    stand_in = Path(tempfile.mkdtemp(prefix="rel-claude-"))
    fake, launched = stand_in_claude(stand_in)
    env[CLAUDE_VAR] = str(fake)
    try:
        # `-p` denies writes by default, and the first run of this hit it: the skill
        # reached the right verdict and then printed the manifest it could not save,
        # which grades the judgement and leaves the artifacts unmeasured. Half of what
        # `release` is for is producing an `RLM` and a `REL`, so the run has to be able
        # to write them. The fixture is already a throwaway copy.
        # `acceptEdits` covers writing inside the copy and not a shell command reaching
        # outside it, which is where `validate.py` lives when the plugin is installed. Three
        # runs in a row reported that they could not execute it, and running the validator
        # is the first instruction in two of these skills: what was being measured was the
        # skill with its own first step removed.
        #
        # Granted by pattern rather than with `bypassPermissions`, which would hand a
        # subprocess on somebody's machine a shell with no guardrails to save typing one
        # argument. `Read` is broad because reading is cheap to be wrong about; the shell is
        # not, and gets exactly the interpreter the two scripts need.
        p = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose",
             "--permission-mode", "acceptEdits",
             "--allowedTools", "Read", "Glob", "Grep", "Bash(python3:*)", "Bash(git:*)"]
            + (["--plugin-dir", str(plugin_dir)] if plugin_dir else [])
            + (["--add-dir", str(tmp)] if beside else []),
            cwd=cwd, env=env, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=timeout)
        out = p.stdout
    except subprocess.TimeoutExpired:
        # Kept explicitly separate from "it answered nothing". Conflating the two is how
        # the trigger measurement produced a wrong number twice. A launch the fake recorded
        # before the time ran out is said all the same.
        shutil.rmtree(tmp, ignore_errors=True)
        calls = [f"+ a code session launched, the fake standing in for it: {call}"
                 for call in launches(launched)]
        shutil.rmtree(stand_in, ignore_errors=True)
        return "TIMED OUT before answering", [], [], "not run", calls, []

    texts, skills = [], []
    for line in out.splitlines():
        if not line.strip().startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "assistant":
            for c in ev.get("message", {}).get("content", []):
                if c.get("type") == "text":
                    texts.append(c["text"])
                if c.get("type") == "tool_use" and c.get("name") == "Skill":
                    skills.append(str(c.get("input", {}).get("skill", "")).split(":")[-1])
    written, valid = inspect(fixture, cwd)
    after = git_state(tmp, cwd, beside) if beside else set()
    moved = ([f"- {line}" for line in sorted(before - after)]
             + [f"+ {line}" for line in sorted(after - before)])
    moved += [f"+ a code session launched, the fake standing in for it: {call}"
              for call in launches(launched)]
    shutil.rmtree(stand_in, ignore_errors=True)
    changes = branch_changes(cwd, base, before, after) if beside else []
    shutil.rmtree(tmp, ignore_errors=True)
    # A run with no assistant turn at all did not choose to do nothing: it did not run.
    # The phrase the regex looks for only appears when the CLI gets far enough for the model
    # to say it, and the trigger set found six cases where nothing came back at all.
    if not texts and not skills:
        return ("NOT A MEASUREMENT. This run produced no assistant turn at all -- no text, "
                "no tool use. The account was out of quota, or the CLI could not start.",
                [], written, valid, moved, changes)
    if not skills and UNUSABLE.search(" ".join(texts)):
        return ("NOT A MEASUREMENT. This run never reached a model: the account was out of "
                "quota, or not logged in. It scores as `none` fired and nothing written, which "
                "is the same shape as a description that stopped working.\n\n"
                + (texts[-1] if texts else "")), \
               [], written, valid, moved, changes
    return ((texts[-1] if texts else "(no closing text)"), skills, written, valid, moved,
            changes)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("skill", help="which case set to run: a skill name, or a scenario")
    ap.add_argument("--case", help="one case, by the name or fixture it starts with")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--baseline", action="store_true",
                    help="run the same fixtures with no plugins and no skills directory: "
                         "the arm that says whether the framework beat the model alone")
    ap.add_argument("--plugin-dir", type=Path,
                    help="load the skills, agents and hooks of this checkout in every run, in "
                         "place of the plugin installed; the fixtures and the validator stay "
                         "those of the tree this runner is in, so a version not yet released "
                         "is run from its own tree with --plugin-dir on that tree")
    args = ap.parse_args()
    if args.plugin_dir and args.baseline:
        sys.exit("--plugin-dir and --baseline: the arm with no framework cannot load one")
    plugin_dir = args.plugin_dir.resolve() if args.plugin_dir else None
    if plugin_dir and not (plugin_dir / ".claude-plugin" / "plugin.json").is_file():
        sys.exit(f"--plugin-dir {plugin_dir}: no .claude-plugin/plugin.json there, so the header "
                 "would name a plugin no run loaded")

    spec_file = HERE / args.skill / "cases.yaml"
    if not spec_file.exists():
        sys.exit(f"no cases for {args.skill!r}: {spec_file} does not exist")
    spec = yaml.safe_load(spec_file.read_text())
    root = Path(spec["fixtures_root"])
    if not root.is_absolute():
        root = (HERE.parents[1] / root).resolve()
    for c in spec["cases"]:
        c.setdefault("name", c["fixture"])
        c.setdefault("prompt", spec.get("prompt"))
        c.setdefault("beside", spec.get("beside") or [])
        c.setdefault("without_sandbox", bool(spec.get("without_sandbox")))
    cases = [c for c in spec["cases"]
             if not args.case or c["name"].startswith(args.case)]
    if not cases:
        sys.exit(f"no case starts with {args.case!r}")

    for c in cases:
        fx = root / c["fixture"]
        if not fx.exists():
            print(f"! {fx} is missing, skipping", file=sys.stderr)
            continue
        arm = ("  [BASELINE: no plugins, no skills]" if args.baseline
               else f"  [PLUGIN: {plugin_dir}]" if plugin_dir else "")
        declared = sandbox_declared(fx, args.baseline)
        print(f"\n{'=' * 78}\n{c['name']}   expected: {c['expect']}{arm}\n  sandbox, as the "
              f"settings declare it: {declared}\n  because: {c['because']}\n{'=' * 78}")
        if c["without_sandbox"] and declared.startswith("on"):
            print("! NOT RUN: the settings declare the Bash sandbox on, and this case is measured "
                  "without it: " + (
                      "the plugin arm is not run under it either, and the two arms differ in "
                      "the framework alone." if args.baseline else
                      "under it the skill hands its commands on git and beside the project to "
                      "the person, as lines to paste, and the run would stop at the first of "
                      "them.") + " Run it with the sandbox off.")
            continue
        text, skills, written, valid, moved, changes = run_one(
            fx, c["prompt"], args.timeout, baseline=args.baseline, beside=c["beside"],
            plugin_dir=plugin_dir)
        # The answer first. A run of this was cut off partway through the front matter
        # listing, and the closing text, which is most of what is being graded, never
        # printed. Reading that transcript back, a grep for what the skill should have
        # said came up empty, which reads exactly like the skill not saying it. Whatever
        # is most expensive to lose goes at the top.
        unusable = text.startswith("NOT A MEASUREMENT")
        if unusable:
            print("! NOT SCORED: this case never reached a model. Re-run it.")
        print(f"skills invoked : {skills or 'none'}")
        print(f"repo after run : {valid}")
        print()
        print(text.strip()[:3500])
        print(f"\n{'-' * 78}\nwrote: " + (", ".join(written) if written else "nothing"))
        timed_out = text.startswith("TIMED OUT")
        if c["beside"] or moved:
            print(("git and beside it: " if c["beside"] else "beside it: ")
                  + ("not read: the run timed out and its copy was removed" if timed_out else "")
                  + ("\n  " + "\n  ".join(moved) if moved
                     else "" if timed_out else "nothing changed"))
        if c["beside"] and not timed_out:
            print("files each branch made or moved changes against the main line before the run: "
                  + ("\n  " + "\n  ".join(changes) if changes else "no branch made or moved"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
