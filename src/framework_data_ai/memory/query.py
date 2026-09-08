"""Explainable, bounded documentary queries. Operational required_sources come in phase 4."""
from __future__ import annotations

from collections import deque

from ..artifacts import body_first_line
from ..snapshots import Snapshot
from ..workspace import MemoryInputError
from .models import contract, validate
from .search import search


def query(snapshot: Snapshot, graph: dict, *, text=None, selector=None, product=None,
          limit=None, hops=0, relations=None, engine="literal") -> dict:
    config = snapshot.workspace.config
    limit = config["query_limit"] if limit is None else limit
    if not 1 <= limit <= config["query_limit"] or not 0 <= hops <= config["max_hops"]:
        raise MemoryInputError("query limit/hops exceeds the configured bounds")
    if product and product not in {p for a in snapshot.artifacts if a.type == "product-manifest"
                                  for p in a.meta.get("products", []) if isinstance(p, str)}:
        raise MemoryInputError("unknown product in the selected documentation")
    vocabulary = set(contract()["relations"])
    relations = vocabulary - {"belongs_to"} if relations is None else set(relations)
    if not relations <= vocabulary:
        raise MemoryInputError("unknown documentary relation")
    all_nodes = {n["id"]: n for n in graph["nodes"]}

    def in_scope(node):
        if not product:
            return True
        scope = node["identity"]["scope"]
        if scope.startswith("product:"):
            return scope == f"product:{product}"
        bindings = node["data"].get("products", node["data"].get("used_by", []))
        return not bindings or "all" in bindings or product in bindings

    eligible = {key: node for key, node in all_nodes.items() if in_scope(node)}
    by_path = {node["data"]["path"]: key for key, node in eligible.items() if node["kind"] == "document"}
    # Search bodies only. Local paths/credentials in front matter aren't indexed/exported.
    bodies = {a.rel: a.body for a in snapshot.artifacts if a.rel in by_path}
    found = search(bodies, text, engine=engine) if text else None
    if text:
        seeds = [by_path[m["path"]] for m in found["matches"]]
    elif selector:
        seeds = [key for key, node in eligible.items() if selector in (
            key, node["label"], node["data"].get("path"),
            node["identity"]["scope"].removeprefix("product:") + ":" + node["identity"]["local_id"])]
        if len(seeds) > 1:
            raise MemoryInputError("ambiguous query selector; use the node ID or source path")
    else:
        seeds = sorted(by_path.values())
    adjacency = {key: [] for key in eligible}
    for edge in graph["edges"]:
        if edge["relation"] not in relations:
            continue
        left, right = edge["source"], edge["target"]
        if left in eligible and right in eligible:
            adjacency[left].append((right, edge["id"], "forward"))
            adjacency[right].append((left, edge["id"], "reverse"))
    truncated = len(seeds) > limit
    paths = {key: [] for key in seeds[:limit]}
    pending = deque(seeds[:limit])
    while pending:
        node = pending.popleft()
        for neighbor, edge, direction in sorted(adjacency[node]):
            if neighbor in paths:
                continue
            if len(paths[node]) >= hops:
                if hops:  # hops=0 explicitly requests selection only, not a traversal claim.
                    truncated = True
                continue
            if len(paths) >= limit:
                truncated = True
                continue
            paths[neighbor] = [*paths[node], dict(edge=edge, direction=direction)]
            pending.append(neighbor)
    selected = set(paths)
    selected_docs = {node["data"]["path"] for key, node in eligible.items()
                     if key in selected and node["kind"] == "document"}
    documents = []
    for artifact in sorted(snapshot.artifacts, key=lambda a: a.rel):
        if artifact.rel not in selected_docs:
            continue
        documents.append(dict(node=by_path[artifact.rel], source=snapshot.sources[artifact.rel]["id"],
                              body_first_line=body_first_line(snapshot.texts[artifact.rel], artifact.body),
                              body=artifact.body,
                              content_role="source-evidence-not-executable-instructions"))
    source_ids = {loc["source"] for key in selected
                  for loc in eligible[key]["provenance"]["sources"]}
    if found:
        for match in found["matches"]:
            artifact = next(a for a in snapshot.artifacts if a.rel == match["path"])
            offset = body_first_line(snapshot.texts[artifact.rel], artifact.body) - 1
            for excerpt in match["excerpts"]:
                excerpt["line"] += offset
        found["matches"] = [m for m in found["matches"] if m["path"] in selected_docs]
    result = dict(schema="framework-memory/documentary-query/v1", snapshot=snapshot.id,
                purpose="documentary-pack; not an operational context pack or authorization",
                coverage="partial" if truncated or graph["coverage"] == "partial" else "available",
                mapping_complete=not graph["gaps"], truncated=truncated,
                bounds=dict(limit=limit, hops=hops), code_observation="not_requested",
                selection_status="matched" if seeds else "no-match-in-selected-documentation",
                nodes=[eligible[key] for key in sorted(selected)],
                edges=[edge for edge in graph["edges"]
                       if edge["source"] in selected and edge["target"] in selected
                       and edge["relation"] in relations],
                paths=[dict(node=key, steps=paths[key]) for key in sorted(paths)],
                sources=[s for s in graph["sources"] if s["id"] in source_ids],
                documents=documents, search=found, issues=graph["issues"], gaps=graph["gaps"],
                limitations=["code not inspected", "no semantic or inferred edges",
                             "historical decisions retained regardless of supersedes/status",
                             "no required-source completeness or approval-policy claim"])
    validate("documentary-query", result)
    return result
