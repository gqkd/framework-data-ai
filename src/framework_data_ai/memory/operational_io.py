"""Bounded strict JSON inputs and integrity checks; hashes are not signatures."""
from pathlib import Path
import json
import stat

from ..workspace import MemoryInputError, no_symlink_ancestors
from .code_graph import validate_code_graph
from .models import canonical, digest, validate


def read_json(path):
    path = Path(path).absolute()
    no_symlink_ancestors(Path(path.anchor), path.relative_to(path.anchor))
    if not stat.S_ISREG(path.stat().st_mode):
        raise MemoryInputError("operational input is not a regular file")
    with path.open("rb") as stream:
        data = stream.read(25_000_001)
    if len(data) > 25_000_000:
        raise MemoryInputError("operational input exceeds 25 MB")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise MemoryInputError("duplicate JSON key in operational input")
            result[key] = value
        return result
    def invalid(_):
        raise MemoryInputError("non-finite JSON number in operational input")
    return json.loads(data, object_pairs_hook=pairs, parse_constant=invalid)


def load_code(directory):
    """Only published snapshot bundles, not a free-floating provider JSON result.

    This verifies internal coherence. It neither authenticates the producer nor rereads
    live checkouts; callers must state that freshness is unknown until re-observed.
    """
    directory = Path(directory)
    manifest = read_json(directory / "manifest.json")
    graph = read_json(directory / "code-graph.json")
    validate("manifest", manifest)
    validate_code_graph(graph)
    inputs = manifest["inputs"]
    if (manifest["id"] != digest(canonical(inputs)) or graph["snapshot"] != manifest["id"]
            or manifest["files"] != {"code-graph.json": digest(canonical(graph))}
            or inputs.get("normalized_observation") != digest(canonical(dict(graph, snapshot="")))
            or inputs.get("document_snapshot") != graph["document_snapshot"]
            or inputs.get("provider") != graph["provider"]):
        raise MemoryInputError("code snapshot bundle has inconsistent identities")
    bundle = dict(graph=graph, inputs=inputs)
    verify_code(bundle)
    return bundle


def verify_code(bundle):
    graph, inputs = bundle["graph"], bundle["inputs"]
    validate_code_graph(graph)
    if (graph["snapshot"] != digest(canonical(inputs))
            or inputs.get("normalized_observation") != digest(canonical(dict(graph, snapshot="")))
            or inputs.get("document_snapshot") != graph["document_snapshot"]
            or inputs.get("provider") != graph["provider"]
            or set(inputs.get("repositories", {})) != {r["repository"] for r in graph["repositories"]}):
        raise MemoryInputError("code observation and its captured inputs disagree")


def seal(value, name):
    value["id"] = digest(canonical(value))
    validate(name, value)
    return value


def verify_seal(value, name):
    validate(name, value)
    if value["id"] != digest(canonical({k: v for k, v in value.items() if k != "id"})):
        raise MemoryInputError("operational report identity disagrees with its contents")
