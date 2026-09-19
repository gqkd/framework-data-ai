"""Offline qualification of the arm-C graph condition. No model, no human review simulated."""
import importlib.util
import json
from pathlib import Path
import shlex
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "evals/behaviour/retrieval"
spec = importlib.util.spec_from_file_location("test_graph_run", HERE / "run_graph.py")
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)
bench = run.base.load("test_graph_bench", HERE / "graph_retrieval_bench.py")


class ArmConditions(unittest.TestCase):
    """Only the candidate arm may carry the engine instruction."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="graph-arm-test-")
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name)
        prompts = self.output / "evaluator/prompts"
        prompts.mkdir(parents=True)
        (prompts / "R001.txt").write_text("Domanda sintetica.\n", encoding="utf-8")

    def test_baseline_arm_never_receives_the_engine_instruction(self):
        prompt = run.expected_prompt(self.output, {"question": "R001", "arm": "A"})
        self.assertNotIn("memory.py", prompt)
        self.assertNotIn("motore di memoria operativa", prompt)

    def test_candidate_arm_receives_the_documented_invocation(self):
        prompt = run.expected_prompt(self.output, {"question": "R001", "arm": "B"})
        self.assertIn("memory.py context --root ../project", prompt)
        self.assertIn("--skill audit", prompt)
        self.assertIn("references/operational-memory.md", prompt)

    def test_the_two_arms_differ_only_by_that_block(self):
        a = run.expected_prompt(self.output, {"question": "R001", "arm": "A"})
        b = run.expected_prompt(self.output, {"question": "R001", "arm": "B"})
        self.assertTrue(b.startswith(a))
        self.assertEqual(b[len(a):], run.GRAPH_PROMPT.format(python=shlex.quote(sys.executable)))

    def test_instruction_states_that_delivery_is_not_reading(self):
        block = run.GRAPH_PROMPT
        self.assertIn("non sono lettura", block)
        self.assertIn("non autorizza", block)
        self.assertIn("Se il motore non e' disponibile", block)

    def test_mode_and_policy_are_distinct_from_the_flexible_experiment(self):
        self.assertEqual(run.MODE, "instrumented-source-retrieval-graph-v3")
        self.assertNotEqual(run.MODE, run.flexible.MODE)
        self.assertNotEqual(run.POLICY, run.flexible.POLICY)
        self.assertEqual(run.POLICY["ranges"], run.flexible.POLICY["ranges"])


class BenchmarkScoring(unittest.TestCase):
    """Group scoring is an AND of groups, each an OR of accepted sources."""

    def setUp(self):
        self.sources = {"a": "A.md", "b": "B.md", "c": "C.md"}

    def test_a_group_is_satisfied_by_any_one_of_its_alternatives(self):
        case = {"sources": [["a", "b"], ["c"]]}
        self.assertEqual(bench.covered(case, self.sources, {"B.md", "C.md"}), (2, 2))

    def test_a_missing_group_is_not_compensated_by_a_repeated_one(self):
        case = {"sources": [["a"], ["c"]]}
        self.assertEqual(bench.covered(case, self.sources, {"A.md"}), (1, 2))

    def test_empty_delivery_scores_zero_not_an_error(self):
        case = {"sources": [["a"], ["b"]]}
        self.assertEqual(bench.covered(case, self.sources, set()), (0, 2))

    def test_terms_are_declared_for_every_question_and_carry_no_oracle_phrases(self):
        import yaml
        oracle = yaml.safe_load((HERE / "oracle.yaml").read_text(encoding="utf-8"))
        questions = yaml.safe_load((HERE / "questions.yaml").read_text(encoding="utf-8"))["questions"]
        self.assertEqual(sorted(bench.TERMS), sorted(q["id"] for q in questions))
        for identifier, terms in bench.TERMS.items():
            phrases = " ".join(oracle["cases"][identifier].get("must_include", [])).lower()
            for term in terms:
                self.assertNotIn(term.lower(), {p.strip() for p in phrases.split(",")})

    def test_delivery_maps_node_and_source_identifiers_back_to_paths(self):
        paths = {"document:1": "X.md", "source:2": "Y.md"}
        found = bench.delivered([{"node": "document:1", "body": "abc"},
                                 {"source": "source:2", "body": "de"},
                                 {"node": "unknown", "body": "ignored"}], paths)
        self.assertEqual(dict(found), {"X.md": 3, "Y.md": 2})

    def test_index_prefers_declared_document_paths_and_adds_sources(self):
        graph = {"nodes": [{"id": "document:1", "data": {"path": "X.md"}},
                           {"id": "document:2", "data": {}}],
                 "sources": [{"id": "source:2", "path": "Y.md"}]}
        self.assertEqual(bench.index(graph), {"document:1": "X.md", "source:2": "Y.md"})


class ReportedFindings(unittest.TestCase):
    """The recorded benchmark stays consistent with its own report."""

    def setUp(self):
        path = HERE / "GRAPH-RETRIEVAL-RESULTS.json"
        if not path.is_file():
            self.skipTest("benchmark report not present in this checkout")
        self.report = json.loads(path.read_text(encoding="utf-8"))

    def test_no_model_was_invoked(self):
        self.assertEqual(self.report["model_invocations"], 0)

    def test_recall_totals_match_the_per_question_rows(self):
        rows = self.report["questions"]
        total = sum(r["groups"] for r in rows)
        for method in ("m1", "m2", "m3"):
            self.assertEqual(self.report["recall"][method]["of"], total)
            self.assertEqual(self.report["recall"][method]["groups"],
                             sum(r[f"{method}_groups"] for r in rows))

    def test_recall_never_exceeds_the_required_groups_of_a_question(self):
        for row in self.report["questions"]:
            for method in ("m1", "m2", "m3"):
                self.assertLessEqual(row[f"{method}_groups"], row["groups"])

    def test_context_pack_is_recorded_as_not_question_sensitive(self):
        self.assertFalse(self.report["context_pack"]["question_sensitive"])

    def test_code_graph_is_recorded_as_unavailable_with_its_reason(self):
        code = self.report["code_graph"]
        self.assertEqual(code["status"], "unavailable")
        self.assertEqual(code["provider_reason"], "provider-not-configured")
        self.assertEqual((code["nodes"], code["edges"], code["sources"]), (0, 0, 0))

    def test_required_sources_stay_stable_under_budget_pressure(self):
        samples = self.report["budget_sensitivity"]["samples"]
        self.assertGreater(len(samples), 3)
        for sample in samples:
            self.assertGreaterEqual(sample["evidence_characters"], 0)
            self.assertGreaterEqual(sample["adopted_rules_characters"], 0)

    def test_tightening_the_budget_does_not_buy_more_evidence(self):
        samples = {s["text_budget"]: s for s in self.report["budget_sensitivity"]["samples"]}
        self.assertLess(samples[50000]["evidence_characters"], samples[100000]["evidence_characters"])
        self.assertLess(samples[20000]["evidence_characters"], samples[50000]["evidence_characters"])

    def test_required_sources_grow_with_the_corpus_instead_of_ranking(self):
        samples = sorted(self.report["corpus_scaling"]["samples"], key=lambda s: s["documents"])
        self.assertGreater(len(samples), 2)
        for smaller, larger in zip(samples, samples[1:]):
            self.assertGreater(larger["required_sources"], smaller["required_sources"])
            self.assertLess(larger["precision_percent"], smaller["precision_percent"])

    def test_delivered_evidence_does_not_grow_with_the_corpus(self):
        evidence = {s["evidence_characters"] for s in self.report["corpus_scaling"]["samples"]}
        self.assertEqual(len(evidence), 1, "budget residue is fixed regardless of corpus size")

    def test_every_missing_context_group_is_a_code_path(self):
        for path in self.report["context_pack"]["missing_paths"]:
            self.assertTrue(path.startswith("code/"), path)


if __name__ == "__main__":
    unittest.main()
