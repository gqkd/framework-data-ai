#!/usr/bin/env python3
"""Documentation written on branches: claim an element, reserve a number, see who works on
what, release a claim, and bring a branch up to date with the main line.

    python3 work.py --root . open --who "Name" --branch od-042 OD-042 [OD-017 ...]
    python3 work.py --root . reserve DEC --who "Name" [--count 2]
    python3 work.py --root . reserve RSK --product atlas --who "Name"   # or platform, repository
    python3 work.py --root . list [--json]
    python3 work.py --root . release OD-042 --who "Name"
    python3 work.py --root . sync [--continue] [--no-push]

ONE PIECE OF WORK, ONE BRANCH, ONE PULL REQUEST, for everybody who writes the documentation,
the person who owns it included. A session that already ran beside two others on one working
tree and one main line, and coordinated with them by hand, is the shape this replaces.

WHAT IS CENTRAL IS A TAG. A claim is `claim/<ID>` and a reservation is `id/<ID>` --
`claim/<product>/<ID>` and `id/<product>/<ID>` for the families the catalog numbers per
product -- annotated, pushed to the remote. Git refuses to replace a tag without force, and two
pushes that create one tag at the same moment are decided by the remote, so whoever pushes
second is told who pushed first. What it does not stop is somebody forcing a push or deleting
a tag by hand: this is the protection of people who use it, and the checks are what see the
rest. The tag object is unique -- who, when, for which branch -- so after a push whose answer
was lost, the remote holding that object is the proof the push went through. The branch is
created in the same atomic push as the claims, with a lease that requires it not to exist yet.
Reservations are never deleted, and a number reserved and not used stays burned; claims are
removed only by `release`, when a person says so.

THE BRANCH IS BROUGHT UP TO DATE BY MERGING THE MAIN LINE INTO IT, never by a rebase: a rebase
needs a forced push and rewrites the commits the exchange and the history name. Commits pushed to
the same work branch from another clone come in first: by a fast-forward when this clone has
nothing of its own, and the main line in the same run; by a merge otherwise, and the main line on
the next run. `sync` does each
merge and resolves exactly three things: a file the generator writes whole, taken from the side
merged in and regenerated; a conflict that lies entirely inside an attestation block, which keeps this
branch's and is reread after; and lines both sides only added at one place of a Markdown body,
all kept, this branch's first. Everything else stops it -- a conflict anywhere else, a file one
side deleted, a file that is not text, a conflict it cannot parse -- because it is content and is
a person's. Before merging it refuses a main line that created an identifier this branch created
too -- the main line, or the branch's own commits pushed from another clone: once both are in one
tree, YAML folds two rows of `entries:` into one without a word.

WHAT IT NEVER DOES. It never pushes the main line, never forces a push, never deletes a
reservation, never decides which of two texts holds, and never deduces who is working from
`git config`: `--who` is the person's name, as they give it.

Only in a project that declares `.framework/work.yaml`. Exit 0 when done, 1 when something is
for the person (claimed by somebody else, a conflict left, a collision), 2 when nothing was
done because the invocation or the repository does not allow it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate as v  # noqa: E402  (the validator's helpers, not its main)

B = v._branches
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# Git's own words are read below -- a refusal, a lease that failed -- so git speaks one language.
ENV = {**os.environ, "LC_ALL": "C", "LANG": "C", "GIT_TERMINAL_PROMPT": "0"}


class _Notes:
    """Findings `load_work` reports, printed: this command is not the validator."""

    def add(self, code: str, path: str, message: str) -> None:
        print(f"{code} {path}: {message}", file=sys.stderr)


def say(message: str) -> None:
    print(message)


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, env=ENV)
    if check and r.returncode:
        v.refuse(f"git {' '.join(args)}: {(r.stderr or r.stdout).strip()}")
    return r


REJECTED = ("[rejected]", "already exists", "[remote rejected]", "non-fast-forward",
            "fetch first", "stale info", "would clobber")


def network(root: Path, retries: int, pause: float, *args: str) -> subprocess.CompletedProcess:
    """A fetch or a push, tried again when the answer is lost and not when it is no.

    A server that drops a share of its connections is the ordinary case for at least one
    project, and a refusal is not a dropped connection: a push of a tag that exists already
    is the answer that matters most here, and trying it again would only repeat it.
    """
    r = None
    for attempt in range(max(1, retries)):
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                           env=ENV)
        if r.returncode == 0 or rejected(r):
            return r
        if attempt + 1 < retries:
            time.sleep(pause)
    return r


def rejected(r: subprocess.CompletedProcess) -> bool:
    out = (r.stderr or "") + (r.stdout or "")
    return r.returncode != 0 and any(s in out for s in REJECTED)


def stamp() -> str:
    now = datetime.now().astimezone().replace(second=0, microsecond=0)
    return f"{now:%Y-%m-%d %H:%M} {v._offset(now)}"


def message(who: str, branch: str, what: str) -> str:
    return f"{what}\n\nwho: {who}\nbranch: {branch}\nwhen: {stamp()}\n"


class Project:
    """The documentation, its remote and main line, and what it declares about branches."""

    def __init__(self, args):
        self.root = args.root.resolve()
        if not self.root.is_dir():
            v.refuse(f"{self.root}: no such directory. `--root` is the documentation.")
        if git(self.root, "rev-parse", "--show-prefix", check=False).returncode:
            v.refuse(f"{self.root} is not inside a git repository.")
        try:
            self.work = v.load_work(self.root, _Notes())
        except SystemExit as e:              # `load_work` stops the validator with exit 1
            v.refuse(str(e.code))
        if self.work is None:
            v.refuse(f"{self.root}: no {B.WORK}. Branches, claims and reservations are for a "
                     "project that says it works that way; write the file -- an empty "
                     f"mapping, or `people:` with the names of who writes -- and commit it.")
        self.remote, self.main = args.remote, args.main
        self.base = f"{self.remote}/{self.main}"
        self.retries, self.pause = args.retries, args.pause
        self.registry = v.yaml.safe_load(v.REGISTRY.read_text(encoding="utf-8"))
        self.scan = v.load_scan(self.registry, v.load_project(self.root))
        self.prefix = str(self.work.get("branch_prefix") or "work/")
        index = v.ReferenceIndex([], self.registry)
        self.id_form, self.local = index.id_re, index.local_prefixes
        self.owners: set[str] | None = None   # where per-product numbers can live, once read

    def net(self, *args: str) -> subprocess.CompletedProcess:
        return network(self.root, self.retries, self.pause, *args)

    def fetch(self, so_far: str = "") -> None:
        """The main line, the work branches, the claims and the reservations, as the remote has
        them now. Claims and reservations are fetched with force and pruned: a claim released
        and taken again is a tag that moved, which a plain fetch refuses to update, and a claim
        released is one this clone must not go on seeing."""
        r = self.net("fetch", "--prune", self.remote,
                     f"+refs/heads/*:refs/remotes/{self.remote}/*",
                     f"+{B.CLAIM_REF}*:{B.CLAIM_REF}*", f"+{B.RESERVED_REF}*:{B.RESERVED_REF}*")
        if r.returncode:
            v.refuse(f"could not fetch {self.remote} after {self.retries} attempts: "
                     f"{(r.stderr or '').strip()}. " + (so_far or "Nothing was done: a claim or a "
                     "number taken without seeing the remote is a guess."))
        if git(self.root, "rev-parse", "--verify", "-q", self.base, check=False).returncode:
            v.refuse(f"{self.base} does not exist after the fetch. `--remote` and `--main` "
                     "name the main line the branches land on.")

    def who(self, name: str | None) -> str:
        if not name or not name.strip():
            v.refuse("`--who` is required: the name of the person working, as they give it. "
                     "It is never read from git config.")
        people = self.work.get("people")
        names = set(map(str, people)) if isinstance(people, (dict, list)) else set()
        if names and name.strip() not in names:
            v.refuse(f"`--who {name}` is not among the people {B.WORK} names: "
                     f"{', '.join(sorted(names))}.")
        return name.strip()

    def view(self, ref: str | None) -> "B.View":
        """The documentation at `ref`, or as the working tree holds it when `ref` is None."""
        if ref is None:
            arts = v.discover(self.root, self.scan, self.registry, B._Sink())
        else:
            try:
                arts = B.snapshot(self.root, ref, self.registry, self.scan)
            except B.BranchError as e:
                v.refuse(f"{ref}: {e}")
        return B.View.of(arts, self.registry)

    def branch(self) -> str:
        return git(self.root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()

    def numbered(self, keys) -> set[tuple[str, str]]:
        return {k for k in keys if self.id_form.fullmatch(k[1])}

    def scope_of(self, owner: str) -> str:
        """`atlas`, `platform` or `repository` as the scope a tree files a number under. A
        product nobody declares is refused: a reservation under it is a number burned for
        nothing, and a claim under it can never match."""
        if self.owners is None:
            # The main line's products and this branch's: a product created on a branch has to
            # be able to reserve its first numbers, which `BR003` asks of it.
            self.owners = {"platform", "repository"}
            for view in (self.view(self.base), self.view(None)):
                self.owners |= set(v.ReferenceIndex(list(view.arts), self.registry).products)
        if owner not in self.owners:
            v.refuse(f"`{owner}` is not a product this repository declares, nor `platform` or "
                     f"`repository`: {', '.join(sorted(self.owners))}.")
        return owner if owner in ("platform", "repository") else f"product:{owner}"

    def element(self, written: str, known: bool = True) -> tuple[tuple[str, str], str]:
        """`OD-042` or `atlas:RSK-012` as the key a tree declares it under, and its tag name.
        `known=False` for a claim being released, whose product may since have gone."""
        owner, sep, ident = written.rpartition(":")
        if not self.id_form.fullmatch(ident):
            v.refuse(f"{written}: not an identifier of the framework.")
        if ident.split("-", 1)[0] in self.local:
            if not sep:
                v.refuse(f"{written} is numbered per product: write it `<product>:{ident}`, "
                         "or `platform:` / `repository:` where it is filed outside a product.")
            scope = self.scope_of(owner) if known else (
                owner if owner in ("platform", "repository") else f"product:{owner}")
            return (scope, ident), f"{owner}/{ident}"
        if sep:
            v.refuse(f"{written}: {ident} is one sequence across the repository; write it bare.")
        return ("*", ident), ident

    def tracking(self, ref: str) -> str:
        """Where a fetch puts the remote's `ref` in this clone."""
        if ref.startswith("refs/heads/"):
            return f"refs/remotes/{self.remote}/{ref[len('refs/heads/'):]}"
        return ref

    def push(self, refspecs: list[str], expect: dict[str, str | None],
             extra: tuple[str, ...] = ()) -> tuple[str, str]:
        """Push, and say what the remote holds afterwards, with git's last words: `ok`;
        `rejected`, refused and not there; `failed`, the remote asked and not holding all of it;
        `unknown`, the remote never answered and the push may have landed.

        `expect` is what the remote must hold for the push to have happened: each ref and the
        object it points at, or None for a ref deleted. After any failure the answer is asked
        of the remote, with `ls-remote`, rather than of the push -- and without fetching, which
        would prune the very tag this push is trying to deliver. A push that landed and whose
        answer was lost, tried again, is refused, and reading that refusal as "somebody else got
        there first" is what this exists to avoid; a push that never landed is tried again.
        """
        stderr, asked = "", False
        for attempt in range(max(1, self.retries)):
            r = subprocess.run(["git", "-C", str(self.root), "push", *extra, self.remote,
                                *refspecs], capture_output=True, text=True, env=ENV)
            stderr = (r.stderr or r.stdout or "").strip()
            if r.returncode == 0:
                return "ok", stderr
            ask = subprocess.run(["git", "-C", str(self.root), "ls-remote", self.remote, *expect],
                                 capture_output=True, text=True, env=ENV)
            asked = ask.returncode == 0
            if asked:
                held = {name: sha for sha, _, name in
                        (line.partition("\t") for line in ask.stdout.splitlines())
                        if not name.endswith("^{}")}
                if all(held.get(ref) == sha for ref, sha in expect.items()):
                    return "ok", stderr
                if rejected(r):
                    return "rejected", stderr
            if attempt + 1 < self.retries:
                time.sleep(self.pause)
        # `failed`: the remote was asked and does not hold all of it. `unknown`: it never
        # answered, and the push may have landed -- which is a different thing to tell a person.
        return ("failed" if asked else "unknown"), stderr


    def held(self, namespace: str) -> dict[str, dict]:
        """The tags of one namespace as the last fetch brought them, each with its message."""
        r = git(self.root, "for-each-ref", "--format=%(refname)%00%(objectname)%00%(contents)%00%00",
                namespace.rstrip("/"))
        out = {}
        for record in r.stdout.split("\x00\x00"):
            record = record.strip("\n")
            if not record:
                continue
            name, _, rest = record.partition("\x00")
            sha, _, body = rest.partition("\x00")
            out[name[len(namespace):]] = {"object": sha, **B.message_fields(body)}
        return out

    def worktree_for(self, slug: str) -> Path:
        """Beside the main checkout, so that every path the project writes relative to its
        root -- the exchange at `../_scambio`, the framework beside it -- means the same thing
        from the worktree. Never inside the repository."""
        common = git(self.root, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
        main_checkout = Path(common).parent
        return main_checkout.parent / f"{main_checkout.name}--{slug}"


def remote_work_branches(p: Project) -> dict[str, str]:
    """The work branches on the remote: remote-tracking ref -> branch name."""
    out = {}
    rows = git(p.root, "for-each-ref", "--format=%(refname)",
               f"refs/remotes/{p.remote}/{p.prefix.rstrip('/')}").stdout.split()
    for ref in rows:
        out[ref] = ref[len(f"refs/remotes/{p.remote}/"):]
    return out


# ─────────────────────────────────────────────────────────────────────────────

def cmd_open(p: Project, args) -> int:
    who = p.who(args.who)
    if not SLUG.match(args.branch):
        v.refuse(f"`--branch {args.branch}`: lower case letters, digits and dashes.")
    branch = p.prefix + args.branch
    p.fetch()
    main = p.view(p.base)
    wanted = [p.element(w) for w in dict.fromkeys(args.ids)]
    for key, tag in wanted:
        if key not in main.ids():
            v.refuse(f"{tag} is not declared on {p.base}. A claim is on an element that "
                     "exists; a new number is reserved with `reserve`, not claimed.")
        ident = key[1]
        if ident in main.entries and main.closed(ident):
            closers = ", ".join(sorted(main.closers(ident))) or main.entries[ident].get("status")
            v.refuse(f"{ident} is already closed on {p.base} ({closers}). Reopening it is a new "
                     "entry, or a decision that `supersedes` the one that closed it.")
    if git(p.root, "rev-parse", "--verify", "-q", f"refs/remotes/{p.remote}/{branch}",
           check=False).returncode == 0:
        v.refuse(f"{branch} exists on {p.remote} already. Choose another `--branch`.")

    claims = p.held(B.CLAIM_REF)
    taken = [tag for _, tag in wanted if tag in claims]
    if taken:
        for tag in taken:
            c = claims[tag]
            say(f"{tag} is claimed by {c.get('who', '?')} on {c.get('branch', '?')} since "
                f"{c.get('when', '?')}.")
        say("Nothing was claimed. Work with them on their branch, wait for it to land, or "
            "release the claim with them if it is abandoned: `release`.")
        return 1

    # The entries decided in one sitting with these, and what another branch is already
    # changing without a claim. Told, not refused: the person decides what to do with it.
    idents = [k[1] for k, _ in wanted]
    for ident in idents:
        for other in v.as_list(main.entries.get(ident, {}).get("decide_with")):
            if isinstance(other, str) and other not in idents:
                note = f", claimed by {claims[other].get('who')}" if other in claims else ""
                say(f"note: {ident} is decided together with {other}{note}. Claim both in one "
                    "`open`, or agree with whoever holds it.")
    for name, work_branch in remote_work_branches(p).items():
        changed = B.touched(p.view(name), p.view(B.merge_base(p.root, p.base, name)))
        for ident, what in changed.items():
            if ident in idents:
                say(f"note: {work_branch} changes {ident} ({'; '.join(what)}) without a claim.")

    mine = {}
    for key, tag in wanted:
        git(p.root, "tag", "-a", f"claim/{tag}", "-m", message(who, branch, f"claim {tag}"), p.base)
        mine[tag] = git(p.root, "rev-parse", f"{B.CLAIM_REF}{tag}").stdout.strip()
    git(p.root, "branch", "--no-track", branch, p.base)

    def undo() -> None:
        for tag in mine:
            git(p.root, "tag", "-d", f"claim/{tag}", check=False)
        git(p.root, "branch", "-D", branch, check=False)

    # One atomic push: the branch, with a lease that says it must not exist yet -- two `open`s
    # naming one branch would otherwise both succeed, the second as "up to date" -- and every
    # claim, created without force.
    refspecs = [f"refs/heads/{branch}:refs/heads/{branch}"] + \
               [f"{B.CLAIM_REF}{t}:{B.CLAIM_REF}{t}" for t in mine]
    head = git(p.root, "rev-parse", branch).stdout.strip()
    expect = {f"refs/heads/{branch}": head, **{f"{B.CLAIM_REF}{t}": sha for t, sha in mine.items()}}
    outcome, said = p.push(refspecs, expect,
                           ("--atomic", f"--force-with-lease=refs/heads/{branch}:"))
    if outcome == "unknown":
        path = p.worktree_for(args.branch)
        there = (f"make the worktree: `git worktree add {path} {branch}` and "
                 f"`git -C {path} branch --set-upstream-to {p.remote}/{branch}`"
                 if not args.no_worktree else
                 f"set the upstream: `git branch --set-upstream-to {p.remote}/{branch} {branch}`")
        v.refuse(f"the push may or may not have landed: the remote did not answer ({said}). The "
                 f"local branch is kept. Once it answers, run `list`, which also drops the local "
                 f"claims the remote does not hold. If {branch} is on {p.remote}, {there}. If it "
                 f"is not, remove the local branch -- `git branch -D {branch}` -- and `open` again.")
    if outcome != "ok":
        undo()
        if outcome == "failed":
            v.refuse(f"the push did not go through ({said}), and the remote holds none of it: "
                     "nothing is claimed, and the local tags and branch were removed.")
        p.fetch()
        there = p.held(B.CLAIM_REF)
        taken = [t for t in mine if t in there]
        branch_taken = git(p.root, "rev-parse", "--verify", "-q",
                           f"refs/remotes/{p.remote}/{branch}", check=False).returncode == 0
        if not taken and not branch_taken:
            v.refuse(f"the remote refused the push and holds none of it: a hook, a protection or "
                     f"a permission, not somebody else's claim. Git said: {said}")
        say("Somebody pushed first, between the check and the push:")
        for tag in taken:
            c = there[tag]
            say(f"  {tag}: {c.get('who', '?')} on {c.get('branch', '?')} since {c.get('when', '?')}")
        if branch_taken:
            say(f"  {branch} exists on {p.remote}: choose another `--branch`.")
        return 1

    path = p.worktree_for(args.branch)
    if not args.no_worktree:
        if path.exists():
            v.refuse(f"{path} exists. The claim and the branch are on {p.remote}; make the "
                     f"worktree yourself: git worktree add <path> {branch}")
        git(p.root, "worktree", "add", str(path), branch)
        git(path, "branch", "--set-upstream-to", f"{p.remote}/{branch}", branch)
    where = B.prefix(p.root)
    say(f"Claimed: {', '.join(mine) or 'nothing (a piece of work without an element)'}.")
    say(f"Branch: {branch}, from {p.base}, on {p.remote}.")
    if not args.no_worktree:
        say(f"Worktree: {path / where if where else path}. Open the session there: the main "
            "checkout stays on the main line, and nothing is written in it.")
    say("Reserve every new number from the branch before writing it: work.py reserve <PREFIX>")
    return 0


def cmd_reserve(p: Project, args) -> int:
    who = p.who(args.who)
    prefix = args.prefix
    if prefix not in p.registry["id_prefixes"]:
        v.refuse(f"{prefix} is not an identifier family of the framework: "
                 f"{', '.join(p.registry['id_prefixes'])}.")
    local = prefix in p.local
    if local and not args.product:
        v.refuse(f"{prefix} is numbered per product: say which, with `--product` -- a product, "
                 "or `platform` / `repository` where it is filed outside one.")
    if not local and args.product:
        v.refuse(f"{prefix} is one sequence across the repository: no `--product`.")
    if args.count < 1:
        v.refuse("`--count` is at least 1.")
    branch = p.branch()
    if not branch.startswith(p.prefix):
        v.refuse(f"on {branch}, not on a work branch. A number is reserved for the branch that "
                 "will write it, and the validator asks the reservation to name that branch.")
    p.fetch()
    if local:
        p.scope_of(args.product)
    form = re.compile(rf"^(?:.*/)?{re.escape(prefix)}-(\d{{3,}})$")
    seen: list[str] = []
    # One number for the whole repository, even for a family numbered per product: unique
    # across products is unique within each, and serves a project that numbers it globally.
    for view in (p.view(p.base), p.view(None)):
        seen += [m.group(1) for m in (form.match(i) for _, i in p.numbered(view.ids())) if m]
    seen += [m.group(1) for m in (form.match(t) for t in p.held(B.RESERVED_REF)) if m]
    n = max((int(s) for s in seen), default=0) + 1
    width = max([3] + [len(s) for s in seen])
    got, tries = [], 0
    while len(got) < args.count:
        tries += 1
        if tries > args.count + 50:
            v.refuse(f"fifty numbers of {prefix} in a row were taken while trying. Something "
                     "else is reserving in a loop; nothing more was reserved.")
        ident = f"{prefix}-{n:0{width}d}"
        tag = f"{args.product}/{ident}" if local else ident
        ref = f"{B.RESERVED_REF}{tag}"
        git(p.root, "tag", "-a", f"id/{tag}", "-m", message(who, branch, f"reserve {tag}"), p.base)
        mine = git(p.root, "rev-parse", ref).stdout.strip()
        outcome, said = p.push([f"{ref}:{ref}"], {ref: mine})
        so_far = f"Reserved so far: {', '.join(got) or 'none'}."
        if outcome == "unknown":
            v.refuse(f"the push of {tag} may or may not have landed: the remote did not answer "
                     f"({said}). The local tag is kept; `list` says whether it is there. {so_far}")
        if outcome == "failed":
            git(p.root, "tag", "-d", f"id/{tag}", check=False)
            v.refuse(f"the push of {tag} did not go through ({said}), and the remote does not "
                     f"hold it. {so_far}")
        if outcome == "rejected":
            git(p.root, "tag", "-d", f"id/{tag}", check=False)
            p.fetch(so_far)
            held = p.held(B.RESERVED_REF).get(tag)
            if held is None:
                v.refuse(f"the remote refused {ref} and does not hold it: a hook, a protection or "
                         f"a permission, not another reservation. Reserved so far: "
                         f"{', '.join(got) or 'none'}.")
            n += 1                       # somebody took it a moment ago: the next one
            continue
        got.append(ident if not local else f"{args.product}:{ident}")
        n += 1
    say(f"Reserved: {', '.join(got)}. They are yours on {branch}; a number reserved and not "
        "used stays burned, and is never reserved again.")
    return 0


def cmd_list(p: Project, args) -> int:
    p.fetch()
    claims = p.held(B.CLAIM_REF)
    reserved = p.held(B.RESERVED_REF)
    now = datetime.now().astimezone()
    rows = []
    for ref, branch in sorted(remote_work_branches(p).items(), key=lambda kv: kv[1]):
        last = git(p.root, "log", "-1", "--format=%an%x00%aI", ref).stdout.strip().split("\x00")
        behind, ahead = git(p.root, "rev-list", "--left-right", "--count",
                            f"{p.base}...{ref}").stdout.split()
        start = B.merge_base(p.root, p.base, ref)
        touched = B.touched(p.view(ref), p.view(start))
        when = datetime.fromisoformat(last[1]) if len(last) > 1 else None
        rows.append({
            "branch": branch, "last_author": last[0], "last_commit": last[1] if when else None,
            "stale": bool(when and now - when > timedelta(days=args.stale_days)),
            "ahead": int(ahead), "behind": int(behind),
            "claims": sorted(t for t, c in claims.items() if c.get("branch") == branch),
            "reserved": sorted(t for t, c in reserved.items() if c.get("branch") == branch),
            "touches": {k: w for k, w in sorted(touched.items())},
        })
    branches = {r["branch"] for r in rows}
    orphans = {t: c for t, c in sorted(claims.items()) if c.get("branch") not in branches}
    if args.json:
        print(json.dumps({"base": p.base, "branches": rows, "claims_without_branch": orphans},
                         indent=2, ensure_ascii=False))
        return 0
    if not rows:
        say(f"No work branch on {p.remote} under {p.prefix}.")
    for r in rows:
        flag = "  STALE" if r["stale"] else ""
        say(f"{r['branch']}: {r['ahead']} ahead, {r['behind']} behind {p.base}; last commit by "
            f"{r['last_author']} {r['last_commit'] or ''}{flag}")
        if r["claims"]:
            say(f"  claims: {', '.join(r['claims'])}")
        if r["reserved"]:
            say(f"  reserved: {', '.join(r['reserved'])}")
        for ident, what in r["touches"].items():
            mark = "" if ident in r["claims"] else "  (not claimed)"
            say(f"  changes {ident}: {'; '.join(what)}{mark}")
    for tag, c in orphans.items():
        say(f"claim without a branch: {tag} by {c.get('who', '?')} for {c.get('branch', '?')} "
            f"since {c.get('when', '?')}. Landed or abandoned: `release` it once its person agrees.")
    return 0


def cmd_release(p: Project, args) -> int:
    who = p.who(args.who)
    p.fetch()
    claims = p.held(B.CLAIM_REF)
    tags = [p.element(w, known=False)[1] for w in args.ids]
    for tag in tags:
        if tag not in claims:
            v.refuse(f"{tag} has no claim on {p.remote}.")
        holder = claims[tag].get("who")
        if holder != who and not args.theirs:
            v.refuse(f"{tag} is claimed by {holder}, not by {who}. Releasing somebody else's "
                     "claim removes the one thing that tells others it is taken: do it only "
                     "with them, and say so with `--theirs`.")
    outcome, said = p.push([f":{B.CLAIM_REF}{t}" for t in tags],
                           {f"{B.CLAIM_REF}{t}": None for t in tags}, ("--atomic",))
    if outcome != "ok":
        v.refuse(f"the release {'may not have gone' if outcome == 'unknown' else 'did not go'} "
                 f"through ({said}): run `list` to see what the remote holds.")
    for tag in tags:
        git(p.root, "tag", "-d", f"claim/{tag}", check=False)
    say(f"Released: {', '.join(tags)}. Reservations are never released.")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# sync

OURS, BASE, THEIRS, END = "<<<<<<< ", "||||||| ", "=======", ">>>>>>> "


class Unreadable(ValueError):
    """A conflict whose markers do not close, or have no common ancestor: not for a script."""


def _hunks(text: str) -> list:
    """The lines of a file in conflict, as plain lines and diff3 hunks (ours, base, theirs)."""
    out, cur, part = [], None, None
    for line in text.split("\n"):
        if cur is None and line.startswith(OURS):
            cur, part = {"ours": [], "base": [], "theirs": [], "open": line}, "ours"
        elif cur is not None and part == "ours" and line.startswith(BASE):
            part, cur["base_mark"] = "base", line
        elif cur is not None and part in ("ours", "base") and line == THEIRS:
            if "base_mark" not in cur:
                raise Unreadable("a conflict without its common ancestor")
            part = "theirs"
        elif cur is not None and part == "theirs" and line.startswith(END):
            cur["close"] = line
            out.append(cur)
            cur = part = None
        elif cur is not None:
            cur[part].append(line)
        else:
            out.append(line)
    if cur is not None:
        raise Unreadable("a conflict whose markers do not close")
    return out


def _attestation_part(lines: list[str]) -> bool:
    """Lines that are an attestation block and nothing else, by the validator's own reading of
    where the block ends: an indented line under `last_review`, or under a `review_scope` with
    a plain value, is a comment and is text."""
    inside = {i for a, b in v.attestation_spans(lines, 0, len(lines)) for i in range(a, b)}
    return all(i in inside or not line.strip() for i, line in enumerate(lines))


def resolve(text: str, rel: str) -> tuple[str, int, list[str]]:
    """Resolve the hunks of one file that are mechanical. Returns the text, how many hunks
    are left for a person, and one line per hunk saying what was done with it. Raises
    `Unreadable` for markers it cannot parse, and the file is then left whole for a person."""
    parts = _hunks(text)
    ours = "\n".join(l for p in parts for l in ([p] if isinstance(p, str) else p["ours"]))
    lo, hi = v._front_matter_lines(ours)
    names = v.GENERATED_REGIONS.get(rel, (None, ()))[1]
    regions = [(ours[:m.start()].count("\n"), ours[:m.end()].count("\n"))
               for m in v.REGION.finditer(ours) if m.group("name") in names]
    out, left, done, at = [], 0, [], 0
    for p in parts:
        if isinstance(p, str):
            out.append(p)
            at += 1
            continue
        start = at
        inside_fm = lo <= start < hi
        if inside_fm and all(_attestation_part(p[k]) for k in ("ours", "base", "theirs")):
            chosen, why = p["ours"], "attestation block: this branch's, to be reread after the merge"
        elif any(a < start < b for a, b in regions):
            chosen, why = p["theirs"], "generated region: the side merged in, regenerated after"
        elif (rel.endswith(".md") and start >= hi and not p["base"]
              and p["ours"] and p["theirs"]):
            # Every line of both, and no line dropped because it looks like one of the other's:
            # a repeated table header or field label is not a duplicate of the entry it heads.
            chosen = p["ours"] + p["theirs"]
            why = "lines both sides added at one place of the body: all kept, this branch's first"
        else:
            out += [p["open"], *p["ours"], p["base_mark"], *p["base"], THEIRS, *p["theirs"],
                    p["close"]]
            left += 1
            at += len(p["ours"])
            done.append(f"line {start + 1}: content, left for a person")
            continue
        out += chosen
        at += len(p["ours"])
        done.append(f"line {start + 1}: {why}")
    return "\n".join(out), left, done


def _markers(top: Path, paths: list[str]) -> list[str]:
    """The staged files that still carry the opening or closing marker of a conflict."""
    out = []
    for path in paths:
        full = top / path
        try:
            text = full.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        if any(l.startswith((OURS, END)) for l in text.split("\n")):
            out.append(path)
    return out


def _collisions(p: Project, mine: str, theirs: str) -> list[str]:
    """Identifiers both sides created since they parted, as `scope:ID` where the scope matters.
    Against every common ancestor: two clones that both merged the main line share two."""
    try:
        start = B.shared(p.root, mine, theirs, p.registry, p.scan)
    except B.BranchError as e:
        v.refuse(f"the common history of {mine} and {theirs} could not be read: {e}")
    both = p.numbered((p.view(mine).ids() - start) & (p.view(theirs).ids() - start))
    return sorted(i if s == "*" else f"{s.removeprefix('product:')}:{i}" for s, i in both)


def cmd_sync(p: Project, args) -> int:
    branch = p.branch()
    if not branch.startswith(p.prefix):
        v.refuse(f"on {branch}, not on a work branch ({p.prefix}...). `sync` brings a work "
                 "branch up to date; the main line is never written here.")
    top = Path(git(p.root, "rev-parse", "--show-toplevel").stdout.strip())
    where = B.prefix(p.root)
    target = Path(git(p.root, "rev-parse", "--path-format=absolute", "--git-path",
                      "framework-data-ai-sync").stdout.strip())
    merging = git(p.root, "rev-parse", "--verify", "-q", "MERGE_HEAD", check=False).returncode == 0
    if args.cont and not merging:
        v.refuse("`--continue` with no merge in progress.")
    left_files: list[str] = []
    if not args.cont:
        if merging:
            v.refuse("a merge is in progress. Finish it -- resolve, `git add` -- and run "
                     "`sync --continue`, or abandon it with `git merge --abort`.")
        if git(p.root, "status", "--porcelain", "--untracked-files=no").stdout.strip():
            v.refuse("the working tree has uncommitted changes. Commit them first: the merge "
                     "is a commit of its own, and nothing of yours should be inside it.")
        p.fetch()
        # Commits pushed to this same branch from another clone come in first: by fast-forward,
        # and then the main line in the same run; or by a merge with the same resolution, and
        # then the main line on the next run.
        own = f"{p.remote}/{branch}"
        if git(p.root, "rev-parse", "--verify", "-q", f"refs/remotes/{own}", check=False).returncode == 0 \
                and git(p.root, "merge-base", "--is-ancestor", own, "HEAD", check=False).returncode:
            if git(p.root, "merge-base", "--is-ancestor", "HEAD", own, check=False).returncode == 0:
                # Nothing here that the remote branch lacks: move to it, with no merge commit --
                # two clones taking turns would otherwise add an empty merge each, for ever.
                git(p.root, "merge", "--ff-only", "-q", own)
                say(f"{own} had commits pushed from elsewhere: {branch} moved forward to them.")
            else:
                into = own
                say(f"{own} has commits this clone does not, pushed from elsewhere: they come "
                    "in first.")
        if git(p.root, "merge-base", "--is-ancestor", own, "HEAD", check=False).returncode == 0 \
                or git(p.root, "rev-parse", "--verify", "-q", f"refs/remotes/{own}",
                       check=False).returncode:
            into = p.base
            if git(p.root, "merge-base", "--is-ancestor", p.base, "HEAD", check=False).returncode == 0:
                say(f"{branch} already contains {p.base}.")
                return 0
        both = _collisions(p, "HEAD", into)
        if both:
            say(f"Not merged: this branch and {into} both created {', '.join(both)}. Once both "
                "are in one tree, two rows of `entries:` become one without a word and two files "
                "carry one name. Renumber the ones this branch created -- reserve new numbers "
                "first -- commit, and run `sync` again.")
            return 1
        # What this merge brings in, recorded where only this worktree reads it: `--continue`
        # finishes this merge and no other, and another session's fetch moving `origin/main`
        # meanwhile does not make it somebody else's.
        target.write_text(git(p.root, "rev-parse", into).stdout.strip() + "\n" + into + "\n")
        r = git(p.root, "-c", "merge.conflictStyle=diff3", "-c", "rerere.enabled=false",
                "merge", "--no-ff", "--no-commit", into, check=False)
        unmerged = git(top, "ls-files", "-u", "-z").stdout
        if r.returncode and not unmerged:
            git(p.root, "merge", "--abort", check=False)
            target.unlink(missing_ok=True)
            v.refuse(f"the merge stopped: {(r.stderr or r.stdout).strip()}")

        stages: dict[str, set[str]] = {}
        for row in filter(None, unmerged.split("\0")):
            meta, _, path = row.partition("\t")
            stages.setdefault(path, set()).add(meta.split()[2])
        arts = v.discover(p.root, p.scan, p.registry, B._Sink())
        generated = {str(x.relative_to(p.root)).replace("\\", "/")
                     for x in v.build_indices(p.root, arts)}
        for path, have in sorted(stages.items()):
            if where and not path.startswith(where):
                left_files.append(f"{path} (from the repository's top)")
                say(f"{path}: outside the documentation, left for a person.")
                continue
            rel = path[len(where):] if where else path
            full = top / path
            if not {"2", "3"} <= have:
                gone = "the side merged in" if "3" not in have else "this branch"
                left_files.append(rel)
                say(f"{rel}: deleted on {gone} and changed on the other side, left for a person.")
                continue
            ours = git(p.root, "show", f":2:{path}", check=False).stdout
            theirs = git(p.root, "show", f":3:{path}", check=False).stdout
            if rel in generated and v.GENERATED_MARK in ours and v.GENERATED_MARK in theirs:
                git(top, "checkout", "--theirs", "--", path)
                git(top, "add", "--", path)
                say(f"{rel}: written whole by the generator; taken from the side merged in, "
                    "regenerated below.")
                continue
            if "1" not in have:
                left_files.append(rel)
                say(f"{rel}: created on both sides with different content, left for a person.")
                continue
            try:
                raw = full.read_bytes().decode("utf-8")
                crlf = "\r\n" in raw           # any CRLF and the file is written back CRLF throughout
                text = raw.replace("\r\n", "\n")
                if not any(l.startswith(OURS) for l in text.split("\n")):
                    # Unmerged and no markers: a file git would not merge line by line (`-merge`,
                    # `binary`), a change of mode, markers of another size. Never this branch's
                    # by default.
                    raise Unreadable("in conflict and without markers")
                resolved, left, done = resolve(text, rel)
            except UnicodeDecodeError:
                left_files.append(rel)
                say(f"{rel}: not text, left for a person.")
                continue
            except Unreadable as e:
                left_files.append(rel)
                say(f"{rel}: {e}, left whole for a person.")
                continue
            # The line endings the file had: a working tree on Windows keeps CRLF.
            full.write_bytes((resolved.replace("\n", "\r\n") if crlf else resolved).encode("utf-8"))
            for line in done:
                say(f"{rel}, {line}")
            if left:
                left_files.append(rel)
            else:
                git(top, "add", "--", path)
    else:
        # Only the merge `sync` started, with the refusal of a shared number.
        incoming = git(p.root, "rev-parse", "MERGE_HEAD").stdout.strip()
        recorded = target.read_text().split() if target.exists() else []
        began, into = (recorded + ["", ""])[:2]
        into = into or p.base                # a record written before the ref was kept
        if incoming != began:
            v.refuse(f"the merge in progress is not the one `sync` began (of {into}). "
                     "`--continue` finishes that merge and no other; finish or abort this one "
                     "with git.")
        both = _collisions(p, "HEAD", "MERGE_HEAD")
        if both:
            v.refuse(f"this branch and {into} both created {', '.join(both)}: abort the merge "
                     "(`git merge --abort`), renumber, and run `sync` again.")
        unmerged = git(top, "ls-files", "-u").stdout.strip()
        if unmerged:
            v.refuse("files are still unmerged: resolve them and `git add` each, then run "
                     "`sync --continue` again.")
        staged = git(p.root, "diff", "--cached", "--name-only").stdout.split("\n")
        marked = _markers(top, [s for s in staged if s])
        if marked:
            v.refuse(f"conflict markers are still in {', '.join(marked)}. A file staged with them "
                     "would be committed with them.")

    if left_files:
        say(f"\nLeft for a person: {', '.join(left_files)}. The markers are in the files, with "
            "this branch's text, the common ancestor's and the side merged in. Which one holds is "
            "a decision when the text is a decision's, and is put to whoever decides that "
            "matter. Then `git add` the files and run `work.py sync --continue`.")
        return 1

    # Regenerated from the merged tree, which is what each of them derives from.
    r = subprocess.run([sys.executable, str(Path(v.__file__)), "--root", str(p.root),
                        "--emit-index", "--json", "--stale-days", "36500"],
                       capture_output=True, text=True)
    try:
        written = json.loads(r.stdout).get("generated", []) if r.returncode in (0, 1) else None
    except json.JSONDecodeError:
        written = None
    if written is None:
        v.refuse(f"the views could not be regenerated (exit {r.returncode}): "
                 f"{(r.stderr or '').strip()[-300:]}. The merge is resolved and not committed: "
                 "repair what stops the validator, then `sync --continue`.")
    for rel in written:
        git(p.root, "add", "--", rel)
    incoming = git(p.root, "rev-parse", "MERGE_HEAD").stdout.strip()
    into = (target.read_text().split() + ["", ""])[1] if target.exists() else p.base
    into = into or p.base
    git(p.root, "commit", "-q", "-m", f"Merge {into} ({incoming[:12]}) into {branch}")
    target.unlink(missing_ok=True)
    merge = git(p.root, "rev-parse", "HEAD").stdout.strip()
    say(f"Merged {into} at {incoming[:12]} into {branch}."
        + (f" Regenerated: {', '.join(written)}." if written else ""))
    if git(p.root, "merge-base", "--is-ancestor", p.base, "HEAD", check=False).returncode != 0:
        say(f"{p.base} is not in {branch} yet" + (" -- this run merged the branch's own commits"
            if into != p.base else ", having moved while this merge was resolved")
            + ": `sync` again.")

    # What the merge produced that nobody has read, as `LC006` sees it: the regenerated union
    # is not among them, because no reading vouches for it.
    r = subprocess.run([sys.executable, str(Path(v.__file__)), "--root", str(p.root), "--json",
                        "--stale-days", "36500"], capture_output=True, text=True)
    try:
        found = json.loads(r.stdout).get("findings", []) if r.stdout.strip() else None
    except json.JSONDecodeError:
        found = None
    if found is None:
        say("The validator gave no report after the merge, so which documents owe a reading is "
            "not known: run it, and reread what `LC006` names.")
        found = []
    owed = sorted({f["path"] for f in found if f["code"] == "LC006" and merge[:12] in f["message"]})
    if owed:
        say("The merge produced a version of these living documents that neither side had, "
            "and a merge records no reading: reread each, attest it with attest.py, and commit "
            f"the attestations on their own: {', '.join(owed)}.")
    if not args.no_push:
        outcome, said = p.push([f"refs/heads/{branch}:refs/heads/{branch}"],
                               {f"refs/heads/{branch}": merge})
        if outcome == "rejected" and "[remote rejected]" in said:
            say(f"The merge is committed and the remote refused it ({said}): a hook or a "
                "protection rule, which is the person's to look at. Never --force.")
            return 1
        if outcome == "rejected":
            say(f"The merge is committed and the remote refused it: {branch} there has commits "
                f"pushed from elsewhere ({said}). Run `sync` again: it fetches them and brings "
                "them in first, the same way. Never --force.")
            return 1
        if outcome != "ok":
            say(f"The merge is committed, and {'it may not have been' if outcome == 'unknown' else 'it was not'} "
                f"pushed ({said}). Push it when the remote answers; never with --force.")
            return 1
    return 0


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description="Documentation written on branches")
    ap.add_argument("--root", default=".", type=Path, help="the documentation repository")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--main", default="main", help="the main line the branches land on")
    ap.add_argument("--retries", type=int, default=5,
                    help="attempts for a fetch or push whose answer is lost (not refused)")
    ap.add_argument("--pause", type=float, default=20.0, help="seconds between attempts")
    sub = ap.add_subparsers(dest="command", required=True)

    o = sub.add_parser("open", help="claim elements and open a branch and a worktree for them")
    o.add_argument("ids", nargs="*", help="the elements this work decides or closes: OD-042, "
                                          "or atlas:RSK-012 for a family numbered per product")
    o.add_argument("--who", required=True)
    o.add_argument("--branch", required=True, help="the name after the prefix: od-042")
    o.add_argument("--no-worktree", action="store_true")

    r = sub.add_parser("reserve", help="reserve the next numbers of an identifier family")
    r.add_argument("prefix")
    r.add_argument("--who", required=True)
    r.add_argument("--count", type=int, default=1)
    r.add_argument("--product", help="for a family numbered per product (RSK, INC, SIG, ANA): "
                                      "the product, or `platform` / `repository` where the "
                                      "register is filed outside one")

    ls = sub.add_parser("list", help="the work branches, their claims and what they change")
    ls.add_argument("--json", action="store_true")
    ls.add_argument("--stale-days", type=int, default=7)

    rl = sub.add_parser("release", help="remove claims, never reservations")
    rl.add_argument("ids", nargs="+")
    rl.add_argument("--who", required=True)
    rl.add_argument("--theirs", action="store_true",
                    help="release a claim somebody else made, with them")

    s = sub.add_parser("sync", help="bring this work branch up to date: its own remote commits, "
                                     "then the main line")
    s.add_argument("--continue", dest="cont", action="store_true")
    s.add_argument("--no-push", action="store_true")

    args = ap.parse_args()
    p = Project(args)
    return {"open": cmd_open, "reserve": cmd_reserve, "list": cmd_list,
            "release": cmd_release, "sync": cmd_sync}[args.command](p, args)


if __name__ == "__main__":
    sys.exit(main())
