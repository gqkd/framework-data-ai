#!/usr/bin/env python3
"""Which of the six skills fires, for a prompt somebody would actually type.

    python evals/trigger/run.py --skill resolve
    python evals/trigger/run.py --skill none          # the shared negatives, once
    python evals/trigger/run.py --case "risolviamo*" --runs 3

WHAT IT MEASURES, AND WHY IT IS NOT A BOOLEAN. Asking "did `audit` fire" per skill hides
the failure that matters: the six overlap, and a prompt going to the wrong one is worse
than a prompt going nowhere, because the wrong skill will confidently do something. Each
case names the one skill that should answer, or `none`, so a single run scores both
whether a skill fires and whether it is the right one, and the confusion between siblings
comes out as a matrix rather than as a rumour.

ONE SKILL AT A TIME, IN A REPOSITORY ITS WORK MAKES SENSE IN. Both halves matter. The
whole set does not fit in a session, and a prompt only means what it means somewhere it
could be acted on: run all six against one fixture with an empty open register and
`resolve` scores 5 of 11 for declining to resolve nothing, which is the fixture answering
and not the description. `fixtures.yaml` is that map.

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
import re
import shutil
import subprocess
import sys
import tempfile
import time
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

# A RUN THAT NEVER REACHED A MODEL IS NOT A RUN THAT CHOSE NOTHING. On 2026-08-18 the
# account hit its session limit partway through, and all fifteen `audit` cases came back
# with no skill fired: 0 of 15, in a set that scores 15 of 15 an hour later. Nothing in the
# output said the measurement had not happened, and 0 of 15 is exactly the shape of a
# description that stopped working.
#
# This is the third time the same failure has produced a number here -- the 120 second
# timeout that read as "no skill fired", and the six skills in one fixture -- and all three
# were wrong in the direction somebody acts on. So the run is marked unusable rather than
# scored, and `main` refuses to print a total while any case is.
#
# Matched on the assistant text, because that is where it was actually observed. Matching
# on a `result` event whose error shape nobody here has seen would be a check written
# against a guess, and an unfired check is worse than none.
UNUSABLE = re.compile(r"session limit|usage limit|rate limit|credit balance|"
                      r"upgrade to increase|Claude AI usage limit", re.I)
UNAVAILABLE = "<unusable>"


def one_run(prompt: str, fixture: Path, timeout: int) -> list[str]:
    """Return the framework skills this prompt invoked, in the order they fired.

    The stream is read as it arrives and the run is killed on the first skill, which is
    the whole answer: what happens after is the skill doing its job, and doing it costs
    minutes and tokens for a question already settled.

    Waiting for the process instead is how the first version of this got a wrong number.
    It ran to a 120 second timeout, and on timeout `subprocess.run` hands back a stdout
    that is usually empty, so every slow case parsed as "no skill fired". `start` reads a
    corpus before it does anything and scored 0 of 12 that way, in a run where the skill
    was in fact being invoked correctly every time.
    """
    tmp = Path(tempfile.mkdtemp(prefix="trig-"))
    cwd = tmp / "project"
    shutil.copytree(fixture, cwd) if fixture.exists() else cwd.mkdir(parents=True)
    # CLAUDECODE marks a nested session and changes how the CLI behaves; this has to look
    # like a user at a terminal, because that is the situation being measured.
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    p = subprocess.Popen(
        ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose",
         "--disallowedTools", *DENY],
        cwd=cwd, env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)

    deadline = time.monotonic() + timeout
    fired: list[str] = []
    said: list[str] = []
    answered = False
    try:
        for line in p.stdout:                       # blocks per line, not per process
            line = line.strip()
            if line.startswith("{"):
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    ev = {}
                if ev.get("type") == "assistant":
                    answered = True
                    for c in ev.get("message", {}).get("content", []):
                        if c.get("type") == "text":
                            said.append(c["text"])
                        if c.get("type") == "tool_use" and c.get("name") == "Skill":
                            # `framework-data-ai:start` when installed as a plugin, `start`
                            # from a bare skills directory. Both are the same answer.
                            name = str(c.get("input", {}).get("skill", "")).split(":")[-1]
                            if name in SKILLS:
                                fired.append(name)
                if fired:
                    break
            if time.monotonic() > deadline:
                break
    finally:
        p.kill()
        p.wait(timeout=10)
        shutil.rmtree(tmp, ignore_errors=True)
    # THE HOLE THIS GUARD HAD, FOUND BY A SET THAT SCORED 10 OF 16 AND THEN PASSED THE SAME
    # PROMPTS ONE AT A TIME. The phrase only appears when the CLI gets far enough to have the
    # model say it. Six cases produced no assistant turn at all -- no text, no tool use,
    # nothing -- and that scored as `none`, which is the answer "the model chose not to fire".
    # A process that never produced an assistant turn did not choose anything.
    if not answered:
        return [UNAVAILABLE]
    if not fired and UNUSABLE.search(" ".join(said)):
        return [UNAVAILABLE]
    return fired


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--skill", help="run one skill's cases in that skill's fixture. The "
                                    "whole set in one go does not fit in a session. Use "
                                    "`--skill none` for the negatives, which are shared")
    ap.add_argument("--with-none", action="store_true",
                    help="also run the negatives alongside a skill. Off by default: they "
                         "are the slowest cases, because nothing fires and there is "
                         "nothing to stop early on, and they are the same 25 for all six")
    ap.add_argument("--runs", type=int, default=1, help="repeats per case (default 1)")
    ap.add_argument("--case", default="*", help="glob over the prompt text")
    ap.add_argument("--fixture", type=Path, help="override the fixture for every case")
    ap.add_argument("--fixtures", type=Path, default=HERE / "fixtures.yaml",
                    help="map of skill -> repository to run its cases in")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--json", type=Path, help="write the full result here")
    args = ap.parse_args()

    if args.skill and args.skill not in SKILLS | {"none"}:
        sys.exit(f"unknown skill {args.skill!r}. One of: none, {', '.join(sorted(SKILLS))}")

    want = {args.skill} | ({"none"} if args.with_none else set()) if args.skill else None
    cases = [c for c in yaml.safe_load((HERE / "cases.yaml").read_text())["cases"]
             if fnmatch.fnmatch(c["prompt"], args.case)
             and (want is None or c["expect"] in want)]
    if not cases:
        sys.exit(f"no case matches {args.case!r}")

    # A prompt only means what it means in a repository where it could be acted on. The
    # first full run put all six in one fixture, and that fixture had an empty open
    # register, so `risolviamo gli open` had nothing to resolve: the model declining to
    # start `resolve` there was arguably right, and it scored as a trigger failure. Each
    # skill gets a repository its work makes sense in, and the `none` cases run in
    # whichever one is loaded, since their answer must not depend on it.
    fmap = {}
    if args.fixtures.exists():
        fmap = {k: (ROOT / v).resolve() if not Path(v).is_absolute() else Path(v)
                for k, v in
                yaml.safe_load(args.fixtures.read_text()).get("fixtures", {}).items()}
    default = args.fixture or fmap.get(args.skill) or fmap.get("default")
    if not default or not Path(default).exists():
        sys.exit(f"no fixture for {args.skill or 'this run'}: set one in {args.fixtures} "
                 "or pass --fixture. Running these prompts in an empty directory measures "
                 "nothing, because none of the six is written for one")

    def fixture_for(c):
        want = c["expect"] if c["expect"] != "none" else (args.skill or "default")
        return Path(args.fixture or fmap.get(want) or default)

    jobs = [(c, i) for c in cases for i in range(args.runs)]
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        fired = list(ex.map(
            lambda j: one_run(j[0]["prompt"], fixture_for(j[0]), args.timeout), jobs))

    per: dict[str, list[list[str]]] = {}
    for (c, _), f in zip(jobs, fired):
        per.setdefault(c["prompt"], []).append(f)

    unusable = sum(1 for f in fired if f == [UNAVAILABLE])
    if unusable:
        print(f"\n{unusable} of {len(jobs)} runs never produced an assistant turn -- the "
              "account was out of quota, or the CLI could not start. Those cases would score "
              "as `none`, which is indistinguishable from a description that does not fire.\n"
              "NOT SCORED. Re-run when the account is available.", file=sys.stderr)
        return 2

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
