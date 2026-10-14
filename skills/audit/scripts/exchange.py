#!/usr/bin/env python3
"""What waits in the exchange between sessions, and for how long.

    python3 exchange.py --root path/to/documentation
    python3 exchange.py --root . --json

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
    4. the resources of elements done still there, with the command that removes each one,
       which is the removal the documentation session proposes and runs only on approval;
    5. the closing declarations in `sessioni/` that no element holds, with their age;
    6. the findings `validate.py` reports on the same place, `EXC001`-`EXC007`, with the ones the
       project has annotated in `.framework/expected-findings.yaml` apart, as it prints them.

"For how long" is the oldest modification among the delivered files, read off the disk: a copy
that does not preserve times resets it. Nothing is moved, deleted or written, and a row of
`risorse.md` that carries the value of a credential is never repeated: `EXC005` says where it is.

WHAT IT REFUSES, WITH EXIT 2. A project that declares no exchange, or an `--root` that is not a
directory. A declared exchange that is not on this machine is not a refusal: it is said, and
the exit is 0, because nothing waits in a place that does not exist yet.

Requires the same environment as `validate.py`, whose helpers it uses.
"""

from __future__ import annotations

import argparse
import json
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


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description="What waits in the exchange between sessions")
    ap.add_argument("--root", default=".", type=Path,
                    help="the documentation repository, whose .framework/sessions.yaml declares "
                         "the exchange")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

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

    def in_history(sha: str) -> bool:
        r = v._git(["merge-base", "--is-ancestor", sha, "HEAD"], root)
        return r is not None and r.returncode == 0

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
    resources = [(e, r) for e in ex.elements if X.closed(states, e.ident)
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
