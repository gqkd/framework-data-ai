"""Offline checks of the G0 source-discovery qualifier, never model invocations."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "evals/behaviour/retrieval/qualify_graph_ablation.py"
spec = importlib.util.spec_from_file_location("graph_g0", SCRIPT)
g0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g0)


class QualificationTests(unittest.TestCase):
    def setUp(self):
        self.seeds = json.loads((g0.HERE / "GRAPH-ABLATION-SEEDS.json").read_bytes())

    def test_frozen_seed_policy(self):
        g0.validate_seeds(self.seeds)

    def test_reject_changed_engine(self):
        self.seeds["engine"] = "semantic"
        with self.assertRaises(ValueError):
            g0.validate_seeds(self.seeds)

    def test_reject_empty_seed(self):
        self.seeds["questions"]["R013"]["terms"] = [""]
        with self.assertRaises(ValueError):
            g0.validate_seeds(self.seeds)

    def test_requests_differ_only_in_hops(self):
        for item in self.seeds["questions"].values():
            for term in item["terms"]:
                a = g0.request_args(Path("/synthetic"), term, 0, self.seeds)
                b = g0.request_args(Path("/synthetic"), term, 2, self.seeds)
                self.assertEqual(a[:-1], b[:-1])
                self.assertEqual(a[-2:], ["--hops", "0"])
                self.assertEqual(b[-2:], ["--hops", "2"])
                self.assertNotIn("oracle", " ".join(a))

    def test_partial_is_not_empty_success(self):
        self.assertEqual(g0.decode_result(1, '{"coverage":"partial"}')["coverage"], "partial")

    def test_unavailable_fails_closed(self):
        for code in (2, 3, -9):
            with self.assertRaises(ValueError):
                g0.decode_result(code, '{"coverage":"available"}')

    def test_invalid_json_fails_closed(self):
        with self.assertRaises(ValueError):
            g0.decode_result(0, "not json")

    def test_status_mismatch_rejected(self):
        for code, coverage in ((0, "partial"), (1, "available"), (0, "unavailable")):
            with self.assertRaises(ValueError):
                g0.decode_result(code, json.dumps({"coverage": coverage}))

    def test_provenance_and_repositories_are_not_documents(self):
        response = {"nodes": [
            {"id": "doc", "kind": "document", "data": {"path": "DEC.md"}},
            {"id": "repo", "kind": "repository", "data": {"path": "code/"}}],
            "documents": [{"node": "doc", "body": "text"}],
            "sources": [{"id": "s", "path": "UNREAD.md"}]}
        self.assertEqual(g0.selected_document_paths(response), {"DEC.md"})

    def test_missing_exported_body_rejected(self):
        with self.assertRaises(ValueError):
            g0.selected_document_paths({"nodes": [
                {"id": "doc", "kind": "document", "data": {"path": "DEC.md"}}], "documents": []})

    def test_required_groups_are_and_of_or(self):
        case = {"sources": [["a", "b"], ["c"]]}
        sources = {key: {"path": key + ".md"} for key in "abc"}
        got = g0.source_group_score(case, sources, {"b.md", "extra.md"})
        self.assertEqual(got["covered_groups"], [0])
        self.assertEqual(got["missing_groups"], [["c.md"]])
        self.assertEqual(got["non_required_documents"], ["extra.md"])

    def test_existing_output_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                g0.absent_output(Path(directory), Path(directory) / "source")

    def test_nested_input_output_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                g0.absent_output(Path(directory) / "new", Path(directory))

    def test_relative_output_rejected(self):
        with self.assertRaises(ValueError):
            g0.absent_output(Path("relative"), Path("/synthetic"))

    def test_serialization_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory) / "a.json", Path(directory) / "b.json"
            g0.save(a, {"z": 1, "a": [2]})
            g0.save(b, {"a": [2], "z": 1})
            self.assertEqual(a.read_bytes(), b.read_bytes())


if __name__ == "__main__":
    unittest.main()
