"""Read-only enrichment backlog over selected documentary sources, never inferred mappings."""
from __future__ import annotations

from .models import canonical, validate


def assess(snapshot, graph):
    artifacts = {a.rel: a for a in snapshot.artifacts}
    gaps = []

    def add(code, path, detail):
        artifact = artifacts.get(path)
        lifecycle = artifact.meta.get("lifecycle") if artifact else None
        lifecycle = lifecycle if lifecycle in ("living", "immutable", "append-only") else "unknown"
        handling = {"immutable": "new-successor-only", "append-only": "new-linked-event-only",
                    "living": "propose-reviewed-edit"}.get(lifecycle, "inspect-source-first")
        item = dict(code=code, path=path, detail=detail, lifecycle=lifecycle, handling=handling)
        if path in snapshot.sources:
            item["source"] = snapshot.sources[path]
        gaps.append(item)

    for gap in graph["gaps"]:
        add(gap["code"], gap["path"], gap["detail"])
    # Only accepted declarations contribute this second-level question. Invalid fields
    # remain graph issues; there is no schema reimplementation or guessed root here.
    documents = {n["id"]: n for n in graph["nodes"] if n["kind"] == "document"}
    components = {n["id"]: n for n in graph["nodes"] if n["kind"] == "component"}
    for edge in graph["edges"]:
        if edge["relation"] != "documents":
            continue
        path = documents[edge["source"]]["data"]["path"]
        component = components[edge["target"]]
        identifier, view = component["label"], edge["data"]["view"]
        record = artifacts[path].meta["components"][identifier][view]
        if "code_roots" not in record:
            add("code-roots-not-declared", path,
                f"{identifier} / {view}: code_roots is absent; design-only may be intentional")
    result = dict(schema="framework-memory/adoption-report/v1", snapshot=snapshot.id,
                  coverage=graph["coverage"], written=False, activation="explicit-commands-only",
                  code_observation="not_requested", gaps=sorted(gaps, key=canonical),
                  issues=graph["issues"], filtered_sources=snapshot.inputs["filtered_sources"],
                  limitations=["Only selected sources are assessed; absence is not a negative assertion",
                               "No completeness score, inferred applies_to/subjects or automatic repairs",
                               "Gaps are optional enrichment questions, not migration failures",
                               "A mapping to code does not establish that code exists or is implemented"])
    validate("adoption-report", result)
    snapshot.assert_unchanged()
    return result
