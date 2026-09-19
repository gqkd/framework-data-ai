#!/usr/bin/env python3
"""Separate flexible-read experiment; keep the historical v1 runner byte-identical."""
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
spec = importlib.util.spec_from_file_location("retrieval_flexible_base", HERE / "run.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
diagnostics = base.load("retrieval_flexible_diagnostics", HERE / "diagnose_reads.py")
MODE = "instrumented-source-retrieval-flexible-v2"
OLD_READING_RULES = """  Parti dalla pagina 1; se serve continua con --start N indicato da next_line.
  Una pagina per comando, senza pipe, riassunti o tagli dell'output.
"""
NEW_READING_RULES = """  Senza opzioni restituisce il file intero. Per intervalli scelti da te usa
  --start N --end M; omettere --end significa fino alla fine del file.
  Una lettura per comando, senza pipe, riassunti o tagli dell'output.
  Se l'output risulta vuoto o troncato, non dichiarare la lettura completa:
  scegli intervalli espliciti per recuperare il testo necessario.
"""
if base.ADAPTER_PROMPT.count(OLD_READING_RULES) != 1:
    raise RuntimeError("v1 adapter changed; review the flexible experiment explicitly")
ADAPTER_PROMPT = base.ADAPTER_PROMPT.replace(OLD_READING_RULES, NEW_READING_RULES)
POLICY = {"default": "whole-file", "ranges": "agent-selected inclusive start/end",
          "forced_page_lines": None, "forced_page_bytes": None,
          "max_source_file_bytes": 2_000_000,
          "delivery": "instrumented, not ordinary unmodified IDE reads"}
EXTRA_INPUTS = ("run_flexible.py", "read_source_flexible.py", "diagnose_reads.py")


def expected_prompt(output, question):
    return (output / "evaluator/prompts" / (question + ".txt")).read_text(
        encoding="utf-8") + ADAPTER_PROMPT.format(python=shlex.quote(sys.executable))


def prepare_run(source, output, questions, repetitions=1, max_trials=6, pair_order="scheduled"):
    output = Path(output)
    # The base reconstructs the frozen corpus and verifies exact local Git objects.
    selected = base.prepare_run(source, output, questions, repetitions, max_trials, pair_order)
    state = json.loads((output / "run.json").read_bytes())
    for row in selected:
        trial = output / "trials" / row["id"]
        shutil.copyfile(HERE / "read_source.py", trial / "tools/read_source_v1.py")
        shutil.copyfile(HERE / "read_source_flexible.py", trial / "tools/read_source.py")
        (trial / "prompt.txt").write_text(expected_prompt(output, row["question"]),
                                         encoding="utf-8", newline="\n")
        # Only tools/prompt change during construction, before any probe or execution.
        before = json.loads((trial / "before.json").read_bytes())
        for scope in ("project", "framework"):
            if before[scope] != base.capture.inventory(trial / scope):
                raise ValueError("source/runtime changed during flexible preparation")
        before["tools"] = base.capture.inventory(trial / "tools")
        base.save(trial / "before.json", before)
    state.update(mode=MODE, reader_policy=POLICY,
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
        raise ValueError("not a flexible-read experiment")
    for row in selected:
        trial = output / "trials" / row["id"]
        if (trial / "prompt.txt").read_text(encoding="utf-8") != expected_prompt(output, row["question"]):
            raise ValueError("flexible prompt changed after preparation")
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
        parser.exit(1, f"Flexible retrieval run stopped: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
