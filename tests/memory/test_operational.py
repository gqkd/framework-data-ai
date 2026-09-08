"""Phase-four deterministic retrieval/impact gates, not measured agent understanding."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

import jsonschema
import yaml

from test_phase0 import ROOT, fixture
from test_references import v
from test_documentary import amend
import test_code_provider as code_tests
from test_code_provider import API, WORKER, RULES, record, base, snapshots, graphs, models

context = importlib.import_module(v._CORE_NAME + ".memory.context")
impact = importlib.import_module(v._CORE_NAME + ".memory.impact")
rules = importlib.import_module(v._CORE_NAME + ".memory.framework_sources")
io = importlib.import_module(v._CORE_NAME + ".memory.operational_io")


class OperationalMemory(unittest.TestCase):
    setUpClass = classmethod(code_tests.CodeMemory.setUpClass.__func__)
    setUp = code_tests.CodeMemory.setUp
    project = code_tests.CodeMemory.project
    bind = code_tests.CodeMemory.bind
    build = code_tests.CodeMemory.build

    def pack(self, root, **kwargs):
        snapshot = snapshots.capture(root)
        return context.compose(snapshot, graphs.build(snapshot), goal="Inspect consequences", **kwargs)

    def bundle(self, root, **kwargs):
        built = self.build(root, **kwargs)
        built.publish()
        directory = root / "_meta/memory/code-snapshots" / built.graph["snapshot"]
        return io.load_code(directory), directory

    def compare(self, root, **kwargs):
        snapshot = snapshots.capture(root)
        return impact.compare(snapshot, graphs.build(snapshot), **kwargs)

    def adopted(self, root):
        exported = self.case / "adopted"
        (exported / "schemas").mkdir(parents=True)
        (exported / "schemas/artifact-types.yaml").write_text(yaml.safe_dump({"version": "synthetic-1"}))
        for relative in rules.BASE:
            path = exported / relative
            path.parent.mkdir(exist_ok=True, parents=True)
            path.write_text("# Synthetic adopted rule\nKeep the original mandate.\n")
        fixture.git(exported, "init", "--initial-branch=main", "--template=")
        fixture.git(exported, "add", "--all")
        fixture.git(exported, "commit", "-m", "Pinned synthetic rules")
        commit = fixture.git(exported, "rev-parse", "HEAD").strip()
        config = yaml.safe_load((root / "framework.yaml").read_text())
        config.update(framework_version="synthetic-1", framework_commit=commit)
        (root / "framework.yaml").write_text(yaml.safe_dump(config))
        return exported, commit

    def exported_rules(self):
        exported = self.case / "rules"
        for relative in (*rules.BASE, "schemas/artifact-types.yaml", "references/operational-memory.md"):
            target = exported / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        return exported

    def test_document_only_context_does_not_require_code_or_invent_architecture(self):
        root = self.project("document-only")
        pack = self.pack(root)
        paths = {r["path"] for r in pack["required_sources"]}
        self.assertIn("products/alpha/product.yaml", paths)
        self.assertIn("initiatives/synthetic-design/SD-001-processor.md", paths)
        self.assertNotIn("products/alpha/ARC.md", paths)
        self.assertEqual(pack["code"]["status"], "not-requested")
        self.assertEqual(pack["mandate"]["authorization"], "not-verified")
        self.assertFalse((root / "_meta/memory").exists())

    def test_required_sources_survive_zero_budget_and_no_reading_is_invented(self):
        root = self.project()
        small, large = self.pack(root, budget=0), self.pack(root, budget=2_000_000)
        self.assertEqual({r["id"] for r in small["required_sources"]}, {r["id"] for r in large["required_sources"]})
        self.assertEqual(small["content"], [])
        self.assertFalse(small["delivery_complete"])
        self.assertEqual(small["reading_status"], "not-attested")
        self.assertEqual(large["understanding"], "not-evaluated")

    def test_rejected_alternative_recovers_full_rationale_and_review_condition(self):
        root = self.project()
        pack = self.pack(root, reconsider=True, budget=2_000_000)
        rows = [r for r in pack["required_sources"] if r["path"] == "decisions/DEC-001-shared-rule.md"]
        self.assertEqual({r["section"] for r in rows}, {"Decision", "Consequences", "Alternatives", "Review condition"})
        text = "\n".join(c["text"] for c in pack["content"] if c["requirement"] in {r["id"] for r in rows})
        self.assertIn("cache", text)
        self.assertIn("incompatible", text)
        normal = self.pack(root)
        self.assertFalse(any(r["section"] == "Alternatives" for r in normal["required_sources"]))

    def test_legacy_and_superseded_decisions_are_not_discarded(self):
        root = self.project()
        path = root / "decisions/DEC-001-shared-rule.md"
        meta, body, _ = v.parse_front_matter(path.read_text())
        meta.pop("applies_to", None)
        meta["status"] = "superseded"
        path.write_text("---\n" + yaml.safe_dump(meta) + "---" + body)
        pack = self.pack(root)
        self.assertTrue(any(r["reason"] == "legacy-decision-scope-fallback" for r in pack["required_sources"]))
        self.assertTrue(any(d["status"] == "superseded" for d in pack["documents"]))

    def test_missing_and_duplicate_decision_sections_remain_explicit(self):
        root = self.project()
        path = root / "decisions/DEC-001-shared-rule.md"
        path.write_text(path.read_text().replace("## Consequences", "## Unknown section") + "\n## Decision\nAmbiguous.\n")
        pack = self.pack(root)
        missing = {r["section"] for r in pack["required_sources"] if r["delivery"] == "missing"}
        self.assertEqual(missing, {"Decision", "Consequences"})
        self.assertFalse(pack["delivery_complete"])

    def test_pin_reads_historical_bytes_not_worktree_or_runtime_rules(self):
        root = self.project("document-only")
        adopted, commit = self.adopted(root)
        (adopted / "FRAMEWORK.md").write_text("# Unauthorized worktree override\n")
        pack = self.pack(root, framework_root=adopted, budget=2_000_000)
        self.assertEqual(pack["framework"]["resolution"], "pinned-commit")
        self.assertEqual(pack["framework"]["commit"], commit)
        self.assertNotIn("Unauthorized worktree override", models.canonical(pack).decode())
        self.assertNotIn("references/operational-memory.md", {r["path"] for r in pack["required_sources"]})
        self.assertNotEqual(pack["framework"]["version"], pack["runtime"]["version"])

    def test_version_mismatch_missing_commit_and_invalid_pin_never_fall_back(self):
        root = self.project("document-only")
        for config in ({"framework_version": "unavailable"},
                       {"framework_version": "3.6.3", "framework_commit": "a" * 40},
                       {"framework_version": "3.6.3", "framework_commit": "HEAD"}):
            (root / "framework.yaml").write_text(yaml.safe_dump(config))
            result = rules.capture_framework(root).result
            self.assertEqual(result["resolution"], "unavailable")
            self.assertEqual(result["sources"], [])

    def test_version_only_rules_are_explicitly_unverified_and_guarded(self):
        root = self.project("document-only")
        captured = rules.capture_framework(root)
        self.assertEqual(captured.result["resolution"], "version-only-unverified")
        with patch.object(rules, "local_bytes", return_value=b"changed"):
            with self.assertRaises(snapshots.ConcurrentChange):
                captured.assert_unchanged()

    def test_all_seven_skills_require_their_adopted_rules_and_shared_guide(self):
        root = self.project("document-only")
        for skill in rules.SKILLS:
            with self.subTest(skill=skill):
                pack = self.pack(root, skill=skill, budget=0)
                sources = {row["path"]: row for row in pack["required_sources"] if row["kind"] == "framework"}
                for relative in (f"skills/{skill}/SKILL.md", "references/operational-memory.md"):
                    source = sources[relative]
                    self.assertEqual(source["revision"], "sha256:" + models.digest((ROOT / relative).read_bytes()))
                    self.assertEqual(source["delivery"], "deferred")
                    self.assertEqual(source["reading"], "not-attested")
                self.assertEqual(pack["mandate"]["authorization"], "not-verified")
                self.assertEqual(pack["understanding"], "not-evaluated")

    def test_shared_rule_byte_change_invalidates_context_not_document_snapshot(self):
        root = self.project("document-only")
        exported = self.exported_rules()
        first = self.pack(root, framework_root=exported)
        captured = rules.capture_framework(root, root=exported)
        path = exported / "references/operational-memory.md"
        path.write_text(path.read_text() + "\nSynthetic local revision.\n")
        second = self.pack(root, framework_root=exported)
        self.assertEqual(first["document_snapshot"], second["document_snapshot"])
        self.assertNotEqual(first["id"], second["id"])
        revisions = [{row["revision"] for row in pack["required_sources"]
                      if row["path"] == "references/operational-memory.md"} for pack in (first, second)]
        self.assertNotEqual(*revisions)
        with self.assertRaises(snapshots.ConcurrentChange):
            captured.assert_unchanged()

    def test_missing_referenced_shared_guide_is_an_explicit_gap(self):
        root = self.project("document-only")
        exported = self.exported_rules()
        (exported / "references/operational-memory.md").unlink()
        pack = self.pack(root, framework_root=exported)
        self.assertIn(dict(path="references/operational-memory.md",
                           reason="referenced-adopted-source-unavailable"), pack["gaps"])
        self.assertNotIn("references/operational-memory.md", {row["path"] for row in pack["required_sources"]})
        self.assertEqual(pack["framework"]["resolution"], "version-only-unverified")

    def test_confidential_source_and_private_binding_never_enter_context(self):
        root = self.project()
        path = root / "decisions/DEC-001-shared-rule.md"
        amend(path, classification="confidential")
        path.write_text(path.read_text() + "\nRESTRICTED_SENTINEL\n")
        self.bind(root, {API: "/private/SENTINEL"})
        pack = self.pack(root, budget=2_000_000)
        encoded = models.canonical(pack).decode()
        self.assertNotIn("RESTRICTED_SENTINEL", encoded)
        self.assertNotIn("/private/SENTINEL", encoded)
        self.assertNotIn("decisions/" + path.name, {r["path"] for r in pack["required_sources"]})

    def test_qualified_candidate_join_retains_architecture_prerequisite(self):
        root = self.project("qualified-impact")
        pack = self.pack(root, change="CHG-001", mode="implement")
        self.assertEqual(pack["mandate"]["declared_status"], "approved")
        self.assertIn("architecture", pack["mandate"]["impact_categories"])
        self.assertIn("architecture-impact-without-cited-accepted-decision", pack["mandate"]["prerequisites"])
        self.assertEqual(pack["mandate"]["authorization"], "not-verified")
        self.assertTrue(any(r["path"].endswith("ICG-001-intake.md") for r in pack["required_sources"]))

    def test_analysis_does_not_require_approval_and_signal_does_not_grant_it(self):
        root = self.project("document-only")
        for mode in ("analysis", "proposal", "implement"):
            pack = self.pack(root, mode=mode)
            self.assertIn("approved-change-not-selected", pack["mandate"]["prerequisites"])
            self.assertEqual(pack["mandate"]["authorization"], "not-verified")
        self.assertFalse((root / "products/alpha/changes").exists())

    def test_documentary_graph_paths_have_evidence_and_never_rank_out_decisions(self):
        root = self.project()
        snapshot = snapshots.capture(root)
        graph = graphs.build(snapshot)
        selector = next(n["id"] for n in graph["nodes"] if n["kind"] == "component")
        pack = self.pack(root, selector=selector, hops=2)
        edges = {e["id"] for e in pack["graph"]["edges"]}
        self.assertTrue(any(r["graph_path"] for r in pack["required_sources"]))
        self.assertTrue(all(s["edge"] in edges for r in pack["required_sources"] for s in r["graph_path"]))

    def test_reading_report_rejects_stale_partial_duplicate_and_forged_claims(self):
        root = self.project("document-only")
        pack = self.pack(root)
        r = pack["required_sources"][0]
        claim = {"requirement": r["id"], **{k: r[k] for k in ("revision", "start_line", "end_line")}}
        valid = dict(context=pack["id"], readings=[claim])
        result = context.reading_report(pack, valid)
        self.assertEqual(result["declared_read"], [r["id"]])
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["last_review"], "not-modified")
        for bad in (dict(valid, context="0" * 64), dict(valid, readings=[claim, claim]),
                    dict(valid, readings=[dict(claim, revision="sha256:" + "0" * 64)]),
                    dict(valid, readings=[dict(claim, end_line=r["end_line"] + 1)])):
            with self.assertRaises(context.MemoryInputError):
                context.reading_report(pack, bad)
        pack["understanding"] = "understood"
        with self.assertRaises(jsonschema.ValidationError):
            context.reading_report(pack, valid)

    def test_full_reading_claims_are_still_not_comprehension_or_authority(self):
        root = self.project("document-only")
        adopted, _ = self.adopted(root)
        pack = self.pack(root, framework_root=adopted, budget=0)
        claims = dict(context=pack["id"], readings=[dict(requirement=r["id"], **{k: r[k] for k in
                           ("revision", "start_line", "end_line")}) for r in pack["required_sources"]])
        report = context.reading_report(pack, claims)
        self.assertEqual(report["status"], "declared-complete")
        self.assertEqual(report["understanding"], "not-evaluated")
        self.assertFalse(pack["delivery_complete"])

    def test_inference_remains_inferred_and_requires_in_scope_provenance(self):
        root = self.project()
        original = self.pack(root)
        source = next(r for r in original["required_sources"] if r["kind"] == "document")
        h = dict(claim="Potential duplicate work; not measured", provenance=dict(source_kind="document",
                 assertion_method="inferred", confidence=0.4, rationale="A relationship to investigate, not a decided constraint",
                 sources=[dict(source=source["source"], start_line=1, end_line=1)]))
        pack = self.pack(root, hypotheses=[h])
        self.assertEqual(pack["hypotheses"], [h])
        h["provenance"]["assertion_method"] = "declared"
        with self.assertRaises(jsonschema.ValidationError):
            self.pack(root, hypotheses=[h])

    def test_code_bundle_is_separate_and_code_reading_stays_outstanding(self):
        root = self.project()
        bundle, _ = self.bundle(root)
        pack = self.pack(root, code=bundle, budget=2_000_000)
        self.assertEqual(pack["code"]["freshness"], "not-rechecked")
        self.assertTrue(all(r["delivery"] == "deferred" for r in pack["required_sources"] if r["kind"] == "code"))
        self.assertFalse(pack["delivery_complete"])
        self.assertNotIn(str(root), models.canonical(pack).decode())

    def test_mismatched_document_snapshot_is_rejected(self):
        root = self.project()
        bundle, _ = self.bundle(root)
        path = root / "products/alpha/PBR.md"
        path.write_text(path.read_text() + "\nChanged context.\n")
        with self.assertRaises(context.MemoryInputError):
            self.pack(root, code=bundle)
        with self.assertRaises(context.MemoryInputError):
            self.compare(root, before=bundle, after=bundle)

    def test_bundle_corruption_duplicate_json_and_symlink_are_rejected(self):
        root = self.project()
        _, directory = self.bundle(root)
        graph_path = directory / "code-graph.json"
        graph = json.loads(graph_path.read_text())
        graph["nodes"][0]["name"] = "mutated"
        graph_path.write_text(json.dumps(graph))
        with self.assertRaises(context.MemoryInputError):
            io.load_code(directory)
        test = self.case / "duplicate.json"
        test.write_text('{"key":1,"key":2}')
        with self.assertRaises(context.MemoryInputError):
            io.read_json(test)
        link = self.case / "link.json"
        link.symlink_to(test)
        with self.assertRaises(context.MemoryInputError):
            io.read_json(link)

    def test_missing_code_does_not_become_zero_impact(self):
        root = self.project("missing-code")
        bundle, _ = self.bundle(root)
        result = self.compare(root, before=bundle, after=bundle)
        self.assertEqual(result["coverage"], "partial")
        self.assertTrue(any(r.get("repository") == WORKER for r in result["uncertainties"]))
        self.assertNotEqual(result["conclusion"], "no-impact")

    def test_changed_bytes_and_all_overlapping_views_are_retained(self):
        root = self.project()
        arc = root / "products/alpha/ARC.md"
        components = deepcopy(self.overlays["multi-repo"]["products/alpha/ARC.md"]["components"])
        components["component:product:alpha:overlap"] = {"current": {"code_roots": [{"repository": "product.api", "path": "."}]},
                                                       "target": {"code_roots": [{"repository": "product.api", "path": "."}]}}
        amend(arc, components=components)
        before, _ = self.bundle(root)
        path = root / "code/alpha-api/service.py"
        path.write_text(path.read_text() + "\n# changed bytes\n")
        after, _ = self.bundle(root)
        result = self.compare(root, before=before, after=after)
        self.assertTrue(any(r["path"] == "service.py" for r in result["observed"]["changed_files"]))
        rows = result["observed"]["components"]
        self.assertEqual(len({r["component"] for r in rows if r["side"] == "after" and r["view"] == "current"}), 2)
        self.assertTrue(any(r["view"] == "target" for r in rows))

    def test_cyclic_traversal_is_bounded_directional_and_reports_stop(self):
        nodes = [dict(id=name, repository=API, file=name) for name in ("a.py", "b.py", "c.py")]
        edges = [dict(id=f"e{i}", source=a, target=b, relation="calls", resolution="resolved")
                 for i, (a, b) in enumerate((("b.py", "a.py"), ("c.py", "b.py"), ("a.py", "c.py")))]
        graph = dict(snapshot="synthetic", nodes=nodes, edges=edges)
        result = impact.traverse(graph, [(API, "a.py")], hops=1, limit=100, direction="dependents")
        self.assertTrue(result["truncated"])
        self.assertEqual({r["path"] for r in result["paths"]}, {"a.py", "b.py"})
        complete = impact.traverse(graph, [(API, "a.py")], hops=3, limit=100, direction="dependents")
        self.assertFalse(complete["truncated"])
        self.assertEqual(len(complete["paths"]), 3)
        limited = impact.traverse(graph, [(API, "a.py")], hops=3, limit=1, direction="both")
        self.assertIn("node-budget", limited["stops"])

    def test_unresolved_edge_is_not_nominally_resolved_by_impact(self):
        root = self.project()
        r = record(relations=[dict(kind="imports", target="shared_rules")])
        provider = base.FakeProvider(lambda _: base.Observation("available", [r]))
        before, _ = self.bundle(root, provider=provider, repositories=[API])
        path = root / "code/alpha-api/service.py"
        path.write_text(path.read_text() + "\n# delta\n")
        after, _ = self.bundle(root, provider=provider, repositories=[API])
        result = self.compare(root, before=before, after=after)
        self.assertTrue(any(r["reason"] == "unresolved-direct-edges" for r in result["uncertainties"]))
        self.assertFalse(any(r["repository"] == RULES for r in result["observed"]["components"]))

    def test_cli_analysis_leaves_product_bytes_unchanged(self):
        root = self.project("document-only")
        before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        run = subprocess.run([sys.executable, "-B", str(ROOT / "memory.py"), "context", "--root", str(root),
                              "--goal", "Explain only", "--skill", "cycle"], capture_output=True, text=True, timeout=60)
        self.assertIn(run.returncode, (0, 1), run.stdout + run.stderr)
        self.assertEqual(json.loads(run.stdout)["request"]["mode"], "analysis")
        self.assertEqual(before, {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()})

    def test_portable_context_has_identical_bytes_and_limits_fail_closed(self):
        one, two = self.project(destination="one"), self.project(destination="two")
        self.assertEqual(models.canonical(self.pack(one)), models.canonical(self.pack(two)))
        for args in (dict(budget=-1), dict(hops=30), dict(products=["unknown"]), dict(change="CHG-999"),
                     dict(selector="component:platform:nonexistent")):
            with self.assertRaises(context.MemoryInputError):
                self.pack(one, **args)

    def test_different_document_namespace_cannot_supply_an_impact_baseline(self):
        root = self.project()
        before, _ = self.bundle(root)
        config = root / ".framework-memory/config.yaml"
        config.write_text("document_repository: another-doc-repository\n")
        after, _ = self.bundle(root)
        with self.assertRaises(context.MemoryInputError):
            self.compare(root, before=before, after=after)

    def test_subset_observation_keeps_other_declared_repositories_unknown(self):
        root = self.project()
        observed, _ = self.bundle(root, repositories=[API])
        report = self.compare(root, before=observed, after=observed)
        missing = {r["repository"] for r in report["uncertainties"]
                   if r["reason"] == "declared-repository-not-observed-on-both-sides"}
        self.assertEqual(missing, {WORKER, RULES})
        pack = self.pack(root, code=observed)
        self.assertTrue(any(r["reason"] == "code-observation-is-incomplete" for r in pack["gaps"]))

    def test_removed_file_remains_mapped_from_before_and_unknown_after(self):
        root = self.project()
        before, _ = self.bundle(root)
        (root / "code/alpha-api/service.py").unlink()
        after, _ = self.bundle(root)
        report = self.compare(root, before=before, after=after)
        removed = next(r for r in report["observed"]["changed_files"] if r["path"] == "service.py")
        self.assertIsNotNone(removed["before"])
        self.assertIsNone(removed["after"])
        self.assertTrue(any("service.py" in r["paths"] for r in report["observed"]["components"]))
        self.assertEqual(report["coverage"], "partial")

    def test_candidate_subjects_keep_categories_at_candidate_level(self):
        root = self.project("qualified-impact")
        # Enrich only this disposable fixture with a component and optional annotations.
        fixture.Documents(root).artifact("products/alpha/ARC.md", "architecture",
                                       "# Architecture\n\n## Current\nSynthetic boundary.\n",
                                       products=["alpha"], components={"component:product:alpha:boundary":
                                                                      {"current": {"section": "Current"}}})
        icg = root / "products/alpha/cycles/ICG-001-intake.md"
        amend(icg, subjects={"SIG-001": ["component:product:alpha:boundary"]})
        report = self.compare(root, change="CHG-001")
        candidate = report["predicted"]["candidates"][0]
        self.assertEqual(candidate["candidate"]["scope"], "product:alpha")
        self.assertEqual(candidate["categories"], ["architecture"])
        self.assertEqual(len(candidate["subjects"]), 1)
        self.assertIn("candidate-only", report["predicted"]["impact_attribution"])

    def test_repository_targets_project_to_components_not_false_scope_expansion(self):
        root = self.project()
        snapshot = snapshots.capture(root)
        graph = graphs.build(snapshot)
        repo = next(n["id"] for n in graph["nodes"] if n["kind"] == "repository" and n["label"] == API)
        result = impact.component_subjects(graph, [repo])
        expected = {b["component"] for b in self.build(root).graph["bridges"] if b["repository"] == API}
        self.assertEqual(result[repo], expected)

    def test_inference_outside_source_range_is_rejected(self):
        root = self.project()
        pack = self.pack(root)
        source = next(r for r in pack["required_sources"] if r["kind"] == "document")
        h = dict(claim="unverified", provenance=dict(source_kind="document", assertion_method="inferred",
                 rationale="needs investigation", sources=[dict(source=source["source"], start_line=1, end_line=100000)]))
        with self.assertRaises(context.MemoryInputError):
            self.pack(root, hypotheses=[h])

    def test_direct_calls_propagate_to_dependent_files_with_edge_provenance(self):
        root = self.project()
        target = record("service.response", path="service.py", line=1)
        caller = record("tests.test_service.test", path="tests/test_service.py", line=1,
                        relations=[dict(kind="calls", target=target["name"], target_id=target["id"])])
        provider = base.FakeProvider(lambda _: base.Observation("available", [target, caller]))
        before, _ = self.bundle(root, provider=provider, repositories=[API])
        path = root / "code/alpha-api/service.py"
        path.write_text(path.read_text() + "\n# change\n")
        after, _ = self.bundle(root, provider=provider, repositories=[API])
        report = self.compare(root, before=before, after=after)
        walked = next(t for t in report["observed"]["traversals"] if t["side"] == "after")
        path = next(p for p in walked["paths"] if p["path"] == "tests/test_service.py")
        self.assertEqual(path["steps"][0]["direction"], "reverse")
        self.assertIn(path["steps"][0]["edge"], {e["id"] for e in after["graph"]["edges"]})

    def test_cli_impact_and_readings_remain_read_only_and_report_incompleteness(self):
        root = self.project("document-only")
        pack = self.pack(root)
        pack_path, claims_path = self.case / "context.json", self.case / "claims.json"
        pack_path.write_bytes(models.canonical(pack))
        claims_path.write_text(json.dumps(dict(context=pack["id"], readings=[])))
        for command, expected in ((["impact", "--root", str(root)], 2),
                                  (["readings", "--pack", str(pack_path), "--claims", str(claims_path)], 1)):
            run = subprocess.run([sys.executable, "-B", str(ROOT / "memory.py"), *command],
                                 capture_output=True, text=True, timeout=60)
            self.assertEqual(run.returncode, expected, run.stdout + run.stderr)
            self.assertIsInstance(json.loads(run.stdout), dict)
        self.assertFalse((root / "_meta/memory").exists())


if __name__ == "__main__":
    unittest.main()
