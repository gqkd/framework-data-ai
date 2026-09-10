"""Phase-three deterministic gates. No network, installation or external binary required."""
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

from test_phase0 import ROOT, fixture
from test_references import v
from test_documentary import amend

snapshots = importlib.import_module(v._CORE_NAME + ".snapshots")
graphs = importlib.import_module(v._CORE_NAME + ".memory.graph")
models = importlib.import_module(v._CORE_NAME + ".memory.models")
code = importlib.import_module(v._CORE_NAME + ".memory.code_graph")
sources = importlib.import_module(v._CORE_NAME + ".memory.code_sources")
base = importlib.import_module(v._CORE_NAME + ".memory.providers.base")
enola = importlib.import_module(v._CORE_NAME + ".memory.providers.enola")
process = importlib.import_module(v._CORE_NAME + ".memory.providers.process")

API = "repository:product:alpha:api"
WORKER = "repository:product:beta:worker"
RULES = "repository:platform:rules"


def record(name="service.response", path="service.py", line=1, relations=None):
    value = dict(kind="symbol", name=name, file=path, line=line, repo="repository", relations=relations or [])
    value["id"] = enola.fact_id(value)
    return value


class CodeMemory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="code-fixtures-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.fixtures = Path(cls.temp.name) / "frozen"
        fixture.build(cls.fixtures)
        cls.overlays = yaml.safe_load((ROOT / "tests/fixtures/memory/phase2-metadata.yaml").read_text())

    def setUp(self):
        self.temp_case = tempfile.TemporaryDirectory(prefix="code-case-")
        self.addCleanup(self.temp_case.cleanup)
        self.case = Path(self.temp_case.name)

    def project(self, name="multi-repo", destination="project"):
        root = self.case / destination
        shutil.copytree(self.fixtures / name, root)
        for path, fields in self.overlays.get(name, {}).items():
            amend(root / path, **fields)
        bindings = {API: "code/alpha-api", WORKER: "code/beta-worker", RULES: "code/shared-rules"}
        self.bind(root, bindings)
        return root

    def bind(self, root, bindings):
        target = root / ".framework-memory/local.yaml"
        target.parent.mkdir(exist_ok=True)
        target.write_text(yaml.safe_dump(dict(checkouts=bindings)))

    def build(self, root, provider=None, **kwargs):
        snapshot = snapshots.capture(root)
        return code.build_code(snapshot, graphs.build(snapshot), provider or base.FakeProvider(), **kwargs)

    def test_provider_interface_has_no_impact_method(self):
        for cls in (base.CodeProvider, base.FakeProvider, enola.EnolaProvider):
            self.assertFalse(hasattr(cls, "impact"))

    def test_document_only_still_works_and_does_not_invent_code(self):
        root = self.project("document-only")
        result = self.build(root)
        self.assertEqual(result.graph["coverage"], "unavailable")
        self.assertEqual(result.graph["nodes"], [])
        self.assertEqual(graphs.build(result.document)["coverage"], "available")

    def test_missing_provider_never_claims_zero_impact_or_opens_code(self):
        root = self.project()
        with patch.object(code, "capture_code", side_effect=AssertionError("must not open")):
            result = self.build(root, base.FakeProvider(available=False))
        self.assertEqual(result.graph["coverage"], "unavailable")
        self.assertTrue(all(r["problems"][0]["code"] == "provider-unavailable" for r in result.graph["repositories"]))
        self.assertEqual(result.graph["edges"], [])

    def test_unbound_and_missing_repository_are_not_empty_success(self):
        root = self.project()
        self.bind(root, {API: "does-not-exist"})
        result = self.build(root)
        states = {r["repository"]: r["observation"] for r in result.graph["repositories"]}
        self.assertEqual(states[API]["path_status"], "missing")
        self.assertEqual(states[WORKER]["path_status"], "unresolved")
        self.assertEqual(result.graph["coverage"], "unavailable")

    def test_worktree_dirty_bytes_index_and_untracked_policy_are_distinct(self):
        root = self.project()
        repo = root / "code/alpha-api"
        first = sources.capture_code(repo)
        path = repo / "service.py"
        path.write_text(path.read_text() + "\n# unstaged A\n")
        second = sources.capture_code(repo)
        path.write_text(path.read_text() + "# unstaged B\n")
        third = sources.capture_code(repo)
        self.assertNotEqual(first.inputs, second.inputs)
        self.assertNotEqual(second.inputs, third.inputs)
        fixture.git(repo, "add", "service.py")
        staged = sources.capture_code(repo)
        self.assertEqual(staged.files, third.files)
        self.assertNotEqual(staged.inputs["index_hash"], third.inputs["index_hash"])
        (repo / "new.py").write_text("def new(): return 1\n")
        self.assertNotIn("new.py", sources.capture_code(repo).files)
        self.assertIn("new.py", sources.capture_code(repo, include_untracked=True).files)

    def test_missing_worktree_requires_explicit_commit_and_never_checks_out(self):
        root = self.project()
        repo = root / "code/alpha-api"
        commit = fixture.git(repo, "rev-parse", "HEAD").strip()
        (repo / "service.py").unlink()
        worktree = sources.capture_code(repo)
        self.assertNotIn("service.py", worktree.files)
        self.assertTrue(any(c["reason"] == "worktree-file-missing" for c in worktree.coverage))
        revision = sources.capture_code(repo, mode="git", revision=commit)
        self.assertIn("service.py", revision.files)
        self.assertFalse((repo / "service.py").exists())
        for kwargs in ({"mode": "git"}, {"mode": "git", "revision": "HEAD"}, {"revision": commit}):
            with self.assertRaises(sources.MemoryInputError):
                sources.capture_code(repo, **kwargs)

    def test_git_objects_work_from_a_bare_repository(self):
        root = self.project()
        original = root / "code/alpha-api"
        bare = self.case / "bare.git"
        fixture.git(self.case, "clone", "--bare", str(original), str(bare))
        commit = fixture.git(bare, "rev-parse", "HEAD").strip()
        self.assertIn("service.py", sources.capture_code(bare, mode="git", revision=commit).files)
        with self.assertRaises(sources.MemoryInputError):
            sources.capture_code(bare)

    def test_provider_cannot_publish_a_concurrently_changed_worktree(self):
        root = self.project()
        def mutate(files):
            path = root / "code/alpha-api/service.py"
            path.write_text(path.read_text() + "\n# concurrent\n")
            return base.Observation("available")
        with self.assertRaises(snapshots.ConcurrentChange):
            self.build(root, base.FakeProvider(mutate), repositories=[API])
        self.assertFalse((root / "_meta/memory").exists())

    def test_change_after_build_blocks_publication(self):
        root = self.project()
        result = self.build(root, repositories=[API])
        path = root / "code/alpha-api/service.py"
        path.write_text(path.read_text() + "\n# after\n")
        with self.assertRaises(snapshots.ConcurrentChange):
            result.publish()

    def test_duplicate_evidence_survives_and_name_only_target_stays_unresolved(self):
        root = self.project()
        caller = record(relations=[dict(kind="calls", target="service.health")])
        same_identity = record(line=2, relations=[dict(kind="calls", target="service.health")])
        target = record("service.health", line=3)
        def observe(_):
            return base.Observation("available", records=[caller, same_identity, target, target],
                                    coverage=[dict(path="service.py", status="available")])
        graph = self.build(root, base.FakeProvider(observe), repositories=[API]).graph
        self.assertEqual(len(graph["records"]), 4)
        symbols = [n for n in graph["nodes"] if n["kind"] == "symbol"]
        self.assertEqual(len(symbols), 2)
        self.assertTrue(all(len(n["provenance"]["records"]) == 2 for n in symbols))
        calls = [e for e in graph["edges"] if e["relation"] == "calls"]
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(e["resolution"] == "unresolved" for e in calls))
        self.assertEqual(graph["coverage"], "partial")

    def test_explicit_target_id_resolves_without_computing_transitive_edges(self):
        root = self.project()
        target = record("service.health", line=3)
        caller = record(relations=[dict(kind="calls", target=target["name"], target_id=target["id"])])
        graph = self.build(root, base.FakeProvider(lambda _: base.Observation("available", [caller, target])),
                           repositories=[API]).graph
        calls = [e for e in graph["edges"] if e["relation"] == "calls"]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["resolution"], "resolved")

    def test_same_checkout_basenames_do_not_merge_repository_identities(self):
        root = self.project()
        first, second = self.case / "one/same", self.case / "two/same"
        shutil.copytree(root / "code/alpha-api", first)
        shutil.copytree(first, second)
        self.bind(root, {API: str(first), WORKER: str(second)})
        graph = self.build(root, repositories=[API, WORKER]).graph
        api = {n["id"] for n in graph["nodes"] if n["repository"] == API}
        worker = {n["id"] for n in graph["nodes"] if n["repository"] == WORKER}
        self.assertTrue(api and worker)
        self.assertFalse(api & worker)
        encoded = models.canonical(graph)
        self.assertNotIn(str(first).encode(), encoded)
        self.assertNotIn(str(second).encode(), encoded)

    def test_relocation_and_provider_record_order_are_deterministic(self):
        first = self.project(destination="one")
        second = self.project(destination="two")
        records = [record(), record("service.health", line=3)]
        one = self.build(first, base.FakeProvider(lambda _: base.Observation("available", records)), repositories=[API])
        two = self.build(second, base.FakeProvider(lambda _: base.Observation("available", list(reversed(records)))), repositories=[API])
        self.assertEqual(models.canonical(one.graph), models.canonical(two.graph))

    def test_zones_and_overlapping_roots_preserve_all_mappings_and_views(self):
        root = self.project()
        arc = root / "products/alpha/ARC.md"
        components = deepcopy(self.overlays["multi-repo"]["products/alpha/ARC.md"]["components"])
        components["component:product:alpha:overlap"] = {"current": {"code_roots": [{"repository": "product.api", "path": "."}]}}
        amend(arc, components=components)
        product = root / "products/alpha/product.yaml"
        meta, _, _ = v.parse_front_matter(product.read_text())
        mapping = meta["code"]
        mapping["api"]["zones"] = [{"path": ".", "kind": "vendor"}, {"path": "tests", "kind": "test"}]
        amend(product, code=mapping)
        result = self.build(root, repositories=[API])
        graph = result.graph
        current = [b for b in graph["bridges"] if b["view"] == "current"]
        self.assertEqual(len(current), 2)
        self.assertTrue(set(current[0]["files"]) & set(current[1]["files"]))
        target = next(b for b in graph["bridges"] if b["view"] == "target")
        self.assertEqual(target["observation"]["path_status"], "missing")
        self.assertTrue(all("vendor" in n["zones"] for n in graph["nodes"] if n["kind"] == "file"))
        self.assertTrue(any(set(n["zones"]) == {"test", "vendor"} for n in graph["nodes"]))
        self.assertFalse(any(n["kind"] == "file" for n in graphs.build(result.document)["nodes"]))

    def test_schema_and_endpoint_validation_reject_fabricated_evidence(self):
        graph = self.build(self.project(), repositories=[API]).graph
        graph["nodes"][0]["provenance"]["records"] = ["absent"]
        with self.assertRaises(sources.MemoryInputError):
            code.validate_code_graph(graph)
        graph["nodes"][0]["provenance"]["assertion_method"] = "declared"
        with self.assertRaises(jsonschema.ValidationError):
            code.validate_code_graph(graph)

    def test_atomic_publication_separate_from_documentary_graph(self):
        root = self.project()
        result = self.build(root, repositories=[API])
        manifest = result.publish()
        result.publish()
        output = root / "_meta/memory/code-snapshots" / result.graph["snapshot"]
        self.assertEqual(models.digest((output / "code-graph.json").read_bytes()), manifest["files"]["code-graph.json"])
        self.assertFalse((root / "_meta/memory/snapshots").exists())
        (output / "code-graph.json").write_text("corrupt")
        with self.assertRaisesRegex(sources.MemoryInputError, "differs"):
            result.publish()

    def test_symlink_fifo_and_limits_do_not_get_observed(self):
        root = self.project()
        repo = root / "code/alpha-api"
        path = repo / "service.py"
        path.unlink()
        path.symlink_to(self.case / "outside.py")
        with self.assertRaises(sources.MemoryInputError):
            sources.capture_code(repo)
        path.unlink()
        os.mkfifo(path)
        with self.assertRaises(sources.MemoryInputError):
            sources.capture_code(repo)
        path.unlink()
        path.write_text("x" * 101)
        with patch.object(sources, "MAX_FILE", 100), self.assertRaises(sources.MemoryInputError):
            sources.capture_code(repo)
        with patch.object(sources, "MAX_FILES", 1), self.assertRaises(sources.MemoryInputError):
            sources.capture_code(repo)

    def test_process_timeout_output_limit_and_log_separation(self):
        env = {"PATH": os.environ["PATH"]}
        rc, output = process.bounded_run([sys.executable, "-c", "import sys; print('log',file=sys.stderr); print('{}')"], env=env)
        self.assertEqual(rc, 0)
        self.assertEqual(output.strip(), b"{}")
        with self.assertRaisesRegex(sources.MemoryInputError, "output limit"):
            process.bounded_run([sys.executable, "-c", "print('x'*10000)"], env=env, limit=100)
        with self.assertRaisesRegex(sources.MemoryInputError, "timeout"):
            process.bounded_run([sys.executable, "-c", "import time; time.sleep(3)"], env=env, timeout=0.1)

    def test_missing_repository_appearing_after_capture_blocks_publish(self):
        root = self.project()
        self.bind(root, {API: "code/not-yet-present"})
        result = self.build(root, repositories=[API])
        (root / "code/not-yet-present").mkdir()
        with self.assertRaises(snapshots.ConcurrentChange):
            result.publish()

    def test_mutated_graph_cannot_be_published_under_original_input_id(self):
        result = self.build(self.project(), repositories=[API])
        result.graph["nodes"][0]["name"] = "different but schema-valid"
        with self.assertRaisesRegex(sources.MemoryInputError, "identities"):
            result.publish()

    def test_binding_and_provider_changes_block_publication(self):
        root = self.project()
        provider = base.FakeProvider()
        result = self.build(root, provider, repositories=[API])
        provider.available = False
        with self.assertRaises(snapshots.ConcurrentChange):
            result.publish()
        provider.available = True
        self.bind(root, {API: "elsewhere"})
        with self.assertRaises(snapshots.ConcurrentChange):
            result.publish()

    def test_unmerged_index_and_git_environment_do_not_change_selected_source(self):
        root = self.project()
        repo = root / "code/alpha-api"
        before = sources.capture_code(repo)
        with patch.dict(os.environ, {"GIT_DIR": "/not-this-repository", "GIT_WORK_TREE": "/not-this-worktree"}):
            self.assertEqual(before.inputs, sources.capture_code(repo).inputs)
        original = sources.git
        def unmerged(path, *args, **kwargs):
            data = original(path, *args, **kwargs)
            return data.replace(b" 0\t", b" 1\t") if args[0] == "ls-files" and "--stage" in args else data
        with patch.object(sources, "git", unmerged), self.assertRaisesRegex(sources.MemoryInputError, "merge stages"):
            sources.capture_code(repo)

    def test_nonstructural_and_indirect_evidence_is_retained_not_promoted(self):
        root = self.project()
        insight = record("route-like", relations=[dict(kind="has_method", target="hidden")])
        insight["kind"] = "route"
        insight["id"] = enola.fact_id(insight)
        result = self.build(root, base.FakeProvider(lambda _: base.Observation("available", [insight])), repositories=[API])
        self.assertEqual(len(result.graph["records"]), 1)
        self.assertFalse(any(n["name"] == "route-like" for n in result.graph["nodes"]))
        self.assertFalse(any(e["relation"] == "has_method" for e in result.graph["edges"]))
        self.assertEqual(result.graph["coverage"], "partial")
        self.assertTrue(any(p["code"] == "provider-evidence-not-projected" for p in result.graph["repositories"][0]["problems"]))

    def test_aggregate_dependency_is_raw_evidence_not_a_direct_edge(self):
        root = self.project()
        direct = record()
        aggregate = dict(kind="dependency", name="package rollup", file=".", repo="repository",
                         props=dict(derived="symbol-rollup", coupling_kind="symbol-rollup", symbol_edges=1),
                         relations=[dict(kind="imports", target=direct["name"], target_id=direct["id"])])
        aggregate["id"] = enola.fact_id(aggregate)
        result = self.build(root, base.FakeProvider(lambda _: base.Observation(
            "available", [direct, aggregate])), repositories=[API])
        self.assertEqual(len(result.graph["records"]), 2)
        self.assertFalse(any(n["name"] == aggregate["name"] for n in result.graph["nodes"]))
        self.assertFalse(any(e["relation"] == "imports" for e in result.graph["edges"]))
        self.assertEqual(result.graph["coverage"], "partial")
        result.publish()

    def test_code_publication_honors_lock_and_rejects_output_symlink(self):
        root = self.project()
        result = self.build(root, repositories=[API])
        result.publish()
        parent = root / "_meta/memory/code-snapshots"
        lock = parent / ".build.lock"
        lock.touch()
        with self.assertRaisesRegex(sources.MemoryInputError, "lock"):
            result.publish()
        self.assertTrue(lock.exists())
        second = self.project(destination="second")
        built = self.build(second, repositories=[API])
        (second / "_meta").mkdir()
        outside = self.case / "outside"
        outside.mkdir()
        (second / "_meta/memory").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(sources.MemoryInputError):
            built.publish()
        self.assertFalse(list(outside.iterdir()))


class StrictEnolaReader(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="enola-reader-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.files = {"service.py": b"def response():\n    return 1\n"}
        self.lock = enola.strict_json(enola.LOCK.read_bytes())["enola"]
        self.records = [record()]

    def write_output(self, records=None, **updates):
        raw = b"".join(models.canonical(r) for r in (self.records if records is None else records))
        insights = b"[]"
        receipt = dict(format_version=1, enola_version=self.lock["version"], extractor_version=self.lock["extractor_version"],
                       extractors=["python"], explainers=[], config_hash="sha256:test", ignore_glob_hash="sha256:test",
                       fact_count=len(self.records if records is None else records), insight_count=0,
                       output_hashes={"facts.jsonl": "sha256:" + models.digest(raw), "insights.json": "sha256:" + models.digest(insights)},
                       quality=dict(files_seen=1, files_parsed=1, files_skipped=0, dirs_skipped=0, parse_errors=0, heuristic_insights=0,
                                    census=dict(files_walked=1, parsed=1, excluded_by_ignore=0, excluded_by_kind=0, skipped_with_cause=0)))
        receipt["snapshot_id"] = "sha256:" + models.digest(raw + self.lock["version"].encode() + receipt["config_hash"].encode())
        receipt.update(updates)
        (self.root / "facts.jsonl").write_bytes(raw)
        (self.root / "insights.json").write_bytes(insights)
        (self.root / "receipt.json").write_bytes(models.canonical(receipt))

    def read(self):
        return enola.read_output(self.root, self.files, self.lock)

    def test_valid_stream_and_duplicate_evidence(self):
        self.write_output(self.records * 2)
        self.assertEqual(len(self.read()["records"]), 2)

    def test_directory_dependency_is_bounded_and_has_no_source_position(self):
        self.files = {"pkg/use.py": b"import json\n"}
        dependency = dict(kind="dependency", name="module-edge: pkg -> other", file="pkg", repo="repository",
                          relations=[], props=dict(derived="symbol-rollup", coupling_kind="symbol-rollup", symbol_edges=1))
        dependency["id"] = enola.fact_id(dependency)
        self.write_output([dependency])
        self.assertEqual(self.read()["records"], [dependency])
        for changes in (dict(file="outside"), dict(kind="symbol"), dict(line=1), dict(column=1),
                        dict(end_line=1), dict(end_column=1), dict(file="../pkg"), dict(props={}),
                        dict(props=dict(derived="symbol-rollup", coupling_kind="symbol-rollup", symbol_edges=True))):
            invalid = dict(dependency, **changes)
            invalid["id"] = enola.fact_id(invalid)
            self.write_output([invalid])
            with self.subTest(changes=changes), self.assertRaises((ValueError, sources.MemoryInputError)):
                self.read()

    def test_receipt_missing_unknown_format_versions_counts_and_hashes_rejected(self):
        for values in (dict(format_version=99), dict(format_version=True), dict(enola_version="dev"),
                       dict(extractor_version="unknown"), dict(fact_count=5), dict(insight_count=1),
                       dict(output_hashes={}), dict(snapshot_id="sha256:wrong"), dict(providers=[{"name": "unsafe"}])):
            with self.subTest(values=values):
                self.write_output(**values)
                with self.assertRaises((ValueError, sources.MemoryInputError)):
                    self.read()
        self.write_output()
        (self.root / "receipt.json").unlink()
        with self.assertRaises(ValueError):
            self.read()

    def test_corrupt_json_duplicate_keys_and_nonfinite_are_rejected(self):
        for data in (b'{"id":1,"id":2}', b'{"x":NaN}', b'{bad'):
            with self.assertRaises(ValueError):
                enola.strict_json(data)
        self.write_output()
        (self.root / "facts.jsonl").write_bytes(b"invalid\n")
        with self.assertRaises(ValueError):
            self.read()

    def test_invalid_id_label_path_and_location_are_rejected(self):
        for changes in (dict(id="bad"), dict(repo="other"), dict(file="../escape.py"), dict(line=100),
                        dict(line=True), dict(end_line=0), dict(kind="surprise")):
            changed = dict(record(), **changes)
            if "id" not in changes:
                changed["id"] = enola.fact_id(changed)
            self.write_output([changed])
            with self.subTest(changes=changes), self.assertRaises((ValueError, sources.MemoryInputError)):
                self.read()

    def test_timestamp_duration_and_private_path_never_enter_evidence(self):
        self.write_output(generated_at="now", duration="1s", repo_path="/private/checkout", git={"remote": "secret"})
        first = self.read()
        self.write_output(generated_at="later", duration="2s", repo_path="/another/checkout")
        self.assertEqual(first, self.read())
        self.assertNotIn("private", json.dumps(first))

    def test_absent_or_unpinned_binary_never_executes(self):
        missing = enola.EnolaProvider()
        with patch.object(enola, "bounded_run", side_effect=AssertionError("must not execute")):
            self.assertEqual(missing.extract(self.files).status, "unavailable")
            binary = self.root / "unknown"
            binary.write_bytes(b"not a trusted executable")
            self.assertEqual(enola.EnolaProvider(binary).extract(self.files).status, "unavailable")

    def test_syntax_guard_never_executes_or_indexes_invalid_sources(self):
        provider = enola.EnolaProvider()
        with patch.object(provider, "status", return_value={"status": "available"}), patch.object(enola, "bounded_run", side_effect=AssertionError("must not execute")):
            result = provider.extract({"broken.py": b"def broken(:\n return missing(\n"})
        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.records, [])
        self.assertEqual(result.problems[0]["code"], "parse-error")

    def test_integration_inventory_is_generated_from_lock(self):
        run = subprocess.run([sys.executable, "-B", str(ROOT / "third_party/inventory.py"), "--check"],
                             capture_output=True, text=True, timeout=15)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        lock = json.loads((ROOT / "providers.lock.json").read_text())
        inventory = json.loads((ROOT / "third_party/inventory.json").read_text())
        self.assertEqual(inventory["providers"]["enola"], lock["enola"])
        # The optional browser renderer is now redistributed; Enola and grammars are not.
        self.assertEqual([r["name"] for r in inventory["incorporated_code"]], ["cytoscape"])
        self.assertEqual(inventory["incorporated_code"][0]["integration"], "optional-offline-viewer-only")

    def test_inconsistent_census_is_rejected(self):
        self.write_output()
        path = self.root / "receipt.json"
        receipt = json.loads(path.read_text())
        receipt["quality"]["census"]["parsed"] = 2
        path.write_bytes(models.canonical(receipt))
        with self.assertRaisesRegex(ValueError, "census"):
            self.read()


if __name__ == "__main__":
    unittest.main()
