"""Offline adversarial capture tests. Fake event streams never count as model evaluations."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("test_retrieval_run",
                                             ROOT / "evals/behaviour/retrieval/run.py")
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)
reader, metrics, dataset = run.metrics.reader, run.metrics, run.dataset


def command_event(text, identifier="tool-1", **fields):
    item = dict(id=identifier, type="command_execution", status="completed",
                exit_code=0, command="source read", aggregated_output=text)
    item.update(fields)
    return {"type": "item.completed", "item": item}


def terminal(**fields):
    return {"type": "turn.completed", "usage": dict(input_tokens=100, output_tokens=30, **fields)}


class RetrievalObservation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="retrieval-metrics-test-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.roots = {s: self.directory / s for s in ("project", "framework")}
        for path in self.roots.values():
            path.mkdir()
            (path / "source.md").write_text("first\nsecond\nthird\n", encoding="utf-8")
        self.value = reader.page(self.roots, "project", "source.md")
        self.requirements = {"one": {
            "path": "source.md", "file_sha256": self.value["file_sha256"],
            "required_spans": [{"start_line": 1, "end_line": 3}]}}
        self.case = {"sources": [["one"]]}

    def test_actual_paginated_reader_and_range(self):
        path = self.roots["project"] / "source.md"
        path.write_text("line\n" * 85)
        first = reader.page(self.roots, "project", "source.md")
        second = reader.page(self.roots, "project", "source.md", first["next_line"])
        third = reader.page(self.roots, "project", "source.md", second["next_line"])
        self.assertEqual((first["end_line"], second["end_line"], third["end_line"]), (40, 80, 85))
        self.assertIsNone(third["next_line"])
        self.assertEqual(first["text"] + second["text"] + third["text"], path.read_text())

    def test_reader_fails_closed_on_paths_and_invalid_offsets(self):
        for path in ("../source.md", "/source.md", ".git/config", "evaluator/oracle.json",
                     "a\\b", "C:/test", "./source.md", "a//b", ".", None):
            with self.subTest(path=path), self.assertRaises(ValueError):
                reader.page(self.roots, "project", path)
        for start in (0, -1, True, 20):
            with self.assertRaises(ValueError):
                reader.page(self.roots, "project", "source.md", start)
        with self.assertRaises(ValueError):
            reader.page(self.roots, "evaluator", "source.md")

    def test_reader_rejects_links_long_lines_and_nontext(self):
        link = self.roots["project"] / "link"
        link.symlink_to(self.roots["framework"] / "source.md")
        with self.assertRaises(ValueError):
            reader.page(self.roots, "project", "link")
        for content in (b"x" * (reader.MAX_PAGE_BYTES + 1), b"\xff"):
            (self.roots["project"] / "long.md").write_bytes(content)
            with self.assertRaises(ValueError):
                reader.page(self.roots, "project", "long.md")

    def test_complete_text_frame_is_observed_but_not_understanding(self):
        observed = metrics.deliveries_from([command_event(reader.frame(self.value))], self.roots)
        self.assertEqual(len(observed["deliveries"]), 1)
        coverage = metrics.retrieval_coverage(self.case, self.requirements, observed["deliveries"])
        self.assertTrue(coverage["complete_delivery"])
        self.assertEqual(coverage["semantic_review"], "pending")
        self.assertIn("unavailable", observed["model_delivery_attestation"])

    def test_truncated_hash_only_and_forged_content_receive_no_credit(self):
        for value in (dict(self.value, text="a summary"), dict(self.value, file_sha256="0" * 64),
                      dict(self.value, start_line=True), dict(self.value, end_line=500),
                      {k: v for k, v in self.value.items() if k != "text"}):
            observed = metrics.deliveries_from([command_event(reader.frame(value))], self.roots)
            self.assertEqual(observed["deliveries"], [])
            self.assertEqual(observed["unverified_frames"], 1)
        for text in (reader.frame(self.value).replace(reader.END, ""),
                     reader.BEGIN + "\nnot-json\n" + reader.END + "\n"):
            observed = metrics.deliveries_from([command_event(text)], self.roots)
            self.assertEqual(observed["deliveries"], [])
            self.assertEqual(observed["unverified_frames"], 1)

    def test_command_exit_status_and_plain_cat_are_not_reading_evidence(self):
        for fields in ({"exit_code": 1}, {"exit_code": True}, {"status": "failed"},
                       {"type": "mcp_tool_call"}):
            observed = metrics.deliveries_from([command_event(reader.frame(self.value), **fields)], self.roots)
            self.assertEqual(observed["deliveries"], [])
        self.assertEqual(metrics.deliveries_from([command_event("first\nsecond\nthird\n")],
                                                self.roots)["deliveries"], [])

    def test_updated_events_and_duplicate_completion_are_not_double_counted(self):
        event = command_event(reader.frame(self.value))
        updated = dict(event, type="item.updated")
        observed = metrics.deliveries_from([updated, event, event], self.roots)
        self.assertEqual(len(observed["deliveries"]), 1)
        self.assertEqual(len(observed["tools"]), 1)
        self.assertEqual(observed["unverified_frames"], 1)

    def test_sections_union_and_and_of_or_groups(self):
        deliveries = [dict(self.value, start_line=1, end_line=1),
                      dict(self.value, start_line=3, end_line=3)]
        self.assertFalse(metrics.retrieval_coverage(self.case, self.requirements, deliveries)["complete_delivery"])
        deliveries.append(dict(self.value, start_line=2, end_line=2))
        requirements = dict(self.requirements, two=dict(self.requirements["one"], path="missing.md"))
        case = {"sources": [["two", "one"], ["two"]]}
        observed = metrics.retrieval_coverage(case, requirements, deliveries)
        self.assertEqual(observed["groups_covered"], 1)
        self.assertFalse(observed["complete_delivery"])

    def test_framework_path_cannot_satisfy_project_source(self):
        observation = dict(self.value, scope="framework")
        self.assertFalse(metrics.retrieval_coverage(self.case, self.requirements,
                                                   [observation])["complete_delivery"])

    def test_usage_subsets_are_not_added_twice(self):
        usage = metrics.usage_from([terminal(cached_input_tokens=90, reasoning_output_tokens=20)])
        self.assertEqual(usage["total_tokens"], 130)
        self.assertEqual(usage["cached_input_tokens"], 90)
        self.assertEqual(usage["reasoning_output_tokens"], 20)
        self.assertIsNone(metrics.usage_from([terminal()])["cached_input_tokens"])

    def test_missing_invalid_or_duplicate_usage_is_unknown_not_zero(self):
        for events in ([], [terminal(), terminal()], [{"type": "turn.completed"}],
                       [terminal(cached_input_tokens=101)], [terminal(reasoning_output_tokens=31)],
                       [{"type": "turn.completed", "usage": {"input_tokens": True, "output_tokens": 4}}],
                       [{"type": "turn.completed", "usage": {"input_tokens": -1, "output_tokens": 4}}]):
            self.assertIsNone(metrics.usage_from(events)["total_tokens"])
            self.assertEqual(metrics.usage_from(events)["status"], "unknown")

    def test_capture_never_grades_its_answer_or_computes_savings(self):
        stream = "\n".join(map(json.dumps, [command_event(reader.frame(self.value)), terminal()]))
        result = metrics.analyze(stream, "correct answer", self.roots, self.case, self.requirements,
                                 {"status": "completed"}, [])
        self.assertEqual(result["status"], "pending-review")
        self.assertIsNone(result["token_savings"])
        self.assertIsNone(result["actual_model_identity"])

    def test_disabled_tool_host_is_unavailable_even_after_a_completed_model_turn(self):
        stream = json.dumps(terminal())
        error = "2026-09-13T17:52:31Z ERROR codex_core::tools::router: error=code-mode host is disabled"
        result = metrics.analyze(stream, "Unable to read", self.roots, self.case, self.requirements,
                                 {"status": "completed"}, [], stderr=error)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "tool-host-unavailable")
        self.assertEqual(result["usage"]["total_tokens"], 130)
        self.assertTrue(result["usage"]["entire_turn_capture"])
        self.assertEqual(result["infrastructure_errors"], ["disabled-code-mode-tool-host"])
        # A quoted phrase in model output is not a trusted host diagnostic.
        quoted = metrics.analyze(stream, error, self.roots, self.case, self.requirements,
                                 {"status": "completed"}, [])
        self.assertEqual(quoted["status"], "pending-review")

    def test_timeout_invalid_stream_and_writes_are_distinct(self):
        stream = json.dumps(terminal()) + "\nnot-json"
        result = metrics.analyze(stream, "answer", self.roots, self.case, self.requirements,
                                 {"status": "timeout"}, [])
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["invalid_event_lines"], [2])
        self.assertEqual(result["usage"]["total_tokens"], 130)
        self.assertFalse(result["usage"]["entire_turn_capture"])
        result = metrics.analyze("", "", self.roots, self.case, self.requirements,
                                 {"status": "completed"}, [{"path": "new", "change": "added"}])
        self.assertEqual(result["status"], "critical-failure")

    def test_summary_includes_failed_costs_and_preserves_unknowns(self):
        result = metrics.summarize([
            {"arm": "A", "status": "unavailable", "usage": {"total_tokens": 130}},
            {"arm": "A", "status": "pending-review", "usage": {"total_tokens": None}}])
        self.assertEqual(result["arms"]["A"]["observed_token_subtotal"], 130)
        self.assertEqual(result["arms"]["A"]["attempts_with_unknown_tokens"], 1)
        self.assertIsNone(result["arms"]["B"]["observed_token_subtotal"])
        self.assertIsNone(result["token_savings"])

    def test_selection_keeps_schedule_order_pairs_and_explicit_cap(self):
        _, questions, _ = dataset.definitions()
        schedule = dataset.schedule(questions)
        rows = run.selection(schedule, ["R001"], 2, 6)
        self.assertEqual(len(rows), 4)
        self.assertEqual([r["arm"] for r in rows], [
            r["arm"] for r in schedule if r["question"] == "R001" and r["repetition"] <= 2])
        for ids, repetitions, cap in (([], 1, 6), (["unknown"], 1, 6), (["R001"] * 2, 1, 6),
                                       (["R001"], 4, 20), (["R001"], 2, 3)):
            with self.assertRaises(ValueError):
                run.selection(schedule, ids, repetitions, cap)

    def test_independent_review_is_bound_to_exact_oracle(self):
        path = self.directory / "review.json"
        oracle_bytes = json.dumps({"cases": {"R001": {}, "R002": {}}}).encode()
        prepared_hash = "a" * 64
        for review in ({"status": "pending"}, {"status": "independently-reviewed", "reviewer": "a"}):
            path.write_text(json.dumps(review))
            with self.assertRaises(ValueError):
                run.review_attestation(path, oracle_bytes, ["R001"], prepared_hash)
        reviewed = {"status": "independently-reviewed", "reviewer": "independent reviewer",
                    "reviewed_on": "2026-09-13", "independent_of_dataset_author": True,
                    "oracle_sha256": run.digest(oracle_bytes), "prepared_manifest_sha256": prepared_hash,
                    "reviewed_questions": ["R001"]}
        path.write_text(json.dumps(reviewed))
        self.assertEqual(run.review_attestation(path, oracle_bytes, ["R001"], prepared_hash), reviewed)
        with self.assertRaises(ValueError):
            run.review_attestation(path, b"changed oracle", ["R001"], prepared_hash)
        with self.assertRaises(ValueError):
            run.review_attestation(path, oracle_bytes, ["R001"], "b" * 64)
        with self.assertRaises(ValueError):
            run.review_attestation(path, oracle_bytes, ["R002"], prepared_hash)

    def test_order_override_changes_only_pair_order_not_calendar_or_rows(self):
        _, questions, _ = dataset.definitions()
        schedule = dataset.schedule(questions)
        original = copy.deepcopy(schedule)
        ordinary = run.selection(schedule, ["R001", "R004"], 2, 8)
        for order in ("AB", "BA"):
            rows = run.selection(schedule, ["R001", "R004"], 2, 8, order)
            self.assertEqual({r["id"]: r for r in rows}, {r["id"]: r for r in ordinary})
            for offset in range(0, len(rows), 2):
                self.assertEqual("".join(r["arm"] for r in rows[offset:offset + 2]), order)
                self.assertEqual(rows[offset]["question"], rows[offset + 1]["question"])
                self.assertEqual(rows[offset]["repetition"], rows[offset + 1]["repetition"])
        self.assertEqual(schedule, original)
        with self.assertRaises(ValueError):
            run.selection(schedule, ["R001"], 1, 6, "random")

    def test_cli_unrestricted_duration_is_explicit_and_does_not_change_default(self):
        base = ["--from-prepared", "/synthetic/prepared", "--output", "/synthetic/output",
                "--question", "R001", "--execute", "--model", "test-model",
                "--reasoning", "high", "--oracle-review", "/synthetic/review.json"]
        for options, expected in (([], 600), (["--no-timeout"], None), (["--timeout", "900"], 900)):
            with patch.object(run, "prepare_run", return_value=[]) as prepare, \
                    patch.object(run, "execute", return_value=0) as execute:
                self.assertEqual(run.main(base + options + ["--pair-order", "AB"]), 0)
                self.assertEqual(execute.call_args.kwargs["timeout"], expected)
                self.assertEqual(prepare.call_args.args[-1], "AB")

    def test_review_scope_rejects_unknown_duplicate_missing_and_nonlist_ids(self):
        path = self.directory / "review.json"
        oracle_bytes = json.dumps({"cases": {"R001": {}}}).encode()
        for scope in (None, [], ["R001", "R001"], ["R999"], ["R001", 4], "R001"):
            reviewed = {"status": "independently-reviewed", "reviewer": "test double",
                        "reviewed_on": "2026-09-13", "independent_of_dataset_author": True,
                        "oracle_sha256": run.digest(oracle_bytes), "prepared_manifest_sha256": "a" * 64,
                        "reviewed_questions": scope}
            path.write_text(json.dumps(reviewed))
            with self.assertRaises(ValueError):
                run.review_attestation(path, oracle_bytes, ["R001"], "a" * 64)

    def test_command_has_read_only_sources_and_no_personal_config(self):
        config = run.settings(self.directory, disabled_skills=["/test/skill"])
        parsed = tomllib.loads("\n".join(config))
        files = parsed["permissions"][run.PROFILE]["filesystem"]
        self.assertEqual(files[str(self.directory / "project")], "read")
        self.assertEqual(files[str(self.directory / "framework")], "read")
        self.assertEqual(files[str(self.directory / "scratch")], "write")
        self.assertNotIn(":root", files)
        self.assertNotIn(str(self.directory), files)
        self.assertEqual(parsed["project_doc_max_bytes"], 0)
        self.assertEqual(parsed["shell_environment_policy"]["inherit"], "none")
        self.assertFalse(parsed["skills"]["config"][0]["enabled"])
        command = run.model_command("codex", self.directory, "test-model", "low", None, [])
        for option in ("--ignore-user-config", "--ignore-rules", "--ephemeral", "--strict-config"):
            self.assertIn(option, command)
        self.assertIn("test-model", command)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", command)
        self.assertNotIn("code_mode_host", run.DISABLED)
        self.assertIn("code_mode_host", run.REQUIRED_FEATURES)
        for feature in run.REQUIRED_FEATURES:
            index = command.index(feature)
            self.assertEqual(command[index - 1], "--enable")

    def test_feature_preflight_rejects_missing_or_disabled_tool_runtime(self):
        states = {**{name: False for name in run.DISABLED},
                  **{name: True for name in run.REQUIRED_FEATURES}}
        def render(values):
            return "\n".join(f"{name} under development {str(value).lower()}" for name, value in values.items())
        self.assertEqual(run.feature_status(render(states))["status"], "passed")
        states["code_mode_host"] = False
        self.assertEqual(run.feature_status(render(states))["status"], "unavailable")
        del states["code_mode_host"]
        self.assertEqual(run.feature_status(render(states))["status"], "unavailable")


class RetrievalRunPreparation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for commit in (dataset.BASELINE, dataset.CANDIDATE):
            try:
                dataset.framework_info(commit)
            except subprocess.CalledProcessError:
                raise unittest.SkipTest("exact historical Git objects absent; no fetch")
        cls.temp = tempfile.TemporaryDirectory(prefix="retrieval-run-test-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.directory = Path(cls.temp.name)
        cls.source = cls.directory / "prepared"
        dataset.prepare(cls.source)

    def output(self):
        return self.directory / self._testMethodName

    def test_default_prepares_fresh_paired_trials_without_invoking_any_cli(self):
        with patch.object(run.capture, "capture_process", side_effect=AssertionError("unexpected model")):
            self.assertEqual(run.main(["--from-prepared", str(self.source), "--output", str(self.output()),
                                       "--question", "R001"]), 0)
        manifest = json.loads((self.output() / "run.json").read_bytes())
        self.assertEqual(manifest["model_invocations_attempted"], 0)
        self.assertEqual(len(manifest["selected"]), 2)
        for row in manifest["selected"]:
            trial = self.output() / "trials" / row["id"]
            self.assertFalse((trial / "project/_meta").exists())
            self.assertNotIn("oracle", "\n".join(run.capture.inventory(trial / "tools")))
            self.assertEqual(run.changes(trial), [])
            read = subprocess.run([sys.executable, "-B", str(trial / "tools/read_source.py"),
                                   "project", "AGENTS.md"], capture_output=True, text=True)
            self.assertEqual(read.returncode, 0)
            self.assertIn(reader.END, read.stdout)

    def test_prepared_oracle_and_prompt_tampering_cannot_hide_behind_manifest(self):
        for name in ("oracle.json", "prompts/R001.txt"):
            tampered = self.output() / name.replace("/", "-")
            shutil.copytree(self.source, tampered)
            (tampered / "evaluator" / name).write_text("tampered")
            with self.assertRaisesRegex(ValueError, "prepared bytes differ"):
                run.prepare_run(tampered, self.output() / (name.replace("/", "-") + "-out"), ["R001"])

    def test_existing_output_and_nested_source_are_refused(self):
        for output in (self.source, self.source / "nested", ROOT / "new-run"):
            with self.assertRaises(ValueError):
                run.prepare_run(self.source, output, ["R001"])

    def test_execute_missing_review_never_reaches_cli(self):
        rows = run.prepare_run(self.source, self.output(), ["R001"])
        with patch.object(run.subprocess, "run", side_effect=AssertionError("unexpected CLI")):
            with self.assertRaises(ValueError):
                run.execute(self.output(), rows, "fake", model="test-model", reasoning="low")

    def test_failed_preflight_stops_before_model_and_keeps_sibling_not_run(self):
        rows = run.prepare_run(self.source, self.output(), ["R001"])
        version = subprocess.CompletedProcess([], 0, "codex-cli 0.150.1\n", "")
        with patch.object(run.subprocess, "run", return_value=version), \
                patch.object(run, "preflight", return_value={"status": "unavailable"}), \
                patch.object(run.capture, "capture_process", side_effect=AssertionError("model invoked")):
            self.assertEqual(run.execute(self.output(), rows, "fake", preflight_only=True), 2)
        results = json.loads((self.output() / "results.json").read_bytes())
        self.assertEqual(len(results["not_run"]), 1)
        self.assertEqual(results["results"][0]["reason"], "sandbox-preflight-not-proven")
        for arm in ("A", "B"):
            self.assertEqual(results["summary"]["arms"][arm]["attempts"], 0)
            self.assertEqual(results["summary"]["arms"][arm]["attempts_with_unknown_tokens"], 0)

    def test_simulated_exec_captures_tokens_but_requires_semantic_review(self):
        rows = run.prepare_run(self.source, self.output(), ["R001"])
        review = self.output() / "review.json"
        oracle_bytes = (self.output() / "evaluator/oracle.json").read_bytes()
        dataset.save(review, {"status": "independently-reviewed", "reviewer": "test double, not a real review",
                             "independent_of_dataset_author": True, "reviewed_on": "2026-09-13",
                             "reviewed_questions": ["R001"],
                             "prepared_manifest_sha256": json.loads((self.output() / "run.json").read_bytes())["prepared_manifest_sha256"],
                             "oracle_sha256": run.digest(oracle_bytes)})

        def fake_capture(command, *, output, **kwargs):
            self.assertIsNone(kwargs["timeout"])
            (output / "answer.md").write_text("Synthetic test-double answer, not an LLM result.")
            (output / "events.stdout").write_text(json.dumps(terminal(cached_input_tokens=20)) + "\n")
            (output / "events.stderr").write_text("")
            return {"status": "completed", "exit_code": 0, "elapsed_seconds": 0.01}

        version = subprocess.CompletedProcess([], 0, "codex-cli 0.150.1\n", "")
        with patch.object(run.subprocess, "run", return_value=version), \
                patch.object(run, "preflight", return_value={"status": "passed"}), \
                patch.object(run, "skill_paths", return_value=[]), \
                patch.object(run.capture, "capture_process", side_effect=fake_capture):
            self.assertEqual(run.execute(self.output(), rows, "fake", model="test-model",
                                         reasoning="low", review=review, timeout=None), 0)
        self.assertIsNone(json.loads((self.output() / "run.json").read_bytes())["timeout_seconds_per_trial"])
        results = json.loads((self.output() / "results.json").read_bytes())
        self.assertEqual(len(results["results"]), 2)
        for result in results["results"]:
            self.assertEqual(result["status"], "pending-review")
            self.assertEqual(result["usage"]["total_tokens"], 130)
            self.assertFalse(result["retrieval"]["complete_delivery"])
        self.assertIsNone(results["summary"]["token_savings"])
        with self.assertRaisesRegex(ValueError, "fresh untouched"):
            run.execute(self.output(), rows, "fake", preflight_only=True)

    def test_full_inventory_detects_git_and_tools_mutations(self):
        rows = run.prepare_run(self.source, self.output(), ["R001"])
        trial = self.output() / "trials" / rows[0]["id"]
        (trial / "project/code/alpha-api/.git/config").write_text("tampered")
        (trial / "tools/read_source.py").write_text("tampered")
        observed = run.changes(trial)
        self.assertEqual({x["scope"] for x in observed}, {"project", "tools"})

    def test_review_packets_include_selected_sources_but_not_other_questions(self):
        rows = run.prepare_run(self.source, self.output(), ["R001"])
        directory = self.output() / "evaluator/review"
        self.assertEqual({p.name for p in directory.iterdir()}, {"README.md", "R001.md"})
        packet = (directory / "R001.md").read_text()
        self.assertIn("Con quale linguaggio", packet)
        self.assertIn("Use Python for alpha and beta application services.", packet)
        self.assertIn("Review if a required supported runtime cannot execute Python.", packet)
        self.assertIn("La risposta non deve affermare:", packet)
        self.assertNotIn("R002", packet)
        pending = json.loads((self.output() / "oracle-review.template.json").read_bytes())
        self.assertEqual(pending["reviewed_questions"], ["R001"])
        self.assertFalse(pending["independent_of_dataset_author"])
        for row in rows:
            self.assertFalse((self.output() / "trials" / row["id"] / "project/evaluator").exists())

    def test_modified_evaluator_requirements_stop_before_cli(self):
        rows = run.prepare_run(self.source, self.output(), ["R001"])
        (self.output() / "evaluator/source-requirements.json").write_text("{}")
        with patch.object(run.subprocess, "run", side_effect=AssertionError("unexpected CLI")):
            with self.assertRaisesRegex(ValueError, "evaluator inputs changed"):
                run.execute(self.output(), rows, "fake", preflight_only=True)


if __name__ == "__main__":
    unittest.main()
