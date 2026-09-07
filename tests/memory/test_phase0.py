"""Frozen acceptance inputs and repaired defects, through the real validator CLI.

The phase-one fixes removed three expectedFailure markers without changing the desired
answers. Historical findings stay frozen; phase1-findings.yaml records the additive delta.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[2]
VALIDATE = ROOT / "skills/audit/scripts/validate.py"
GENERATOR = ROOT / "evals/fixtures/generators/memory.py"
SPEC = ROOT / "tests/fixtures/memory/acceptance.yaml"
CASES = ROOT / "evals/behaviour/memory/cases.yaml"
spec = importlib.util.spec_from_file_location("memory_fixture_generator", GENERATOR)
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


def metadata(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---", 2)[1] if text.startswith("---\n") else text)


def content_hashes(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()
            and ".git" not in p.relative_to(root).parts}


def validate(root: Path, *, pr=False) -> dict:
    command = [sys.executable, "-B", str(VALIDATE), "--root", str(root),
               "--json", "--stale-days", "36500"]
    if pr:
        command += ["--pr-text-file", str(root / ".acceptance/pr.txt"),
                    "--changed-files", str(root / ".acceptance/changed.txt")]
    run = subprocess.run(command, capture_output=True, text=True, timeout=60)
    if run.returncode not in (0, 1):
        raise AssertionError(f"Validator failed to run for {root.name}: {run.stderr}")
    report = json.loads(run.stdout)
    for key in ("errors", "warnings", "findings"):
        if key not in report:
            raise AssertionError(f"Missing {key} in validator report: {report}")
    if run.returncode != (1 if report["errors"] else 0):
        raise AssertionError(f"Exit status disagrees with JSON: {report}")
    return report


def findings(report: dict, code: str) -> set[str]:
    return {f["path"].replace("\\", "/") for f in report["findings"] if f["code"] == code}


class PhaseZero(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="framework-memory-phase0-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name) / "fixtures"
        fixture.build(cls.root)
        cls.contract = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
        cls.behaviour = yaml.safe_load(CASES.read_text(encoding="utf-8"))
        cls.before = content_hashes(cls.root)
        cls.reports = {name: validate(cls.root / name) for name in fixture.SCENARIOS}
        cls.pr_reports = {name: validate(cls.root / name, pr=True)
                          for name in ("qualified-impact", "local-impact-control")}
        # These are real documents discovered from disk, not mocked Artifact instances.
        # Permit only the intended contract/PR error here; the exact severity and finding
        # delta are asserted below, independently of the regression assertions.
        for name, report in [*cls.reports.items(), *cls.pr_reports.items()]:
            allowed = {"CHG002", "PR004"} if name in (
                "qualified-impact", "local-impact-control") else set()
            errors = [f for f in report["findings"]
                      if f["level"] == "error" and f["code"] not in allowed]
            if errors:
                raise AssertionError(f"Invalid fixture {name}: {json.dumps(errors, indent=2)}")
        # Validate the actual shape the historical regressions depend on.
        root = cls.root / "qualified-impact"
        chg = metadata(root / fixture.CHG)
        icg = metadata(root / fixture.ICG)
        if (chg["derives_from"] != ["alpha:SIG-001"] or chg["icg"] != icg["id"]
                or chg["products"] != icg["products"] or chg["status"] != "approved"
                or icg["status"] != "accepted"
                or icg["impacts"] != {"SIG-001": ["architecture"]}
                or "SIG-001" not in (root / "products/alpha/LOG.md").read_text()):
            raise AssertionError("The qualified-reference reproducer lost its prerequisites")
        root = cls.root / "triage-collision"
        if (metadata(root / fixture.ICG)["products"] != ["alpha"]
                or list((root / "products/beta").glob("cycles/*.md"))):
            raise AssertionError("The scope reproducer no longer triages only alpha")
        for product in ("alpha", "beta"):
            log = root / f"products/{product}/LOG.md"
            if metadata(log)["products"] != [product] or "### SIG-001" not in log.read_text():
                raise AssertionError("The scope reproducer lost its two distinct signals")
        # Freeze warnings and informational findings too: a broken reference must not
        # masquerade as a successful reproduction simply because it is non-blocking.
        baseline = yaml.safe_load((SPEC.parent / "baseline-findings.yaml").read_text())
        corrections = yaml.safe_load((SPEC.parent / "phase1-findings.yaml").read_text())
        for mode, reports in (("audit", cls.reports), ("pr", cls.pr_reports)):
            if set(baseline[mode]) != set(reports):
                raise AssertionError(f"Incomplete {mode} baseline")
            for name, report in reports.items():
                observed = [(f["code"], f["path"].replace("\\", "/"), f["level"])
                            for f in report["findings"]]
                expected = [tuple(item) for item in baseline[mode][name]]
                expected += [tuple(item) for item in corrections.get(mode, {}).get(name, [])]
                if sorted(observed) != sorted(expected):
                    raise AssertionError(f"Unplanned finding drift in {mode}/{name}: {observed}")

    def test_all_scenarios_are_generated_and_readable(self):
        self.assertEqual(set(fixture.SCENARIOS), {p.name for p in self.root.iterdir()})
        for name in fixture.SCENARIOS:
            with self.subTest(fixture=name):
                self.assertTrue((self.root / name / "AGENTS.md").is_file())
                self.assertIsInstance(self.reports[name]["findings"], list)

    def test_generation_is_content_and_commit_deterministic(self):
        another = Path(self.temp.name) / "repeat"
        fixture.build(another)
        self.assertEqual(self.before, content_hashes(another))
        for dotgit in self.root.rglob(".git"):
            repo = dotgit.parent
            other = another / repo.relative_to(self.root)
            self.assertEqual(fixture.git(repo, "rev-parse", "HEAD"),
                             fixture.git(other, "rev-parse", "HEAD"))

    def test_generator_refuses_to_overwrite_an_existing_destination(self):
        with self.assertRaises(ValueError):
            fixture.build(self.root)
        self.assertEqual(self.before, content_hashes(self.root))

    def test_document_only_has_design_without_invented_code(self):
        root = self.root / "document-only"
        self.assertNotIn("code", metadata(root / "products/alpha/product.yaml"))
        self.assertFalse((root / "code").exists())
        self.assertFalse((root / "products/alpha/ARC.md").exists())
        self.assertEqual(len(list(root.glob("initiatives/*/SD-*.md"))), 1)
        self.assertFalse(list(root.glob("products/*/changes/CHG-*.md")))

    def test_available_repositories_are_separate_clean_local_git_repositories(self):
        root = self.root / "multi-repo"
        repos = sorted(p for p in (root / "code").iterdir() if (p / ".git").is_dir())
        self.assertEqual([p.name for p in repos], ["alpha-api", "beta-worker", "shared-rules"])
        for repo in repos:
            with self.subTest(repo=repo.name):
                self.assertEqual(Path(fixture.git(repo, "rev-parse", "--show-toplevel")).resolve(),
                                 repo.resolve())
                self.assertEqual(fixture.git(repo, "status", "--porcelain"), "")
                self.assertEqual(fixture.git(repo, "remote"), "")

    def test_shared_repository_has_one_authoritative_declaration(self):
        root = self.root / "multi-repo"
        self.assertEqual(set(metadata(root / "PLATFORM.md")["code"]), {"rules"})
        for product in ("alpha", "beta"):
            own = metadata(root / f"products/{product}/product.yaml")["code"]
            self.assertEqual(len(own), 1)
            self.assertNotIn("rules", own)

    def test_unavailable_checkout_is_declared_not_fabricated(self):
        root = self.root / "missing-code"
        entry = metadata(root / "products/beta/product.yaml")["code"]["worker"]
        self.assertEqual(entry["path"], "code/beta-worker")
        self.assertFalse((root / entry["path"]).exists())
        self.assertNotIn("verified_code", metadata(root / "products/beta/ARC.md"))

    def test_old_attestation_points_to_a_real_parent_commit(self):
        root = self.root / "multi-repo"
        recorded = metadata(root / "products/alpha/ARC.md")["verified_code"]["product.api"]
        repo = root / "code/alpha-api"
        self.assertEqual(recorded, fixture.git(repo, "rev-parse", "HEAD^"))
        self.assertNotEqual(recorded, fixture.git(repo, "rev-parse", "HEAD"))
        self.assertNotIn("def health", fixture.git(repo, "show", f"{recorded}:service.py"))
        self.assertIn("def health", (repo / "service.py").read_text())

    def test_synthetic_code_tests_run_without_network_or_extra_dependencies(self):
        root = self.root / "multi-repo/code"
        for repo in ("alpha-api", "beta-worker"):
            with self.subTest(repo=repo):
                env = dict(os.environ, PYTHONPATH=os.pathsep.join(
                    str(p) for p in (root / repo, root / "shared-rules")),
                    PYTHONDONTWRITEBYTECODE="1")
                run = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover",
                                      "-s", "tests"], cwd=root / repo, env=env,
                                     capture_output=True, text=True, timeout=30)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                self.assertIn("Ran 1 test", run.stderr)

    def test_unqualified_global_candidate_exercises_both_gates(self):
        self.assertEqual(findings(self.reports["local-impact-control"], "CHG002"), {fixture.CHG})
        self.assertEqual(findings(self.pr_reports["local-impact-control"], "PR004"), {fixture.CHG})

    def test_unrouted_and_fully_routed_controls(self):
        self.assertEqual(findings(self.reports["triage-unrouted"], "ICG001"),
                         {"products/alpha/LOG.md", "products/beta/LOG.md"})
        self.assertEqual(findings(self.reports["triage-complete"], "ICG001"), set())

    def test_qualified_change_preserves_architecture_obligation(self):
        self.assertEqual(findings(self.reports["qualified-impact"], "CHG002"), {fixture.CHG})

    def test_qualified_pr_preserves_arc_obligation(self):
        self.assertEqual(findings(self.pr_reports["qualified-impact"], "PR004"), {fixture.CHG})

    def test_same_number_does_not_triage_another_product(self):
        self.assertEqual(findings(self.reports["triage-collision"], "ICG001"),
                         {"products/beta/LOG.md"})

    def test_acceptance_sources_exist_and_cover_the_frozen_contract(self):
        self.assertEqual(self.contract["contract_version"], self.behaviour["contract_version"])
        self.assertEqual(self.behaviour["evaluation_policy"]["results"], "not-run")
        self.assertFalse(self.behaviour["evaluation_policy"]["aggregate_score_can_override_critical_failure"])
        coverage, names = set(), set()
        for case in self.behaviour["cases"]:
            with self.subTest(case=case["name"]):
                self.assertNotIn(case["name"], names)
                names.add(case["name"])
                self.assertIn(case["fixture"], fixture.SCENARIOS)
                self.assertIn(case["expected_status"], {"documented", "partial", "blocked", "unknown"})
                for key in ("prompt", "expect", "because", "must_include", "must_not", "required_sources"):
                    self.assertTrue(case[key], key)
                coverage.update(case["coverage"])
                root = self.root / case["fixture"]
                for source in case["required_sources"]:
                    path = root / source["path"]
                    self.assertTrue(path.resolve().is_relative_to(root.resolve()))
                    self.assertTrue(path.is_file(), source["path"])
                    self.assertIn(source["read"], {"full-file", "full-sections"})
                    text = path.read_text(encoding="utf-8")
                    if source["read"] == "full-sections":
                        self.assertTrue(source["sections"])
                        for section in source["sections"]:
                            self.assertRegex(text, rf"(?m)^#+ {re.escape(section)}\s*$")
                for absent in case.get("required_absences", []):
                    self.assertFalse((root / absent).exists(), absent)
        self.assertEqual(coverage, set(self.contract["coverage_required"]))

    def test_fixed_regressions_remain_tests_without_expected_failure(self):
        names = {name for name in dir(type(self))
                 if getattr(getattr(type(self), name), "__unittest_expecting_failure__", False)}
        declared = {name for bug in self.contract["known_regressions"].values() for name in bug["tests"]}
        self.assertEqual(names, set())
        self.assertEqual(len(declared), 3)
        self.assertTrue(all(callable(getattr(type(self), name)) for name in declared))
        self.assertEqual(len(self.contract["known_regressions"]), 2)

    def test_future_acceptance_obligations_are_explicitly_deferred(self):
        checks = self.contract["deferred_checks"]
        self.assertEqual(len(checks), 24)
        self.assertEqual(len({check["id"] for check in checks}), len(checks))
        for check in checks:
            self.assertIn(check["phase"], range(1, 8))
            self.assertTrue(check["input"])
            self.assertTrue(check["expect"])

    def test_current_version_migration_is_a_read_only_noop(self):
        root = self.root / "document-only"
        before = content_hashes(root)
        run = subprocess.run([sys.executable, "-B", str(VALIDATE.with_name("migrate.py")),
                              "--root", str(root), "--framework", str(ROOT), "--json"],
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        report = json.loads(run.stdout)
        self.assertTrue(report["up_to_date"])
        self.assertFalse(report["problems"])
        self.assertFalse(report.get("adopted"))
        self.assertEqual(before, content_hashes(root))

    def test_read_only_validation_does_not_modify_fixture_sources(self):
        self.assertEqual(self.before, content_hashes(self.root))


if __name__ == "__main__":
    unittest.main()
