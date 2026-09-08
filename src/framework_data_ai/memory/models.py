"""One contract for runtime rules and generated, self-contained JSON Schema."""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path

import jsonschema
import yaml

FRAMEWORK = Path(__file__).resolve().parents[3]
CONTRACT_PATH = FRAMEWORK / "schemas/memory-contracts.yaml"


def contract() -> dict:
    # Content-keyed, not mtime-keyed: a long-running caller must notice a changed contract.
    return deepcopy(_read_contract(CONTRACT_PATH.read_bytes()))


@lru_cache(maxsize=8)
def _read_contract(content: bytes) -> dict:
    class UniqueKeys(yaml.SafeLoader):
        pass

    def mapping(loader, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in result:
                raise ValueError("duplicate key in memory contract")
            result[key] = loader.construct_object(value_node, deep=deep)
        return result

    UniqueKeys.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    return yaml.load(content, Loader=UniqueKeys)


def canonical(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def schema(name: str, rules: dict | None = None) -> dict:
    rules = rules if rules is not None else contract()
    definitions = deepcopy(rules["definitions"])
    conditions = []
    for relation, rule in rules["relations"].items():
        provenance = {"properties": {"assertion_method": {"const": rule["method"]}}}
        if rule["method"] == "derived":
            derivation = {"properties": {"id": {"const": rule["rule"]},
                                          "version": {"const": rule["version"]}}}
            if rule.get("inverse_of"):
                derivation["required"] = ["origin_edge"]
            provenance["properties"]["rule"] = derivation
        conditions.append({"if": {"properties": {"relation": {"const": relation}}},
                           "then": {"properties": {"provenance": provenance}}})
    definitions["edge"]["properties"]["relation"] = {"enum": sorted(rules["relations"])}
    definitions["edge"]["allOf"] = conditions
    used = {}

    def include(value):
        if isinstance(value, list):
            for child in value:
                include(child)
        elif isinstance(value, dict):
            if "$ref" in value:
                key = value["$ref"].removeprefix("#/$defs/")
                if key not in used:
                    used[key] = definitions[key]
                    include(used[key])
            for child in value.values():
                include(child)

    include({"$ref": f"#/$defs/{name}"})
    return {"$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"framework-memory/{name}/v1", "$ref": f"#/$defs/{name}",
            "$defs": {key: used[key] for key in sorted(used)}}


def artifact_field(name: str) -> dict:
    """Inline only the selected field: artifact schemas need no external resolver."""
    return deepcopy(_artifact_field(name, CONTRACT_PATH.read_bytes()))


@lru_cache(maxsize=128)
def _artifact_field(name: str, content: bytes) -> dict:
    definitions = _read_contract(content)["definitions"]

    def expand(value, stack=()):
        if isinstance(value, list):
            return [expand(item, stack) for item in value]
        if not isinstance(value, dict):
            return value
        if "$ref" in value:
            ref = value["$ref"]
            key = ref.removeprefix("#/$defs/")
            if ref != f"#/$defs/{key}" or key in stack or len(value) != 1:
                raise ValueError(f"unsupported or cyclic field reference: {ref}")
            return expand(definitions[key], (*stack, key))
        return {key: expand(item, stack) for key, item in value.items()}

    result = expand(definitions[name], (name,))
    jsonschema.Draft202012Validator.check_schema(result)
    return result


def validate(name: str, value) -> None:
    _validator(name, CONTRACT_PATH.read_bytes()).validate(value)


@lru_cache(maxsize=32)
def _validator(name, content):
    return jsonschema.Draft202012Validator(schema(name, _read_contract(content)))


def validate_graph(graph: dict) -> None:
    validate("graph", graph)
    sources = {s["id"]: s for s in graph["sources"]}
    nodes = {n["id"]: n for n in graph["nodes"]}
    edges = {e["id"]: e for e in graph["edges"]}
    if any(len(index) != len(graph[key]) for index, key in (
            (sources, "sources"), (nodes, "nodes"), (edges, "edges"))):
        raise ValueError("duplicate graph identity")
    rules = contract()["relations"]
    for item in [*nodes.values(), *edges.values()]:
        p = item["provenance"]
        if p["assertion_method"] == "inferred":
            raise ValueError("inferences belong outside the authoritative projection")
        for location in p["sources"]:
            source = sources.get(location["source"])
            if not source or not 1 <= location["start_line"] <= location["end_line"] <= source["lines"]:
                raise ValueError("source localization is not in this snapshot")
        if "relation" not in item:
            continue
        if item["source"] not in nodes or item["target"] not in nodes:
            raise ValueError("edge endpoint is not in this graph")
        inverse_of = rules[item["relation"]].get("inverse_of")
        if inverse_of:
            origin = edges.get(p["rule"]["origin_edge"])
            if (not origin or origin["relation"] not in inverse_of or
                    (origin["source"], origin["target"]) != (item["target"], item["source"]) or
                    origin["provenance"]["sources"] != p["sources"]):
                raise ValueError("inverse does not preserve its originating edge")
