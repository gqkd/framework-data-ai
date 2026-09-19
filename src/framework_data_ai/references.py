"""Scoped identities and reference resolution, independent of validator policy.

An identity is not an assertion that code exists or a document is current. Logical
document-repository IDs are supplied by callers; checkout paths never enter them.
No historical aliases are guessed, and ambiguous declarations never choose a winner.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re

from .artifacts import Artifact, as_list, as_map


def canonical_repo(url: str) -> str:
    """One repository, one string, whichever way somebody wrote the remote.

    The three forms below are the same repository and compare unequal as text:

        git@github.com:org/repo.git
        ssh://git@github.com/org/repo.git
        https://github.com/org/repo.git

    This matters because the key of a `code:` entry is a local nickname and not an identity.
    Two products calling their own repository `backend` are not sharing one; the same
    repository entered as `identity` under one product and `auth` under another is. Keyed on
    the nickname, a check meant to catch a repository described twice reports the first case
    and passes the second -- and the second is how the duplication actually arises, because
    two teams naming the same thing each use their own word for it.

    An address this cannot parse comes back stripped and lowercased rather than empty. Two
    identical unparseable strings are still one repository, and losing that would trade a
    wrong answer for no answer.
    """
    s = str(url).strip().rstrip("/")
    s = re.sub(r"^[a-z+]+://", "", s, flags=re.I)      # scheme, if any
    s = re.sub(r"^[^/@]+@", "", s)                     # user, git@ and the rest
    # scp-style `host:path`, but not `host:port/path`: a port is part of the address and a
    # self-hosted GitLab on 8443 would otherwise have it turned into a directory.
    if re.match(r"^[^/]+:(?!\d+(?:/|$))[^/]", s):
        s = s.replace(":", "/", 1)
    s = re.sub(r"\.git$", "", s, flags=re.I)
    host, _, path = s.partition("/")
    return f"{host.lower()}/{path}" if path else s.lower()


def product_dirs(arts: list[Artifact]) -> dict[Path, tuple[str, str]]:
    """Where each product's documents live, read off its manifest: dir -> (product, rel).

    The directory and not the `products:` field, because that is how a register declares
    its scope now. In `products/<p>/OPEN.md` the field is redundant and nobody writes it:
    the entry is about that product by virtue of where it was filed, the same way an entry
    in `platform/OPEN.md` is about the substrate. Reading scope off the field instead put
    every unlabelled entry of every register into every product's derived view, which is
    the one direction this must not fail in: `AGENTS.md` sends an agent to that view first.
    """
    out: dict[Path, tuple[str, str]] = {}
    for m in arts:
        if m.type != "product-manifest":
            continue
        p = next(iter(as_list(m.meta.get("products"))), None)
        if p:
            out[m.path.parent] = (p, str(PurePosixPath(m.rel).parent))
    return out


@dataclass(frozen=True, order=True)
class Identity:
    document_repository: str
    scope: str
    local_id: str


@dataclass(frozen=True)
class Target:
    identity: Identity
    artifact: Artifact
    key: str | None = None


@dataclass(frozen=True)
class Resolution:
    status: str
    matches: tuple[Target, ...] = ()
    reason: str = ""

    @property
    def target(self) -> Target | None:
        return self.matches[0] if self.status == "resolved" and len(self.matches) == 1 else None


@dataclass(frozen=True)
class NormalizedCandidate:
    status: str
    identity: Identity | None = None
    reason: str = ""


@dataclass(frozen=True)
class ImpactLookup:
    impacts: frozenset[str]
    matched: tuple[Identity, ...]
    problems: tuple[str, ...] = ()


def _result(matches: list[Target]) -> Resolution:
    matches = sorted(matches, key=lambda t: (t.identity, t.artifact.rel, t.key or ""))
    if not matches:
        return Resolution("missing", reason="no declaration matches")
    if len(matches) != 1:
        return Resolution("ambiguous", tuple(matches), "multiple declarations match")
    return Resolution("resolved", tuple(matches))


class ReferenceIndex:
    def __init__(self, artifacts: list[Artifact], registry: dict,
                 *, document_repository: str = "local"):
        if not isinstance(document_repository, str) or not document_repository.strip():
            raise ValueError("a logical document_repository ID is required")
        self.artifacts = tuple(artifacts)
        self.document_repository = document_repository
        self.id_re = re.compile(r"\b((?:%s)-\d{3,})\b" %
                                "|".join(re.escape(p) for p in registry["id_prefixes"]))
        self.qualified_prefixes = set(registry.get("qualified_reference_prefixes") or ())
        self.repository_re = re.compile(registry["types"]["architecture"]["maps"]["verified_code"]["keys"])
        self.qualified_re = re.compile(
            r"^([a-z0-9][a-z0-9-]*):((?:%s)-\d{3,})$" %
            "|".join(re.escape(p) for p in sorted(self.qualified_prefixes))
        ) if self.qualified_prefixes else re.compile(r"(?!)")
        inline = registry["inline_id_declarations"]
        # Roadmap candidates are local too, even though their *references* need no prefix.
        self.local_prefixes = {prefix for kind, prefixes in inline.items()
                               if registry["types"][kind].get("axis") == "product"
                               for prefix in prefixes} | self.qualified_prefixes
        self.product_directories = product_dirs(artifacts)
        self._product_bindings = [(PurePosixPath(a.rel.replace("\\", "/")).parent, p)
                                  for a in artifacts if a.type == "product-manifest"
                                  for p in as_list(a.meta.get("products")) if isinstance(p, str)]
        self.products = {p for p, _ in self.product_directories.values()}
        self.by_id: dict[str, list[Target]] = {}
        self.declarations: dict[str, list[Target]] = {}
        self.inline: set[str] = set()
        self.inline_per_product: dict[str, set[str]] = {}
        self.repositories: dict[tuple[str, str], list[Target]] = {}
        for artifact in artifacts:
            owner = self.owner(artifact)
            if isinstance(artifact.id, str):
                target = Target(self.identity(artifact), artifact)
                self.by_id.setdefault(artifact.id, []).append(target)
                self.declarations.setdefault(artifact.id, []).append(target)
            prefixes = inline.get(artifact.type or "", ())
            for identifier in sorted(artifact.ids):
                if identifier.split("-", 1)[0] not in prefixes:
                    continue
                target = Target(Identity(document_repository, owner, identifier), artifact, identifier)
                self.declarations.setdefault(identifier, []).append(target)
                self.inline.add(identifier)
                if owner.startswith("product:"):
                    self.inline_per_product.setdefault(owner[8:], set()).add(identifier)
            if artifact.type in ("product-manifest", "platform-architecture"):
                for key in as_map(artifact.meta.get("code")):
                    if isinstance(key, str):
                        target = Target(Identity(document_repository, owner, f"repository:{key}"),
                                        artifact, key)
                        self.repositories.setdefault((owner, key), []).append(target)
        self.known = set(self.by_id) | self.inline

    def owner(self, artifact: Artifact) -> str:
        rel = PurePosixPath(artifact.rel.replace("\\", "/"))
        # Use the longest containing manifest directory; products: is binding, not ownership.
        owners = [(directory, product) for directory, product in self._product_bindings
                  if rel.is_relative_to(directory)]
        if owners:
            longest = max(len(directory.parts) for directory, _ in owners)
            names = {product for directory, product in owners if len(directory.parts) == longest}
            if len(names) == 1:
                return f"product:{next(iter(names))}"
            return "ambiguous"
        # Preserve incomplete legacy fixtures: a physical product directory still scopes
        # a local row, even when a missing manifest is reported elsewhere.
        if len(rel.parts) >= 3 and rel.parts[0] == "products":
            return f"product:{rel.parts[1]}"
        if (rel.parts and rel.parts[0] == "platform") or artifact.type == "platform-architecture":
            return "platform"
        return "repository"

    def identity(self, artifact: Artifact) -> Identity:
        local = artifact.id if isinstance(artifact.id, str) else artifact.rel.replace("\\", "/")
        return Identity(self.document_repository, self.owner(artifact), local)

    def artifact(self, ref: object, *, kind: str | None = None) -> Resolution:
        if not isinstance(ref, str):
            return Resolution("invalid", reason="reference is not a string")
        result = _result(self.by_id.get(ref, []))
        if result.target and kind and result.target.artifact.type != kind:
            return Resolution("wrong-type", result.matches, f"target is not {kind}")
        return result

    def normalize_candidate(self, ref: object, source: Artifact) -> NormalizedCandidate:
        """Normalize a row/reference; this does not assert a register declaration exists."""
        if not isinstance(ref, str):
            return NormalizedCandidate("invalid", reason="candidate is not a string")
        qualified = self.qualified_re.fullmatch(ref)
        if qualified:
            product, bare = qualified.groups()
            if product not in self.products:
                return NormalizedCandidate("unknown-product", reason=f"unknown product {product!r}")
            named = [p for p in as_list(source.meta.get("products")) if isinstance(p, str)]
            if named and "all" not in named and product not in named:
                return NormalizedCandidate("out-of-scope", reason=f"{ref!r} is outside products:")
            owner = f"product:{product}"
        elif self.id_re.fullmatch(ref):
            bare = ref
            owner = self.owner(source) if bare.split("-", 1)[0] in self.local_prefixes else "repository"
        else:
            return NormalizedCandidate("invalid", reason="unrecognized candidate syntax")
        if owner == "ambiguous":
            return NormalizedCandidate("ambiguous", reason="candidate ownership is ambiguous")
        return NormalizedCandidate("resolved", Identity(self.document_repository, owner, bare))

    def resolve(self, ref: object, source: Artifact, *, allow_local=False) -> Resolution:
        normalized = self.normalize_candidate(ref, source)
        if normalized.identity is None:
            return Resolution(normalized.status, reason=normalized.reason)
        identity = normalized.identity
        prefix = identity.local_id.split("-", 1)[0]
        if prefix in self.qualified_prefixes and not self.qualified_re.fullmatch(ref) and not allow_local:
            return Resolution("invalid", reason="this reference must name its product")
        matches = self.declarations.get(identity.local_id, [])
        if prefix in self.local_prefixes:
            matches = [t for t in matches if t.identity.scope == identity.scope]
        return _result(matches)

    def impacts_for(self, change: Artifact, classification: Artifact) -> ImpactLookup:
        """Join only the candidate's identity, never a number stripped of its namespace."""
        routing = as_map(classification.meta.get("routing"))
        impacts = as_map(classification.meta.get("impacts"))
        rows: dict[Identity, list[str]] = {}
        for key in set(routing) | set(impacts):
            normalized = self.normalize_candidate(key, classification)
            if normalized.identity:
                rows.setdefault(normalized.identity, []).append(key)
        values, matched, problems = set(), set(), []
        unmatched = []
        for ref in as_list(change.meta.get("derives_from")):
            normalized = self.normalize_candidate(ref, change)
            if normalized.identity is None:
                if isinstance(ref, str) and self.qualified_re.fullmatch(ref):
                    problems.append(normalized.reason)
                continue
            identity = normalized.identity
            keys = rows.get(identity, [])
            if len(keys) > 1:
                problems.append(f"multiple classification rows match {ref!r}")
            elif keys:
                matched.add(identity)
                values.update(value for value in as_list(impacts.get(keys[0])) if isinstance(value, str))
            elif identity.local_id.split("-", 1)[0] in self.local_prefixes:
                unmatched.append(ref)
                if any(row.local_id == identity.local_id for row in rows):
                    problems.append(f"classification row for {ref!r} belongs to a different scope")
        if unmatched and not matched:
            problems.append("no classification row in the candidate's scope for " +
                            ", ".join(repr(ref) for ref in unmatched))
        return ImpactLookup(frozenset(values), tuple(sorted(matched)), tuple(sorted(set(problems))))

    def repository(self, ref: object, source: Artifact) -> Resolution:
        """Resolve existing verified_code aliases, without opening a checkout."""
        if not isinstance(ref, str) or not self.repository_re.fullmatch(ref):
            return Resolution("invalid", reason="repository alias must be qualified")
        family, key = ref.split(".", 1)
        owner = self.owner(source) if family == "product" else "platform"
        if family not in ("product", "platform") or not key:
            return Resolution("invalid", reason="unknown repository qualifier")
        if family == "product" and not owner.startswith("product:"):
            return Resolution("ambiguous", reason="product alias requires a product-owned artifact")
        return _result(self.repositories.get((owner, key), []))
