#!/usr/bin/env python3
"""What there is to do, in a project in the additive mode, and in which threads.

    python3 todo.py --root path/to/documentation
    python3 todo.py --root . --json
    python3 todo.py --root . --summary          # the few lines the SessionStart hook shows
    python3 todo.py --root . --out <file>

THE THREADS ARE COMPUTED, NEVER DRAWN. Nobody -- no person, no agent -- proposes which pieces of
work go together: a script does, from the registers, the contribution policy and the version
pinned of the main line and the claims of the threads already open, with fixed rules, so that
two people reading the to-do on the same day read the same threads. The one input a person
writes is `affects`, the forecast of what an entry or a change will touch, and `AFF001` keeps it
honest; where a mandate is kept apart (`MANDATES APART`, below), a mandate's is instead the code
prefixes of its block in the contribution policy.

THE NODES are the open entries of the open registers (not `parked`, and not closed as `View`
reads it: by a decision their `closed_by` names, or an accepted one deriving from them; and,
where a mandate is kept apart, not a known issue an approved change to do repairs), one node
per `decide_with` group; the changes `approved`; and the increments of each product's current
stage with nothing under them yet -- no `requires`, no change listed in `changes` but a
withdrawn one, no change carrying them -- which are to be decomposed. A change
carries the increments it derives from; a `withdrawn` one hands them on along `withdrawn_by` to
the changes of its product folder it reaches, and one nobody receives is to be decomposed again
(`validate.carried_increments`). A listing in `changes` hands nothing on. An increment is numbered per product, and is
`<product>/INC-NNN` here, as in its claim. A change in `draft` is not a node: it is listed to be
approved, at a join.

THE EDGES order and never join: an entry waits for what its `depends_on` names; a change for the
decisions and entries it derives from -- where a mandate is kept apart, not for a known issue
but one its increments require, below -- and for the entries its increments require; an
increment for the increments it depends on. A node is TO DO when everything it waits for is
closed on the main line; AFTER THE JOIN when what it waits for is closed on the branch of a
thread that is ready; AFTER THREAD X when it is closed on a thread open and not ready yet;
WAITING otherwise, and then it is only counted.

TWO NODES TO DO ARE IN ONE THREAD when they are one `decide_with` group, when they forecast one
anchor -- one `<path>#<anchor>`, two of one document one inside the other by name (`#delta`,
`#delta-inc-17`; the keys of a map stay flat), or one document when either names it whole -- or,
below 4.11.0, when they are changes whose mandates in the contribution policy overlap: code
prefixes in one repository, or the `documents` prefixes, which also meet a forecast on a
document under them; below 4.11.0 too, a node that declares no `affects` touches its whole
product, whatever its mandate says. An entry of the root or the platform register with
`products: [all]`, or with no `products`, stays out of the threads until it has anchors; one
with `[none]` and no anchors is with the others `[none]`. A thread is a connected component; it
is named after its product and its lowest identifier -- OD, then KI, then CHG, then INC, then
the number --, a mandate kept apart after its change. Where a mandate is kept apart, below, the
mandates, the kinds and the nodes with no `affects` follow the rules of that paragraph.

MANDATES APART, where the main line pins 4.11.0 or later, or no version that reads
(`APART_SINCE`, `validate.rules_hold`). A change approved is a thread by itself: it never shares
one with a decision or an entry, and two of them never share one. What two mandates change at
the same time is code -- on the documentation a thread writes effects, and the join reconciles
them -- so a mandate's anchors are the code prefixes of its block in the contribution policy,
and nothing else: not its `affects`, not the `documents` of its block. Two mandates whose
prefixes meet are two threads, each said to share them with the other; whoever opens one makes
the other wait for it, "after thread X", until the join lands it. A mandate with no code
prefixes is said to have none, and makes nobody wait. A known issue an approved change derives
from is not waited for -- the change is what repairs it --, unless an increment of the change
requires it, one it carries or one that lists it in `changes`: then it is a wait, the order a
roadmap wants. An open one not waited for is what the change repairs; a parked one nothing
requires is neither waited for nor listed. While an approved change to do repairs a known issue,
it is no node of its own -- nobody takes it apart from them, even where another change waits for
it -- and is listed with every mandate to do that repairs it; while every change that repairs
it waits, the issue is a node, so that nothing a change waits for can wait on it in turn. The
thread of the change closes it on its branch, `closed_by` the change, when the to-do lists that
mandate alone for it -- of several listed together, none while another is still listed; from
`LINK_SINCE` the join that brings the mandate's code in closes it, `THE CODE OF A THREAD` --; one
its mandates land without closing is a node again. A mandate's thread does not claim it, and
its own `depends_on` and `decide_with` are not followed while it is in their hands. One a
thread claimed before -- while its change waited, before the change was approved, or before
the adoption -- is said with that thread, which releases its claim: the mandate's thread then
closes it, `closed_by` the change, once the code is merged -- from `LINK_SINCE` the join does --,
and two branches never write its row. The other edges stay: the
decisions and the changes a change derives from, and the entries its increments require. So a
mandate whose code is merged and whose closing is pushed is ready -- from `LINK_SINCE`, one whose
verification carries the line of its merge request --, and the next join opened on
the ready threads lands it, whatever else is open. The other nodes meet only nodes of their
own kind, decisions with decisions and work -- entries that are not decisions, increments to
decompose -- with work, and an entry with no `affects` is out of the threads, listed to be
anchored at the next join, instead of tying its whole product to itself.

WHERE A JOIN WAITS FOR NO READING (`rereading: optional`), the living documents whose text a join
brought and nobody has read since, with the day of that join; `LC009` reminds of them past
`unread_days`.

A THREAD OPEN IS FIXED until the join that lands it: the nodes that would fall into its component
wait for it, "after thread X". It is ready when its elements are done on its remote branch --
an entry closed, a change `implemented` (or, from `LINK_SINCE`, with the line of its merge
request), an increment decomposed (a change carrying it, or an
effect on its anchor); in a thread with a decision and a change, all but its changes, which go
back to the main line for the next round -- and the branch carries a commit of its own past the
main line.

THE CODE OF A THREAD, where the main line pins 4.13.0 or later, or no version that reads
(`LINK_SINCE`). A mandate's thread no longer waits for its code to be merged: the join merges it,
and writes the change `implemented`, closing the known issues it repairs, which the thread no
longer closes. Its change is done on the branch when its `## Verification`
carries the line of its merge request, `Merge request: <link> @ <commit>` -- the link, and the
commit of the code's branch the delivery was verified at, forty characters --, the last such
line where there are several. A change written `implemented` on the branch -- before the
adoption, or one with no code to merge --, or closed there otherwise, is done as before, and the
join asks whoever decides whether its code is merged before it lets it in, naming the state
written; the page and the summary say so.
The to-do reads the line and asks nothing of the forge; `work.py join` asks it, at its first
step. A hotfix is no thread, and is listed with the name of its parking branch, where whoever
launches its code delivers it, and which is its claim: `open --branch hotfix-<home>-<change>`.
A parking branch named so, `parcheggio-hotfix-...`, is ready once a `consegne/<CHG>/mr-link.txt`
of its delivery carries the same line, the last of the file, and not before -- its own commit is
not enough --; the join brings it in only once that code is merged.

Read only, and no network: the main line and the remote branches as this clone has them, after
whatever fetch was last made. Exit 0, or 2 when the repository does not allow it.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate as v  # noqa: E402  (the validator's helpers, not its main)

B = v._branches
E = v._effects
FAMILY = {"OD": 0, "KI": 1, "CHG": 2, "INC": 3}
CLOSED_CHANGE = {"implemented", "verified", "rolled-back", "withdrawn"}
# The first version whose to-do keeps a mandate apart (`MANDATES APART`, above): a project whose
# main line pins an earlier one is computed as before, whatever plugin reads it.
APART_SINCE = "4.11.0"
# The first version whose to-do keeps a hotfix out of the threads: an approved change with
# `hotfix: true` has its brief from the lightning join that approved it and its code under way, so
# nobody takes it as a thread -- from `LINK_SINCE` whoever launches its code takes it with its
# parking branch --; whoever decides writes it `implemented` at the first join after its code is
# merged, and until then it holds the mandates that share its code prefixes, as a mandate a thread
# holds does. One whose code will not reach production whoever decides withdraws, at a join: it is
# then no node, and holds nothing.
HOTFIX_SINCE = "4.12.0"
# The first version whose mandate's thread is ready with the line of its merge request in the
# change's `## Verification` (`THE CODE OF A THREAD`, above), and whose hotfix is listed with its
# parking branch: from it whoever launches a hotfix's code opens that branch, which is its claim,
# rather than nobody taking it.
LINK_SINCE = "4.13.0"
# The line: a link and a whole commit, as `exchange.py integrate`'s verification is written by
# the thread from what the code session delivered. A list's dash may open it.
MR_LINE = re.compile(r"^[ \t]*(?:[-*][ \t]+)?Merge request:[ \t]+(https?://\S+)[ \t]+@[ \t]+"
                     r"([0-9a-f]{40})[ \t]*$", re.M)
# A line of front matter that writes a change `approved`: the last commit of the main line whose
# diff adds or removes one, on a hotfix still approved, is the one that approved it. Read by
# `git log -G`, whose regular expression is POSIX: nothing here that reads otherwise in the basic
# and the extended syntax.
APPROVED_LINE = "^status:.*approved"


def git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                       env=B.ENV)
    return r.stdout if r.returncode == 0 else ""


def bare(ident: str) -> str:
    """`INC-001` out of `c/INC-001`."""
    return ident.rsplit("/", 1)[-1]


def merge_request(text: str) -> tuple[str, str] | None:
    """The link and the commit of the last `Merge request: <link> @ <commit>` line of `text`."""
    found = MR_LINE.findall(text or "")
    return (found[-1][0], found[-1][1]) if found else None


def verification(body: str) -> str:
    """A change's `## Verification` section, as the validator locates it; empty where none."""
    lines = (body or "").splitlines()
    span = next((s for s in v.locate_sections(body or "")
                 if s.level == 2 and s.title == "Verification"), None)
    return "" if span is None else "\n".join(lines[span.heading_line:span.end_line])


def hotfix_branch(n: "Node") -> str:
    """The name after the prefix of a hotfix's parking branch, as `exchange.py code` computes
    it: `open --branch hotfix-<home>-<change>` opens it as `parcheggio-hotfix-...`."""
    return "hotfix-" + slug(f"{n.home}-{bare(n.key)}")


def delivered_links(root: Path, ref: str) -> dict[str, tuple[str, str]]:
    """The merge request of each delivery a hotfix's parking branch holds, by change: the line
    of its `<threads>/<slug>/consegne/<CHG>/mr-link.txt`, read on `ref` as `work.py join` reads
    it, with no network."""
    found = {}
    for path in git(root, "ls-tree", "-r", "--name-only", "--full-tree", ref, "--",
                    f"{B.prefix(root)}{E.THREADS}").splitlines():
        m = re.search(r"/consegne/([^/]+)/mr-link\.txt$", path)
        line = merge_request(git(root, "show", f"{ref}:{path}")) if m else None
        if line:
            found[m.group(1)] = line
    return found


def order(ident: str) -> tuple:
    fam, _, num = bare(ident).partition("-")
    return (FAMILY.get(fam, 9), int(num) if num.isdigit() else 0, ident)


def slug(text: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def product_of_path(rel: str) -> str | None:
    parts = rel.split("/")
    return parts[1] if len(parts) > 2 and parts[0] == "products" else None


class Tree:
    """What one tree of the documentation declares, for the to-do: entries with their register,
    decisions, changes, increments and stages, read with the validator's discovery."""

    def __init__(self, arts, registry: dict):
        # Whether an entry is closed is `View`'s to say, as for `open` and `BR002`.
        self.view = B.View.of(arts, registry)
        self.entries: dict[str, dict] = {}      # OD/KI -> row
        self.register: dict[str, str] = {}      # OD/KI -> path of its register
        self.titles: dict[str, str] = {}
        self.decisions: dict[str, str] = {}     # DEC -> status
        self.changes: dict[str, object] = {}    # CHG -> artifact
        self.increments: dict[str, dict] = {}   # <product>/INC -> row
        self.roadmap: dict[str, str] = {}       # <product>/INC -> path of its roadmap
        self.roadmaps = []
        self.keys: set[str] = set()           # `<path>#<key>` of the maps an anchor can name
        for a in arts:
            rel = a.rel.replace("\\", "/")
            if a.meta.get("lifecycle") == "living":
                self.keys |= {f"{rel}#{k}" for m in E.ANCHOR_MAPS.get(a.type or "", ())
                              for k in v.as_map(a.meta.get(m))}
            if a.type == "open-register":
                for key, row in v.as_map(a.meta.get("entries")).items():
                    if isinstance(row, dict):
                        self.entries[str(key)] = row
                        self.register[str(key)] = rel
                for m in re.finditer(r"^###\s+((?:OD|KI)-\d+)\s*[·:.-]?\s*(.*)$", a.body, re.M):
                    self.titles.setdefault(m.group(1), m.group(2).strip())
            elif a.type == "decision-record" and isinstance(a.id, str):
                self.decisions[a.id] = str(a.meta.get("status"))
            elif a.type == "change-contract" and isinstance(a.id, str):
                self.changes[a.id] = a
                head = re.search(r"^#\s+(.+)$", a.body, re.M)
                self.titles.setdefault(a.id, head.group(1).strip() if head else "")
            elif a.type == "roadmap":
                self.roadmaps.append(a)
                product = product_of_path(rel) or "radice"
                for key, row in v.as_map(a.meta.get("increments")).items():
                    if isinstance(row, dict):
                        self.increments[f"{product}/{key}"] = row
                        self.roadmap[f"{product}/{key}"] = rel
        # What each change carries of the increments it derives from, `<product>/INC-NNN`, with
        # what the withdrawn ones handed on. The product is the folder, here as for the roadmap.
        self.carried: dict[str, set[str]] = {}
        products = {c: product_of_path(a.rel.replace("\\", "/")) or "radice"
                    for c, a in self.changes.items()}
        for c, incs in v.carried_increments({c: dict(a.meta, product=products[c])
                                             for c, a in self.changes.items()}).items():
            self.carried[c] = {f"{products[c]}/{x}" for x in incs}

    def closed(self, ident: str) -> bool:
        fam = bare(ident).split("-", 1)[0]
        if fam in ("OD", "KI"):
            return self.view.closed(ident)
        if fam == "DEC":
            return self.decisions.get(ident) in ("accepted", "superseded")
        if fam == "CHG":
            a = self.changes.get(ident)
            return a is not None and a.meta.get("status") in CLOSED_CHANGE
        if fam == "INC":
            return (self.increments.get(ident) or {}).get("state") == "delivered"
        return True                       # what the to-do does not order on does not hold

    def known(self, ident: str) -> bool:
        return ident in self.entries or ident in self.decisions or ident in self.changes \
            or ident in self.increments

    def derives(self, change) -> tuple[set[str], set[str]]:
        """What a change derives from: the identifiers it waits for, and the increments of its
        product it carries, `<product>/INC-NNN` -- its own, or handed on by a withdrawn one."""
        named = [str(x) for x in v.as_list(change.meta.get("derives_from"))]
        return ({x for x in named if not x.startswith("INC-")},
                set(self.carried.get(change.id, set())))


class Node:
    def __init__(self, ids: list[str], kind: str, home: str, products: set[str],
                 anchors: set[str], declared: bool, preds: set[str], everywhere: bool,
                 repairs: tuple[str, ...] = ()):
        self.ids = sorted(ids, key=order)
        self.key = self.ids[0]
        self.kind = kind                  # "decision", "work", or "mandate" where kept apart
        self.home = home                  # the product the name carries: a product, radice, platform
        self.products = products
        self.anchors = anchors
        self.declared = declared          # it has `affects`, or is an increment with its anchor
        self.preds = preds - set(ids)
        self.everywhere = everywhere      # [all], or no products, and no anchors: out of the threads
        self.repairs = sorted(repairs, key=order)   # the known issues a mandate repairs

    def as_dict(self, tree: Tree) -> dict:
        out = {"ids": self.ids, "kind": self.kind,
               "titles": {i: tree.titles.get(i, "") for i in self.ids if tree.titles.get(i)}}
        if self.repairs:
            out["repairs"] = self.repairs
        return out


def listing_of(tree: Tree, change: str) -> set[str]:
    """The increments that list `change` in their `changes`, as the changes written before
    4.3.0 are listed."""
    return {inc for inc, row in tree.increments.items()
            if change in {str(c) for c in v.as_list(row.get("changes"))}}


def policy_at(root: Path, ref: str) -> dict:
    """The contribution policy `ref` holds, or none when it has none that reads."""
    try:
        return json.loads(git(root, "show", f"{ref}:{B.prefix(root)}.framework/contribution-policy.json")
                          or "{}")
    except ValueError:
        return {}


def code_prefixes(policy: dict, rel: str) -> set[str]:
    """A mandate's anchors where it is kept apart: the code prefixes of its block, as
    `code:<repository>:<prefix>`."""
    mandate = (policy.get("mandates") or {}).get(rel) or {}
    return {f"code:{repo}:{str(p).rstrip('/')}"
            for repo, prefixes in (mandate.get("paths") or {}).items()
            if repo != "documents" for p in v.as_list(prefixes)}


def nodes_of(tree: Tree, policy: dict, apart: bool = False) -> tuple[list[Node], list[str]]:
    """The nodes of the main line, and the changes in draft, to be approved. `apart`: a mandate
    is kept apart, and an open known issue an approved change to do repairs is no node."""
    out: list[Node] = []
    # A known issue an approved change derives from is not waited for: waiting for it to close
    # first would hold the change on what the change itself repairs. Open, it is what the change
    # repairs, and no node of its own while an approved change to do repairs it -- nobody takes
    # it apart from them, even where another change waits for it -- but listed with them; the
    # thread of a change that repairs it closes it when the to-do lists that change alone for it,
    # and one its mandates land without closing is a node again, since they are approved no
    # longer. A mandate's thread does not claim it, and its own `depends_on` and `decide_with`
    # are not followed while it is in their hands. One an increment of the change requires --
    # one it carries, or one that lists it in `changes` -- is the order a roadmap wants: a wait
    # for that change, which does not repair it, and a node while no other approved change to
    # do repairs it.
    repairs: dict[str, set[str]] = {}
    if apart:
        for ident, a in tree.changes.items():
            if a.meta.get("status") != "approved":
                continue
            named, carried = tree.derives(a)
            required = {str(r) for inc in carried | listing_of(tree, ident)
                        for r in v.as_list((tree.increments.get(inc) or {}).get("requires"))}
            # Held only by a mandate that is to do: one that waits would hold its issue while
            # what it waits for may wait on that issue, and neither would ever move.
            waits = {w for w in named if not w.startswith("KI-") or w in required} | required
            if any(tree.known(w) and not tree.closed(w) for w in waits):
                continue
            for x in v.as_list(a.meta.get("derives_from")):
                x = str(x)
                if x.startswith("KI-") and x not in required \
                        and tree.entries.get(x, {}).get("status") == "open" and not tree.closed(x):
                    repairs.setdefault(ident, set()).add(x)
    repaired = set().union(*repairs.values())
    # Entries open, one node per `decide_with` group.
    open_entries = [k for k, row in tree.entries.items()
                    if row.get("status") == "open" and not tree.closed(k) and k not in repaired]
    group: dict[str, str] = {k: k for k in open_entries}

    def find(k):
        while group[k] != k:
            group[k] = group[group[k]]
            k = group[k]
        return k
    for k in open_entries:
        for other in v.as_list(tree.entries[k].get("decide_with")):
            if str(other) in group:
                group[find(str(other))] = find(k)
    members: dict[str, list[str]] = {}
    for k in open_entries:
        members.setdefault(find(k), []).append(k)
    for ids in members.values():
        products: set[str] = set()
        anchors: set[str] = set()
        preds: set[str] = set()
        everywhere = False
        for k in ids:
            row = tree.entries[k]
            own = product_of_path(tree.register[k])
            if own:
                products.add(own)
            else:
                named = {str(p) for p in v.as_list(row.get("products"))}
                if not named or "all" in named:
                    everywhere = True
                products |= named - {"all"}
            anchors |= {str(x) for x in v.as_list(row.get("affects"))}
            for x in v.as_list(row.get("depends_on")):
                x = str(x)
                preds.add(f"{own}/{x}" if x.startswith("INC-") and own else x)
        key = sorted(ids, key=order)[0]
        reg = tree.register[key]
        home = product_of_path(reg) or ("platform" if reg.startswith("platform/") else "radice")
        kind = "decision" if any(i.startswith("OD-") for i in ids) else "work"
        out.append(Node(ids, kind, home, products, anchors, bool(anchors), preds,
                        everywhere and not anchors))
    # Changes approved; drafts are listed apart. A change waits for what its increments require,
    # the ones it derives from and, as the changes written before 4.3.0 are listed, the ones that
    # list it in `changes`.
    drafts = []
    proposed = sorted((d for d, s in tree.decisions.items() if s == "proposed"), key=order)
    listing: dict[str, set[str]] = {}
    for inc, row in tree.increments.items():
        for c in v.as_list(row.get("changes")):
            listing.setdefault(str(c), set()).add(inc)
    decomposed: set[str] = set()
    for ident, a in tree.changes.items():
        waits, incs = tree.derives(a)
        decomposed |= incs
        status = a.meta.get("status")
        if status == "draft":
            drafts.append(ident)
        if status != "approved":
            continue
        rel = a.rel.replace("\\", "/")
        product = product_of_path(rel) or "radice"
        derived_kis = {w for w in waits if w.startswith("KI-")}
        required = set()
        for inc in incs | listing.get(ident, set()):
            required |= {str(r) for r in v.as_list((tree.increments.get(inc) or {}).get("requires"))}
        waits |= required
        declared = {str(x) for x in v.as_list(a.meta.get("affects"))}
        anchors = set(declared)
        mandate = (policy.get("mandates") or {}).get(rel) or {}
        if apart:
            # What a mandate changes at the same time as another is code: on the documentation
            # a thread writes effects, and the join reconciles them. Its anchors are its code
            # prefixes, and nothing else.
            code = code_prefixes(policy, rel)
            out.append(Node([ident], "mandate", product, {product}, code, bool(code),
                            (waits - derived_kis) | required, False,
                            tuple(repairs.get(ident, ()))))
            continue
        for repo, prefixes in (mandate.get("paths") or {}).items():
            kind = "doc" if repo == "documents" else f"code:{repo}"
            anchors |= {f"{kind}:{str(p).rstrip('/')}" for p in v.as_list(prefixes)}
        out.append(Node([ident], "work", product, {product}, anchors, bool(declared), waits,
                        False))
    # Increments of the current stage of each roadmap with nothing under them yet.
    for rmp in tree.roadmaps:
        rel = rmp.rel.replace("\\", "/")
        product = product_of_path(rel) or "radice"
        plan = v.roadmap_plan(rmp.meta)
        done = {s: all((plan["increments"].get(str(i)) or {}).get("state") == "delivered"
                       for i in v.as_list(plan["stages"][s].get("increments")))
                for s in plan["order"]}
        current = [s for s in plan["order"] if not done[s]
                   and all(done.get(str(x), True) for x in v.as_list(plan["stages"][s].get("after")))]
        for s in current:
            for inc in plan["per_stage"].get(s, []):
                row = plan["increments"].get(inc) or {}
                # A change it lists, as the changes written before 4.3.0 are listed, holds it
                # as a change carrying it does -- unless it was withdrawn: the listing hands
                # nothing on, and the increment is to be decomposed again.
                listed = [c for c in v.as_list(row.get("changes"))
                          if (tree.changes.get(str(c)) is None
                              or tree.changes[str(c)].meta.get("status") != "withdrawn")]
                if row.get("state") == "delivered" or v.as_list(row.get("requires")) \
                        or listed or f"{product}/{inc}" in decomposed:
                    continue
                out.append(Node([f"{product}/{inc}"], "work", product, {product},
                                {f"{rel}#{inc}"}, True,
                                {f"{product}/{x}" for x in v.as_list(row.get("depends_on"))},
                                False))
    return out, sorted(drafts, key=order) + proposed


def meet(a: set[str], b: set[str], nest: str = "both", flat=frozenset()) -> list[str]:
    """The anchors two forecasts share: one `<path>#<anchor>`; two of one document one of which
    is inside the other by name, `#delta` and `#delta-inc-17`; one document when either names
    it whole; a code prefix within another in one repository; a documents prefix with a
    document under it.

    INSIDE BY NAME, SINCE 4.10.0, `<id>-<rest>` within `<id>`, and not by the headings. A name
    does not move when a thread adds lines, and a heading's reach does: a line between a marker
    and its heading, a second marker, a heading of the same level, and two threads on a
    section and on one inside it would stop meeting without anybody seeing it. A name the
    headings contradict would err both ways -- in the threads one meeting too many, at the
    join an effect taken as within a forecast it is not within --, and `AFF001` and `EFF001`
    hold the name to the headings, both ways, wherever an anchor is in use. Keys of a map stay flat --
    nothing in a body says for sure which section holds one, and a key of `STACK` or of
    `GLOSSARY` is written with hyphens --: `flat` holds the anchors that are keys
    (`Tree.keys`).

    `nest="inside"` reads the second set inside the first and not the reverse: the join asks
    whether an effect is within what its thread forecast, and one on `#delta` is not within a
    forecast on `#delta-inc-17`, nor one on the whole document within a forecast on a section."""
    def doc(x: str) -> str | None:
        return x[4:] if x.startswith("doc:") else None
    out = []
    for x in a:
        for y in b:
            if x == y:
                out.append(x)
            elif "#" in x and "#" in y and not x.startswith(("code:", "doc:")) \
                    and x.split("#", 1)[0] == y.split("#", 1)[0] and x not in flat and y not in flat:
                ax, ay = x.split("#", 1)[1], y.split("#", 1)[1]
                if ay.startswith(ax + "-"):
                    out.append(x)
                elif nest == "both" and ax.startswith(ay + "-"):
                    out.append(y)
            elif x.startswith("code:") and y.startswith("code:"):
                rx, _, px = x[5:].rpartition(":")
                ry, _, py = y[5:].rpartition(":")
                if rx == ry and (px == py or px.startswith(py + "/") or py.startswith(px + "/")):
                    out.append(f"{rx}:{min(px, py, key=len)}")
            elif doc(x) is not None or doc(y) is not None:
                pre, other = (doc(x), y) if doc(x) is not None else (doc(y), x)
                path = doc(other) if doc(other) is not None else other.split("#", 1)[0]
                if not other.startswith("code:") and (path == pre or path.startswith(pre + "/")
                                                     or pre.startswith(path + "/")):
                    out.append(pre)
            elif "#" not in x and y.split("#", 1)[0] == x or \
                    nest == "both" and "#" not in y and x.split("#", 1)[0] == y:
                out.append(x if "#" not in x else y)
    return sorted(set(out))


def placed(target: str, own: set[str], others: dict[str, set[str]], flat=frozenset()) -> tuple[bool, list[str]]:
    """Where an effect stands at the join: within what its own thread forecast -- the same
    anchor, or one inside it --, and which other threads forecast anything it meets, in either
    direction, so that two threads on the same lines are seen."""
    return (bool(meet(own, {target}, nest="inside", flat=flat)),
            sorted(n for n, anchors in others.items() if meet(anchors, {target}, flat=flat)))


def threads_of(nodes: list[Node], flat=frozenset(), apart: bool = False) -> list[dict]:
    """The connected components of the nodes to do, with why each holds together.

    `apart`: a mandate is a thread by itself, and what it shares with another -- a code prefix
    -- is said in its `notes`, for whoever opens one to know the other waits; the others meet
    only nodes of their own kind, decisions with decisions and work with work, and a node with
    no anchors is not here at all (`compute` lists it to be anchored)."""
    parent = list(range(len(nodes)))
    why: dict[int, set[str]] = {i: set() for i in range(len(nodes))}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def join(i, j, reason):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri
            why[ri] |= why.pop(rj, set())
        why[find(i)].add(reason)
    notes: dict[int, list[str]] = {i: [] for i in range(len(nodes))}
    for i, a in enumerate(nodes):
        if apart and a.kind == "mandate" and not a.declared:
            notes[i].append("no code paths in the contribution policy: nothing says which "
                            "files it changes, and nothing makes another mandate wait for it")
        for j in range(i + 1, len(nodes)):
            b = nodes[j]
            if apart and (a.kind == "mandate") != (b.kind == "mandate"):
                continue
            shared = meet(a.anchors, b.anchors, flat=flat)
            if apart and a.kind == "mandate":
                if shared:
                    for x, y in ((i, b), (j, a)):
                        notes[x].append(f"shares {', '.join(shared)} with "
                                        f"{bare(y.key)}: whoever opens one makes the other wait")
                continue
            if apart and a.kind != b.kind:
                continue
            if shared:
                join(i, j, f"{bare(a.key)} and {bare(b.key)}: {', '.join(shared)}")
                continue
            if apart:
                continue
            # A node that declares no forecast touches its whole product.
            for x, y in ((a, b), (b, a)):
                if not x.declared and x.products & y.products:
                    join(i, j, f"{bare(x.key)} has no affects, and touches "
                               f"{', '.join(sorted(x.products & y.products))}")
                    break
    out: dict[int, list[int]] = {}
    for i in range(len(nodes)):
        out.setdefault(find(i), []).append(i)
    threads = []
    for root, members in out.items():
        ns = sorted((nodes[i] for i in members), key=lambda n: order(n.key))
        first = ns[0]
        threads.append({"name": slug(f"{first.home}-{bare(first.key)}"), "nodes": ns,
                        "why": sorted(why.get(root, set())),
                        "notes": sorted({x for i in members for x in notes[i]}),
                        "mixed": any(n.kind == "decision" for n in ns)
                        and any(bare(n.key).startswith("CHG-") for n in ns)})
    return sorted(threads, key=lambda t: t["name"])


def remote_branches(root: Path, remote: str, prefix: str) -> dict[str, str]:
    """Branch name -> remote-tracking ref, for the work branches."""
    out = {}
    for ref in git(root, "for-each-ref", "--format=%(refname)", f"refs/remotes/{remote}/").split():
        name = ref[len(f"refs/remotes/{remote}/"):]
        if name.startswith(prefix):
            out[name] = ref
    return out


def claims(root: Path) -> dict[str, list[tuple[str, str]]]:
    """Branch -> [(element, who)], from the claim tags this clone holds: `OD-042`, or
    `<product>/INC-001` for a family numbered per product."""
    out: dict[str, list[tuple[str, str]]] = {}
    listed = git(root, "for-each-ref", "--format=%(refname)%00%(contents)%00%00",
                 B.CLAIM_REF.rstrip("/"))
    for record in listed.split("\x00\x00"):
        record = record.strip("\n")
        if not record:
            continue
        name, _, body = record.partition("\x00")
        f = B.message_fields(body)
        if f.get("branch"):
            out.setdefault(f["branch"], []).append((name[len(B.CLAIM_REF):], f.get("who", "?")))
    return out


def effects_on(root: Path, ref: str) -> list:
    where = B.prefix(root)
    listed = git(root, "ls-tree", "-r", "--name-only", "--full-tree", ref, "--",
                 f"{where}{E.THREADS}")
    found = []
    for path in listed.split("\n"):
        if path.endswith(f"/{E.EFFECTS}"):
            found += E.read(git(root, "show", f"{ref}:{path}"))[0]
    return found


def join_state(after_join: bool, ready_ages: list[int], per_section: dict[str, int],
               limits: dict) -> str:
    """Needed when something waits on a thread that is ready; advised when the effects waiting
    on one section, or the age of the oldest thread ready, pass their threshold; possible when a
    thread is ready."""
    if after_join:
        return "needed"
    if ready_ages and (any(c > limits["effects_per_section"] for c in per_section.values())
                       or max(ready_ages) > limits["ready_days"]):
        return "advised"
    return "possible" if ready_ages else "not yet"


def compute(root: Path, remote: str, main: str) -> dict:
    registry = v.yaml.safe_load(v.REGISTRY.read_text(encoding="utf-8"))
    scan = v.load_scan(registry, v.load_project(root))
    base = f"{remote}/{main}"
    if not git(root, "rev-parse", "--verify", "-q", f"{base}^{{commit}}").strip():
        base = main
    if not git(root, "rev-parse", "--verify", "-q", f"{base}^{{commit}}").strip():
        v.refuse(f"neither {remote}/{main} nor {main} is a commit here: the to-do reads the main line.")
    work = B.work_at(root, base)
    if work.get("mode") != "additive":
        return {"additive": False, "base": base}
    prefix = str(work.get("branch_prefix") or "work/")
    limits = {**B.THRESHOLDS, **(work.get("thresholds") or {})}
    policy = policy_at(root, base)
    main_tree = Tree(B.snapshot(root, base, registry, scan), registry)
    # The version the main line pins, as its registers, `work.yaml` and policy are read here --
    # the `scan` above is still the checkout's --: a pin in this checkout and not landed, or a
    # checkout nobody brought up to the adoption, would give two people reading the same remote
    # two sets of rules.
    try:
        pinned = v.yaml.safe_load(git(root, "show", f"{base}:{B.prefix(root)}framework.yaml")) or {}
    except v.yaml.YAMLError:
        pinned = {}
    apart = v.rules_hold(pinned if isinstance(pinned, dict) else {}, APART_SINCE)
    hotfix_on = v.rules_hold(pinned if isinstance(pinned, dict) else {}, HOTFIX_SINCE)
    link_on = v.rules_hold(pinned if isinstance(pinned, dict) else {}, LINK_SINCE)
    nodes, drafts = nodes_of(main_tree, policy, apart)

    # Threads open: a work branch with claims, or a parking branch. The others are abandoned,
    # and what they hold counts for nothing until somebody takes them again.
    branches = remote_branches(root, remote, prefix)
    held = claims(root)
    open_threads: dict[str, dict] = {}
    for name, ref in branches.items():
        tail = name[len(prefix):]
        if tail.startswith(B.JOIN):
            continue
        if tail.startswith(B.PARKING) or held.get(name):
            open_threads[name] = {"ref": ref, "claims": held.get(name, []),
                                  "parking": tail.startswith(B.PARKING)}
    abandoned = sorted(name for name in branches if name not in open_threads
                       and not name[len(prefix):].startswith(B.JOIN))
    trees: dict[str, Tree] = {}
    for name, t in open_threads.items():
        try:
            trees[name] = Tree(B.snapshot(root, t["ref"], registry, scan), registry)
        except B.BranchError:
            continue

    # Readiness, and the effects waiting, per thread open.
    now = datetime.now(timezone.utc)
    effects: dict[str, list[str]] = {}
    per_section: dict[str, int] = {}
    for name, t in sorted(open_threads.items()):
        tree = trees.get(name)
        found = effects_on(root, t["ref"])
        for eff in found:
            effects.setdefault(eff.path, []).append(f"{eff.target} ({name})")
            per_section[eff.target] = per_section.get(eff.target, 0) + 1
        own = int(git(root, "rev-list", "--count", "--no-merges", f"{base}..{t['ref']}").strip() or 0)
        anchored = {f"{e.path}#{e.anchor}" for e in found if e.anchor}
        ids = [i for i, _ in t["claims"]]
        # Mixed -- a decision and a change: ready when its entries are closed, and its changes go
        # back to the main line for the next round.
        mixed = any(i.startswith("OD-") for i in ids) and any(i.startswith("CHG-") for i in ids)
        pending = [i for i in ids if not i.startswith("CHG-")] if mixed else ids

        # The merge request of each change claimed, where its verification on the branch has
        # the line (`LINK_SINCE`): what makes the change done, and what the join checks.
        t["links"] = {}
        for i in ids:
            change = tree.changes.get(i) if tree is not None and link_on else None
            line = merge_request(verification(change.body)) if change is not None else None
            if line:
                t["links"][i] = line
        # The changes claimed written `implemented` -- or closed otherwise -- on the branch with
        # no line, each with the state written: done, and the join asks whoever decides whether
        # their code is merged, naming that state.
        t["implemented"] = {i: tree.changes[i].meta.get("status") for i in ids
                            if link_on and bare(i).startswith("CHG-") and tree is not None
                            and tree.closed(i) and i not in t["links"]}
        # A hotfix's parking branch, by its name: ready with the line of its delivery's
        # `mr-link.txt`, which `join` checks on the forge, and not from its first commit.
        t["hotfix"] = link_on and t["parking"] and name[len(prefix):].startswith(
            f"{B.PARKING}hotfix-")
        if t["hotfix"]:
            t["links"] = delivered_links(root, t["ref"])

        def done(i: str) -> bool:
            if tree is None:
                return False
            if bare(i).startswith("INC-"):
                decomposing = any(i in tree.derives(a)[1] for a in tree.changes.values())
                return decomposing or f"{main_tree.roadmap.get(i, '')}#{bare(i)}" in anchored
            return tree.closed(i) or i in t["links"]
        t["ready"] = own > 0 and all(done(i) for i in pending) \
            and (not t["hotfix"] or bool(t["links"]))
        t["effects"] = len(found)
        stamp = git(root, "log", "-1", "--format=%cI", t["ref"]).strip()
        t["age_days"] = (now - datetime.fromisoformat(stamp)).days if stamp else 0
    ready = sorted(n for n, t in open_threads.items() if t["ready"])

    # What a join brought and nobody has read since, where a join waits for no reading: as
    # `LC009` reads it, a bare `last_review` in the offset of the commit that wrote the line.
    # A shallow clone has no history to read it from, and the to-do says so rather than stop.
    unread: list[dict] | None = []
    if v.rereading_optional(work, pinned if isinstance(pinned, dict) else {}):
        repo = None
        try:
            # A refusal here leaves the rest of the to-do standing: what it would print is
            # replaced by the line that says this part was not computed.
            with contextlib.redirect_stderr(io.StringIO()):
                if git(root, "rev-parse", "--is-shallow-repository").strip() == "true":
                    raise B.BranchError("shallow")
                repo = v.Repository.open(root, tip=base)
                if repo is not None:
                    _unread(repo, v.read_joins(repo), main_tree, base, now, unread)
        except (SystemExit, B.BranchError):
            unread = None
        finally:
            if repo is not None:
                repo.close()


    def state(n: Node) -> tuple[str, list[str]]:
        open_ = [p for p in n.preds if main_tree.known(p) and not main_tree.closed(p)]
        if not open_:
            return "todo", []
        if all(any(trees[r].closed(p) for r in ready if r in trees) for p in open_):
            return "after-join", []
        if all(any(t.closed(p) for t in trees.values()) for p in open_):
            return "after-thread", sorted(name for name, t in trees.items()
                                          if any(t.closed(p) for p in open_))
        return "waiting", []
    # The hotfixes approved, out of the threads (`HOTFIX_SINCE`): listed apart, with the known
    # issues each repairs, until a join writes them `implemented`.
    hotfixes = [n for n in nodes if hotfix_on and n.kind == "mandate"
                and (main_tree.changes.get(n.key) is not None)
                and main_tree.changes[n.key].meta.get("hotfix") is True]
    others = [n for n in nodes if not any(n is h for h in hotfixes)]
    # The days since each was approved, so that one stuck -- its code never merged -- is seen:
    # one `git log` on its file, none where there is no hotfix. A shallow clone says none: the
    # commit at its edge adds every file whole, and would read as the approval of each.
    hotfix_days: dict[str, int | None] = {h.key: None for h in hotfixes}
    if hotfixes and git(root, "rev-parse", "--is-shallow-repository").strip() != "true":
        for h in hotfixes:
            rel = main_tree.changes[h.key].rel.replace("\\", "/")
            stamp = git(root, "log", "-1", "--format=%cI", "-G", APPROVED_LINE, base, "--",
                        rel).strip()
            hotfix_days[h.key] = (now - datetime.fromisoformat(stamp)).days if stamp else None
    states = {id(n): state(n) for n in others}
    todo = [n for n in others if states[id(n)][0] == "todo"]
    after_join = [n for n in others if states[id(n)][0] == "after-join"]
    after_thread = [{"node": n, "threads": states[id(n)][1]} for n in others
                    if states[id(n)][0] == "after-thread"]
    waiting: dict[str, int] = {}
    for n in others:
        if states[id(n)][0] == "waiting":
            waiting[n.home] = waiting.get(n.home, 0) + 1
    # Out of the threads until somebody anchors them: where a mandate is kept apart, every entry
    # with no `affects`, which is an exception for the next join to clear and no longer a node
    # that ties its whole product to itself; before, those of every product.
    unanchored = [n for n in todo if n.everywhere
                  or (apart and n.kind != "mandate" and not n.declared)]

    # The threads to take; what falls into the component of a thread open waits for it, and a
    # mandate that shares a code prefix with one a thread open holds waits for that thread.
    claimed = {ident: name for name, t in open_threads.items() for ident, _ in t["claims"]}
    held_mandates = [n for n in nodes if n.kind == "mandate" and n.key in claimed]
    free = []
    for t in threads_of([n for n in todo if n not in unanchored], flat=main_tree.keys,
                        apart=apart):
        holders = sorted({claimed[i] for n in t["nodes"] for i in n.ids if i in claimed}
                         | {claimed[m.key] for n in t["nodes"] if n.kind == "mandate"
                            for m in held_mandates
                            if m is not n and meet(n.anchors, m.anchors)}
                         | {f"hotfix {bare(h.key)}" for n in t["nodes"] if n.kind == "mandate"
                            for h in hotfixes if meet(n.anchors, h.anchors)})
        if holders:
            after_thread += [{"node": n, "threads": holders} for n in t["nodes"]
                             if not any(i in claimed for i in n.ids)]
        else:
            free.append(t)
    join = join_state(bool(after_join), [open_threads[n]["age_days"] for n in ready],
                      per_section, limits)
    return {"additive": True, "base": base, "prefix": prefix, "limits": limits,
            "threads": free, "open": open_threads, "after_thread": after_thread,
            "after_join": after_join, "waiting": waiting, "drafts": drafts,
            "unanchored": unanchored, "abandoned": abandoned, "effects": effects,
            "hotfixes": hotfixes, "hotfix_days": hotfix_days, "link_on": link_on,
            "ready": ready, "join": join, "unread": unread, "tree": main_tree,
            "repaired": repaired_by(nodes),
            # A repaired issue a thread claimed before -- while its change waited, before the
            # change was approved, or before the adoption -- is said with that thread, which
            # releases its claim so that the mandate's thread closes it.
            "repaired_held": {k: claimed[k] for k in repaired_by(nodes) if k in claimed}}


def repaired_by(nodes: list[Node]) -> dict[str, list[str]]:
    """Each known issue an approved mandate to do repairs, with every mandate to do that does: a
    mandate that waits holds none, and the issue it would repair stays a node while it waits."""
    out: dict[str, list[str]] = {}
    for n in nodes:
        for k in n.repairs:
            out.setdefault(k, []).append(n.key)
    return {k: sorted(out[k], key=order) for k in sorted(out, key=order)}


def _unread(repo, joins: dict, tree: Tree, base: str, now: datetime, out: list) -> None:
    """The living documents of the main line whose text a join brought and nobody has read
    since, with the day of that join, into `out`."""
    for a in tree.view.arts:
        if a.meta.get("lifecycle") != "living":
            continue
        rel = a.rel.replace("\\", "/")
        value = v.parse_moment(a.meta.get("last_review"))
        attested = None
        if value is not None:
            line = v._review_line(repo.blob(base, rel) or "")
            committed = repo.blame(rel, line, rev=base)[1] if line else None
            attested = v.as_instant(value, committed.tzinfo if committed else None)[0]
        hit = v.unread_join(repo, joins, rel, attested)
        if hit:
            out.append({"path": rel, "merged": hit[1], "days": (now - hit[1]).days})


def _approved_ago(days: int | None, lead: str = " --") -> str:
    """How long ago a hotfix was approved, where the main line's history says it."""
    return "" if days is None else f"{lead} approved {days} day{'' if days == 1 else 's'} ago"


def _parking(r: dict, n: Node) -> str:
    """The parking branch of a hotfix, from `LINK_SINCE`: open, and so taken, or its name."""
    if not r.get("link_on"):
        return ""
    name = f"{r.get('prefix', 'work/')}{B.PARKING}{hotfix_branch(n)}"
    if name in r.get("open", {}):
        return f" -- parking branch {name}, open: taken"
    return f" -- parking branch {name}, `open --branch {hotfix_branch(n)}`"


def describe(n: Node, tree: Tree) -> str:
    titles = "; ".join(f"{bare(i)} {tree.titles[i]}" if tree.titles.get(i) else
                       (f"{bare(i)} ({i.split('/')[0]})" if "/" in i else i) for i in n.ids)
    kind = ("decision" if n.kind == "decision" else "mandate" if n.kind == "mandate" else
            "to decompose" if bare(n.key).startswith("INC-") else "work")
    repairs = f" -- repairs {', '.join(n.repairs)}" if n.repairs else ""
    return f"{kind}: {titles}{repairs}"


def markdown(r: dict) -> str:
    if not r["additive"]:
        return f"The main line ({r['base']}) does not declare `mode: additive`: no to-do here.\n"
    tree = r["tree"]
    out = [f"# To do, from {r['base']}", ""]
    out.append(f"Join: **{r['join']}**" + (f" -- ready: {', '.join(r['ready'])}" if r["ready"] else ""))
    if r["unanchored"]:
        out.append(f"To anchor, at the next join: **{len(r['unanchored'])}**")
    out.append("")
    if r["open"]:
        out.append("## Threads open")
        for name, t in sorted(r["open"].items()):
            who = sorted({w for _, w in t["claims"]})
            what = "parking" if t["parking"] else ", ".join(i for i, _ in t["claims"])
            line = ("" if not t.get("hotfix") else
                    " -- a hotfix's: `join` brings it in once its code is merged on the forge, "
                    "which only `join` asks, and until then it waits there"
                    if t["ready"] else
                    " -- a hotfix's, by its name: ready once a `consegne/<CHG>/mr-link.txt` of "
                    "its delivery carries `Merge request: <link> @ <commit>`; a parking branch "
                    "that is no hotfix's goes on one opened with another name"
                    if not t.get("links") else "")
            closed = t.get("implemented") or {}
            if t["ready"] and closed:
                line += (" -- " + ", ".join(f"{i} `{s}`" for i, s in sorted(closed.items()))
                         + " on its branch with no line of its merge request: `join` asks "
                         "whoever decides whether its code is merged")
            out.append(f"- {name}: {what}; in the hands of {', '.join(who) or '-'}; "
                       f"{'ready' if t['ready'] else 'not ready'}{line}; effects waiting: "
                       f"{t['effects']}")
        out.append("")
    out.append("## Threads to take")
    if not r["threads"]:
        out.append("- none")
    for t in r["threads"]:
        flag = " (with a decision: an admin, a deputy or a delegate takes it)" if any(
            n.kind == "decision" for n in t["nodes"]) else ""
        big = (f" -- over {r['limits']['items_per_thread']} elements: what holds it together is "
               "below" if sum(len(n.ids) for n in t["nodes"]) > r["limits"]["items_per_thread"] else "")
        out.append(f"### {t['name']}{flag}{big}")
        for n in t["nodes"]:
            out.append(f"- {describe(n, tree)}")
        for reason in t["why"]:
            out.append(f"  - together: {reason}")
        for note in t.get("notes", []):
            out.append(f"  - note: {note}")
    out.append("")
    if r["after_thread"]:
        out.append("## After a thread open")
        for item in r["after_thread"]:
            out.append(f"- {describe(item['node'], tree)} -- after {', '.join(item['threads'])}")
        out.append("")
    if r.get("hotfixes"):
        out.append("## Hotfixes: no thread to take; `implemented` at the first join after the "
                   "merge of their code, by whoever decides"
                   + ("; whoever launches the code of one opens its parking branch, its claim, "
                      "where the delivery goes" if r.get("link_on") else ""))
        days = r.get("hotfix_days", {})
        for n in r["hotfixes"]:
            out.append(f"- {describe(n, tree)}" + _approved_ago(days.get(n.key))
                       + _parking(r, n)
                       + ("" if n.declared else " -- no code paths in the contribution policy: "
                          "nothing says which files it changes, and nothing waits for it"))
        out.append("  One whose code will not reach production whoever decides withdraws at a "
                   "join, `withdrawn_by` the `DEC` that says so: the mandates it holds stop "
                   "waiting, and the known issues it repairs are threads to take again.")
        out.append("")
    if r["after_join"]:
        out.append("## After the join")
        for n in r["after_join"]:
            out.append(f"- {describe(n, tree)}")
        out.append("")
    if r.get("repaired"):
        out.append("## Known issues an approved mandate to do repairs: closed, `closed_by` the "
                   + ("change, by whoever decides at the join that writes it `implemented` -- "
                      "the one that brings in the code of a mandate listed alone for one, or "
                      "after a hotfix's code is merged" if r.get("link_on") else
                      "change, by the thread of a mandate listed alone for one -- for a hotfix, "
                      "by whoever decides at the join that writes it `implemented`"))
        held = r.get("repaired_held", {})
        out += [f"- {k}: {', '.join(cs)}" + (f" -- claimed by {held[k]}, which releases it: "
                                             + ("the join of its mandate closes it"
                                                if r.get("link_on") else "its mandate closes it")
                                             if k in held else "")
                for k, cs in r["repaired"].items()]
        out.append("")
    if r["drafts"]:
        out.append("## Changes to approve and decisions to accept, at a join")
        out += [f"- {d} {tree.titles.get(d, '')}".rstrip() for d in r["drafts"]]
        out.append("")
    if r["unanchored"]:
        out.append("## Without anchors: out of the threads until somebody anchors them, at a join")
        out += [f"- {describe(n, tree)}" for n in r["unanchored"]]
        out.append("")
    if r["waiting"]:
        out.append("## Waiting")
        out += [f"- {p}: {c}" for p, c in sorted(r["waiting"].items())]
        out.append("")
    if r["effects"]:
        out.append("## Effects waiting, by document")
        for path, targets in sorted(r["effects"].items()):
            out.append(f"- {path}: {len(targets)} -- {'; '.join(sorted(targets))}")
        out.append("")
    if r["unread"] is None:
        out += ["## Merged by a join, not reread", "- not computed: the history of the joins could "
                "not be read here -- a shallow clone wants `git fetch --unshallow`", ""]
    if r["unread"]:
        out.append("## Merged by a join, not reread")
        for u in r["unread"]:
            late = " -- past the reminder" if u["days"] > r["limits"]["unread_days"] else ""
            out.append(f"- {u['path']}: merged on {u['merged']:%Y-%m-%d}, not reread "
                       f"({u['days']} days){late}")
        out.append("")
    if r["abandoned"]:
        out.append("## Branches without claims (abandoned)")
        out += [f"- {b}" for b in r["abandoned"]]
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def summary(r: dict) -> str:
    """The few lines the SessionStart hook puts in a session's context."""
    if not r["additive"]:
        return ""
    lines = [f"Additive mode, from {r['base']}. Join: {r['join']}."
             + (f" To anchor at the next join: {len(r['unanchored'])}." if r["unanchored"] else "")]
    for name, t in sorted(r["open"].items()):
        who = sorted({w for _, w in t["claims"]}) or ["-"]
        lines.append(f"- open: {name} ({', '.join(who)}){' ready' if t['ready'] else ''}"
                     + (", a hotfix's: `join` brings it in once its code is merged on the forge"
                        if t["ready"] and t.get("hotfix") else "")
                     + (", with a change closed on its branch with no line of its merge request: "
                        "`join` asks whoever decides whether its code is merged"
                        if t["ready"] and t.get("implemented") else ""))
    for t in r["threads"][:10]:
        lines.append(f"- to take: {t['name']} ({', '.join(i for n in t['nodes'] for i in n.ids)})")
    if len(r["threads"]) > 10:
        lines.append(f"- and {len(r['threads']) - 10} more threads to take")
    for n in r.get("hotfixes", []):
        ago = _approved_ago(r.get("hotfix_days", {}).get(n.key), ",")
        lines.append(f"- hotfix: {bare(n.key)}{ago}, `implemented` at the first join after its "
                     "code is merged"
                     + (f"; repairs {', '.join(n.repairs)}" if n.repairs else "")
                     + _parking(r, n).replace(" -- ", "; ", 1))
    for path, targets in sorted(r["effects"].items()):
        lines.append(f"- effects waiting on {path}: {len(targets)}")
    if r["unread"] is None:
        lines.append("- what the joins brought and nobody read: not computed here (`todo.py` says why)")
    late = [u["path"] for u in r["unread"] or [] if u["days"] > r["limits"]["unread_days"]]
    if late:
        lines.append(f"- merged by a join and not reread for over {r['limits']['unread_days']} "
                     f"days: {', '.join(late[:5])}" + (f" and {len(late) - 5} more" if len(late) > 5 else ""))
    lines.append("The whole to-do: python3 <framework>/skills/audit/scripts/todo.py --root <documentation>")
    return "\n".join(lines)[:4000] + "\n"


def as_json(r: dict) -> dict:
    if not r["additive"]:
        return {"additive": False, "base": r["base"]}
    tree = r["tree"]
    return {"additive": True, "base": r["base"], "join": r["join"], "ready": r["ready"],
            "threads": [{"name": t["name"], "why": t["why"], "notes": t.get("notes", []),
                         "mixed": t["mixed"], "nodes": [n.as_dict(tree) for n in t["nodes"]]}
                        for t in r["threads"]],
            "open": {k: {"claims": [i for i, _ in t["claims"]], "who": sorted({w for _, w in t["claims"]}),
                         "parking": t["parking"], "ready": t["ready"], "effects": t["effects"],
                         "merge_requests": {c: {"link": link, "commit": sha}
                                            for c, (link, sha) in t.get("links", {}).items()}}
                     for k, t in r["open"].items()},
            "after_thread": [{"ids": i["node"].ids, "threads": i["threads"]} for i in r["after_thread"]],
            "after_join": [n.ids for n in r["after_join"]], "waiting": r["waiting"],
            "drafts": r["drafts"], "unanchored": [n.ids for n in r["unanchored"]],
            "hotfixes": [{**n.as_dict(tree), "days": r.get("hotfix_days", {}).get(n.key),
                          **({"branch": f"{r['prefix']}{B.PARKING}{hotfix_branch(n)}"}
                             if r.get("link_on") else {})}
                         for n in r.get("hotfixes", [])],
            "repaired": r.get("repaired", {}), "repaired_held": r.get("repaired_held", {}),
            "abandoned": r["abandoned"], "effects": r["effects"],
            "unread": None if r["unread"] is None else
            [{"path": u["path"], "merged": u["merged"].date().isoformat(), "days": u["days"]}
             for u in r["unread"]]}


def main() -> int:
    ap = argparse.ArgumentParser(description="The to-do of a project in the additive mode")
    ap.add_argument("--root", default=".", type=Path, help="the documentation repository")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--main", default="main", help="the main line")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--summary", action="store_true", help="the lines the SessionStart hook shows")
    ap.add_argument("--out", type=Path, help="write the to-do to this file")
    args = ap.parse_args()
    root = args.root.resolve()
    if not root.is_dir() or not git(root, "rev-parse", "--show-toplevel"):
        v.refuse(f"{root}: not a directory inside a git repository.")
    r = compute(root, args.remote, args.main)
    text = (json.dumps(as_json(r), indent=2, ensure_ascii=False) + "\n" if args.json
            else summary(r) if args.summary else markdown(r))
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
