"""Offline qualification of the Claude/Opus adapter. No model is called."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "evals/behaviour/retrieval"
spec = importlib.util.spec_from_file_location("test_claude_run", HERE / "run_claude.py")
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


def assistant(tool_id, command):
    return json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": tool_id, "name": "Bash", "input": {"command": command}}]}})


def result(tool_id, text, error=False):
    return json.dumps({"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": tool_id, "is_error": error,
         "content": [{"type": "text", "text": text}]}]}})


class StreamTranslation(unittest.TestCase):
    """Claude's stream must become the shape the shared diagnostics already parse."""

    def test_a_bash_call_and_its_result_become_one_completed_event(self):
        stream = "\n".join([assistant("t1", "python ../tools/read_source.py project A.md"),
                            result("t1", "<<<retrieval-source-v1>>>")])
        events, _, pending = run.translate(stream)
        self.assertEqual(pending, 0)
        self.assertEqual(len(events), 1)
        item = events[0]["item"]
        self.assertEqual(events[0]["type"], "item.completed")
        self.assertIn("read_source.py project A.md", item["command"])
        self.assertEqual(item["aggregated_output"], "<<<retrieval-source-v1>>>")
        self.assertEqual(item["exit_code"], 0)

    def test_an_errored_tool_result_keeps_a_nonzero_exit_code(self):
        stream = "\n".join([assistant("t1", "cat /etc/shadow"), result("t1", "denied", error=True)])
        events, _, _ = run.translate(stream)
        self.assertEqual(events[0]["item"]["exit_code"], 1)

    def test_an_empty_result_is_preserved_as_empty_not_dropped(self):
        stream = "\n".join([assistant("t1", "read"), result("t1", "")])
        events, _, _ = run.translate(stream)
        self.assertEqual(events[0]["item"]["aggregated_output"], "")

    def test_a_call_without_its_result_is_reported_as_pending_not_scored(self):
        events, _, pending = run.translate(assistant("t1", "read"))
        self.assertEqual(pending, 1)
        self.assertEqual(events, [])

    def test_unparsable_lines_are_kept_verbatim_instead_of_being_silently_lost(self):
        events, _, _ = run.translate("not json at all")
        self.assertEqual(events[0]["type"], "unparsed")
        self.assertIn("not json", events[0]["raw"])

    def test_usage_is_taken_from_the_final_result_record(self):
        stream = json.dumps({"type": "result", "usage": {"input_tokens": 10, "output_tokens": 2}})
        events, usage, _ = run.translate(stream)
        self.assertEqual(usage, {"input_tokens": 10, "output_tokens": 2})
        self.assertEqual(events[-1]["type"], "turn.completed")

    def test_a_missing_usage_record_yields_none_rather_than_zero(self):
        _, usage, _ = run.translate(assistant("t1", "read") + "\n" + result("t1", "x"))
        self.assertIsNone(usage)

    def test_non_bash_tool_calls_are_not_counted_as_reader_commands(self):
        stream = json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": "A.md"}}]}})
        events, _, pending = run.translate(stream)
        self.assertEqual((events, pending), ([], 0))


class Capabilities(unittest.TestCase):
    """The adapter grants what the frozen prompt already grants, and no more."""

    def test_allowed_tools_cover_the_instrumented_reader(self):
        tools = run.allowed_tools("/usr/bin/python3")
        self.assertTrue(any("read_source.py" in t for t in tools))

    def test_allowed_tools_do_not_include_a_general_shell_escape(self):
        for tool in run.allowed_tools("/usr/bin/python3"):
            self.assertNotIn("Bash(*)", tool)
            self.assertNotEqual(tool, "Bash")

    def test_network_and_delegation_tools_are_refused(self):
        command = run.model_command("claude", Path("/trial"), "opus", "/usr/bin/python3")
        index = command.index("--disallowedTools")
        for name in ("WebFetch", "WebSearch", "Task"):
            self.assertIn(name, command[index + 1:index + 4])

    def test_permission_prompts_are_denied_not_asked_or_bypassed(self):
        command = run.model_command("claude", Path("/trial"), "opus", "/usr/bin/python3")
        self.assertIn("--permission-prompts", command)
        self.assertEqual(command[command.index("--permission-prompts") + 1], "none")
        self.assertNotIn("--dangerously-skip-permissions", command)
        self.assertNotIn("bypassPermissions", command)

    def test_restricted_mode_is_requested(self):
        self.assertIn("--restricted", run.model_command("claude", Path("/t"), "opus", "/p"))

    def test_mode_is_distinct_from_the_codex_experiments(self):
        self.assertEqual(run.MODE, "instrumented-source-retrieval-claude-v4")
        self.assertNotEqual(run.MODE, run.flexible.MODE)
        self.assertEqual(run.POLICY["ranges"], run.flexible.POLICY["ranges"])
        self.assertEqual(run.POLICY["agent_runtime"], "claude-code")


if __name__ == "__main__":
    unittest.main()
