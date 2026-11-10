#!/usr/bin/env python3
"""What waits in the exchange between sessions, and for how long.

    python3 exchange.py --root path/to/documentation
    python3 exchange.py --root . --json
    python3 exchange.py --root <thread worktree> integrate CHG-021
    python3 exchange.py --root <thread worktree> code CHG-021 --repo ../app [--base <branch>] [--join-base [auto|merge|rebase]]
    python3 exchange.py --root <thread worktree> code CHG-021 --launch
    python3 exchange.py --root <thread worktree> code CHG-021 --resume [--allow <file>]... [--reply <file>]
    python3 exchange.py --root <thread worktree> code CHG-021 --status

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
here can tell the one delivered from one already there. Since 4.13.0 it also places
`documentazione.md` outside the additive mode, written into the documents by the commit it
names; on the parking branch of a hotfix it takes the verification, `mr-link.txt` and
`evidenze/` where the branch's delivery folder holds them, while the change has no verification
yet or is not written; and an element already in `integrati/` -- a change asked for after a
launch closed is a new launch -- is joined there, one block more in `INTEGRATO`, a part
delivered again taking the place of the one with its name and `evidenze/` adding up, a file
whose name is taken getting the number of its block. The launch file goes with the folder and
says the launch closed. It refuses, with exit 2 and nothing moved, below 4.13.0 pinned an
element already in `integrati/` -- a second integration joins the folders by hand, one block
more in `INTEGRATO` --, a name the folder should not hold, uncommitted changes in `--root`
when the commit is its `HEAD`, a `--commit` outside the history of that `HEAD`, a change
withdrawn in the working tree and not at the commit, a verification delivered for a change
whose `## Verification` is empty at the commit -- what `templates/CHG.md` puts there, its
sentence and a comment, is not a verification --, and a delivered file the documentation does
not hold at the commit.

`code <ID>`, SINCE 4.13.0, IS THE CODE SESSION LAUNCHED BY THE DOCUMENTATION SESSION, which
runs it and answers what is its to answer: the person never opens Claude in the code
repository. Four forms, each one call:

    --repo    prepares: the code session's worktree `<repository>-<id>` beside the code
              repository, on its branch -- the thread's in the additive mode, the parking
              branch of a hotfix, `<id>` outside the mode --, from `--base` or the remote's
              default branch, after a fetch; the files the brief links, from the main
              checkout; their rows in `risorse.md`; the launch file. It compares the branch
              with the remote's: behind or level is a new launch on the same branch, ahead is
              brought forward and its commits said to the code session as not its own,
              diverged is said with both sides and the two commands -- join, a rebase of the
              local commits on the remote's, or keep the remote -- that the documentation
              session runs on the person's choice. It says how far the branch is behind its
              base -- `--base`, or else the start an earlier launch of the change recorded,
              or else the remote's default branch --; with `--join-base`, on the person's
              yes, it joins the base into the branch -- a merge, with the person's `rerere`
              off --, the base's commits said to the code session as not its own, and a merge
              stopped on conflicts given to the code session first, whose concluding commit
              is the documentation session's, as the step of a rebase (V-5), and pushed at
              once: refused there, the remote is kept and the base joined again, never the
              two joined by a rebase (V-6). Where the code is merged by a rebase --
              `merge_method: rebase` in the additive mode, or `--join-base rebase` --, the
              branch's commits are re-applied on the base instead, with the steps of a
              rebase, and its push is forced, with lease, on the person's yes (V-7); not
              pushed while the remote moved, or refused, the same: the remote kept and the
              branch re-applied again. `--join-base` alone, or `auto`, takes the way from
              `merge_method`; `merge` or `rebase` names it, against the key too. Re-applied,
              the commits that were on the branch before -- the code session's and others' --
              have new ids, which the code session is told. This is for where the forge
              wants the branch up to date with its base, or its merge request conflicts with
              it. A launch closed by the integration is prepared again with its brief back in
              `in-arrivo/<id>/`. A merge in progress that no `--join-base` made is the
              person's to conclude or abort first. It stops there: the push and the
              preparation the brief names are the documentation session's commands, in view.
    --launch  runs `claude -p` in the worktree, under `dontAsk`, with the plugin this command
              runs from, the delivery folder, and what the code session may do without asking:
              read, write -- the guard is the limit --, the reviser, the git commands that
              read, `git add`, the validator and the brief's tests. Never a credential or a
              provider of the environment: it runs on the person's subscription, is refused
              where Claude Code's settings set one, and is stopped at its start when its
              first event says otherwise. Under a sandbox the sandbox does not approve a
              command by itself. A rebase in progress, or a merge of the base, is the first
              thing the code session is given; the join, each `--continue` and the commit
              that concludes the merge are printed with the person's `rerere` off, so that no
              resolution of another rebase or merge comes back by itself.
    --resume  the same session, with the rule the person approved now, written whole, for
              this run only (`--allow`, a file), or the answer to its question (`--reply`), or
              neither: after the documentation session ran `git rebase --continue`, or the
              commit that concludes the merge of the base, or after a stop with nothing to
              approve or answer.
    --status  whether it runs, and where it stopped; a run whose end was never written, its
              process gone, is read from its output.

Each run ends on a stop, said in a few lines and written into the launch file, exit 0: `negata`
(each action denied with the rule that would grant it; a block of the framework's guard, or of a
hook of the person's, said apart; `git rebase --continue`, and with a merge of the base in
progress the commit that concludes it -- `git commit` or `git merge --continue` --, which the
documentation session runs on the person's yes and never grants, said with its command; a push
or a merge request, never the code session's, said apart and no question, and with other
commands on its line no rule), `account` (a limit or a credential of the account), `domanda`
(the last entry of `domande.md`, said with any stop of its run), `consegna` (the fixed names
delivered since the launch began, never with a rebase or a merge of the base in progress) and
`fine` (with an error of the run, if one ended it). The
launch file, `sessione-codice.json`, holds no value: one beside a name is withheld. The output of
a run waits in the person's outputs folder, the person's alone, until its stop is written.
`--allow` takes only the rules the last stop proposed, compared as the launch file keeps them:
with their values withheld, so that a rule differing from one in a value alone passes. A resume
that finds a stop nobody read says it and resumes nothing. `code` refuses, exit 2 and nothing
launched: a project below 4.13.0, no exchange or no brief, a change not approved
(`--no-chg "hotfix <reference>"` launches a hotfix whose change is not written yet, and is
refused for one written), in the additive mode a change the thread of `--root` does not hold,
or a hotfix launched from outside its parking branch, a `--repo` that is not a repository
beside the documentation, or another repository than the launch's before, a repository with no
`origin`, or whose `origin/HEAD` is not set and no `--base` given, a `--base` that does not
exist, a launch running, a branch or a folder that is not this launch's, a worktree not on its
branch, at `--launch`, `--resume` and `--status` a launch file not as this command writes it --
its shape, a session or a commit that is no id -- (the first call writes a new one in its
place, without its history; the listing says it, and `integrate` moves it as it is), a launch
closed at `--launch`, `--resume` and `--status`, a branch that diverges from its remote at
`--launch` with no choice made, a rule `--allow` was not proposed, a resume after a
`--continue` that did not move the rebase, or after it was aborted and the branch holds its own
commits again without the remote's, or, re-applied on the base, without the base, a resume
after a commit that did not conclude the merge of
the base, or after the merge was aborted and the branch does not hold the base, `--join-base`
with a rebase or a merge in progress or a branch diverged from its remote, a join of the base
that fails short of a conflict (aborted, nothing else changed), at the first call and at
`--launch` a merge in progress that no `--join-base` made, `claude` not found, at
`--launch` and `--resume` a settings file of Claude Code's -- the organisation's, the person's,
the worktree's -- whose `env` sets a provider, an address, a key or a token, or that sets an
`apiKeyHelper`, or that opens and does not read (each said with its file and line, and by the
first call ahead; one the person cannot open is skipped, as the code session, the person's
process, cannot open it either), and Windows outside WSL, where asking whether a process runs
ends it. A run is told from a process that took its number after a restart by its session, on
its command line.
`integrate` refuses an element whose last run is running or was never read, and on Windows
outside WSL one whose last run has not ended: `--status`, under WSL, Linux or macOS, says which.

WHAT IT REFUSES, WITH EXIT 2. A project that declares no exchange, or an `--root` that is not a
directory. A declared exchange that is not on this machine is not a refusal: it is said, and
the exit is 0, because nothing waits in a place that does not exist yet.

Requires the same environment as `validate.py`, whose helpers it uses.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path, PurePosixPath

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
    # A run of the code session not ended, or whose stop nobody read: the launch file would be
    # moved under it, and its output left behind.
    try:
        launched = json.loads((folder / X.LAUNCH).read_text(encoding="utf-8"))
        last = (launched["lanci"][-1].get("tranche") or [{}])[-1]
        session = launched["lanci"][-1].get("sessione")
    except (OSError, ValueError, RecursionError, KeyError, IndexError, TypeError,
            AttributeError):
        last, session = {}, None
    if isinstance(last, dict) and last.get("inizio") and not last.get("fine"):
        alive = _alive(last.get("processo"), session if isinstance(session, str) else None,
                       last.get("uscita"))
        if alive is None:                  # Windows outside WSL, where `code` does not run
            said = ("has not ended, and whether it runs is not told on Windows outside WSL: "
                    f"`code {ident} --status`, under WSL, Linux or macOS, says it first")
        else:
            said = (("is running" if alive else "ended and its stop was not read")
                    + f": `code {ident} --status` says it first")
        v.refuse(f"a run of the code session of {ident} {said}. Nothing is moved.")
    # Since 4.13.0 pinned, as every rule follows the version a project pins: a second
    # integration of the same element -- a change asked for after a launch closed is a new
    # launch, R-2 -- is joined here, one block more in `INTEGRATO`; below, by hand.
    since = v.rules_hold(v.load_project(root), CODE_SINCE)
    blocks: list = []
    if target.exists() and not since:
        v.refuse(f"{target} already holds an integration of {ident}. A second one joins the "
                 "folders by hand, one block more in `INTEGRATO`, as "
                 "`references/contributions.md` says: nothing is moved.")
    if target.exists():
        try:
            blocks = X._blocks(v.yaml.safe_load((target / X.MARK).read_text(encoding="utf-8"))) \
                or []
        except (OSError, v.yaml.YAMLError, UnicodeError):
            blocks = []
        if not blocks:
            v.refuse(f"{target} is in `{X.INTEGRATED}/` without an `{X.MARK}` that reads: "
                     "nothing says what the first integration placed, and nothing is moved.")
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
    # Since 4.13.0 `documentazione.md` is read the same way: outside the mode the documentation
    # session writes it into the documents (R-4). Elsewhere the mode is read only for the
    # parking branch of a hotfix, and a `work.yaml` that does not read means none.
    additive, work = False, {}
    needs_mode = "contribution-policy.json" in el.delivered or (
        since and "documentazione.md" in el.delivered)
    try:
        work = v.load_work(root, report) or {}
    except SystemExit as e:              # `load_work` stops the validator with exit 1
        if needs_mode:
            v.refuse(f"{e.code} Nothing is moved.")
    additive = work.get("mode") == "additive"
    # The parking branch of a hotfix (R-14), since 4.13.0: what the change's verification will
    # cite is kept in the branch's delivery folder until the join writes the change, or its
    # verification.
    branch = v._git(["rev-parse", "--abbrev-ref", "HEAD"], root)
    parking = since and additive and branch is not None and branch.returncode == 0 and \
        branch.stdout.strip().startswith(
            f"{work.get('branch_prefix') or 'work/'}{v._branches.PARKING}hotfix-")
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
    kept = parking and not _verification_written(then_body)
    if change and not withdrawn and cited and not kept and not _verification_written(then_body):
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
        elif name in CITED and kept:
            whole = X.DELIVERED.get(name) == "dir"
            inside = f"/consegne/{ident}/{name}" + ("/" if whole else "")
            held = sorted({t[: t.index(inside) + len(f"/consegne/{ident}/")] for t in tracked
                           if (inside in t if whole else t.endswith(inside))})
            if len(held) == 1:
                parts[key] = held[0]
            else:
                missing.append(name)
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
            elif name == "documentazione.md" and not additive and since:
                # Outside the additive mode the documentation session writes what the code
                # session proposed into the documents themselves (R-4): the commit says where.
                parts[name] = f"written into the documents by {sha_full[:12]}"

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
    if blocks:
        _join_into(folder, target, len(blocks) + 1)
        block = {"commit": sha_full[:12], "date": date.today().isoformat(), "parts": parts}
        (target / X.MARK).write_text(_blocks_text([*blocks, block]), encoding="utf-8")
    else:
        shutil.move(str(folder), str(target))
        lines = [f'commit: "{sha_full[:12]}"', f"date: {date.today().isoformat()}",
                 "parts:" + ("" if parts else " {}")]
        # Quoted where YAML would not read it back as written -- `dropped: ...` holds `: `.
        lines += [f"  {_plain(k)}: {_plain(where)}" for k, where in parts.items()]
        (target / X.MARK).write_text("\n".join(lines) + "\n", encoding="utf-8")
    _close_launch(target)
    print(f"{ident}: moved to {target}, with `{X.MARK}` naming {sha_full[:12]}"
          + (f", block {len(blocks) + 1}." if blocks else "."))
    for k, where in parts.items():
        print(f"  {k}: {where}")
    for name in by_hand:
        print(f"  {name}: not placed. Write in `parts` where it went; `EXC003` says it until "
              "then.")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# `code`, since 4.13.0: the code session launched by the documentation session.

CODE_SINCE = "4.13.0"
# The `claude` to launch, where the environment names one: the behaviour runner points it at a
# fake that records the call, so that a skill that does not stop at "launch?" starts nothing.
# Not the `PATH`, which the shell of a run takes again from the person's profile.
CLAUDE_VAR = "FRAMEWORK_DATA_AI_CLAUDE"
# Never passed to the code session. The first six take a session off the person's subscription
# or onto another provider: the code session runs on the subscription alone, and the first
# event it writes says where its credential comes from (T-2). `CLAUDECODE` marks a nested
# session, and `CLAUDE_PROJECT_DIR` is read by the hooks before the folder a session starts in:
# kept, it would make the guard of the code session take the documentation for its own.
DROPPED_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
               "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY",
               "CLAUDECODE", "CLAUDE_PROJECT_DIR")
# The first six again, as Claude Code reads them from the `env` block of its settings too, where
# no environment of this command's reaches them: there the first event says `none` for all but
# the key (trial of 9/11, after the review of step 1), and the run goes to another provider, an
# address or a token unseen. A settings file that sets one is refused before any launch, said
# with its file and line; `apiKeyHelper` with them, which the first event names, refused before
# rather than stopped after. A `CLAUDE_CODE_USE_*` set to a value that turns it off is no
# provider.
PROVIDER_ENV = DROPPED_ENV[:6]
TURNED_OFF = ("", "0", "false", "no", "off")
# Where the code session's process is watched with POSIX calls: on Windows outside WSL
# `os.kill(pid, 0)` ends the process it asks about, and process groups do not exist. `code` is
# refused there, and the listing does not ask.
WINDOWS = os.name == "nt"
GIT_ENV = {"LC_ALL": "C", "LANG": "C", "GIT_TERMINAL_PROMPT": "0"}
STOPS = ("negata", "account", "domanda", "consegna", "fine")
# The output of one run, in the outputs folder, under the name the command gives it and no other.
OUTPUT_NAME = re.compile(r"^[A-Z]{2,3}-\d{3,}-[0-9a-f]{8}-\d+\.jsonl$")
# A session and a commit as this command writes them in the launch file, which the code session
# can write too: never an option on a command line, `claude --resume` or `git log`.
SESSION_ID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}")
COMMIT_ID = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?")
# Never the code session's, even on a yes: the push and the merge request, which the
# documentation session makes (R-1). Denied, they are said apart, and are no question, where
# they are the whole line, read at the start of each of its commands.
# What may stand before a command -- `env`, assignments -- and git with its own options, those
# whose value may follow a space named.
_LEAD = r"^\s*\(?\s*(?:env\s+(?:-\S+\s+)*)?(?:[A-Za-z_]\w*=\S*\s+)*"
_GIT = (r"git(?:\s+-[Cc]\s+\S+|\s+--(?:git-dir|work-tree|namespace|config-env|exec-path)"
        r"(?:=|\s+)\S+|\s+--[A-Za-z][\w-]*(?:=\S+)?)*")
_NOT_B = (rf"{_GIT}\s+push|gh\s+pr\s+(?:create|merge)|glab\s+mr\s+(?:create|merge)")
NOT_B = re.compile(rf"{_LEAD}(?:{_NOT_B})\b")
# The commit of a step of a rebase, which the documentation session runs on the person's yes and
# never grants (R-27): its `--continue`, and with a rebase in progress a `git commit` too; with
# a merge of the base in progress, the commit that concludes it, `git commit` or `git merge
# --continue` (V-5).
CONTINUE = re.compile(rf"{_LEAD}{_GIT}\s+rebase\s+--continue\b")
COMMIT = re.compile(rf"{_LEAD}{_GIT}\s+(?:commit|merge\s+--continue)\b")
# The same anywhere on a line -- among other commands, inside `bash -c "..."`, or only in the
# text of a message, which nothing here tells apart --: such a line gets no rule, which would
# grant it too, and the stop says so.
NOT_B_ANYWHERE = re.compile(rf"(?:^|[^\w-])(?:{_NOT_B}|{_GIT}\s+rebase\s+--continue)\b")
COMMIT_ANYWHERE = re.compile(rf"(?:^|[^\w-]){_GIT}\s+(?:commit|merge\s+--continue)\b")
# Where a line of the shell holds more than one command. A separator inside quotes splits a
# message too: what is read here is only whether every command, or some, is one of the above.
SEPARATORS = re.compile(r"&&|\|\||;|\||\n")
# A value beside a name, in a command denied or an answer: withheld in the launch file, which
# like `risorse.md` never holds one. The name stays, so the prose still reads.
WITHHELD = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)(\s*=\s*)(\"[^\"]*\"|'[^']*'|[^\s,;)]+)")
COMMAND_KINDS = ("test", "prepare", "generated", "link")
GUARD_SAYS = "The framework's write guard"


def _withhold(text: str) -> str:
    return WITHHELD.sub(lambda m: f"{m.group(1)}{m.group(2)}<trattenuto>", text)


def _now() -> str:
    """To the microsecond: a stop compares it with the times of the files a run wrote, and a
    question written in one run must not read as new in the run that answers it."""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="microseconds")


def _when(text: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(text) if text else None
    except ValueError:
        return None


def _git_in(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    """git with no prompt and no translation, never an exception: a failure is its exit code."""
    try:
        return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                              env={**os.environ, **GIT_ENV}, timeout=300)
    except (OSError, subprocess.SubprocessError) as e:
        return subprocess.CompletedProcess(args, 1, "", str(e))


def _out(cwd: Path, *args: str) -> str:
    r = _git_in(cwd, *args)
    return r.stdout.strip() if r.returncode == 0 else ""


def outputs_folder() -> Path:
    """Where the output of each run of a code session is written while it runs: the person's,
    the same for every session of the machine, since a resume is made from any of them, and
    outside the folder of the repositories, because an output holds what the run read. Not
    `$TMPDIR`, which a sandbox moves and a restart empties."""
    state = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(state) / "framework-data-ai" / "uscite"


def claude_binary() -> str | None:
    named = os.environ.get(CLAUDE_VAR)
    return named if named else shutil.which("claude")


def brief_commands(text: str) -> dict[str, list]:
    """The `Commands` block of a brief: the tests the launch grants, the preparation of the
    worktree that the documentation session runs, the generated files with the command that
    regenerates them, and the files git ignores that are linked from the main checkout.

        Commands           test: `pytest -q`
                           prepare: `uv sync`
                           generated: `uv.lock`, by `uv lock`
                           link: `.env`

    One item per line, the block ending at the first line not indented. A command or a file is
    what is between backticks; a line without them is taken whole."""
    out: dict[str, list] = {k: [] for k in COMMAND_KINDS}
    inside = False
    for line in text.splitlines():
        head = re.match(r"^\s{0,3}Commands\b[ \t]*(.*)$", line)
        if head:
            inside, rest = True, head.group(1).strip()
        elif inside and line[:1] in (" ", "\t") and line.strip():
            rest = line.strip()
        elif inside:
            break
        else:
            continue
        item = re.match(r"^(test|prepare|generated|link):\s*(.+)$", rest)
        if not item:
            continue
        kind, value = item.groups()
        ticked = re.findall(r"`([^`]+)`", value)
        if kind == "generated":
            if ticked:
                out[kind].append((ticked[0], ticked[1] if len(ticked) > 1 else None))
        else:
            out[kind].append((ticked[0] if ticked else value).strip())
    return out


def granted(framework: Path, commands: dict) -> list[str]:
    """What the code session may do without asking (piano 4.11.0 v2 §6, and the trial of 9/11):
    read, write -- the guard is the limit --, the reviser the brief asks for, the git commands
    that read, `git add`, the validator, and the tests the brief names, each as written."""
    rules = ["Read", "Glob", "Grep", "Write", "Edit", "Agent",
             "Bash(git status *)", "Bash(git diff *)", "Bash(git log *)", "Bash(git show *)",
             "Bash(git add *)",
             f"Bash(python3 {framework / 'skills' / 'audit' / 'scripts' / 'validate.py'} *)"]
    rules += [f"Bash({c})" for c in commands.get("test", []) if c]
    return list(dict.fromkeys(rules))


def _command_line(pid: int) -> str | None:
    """The command line of a process: `/proc` where there is one, `ps` elsewhere; empty for a
    process that is gone or ended unreaped, `None` where neither can be read."""
    try:
        return Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode(
            "utf-8", "replace")
    except FileNotFoundError:
        if Path("/proc/self").exists():
            return ""
    except OSError:
        pass
    try:
        r = subprocess.run(["ps", "-ww", "-o", "args=", "-p", str(pid)], capture_output=True,
                           text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else ""


def _word(value) -> bool:
    """A string a path or a name can be made of: not empty, no null byte."""
    return isinstance(value, str) and bool(value) and "\0" not in value


def _launch_shape(data, outputs: Path | None = None) -> str | None:
    """What, in a launch file, is not as this command writes it, or `None`. Anyone can write
    the file -- the code session too --, and its values reach `claude` and git as arguments:
    every reader takes it whole or not at all. Every key `prepare` and `run` write is there,
    with its type; a time has its offset; with `outputs`, the folder of the outputs of this
    environment, the output of a run not ended, the only one read, is there -- the listing,
    read from any environment, leaves that to `code`."""
    if not isinstance(data, dict):
        return "not an object"
    for key in ("elemento", "repository", "worktree", "ramo"):
        if not _word(data.get(key)):
            return f"`{key}`"
    launches = data.get("lanci")
    if not isinstance(launches, list) or not launches:
        return "`lanci`"

    def commit(value) -> bool:
        return isinstance(value, str) and bool(COMMIT_ID.fullmatch(value))

    def texts(values) -> bool:
        return all(isinstance(s, str) for s in values)

    def when(value, required: bool = False) -> bool:
        if value is None:
            return not required
        try:
            return isinstance(value, str) and datetime.fromisoformat(value).tzinfo is not None
        except ValueError:
            return False

    for n, launch in enumerate(launches, 1):
        where = f"launch {n}"
        if not isinstance(launch, dict):
            return where
        for key in ("estranei", "collegati", "concessi", "approvate", "tranche"):
            if not isinstance(launch.get(key), list):
                return f"{where}, `{key}`"
        session = launch.get("sessione")
        if session is not None and not (isinstance(session, str)
                                        and SESSION_ID.fullmatch(session)):
            return f"{where}, `sessione`"
        if not all(commit(s) for s in launch["estranei"]):
            return f"{where}, `estranei`"
        diverged = launch.get("divergente")
        if diverged is not None and not (isinstance(diverged, dict)
                                         and commit(diverged.get("remoto_sha"))
                                         and texts([diverged.get("locale", ""),
                                                    diverged.get("remoto", "")])):
            return f"{where}, `divergente`"
        for key in ("collegati", "concessi"):
            if not texts(launch[key]):
                return f"{where}, `{key}`"
        if not when(launch.get("inizio"), required=True):
            return f"{where}, `inizio`"
        if launch.get("base") is not None and not _word(launch.get("base")):
            return f"{where}, `base`"
        if launch.get("lease") is not None and not commit(launch.get("lease")):
            return f"{where}, `lease`"
        if launch.get("modo") not in (None, "merge", "rebase"):
            return f"{where}, `modo`"
        for m, run in enumerate(launch["tranche"], 1):
            at = f"{where}, run {m}"
            if not isinstance(run, dict):
                return at
            if not when(run.get("inizio"), required=True) or not when(run.get("fine")):
                return f"{at}, its times"
            # Where the output is, only for a run not ended, the one whose output is read: an
            # ended run's was deleted with its stop, under whatever folder it was.
            out = run.get("uscita")
            if not _word(out) or not OUTPUT_NAME.match(Path(out).name) \
                    or not Path(out).name.startswith(f"{data['elemento']}-") \
                    or (outputs is not None and not run.get("fine")
                        and Path(out).parent != outputs):
                return f"{at}, `uscita`"
            pid = run.get("processo")
            if pid is not None and (isinstance(pid, bool) or not isinstance(pid, int)):
                return f"{at}, `processo`"
            # Empty where the rebase said none: `_rebase_says` reads nothing.
            if run.get("onto") not in (None, "") and not commit(run.get("onto")):
                return f"{at}, `onto`"
            if not isinstance(run.get("proposte") or [], list) \
                    or not texts(run.get("proposte") or []):
                return f"{at}, `proposte`"
            if run.get("passo") is not None and not isinstance(run.get("passo"), list):
                return f"{at}, `passo`"
            if run.get("unione") is not None and not isinstance(run.get("unione"), bool):
                return f"{at}, `unione`"
            if run.get("sulla_base") is not None and not isinstance(run.get("sulla_base"), bool):
                return f"{at}, `sulla_base`"
            if run.get("fermata") is not None and not isinstance(run.get("fermata"), str):
                return f"{at}, `fermata`"
    return None


def _writes_to(pid: int, output) -> bool:
    """Whether the standard output of a process is the output file of a run, which this command
    opened for it and nothing else holds: read in `/proc` where there is one, with `lsof`
    elsewhere -- macOS has it --, and no where neither tells."""
    if not isinstance(output, str) or not output:
        return False
    try:
        want = os.path.realpath(output)
        if Path("/proc/self/fd").is_dir():
            return os.readlink(f"/proc/{pid}/fd/1") == want
        r = subprocess.run(["lsof", "-a", "-p", str(pid), "-d", "1", "-Fn"],
                           capture_output=True, text=True, timeout=10)
    except (OSError, ValueError, subprocess.SubprocessError):
        return False
    return any(line[1:] == want for line in r.stdout.splitlines() if line.startswith("n"))


def _alive(pid, session: str | None = None, output: str | None = None) -> bool | None:
    """Whether the process of a run still runs: `None` on Windows outside WSL, where asking
    would end it. With the session, a number another process took after a restart is not the
    run: the code session carries its session on its command line, `--session-id` or
    `--resume`, as Claude Code 2.1.321 keeps it for the whole run, in `/proc` and in `ps`
    (trial of 9/11, on WSL2; macOS not tried). A command line a later version rewrote would
    hide it: then the run's output, the process's standard output, still tells it is the run,
    where `/proc` or `lsof` reads it."""
    if WINDOWS:
        return None
    if isinstance(pid, bool) or not isinstance(pid, int) or not 0 < pid < 2 ** 31:
        return False
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, OverflowError):
        return False
    except PermissionError:
        pass                               # another user's: read below, never the code session
    # A child of this process: its number is not taken while it is, and one that ended and was
    # not reaped is no run in progress.
    try:
        done, _ = os.waitpid(pid, os.WNOHANG)
        return done == 0
    except ChildProcessError:
        pass
    if session and isinstance(session, str):   # anyone can write the launch file
        line = _command_line(pid)
        if line is not None and session not in line and not _writes_to(pid, output):
            return False
    return True


def _settings_files(tree: Path) -> list[Path]:
    """The settings Claude Code reads for a session started in `tree`: the organisation's, the
    person's, the project's and its local ones."""
    managed = Path("/Library/Application Support/ClaudeCode") if sys.platform == "darwin" \
        else Path("/etc/claude-code")
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    return [managed / "managed-settings.json", config / "settings.json",
            tree / ".claude" / "settings.json", tree / ".claude" / "settings.local.json"]


def off_subscription(tree: Path) -> list[str]:
    """What, in those settings, would take the code session off the person's subscription:
    each said `<file>, line <n>: <key>`, never with its value. A file that opens and does not
    read is said too, since what it sets cannot be told; one the person cannot open is skipped,
    since the code session runs as the person and cannot open it either."""
    found: list[str] = []
    for path in _settings_files(tree):
        try:
            text = path.read_text(encoding="utf-8")
        except (FileNotFoundError, NotADirectoryError, PermissionError, IsADirectoryError):
            continue
        except (OSError, UnicodeDecodeError) as e:
            found.append(f"{path}: cannot be read ({getattr(e, 'strerror', None) or e}), and "
                         "what it sets cannot be told")
            continue
        try:
            data = json.loads(text)
        except ValueError:
            found.append(f"{path}: does not read as JSON, and what it sets cannot be told")
            continue
        if not isinstance(data, dict):
            continue
        env = data.get("env") if isinstance(data.get("env"), dict) else {}
        keys = [f"env.{n}" for n in PROVIDER_ENV
                if str(env.get(n) or "").strip().lower()
                not in (TURNED_OFF if n.startswith("CLAUDE_CODE_USE_") else ("",))]
        if str(data.get("apiKeyHelper") or "").strip():
            keys.append("apiKeyHelper")
        lines = text.splitlines()
        for key in keys:
            name = key.rsplit(".", 1)[-1]
            at = next((n for n, line in enumerate(lines, 1) if f'"{name}"' in line), None)
            found.append(f"{path}" + (f", line {at}" if at else "") + f": {key}")
    return found


@dataclass
class Rebase:
    step: int
    of: int
    commit: str
    subject: str
    conflicted: list[str]


def rebase_in(tree: Path) -> Rebase | None:
    """The rebase stopped in the code session's worktree, if one is: which step of how many,
    the local commit it re-applies, the files left in conflict."""
    for name in ("rebase-merge", "rebase-apply"):
        place = _out(tree, "rev-parse", "--path-format=absolute", "--git-path", name)
        if place and Path(place).is_dir():
            d = Path(place)

            def num(*names: str) -> int:
                for n in names:
                    try:
                        return int((d / n).read_text().strip())
                    except (OSError, ValueError):
                        continue
                return 0
            sha = _out(tree, "rev-parse", "--verify", "-q", "REBASE_HEAD")
            subject = _out(tree, "log", "-1", "--format=%s", sha) if sha else ""
            conflicted = _out(tree, "diff", "--name-only", "--diff-filter=U").splitlines()
            return Rebase(num("msgnum", "next"), num("end", "last"), sha[:12], subject,
                          conflicted)
    return None


def merge_in(tree: Path) -> list[str] | None:
    """The merge of the base stopped in the code session's worktree, if one is (V-5): the files
    still in conflict, none where all are resolved and its commit is left."""
    if not _out(tree, "rev-parse", "--verify", "-q", "MERGE_HEAD"):
        return None
    return _out(tree, "diff", "--name-only", "--diff-filter=U").splitlines()


def _rebase_says(tree: Path, what: str) -> str:
    """A file of the rebase stopped in `tree`: `head-name`, the branch it re-applies; `onto`,
    the commit it re-applies on."""
    for name in ("rebase-merge", "rebase-apply"):
        place = _out(tree, "rev-parse", "--path-format=absolute", "--git-path", f"{name}/{what}")
        try:
            said = Path(place).read_text(encoding="utf-8").strip() if place else ""
        except OSError:
            continue
        if said:
            return said
    return ""


def rebasing_branch(tree: Path) -> str:
    """The branch a rebase stopped in `tree` re-applies: meanwhile its `HEAD` is detached, and
    `git worktree list` names no branch for it."""
    head = _rebase_says(tree, "head-name")
    return head[len("refs/heads/"):] if head.startswith("refs/heads/") else ""


def _person_allowed_dirs() -> list[str]:
    """The value the person gave to the plugin's `allowed_dirs`, as their user settings hold it:
    a plugin loaded with `--plugin-dir` is another copy, `framework-data-ai@inline`, and does
    not receive the value given to the one installed (trial of 9/11, 3d and 3e)."""
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    try:
        data = json.loads((config / "settings.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    for key, value in ((data.get("pluginConfigs") or {}) if isinstance(data, dict) else {}).items():
        if str(key).split("@", 1)[0] == "framework-data-ai" and isinstance(value, dict):
            dirs = (value.get("options") or {}).get("allowed_dirs")
            if isinstance(dirs, list):
                return [str(d) for d in dirs if str(d).strip()]
            if isinstance(dirs, str) and dirs.strip():
                return [dirs.strip()]
    return []


class Code:
    """One element's launch: its folder in the exchange, the documentation it is launched from,
    and the launch file, which only this command writes and reads."""

    def __init__(self, root: Path, path: Path, shown: str, ident: str):
        if not X.ELEMENT.match(ident):
            v.refuse(f"{ident!r} is not an element's identifier, as `CHG-021`.")
        self.root, self.exchange, self.shown, self.ident = root, path, shown, ident
        self.folder = path / X.INCOMING / ident
        self.file = self.folder / X.LAUNCH
        self.data: dict = {}
        # A launch file not as this command writes it, found by the first call: what is wrong,
        # and the branch and repository it named.
        self.broken: str | None = None
        self.kept: dict = {}
        self.kept_run: dict = {}
        # The closed launch's file in `integrati/`, not of its shape: its history is not taken.
        self.closed_broken: str | None = None

    # The launch file ─────────────────────────────────────────────────────────

    def load(self, required: bool = True) -> dict:
        if not self.file.is_file():
            # The first call does not need one: after a launch closed it prepares the new one,
            # with the history of the closed one (`_closed_launch`).
            if required and (self.exchange / X.INTEGRATED / self.ident / X.LAUNCH).is_file():
                v.refuse(f"the launch of {self.ident} is closed: its folder is in "
                         f"`{X.INTEGRATED}/`. A change asked for after is a new launch: put the "
                         f"brief back in `{X.INCOMING}/{self.ident}/`, with what to change at its "
                         "end, and make the first call again.")
            if required:
                v.refuse(f"{self.file}: no launch of {self.ident}. The first call, `code "
                         f"{self.ident} --repo <code repository>`, prepares it.")
            return {}
        try:
            data = json.loads(self.file.read_text(encoding="utf-8"))
        except (OSError, ValueError, RecursionError) as e:
            data, bad = None, f"it does not read as JSON: {e}"
        else:
            bad = _launch_shape(data, outputs_folder())
        if bad is None:
            self.data = data
            return self.data
        if required:
            where = data.get("repository") if isinstance(data, dict) \
                and _word(data.get("repository")) else "<code repository>"
            v.refuse(f"{self.file} is not a launch file as this command writes it ({bad}): "
                     "nothing is launched, and nothing is passed on its word. The first call, "
                     f"`code {self.ident} --repo {where}`, writes a new one in its place, "
                     "without the history this one held, once no code session it names runs.")
        # The first call is the way out: it keeps only the branch and the repository the file
        # names, when they read, so that the branch an earlier launch made is still its own;
        # and the process of its last run, if it has not ended, which may be the code session
        # still running.
        self.broken = bad
        self.kept = {k: data[k] for k in ("repository", "ramo")
                     if isinstance(data, dict) and _word(data.get(k))}
        try:
            launch = data["lanci"][-1]
            run = launch["tranche"][-1]
            if isinstance(run, dict) and not run.get("fine"):
                session = launch.get("sessione")
                self.kept_run = {"processo": run.get("processo"),
                                 "sessione": session if isinstance(session, str) else None,
                                 "uscita": run.get("uscita")}
        except (KeyError, IndexError, TypeError, AttributeError):
            pass
        self.data = {}
        return self.data

    def save(self) -> None:
        tmp = self.file.with_name(f".{self.file.name}.tmp")
        tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        os.replace(tmp, self.file)

    @property
    def launch(self) -> dict:
        return self.data["lanci"][-1]

    @property
    def tree(self) -> Path:
        return Path(self.data["worktree"])

    @property
    def repo(self) -> Path:
        return Path(self.data["repository"])

    def running(self) -> dict | None:
        """The run in progress, if any: one with no end whose process is alive."""
        runs = self.launch.get("tranche") or []
        last = runs[-1] if runs else None
        if last and not last.get("fine") \
                and _alive(last.get("processo"), self.launch.get("sessione"), last.get("uscita")):
            return last
        return None

    def check_subscription(self) -> None:
        """Before every run: the settings Claude Code reads that would take the code session off
        the person's subscription, refused with their file and line (T-2)."""
        found = off_subscription(self.tree)
        if found:
            v.refuse("the code session would not run on the person's subscription, which is the "
                     "only account it runs on. Claude Code's settings set: " + "; ".join(found)
                     + ". Remove it there, or keep it to the sessions that need it; a managed "
                     "file is the organisation's, for its administrator. Nothing is launched.")

    # What every call checks again ────────────────────────────────────────────

    def docs_folder(self) -> Path:
        """The folder that holds the main checkout of the documentation, and so the exchange and
        the code repositories beside it."""
        common = _out(self.root, "rev-parse", "--path-format=absolute", "--git-common-dir")
        return (Path(common).parent if common else self.root).parent.resolve()

    def check_repo(self, repo: Path) -> Path:
        """The code repository: a git repository of its own, beside the documentation, where the
        guard holds the code session (`hooks/guard.py`): anywhere else it lets every write
        through."""
        repo = repo.expanduser().resolve()
        top = _out(repo, "rev-parse", "--show-toplevel") if repo.is_dir() else ""
        if not top or Path(top).resolve() != repo:
            v.refuse(f"{repo} is not the top of a git repository. `--repo` is the code "
                     "repository, beside the documentation.")
        docs_common = Path(_out(self.root, "rev-parse", "--path-format=absolute",
                                "--git-common-dir") or self.root).resolve()
        repo_common = Path(_out(repo, "rev-parse", "--path-format=absolute",
                                "--git-common-dir") or repo).resolve()
        if repo_common == docs_common:
            v.refuse(f"{repo} is the documentation, or one of its worktrees: the code session "
                     "works in the code repository.")
        if repo == self.exchange or self.exchange in repo.parents:
            v.refuse(f"{repo} is inside the exchange, which belongs outside every repository.")
        if repo.parent != self.docs_folder():
            v.refuse(f"{repo} is not beside the documentation, in {self.docs_folder()}. The "
                     "framework's write guard holds the code session only in a repository "
                     "beside one with `.framework/`; anywhere else it would write unguarded.")
        return repo

    def check_tree(self) -> None:
        """What a launch file says, read again before it is used: anyone can write the file."""
        d = self.data
        if d.get("elemento") != self.ident or not isinstance(d.get("ramo"), str) \
                or not d.get("worktree") or not d.get("repository"):
            v.refuse(f"{self.file} does not say this launch's element, repository, worktree and "
                     "branch: nothing is launched.")
        # Its shape, and every value that reaches `claude` or git as an argument, `load` read.
        repo = self.check_repo(Path(d["repository"]))
        tree = Path(d["worktree"]).resolve()
        if tree != repo.parent / f"{repo.name}-{self.ident.lower()}":
            v.refuse(f"{tree} is not the worktree this command names for {self.ident}: nothing "
                     "is launched.")
        trees = self._trees(repo)
        if tree not in trees:
            v.refuse(f"{tree} is not a worktree of {repo}: the first call creates it.")
        on = trees[tree] or rebasing_branch(tree)
        if on != d["ramo"]:
            v.refuse(f"{tree} is on {on or 'a detached HEAD'}, not on {d['ramo']}, the branch of "
                     f"this launch: check it out there again (`git -C {tree} switch "
                     f"{d['ramo']}`), and nothing is launched until then.")

    def check_output(self, name) -> Path | None:
        if not isinstance(name, str):
            return None
        path = Path(name)
        if path.parent != outputs_folder() or not OUTPUT_NAME.match(path.name) \
                or not path.name.startswith(f"{self.ident}-"):
            v.refuse(f"{self.file} names {name} as a run's output, which is not where this "
                     f"command writes them ({outputs_folder()}): nothing is read or deleted.")
        return path

    # The documentation's side ────────────────────────────────────────────────

    def change(self) -> tuple[dict | None, str | None]:
        """The change as the checkout of `--root` holds it: front matter and path."""
        registry = v.yaml.safe_load(v.REGISTRY.read_text(encoding="utf-8"))
        project = v.load_project(self.root)
        config, _ = v.load_config(project)
        for a in v.discover(self.root, v.load_scan(registry, project), registry,
                            v.Report(config)):
            if a.type == "change-contract" and a.id == self.ident:
                return a.meta, a.rel.replace("\\", "/")
        return None, None

    def check_mandate(self, no_chg: str | None) -> dict:
        """The refusals that read the documentation: what is launched, and from where."""
        project = v.load_project(self.root)
        if not v.rules_hold(project, CODE_SINCE):
            v.refuse(f"{self.root} pins {project.get('framework_version')}: the launch of a code "
                     f"session is a {CODE_SINCE} command. Below it the code session is opened "
                     "by hand, as before.")
        if not (self.folder / X.BRIEF).is_file():
            v.refuse(f"{self.folder / X.BRIEF}: no brief. The code session executes a brief, "
                     "which `cycle` writes for an approved change.")
        meta, rel = self.change()
        hotfix = bool(no_chg)
        if no_chg:
            if not re.fullmatch(r"hotfix\s+\S.*", no_chg.strip()):
                v.refuse(f"`--no-chg {no_chg!r}`: write it `--no-chg \"hotfix <reference>\"`, "
                         "the reference of the incident the hotfix answers.")
            if meta is not None:
                v.refuse(f"{self.ident} is written already in {self.root} "
                         f"({meta.get('status')}): `--no-chg` launches a hotfix whose change is "
                         "not written yet, and has no mandate to check. Launch the change "
                         "without it, once approved.")
        else:
            if meta is None:
                v.refuse(f"{self.ident} is not a change the documentation in {self.root} "
                         "declares. A hotfix whose change is not written yet is launched with "
                         "`--no-chg \"hotfix <reference>\"`.")
            if meta.get("status") != "approved":
                v.refuse(f"{self.ident} is {meta.get('status')} in {self.root}: a code session "
                         "executes an approved change.")
            hotfix = meta.get("hotfix") is True
        try:
            work = v.load_work(self.root, v.Report(v.load_config(project)[0])) or {}
        except SystemExit as e:
            v.refuse(f"{e.code} Nothing is launched.")
        additive = work.get("mode") == "additive"
        prefix = str(work.get("branch_prefix") or "work/")
        branch = _out(self.root, "rev-parse", "--abbrev-ref", "HEAD")
        name = self.ident.lower()
        if additive and hotfix:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import todo as T  # noqa: E402  (the slug the to-do and `work.py` compute)
            if no_chg:
                short = "hotfix-" + T.slug(no_chg.strip().split(None, 1)[1])
            else:
                # As the to-do names a mandate's home: its product, or `radice`, under
                # `platform/` too.
                home = T.product_of_path(rel or "") or "radice"
                short = "hotfix-" + T.slug(f"{home}-{T.bare(self.ident)}")
            name = f"{prefix}{v._branches.PARKING}{short}"
            if branch != name:
                v.refuse(f"{self.ident} is a hotfix: every launch of a hotfix starts from its "
                         f"parking branch, {name}, which is its claim. Open it with `work.py "
                         f"open --branch {short}` and launch from that worktree; `--root` is on "
                         f"{branch or 'no branch'}.")
        elif additive:
            held = _out(self.root, "for-each-ref", "--format=%(refname)%00%(contents)%00%00",
                        v._branches.CLAIM_REF.rstrip("/"))
            holds = False
            for record in held.split("\x00\x00"):
                ref, _, body = record.strip("\n").partition("\x00")
                if ref.rsplit("/", 1)[-1] == self.ident \
                        and v._branches.message_fields(body).get("branch") == branch:
                    holds = True
            if not holds:
                where = branch or "no branch"
                v.refuse(f"{self.ident} is not held by the thread of {self.root} ({where}), as "
                         "its claims stood at the last fetch. Whoever implements a "
                         "change holds its thread, and launches from that worktree: `contribute` "
                         "takes it.")
            name = branch
        # `merge_method` is read only in the additive mode, as `WK002` says of it outside.
        return {"additive": additive, "branch": name, "hotfix": hotfix, "rel": rel,
                "merge_method": work.get("merge_method") if additive else None}

    # The first call ──────────────────────────────────────────────────────────

    def prepare(self, repo_arg: Path, base: str | None, no_chg: str | None,
                join_base: str | None = None) -> int:
        mandate = self.check_mandate(no_chg)
        repo = self.check_repo(repo_arg)
        if claude_binary() is None:
            v.refuse("`claude` is not on the PATH: the launch runs the code session with the "
                     "Claude Code command line, which the desktop app or an editor extension "
                     "alone do not install. `work.py doctor` says how to add it.")
        self.load(required=False)
        if self.data and self.running():
            v.refuse(f"a code session of {self.ident} is running: `code {self.ident} --status` "
                     "says where it is.")
        unread = None
        if self.broken and self.kept_run:
            run = self.kept_run
            if _alive(run["processo"], run["sessione"], run["uscita"]) is not False:
                v.refuse(f"a code session of {self.ident} may be running, process "
                         f"{run['processo']}, named by a launch file not as this command writes "
                         f"it ({self.broken}): nothing is prepared until it has ended, and then "
                         "the first call writes a new launch file.")
            # Ended, and its stop never read: nothing will read its output once the file is
            # replaced, and an output waits only until its stop is written. Removed, where it is
            # one this command names and the process is one that can be told ended: with no
            # number, a code session may still write it.
            out = run["uscita"]
            pid = run["processo"]
            if isinstance(pid, int) and not isinstance(pid, bool) and _word(out) \
                    and Path(out).parent == outputs_folder() \
                    and OUTPUT_NAME.match(Path(out).name) \
                    and Path(out).name.startswith(f"{self.ident}-"):
                unread = Path(out)
        # The closed launch's history before the branch and repository a broken file kept:
        # it is whole in `integrati/`.
        previous = self.data or self._closed_launch() or self.kept
        if previous and previous.get("ramo") not in (None, mandate["branch"]):
            v.refuse(f"{self.ident} was launched before on the branch {previous.get('ramo')}, "
                     f"and would be on {mandate['branch']} now: a change is one branch.")
        if previous and previous.get("repository") not in (None, str(repo)):
            v.refuse(f"{self.ident} was launched before in {previous.get('repository')}, and "
                     f"would be in {repo} now: a change changes one repository (R-8), and "
                     "another one is a change of its own.")
        if self.data:
            # A run whose end was never written is read before a new launch takes its place.
            self.recover()
        if not _out(repo, "remote", "get-url", "origin"):
            v.refuse(f"{repo} has no remote `origin`: the branch of the code session is pushed "
                     "there, and its merge request opened on it.")
        notes: list[str] = []
        if self.broken:
            notes.append(f"{self.file} was not as this command writes it ({self.broken}): a new "
                         "one takes its place, without the history it held.")
        if self.closed_broken:
            notes.append(f"The closed launch's file in `{X.INTEGRATED}/` is not as this command "
                         f"writes it ({self.closed_broken}): its history is not carried over.")
        fetched = _git_in(repo, "fetch", "--prune", "origin")
        if fetched.returncode:
            head = Path(_out(repo, "rev-parse", "--path-format=absolute", "--git-path",
                             "FETCH_HEAD") or "/nonexistent")
            stamp = datetime.fromtimestamp(head.stat().st_mtime) if head.exists() else None
            age = (f"the last one is from {stamp:%Y-%m-%d %H:%M}" if stamp is not None
                   else "there was none")
            notes.append(f"The fetch of {repo} failed ({(fetched.stderr or '').strip()[:200]}): "
                         f"what follows is as the last fetch left it, and {age}.")
        # The base of a branch an earlier launch made is the start it recorded, unless `--base`
        # names another: the one it is said behind and joined from (V-5). The remote's default
        # branch only for a new one, or where the recorded start is gone, said.
        # Read from a file anyone can write: only as a ref that exists, never as an option.
        recorded = (previous or {}).get("partenza")
        if not base and _word(recorded) and not recorded.startswith("-") and any(
                _out(repo, "rev-parse", "--verify", "-q", f"refs/{kind}/{recorded}")
                for kind in ("remotes", "heads")):
            start = recorded
        else:
            start = self._base(repo, base)
            if not base and _word(recorded) and recorded != start:
                notes.append(f"The start an earlier launch of {self.ident} recorded, {recorded}, "
                             f"is not in {repo}: the base is {start}, the remote's default "
                             "branch, unless `--base` names another.")
        branch = mandate["branch"]
        tree = repo.parent / f"{repo.name}-{self.ident.lower()}"
        remote = f"origin/{branch}"
        has_remote = bool(_out(repo, "rev-parse", "--verify", "-q", f"refs/remotes/{remote}"))
        local = _out(repo, "rev-parse", "--verify", "-q", f"refs/heads/{branch}")
        trees = self._trees(repo)
        known = bool(previous) and previous.get("ramo") == branch
        from_remote: list[str] = []
        if tree.exists():
            # A rebase stopped in the worktree leaves its `HEAD` detached, and `git worktree
            # list` names no branch: the one it re-applies is read from the rebase (R-22).
            on = trees.get(tree)
            if on == "":
                on = rebasing_branch(tree)
            if on is None:
                v.refuse(f"{tree} exists and is not the worktree of {branch}: remove it or move "
                         "it, and nothing is created.")
            if on != branch:
                v.refuse(f"{tree} is the code session's worktree, on {on or 'a detached HEAD'} "
                         f"and not on {branch}: check it out there again (`git -C {tree} switch "
                         f"{branch}`), and nothing is created until then.")
        elif local:
            where = next((t for t, b in trees.items() if b == branch), None)
            if where is not None:
                v.refuse(f"{branch} is checked out in {where}: a code session works in its own "
                         "worktree. Remove that worktree, or rename the branch, first.")
            if not known:
                v.refuse(f"{repo} has a branch {branch} that no launch of {self.ident} made, "
                         "with commits that are not the code session's: remove it or rename it, "
                         "and nothing is created.")
            self._git_or_refuse(repo, "worktree", "add", str(tree), branch)
            notes.append(f"Worktree {tree} created on the branch {branch} of an earlier launch.")
        elif has_remote:
            self._git_or_refuse(repo, "worktree", "add", "--track", "-b", branch, str(tree),
                                remote)
            # No local branch -- a thread taken again on the branch of whoever held it, or a
            # worktree and branch the person removed --: the commits of the remote's branch
            # above the start are not the code session's.
            from_remote = _out(repo, "rev-list", "--reverse", f"{start}..{remote}").split()
            notes.append(f"Worktree {tree} created on {remote}, which the remote already had"
                         + (f", with {len(from_remote)} commit(s) the code session did not make."
                            if from_remote else "."))
        else:
            self._git_or_refuse(repo, "worktree", "add", "--no-track", "-b", branch, str(tree),
                                start)
            notes.append(f"Worktree {tree} created, branch {branch} from {start}.")
        strangers: list[str] = from_remote
        diverged = None
        rebase = rebase_in(tree)
        # A merge of the base stopped in the worktree (V-5) goes to the code session first, as a
        # rebase does: nothing is brought forward or joined in the middle of it.
        merging = merge_in(tree) if rebase is None else None
        joined = None
        local = _out(repo, "rev-parse", "--verify", "-q", f"refs/heads/{branch}")
        theirs = _out(repo, "rev-parse", "--verify", "-q", f"refs/remotes/{remote}")
        push = not theirs
        # The last launch's join of the base (V-5..V-7): the base it joined, and, re-applied by
        # a rebase, the remote's commit that rebase rewrote, the lease of its forced push.
        # The latest launch that joined it, whatever launches came after: a first call made
        # again appends one with none. Its lease counts while the join is still to push: the
        # remote holds the commit the rebase rewrote, and the branch here does not.
        last = next((entry for entry in reversed((previous or {}).get("lanci") or [])
                     if entry.get("base")), {})
        lease = last.get("lease")
        lease = lease if lease and theirs and local and _git_in(
            repo, "merge-base", "--is-ancestor", lease, theirs).returncode == 0 and _git_in(
            repo, "merge-base", "--is-ancestor", lease, local).returncode != 0 else None
        forced = None
        # How the base was joined, `merge` or `rebase`, kept with it: the texts of a rebase and
        # the joins printed again read it, as `lease` is only where the branch was on a remote.
        joined_by = None
        # The base joined here and not pushed, where the remote moved meanwhile (V-6): how it
        # was joined, to join it again the same way.
        over_base = None
        if merging is not None:
            joined = (previous or {}).get("lanci", [{}])[-1].get("base")
            joined_by = "merge"
            if not joined:
                v.refuse(f"a merge is in progress in {tree} that no `--join-base` made: it is the "
                         f"person's to conclude or abort (`git -C {tree} merge --abort`), and "
                         "nothing is prepared until then.")
            notes.append(f"A merge of the base is in progress in {tree}"
                         + (f", in conflict in {', '.join(merging)}" if merging else
                            ", its conflicts resolved")
                         + ": it is not made again, the launch gives the code session what is "
                         "left of it first, and the commit that concludes it is yours, on the "
                         "person's yes.")
            strangers = list((previous or {}).get("lanci", [{}])[-1].get("estranei") or [])
            if theirs and local and _git_in(repo, "merge-base", "--is-ancestor", theirs,
                                            local).returncode != 0:
                notes.append(f"{remote} has commits {branch} has not: the push after the merge "
                             "will be refused (R-28), unless the merge is aborted (`git -C "
                             f"{tree} merge --abort`, in view, on the person's yes) and the first "
                             "call made again.")
        elif rebase is not None:
            notes.append(f"A rebase is in progress in {tree}, stopped at step {rebase.step} of "
                         f"{rebase.of}: it is not applied again, and the launch gives the code "
                         "session the stopped step first.")
            strangers = list((previous or {}).get("lanci", [{}])[-1].get("estranei") or [])
            onto = _rebase_says(tree, "onto")
            if last.get("modo") == "rebase" and not (
                    theirs and onto and _git_in(repo, "merge-base", "--is-ancestor", onto,
                                                theirs).returncode == 0):
                # A rebase on the base (V-7): its push is forced, at the lease, where the branch
                # was on the remote; with none, a push.
                # Mid-rebase the branch still points at its old commit: the lease is read whole.
                lease = last.get("lease")
                joined, forced, joined_by = last.get("base"), lease, "rebase"
                if lease and theirs and theirs != lease:
                    notes.append(f"{remote} has moved since the rebase on the base began: its "
                                 "forced push will be refused, and then the remote is kept and "
                                 "the base joined again, the first call with `--join-base "
                                 "rebase` (V-6).")
            elif theirs and onto and _git_in(repo, "merge-base", "--is-ancestor", theirs,
                                             onto).returncode != 0:
                notes.append(f"{remote} has moved past {onto[:12]}, the commit the rebase "
                             "re-applies on: the push after it will be refused (R-28), unless the "
                             f"rebase is aborted (`git -C {tree} rebase --abort`, in view, on the "
                             "person's yes) and the first call made again.")
        elif theirs and local and theirs != local:
            if _git_in(repo, "merge-base", "--is-ancestor", local, theirs).returncode == 0:
                strangers = _out(repo, "rev-list", "--reverse", f"{local}..{theirs}").split()
                r = _git_in(tree, "merge", "--ff-only", "-q", theirs)
                if r.returncode:
                    v.refuse(f"{remote} is ahead of {branch}, and bringing {tree} to it failed: "
                             f"{(r.stderr or '').strip()[:300]}. Nothing else is changed.")
                notes.append(f"{remote} was ahead: {branch} brought to it, {len(strangers)} "
                             "commit(s) the code session did not make.")
            elif _git_in(repo, "merge-base", "--is-ancestor", theirs, local).returncode == 0:
                push = True
            elif lease and theirs == lease and _git_in(repo, "merge-base", "--is-ancestor",
                                                       lease, local).returncode != 0:
                # Re-applied on the base and not pushed yet (V-7): not diverged, its forced
                # push is next.
                joined, forced, joined_by = last.get("base"), lease, "rebase"
                strangers = list(last.get("estranei") or [])
                notes.append(f"{branch} was re-applied on {joined} and not pushed: its push is "
                             "forced, with lease, on the person's yes (V-7).")
            else:
                diverged = {"locale": _out(repo, "log", "--format=%h %s", f"{theirs}..{local}"),
                            "remoto": _out(repo, "log", "--format=%h %s", f"{local}..{theirs}"),
                            "remoto_sha": theirs}
                strangers = _out(repo, "rev-list", "--reverse", f"{local}..{theirs}").split()
                # Re-applied on the base and not pushed: the remote still holds the commit the
                # rebase rewrote, and the branch does not. Once its forced push was made the
                # remote no longer holds it: the join was pushed, and R-26's way holds.
                if lease and _git_in(repo, "merge-base", "--is-ancestor", lease,
                                     theirs).returncode == 0 \
                        and _git_in(repo, "merge-base", "--is-ancestor", lease,
                                    local).returncode != 0:
                    over_base = "rebase"
                elif _out(repo, "rev-list", "--merges", f"{theirs}..{local}"):
                    over_base = "merge"
        # The base (V-5): how far the branch is behind it, said; joined on the person's yes,
        # `--join-base`, where the forge wants the branch up to date with it or its merge
        # request conflicts with it.
        head = _out(tree, "rev-parse", "--verify", "-q", "HEAD")
        behind = _out(repo, "rev-list", "--reverse", f"{head}..{start}").split() \
            if head and rebase is None and merging is None and not diverged else []
        brought: list[str] = []
        if join_base:
            if rebase is not None or merging is not None or diverged:
                v.refuse(f"`--join-base`: {branch} has "
                         + ("a rebase in progress" if rebase is not None else
                            "a merge in progress" if merging is not None else
                            "diverged from its remote")
                         + ", which comes first. Nothing is joined; the launch file is as it "
                         "was.")
            # Where the code is merged by a rebase, the branch's commits are re-applied on the
            # base (V-7): a merge of it would come undone on the forge, its conflicts with it.
            way = (join_base if join_base in ("merge", "rebase") else
                   "rebase" if mandate.get("merge_method") == "rebase" else "merge")
            if not behind:
                notes.append(f"{branch} holds {start} already: there is nothing to join.")
            elif way == "rebase":
                r = _git_in(tree, "-c", "rerere.enabled=false", "rebase", start)
                rebase = rebase_in(tree)
                if r.returncode and rebase is None:
                    _git_in(tree, "rebase", "--abort")
                    v.refuse(f"the rebase of {branch} on {start} failed: "
                             f"{(r.stderr or r.stdout or '').strip()[:300]}. Nothing else is "
                             "changed.")
                strangers = behind + [s for s in strangers if s not in set(behind)]
                brought = behind
                joined, joined_by = start, "rebase"
                forced = theirs or None
                notes.append(f"{branch} re-applied on {start}, on the person's yes, as the code "
                             "is merged by a rebase: "
                             f"{len(behind)} commit(s) of the base the code session did not make"
                             + (f"; the rebase stopped at step {rebase.step} of {rebase.of}, which "
                                "the launch gives the code session first" if rebase is not None
                                else "")
                             + (". The push after it is forced, with lease, on the person's yes "
                                "(V-7)." if theirs else "."))
                behind = []
            else:
                # Without the person's `rerere`, as the join of the remote's (T-5).
                r = _git_in(tree, "-c", "rerere.enabled=false", "merge", "--no-ff", "-m",
                            f"Merge {start} into {branch}", start)
                if r.returncode and not _out(tree, "ls-files", "-u"):
                    _git_in(tree, "merge", "--abort")
                    v.refuse(f"the join of {start} into {branch} failed: "
                             f"{(r.stderr or r.stdout or '').strip()[:300]}. Nothing else is "
                             "changed.")
                # The base's first: the code session is shown the last thirty, and those made
                # on this branch are the ones to read before all (`_strangers`).
                strangers = behind + strangers
                brought = behind
                joined, joined_by = start, "merge"
                merging = merge_in(tree)
                push = merging is None or push
                notes.append(f"{start} joined into {branch}, on the person's yes: "
                             f"{len(behind)} commit(s) of the base the code session did not make"
                             + (f"; the merge stopped on conflicts in {', '.join(merging)}, which "
                                "the launch gives the code session first" if merging else "")
                             + ".")
                behind = []
        if behind:
            notes.append(f"{branch} is {len(behind)} commit(s) behind {start}. Where the forge "
                         "wants the branch up to date with its base, or its merge request "
                         "conflicts with it -- `work.py join` says so at its first step --, the "
                         "base is joined into it on the person's yes: this call again with "
                         "`--join-base`.")
        links = self._links(repo, tree, notes)
        blocked = off_subscription(tree)
        if blocked:
            notes.append("`--launch` will refuse while Claude Code's settings would take the "
                         "code session off the person's subscription: " + "; ".join(blocked)
                         + ".")
        self._resources(repo, tree, branch, links)
        if previous and not self.data:            # a closed launch: its history comes along
            self.data = dict(previous)
            self.data.pop("chiuso", None)
        self.data.update({"versione": 1, "elemento": self.ident, "repository": str(repo),
                          "worktree": str(tree), "ramo": branch, "partenza": start,
                          "no_chg": no_chg, "stato": "preparato"})
        lanci = self.data.setdefault("lanci", [])
        # The subjects of the commits are said whole, and kept withheld, as every value.
        kept = None if diverged is None else {**diverged,
                                              "locale": _withhold(diverged["locale"]),
                                              "remoto": _withhold(diverged["remoto"])}
        entry = {"inizio": _now(), "sessione": None, "estranei": strangers,
                 "divergente": kept, "collegati": links, "concessi": [], "approvate": [],
                 "tranche": [], "base": joined, "lease": forced,
                 "modo": joined_by if joined else None}
        if lanci and not lanci[-1].get("tranche"):
            # Prepared again, never launched: what the call before found not the code session's
            # -- brought forward, or kept from the remote -- stays so, where the branch holds it.
            head = _out(repo, "rev-parse", "--verify", "-q", f"refs/heads/{branch}")
            entry["estranei"] = [s for s in lanci[-1].get("estranei") or []
                                 if s not in strangers and head and
                                 _git_in(repo, "merge-base", "--is-ancestor", s,
                                         head).returncode == 0] + strangers
            if brought:
                # The base's first, as above.
                entry["estranei"] = brought + [s for s in entry["estranei"]
                                               if s not in set(brought)]
            # And the base it joined, which the launch tells the code session (V-5), where the
            # branch still holds commits of it: not after its merge was aborted.
            kept_base = lanci[-1].get("base")
            held = set(entry["estranei"])
            if kept_base and not joined and not any(
                    s in held and _git_in(repo, "merge-base", "--is-ancestor", s,
                                          start).returncode == 0
                    for s in lanci[-1].get("estranei") or []):
                kept_base = None
            if rebase is not None and joined_by != "rebase":
                # R-26's rebase on the remote's, begun since: the join of the base was pushed.
                kept_base = None
            entry["base"] = joined or kept_base
            if not joined and entry["base"]:
                # Kept from the call before, with how it was joined and, re-applied, its lease
                # while the remote still holds it: once the forced push was made, none.
                entry["modo"] = lanci[-1].get("modo")
                entry["lease"] = lease
            lanci[-1] = entry
        else:
            lanci.append(entry)
        self.save()
        if unread is not None:
            try:
                unread.unlink()
                notes.append(f"Its last run ended without its stop read: its output, {unread}, "
                             "is removed, as no file names it now; the session keeps what it "
                             "said.")
            except FileNotFoundError:
                pass
            except OSError as e:
                notes.append(f"Its last run ended without its stop read, and its output, "
                             f"{unread}, could not be removed ({e.strerror or e}): remove it by "
                             "hand, as no file names it now.")
        commands = brief_commands((self.folder / X.BRIEF).read_text(encoding="utf-8"))
        print(f"{self.ident}: prepared in {tree}, on the branch {branch}.")
        for n in notes:
            print(f"  {n}")
        if mandate["hotfix"] and not mandate["additive"] and no_chg:
            print("  Outside the additive mode the delivery of a hotfix without a change waits "
                  "for the change to be written, then is integrated as always.")
        if self.exchange.name != "_scambio" or self.exchange.parent != repo.parent:
            print(f"  The exchange is {self.exchange}, not `_scambio` beside {repo.name}: the "
                  "guard of the code session opens only `_scambio` beside its repository, and a "
                  "delivery here stops unless the person's `allowed_dirs` names it (`EXC008`).")
        if diverged:
            print(f"\nDIVERGED: {branch} here and {remote} each have commits the other has not.")
            print("  here, not on the remote:\n    " + (diverged["locale"].replace("\n", "\n    ")
                                                       or "none"))
            print("  on the remote, not here:\n    " + (diverged["remoto"].replace("\n", "\n    ")
                                                       or "none"))
            if over_base:
                # The base joined here and not pushed (V-6): a rebase would undo its merge and
                # copy the base's commits into the branch, or re-apply rewritten commits on their
                # old selves. The remote is kept, and the base joined again.
                print("  Here the base was joined, and not pushed: joining the two would undo "
                      "that join. Keep the remote, dropping the commits here, and join the base "
                      "again -- the code session resolves its conflicts again --, as commands of "
                      "yours, in view, on the person's yes:")
                print(f"    keep remote: git -C {tree} reset --keep "
                      f"{diverged['remoto_sha'][:12]}")
                # The same way: a branch re-applied on the base is re-applied again (V-7).
                print(f"    then this call again with `--join-base {over_base}`")
            else:
                print("  Ask the person: join them -- the commits here re-applied on the "
                      "remote's, rewritten, approved again only where a step stops on a "
                      "conflict -- or keep the remote and drop the commits here. Then, as a "
                      "command of yours, in view:")
                # Without the person's `rerere`, which would put back a resolution recorded in
                # another rebase, one nobody chose in this one: every conflict reaches the code
                # session with its markers (the owner's choice, 9/11). For this command only.
                print(f"    join:        git -C {tree} -c rerere.enabled=false rebase "
                      f"{diverged['remoto_sha'][:12]}")
                print(f"    keep remote: git -C {tree} reset --keep "
                      f"{diverged['remoto_sha'][:12]}")
            print("  `--launch` refuses while they diverge with no rebase in progress.")
        print("\nNext, each as a command of yours, in view:")
        if forced and rebase is None and not diverged:
            print(f"  on the person's yes, forced with lease (V-7): git -C {tree} push "
                  f"--force-with-lease=refs/heads/{branch}:{forced} origin {branch}")
        elif push and not diverged and merging is None and rebase is None:
            print(f"  git -C {tree} push -u origin {branch}")
        if merging is not None:
            print("  The merge of the base first, by the code session; its commit, yours on the "
                  "person's yes, when the code session stops on it; then the push.")
        for c in commands["prepare"]:
            print(f"  (in {tree}) {c}")
        if rebase is not None and commands["prepare"]:
            print("  A rebase is in progress: a preparation that fails on the conflict does not "
                  "stop the launch, and runs again on the final tree.")
        elif merging is not None and commands["prepare"]:
            print("  A merge of the base is in progress: a preparation that fails on the conflict "
                  "does not stop the launch, and runs again on the merged tree.")
        for f, how in commands["generated"]:
            print(f"  generated, never written by the code session: {f}"
                  + (f", by `{how}`" if how else ""))
        print(f"Then: python3 {Path(__file__).resolve()} --root {self.root} code {self.ident} "
              "--launch")
        return 0

    def _closed_launch(self) -> dict:
        old = self.exchange / X.INTEGRATED / self.ident / X.LAUNCH
        try:
            data = json.loads(old.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, ValueError, RecursionError) as e:
            self.closed_broken = f"it does not read: {e}"
            return {}
        # Its history comes along only whole, as every reader takes the file (`_launch_shape`).
        self.closed_broken = _launch_shape(data)
        return data if self.closed_broken is None else {}

    def _base(self, repo: Path, base: str | None) -> str:
        if base:
            for ref in (f"refs/remotes/origin/{base}", f"refs/heads/{base}"):
                if _out(repo, "rev-parse", "--verify", "-q", ref):
                    return ref.split("/", 2)[-1]
            v.refuse(f"`--base {base}`: neither origin/{base} nor {base} exists in {repo}.")
        head = _out(repo, "symbolic-ref", "-q", "refs/remotes/origin/HEAD")
        if not head:
            v.refuse(f"{repo} does not say the default branch of its remote "
                     f"(refs/remotes/origin/HEAD). Name the start with `--base <branch>`, or "
                     f"set it: git -C {repo} remote set-head origin --auto")
        return head[len("refs/remotes/"):]

    @staticmethod
    def _trees(repo: Path) -> dict[Path, str]:
        out, current = {}, None
        for line in _out(repo, "worktree", "list", "--porcelain").splitlines():
            if line.startswith("worktree "):
                current = Path(line[9:]).resolve()
                out[current] = ""
            elif line.startswith("branch refs/heads/") and current is not None:
                out[current] = line[len("branch refs/heads/"):]
        return out

    @staticmethod
    def _git_or_refuse(repo: Path, *args: str) -> None:
        r = _git_in(repo, *args)
        if r.returncode:
            v.refuse(f"git {' '.join(args)} failed in {repo}: {(r.stderr or '').strip()[:400]}")

    def _links(self, repo: Path, tree: Path, notes: list[str]) -> list[str]:
        """The files the brief names that git ignores, linked from the main checkout, never
        copied: no credential is copied under the folder of the repositories."""
        made = []
        for name in brief_commands((self.folder / X.BRIEF).read_text(encoding="utf-8"))["link"]:
            rel = PurePosixPath(name)
            if rel.is_absolute() or ".." in rel.parts:
                notes.append(f"`{name}` is not a path inside the repository: not linked.")
                continue
            source, target = repo / rel, tree / rel
            if not source.exists():
                notes.append(f"{source} does not exist: not linked.")
                continue
            if _git_in(repo, "check-ignore", "-q", str(rel)).returncode != 0:
                notes.append(f"{rel} is not ignored by git in {repo}: not linked, the worktree "
                             "has its own.")
                continue
            if target.is_symlink() or target.exists():
                made.append(str(rel))
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(source)
            made.append(str(rel))
            notes.append(f"{target} linked to {source}: read, never written.")
        return made

    def _resources(self, repo: Path, tree: Path, branch: str, links: list[str]) -> None:
        """The worktree, its branch and the links in it in `risorse.md`, the moment they exist
        (D-12, R-9): a link goes with the worktree, and its row says so."""
        path = self.folder / X.RESOURCES
        text = path.read_text(encoding="utf-8") if path.is_file() else \
            "| Tipo | Percorso o nome | Comando che la toglie |\n|---|---|---|\n"
        rows = [f"| worktree | {tree} | git -C {repo} worktree remove {tree} |",
                f"| ramo locale | {branch} in {repo} | git -C {repo} branch -D {branch} |"]
        rows += [f"| altro | link {tree / rel} to {repo / rel}, gone with the worktree | "
                 f"rm {tree / rel} |" for rel in links if (tree / rel).is_symlink()]
        added = [r for r in rows if r.split("|")[2].strip() not in text]
        if added:
            path.write_text(text.rstrip("\n") + "\n" + "\n".join(added) + "\n", encoding="utf-8")

    # The launch and the resume ───────────────────────────────────────────────

    def start(self) -> int:
        self.load()
        self.check_tree()
        if self.running():
            v.refuse(f"a code session of {self.ident} is running: `--status` says where it is.")
        if self.data.get("stato") == "chiuso":
            v.refuse(f"the launch of {self.ident} is closed: a change asked for after is a new "
                     "launch, prepared by the first call.")
        launch = self.launch
        if launch.get("sessione"):
            v.refuse(f"{self.ident} was launched already, session {launch['sessione']}: resume it "
                     "with `--resume`, or prepare a new launch with the first call.")
        rebase = rebase_in(self.tree)
        if rebase is None and merge_in(self.tree) is not None and not launch.get("base"):
            v.refuse(f"a merge is in progress in {self.tree} that no `--join-base` made: it is "
                     f"the person's to conclude or abort (`git -C {self.tree} merge --abort`), "
                     "and nothing is launched until then.")
        diverged = launch.get("divergente")
        if diverged and rebase is None:
            here = _out(self.tree, "rev-parse", "HEAD")
            if _git_in(self.tree, "merge-base", "--is-ancestor", diverged["remoto_sha"],
                       here).returncode != 0 and here != diverged["remoto_sha"]:
                v.refuse(f"{self.data['ramo']} and its remote diverge, and nothing was chosen: "
                         "the first call printed the commands -- join or keep the remote, or, "
                         "over a join of the base not pushed, keep the remote and join the base "
                         "again (V-6).")
        if claude_binary() is None:
            v.refuse("`claude` is not on the PATH: the launch needs the command line.")
        self.check_subscription()
        launch["sessione"] = str(uuid.uuid4())
        commands = brief_commands((self.folder / X.BRIEF).read_text(encoding="utf-8"))
        rules = granted(v.FRAMEWORK, commands)
        # History, and withheld as every value: a test the brief names may carry one.
        launch["concessi"] = [_withhold(r) for r in rules]
        return self.run(self.first_prompt(commands, rebase), rules, resume=False)

    def resume(self, allow: list[Path], reply: Path | None) -> int:
        self.load()
        self.check_tree()
        if self.data.get("stato") == "chiuso":
            v.refuse(f"the launch of {self.ident} is closed: a change asked for after is a new "
                     "launch, prepared by the first call.")
        launch = self.launch
        if not launch.get("sessione"):
            v.refuse(f"{self.ident} is prepared and not launched: `--launch` first.")
        if self.running():
            v.refuse(f"a code session of {self.ident} is running: `--status` says where it is.")
        if self.recover():
            # A stop nobody had said: said now, above, and the person answers it before any
            # resume (§4). Nothing is launched.
            print("Nothing is resumed: this stop is the person's to answer first, then resume "
                  "with what it asks for.")
            return 0
        if claude_binary() is None:
            v.refuse("`claude` is not on the PATH: the resume needs the command line.")
        self.check_subscription()
        last = (launch.get("tranche") or [{}])[-1]
        # Only what the last stop proposed, each written whole (S-5): never a prefix, a pattern
        # or a rule for a push. A file holding one rule alone may span lines, as a commit
        # message does; otherwise it holds one rule per line.
        proposed = set(last.get("proposte") or [])
        rules: list[str] = []
        for f in allow:
            try:
                text = f.read_text(encoding="utf-8").strip()
            except OSError as e:
                v.refuse(f"--allow {f}: {e}")
            rules += [text] if _withhold(text) in proposed else \
                [line.strip() for line in text.splitlines() if line.strip()]
        for rule in rules:
            if _withhold(rule) not in proposed:
                v.refuse(f"--allow: {rule!r} is not a rule the last stop proposed. A yes grants "
                         "the action denied, written whole as the stop said it, for the next run "
                         "only: nothing is resumed.")
        answer = None
        if reply is not None:
            try:
                answer = reply.read_text(encoding="utf-8").strip()
            except OSError as e:
                v.refuse(f"--reply {reply}: {e}")
        commands = brief_commands((self.folder / X.BRIEF).read_text(encoding="utf-8"))
        base = granted(v.FRAMEWORK, commands)
        # What comes after, with a rebase in progress, is its step, not the brief.
        rebase = rebase_in(self.tree)
        merging = merge_in(self.tree)
        then = (self._rebase_lines(rebase, commands) if rebase is not None else
                self._merge_lines(merging, commands) if merging is not None else
                "Go on with the brief.")
        if rules:
            launch.setdefault("approvate", []).append({"quando": _now(),
                                                       "regole": [_withhold(r) for r in rules]})
            prompt = ("Your person approved what you asked: " + "; ".join(rules) + ". Run it as "
                      "you wrote it -- it is granted for this run only. " + then)
        elif answer is not None:
            prompt = ("The answer to your question, from the documentation session:\n\n"
                      f"{answer}\n\n{then}")
        elif last.get("continua"):
            prompt = self.after_continue(commands)
        else:
            # After a stop with nothing to approve or answer: an account that lets it go on
            # again, or a block of the guard or of a hook, which no rule approves.
            prompt = ("The documentation session resumes you where you stopped: nothing new is "
                      "approved, and there is no answer to give. " + then)
        return self.run(prompt, [*base, *rules], resume=True)

    def first_prompt(self, commands: dict, rebase: Rebase | None) -> str:
        brief = self.folder / X.BRIEF
        merging = merge_in(self.tree)
        # With a rebase in progress its stopped step comes before everything else (R-22), and
        # so does a merge of the base (V-5).
        first = ("read it, and execute it once the step of the rebase below is done"
                 if rebase is not None else
                 "read it, and execute it once the merge below is concluded"
                 if merging is not None else "read it first and execute it")
        lines = [f"You are the code session of {self.ident}, launched by the documentation "
                 f"session of its project. Your brief is {brief}: {first}. "
                 f"You work in {self.tree}, on the branch {self.data['ramo']}, checked out "
                 f"already; you deliver into {self.folder}, under the fixed names the brief "
                 "lists.",
                 "If an action is denied to you, do not look for another way to do it: stop, "
                 "and say in your final answer what you need and why. The documentation "
                 "session asks your person and resumes you.",
                 "Pushing and opening the merge request are not yours: the session that "
                 "launched you does them.",
                 f"A question for your person: ask it, write it also in {self.folder / X.QUESTIONS}"
                 ", one entry per question with the day, and stop.",
                 "One command per Bash call; change files with Edit or Write, not with the "
                 "shell; add files to the index by name, never with `git add -A` or `git add .`."]
        links = self.launch.get("collegati") or []
        if links:
            lines.append("Linked from the main checkout, read and never written: "
                         + ", ".join(links) + ".")
        lines += self._strangers()
        if rebase is not None:
            lines.insert(1, self._rebase_lines(rebase, commands))
        elif merging is not None:
            lines.insert(1, self._merge_lines(merging, commands))
        elif self.launch.get("base"):
            lines.insert(1, self._joined_lines())
        return "\n\n".join(lines)

    def _merge_lines(self, conflicted: list[str], commands: dict) -> str:
        generated = [f for f, _ in commands.get("generated", [])]
        text = (f"The documentation session joined {self.launch.get('base') or 'the base'} into "
                "your branch on your person's yes, and the merge stopped on conflicts"
                + (f" in {', '.join(conflicted)}" if conflicted else ", resolved already")
                + ". Before anything else: resolve them, keeping what both sides meant -- the "
                "base's changes and yours --; add the files you resolved with git add, by "
                "name; then try `git commit` and stop: the documentation session concludes the "
                "merge on your person's yes.")
        if generated:
            text += (" Do not write the generated files (" + ", ".join(generated) + "), nor add "
                     "them: the documentation session regenerates them.")
        return text

    def _rebased(self) -> bool:
        """Whether this launch's join of the base re-applied the branch on it (V-7) -- and, with
        a rebase in progress, whether that rebase is it, and not R-26's on the remote's."""
        if not (self.launch.get("base") and self.launch.get("modo") == "rebase"):
            return False
        if rebase_in(self.tree) is None:
            return True
        onto = _rebase_says(self.tree, "onto")
        theirs = _out(self.tree, "rev-parse", "--verify", "-q",
                      f"refs/remotes/origin/{self.data.get('ramo')}")
        return not (onto and theirs and _git_in(self.tree, "merge-base", "--is-ancestor", onto,
                                                theirs).returncode == 0)

    def _joined_lines(self) -> str:
        done = (f"re-applied your branch's commits on {self.launch.get('base')}, as the code is "
                "merged by a rebase," if self._rebased() else
                f"joined {self.launch.get('base')} into your branch")
        return (f"The documentation session {done} on your person's yes: the base's commits are "
                "listed below as not yours. The brief's work may be done already: verify again "
                "as the brief says, on the branch as it is now, and deliver the verification "
                "again.")

    def _strangers(self, on_base: bool | None = None) -> list[str]:
        """The commits the code session did not make. `on_base`, once a rebase is over, says
        whether it was the one on the base, which the branch no longer tells (`sulla_base`)."""
        shas = self.launch.get("estranei") or []
        if not shas:
            return []
        # The base joined may bring many (V-5): the last thirty, and how many more. The base's
        # stand first in the list, so that those made on this branch are among the thirty.
        shown = [_out(self.tree, "log", "-1", "--format=%h %s", s) or s[:12] for s in shas[-30:]]
        more = f", and {len(shas) - 30} before them" if len(shas) > 30 else ""
        # Re-applied on the base (V-7), those that were on the branch before have new ids.
        moved = (" Re-applied on the base, those of them that were on this branch before have "
                 "new ids now, with the same subjects."
                 if (self._rebased() if on_base is None else on_base) else "")
        return ["Commits on this branch that are not yours, made elsewhere or on the forge: "
                + "; ".join(shown) + more + "." + moved + " Read them before you change what "
                "they touched."]

    def _rebase_lines(self, rebase: Rebase, commands: dict) -> str:
        generated = [f for f, _ in commands.get("generated", [])]
        # On the base, where the code is merged by a rebase (V-7), or on the remote's (R-26).
        on = (f"your commits are being re-applied on the base, {self.launch.get('base')}, as "
              "the code is merged by a rebase" if self._rebased() else
              "your local commits are being re-applied on the remote's")
        text = (f"A rebase is in progress in your worktree: {on}, and it stopped at step "
                f"{rebase.step} of "
                f"{rebase.of}, re-applying {rebase.commit} \"{rebase.subject}\". Before anything "
                f"else: resolve the conflicts of this step"
                + (f" ({', '.join(rebase.conflicted)})" if rebase.conflicted else "")
                + ", keeping what both sides meant; add the files you resolved with git add, "
                "by name; then try `git rebase --continue` and stop.")
        if generated:
            text += (" Do not write the generated files (" + ", ".join(generated) + "), nor add "
                     "them: the documentation session regenerates them.")
        return text

    def after_continue(self, commands: dict) -> str:
        if (self.launch.get("tranche") or [{}])[-1].get("unione"):
            # The commit that concludes the merge of the base (V-5).
            if merge_in(self.tree) is not None:
                v.refuse(f"the merge of the base in {self.tree} is not concluded: the commit did "
                         "not conclude it. Read what git said, and ask the person; nothing is "
                         "resumed.")
            # Gone and not in the branch: aborted, which leaves the branch without the base.
            onto = (self.launch.get("tranche") or [{}])[-1].get("onto")
            here = _out(self.tree, "rev-parse", "HEAD")
            if onto and _git_in(self.tree, "merge-base", "--is-ancestor", onto, here).returncode:
                v.refuse(f"the merge of the base in {self.tree} was aborted: the branch does not "
                         f"hold {self.launch.get('base') or 'the base'}. The first call joins it "
                         "again with `--join-base merge`, on the person's yes, and a new launch "
                         "gives "
                         "the code session what stops; nothing is resumed.")
            return " ".join([f"The documentation session concluded the merge of "
                             f"{self.launch.get('base') or 'the base'} into your branch, on your "
                             "person's yes.", *self._strangers(False), "Verify again as the brief "
                             "says, on the branch as it is now, and deliver the verification "
                             "again."])
        rebase = rebase_in(self.tree)
        stopped = (self.launch.get("tranche") or [{}])[-1].get("passo")
        if rebase is not None and stopped == [rebase.step, rebase.commit]:
            # A `--continue` that did not move the rebase -- a step left with nothing to commit,
            # a file still in conflict -- is not one the code session can be told of.
            v.refuse(f"the rebase in {self.tree} is still at step {rebase.step} of {rebase.of}, "
                     f"re-applying {rebase.commit}, where the code session stopped: the `git "
                     "rebase --continue` did not move it. Read what git said, and ask the person; "
                     "nothing is resumed. A rebase aborted and joined again, which stops on the "
                     "same step, is a new launch: the first call prepares it, and `--launch` "
                     "gives the code session that step.")
        if rebase is not None:
            return ("The documentation session ran `git rebase --continue` on your person's yes. "
                    + self._rebase_lines(rebase, commands))
        # Gone: finished, by a `--continue` or a `--skip` the person chose; aborted, which
        # leaves the branch without the commit it re-applied on, diverging as before; or
        # aborted and the remote kept, `reset --keep`, which leaves the remote's commits alone
        # and none of the code session's. The text says what to read, not which of the two.
        onto = (self.launch.get("tranche") or [{}])[-1].get("onto")
        here = _out(self.tree, "rev-parse", "HEAD")
        on_base = bool((self.launch.get("tranche") or [{}])[-1].get("sulla_base"))
        if onto and _git_in(self.tree, "merge-base", "--is-ancestor", onto, here).returncode:
            v.refuse(f"the rebase in {self.tree} was aborted: the branch holds its own commits "
                     "again, without " + ("the base. The first call re-applies them on it again "
                                          "with `--join-base rebase`, on the person's yes (V-7)"
                                          if on_base else
                                          "the remote's. The first call proposes again to join "
                                          "them or keep the remote (R-19)")
                     + "; nothing is resumed.")
        if on_base:
            return " ".join([f"The documentation session finished re-applying your commits on "
                             f"{self.launch.get('base')}, on your person's yes.",
                             *self._strangers(True), "Verify again as the brief says, on the "
                             "branch as it is now, and deliver the verification again."])
        return " ".join(["The rebase is over, by what the documentation session ran with your "
                         "person: finished, or given up to keep the remote's commits alone.",
                         *self._strangers(False), "Read with git log which of your commits the "
                         "branch holds, and go on with the brief from there."])

    def run(self, prompt: str, rules: list[str], resume: bool) -> int:
        """One run of the code session, from a launch or a resume to its stop."""
        claude = claude_binary()
        launch = self.launch
        runs = launch.setdefault("tranche", [])
        sid = launch["sessione"]
        outputs = outputs_folder()
        outputs.mkdir(parents=True, exist_ok=True)
        try:
            outputs.chmod(0o700)               # the person's alone: an output holds what B read
        except OSError:
            pass
        out = outputs / f"{self.ident}-{sid[:8]}-{len(runs) + 1}.jsonl"
        settings = {"sandbox": {"autoAllowBashIfSandboxed": False}}
        dirs = _person_allowed_dirs()
        if dirs:
            settings["pluginConfigs"] = {"framework-data-ai@inline":
                                         {"options": {"allowed_dirs": dirs}}}
        cmd = [claude, "-p", prompt, *(["--resume", sid] if resume else ["--session-id", sid]),
               "--permission-mode", "dontAsk", "--plugin-dir", str(v.FRAMEWORK),
               "--add-dir", str(self.folder), "--settings", json.dumps(settings),
               "--output-format", "stream-json", "--verbose", "--allowedTools", *rules]
        env = {k: val for k, val in os.environ.items() if k not in DROPPED_ENV}
        held = [_withhold(r) for r in rules]
        run = {"come": "ripresa" if resume else "lancio", "inizio": _now(), "fine": None,
               "fermata": None, "uscita": str(out),
               "regole": [r for r in held if r not in launch["concessi"]]}
        runs.append(run)
        written = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with open(written, "w", encoding="utf-8") as fo, open(os.devnull) as fi:
            try:
                proc = subprocess.Popen(cmd, cwd=self.tree, stdin=fi, stdout=fo,
                                        stderr=subprocess.STDOUT, env=env,
                                        start_new_session=True)
            except OSError as e:
                runs.pop()
                if not resume:                 # a session never started is no session
                    launch["sessione"] = None
                self.save()
                out.unlink(missing_ok=True)
                v.refuse(f"{claude} could not be started: {e}. Nothing is launched.")
        run["processo"] = proc.pid
        self.data["stato"] = "in corso"
        self.save()
        print(f"{self.ident}: the code session runs (session {sid}, run {len(runs)}, process "
              f"{proc.pid}); its output goes to {out}.", flush=True)
        source = None
        while proc.poll() is None:
            if source is None:
                source = self._source(out)
                if source not in (None, "none"):
                    for sig in (signal.SIGTERM, signal.SIGKILL):
                        try:
                            os.killpg(proc.pid, sig)
                        except ProcessLookupError:      # it ended meanwhile
                            break
                        try:
                            proc.wait(timeout=30)
                            break
                        except subprocess.TimeoutExpired:
                            continue
                    proc.wait()
                    break
            time.sleep(0.2)
        # The first event is read again from the output by `finish`: a run that ended between
        # two looks, or is read back later, passes the same check (T-2).
        return self.finish(run, credential=source if source not in (None, "none") else None)

    @staticmethod
    def _source(out: Path) -> str | None:
        """Where the code session's credential comes from, as its first event says: `none` is
        the person's subscription. A first event that does not say is not the subscription
        either (T-2): the empty string, which the stop says as such."""
        try:
            with open(out, encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        e = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(e, dict) and e.get("type") == "system" \
                            and e.get("subtype") == "init":
                        source = e.get("apiKeySource")
                        return str(source) if source else ""
        except OSError:
            return None
        return None

    def recover(self) -> bool:
        """A run whose end was never written -- the command that waited for it was closed --
        is closed now from its output, if its process has ended, and its stop said. Whether one
        was."""
        runs = self.launch.get("tranche") or []
        if runs and not runs[-1].get("fine") \
                and _alive(runs[-1].get("processo"), self.launch.get("sessione"),
                           runs[-1].get("uscita")) is False:
            self.finish(runs[-1], credential=None, quiet=False, recovered=True)
            return True
        return False

    def finish(self, run: dict, credential: str | None, quiet: bool = False,
               recovered: bool = False) -> int:
        out = self.check_output(run.get("uscita"))
        if credential is None and out is not None and out.is_file():
            source = self._source(out)
            if source not in (None, "none"):
                credential = source
        events, other = [], []
        if out is not None and out.is_file():
            for line in out.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    e = json.loads(line)
                except ValueError:
                    e = None
                if isinstance(e, dict):
                    events.append(e)
                elif line.strip():
                    other.append(line)
        stop, said = self.classify(events, run, credential)
        result = next((e for e in reversed(events) if e.get("type") == "result"), {})
        # With no answer, what the command line wrote outside its events -- an option it
        # refused, an error at its start -- is the only word of the run, and the output that
        # holds it is deleted below.
        answer = str(result.get("result") or "") or "\n".join(other[-20:])
        step = bool(said.get("continue")) and said.get("rebase") is not None
        joining = bool(said.get("continue")) and said.get("rebase") is None \
            and said.get("merge") is not None
        run.update({"fine": _now(), "fermata": stop,
                    "negate": [_withhold(d) for d in said.get("denied_raw", [])],
                    "risposta": _withhold(answer)[:2000],
                    # The rules the stop proposes, the only ones `--allow` takes (S-5).
                    "proposte": [_withhold(r) for _, _, r in said.get("denied", []) if r],
                    # Whether it stopped on the commit of a step of a rebase, which step, and the
                    # commit the rebase re-applies on: the resume after says what became of it
                    # (R-27).
                    "continua": step or joining,
                    # Or on the commit that concludes the merge of the base (V-5), with the
                    # commit it joins: the resume after tells concluded from aborted.
                    "unione": joining,
                    # And, a step of a rebase, whether it is the one on the base (V-7), told
                    # while it runs: once it is over, nothing in git tells it from R-26's.
                    "sulla_base": self._rebased() if step else None,
                    "passo": [said["rebase"].step, said["rebase"].commit] if step else None,
                    "onto": _rebase_says(self.tree, "onto") if step else
                    _out(self.tree, "rev-parse", "--verify", "-q", "MERGE_HEAD") if joining
                    else None})
        run.pop("processo", None)
        self.data["stato"] = "fermo"
        self.save()
        if out is not None and out.is_file():
            out.unlink()
        if not quiet:
            self.say(stop, said, answer, recovered)
        return 0

    def classify(self, events: list[dict], run: dict, credential: str | None):
        """The stop, of the five, and what to say of it."""
        said: dict = {"denied": [], "guard": [], "hook": [], "not_b": [], "continue": [],
                      "denied_raw": []}
        if credential is not None:
            where = (f"its credential came from `{credential}`" if credential else
                     "its first event did not say where its credential comes from")
            said["account"] = (f"the code session was not on the person's subscription: {where}, "
                               "and it was stopped at its start. It runs on the subscription "
                               "alone: remove that credential for it, then resume it "
                               "(`--resume`); where the resume does not start, a new launch "
                               "from the first call.")
            return "account", said
        result = next((e for e in reversed(events) if e.get("type") == "result"), None)
        if result is None:
            said["fine"] = ("the code session ended without an answer; what the command line "
                            "wrote, if anything, is its answer below")
            return "fine", said
        # An error of the account -- a limit of the subscription, a credential refused -- comes
        # with `is_error` and the subtype `success` (trial of 9/11); a subtype `error_...` is an
        # error of the run, said at `fine` unless actions were denied.
        failed = str(result.get("subtype", ""))
        if result.get("is_error") and not failed.startswith("error"):
            said["account"] = str(result.get("result") or "an error of the account")
            return "account", said
        texts: dict[str, str] = {}
        for e in events:
            m = e.get("message")
            content = m.get("content") if isinstance(m, dict) else None
            for c in content if isinstance(content, list) else []:
                if isinstance(c, dict) and c.get("type") == "tool_result":
                    body = c.get("content")
                    texts[str(c.get("tool_use_id"))] = body if isinstance(body, str) else \
                        json.dumps(body, ensure_ascii=False)
        rebase = rebase_in(self.tree)
        said["rebase"] = rebase
        said["merge"] = merge_in(self.tree)
        # With a rebase in progress a commit is the commit of its step, which is the
        # documentation session's (R-27); with a merge of the base in progress, the commit that
        # concludes it (V-5).
        stepping = rebase is not None or said["merge"] is not None
        steps = (CONTINUE, COMMIT) if stepping else (CONTINUE,)
        for d in result.get("permission_denials") or []:
            if not isinstance(d, dict):
                continue
            tool = str(d.get("tool_name"))
            given = d.get("tool_input") or {}
            what = str(given.get("command") or given.get("file_path") or
                       given.get("notebook_path") or json.dumps(given, ensure_ascii=False))
            text = texts.get(str(d.get("tool_use_id")), "")
            said["denied_raw"].append(f"{tool}: {what}")
            if GUARD_SAYS in text:
                said["guard"].append((tool, what))
            elif "hook error" in text:
                said["hook"].append((tool, what, text[:300]))
            elif tool == "Bash":
                parts = [p for p in SEPARATORS.split(what) if p.strip()] or [what]
                if all(NOT_B.search(p) for p in parts):
                    said["not_b"].append(what)
                elif all(any(s.search(p) for s in steps) for p in parts):
                    said["continue"].append(what)
                elif NOT_B_ANYWHERE.search(what) or (stepping
                                                     and COMMIT_ANYWHERE.search(what)):
                    # A push, a merge request or the commit of a step among other commands, or
                    # inside another shell: no rule for the line, which would grant it too.
                    said["denied"].append((tool, what, None))
                else:
                    said["denied"].append((tool, what, f"Bash({what})"))
            else:
                # The narrowest rule Claude Code writes for the tool: a domain for a fetch.
                url = given.get("url") if tool == "WebFetch" else None
                host = re.match(r"^[A-Za-z][\w+.-]*://([^/:?#@]+)", url) \
                    if isinstance(url, str) else None
                said["denied"].append((tool, what,
                                       f"WebFetch(domain:{host.group(1)})" if host else tool))
        began = _when(run.get("inizio"))
        questions = self.folder / X.QUESTIONS
        if questions.is_file() and began and \
                datetime.fromtimestamp(questions.stat().st_mtime).astimezone() >= began:
            # Said with any stop of this run: the next run reads only its own.
            said["domanda"] = self._last_question(questions)
        if said["denied"] or said["guard"] or said["hook"] or said["continue"]:
            return "negata", said
        if failed.startswith("error"):
            said["fine"] = (f"the run ended on an error of its own, `{failed}`, not of the "
                            "account" + (f": {result.get('result')}" if result.get("result")
                                         else ""))
            return "fine", said
        if said.get("domanda"):
            return "domanda", said
        launched = _when(self.launch.get("inizio"))
        delivered = []
        for name, kind in X.DELIVERED.items():
            p = self.folder / name
            if not p.exists():
                continue
            files = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file()]
            newest = max((f.stat().st_mtime for f in files), default=None)
            if newest is not None and (launched is None or
                                       datetime.fromtimestamp(newest).astimezone() >= launched):
                delivered.append(name + ("/" if kind == "dir" else ""))
        if delivered and not stepping:
            said["consegna"] = delivered
            return "consegna", said
        return "fine", said

    @staticmethod
    def _last_question(path: Path) -> str:
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        blocks = re.split(r"(?m)^(?=#{1,6}\s|-\s+\d{4}-\d\d-\d\d|\d{4}-\d\d-\d\d)", text)
        return (blocks[-1] if blocks else text).strip()[:1500]

    def _say_merge(self, asked: list[str], conflicted: list[str]) -> None:
        """The commit that concludes the merge of the base, which the code session asked for and
        the documentation session makes on the person's yes (V-5), in the order of a step of a
        rebase: the generated files it touches regenerated, the question, the commit, the
        preparation, the resume."""
        try:
            commands = brief_commands((self.folder / X.BRIEF).read_text(encoding="utf-8"))
        except OSError:
            commands = {k: [] for k in COMMAND_KINDS}
        t = self.tree
        for what in asked:
            print(f"  denied: Bash `{what}`, the commit that concludes the merge of the base: "
                  "never a rule of the code session's (V-5).")
        print(f"  The merge of {self.launch.get('base') or 'the base'} into "
              f"{self.data.get('ramo')}" + (f"; still in conflict: {', '.join(conflicted)}"
                                           if conflicted else "") + ".")
        # In conflict still, or changed by the base the merge joins: one already added with its
        # markers is no longer in conflict, and would enter the merge's commit (as R-25).
        touched = set(conflicted) | set(_out(t, "diff", "--name-only",
                                             "HEAD...MERGE_HEAD").splitlines())
        held = [(f, how) for f, how in commands["generated"] if f in touched]
        if held:
            print("  Before the question, in view, the generated files of the merge:")
            for f, how in held:
                print(f"    (in {t}) {how or '<the command the brief names for it>'}, then "
                      f"git -C {t} add {f}")
        print("  The question to the person, with what the merge would commit, read by you:")
        print(f"    git -C {t} status --short; git -C {t} diff --cached --stat; each file "
              f"against the branch, git -C {t} diff --cached HEAD -- <file>, and against the "
              f"base, git -C {t} diff --cached MERGE_HEAD -- <file>")
        print("  On the yes, in view:")
        print(f"    GIT_EDITOR=true git -C {t} -c rerere.enabled=false commit --no-edit")
        if commands["prepare"]:
            print("    the preparation on the merged tree: "
                  + "; ".join(f"(in {t}) {c}" for c in commands["prepare"]))
        # Pushed at once, before the code session goes on (V-6): kept here until the delivery,
        # a commit pushed meanwhile on the merge request would make the two diverge, and the
        # merge cannot be joined to it by a rebase.
        branch = self.data.get("ramo")
        print(f"    the push of the merge, at once: git -C {t} push origin {branch}; refused, "
              f"the remote moved meanwhile: keep the remote, git -C {t} reset --keep "
              f"origin/{branch}, and join the base again the same way, the first call with "
              "`--join-base merge` (V-6)")
        print("    then resume with neither --allow nor --reply.")

    def _say_step(self, asked: list[str], rebase: Rebase | None) -> None:
        """The commit of a step of the rebase, which the code session asked for and the
        documentation session makes, in its order (§4, R-25, R-27): the generated files the step
        holds in conflict regenerated, the question with what the step would commit, the
        `--continue` on the yes, the preparation once the rebase is finished, the resume."""
        try:
            commands = brief_commands((self.folder / X.BRIEF).read_text(encoding="utf-8"))
        except OSError:
            commands = {k: [] for k in COMMAND_KINDS}
        t = self.tree
        for what in asked:
            print(f"  denied: Bash `{what}`, the commit of the step of the rebase: never a rule "
                  "of the code session's (R-27).")
        if rebase is None:
            print("  No rebase is in progress: there is no step to commit.")
            return
        print(f"  The step: {rebase.step} of {rebase.of}, re-applying {rebase.commit} "
              f"\"{rebase.subject}\"" + (f"; still in conflict: {', '.join(rebase.conflicted)}"
                                         if rebase.conflicted else "") + ".")
        # In conflict still, or changed by the commit the step re-applies: one already added
        # with its markers is no longer in conflict, and would enter the step's commit.
        touched = set(rebase.conflicted) | set(_out(t, "diff", "--name-only", "REBASE_HEAD~1",
                                                    "REBASE_HEAD").splitlines())
        held = [(f, how) for f, how in commands["generated"] if f in touched]
        if held:
            print("  Before the question, in view, the generated files of the step:")
            for f, how in held:
                print(f"    (in {t}) {how or '<the command the brief names for it>'}, then "
                      f"git -C {t} add {f}")
        print("  The question to the person, with what the step would commit, read by you:")
        print(f"    git -C {t} status --short; git -C {t} diff --cached --stat")
        print(f"    the files of the step: git -C {t} diff --name-only REBASE_HEAD~1 REBASE_HEAD; "
              f"each against the remote's side, git -C {t} diff --cached HEAD -- <file>, and "
              f"against the local commit, git -C {t} diff --cached REBASE_HEAD -- <file>")
        print("  On the yes, in view:")
        # The next steps are applied by this command: without `rerere` too, as the join.
        print(f"    GIT_EDITOR=true git -C {t} -c rerere.enabled=false rebase --continue")
        if commands["prepare"]:
            print("    if that finished the rebase, the preparation on the final tree: "
                  + "; ".join(f"(in {t}) {c}" for c in commands["prepare"]))
        lease = self.launch.get("lease") if self._rebased() else None
        if self._rebased() and not lease:
            print(f"    if that finished the rebase on the base, the push: git -C {t} push -u "
                  f"origin {self.data.get('ramo')}")
        if lease:
            # Re-applied on the base (V-7): the branch's commits are rewritten, and the push of
            # them is forced, at the remote's commit the rebase began from.
            branch = self.data.get("ramo")
            print(f"    if that finished the rebase on the base, the push, forced with lease, on "
                  f"the person's yes: git -C {t} push --force-with-lease=refs/heads/"
                  f"{branch}:{lease} origin {branch}; refused, the remote moved meanwhile: keep "
                  f"the remote, git -C {t} reset --keep origin/{branch}, and join the base "
                  "again, the first call with `--join-base rebase` (V-6)")
        print("    then resume with neither --allow nor --reply.")

    def say(self, stop: str, said: dict, answer: str, recovered: bool = False) -> None:
        runs = self.launch.get("tranche") or []
        print(f"{self.ident}: stopped on `{stop}`" + (" (read again from its output)"
                                                      if recovered else "")
              + f", run {len(runs)} of this launch, session {self.launch.get('sessione')}.")
        for tool, what, rule in said.get("denied", []):
            if rule is None:
                print(f"  denied: {tool} `{what}`\n    it names a push, a merge request or, "
                      "with a rebase or a merge of the base in progress, the commit of its "
                      "step -- among other "
                      "commands, inside another shell, or in the text of a message --, and no "
                      "rule is proposed for it: on the person's yes to the rest, resume with "
                      "`--reply` asking it to run what it needs without them, one command per "
                      "call, with a message that does not name them.")
            else:
                print(f"  denied: {tool} `{what}`\n    on the person's yes, resume with the "
                      f"rule: {rule}")
        if said.get("continue") and said.get("rebase") is None \
                and said.get("merge") is not None:
            self._say_merge(said["continue"], said["merge"])
        elif said.get("continue"):
            self._say_step(said["continue"], said.get("rebase"))
        for tool, what in said.get("guard", []):
            print(f"  stopped by the framework's write guard: {tool} {what}. No rule approves "
                  "it: the code session proposes what the documentation should say in "
                  "`documentazione.md`, and writes nothing outside its places.")
        for tool, what, text in said.get("hook", []):
            print(f"  stopped by a hook of the person's, not the framework's: {tool} {what}: "
                  f"{text}")
        for what in said.get("not_b", []):
            print(f"  not the code session's, and no question: `{what}`. The documentation "
                  "session pushes and opens the merge request, on the person's yes.")
        if stop == "account":
            print(f"  {said.get('account')}")
        if stop == "fine" and said.get("fine"):
            print(f"  {said['fine']}")
        if said.get("domanda"):
            print(f"  the question, from {X.QUESTIONS}"
                  + ("" if stop == "domanda" else ", asked in this run too") + ":\n    "
                  + said["domanda"].replace("\n", "\n    "))
        if stop == "consegna":
            print(f"  delivered in {self.folder}: {', '.join(said['consegna'])}")
        rebase = said.get("rebase")
        if rebase is not None:
            print(f"  a rebase is in progress in {self.tree}, at step {rebase.step} of "
                  f"{rebase.of} ({rebase.commit} \"{rebase.subject}\"): no delivery until it is "
                  "finished or aborted.")
        elif said.get("merge") is not None:
            print(f"  a merge of the base is in progress in {self.tree}: no delivery until it is "
                  "concluded.")
        if answer:
            print("  the code session's answer:\n    " + answer[:1500].replace("\n", "\n    "))

    def status(self) -> int:
        self.load()
        self.check_tree()
        self.recover()
        launch = self.launch
        runs = launch.get("tranche") or []
        live = self.running()
        print(f"{self.ident}: {self.data.get('stato')}, worktree {self.tree} on "
              f"{self.data.get('ramo')}, launch {len(self.data['lanci'])}, session "
              f"{launch.get('sessione') or 'not launched'}, {len(runs)} run(s).")
        if live:
            print(f"  running since {live.get('inizio')}, process {live.get('processo')}.")
        elif runs:
            last = runs[-1]
            print(f"  last stop: `{last.get('fermata')}` at {last.get('fine')}.")
        rebase = rebase_in(self.tree)
        if rebase is not None:
            print(f"  a rebase is in progress, at step {rebase.step} of {rebase.of}.")
        elif merge_in(self.tree) is not None:
            print("  a merge of the base is in progress.")
        return 0


def launch_state(folder: Path, today: date) -> str | None:
    """How the listing says an element's launch stands: running, or stopped on what since when."""
    try:
        data = json.loads((folder / X.LAUNCH).read_text(encoding="utf-8"))
    except OSError:
        return None
    except (ValueError, RecursionError):
        data = None
    if _launch_shape(data) is not None:
        return "launch file not as `code` writes it: its first call writes a new one"
    runs = data["lanci"][-1].get("tranche") or []
    session = data["lanci"][-1].get("sessione")
    if not runs:
        return "launch prepared"
    last = runs[-1]
    if not last.get("fine"):
        alive = _alive(last.get("processo"), session, last.get("uscita"))
        if alive is None:
            return "a run of the code session not ended, whether it runs not told here"
        return "code session running" if alive \
            else "code session ended, its stop not read yet (--status)"
    when = _when(last.get("fine"))
    return f"stopped on {last.get('fermata')}" + (f" {ago(when.date(), today)}" if when else "")


def _join_into(folder: Path, target: Path, block: int) -> None:
    """A second integration into the folder of the first: a part delivered again takes the
    place of the one with its name -- the one before stays reachable from the commit of the
    block before, which says where it went --, and `evidenze/` and `sessioni/` add up, a file
    whose name is taken getting the number of its block. What the sessions wrote about the work
    no commit keeps, so it adds up too: the rows of `risorse.md` the first launch listed, the
    entries of `domande.md`. The brief and the launch file of the new launch already carry what
    came before them."""
    for entry in sorted(folder.iterdir()):
        dest = target / entry.name
        if entry.name in (X.RESOURCES, X.QUESTIONS) and entry.is_file() and dest.is_file():
            old = dest.read_text(encoding="utf-8", errors="replace")
            new = entry.read_text(encoding="utf-8", errors="replace")
            if entry.name == X.RESOURCES:
                known = {line.strip() for line in old.splitlines()}
                added = [line for line in new.splitlines() if line.strip().startswith("|")
                         and line.strip() not in known]
                text = old.rstrip("\n") + ("\n" + "\n".join(added) if added else "") + "\n"
            else:
                text = old.rstrip("\n") + "\n\n" + new.lstrip("\n")
            dest.write_text(text, encoding="utf-8")
            entry.unlink()
            continue
        if entry.is_dir() and dest.is_dir():
            for f in sorted(p for p in entry.rglob("*") if p.is_file()):
                to = dest / f.relative_to(entry)
                if to.exists():
                    to = to.with_name(f"{to.stem}.{block}{to.suffix}")
                to.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(f), str(to))
            shutil.rmtree(entry)
            continue
        if dest.is_dir():
            shutil.rmtree(dest)
        elif dest.exists():
            dest.unlink()
        shutil.move(str(entry), str(dest))
    folder.rmdir()


def _plain(value: str) -> str:
    """A key or a place of the first block of `INTEGRATO`, as written where YAML reads it back
    the same, quoted otherwise."""
    try:
        if v.yaml.safe_load(f"x: {value}") == {"x": value}:
            return value
    except v.yaml.YAMLError:
        pass
    return json.dumps(value, ensure_ascii=False)


def _blocks_text(blocks: list[dict]) -> str:
    """`INTEGRATO` as a list of blocks, one per integration, every string quoted: a commit of
    digits and one `e` would read as a number, and a place with `: ` in it as a mapping."""
    def q(value) -> str:
        return json.dumps(value.isoformat() if isinstance(value, date) else str(value),
                          ensure_ascii=False)
    out = []
    for b in blocks:
        out.append(f"- commit: {q(b.get('commit'))}")
        out.append(f"  date: {b.get('date').isoformat() if isinstance(b.get('date'), date) else b.get('date')}")
        parts = b.get("parts") or {}
        out.append("  parts:" + ("" if parts else " {}"))
        out += [f"    {q(k)}: {q(where)}" for k, where in parts.items()]
    return "\n".join(out) + "\n"


def _close_launch(target: Path) -> None:
    """The launch file goes with the folder, and says the launch closed (R-2)."""
    path = target / X.LAUNCH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError):
        return
    if isinstance(data, dict):
        data.update(stato="chiuso", chiuso=_now())
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description="What waits in the exchange between sessions")
    ap.add_argument("--root", default=".", type=Path,
                    help="the documentation repository, whose .framework/sessions.yaml declares "
                         "the exchange")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("command", nargs="?", choices=["integrate", "code"],
                    help="integrate: move one element to integrati/ and write its INTEGRATO; "
                         "code: prepare, launch, resume or say the code session of a change")
    ap.add_argument("ident", nargs="?", help="the element, as CHG-021")
    ap.add_argument("--commit", help="with integrate: the commit that integrated it, when it "
                                     "is not HEAD of --root")
    ap.add_argument("--repo", type=Path, help="with code, the first call: the code repository, "
                                              "beside the documentation")
    ap.add_argument("--base", help="with code, the first call: the start of a new branch, and "
                                   "the base it is compared with and joined from, when it is "
                                   "not the start an earlier launch recorded or, for a new "
                                   "branch, the remote's default branch")
    ap.add_argument("--no-chg", dest="no_chg", help='with code, the first call: "hotfix '
                    '<reference>", for a hotfix whose change is not written yet')
    ap.add_argument("--join-base", dest="join_base", nargs="?", const="auto",
                    choices=("auto", "merge", "rebase"),
                    help="with code, the first call, on the person's yes: join the base into "
                         "the branch, where the forge wants it up to date or its merge request "
                         "conflicts with it -- a merge, or, where the code is merged by a "
                         "rebase (`merge_method: rebase` in the additive mode, or `rebase` "
                         "given), the branch re-applied on the base; alone, or `auto`, the way "
                         "`merge_method` says, `merge` or `rebase` the one named")
    ap.add_argument("--launch", action="store_true", help="with code: launch the code session "
                                                          "prepared by the first call")
    ap.add_argument("--resume", action="store_true", help="with code: resume it after a stop")
    ap.add_argument("--allow", type=Path, action="append", default=[],
                    help="with --resume: a file holding the rule approved now, as Claude Code "
                         "writes it, Bash(<the command>); one per line")
    ap.add_argument("--reply", type=Path, help="with --resume: a file holding the answer to "
                                                "the code session's question")
    ap.add_argument("--status", action="store_true", help="with code: whether it runs, and "
                                                          "where it stopped")
    args = ap.parse_args()
    if args.command in ("integrate", "code") and not args.ident:
        ap.error(f"{args.command} takes the element's identifier")
    if args.command is None and (args.ident or args.commit):
        ap.error("an identifier and --commit go with integrate")
    forms = [bool(args.repo), args.launch, args.resume, args.status]
    if args.command == "code" and sum(forms) != 1:
        ap.error("code takes one of --repo (the first call), --launch, --resume, --status")
    if args.command != "code" and (any(forms) or args.base or args.no_chg or args.allow
                                   or args.reply or args.join_base):
        ap.error("--repo, --base, --no-chg, --join-base, --launch, --resume, --allow, --reply "
                 "and --status go with code")
    if args.command == "code" and (args.allow or args.reply) and not args.resume:
        ap.error("--allow and --reply go with --resume")
    if args.command == "code" and (args.base or args.no_chg or args.join_base) \
            and not args.repo:
        ap.error("--base, --no-chg and --join-base go with the first call, --repo")
    if args.allow and args.reply:
        ap.error("a resume carries the rules approved, or an answer: one of --allow, --reply")
    if args.command == "code" and WINDOWS:
        v.refuse("`code` launches and watches the code session with POSIX process calls, which "
                 "Windows outside WSL does not have: there, asking whether a process runs ends "
                 "it. Run it under WSL, Linux or macOS; nothing is launched.")

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
    if args.command == "code":
        code = Code(root, path, shown, args.ident)
        if args.repo:
            return code.prepare(args.repo, args.base, args.no_chg, args.join_base)
        if args.launch:
            return code.start()
        if args.resume:
            return code.resume(args.allow, args.reply)
        return code.status()
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
            in_history if repo is not None and repo.has_head else None, report,
            joined=v.rules_hold(project, v.JOINED_SINCE))
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
            "waiting": [{**row(e), "launch": launch_state(e.path, today)} for e in waiting],
            "at_a_code_session": [{**row(e), "launch": launch_state(e.path, today)}
                                  for e in working],
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
            launched = launch_state(e.path, today)
            print(f"   {e.ident:<9} {X.state(states, e.ident):<12} {', '.join(e.delivered)}"
                  + (f", waiting {waited(e.oldest, today)}" if e.oldest else ", all empty")
                  + (f"; {launched}" if launched else ""))
    if section("AT A CODE SESSION: nothing delivered yet", working):
        for e in working:
            what = f"brief written {ago(e.brief, today)}" if e.brief else "no brief"
            launched = launch_state(e.path, today)
            print(f"   {e.ident:<9} {X.state(states, e.ident):<12} {what}"
                  + (f"; {launched}" if launched else ""))
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
