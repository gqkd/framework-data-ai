"""Offline fixture integrity, not model retrieval quality or token measurements."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "retrieval_prepare", ROOT / "evals/behaviour/retrieval/prepare.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


def metadata(path):
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1])


class RetrievalDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="framework-retrieval-test-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.directory = Path(cls.temp.name)
        cls.project = cls.directory / "project"
        cls.corpus, cls.questions, cls.oracle = prepare.definitions()
        cls.commits = prepare.build_project(cls.project, cls.corpus)
        cls.before = prepare.inventory(cls.project)

    def test_balanced_questions_and_review_status(self):
        self.assertEqual(len(self.questions["questions"]), 24)
        self.assertEqual(self.oracle["review_status"], "pending-independent-human-review")
        self.assertEqual(len(self.oracle["critical_failures"]), 4)
        self.assertEqual(set(self.oracle["cases"]), {q["id"] for q in self.questions["questions"]})

    def test_fiction_is_reproducible_in_another_directory(self):
        destination = self.directory / "repeat"
        commits = prepare.build_project(destination, self.corpus)
        self.assertEqual(commits, self.commits)
        self.assertEqual(prepare.inventory(destination), self.before)

    def test_generated_workspace_excludes_evaluator_and_precomputed_context(self):
        self.assertFalse((self.project / "evaluator").exists())
        self.assertFalse((self.project / "_meta").exists())
        self.assertFalse((self.project / ".framework-memory").exists())
        exposed_names = {Path(p).name for p in self.before}
        for name in ("oracle.yaml", "oracle.json", "questions.yaml", "questions.json",
                     "corpus.yaml", "prepare.py", "schedule.json", "answer.md"):
            self.assertNotIn(name, exposed_names)
        self.assertNotIn("context.json", prepare.PROMPT)

    def test_source_requirements_resolve_and_contain_full_decision_sections(self):
        receipts = prepare.source_receipts(self.project, self.oracle)
        self.assertEqual(set(receipts), set(self.oracle["sources"]))
        for receipt in receipts.values():
            path = self.project / receipt["path"]
            self.assertEqual(receipt["file_sha256"], prepare.digest(path.read_bytes()))
            self.assertTrue(all(span["start_line"] <= span["end_line"]
                                for span in receipt["required_spans"]))
        sections = [span["section"] for span in receipts["sharing-alternatives"]["required_spans"]]
        self.assertEqual(sections, ["Decision", "Consequences", "Alternatives", "Review condition"])

    def test_broken_required_section_is_not_silently_accepted(self):
        oracle = copy.deepcopy(self.oracle)
        oracle["sources"]["sharing"]["sections"] = ["Nonexistent"]
        with self.assertRaisesRegex(ValueError, "Missing/ambiguous section"):
            prepare.source_receipts(self.project, oracle)

    def test_declared_absence_cannot_be_satisfied_by_a_present_file(self):
        oracle = copy.deepcopy(self.oracle)
        oracle["cases"]["R016"]["absences"] = ["AGENTS.md"]
        with self.assertRaisesRegex(ValueError, "Required absence is present"):
            prepare.source_receipts(self.project, oracle)

    def test_no_fake_attestation_or_remote_repository(self):
        helper = prepare.load_generator()
        for name, commits in self.commits.items():
            repo = self.project / "code" / name
            self.assertEqual(helper.git(repo, "remote"), "")
            self.assertEqual(helper.git(repo, "status", "--porcelain"), "")
            self.assertEqual(helper.git(repo, "rev-parse", "HEAD"), commits["head"])
        alpha = self.commits["alpha-api"]
        self.assertNotEqual(alpha["head"], alpha["attested"])
        repo = self.project / "code/alpha-api"
        self.assertEqual(helper.git(repo, "rev-parse", "HEAD^"), alpha["attested"])
        self.assertNotIn("def health", helper.git(repo, "show", alpha["attested"] + ":service.py"))
        self.assertIn("def health", helper.git(repo, "show", alpha["head"] + ":service.py"))
        arc = metadata(self.project / "products/alpha/ARC.md")
        self.assertEqual(arc["verified_code"]["product.api"], alpha["attested"])

    def test_document_only_and_approval_states_are_not_fabricated(self):
        gamma = metadata(self.project / "products/gamma/product.yaml")
        self.assertNotIn("code", gamma)
        self.assertNotIn("verified_code", metadata(self.project / "products/gamma/ARC.md"))
        self.assertFalse((self.project / "code/gamma-scheduler").exists())
        self.assertEqual(metadata(self.project / "products/alpha/changes/CHG-001-boundary.md")["status"],
                         "approved")
        self.assertEqual(metadata(self.project / "products/alpha/changes/CHG-002-trim.md")["status"],
                         "draft")

    def test_same_number_contracts_have_distinct_product_scope(self):
        a = metadata(self.project / "products/alpha/contracts/DC-001-item.md")
        b = metadata(self.project / "products/beta/contracts/DC-001-report.md")
        self.assertEqual(a["id"], b["id"])
        self.assertNotEqual(a["products"], b["products"])

    def test_synthetic_producer_and_consumer_unit_tests_execute(self):
        bootstrap = (
            "import sys, unittest; from pathlib import Path; "
            "root=Path(sys.argv[1]); "
            "sys.path[:0]=[str(root/'code/shared-rules'),str(root/'code'/sys.argv[2])]; "
            "suite=unittest.defaultTestLoader.discover(str(root/'code'/sys.argv[2]/'tests')); "
            "result=unittest.TextTestRunner().run(suite); "
            "sys.exit(0 if result.wasSuccessful() else 1)"
        )
        for repo in ("alpha-api", "beta-worker"):
            result = subprocess.run([sys.executable, "-B", "-c", bootstrap, str(self.project), repo],
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(prepare.inventory(self.project), self.before)

    def test_missing_field_really_breaks_and_independent_input_really_normalizes(self):
        script = """
import sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path[:0] = [str(root/'code/shared-rules'), str(root/'code/beta-worker')]
from worker import consume
assert consume({'item_key': ' OTHER '}) == 'other'
try:
    consume({})
except KeyError as error:
    assert error.args == ('item_key',)
else:
    raise AssertionError('The missing field unexpectedly acquired a fallback')
"""
        result = subprocess.run([sys.executable, "-B", "-c", script, str(self.project)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_schedule_is_paired_repeated_and_deterministic(self):
        schedule = prepare.schedule(self.questions)
        self.assertEqual(len(schedule), 144)
        self.assertEqual(schedule, prepare.schedule(self.questions))
        self.assertNotEqual(schedule, prepare.schedule(self.questions, seed=99))
        self.assertTrue(all(row["status"] == "not-run" for row in schedule))
        for first, second in zip(schedule[::2], schedule[1::2]):
            self.assertEqual(first["question"], second["question"])
            self.assertEqual(first["repetition"], second["repetition"])
            self.assertEqual({first["arm"], second["arm"]}, {"A", "B"})

    def test_path_and_yaml_ambiguities_are_rejected(self):
        for value in ("../escape", "/outside", "C:/outside", "code/../../escape",
                      "a/./b", ".git/config", "evaluator/oracle.json", "a\\b"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                prepare.relative_path(value)
        with self.assertRaisesRegex(ValueError, "Duplicate YAML key"):
            yaml.load("answer: first\nanswer: replacement\n", Loader=prepare.UniqueLoader)

    def test_output_cannot_overwrite_or_enter_framework(self):
        with self.assertRaises(ValueError):
            prepare.build_project(self.project, self.corpus)
        self.assertEqual(prepare.inventory(self.project), self.before)
        for path in (Path("relative"), self.directory, ROOT / "new-benchmark-output"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                prepare.prepare(path)
        if os.name != "nt":
            alias = self.directory / "alias"
            alias.symlink_to(self.project, target_is_directory=True)
            with self.assertRaises(ValueError):
                prepare.prepare(alias / "new")

    def test_commit_inputs_do_not_allow_shell_commands_or_floating_refs(self):
        for value in ("main", "HEAD", "faaf422", "-c", "x;echo injected"):
            with self.assertRaisesRegex(ValueError, "full lowercase commit IDs"):
                prepare.framework_info(value)

    def test_no_execution_or_real_corpus_option_exists(self):
        for argument in ("--execute", "--root"):
            result = subprocess.run([sys.executable, "-B", str(prepare.HERE / "prepare.py"),
                                     "--output", str(self.directory / "never-created"), argument],
                                    capture_output=True, text=True, timeout=20)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unrecognized arguments", result.stderr)
        self.assertFalse((self.directory / "never-created").exists())

    def test_frozen_runtime_preparation_and_historical_compatibility(self):
        # Core fixture tests above work from a shallow checkout. This integration check
        # deliberately does not fetch missing history or substitute a newer baseline.
        try:
            prepare.framework_info(prepare.BASELINE)
            prepare.framework_info(prepare.CANDIDATE)
        except subprocess.CalledProcessError:
            self.skipTest("Pinned Git objects unavailable locally; historical A/B not exercised")
        output = self.directory / "comparison"
        manifest = prepare.prepare(output)
        self.assertEqual(manifest["model_runs"], 0)
        self.assertFalse(manifest["precomputed_context"])
        self.assertEqual(manifest["allowed_arm_differences"], ["framework.yaml"])
        a, b = output / "arms/A/project", output / "arms/B/project"
        self.assertEqual(prepare.inventory(a, omit_config=True),
                         prepare.inventory(b, omit_config=True))
        self.assertNotEqual((a / "framework.yaml").read_bytes(), (b / "framework.yaml").read_bytes())
        for project in (a, b):
            self.assertNotIn("framework_commit", prepare.read_yaml(project / "framework.yaml"))
        for arm in ("A", "B"):
            runtime = output / "arms" / arm / "framework"
            project = runtime.parent / "project"
            for forbidden in ("evals", "tests", ".git"):
                self.assertFalse((runtime / forbidden).exists())
            result = subprocess.run([sys.executable, "-B",
                                     str(runtime / "skills/audit/scripts/validate.py"),
                                     "--root", str(project), "--json", "--stale-days", "36500"],
                                    capture_output=True, text=True, timeout=60)
            report = json.loads(result.stdout)
            self.assertEqual(report["errors"], 0, report["findings"])
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = prepare.read_yaml(prepare.HERE / "validation-expected.yaml")[arm]
            actual = [[f["code"], f["path"].replace("\\", "/"), f["level"]]
                      for f in report["findings"]]
            self.assertEqual(sorted(actual), sorted(expected), report["findings"])
            self.assertEqual(manifest["arms"][arm]["project_files"], prepare.inventory(project))
        self.assertTrue((output / "evaluator/oracle.json").is_file())
        self.assertEqual(len(list((output / "evaluator/prompts").glob("*.txt"))), 24)
        # Schema validation cannot detect an unreachable pin in a Git-less export.
        script = """
import importlib, json, sys
from pathlib import Path
runtime, project = map(Path, sys.argv[1:])
sys.path.insert(0, str(runtime))
import memory
reader = importlib.import_module(memory._name + '.memory.framework_sources')
result = reader.capture_framework(project, root=runtime, skill='audit').result
print(json.dumps({'resolution': result['resolution'], 'gaps': result['gaps'],
                  'sources': [source['path'] for source in result['sources']]}))
"""
        result = subprocess.run([sys.executable, "-B", "-c", script,
                                 str(output / "arms/B/framework"), str(b)],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        rules = json.loads(result.stdout)
        self.assertEqual(rules["resolution"], "version-only-unverified")
        self.assertIn("FRAMEWORK.md", rules["sources"])
        self.assertIn("skills/audit/SKILL.md", rules["sources"])
        self.assertEqual(rules["gaps"], [{"path": "framework.yaml",
                                          "reason": "version-only-does-not-pin-rule-bytes"}])


if __name__ == "__main__":
    unittest.main()
