#!/usr/bin/env python3
"""Does a skill do the right thing once it fires, on repositories built to tell it apart.

    python evals/behaviour/run.py release           # every case, one at a time
    python evals/behaviour/run.py release --case D  # one of them
    python evals/behaviour/run.py cycle

Triggering asks whether the skill answers. This asks whether the answer is right, which
for a gate is the half that matters: one that fires reliably and says yes to everything is
worse than no gate, because somebody is now relying on it.

One sentence per skill, the same for all of its cases, so what the model gets right or
wrong comes from the repository rather than from how the question was put.

NO TOOL IS DENIED, DELIBERATELY. The release gate has to recompute a hash and recover a
frozen plan with `git show`; without a shell it cannot do what it is told, and the run
would fail for a reason that has nothing to do with the skill. Writes are allowed for the
same reason: `-p` denies them by default, and the first run of this graded judgement only,
because the skill reached the right verdict and then printed a manifest it could not save.
Half of what these skills do is produce artifacts, and an unwritten one cannot be wrong.
The fixture is copied first.

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
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
VALIDATE = HERE.parents[1] / "skills" / "audit" / "scripts" / "validate.py"
FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)


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


def run_one(fixture: Path, prompt: str, timeout: int) -> tuple[str, list[str], list[str], str]:
    """Return the closing text, the skills invoked, what was written, and the validator."""
    tmp = Path(tempfile.mkdtemp(prefix="rel-"))
    cwd = tmp / "project"
    shutil.copytree(fixture, cwd)
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
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
             "--allowedTools", "Read", "Glob", "Grep", "Bash(python3:*)", "Bash(git:*)"],
            cwd=cwd, env=env, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=timeout)
        out = p.stdout
    except subprocess.TimeoutExpired:
        # Kept explicitly separate from "it answered nothing". Conflating the two is how
        # the trigger measurement produced a wrong number twice.
        shutil.rmtree(tmp, ignore_errors=True)
        return "TIMED OUT before answering", [], [], "not run"

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
    shutil.rmtree(tmp, ignore_errors=True)
    return (texts[-1] if texts else "(no closing text)"), skills, written, valid


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("skill", help="which skill's cases to run")
    ap.add_argument("--case", help="one fixture, by the letter or name it starts with")
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()

    spec_file = HERE / args.skill / "cases.yaml"
    if not spec_file.exists():
        sys.exit(f"no cases for {args.skill!r}: {spec_file} does not exist")
    spec = yaml.safe_load(spec_file.read_text())
    root = Path(spec["fixtures_root"])
    if not root.is_absolute():
        root = (HERE.parents[1] / root).resolve()
    cases = [c for c in spec["cases"]
             if not args.case or c["fixture"].startswith(args.case)]
    if not cases:
        sys.exit(f"no fixture starts with {args.case!r}")

    for c in cases:
        fx = root / c["fixture"]
        if not fx.exists():
            print(f"! {fx} is missing, skipping", file=sys.stderr)
            continue
        print(f"\n{'=' * 78}\n{c['fixture']}   expected: {c['expect']}\n  because: "
              f"{c['because']}\n{'=' * 78}")
        text, skills, written, valid = run_one(fx, spec["prompt"], args.timeout)
        print(f"skills invoked : {skills or 'none'}")
        print(f"repo after run : {valid}")
        print("wrote          : " + (", ".join(written) if written else "nothing"))
        print()
        print(text.strip()[:3500])
    return 0


if __name__ == "__main__":
    sys.exit(main())
