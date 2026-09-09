"""Phase-five trust-boundary attacks and positive controls on disposable Git histories."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

from test_phase0 import ROOT, fixture
from test_references import v, amend

authority = importlib.import_module(v._CORE_NAME + ".authority")
controller = importlib.import_module(v._CORE_NAME + ".contribution_ci")
models = importlib.import_module(v._CORE_NAME + ".memory.models")
API = "repository:product:alpha:api"
HELPER = "repository:product:alpha:helper"
DC = "products/alpha/contracts/DC-001-input.md"
OTHER_DC = "products/alpha/contracts/DC-002-other.md"


class ContributionAuthority(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="contribution-runtime-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.shared = Path(cls.temp.name)
        cls.runtime = cls.shared / "framework"
        cls.runtime.mkdir()
        for relative in ("schemas", "src/framework_data_ai", "references", "skills"):
            shutil.copytree(ROOT / relative, cls.runtime / relative, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copyfile(ROOT / "FRAMEWORK.md", cls.runtime / "FRAMEWORK.md")
        fixture.git(cls.runtime, "init", "--initial-branch=main", "--template=")
        fixture.git(cls.runtime, "add", "--all")
        fixture.git(cls.runtime, "commit", "-m", "Synthetic trusted framework runtime")
        cls.pin = fixture.git(cls.runtime, "rev-parse", "HEAD")
        fixture.build(cls.shared / "fixtures")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="contribution-case-")
        self.addCleanup(temporary.cleanup)
        self.case = Path(temporary.name)
        self.docs = self.case / "documents"
        shutil.copytree(self.shared / "fixtures/qualified-impact", self.docs)
        config = yaml.safe_load((self.docs / "framework.yaml").read_text())
        config["framework_commit"] = self.pin
        (self.docs / "framework.yaml").write_text(yaml.safe_dump(config))
        amend(self.docs / fixture.ICG, impacts={"SIG-001": ["data"]})
        documents = fixture.Documents(self.docs)
        for path, identifier in ((DC, "DC-001"), (OTHER_DC, "DC-002")):
            documents.artifact(path, "data-contract", "# Synthetic contract\nPreserve the public shape.",
                               id=identifier, products=["alpha"], version="1.0.0")
        self.code, code_metadata, observed = {}, {}, {}
        for rid, key in ((API, "api"), (HELPER, "helper")):
            first, _ = fixture.code_repository(self.case, key, {"service.py": "VALUE = 1\n"})
            root = self.case / key
            self.code[rid] = root
            remote = f"https://example.invalid/synthetic/{key}.git"
            code_metadata[key] = dict(url=remote, contains="Synthetic service")
            observed[rid] = dict(root=str(root), repository=remote, base=first, head=first)
        amend(self.docs / "products/alpha/product.yaml", code=code_metadata)
        self.policy = dict(schema="framework-memory/contribution-policy/v1",
                           document_repository="synthetic/documents", classifications=["internal", "public"],
                           exclude=[], repositories={rid: row["repository"] for rid, row in observed.items()},
                           mandates={fixture.CHG: dict(repositories=[API, HELPER],
                                paths={"documents": [DC], API: ["service.py"], HELPER: []},
                                obligations=[dict(impact="data", path=DC)], tests=["contract"])},
                           tests={"contract": dict(command=["python", "-m", "unittest"], producer="ci:contract")},
                           exception_reviewers=["independent-reviewer"], exception_tests=["contract"])
        fixture.write(self.docs, authority.POLICY, json.dumps(self.policy))
        fixture.git(self.docs, "init", "--initial-branch=main", "--template=")
        self.base = self.commit_docs("Approved documentary base")
        self.control = dict(schema="framework-memory/contribution-input/v1", framework_commit=self.pin,
                            author="external-contributor",
                            documents=dict(root=str(self.docs), repository="synthetic/documents", commit=self.base,
                                           approved_tip=self.base, proposed=self.base),
                            repositories=observed, receipts=[], selected_tests=[])
        (self.code[API] / "service.py").write_text("VALUE = 2\n")
        fixture.git(self.code[API], "add", "--all")
        fixture.git(self.code[API], "commit", "-m", "Proposed code")
        observed[API]["head"] = fixture.git(self.code[API], "rev-parse", "HEAD")
        self.propose_contract()
        self.receipt()

    def commit_docs(self, message="Synthetic document change"):
        fixture.git(self.docs, "add", "--all")
        fixture.git(self.docs, "commit", "--allow-empty", "-m", message)
        return fixture.git(self.docs, "rev-parse", "HEAD")

    def propose_contract(self, path=DC, version="1.1.0"):
        amend(self.docs / path, version=version)
        self.control["documents"]["proposed"] = self.commit_docs()

    def base_change(self, modify):
        fixture.git(self.docs, "checkout", "--detach", self.base)
        modify()
        self.base = self.commit_docs("Revised synthetic approved base")
        self.policy = json.loads((self.docs / authority.POLICY).read_text())
        self.control["documents"].update(commit=self.base, approved_tip=self.base)
        self.propose_contract()
        self.receipt()

    def code_set(self):
        return {rid: dict(repository=row["repository"], commit=row["head"])
                for rid, row in self.control["repositories"].items()}

    def document(self):
        return dict(repository=self.control["documents"]["repository"], commit=self.control["documents"]["commit"])

    def receipt(self, modify=None, *, authenticate=True):
        value = dict(schema="framework-memory/execution-receipt/v1", producer="ci:contract", run="synthetic-run-1",
                     test="contract", command=["python", "-m", "unittest"], document=self.document(),
                     policy_hash=models.digest(models.canonical(self.policy)), code_set=self.code_set(),
                     result="passed", exit_code=0)
        if modify:
            modify(value)
        path = self.case / "receipt.json"
        path.write_bytes(models.canonical(value))
        if authenticate:
            self.control["receipts"] = [dict(path=str(path), digest=models.digest(models.canonical(value)),
                                             producer="ci:contract", run="synthetic-run-1")]
        return value

    def run_gate(self, text="Implements CHG-001."):
        result = authority.evaluate(self.control, text, v, framework_root=self.runtime)
        models.validate("contribution-report", result)
        return result

    def codes(self, text="Implements CHG-001."):
        return {f["code"] for f in self.run_gate(text)["findings"]}

    def test_positive_control_joins_specific_contract_and_exact_two_repository_set(self):
        result = self.run_gate()
        self.assertEqual(result["findings"], [], result)
        self.assertEqual(result["gate"], "passed")
        self.assertTrue(result["review_required"])
        self.assertEqual(result["evidence"]["mandatory"], ["contract"])
        self.assertEqual(result["changes"][HELPER], [])
        self.assertEqual(result["authorization"], "verified-against-caller-trusted-base")

    def test_approval_only_in_proposal_is_not_authority(self):
        self.base_change(lambda: amend(self.docs / fixture.CHG, status="draft"))
        amend(self.docs / fixture.CHG, status="approved")
        self.control["documents"]["proposed"] = self.commit_docs()
        self.assertIn("AUT002", self.codes())

    def test_chg_added_only_in_proposal_is_not_authority(self):
        original = (self.docs / fixture.CHG).read_bytes()
        self.base_change(lambda: (self.docs / fixture.CHG).unlink())
        (self.docs / fixture.CHG).write_bytes(original)
        self.control["documents"]["proposed"] = self.commit_docs()
        self.assertIn("AUT002", self.codes())

    def test_all_normative_fields_and_unmarked_additions_are_protected(self):
        original = (self.docs / fixture.CHG).read_text()
        for old, new in (("Separate", "Remove"), ("Preserve", "Break"), ("regression test", "no test"),
                         ("# Change processing boundary", "# New scope")):
            with self.subTest(old=old):
                (self.docs / fixture.CHG).write_text(original.replace(old, new))
                self.control["documents"]["proposed"] = self.commit_docs()
                self.assertIn("AUT003", self.codes())
        (self.docs / fixture.CHG).write_text(original + "\nAdditional unrestricted mandate.\n")
        self.control["documents"]["proposed"] = self.commit_docs()
        self.assertIn("AUT003", self.codes())

    def test_closure_status_can_change_without_rewriting_the_mandate(self):
        self.base_change(lambda: self.allow_documents(fixture.CHG))
        amend(self.docs / fixture.CHG, status="implemented", verified_by="EVR-001")
        self.control["documents"]["proposed"] = self.commit_docs()
        self.assertEqual(self.run_gate()["gate"], "passed")

    def allow_documents(self, path):
        self.policy["mandates"][fixture.CHG]["paths"]["documents"].append(path)
        fixture.write(self.docs, authority.POLICY, json.dumps(self.policy))

    def test_missing_shallow_invalid_or_unapproved_history_fails_closed(self):
        original = deepcopy(self.control["documents"])
        for key, value in (("commit", "HEAD"), ("approved_tip", "a" * 40), ("root", str(self.case / "missing"))):
            with self.subTest(key=key):
                self.control["documents"] = {**original, key: value}
                self.assertIn("AUT001", self.codes())
        self.control["documents"] = original
        self.control["documents"]["commit"] = original["proposed"]
        self.assertIn("AUT001", self.codes())

    def test_older_approval_cannot_revive_a_revoked_mandate(self):
        amend(self.docs / fixture.CHG, status="rolled-back")
        self.control["documents"]["approved_tip"] = self.commit_docs("Revocation on approved branch")
        self.control["documents"]["proposed"] = self.control["documents"]["approved_tip"]
        self.assertIn("AUT002", self.codes())

    def test_proposed_policy_and_check_overrides_do_not_weaken_the_gate(self):
        self.policy["mandates"][fixture.CHG]["obligations"] = []
        self.policy["mandates"][fixture.CHG]["paths"]["documents"] = ["products"]
        fixture.write(self.docs, authority.POLICY, json.dumps(self.policy))
        config = yaml.safe_load((self.docs / "framework.yaml").read_text())
        config["checks"] = {"AUT004": "off", "AUT005": "off"}
        (self.docs / "framework.yaml").write_text(yaml.safe_dump(config))
        self.control["documents"]["proposed"] = self.commit_docs()
        self.assertIn("AUT004", self.codes())

    def test_relevant_contract_cannot_be_replaced_by_an_unrelated_update(self):
        amend(self.docs / DC, version="1.0.0")
        self.propose_contract(OTHER_DC)
        self.assertIn("AUT005", self.codes())

    def test_contract_touched_without_version_increase_does_not_satisfy_obligation(self):
        amend(self.docs / DC, version="1.0.0")
        with (self.docs / DC).open("a") as stream:
            stream.write("\nA changed explanation.\n")
        self.control["documents"]["proposed"] = self.commit_docs()
        self.assertIn("AUT005", self.codes())

    def test_missing_repository_and_wrong_namespace_are_not_empty_success(self):
        row = self.control["repositories"].pop(HELPER)
        self.assertIn("AUT004", self.codes())
        self.control["repositories"][HELPER] = row
        self.control["repositories"][API]["repository"] = "https://example.invalid/another/api.git"
        self.assertIn("AUT001", self.codes())

    def test_out_of_scope_code_path_is_not_authorized_by_a_shared_number(self):
        (self.code[API] / "outside.py").write_text("UNRELATED = 1\n")
        fixture.git(self.code[API], "add", "--all")
        fixture.git(self.code[API], "commit", "-m", "Unbound file")
        self.control["repositories"][API]["head"] = fixture.git(self.code[API], "rev-parse", "HEAD")
        self.receipt()
        self.assertIn("AUT004", self.codes())

    def test_stale_code_set_document_policy_or_command_is_not_current_evidence(self):
        edits = [
            lambda r: r["code_set"][API].update(commit=self.control["repositories"][API]["base"]),
            lambda r: r["code_set"].pop(HELPER),
            lambda r: r["document"].update(commit="a" * 40),
            lambda r: r.update(policy_hash="0" * 64),
            lambda r: r.update(command=["echo", "passed"]),
        ]
        for change in edits:
            with self.subTest(change=change):
                self.receipt(change)
                self.assertIn("EVI002", self.codes())

    def test_fast_selection_does_not_remove_mandatory_tests(self):
        self.control["receipts"] = []
        self.control["selected_tests"] = []
        self.assertIn("EVI003", self.codes())

    def test_digest_producer_duplicate_and_failed_receipts_are_rejected(self):
        self.control["receipts"][0]["digest"] = "0" * 64
        self.assertIn("EVI001", self.codes())
        self.receipt(lambda r: r.update(producer="pr:author"))
        self.assertIn("EVI001", self.codes())
        self.receipt()
        self.control["receipts"] *= 2
        self.assertIn("EVI001", self.codes())
        self.receipt(lambda r: r.update(result="failed", exit_code=1))
        self.assertIn("EVI003", self.codes())

    def test_no_chg_requires_independent_review_and_still_requires_tests(self):
        reason = "Synthetic maintenance with reviewed scope."
        self.assertIn("AUT006", self.codes("no-chg: " + reason))
        request_hash = models.digest(models.canonical(dict(document=self.document(),
                    proposed=self.control["documents"]["proposed"], code_set=self.code_set(), reason=reason)))
        self.control["exception_review"] = dict(reviewer="independent-reviewer", request_hash=request_hash)
        self.assertEqual(self.run_gate("no-chg: " + reason)["gate"], "passed")
        self.control["receipts"] = []
        self.assertIn("EVI003", self.codes("no-chg: " + reason))
        self.assertIn("AUT006", self.codes("no-chg: A different request"))

    def test_no_chg_author_cannot_supply_the_independent_review(self):
        reason = "Reviewed maintenance."
        request_hash = models.digest(models.canonical(dict(document=self.document(),
                    proposed=self.control["documents"]["proposed"], code_set=self.code_set(), reason=reason)))
        self.control["exception_review"] = dict(reviewer="independent-reviewer", request_hash=request_hash)
        self.control["author"] = "INDEPENDENT-REVIEWER"
        self.assertIn("AUT006", self.codes("no-chg: " + reason))

    def test_receipt_run_must_match_the_independently_authenticated_witness(self):
        self.receipt(lambda r: r.update(run="another-run"))
        self.assertIn("EVI001", self.codes())

    def test_code_in_document_repository_requires_matching_observation(self):
        self.base_change(lambda: self.allow_documents("service.py"))
        (self.docs / "service.py").write_text("raise SystemExit('not a document')\n")
        self.control["documents"]["proposed"] = self.commit_docs()
        self.assertIn("AUT004", self.codes())

    def api_inputs(self):
        info = dict(full_name="synthetic/documents", default_branch="main", html_url="synthetic/documents")
        pull = dict(state="open", draft=False, user=dict(login="external-contributor"),
                    base=dict(repo=dict(full_name="synthetic/documents"), ref="main", sha=self.base),
                    head=dict(sha=self.control["documents"]["proposed"]),
                    title="Implements CHG-001.", body="Literal \\c and $(touch SENTINEL); no shell execution.")
        branch = dict(name="main", protected=True, commit=dict(sha=self.base))
        return info, pull, branch

    def test_controller_preserves_literal_metadata_and_never_invents_receipts(self):
        info, pull, branch = self.api_inputs()
        control, text = controller.prepare("synthetic/documents", info, pull, branch, self.docs, self.pin)
        models.validate("contribution-input", control)
        self.assertEqual(text, pull["title"] + "\n" + pull["body"])
        self.assertEqual(control["author"], pull["user"]["login"])
        self.assertEqual(control["documents"], self.control["documents"])
        self.assertEqual(control["receipts"], [])
        self.assertEqual(control["repositories"], {})
        result = authority.evaluate(control, text, v, framework_root=self.runtime)
        self.assertEqual(result["gate"], "failed", "document-only helper cannot satisfy a code mandate")

    def test_controller_refuses_unprotected_stale_or_wrong_repository_bases(self):
        mutations = (
            lambda i, p, b: i.update(full_name="untrusted/documents"),
            lambda i, p, b: p["base"]["repo"].update(full_name="untrusted/documents"),
            lambda i, p, b: p.update(state="closed"),
            lambda i, p, b: p.update(draft=True),
            lambda i, p, b: p["base"].update(ref="unreviewed"),
            lambda i, p, b: b.update(protected=False),
            lambda i, p, b: b["commit"].update(sha="a" * 40),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                info, pull, branch = self.api_inputs()
                mutate(info, pull, branch)
                with self.assertRaises(authority.MemoryInputError):
                    controller.prepare("synthetic/documents", info, pull, branch, self.docs, self.pin)

    def test_documentary_controller_refuses_code_files(self):
        (self.docs / "new.py").write_text("raise SystemExit('must not run')\n")
        self.control["documents"]["proposed"] = self.commit_docs()
        info, pull, branch = self.api_inputs()
        with self.assertRaises(authority.MemoryInputError):
            controller.prepare("synthetic/documents", info, pull, branch, self.docs, self.pin)

    def test_fetch_uses_fixed_base_ref_no_shell_and_no_token_in_command(self):
        with patch.object(controller.subprocess, "run") as run, patch.object(controller, "git") as read:
            run.return_value.returncode = 0
            read.return_value = ("a" * 40).encode()
            self.assertEqual(controller.fetch_head(self.docs, "https://example.invalid", "org/docs", 12,
                                                   "SYNTHETIC_TOKEN"), "a" * 40)
        command = run.call_args.args[0]
        options = run.call_args.kwargs
        self.assertNotIn("SYNTHETIC_TOKEN", " ".join(command))
        self.assertFalse(options.get("shell", False))
        self.assertEqual(command[-2:], ["https://example.invalid/org/docs.git",
                                      "+refs/pull/12/head:refs/framework/contribution-head"])
        self.assertNotIn("GITHUB_TOKEN", options["env"])
        self.assertEqual(options["env"]["GIT_CONFIG_KEY_0"],
                         "http.https://example.invalid/org/docs.git.extraheader")

    def test_controller_endpoint_and_redirect_guards(self):
        for value in ("http://example.invalid", "https://user:secret@example.invalid", "https://example.invalid?x=1",
                      "https://example.invalid#fragment", "file:///tmp/example"):
            with self.subTest(value=value), self.assertRaises(authority.MemoryInputError):
                controller.endpoint(value)
        self.assertEqual(controller.endpoint("https://example.invalid/api/v3/"), "https://example.invalid/api/v3")
        self.assertIsNone(controller.NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.invalid"))

    def test_optional_workflow_is_manual_pinned_and_has_no_pr_checkout(self):
        workflow = yaml.load((ROOT / "ci/contribution.yml").read_text(), Loader=yaml.BaseLoader)
        self.assertEqual(set(workflow["on"]), {"workflow_dispatch"})
        self.assertEqual(workflow["permissions"], {"contents": "read", "pull-requests": "read"})
        for step in workflow["jobs"]["inspect"]["steps"]:
            if "uses" in step:
                self.assertRegex(step["uses"], r"@[0-9a-f]{40}$")
            if "run" in step:
                self.assertNotIn("${{", step["run"])
            if step.get("uses", "").startswith("actions/checkout@"):
                self.assertEqual(step["with"]["persist-credentials"], "false")
                self.assertNotIn("pull_request", step["with"]["ref"])

    def test_html_fences_and_shell_text_are_never_executed_or_authority(self):
        sentinel = self.case / "executed"
        text = f"<!-- no-chg: exempt -->\n```\nCHG-001\n```\n$(touch {sentinel})"
        self.assertIn("AUT006", self.codes(text))
        self.assertFalse(sentinel.exists())

    def test_uncommitted_instructions_are_not_read_and_graphs_are_not_started(self):
        (self.docs / fixture.CHG).write_text("Uncommitted permissive instruction")
        (self.code[API] / "service.py").write_text("raise SystemExit('do not run')\n")
        self.assertEqual(self.run_gate()["gate"], "passed")
        self.assertFalse((self.docs / "_meta/memory").exists())

    def test_excluded_source_never_becomes_approval_or_report_content(self):
        self.base_change(lambda: amend(self.docs / DC, classification="confidential"))
        with (self.docs / DC).open("a") as stream:
            stream.write("\nCONFIDENTIAL_SENTINEL\n")
        self.control["documents"]["proposed"] = self.commit_docs()
        result = self.run_gate()
        self.assertEqual(result["gate"], "failed")
        self.assertNotIn("CONFIDENTIAL_SENTINEL", models.canonical(result).decode())
        self.assertNotIn(DC, result["changes"]["documents"])

    def test_runtime_pin_cannot_be_a_dirty_or_different_checkout(self):
        path = self.runtime / "src/framework_data_ai/authority.py"
        original = path.read_bytes()
        try:
            path.write_bytes(original + b"\n# altered runtime\n")
            self.assertIn("AUT001", self.codes())
        finally:
            path.write_bytes(original)
        self.control["framework_commit"] = "a" * 40
        self.assertIn("AUT001", self.codes())

    def test_duplicate_policy_key_is_refused(self):
        original = (self.docs / authority.POLICY).read_text()
        self.base_change(lambda: (self.docs / authority.POLICY).write_text(
            original[:-1] + ', "document_repository": "forged"}'))
        self.assertIn("AUT001", self.codes())

    def test_multiple_changes_keep_obligations_and_repository_sets_separate(self):
        other = "products/alpha/changes/CHG-002-other.md"
        def add():
            shutil.copyfile(self.docs / fixture.CHG, self.docs / other)
            amend(self.docs / other, id="CHG-002")
            self.policy["mandates"][other] = deepcopy(self.policy["mandates"][fixture.CHG])
            fixture.write(self.docs, authority.POLICY, json.dumps(self.policy))
        self.base_change(add)
        self.assertEqual(self.run_gate("Implements CHG-001 and CHG-002.")["gate"], "passed")

    def test_symlinked_required_document_is_not_followed(self):
        path = self.docs / DC
        path.unlink()
        path.symlink_to(self.case / "unreadable-private-source")
        self.control["documents"]["proposed"] = self.commit_docs()
        self.assertIn("AUT001", self.codes())

    def test_changed_code_symlink_is_not_an_ordinary_file_change(self):
        path = self.code[API] / "service.py"
        path.unlink()
        path.symlink_to(self.case / "private")
        fixture.git(self.code[API], "add", "--all")
        fixture.git(self.code[API], "commit", "-m", "Link substitution")
        self.control["repositories"][API]["head"] = fixture.git(self.code[API], "rev-parse", "HEAD")
        self.receipt()
        self.assertIn("AUT004", self.codes())

    def test_malformed_affected_contract_does_not_pass_with_a_version_bump(self):
        amend(self.docs / DC, owners="not-an-owner-list")
        self.control["documents"]["proposed"] = self.commit_docs()
        self.assertIn("FM002", self.codes())

    def test_cli_export_reads_only_explicit_inputs_and_legacy_remains_visible(self):
        control = self.case / "control.json"
        control.write_text(json.dumps(self.control))
        body = self.case / "pr.txt"
        body.write_text("Implements CHG-001.")
        command = [sys.executable, "-I", "-B", str(self.runtime / "skills/audit/scripts/validate.py"),
                   "--profile", "strict-contribution", "--trust-input", str(control),
                   "--pr-text-file", str(body), "--json"]
        run = subprocess.run(command, cwd=self.case, capture_output=True, text=True, timeout=40)
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        self.assertEqual(json.loads(run.stdout)["gate"], "passed")
        run = subprocess.run(command + ["--emit-index"], capture_output=True, text=True, timeout=20)
        self.assertNotEqual(run.returncode, 0)
        self.assertFalse((self.docs / "TRACEABILITY.md").exists())
        legacy = subprocess.run([sys.executable, "-B", str(ROOT / "skills/audit/scripts/validate.py"),
                                 "--root", str(self.shared / "fixtures/qualified-impact"), "--json",
                                 "--pr-text", "Implements CHG-001.", "--stale-days", "36500"],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(json.loads(legacy.stdout)["contribution_profile"], "legacy")
        self.assertIn("not verified", legacy.stderr)


if __name__ == "__main__":
    unittest.main()
