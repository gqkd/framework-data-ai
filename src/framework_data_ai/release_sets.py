"""Release identities and cross-artifact coherence; no reads, commands or attestations."""
from copy import deepcopy

import jsonschema

from .artifacts import as_list, as_map, jsonify
from .memory.models import canonical, digest, validate
from .references import ReferenceIndex, canonical_repo
from .workspace import MemoryInputError

CONTEXT = ("config", "infrastructure", "ai", "data")


def repositories(index, source):
    """Eligible code declarations and required subset in this manifest's product scope."""
    products = as_list(source.meta.get("products"))
    if len(products) != 1 or index.owner(source) != "product:" + products[0]:
        raise MemoryInputError("a release requires one unambiguous product owner")
    eligible, required, remotes = {}, set(), set()
    for (owner, key), entries in index.repositories.items():
        for entry in entries:
            row = as_map(as_map(entry.artifact.meta.get("code")).get(key))
            relevant = str(row.get("release_relevant")).lower() == "true"
            users = as_list(row.get("used_by"))
            if owner == "platform" and relevant and (not users or set(users) - index.products):
                raise MemoryInputError("release-relevant shared code has unavailable product scope")
            if owner != "product:" + products[0] and not (owner == "platform" and products[0] in users):
                continue
            rid = "repository:" + owner + ":" + key
            remote = canonical_repo(row.get("url", ""))
            if not remote or rid in eligible or remote in remotes:
                raise MemoryInputError("release code declaration is missing or ambiguous")
            remotes.add(remote)
            eligible[rid] = dict(remote=remote, artifact=entry.artifact.rel,
                                 alias=("platform." if owner == "platform" else "product.") + key)
            if relevant:
                required.add(rid)
    return eligible, required


def normalize(manifest, index):
    """Return a detached v1 view. A legacy scalar is never broadcast across repositories."""
    eligible, required = repositories(index, manifest)
    value = manifest.meta.get("release_set")
    origin = "release-set-v1"
    if value is None:
        if len(eligible) != 1:
            raise MemoryInputError("legacy single commit cannot identify this repository set")
        rid = next(iter(eligible))
        value = dict(version=1, repositories={rid: dict(commit=as_map(manifest.meta.get("code")).get("commit"),
                      build_digest=as_map(manifest.meta.get("build")).get("image_digest"))}, dependencies=[])
        origin = "legacy-single-repository"
    elif as_map(manifest.meta.get("code")).get("commit") or as_map(manifest.meta.get("build")).get("image_digest"):
        raise MemoryInputError("legacy code/build and release_set both claim authority")
    validate("release-set", jsonify(value))
    value = deepcopy(value)
    if set(value["repositories"]) - eligible.keys() or not required <= value["repositories"].keys():
        raise MemoryInputError("release set omits required or includes undeclared code repositories")
    paths = [row["manifest"] for row in value["dependencies"]]
    if len(set(paths)) != len(paths):
        raise MemoryInputError("duplicate dependency manifest")
    value["dependencies"].sort(key=lambda row: row["manifest"])
    # Config/model/data/target changes alter candidate identity too. These facts retain
    # their existing home in RLM; the derived payload is not another authored manifest.
    payload = {**value, **{field: jsonify(manifest.meta.get(field, {})) for field in CONTEXT}}
    return dict(origin=origin, payload=payload, hash=digest(canonical(payload)), eligible=eligible)


def evaluation(manifest, index, normalized):
    result = index.artifact(as_map(manifest.meta.get("evaluation")).get("report"), kind="evaluation-report")
    evr = result.target.artifact if result.target else None
    if not evr or index.owner(evr) != index.owner(manifest):
        raise MemoryInputError("candidate EVR is missing or ambiguous in this product")
    measured = {}
    for alias, revision in as_map(evr.meta.get("verified_code")).items():
        target = index.repository(alias, evr).target
        if not target:
            raise MemoryInputError("evaluated repository alias does not resolve")
        rid = "repository:" + target.identity.scope + ":" + target.key
        measured[rid] = revision
    intended = {rid: row["commit"] for rid, row in normalized["payload"]["repositories"].items()}
    if measured != intended or evr.meta.get("release_set_hash") != normalized["hash"]:
        raise MemoryInputError("EVR measured a different or incomplete candidate set")
    claimed = as_map(manifest.meta.get("evaluation"))
    if any(claimed.get(field) != evr.meta.get(field) for field in ("evp_version", "evp_hash")):
        raise MemoryInputError("manifest and EVR refer to different frozen plans")
    if claimed.get("verdict") != "go":
        raise MemoryInputError("candidate does not declare a passing release evaluation")
    return evr


def check(arts, registry, report):
    """Additive documentary lint: only new metadata opts in; never a deployment check."""
    index = ReferenceIndex(arts, registry)
    for manifest in arts:
        if manifest.type != "release-manifest" or "release_set" not in manifest.meta:
            continue
        try:
            normalized = normalize(manifest, index)
        except (MemoryInputError, ValueError, TypeError, KeyError, jsonschema.ValidationError):
            report.add("RLS001", manifest.rel, "release set has an invalid, ambiguous or incomplete repository/build binding")
            continue
        try:
            evaluation(manifest, index, normalized)
        except (MemoryInputError, ValueError, TypeError, KeyError):
            report.add("RLS002", manifest.rel, "candidate and EVR do not attest the same complete set and frozen plan")
