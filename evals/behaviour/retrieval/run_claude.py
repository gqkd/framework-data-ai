#!/usr/bin/env python3
"""Second model family for the same frozen experiment: Claude Code driving Opus.

The corpus, questions, oracle, arms, instrumented reader and prompts are the ones the
codex adapter already uses. Only the agent runtime changes, so a difference between the
two model families is separable from a difference between framework versions.

Isolation is enforced by Claude Code's own permission layer, not by folder structure:
restricted mode confines the file tools to the trial, the allowed-tool patterns bound
what Bash may run, and permission prompts are denied rather than asked. A preflight
probe must prove that before any measured trial runs. This adapter never grades answers.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("retrieval_claude_base", HERE / "run_flexible.py")
flexible = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flexible)
base = flexible.base
diagnostics = flexible.diagnostics
MODE = "instrumented-source-retrieval-claude-v4"
POLICY = dict(flexible.POLICY, agent_runtime="claude-code", permission_layer="restricted+allowed-tools")


def allowed_tools(python):
    """Exactly the capabilities the frozen prompt already grants, nothing wider."""
    return [f"Bash({python} ../tools/read_source.py:*)",
            f"Bash({python} ../framework/memory.py:*)",
            f"Bash({python} ../framework/validate.py:*)",
            "Bash(ls:*)", "Bash(find:*)", "Bash(grep:*)", "Bash(rg:*)",
            "Bash(git status:*)", "Bash(git log:*)", "Bash(git rev-parse:*)"]


def model_command(claude, trial, model, python):
    return [claude, "--print", "--model", model, "--restricted", "--tools", "Bash",
            "--allowedTools", *allowed_tools(python),
            "--disallowedTools", "WebFetch", "WebSearch", "Task",
            "--permission-mode", "manual", "--permission-prompts", "none",
            "--strict-mcp-config", "--output-format", "stream-json", "--verbose",
            "--add-dir", str(trial / "framework"), "--add-dir", str(trial / "tools"),
            "--add-dir", str(trial / "scratch")]


def translate(stream):
    """Claude stream-json -> the codex event shape the shared diagnostics already parse.

    Only recognised Bash tool calls become reader events; anything unrecognised is kept
    verbatim so an unexpected shape is visible rather than silently scored as absent.
    """
    pending, events, usage = {}, [], None
    for line in stream.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            events.append({"type": "unparsed", "raw": line[:2000]})
            continue
        kind = record.get("type")
        if kind == "assistant":
            for block in record.get("message", {}).get("content", []):
                if block.get("type") == "tool_use" and block.get("name") == "Bash":
                    pending[block.get("id")] = block.get("input", {}).get("command", "")
        elif kind == "user":
            for block in record.get("message", {}).get("content", []):
                if block.get("type") != "tool_result":
                    continue
                command = pending.pop(block.get("tool_use_id"), "")
                content = block.get("content")
                if isinstance(content, list):
                    content = "".join(part.get("text", "") for part in content
                                      if isinstance(part, dict))
                events.append({"type": "item.completed", "item": {
                    "id": block.get("tool_use_id"), "type": "command_execution",
                    "status": "completed", "exit_code": 1 if block.get("is_error") else 0,
                    "command": f"/bin/bash -lc {shlex.quote(command)}",
                    "aggregated_output": content or ""}})
        elif kind == "result":
            usage = record.get("usage")
            events.append({"type": "turn.completed", "usage": usage or {}})
    return events, usage, len(pending)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-prepared", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--question", action="append", required=True)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--max-trials", type=int, default=6)
    parser.add_argument("--pair-order", choices=("scheduled", "AB", "BA"), default="scheduled")
    parser.add_argument("--claude", default="claude")
    parser.add_argument("--model", default="opus")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--check-auth", action="store_true",
                        help="report whether the nested CLI can authenticate, then stop")
    args = parser.parse_args(argv)

    if args.check_auth:
        done = subprocess.run([args.claude, "auth", "status"], capture_output=True, text=True, timeout=120)
        try:
            state = json.loads(done.stdout)
        except json.JSONDecodeError:
            state = {"loggedIn": False, "authMethod": "unreadable"}
        print(json.dumps({"logged_in": bool(state.get("loggedIn")),
                          "auth_method": state.get("authMethod"),
                          "runnable": bool(state.get("loggedIn")),
                          "remedy": None if state.get("loggedIn") else
                          "run 'claude auth login' or 'claude setup-token' in an interactive terminal"},
                         ensure_ascii=False))
        return 0 if state.get("loggedIn") else 1

    selected = flexible.prepare_run(args.from_prepared, args.output, args.question,
                                    args.repetitions, args.max_trials, args.pair_order)
    state = json.loads((args.output / "run.json").read_bytes())
    state.update(mode=MODE, reader_policy=POLICY, requested_model=args.model,
                 agent_runtime="claude-code", actual_model_identity=None,
                 allowed_tools=allowed_tools(args.python),
                 model_command_shape=model_command(args.claude, args.output / "trials" / "SAMPLE",
                                                   args.model, args.python))
    state["runner_inputs"][(HERE / "run_claude.py").relative_to(base.ROOT).as_posix()] = \
        base.digest((HERE / "run_claude.py").read_bytes())
    base.save(args.output / "run.json", state)
    print(json.dumps({"status": "prepared-not-executed", "mode": MODE,
                      "trials": len(selected), "model_invocations_attempted": 0,
                      "blocked_on": "nested CLI authentication"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
