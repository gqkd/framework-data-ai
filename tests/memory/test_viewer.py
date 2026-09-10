"""Offline viewer: synthetic sources only, no browser/network required by these tests."""
from copy import deepcopy
import base64
import hashlib
from html import unescape
import importlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

import test_code_provider as cp
import test_documentary as doc
from test_phase0 import ROOT, fixture, content_hashes

viewer = importlib.import_module(cp.v._CORE_NAME + ".memory.viewer")
io = importlib.import_module(cp.v._CORE_NAME + ".memory.operational_io")


class Viewer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="viewer-fixtures-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.fixtures = Path(cls.temp.name) / "fixtures"
        fixture.build(cls.fixtures)
        cls.overlays = yaml.safe_load((ROOT / "tests/fixtures/memory/phase2-metadata.yaml").read_text())

    def setUp(self):
        self.case = tempfile.TemporaryDirectory(prefix="viewer-case-")
        self.addCleanup(self.case.cleanup)
        self.root = Path(self.case.name) / "project"
        shutil.copytree(self.fixtures / "multi-repo", self.root)
        for path, fields in self.overlays["multi-repo"].items():
            doc.amend(self.root / path, **fields)
        bindings = {cp.API: "code/alpha-api", cp.WORKER: "code/beta-worker", cp.RULES: "code/shared-rules"}
        cp.CodeMemory.bind(self, self.root, bindings)

    def build(self):
        s = cp.snapshots.capture(self.root)
        return s, cp.graphs.build(s)

    def code(self, provider=None):
        s, g = self.build()
        result = cp.code.build_code(s, g, provider or cp.base.FakeProvider())
        return dict(graph=result.graph, inputs=result.inputs)

    def test_export_is_atomic_deterministic_and_only_writes_derived_html(self):
        s, g = self.build()
        before = content_hashes(self.root)
        dry = viewer.export(s, g, dry_run=True)
        self.assertEqual(before, content_hashes(self.root))
        report = viewer.export(s, g)
        again = viewer.export(s, g)
        self.assertEqual(report, again)
        self.assertEqual(dry["id"], report["id"])
        target = self.root / report["output"]
        manifest = json.loads(target.with_name("manifest.json").read_bytes())
        self.assertEqual(manifest["files"], {"index.html": cp.models.digest(target.read_bytes())})
        self.assertEqual(manifest["id"], cp.models.digest(cp.models.canonical(manifest["inputs"])))
        after = content_hashes(self.root)
        self.assertEqual(before, {p:after[p] for p in before})
        self.assertEqual(set(after)-set(before), {report["output"], str(Path(report["output"]).with_name("manifest.json"))})

    def test_existing_export_is_never_overwritten(self):
        s, g = self.build()
        report = viewer.export(s, g)
        target = self.root / report["output"]
        target.write_text("tampered")
        with self.assertRaisesRegex(doc.workspace.MemoryInputError, "refusing to overwrite"):
            viewer.export(s, g)
        self.assertEqual(target.read_text(), "tampered")

    def test_document_only_and_optional_provider_unavailable_are_distinct(self):
        root = Path(self.case.name) / "document-only"
        shutil.copytree(self.fixtures / "document-only", root)
        s = cp.snapshots.capture(root)
        g = cp.graphs.build(s)
        data = viewer.model(s, g)
        self.assertIsNone(data["code"])
        self.assertFalse(data["mapping_compatible"])
        unavailable = self.code(cp.base.FakeProvider(available=False))
        s, g = self.build()
        data = viewer.model(s, g, code=unavailable)
        self.assertEqual(data["code"]["coverage"], "unavailable")
        self.assertTrue(any("no absence-of-impact" in w for w in data["warnings"]))

    def test_compatible_mapping_preserves_both_graphs_without_mutation(self):
        code = self.code()
        s, g = self.build()
        before = cp.models.canonical([g, code])
        data = viewer.model(s, g, code=code)
        self.assertTrue(data["mapping_compatible"])
        self.assertTrue(data["bridges"])
        self.assertEqual(data["document"], g)
        self.assertEqual(data["code"], code["graph"])
        self.assertEqual(before, cp.models.canonical([g,code]))

    def test_revision_mismatch_disables_only_presentation_bridges(self):
        code = self.code()
        p = self.root / "products/alpha/PBR.md"
        p.write_text(p.read_text() + "\nA new documentary revision.\n")
        s, g = self.build()
        data = viewer.model(s, g, code=code)
        self.assertFalse(data["mapping_compatible"])
        self.assertEqual(data["bridges"], [])
        self.assertTrue(any("revisions differ" in w for w in data["warnings"]))
        self.assertEqual(data["code"], code["graph"])

    def test_wrong_namespace_is_rejected(self):
        code = self.code()
        doc.config(self.root, document_repository="different")
        s, g = self.build()
        with self.assertRaisesRegex(doc.workspace.MemoryInputError, "namespace"):
            viewer.model(s, g, code=code)

    def test_forged_bridge_even_in_self_consistent_bundle_is_rejected(self):
        code = self.code()
        code["graph"]["bridges"][0]["declaration"]["rule"]["version"] = "forged"
        code["inputs"]["normalized_observation"] = cp.models.digest(cp.models.canonical(dict(code["graph"],snapshot="")))
        code["graph"]["snapshot"] = cp.models.digest(cp.models.canonical(code["inputs"]))
        s, g = self.build()
        with self.assertRaises((doc.workspace.MemoryInputError, cp.jsonschema.ValidationError)):
            viewer.model(s, g, code=code)

    def test_no_private_bindings_or_code_bodies_are_exported(self):
        code = self.code()
        s, g = self.build()
        data = viewer.model(s, g, code=code)
        text = cp.models.canonical(data).decode()
        self.assertNotIn(str(self.root), text)
        self.assertNotIn(".framework-memory/local.yaml", text)
        self.assertEqual(set(data["source_text"]), {r["id"] for r in g["sources"]})
        self.assertTrue(all(r["id"] not in data["source_text"] for r in code["graph"]["sources"]))

    def test_filtered_documents_never_enter_export(self):
        path = self.root / "products/alpha/PBR.md"
        doc.amend(path, classification="confidential")
        path.write_text(path.read_text() + "\nVIEWER_SECRET_SENTINEL\n")
        s, g = self.build()
        html = viewer.render(viewer.model(s,g), viewer.assets())
        self.assertNotIn(b"VIEWER_SECRET_SENTINEL", html)

    def test_inferred_hypotheses_require_selected_source_and_line_bounds(self):
        s, g = self.build()
        source = g["sources"][0]
        hypothesis = dict(claim="Synthetic hypothesis", provenance=dict(source_kind="document",assertion_method="inferred",
            sources=[dict(source=source["id"],start_line=1,end_line=1)], confidence=0.6,rationale="Synthetic fixture"))
        data = viewer.model(s,g,hypotheses=[hypothesis])
        self.assertEqual(data["hypotheses"], [hypothesis])
        self.assertFalse(any(e["provenance"]["assertion_method"] == "inferred" for e in data["document"]["edges"]))
        hypothesis["provenance"]["sources"][0]["end_line"] = source["lines"] + 1
        with self.assertRaises(doc.workspace.MemoryInputError):
            viewer.model(s,g,hypotheses=[hypothesis])

    def test_script_terminators_are_data_and_executable_hashes_match_csp(self):
        s, g = self.build()
        data = viewer.model(s,g)
        sentinel = '</script><script>globalThis.pwned=true</script>&\u2028\u2029'
        key = next(iter(data["source_text"]))
        data["source_text"][key] = sentinel
        html = viewer.render(data,viewer.assets()).decode()
        block = re.search(r'<script id="memory-data" type="application/json">(.*?)</script>',html,re.S)[1]
        self.assertNotIn("<",block)
        self.assertEqual(json.loads(block)["source_text"][key],sentinel)
        scripts = re.findall(r"<script>(.*?)</script>",html,re.S)
        self.assertEqual(len(scripts),3)
        for script in scripts:
            expected = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
            self.assertIn("sha256-"+expected,unescape(html))
        self.assertIn("connect-src 'none'",unescape(html))
        self.assertNotIn("<script src=",html)
        self.assertNotIn("unsafe-eval",unescape(html).split('content="')[1].split('"')[0])

    def test_asset_change_changes_export_id_but_not_document_graph(self):
        s, g = self.build()
        before = viewer.export(s,g,dry_run=True)
        content = viewer.assets()
        content["assets/memory-viewer/style.css"] += b"\n/* fixture */"
        with patch.object(viewer,"assets",return_value=content):
            after = viewer.export(s,g,dry_run=True)
        self.assertNotEqual(before["id"],after["id"])
        self.assertEqual(before["document_snapshot"],after["document_snapshot"])

    def test_dependency_tampering_and_missing_viewer_fail_closed(self):
        package = Path(self.case.name) / "package"
        shutil.copytree(ROOT / "assets", package / "assets")
        shutil.copytree(ROOT / "third_party", package / "third_party")
        for name in ("LICENSE", "NOTICE"):
            shutil.copy2(ROOT / name, package / name)
        with patch.object(viewer,"FRAMEWORK",package):
            viewer.assets()
            (package / "third_party/cytoscape/dist/cytoscape.min.js").write_text("modified")
            with self.assertRaisesRegex(doc.workspace.MemoryInputError,"checksum"):
                viewer.assets()
        with patch.object(viewer,"FRAMEWORK",Path(self.case.name)/"absent"):
            with self.assertRaises(OSError):
                viewer.assets()

    def test_byte_limit_and_symlink_output_fail_closed(self):
        s, g = self.build()
        with patch.object(viewer,"MAX_HTML_BYTES",10):
            with self.assertRaisesRegex(doc.workspace.MemoryInputError,"25 MB"):
                viewer.export(s,g)
        base = self.root / "_meta/memory"
        base.mkdir(parents=True,exist_ok=True)
        elsewhere = Path(self.case.name) / "elsewhere"
        elsewhere.mkdir()
        (base / "views").symlink_to(elsewhere,target_is_directory=True)
        with self.assertRaises(doc.workspace.MemoryInputError):
            viewer.export(s,g)
        self.assertFalse(list(elsewhere.iterdir()))

    def test_publisher_cannot_use_html_in_existing_snapshot_namespaces(self):
        for namespace, payload in [("snapshots",{"index.html":b"x"}),("views",{"other.html":b"x"})]:
            with self.assertRaises(doc.workspace.MemoryInputError):
                cp.snapshots.publish_payload(self.root,namespace,"a"*64,payload,lambda:None)

    def test_cli_and_loaded_code_bundle(self):
        built = cp.code.build_code(*self.build(), cp.base.FakeProvider())
        built.publish()
        bundle = self.root / "_meta/memory/code-snapshots" / built.graph["snapshot"]
        # Synthetic snapshots are coherent before serialization as well as after loading.
        io.load_code(bundle)
        run = subprocess.run([sys.executable,"-B",str(ROOT/"memory.py"),"view","--root",str(self.root),
                              "--code-snapshot",str(bundle),"--dry-run"],capture_output=True,text=True,timeout=30)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        report = json.loads(run.stdout)
        self.assertEqual(report["code_observation"],"captured-not-rechecked")
        self.assertFalse(report["written"])


if __name__ == "__main__":
    unittest.main()
