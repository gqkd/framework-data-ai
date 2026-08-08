#!/usr/bin/env python3
"""Which of the six skills fires, for a prompt somebody would actually type.

    python evals/trigger/run.py --runs 1
    python evals/trigger/run.py --case "risolviamo*" --runs 3

WHAT IT MEASURES, AND WHY IT IS NOT A BOOLEAN. Asking "did `audit` fire" per skill hides
the failure that matters: the six overlap, and a prompt going to the wrong one is worse
than a prompt going nowhere, because the wrong skill will confidently do something. Each
case names the one skill that should answer, or `none`, so a single run scores both
whether a skill fires and whether it is the right one, and the confusion between siblings
comes out as a matrix rather than as a rumour.

THE PLUGIN HAS TO BE INSTALLED. The measurement is only worth reading if the skills
resolve the way they will in front of a user. An earlier version of this registered the
six descriptions as `.claude/commands/*.md`, which is a different mechanism, and its
numbers were low for reasons that had nothing to do with the descriptions. Install the
plugin first, from a checkout:

    ln -s $PWD ~/.claude/skills/framework-data-ai      # loads as framework-data-ai@skills-dir
    claude plugin details framework-data-ai            # should list all six

WHY NOT `claude plugin eval`. Because it is in early access and refuses to run on this
account. It is the right tool the day it opens: it reads `evals/**/case.yaml`, resolves
skills-dir plugins, and runs a no-plugin baseline arm by itself. `cases.yaml` is written
to be portable to it, which is why the labels live in data and not in this file.

THE LABELS ARE A JUDGEMENT. `expect` was assigned by hand for the prompts no earlier eval
set claimed, with the reason in `why` where it is not obvious. Read them before trusting a
score: a gold label nobody disagrees with is usually a set of cases that were too easy.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SKILLS = {p.name for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").exists()}

# Writing is denied rather than sandboxed. The run only has to get far enough to pick a
# skill, and a hundred agents let loose with Edit on a copy of a fixture is a slow way to
# discover that one of them rewrote it.
DENY = ["Write", "Edit", "NotebookEdit", "Bash", "WebFetch", "WebSearch"]


def one_run(prompt: str, fixture: Path, timeout: int) -> list[str]:
    """Return the framework skills this prompt invoked, in the order they fired."""
    tmp = Path(tempfile.mkdtemp(prefix="trig-"))
    cwd = tmp / "project"
    shutil.copytree(fixture, cwd) if fixture.exists() else cwd.mkdir(parents=True)
    # CLAUDECODE marks a nested session and changes how the CLI behaves; this has to look
    # like a user at a terminal, because that is the situation being measured.
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    try:
        p = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose",
             "--disallowedTools", *DENY],
            cwd=cwd, env=env, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=timeout)
        out = p.stdout
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    fired = []
    for line in out.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") != "assistant":
            continue
        for c in ev.get("message", {}).get("content", []):
            if c.get("type") == "tool_use" and c.get("name") == "Skill":
                name = str(c.get("input", {}).get("skill", "")).split(":")[-1]
                if name in SKILLS:
                    fired.append(name)
    return fired


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--runs", type=int, default=1, help="repeats per case (default 1)")
    ap.add_argument("--case", default="*", help="glob over the prompt text")
    ap.add_argument("--fixture", type=Path, help="repository to run inside")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--json", type=Path, help="write the full result here")
    args = ap.parse_args()

    cases = [c for c in yaml.safe_load((HERE / "cases.yaml").read_text())["cases"]
             if fnmatch.fnmatch(c["prompt"], args.case)]
    if not cases:
        sys.exit(f"no case matches {args.case!r}")
    fixture = args.fixture or (HERE / "fixture")
    if not fixture.exists():
        print(f"! {fixture} does not exist: running in an empty directory, which is not "
              "a state any of these skills is written for", file=sys.stderr)

    jobs = [(c, i) for c in cases for i in range(args.runs)]
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        fired = list(ex.map(lambda j: one_run(j[0]["prompt"], fixture, args.timeout), jobs))

    per: dict[str, list[list[str]]] = {}
    for (c, _), f in zip(jobs, fired):
        per.setdefault(c["prompt"], []).append(f)

    rows, confusion = [], Counter()
    for c in cases:
        runs = per[c["prompt"]]
        picks = [f[0] if f else "none" for f in runs]
        top = Counter(picks).most_common(1)[0][0]
        hits = sum(1 for p in picks if p == c["expect"])
        rows.append({"prompt": c["prompt"], "expect": c["expect"], "picked": picks,
                     "majority": top, "hits": hits, "runs": len(runs),
                     "pass": hits > len(runs) // 2})
        confusion[(c["expect"], top)] += 1

    names = sorted(SKILLS) + ["none"]
    width = max(len(n) for n in names)
    print(f"\n{'expected':>{width}}  " + " ".join(f"{n[:6]:>6}" for n in names))
    for want in names:
        cells = " ".join(f"{confusion[(want, got)] or '.':>6}" for got in names)
        print(f"{want:>{width}}  {cells}")
    print("\nrows are what should have fired, columns what did\n")

    for r in sorted(rows, key=lambda r: (r["pass"], r["expect"])):
        if not r["pass"]:
            print(f"  MISS  {r['expect']:>11} -> {r['majority']:<11} {r['prompt'][:78]}")
    passed = sum(r["pass"] for r in rows)
    print(f"\n{passed}/{len(rows)} cases")

    if args.json:
        args.json.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"full result -> {args.json}")
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
