#!/usr/bin/env python3
"""Documentation written on branches: claim an element, reserve a number, see who works on
what, release a claim, and bring a branch up to date with the main line.

    python3 work.py --root . open --who "Name" --branch od-042 OD-042 [OD-017 ...]
    python3 work.py --root . reserve DEC --who "Name" [--count 2]
    python3 work.py --root . reserve RSK --product atlas --who "Name"   # or platform, repository
    python3 work.py --root . list [--json]
    python3 work.py --root . release OD-042 --who "Name"
    python3 work.py --root . sync [--continue] [--no-push]
    python3 work.py --root . delegate --to "Name" --who "Admin"
    python3 work.py --root . revoke --to "Name" --who "Admin"         # or the delegate, for their own
    python3 work.py --root . open --thread beta-od-042 --who "Name"   # the additive mode
    python3 work.py --root . join --who "Admin" [THREAD ...] [--no-threads]
    python3 work.py --root . join --finish --who "Admin"
    python3 work.py --root . join --merge --who "Admin"               # or --close, --abandon
    python3 work.py --root . doctor [--who "Name"]                    # read only: this machine

ONE PIECE OF WORK, ONE BRANCH, ONE PULL REQUEST, for everybody who writes the documentation,
the person who owns it included. A session that already ran beside two others on one working
tree and one main line, and coordinated with them by hand, is the shape this replaces. In the
additive mode the piece of work is a thread the to-do computes, taken whole with `open --thread`,
and the threads land on the main line together, at a join, by a local merge and no pull request.

WHAT IS CENTRAL IS A TAG. A claim is `claim/<ID>` and a reservation is `id/<ID>` --
`claim/<product>/<ID>` and `id/<product>/<ID>` for the families the catalog numbers per
product -- annotated, pushed to the remote. Git refuses to replace a tag without force, and two
pushes that create one tag at the same moment are decided by the remote, so whoever pushes
second is told who pushed first. What it does not stop is somebody forcing a push or deleting
a tag by hand: this is the protection of people who use it, and the checks are what see the
rest. The tag object is unique -- who, when, for which branch -- so after a push whose answer
was lost, the remote holding that object is the proof the push went through. The branch is
created in the same atomic push as the claims, with a lease that requires it not to exist yet --
but for a thread taken again, whose branch exists and whose claims alone are pushed. Reservations
are never deleted, and a number reserved and not used stays burned; claims are removed by
`release`, when a person says so, and by `join --close`, by role, for what a join landed.

A DELEGATION IS A TAG TOO. `delega/<slug of the name>`, annotated with who gave it, to whom and
when: in the additive mode the person it names decides as an admin does, until it is revoked.
Only an admin gives one, since deputies are declared beforehand for the day the admin cannot
act; the admin or the delegate takes it back. A delegation is not a role in `work.yaml`, which
only an admin changes, and so it needs no join to start.

THE BRANCH IS BROUGHT UP TO DATE BY MERGING THE MAIN LINE INTO IT, never by a rebase: a rebase
needs a forced push and rewrites the commits the exchange and the history name. Commits pushed to
the same work branch from another clone come in first: by a fast-forward when this clone has
nothing of its own, and the main line in the same run; by a merge otherwise, and the main line on
the next run. `sync` does each
merge and resolves exactly three things: a file the generator writes whole, taken from the side
merged in and regenerated; a conflict that lies entirely inside an attestation block, which keeps this
branch's and is reread after; and lines both sides only added at one place of a Markdown body,
all kept, this branch's first. In the additive mode, when the main line comes in, two more: keys
both sides added to one map of the front matter, all kept; and lines a thread only added to an
open register, put back over what the main line changed, where they stand by themselves -- see
`resolve`. Everything else stops it -- a conflict anywhere else, a file one
side deleted, a file that is not text, a conflict it cannot parse -- because it is content and is
a person's. Before merging it refuses a main line that created an identifier this branch created
too -- the main line, or the branch's own commits pushed from another clone: once both are in one
tree, YAML folds two rows of `entries:` into one without a word.

WHAT IT NEVER DOES. It never pushes the main line -- but for `join --merge`, the one gesture
by which an admin, a deputy or a delegate lands a join, with their name --, never forces a push,
never deletes a reservation, never decides which of two texts holds, and never deduces who is
working from `git config`: `--who` is the person's name, as they give it.

Only in a project that declares `.framework/work.yaml`. Exit 0 when done, 1 when something is
for the person (claimed by somebody else, a conflict left, a collision), 2 when nothing was
done because the invocation or the repository does not allow it.
"""

from __future__ import annotations

import argparse
import difflib
import importlib
import importlib.metadata
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate as v  # noqa: E402  (the validator's helpers, not its main)
import todo as T  # noqa: E402  (the threads, computed as the to-do computes them)

B = v._branches
S = importlib.import_module(f"{v._CORE_NAME}.strict_yaml")
E = v._effects
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
        """The main line, the work branches, the claims, the reservations and the delegations,
        as the remote has them now. The tags are fetched with force and pruned: a claim
        released and taken again is a tag that moved, which a plain fetch refuses to update,
        and a claim released, or a delegation revoked, is one this clone must not go on
        seeing."""
        r = self.net("fetch", "--prune", self.remote,
                     f"+refs/heads/*:refs/remotes/{self.remote}/*",
                     f"+{B.CLAIM_REF}*:{B.CLAIM_REF}*", f"+{B.RESERVED_REF}*:{B.RESERVED_REF}*",
                     f"+{B.DELEGATION_REF}*:{B.DELEGATION_REF}*")
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

def _computed_thread(p: Project, name: str) -> dict:
    """The thread the to-do computes now, by its name, after the fetch: two clones that had not
    fetched would see different threads."""
    r = T.compute(p.root, p.remote, p.main)
    found = next((t for t in r.get("threads", []) if t["name"] == name), None)
    if found is None:
        if f"{p.prefix}{name}" in r.get("open", {}):
            v.refuse(f"{name} is open already: {p.prefix}{name}. A thread open is fixed until "
                     "the join that lands it.")
        v.refuse(f"{name} is not a thread the to-do computes now. The threads to take: "
                 f"{', '.join(t['name'] for t in r.get('threads', [])) or 'none'}.")
    return found


def cmd_open(p: Project, args) -> int:
    who = p.who(args.who)
    args.thread = getattr(args, "thread", None)      # a caller that predates it passes none
    if args.thread and (args.branch or args.ids):
        v.refuse("`--thread` takes the thread whole, on a branch named after it: no `--branch`, "
                 "no elements.")
    args.branch = args.branch or args.thread
    if not args.branch:
        v.refuse("`--branch` names the branch: the name after the prefix, such as od-042.")
    if not SLUG.match(args.branch):
        v.refuse(f"`--branch {args.branch}`: lower case letters, digits and dashes.")
    if args.branch.startswith(B.JOIN):
        v.refuse(f"`--branch {args.branch}`: `{B.JOIN}` is the name of a join's branch, where "
                 "living documents are rewritten and the additive check does not read.")
    if args.ids and args.branch.startswith(B.PARKING):
        v.refuse(f"`--branch {args.branch}`: `{B.PARKING}` is the name of a parking branch, which "
                 "claims no element.")
    p.fetch()
    roles = main_roles(p)
    additive = roles.get("mode") == "additive"
    ids, resume = list(args.ids), False
    if args.thread and not additive:
        v.refuse("`--thread` is for a project in the additive mode, whose to-do computes the "
                 "threads; here, name the elements.")
    if additive and args.thread:
        thread = _computed_thread(p, args.thread)
        delegated = {c.get("to") for c in p.held(B.DELEGATION_REF).values() if c.get("to")}
        if any(n.kind == "decision" for n in thread["nodes"]) \
                and who not in B.deciders(roles, delegated):
            v.refuse(f"{args.thread} holds a decision, and only an admin, a deputy or a delegate "
                     "decides: a contributor implements.")
        ids = [i.replace("/", ":") for n in thread["nodes"] for i in n.ids]
    elif additive and ids:
        v.refuse("In the additive mode a thread is taken whole, as the to-do computes it: "
                 "`open --thread <name>`, or no element for a parking branch. "
                 "`todo.py` lists the threads to take.")
    # In the additive mode a piece of work without an element is a parking branch, and it is
    # known by its name: no claims is also what a thread whose claims were released looks like.
    short = args.branch
    if not ids and additive and not short.startswith(B.PARKING):
        short = B.PARKING + short
    branch = p.prefix + short
    main = p.view(p.base)
    wanted = [p.element(w) for w in dict.fromkeys(ids)]
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
        # A thread abandoned -- its claims all released -- is taken again on its own branch,
        # with the work half done; anything else under that name is somebody's.
        holders = [c for c in p.held(B.CLAIM_REF).values() if c.get("branch") == branch]
        if additive and args.thread and holders:
            v.refuse(f"{branch} is open, in the hands of "
                     f"{', '.join(sorted({c.get('who', '?') for c in holders}))}.")
        if not (additive and args.thread):
            v.refuse(f"{branch} exists on {p.remote} already. Choose another `--branch`.")
        resume = True
        # Checked before anything is pushed: a local branch that is not the remote's, or a
        # worktree left from before, would stop the work after the claims were taken.
        local = git(p.root, "rev-parse", "--verify", "-q", f"refs/heads/{branch}", check=False).stdout.strip()
        remote = git(p.root, "rev-parse", f"refs/remotes/{p.remote}/{branch}").stdout.strip()
        if local and local != remote:
            v.refuse(f"{branch} here is not {p.remote}'s: bring it to the remote's commit, or "
                     "remove it, before taking the thread again.")
        if not args.no_worktree and p.worktree_for(short).exists():
            v.refuse(f"{p.worktree_for(short)} exists: remove it before taking the thread again.")

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
        if work_branch == branch or work_branch[len(p.prefix):].startswith(B.JOIN):
            continue
        changed = B.touched(p.view(name), p.view(B.merge_base(p.root, p.base, name)))
        for ident, what in changed.items():
            if ident in idents:
                say(f"note: {work_branch} changes {ident} ({'; '.join(what)}) without a claim.")

    mine = {}
    for key, tag in wanted:
        git(p.root, "tag", "-a", f"claim/{tag}", "-m", message(who, branch, f"claim {tag}"), p.base)
        mine[tag] = git(p.root, "rev-parse", f"{B.CLAIM_REF}{tag}").stdout.strip()
    start = f"refs/remotes/{p.remote}/{branch}" if resume else p.base
    if git(p.root, "rev-parse", "--verify", "-q", f"refs/heads/{branch}", check=False).returncode:
        git(p.root, "branch", "--no-track", branch, start)
    elif not resume:
        for tag in mine:
            git(p.root, "tag", "-d", f"claim/{tag}", check=False)
        v.refuse(f"a branch {branch} is here already, not on {p.remote}: remove it"
                 + ("" if args.thread else ", or choose another name") + ". Nothing was claimed.")

    def undo() -> None:
        for tag in mine:
            git(p.root, "tag", "-d", f"claim/{tag}", check=False)
        if not resume:
            git(p.root, "branch", "-D", branch, check=False)

    # One atomic push: the branch, with a lease that says it must not exist yet -- two `open`s
    # naming one branch would otherwise both succeed, the second as "up to date" -- and every
    # claim, created without force. A thread taken again pushes its claims alone.
    refspecs = ([] if resume else [f"refs/heads/{branch}:refs/heads/{branch}"]) + \
               [f"{B.CLAIM_REF}{t}:{B.CLAIM_REF}{t}" for t in mine]
    head = git(p.root, "rev-parse", branch).stdout.strip()
    expect = {**({} if resume else {f"refs/heads/{branch}": head}),
              **{f"{B.CLAIM_REF}{t}": sha for t, sha in mine.items()}}
    outcome, said = p.push(refspecs, expect, ("--atomic",) if resume else
                           ("--atomic", f"--force-with-lease=refs/heads/{branch}:"))
    if outcome == "unknown" and resume:
        v.refuse(f"the push of the claims may or may not have landed: the remote did not answer "
                 f"({said}). Run `list` once it answers: it says whether {', '.join(mine)} are "
                 f"claimed on {branch}; if they are not, `open --thread` again.")
    if outcome == "unknown":
        path = p.worktree_for(short)
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
        if branch_taken and not resume:
            say(f"  {branch} exists on {p.remote}: choose another `--branch`.")
        return 1

    path = p.worktree_for(short)
    if not args.no_worktree:
        if path.exists():
            v.refuse(f"{path} exists. The claim and the branch are on {p.remote}; make the "
                     f"worktree yourself: git worktree add <path> {branch}")
        git(p.root, "worktree", "add", str(path), branch)
        git(path, "branch", "--set-upstream-to", f"{p.remote}/{branch}", branch)
    where = B.prefix(p.root)
    say(f"Claimed: {', '.join(mine) or 'nothing (a piece of work without an element)'}.")
    say(f"Branch: {branch}, " + (f"taken again on {p.remote}, with what it already carries:"
                                  if resume else f"from {p.base}, on {p.remote}."))
    if resume:
        for line in git(p.root, "log", "--oneline", f"{p.base}..{branch}").stdout.splitlines():
            say(f"  {line}")
        for ident, what in B.touched(p.view(branch),
                                     p.view(B.merge_base(p.root, p.base, branch))).items():
            say(f"  {ident}: {'; '.join(what)}")
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
    delegations = {c.get("to", t): c for t, c in sorted(p.held(B.DELEGATION_REF).items())}
    landed: dict[str, str] = {}
    if main_roles(p).get("mode") == "additive":
        joining = p.held(B.CLAIM_REF).get(JOIN_CLAIM, {}).get("branch")
        for name in git(p.root, "for-each-ref", "--format=%(refname:short)", "refs/heads/").stdout.split():
            if not name.startswith(p.prefix):
                continue
            at = _landed_at(p, name)
            if at:
                landed[name] = _landed_note(p, name, at)
            elif name[len(p.prefix):].startswith(B.JOIN) and name != joining:
                landed[name] = (f"{name} is the branch of a join closed or abandoned: remove it "
                                f"here: {_remove_hint(p, name, force=True)}.")
    if args.json:
        print(json.dumps({"base": p.base, "branches": rows, "claims_without_branch": orphans,
                          "delegations": delegations, "landed": landed}, indent=2,
                         ensure_ascii=False))
        return 0
    for name, c in delegations.items():
        say(f"delegation: {name} decides as an admin, given by {c.get('who', '?')} on "
            f"{c.get('when', '?')}.")
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
        joining = r["branch"][len(p.prefix):].startswith(B.JOIN)
        for ident, what in r["touches"].items():
            mark = "" if ident in r["claims"] or joining else "  (not claimed)"
            say(f"  changes {ident}: {'; '.join(what)}{mark}")
    for tag, c in orphans.items():
        say(f"claim without a branch: {tag} by {c.get('who', '?')} for {c.get('branch', '?')} "
            f"since {c.get('when', '?')}. Landed or abandoned: `release` it once its person agrees.")
    for note in landed.values():
        say(note)
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


def main_roles(p: Project) -> dict:
    """`.framework/work.yaml` as the main line has it after the fetch: where the job and
    `BR004` read the mode and the roles, and not the working tree, which may be behind it or
    on a branch that changes them. A file that cannot be read there reads as empty, and the
    refusals that follow say what is missing."""
    return B.work_at(p.root, p.base)


def main_person(p: Project, roles: dict, name: str | None, flag: str) -> str:
    """A name among the people of the main line's `work.yaml`, as `who` checks the working
    tree's for every other command."""
    name = (name or "").strip()
    people = B.names(roles.get("people"))
    if not name or (people and name not in people):
        v.refuse(f"`{flag} {name}` is not among the people {B.WORK} names on {p.base}: "
                 f"{', '.join(sorted(people))}.")
    return name


def cmd_delegate(p: Project, args) -> int:
    p.fetch()
    roles = main_roles(p)
    who = main_person(p, roles, args.who, "--who")
    if roles.get("mode") != "additive":
        v.refuse(f"{B.WORK} on {p.base} does not declare `mode: additive`, or cannot be read "
                 "there, and only that mode reads a delegation: here it would say somebody "
                 "decides and change nothing.")
    if who not in B.names(roles.get("admins")):
        v.refuse(f"{who} is not among the admins of {B.WORK} on {p.base}: only an admin gives a "
                 "delegation. A deputy is declared there beforehand, by an admin.")
    to = main_person(p, roles, args.to, "--to")
    if to in B.names(roles.get("admins")) | B.names(roles.get("deputies")):
        v.refuse(f"{to} already decides, as an admin or a deputy: a delegation adds nothing.")
    name = B.slug(to)
    if not name:
        v.refuse(f"`{to}` gives no name a ref can carry.")
    held = p.held(B.DELEGATION_REF).get(name)
    if held is not None:
        v.refuse(f"{held.get('to', to)} already holds a delegation, given by {held.get('who', '?')} "
                 f"on {held.get('when', '?')}.")
    ref = f"{B.DELEGATION_REF}{name}"
    git(p.root, "tag", "-a", f"delega/{name}", "-m",
        f"delegate {to}\n\nwho: {who}\nto: {to}\nwhen: {stamp()}\n", p.base)
    mine = git(p.root, "rev-parse", ref).stdout.strip()
    outcome, said = p.push([f"{ref}:{ref}"], {ref: mine})
    if outcome == "unknown":
        v.refuse(f"the push of the delegation may or may not have landed: the remote did not "
                 f"answer ({said}). The local tag is kept; `list` says whether it is there.")
    if outcome != "ok":
        git(p.root, "tag", "-d", f"delega/{name}", check=False)
        v.refuse(f"the delegation did not go through ({said}); nothing was given.")
    say(f"{to} decides as an admin until the delegation is revoked: `revoke --to \"{to}\"`, by "
        f"an admin or by {to}.")
    return 0


def cmd_revoke(p: Project, args) -> int:
    p.fetch()
    roles = main_roles(p)
    who = main_person(p, roles, args.who, "--who")
    # `--to` is not checked against the people: the delegation of somebody no longer among
    # them is the one most worth taking back. Found by the name it was given to, not by its
    # slug, which two names can share.
    to = (args.to or "").strip()
    if who != to and who not in B.names(roles.get("admins")):
        v.refuse(f"{who} is not an admin on {p.base}, and the delegation is {to}'s: an admin "
                 "takes it back, or the delegate gives it up.")
    found = [t for t, c in p.held(B.DELEGATION_REF).items() if c.get("to") == to]
    if not found:
        v.refuse(f"{to} holds no delegation on {p.remote}.")
    name = found[0]
    ref = f"{B.DELEGATION_REF}{name}"
    outcome, said = p.push([f":{ref}"], {ref: None})
    if outcome != "ok":
        v.refuse(f"the revocation {'may not have gone' if outcome == 'unknown' else 'did not go'} "
                 f"through ({said}): run `list` to see what the remote holds.")
    git(p.root, "tag", "-d", f"delega/{name}", check=False)
    say(f"Revoked: {to} no longer decides as an admin.")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# join

JOIN_CLAIM = "ricongiungimento"       # claim/ricongiungimento: one join at a time
E_THREADS = "_filoni"


def _joiner(p: Project, args) -> tuple[dict, str]:
    """The main line's roles, and the person, who decides there."""
    p.fetch()
    roles = main_roles(p)
    if roles.get("mode") != "additive":
        v.refuse(f"{B.WORK} on {p.base} does not declare `mode: additive`: a join lands threads, "
                 "and there are none here.")
    who = main_person(p, roles, args.who, "--who")
    delegated = {c.get("to") for c in p.held(B.DELEGATION_REF).values() if c.get("to")}
    if who not in B.deciders(roles, delegated):
        v.refuse(f"{who} is not an admin, a deputy or a delegate on {p.base}: a join is theirs.")
    return roles, who


def _joined(p: Project, ref: str) -> list[tuple[str, str]]:
    """The threads a join's branch merged, and at which commits, from its merge messages."""
    log = git(p.root, "log", "--merges", "--format=%B", f"{p.base}..{ref}", check=False).stdout
    out = []
    for line in log.splitlines():
        if line.startswith(B.JOINED):
            parts = line[len(B.JOINED):].split()
            if len(parts) == 2:
                out.append((parts[0], parts[1]))
    return out


def _join_root(p: Project) -> str:
    """The commit the open join started from: where its claim points."""
    return git(p.root, "rev-parse", "--verify", "-q", f"{B.CLAIM_REF}{JOIN_CLAIM}^{{commit}}",
               check=False).stdout.strip()


def _join_landed(p: Project, branch: str) -> bool:
    """The open join is on the main line: its branch, as the remote has it, signed since it
    started, and contained in the main line. Read the same by every step, since a push of the
    main line whose answer was lost leaves exactly this state to be closed."""
    ref = f"refs/remotes/{p.remote}/{branch}"
    root = _join_root(p)
    if not root or git(p.root, "rev-parse", "--verify", "-q", ref, check=False).returncode:
        return False
    signed = git(p.root, "log", f"--format=%(trailers:key={B.JOIN_TRAILER},valueonly)",
                 f"{root}..{ref}", check=False).stdout.strip()
    return bool(signed) and git(p.root, "merge-base", "--is-ancestor", ref, p.base,
                                check=False).returncode == 0


def _landed(p: Project, ref: str) -> list[tuple[str, str]]:
    """The threads a finished join merged, from the commit that carries its trailer: read the
    same before and after the join reaches the main line, when its merges are no longer past
    it. Only since the join started: an earlier join's commit is not this one's."""
    since = _join_root(p)
    log = git(p.root, "log", "--format=%H%x00%(trailers:key=" + B.JOIN_TRAILER + ",valueonly)%x00%B%x1e",
              f"{since}..{ref}" if since else ref, check=False).stdout
    for record in log.split("\x1e"):
        parts = record.strip("\n").split("\x00")
        if len(parts) == 3 and parts[1].strip():
            return [(x.split()[0], x.split()[1]) for x in
                    (l[len(B.JOINED):] for l in parts[2].splitlines() if l.startswith(B.JOINED))
                    if len(x.split()) == 2]
    return []


def _signed_tip(p: Project, ref: str) -> bool:
    """Whether the last commit of the join's branch carries its trailer: what lands is signed
    whole, a `sync` or a correction after `--finish` included."""
    return bool(git(p.root, "log", "-1", f"--format=%(trailers:key={B.JOIN_TRAILER},valueonly)",
                    ref, check=False).stdout.strip())


def _finished(p: Project, ref: str) -> bool:
    """Whether the join's branch carries its trailer past the main line."""
    return bool(git(p.root, "log", f"--format=%(trailers:key={B.JOIN_TRAILER},valueonly)",
                    f"{p.base}..{ref}", check=False).stdout.strip())


def _join_tree(p: Project, branch: str) -> Path:
    """The join's worktree, beside the main checkout; one left there holding another branch is
    somebody's, and is not reused."""
    path = p.worktree_for(branch[len(p.prefix):])
    if path.exists():
        held = git(path, "rev-parse", "--abbrev-ref", "HEAD", check=False).stdout.strip()
        if held != branch:
            v.refuse(f"{path} exists and holds {held or 'no branch'}, not {branch}: remove or "
                     "move it first.")
        return path
    if git(p.root, "rev-parse", "--verify", "-q", f"refs/heads/{branch}", check=False).returncode:
        git(p.root, "branch", "--no-track", branch, f"refs/remotes/{p.remote}/{branch}")
    git(p.root, "worktree", "add", str(path), branch)
    return path


def _regenerate(root: Path) -> list[str]:
    """The views regenerated from the tree at `root`, staged: what each of them derives from."""
    r = subprocess.run([sys.executable, str(Path(v.__file__)), "--root", str(root),
                        "--emit-index", "--json", "--stale-days", "36500"],
                       capture_output=True, text=True)
    try:
        written = json.loads(r.stdout).get("generated", []) if r.returncode in (0, 1) else None
    except json.JSONDecodeError:
        written = None
    if written is None:
        v.refuse(f"the views could not be regenerated (exit {r.returncode}): "
                 f"{(r.stderr or '').strip()[-300:]}.")
    for rel in written:
        git(root, "add", "--", rel)
    return written


def _branch_findings(p: Project, name: str, ref: str) -> list[str]:
    """What the validator says of a thread's branch against the main line, `BR005` first -- a
    write that is not additive: nothing else runs it, since a thread has no pull request. Run
    with `--base` in a worktree of its own, detached at the remote branch, because git does not
    check one branch out twice, and with the branch's name in `GITHUB_HEAD_REF`, which the
    validator reads when HEAD is detached."""
    with tempfile.TemporaryDirectory(prefix="join-") as tmp:
        tree = Path(tmp) / "tree"
        if git(p.root, "worktree", "add", "-q", "--detach", str(tree), ref, check=False).returncode:
            return ["its branch could not be checked out to run the validator on it"]
        try:
            where = B.prefix(p.root)
            r = subprocess.run([sys.executable, str(Path(v.__file__)), "--root",
                                str(tree / where if where else tree), "--base", p.base, "--json",
                                "--stale-days", "36500"], capture_output=True, text=True,
                               env={**os.environ, "GITHUB_HEAD_REF": name})
            try:
                found = json.loads(r.stdout).get("findings", [])
            except ValueError:
                return [f"the validator gave no report on its branch (exit {r.returncode})"]
        finally:
            git(p.root, "worktree", "remove", "--force", str(tree), check=False)
    found = sorted((f for f in found if str(f.get("code", "")).startswith("BR")),
                   key=lambda f: (f["code"] not in ("BR005", "BR006"), f["code"], f["path"]))
    said = [f"{f['code']} {f['path']}: {f['message'][:200]}" for f in found[:10]]
    return said + ([f"and {len(found) - 10} more findings of the branches"] if len(found) > 10 else [])


def _before_merging(p: Project, r: dict, names: list[str], every: list[str]) -> None:
    """What the threads bring that the roles keep to those who decide (§10), the effects each
    wrote outside what it forecast -- first those another thread of this join forecast -- and
    what the checks of the branches find on each: shown to the admin before anything is merged,
    to be read, not judged here."""
    tree = r.get("tree")
    where = B.prefix(p.root)
    try:
        policy = json.loads(git(p.root, "show", f"{p.base}:{where}.framework/contribution-policy.json",
                                check=False).stdout or "{}")
    except ValueError:
        policy = {}
    declared: dict[str, set[str]] = {}
    for name in every:
        anchors: set[str] = set()
        for ident, _ in r.get("open", {}).get(name, {}).get("claims", []):
            bare_id = ident.rsplit("/", 1)[-1]
            if tree and bare_id in tree.entries:
                anchors |= {str(x) for x in v.as_list(tree.entries[bare_id].get("affects"))}
            if tree and bare_id in tree.changes:
                change = tree.changes[bare_id]
                anchors |= {str(x) for x in v.as_list(change.meta.get("affects"))}
                # The forecast the to-do reads: the mandate's prefixes too.
                mandate = (policy.get("mandates") or {}).get(change.rel.replace("\\", "/")) or {}
                for repo, prefixes in (mandate.get("paths") or {}).items():
                    kind = "doc" if repo == "documents" else f"code:{repo}"
                    anchors |= {f"{kind}:{str(x).rstrip('/')}" for x in v.as_list(prefixes)}
            if tree and ident in tree.roadmap:
                anchors.add(f"{tree.roadmap[ident]}#{bare_id}")
        declared[name] = anchors
    for name in names:
        ref = f"refs/remotes/{p.remote}/{name}"
        said = []
        changed = set(git(p.root, "diff", "--name-only", f"{p.base}...{ref}").stdout.split())
        if f"{where}.framework/contribution-policy.json" in changed:
            said.append("the contribution policy changes on the thread's branch")
        for path in sorted(c for c in changed if c.endswith("/contribution-policy.json")
                           and f"/{E_THREADS}/" in f"/{c}"):
            said.append(f"a contribution policy delivered, {path}: an admin or whoever stands in "
                        "carries it into `.framework/`, after reading it")
        before = {a.rel.replace("\\", "/"): a for a in p.view(p.base).arts}
        for a in p.view(ref).arts:
            rel = a.rel.replace("\\", "/")
            if f"{where}{rel}" not in changed:
                continue
            was = (before.get(rel).meta.get("status") if before.get(rel) else None)
            now = a.meta.get("status")
            if now == was:
                continue
            if a.type == "impact-classification" and now == "accepted":
                said.append(f"{a.id or rel} accepted: a classification is confirmed by who decides")
            elif a.type == "change-contract" and now == "verified":
                said.append(f"{a.id or rel} verified")
            elif a.type == "decision-record" and now == "proposed" and was is None:
                said.append(f"{a.id or rel} proposed: accept it -- and write its cascade on the "
                            "join's branch -- or leave it proposed")
        # The evaluation plan: one already there that changes -- its thresholds are decisions --
        # and an evaluation report new on the thread that records a freeze of it.
        for a in p.view(ref).arts:
            rel = a.rel.replace("\\", "/")
            if f"{where}{rel}" not in changed:
                continue
            old = before.get(rel)
            if a.type == "evaluation-plan" and old is not None \
                    and (old.meta != a.meta or old.body != a.body):
                said.append(f"{rel} changes")
            elif a.type == "evaluation-report" and old is None and a.meta.get("evp_hash"):
                said.append(f"{a.id or rel} records a freeze of the evaluation plan "
                            f"{a.meta.get('evp_version', '')}".rstrip())
        thread_view, main_view = p.view(ref), p.view(p.base)
        for k, row in thread_view.entries.items():
            if k.startswith("KI-") and thread_view.closed(k) and not main_view.closed(k):
                closers = sorted(thread_view.closers(k))
                if not any(c.startswith("CHG-") for c in closers):
                    said.append(f"{k} closed by {', '.join(closers) or 'its row'}, not by a "
                                "change: a commit, or kept as it is, which only who decides "
                                "can say")
        listed = git(p.root, "ls-tree", "-r", "--name-only", "--full-tree", ref, "--",
                     f"{where}{E_THREADS}").stdout.split("\n")
        outside = []
        for path in (x for x in listed if x.endswith(f"/{E.EFFECTS}")):
            for eff in E.read(git(p.root, "show", f"{ref}:{path}").stdout)[0]:
                within, other = T.placed(eff.target, declared[name],
                                         {n: declared[n] for n in every if n != name},
                                         flat=tree.keys if tree else frozenset())
                if within:
                    continue
                outside.append((not other, f"effect on {eff.target}, outside the forecast"
                                + (f" -- {', '.join(other)} forecast it" if other else "")))
        said = [line for _, line in sorted(outside)] + said + _branch_findings(p, name, ref)
        if said:
            say(f"{name}, before it is merged:")
            for line in said:
                say(f"  - {line}")


def _join_start(p: Project, who: str, args) -> int:
    held = p.held(B.CLAIM_REF).get(JOIN_CLAIM)
    r = T.compute(p.root, p.remote, p.main)
    ready = r.get("ready", [])
    named = [x if x.startswith(p.prefix) else p.prefix + x for x in args.threads]
    wanted = [] if args.no_threads else (named or ready)
    not_ready = [x for x in wanted if x not in ready]
    if not_ready:
        v.refuse(f"not ready: {', '.join(not_ready)}. A join merges the threads that are ready: "
                 f"{', '.join(ready) or 'none now'}.")
    if not wanted and not args.no_threads and not held:
        v.refuse("no thread is ready. `--no-threads` opens a join with no thread, for what is "
                 "written only on a join's branch: `work.yaml`, an adoption, the contribution "
                 "policy, annotations, and what only those who decide write -- a release, a "
                 "change verified, the freeze of the evaluation plan, an approval, a mandate "
                 "withdrawn or the forecast of an approved one.")
    if held:
        branch = held.get("branch", "")
        if _join_landed(p, branch):
            v.refuse(f"{branch} is on {p.base} already: `join --close` releases what it landed.")
        if _finished(p, branch) or _finished(p, f"refs/remotes/{p.remote}/{branch}"):
            then = ("`join --merge` lands it" if _signed_tip(p, f"refs/remotes/{p.remote}/{branch}")
                    else "it has commits after its last signature, which `join --finish` signs; "
                         "then `join --merge` lands it")
            v.refuse(f"{branch} is finished: {then}, `join --abandon` drops it. A thread ready "
                     "since waits for the next join.")
        remote_branch = f"refs/remotes/{p.remote}/{branch}"
        local = git(p.root, "rev-parse", "--verify", "-q", f"refs/heads/{branch}", check=False).stdout.strip()
        if local and git(p.root, "merge-base", "--is-ancestor", remote_branch, local,
                         check=False).returncode:
            v.refuse(f"{branch} here is behind or apart from {p.remote}'s: bring it to the remote's "
                     "commit first.")
        if not named and not args.no_threads:
            v.refuse(f"{branch} is open, and merged {', '.join(n for n, _ in _joined(p, remote_branch)) or 'no thread yet'}: "
                     "name the threads to merge in it, as when it was opened -- a thread ready since "
                     "is not added by itself.")
        say(f"A join is open: {branch}, by {held.get('who', '?')} since {held.get('when', '?')}. "
            "It goes on from where it is.")
    else:
        # One more than the joins on the main line, and than every number a join reserved: a
        # join abandoned leaves nothing on the main line, and its number, reused, would give
        # the next join the name of a branch some clone still holds.
        signed = git(p.root, "log", f"--format=%s%x00%(trailers:key={B.JOIN_TRAILER},valueonly)%x1e",
                     p.base).stdout
        landed = [int(m.group(1)) for s, _, who in (r.strip().partition("\x00") for r in signed.split("\x1e"))
                  if who.strip() and (m := re.search(rf"{re.escape(B.JOIN)}(\d+)", s))]
        reserved = [int(m.group(1)) for m in (re.fullmatch(rf"{re.escape(B.JOIN)}(\d+)", t)
                                              for t in p.held(B.RESERVED_REF)) if m]
        n = 1 + max([*landed, *reserved], default=0)
        branch = f"{p.prefix}{B.JOIN}{n}"
        if git(p.root, "rev-parse", "--verify", "-q", f"refs/heads/{branch}", check=False).returncode == 0:
            v.refuse(f"{branch} is left here by a join that did not land: remove it -- "
                     f"{_remove_hint(p, branch, force=True)} -- and `join` again.")
        number = f"{B.JOIN}{n}"
        git(p.root, "tag", "-a", f"claim/{JOIN_CLAIM}", "-m",
            message(who, branch, f"claim {JOIN_CLAIM}"), p.base)
        git(p.root, "tag", "-a", f"id/{number}", "-m", message(who, branch, f"reserve {number}"),
            p.base)
        tag = git(p.root, "rev-parse", f"{B.CLAIM_REF}{JOIN_CLAIM}").stdout.strip()
        mark = git(p.root, "rev-parse", f"{B.RESERVED_REF}{number}").stdout.strip()
        git(p.root, "branch", "--no-track", branch, p.base)
        head = git(p.root, "rev-parse", branch).stdout.strip()
        outcome, said = p.push([f"refs/heads/{branch}:refs/heads/{branch}",
                                f"{B.CLAIM_REF}{JOIN_CLAIM}:{B.CLAIM_REF}{JOIN_CLAIM}",
                                f"{B.RESERVED_REF}{number}:{B.RESERVED_REF}{number}"],
                               {f"refs/heads/{branch}": head, f"{B.CLAIM_REF}{JOIN_CLAIM}": tag,
                                f"{B.RESERVED_REF}{number}": mark},
                               ("--atomic", f"--force-with-lease=refs/heads/{branch}:"))
        if outcome != "ok":
            git(p.root, "tag", "-d", f"claim/{JOIN_CLAIM}", check=False)
            git(p.root, "tag", "-d", f"id/{number}", check=False)
            git(p.root, "branch", "-D", branch, check=False)
            v.refuse(f"the join could not be opened ({said}): another may have been opened a "
                     "moment ago; run `list`.")
    tree = _join_tree(p, branch)
    if git(tree, "rev-parse", "--verify", "-q", "MERGE_HEAD", check=False).returncode == 0:
        v.refuse(f"a merge is in progress in {tree}: resolve it and `git commit` -- its message "
                 "names the thread -- or `git merge --abort`, then `join` again.")
    if git(tree, "status", "--porcelain", "--untracked-files=no").stdout.strip():
        v.refuse(f"{tree} has changes not committed: commit them, or put them aside, first. A "
                 "merge is a commit of its own.")
    where = B.prefix(p.root)
    done = {name for name, _ in _joined(p, branch)}
    todo_now = sorted(set(wanted) - done)
    _before_merging(p, r, todo_now, sorted(done | set(todo_now)))
    again = (f"--who \"{who}\" " + (" ".join(n[len(p.prefix):] for n in sorted(set(wanted)))
                                     or "--no-threads"))
    for name in todo_now:
        sha = git(p.root, "rev-parse", f"refs/remotes/{p.remote}/{name}").stdout.strip()
        both = _collisions(p, branch, sha)
        if both:
            say(f"Not merged: {name} and this join both created {', '.join(both)}. Renumber on "
                f"{name}, and run `join {again}` again.")
            return 1
        msg = f"Join {branch}: merge {name}\n\n{B.JOINED}{name} {sha}\n"
        r = git(tree, "-c", "merge.conflictStyle=diff3", "-c", "rerere.enabled=false", "merge",
                "--no-ff", "--no-commit", "-m", msg, sha, check=False)
        if r.returncode and not git(tree, "ls-files", "-u").stdout.strip():
            git(tree, "merge", "--abort", check=False)
            v.refuse(f"the merge of {name} stopped: {(r.stderr or r.stdout).strip()[-300:]}")
        root = tree / where if where else tree
        left = _settle(p, root, tree, where, True, branch_ours=False)
        if left:
            say(f"\n{name}: left for a person: {', '.join(left)}. Resolve them in {tree}, "
                "`git add` them and `git commit` -- the message is ready, and it names the thread "
                f"and its commit -- then run `join {again}` again.")
            return 1
        _regenerate(root)
        git(tree, "commit", "-q", "-m", msg)
        say(f"Merged {name} at {sha[:12]}.")
    say(f"\nJoin: {branch}, in {tree}. Now rewrite the living documents from the effects in "
        f"`{E_THREADS}/*/effetti.md`, approve the changes to approve, accept or leave the "
        "decisions proposed, regenerate the views (`validate.py --emit-index`), have the reviser "
        "read the diff, commit, and `join --finish`.")
    return 0


def _join_finish(p: Project, who: str) -> int:
    held = p.held(B.CLAIM_REF).get(JOIN_CLAIM)
    if not held:
        v.refuse("no join is open: `join` opens one.")
    branch = held.get("branch", "")
    if _join_landed(p, branch):
        v.refuse(f"{branch} is on {p.base} already: `join --close` releases what it landed.")
    tree = _join_tree(p, branch)
    if git(tree, "status", "--porcelain", "--untracked-files=no").stdout.strip():
        v.refuse(f"{tree} has changes not committed: commit the rewritten documents first.")
    remote_branch = f"refs/remotes/{p.remote}/{branch}"
    if git(p.root, "merge-base", "--is-ancestor", remote_branch, branch, check=False).returncode:
        v.refuse(f"{branch} here is behind or apart from {p.remote}'s, which another clone may "
                 "have finished: bring it to the remote's commit first.")
    if not _signed_tip(p, branch):
        where = B.prefix(p.root)
        folder = (tree / where / E_THREADS) if where else tree / E_THREADS
        rewritten = []
        for path in sorted(folder.glob(f"*/{E.EFFECTS}")) if folder.is_dir() else []:
            for eff in E.read(path.read_text(encoding="utf-8"))[0]:
                rewritten.append(f"- {eff.target} (from {path.parent.name})")
        if folder.exists():
            git(tree, "rm", "-r", "-q", "--", str(folder.relative_to(tree)))
        joined = _joined(p, branch)
        body = (f"Join {branch} finished: {', '.join(n for n, _ in joined) or 'no thread'}\n\n"
                + ("Rewritten from the effects:\n" + "\n".join(rewritten) + "\n\n" if rewritten else "")
                + "".join(f"{B.JOINED}{n} {sha}\n" for n, sha in joined) + "\n"
                + f"{B.JOIN_TRAILER}: {who}\n")
        git(tree, "commit", "-q", "--allow-empty", "-m", body)
    # What the branches' checks say of the join's own branch -- who approved, what was withdrawn
    # and when, a forecast moved --: warnings nothing else shows before it lands.
    where = B.prefix(p.root)
    check = subprocess.run([sys.executable, str(Path(v.__file__)), "--root",
                            str(tree / where if where else tree), "--base", p.base, "--json",
                            "--stale-days", "36500"], capture_output=True, text=True)
    try:
        own = [f for f in json.loads(check.stdout).get("findings", [])
               if str(f.get("code", "")).startswith("BR")]
    except ValueError:
        own = []
        say(f"the checks of the branches could not be read on {branch} (exit "
            f"{check.returncode}): run `validate.py --base {p.base}` in {tree} before `--merge`.")
    for f in own[:10]:
        say(f"  {f['code']} {f['path']}: {f['message'][:200]}")
    if own:
        say(f"{len(own)} findings of the branches on {branch}: read them before `join --merge`; "
            "a correction is committed and `join --finish` run again.")
    # Signed again only when something came after the last signature -- a `sync` because the
    # main line moved, a correction --, so that what lands is signed whole; finished already and
    # not pushed, pushed again.
    head = git(tree, "rev-parse", "HEAD").stdout.strip()
    outcome, said = p.push([f"refs/heads/{branch}:refs/heads/{branch}"],
                           {f"refs/heads/{branch}": head})
    if outcome != "ok":
        v.refuse(f"the join is finished here and the push "
                 f"{'may not have gone' if outcome == 'unknown' else 'did not go'} through "
                 f"({said}). Never --force: `join --finish` again pushes what is committed.")
    say(f"{branch} finished and pushed. `join --merge --who {who}` lands it on {p.main}.")
    return 0


def _main_checkout(p: Project) -> Path:
    common = git(p.root, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    return Path(common).parent


def _join_merge(p: Project, who: str) -> int:
    held = p.held(B.CLAIM_REF).get(JOIN_CLAIM)
    if not held:
        v.refuse("no join is open: `join` opens one.")
    branch = held.get("branch", "")
    remote_branch = f"refs/remotes/{p.remote}/{branch}"
    if not _signed_tip(p, remote_branch):
        v.refuse(f"{branch} on {p.remote} ends with a commit no `{B.JOIN_TRAILER}:` trailer signs "
                 "-- not finished, or with commits after its last signature: `join --finish` "
                 "signs it.")
    if git(p.root, "merge-base", "--is-ancestor", p.base, remote_branch, check=False).returncode:
        v.refuse(f"{p.base} moved past {branch}: bring the join up to date -- `sync` in its "
                 "worktree -- and finish it again.")
    # What is validated is what is merged: the join's tree at the commit the remote holds.
    tree = _join_tree(p, branch)
    tip = git(p.root, "rev-parse", remote_branch).stdout.strip()
    if git(tree, "rev-parse", "HEAD").stdout.strip() != tip or \
            git(tree, "status", "--porcelain", "--untracked-files=no").stdout.strip():
        v.refuse(f"{tree} is not {branch} as {p.remote} holds it, clean: push or pull it first.")
    main = _main_checkout(p)
    if git(main, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip() != p.main:
        v.refuse(f"{main} is not on {p.main}: the merge is made there.")
    r = git(main, "merge", "--ff-only", "-q", p.base, check=False)
    if r.returncode:
        v.refuse(f"{p.main} in {main} has commits of its own, or changes: it cannot move to "
                 f"{p.base}. Nothing was merged.")
    where = B.prefix(p.root)
    check = subprocess.run([sys.executable, str(Path(v.__file__)), "--root",
                            str(tree / where if where else tree), "--base", p.base, "--json",
                            "--stale-days", "36500"], capture_output=True, text=True)
    try:
        errors = [f for f in json.loads(check.stdout).get("findings", []) if f["level"] == "error"]
    except (ValueError, KeyError):
        v.refuse(f"the validator gave no report on the join ({check.stderr.strip()[-200:]}).")
        return 2
    if errors:
        for f in errors[:10]:
            say(f"  {f['code']} {f['path']}: {f['message'][:160]}")
        v.refuse(f"the join has {len(errors)} errors: nothing was merged.")
    git(main, "merge", "--no-ff", "-q", "-m", f"Merge {branch} into {p.main}", tip)
    head = git(main, "rev-parse", "HEAD").stdout.strip()
    outcome, said = p.push([f"refs/heads/{p.main}:refs/heads/{p.main}"],
                           {f"refs/heads/{p.main}": head})
    if outcome == "rejected" and "[remote rejected]" in said and "cannot lock ref" not in said:
        v.refuse(f"{p.remote} refused the push of {p.main} ({said}): a hook or a protection rule, "
                 "the person's to look at. The merge is here, not pushed. Never --force.")
    if outcome == "rejected":
        v.refuse(f"{p.main} moved on {p.remote} while this merged ({said}). Undo the local merge "
                 f"-- `git -C {main} reset --keep HEAD~1` --, bring the join up to date with "
                 "`sync` in its worktree, `join --finish`, and `join --merge` again. Never --force.")
    if outcome != "ok":
        v.refuse(f"{p.main} is merged here and the push "
                 f"{'may not have gone' if outcome == 'unknown' else 'did not go'} through "
                 f"({said}). Never --force: push it once the remote answers, then `join --close`.")
    say(f"{branch} landed on {p.main}, pushed.")
    return _join_close(p, who)


def _join_close(p: Project, who: str) -> int:
    p.fetch()
    held = p.held(B.CLAIM_REF).get(JOIN_CLAIM)
    if not held:
        v.refuse("no join is open.")
    branch = held.get("branch", "")
    remote_branch = f"refs/remotes/{p.remote}/{branch}"
    if not _join_landed(p, branch):
        v.refuse(f"{branch} is not on {p.base}: the join has not landed, and nothing is released.")
    tip = git(p.root, "rev-parse", remote_branch).stdout.strip()
    landing = [row.split()[0] for row in git(p.root, "log", "--merges", "--format=%H %P%x00%s",
                                             f"{_join_root(p)}..{p.base}").stdout.splitlines()
               if tip in row.split("\x00")[0].split()[2:]
               and branch in (B.landing(row.split("\x00", 1)[-1]) or "")]
    if not _signed_tip(p, remote_branch):
        say(f"{branch} reached {p.main} with commits after its last signature, merged by hand: "
            "the validator reads them as text that came outside a join, and `LC006` speaks on "
            "them; a later join that changes the same text covers them. `join --merge` lands "
            "only a branch signed whole.")
    if not landing:
        say(f"{branch} reached {p.main} without a merge of its own that names it -- a fast-forward, "
            "or a merge by hand with another message: the validator does not read what it brought "
            "as a join's, and `LC006` speaks on it where the rereading is optional. `join --merge` "
            "merges with --no-ff and names the branch.")
    claims = p.held(B.CLAIM_REF)
    kept, failed = [], []
    for name, sha in _landed(p, remote_branch):
        there = git(p.root, "rev-parse", "--verify", "-q", f"refs/remotes/{p.remote}/{name}",
                    check=False).stdout.strip()
        if there and there != sha:
            kept.append(name)
            say(f"{name}: kept -- it has commits after the join merged it; it and its claims "
                "stay, for the next join.")
            continue
        if there:
            outcome, said = p.push([f":refs/heads/{name}"], {f"refs/heads/{name}": None},
                                   (f"--force-with-lease=refs/heads/{name}:{sha}",))
            if outcome != "ok":
                failed.append(name)
                say(f"{name}: not deleted ({said}).")
                continue
        tags = [tag for tag, c in claims.items() if c.get("branch") == name]
        if tags:
            outcome, said = p.push([f":{B.CLAIM_REF}{tag}" for tag in tags],
                                   {f"{B.CLAIM_REF}{tag}": None for tag in tags}, ("--atomic",))
            if outcome != "ok":
                failed.append(name)
                say(f"{name}: claims not released ({said}).")
                continue
            for tag in tags:
                git(p.root, "tag", "-d", f"claim/{tag}", check=False)
        say(f"{name}: landed; branch deleted and claims released ({', '.join(tags) or 'none'}), "
            f"by role, by {who}. Here: {_remove_hint(p, name)}.")
    if failed:
        say("The join stays open, so that `join --close` again finishes what did not go through.")
        return 1
    tip = git(p.root, "rev-parse", remote_branch).stdout.strip()
    outcome, said = p.push([f":refs/heads/{branch}", f":{B.CLAIM_REF}{JOIN_CLAIM}"],
                           {f"refs/heads/{branch}": None, f"{B.CLAIM_REF}{JOIN_CLAIM}": None},
                           ("--atomic", f"--force-with-lease=refs/heads/{branch}:{tip}"))
    if outcome != "ok":
        v.refuse(f"the join's branch and claim could not be removed ({said}): `join --close` "
                 "again once the remote answers.")
    git(p.root, "tag", "-d", f"claim/{JOIN_CLAIM}", check=False)
    say(f"{branch} closed. Here: {_remove_hint(p, branch)}.")
    return 1 if kept else 0


def _join_abandon(p: Project, who: str) -> int:
    held = p.held(B.CLAIM_REF).get(JOIN_CLAIM)
    if not held:
        v.refuse("no join is open.")
    branch = held.get("branch", "")
    remote_branch = f"refs/remotes/{p.remote}/{branch}"
    tip = git(p.root, "rev-parse", "--verify", "-q", remote_branch, check=False).stdout.strip()
    if _join_landed(p, branch):
        v.refuse(f"{branch} is on {p.base} already: it landed, and `join --close` releases what "
                 "it landed.")
    refspecs = [f":{B.CLAIM_REF}{JOIN_CLAIM}"] + ([f":refs/heads/{branch}"] if tip else [])
    expect = {f"{B.CLAIM_REF}{JOIN_CLAIM}": None, **({f"refs/heads/{branch}": None} if tip else {})}
    outcome, said = p.push(refspecs, expect, ("--atomic",) + (
        (f"--force-with-lease=refs/heads/{branch}:{tip}",) if tip else ()))
    if outcome != "ok":
        v.refuse(f"the join could not be abandoned ({said}).")
    git(p.root, "tag", "-d", f"claim/{JOIN_CLAIM}", check=False)
    say(f"{branch} abandoned by {who}: nothing landed, the threads keep their branches and "
        f"claims. Here: {_remove_hint(p, branch, force=True)}.")
    return 0


def cmd_join(p: Project, args) -> int:
    _, who = _joiner(p, args)
    for flag, step in (("finish", _join_finish), ("merge", _join_merge), ("close", _join_close),
                       ("abandon", _join_abandon)):
        if getattr(args, flag):
            return step(p, who)
    return _join_start(p, who, args)


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


# A key of a YAML mapping at the start of a line; an entry of a register; the heading of one.
KEY_LINE = re.compile(r"^(?P<indent> *)(?:'[^']*'|\"[^\"]*\"|[^\s#:'\"-][^:]*):(?:\s|$)")
ENTRY_KEY = re.compile(r"^(?P<indent> +)[A-Z]{2,3}-\d+:\s*$")
ENTRY_HEADING = re.compile(r"^###\s+(?:OD|KI)-\d+")


def _whole_keys(lines: list[str]) -> int | None:
    """The indentation of `lines` when they are whole keys of one mapping, each with what is
    indented under it; None otherwise."""
    first = KEY_LINE.match(lines[0]) if lines else None
    if first is None:
        return None
    indent = len(first.group("indent"))
    for line in lines[1:]:
        lead = len(line) - len(line.lstrip(" "))
        if line.strip() and not (lead > indent or (lead == indent and KEY_LINE.match(line))):
            return None
    return indent


def _keys_of(lines: list[str], indent: int) -> dict | None:
    """The keys `lines` hold, read as YAML with every key written once; None if they do not
    read so."""
    try:
        got = S.load("\n".join(line[indent:] for line in lines))
    except (v.yaml.YAMLError, ValueError, TypeError):    # DuplicateKey, or a date like 2026-09-31
        return None
    return got if isinstance(got, dict) else None


def _added(base: list[str], side: list[str]) -> list[str] | None:
    """The lines `side` added to `base`, when it only added: every line of the base still
    there, in its order."""
    ops = difflib.SequenceMatcher(None, base, side, autojunk=False).get_opcodes()
    if any(tag in ("replace", "delete") for tag, *_ in ops):
        return None
    return [line for tag, _, _, j1, j2 in ops if tag == "insert" for line in side[j1:j2]]


def _thread_added(p: dict, branch_ours: bool, start: int, inside_fm: bool,
                  ours_lines: list[str], after: str | None) -> list[str] | None:
    """The main line's side with the lines the thread added after it, in an open register, when
    the main line changed or removed lines of the base, the thread only added, in one place,
    and what it added stands by itself: parking lines, under the level-one heading that starts
    with `# §3`; a whole entry, in the body from its heading to the next heading, `---` or the
    end of the file, or in the front matter a whole key of `entries:`, with the main line's side
    still inside `entries:`. None otherwise, and the hunk is a person's: a line under an entry
    the main line moved would land, with no conflict, under another."""
    thread, main = (p["ours"], p["theirs"]) if branch_ours else (p["theirs"], p["ours"])
    if not p["base"] or main == p["base"]:
        return None
    ops = difflib.SequenceMatcher(None, p["base"], thread, autojunk=False).get_opcodes()
    inserts = [i1 for tag, i1, *_ in ops if tag == "insert"]
    if len(inserts) != 1:
        return None
    added = _added(p["base"], thread)
    if not added:
        return None
    if inside_fm:
        first = ENTRY_KEY.match(added[0])
        if first is None or _whole_keys(added) != len(first.group("indent")):
            return None
        indent = len(first.group("indent"))
        parent = next((l for l in reversed(ours_lines[:start])
                       if l.strip() and len(l) - len(l.lstrip(" ")) < indent), "")
        inside = all(len(l) - len(l.lstrip(" ")) >= indent for l in main if l.strip())
        return main + added if parent.strip() == "entries:" and inside else None
    heading = next((l for l in reversed(ours_lines[:start]) if l.startswith("# ")), "")
    # Still under `# §3` where the thread wrote, and where the result puts it: no level-one
    # heading in the base before that point, nor on the main line's side.
    parked = (heading.startswith("# §3")
              and not any(l.startswith("# ") for l in p["base"][:inserts[0]] + main))
    whole = bool(ENTRY_HEADING.match(added[0])) and (
        after is None or after.startswith("#") or after.strip() == "---")
    return main + added if parked or whole else None


def _front_matter_reads(text: str) -> bool:
    lo, hi = v._front_matter_lines(text)
    if hi <= lo:
        return True
    try:
        S.load("\n".join(text.split("\n")[lo:hi]))
    except (v.yaml.YAMLError, ValueError, TypeError):
        return False
    return True


def resolve(text: str, rel: str, additive: bool = False,
            branch_ours: bool = True) -> tuple[str, int, list[str]]:
    """Resolve the hunks of one file that are mechanical. Returns the text, how many hunks
    are left for a person, and one line per hunk saying what was done with it. Raises
    `Unreadable` for markers it cannot parse, and the file is then left whole for a person.

    `additive` -- a merge of the main line in a project in the additive mode -- adds two rules:
    keys both sides added to one map of the front matter are all kept, and lines a thread only
    added are put back over what the main line changed, where they stand by themselves (see
    `_thread_added`). Either one holds only if the front matter it leaves reads as YAML with
    every key written once; otherwise the file is resolved without them. `branch_ours` says
    which side is the thread: `ours` in `sync`, `theirs` in a join, where the main line is."""
    parts = _hunks(text)
    ours = "\n".join(l for p in parts for l in ([p] if isinstance(p, str) else p["ours"]))
    ours_lines = ours.split("\n")
    lo, hi = v._front_matter_lines(ours)
    names = v.GENERATED_REGIONS.get(rel, (None, ()))[1]
    regions = [(ours[:m.start()].count("\n"), ours[:m.end()].count("\n"))
               for m in v.REGION.finditer(ours) if m.group("name") in names]
    out, left, done, at, ruled = [], 0, [], 0, False
    # What the front matter would read with every hunk left to a person taken from this branch:
    # the check of the two rules, which a hunk with its markers still in would make fail.
    probe: list[str] = []
    register = rel.rsplit("/", 1)[-1] == "OPEN.md"
    for n, p in enumerate(parts):
        if isinstance(p, str):
            out.append(p)
            probe.append(p)
            at += 1
            continue
        start = at
        inside_fm = lo <= start < hi
        indent = _whole_keys(p["ours"]) if additive and inside_fm and not p["base"] else None
        # What the result puts after this hunk: a plain line, the end, or a hunk, whose side in
        # the result is not known yet -- and then a whole entry is not taken as standing alone.
        after = next(((q if isinstance(q, str) else "\0") for q in parts[n + 1:]
                      if not isinstance(q, str) or q.strip()), None)
        thread = (_thread_added(p, branch_ours, start, inside_fm, ours_lines, after)
                  if additive and register else None)
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
        elif (indent is not None and p["theirs"] and _whole_keys(p["theirs"]) == indent
              and (both := _keys_of(p["ours"] + p["theirs"], indent)) is not None
              and len(both) == len(_keys_of(p["ours"], indent) or {})
              + len(_keys_of(p["theirs"], indent) or {})):
            chosen, why, ruled = (p["ours"] + p["theirs"],
                                  "keys both sides added to one map: all kept", True)
        elif thread is not None:
            chosen, why, ruled = (thread, "lines the thread only added, put back over what the "
                                          "main line changed", True)
        else:
            out += [p["open"], *p["ours"], p["base_mark"], *p["base"], THEIRS, *p["theirs"],
                    p["close"]]
            probe += p["ours"]
            left += 1
            at += len(p["ours"])
            done.append(f"line {start + 1}: content, left for a person")
            continue
        out += chosen
        probe += chosen
        at += len(p["ours"])
        done.append(f"line {start + 1}: {why}")
    if ruled and not _front_matter_reads("\n".join(probe)):
        return resolve(text, rel)        # the two rules left keys twice: a person reads it
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


def _settle(p: Project, root: Path, top: Path, where: str, additive: bool,
            branch_ours: bool) -> list[str]:
    """Resolve what is mechanical in the merge in progress in `top`, and stage it: the files
    left for a person. `branch_ours` says which side is the thread -- this branch in `sync`, the
    side merged in at a join."""
    left_files: list[str] = []
    unmerged = git(top, "ls-files", "-u", "-z").stdout
    stages: dict[str, set[str]] = {}
    for row in filter(None, unmerged.split("\0")):
        meta, _, path = row.partition("\t")
        stages.setdefault(path, set()).add(meta.split()[2])
    arts = v.discover(root, p.scan, p.registry, B._Sink())
    generated = {str(x.relative_to(root)).replace("\\", "/")
                 for x in v.build_indices(root, arts)}
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
        ours = git(top, "show", f":2:{path}", check=False).stdout
        theirs = git(top, "show", f":3:{path}", check=False).stdout
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
            resolved, left, done = resolve(text, rel, additive=additive, branch_ours=branch_ours)
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
    return left_files


def _landed_at(p: Project, branch: str) -> str | None:
    """The commit at which a join landed this work branch, when the branch is gone from the
    remote: the `joined:` line of the join's commit on the main line. None otherwise -- a branch
    that was never pushed is not one a join landed, whatever its tip."""
    if git(p.root, "rev-parse", "--verify", "-q", f"refs/remotes/{p.remote}/{branch}",
           check=False).returncode == 0:
        return None
    for line in git(p.root, "log", "--format=%B", p.base, check=False).stdout.splitlines():
        parts = line[len(B.JOINED):].split() if line.startswith(B.JOINED) else []
        if len(parts) == 2 and parts[0] == branch:
            return parts[1]
    return None


def _landed_note(p: Project, branch: str, sha: str) -> str:
    after = git(p.root, "log", "--oneline", f"{sha}..{branch}", check=False).stdout.strip()
    return (f"{branch} was landed by a join, at {sha[:12]}, and deleted from {p.remote}: brought "
            "up to date and pushed, it would come back without its claims. "
            + (f"These commits came after the join, and are not on the main line -- take them "
               f"into a thread of their own, or drop them; that is yours to decide:\n{after}\n"
               if after else "")
            + f"Remove it here: {_remove_hint(p, branch, force=bool(after))}.")


def _remove_hint(p: Project, branch: str, force: bool = False) -> str:
    trees = git(p.root, "worktree", "list", "--porcelain").stdout.split("\n\n")
    path = next((b.splitlines()[0][len("worktree "):] for b in trees
                 if f"branch refs/heads/{branch}" in b.splitlines()), None)
    return ((f"`git worktree remove {path}` and " if path else "")
            + f"`git branch -{'D' if force else 'd'} {branch}`")


def cmd_sync(p: Project, args) -> int:
    branch = p.branch()
    if not branch.startswith(p.prefix):
        v.refuse(f"on {branch}, not on a work branch ({p.prefix}...). `sync` brings a work "
                 "branch up to date; the main line is written only by `join --merge`.")
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
        landed = _landed_at(p, branch) if main_roles(p).get("mode") == "additive" else None
        if landed:
            v.refuse(_landed_note(p, branch, landed))
        if branch[len(p.prefix):].startswith(B.JOIN) and \
                p.held(B.CLAIM_REF).get(JOIN_CLAIM, {}).get("branch") != branch:
            v.refuse(f"{branch} is the branch of a join that is closed or abandoned: pushed again, "
                     f"it would come back with no join. Remove it here: "
                     f"{_remove_hint(p, branch, force=True)}.")
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
        # The two rules of the additive mode are for the main line coming into a thread, not for
        # the thread's own commits from another clone.
        additive = into == p.base and main_roles(p).get("mode") == "additive"
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

        left_files += _settle(p, p.root, top, where, additive, branch_ours=True)
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


# ── What a machine has ───────────────────────────────────────────────────────

# The first version whose plugin brings the hooks: below it a project needs none.
SINCE_HOOKS = (4, 9, 0)


def _semver(text: str) -> tuple[int, ...] | None:
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(text or "").strip())
    return tuple(map(int, m.groups())) if m else None


# The placeholders of the workflows in `ci/`, which a project fills when it copies one.
PLACEHOLDERS = {"OWNER/framework-data-ai": r"[\w.-]+/[\w.-]+", "COMMIT_OR_TAG": r"[\w./-]+"}


def _filled_copy(expected: str, copy: str) -> bool:
    """Whether `copy` is `expected` with its placeholders filled, and nothing else changed."""
    a, b = expected.splitlines(), copy.splitlines()
    if len(a) != len(b):
        return False
    for want, have in zip(a, b):
        if want == have:
            continue
        pattern = re.escape(want)
        for name, value in PLACEHOLDERS.items():
            pattern = pattern.replace(re.escape(name), value)
        if pattern == re.escape(want) or not re.fullmatch(pattern, have):
            return False
    return True


def cmd_doctor(p: Project, args) -> int:
    """What this machine has of what `references/workstation.md` asks: read only and offline.

    It says what the files declare, not what a session has: the settings an organisation
    manages and a plugin loaded with `--plugin-dir` are out of its sight, and it says so. `todo`
    is what the framework needs; `note` is what it recommends, or only tells. Exit 1 when there
    is a `todo`.
    """
    todo: list[str] = []

    def line(ok: bool, text: str, needed: bool = True) -> None:
        say(f"{'ok  ' if ok else 'todo' if needed else 'note'}  {text}")
        if not ok and needed:
            todo.append(text)

    pin = str(v.load_project(p.root).get("framework_version") or "")
    if not pin:
        say("note  the project pins no version in framework.yaml: nothing to compare the plugin with")
    framework = Path(__file__).resolve().parents[3]
    top = Path(git(p.root, "rev-parse", "--show-toplevel").stdout.strip())
    say("Read only and offline: what the files of this machine declare.")

    # The plugin, as Claude Code lists it.
    try:
        r = subprocess.run(["claude", "plugin", "details", "framework-data-ai"],
                           capture_output=True, text=True, timeout=60)
        shown = r.stdout if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        shown = ""
    version = re.search(r"^framework-data-ai\s+(\S+)", shown, re.M)
    hooks = re.search(r"^\s*Hooks\s*\((\d+)\)", shown, re.M)
    if version is None:
        line(False, "`claude plugin details framework-data-ai` gave no version: Claude Code is not "
             "on the PATH, or the plugin is not installed. Install it at the version the project "
             f"pins{', ' + pin if pin else ''}.")
    else:
        have, want = _semver(version.group(1)), _semver(pin)
        older = bool(have and want and have < want)
        line(version.group(1) == pin, f"the plugin installed is {version.group(1)}, and the "
             f"project pins {pin or 'no version'}" + (": older, so its skills and validator do not "
             "know what the project declares" if older else ""), needed=older)
        n = int(hooks.group(1)) if hooks else 0
        line(n >= 2, f"the plugin brings {n} hook(s)" + (": the write guard and the to-do at the "
             "start of a session" if n >= 2 else ", and the write guard and the to-do at the start "
             "of a session are two"), needed=bool(want and want >= SINCE_HOOKS))
    say("      A plugin loaded with `--plugin-dir` replaces the one installed for that session "
        "alone, and is not seen here.")

    # The settings files: the sandbox and the bypass mode, recommended and not required.
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    found: dict[str, tuple[object, Path]] = {}
    for f in (config / "settings.json", top / ".claude" / "settings.json",
              top / ".claude" / "settings.local.json"):      # later ones win, as in Claude Code
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        box = data.get("sandbox") if isinstance(data, dict) else None
        perms = data.get("permissions") if isinstance(data, dict) else None
        for key, holder, field in (("sandbox", box, "enabled"),
                                   ("fallback", box, "allowUnsandboxedCommands"),
                                   ("unavailable", box, "failIfUnavailable"),
                                   ("bypass", perms, "disableBypassPermissionsMode")):
            if isinstance(holder, dict) and field in holder:
                found[key] = (holder[field], f)

    def where(key: str) -> str:
        if key not in found:
            return ""
        local = found[key][1].name == "settings.local.json"
        return f" ({found[key][1]}" + (", which a thread's worktree does not have" if local else "") + ")"
    line(found.get("sandbox", (None,))[0] is True, "the Bash sandbox is "
         + ("declared" if found.get("sandbox", (None,))[0] is True else "not declared")
         + f" in the settings files{where('sandbox')}: recommended, see references/workstation.md",
         needed=False)
    line(found.get("fallback", (None,))[0] is False, "commands outside the sandbox are "
         + ("refused" if found.get("fallback", (None,))[0] is False else "not refused")
         + f"{where('fallback')}: `sandbox.allowUnsandboxedCommands: false` is recommended",
         needed=False)
    line(found.get("unavailable", (None,))[0] is True, "a session whose sandbox cannot start "
         + ("stops" if found.get("unavailable", (None,))[0] is True else "runs Bash with none")
         + f"{where('unavailable')}: `sandbox.failIfUnavailable: true` is recommended",
         needed=False)
    line(found.get("bypass", (None,))[0] == "disable", "the mode that skips the permissions is "
         + ("disabled" if found.get("bypass", (None,))[0] == "disable" else "not disabled")
         + f"{where('bypass')}: `permissions.disableBypassPermissionsMode: disable` is recommended",
         needed=False)
    say("      The settings an organisation manages are not read here.")

    # The folders: one project per parent folder, and the exchange beside the repositories.
    parent = top.parent
    ours = {Path(l[len("worktree "):]).resolve() for l in
            git(top, "worktree", "list", "--porcelain").stdout.splitlines()
            if l.startswith("worktree ")}
    beside = sorted(d for d in parent.iterdir()
                    if d.is_dir() and (d / ".git").exists() and d.resolve() not in ours)
    others = [d.name for d in beside if (d / ".framework").is_dir()]
    line(not others, f"one project in {parent}" if not others else
         f"another project with .framework/ in {parent}: {', '.join(others)}. One project per "
         "parent folder: two would share the exchange")
    say(f"note  repositories beside it: {', '.join(d.name for d in beside if d.name not in others) or 'none'}")
    try:
        sessions = v.yaml.safe_load((p.root / ".framework" / "sessions.yaml").read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeError, v.yaml.YAMLError):
        sessions = {}
    declared = sessions.get("exchange") if isinstance(sessions, dict) else None
    if not declared:
        line(False, "no `exchange:` in .framework/sessions.yaml: a code session has nowhere to "
             "deliver what the documentation should say")
    else:
        place = (p.root / str(declared)).resolve()
        line(place.is_dir(), f"the exchange {declared} is {place}"
             + ("" if place.is_dir() else ", which this machine does not have: create it"))
        line(place == parent / "_scambio", "the exchange is `_scambio` beside the repositories"
             if place == parent / "_scambio" else "the exchange is not `_scambio` beside the "
             "repositories: code sessions, which read no sessions.yaml, do not know it",
             needed=False)

    # The tools.
    pins = {}
    try:
        for row in (framework / "constraints.txt").read_text(encoding="utf-8").splitlines():
            name, _, value = row.split(";")[0].strip().partition("==")
            if value:
                pins[name.lower()] = value.strip()
    except OSError:
        pass
    say(f"note  Python {sys.version.split()[0]}, at {sys.executable}")
    # PyYAML, jsonschema and git it needed to start at all: without them it stopped before
    # this, saying which. Their versions are what is left to tell.
    for name in ("pyyaml", "jsonschema"):
        try:
            have = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            have = "?"
        line(have == pins.get(name, have), f"{name} {have}" + (
            "" if have == pins.get(name, have) else f", and constraints.txt pins {pins[name]}"),
            needed=False)
    say(f"note  {git(p.root, '--version', check=False).stdout.strip()}")

    # The name.
    people = B.names(p.work.get("people"))
    if args.who:
        line(not people or args.who.strip() in people, f"`{args.who.strip()}` is "
             + ("" if not people or args.who.strip() in people else "not ")
             + f"among the people of {B.WORK}")
    else:
        say(f"note  the names `--who` takes: {', '.join(sorted(people)) or 'any, no people declared'}")

    # The workflow of the branches, as the pinned version has it.
    flows = top / ".github" / "workflows"
    branches, request = flows / "branches.yml", flows / "pull-request.yml"
    if request.is_file():
        line(False, "pull-request.yml is in .github/workflows/" + (
            ", beside branches.yml: copy one or the other" if branches.is_file() else
            ", and it has no `main` job: a project with work.yaml copies ci/branches.yml in its "
            "place"))
    if not branches.is_file():
        line(False, "no .github/workflows/branches.yml: nothing sees what reaches the main line "
             "outside a pull request or a join")
    else:
        copy = branches.read_text(encoding="utf-8")
        import migrate as M                  # the framework's history, read as `migrate.py` reads it
        sha, why = M.commit_declaring(pin, framework) if pin else (None, "the project pins no version")
        shown = git(framework, "show", f"{sha}:ci/branches.yml", check=False) if sha else None
        if shown is None or shown.returncode:
            line(False, f"branches.yml cannot be compared with the one of {pin or 'the pin'}: "
                 f"{why or 'that version has no ci/branches.yml'}", needed=False)
        elif any(name in copy for name in PLACEHOLDERS):
            line(False, "branches.yml still has OWNER/framework-data-ai or COMMIT_OR_TAG: fill them")
        else:
            same = _filled_copy(shown.stdout, copy)
            line(same, f"branches.yml is the one of {pin}, its placeholders filled" if same else
                 f"branches.yml differs from the one of {pin}: copy ci/branches.yml again and "
                 "fill its placeholders")
    return 1 if todo else 0


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
    o.add_argument("--branch", help="the name after the prefix: od-042; in the additive mode, with "
                                    "no element, it becomes parcheggio-<name>; not with --thread, "
                                    "whose branch is named after the thread")
    o.add_argument("--thread", help="in the additive mode: the thread the to-do computes, taken "
                                    "whole")
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

    d = sub.add_parser("delegate", help="let a person decide as an admin, until revoked")
    d.add_argument("--to", required=True, help="the person, among the people")
    d.add_argument("--who", required=True, help="the admin giving it")
    j = sub.add_parser("join", help="in the additive mode: land the threads that are ready")
    j.add_argument("threads", nargs="*", help="the threads to merge; all those ready if none")
    j.add_argument("--who", required=True, help="an admin, a deputy or a delegate")
    j.add_argument("--no-threads", action="store_true",
                   help="a join with no thread: for work.yaml, an adoption, the policy, annotations, "
                        "a release, approvals")
    step = j.add_mutually_exclusive_group()
    step.add_argument("--finish", action="store_true", help="drop _filoni, commit with the trailer, push")
    step.add_argument("--merge", action="store_true", help="merge the join into the main line, push, close")
    step.add_argument("--close", action="store_true", help="release what a join landed")
    step.add_argument("--abandon", action="store_true", help="drop a join that did not land")
    rv = sub.add_parser("revoke", help="take a delegation back, or give one's own up")
    rv.add_argument("--to", required=True, help="the person holding it")
    rv.add_argument("--who", required=True, help="an admin, or the delegate")
    d = sub.add_parser("doctor", help="what this machine has of what references/workstation.md "
                                      "asks; read only and offline")
    d.add_argument("--who", help="the name you work under, to check it is among the people")

    args = ap.parse_args()
    p = Project(args)
    return {"open": cmd_open, "reserve": cmd_reserve, "list": cmd_list,
            "release": cmd_release, "sync": cmd_sync, "delegate": cmd_delegate,
            "revoke": cmd_revoke, "join": cmd_join, "doctor": cmd_doctor}[args.command](p, args)


if __name__ == "__main__":
    sys.exit(main())
