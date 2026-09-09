"""Phase-six release proofs on synthetic Git histories; no real build/deploy claims."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

import test_authority as helpers
from test_phase0 import ROOT, fixture
from test_references import v, amend

releases = importlib.import_module(v._CORE_NAME + ".release_evidence")
sets = importlib.import_module(v._CORE_NAME + ".release_sets")
models = helpers.models
API = "repository:product:alpha:api"
WORKER = "repository:product:alpha:worker"
RLM = "products/alpha/releases/RLM-001-candidate.yaml"
EVR = "products/alpha/releases/EVR-001-candidate.md"
REL = "products/alpha/releases/REL-001-candidate.md"
PLAN = "products/alpha/EVP.md"


class ReleaseEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reuse fixture setup, not its test class (which would rerun unrelated tests).
        helpers.ContributionAuthority.setUpClass.__func__(cls)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="release-case-")
        self.addCleanup(temporary.cleanup)
        self.case = Path(temporary.name)
        self.docs = self.case / "documents"
        shutil.copytree(self.shared / "fixtures/qualified-impact", self.docs)
        config = yaml.safe_load((self.docs / "framework.yaml").read_text())
        config["framework_commit"] = self.pin
        fixture.write(self.docs, "framework.yaml", yaml.safe_dump(config))
        amend(self.docs / fixture.ICG, impacts={"SIG-001": ["ai"]})
        builder = fixture.Documents(self.docs)
        self.code, declarations, observed, revisions = {}, {}, {}, {}
        for key in ("api", "worker"):
            rid = "repository:product:alpha:" + key
            fixture.code_repository(self.case, key, {"service.py": "VALUE = 1\n"})
            root = self.case / key
            if key == "worker":
                fixture.git(root, "branch", "-m", "master")
            revision = fixture.git(root, "rev-parse", "HEAD")
            remote = "https://example.invalid/synthetic/" + key
            self.code[rid] = root
            declarations[key] = dict(url=remote, contains="Synthetic code", release_relevant="true")
            revisions[rid] = dict(commit=revision, build_digest="sha256:" + ("a" if key == "api" else "b") * 64)
            observed[rid] = dict(root=str(root), repository=remote, default_branch="master" if key == "worker" else "main",
                                 approved_tip=revision)
        amend(self.docs / "products/alpha/product.yaml", code=declarations)
        builder.artifact(PLAN, "evaluation-plan", "# Frozen synthetic plan\nA score of at least 0.9 is mandatory.",
                         products=["alpha"], version="1.0.0")
        fixture.git(self.docs, "init", "--initial-branch=main", "--template=")
        self.frozen = self.commit_docs()
        self.manifest = dict(release_set=dict(version=1, repositories=revisions, dependencies=[]),
                             release_note="REL-001", config=dict(hash="config-one"),
                             infrastructure=dict(version="infra-one", target="production"),
                             ai=dict(model="synthetic", prompt_hash="prompt-one"), data=dict(eval_dataset_version="fixture-1"),
                             evaluation=dict(report="EVR-001", evp_version="1.0.0", evp_hash=models.digest((self.docs / PLAN).read_bytes()), verdict="go"),
                             changes=dict(contracts=["CHG-001"], decisions=[]), rollback=dict(target="RLM-000", tested=True))
        builder.artifact(EVR, "evaluation-report", "# Evaluation\nSynthetic fixture result, not an actual model execution.",
                         lifecycle="immutable", id="EVR-001", products=["alpha"], derives_from=["EVP"],
                         evp_version="1.0.0", evp_hash=self.manifest["evaluation"]["evp_hash"], frozen_at=self.frozen,
                         verified_code={"product." + rid.rsplit(":", 1)[1]: row["commit"] for rid, row in revisions.items()})
        builder.artifact(REL, "release-note", "# Prepared synthetic release\nNot yet observed in production.",
                         lifecycle="immutable", id="REL-001", products=["alpha"], derives_from=["CHG-001", "EVR-001"])
        self.control = dict(schema="framework-memory/release-input/v1", framework_commit=self.pin,
                            documents=dict(repository="synthetic/documents", root=str(self.docs), commit=self.frozen, approved_tip=self.frozen),
                            manifest=RLM, stage="prepared", classifications=["public", "internal"], exclude=[],
                            repositories=observed, receipts=[])
        self.save()

    def commit_docs(self):
        fixture.git(self.docs, "add", "--all")
        fixture.git(self.docs, "commit", "--allow-empty", "-m", "Synthetic release evidence")
        return fixture.git(self.docs, "rev-parse", "HEAD")

    def index(self):
        registry = helpers.authority.mapping((ROOT / "schemas/artifact-types.yaml").read_bytes())
        arts = v.discover(self.docs, v.load_scan(registry, v.load_project(self.docs)), registry, v.Report({}))
        return {a.rel: a for a in arts}, v.ReferenceIndex(arts, registry)

    def save(self, *, refresh_identity=True):
        # All artifacts here are disposable fixtures; no historical source is rewritten.
        builder = fixture.Documents(self.docs)
        builder.artifact(RLM, "release-manifest", "", lifecycle="immutable", id="RLM-001",
                         generated_by="synthetic-fixture", products=["alpha"], **self.manifest)
        if refresh_identity:
            arts, index = self.index()
            self.identity = sets.normalize(arts[RLM], index)["hash"]
            amend(self.docs / EVR, release_set_hash=self.identity)
        revision = self.commit_docs()
        self.control["documents"].update(commit=revision, approved_tip=revision)
        self.make_receipts()

    def make_receipts(self, stages=("pre-release", "integration"), modify=None):
        self.control["receipts"] = []
        for stage in stages:
            receipt = dict(schema="framework-memory/release-receipt/v1", stage=stage,
                           producer="synthetic-ci/" + stage, run="synthetic-run-1",
                           document=dict(repository="synthetic/documents", commit=self.control["documents"]["commit"]),
                           manifest=RLM, report=EVR, release_set_hash=self.identity, result="passed", exit_code=0)
            if stage == "deployment":
                receipt.update(environment="production", observed_set_hash=self.identity, observed_at="2026-06-09T12:00:00Z")
            if modify:
                modify(receipt)
            path = self.case / (stage + ".json")
            path.write_bytes(models.canonical(receipt))
            self.control["receipts"].append(dict(path=str(path), digest=models.digest(models.canonical(receipt)),
                                                producer="synthetic-ci/" + stage, run="synthetic-run-1", stage=stage))

    def run_gate(self):
        result = releases.evaluate(self.control, v, framework_root=self.runtime)
        models.validate("release-report", result)
        return result

    def codes(self):
        return {f["code"] for f in self.run_gate()["findings"]}

    def test_candidate_preparation_is_not_deployment_and_default_branch_is_not_assumed_main(self):
        result = self.run_gate()
        self.assertEqual(result["gate"], "passed", result)
        self.assertEqual(result["supported_state"], "implemented")
        self.assertEqual(result["deployment_observation"], "not-observed")
        self.assertFalse(result["status_changed"])
        self.assertFalse(result["deployment_executed"])
        self.assertFalse(result["atomic"])
        self.assertEqual(self.control["repositories"][WORKER]["default_branch"], "master")

    def test_verified_requires_independent_observation_and_smoke(self):
        self.control["stage"] = "verified"
        self.assertIn("RLS004", self.codes())
        self.make_receipts(("pre-release", "integration", "deployment"))
        result = self.run_gate()
        self.assertEqual(result["gate"], "passed", result)
        self.assertEqual(result["supported_state"], "verified")
        self.assertTrue(result["review_required"])

    def test_generated_manifest_alone_has_no_execution_evidence(self):
        self.control["receipts"] = []
        self.assertIn("RLS004", self.codes())
        self.assertEqual(self.run_gate()["supported_state"], "not-established")

    def test_code_change_does_not_reuse_old_evr(self):
        self.manifest["release_set"]["repositories"][WORKER]["commit"] = "c" * 40
        self.save(refresh_identity=False)
        self.assertEqual(self.run_gate()["gate"], "failed")

    def test_matching_code_with_old_build_config_ai_data_or_target_is_not_same_candidate(self):
        original = deepcopy(self.manifest)
        for modify in (
            lambda m: m["release_set"]["repositories"][API].update(build_digest="sha256:" + "d" * 64),
            lambda m: m["config"].update(hash="new-config"),
            lambda m: m["ai"].update(prompt_hash="new-prompt"),
            lambda m: m["data"].update(eval_dataset_version="new-dataset"),
            lambda m: m["infrastructure"].update(target="another-environment"),
        ):
            with self.subTest(modify=modify):
                self.manifest = deepcopy(original)
                modify(self.manifest)
                self.save(refresh_identity=False)
                self.assertEqual(self.run_gate()["gate"], "failed")

    def test_stale_forged_failed_or_missing_receipts_never_pass(self):
        mutations = (
            lambda r: r.update(release_set_hash="0" * 64),
            lambda r: r["document"].update(commit=self.frozen),
            lambda r: r.update(report="products/alpha/releases/EVR-002-other.md"),
            lambda r: r.update(manifest="products/alpha/releases/RLM-002-other.yaml"),
            lambda r: r.update(result="failed", exit_code=1),
            lambda r: r.update(run="another-run"),
            lambda r: r.update(producer="pr-author"),
        )
        for modify in mutations:
            with self.subTest(modify=modify):
                self.make_receipts(modify=modify)
                self.assertIn("RLS004", self.codes())
        self.make_receipts()
        self.control["receipts"][0]["digest"] = "0" * 64
        self.assertIn("RLS004", self.codes())
        self.make_receipts()
        self.control["receipts"].append(self.control["receipts"][0])
        self.assertIn("RLS004", self.codes())

    def test_unobserved_consumer_is_not_a_pass(self):
        self.control["repositories"].pop(WORKER)
        self.assertIn("RLS006", self.codes())

    def test_wrong_repository_identity_and_unavailable_history_fail_closed(self):
        self.control["repositories"][API]["repository"] = "https://example.invalid/wrong"
        self.assertIn("RLS003", self.codes())
        self.control["repositories"][API]["root"] = str(self.case / "missing")
        self.assertEqual(self.run_gate()["gate"], "failed")

    def test_unmerged_candidate_can_be_prepared_but_not_implemented(self):
        root = self.code[API]
        fixture.write(root, "service.py", "VALUE = 2\n")
        fixture.git(root, "add", "--all")
        fixture.git(root, "commit", "-m", "Synthetic not-yet-merged candidate")
        revision = fixture.git(root, "rev-parse", "HEAD")
        self.manifest["release_set"]["repositories"][API]["commit"] = revision
        arts, _ = self.index()
        measured = arts[EVR].meta["verified_code"]
        amend(self.docs / EVR, verified_code={**measured, "product.api": revision})
        self.save()
        self.assertEqual(self.run_gate()["supported_state"], "prepared")
        self.control["stage"] = "implemented"
        self.assertIn("RLS006", self.codes())

    def test_verified_chg_cannot_be_laundered_by_requesting_prepared(self):
        amend(self.docs / fixture.CHG, status="verified", verified_by="EVR-001")
        self.save()
        self.assertEqual(self.control["stage"], "prepared")
        self.assertIn("RLS004", self.codes())
        self.make_receipts(("pre-release", "integration", "deployment"))
        self.assertEqual(self.run_gate()["gate"], "passed")

    def test_revoked_contract_and_wrong_closure_evaluation_block(self):
        amend(self.docs / fixture.CHG, status="rolled-back")
        self.save()
        self.assertIn("RLS006", self.codes())
        amend(self.docs / fixture.CHG, status="verified", verified_by="EVR-002")
        self.save()
        self.make_receipts(("pre-release", "integration", "deployment"))
        self.assertIn("RLS002", self.codes())

    def test_wrong_environment_partial_observation_or_failed_smoke_is_not_verified(self):
        self.control["stage"] = "verified"
        for field, value in (("environment", "staging"), ("observed_set_hash", "0" * 64),
                             ("observed_at", "2026-06-09T12:00:00"), ("result", "failed")):
            with self.subTest(field=field):
                self.make_receipts(("pre-release", "integration", "deployment"),
                    lambda r: r.update({field: value}) if r["stage"] == "deployment" else None)
                self.assertEqual(self.run_gate()["gate"], "failed")

    def test_evr_must_cover_every_required_repository_and_the_frozen_plan(self):
        arts, _ = self.index()
        measured = arts[EVR].meta["verified_code"]
        amend(self.docs / EVR, verified_code={"product.api": measured["product.api"]})
        self.save()
        self.assertEqual(self.run_gate()["gate"], "failed")
        amend(self.docs / EVR, verified_code=measured, evp_hash="0" * 64)
        self.manifest["evaluation"]["evp_hash"] = "0" * 64
        self.save()
        self.assertIn("RLS003", self.codes())

    def test_release_note_must_describe_the_same_changes(self):
        amend(self.docs / REL, derives_from=["EVR-001"])
        self.save()
        self.assertIn("RLS002", self.codes())

    def test_current_plan_change_does_not_rewrite_or_substitute_frozen_plan(self):
        amend(self.docs / PLAN, version="2.0.0")
        self.save()
        self.assertEqual(self.run_gate()["gate"], "passed")

    def test_classification_filter_does_not_export_private_evidence(self):
        amend(self.docs / EVR, classification="confidential")
        with (self.docs / EVR).open("a") as stream:
            stream.write("\nPRIVATE_SENTINEL\n")
        self.save()
        result = self.run_gate()
        self.assertEqual(result["gate"], "failed")
        self.assertNotIn("PRIVATE_SENTINEL", models.canonical(result).decode())

    def test_unclassified_generated_manifest_is_readable_without_broadening_other_sources(self):
        amend(self.docs / RLM, classification=None)
        revision = self.commit_docs()
        self.control["documents"].update(commit=revision, approved_tip=revision)
        self.make_receipts()
        self.assertEqual(self.run_gate()["gate"], "passed")

    def test_new_metadata_is_optional_and_legacy_scalar_is_not_broadcast(self):
        arts, index = self.index()
        source = deepcopy(arts[RLM])
        row = self.manifest["release_set"]["repositories"][API]
        source.meta.pop("release_set")
        source.meta.update(code=dict(commit=row["commit"]), build=dict(image_digest=row["build_digest"]))
        with self.assertRaises(helpers.authority.MemoryInputError):
            sets.normalize(source, index)
        report = v.Report({})
        sets.check([source], helpers.authority.mapping((ROOT / "schemas/artifact-types.yaml").read_bytes()), report)
        self.assertEqual(report.findings, [])
        manifest = arts["products/alpha/product.yaml"]
        manifest.meta["code"].pop("worker")
        index = v.ReferenceIndex(list(arts.values()), helpers.authority.mapping((ROOT / "schemas/artifact-types.yaml").read_bytes()))
        original = deepcopy(source.meta)
        normalized = sets.normalize(source, index)
        self.assertEqual(normalized["origin"], "legacy-single-repository")
        self.assertEqual(set(normalized["payload"]["repositories"]), {API})
        self.assertEqual(source.meta, original)

    def test_duplicate_legacy_and_new_authorities_are_rejected(self):
        self.manifest["code"] = dict(commit=self.manifest["release_set"]["repositories"][API]["commit"])
        self.save(refresh_identity=False)
        self.assertEqual(self.run_gate()["gate"], "failed")

    def test_normalized_identity_is_order_independent_and_not_a_wall_clock(self):
        arts, index = self.index()
        first = sets.normalize(arts[RLM], index)
        arts[RLM].meta["release_set"]["repositories"] = dict(reversed(list(arts[RLM].meta["release_set"]["repositories"].items())))
        arts[RLM].meta["created"] = "2029-01-01 00:00"
        second = sets.normalize(arts[RLM], index)
        self.assertEqual(first["hash"], second["hash"])

    def test_cli_from_committed_export_does_not_write_or_execute_sources(self):
        control = self.case / "control.json"
        control.write_bytes(models.canonical(self.control))
        before = (self.docs / RLM).read_bytes()
        fixture.write(self.code[API], "service.py", "raise SystemExit('must not execute')\n")
        command = [sys.executable, "-I", "-B", str(self.runtime / "skills/audit/scripts/validate.py"),
                   "--profile", "strict-release", "--trust-input", str(control), "--json"]
        run = subprocess.run(command, cwd=self.case, capture_output=True, text=True, timeout=40)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(json.loads(run.stdout)["supported_state"], "implemented")
        self.assertEqual((self.docs / RLM).read_bytes(), before)
        run = subprocess.run(command + ["--emit-index"], capture_output=True, text=True, timeout=20)
        self.assertNotEqual(run.returncode, 0)
        self.assertFalse((self.docs / "TRACEABILITY.md").exists())

    def add_dependency(self):
        builder = fixture.Documents(self.docs)
        builder.manifest("beta")
        rid = "repository:platform:identity"
        fixture.code_repository(self.case, "identity", {"identity.py": "VERSION = 1\n"})
        root = self.case / "identity"
        revision = fixture.git(root, "rev-parse", "HEAD")
        remote = "https://example.invalid/synthetic/identity"
        builder.artifact("PLATFORM.md", "platform-architecture", "# Shared synthetic release",
                         code={"identity": dict(url=remote, contains="Synthetic shared service", used_by=["alpha", "beta"])})
        self.control["repositories"][rid] = dict(repository=remote, root=str(root), default_branch="main", approved_tip=revision)
        plan_path = "products/beta/EVP.md"
        builder.artifact(plan_path, "evaluation-plan", "# Shared release plan\nRequired compatibility tests.", products=["beta"], version="1.0.0")
        condition = "products/alpha/contracts/DC-090-compatibility.md"
        builder.artifact(condition, "data-contract", "# Compatibility\n<!-- section: compatibility -->\n## Condition\nProtocol one.",
                         id="DC-090", products=["alpha"], version="1.0.0")
        frozen = self.commit_docs()
        child = "products/beta/releases/RLM-002-shared.yaml"
        child_evr = "products/beta/releases/EVR-002-shared.md"
        payload = deepcopy(self.manifest)
        payload.update(release_set=dict(version=1, repositories={rid: dict(commit=revision, build_digest="sha256:" + "e" * 64)}, dependencies=[]),
                       release_note="REL-002", changes=dict(contracts=[], decisions=[]),
                       evaluation=dict(report="EVR-002", evp_version="1.0.0", evp_hash=models.digest((self.docs / plan_path).read_bytes()), verdict="go"))
        builder.artifact(child, "release-manifest", "", lifecycle="immutable", id="RLM-002", products=["beta"], generated_by="fixture", **payload)
        builder.artifact(child_evr, "evaluation-report", "# Shared evaluation\nSynthetic, not executed.",
                         lifecycle="immutable", id="EVR-002", products=["beta"], evp_version="1.0.0",
                         evp_hash=payload["evaluation"]["evp_hash"], frozen_at=frozen, verified_code={"platform.identity": revision})
        builder.artifact("products/beta/releases/REL-002-shared.md", "release-note", "# Shared release",
                         lifecycle="immutable", id="REL-002", products=["beta"], derives_from=["EVR-002"])
        arts, index = self.index()
        identity = sets.normalize(arts[child], index)["hash"]
        amend(self.docs / child_evr, release_set_hash=identity)
        self.manifest["release_set"]["dependencies"] = [dict(manifest=child, release_set_hash=identity,
                       compatibility=dict(path=condition, sha256=models.digest((self.docs / condition).read_bytes()), section="compatibility"))]
        self.save()
        return child, condition, rid

    def test_shared_release_requires_transitive_code_and_compatibility_source(self):
        child, _, rid = self.add_dependency()
        result = self.run_gate()
        self.assertEqual(result["gate"], "passed", result)
        self.assertEqual(result["dependencies"], [child])
        self.control["repositories"].pop(rid)
        self.assertIn("RLS006", self.codes())

    def test_dependency_identity_and_compatibility_marker_cannot_drift(self):
        self.add_dependency()
        dependency = self.manifest["release_set"]["dependencies"][0]
        original = deepcopy(dependency)
        for key, value in (("release_set_hash", "0" * 64),):
            dependency[key] = value
            self.save()
            self.assertIn("RLS007", self.codes())
        self.manifest["release_set"]["dependencies"] = [original]
        original["compatibility"]["section"] = "absent-marker"
        self.save()
        self.assertIn("RLS007", self.codes())

    def test_missing_private_or_changed_compatibility_source_blocks(self):
        _, condition, _ = self.add_dependency()
        amend(self.docs / condition, classification="confidential")
        self.save()
        self.assertIn("RLS007", self.codes())

    def test_dependency_cycle_is_bounded_and_unavailable_not_a_pass(self):
        child, _, _ = self.add_dependency()
        arts, _ = self.index()
        child_set = deepcopy(arts[child].meta["release_set"])
        dependency = deepcopy(self.manifest["release_set"]["dependencies"][0])
        dependency.update(manifest=child, release_set_hash="0" * 64)
        child_set["dependencies"] = [dependency]
        amend(self.docs / child, release_set=child_set)
        arts, index = self.index()
        amend(self.docs / "products/beta/releases/EVR-002-shared.md", release_set_hash=sets.normalize(arts[child], index)["hash"])
        self.save()
        self.assertEqual(self.run_gate()["gate"], "failed")

    def test_latest_revocation_and_changed_rule_bytes_cannot_be_hidden_by_older_base(self):
        amend(self.docs / fixture.CHG, status="rolled-back")
        self.control["documents"]["approved_tip"] = self.commit_docs()
        self.assertIn("RLS006", self.codes())
        fixture.write(self.docs, "AGENTS.md", "Altered unapproved control plane")
        self.control["documents"]["approved_tip"] = self.commit_docs()
        self.assertIn("RLS003", self.codes())

    def test_new_structural_warnings_do_not_authenticate_delivery(self):
        arts, _ = self.index()
        arts[EVR].meta["release_set_hash"] = "0" * 64
        report = v.Report({})
        registry = helpers.authority.mapping((ROOT / "schemas/artifact-types.yaml").read_bytes())
        sets.check(list(arts.values()), registry, report)
        self.assertEqual({f.code for f in report.findings}, {"RLS002"})

    def test_malformed_receipt_and_missing_history_have_no_traceback_or_success(self):
        self.control["documents"]["commit"] = "HEAD"
        self.assertIn("RLS003", self.codes())
        self.control["documents"]["commit"] = self.control["documents"]["approved_tip"]
        Path(self.control["receipts"][0]["path"]).write_text('{"duplicate":1,"duplicate":2}')
        self.assertIn("RLS003", self.codes())

    def test_release_context_keeps_the_adopted_release_guide_as_a_source(self):
        sources = importlib.import_module(v._CORE_NAME + ".memory.framework_sources")
        captured = sources.capture_framework(self.docs, root=self.runtime, skill="release").result
        self.assertIn("references/release-evidence.md", {s["path"] for s in captured["sources"]})


if __name__ == "__main__":
    unittest.main()
