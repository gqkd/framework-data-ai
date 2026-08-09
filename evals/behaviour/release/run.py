#!/usr/bin/env python3
"""Does the release gate reach the right verdict, on six repositories that differ only in
the evidence they carry.

    python evals/behaviour/release/run.py                 # all six, one at a time
    python evals/behaviour/release/run.py --case D        # one of them

Triggering asks whether the skill answers. This asks whether the answer is right, which is
the half that matters for a gate: a gate that fires reliably and says yes to everything is
worse than no gate, because somebody is now relying on it.

The same sentence goes to all six. Only the repository differs, so anything the model gets
right or wrong comes from the evidence rather than from how the question was put. Five of
the six must block, each for its own reason, and `F` must ship: a set where everything
blocks scores full marks for a gate that refuses everything, which is why `F` was built.

`Bash` is allowed and that is deliberate. The gate as written requires recomputing the
hash of the frozen plan and recovering it from `git show` when it does not match; without
a shell the skill cannot do what it is told to do, and the run would fail for a reason
that has nothing to do with the skill. The fixture is copied first, so it can write
whatever it likes.

GRADING IS BY HAND, AND SIX IS WHY. A keyword match on "go" and "block" would score the
laundering case correct for saying the word while missing that `answer_accuracy` at 0.812
is below a 0.85 threshold, which is the entire point of that fixture. The verdicts are
printed in full and read. That does not scale, and at six cases it does not have to.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
PROMPT = ("possiamo rilasciare la 1.7? il cliente ci ha chiesto se andiamo in produzione "
          "questa settimana")


VALIDATE = HERE.parents[2] / "skills" / "audit" / "scripts" / "validate.py"


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

    try:
        r = subprocess.run([sys.executable, str(VALIDATE), "--root", str(cwd), "--json"],
                           capture_output=True, text=True, timeout=120)
        d = json.loads(r.stdout)
        verdict = (f"{d['errors']} errors, {d['warnings']} warnings: "
                   + (", ".join(sorted({f['code'] for f in d['findings']})) or "clean"))
    except Exception as e:
        verdict = f"the validator did not complete: {e}"
    return changed, verdict


def run_one(fixture: Path, timeout: int) -> tuple[str, list[str], list[str], str]:
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
        p = subprocess.run(
            ["claude", "-p", PROMPT, "--output-format", "stream-json", "--verbose",
             "--permission-mode", "acceptEdits"],
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
    ap.add_argument("--case", help="one fixture, by the letter that starts its name")
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()

    spec = yaml.safe_load((HERE / "cases.yaml").read_text())
    root = Path(spec["fixtures_root"]).expanduser()
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
        text, skills, written, valid = run_one(fx, args.timeout)
        print(f"skills invoked : {skills or 'none'}")
        print(f"repo after run : {valid}")
        print("wrote          : " + (", ".join(written) if written else "nothing"))
        print()
        print(text.strip()[:3500])
    return 0


if __name__ == "__main__":
    sys.exit(main())
