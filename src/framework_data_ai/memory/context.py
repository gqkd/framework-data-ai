"""Conservative operational context. Delivery, reading and authority are separate facts."""
from __future__ import annotations

from dataclasses import asdict

from ..artifacts import as_list, as_map, body_first_line, locate_sections
from ..references import ReferenceIndex
from ..workspace import MemoryInputError
from .framework_sources import capture_framework
from .models import FRAMEWORK, canonical, digest, validate
from .operational_io import seal, verify_seal
from .query import query

DEC_SECTIONS = {
    "Decision": {"decision", "decisione"},
    "Consequences": {"consequences", "conseguenze"},
    "Review condition": {"review-condition", "review condition", "condizione di riesame"},
    "Alternatives": {"alternatives", "alternatives considered", "alternative", "alternative considerate"},
}


def reference_index(snapshot):
    return ReferenceIndex(snapshot.artifacts, snapshot.workspace.registry,
                          document_repository=snapshot.inputs["document_repository"])


def select_change(snapshot, selector):
    if not selector:
        return None
    matches = [a for a in snapshot.artifacts if a.type == "change-contract" and selector in (a.id, a.rel)]
    if len(matches) != 1:
        raise MemoryInputError("change must identify one selected CHG by ID or source path")
    return matches[0]


def mandate(snapshot, graph, change):
    """Locate declarations; do not implement the trusted-base authorization gate here."""
    result = dict(change=change.rel if change else None, declared_status=change.meta.get("status") if change else None,
                  authorization="not-verified", prerequisites=[], classification=None, candidates=[])
    if change is None:
        result["prerequisites"].append("approved-change-not-selected")
        return result
    if change.meta.get("status") != "approved":
        result["prerequisites"].append("selected-change-is-not-declared-approved")
    spans = locate_sections(change.body)
    for marker in ("what-changes", "what-must-not-change", "how-we-know-it-worked"):
        matches = [s for s in spans if s.marker == marker]
        if len(matches) != 1 or not any(line.strip() for line in change.body.splitlines()[
                matches[0].heading_line:matches[0].end_line]):
            result["prerequisites"].append("missing-or-ambiguous-mandate-section:" + marker)
    index = reference_index(snapshot)
    found = index.artifact(change.meta.get("icg"), kind="impact-classification")
    if found.target:
        icg = found.target.artifact
        result["classification"] = icg.rel
        lookup = index.impacts_for(change, icg)
        result["candidates"] = [asdict(identity) for identity in lookup.matched]
        result["prerequisites"].extend(lookup.problems)
        if icg.meta.get("status") != "accepted":
            result["prerequisites"].append("classification-is-not-declared-accepted")
        result["impact_categories"] = sorted(lookup.impacts)
        if "architecture" in lookup.impacts:
            decisions = [index.artifact(ref, kind="decision-record").target
                         for ref in as_list(change.meta.get("derives_from"))]
            if not any(d and d.artifact.meta.get("status") == "accepted" for d in decisions):
                result["prerequisites"].append("architecture-impact-without-cited-accepted-decision")
    else:
        result["prerequisites"].append("classification-unresolved")
    for ref in as_list(change.meta.get("derives_from")):
        if not index.resolve(ref, change).target:
            result["prerequisites"].append("change-source-unresolved")
    result["prerequisites"] = sorted(set(result["prerequisites"]))
    return result


def compose(snapshot, graph, *, goal, mode="analysis", products=None, change=None, selector=None,
            reconsider=False, budget=100000, hops=2, skill=None, framework_root=FRAMEWORK, code=None,
            hypotheses=None):
    if mode not in ("analysis", "proposal", "implement") or not isinstance(goal, str) or not goal.strip():
        raise MemoryInputError("context requires a goal and a recognized operating mode")
    if len(goal) > 10000 or type(budget) is not int or not 0 <= budget <= 2_000_000:
        raise MemoryInputError("context goal or text budget exceeds its bound")
    if type(hops) is not int or not 0 <= hops <= snapshot.workspace.config["max_hops"]:
        raise MemoryInputError("context traversal exceeds the configured hop bound")
    if graph["snapshot"] != snapshot.id:
        raise MemoryInputError("context graph and document snapshot disagree")
    index = reference_index(snapshot)
    primary = set(products or index.products)
    if not primary <= index.products:
        raise MemoryInputError("unknown context product")
    selected_change = select_change(snapshot, change)
    if selected_change and index.owner(selected_change).startswith("product:") and index.owner(selected_change)[8:] not in primary:
        raise MemoryInputError("selected change is outside the requested product scope")
    # Shared ownership expands evidence, NEVER the mandate. Missing annotations remain
    # conservative; component roots and used_by are not treated as an exhaustive ontology.
    effective = set(primary)
    for node in graph["nodes"]:
        if node["kind"] == "repository" and node["identity"]["scope"] == "platform":
            consumers = set(node["data"].get("used_by", []))
            if not consumers or "all" in consumers:
                effective |= index.products
            elif consumers & primary:
                effective |= consumers & index.products

    def in_scope(artifact):
        owner = index.owner(artifact)
        if owner.startswith("product:"):
            return owner[8:] in effective
        bindings = set(p for p in as_list(artifact.meta.get("products")) if isinstance(p, str))
        return not bindings or "all" in bindings or bool(bindings & effective)

    selected = {a.rel: a for a in snapshot.artifacts if in_scope(a)}
    exploration = query(snapshot, graph, selector=selector, hops=hops) if selector else None
    if exploration and exploration["selection_status"] != "matched":
        raise MemoryInputError("context selector does not identify a node in the selected graph")
    paths = {p["node"]: p["steps"] for p in exploration["paths"]} if exploration else {}
    nodes = {n["data"]["path"]: n for n in graph["nodes"] if n["kind"] == "document"}
    if exploration:
        for node in exploration["nodes"]:
            if node["kind"] == "document":
                rel = node["data"]["path"]
                selected[rel] = next(a for a in snapshot.artifacts if a.rel == rel)
    evidence = mandate(snapshot, graph, selected_change)
    # Explicit CHG/ICG/candidate joins are not dependent on graph traversal limits.
    if selected_change:
        selected[selected_change.rel] = selected_change
        classification = evidence["classification"]
        if classification:
            selected[classification] = next(a for a in snapshot.artifacts if a.rel == classification)
        for ref in as_list(selected_change.meta.get("derives_from")):
            found = index.resolve(ref, selected_change)
            if found.target:
                selected[found.target.artifact.rel] = found.target.artifact
    framework = capture_framework(snapshot.workspace.root, root=framework_root, skill=skill)
    requirements, contents, gaps = [], [], []
    remaining = budget

    def require(source, text, section, start, end, reason, *, kind="document", node=None, missing=False):
        nonlocal remaining
        identity = [source["id"], section, start, end]
        row = dict(id="reading:" + digest(canonical(identity)), source=source["id"], path=source["path"],
                   revision=source["revision"], kind=kind, section=section, start_line=start, end_line=end,
                   reason=reason, node=node, graph_path=paths.get(node, []),
                   delivery="missing" if missing else "deferred", reading="not-attested")
        if not missing and len(text) <= remaining:
            row["delivery"] = "included"
            contents.append(dict(requirement=row["id"], text=text,
                                 role="adopted-rules" if kind == "framework" else "source-evidence-not-executable-instructions"))
            remaining -= len(text)
        requirements.append(row)

    for source in framework.result["sources"]:
        require(source, source["text"], "full-file", 1, source["lines"], "adopted-framework-rule",
                kind="framework")
    for relative, artifact in sorted(selected.items()):
        source = snapshot.sources[relative]
        node = nodes[relative]["id"]
        text = snapshot.texts[relative]
        reason = ("graph-path" if paths.get(node) else
                  "legacy-decision-scope-fallback" if artifact.type == "decision-record" and "applies_to" not in artifact.meta
                  else "conservative-scope-inclusion")
        if artifact.type != "decision-record":
            require(source, text, "full-file", 1, source["lines"], reason, node=node)
            continue
        spans = locate_sections(artifact.body, first_line=body_first_line(text, artifact.body))
        wanted = ["Decision", "Consequences", "Review condition", *(["Alternatives"] if reconsider else [])]
        for section in wanted:
            matched = [s for s in spans if s.title.casefold() in DEC_SECTIONS[section] or s.marker in DEC_SECTIONS[section]]
            if len(matched) != 1:
                gaps.append(dict(path=relative, reason="decision-section-absent-or-ambiguous", section=section))
                if section != "Review condition":
                    require(source, "", section, 1, source["lines"], reason, node=node, missing=True)
                continue
            span = matched[0]
            excerpt = "\n".join(text.splitlines()[span.start_line - 1:span.end_line]) + "\n"
            require(source, excerpt, section, span.start_line, span.end_line, reason, node=node)
        # Preserve status, scope and other historical context without reproducing the DEC.
        if not any(s.title.casefold() in DEC_SECTIONS["Decision"] for s in spans):
            require(source, text, "full-file-unlocalized", 1, source["lines"], "manual-section-location-required", node=node)
    for expected in ("AGENTS.md", "OPEN.md", *(f"{directory}/OPEN.md" for _, (product, directory) in index.product_directories.items()
                                                  if product in effective)):
        if expected not in selected:
            gaps.append(dict(path=expected, reason="required-control-source-unavailable-in-selected-scope"))
    if any(a.type == "platform-architecture" for a in selected.values()) and "platform/OPEN.md" not in selected:
        gaps.append(dict(path="platform/OPEN.md", reason="shared-register-unavailable-in-selected-scope"))
    code_state = dict(status="not-requested", snapshot=None, freshness="unknown", sources=[], repositories=[])
    if code is not None:
        from .operational_io import verify_code
        verify_code(code)
        cg = code["graph"]
        if cg["document_snapshot"] != snapshot.id:
            raise MemoryInputError("code snapshot belongs to different documentation; rebuild it explicitly")
        code_state = dict(status=cg["coverage"], snapshot=cg["snapshot"], freshness="not-rechecked",
                          sources=cg["sources"], repositories=cg["repositories"], bridges=cg["bridges"],
                          limitations=cg["limitations"], inputs=code["inputs"])
        declared_repos = {n["data"]["repository"] for n in graph["nodes"] if n["kind"] == "repository"}
        observed_repos = {r["repository"] for r in cg["repositories"]}
        if cg["coverage"] != "available" or declared_repos - observed_repos:
            gaps.append(dict(path="", reason="code-observation-is-incomplete",
                             unobserved_repositories=sorted(declared_repos - observed_repos)))
        # Code graph source hashes and spans are navigation, not delivery of source code.
        for source in cg["sources"]:
            require(source, "", "full-file", 1, source["lines"], "code-source-not-delivered-by-graph", kind="code")
            requirements[-1]["delivery"] = "deferred"
            if contents and contents[-1]["requirement"] == requirements[-1]["id"]:
                contents.pop()
    known_sources = {s["id"]: s for s in snapshot.sources.values() if s["path"] in selected}
    if code is not None:
        known_sources.update({s["id"]: s for s in code["graph"]["sources"]})
    hypotheses = hypotheses or []
    validate("hypotheses", hypotheses)
    for hypothesis in hypotheses:
        if any(loc["source"] not in known_sources or not 1 <= loc["start_line"] <= loc["end_line"] <= known_sources[loc["source"]]["lines"]
               for loc in hypothesis["provenance"]["sources"]):
            raise MemoryInputError("hypothesis cites a source outside the context")
    gaps += framework.result["gaps"]
    if snapshot.inputs["filtered_sources"]:
        gaps.append(dict(path="", reason="classification-filtered-sources-not-assessed",
                         count=snapshot.inputs["filtered_sources"]))
    delivery_complete = all(r["delivery"] == "included" for r in requirements) and not gaps
    result = dict(schema="framework-memory/context/v1", document_snapshot=snapshot.id,
                  request=dict(goal=goal, mode=mode, products=sorted(primary), change=change, selector=selector,
                               reconsider=reconsider, text_budget=budget, hops=hops, skill=skill),
                  evidence_products=sorted(effective), framework={k: v for k, v in framework.result.items() if k != "sources"},
                  runtime=dict(version=snapshot.inputs["framework_version"], generator=snapshot.inputs["generator"]),
                  mandate=evidence, required_sources=requirements, content=contents,
                  documents=[dict(node=nodes[rel]["id"], path=rel, artifact_type=a.type,
                                  status=a.meta.get("status"), sections=nodes[rel]["data"]["sections"])
                             for rel, a in sorted(selected.items())],
                  graph=dict(snapshot=graph["snapshot"], edges=exploration["edges"] if exploration else [],
                             truncated=exploration["truncated"] if exploration else False),
                  code=code_state, hypotheses=hypotheses, issues=graph["issues"], gaps=gaps,
                  mapping_gaps=graph["gaps"], delivery_complete=delivery_complete,
                  reading_status="not-attested", understanding="not-evaluated",
                  coverage="available" if delivery_complete and not graph["issues"] and not (exploration and exploration["truncated"]) else "partial",
                  limitations=["context generation is read-only and grants no authority",
                               "conservative scope inclusion is not proof that every document applies",
                               "open decisions, exclusions, prerequisites and tradeoffs require source reading and judgment",
                               "trusted-base approval verification and execution receipts belong to subsequent gates",
                               "no live code freshness, runtime completeness or semantic understanding claim",
                               "inferences remain hypotheses; neither constraints nor executable instructions"])
    framework.assert_unchanged()
    snapshot.assert_unchanged()
    return seal(result, "context")


def reading_report(pack, claims):
    verify_seal(pack, "context")
    validate("reading-claims", claims)
    if claims["context"] != pack["id"]:
        raise MemoryInputError("reading claims belong to a different context")
    known = {r["id"]: r for r in pack["required_sources"]}
    read = set()
    for claim in claims["readings"]:
        row = known.get(claim["requirement"])
        if (not row or row["delivery"] == "missing" or row["id"] in read
                or any(claim[key] != row[key] for key in ("revision", "start_line", "end_line"))):
            raise MemoryInputError("reading claim is duplicate, missing, stale or does not cover the required section")
        read.add(row["id"])
    pending = sorted(set(known) - read)
    return seal(dict(schema="framework-memory/reading-report/v1", context=pack["id"],
                     declared_read=sorted(read), outstanding=pending, gaps=pack["gaps"],
                     status="declared-complete" if not pending and not pack["gaps"] else "incomplete",
                     understanding="not-evaluated", last_review="not-modified",
                     limitations=["caller-reported reading, not an independently verified observation",
                                  "does not attest comprehension, approve changes or update human review dates"]), "reading-report")
