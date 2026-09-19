#!/usr/bin/env python3
"""Arm C: the candidate runtime with its operational memory actually invoked.

Arms A and B measured whether an agent *discovers* the engine; it never did.
This third condition keeps every frozen input identical and adds, to the candidate
arm only, the invocation documented in references/operational-memory.md. Arm A keeps
the unchanged flexible prompt, so each pair is baseline versus graph-in-use.
Nothing here grades answers, changes the oracle, or relaxes an existing check.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("retrieval_graph_base", HERE / "run_flexible.py")
flexible = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flexible)
base = flexible.base
diagnostics = flexible.diagnostics
MODE = "instrumented-source-retrieval-graph-v3"
POLICY = dict(flexible.POLICY, engine="documented invocation supplied to the candidate arm")
EXTRA_INPUTS = ("run_graph.py",)

# Verbatim command form from references/operational-memory.md, "Assemble, then read".
GRAPH_PROMPT = """- Il runtime adottato include il motore di memoria operativa. Prima di leggere le fonti
  assemblalo esplicitamente, come prescrive references/operational-memory.md:
  {python} ../framework/memory.py context --root ../project --goal "<la domanda>" --skill audit
  Puoi aggiungere --product per il prodotto interessato e interrogare il grafo con
  {python} ../framework/memory.py query --root ../project --text "<termine>"
  Generazione e consegna non sono lettura: le fonti che ti servono vanno comunque aperte
  con il lettore strumentato. Il pacchetto non autorizza nulla e non attesta comprensione.
  Se il motore non e' disponibile, leggi direttamente le fonti e dichiara il limite.
"""


def expected_prompt(output, row):
    prompt = flexible.expected_prompt(output, row["question"])
    if row["arm"] == "B":
        prompt += GRAPH_PROMPT.format(python=shlex.quote(sys.executable))
    return prompt


def prepare_run(source, output, questions, repetitions=1, max_trials=6, pair_order="scheduled"):
    output = Path(output)
    selected = flexible.prepare_run(source, output, questions, repetitions, max_trials, pair_order)
    state = json.loads((output / "run.json").read_bytes())
    for row in selected:
        trial = output / "trials" / row["id"]
        (trial / "prompt.txt").write_text(expected_prompt(output, row), encoding="utf-8", newline="\n")
        before = json.loads((trial / "before.json").read_bytes())
        for scope in ("project", "framework"):
            if before[scope] != base.capture.inventory(trial / scope):
                raise ValueError("source/runtime changed during graph preparation")
    state.update(mode=MODE, reader_policy=POLICY,
                 arm_conditions={"A": "baseline runtime, unchanged flexible prompt",
                                 "B": "candidate runtime, documented memory invocation supplied"},
                 prompt_hashes={row["id"]: base.digest(
                     (output / "trials" / row["id"] / "prompt.txt").read_bytes()) for row in selected})
    state["runner_inputs"].update({
        (HERE / name).relative_to(base.ROOT).as_posix(): base.digest((HERE / name).read_bytes())
        for name in EXTRA_INPUTS})
    base.save(output / "run.json", state)
    return selected


def execute(output, selected, codex, helper=None, **kwargs):
    output = Path(output)
    state = json.loads((output / "run.json").read_bytes())
    if state.get("mode") != MODE or state.get("reader_policy") != POLICY:
        raise ValueError("not a graph-condition experiment")
    for row in selected:
        trial = output / "trials" / row["id"]
        if (trial / "prompt.txt").read_text(encoding="utf-8") != expected_prompt(output, row):
            raise ValueError("graph prompt changed after preparation")
        if row["arm"] == "A" and GRAPH_PROMPT.split("\n")[0] in (trial / "prompt.txt").read_text(encoding="utf-8"):
            raise ValueError("baseline arm must not carry the engine instruction")
        for target, source in (("read_source.py", "read_source_flexible.py"),
                               ("read_source_v1.py", "read_source.py")):
            if (trial / "tools" / target).read_bytes() != (HERE / source).read_bytes():
                raise ValueError("flexible reader changed after preparation")
    result = base.execute(output, selected, codex, helper, **kwargs)
    for row in selected:
        trial = output / "trials" / row["id"]
        if (trial / "events.stdout").is_file():
            base.save(trial / "reading-diagnostics.json", diagnostics.inspect_trial(trial))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-prepared", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--question", action="append", required=True)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--max-trials", type=int, default=6)
    parser.add_argument("--pair-order", choices=("scheduled", "AB", "BA"), default="scheduled")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--preflight-only", action="store_true")
    modes.add_argument("--execute", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--reasoning", choices=("minimal", "low", "medium", "high", "xhigh"))
    parser.add_argument("--oracle-review", type=Path)
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--sandbox-helper", type=Path)
    parser.add_argument("--expected-cli", default="0.150.1")
    duration = parser.add_mutually_exclusive_group()
    duration.add_argument("--timeout", type=int, default=600)
    duration.add_argument("--no-timeout", action="store_true")
    args = parser.parse_args(argv)
    if args.timeout <= 0 or (args.execute and (not args.model or not args.reasoning or not args.oracle_review)):
        parser.error("positive timeout and explicit model, reasoning, review required for execution")
    try:
        selected = prepare_run(args.from_prepared, args.output, args.question, args.repetitions,
                               args.max_trials, args.pair_order)
        if args.execute or args.preflight_only:
            return execute(args.output, selected, args.codex, args.sandbox_helper,
                           model=args.model, reasoning=args.reasoning,
                           timeout=None if args.no_timeout else args.timeout,
                           preflight_only=args.preflight_only, review=args.oracle_review,
                           expected_cli=args.expected_cli)
        print(json.dumps({"status": "prepared-not-executed", "mode": MODE,
                          "trials": len(selected), "model_invocations_attempted": 0}))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError, KeyError, TypeError) as error:
        parser.exit(1, f"Graph retrieval run stopped: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
