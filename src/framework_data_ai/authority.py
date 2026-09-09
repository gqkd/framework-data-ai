"""Opt-in contribution checks against caller-trusted Git history; no network or execution."""
from pathlib import Path
import json
import re

import jsonschema
import yaml

from .artifacts import Artifact, as_list, document_selected, load_scan, locate_sections
from .git_snapshot import GitSnapshot, ancestor, commit, relative, MAX_TOTAL, git
from .memory.models import FRAMEWORK, canonical, digest, validate, _read_contract
from .memory.operational_io import read_json
from .references import ReferenceIndex, canonical_repo
from .snapshots import bounded_metadata
from .workspace import MemoryInputError
from .evidence import verify_receipts

POLICY = ".framework/contribution-policy.json"
SECTIONS = ("what-changes", "what-must-not-change", "how-we-know-it-worked")
OBLIGES = {"data": "data-contract", "architecture": "architecture", "risk-compliance": "risk-register"}


def mapping(data):
    # Reuse the duplicate-key rejecting SafeLoader, plus the existing expansion bound.
    result = bounded_metadata(_read_contract(data))
    if not isinstance(result, dict):
        raise MemoryInputError("source must contain a mapping")
    return result


def artifact(tree, path):
    text = tree.read(path).decode("utf-8").replace("\r\n", "\n")
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end < 0:
            raise MemoryInputError("unclosed artifact metadata")
        meta, body = mapping(text[4:end].encode()), text[end + 4:]
    elif re.search(r"^schema:", text, re.M):
        meta, body = mapping(text.encode()), ""
    else:
        return None
    return Artifact(Path(path), path, meta, body)


def artifacts(tree, project, policy, registry, *, include_generated=False):
    scan = load_scan(registry, project)
    result, blocked, size = [], set(), 0
    for path in sorted(tree.entries):
        if not document_selected(Path(path), scan):
            continue
        if any(path == p or path.startswith(p + "/") for p in policy["exclude"]):
            blocked.add(path)
            continue
        data = tree.read(path)
        size += len(data)
        if size > MAX_TOTAL:
            raise MemoryInputError("selected documentary sources exceed the byte bound")
        art = artifact(tree, path)
        generated = (art and include_generated and art.meta.get("classification") is None
                     and registry["types"].get(art.type, {}).get("generated") is True)
        if art and (art.meta.get("classification") in policy["classifications"] or generated):
            art.ids = set(re.findall(r"\b((?:%s)-\d{3,})\b" % "|".join(registry["id_prefixes"]), art.body))
            result.append(art)
        elif art:
            blocked.add(path)
    return result, blocked


def normative(art):
    # The whole immutable body is retained, not only the three headings: a new paragraph
    # outside a marker can change a mandate too. Only existing closure metadata is exempt.
    mutable = {"status", "verified_by"} if art.type == "change-contract" else {"status"}
    return canonical(dict(meta={k: v for k, v in art.meta.items() if k not in mutable},
                          body=art.body))


def permits(path, prefixes):
    return any(path == prefix or path.startswith(prefix + "/") for prefix in prefixes)


def runtime(project, requested_pin, framework_root=FRAMEWORK):
    """One clean-runtime check shared by contribution and release verification."""
    root = Path(framework_root)
    registry = mapping((root / "schemas/artifact-types.yaml").read_bytes())
    pin = project.get("framework_commit")
    commit(root, pin)
    if project.get("framework_version") != registry["version"] or requested_pin != pin:
        raise MemoryInputError("runtime and adopted framework pin/version disagree")
    rules = GitSnapshot.open(root, pin)
    if git(root, "rev-parse", "HEAD").decode().strip() != pin:
        raise MemoryInputError("runtime checkout does not match the adopted pin")
    paths = {"skills/audit/scripts/validate.py", "skills/audit/checks.yaml",
             "schemas/artifact-types.yaml", "schemas/memory-contracts.yaml"}
    paths.update(p.relative_to(root).as_posix() for p in (root / "src/framework_data_ai").rglob("*.py"))
    paths.update(p.relative_to(root).as_posix() for p in (root / "schemas").rglob("*.json"))
    # Check the union too: removing an optional runtime module must not hide its absence.
    paths.update(p for p in rules.entries if (p.startswith("src/framework_data_ai/") and p.endswith(".py"))
                 or (p.startswith("schemas/") and p.endswith(".json")))
    for path in paths:
        if rules.read(path) != (root / path).read_bytes():
            raise MemoryInputError("runtime source bytes differ from the pinned commit")
    return registry, rules


def evaluate(control, text, api, *, framework_root=FRAMEWORK):
    report = api.Report({})
    # Explicit strict profile: project/PR severity overrides cannot disable these gates.
    report.config = {code: {"level": "error"} for code in
                     ("AUT001", "AUT002", "AUT003", "AUT004", "AUT005", "AUT006",
                      "EVI001", "EVI002", "EVI003", "FM001", "FM002")}
    details = dict(profile="strict-contribution", authorization="not-verified",
                   review_required=True, deployment="not-assessed", checks="bounded-structural-and-receipt-checks")
    try:
        validate("contribution-input", control)
        docs = control["documents"]
        ancestor(Path(docs["root"]), docs["commit"], docs["approved_tip"])
        before = GitSnapshot.open(docs["root"], docs["commit"])
        after = GitSnapshot.open(docs["root"], docs["proposed"])
        ancestor(before.root, before.revision, after.revision)
        tip = GitSnapshot.open(docs["root"], docs["approved_tip"])
        if before.changed(after):
            ancestor(before.root, tip.revision, after.revision)
        policy = json.loads(before.read(POLICY), object_pairs_hook=unique_pairs)
        validate("contribution-policy", policy)
        policy_hash = digest(canonical(policy))
        current_policy = json.loads(tip.read(POLICY), object_pairs_hook=unique_pairs)
        if policy != current_policy:
            raise MemoryInputError("selected policy has changed on the approved branch")
        if docs["repository"] != policy["document_repository"]:
            raise MemoryInputError("document repository differs from the approved policy")
        project = mapping(before.read("framework.yaml"))
        if (project != mapping(tip.read("framework.yaml"))
                or before.read("AGENTS.md") != tip.read("AGENTS.md")):
            raise MemoryInputError("selected rules have changed on the approved branch")
        registry, rules = runtime(project, control["framework_commit"], framework_root)
        pin = rules.revision
        rule_hashes = {p: digest(rules.read(p)) for p in
                       ("FRAMEWORK.md", "references/preamble.md", "references/routing-table.md",
                        "references/operational-memory.md", "references/contributions.md",
                        "skills/audit/SKILL.md")}
        rule_hashes["AGENTS.md"] = digest(before.read("AGENTS.md"))
        base_arts, base_blocked = artifacts(before, project, policy, registry)
        head_arts, head_blocked = artifacts(after, project, policy, registry)
        tip_arts, _ = artifacts(tip, project, policy, registry)
        current = {a.rel: a for a in tip_arts}
        index = ReferenceIndex(base_arts, registry, document_repository=docs["repository"])
        by_path, proposed = {a.rel: a for a in base_arts}, {a.rel: a for a in head_arts}
        document = dict(repository=docs["repository"], commit=docs["commit"])
        details.update(document=document, approved_tip=docs["approved_tip"], proposed=docs["proposed"],
                       policy_hash=policy_hash, rules=rule_hashes, framework_commit=pin)
        changes = {"documents": before.changed(after)}
        code_set = {}
        for rid, observed in control["repositories"].items():
            if rid not in policy["repositories"] or observed["repository"] != policy["repositories"][rid]:
                raise MemoryInputError("code repository binding is outside the approved policy")
            owner, key = rid.removeprefix("repository:").rsplit(":", 1)
            declarations = index.repositories.get((owner, key), [])
            if len(declarations) != 1:
                raise MemoryInputError("code binding is missing or ambiguous in approved manifests")
            declared = declarations[0].artifact.meta["code"][key]
            remote = declared.get("url") if isinstance(declared, dict) else declared
            current_manifest = current.get(declarations[0].artifact.rel)
            if not current_manifest or current_manifest.meta.get("code") != declarations[0].artifact.meta.get("code"):
                raise MemoryInputError("repository bindings changed on the approved branch")
            if canonical_repo(remote) != canonical_repo(observed["repository"]):
                raise MemoryInputError("observed repository differs from its approved manifest")
            old = GitSnapshot.open(observed["root"], observed["base"])
            new = GitSnapshot.open(observed["root"], observed["head"])
            ancestor(old.root, old.revision, new.revision)
            changes[rid] = old.changed(new)
            if any(entry and entry[0] not in ("100644", "100755")
                   for path in changes[rid] for entry in (old.entries.get(path), new.entries.get(path))):
                report.add("AUT004", rid, "changed code links/submodules require separate assessment")
            code_set[rid] = dict(repository=observed["repository"], commit=observed["head"])
        # Recompute every changed path from immutable objects; never trust --changed-files.
        co_located = any(canonical_repo(row["repository"]) == canonical_repo(docs["repository"])
                         and row["base"] == before.revision and row["head"] == after.revision
                         for row in control["repositories"].values())
        for path in changes["documents"]:
            if any(entry and entry[0] not in ("100644", "100755")
                   for entry in (before.entries.get(path), after.entries.get(path))):
                report.add("AUT004", "documentary scope", "changed links/submodules require separate assessment")
            if (Path(path).suffix not in (".md", ".yaml", ".yml") and path != POLICY and not co_located):
                report.add("AUT004", "documentary scope", "non-documentary files require an explicit matching code observation")
        blocked = base_blocked | head_blocked
        if blocked.intersection(changes["documents"]):
            report.add("AUT004", "documentary scope", "changed sources outside the authorized filter remain unassessed")
        details.update(changes={**changes, "documents": [p for p in changes["documents"] if p not in blocked]},
                       code_set=code_set)
        said = api.asserted(text)
        ids = sorted(set(api.CHG_IN_TEXT.findall(said)))
        exempt = api.NO_CHG.search(said)
        if not ids:
            review = control.get("exception_review")
            request_hash = digest(canonical(dict(document=document, proposed=docs["proposed"],
                                                 code_set=code_set, reason=exempt.group(1) if exempt else "")))
            if (not exempt or not review or review["request_hash"] != request_hash
                    or review["reviewer"].casefold() == control["author"].casefold()
                    or review["reviewer"] not in policy["exception_reviewers"]):
                report.add("AUT006", "pull request", "no-chg requires a reason and independent CI-verified review of this exact request")
            else:
                details["exception"] = dict(reason=exempt.group(1), reviewer=review["reviewer"])
            # Exceptions retain evidence requirements; they do not turn a code run into
            # a documentary typo. Scope is review-owned, not silently inferred here.
            required = set(policy["exception_tests"])
            if control["repositories"] and not required:
                report.add("EVI003", "evidence", "a code exception has no mandatory test binding")
        else:
            required, allowed, required_repositories = set(), {}, set()
            for cid in ids:
                found = index.artifact(cid, kind="change-contract")
                change = found.target.artifact if found.target else None
                if not change or change.meta.get("status") not in api.AUTHORIZED_FOR_A_PR:
                    report.add("AUT002", cid, "CHG is absent, ambiguous or not approved in the trusted base")
                    continue
                latest = current.get(change.rel)
                if (not latest or normative(latest) != normative(change)
                        or latest.meta.get("status") not in api.AUTHORIZED_FOR_A_PR):
                    report.add("AUT002", cid, "selected mandate was revoked or changed on the approved branch")
                head = proposed.get(change.rel)
                api.check_front_matter(change, registry, report)
                if head:
                    api.check_front_matter(head, registry, report)
                if (not head or normative(change) != normative(head)
                        or head.meta.get("status") not in api.AUTHORIZED_FOR_A_PR
                        or api.AUTHORIZED_FOR_A_PR.index(head.meta["status"]) <
                           api.AUTHORIZED_FOR_A_PR.index(change.meta["status"])):
                    report.add("AUT003", cid, "approved mandate was removed or changed by the contribution")
                spans = locate_sections(change.body)
                for marker in SECTIONS:
                    matches = [s for s in spans if s.marker == marker]
                    if len(matches) != 1 or not any(l.strip() for l in change.body.splitlines()[
                            matches[0].heading_line:matches[0].end_line]):
                        report.add("AUT002", cid, "approved mandate has a missing or ambiguous normative section")
                classified = index.artifact(change.meta.get("icg"), kind="impact-classification")
                icg = classified.target.artifact if classified.target else None
                if not icg or icg.meta.get("status") != "accepted":
                    report.add("AUT002", cid, "accepted classification is unavailable in the trusted base")
                    continue
                latest_icg = current.get(icg.rel)
                api.check_front_matter(icg, registry, report)
                if not latest_icg or normative(latest_icg) != normative(icg) or latest_icg.meta.get("status") != "accepted":
                    report.add("AUT002", cid, "selected classification is no longer accepted on the approved branch")
                lookup = index.impacts_for(change, icg)
                if lookup.problems or not lookup.matched:
                    report.add("AUT002", cid, "candidate classification does not resolve in its approved scope")
                if "architecture" in lookup.impacts:
                    decisions = [index.artifact(ref, kind="decision-record").target
                                 for ref in as_list(change.meta.get("derives_from"))]
                    if not any(d and d.artifact.meta.get("status") == "accepted" for d in decisions):
                        report.add("AUT002", cid, "architecture mandate lacks an accepted decision in the trusted base")
                binding = policy["mandates"].get(change.rel)
                if not binding:
                    report.add("AUT004", cid, "no approved machine-readable path/obligation/test binding; scope is not inferred")
                    continue
                required.update(binding["tests"])
                required_repositories.update(binding["repositories"])
                for rid, paths in binding["paths"].items():
                    allowed.setdefault(rid, set()).update(relative(p) for p in paths)
                obligations = binding["obligations"]
                for impact in sorted(set(lookup.impacts) & OBLIGES.keys()):
                    wanted = OBLIGES[impact]
                    matching = [o for o in obligations if o["impact"] == impact]
                    if not matching:
                        report.add("AUT005", cid, "impact has no approved binding to its relevant artifact")
                    for obligation in matching:
                        path = relative(obligation["path"])
                        old, new = by_path.get(path), proposed.get(path)
                        if new:
                            api.check_front_matter(new, registry, report)
                        if (not new or new.type != wanted or path not in changes["documents"]
                                or (old and old.type != wanted)):
                            report.add("AUT005", path, "the specifically bound artifact was not updated")
                        elif impact == "data":
                            previous = api.semver(old.meta.get("version")) if old else (0, 0, 0)
                            new_version = api.semver(new.meta.get("version"))
                            if previous is None or new_version is None or new_version <= previous:
                                report.add("AUT005", path, "the affected data contract has no increasing semantic version")
                if binding["repositories"] and not binding["tests"]:
                    report.add("EVI003", cid, "code mandate has no mandatory execution tests")
            if set(control["repositories"]) != required_repositories:
                report.add("AUT004", "repositories", "observed code set omits a required repository or includes an unbound one")
            for rid, paths in changes.items():
                for path in paths:
                    if rid == "documents" and path in blocked:
                        continue
                    if not permits(path, allowed.get(rid, ())):
                        report.add("AUT004", path, "changed path is outside the approved machine-readable scope")
        for path in changes["documents"]:
            old, new = by_path.get(path), proposed.get(path)
            if old and old.meta.get("lifecycle") == "immutable" and (not new or normative(old) != normative(new)):
                report.add("AUT003", path, "historical immutable content changed; create a superseding artifact")
        if not required <= policy["tests"].keys():
            raise MemoryInputError("mandatory tests are missing from the approved policy")
        details["evidence"] = verify_receipts(control["receipts"], policy["tests"], required,
                                             set(control["selected_tests"]), code_set, document, policy_hash, report)
        if ids and not any(f.code.startswith(("AUT", "FM")) for f in report.findings):
            details["authorization"] = "verified-against-caller-trusted-base"
    except (MemoryInputError, OSError, ValueError, TypeError, KeyError, RecursionError, yaml.YAMLError, jsonschema.ValidationError):
        # Do not print source bodies, checkout paths, or arbitrary exception strings.
        report.add("AUT001", "trusted inputs", "required authority, policy, history, source or receipt is unavailable/invalid")
        details["authorization"] = "not-verified"
    return dict(schema="framework-memory/contribution-report/v1", **details,
                gate="failed" if report.findings else "passed", findings=[f.as_json() for f in report.findings],
                limitations=["caller must authenticate repository identities, approved tips, runtime and receipt witnesses",
                             "path scope and artifact updates do not prove semantic preservation or complete impact",
                             "human review and repository protections remain required; no merge or deployment was performed"])


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise MemoryInputError("duplicate JSON key")
        result[key] = value
    return result


def main(args, api):
    if (args.emit_index or args.check or args.list_checks or args.stale_days is not None
            or args.changed_files or args.pr_text is not None or not args.trust_input or not args.pr_text_file):
        raise SystemExit("strict-contribution requires --trust-input and --pr-text-file; no writes or caller path list")
    try:
        control = read_json(args.trust_input)
        if str(args.pr_text_file) == "-":
            raise MemoryInputError("strict PR metadata requires a bounded regular file")
        from .memory.framework_sources import local_bytes
        text = local_bytes(args.pr_text_file.absolute().parent, args.pr_text_file.name).decode("utf-8")
        result = evaluate(control, text, api)
        validate("contribution-report", result)
    except (OSError, ValueError, TypeError, KeyError, RecursionError, yaml.YAMLError, jsonschema.ValidationError):
        print('{"profile":"strict-contribution","gate":"unavailable","authorization":"not-verified","review_required":true}')
        return 2
    print(canonical(result).decode(), end="")
    return 0 if result["gate"] == "passed" else 1
