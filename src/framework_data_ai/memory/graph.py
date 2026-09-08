"""Project explicit documentary facts. Text similarity never emits an authoritative edge."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import re

import jsonschema

from ..artifacts import as_list, as_map, body_first_line, locate_sections
from ..references import Identity, ReferenceIndex
from ..snapshots import Snapshot
from .models import artifact_field, canonical, contract, digest, validate_graph


class DocumentaryGraph:
    def __init__(self, snapshot: Snapshot):
        self.snapshot = snapshot
        self.rules = contract()
        self.index = ReferenceIndex(snapshot.artifacts, snapshot.workspace.registry,
                                    document_repository=snapshot.inputs["document_repository"])
        self.nodes, self.edges, self.documents, self.entries = {}, {}, {}, {}
        self.components, self.repositories = {}, {}
        self.issues = list(snapshot.issues)
        self.gaps = []
        self.valid_fields = {}

    def issue(self, code, artifact, detail, *, gap=False):
        (self.gaps if gap else self.issues).append(
            dict(code=code, path=artifact.rel, detail=detail))

    def location(self, artifact, *, metadata=False):
        source = self.snapshot.sources[artifact.rel]
        end = (body_first_line(self.snapshot.texts[artifact.rel], artifact.body) - 1
               if metadata and artifact.body else source["lines"])
        return dict(source=source["id"], start_line=1, end_line=max(1, end))

    def provenance(self, artifact, method="declared", *, rule=None, metadata=False):
        result = dict(source_kind="document", assertion_method=method,
                      sources=[self.location(artifact, metadata=metadata)])
        if method == "derived":
            result["rule"] = dict(self.rules["node_rule"])
            if rule:
                result["rule"]["id"] = rule
        return result

    def node(self, kind, identity, label, artifact, *, data=None, discriminator="", code=False):
        ident = asdict(identity)
        key = kind + ":" + digest(canonical([ident, discriminator]))
        if key not in self.nodes:
            self.nodes[key] = dict(
                id=key, kind=kind, identity=ident, label=label,
                provenance=self.provenance(artifact, "derived"),
                observation=dict(path_status="unresolved" if code else "present" if kind in ("document", "entry") else "not_applicable",
                                 observation_status="not_requested" if code else "available",
                                 freshness="unknown" if code else "current"),
                data=data or {})
        else:
            sources = self.nodes[key]["provenance"]["sources"]
            location = self.location(artifact)
            if location not in sources:
                sources.append(location)
        return key

    def edge(self, relation, source, target, artifact, *, data=None, origin=None):
        rule = self.rules["relations"][relation]
        provenance = self.provenance(artifact, rule["method"], rule=rule.get("rule"), metadata=True)
        if rule["method"] == "derived":
            provenance["rule"]["version"] = rule["version"]
        if origin:
            provenance["sources"] = origin["provenance"]["sources"]
            provenance["rule"]["origin_edge"] = origin["id"]
        value = dict(relation=relation, source=source, target=target,
                     provenance=provenance, data=data or {})
        value["id"] = "edge:" + digest(canonical(value))
        self.edges[value["id"]] = value
        return value

    def owned(self, node, owner, artifact):
        identity = Identity(self.index.document_repository, owner, "scope")
        scope = self.node("scope", identity, owner, artifact)
        self.edge("belongs_to", node, scope, artifact)

    def fields(self, artifact):
        spec = self.snapshot.workspace.registry["types"].get(artifact.type, {})
        valid = {}
        for field, definition in spec.get("memory_fields", {}).items():
            if field not in artifact.meta:
                self.issue("mapping-not-declared", artifact, field + " is absent; not a negative assertion", gap=True)
                continue
            try:
                jsonschema.Draft202012Validator(artifact_field(definition)).validate(artifact.meta[field])
                valid[field] = artifact.meta[field]
            except (jsonschema.ValidationError, TypeError, ValueError, RecursionError):
                self.issue("invalid-metadata", artifact, field + " does not satisfy its optional contract")
        return valid

    def register_documents(self):
        for artifact in sorted(self.snapshot.artifacts, key=lambda a: a.rel):
            identity = self.index.identity(artifact)
            sections = [asdict(span) for span in locate_sections(
                artifact.body, first_line=body_first_line(self.snapshot.texts[artifact.rel], artifact.body))]
            fields = self.valid_fields[artifact.rel] = self.fields(artifact)
            data = dict(path=artifact.rel, artifact_type=artifact.type,
                        status=artifact.meta.get("status") if isinstance(artifact.meta.get("status"), str) else None,
                        products=[p for p in as_list(artifact.meta.get("products")) if isinstance(p, str)],
                        sections=sections,
                        metadata_presence={key: "declared-empty" if not value else "declared"
                                           for key, value in fields.items()})
            node = self.node("document", identity, artifact.id if isinstance(artifact.id, str) else artifact.rel, artifact,
                             data=data, discriminator=artifact.rel)
            self.documents[artifact.rel] = node
            self.owned(node, identity.scope, artifact)
            if identity.scope == "ambiguous":
                self.issue("ambiguous-owner", artifact, "more than one product owns this location")
        for identifier, targets in sorted(self.index.declarations.items()):
            targets = sorted(targets, key=lambda t: (t.identity, t.artifact.rel, t.key or ""))
            for target in targets:
                if target.key is None:
                    continue
                node = self.node("entry", target.identity, identifier, target.artifact,
                                 data={"document": self.documents[target.artifact.rel]},
                                 discriminator=target.artifact.rel)
                self.entries[(target.artifact.rel, target.key)] = node
                self.owned(node, target.identity.scope, target.artifact)
            if len(targets) > 1:
                by_scope = {}
                for target in targets:
                    by_scope.setdefault(target.identity.scope, []).append(target)
                for matches in by_scope.values():
                    if len(matches) > 1:
                        self.issue("ambiguous-declaration", matches[0].artifact,
                                   identifier + " has multiple declarations in this scope")

    def register_repositories(self):
        for (scope, key), targets in sorted(self.index.repositories.items()):
            targets = sorted(targets, key=lambda t: t.artifact.rel)
            full = f"repository:{scope}:{key}"
            nodes = []
            for target in targets:
                row = as_map(as_map(target.artifact.meta.get("code")).get(key))
                data = dict(repository=full, used_by=[p for p in as_list(row.get("used_by")) if isinstance(p, str)],
                            unclassified_code="normal")
                if "zones" in row:
                    try:
                        jsonschema.Draft202012Validator(artifact_field("code-zones")).validate(row["zones"])
                        data["zones"] = sorted(row["zones"], key=canonical)
                    except jsonschema.ValidationError:
                        self.issue("invalid-metadata", target.artifact, f"code.{key}.zones is invalid")
                node = self.node("repository", target.identity, full, target.artifact,
                                 data=data, code=True, discriminator=target.artifact.rel)
                nodes.append(node)
                self.owned(node, scope, target.artifact)
            self.repositories[full] = nodes
            if len(nodes) > 1:
                self.issue("ambiguous-repository", targets[0].artifact, "repository alias is declared twice")

    def register_components(self):
        for artifact in sorted(self.snapshot.artifacts, key=lambda a: a.rel):
            for full, views in sorted(self.valid_fields[artifact.rel].get("components", {}).items()):
                scope, _, key = full.removeprefix("component:").rpartition(":")
                owner = self.index.owner(artifact)
                if artifact.type in ("architecture", "platform-architecture") and scope != owner:
                    self.issue("component-owner-mismatch", artifact, "components must be declared in their owning architecture")
                    continue
                if artifact.type == "solution-design" and scope.startswith("product:") and (
                        scope[8:] not in self.index.products or
                        scope[8:] not in as_list(artifact.meta.get("products"))):
                    self.issue("component-owner-mismatch", artifact, "design component requires a known product binding")
                    continue
                identity = Identity(self.index.document_repository, scope, full)
                node = self.node("component", identity, full, artifact, data={"views": []})
                self.components[full] = node
                self.owned(node, scope, artifact)
                for view, record in sorted(views.items()):
                    declaration = dict(view=view, document=self.documents[artifact.rel])
                    self.nodes[node]["data"]["views"].append(declaration)
                    self.edge("documents", self.documents[artifact.rel], node, artifact, data={"view": view})
                    if "section" in record:
                        spans = self.nodes[self.documents[artifact.rel]]["data"]["sections"]
                        matched = [s for s in spans if s["marker"] == record["section"] or
                                   s["title"].casefold() == record["section"].casefold()]
                        if len(matched) != 1:
                            self.issue("section-unresolved", artifact, "component section is absent or ambiguous")
                        else:
                            declaration["section"] = matched[0]
                    if "code_roots" not in record:
                        self.issue("mapping-not-declared", artifact, f"{full} / {view}: roots not declared", gap=True)

    def repository_target(self, reference, artifact):
        if reference in self.repositories:
            nodes = self.repositories[reference]
            return (nodes[0], "resolved") if len(nodes) == 1 else (None, "ambiguous")
        result = self.index.repository(reference, artifact)
        if result.target:
            full = f"repository:{result.target.identity.scope}:{result.target.key}"
            nodes = self.repositories.get(full, [])
            if len(nodes) == 1:
                return nodes[0], "resolved"
        return None, result.status

    def register_roots(self):
        for artifact in sorted(self.snapshot.artifacts, key=lambda a: a.rel):
            for full, views in sorted(self.valid_fields[artifact.rel].get("components", {}).items()):
                component = self.components.get(full)
                if component is None:
                    continue
                # Only declarations accepted in register_components may contribute roots.
                if not any(e["relation"] == "documents" and e["source"] == self.documents[artifact.rel]
                           and e["target"] == component for e in self.edges.values()):
                    continue
                for view, record in sorted(views.items()):
                    for root in sorted(record.get("code_roots", []), key=canonical):
                        repository, status = self.repository_target(root["repository"], artifact)
                        if repository is None:
                            self.issue("root-unresolved", artifact, f"{full} / {view}: repository {status}")
                            continue
                        repo = self.nodes[repository]
                        path = Path(root["path"]).as_posix()
                        local = f"{repo['label']}:{view}:{path}"
                        node = self.node("code-root", Identity(self.index.document_repository,
                                         repo["identity"]["scope"], local), local, artifact, code=True,
                                         data=dict(repository=repository, path=path, view=view,
                                                   meaning="declared-location-not-observed-code"))
                        self.edge("realized_in", component, node, artifact, data={"view": view})

    def resolve(self, reference, artifact):
        if not isinstance(reference, str):
            return None, "invalid"
        if reference in self.components:
            return self.components[reference], "resolved"
        if reference.startswith("repository:") or self.index.repository_re.fullmatch(reference):
            return self.repository_target(reference, artifact)
        if reference in self.documents:
            return self.documents[reference], "resolved"
        result = self.index.resolve(reference, artifact)
        if result.target:
            target = result.target
            node = (self.entries.get((target.artifact.rel, target.key)) if target.key else
                    self.documents[target.artifact.rel])
            return node, "resolved" if node else "missing"
        return None, result.status

    def relations(self):
        for artifact in sorted(self.snapshot.artifacts, key=lambda a: a.rel):
            spec = self.snapshot.workspace.registry["types"].get(artifact.type, {})
            optional = spec.get("memory_fields", {})
            for relation, rule in self.rules["relations"].items():
                if rule["method"] != "declared" or (rule.get("types") and artifact.type not in rule["types"]):
                    continue
                field = rule["field"]
                if field in optional and field not in self.valid_fields[artifact.rel]:
                    continue
                for position, reference in enumerate(as_list(artifact.meta.get(field))):
                    target, status = self.resolve(reference, artifact)
                    if target is None:
                        self.issue("reference-unresolved", artifact, f"{field}[{position}]: {status}")
                        continue
                    origin = self.edge(relation, self.documents[artifact.rel], target, artifact)
                    for inverse, inverse_rule in self.rules["relations"].items():
                        if relation in inverse_rule.get("inverse_of", []):
                            self.edge(inverse, target, origin["source"], artifact, origin=origin)

    def subjects(self):
        for artifact in sorted(self.snapshot.artifacts, key=lambda a: a.rel):
            if artifact.type != "impact-classification":
                continue
            subjects = self.valid_fields[artifact.rel].get("subjects", {})
            routing = {}
            for candidate in as_map(artifact.meta.get("routing")):
                normalized = self.index.normalize_candidate(candidate, artifact)
                if normalized.identity:
                    routing.setdefault(normalized.identity, []).append(candidate)
            identities = [self.index.normalize_candidate(c, artifact).identity for c in subjects]
            rows = []
            for candidate, components in sorted(subjects.items()):
                normalized = self.index.normalize_candidate(candidate, artifact)
                identity = normalized.identity
                matches = routing.get(identity, [])
                declared = self.index.resolve(candidate, artifact, allow_local=True)
                if identity is None or len(matches) != 1 or identities.count(identity) != 1 or not declared.target:
                    self.issue("subjects-candidate-unresolved", artifact,
                               "subjects must join one declared candidate and one routing row in the same scope")
                    continue
                mapped = [self.components[c] for c in components if c in self.components]
                complete = len(mapped) == len(components)
                if not complete:
                    self.issue("subjects-component-unresolved", artifact, "a declared component is not registered")
                candidate_node = (self.entries.get((declared.target.artifact.rel, declared.target.key))
                                  if declared.target.key else self.documents[declared.target.artifact.rel])
                rows.append(dict(candidate=asdict(identity), candidate_node=candidate_node,
                                 routing_key=matches[0], components=sorted(mapped),
                                 unresolved_components=sorted(c for c in components if c not in self.components),
                                 mapping_status="declared" if complete else "partial",
                                 impact_attribution="candidate-only"))
            if subjects:
                self.nodes[self.documents[artifact.rel]]["data"]["subjects"] = rows

    def build(self) -> dict:
        if not self.snapshot.artifacts:
            self.issues.append(dict(code="no-document-sources", path="",
                                    detail="no readable artifacts in the selected scope"))
        self.register_documents()
        self.register_repositories()
        self.register_components()
        self.register_roots()
        self.relations()
        self.subjects()
        for node in self.nodes.values():
            node["provenance"]["sources"].sort(key=canonical)
            if "views" in node["data"]:
                node["data"]["views"].sort(key=canonical)
        result = dict(schema="framework-memory/graph/v1", snapshot=self.snapshot.id,
                      coverage="partial" if self.issues else "available",
                      sources=sorted(self.snapshot.sources.values(), key=lambda s: s["id"]),
                      nodes=sorted(self.nodes.values(), key=lambda n: n["id"]),
                      edges=sorted(self.edges.values(), key=lambda e: e["id"]),
                      issues=sorted(self.issues, key=canonical), gaps=sorted(self.gaps, key=canonical))
        validate_graph(result)
        return result


def build(snapshot: Snapshot) -> dict:
    return DocumentaryGraph(snapshot).build()
