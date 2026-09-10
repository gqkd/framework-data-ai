"""Optional offline projection. No graph mutation, provider execution or source URL opening."""
from __future__ import annotations

import base64
import hashlib
from html import escape
from pathlib import Path
import re

import yaml

from ..snapshots import publish_payload
from ..workspace import MemoryInputError, no_symlink_ancestors
from .models import FRAMEWORK, canonical, digest, validate, validate_graph
from .operational_io import verify_code

MAX_HTML_BYTES = 25_000_000
ASSETS = ("index.html", "style.css", "model.js", "app.js")


def assets():
    """Hash every executed byte; the inventory is the only third-party pin authority."""
    paths = ["assets/memory-viewer/" + name for name in ASSETS] + ["LICENSE", "NOTICE"]
    manifest_path = FRAMEWORK / "third_party/manifest.yaml"
    no_symlink_ancestors(FRAMEWORK, manifest_path.relative_to(FRAMEWORK))
    manifest_bytes = manifest_path.read_bytes()
    manifest = yaml.safe_load(manifest_bytes)
    rows = [r for r in manifest["incorporated_code"] if r["name"] == "cytoscape"]
    if len(rows) != 1:
        raise MemoryInputError("optional viewer dependency inventory is missing or ambiguous")
    dependency = rows[0]
    expected = {"third_party/cytoscape/dist/cytoscape.min.js", "third_party/cytoscape/LICENSE"}
    if set(dependency["files"]) != expected or dependency["license"] != "MIT":
        raise MemoryInputError("optional viewer dependency inventory is invalid")
    paths += sorted(expected)
    contents = {}
    for relative in paths:
        no_symlink_ancestors(FRAMEWORK, Path(relative))
        path = FRAMEWORK / relative
        if not path.is_file() or path.stat().st_size > 2_000_000:
            raise MemoryInputError("optional viewer asset is missing or exceeds its limit")
        raw = path.read_bytes()
        if relative in expected and digest(raw) != dependency["files"][relative]:
            raise MemoryInputError("optional viewer dependency checksum mismatch")
        contents[relative] = raw
    contents["third_party/manifest.yaml"] = manifest_bytes
    return contents


def model(snapshot, graph, *, code=None, hypotheses=None):
    validate_graph(graph)
    if graph["snapshot"] != snapshot.id:
        raise MemoryInputError("viewer documentary snapshot mismatch")
    cg = None
    compatible = False
    warnings = ["Navigation is not impact analysis or proof of understanding.",
                "Captured documents may be sensitive. This HTML includes their selected text; do not publish it."]
    if graph["coverage"] != "available" or graph["gaps"]:
        warnings.append("Documentary coverage has gaps; inspect the exported diagnostics.")
    if code is not None:
        verify_code(code)
        if code["inputs"].get("document_repository") != snapshot.inputs["document_repository"]:
            raise MemoryInputError("code snapshot belongs to another documentary namespace")
        cg = code["graph"]
        compatible = cg["document_snapshot"] == snapshot.id
        warnings.append("Code is captured, not re-observed: live freshness is unknown. Hashes are not signatures.")
        if not compatible:
            warnings.append("Document revisions differ. Code is shown separately; mapping is disabled.")
        if cg["coverage"] != "available":
            warnings.append("Code coverage is " + cg["coverage"] + "; no absence-of-impact claim is possible.")
    else:
        warnings.append("Code observation not requested. A documentary view does not establish code availability.")
    bridges = []
    if compatible:
        nodes = {n["id"]: n for n in graph["nodes"]}
        edges = {(e["source"], e["target"]): e for e in graph["edges"] if e["relation"] == "realized_in"}
        for bridge in cg["bridges"]:
            component, root = nodes.get(bridge["component"]), nodes.get(bridge["root"])
            declaration = edges.get((bridge["component"], bridge["root"]))
            repository = nodes.get(root["data"]["repository"]) if root else None
            if (not component or component["kind"] != "component" or not root or root["kind"] != "code-root"
                    or not declaration or not repository
                    or repository["data"]["repository"] != bridge["repository"]
                    or root["data"]["path"] != bridge["path"] or root["data"]["view"] != bridge["view"]
                    or declaration["provenance"] != bridge["declaration"]):
                raise MemoryInputError("code bridge does not match its documentary declaration")
            bridges.append(bridge)
    known = {s["id"]: s for s in graph["sources"]}
    if cg:
        known.update({s["id"]: s for s in cg["sources"]})
    hypotheses = [] if hypotheses is None else hypotheses
    validate("hypotheses", hypotheses)
    for hypothesis in hypotheses:
        for location in hypothesis["provenance"]["sources"]:
            source = known.get(location["source"])
            if not source or not 1 <= location["start_line"] <= location["end_line"] <= source["lines"]:
                raise MemoryInputError("hypothesis cites a source outside the viewer")
    result = dict(schema="framework-memory/viewer-data/v1", document=graph, code=cg, bridges=bridges,
                mapping_compatible=compatible, hypotheses=hypotheses, warnings=warnings,
                source_text={s["id"]: snapshot.texts[s["path"]] for s in graph["sources"]},
                limits=dict(nodes=250, edges=1500),
                observation=dict(code="captured-not-rechecked" if cg else "not_requested"))
    validate("viewer-data", result)
    return result


def script_json(value):
    return canonical(value).decode().replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def render(data, content):
    local = lambda name: content["assets/memory-viewer/" + name].decode("utf-8")
    scripts = [content["third_party/cytoscape/dist/cytoscape.min.js"].decode("utf-8"),
               local("model.js"), local("app.js")]
    if any(re.search(r"</script", script, re.I) for script in scripts):
        raise MemoryInputError("viewer executable asset contains an unsafe HTML terminator")
    hashes = ["'sha256-" + base64.b64encode(hashlib.sha256(s.encode()).digest()).decode() + "'" for s in scripts]
    policy = ("default-src 'none'; script-src " + " ".join(hashes) +
              "; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; font-src 'none'; "
              "object-src 'none'; base-uri 'none'; form-action 'none'")
    slots = dict(CSP=escape(policy, quote=True), STYLE=local("style.css"), DATA=script_json(data),
                 SCRIPTS="\n".join("<script>" + s + "</script>" for s in scripts),
                 LICENSE=escape(content["third_party/cytoscape/LICENSE"].decode("utf-8")),
                 FRAMEWORKLICENSE=escape(content["LICENSE"].decode("utf-8")),
                 NOTICE=escape(content["NOTICE"].decode("utf-8")))
    html = re.sub(r"@@([A-Z]+)@@", lambda match: slots[match[1]], local("index.html")).encode("utf-8")
    if len(html) > MAX_HTML_BYTES:
        raise MemoryInputError("viewer export exceeds 25 MB; narrow documentary scan or code input")
    return html


def export(snapshot, graph, *, code=None, hypotheses=None, dry_run=False):
    content = assets()
    data = model(snapshot, graph, code=code, hypotheses=hypotheses)
    html = render(data, content)
    inputs = dict(schema="framework-memory/viewer-inputs/v1", document_snapshot=snapshot.id,
                  code_snapshot=data["code"]["snapshot"] if data["code"] else None,
                  data_sha256=digest(canonical(data)),
                  assets={path: digest(raw) for path, raw in sorted(content.items())})
    validate("viewer-inputs", inputs)
    identifier = digest(canonical(inputs))
    manifest = dict(schema="framework-memory/manifest/v1", id=identifier, inputs=inputs, files={"index.html": digest(html)})
    validate("manifest", manifest)

    def unchanged():
        snapshot.assert_unchanged()
        if assets() != content:
            raise MemoryInputError("viewer assets changed during export")
    unchanged()
    if not dry_run:
        publish_payload(snapshot.workspace.root, "views", identifier,
                        {"index.html": html, "manifest.json": canonical(manifest)}, unchanged)
    return dict(command="view", id=identifier, document_snapshot=snapshot.id,
                coverage=graph["coverage"], written=not dry_run,
                output=f"_meta/memory/views/{identifier}/index.html" if not dry_run else None,
                bytes=len(html), code_observation=data["observation"]["code"],
                code_coverage=data["code"]["coverage"] if data["code"] else "not_requested",
                mapping_compatible=data["mapping_compatible"], warnings=data["warnings"])
