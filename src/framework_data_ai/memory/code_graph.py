"""Separate code graph and documentary-root bridge. No inferred impact or authority."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from ..snapshots import ConcurrentChange, publish_payload
from ..workspace import MemoryInputError
from .code_sources import capture_code, safe_path
from .models import canonical, digest, validate
from .providers.base import Observation

STRUCTURAL = {"module", "symbol", "dependency", "test_ref", "file_ref"}
DIRECT = {"calls", "imports", "declares", "implements", "instantiates", "names"}


def structural_record(record):
    # Provider aggregate/derived rows remain in records, never in the direct graph.
    return record.get("kind") in STRUCTURAL and "derived" not in record.get("props", {})


def identifier(kind, *values):
    return kind + ":" + digest(canonical(values))


def under(path, root):
    return root == "." or path == root or path.startswith(root + "/")


def provenance(records=(), locations=(), rule="provider-direct-fact"):
    return dict(source_kind="code", assertion_method="derived", records=sorted(set(records)),
                locations=sorted(locations, key=canonical), rule=dict(id=rule, version="1"))


@dataclass
class CodeBuild:
    document: object
    captures: list
    bindings: dict
    provider: object
    provider_state: dict
    graph: dict
    inputs: dict

    def assert_unchanged(self):
        self.document.assert_unchanged()
        if (self.document.workspace.local_bindings() != self.bindings
                or self.provider.status() != self.provider_state):
            raise ConcurrentChange("code bindings or provider changed; code snapshot not published")
        for repo, inputs in self.inputs["repositories"].items():
            if repo in self.bindings and inputs.get("path_status") in ("missing", "present"):
                bound = Path(self.bindings[repo])
                bound = bound if bound.is_absolute() else self.document.workspace.root / bound
                if ("present" if bound.is_dir() else "missing") != inputs["path_status"]:
                    raise ConcurrentChange("code repository availability changed; code snapshot not published")
        for capture in self.captures:
            capture.assert_unchanged()

    def publish(self):
        validate_code_graph(self.graph)
        unsigned = dict(self.graph, snapshot="")
        if (self.graph["snapshot"] != digest(canonical(self.inputs))
                or digest(canonical(unsigned)) != self.inputs["normalized_observation"]):
            raise MemoryInputError("code graph and input identities disagree")
        data = canonical(self.graph)
        manifest = dict(schema="framework-memory/manifest/v1", id=self.graph["snapshot"], inputs=self.inputs,
                        files={"code-graph.json": digest(data)})
        validate("manifest", manifest)
        publish_payload(self.document.workspace.root, "code-snapshots", self.graph["snapshot"],
                        {"code-graph.json": data, "manifest.json": canonical(manifest)}, self.assert_unchanged)
        return manifest


def build_code(snapshot, documentary, provider, *, repositories=None, mode="worktree", revision=None,
               include_untracked=False):
    if documentary["snapshot"] != snapshot.id:
        raise MemoryInputError("documentary graph and source snapshot disagree")
    bindings = snapshot.workspace.local_bindings()
    declared = {}
    for node in documentary["nodes"]:
        if node["kind"] == "repository":
            declared.setdefault(node["data"]["repository"], []).append(node)
    selected = sorted(set(repositories if repositories is not None else declared))
    if any(repo not in declared for repo in selected):
        raise MemoryInputError("code selection names an undeclared repository")
    if revision is not None and len(selected) != 1:
        raise MemoryInputError("an explicit Git revision selects exactly one repository")
    if (mode == "git") != (revision is not None):
        raise MemoryInputError("Git observation requires an explicit commit; no HEAD fallback")
    provider_state = provider.status()
    document_id = snapshot.workspace.config["document_repository"]
    nodes, edges, sources, raw_records, repos, captures = {}, {}, [], [], [], []
    input_repos = {}
    for repo in selected:
        declarations = declared[repo]
        capture = None
        path_status = "unresolved"
        observation = Observation("unavailable", problems=[dict(code="binding-unavailable")])
        if len(declarations) != 1:
            observation.problems = [dict(code="ambiguous-repository-declaration")]
        elif repo in bindings:
            bound = Path(bindings[repo])
            bound = bound if bound.is_absolute() else snapshot.workspace.root / bound
            path_status = "present" if bound.is_dir() else "missing"
            if provider_state["status"] != "available":
                observation.problems = [dict(code="provider-unavailable")]
            else:
                try:
                    capture = capture_code(bound, mode=mode, revision=revision, include_untracked=include_untracked)
                    captures.append(capture)
                    observation = provider.extract(capture.files)
                    accounted = {row["path"] for row in observation.coverage}
                    for path in sorted(set(capture.files) - accounted):
                        observation.coverage.append(dict(path=path, status="unavailable", reason="provider-coverage-missing"))
                    if observation.status == "available" and set(capture.files) - accounted:
                        observation.status = "partial"
                    capture.assert_unchanged()
                except ConcurrentChange:
                    raise
                except (MemoryInputError, OSError):
                    observation = Observation("unavailable", problems=[dict(code="source-unavailable")])
        unprojected = sum(not structural_record(r) for r in observation.records)
        indirect = sum(e.get("kind") not in DIRECT for r in observation.records for e in r.get("relations", []))
        if unprojected or indirect:
            observation.problems.append(dict(code="provider-evidence-not-projected", records=unprojected, relations=indirect))
            if observation.status == "available":
                observation.status = "partial"
        input_repos[repo] = capture.inputs if capture else dict(mode=mode, revision=revision, path_status=path_status)
        coverage = (capture.coverage if capture else []) + observation.coverage
        coverage = sorted(coverage, key=canonical)
        status = observation.status
        if coverage and status == "available" and any(c["status"] != "available" for c in coverage):
            status = "partial"
        state = dict(path_status=path_status, observation_status=status,
                     freshness="current" if capture and mode == "worktree" else "unknown")
        repos.append(dict(repository=repo, observation=state, coverage=coverage, problems=observation.problems,
                          evidence=observation.evidence, insights=observation.insights))
        if not capture:
            continue
        file_nodes, source_by_path = {}, {}
        status_by_path = {row["path"]: row["status"] for row in coverage}
        for path, data in sorted(capture.files.items()):
            source_id = identifier("code-source", document_id, repo, path, digest(data))
            source = dict(id=source_id, repository=repo, path=path, revision="sha256:" + digest(data),
                          lines=max(1, len(data.splitlines())))
            source_by_path[path] = source
            sources.append(source)
            node_id = identifier("code-node", document_id, repo, "file", path)
            file_nodes[path] = node_id
            zones = sorted({z["kind"] for z in declarations[0]["data"].get("zones", []) if under(path, z["path"])})
            observed = status_by_path.get(path, "unavailable")
            observed = observed if observed in ("available", "partial", "unavailable") else "unavailable"
            nodes[node_id] = dict(id=node_id, kind="file", repository=repo, name=path, file=path,
                                  provenance=provenance(locations=[dict(source=source_id, start_line=1,
                                                                       end_line=source["lines"])], rule="captured-file"),
                                  observation=dict(path_status="present", observation_status=observed,
                                                   freshness=state["freshness"]), zones=zones or ["normal"])
        retained = {}
        record_rows = []
        # Sorting and exact-record occurrence retain multiplicity without depending on provider order.
        occurrences = {}
        for record in sorted(observation.records, key=canonical):
            key = digest(canonical(record))
            occurrence = occurrences.get(key, 0)
            occurrences[key] = occurrence + 1
            record_id = identifier("provider-record", document_id, repo, key, occurrence)
            raw_records.append(dict(id=record_id, repository=repo, occurrence=occurrence,
                                    role="provider-evidence-not-authority", record=record))
            if not structural_record(record):
                continue  # Kept as provider evidence, not promoted to structural fact.
            provider_id = record["id"]
            identity = (record["kind"], record["name"], record.get("file", ""))
            if provider_id in retained and retained[provider_id][0] != identity:
                raise MemoryInputError("provider reused one identity for different entities")
            node_id = identifier("code-node", document_id, repo, provider.capabilities.name, *identity)
            retained[provider_id] = identity, node_id
            locations = []
            path = record.get("file", "")
            if path in source_by_path and "line" in record:
                locations.append(dict(source=source_by_path[path]["id"], start_line=record["line"],
                                      end_line=record.get("end_line", record["line"])))
            if node_id not in nodes:
                nodes[node_id] = dict(id=node_id, kind=record["kind"], repository=repo, name=record["name"], file=path,
                                      provenance=provenance(), observation=dict(path_status="present" if path else "not_applicable",
                                      observation_status=observation.status, freshness=state["freshness"]), zones=[])
            prov = nodes[node_id]["provenance"]
            prov["records"].append(record_id)
            prov["locations"] = sorted({canonical(loc): loc for loc in prov["locations"] + locations}.values(), key=canonical)
            record_rows.append((record_id, record, node_id, locations))
            if path in file_nodes:
                edge_id = identifier("code-edge", file_nodes[path], node_id, "contains", record_id)
                edges[edge_id] = dict(id=edge_id, relation="contains", source=file_nodes[path], target=node_id,
                                     target_name=record["name"], resolution="resolved",
                                     provenance=provenance([record_id], locations, "file-contains-entity"))
        for record_id, record, node_id, locations in record_rows:
            for position, relation in enumerate(sorted(record.get("relations", []), key=canonical)):
                if relation["kind"] not in DIRECT:
                    continue
                target = retained.get(relation.get("target_id"))
                # Explicit provider IDs only. Even a unique nominal match is NOT a binding.
                if target and target[0][1] != relation["target"]:
                    raise MemoryInputError("provider target identity disagrees with its name")
                edge_id = identifier("code-edge", record_id, relation, position)
                edges[edge_id] = dict(id=edge_id, relation=relation["kind"], source=node_id,
                                     target=target[1] if target else None, target_name=relation["target"],
                                     resolution="resolved" if target else "unresolved",
                                     provenance=provenance([record_id], locations))
                if "target_id" in relation:
                    edges[edge_id]["target_provider_id"] = relation["target_id"]
        if any(e["resolution"] == "unresolved" and nodes[e["source"]]["repository"] == repo for e in edges.values()):
            if state["observation_status"] == "available":
                state["observation_status"] = "partial"
            repos[-1]["problems"].append(dict(code="unresolved-direct-edges"))
    # Bridge root declarations to file observations without adding code nodes to the document graph.
    node_lookup = {n["id"]: n for n in documentary["nodes"]}
    repo_lookup = {declared[r][0]["id"]: r for r in selected if len(declared[r]) == 1}
    bridges = []
    for edge in documentary["edges"]:
        if edge["relation"] != "realized_in":
            continue
        root = node_lookup[edge["target"]]
        repo = repo_lookup.get(root["data"]["repository"])
        if repo is None:
            continue
        path = root["data"]["path"]
        matched = sorted(n["id"] for n in nodes.values() if n["kind"] == "file" and
                         n["repository"] == repo and under(n["file"], path))
        inventory = input_repos[repo].get("inventory", {})
        observed_repo = next(r for r in repos if r["repository"] == repo)["observation"]
        has_capture = "inventory" in input_repos[repo]
        missing_paths = {c["path"] for c in input_repos[repo].get("coverage", [])
                         if c.get("reason") == "worktree-file-missing"}
        present = any(under(p, path) and p not in missing_paths for p in inventory)
        bridges.append(dict(component=edge["source"], root=root["id"], repository=repo, path=path,
                            view=root["data"]["view"], files=matched,
                            meaning="declared-location-match-not-proof-of-implementation",
                            observation=dict(path_status=("present" if present else "missing") if has_capture else "unresolved",
                                             observation_status=observed_repo["observation_status"] if present else "unavailable",
                                             freshness=observed_repo["freshness"]),
                            declaration=edge["provenance"]))
    statuses = [r["observation"]["observation_status"] for r in repos]
    coverage = ("unavailable" if not statuses or all(s == "unavailable" for s in statuses) else
                "partial" if any(s != "available" for s in statuses) else "available")
    capabilities = asdict(provider.capabilities)
    capabilities["languages"] = list(capabilities["languages"])
    capabilities["direct_edges"] = list(capabilities["direct_edges"])
    graph = dict(schema="framework-memory/code-graph/v1", snapshot="", document_snapshot=snapshot.id,
                 coverage=coverage, provider=dict(capabilities, status=provider_state),
                 repositories=repos, sources=sorted(sources, key=lambda s: s["id"]),
                 nodes=sorted(nodes.values(), key=lambda n: n["id"]), edges=sorted(edges.values(), key=lambda e: e["id"]),
                 records=sorted(raw_records, key=lambda r: r["id"]), bridges=sorted(bridges, key=canonical),
                 limitations=["direct static observations, not runtime behavior or absence of impact",
                              "nominal and cross-repository targets remain unresolved without verified bindings",
                              "zones classify; they never exclude code or establish irrelevance",
                              "target/design root matches do not attest implementation",
                              "provider annotations and insights are evidence, not decisions"])
    graph["limitations"].append("Git-ignored untracked files are not inventoried; absent edges never prove irrelevance")
    inputs = dict(document_snapshot=snapshot.id, document_repository=document_id,
                  provider=graph["provider"], repositories=input_repos,
                  normalized_observation=digest(canonical(graph)))
    graph["snapshot"] = digest(canonical(inputs))
    result = CodeBuild(snapshot, captures, bindings, provider, provider_state, graph, inputs)
    validate_code_graph(graph)
    result.assert_unchanged()
    return result


def validate_code_graph(graph):
    validate("code-graph", graph)
    nodes = {node["id"]: node for node in graph["nodes"]}
    records = {record["id"] for record in graph["records"]}
    sources = {source["id"]: source for source in graph["sources"]}
    if len(nodes) != len(graph["nodes"]) or len(records) != len(graph["records"]) or len(sources) != len(graph["sources"]):
        raise MemoryInputError("code graph contains duplicate canonical identities")
    if len({e["id"] for e in graph["edges"]}) != len(graph["edges"]):
        raise MemoryInputError("code graph contains duplicate edge identities")
    for item in graph["nodes"] + graph["edges"]:
        prov = item["provenance"]
        if any(r not in records for r in prov["records"]):
            raise MemoryInputError("code graph provenance is missing provider evidence")
        for loc in prov["locations"]:
            if loc["source"] not in sources or not 1 <= loc["start_line"] <= loc["end_line"] <= sources[loc["source"]]["lines"]:
                raise MemoryInputError("code graph source location is outside captured input")
    for edge in graph["edges"]:
        if edge["source"] not in nodes or (edge["target"] is not None and edge["target"] not in nodes):
            raise MemoryInputError("code graph edge endpoint is absent")
        if (edge["target"] is not None) != (edge["resolution"] == "resolved"):
            raise MemoryInputError("code graph resolution state is inconsistent")
        if edge["target"] and nodes[edge["source"]]["repository"] != nodes[edge["target"]]["repository"]:
            raise MemoryInputError("cross-repository edge requires a separately verified binding")
    for bridge in graph["bridges"]:
        if any(n not in nodes or nodes[n]["kind"] != "file" or nodes[n]["repository"] != bridge["repository"]
               or not under(nodes[n]["file"], bridge["path"]) for n in bridge["files"]):
            raise MemoryInputError("component bridge is outside its declared root")
