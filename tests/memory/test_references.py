"""Phase-one scope, parsing and checkout/export compatibility regressions."""
from __future__ import annotations

from dataclasses import replace
import importlib.util
import inspect
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

import yaml

from test_phase0 import ROOT, VALIDATE, fixture, findings, metadata, validate


def load_validator(root: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, root / "skills/audit/scripts/validate.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


v = load_validator(ROOT, "phase_one_validator")
REGISTRY = yaml.safe_load(v.REGISTRY.read_text())


def read(root: Path):
    report = v.Report({})
    arts = v.discover(root, v.load_scan(REGISTRY, v.load_project(root)), REGISTRY, report)
    if report.findings:
        raise AssertionError(report.findings)
    return arts


def amend(path: Path, **updates):
    meta, body, error = v.parse_front_matter(path.read_text())
    if error:
        raise AssertionError(error)
    meta.update(updates)
    path.write_text("---\n" + yaml.safe_dump(meta, sort_keys=False) + "---" + body,
                    encoding="utf-8", newline="\n")


class References(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="framework-references-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        fixture.build(cls.root / "inputs")

    def scenario(self, name):
        root = self.root / "inputs" / name
        arts = read(root)
        return root, {a.rel.replace("\\", "/"): a for a in arts}, v.ReferenceIndex(arts, REGISTRY)

    def copy_scenario(self, name):
        root = self.root / self._testMethodName
        shutil.copytree(self.root / "inputs" / name, root)
        return root

    def test_local_and_qualified_candidate_keep_the_same_identity(self):
        _, arts, index = self.scenario("qualified-impact")
        local = index.normalize_candidate("SIG-001", arts[fixture.ICG])
        qualified = index.normalize_candidate("alpha:SIG-001", arts[fixture.CHG])
        self.assertEqual(local.identity, qualified.identity)
        self.assertEqual(local.identity.scope, "product:alpha")
        self.assertEqual(index.resolve("SIG-001", arts[fixture.ICG], allow_local=True).target.identity,
                         index.resolve("alpha:SIG-001", arts[fixture.CHG]).target.identity)

    def test_equal_numbers_in_two_products_are_distinct(self):
        _, arts, index = self.scenario("triage-collision")
        left = index.normalize_candidate("SIG-001", arts["products/alpha/LOG.md"])
        right = index.normalize_candidate("SIG-001", arts["products/beta/LOG.md"])
        self.assertNotEqual(left.identity, right.identity)

    def test_qualified_reference_does_not_cross_its_declared_binding(self):
        _, arts, index = self.scenario("triage-collision")
        for binding, status in ((["alpha"], "out-of-scope"), (["none"], "out-of-scope"),
                                (["all"], "resolved"), ([], "resolved")):
            source = replace(arts[fixture.ICG], meta={**arts[fixture.ICG].meta, "products": binding})
            with self.subTest(binding=binding):
                self.assertEqual(index.resolve("beta:SIG-001", source).status, status)

    def test_binding_metadata_is_not_product_ownership(self):
        _, arts, index = self.scenario("triage-collision")
        source = replace(arts[fixture.ICG], meta={**arts[fixture.ICG].meta, "products": ["beta"]})
        self.assertEqual(index.normalize_candidate("SIG-001", source).identity.scope, "product:alpha")

    def test_missing_unknown_invalid_and_unqualified_are_explicit(self):
        _, arts, index = self.scenario("qualified-impact")
        source = arts[fixture.CHG]
        for ref, status in (("alpha:SIG-999", "missing"), ("retired:SIG-001", "unknown-product"),
                            ("alpha:DEC-001", "invalid"), ([], "invalid"), ("SIG-001", "invalid")):
            with self.subTest(ref=ref):
                result = index.resolve(ref, source)
                self.assertEqual(result.status, status)
                self.assertIsNone(result.target)

    def test_root_binding_does_not_make_a_root_decision_product_owned(self):
        _, arts, index = self.scenario("multi-repo")
        self.assertEqual(index.owner(arts["decisions/DEC-001-shared-rule.md"]), "repository")
        self.assertEqual(index.owner(arts["PLATFORM.md"]), "platform")
        self.assertNotIn("platform", index.products)

    def test_physical_checkout_location_does_not_change_identity(self):
        _, arts, index = self.scenario("qualified-impact")
        moved = [replace(a, path=Path("/another-checkout") / a.rel) for a in arts.values()]
        other = v.ReferenceIndex(moved, REGISTRY)
        moved_change = next(a for a in moved if a.rel == fixture.CHG)
        self.assertEqual(index.identity(arts[fixture.CHG]), other.identity(moved_change))

    def test_different_document_repositories_have_different_identities(self):
        _, arts, _ = self.scenario("qualified-impact")
        left = v.ReferenceIndex(list(arts.values()), REGISTRY, document_repository="docs-a")
        right = v.ReferenceIndex(list(arts.values()), REGISTRY, document_repository="docs-b")
        self.assertNotEqual(left.identity(arts[fixture.CHG]), right.identity(arts[fixture.CHG]))

    def test_duplicate_artifact_ids_are_ambiguous_independent_of_scan_order(self):
        _, arts, _ = self.scenario("qualified-impact")
        duplicate = replace(arts[fixture.ICG], rel="products/alpha/cycles/ICG-001-copy.md")
        for ordered in (list(arts.values()) + [duplicate], [duplicate] + list(reversed(arts.values()))):
            result = v.ReferenceIndex(ordered, REGISTRY).artifact("ICG-001", kind="impact-classification")
            self.assertEqual(result.status, "ambiguous")
            self.assertEqual(len(result.matches), 2)
            self.assertIsNone(result.target)

    def test_duplicate_manifest_ownership_is_not_last_writer_wins(self):
        _, arts, _ = self.scenario("qualified-impact")
        manifest = arts["products/alpha/product.yaml"]
        duplicate = replace(manifest, meta={**manifest.meta, "products": ["beta"]})
        for order in (list(arts.values()) + [duplicate], [duplicate] + list(arts.values())):
            index = v.ReferenceIndex(order, REGISTRY)
            self.assertEqual(index.normalize_candidate("SIG-001", arts[fixture.ICG]).status, "ambiguous")

    def test_roadmap_candidate_is_local_even_without_written_qualifier(self):
        _, arts, _ = self.scenario("local-impact-control")
        roadmap = arts["products/alpha/RMP.md"]
        duplicate = replace(roadmap, rel="products/beta/RMP.md", path=Path("products/beta/RMP.md"))
        index = v.ReferenceIndex([*arts.values(), duplicate], REGISTRY)
        result = index.resolve("INC-001", arts[fixture.CHG])
        self.assertEqual(result.target.identity.scope, "product:alpha")
        without_local = v.ReferenceIndex([a for a in arts.values() if a is not roadmap] + [duplicate], REGISTRY)
        self.assertEqual(without_local.resolve("INC-001", arts[fixture.CHG]).status, "missing")

    def test_repository_alias_cannot_borrow_another_products_checkout(self):
        _, arts, index = self.scenario("multi-repo")
        alpha = arts["products/alpha/ARC.md"]
        beta = arts["products/beta/ARC.md"]
        self.assertEqual(index.repository("product.api", alpha).target.identity.scope, "product:alpha")
        self.assertEqual(index.repository("product.worker", alpha).status, "missing")
        self.assertEqual(index.repository("product.worker", beta).target.identity.scope, "product:beta")
        self.assertEqual(index.repository("platform.rules", alpha).target.identity,
                         index.repository("platform.rules", beta).target.identity)
        self.assertEqual(index.repository("product.api", arts["PLATFORM.md"]).status, "ambiguous")

    def test_same_repository_nickname_in_distinct_products_is_not_one_repository(self):
        _, arts, _ = self.scenario("multi-repo")
        changed = []
        for artifact in arts.values():
            if artifact.type == "product-manifest":
                entry = next(iter(artifact.meta["code"].values()))
                artifact = replace(artifact, meta={**artifact.meta, "code": {"backend": entry}})
            changed.append(artifact)
        index = v.ReferenceIndex(changed, REGISTRY)
        self.assertNotEqual(index.repository("product.backend", arts["products/alpha/ARC.md"]).target.identity,
                            index.repository("product.backend", arts["products/beta/ARC.md"]).target.identity)

    def test_canonical_remote_aliases_keep_legacy_equivalence(self):
        values = [v.canonical_repo(url) for url in (
            "git@example.invalid:org/repo.git", "ssh://git@example.invalid/org/repo.git",
            "https://example.invalid/org/repo.git")]
        self.assertEqual(len(set(values)), 1)

    def test_repository_reference_syntax_comes_from_the_existing_registry(self):
        _, arts, index = self.scenario("multi-repo")
        source = arts["products/alpha/ARC.md"]
        for ref in ("backend", "customer.backend", "product.", "product../escape", None):
            with self.subTest(ref=ref):
                self.assertEqual(index.repository(ref, source).status, "invalid")

    def test_multiple_inline_declarations_do_not_choose_the_first_log(self):
        _, arts, _ = self.scenario("qualified-impact")
        duplicate = replace(arts["products/alpha/LOG.md"], rel="products/alpha/second-log.md")
        index = v.ReferenceIndex([*arts.values(), duplicate], REGISTRY)
        result = index.resolve("alpha:SIG-001", arts[fixture.CHG])
        self.assertEqual(result.status, "ambiguous")
        self.assertIsNone(result.target)

    def test_cross_product_chg_is_not_classified_by_the_other_signal(self):
        root = self.copy_scenario("qualified-impact")
        shutil.copytree(self.root / "inputs/triage-collision/products/beta", root / "products/beta")
        amend(root / fixture.CHG, products=["alpha", "beta"], derives_from=["beta:SIG-001"])
        report = validate(root, pr=True)
        self.assertEqual(report["errors"], 0)
        self.assertEqual(findings(report, "CHG003"), {fixture.CHG})
        self.assertFalse(findings(report, "CHG002"))
        self.assertFalse(findings(report, "PR004"))

    def test_duplicate_classification_cannot_authorize_a_join(self):
        root = self.copy_scenario("qualified-impact")
        shutil.copyfile(root / fixture.ICG, root / "products/alpha/cycles/ICG-001-copy.md")
        report = validate(root)
        self.assertTrue(findings(report, "ID001"))
        self.assertEqual(findings(report, "CHG003"), {fixture.CHG})

    def test_duplicate_change_contract_cannot_authorize_a_pr(self):
        root = self.copy_scenario("qualified-impact")
        duplicate = root / "products/alpha/changes/CHG-001-copy.md"
        shutil.copyfile(root / fixture.CHG, duplicate)
        amend(duplicate, status="draft")
        report = validate(root, pr=True)
        self.assertEqual(findings(report, "PR002"), {"pull request"})
        self.assertTrue(findings(report, "ID001"))

    def test_qualified_ai_impact_also_keeps_its_evaluation_obligation(self):
        root = self.copy_scenario("qualified-impact")
        amend(root / fixture.ICG, impacts={"SIG-001": ["architecture", "ai"]})
        amend(root / fixture.CHG, status="verified", verified_by=None)
        report = validate(root)
        self.assertEqual(report["errors"], 0)
        self.assertEqual(findings(report, "CHG001"), {fixture.CHG})
        self.assertEqual(findings(report, "CHG002"), {fixture.CHG})

    def test_triage_status_policy_is_unchanged(self):
        _, arts, _ = self.scenario("triage-complete")
        for status in ("proposed", "accepted", "superseded"):
            with self.subTest(status=status):
                modified = [replace(a, meta={**a.meta, "status": status})
                            if a.type == "impact-classification" else a for a in arts.values()]
                report = v.Report({})
                v.check_triage(modified, report)
                self.assertFalse(report.findings)


class ArtifactReading(unittest.TestCase):
    def test_legacy_imports_are_aliases_not_second_implementations(self):
        for name in ("Artifact", "as_list", "as_map", "jsonify", "is_bare_yaml",
                     "parse_front_matter", "discover", "skipped_dir", "SECTION_MARK"):
            self.assertIs(getattr(v, name), getattr(v._artifacts, name))
        self.assertIs(v.product_dirs, v._references.product_dirs)

    def test_parser_shapes_and_failures_remain_explicit(self):
        for source in ("plain text", "---\na: 1", "---\n[1, 2]\n---\n", "---\na: [\n---\n"):
            with self.subTest(source=source):
                self.assertIsNotNone(v.parse_front_matter(source)[2])
        self.assertEqual(v.parse_front_matter("# comment\nschema: x\na: 1\n"),
                         ({"schema": "x", "a": 1}, "", None))

    def test_sections_have_exact_source_lines_and_keep_nested_content(self):
        source = ("---\nschema: test\n---\n\n# Title\n"
                  "<!-- section: current -->\n## Current\nbody\n### Detail\nmore\n"
                  "<!-- section: target -->\n## Target\nfuture\n")
        _, body, error = v.parse_front_matter(source)
        self.assertIsNone(error)
        sections = v.locate_sections(body, first_line=v.body_first_line(source, body))
        current = next(section for section in sections if section.marker == "current")
        self.assertEqual((current.start_line, current.heading_line, current.end_line), (6, 7, 10))
        self.assertEqual(source.splitlines()[current.start_line - 1:current.end_line],
                         ["<!-- section: current -->", "## Current", "body", "### Detail", "more"])

    def test_fenced_examples_are_not_sections_and_duplicates_are_not_collapsed(self):
        body = ("## Decision\na\n```md\n<!-- section: false -->\n## Fake\n```\n"
                "## Decision\nb\n")
        spans = v.locate_sections(body)
        self.assertEqual([span.title for span in spans], ["Decision", "Decision"])
        self.assertNotEqual(spans[0].start_line, spans[1].start_line)

    def test_orphan_marker_does_not_label_a_later_heading(self):
        spans = v.locate_sections("<!-- section: current -->\nprose\n## Later\n")
        self.assertIsNone(spans[0].marker)
        with self.assertRaises(ValueError):
            v.locate_sections("## A", first_line=0)


class ExportCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="framework-export-core-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        fixture.build(cls.root / "inputs")
        repository = cls.root / "repository"
        repository.mkdir()
        # A real Git export of the new source, including uncommitted development files.
        # This fixture does not depend on the calling repository's current Git index.
        for relative in ("schemas", "src/framework_data_ai"):
            shutil.copytree(ROOT / relative, repository / relative,
                            ignore=shutil.ignore_patterns("__pycache__"))
        for relative in ("skills/audit/scripts/validate.py", "skills/audit/scripts/migrate.py",
                          "skills/audit/checks.yaml", "memory.py", "providers.lock.json"):
            target = repository / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        fixture.git(repository, "init", "--initial-branch=main", "--template=")
        fixture.git(repository, "add", "--all")
        fixture.git(repository, "commit", "-m", "Export compatibility fixture")
        archive = cls.root / "export.tar"
        fixture.git(repository, "archive", "--format=tar", f"--output={archive}", "HEAD")
        cls.export = cls.root / "export"
        cls.export.mkdir()
        with tarfile.open(archive) as stream:
            stream.extractall(cls.export, filter="data")
        cls.foreign = cls.root / "foreign-path"
        (cls.foreign / "framework_data_ai").mkdir(parents=True)
        (cls.foreign / "framework_data_ai/__init__.py").write_text(
            "raise RuntimeError('wrong checkout imported')\n")

    def test_exported_cli_uses_its_own_package_from_an_unrelated_working_directory(self):
        root = self.root / "inputs/qualified-impact"
        run = subprocess.run([sys.executable, "-B", str(self.export / "skills/audit/scripts/validate.py"),
                              "--root", str(root), "--json", "--stale-days", "36500"],
                             cwd=self.foreign, env=dict(os.environ, PYTHONPATH=str(self.foreign)),
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["findings"], validate(root)["findings"])

    def test_importing_live_and_exported_validators_does_not_mix_packages(self):
        exported = load_validator(self.export, "exported_phase_one_validator")
        self.assertIsNot(exported.Artifact, v.Artifact)
        self.assertTrue(Path(inspect.getfile(exported.Artifact)).is_relative_to(self.export))
        self.assertTrue(Path(inspect.getfile(v.Artifact)).is_relative_to(ROOT))
        self.assertEqual(exported.canonical_repo("git@example.invalid:org/repo.git"),
                         v.canonical_repo("https://example.invalid/org/repo.git"))

    def test_exported_package_is_also_directly_importable(self):
        run = subprocess.run([sys.executable, "-B", "-c",
                              "from framework_data_ai.artifacts import parse_front_matter; "
                              "from framework_data_ai.references import ReferenceIndex; "
                              "assert parse_front_matter('schema: example')[2] is None"],
                             cwd=self.root, env=dict(os.environ, PYTHONPATH=str(self.export / "src")),
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)

    def test_migrator_noop_also_runs_against_the_export(self):
        run = subprocess.run([sys.executable, "-B", str(self.export / "skills/audit/scripts/migrate.py"),
                              "--root", str(self.root / "inputs/document-only"),
                              "--framework", str(self.export), "--json"], cwd=self.foreign,
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(json.loads(run.stdout)["up_to_date"])

    def test_exported_memory_cli_is_self_contained_and_read_only(self):
        run = subprocess.run([sys.executable, "-B", str(self.export / "memory.py"), "query",
                              "--root", str(self.root / "inputs/document-only"), "--product", "alpha"],
                             cwd=self.foreign, env=dict(os.environ, PYTHONPATH=str(self.foreign)),
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        pack = json.loads(run.stdout)
        self.assertTrue(pack["documents"])
        self.assertEqual(pack["code_observation"], "not_requested")
        self.assertFalse((self.root / "inputs/document-only/_meta/memory").exists())


if __name__ == "__main__":
    unittest.main()
