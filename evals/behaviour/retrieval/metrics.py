"""Conservative delivery/usage extraction. Never grades comprehension or estimates tokens."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re

spec = importlib.util.spec_from_file_location("retrieval_reader_metrics",
                                             Path(__file__).with_name("read_source.py"))
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


def events_from(text):
    events, invalid = [], []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            if not isinstance(event, dict) or not isinstance(event.get("type"), str):
                raise ValueError("not an event")
            events.append(event)
        except ValueError:
            invalid.append(number)
    return events, invalid


def usage_from(events):
    terminal = [e.get("usage") for e in events if e.get("type") == "turn.completed"]
    result = {"status": "unknown", "raw": terminal, "total_tokens": None,
              "input_tokens": None, "output_tokens": None,
              "cached_input_tokens": None, "reasoning_output_tokens": None}
    if len(terminal) != 1 or not isinstance(terminal[0], dict):
        result["reason"] = "one-terminal-usage-required"
        return result
    raw = terminal[0]
    for key in ("input_tokens", "output_tokens"):
        if type(raw.get(key)) is not int or raw[key] < 0:
            result["reason"] = "invalid-or-missing-token-counter"
            return result
    for subset, total in (("cached_input_tokens", "input_tokens"),
                          ("reasoning_output_tokens", "output_tokens")):
        if subset in raw and (type(raw[subset]) is not int or not 0 <= raw[subset] <= raw[total]):
            result["reason"] = "inconsistent-subset-counter"
            return result
    result.update({key: raw.get(key) for key in result if key.endswith("_tokens")})
    result.update(status="observed", total_tokens=raw["input_tokens"] + raw["output_tokens"])
    return result


def valid_delivery(value, roots):
    """Validate delivered text, not a self-report, hash-only receipt, or command intent."""
    if not isinstance(value, dict) or value.get("schema") != "retrieval/source-delivery/v1":
        raise ValueError("invalid source delivery")
    scope = value.get("scope")
    if scope not in ("project", "framework"):
        raise ValueError("invalid scope")
    path = reader.source_path(roots[scope], value.get("path"))
    content = path.read_bytes()
    lines = content.decode("utf-8").splitlines(keepends=True)
    start, end = value.get("start_line"), value.get("end_line")
    if type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines):
        raise ValueError("invalid delivered range")
    if value.get("file_sha256") != hashlib.sha256(content).hexdigest() or (
            value.get("total_lines") != len(lines) or value.get("text") != "".join(lines[start - 1:end])):
        raise ValueError("delivered content does not match frozen source")
    return {"scope": scope, "path": value["path"], "start_line": start, "end_line": end,
            "file_sha256": value["file_sha256"]}


def deliveries_from(events, roots):
    deliveries, rejected, tools = [], 0, []
    seen = set()
    pattern = re.compile(r"^" + re.escape(reader.BEGIN) + r"\n([^\n]+)\n" +
                         re.escape(reader.END) + r"(?:\n|$)", re.MULTILINE)
    for event in events:
        if event.get("type") != "item.completed":
            continue
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") not in (
                "command_execution", "mcp_tool_call", "web_search"):
            continue
        identifier = item.get("id")
        if not isinstance(identifier, str) or identifier in seen:
            rejected += 1
            continue
        seen.add(identifier)
        tools.append({"id": identifier, "type": item["type"], "status": item.get("status"),
                      "exit_code": item.get("exit_code"), "command": item.get("command")})
        # This adapter supports only the documented command_execution output shape.
        # Unknown tool shapes are retained, never silently promoted to source reads.
        if item.get("type") != "command_execution" or item.get("status") != "completed" or (
                type(item.get("exit_code")) is not int or item["exit_code"] != 0):
            continue
        output = item.get("aggregated_output")
        if not isinstance(output, str):
            continue
        matches = list(pattern.finditer(output))
        rejected += max(0, output.count(reader.BEGIN) - len(matches))
        for match in matches:
            try:
                delivery = valid_delivery(json.loads(match[1]), roots)
                deliveries.append(dict(delivery, item_id=identifier))
            except (ValueError, OSError, TypeError, KeyError):
                rejected += 1
    return {"deliveries": deliveries, "unverified_frames": rejected, "tools": tools,
            "scope": "verified source text in captured command outputs; not cognition",
            "model_delivery_attestation": "unavailable; CLI output is not an attested model-input payload"}


def retrieval_coverage(case, requirements, deliveries):
    covered = {}
    for identifier in {s for group in case["sources"] for s in group}:
        requirement = requirements[identifier]
        spans = [(d["start_line"], d["end_line"]) for d in deliveries
                 if d["scope"] == "project" and d["path"] == requirement["path"] and
                 d["file_sha256"] == requirement["file_sha256"]]
        received = {n for start, end in spans for n in range(start, end + 1)}
        expected = {n for span in requirement["required_spans"]
                    for n in range(span["start_line"], span["end_line"] + 1)}
        covered[identifier] = bool(expected) and expected <= received
    groups = [any(covered[s] for s in group) for group in case["sources"]]
    return {"required_sources": covered, "groups_covered": sum(groups),
            "groups_required": len(groups), "complete_delivery": bool(groups) and all(groups),
            "semantic_review": "pending", "other_observations": case.get("observations", []),
            "absence_checks": "not-automatically-graded"}


def analyze(text, answer, roots, case, requirements, process, changes, *, stderr=""):
    events, invalid = events_from(text)
    usage = usage_from(events)
    delivery = deliveries_from(events, roots)
    complete = (not invalid and len([e for e in events if e["type"] == "turn.completed"]) == 1
                and not any(e["type"] in ("error", "turn.failed") for e in events)
                and bool(answer.strip()) and process.get("status") == "completed")
    usage["entire_turn_capture"] = complete
    status = "pending-review" if complete else "unavailable"
    reason = "answer-captured-not-graded" if complete else "incomplete-or-invalid-capture"
    infrastructure_errors = []
    if "codex_core::tools::router: error=code-mode host is disabled" in stderr:
        infrastructure_errors.append("disabled-code-mode-tool-host")
        status, reason = "unavailable", "tool-host-unavailable"
    if changes:
        status, reason = "critical-failure", "unauthorized-write"
    return {"status": status, "reason": reason, "invalid_event_lines": invalid,
            "usage": usage, "delivery": delivery, "changes": changes, "process": process,
            "infrastructure_errors": infrastructure_errors,
            "retrieval": retrieval_coverage(case, requirements, delivery["deliveries"]),
            "actual_model_identity": None,
            "quality": "pending-independent-review", "token_savings": None}


def summarize(results):
    arms = {}
    for arm in ("A", "B"):
        observed = [r for r in results if r["arm"] == arm]
        rows = [r for r in observed if r.get("model_invocation_attempted", "usage" in r)]
        known = [r["usage"]["total_tokens"] for r in rows
                 if r.get("usage", {}).get("total_tokens") is not None]
        arms[arm] = {"trials_observed": len(observed), "attempts": len(rows),
                     "observed_token_subtotal": sum(known) if known else None,
                     "attempts_with_unknown_tokens": len(rows) - len(known),
                     "pending_review": sum(r["status"] == "pending-review" for r in rows)}
    return {"arms": arms, "quality_comparison": "not-performed", "token_savings": None,
            "note": "Observed subtotals include unsuccessful attempts; unknown costs are not zero."}
