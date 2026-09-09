"""Opt-in release verification from caller-authenticated inputs. Never merge or deploy."""
from datetime import datetime
from pathlib import Path

import jsonschema
import yaml

from . import authority, release_sets
from .artifacts import as_list, as_map, locate_sections
from .git_snapshot import GitSnapshot, ancestor, commit, relative, git
from .memory.models import FRAMEWORK, canonical, digest, validate
from .memory.operational_io import read_json
from .references import ReferenceIndex, canonical_repo
from .workspace import MemoryInputError

STATES = ("prepared", "implemented", "verified")


def receipts(witnesses, document, manifest, evr, identity, target, report):
    seen = {}
    for witness in witnesses:
        receipt = read_json(Path(witness["path"]))
        validate("release-receipt", receipt)
        stage = receipt["stage"]
        if (stage in seen or digest(canonical(receipt)) != witness["digest"]
                or any(receipt[key] != witness[key] for key in ("producer", "run", "stage"))):
            report.add("RLS004", "receipts", "duplicate stage or unauthenticated receipt bytes/producer/run/stage")
            continue
        if (receipt["document"] != document or receipt["manifest"] != manifest.rel
                or receipt["report"] != evr.rel or receipt["release_set_hash"] != identity
                or receipt["result"] != "passed" or receipt["exit_code"] != 0):
            report.add("RLS004", stage, "receipt is failed, unavailable or belongs to another candidate/document/evaluation")
            continue
        if stage == "deployment":
            observed = datetime.fromisoformat(receipt["observed_at"].replace("Z", "+00:00"))
            if (observed.tzinfo is None or not target or receipt["environment"] != target
                    or receipt["observed_set_hash"] != identity):
                report.add("RLS005", "deployment", "observed set/environment differs or observation has no timezone")
                continue
        seen[stage] = receipt
    return seen


def evaluate(control, api, *, framework_root=FRAMEWORK):
    report = api.Report({})
    report.config = {code: {"level": "error"} for code in
                     ("RLS001", "RLS002", "RLS003", "RLS004", "RLS005", "RLS006", "RLS007",
                      "FM001", "FM002", "SEC001", "CHG001", "CHG002", "CHG003")}
    details = dict(requested="prepared", supported_state="not-established", status_changed=False,
                   deployment_executed=False, atomic=False, review_required=True)
    try:
        validate("release-input", control)
        details["requested"] = control["stage"]
        docs = control["documents"]
        ancestor(Path(docs["root"]), docs["commit"], docs["approved_tip"])
        before, tip = (GitSnapshot.open(docs["root"], docs[key]) for key in ("commit", "approved_tip"))
        project = authority.mapping(before.read("framework.yaml"))
        if (project != authority.mapping(tip.read("framework.yaml"))
                or before.read("AGENTS.md") != tip.read("AGENTS.md")):
            raise MemoryInputError("adopted rules changed on the approved branch")
        registry, rules = authority.runtime(project, control["framework_commit"], framework_root)
        scope = {key: control[key] for key in ("classifications", "exclude")}
        arts, _ = authority.artifacts(before, project, scope, registry, include_generated=True)
        current, _ = authority.artifacts(tip, project, scope, registry, include_generated=True)
        by_path, latest = {a.rel: a for a in arts}, {a.rel: a for a in current}
        index = ReferenceIndex(arts, registry, document_repository=docs["repository"])
        document = dict(repository=docs["repository"], commit=docs["commit"])
        rule_hashes = {path: digest(rules.read(path)) for path in
                       ("FRAMEWORK.md", "references/preamble.md", "references/release-evidence.md", "skills/release/SKILL.md")}
        rule_hashes["AGENTS.md"] = digest(before.read("AGENTS.md"))
        details.update(document=document, framework_commit=rules.revision, rules=rule_hashes)

        def selected(path, kind):
            source = by_path.get(relative(path))
            if not source or source.type != kind:
                raise MemoryInputError("required release source is unavailable in authorized scope")
            api.check_front_matter(source, registry, report)
            if path not in latest or authority.normative(source) != authority.normative(latest[path]):
                raise MemoryInputError("selected release source changed on the approved branch")
            api.check_front_matter(latest[path], registry, report)
            return source

        visited, active, all_code, eligible = {}, set(), {}, {}

        def inspect(path):
            if path in active or len(active) >= 16 or (path not in visited and len(visited) >= 32):
                raise MemoryInputError("release dependency cycle or traversal bound")
            if path in visited:
                return visited[path]
            active.add(path)
            manifest = selected(path, "release-manifest")
            normalized = release_sets.normalize(manifest, index)
            if path == control["manifest"]:
                # Expose the computed candidate identity for diagnostics/preparation even
                # if the EVR is missing or mismatched; this does not pass any evidence gate.
                details.update(manifest=path, release_set_hash=normalized["hash"], normalization=normalized["origin"])
            evr = release_sets.evaluation(manifest, index, normalized)
            selected(evr.rel, "evaluation-report")
            note_ref = index.artifact(manifest.meta.get("release_note"), kind="release-note").target
            if not note_ref or index.owner(note_ref.artifact) != index.owner(manifest):
                raise MemoryInputError("release note is absent or belongs to another product")
            note = selected(note_ref.artifact.rel, "release-note")
            if evr.id not in as_list(note.meta.get("derives_from")):
                raise MemoryInputError("release note does not reference this evaluation")
            plans = [a for a in arts if a.type == "evaluation-plan" and index.owner(a) == index.owner(manifest)]
            if len(plans) != 1:
                raise MemoryInputError("frozen plan path is ambiguous or missing")
            frozen = GitSnapshot.open(before.root, evr.meta.get("frozen_at"))
            ancestor(before.root, frozen.revision, before.revision)
            plan = authority.artifact(frozen, plans[0].rel)
            if (not plan or plan.type != "evaluation-plan" or plan.meta.get("classification") not in control["classifications"]
                    or plan.meta.get("version") != evr.meta.get("evp_version")
                    or digest(frozen.read(plan.rel)) != evr.meta.get("evp_hash")):
                report.add("RLS003", evr.rel, "frozen plan bytes/version are not those referenced by this evaluation")
            for rid, row in normalized["payload"]["repositories"].items():
                if rid in all_code and all_code[rid] != row:
                    report.add("RLS001", manifest.rel, "dependency releases require conflicting versions of a repository")
                all_code[rid] = row
                eligible[rid] = normalized["eligible"][rid]
            for dependency in normalized["payload"]["dependencies"]:
                other = inspect(dependency["manifest"])
                if dependency["release_set_hash"] != other[1]["hash"]:
                    report.add("RLS007", manifest.rel, "shared release reference has a different candidate identity")
                condition = dependency["compatibility"]
                source = by_path.get(relative(condition["path"]))
                if (not source or digest(before.read(source.rel)) != condition["sha256"]
                        or before.read(source.rel) != tip.read(source.rel)
                        or condition["section"] not in {s.marker for s in locate_sections(source.body)}):
                    report.add("RLS007", manifest.rel, "compatibility source is missing, filtered, stale or changed")
                # The section is a locator for review, not an executable compatibility claim.
            result = (manifest, normalized, evr)
            active.remove(path)
            visited[path] = result
            return result

        manifest, normalized, evr = inspect(control["manifest"])
        identity = normalized["hash"]
        details.update(manifest=manifest.rel, release_set_hash=identity, normalization=normalized["origin"],
                       dependencies=sorted(set(visited) - {manifest.rel}))
        merged = True
        if set(control["repositories"]) != set(all_code):
            report.add("RLS006", "repositories", "controller did not observe the exact candidate and dependency repository set")
            merged = False
        for rid, row in all_code.items():
            observed = control["repositories"].get(rid)
            if not observed:
                continue
            binding = eligible[rid]
            declaration = by_path[binding["artifact"]]
            api.check_front_matter(declaration, registry, report)
            api.check_front_matter(latest[declaration.rel], registry, report)
            if (canonical_repo(observed["repository"]) != binding["remote"]
                    or declaration.meta.get("code") != latest[declaration.rel].meta.get("code")):
                raise MemoryInputError("observed repository identity differs from its approved declaration")
            root = Path(observed["root"])
            commit(root, row["commit"])
            commit(root, observed["approved_tip"])
            # Default branch name/tip are authenticated by the controller, not assumed main.
            is_merged = git(root, "merge-base", row["commit"], observed["approved_tip"]).decode().strip() == row["commit"]
            merged = merged and is_merged
        changes = []
        needed = STATES.index(control["stage"])
        contracts = as_map(manifest.meta.get("changes")).get("contracts")
        if not isinstance(contracts, list) or any(not isinstance(c, str) for c in contracts) or len(set(contracts)) != len(contracts):
            raise MemoryInputError("manifest must explicitly list distinct change contracts")
        note = index.artifact(manifest.meta["release_note"], kind="release-note").target.artifact
        if set(contracts) != {r for r in as_list(note.meta.get("derives_from")) if isinstance(r, str) and r.startswith("CHG-")}:
            report.add("RLS002", note.rel, "release note and manifest include different change contracts")
        for identifier in contracts:
            resolved = index.artifact(identifier, kind="change-contract").target
            if not resolved or index.owner(resolved.artifact) != index.owner(manifest):
                raise MemoryInputError("release contract is missing or outside the product")
            change = selected(resolved.artifact.rel, "change-contract")
            changes.append(change)
            if (change.meta.get("status") not in api.AUTHORIZED_FOR_A_PR
                    or latest[change.rel].meta.get("status") not in api.AUTHORIZED_FOR_A_PR):
                report.add("RLS006", change.rel, "release contract is not currently authorized")
            for state in (change.meta.get("status"), latest[change.rel].meta.get("status")):
                if state in STATES:
                    needed = max(needed, STATES.index(state))
            for observed_change in (change, latest[change.rel]):
                if observed_change.meta.get("status") == "verified" and observed_change.meta.get("verified_by") != evr.id:
                    report.add("RLS002", change.rel, "verified closure refers to a different evaluation")
        api.check_change_contracts(changes, report, references=index)
        details["required_state"] = STATES[needed]
        observed = receipts(control["receipts"], document, manifest, evr, identity,
                            as_map(manifest.meta.get("infrastructure")).get("target"), report)
        mandatory = {"pre-release", "integration"} | ({"deployment"} if needed == 2 else set())
        for stage in sorted(mandatory - observed.keys()):
            report.add("RLS004", stage, "mandatory independently witnessed execution evidence is missing")
        if needed >= 1 and not merged:
            report.add("RLS006", "integration", "not every released code commit is on its authenticated default-branch history")
        details.update(default_branches_contain_code=merged, evidence=sorted(observed),
                       deployment_observation=observed.get("deployment", {}).get("observed_at", "not-observed"))
        if not report.findings:
            details["supported_state"] = "verified" if merged and "deployment" in observed else "implemented" if merged else "prepared"
    except (MemoryInputError, OSError, ValueError, TypeError, KeyError, RecursionError, yaml.YAMLError, jsonschema.ValidationError):
        report.add("RLS003", "release inputs", "required trusted history, runtime, source, mapping or receipt is unavailable/invalid")
    return dict(schema="framework-memory/release-report/v1", profile="strict-release", **details,
                gate="failed" if report.findings else "passed", findings=[f.as_json() for f in report.findings],
                limitations=["caller authenticates approved documentary/default-branch identities and receipt issuer/run/artifact",
                             "pre-release witness must verify frozen thresholds and build provenance, not copy an EVR verdict",
                             "integration witness includes dependency compatibility; deployment witness observes the whole set and smoke result",
                             "observations are as-of evidence, not continuous monitoring or atomic merge/deploy",
                             "no source execution, remote operation, manifest rewrite or lifecycle update was performed"])


def main(args, api):
    if (not args.trust_input or args.pr_text is not None or args.pr_text_file or args.changed_files
            or args.emit_index or args.check or args.list_checks or args.stale_days is not None):
        raise SystemExit("strict-release requires only --trust-input; no PR context, writes or path list")
    try:
        result = evaluate(read_json(args.trust_input), api)
        validate("release-report", result)
    except (OSError, ValueError, TypeError, KeyError, RecursionError, yaml.YAMLError, jsonschema.ValidationError):
        print('{"profile":"strict-release","gate":"unavailable","supported_state":"not-established"}')
        return 2
    print(canonical(result).decode(), end="")
    return 0 if result["gate"] == "passed" else 1
