#!/usr/bin/env python3
"""What waits in the exchange between sessions, and for how long.

    python3 exchange.py --root path/to/documentation
    python3 exchange.py --root . --json
    python3 exchange.py --root <thread worktree> integrate CHG-021

THE QUESTION IT ANSWERS. A project that declares `exchange:` in `.framework/sessions.yaml` keeps
there what its sessions hand each other: a brief going to a code session, a verification, the text of
a merge request, evidence, a contribution policy coming back. Each element has a folder named by
its identifier in `in-arrivo/` until the documentation session has integrated it, and in
`integrati/` afterwards, with an `INTEGRATO` file saying where each part went. This lists, in
the order they are worth reading:

    1. the elements the documents already call done whose folder is still in `in-arrivo/`:
       integrated and not moved, or waiting behind a state that says they are done;
    2. the deliveries waiting for integration, the oldest first, with how many days;
    3. the elements with a brief and nothing delivered yet: at a code session;
    4. below 4.12.0 pinned, the resources of elements done still there, with the command that
       removes each one, which is the removal the documentation session proposes and runs only
       on approval; from 4.12.0 pinned, or no version that reads, they belong to whoever
       created them, `EXC004` is retired, and this section is not listed;
    5. the closing declarations in `sessioni/` that no element holds, with their age;
    6. the findings `validate.py` reports on the same place, `EXC001`-`EXC007`, with the ones the
       project has annotated in `.framework/expected-findings.yaml` apart, as it prints them.

"For how long" is the oldest modification among the delivered files, read off the disk: a copy
that does not preserve times resets it. The listing moves, deletes and writes nothing, and a row
of `risorse.md` that carries the value of a credential is never repeated: `EXC005` says where it
is.

`integrate <ID>`, SINCE 4.12.0, IS THE CLOSING OF ONE ELEMENT, done by hand before. Once the
documentation has integrated what `in-arrivo/<ID>/` delivered, and committed it, it moves the
folder to `integrati/` and writes `INTEGRATO` with the commit -- `HEAD` of `--root`, the
thread's worktree in the additive mode, or `--commit` -- the day, and the place of each part:
`verifica.md`, `mr-link.txt` and `evidenze/` the change's verification, where they are cited;
`documentazione.md` and `contribution-policy.json` the folder that holds them in the
documentation at that commit, `_filoni/<slug>/consegne/<ID>/`. A change `withdrawn` integrates
nothing: each part is said dropped, and the commit named holds the withdrawal, as the commit
that withdrew it does. Left for a person to place, with `EXC003` saying so until
`parts` does: `mr.md`; what a verification cites for an entry, which has no verification
section; and a policy outside the additive mode, which goes to `.framework/`, where nothing
here can tell the one delivered from one already there. It refuses, with exit 2 and nothing
moved, an element already in `integrati/` -- a second integration joins the folders by hand, one
block more in `INTEGRATO` --, a name the folder should not hold, uncommitted changes in `--root`
when the commit is its `HEAD`, a `--commit` outside the history of that `HEAD`, a change
withdrawn in the working tree and not at the commit, a verification delivered for a change
whose `## Verification` is empty at the commit -- what `templates/CHG.md` puts there, its
sentence and a comment, is not a verification --, and a delivered file the documentation does
not hold at the commit.

WHAT IT REFUSES, WITH EXIT 2. A project that declares no exchange, or an `--root` that is not a
directory. A declared exchange that is not on this machine is not a refusal: it is said, and
the exit is 0, because nothing waits in a place that does not exist yet.

Requires the same environment as `validate.py`, whose helpers it uses.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate as v  # noqa: E402  (the validator's helpers, not its main)

X = v._exchange


def ago(day: date, today: date) -> str:
    n = (today - day).days
    return "today" if n <= 0 else "1 day ago" if n == 1 else f"{n} days ago"


def waited(day: date, today: date) -> str:
    n = (today - day).days
    return "since today" if n <= 0 else "1 day" if n == 1 else f"{n} days"


# Where each delivered part goes by default, when it is cited by the element's verification.
CITED = {"verifica.md": "§Verification", "mr-link.txt": "§Verification",
         "evidenze": "§Verification, cited"}
# Delivered parts that the documentation holds as files: their place is where they are.
HELD = ("documentazione.md", "contribution-policy.json")


def _verification_written(body: str | None) -> bool:
    """Whether a change's `## Verification` holds anything but what `templates/CHG.md` puts
    there: comments, rules and the template's own sentence are not a verification."""
    if body is None:
        return False

    def bare(text: str) -> list[str]:
        text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
        return " ".join(line for line in text.splitlines()
                        if not re.fullmatch(r"\s*(?:-{3,}|\*{3,}|_{3,})?\s*", line)).split()

    def section(text: str) -> str | None:
        lines = text.splitlines()
        span = next((s for s in v.locate_sections(text)
                     if s.level == 2 and s.title == "Verification"), None)
        return None if span is None else "\n".join(lines[span.heading_line:span.end_line])

    own = section(body)
    if own is None:
        return False
    template = section(v.parse_front_matter(
        (v.FRAMEWORK / "templates" / "CHG.md").read_text(encoding="utf-8"))[1] or "")
    return bool(bare(own)) and bare(own) != bare(template or "")


def integrate(root: Path, path: Path, shown: str, ident: str, commit: str | None,
              report: v.Report, states: dict, places: dict[str, str]) -> int:
    """Move `in-arrivo/<ident>/` to `integrati/` and write its `INTEGRATO`. Exit 2, with
    nothing moved, on anything that would leave the integration unreadable."""
    if not X.ELEMENT.match(ident):
        v.refuse(f"{ident!r} is not an element's identifier, as `CHG-021`.")
    folder, target = path / X.INCOMING / ident, path / X.INTEGRATED / ident
    if not folder.is_dir():
        v.refuse(f"{folder}: no such folder. Nothing of {ident} waits in `{X.INCOMING}/`.")
    if target.exists():
        v.refuse(f"{target} already holds an integration of {ident}. A second one joins the "
                 "folders by hand, one block more in `INTEGRATO`, as "
                 "`references/contributions.md` says: nothing is moved.")
    el = X._element(X.Exchange(path, shown), X.INCOMING, folder, report)
    strays = [f for f in report.findings if f.code == "EXC006"]
    if strays:
        v.refuse("the folder holds names an element folder does not: "
                 + "; ".join(f.path for f in strays) + ". Move them into `evidenze/` or remove "
                 "them first: nothing is moved.")
    if commit is None:
        dirty = v._git(["status", "--porcelain", "--untracked-files=no"], root)
        if dirty is None or dirty.returncode != 0:
            v.refuse(f"{root} is not a git repository that can be read: the commit that "
                     "integrated the material cannot be named.")
        if dirty.stdout.strip():
            v.refuse(f"{root} has changes not committed. Commit the integration first: "
                     "`INTEGRATO` names the commit that holds it.")
        commit = "HEAD"
    sha = v._git(["rev-parse", "--verify", "-q", f"{commit}^{{commit}}"], root)
    if sha is None or sha.returncode != 0:
        v.refuse(f"{commit} is not a commit of {root}.")
    sha_full = sha.stdout.strip()
    ancestor = v._git(["merge-base", "--is-ancestor", sha_full, "HEAD"], root)
    if ancestor is None or ancestor.returncode != 0:
        v.refuse(f"{commit} is not in the history of {root}'s HEAD: `INTEGRATO` would name an "
                 "integration nobody reading this branch can find.")
    listed = v._git(["ls-tree", "-r", "--name-only", sha_full], root)
    tracked = set(listed.stdout.split("\n")) if listed is not None else set()
    # A policy outside the additive mode goes to `.framework/`, where an older one may already
    # be, and the committed policy may rightly differ from the one delivered: nothing here can
    # tell that it was carried, so a person places it. In the mode it is in the `consegne/` of
    # the thread or of the join. A `work.yaml` that does not read is a refusal, exit 2.
    additive = False
    if "contribution-policy.json" in el.delivered:
        try:
            additive = (v.load_work(root, report) or {}).get("mode") == "additive"
        except SystemExit as e:          # `load_work` stops the validator with exit 1
            v.refuse(f"{e.code} Nothing is moved.")
    # What the documents say of the element: a change withdrawn integrates nothing, and each
    # part is said dropped (`references/contributions.md`); an entry has no verification
    # section to cite, so what a verification cites there is a person's to place.
    change = ident.startswith("CHG-")
    rel = places.get(ident) if change else None
    # The change as the commit `INTEGRATO` names holds it: `<commit>:<path>` reads from the top
    # of the repository. None where the commit does not hold it.
    read = (v._git(["show", f"{sha_full}:{v._branches.prefix(root)}{rel}"], root)
            if rel else None)
    then_meta, then_body = (v.parse_front_matter(read.stdout)[:2]
                            if read is not None and read.returncode == 0 else (None, None))
    withdrawn = change and X.state(states, ident) == "withdrawn"
    if withdrawn and (then_meta or {}).get("status") != "withdrawn":
        # Withdrawn in the working tree, and so at the commit `INTEGRATO` names, which is the one
        # that withdrew it (`references/contributions.md`), never one before it.
        v.refuse(f"{ident} is withdrawn in {root} and not at {sha_full[:12]}: `INTEGRATO` "
                 "names the commit that withdrew it. Commit the withdrawal first, or name "
                 "that commit with `--commit`. Nothing is moved.")
    cited = [n for n in el.delivered if n in CITED]
    if change and not withdrawn and cited and not _verification_written(then_body):
        # `INTEGRATO` says the change's verification holds what was delivered: a section still
        # empty at the commit would make it say what nobody wrote.
        where = f"{rel} at {sha_full[:12]}" if then_body is not None else \
            f"the documentation at {sha_full[:12]}, which does not hold {ident}"
        v.refuse(f"{ident} has no verification written under `## Verification` in {where}, "
                 "and " + ", ".join(f"`{n}`" for n in cited) + " would be said integrated there. "
                 "Write the verification from `verifica.md` into the change and commit it "
                 "first -- on a thread that is a text of its own -- or name with `--commit` "
                 "the commit that holds it. Nothing is moved.")
    parts: dict[str, str] = {}
    by_hand: list[str] = []
    missing: list[str] = []
    for name in el.delivered:
        key = name + ("/" if X.DELIVERED.get(name) == "dir" else "")
        if withdrawn:
            parts[key] = f"dropped: {ident} was withdrawn"
        elif name in CITED:
            if change:
                parts[key] = f"{ident} {CITED[name]}"
            else:
                by_hand.append(name)
        elif name in HELD:
            held = sorted(t[: -len(name)] for t in tracked
                          if t.endswith(f"/consegne/{ident}/{name}"))
            if len(held) == 1:
                parts[name] = held[0]
            elif name == "contribution-policy.json" and not additive:
                by_hand.append(name)
            else:
                missing.append(name)
        else:
            by_hand.append(name)
    if missing:
        v.refuse(f"the documentation at {sha_full[:12]} does not hold "
                 + ", ".join(f"`{n}`" for n in missing) + f" of {ident} in one place: copy it "
                 f"to `_filoni/<slug>/consegne/{ident}/` and commit it first; where a join has "
                 "already landed that "
                 "folder, which the main line no longer holds, name with `--commit` the commit "
                 "of the thread or of the join that does. Nothing is moved.")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(folder), str(target))
    lines = [f'commit: "{sha_full[:12]}"', f"date: {date.today().isoformat()}",
             "parts:" + ("" if parts else " {}")]
    lines += [f"  {k}: {where}" for k, where in parts.items()]
    (target / X.MARK).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{ident}: moved to {target}, with `{X.MARK}` naming {sha_full[:12]}.")
    for k, where in parts.items():
        print(f"  {k}: {where}")
    for name in by_hand:
        print(f"  {name}: not placed. Write in `parts` where it went; `EXC003` says it until "
              "then.")
    return 0


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description="What waits in the exchange between sessions")
    ap.add_argument("--root", default=".", type=Path,
                    help="the documentation repository, whose .framework/sessions.yaml declares "
                         "the exchange")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("command", nargs="?", choices=["integrate"],
                    help="integrate: move one element to integrati/ and write its INTEGRATO")
    ap.add_argument("ident", nargs="?", help="the element to integrate, as CHG-021")
    ap.add_argument("--commit", help="with integrate: the commit that integrated it, when it "
                                     "is not HEAD of --root")
    args = ap.parse_args()
    if args.command == "integrate" and not args.ident:
        ap.error("integrate takes the element's identifier")
    if args.command is None and (args.ident or args.commit):
        ap.error("an identifier and --commit go with integrate")

    root = args.root.resolve()
    if not root.is_dir():
        v.refuse(f"{root}: no such directory. `--root` is the documentation repository.")
    project = v.load_project(root)
    shown, path = v.load_exchange(root)  # stops on an `exchange` that is not a place
    if path is None:
        v.refuse(f"{root}: no `exchange` declared in {v.SESSIONS}. Without one, sessions hand "
                 "each other material the way they did before, and there is nothing here to "
                 "list. To declare one, write `exchange: ../_scambio` there, relative to the "
                 "root of the repository.")
    if args.command == "integrate":
        registry = v.yaml.safe_load(v.REGISTRY.read_text(encoding="utf-8"))
        config, _ = v.load_config(project)
        arts = v.discover(root, v.load_scan(registry, project), registry, v.Report(config))
        return integrate(root, path, shown, args.ident, args.commit, v.Report(config),
                         X.standing(arts), {a.id: a.rel for a in arts
                                            if a.type == "change-contract"
                                            and isinstance(a.id, str)})
    if not path.is_dir():
        if args.json:
            print(json.dumps({"exchange": str(path), "declared": shown, "present": False},
                             indent=2, ensure_ascii=False))
        else:
            print(f"Exchange: {path} (framework.yaml: {shown}) is not on this machine. Nothing "
                  "waits in it: the first brief written by `cycle` creates it.")
        return 0

    registry = v.yaml.safe_load(v.REGISTRY.read_text(encoding="utf-8"))
    config, _ = v.load_config(project)
    arts = v.discover(root, v.load_scan(registry, project), registry, v.Report(config))
    references = v.ReferenceIndex(arts, registry)
    report = v.Report(config)
    repo = v.Repository.open(root)
    ex = X.read(path, shown, report)
    states = X.standing(arts)

    # As the validator reads it: in the additive mode an integration is committed on a thread's
    # branch, in no history of HEAD from the main checkout until the join, and the work branches
    # of this clone hold it.
    try:
        work = v.load_work(root, v.Report(config)) or {}
    except SystemExit as e:              # `load_work` stops on a file that does not read
        work = {}
        print(f"{e.code} The integrations committed on the work branches are not looked for: "
              "an element integrated on a thread may be listed as not integrated.",
              file=sys.stderr)
    prefix = str(work.get("branch_prefix") or "work/")

    def in_history(sha: str) -> bool:
        r = v._git(["merge-base", "--is-ancestor", sha, "HEAD"], root)
        if r is not None and r.returncode == 0:
            return True
        if work.get("mode") != "additive":
            return False
        held = v._git(["for-each-ref", "--contains", sha, "--format=%(refname)", "refs/heads/",
                       "refs/remotes/"], root)
        names = held.stdout.split() if held is not None and held.returncode == 0 else []
        return any(n.startswith(f"refs/heads/{prefix}")
                   or (n.startswith("refs/remotes/") and n.split("/", 3)[-1].startswith(prefix))
                   for n in names)

    X.check(ex, references.known, states, v.projects_folder(root),
            in_history if repo is not None and repo.has_head else None, report)
    if repo is not None:
        repo.close()
    # The same join `validate.py` makes, on the same pair, for these codes only: the rest of
    # the file is about findings this command does not produce.
    annotations, _, _ = v.load_annotations(root)
    for row in annotations:
        for f in report.findings:
            if (f.code, f.path) == (row["code"], row["path"]):
                f.accepted = {"reason": row["reason"], "clears_when": row["clears_when"]}
    standing = [f for f in report.findings if f.accepted]
    findings = [f for f in report.findings if not f.accepted]

    today = date.today()
    incoming = [e for e in ex.elements if e.stage == X.INCOMING]
    closed = [e for e in incoming if X.closed(states, e.ident)]
    waiting = sorted((e for e in incoming if e not in closed and e.delivered),
                     key=lambda e: (e.oldest or today, e.ident))
    working = [e for e in incoming if e not in closed and not e.delivered]
    # The documentation's to propose only where `EXC004` still reports, below 4.12.0 pinned.
    resources = [] if report.level("EXC004") == v.RETIRED else [
        (e, r) for e in ex.elements if X.closed(states, e.ident)
        for r in e.resources if r.present]

    def row(e) -> dict:
        return {"id": e.ident, "state": X.state(states, e.ident), "delivered": e.delivered,
                "since": e.oldest.isoformat() if e.oldest else None,
                "brief": e.brief.isoformat() if e.brief else None, "path": str(e.path)}

    if args.json:
        print(json.dumps({
            "exchange": str(path), "declared": shown, "present": True,
            "done_in_incoming": [row(e) for e in closed],
            "waiting": [row(e) for e in waiting],
            "at_a_code_session": [row(e) for e in working],
            "resources_to_remove": [{"id": e.ident, "kind": r.kind, "where": r.shown,
                                     "command": r.shown_command} for e, r in resources],
            "declarations": [{"path": str(p), "since": d.isoformat()}
                             for p, d in ex.declarations],
            "findings": [f.as_json() for f in report.findings],
        }, indent=2, ensure_ascii=False))
        return 0

    print(f"Exchange: {path} (framework.yaml: {shown})")

    def section(title: str, items: list) -> bool:
        if items:
            print(f"\n-- {title} ({len(items)}) " + "-" * 30)
        return bool(items)

    if section("DONE IN THE DOCUMENTS, STILL IN in-arrivo/", closed):
        print("   integrated and not moved, or waiting behind a state that says done")
        for e in closed:
            print(f"   {e.ident:<9} {X.state(states, e.ident):<12} "
                  f"{', '.join(e.delivered) or 'nothing delivered'}"
                  + (f", delivered {ago(e.oldest, today)}" if e.oldest else ""))
    if section("WAITING FOR INTEGRATION", waiting):
        for e in waiting:
            print(f"   {e.ident:<9} {X.state(states, e.ident):<12} {', '.join(e.delivered)}"
                  + (f", waiting {waited(e.oldest, today)}" if e.oldest else ", all empty"))
    if section("AT A CODE SESSION: nothing delivered yet", working):
        for e in working:
            what = f"brief written {ago(e.brief, today)}" if e.brief else "no brief"
            print(f"   {e.ident:<9} {X.state(states, e.ident):<12} {what}")
    if section("RESOURCES OF ELEMENTS DONE, TO PROPOSE FOR REMOVAL", resources):
        print("   run each one only on the person's approval, then delete its row")
        for e, r in resources:
            print(f"   {e.ident:<9} {r.kind}: {r.shown}\n             {r.shown_command}")
    if section("CLOSING DECLARATIONS IN sessioni/", ex.declarations):
        print("   removed once what they declare not committed is committed")
        for p, d in ex.declarations:
            print(f"   {p.name}  written {ago(d, today)}")
    if section("FINDINGS", findings):
        for f in findings:
            print(f.line())
    if section("EXAMINED AND LEFT STANDING", standing):
        for f in standing:
            print(f.line())
    if not (closed or waiting or working or resources or ex.declarations or report.findings):
        print("\nNothing waits.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
