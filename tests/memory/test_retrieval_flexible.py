"""Offline qualification of flexible reads. No real model or human review simulated as fact."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "evals/behaviour/retrieval"
spec = importlib.util.spec_from_file_location("test_flexible_run", HERE / "run_flexible.py")
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)
reader = run.base.load("test_flexible_reader", HERE / "read_source_flexible.py")
base, metrics, diagnostics = run.base, run.base.metrics, run.diagnostics


def event(output, identifier="read-1", **extra):
    item = {"id": identifier, "type": "command_execution", "status": "completed",
            "exit_code": 0, "command": "/bin/bash -lc 'python ../tools/read_source.py project source.md'",
            "aggregated_output": output}
    item.update(extra)
    return {"type": "item.completed", "item": item}


class FlexibleReader(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="flexible-reader-test-")
        self.addCleanup(temporary.cleanup)
        self.trial = Path(temporary.name)
        self.roots = {scope: self.trial / scope for scope in ("project", "framework")}
        for root in self.roots.values():
            root.mkdir()
            (root / "source.md").write_text("line\n" * 130, encoding="utf-8")

    def test_default_reads_whole_file_without_40_line_or_4000_byte_pages(self):
        path = self.roots["project"] / "source.md"
        path.write_text("long synthetic line: " + "a" * 5000 + "\n" + "line\n" * 130)
        value = reader.page(self.roots, "project", "source.md")
        self.assertEqual(value["end_line"], 131)
        self.assertIsNone(value["next_line"])
        self.assertEqual(value["text"], path.read_text())
        observed = metrics.deliveries_from([event(reader.legacy.frame(value))], self.roots)
        self.assertEqual(observed["deliveries"][0]["end_line"], 131)

    def test_agent_selects_ranges_and_end_beyond_eof_is_clamped(self):
        first = reader.page(self.roots, "project", "source.md", 1, 70)
        last = reader.page(self.roots, "project", "source.md", first["next_line"], 999)
        self.assertEqual((first["end_line"], last["start_line"], last["end_line"]), (70, 71, 130))
        self.assertEqual(first["text"] + last["text"], (self.roots["project"] / "source.md").read_text())
        self.assertEqual(reader.page(self.roots, "project", "source.md", 129)["text"], "line\nline\n")

    def test_invalid_ranges_paths_and_scopes_are_rejected(self):
        for start, end in ((0, None), (True, None), (1, False), (4, 3), (131, 150), (1, "2")):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                reader.page(self.roots, "project", "source.md", start, end)
        for path in ("../source.md", "/source.md", ".git/config", "evaluator/oracle.json", "a//b"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                reader.page(self.roots, "project", path)
        with self.assertRaises(ValueError):
            reader.page(self.roots, "outside", "source.md")

    def test_source_file_safety_limit_and_links_remain(self):
        source = self.roots["project"] / "source.md"
        (source.parent / "alias").symlink_to(source)
        with self.assertRaises(ValueError):
            reader.page(self.roots, "project", "alias")
        source.write_bytes(b"a" * (reader.legacy.MAX_FILE_BYTES + 1))
        with self.assertRaises(ValueError):
            reader.page(self.roots, "project", "source.md")

    def test_nontext_and_empty_file_are_not_claimed_as_read(self):
        source = self.roots["project"] / "source.md"
        for content in (b"", b"\xff"):
            source.write_bytes(content)
            with self.assertRaises(ValueError):
                reader.page(self.roots, "project", "source.md")

    def test_copied_standalone_reader_works_with_only_local_helper(self):
        tools = self.trial / "tools"
        tools.mkdir()
        shutil.copyfile(HERE / "read_source.py", tools / "read_source_v1.py")
        shutil.copyfile(HERE / "read_source_flexible.py", tools / "read_source.py")
        result = subprocess.run([sys.executable, "-B", str(tools / "read_source.py"),
                                 "project", "source.md", "--start", "41", "--end", "100"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout.splitlines()[1])
        self.assertEqual((value["start_line"], value["end_line"]), (41, 100))

    def test_diagnostics_distinguish_empty_missing_failed_and_nonframe(self):
        events = [event("", "empty"), event(None, "missing"), event("failure", "failed", exit_code=2),
                  event("unrecognized", "other"), event(reader.legacy.BEGIN + "\n{", "truncated")]
        result = diagnostics.inspect("\n".join(map(json.dumps, events)), self.roots)
        self.assertEqual(result["reader_commands"], 5)
        for status in ("empty_output", "missing_output", "command_failed",
                       "unrecognized_output", "unverified_or_truncated_output"):
            self.assertEqual(result["counts"][status], 1)
        self.assertEqual(result["source_output_status"], "incomplete-observed-outputs")
        self.assertFalse(result["retroactive_credit"])

    def test_valid_frames_and_partial_output_remain_distinct(self):
        value = reader.page(self.roots, "project", "source.md")
        frame = reader.legacy.frame(value)
        result = diagnostics.inspect(json.dumps(event(frame)), self.roots)
        self.assertEqual(result["counts"]["verified_text"], 1)
        self.assertEqual(result["source_output_status"], "complete-observed-outputs")
        result = diagnostics.inspect(json.dumps(event(frame + reader.legacy.BEGIN + "\n{")), self.roots)
        self.assertEqual(result["counts"]["partial_verified_text"], 1)
        self.assertEqual(result["source_output_status"], "incomplete-observed-outputs")

    def test_duplicate_and_invalid_events_do_not_give_complete_output_status(self):
        value = reader.page(self.roots, "project", "source.md")
        line = json.dumps(event(reader.legacy.frame(value)))
        result = diagnostics.inspect(line + "\n" + line + "\n{", self.roots)
        self.assertEqual(result["reader_commands"], 1)
        self.assertEqual(result["duplicate_reader_ids"], ["read-1"])
        self.assertEqual(result["invalid_event_lines"], [3])
        self.assertEqual(result["source_output_status"], "incomplete-observed-outputs")

    def test_nonreader_tools_are_not_claimed_as_reader_coverage(self):
        result = diagnostics.inspect(json.dumps(event("text", command="cat source.md")), self.roots)
        self.assertEqual(result["reader_commands"], 0)
        self.assertEqual(result["source_output_status"], "not-assessed")
        self.assertFalse(diagnostics.reader_command(None))
        self.assertFalse(diagnostics.reader_command("'broken"))
        self.assertTrue(diagnostics.reader_command("python /tmp/trial/tools/read_source.py project source.md"))

    def test_truncated_full_file_receives_no_retroactive_credit(self):
        value = reader.page(self.roots, "project", "source.md")
        truncated = reader.legacy.frame(value)[:-30]
        observed = metrics.deliveries_from([event(truncated)], self.roots)
        self.assertEqual(observed["deliveries"], [])
        self.assertEqual(observed["unverified_frames"], 1)


class FlexiblePreparation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for commit in (base.dataset.BASELINE, base.dataset.CANDIDATE):
            try:
                base.dataset.framework_info(commit)
            except subprocess.CalledProcessError:
                raise unittest.SkipTest("exact historical Git objects absent; no fetch")
        temporary = tempfile.TemporaryDirectory(prefix="flexible-run-test-")
        cls.addClassCleanup(temporary.cleanup)
        cls.directory = Path(temporary.name)
        cls.source = cls.directory / "prepared"
        base.dataset.prepare(cls.source)

    def output(self):
        return self.directory / self._testMethodName

    def test_prepare_changes_only_tools_prompt_and_experiment_metadata(self):
        old_hashes = {p: base.digest((HERE / p).read_bytes()) for p in
                      ("run.py", "read_source.py", "metrics.py", "prepare.py")}
        with patch.object(base.capture, "capture_process", side_effect=AssertionError("unexpected model")):
            rows = run.prepare_run(self.source, self.output(), ["R001"], pair_order="AB")
        state = json.loads((self.output() / "run.json").read_bytes())
        self.assertEqual([r["arm"] for r in rows], ["A", "B"])
        self.assertEqual(state["mode"], run.MODE)
        self.assertEqual(state["reader_policy"], run.POLICY)
        self.assertEqual(state["model_invocations_attempted"], 0)
        self.assertEqual(len(set(state["prompt_hashes"].values())), 1)
        for row in rows:
            trial = self.output() / "trials" / row["id"]
            for scope in ("project", "framework"):
                # Non-Git source inventory; synthetic Git identity is checked by base.prepare_run.
                self.assertEqual(base.dataset.inventory(trial / scope),
                                 base.dataset.inventory(self.source / "arms" / row["arm"] / scope))
            self.assertEqual(base.changes(trial), [])
            self.assertEqual(set(base.capture.inventory(trial / "tools")),
                             {"read_source.py", "read_source_v1.py"})
        for path, sha in old_hashes.items():
            self.assertEqual(base.digest((HERE / path).read_bytes()), sha)

    def test_v1_remains_default_and_its_prompt_has_not_been_replaced(self):
        rows = base.prepare_run(self.source, self.output(), ["R001"])
        state = json.loads((self.output() / "run.json").read_bytes())
        self.assertEqual(state["mode"], base.MODE)
        self.assertNotIn("reader_policy", state)
        trial = self.output() / "trials" / rows[0]["id"]
        self.assertNotIn("--end M", (trial / "prompt.txt").read_text())
        self.assertEqual(set(base.capture.inventory(trial / "tools")), {"read_source.py"})

    def test_modified_prompt_or_helper_stops_before_cli(self):
        rows = run.prepare_run(self.source, self.output(), ["R001"])
        trial = self.output() / "trials" / rows[0]["id"]
        with patch.object(base, "execute", side_effect=AssertionError("unexpected execution")):
            for relative in ("prompt.txt", "tools/read_source.py", "tools/read_source_v1.py"):
                path = trial / relative
                before = path.read_bytes()
                path.write_text("changed")
                with self.subTest(relative=relative), self.assertRaisesRegex(ValueError, "changed"):
                    run.execute(self.output(), rows, "fake", preflight_only=True)
                path.write_bytes(before)

    def test_modified_mode_is_rejected_before_cli(self):
        rows = run.prepare_run(self.source, self.output(), ["R001"])
        state = json.loads((self.output() / "run.json").read_bytes())
        state["mode"] = base.MODE
        base.save(self.output() / "run.json", state)
        with self.assertRaisesRegex(ValueError, "not a flexible"):
            run.execute(self.output(), rows, "fake", preflight_only=True)

    def test_unrestricted_cli_duration_and_review_requirements_are_preserved(self):
        with patch.object(run, "prepare_run", return_value=[]), patch.object(run, "execute", return_value=0) as mocked:
            self.assertEqual(run.main(["--from-prepared", "/tmp/base", "--output", "/tmp/new",
                                      "--question", "R001", "--execute", "--model", "test-model",
                                      "--reasoning", "high", "--oracle-review", "/tmp/review",
                                      "--no-timeout"]), 0)
            self.assertIsNone(mocked.call_args.kwargs["timeout"])
        rows = run.prepare_run(self.source, self.output(), ["R001"])
        with patch.object(base.subprocess, "run", side_effect=AssertionError("unexpected CLI")):
            with self.assertRaises(ValueError):
                run.execute(self.output(), rows, "fake", model="test-model", reasoning="high")

    def test_simulated_execution_keeps_results_and_adds_diagnostics(self):
        rows = run.prepare_run(self.source, self.output(), ["R001"])
        state = json.loads((self.output() / "run.json").read_bytes())
        review = self.output() / "review.json"
        base.save(review, {"status": "independently-reviewed", "reviewer": "test double only",
                          "independent_of_dataset_author": True, "reviewed_on": "2026-09-14",
                          "reviewed_questions": ["R001"],
                          "prepared_manifest_sha256": state["prepared_manifest_sha256"],
                          "oracle_sha256": base.digest((self.output() / "evaluator/oracle.json").read_bytes())})

        def fake_capture(command, *, output, **kwargs):
            self.assertIsNone(kwargs["timeout"])
            (output / "answer.md").write_text("Test double; not a real answer.")
            events = [event(""), {"type": "turn.completed",
                                  "usage": {"input_tokens": 100, "output_tokens": 20}}]
            (output / "events.stdout").write_text("\n".join(map(json.dumps, events)))
            (output / "events.stderr").write_text("")
            return {"status": "completed", "exit_code": 0, "elapsed_seconds": 0.01}

        version = subprocess.CompletedProcess([], 0, "codex-cli 0.150.1\n", "")
        with patch.object(base.subprocess, "run", return_value=version), \
                patch.object(base, "preflight", return_value={"status": "passed"}), \
                patch.object(base, "skill_paths", return_value=[]), \
                patch.object(base.capture, "capture_process", side_effect=fake_capture):
            self.assertEqual(run.execute(self.output(), rows, "fake", model="test-model",
                                         reasoning="high", timeout=None, review=review), 0)
        for row in rows:
            trial = self.output() / "trials" / row["id"]
            result = json.loads((trial / "result.json").read_bytes())
            diagnostic = json.loads((trial / "reading-diagnostics.json").read_bytes())
            self.assertEqual(result["status"], "pending-review")
            self.assertEqual(result["usage"]["total_tokens"], 120)
            self.assertEqual(result["quality"], "pending-independent-review")
            self.assertEqual(diagnostic["counts"]["empty_output"], 1)
        with self.assertRaisesRegex(ValueError, "fresh untouched"):
            run.execute(self.output(), rows, "fake", preflight_only=True)


if __name__ == "__main__":
    unittest.main()
