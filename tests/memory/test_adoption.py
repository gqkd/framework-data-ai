"""Real old/new complete exports, isolated adoption, opt-in memory and forward-only gaps."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import yaml

from test_phase0 import ROOT, fixture, content_hashes
from test_documentary import amend, config
import test_documentary as documentary

BASE = "db75f310e2f42453cb0fe1b26573c3f6b5736790"
REGISTRY = "schemas/artifact-types.yaml"
MIGRATE = "skills/audit/scripts/migrate.py"
VALIDATE = "skills/audit/scripts/validate.py"


def extract(repository, revision, into):
    archive = into.with_suffix(".tar")
    fixture.git(repository, "archive", "--format=tar", f"--output={archive}", revision)
    into.mkdir()
    with tarfile.open(archive) as stream:
        stream.extractall(into, filter="data")


class AdoptionCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="framework-adoption-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.area = Path(cls.temp.name)
        cls.old = cls.area / "old-package"
        extract(ROOT, BASE, cls.old)
        cls.old_version = yaml.safe_load((cls.old / REGISTRY).read_text())["version"]
        cls.current_version = yaml.safe_load((ROOT / REGISTRY).read_text())["version"]
        cls.repository = cls.area / "new-repository"
        cls.repository.mkdir()
        # Complete tracked + nonignored development source, not an entry-point subset.
        files = fixture.git(ROOT, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
        for relative in sorted(set(files.split("\0")) - {""}):
            source = ROOT / relative
            if source.is_file():
                target = cls.repository / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
        fixture.git(cls.repository, "init", "--initial-branch=main", "--template=")
        fixture.git(cls.repository, "add", "--all")
        fixture.git(cls.repository, "commit", "-m", "Complete proposed package")
        cls.new = cls.area / "new-package"
        extract(cls.repository, "HEAD", cls.new)
        fixture.build(cls.area / "fixtures")
        cls.foreign = cls.area / "foreign"
        (cls.foreign / "framework_data_ai").mkdir(parents=True)
        (cls.foreign / "framework_data_ai/__init__.py").write_text("raise RuntimeError('foreign core imported')\n")
        cls.overlays = yaml.safe_load((ROOT / "tests/fixtures/memory/phase2-metadata.yaml").read_text())

    def setUp(self):
        self.case = tempfile.TemporaryDirectory(prefix="framework-adoption-case-")
        self.addCleanup(self.case.cleanup)
        self.root = Path(self.case.name) / "project"
        shutil.copytree(self.area / "fixtures/document-only", self.root)
        self.declare(self.old_version)

    def declare(self, version, commit=None):
        cfg = self.root / "framework.yaml"
        data = yaml.safe_load(cfg.read_text())
        data["framework_version"] = version
        if commit:
            data["framework_commit"] = commit
        else:
            data.pop("framework_commit", None)
        cfg.write_text(yaml.safe_dump(data, sort_keys=False))

    def run_cli(self, entry, *args):
        run = subprocess.run([sys.executable, "-B", str(entry), *map(str, args)],
                             cwd=self.foreign, env=dict(os.environ, PYTHONPATH=str(self.foreign)),
                             capture_output=True, text=True, timeout=90)
        self.assertIn(run.returncode, (0, 1, 2), run.stdout + run.stderr)
        return run, json.loads(run.stdout)

    def migrate(self, *args, target=None):
        return self.run_cli(self.new / MIGRATE, "--root", self.root, "--framework", target or self.new,
                            "--from-framework", self.old, "--json", *args)

    def memory(self, command, *args):
        return self.run_cli(self.new / "memory.py", command, "--root", self.root, *args)

    def test_complete_previous_and_new_packages_compare_without_git_or_import_leakage(self):
        before = content_hashes(self.root)
        old_package, new_package = content_hashes(self.old), content_hashes(self.new)
        run, result = self.migrate()
        self.assertFalse(result["problems"], result)
        self.assertFalse(result["new"], result)
        self.assertEqual(result["previous_source"]["kind"], "explicit-export")
        self.assertFalse(result["previous_source"]["commit_verified"])
        self.assertNotIn("adopted", result)
        self.assertEqual(before, content_hashes(self.root))
        self.assertEqual(old_package, content_hashes(self.old))
        # The invoking interpreter may create no bytecode either: all entry points isolate.
        self.assertEqual(new_package, content_hashes(self.new))
        self.assertFalse((self.root / "_meta/memory").exists())

    def test_all_eight_legacy_scenarios_keep_passing_without_new_fields(self):
        for name in fixture.SCENARIOS:
            with self.subTest(scenario=name):
                project = Path(self.case.name) / name
                shutil.copytree(self.area / "fixtures" / name, project)
                settings = yaml.safe_load((project / "framework.yaml").read_text())
                settings["framework_version"] = self.old_version
                (project / "framework.yaml").write_text(yaml.safe_dump(settings))
                before = content_hashes(project)
                for framework in (self.old, self.new):
                    _, report = self.run_cli(framework / VALIDATE, "--root", project, "--json",
                                             "--stale-days", "36500")
                    self.assertEqual(report["errors"], 0, report)
                self.assertEqual(before, content_hashes(project))

    def test_exact_project_pin_is_the_baseline_not_the_last_registry_revision(self):
        self.declare(self.old_version, BASE)
        _, result = self.run_cli(self.new / MIGRATE, "--root", self.root, "--framework", ROOT,
                                 "--from-commit", BASE, "--json")
        self.assertFalse(result["problems"], result)
        self.assertEqual(result["previous_source"]["commit"], BASE)

    def test_explicit_export_with_wrong_version_is_not_a_clean_migration(self):
        wrong = Path(self.case.name) / "wrong"
        shutil.copytree(self.old, wrong)
        registry = (wrong / REGISTRY).read_text().replace(f'version: "{self.old_version}"', 'version: "0.0.1"', 1)
        (wrong / REGISTRY).write_text(registry)
        _, result = self.run_cli(self.new / MIGRATE, "--root", self.root, "--framework", self.new,
                                 "--from-framework", wrong, "--json")
        self.assertTrue(result["problems"])

    def test_partial_previous_package_is_rejected(self):
        partial = Path(self.case.name) / "partial"
        (partial / "schemas").mkdir(parents=True)
        shutil.copyfile(self.old / REGISTRY, partial / REGISTRY)
        _, result = self.run_cli(self.new / MIGRATE, "--root", self.root, "--framework", self.new,
                                 "--from-framework", partial, "--json")
        self.assertTrue(result["problems"])

    def test_missing_pin_is_not_replaced_by_version_history(self):
        _, result = self.run_cli(self.new / MIGRATE, "--root", self.root, "--framework", ROOT,
                                 "--from-commit", "f" * 40, "--json")
        self.assertTrue(result["problems"])
        self.assertNotIn("previous_source", result)

    def test_adoption_from_clean_git_moves_pin_only_and_does_not_enable_memory(self):
        self.declare(self.old_version, BASE)
        before = content_hashes(self.root)
        run, result = self.migrate("--adopt", target=self.repository)
        self.assertEqual(run.returncode, 0, result)
        self.assertEqual(result["adopted"], self.current_version)
        after = content_hashes(self.root)
        self.assertEqual({p for p in before if before[p] != after[p]}, {"framework.yaml"})
        self.assertEqual(set(before), set(after))
        self.assertEqual(yaml.safe_load((self.root / "framework.yaml").read_text())["framework_commit"],
                         fixture.git(self.repository, "rev-parse", "HEAD"))

    def test_pinned_adoption_from_gitless_package_is_refused_without_writing(self):
        self.declare(self.old_version, BASE)
        before = content_hashes(self.root)
        run, result = self.migrate("--adopt")
        self.assertNotEqual(run.returncode, 0, result)
        self.assertNotIn("adopted", result)
        self.assertEqual(before, content_hashes(self.root))

    def test_dirty_target_cannot_be_adopted(self):
        dirty = Path(self.case.name) / "dirty"
        shutil.copytree(self.repository, dirty)
        (dirty / "uncommitted.py").write_text("# pending\n")
        before = content_hashes(self.root)
        _, result = self.migrate("--adopt", target=dirty)
        self.assertTrue(result["problems"])
        self.assertNotIn("adopted", result)
        self.assertEqual(before, content_hashes(self.root))

    def test_gaps_are_reproducible_selected_and_forward_only(self):
        before = content_hashes(self.root)
        first, report = self.memory("gaps")
        second, _ = self.memory("gaps")
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(report["schema"], "framework-memory/adoption-report/v1")
        self.assertFalse(report["written"])
        self.assertEqual(report["code_observation"], "not_requested")
        self.assertTrue(report["gaps"])
        immutable = [g for g in report["gaps"] if g["lifecycle"] == "immutable"]
        self.assertTrue(immutable)
        self.assertTrue(all(g["handling"] == "new-successor-only" for g in immutable))
        self.assertTrue(all(g["source"]["revision"].startswith("sha256:") for g in report["gaps"]))
        self.assertEqual(before, content_hashes(self.root))
        config(self.root, classifications=["public"], include_unclassified=False)
        _, filtered = self.memory("gaps")
        self.assertGreater(filtered["filtered_sources"], 0)
        self.assertFalse(filtered["gaps"])

    def test_design_without_roots_is_a_question_not_a_missing_implementation(self):
        for path, fields in self.overlays["document-only"].items():
            amend(self.root / path, **fields)
        _, report = self.memory("gaps")
        roots = [g for g in report["gaps"] if g["code"] == "code-roots-not-declared"]
        self.assertEqual(len(roots), 1)
        self.assertIn("design-only may be intentional", roots[0]["detail"])
        self.assertEqual(roots[0]["handling"], "new-successor-only")

    def test_missing_provider_and_literal_search_need_no_semantic_service(self):
        run, report = self.memory("query", "--product", "alpha", "--search-engine", "literal")
        self.assertEqual(run.returncode, 0, report)
        self.assertTrue(report["documents"])
        self.declare(self.current_version)
        _, context = self.memory("context", "--goal", "Explain the design", "--skill", "audit")
        self.assertTrue(context["required_sources"])
        self.assertIn("references/adoption.md", {s["path"] for s in context["required_sources"]})
        self.assertEqual(context["understanding"], "not-evaluated")
        self.assertFalse((self.root / "_meta/memory").exists())

    def test_declared_project_pin_is_used_without_explicit_baseline_flags(self):
        self.declare(self.old_version, BASE)
        _, result = self.run_cli(self.new / MIGRATE, "--root", self.root, "--framework", ROOT, "--json")
        self.assertFalse(result["problems"], result)
        self.assertEqual(result["previous_source"]["kind"], "project-pin")
        self.assertEqual(result["previous_source"]["commit"], BASE)

    def test_same_version_adoption_failure_is_not_exit_zero(self):
        self.declare(self.current_version, BASE)
        run, result = self.run_cli(self.new / MIGRATE, "--root", self.root, "--framework", self.new,
                                   "--adopt", "--json")
        self.assertNotEqual(run.returncode, 0, result)
        self.assertNotIn("adopted", result)

    def test_changed_dependency_version_changes_snapshot_identity(self):
        before = documentary.snapshots.capture(self.root)
        original = documentary.snapshots.metadata.version
        with patch.object(documentary.snapshots.metadata, "version",
                          side_effect=lambda name: "0.0.0-test" if name == "PyYAML" else original(name)):
            after = documentary.snapshots.capture(self.root)
        self.assertNotEqual(before.id, after.id)
        self.assertNotEqual(before.inputs["generator"]["runtime:PyYAML"],
                            after.inputs["generator"]["runtime:PyYAML"])

    def test_absent_optional_dependency_does_not_become_a_new_requirement(self):
        with patch.object(documentary.snapshots.metadata, "version",
                          side_effect=documentary.snapshots.metadata.PackageNotFoundError):
            self.assertEqual(documentary.snapshots.optional_dependency_version("typing-extensions"),
                             "not-installed")

    def test_tool_rollback_preserves_historical_documents_and_ignores_generated_memory(self):
        before = content_hashes(self.root)
        _, old_before = self.run_cli(self.old / VALIDATE, "--root", self.root, "--json")
        self.memory("build")
        _, old_after = self.run_cli(self.old / VALIDATE, "--root", self.root, "--json")
        self.assertEqual(old_before["findings"], old_after["findings"])
        after = content_hashes(self.root)
        self.assertEqual(before, {p: after[p] for p in before})
        self.assertTrue(set(after) - set(before))
        self.assertTrue(all(p.startswith("_meta/memory/") for p in set(after) - set(before)))

    def test_complete_package_contains_all_generated_contracts_and_runtime_inventory(self):
        for script in ("schemas/generate.py", "schemas/generate_memory.py", "third_party/inventory.py"):
            run = subprocess.run([sys.executable, "-B", str(self.new / script), "--check"],
                                 cwd=self.foreign, capture_output=True, text=True, timeout=60)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        inventory = json.loads((self.new / "third_party/inventory.json").read_text())
        self.assertEqual(inventory["incorporated_code"], [])
        self.assertTrue(inventory["python_runtime"]["dependencies"])


if __name__ == "__main__":
    unittest.main()
