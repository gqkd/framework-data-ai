"""Capture validity is testable offline; understanding still requires independent review."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess
import sys

import yaml

from test_phase0 import ROOT

spec = importlib.util.spec_from_file_location("qualify", ROOT / "evals/behaviour/memory/qualify.py")
qualify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualify)
spec = importlib.util.spec_from_file_location("pilot", ROOT / "evals/behaviour/memory/pilot.py")
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


class Qualification(unittest.TestCase):
    def test_capture_never_grades_its_own_answer(self):
        process = {"status": "completed"}
        events = '{"type":"turn.completed"}\n'
        for answer in ("Everything is safe to deploy", "Blocked by the decision"):
            result = qualify.usable_result(process, events, answer, [])
            self.assertEqual(result["status"], "pending-review")
            self.assertNotIn("pass", result)

    def test_incomplete_or_unusable_turn_is_not_a_measurement(self):
        for status, events, answer in (
            ("timeout", '{"type":"turn.completed"}', "answer"),
            ("unavailable", '{"type":"turn.completed"}', "answer"),
            ("completed", 'broken json', "answer"),
            ("completed", '{"type":"turn.started"}', "answer"),
            ("completed", '{"type":"turn.completed"}', ""),
            ("completed", '{"type":"turn.completed"}\n{"type":"error"}', "answer"),
        ):
            self.assertEqual(qualify.usable_result({"status": status}, events, answer, [])["status"],
                             "unavailable")

    def test_deletions_modes_and_symlinks_are_not_invisible(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "keep").write_text("original")
            (root / "remove").write_text("original")
            before = qualify.inventory(root)
            (root / "remove").unlink()
            (root / "keep").write_text("changed")
            (root / "new").write_text("created")
            if os.name != "nt":
                (root / "outside").symlink_to("/does-not-exist")
            changes = qualify.differences(before, qualify.inventory(root))
            self.assertIn({"path": "remove", "change": "deleted"}, changes)
            self.assertIn({"path": "keep", "change": "modified"}, changes)
            self.assertIn({"path": "new", "change": "added"}, changes)
            result = qualify.usable_result({"status": "unavailable"}, "", "", changes)
            self.assertEqual(result["status"], "critical-failure")
            self.assertEqual(result["reason"], "unauthorized-write")

    def test_policy_has_no_write_or_network_grant(self):
        config = qualify.settings(Path("/trial/project"), Path("/runtime"))
        self.assertIn('approval_policy="never"', config)
        self.assertIn('permissions.memory-eval.network.enabled=false', config)
        filesystem = next(c for c in config if c.startswith("permissions.memory-eval.filesystem="))
        self.assertNotIn('"write"', filesystem)
        self.assertNotIn('":root"', filesystem)
        self.assertIn("hooks", qualify.DISABLED)
        self.assertIn("plugins", qualify.DISABLED)
        self.assertIn("multi_agent", qualify.DISABLED)

    def test_prompt_and_exposed_runtime_do_not_include_answer_keys(self):
        self.assertNotIn("must_include", qualify.INSTRUCTIONS)
        self.assertNotIn("expected_status", qualify.INSTRUCTIONS)
        self.assertFalse({"tests", "evals", ".git"} & set(qualify.FRAMEWORK_FILES))

    def test_prepare_requires_an_absent_absolute_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            for destination in (Path("relative"), Path(temporary)):
                with self.assertRaises(ValueError):
                    qualify.prepare(destination, [])

    def test_prepare_and_replay_keep_exact_inputs_without_old_answers(self):
        case = yaml.safe_load(qualify.CASES.read_text())["cases"][0]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original, replay = root / "original", root / "replay"
            qualify.prepare(original, [case])
            trial = original / "trials" / case["name"]
            (trial / "answer.md").write_text("Old answer must not enter the new attempt")
            qualify.replay(original, replay, [case])
            self.assertEqual(qualify.inventory(original / "framework"),
                             qualify.inventory(replay / "framework"))
            self.assertEqual(qualify.inventory(trial / "project"),
                             qualify.inventory(replay / "trials" / case["name"] / "project"))
            self.assertFalse((replay / "trials" / case["name"] / "answer.md").exists())
            self.assertFalse((replay / "framework/evals").exists())
            self.assertEqual((trial / "prompt.txt").read_text(), qualify.INSTRUCTIONS + case["prompt"] + "\n")
            (trial / "project/AGENTS.md").write_text("tampered")
            with self.assertRaisesRegex(ValueError, "project changed"):
                qualify.replay(original, root / "tampered-project", [case])
            (original / "framework/FRAMEWORK.md").write_text("tampered")
            with self.assertRaisesRegex(ValueError, "framework changed"):
                qualify.replay(original, root / "tampered-framework", [case])

    def test_framework_mutation_is_captured_as_well_as_project_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project, framework = root / "project", root / "framework"
            project.mkdir()
            framework.mkdir()
            before = qualify.inventory(project), qualify.inventory(framework)
            (framework / "new-rule").write_text("tampered")
            changes = qualify.input_changes(project, before[0], framework, before[1])
            self.assertEqual(changes, [dict(path="new-rule", change="added", scope="framework")])
            self.assertEqual(qualify.usable_result({"status": "completed"},
                '{"type":"turn.completed"}', "answer", changes)["status"], "critical-failure")

    def test_process_capture_keeps_full_streams(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            process = qualify.capture_process([sys.executable, "-B", "-c",
                "import sys; print('x' * 100000); print('diagnostic', file=sys.stderr)"],
                cwd=output, output=output, prefix="test", timeout=10)
            self.assertEqual(process["status"], "completed")
            self.assertEqual((output / "test.stdout").read_text(), "x" * 100000 + "\n")
            self.assertEqual((output / "test.stderr").read_text(), "diagnostic\n")

    @unittest.skipUnless(sys.platform == "linux", "process-group containment adapter is Linux-only")
    def test_timeout_retains_diagnostics_and_is_not_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            process = qualify.capture_process([sys.executable, "-B", "-c",
                "import time; print('started', flush=True); time.sleep(30)"],
                cwd=output, output=output, prefix="test", timeout=0.5)
            self.assertEqual(process["status"], "timeout")
            self.assertLess(process["exit_code"], 0)
            self.assertEqual((output / "test.stdout").read_text(), "started\n")

    def test_pilot_output_cannot_resolve_into_an_input_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / "repo"
            repo.mkdir()
            for destination in (repo, repo / "new", Path("relative")):
                with self.assertRaises(ValueError):
                    pilot.private_output(destination, [repo])
            if os.name != "nt":
                (root / "alias").symlink_to(repo, target_is_directory=True)
                with self.assertRaises(ValueError):
                    pilot.private_output(root / "alias/new", [repo])
            self.assertEqual(pilot.private_output(root / "private", [repo]), root / "private")

    def test_pilot_git_status_disables_local_fsmonitor(self):
        with patch.object(pilot.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "dirty\n")) as run:
            self.assertEqual(pilot.git_state(Path("/synthetic")), "dirty\n")
            command = run.call_args.args[0]
            self.assertIn("core.fsmonitor=false", command)
            self.assertEqual(run.call_args.kwargs["env"]["GIT_OPTIONAL_LOCKS"], "0")


if __name__ == "__main__":
    unittest.main()
