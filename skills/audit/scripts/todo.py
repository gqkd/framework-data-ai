#!/usr/bin/env python3
"""What there is to do, in a project in the additive mode, and in which threads.

    python3 todo.py --root path/to/documentation
    python3 todo.py --root . --json
    python3 todo.py --root . --summary          # the few lines the SessionStart hook shows
    python3 todo.py --root . --out <file>

THE THREADS ARE COMPUTED, NEVER DRAWN. Nobody -- no person, no agent -- proposes which pieces of
work go together: a script does, from the registers of the main line and the claims of the
threads already open, with fixed rules, so that two people reading the to-do on the same day
read the same threads. The one input a person writes is `affects`, the forecast of what an entry
or a change will touch, and `AFF001` keeps it honest.

THE NODES are the open entries of the open registers (not `parked`, and not closed as `View`
reads it: by a decision their `closed_by` names, or an accepted one deriving from them), one node
per `decide_with` group; the changes `approved`; and the increments of each
product's current stage with nothing under them yet -- no `requires`, no `changes`, no change
deriving from them -- which are to be decomposed. An increment is numbered per product, and is
`<product>/INC-NNN` here, as in its claim. A change in `draft` is not a node: it is listed to be
approved, at a join.

THE EDGES order and never join: an entry waits for what its `depends_on` names; a change for the
decisions and entries it derives from and for the entries its increments require; an increment
for the increments it depends on. A node is TO DO when everything it waits for is closed on the
main line; AFTER THE JOIN when what it waits for is closed on the branch of a thread that is
ready; AFTER THREAD X when it is closed on a thread open and not ready yet; WAITING otherwise,
and then it is only counted.

TWO NODES TO DO ARE IN ONE THREAD when they are one `decide_with` group, when they forecast one
anchor -- one `<path>#<anchor>`, or one document when either names it whole -- or when they are
changes whose mandates in the contribution policy overlap: code prefixes in one repository, or
the `documents` prefixes, which also meet a forecast on a document under them. A node that
declares no `affects` touches its whole product, whatever its mandate says. An entry of the root or
the platform register with `products: [all]`, or with no `products`, stays out of the threads
until it has anchors; one with `[none]` and no anchors is with the others `[none]`. A thread is a
connected component; it is named after its product and its lowest identifier -- OD, then KI, then
CHG, then INC, then the number.

A THREAD OPEN IS FIXED until the join that lands it: the nodes that would fall into its component
wait for it, "after thread X". It is ready when its elements are done on its remote branch --
an entry closed, a change `implemented`, an increment decomposed (a change deriving from it, or
an effect on its anchor); in a thread with a decision and a change, all but its changes, which go
back to the main line for the next round -- and the branch carries a commit of its own past the
main line.

Read only, and no network: the main line and the remote branches as this clone has them, after
whatever fetch was last made. Exit 0, or 2 when the repository does not allow it.
"""

from __future__ import annotations

import argparse
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
CLOSED_CHANGE = {"implemented", "verified", "rolled-back"}


def git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                       env=B.ENV)
    return r.stdout if r.returncode == 0 else ""


def bare(ident: str) -> str:
    """`INC-001` out of `c/INC-001`."""
    return ident.rsplit("/", 1)[-1]


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
        for a in arts:
            rel = a.rel.replace("\\", "/")
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
        product it decomposes, `<product>/INC-NNN`."""
        product = product_of_path(change.rel.replace("\\", "/")) or "radice"
        named = [str(x) for x in v.as_list(change.meta.get("derives_from"))]
        return ({x for x in named if not x.startswith("INC-")},
                {f"{product}/{x}" for x in named if x.startswith("INC-")})


class Node:
    def __init__(self, ids: list[str], kind: str, home: str, products: set[str],
                 anchors: set[str], declared: bool, preds: set[str], everywhere: bool):
        self.ids = sorted(ids, key=order)
        self.key = self.ids[0]
        self.kind = kind                  # "decision" or "work"
        self.home = home                  # the product the name carries: a product, radice, platform
        self.products = products
        self.anchors = anchors
        self.declared = declared          # it has `affects`, or is an increment with its anchor
        self.preds = preds - set(ids)
        self.everywhere = everywhere      # [all], or no products, and no anchors: out of the threads

    def as_dict(self, tree: Tree) -> dict:
        return {"ids": self.ids, "kind": self.kind,
                "titles": {i: tree.titles.get(i, "") for i in self.ids if tree.titles.get(i)}}


def nodes_of(tree: Tree, policy: dict) -> tuple[list[Node], list[str]]:
    """The nodes of the main line, and the changes in draft, to be approved."""
    out: list[Node] = []
    # Entries open, one node per `decide_with` group.
    open_entries = [k for k, row in tree.entries.items()
                    if row.get("status") == "open" and not tree.closed(k)]
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
    # the ones it derives from and, as the roadmaps written before 4.3.0 say it, the ones that
    # list it in `changes`.
    drafts = []
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
        for inc in incs | listing.get(ident, set()):
            waits |= {str(r) for r in v.as_list((tree.increments.get(inc) or {}).get("requires"))}
        declared = {str(x) for x in v.as_list(a.meta.get("affects"))}
        anchors = set(declared)
        mandate = (policy.get("mandates") or {}).get(rel) or {}
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
                if row.get("state") == "delivered" or v.as_list(row.get("requires")) \
                        or v.as_list(row.get("changes")) or f"{product}/{inc}" in decomposed:
                    continue
                out.append(Node([f"{product}/{inc}"], "work", product, {product},
                                {f"{rel}#{inc}"}, True,
                                {f"{product}/{x}" for x in v.as_list(row.get("depends_on"))},
                                False))
    return out, sorted(drafts, key=order)


def meet(a: set[str], b: set[str]) -> list[str]:
    """The anchors two forecasts share: one `<path>#<anchor>`; one document when either names
    it whole; a code prefix within another in one repository; a documents prefix with a
    document under it."""
    def doc(x: str) -> str | None:
        return x[4:] if x.startswith("doc:") else None
    out = []
    for x in a:
        for y in b:
            if x == y:
                out.append(x)
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
            elif "#" not in x and y.split("#", 1)[0] == x or "#" not in y and x.split("#", 1)[0] == y:
                out.append(x if "#" not in x else y)
    return sorted(set(out))


def threads_of(nodes: list[Node]) -> list[dict]:
    """The connected components of the nodes to do, with why each holds together."""
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
    for i, a in enumerate(nodes):
        for j in range(i + 1, len(nodes)):
            b = nodes[j]
            shared = meet(a.anchors, b.anchors)
            if shared:
                join(i, j, f"{bare(a.key)} and {bare(b.key)}: {', '.join(shared)}")
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
    try:
        policy = json.loads(git(root, "show", f"{base}:{B.prefix(root)}.framework/contribution-policy.json") or "{}")
    except ValueError:
        policy = {}
    main_tree = Tree(B.snapshot(root, base, registry, scan), registry)
    nodes, drafts = nodes_of(main_tree, policy)

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

        def done(i: str) -> bool:
            if tree is None:
                return False
            if bare(i).startswith("INC-"):
                decomposing = any(i in tree.derives(a)[1] for a in tree.changes.values())
                return decomposing or f"{main_tree.roadmap.get(i, '')}#{bare(i)}" in anchored
            return tree.closed(i)
        t["ready"] = own > 0 and all(done(i) for i in pending)
        t["effects"] = len(found)
        stamp = git(root, "log", "-1", "--format=%cI", t["ref"]).strip()
        t["age_days"] = (now - datetime.fromisoformat(stamp)).days if stamp else 0
    ready = sorted(n for n, t in open_threads.items() if t["ready"])

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
    states = {id(n): state(n) for n in nodes}
    todo = [n for n in nodes if states[id(n)][0] == "todo"]
    after_join = [n for n in nodes if states[id(n)][0] == "after-join"]
    after_thread = [{"node": n, "threads": states[id(n)][1]} for n in nodes
                    if states[id(n)][0] == "after-thread"]
    waiting: dict[str, int] = {}
    for n in nodes:
        if states[id(n)][0] == "waiting":
            waiting[n.home] = waiting.get(n.home, 0) + 1
    unanchored = [n for n in todo if n.everywhere]

    # The threads to take; what falls into the component of a thread open waits for it.
    claimed = {ident: name for name, t in open_threads.items() for ident, _ in t["claims"]}
    free = []
    for t in threads_of([n for n in todo if not n.everywhere]):
        holders = sorted({claimed[i] for n in t["nodes"] for i in n.ids if i in claimed})
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
            "ready": ready, "join": join, "tree": main_tree}


def describe(n: Node, tree: Tree) -> str:
    titles = "; ".join(f"{bare(i)} {tree.titles[i]}" if tree.titles.get(i) else
                       (f"{bare(i)} ({i.split('/')[0]})" if "/" in i else i) for i in n.ids)
    kind = ("decision" if n.kind == "decision" else
            "to decompose" if bare(n.key).startswith("INC-") else "work")
    return f"{kind}: {titles}"


def markdown(r: dict) -> str:
    if not r["additive"]:
        return f"The main line ({r['base']}) does not declare `mode: additive`: no to-do here.\n"
    tree = r["tree"]
    out = [f"# To do, from {r['base']}", ""]
    out.append(f"Join: **{r['join']}**" + (f" -- ready: {', '.join(r['ready'])}" if r["ready"] else ""))
    out.append("")
    if r["open"]:
        out.append("## Threads open")
        for name, t in sorted(r["open"].items()):
            who = sorted({w for _, w in t["claims"]})
            what = "parking" if t["parking"] else ", ".join(i for i, _ in t["claims"])
            out.append(f"- {name}: {what}; in the hands of {', '.join(who) or '-'}; "
                       f"{'ready' if t['ready'] else 'not ready'}; effects waiting: {t['effects']}")
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
    out.append("")
    if r["after_thread"]:
        out.append("## After a thread open")
        for item in r["after_thread"]:
            out.append(f"- {describe(item['node'], tree)} -- after {', '.join(item['threads'])}")
        out.append("")
    if r["after_join"]:
        out.append("## After the join")
        for n in r["after_join"]:
            out.append(f"- {describe(n, tree)}")
        out.append("")
    if r["drafts"]:
        out.append("## Changes to approve, at a join")
        out += [f"- {d} {tree.titles.get(d, '')}".rstrip() for d in r["drafts"]]
        out.append("")
    if r["unanchored"]:
        out.append("## For every product, with no anchors: out of the threads until anchored")
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
    if r["abandoned"]:
        out.append("## Branches without claims (abandoned)")
        out += [f"- {b}" for b in r["abandoned"]]
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def summary(r: dict) -> str:
    """The few lines the SessionStart hook puts in a session's context."""
    if not r["additive"]:
        return ""
    lines = [f"Additive mode, from {r['base']}. Join: {r['join']}."]
    for name, t in sorted(r["open"].items()):
        who = sorted({w for _, w in t["claims"]}) or ["-"]
        lines.append(f"- open: {name} ({', '.join(who)}){' ready' if t['ready'] else ''}")
    for t in r["threads"][:10]:
        lines.append(f"- to take: {t['name']} ({', '.join(i for n in t['nodes'] for i in n.ids)})")
    if len(r["threads"]) > 10:
        lines.append(f"- and {len(r['threads']) - 10} more threads to take")
    for path, targets in sorted(r["effects"].items()):
        lines.append(f"- effects waiting on {path}: {len(targets)}")
    lines.append("The whole to-do: python3 <framework>/skills/audit/scripts/todo.py --root <documentation>")
    return "\n".join(lines)[:4000] + "\n"


def as_json(r: dict) -> dict:
    if not r["additive"]:
        return {"additive": False, "base": r["base"]}
    tree = r["tree"]
    return {"additive": True, "base": r["base"], "join": r["join"], "ready": r["ready"],
            "threads": [{"name": t["name"], "why": t["why"], "mixed": t["mixed"],
                         "nodes": [n.as_dict(tree) for n in t["nodes"]]} for t in r["threads"]],
            "open": {k: {"claims": [i for i, _ in t["claims"]], "who": sorted({w for _, w in t["claims"]}),
                         "parking": t["parking"], "ready": t["ready"], "effects": t["effects"]}
                     for k, t in r["open"].items()},
            "after_thread": [{"ids": i["node"].ids, "threads": i["threads"]} for i in r["after_thread"]],
            "after_join": [n.ids for n in r["after_join"]], "waiting": r["waiting"],
            "drafts": r["drafts"], "unanchored": [n.ids for n in r["unanchored"]],
            "abandoned": r["abandoned"], "effects": r["effects"]}


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
