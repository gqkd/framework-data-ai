"""Compare declared intent with bounded structural changes; never infer zero impact."""
from __future__ import annotations

from collections import deque

from ..artifacts import as_list, as_map
from ..workspace import MemoryInputError
from .code_graph import under
from .context import mandate, reference_index, select_change
from .models import canonical
from .operational_io import seal, verify_code


def predicted(snapshot, graph, change):
    result = dict(change=change.rel if change else None, targets=[], preserves=[], candidates=[],
                  gaps=[], impact_attribution="candidate-only; not distributed over components")
    if change is None:
        result["gaps"].append("no-change-selected")
        return result
    index = reference_index(snapshot)
    node = next(n for n in graph["nodes"] if n["kind"] == "document" and n["data"]["path"] == change.rel)
    for field in ("targets", "preserves"):
        result[field] = [dict(node=e["target"], edge=e["id"], provenance=e["provenance"])
                         for e in graph["edges"] if e["source"] == node["id"] and e["relation"] == field]
        if field not in change.meta:
            result["gaps"].append(field + "-not-declared")
        elif len(result[field]) != len(as_list(change.meta[field])):
            result["gaps"].append(field + "-unresolved")
    found = index.artifact(change.meta.get("icg"), kind="impact-classification")
    if not found.target:
        result["gaps"].append("classification-unresolved")
        return result
    icg = found.target.artifact
    lookup = index.impacts_for(change, icg)
    result["gaps"] += list(lookup.problems)
    icg_node = next(n for n in graph["nodes"] if n["kind"] == "document" and n["data"]["path"] == icg.rel)
    for identity in lookup.matched:
        keys = [key for key in as_map(icg.meta.get("routing"))
                if index.normalize_candidate(key, icg).identity == identity]
        if len(keys) != 1:
            result["gaps"].append("classification-key-ambiguous")
            continue
        key = keys[0]
        rows = [row for row in icg_node["data"].get("subjects", []) if row["routing_key"] == key]
        result["candidates"].append(dict(candidate=dict(document_repository=identity.document_repository,
                                                       scope=identity.scope, local_id=identity.local_id),
                                          source=snapshot.sources[icg.rel],
                                          categories=as_list(as_map(icg.meta.get("impacts")).get(key)),
                                          subjects=rows[0]["components"] if len(rows) == 1 else [],
                                          mapping_status=rows[0]["mapping_status"] if len(rows) == 1 else "undeclared"))
    return result


def traverse(graph, changed, *, hops, limit, direction):
    """File-level projection of direct, resolved provider edges, preserving edge IDs.

    Same-file containment is bookkeeping, not an extra inferred dependency. Cycles visit
    each file once. Cross-repository nominal matches never become traversal edges.
    """
    nodes = {n["id"]: n for n in graph["nodes"]}
    keys = {(n["repository"], n["file"]) for n in graph["nodes"] if n["file"]}
    adjacency = {key: [] for key in keys}
    for edge in graph["edges"]:
        if edge["resolution"] != "resolved" or edge["relation"] == "contains":
            continue
        source, target = nodes[edge["source"]], nodes[edge["target"]]
        left, right = (source["repository"], source["file"]), (target["repository"], target["file"])
        if left == right or not source["file"] or not target["file"]:
            continue
        if direction in ("dependencies", "both"):
            adjacency[left].append((right, edge["id"], "forward"))
        if direction in ("dependents", "both"):
            adjacency[right].append((left, edge["id"], "reverse"))
    seeds = sorted(set(changed) & keys)
    paths = {key: [] for key in seeds[:limit]}
    pending = deque(paths)
    stops = set()
    if len(seeds) > limit:
        stops.add("node-budget")
    while pending:
        current = pending.popleft()
        for neighbor, edge, edge_direction in sorted(adjacency[current]):
            if neighbor in paths:
                continue
            if len(paths[current]) >= hops:
                stops.add("hop-limit")
                continue
            if len(paths) >= limit:
                stops.add("node-budget")
                continue
            paths[neighbor] = [*paths[current], dict(edge=edge, direction=edge_direction)]
            pending.append(neighbor)
    return dict(snapshot=graph["snapshot"], direction=direction, hops=hops, limit=limit,
                truncated=bool(stops), stops=sorted(stops),
                paths=[dict(repository=repo, path=path, steps=steps) for (repo, path), steps in sorted(paths.items())])


def component_subjects(graph, node_ids):
    """Project explicit object targets to components, without semantic guesses."""
    nodes = {n["id"]: n for n in graph["nodes"]}
    result = {}
    for node_id in node_ids:
        node = nodes[node_id]
        components = {node_id} if node["kind"] == "component" else set()
        roots = {n["id"] for n in graph["nodes"] if n["kind"] == "code-root"
                 and (n["id"] == node_id or n["data"]["repository"] == node_id)}
        for edge in graph["edges"]:
            if edge["relation"] == "realized_in" and edge["target"] in roots:
                components.add(edge["source"])
            if edge["source"] == node_id and edge["relation"] in ("documents", "applies_to"):
                if nodes[edge["target"]]["kind"] == "component":
                    components.add(edge["target"])
        result[node_id] = components
    return result


def compare(snapshot, graph, *, before=None, after=None, change=None, hops=3, limit=100, direction="dependents"):
    if type(hops) is not int or not 0 <= hops <= snapshot.workspace.config["max_hops"]:
        raise MemoryInputError("impact traversal exceeds the configured hop bound")
    if type(limit) is not int or not 1 <= limit <= snapshot.workspace.config["query_limit"]:
        raise MemoryInputError("impact traversal exceeds the configured node bound")
    if direction not in ("dependents", "dependencies", "both"):
        raise MemoryInputError("invalid impact traversal direction")
    if graph["snapshot"] != snapshot.id:
        raise MemoryInputError("impact graph and document snapshot disagree")
    for bundle in (before, after):
        if bundle is not None:
            verify_code(bundle)
            if bundle["inputs"].get("document_repository") != snapshot.inputs["document_repository"]:
                raise MemoryInputError("code snapshot document namespace is missing or differs; re-observe with this generator")
    if after and after["graph"]["document_snapshot"] != snapshot.id:
        raise MemoryInputError("after snapshot belongs to different documentation; rebuild it explicitly")
    selected_change = select_change(snapshot, change)
    plan = predicted(snapshot, graph, selected_change)
    changed, uncertain, traversals, mapped = [], [], [], []
    document_nodes = {n["id"]: n for n in graph["nodes"]}
    if before is None or after is None:
        uncertain.append(dict(reason="two-explicit-code-snapshots-required"))
    else:
        if before["graph"]["provider"] != after["graph"]["provider"]:
            uncertain.append(dict(reason="provider-profiles-differ"))
        inventories = [b["inputs"]["repositories"] for b in (before, after)]
        declared = {n["data"]["repository"] for n in graph["nodes"] if n["kind"] == "repository"}
        for repo in sorted(declared - (set(inventories[0]) & set(inventories[1]))):
            uncertain.append(dict(repository=repo, reason="declared-repository-not-observed-on-both-sides"))
        captured = [{(s["repository"], s["path"]): s["revision"] for s in b["graph"]["sources"]}
                    for b in (before, after)]
        for repo in sorted(set(inventories[0]) | set(inventories[1])):
            left, right = (inv.get(repo, {}) for inv in inventories)
            if "inventory" not in left or "inventory" not in right:
                uncertain.append(dict(repository=repo, reason="repository-not-observed-on-both-sides"))
                continue
            if (left["mode"], left["include_untracked"]) != (right["mode"], right["include_untracked"]):
                uncertain.append(dict(repository=repo, reason="capture-policies-differ"))
            for path in sorted(set(left["inventory"]) | set(right["inventory"])):
                old, new = (values.get((repo, path)) for values in captured)
                index_changed = left["inventory"].get(path) != right["inventory"].get(path)
                if old != new or index_changed:
                    changed.append(dict(repository=repo, path=path, before=old, after=new,
                                        basis="captured-bytes" if old != new else "git-inventory",
                                        status="changed" if old and new else "added-or-newly-observed" if new else "removed-or-no-longer-observed"))
                if old is None or new is None:
                    uncertain.append(dict(repository=repo, path=path, reason="not-byte-observed-on-both-sides"))
        seeds = [(row["repository"], row["path"]) for row in changed]
        for side, bundle in (("before", before), ("after", after)):
            cg = bundle["graph"]
            walked = traverse(cg, seeds, hops=hops, limit=limit, direction=direction)
            walked["side"] = side
            traversals.append(walked)
            affected_files = set(seeds) | {(r["repository"], r["path"]) for r in walked["paths"]}
            for bridge in cg["bridges"]:
                matched = sorted(path for repo, path in affected_files if repo == bridge["repository"] and under(path, bridge["path"]))
                if matched:
                    mapped.append(dict(side=side, snapshot=cg["snapshot"], component=bridge["component"],
                                       component_reference=document_nodes.get(bridge["component"], {}).get("label"),
                                       repository=bridge["repository"], root=bridge["path"], view=bridge["view"],
                                       paths=matched, declaration=bridge["declaration"],
                                       meaning="structural-location-match-not-functional-impact"))
            for row in cg["repositories"]:
                if row["observation"]["observation_status"] != "available":
                    uncertain.append(dict(side=side, repository=row["repository"], reason="partial-or-unavailable-repository",
                                          coverage=row["coverage"], problems=row["problems"]))
            unresolved = [e["id"] for e in cg["edges"] if e["resolution"] == "unresolved"]
            if unresolved:
                uncertain.append(dict(side=side, reason="unresolved-direct-edges", edges=unresolved))
            bridged = {(row["repository"], path) for row in mapped if row["side"] == side for path in row["paths"]}
            for repo, path in sorted(affected_files - bridged):
                uncertain.append(dict(side=side, repository=repo, path=path, reason="no-component-root-mapping"))
    target_objects = component_subjects(graph, [r["node"] for r in plan["targets"]])
    preserved_objects = component_subjects(graph, [r["node"] for r in plan["preserves"]])
    intended = {n for subjects in target_objects.values() for n in subjects} | {n for c in plan["candidates"] for n in c["subjects"]}
    observed = {r["component"] for r in mapped if r["view"] == "current"}
    # A missing structural match can never establish preservation or functional safety.
    comparison = dict(observed_beyond_declared_components=sorted(observed - intended),
                      declared_components_without_observed_match=sorted(intended - observed),
                      preserved_objects_with_structural_match=sorted(n for n, subjects in preserved_objects.items() if subjects & observed),
                      declared_objects_without_component_mapping=sorted(n for n, subjects in
                                                                         {**target_objects, **preserved_objects}.items() if not subjects),
                      semantics="differences-to-review; not regression, compliance or preservation proof")
    for issue in graph["issues"]:
        uncertain.append(dict(reason="documentary-issue", issue=issue))
    for gap in graph["gaps"]:
        uncertain.append(dict(reason="documentary-mapping-gap", gap=gap))
    truncated = any(t["truncated"] for t in traversals)
    result = dict(schema="framework-memory/impact/v1", document_snapshot=snapshot.id,
                  predicted=plan, mandate=mandate(snapshot, graph, selected_change),
                  observed=dict(before=before["graph"]["snapshot"] if before else None,
                                after=after["graph"]["snapshot"] if after else None,
                                freshness="not-rechecked", changed_files=changed, components=sorted(mapped, key=canonical),
                                traversals=traversals, truncated=truncated),
                  comparison=comparison, hypotheses=[], uncertainties=uncertain,
                  coverage="partial" if before and after else "unavailable",
                  conclusion="structural-changes-observed" if changed else "no-structural-change-established-in-selected-snapshots",
                  limitations=["static observations never exclude runtime, semantic or cross-repository impact",
                               "snapshots are explicit historical inputs; current checkouts were not read",
                               "unsupported or missing files cannot establish absence of change",
                               "target/design mappings are not current implementation",
                               "incomplete mappings and traversal limits retain unexamined consequences",
                               "a component test does not attest all consumers or production",
                               "no test command executed and no authorization or functional correctness attested"])
    snapshot.assert_unchanged()
    return seal(result, "impact")
