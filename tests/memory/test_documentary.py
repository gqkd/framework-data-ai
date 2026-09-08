"""Phase-two executable gates. No provider/model/network and no fixture-answer rewrites."""
from __future__ import annotations

from copy import deepcopy
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import jsonschema
import yaml

from test_phase0 import ROOT, fixture, metadata, validate as audit
from test_references import v

snapshots = importlib.import_module(v._CORE_NAME + ".snapshots")
workspace = importlib.import_module(v._CORE_NAME + ".workspace")
models = importlib.import_module(v._CORE_NAME + ".memory.models")
graphs = importlib.import_module(v._CORE_NAME + ".memory.graph")
queries = importlib.import_module(v._CORE_NAME + ".memory.query")
searches = importlib.import_module(v._CORE_NAME + ".memory.search")


def amend(path, **fields):
    text = path.read_text(encoding="utf-8")
    meta, body, error = v.parse_front_matter(text)
    assert error is None, error
    meta.update(fields)
    path.write_text("---\n" + yaml.safe_dump(meta, sort_keys=False) + "---" + body, encoding="utf-8")


def config(root, **values):
    path = root / ".framework-memory/config.yaml"
    path.parent.mkdir(exist_ok=True)
    path.write_text(yaml.safe_dump(values), encoding="utf-8")


def nodes(graph, kind):
    return [n for n in graph["nodes"] if n["kind"] == kind]


class DocumentaryMemory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="documentary-fixtures-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.fixtures = Path(cls.temp.name) / "frozen"
        fixture.build(cls.fixtures)
        cls.overlays = yaml.safe_load((ROOT / "tests/fixtures/memory/phase2-metadata.yaml").read_text())

    def setUp(self):
        self.temp_case = tempfile.TemporaryDirectory(prefix="documentary-case-")
        self.addCleanup(self.temp_case.cleanup)
        self.case = Path(self.temp_case.name)

    def project(self, name="multi-repo", *, enrich=True, destination="project"):
        root = self.case / destination
        shutil.copytree(self.fixtures / name, root)
        if enrich:
            for path, fields in self.overlays.get(name, {}).items():
                amend(root / path, **fields)
        return root

    def build(self, root):
        snapshot = snapshots.capture(root)
        return snapshot, graphs.build(snapshot)

    def cli(self, root, command, *options, entry=None):
        run = subprocess.run([sys.executable, "-B", str(entry or ROOT / "memory.py"), command,
                              "--root", str(root), *options], capture_output=True, text=True,
                             cwd=self.case, timeout=30)
        self.assertIn(run.returncode, (0, 1, 2), run.stderr)
        self.assertFalse(run.stderr, run.stderr)
        return run.returncode, json.loads(run.stdout)

    def test_document_only_pack_without_arc_repository_or_provider(self):
        root = self.project("document-only")
        snapshot, graph = self.build(root)
        self.assertFalse(nodes(graph, "repository"))
        self.assertFalse(nodes(graph, "code-root"))
        self.assertEqual(graph["coverage"], "available", graph["issues"])
        pack = queries.query(snapshot, graph, product="alpha")
        self.assertTrue(any("Processor design" in d["body"] for d in pack["documents"]))
        self.assertEqual(pack["code_observation"], "not_requested")
        self.assertFalse((root / "products/alpha/ARC.md").exists())
        self.assertFalse((root / "_meta/memory").exists())

    def test_same_sources_reversed_discovery_order_have_identical_bytes(self):
        root = self.project()
        original, graph = self.build(root)
        paths = workspace.Workspace.paths
        with patch.object(workspace.Workspace, "paths", lambda obj: list(reversed(paths(obj)))):
            reversed_snapshot = snapshots.capture(root)
        reversed_snapshot.artifacts.reverse()
        self.assertEqual(original.id, reversed_snapshot.id)
        self.assertEqual(models.canonical(graph), models.canonical(graphs.build(reversed_snapshot)))

    def test_checkout_location_and_mtime_do_not_change_snapshot_or_graph(self):
        left = self.project(destination="left")
        right = self.project(destination="other-location")
        for path in right.rglob("*.md"):
            os.utime(path, (1700000000, 1700000000))
        first, graph = self.build(left)
        second, other = self.build(right)
        self.assertEqual(first.id, second.id)
        self.assertEqual(models.canonical(graph), models.canonical(other))
        self.assertNotIn(str(self.case), models.canonical(graph).decode())

    def test_effective_generator_identity_is_an_input(self):
        root = self.project()
        one, _ = self.build(root)
        with patch.object(snapshots, "generator_inputs", return_value={"generator": "next"}):
            two, _ = self.build(root)
        self.assertNotEqual(one.id, two.id)
        self.assertIn("generator_version", one.inputs)

    def test_logical_document_repository_scopes_sources_and_nodes(self):
        root = self.project("document-only")
        before, first = self.build(root)
        config(root, document_repository="another-doc-repository")
        after, second = self.build(root)
        self.assertNotEqual(before.id, after.id)
        self.assertFalse({s["id"] for s in first["sources"]} & {s["id"] for s in second["sources"]})
        self.assertFalse({n["id"] for n in first["nodes"]} & {n["id"] for n in second["nodes"]})

    def test_git_commit_and_working_document_bytes_are_distinct_inputs(self):
        root = self.project("document-only")
        fixture.git(root, "init", "--initial-branch=main", "--template=")
        fixture.git(root, "add", "--all")
        fixture.git(root, "commit", "-m", "Document baseline")
        before, _ = self.build(root)
        path = root / "products/alpha/PBR.md"
        path.write_text(path.read_text() + "\nUnstaged documentation\n")
        after, _ = self.build(root)
        self.assertEqual(before.inputs["document_commit"], fixture.git(root, "rev-parse", "HEAD"))
        self.assertEqual(before.inputs["document_commit"], after.inputs["document_commit"])
        self.assertNotEqual(before.id, after.id)

    def test_dirty_contents_not_a_boolean_and_deletion_change_identity(self):
        root = self.project()
        before, _ = self.build(root)
        path = root / "products/alpha/PBR.md"
        path.write_text(path.read_text() + "\nFirst change.\n")
        first, _ = self.build(root)
        path.write_text(path.read_text() + "\nSecond change.\n")
        second, _ = self.build(root)
        path.unlink()
        deleted, _ = self.build(root)
        self.assertEqual(len({s.id for s in (before, first, second, deleted)}), 4)

    def test_current_target_mappings_do_not_observe_even_present_code(self):
        _, graph = self.build(self.project())
        roots = nodes(graph, "code-root")
        self.assertEqual({n["data"]["view"] for n in roots}, {"current", "target"})
        for node in roots + nodes(graph, "repository"):
            self.assertEqual(node["observation"], dict(path_status="unresolved",
                observation_status="not_requested", freshness="unknown"))
        self.assertEqual(len(nodes(graph, "component")), 3)
        self.assertFalse(any(n["label"] == "product:platform" for n in graph["nodes"]))

    def test_realized_in_and_inverse_rules_have_verifiable_provenance(self):
        _, graph = self.build(self.project())
        by_id = {e["id"]: e for e in graph["edges"]}
        for edge in graph["edges"]:
            rules = models.contract()["relations"][edge["relation"]]
            self.assertEqual(edge["provenance"]["assertion_method"], rules["method"])
            if rules.get("inverse_of"):
                origin = by_id[edge["provenance"]["rule"]["origin_edge"]]
                self.assertEqual(edge["source"], origin["target"])
                self.assertEqual(edge["target"], origin["source"])
                self.assertEqual(edge["provenance"]["sources"], origin["provenance"]["sources"])
        models.validate_graph(graph)

    def test_all_ten_relations_reject_wrong_assertion_methods(self):
        _, graph = self.build(self.project())
        prototype = deepcopy(graph["edges"][0])
        for relation, rule in models.contract()["relations"].items():
            with self.subTest(relation=relation):
                edge = deepcopy(prototype)
                edge["relation"] = relation
                edge["provenance"]["assertion_method"] = "declared" if rule["method"] == "derived" else "derived"
                edge["provenance"]["rule"] = dict(id=rule.get("rule", "bad"), version="1", origin_edge="origin")
                with self.assertRaises(jsonschema.ValidationError):
                    models.validate("edge", edge)

    def test_confidence_is_only_allowed_on_inferred_and_inferences_not_in_projection(self):
        _, graph = self.build(self.project())
        value = deepcopy(graph["nodes"][0]["provenance"])
        value["confidence"] = 0.9
        with self.assertRaises(jsonschema.ValidationError):
            models.validate("provenance", value)
        value.update(assertion_method="inferred", rationale="synthetic hypothesis")
        models.validate("provenance", value)
        graph["nodes"][0]["provenance"] = value
        with self.assertRaisesRegex(ValueError, "inferences"):
            models.validate_graph(graph)

    def test_inverse_cannot_lie_about_its_origin_or_revision(self):
        _, graph = self.build(self.project())
        inverse = next(e for e in graph["edges"] if e["relation"] == "constrained_by")
        inverse["provenance"]["rule"]["origin_edge"] = "absent"
        with self.assertRaisesRegex(ValueError, "inverse"):
            models.validate_graph(graph)
        _, graph = self.build(self.project(destination="second"))
        graph["nodes"][0]["provenance"]["sources"][0]["end_line"] = 100000
        with self.assertRaisesRegex(ValueError, "localization"):
            models.validate_graph(graph)

    def test_legacy_decision_is_retrievable_and_partial_supersession_keeps_it(self):
        root = self.project(enrich=False)
        fixture.Documents(root).artifact("decisions/DEC-002-partial.md", "decision-record",
            "# Partial replacement\n\n## Decision\nChange normalization only; keep tenant isolation.\n",
            lifecycle="immutable", status="accepted", id="DEC-002", products=["alpha", "beta"],
            scope="architecture", supersedes="DEC-001", leaves_open=[])
        snapshot, graph = self.build(root)
        pack = queries.query(snapshot, graph, selector="DEC-002", hops=1)
        self.assertEqual({n["label"] for n in pack["nodes"]}, {"DEC-001", "DEC-002"})
        self.assertTrue(any("Tenant state must not be cached" in d["body"] for d in pack["documents"]))
        result = queries.query(snapshot, graph, text="mutable cache")
        self.assertTrue(result["documents"])

    def test_subjects_keep_candidate_join_and_never_spread_impacts(self):
        root = self.project()
        docs = fixture.Documents(root)
        docs.log("alpha")
        docs.triage()
        docs.change("alpha:SIG-001")
        amend(root / fixture.ICG, subjects={"SIG-001": ["component:product:alpha:api"]})
        amend(root / fixture.CHG, targets=["component:product:alpha:api"], preserves=["DEC-001"])
        _, graph = self.build(root)
        icg = next(n for n in nodes(graph, "document") if n["label"] == "ICG-001")
        row = icg["data"]["subjects"][0]
        self.assertEqual(row["candidate"]["scope"], "product:alpha")
        self.assertEqual(row["impact_attribution"], "candidate-only")
        self.assertNotIn("impacts", row)
        self.assertEqual(row["mapping_status"], "declared")
        self.assertTrue(row["candidate_node"])
        self.assertTrue(any(e["relation"] == "targets" for e in graph["edges"]))
        self.assertTrue(any(e["relation"] == "preserves" for e in graph["edges"]))

    def test_subjects_duplicates_and_unrouted_keys_are_not_chosen(self):
        for fields in ({"SIG-001": [], "alpha:SIG-001": []}, {"SIG-999": []}):
            with self.subTest(fields=fields):
                root = self.project(destination="case" + str(len(list(self.case.iterdir()))))
                docs = fixture.Documents(root)
                docs.log("alpha")
                docs.triage()
                amend(root / fixture.ICG, subjects=fields)
                _, graph = self.build(root)
                self.assertTrue(any(i["code"] == "subjects-candidate-unresolved" for i in graph["issues"]))
                icg = next(n for n in nodes(graph, "document") if n["label"] == "ICG-001")
                self.assertFalse(icg["data"]["subjects"])

    def test_missing_component_is_explicit_not_empty_mapping(self):
        root = self.project()
        docs = fixture.Documents(root)
        docs.log("alpha")
        docs.triage()
        amend(root / fixture.ICG, subjects={"SIG-001": ["component:product:alpha:absent"]})
        _, graph = self.build(root)
        row = next(n for n in nodes(graph, "document") if n["label"] == "ICG-001")["data"]["subjects"][0]
        self.assertEqual(row["mapping_status"], "partial")
        self.assertEqual(row["unresolved_components"], ["component:product:alpha:absent"])
        self.assertEqual(graph["coverage"], "partial")

    def test_references_never_guess_missing_targets(self):
        root = self.project()
        amend(root / "decisions/DEC-001-shared-rule.md", applies_to=["component:platform:absent"])
        _, graph = self.build(root)
        self.assertEqual(graph["coverage"], "partial")
        self.assertFalse(any(e["relation"] == "applies_to" for e in graph["edges"]))

    def test_duplicate_local_ids_are_separate_and_bare_selector_is_ambiguous(self):
        root = self.project("triage-collision")
        snapshot, graph = self.build(root)
        signals = [n for n in nodes(graph, "entry") if n["label"] == "SIG-001"]
        self.assertEqual({n["identity"]["scope"] for n in signals}, {"product:alpha", "product:beta"})
        with self.assertRaises(workspace.MemoryInputError):
            queries.query(snapshot, graph, selector="SIG-001")
        result = queries.query(snapshot, graph, selector="beta:SIG-001")
        self.assertEqual(len(result["nodes"]), 1)

    def test_path_alias_and_overlapping_roots_keep_all_component_mappings(self):
        root = self.project()
        fields = deepcopy(self.overlays["multi-repo"]["products/alpha/ARC.md"])
        fields["components"]["component:product:alpha:second"] = {
            "current": {"code_roots": [{"repository": "product.api", "path": "."}]}}
        amend(root / "products/alpha/ARC.md", **fields)
        _, graph = self.build(root)
        root_node = next(n for n in nodes(graph, "code-root")
                         if n["data"]["path"] == "." and "product:alpha" in n["label"])
        edges = [e for e in graph["edges"] if e["relation"] == "realized_in" and e["target"] == root_node["id"]]
        self.assertEqual(len({e["source"] for e in edges}), 2)

    def test_invalid_root_shapes_and_wrong_design_view_are_rejected(self):
        for path in ("../outside", "/absolute", "C:/private", "src\\module"):
            with self.subTest(path=path), self.assertRaises(jsonschema.ValidationError):
                models.validate("code-root", {"repository": "product.api", "path": path})
        with self.assertRaises(jsonschema.ValidationError):
            models.validate("design-components", {"component:product:alpha:api": {"current": {}}})

    def test_new_optional_schema_fields_and_legacy_documents_validate(self):
        for name in ("multi-repo", "document-only"):
            root = self.project(name, destination=name)
            report = audit(root)
            self.assertFalse([f for f in report["findings"] if f["level"] == "error"], report)
        root = self.project("multi-repo", enrich=False, destination="legacy")
        self.assertEqual(audit(root)["errors"], 0)

    def test_reserved_directories_are_excluded_when_skip_hidden_is_false(self):
        root = self.project("document-only")
        (root / "framework.yaml").write_text("scan:\n  skip_hidden: false\n  skip_dirs: [code]\n")
        config(root)
        fixture.write(root, ".framework-memory/local.yaml", "checkouts: {}\n")
        fixture.write(root, "_meta/memory/cache/not-an-artifact.md", "private cache\n")
        snapshot, graph = self.build(root)
        self.assertFalse(any("memory/" in p or "framework-memory/" in p for p in snapshot.texts))
        self.assertFalse([f for f in audit(root)["findings"] if f["code"] == "FM001"])
        self.assertEqual(graph["coverage"], "available")

    def test_local_bindings_and_repository_urls_are_not_exported(self):
        root = self.project()
        config(root)
        fixture.write(root, ".framework-memory/local.yaml",
                      "checkouts:\n  repository:product:alpha:api: /private/person/token-secret\n")
        snapshot, graph = self.build(root)
        one = snapshot.id
        raw = models.canonical({"graph": graph, "inputs": snapshot.inputs}).decode()
        self.assertNotIn("token-secret", raw)
        self.assertNotIn("https://example.invalid", raw)
        fixture.write(root, ".framework-memory/local.yaml", "checkouts: {}\n")
        self.assertEqual(one, snapshots.capture(root).id)
        self.assertEqual(self.cli(root, "doctor")[0], 0)

    def test_restricted_source_is_neither_indexed_nor_exported(self):
        root = self.project()
        fixture.Documents(root).artifact("decisions/DEC-099-secret.md", "decision-record",
            "# DO NOT EXPORT\nsecretneedle\n", lifecycle="immutable", id="DEC-099",
            classification="confidential", scope="platform", products=["alpha"], leaves_open=[])
        snapshot, graph = self.build(root)
        pack = queries.query(snapshot, graph, text="secretneedle")
        result = models.canonical({"graph": graph, "pack": pack, "inputs": snapshot.inputs}).decode()
        self.assertNotIn("DEC-099", result)
        self.assertNotIn("secretneedle", result)
        self.assertFalse(pack["documents"])
        self.assertEqual(snapshot.inputs["filtered_sources"], 1)

    def test_literal_search_reports_exact_source_lines_and_keeps_no_inferred_edges(self):
        snapshot, graph = self.build(self.project())
        original = models.canonical(graph)
        pack = queries.query(snapshot, graph, text="mutable cache")
        hit = pack["search"]["matches"][0]
        for excerpt in hit["excerpts"]:
            self.assertEqual(snapshot.texts[hit["path"]].splitlines()[excerpt["line"] - 1], excerpt["text"])
        self.assertEqual(original, models.canonical(graph))
        self.assertTrue(all(n["provenance"]["assertion_method"] != "inferred" for n in pack["nodes"]))

    def test_fts5_is_optional_and_fallback_is_visible(self):
        with patch.object(searches.sqlite3, "connect", side_effect=searches.sqlite3.OperationalError):
            result = searches.search({"a": "Tenant state"}, "tenant", engine="fts5")
        self.assertEqual(result["engine"], "literal")
        self.assertEqual(result["fallback"], "fts5-unavailable")
        self.assertTrue(result["matches"])
        result = searches.search({"a": "Tenant state"}, 'tenant OR "*', engine="fts5")
        self.assertIn(result["engine"], ("fts5", "literal"))

    def test_query_limits_cycles_and_explanations_are_explicit(self):
        snapshot, graph = self.build(self.project())
        result = queries.query(snapshot, graph, selector="DEC-001", hops=3, limit=2)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["coverage"], "partial")
        self.assertLessEqual(len(result["nodes"]), 2)
        edge_ids = {e["id"] for e in result["edges"]}
        self.assertTrue(any(p["steps"] for p in result["paths"]))
        self.assertTrue(all(step["edge"] in edge_ids for p in result["paths"] for step in p["steps"]))
        with self.assertRaises(workspace.MemoryInputError):
            queries.query(snapshot, graph, hops=100)

    def test_parse_failure_is_partial_not_an_empty_success(self):
        root = self.project()
        fixture.write(root, "broken.md", "---\ninvalid: [\n---\n")
        _, graph = self.build(root)
        self.assertEqual(graph["coverage"], "partial")
        self.assertTrue(any(i["code"] == "parse-failed" and i["path"] == "broken.md" for i in graph["issues"]))
        self.assertTrue(nodes(graph, "document"))

    def test_yaml_alias_cycles_are_bounded_and_other_documents_remain_available(self):
        root = self.project()
        fixture.write(root, "cyclic.md", "---\nclassification: internal\ncycle: &cycle [*cycle]\n---\n")
        _, graph = self.build(root)
        self.assertEqual(graph["coverage"], "partial")
        self.assertTrue(any(i["code"] == "metadata-limit" for i in graph["issues"]))
        self.assertTrue(nodes(graph, "document"))

    def test_atomic_publish_twice_identical_does_not_rewrite_sources(self):
        root = self.project()
        snapshot, graph = self.build(root)
        manifest = snapshots.publish(snapshot, graph)
        snapshots.publish(snapshot, graph)
        directory = root / "_meta/memory/snapshots" / snapshot.id
        self.assertEqual((directory / "graph.json").read_bytes(), models.canonical(graph))
        self.assertEqual(manifest["files"]["graph.json"], models.digest((directory / "graph.json").read_bytes()))
        self.assertEqual(snapshot.id, snapshots.capture(root).id)
        self.assertFalse(list(directory.parent.glob(".pending-*")))

    def test_a_graph_cannot_be_published_under_another_snapshot_identity(self):
        root = self.project()
        snapshot, graph = self.build(root)
        graph["snapshot"] = "not-this-snapshot"
        with self.assertRaisesRegex(workspace.MemoryInputError, "identities"):
            snapshots.publish(snapshot, graph)
        self.assertFalse((root / "_meta/memory").exists())

    def test_mutation_during_read_or_before_publish_cannot_publish_mixed_snapshot(self):
        root = self.project()
        original = snapshots.read_inputs
        calls = 0
        def changing(ws):
            nonlocal calls
            result = original(ws)
            calls += 1
            if calls == 1:
                path = root / "products/alpha/PBR.md"
                path.write_text(path.read_text() + "\nConcurrent change\n")
            return result
        with patch.object(snapshots, "read_inputs", changing), self.assertRaises(snapshots.ConcurrentChange):
            snapshots.capture(root)
        snapshot, graph = self.build(root)
        fixture.write(root, "new.md", "not an artifact")
        with self.assertRaises(snapshots.ConcurrentChange):
            snapshots.publish(snapshot, graph)
        self.assertFalse((root / "_meta/memory").exists())

    def test_corrupt_snapshot_and_competing_writer_are_not_overwritten(self):
        root = self.project()
        snapshot, graph = self.build(root)
        snapshots.publish(snapshot, graph)
        directory = root / "_meta/memory/snapshots" / snapshot.id
        (directory / "graph.json").write_text("corrupt")
        with self.assertRaisesRegex(workspace.MemoryInputError, "differs"):
            snapshots.publish(snapshot, graph)
        self.assertEqual((directory / "graph.json").read_text(), "corrupt")
        (directory.parent / ".build.lock").touch()
        with self.assertRaisesRegex(workspace.MemoryInputError, "lock"):
            snapshots.publish(snapshot, graph)
        self.assertTrue((directory.parent / ".build.lock").exists())

    def test_output_and_source_links_cannot_escape_workspace(self):
        root = self.project()
        outside = self.case / "outside"
        outside.mkdir()
        (root / "_meta").mkdir()
        (root / "_meta/memory").symlink_to(outside, target_is_directory=True)
        snapshot, graph = self.build(root)
        with self.assertRaises(workspace.MemoryInputError):
            snapshots.publish(snapshot, graph)
        self.assertFalse(list(outside.iterdir()))
        (outside / "document.md").write_text("outside")
        (root / "linked.md").symlink_to(outside / "document.md")
        with self.assertRaises(workspace.MemoryInputError):
            snapshots.capture(root)

    def test_invalid_config_and_limits_fail_without_echoing_private_values(self):
        root = self.project()
        config(root, unknown="token-private")
        code, result = self.cli(root, "doctor")
        self.assertEqual(code, 2)
        self.assertNotIn("token-private", json.dumps(result))
        config(root, max_files=1)
        self.assertEqual(self.cli(root, "build")[0], 2)
        self.assertFalse((root / "_meta/memory").exists())

    def test_config_change_during_loading_is_not_accepted_as_coherent(self):
        root = self.project()
        config(root, max_hops=3)
        read = snapshots.read_inputs
        first = True
        def changing(ws):
            nonlocal first
            if first:
                first = False
                config(root, max_hops=1)
            return read(ws)
        with patch.object(snapshots, "read_inputs", changing), self.assertRaises(snapshots.ConcurrentChange):
            snapshots.capture(root)

    def test_duplicate_contract_keys_and_generator_field_definitions_fail(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            models._read_contract(b"definitions: {}\ndefinitions: {}\n")
        module_spec = importlib.util.spec_from_file_location("_phase2_generate", ROOT / "schemas/generate.py")
        generator = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(generator)
        registry = yaml.safe_load((ROOT / "schemas/artifact-types.yaml").read_text())
        spec = deepcopy(registry["types"]["product-manifest"])
        spec["maps"]["code"]["fields"]["typed"]["url"] = "reference"
        with self.assertRaises(SystemExit):
            generator.build("product-manifest", spec, registry)
        spec = deepcopy(registry["types"]["decision-record"])
        spec["memory_fields"]["status"] = "reference"
        with self.assertRaises(SystemExit):
            generator.build("decision-record", spec, registry)

    def test_file_limits_and_fifo_sources_fail_without_hanging(self):
        root = self.project()
        config(root, max_file_bytes=1)
        with self.assertRaises(workspace.MemoryInputError):
            snapshots.capture(root)
        config(root)
        if hasattr(os, "mkfifo"):
            os.mkfifo(root / "pipe.md")
            with self.assertRaises(workspace.MemoryInputError):
                snapshots.capture(root)

    def test_cli_read_only_commands_and_build_export(self):
        root = self.project("document-only")
        self.assertEqual(self.cli(root, "doctor")[0], 0)
        code, graph = self.cli(root, "build", "--dry-run", "--export")
        self.assertEqual(code, 0, graph)
        models.validate_graph(graph)
        code, result = self.cli(root, "query", "--product", "alpha")
        self.assertEqual(code, 0, result)
        self.assertTrue(result["documents"])
        self.assertFalse((root / "_meta/memory").exists())
        code, result = self.cli(root, "build")
        self.assertEqual(code, 0, result)
        self.assertTrue((root / result["output"] / "graph.json").is_file())

    def test_generated_contract_schemas_are_fresh(self):
        run = subprocess.run([sys.executable, "-B", str(ROOT / "schemas/generate_memory.py"), "--check"],
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
