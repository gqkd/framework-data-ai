"""Documentation written on branches: what one tree declares, closes and changes against another.

Read by `validate.py --base` for the `BR` checks and by `skills/audit/scripts/work.py`, which
claims elements, reserves identifiers and brings a branch up to date. Both have to agree on
what "this branch created DEC-042" means -- declared here and by no common ancestor, `shared` --
so what a tree declares and what its ancestors share have one home, here.

A TREE IS READ FROM GIT OBJECTS, NOT FROM A CHECKOUT. The other side of a comparison -- the
main line, the point a branch left it -- is a commit, and a second checkout of it would be a
worktree somebody has to remove. The tree's blobs under the project's own directory are written
into a temporary directory and read by the same discovery the validator uses on the working
tree, so an artifact means the same thing on both sides.

NOTHING HERE WRITES TO THE REPOSITORY, fetches or pushes. Those are `work.py`'s, and they are
the person's to approve.
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yaml

from .artifacts import Artifact, as_list, as_map, discover
from .references import ReferenceIndex

# Where a project says that its documentation is written on branches. Its presence is the
# switch: `BR003` asks for reservations only where it exists, and `work.py` refuses to work
# without it. A new file rather than a key in `.framework/sessions.yaml`, because the keys of
# that file are closed and a validator that predates a key stops on it -- every validator a
# project has pinned, and the one `migrate.py` rebuilds out of the history.
WORK = ".framework/work.yaml"

# The keys this version reads. Unlike `sessions.yaml`, an unknown key is a warning and not a
# stop, so that the next version can add one without stopping this one. `mode: additive` is the
# switch of the additive mode; `admins` and `deputies` say who decides in it, `rereading`
# whether a join waits for an attested reading, `thresholds` when the to-do suggests a join.
# Only `mode` and `admins` mean anything without the mode: the rest is read under it.
WORK_KEYS = {"branch_prefix", "people", "mode", "admins", "deputies", "rereading", "thresholds"}

# What `thresholds:` holds, and the value where the project gives none: low, so that joins come
# often and each touches few documents, and a thread stays small.
THRESHOLDS = {"items_per_thread": 5, "effects_per_section": 3, "ready_days": 3, "od_affects": 3,
              "unread_days": 15}

# Refs: a claim on an element, and a reserved number. Tags because a push of a tag that
# exists already is rejected, on every host, without a paid plan: the one atomic operation
# with a central answer that git offers for nothing. Annotated, so that each carries who made
# it, when, and for which branch, and so that after a push whose answer was lost the tag
# object on the remote can be compared with the one made here.
CLAIM_REF = "refs/tags/claim/"
RESERVED_REF = "refs/tags/id/"
# A delegation: who stands in for an admin until it is revoked, named by a slug of the name,
# since a ref carries no spaces and the names in `people` do. The whole name is in the message.
DELEGATION_REF = "refs/tags/delega/"


class BranchError(RuntimeError):
    """A tree or a ref that cannot be read. Never a guess about what it would have said."""


class _Sink:
    """Discovery reports malformed documents; the other side of a comparison is not checked."""

    def add(self, code: str, path: str, message: str) -> None:
        pass


ENV = {**os.environ, "LC_ALL": "C", "LANG": "C", "GIT_TERMINAL_PROMPT": "0"}


def git(root: Path, *args: str, binary: bool = False, stdin: bytes | None = None) -> str | bytes:
    try:
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, timeout=300,
                           env=ENV, input=stdin)
    except (OSError, subprocess.SubprocessError) as e:
        raise BranchError(f"git {' '.join(args[:3])}: {e}") from e
    if r.returncode:
        tail = r.stderr.decode("utf-8", "replace").strip().splitlines()[-1:] or ["failed"]
        raise BranchError(f"git {' '.join(args[:3])}: {tail[0]}")
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")


def prefix(root: Path) -> str:
    """Where the documentation sits inside its repository, `` when at the top."""
    return str(git(root, "rev-parse", "--show-prefix")).strip()


def resolve(root: Path, ref: str) -> str:
    return str(git(root, "rev-parse", "--verify", "-q", f"{ref}^{{commit}}")).strip()


def names(value) -> set[str]:
    """The names `people`, `admins` or `deputies` holds: a list, or a mapping keyed by name."""
    if isinstance(value, dict):
        return {str(k) for k in value}
    if isinstance(value, list):
        return {str(n) for n in value}
    return set()


def slug(name: str) -> str:
    """A name as a ref can carry it."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def delegates(root: Path) -> set[str]:
    """Whoever the delegations this clone holds stand in, as `work.py delegate` named them."""
    listed = str(git(root, "for-each-ref", "--format=%(contents)%00", DELEGATION_REF.rstrip("/")))
    return {f["to"] for f in map(message_fields, listed.split("\0")) if f.get("to")}


def deciders(work: dict | None, delegated: set[str]) -> set[str]:
    """Who decides in the additive mode: the admins, the deputies and whoever holds a delegation."""
    work = work or {}
    return names(work.get("admins")) | names(work.get("deputies")) | delegated


def work_at(root: Path, ref: str) -> dict:
    """`.framework/work.yaml` as `ref` holds it; empty where it does not, or does not parse."""
    try:
        text = str(git(root, "show", f"{ref}:{prefix(root)}{WORK}"))
        data = yaml.safe_load(text) or {}
    except (BranchError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def merge_base(root: Path, a: str, b: str) -> str:
    return str(git(root, "merge-base", a, b)).strip()


def merge_bases(root: Path, a: str, b: str) -> list[str]:
    """Every best common ancestor, not the one git would pick. Two branches that have both
    merged the main line since they parted have two, and comparing with either alone counts
    what the other one holds as created on both sides."""
    return str(git(root, "merge-base", "--all", a, b)).split()


def base_views(root: Path, a: str, b: str, registry: dict,
               scan: dict) -> tuple[list[str], list["View"]]:
    """Every common ancestor of `a` and `b`, and what each holds."""
    bases = merge_bases(root, a, b)
    return bases, [View.of(snapshot(root, base, registry, scan), registry) for base in bases]


def declared_by(views: list["View"]) -> set[tuple[str, str]]:
    """What any of the common ancestors declares: what neither side created."""
    return set().union(*(view.ids() for view in views))


def shared(root: Path, a: str, b: str, registry: dict, scan: dict) -> set[tuple[str, str]]:
    """What any common ancestor of `a` and `b` declares: what neither of them created."""
    return declared_by(base_views(root, a, b, registry, scan)[1])


def snapshot(root: Path, ref: str, registry: dict, scan: dict) -> list[Artifact]:
    """The artifacts of the documentation as `ref` holds it, with paths relative to the root.

    Read from the tree and its blobs, not with `git archive`, which honours `export-ignore`:
    a path a project keeps out of its archives would be missing from this side and look
    created on the other. Links and submodules are not followed. `rel` is what the working
    tree's artifacts carry, so the two sides compare by `rel`. The `path` of each points into a
    temporary directory that is gone when this returns: product directories are compared as
    paths and never opened again.
    """
    where = prefix(root)
    listing = git(root, "ls-tree", "-r", "-z", "--full-tree", ref, *([where] if where else []),
                  binary=True)
    blobs = []
    for row in listing.split(b"\0"):
        if not row:
            continue
        head, _, name = row.partition(b"\t")
        mode, kind, oid = head.decode("ascii").split()
        if kind == "blob" and mode in ("100644", "100755"):
            blobs.append((name.decode("utf-8", "replace"), oid))
    with tempfile.TemporaryDirectory() as tmp:
        if blobs:
            data = git(root, "cat-file", "--batch", binary=True,
                       stdin=b"".join(f"{oid}\n".encode() for _, oid in blobs))
            at = 0
            for name, oid in blobs:
                end = data.index(b"\n", at)
                size = int(data[at:end].split()[2])
                content = data[end + 1:end + 1 + size]
                at = end + 1 + size + 1
                target = Path(tmp) / name
                if ".." in Path(name).parts:
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
        top = Path(tmp) / where if where else Path(tmp)
        if not top.is_dir():
            return []
        return discover(top, scan, registry, _Sink())


@dataclass(frozen=True)
class View:
    """What one tree declares and closes, read once."""
    arts: tuple[Artifact, ...]
    declared: dict[tuple[str, str], tuple[str, ...]]   # (scope, id) -> the files declaring it
    entries: dict[str, dict]                          # OD/KI -> its row in `entries:`
    decisions: dict[str, Artifact]                     # path of a decision -> the decision

    @classmethod
    def of(cls, arts: list[Artifact], registry: dict) -> "View":
        index = ReferenceIndex(arts, registry)
        local = index.local_prefixes
        declared: dict[tuple[str, str], list[str]] = {}
        for ident, targets in index.declarations.items():
            for t in targets:
                # A register's body names entries it does not declare -- a parking line citing
                # an entry of another register -- and the index counts them. For `OD` and `KI`
                # the map is where the declaration is, and it is read below.
                if t.key is not None and t.artifact.type == "open-register":
                    continue
                # Per product only for the families the catalog numbers per product; every
                # other identifier is one sequence across the repository, and a `DEC-042` in
                # one product collides with a `DEC-042` anywhere.
                scope = t.identity.scope if ident.split("-", 1)[0] in local else "*"
                declared.setdefault((scope, ident), []).append(t.artifact.rel.replace("\\", "/"))
        entries: dict[str, dict] = {}
        for a in arts:
            if a.type != "open-register":
                continue
            for key, row in as_map(a.meta.get("entries")).items():
                if isinstance(key, str) and isinstance(row, dict):
                    entries[key] = row
                    # The map is where an entry is declared, and the body may never name it:
                    # the index reads bodies, so the keys are added here. One sequence across
                    # the registers, which is what `REG007` holds them to.
                    rel = a.rel.replace("\\", "/")
                    if rel not in declared.setdefault(("*", key), []):
                        declared[("*", key)].append(rel)
        # By path and not by number: two files carrying one `DEC` number are two decisions,
        # and the case that matters most -- two people deciding one entry, each with the next
        # free number -- is exactly that.
        decisions = {a.rel.replace("\\", "/"): a for a in arts if a.type == "decision-record"}
        return cls(tuple(arts), {k: tuple(sorted(v)) for k, v in declared.items()},
                   entries, decisions)

    def ids(self) -> set[tuple[str, str]]:
        return set(self.declared)

    def closers(self, entry: str) -> set[str]:
        """The decisions this tree says close `entry`: its `closed_by`, and every `accepted`
        decision whose `derives_from` names it. Two sources, read together: `REG005` is the
        check that they agree, and a branch can meet either one first."""
        out = {c for c in as_list(self.entries.get(entry, {}).get("closed_by")) if isinstance(c, str)}
        for dec in self.decisions.values():
            if (dec.meta.get("status") == "accepted" and isinstance(dec.id, str)
                    and entry in as_list(dec.meta.get("derives_from"))):
                out.add(dec.id)
        return out

    def closed(self, entry: str) -> bool:
        """Decided or superseded by its row, or closed by a decision. `parked` is not closed:
        set aside is not answered, and a branch that answers it decides nothing twice."""
        row = self.entries.get(entry)
        if row is not None and row.get("status") in ("decided", "superseded"):
            return True
        return bool(self.closers(entry))


def touched(head: View, before: View) -> dict[str, list[str]]:
    """The open entries a tree changes against another, with what it did to each.

    An entry whose row changed in any field, and an entry a new decision derives from. The
    body of a register is not compared: where the row did not move, a branch that only wrote
    options under an entry is not seen here, and the claim is what makes that work visible.
    """
    out: dict[str, list[str]] = {}
    for key, row in head.entries.items():
        old = before.entries.get(key)
        if old is None:
            out.setdefault(key, []).append("added")
        elif old != row:
            what = "status " + str(row.get("status")) if old.get("status") != row.get("status") else "row changed"
            out.setdefault(key, []).append(what)
    for rel, dec in head.decisions.items():
        if rel in before.decisions:
            continue
        for ref in as_list(dec.meta.get("derives_from")):
            if isinstance(ref, str) and ref in head.entries:
                out.setdefault(ref, []).append(f"{dec.id or rel} derives from it")
    return out


def message_fields(text: str) -> dict:
    """`who`, `branch`, `when` and `to` out of the message `work.py` writes into a claim, a
    reservation or a delegation."""
    out = {}
    for line in text.splitlines():
        key, sep, value = line.partition(": ")
        if sep and key in ("who", "branch", "when", "to"):
            out[key] = value.strip()
    return out
