#!/usr/bin/env python3
"""Sidecar diagnostics: never replace results, infer cognition, or grant reading credit."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shlex

spec = importlib.util.spec_from_file_location(
    "retrieval_diagnostic_metrics", Path(__file__).with_name("metrics.py"))
metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics)


def reader_command(command):
    """Recognize the instrumented reader, not arbitrary shell reads; never execute text."""
    if not isinstance(command, str):
        return False
    try:
        words = shlex.split(command)
        if len(words) == 3 and Path(words[0]).name in ("bash", "sh") and words[1] in ("-lc", "-c"):
            words = shlex.split(words[2])
    except ValueError:
        return False
    return any(word == "../tools/read_source.py" or word.endswith("/tools/read_source.py")
               for word in words)


def inspect(text, roots):
    events, invalid = metrics.events_from(text)
    records, seen = [], set()
    duplicate_ids = []
    for event in events:
        item = event.get("item")
        if event.get("type") != "item.completed" or not isinstance(item, dict) or (
                item.get("type") != "command_execution" or not reader_command(item.get("command"))):
            continue
        identifier = item.get("id")
        if not isinstance(identifier, str):
            continue
        if identifier in seen:
            duplicate_ids.append(identifier)
            continue
        seen.add(identifier)
        observed = metrics.deliveries_from([event], roots)
        output = item.get("aggregated_output")
        if item.get("status") != "completed" or type(item.get("exit_code")) is not int or item["exit_code"] != 0:
            status = "command_failed"
        elif not isinstance(output, str):
            status = "missing_output"
        elif not output.strip():
            status = "empty_output"
        elif observed["deliveries"] and not observed["unverified_frames"]:
            status = "verified_text"
        elif observed["deliveries"]:
            status = "partial_verified_text"
        elif metrics.reader.BEGIN in output:
            status = "unverified_or_truncated_output"
        else:
            status = "unrecognized_output"
        records.append({"item_id": identifier, "command": item["command"], "status": status,
                        "output_characters": len(output) if isinstance(output, str) else None,
                        "verified_frames": len(observed["deliveries"]),
                        "unverified_frames": observed["unverified_frames"]})
    counts = {name: sum(row["status"] == name for row in records) for name in (
        "verified_text", "partial_verified_text", "empty_output", "missing_output",
        "command_failed", "unverified_or_truncated_output", "unrecognized_output")}
    return {"schema": "framework/retrieval-reading-diagnostics/v1",
            "scope": "recognized reader commands only; no model-input attestation",
            "reader_commands": len(records), "counts": counts, "records": records,
            "invalid_event_lines": invalid, "duplicate_reader_ids": duplicate_ids,
            "source_output_status": (
                "not-assessed" if not records else
                "complete-observed-outputs" if not invalid and not duplicate_ids and
                all(row["status"] == "verified_text" for row in records) else
                "incomplete-observed-outputs"),
            "semantic_quality": "not-graded", "retroactive_credit": False}


def inspect_trial(trial):
    trial = Path(trial)
    return inspect((trial / "events.stdout").read_text(encoding="utf-8", errors="replace"),
                   {name: trial / name for name in ("project", "framework")})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trial", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_trial(args.trial), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
