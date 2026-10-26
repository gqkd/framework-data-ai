"""The exchange between sessions: where material waits outside the repositories, and until when.

A project that declares `exchange:` in `.framework/sessions.yaml` keeps there what its sessions
hand each other: the brief a documentation session writes for a code session, and what the code session
delivers back. Every rule before this one said where to put things and none said when to take
them away, so this reads the place for the two questions that answer it: what still waits, and
what should already be gone.

Read only, and only so much: names, modification times, `risorse.md`, `INTEGRATO` and the
headings of the closing declarations. Never the content of a verification, an evidence or a
copy of credentials.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import subprocess

import yaml

from .artifacts import FindingSink, as_map

INCOMING, INTEGRATED, SESSIONS = "in-arrivo", "integrati", "sessioni"
BRIEF, RESOURCES, MARK = "brief.md", "risorse.md", "INTEGRATO"
# What a code session delivers, by name. Each one is a part that `INTEGRATO` says the fate of.
DELIVERED = {"verifica.md": "file", "mr.md": "file", "mr-link.txt": "file",
             "evidenze": "dir", "contribution-policy.json": "file",
             # In the additive mode: what the documentation should say, as the code session
             # learned it, which the thread turns into effects.
             "documentazione.md": "file"}
# Written by the sessions about the work rather than delivered as its result: no part, no age.
OWN = {BRIEF: "file", RESOURCES: "file", SESSIONS: "dir"}

RESOURCE_TYPES = ("worktree", "ramo locale", "stack isolato", "volume", "immagine",
                  "copia di credenziali", "altro")
# The two kinds whose presence can be read off the disk. The others are names in a tool this
# does not run -- git in another repository, docker -- so a row there is a resource there.
ON_DISK = ("worktree", "copia di credenziali")
CREDENTIALS = "copia di credenziali"
HEADINGS = ("Committato", "Non committato", "Fuori dai repository")

ELEMENT = re.compile(r"^[A-Z]{2,3}-\d{3,}$")
DECLARATION = re.compile(r"^\d{4}-\d\d-\d\d-[A-Za-z0-9][A-Za-z0-9_.-]*\.md$")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.M)
# A value written beside a name, which is what the list must never carry: `DB_PASSWORD=...`.
VALUE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\s*=\s*\S")
KEYS = re.compile(r"\(([^()]*)\)\s*$")

# DONE, FOR THE EXCHANGE: the work an element asked for is merged, or its question answered. A
# change is done here at `implemented`, which is earlier than the digest's "closed" (it waits for
# `verified`, the Definition of Done) and on purpose: what a mandate created outside the
# repositories serves the work up to the merge, and what was delivered is integrated then.
# Every status the schemas allow is in one set or the other, and `tests/selfcheck.py` says so.
CLOSED_CHANGE = {"implemented", "verified", "rolled-back"}
OPEN_CHANGE = {"draft", "approved"}
CLOSED_ENTRY = {"decided", "superseded"}
OPEN_ENTRY = {"open", "parked"}
# What file managers leave behind, and nobody delivered.
LITTER = {"desktop.ini", "Thumbs.db"}


def declared(value, root: Path) -> tuple[Path | None, str | None]:
    """Where `exchange:` points, or why it cannot be read as a place.

    Relative to the documentation, because the value is committed and read on every machine:
    `../_scambio` is the same place beside every clone, and `/home/someone/_scambio` is a place
    on one of them. Outside the documentation, because what waits there is not committed.
    """
    if value is None:
        return None, None
    if not isinstance(value, str) or not value.strip():
        return None, ("`exchange` has to be a path, relative to the root of the documentation "
                      "repository, of a directory outside it, such as `../_scambio`.")
    text = value.strip()
    if (text.startswith("~") or PurePosixPath(text).is_absolute()
            or PureWindowsPath(text).anchor):
        return None, (f"`exchange` is {text!r}, a place on one machine. The value is committed "
                      "and read on every machine that has a clone: write it relative to the "
                      "root of the documentation repository, such as `../_scambio`.")
    root = root.resolve()
    path = (root / text).resolve()
    if path == root or path.is_relative_to(root):
        return None, (f"`exchange` is {text!r}, inside the documentation repository. What waits "
                      "there is not committed, and inside the repository it would be, or would "
                      "need an ignore rule to say it is not: put it beside the repository, such "
                      "as `../_scambio`.")
    return path, None


@dataclass
class Resource:
    kind: str
    where: str
    command: str
    line: int
    present: bool

    @property
    def secret(self) -> bool:
        """A copy of credentials whose row carries a value, which no output may repeat."""
        return self.kind == CREDENTIALS and bool(VALUE.search(self.where)
                                                 or VALUE.search(self.command))

    @property
    def shown(self) -> str:
        if self.secret:
            on_disk = _on_disk(self.where)
            return f"{on_disk or 'a copy of credentials'} (row withheld: it carries a value)"
        return self.where

    @property
    def shown_command(self) -> str:
        return "(withheld: the row carries a value)" if self.secret else self.command


@dataclass
class Element:
    ident: str
    stage: str
    path: Path
    entries: dict[str, Path]
    resources: list[Resource] = field(default_factory=list)
    oldest: date | None = None           # the oldest delivered file: since when it waits
    brief: date | None = None

    @property
    def delivered(self) -> list[str]:
        return sorted(n for n in self.entries if n in DELIVERED)


@dataclass
class Exchange:
    path: Path
    shown: str                           # how findings name it: the value as declared
    elements: list[Element] = field(default_factory=list)
    declarations: list[tuple[Path, date]] = field(default_factory=list)

    def rel(self, path: Path) -> str:
        return str(PurePosixPath(self.shown) / path.relative_to(self.path).as_posix())


def _day(seconds: float) -> date:
    return datetime.fromtimestamp(seconds).date()


def _oldest(path: Path) -> date | None:
    """The oldest modification among the files under `path`: when the delivery started waiting."""
    if path.is_file():
        return _day(path.stat().st_mtime)
    times = [p.stat().st_mtime for p in path.rglob("*") if p.is_file()]
    return _day(min(times)) if times else None


def _cells(line: str) -> list[str]:
    return [c.strip().strip("`").strip() for c in line.strip().strip("|").split("|")]


def _on_disk(where: str) -> Path | None:
    """The path a row names, without the key names written after it."""
    text = KEYS.sub("", where).strip().strip("`").strip()
    if not text:
        return None
    path = Path(os.path.expanduser(text))
    return path if path.is_absolute() else None


def resources(path: Path, rel: str, report: FindingSink) -> list[Resource]:
    """The rows of `risorse.md`, each with whether the resource is still there."""
    rows: list[Resource] = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for n, line in enumerate(lines, 1):
        if not line.strip().startswith("|"):
            continue
        cells = _cells(line)
        if all(set(c) <= set("-: ") for c in cells):
            continue                     # the separator row
        if cells and cells[0].casefold() == "tipo":
            continue                     # the header
        if len(cells) < 3 or not all(cells[:3]):
            report.add("EXC007", rel, f"line {n}: a resource needs three cells, its type, its "
                       "path or name, and the command that removes it. Without the command the "
                       "session that closes the work cannot propose the removal.")
            continue
        kind, where, command = cells[0].casefold(), cells[1], cells[2]
        if kind not in RESOURCE_TYPES:
            report.add("EXC007", rel, f"line {n}: `{cells[0]}` is not a type of resource this "
                       f"reads. One of: {', '.join(RESOURCE_TYPES)}.")
            continue
        present = True
        if kind in ON_DISK:
            on_disk = _on_disk(where)
            if on_disk is None:
                what = "the path" if kind == CREDENTIALS else f"`{where}`"
                report.add("EXC007", rel, f"line {n}: {what} is not an absolute path. A "
                           f"{kind} is read on the machine where it lives, from whatever "
                           "directory the next session starts in.")
                continue
            present = on_disk.exists()
        if kind == CREDENTIALS and not KEYS.search(where):
            report.add("EXC007", rel, f"line {n}: a copy of credentials names its path and, in "
                       "brackets after it, the names of the keys it holds -- never their "
                       "values. Without the names nobody can tell what to rotate if the copy "
                       "is found where it should not be.")
        rows.append(Resource(kind, where, command, n, present))
    return rows


def _declaration(path: Path, rel: str, report: FindingSink) -> bool:
    if not DECLARATION.match(path.name):
        report.add("EXC007", rel, "a closing declaration is named `AAAA-MM-GG-<session>.md`, "
                   "the day it was written and the session that wrote it, so that two "
                   "sessions closing the same day do not write over each other.")
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    found = {h.strip().casefold() for h in HEADING.findall(text)}
    missing = [h for h in HEADINGS if h.casefold() not in found]
    if missing:
        report.add("EXC007", rel, f"the closing declaration has no {', '.join(missing)} "
                   "section. Each of the three is what lets another session in the same "
                   "working tree commit the work of all of them without guessing whose a "
                   "line is; one written as `nothing` says so, one missing says nothing.")
    return True


def read(path: Path, shown: str, report: FindingSink) -> Exchange:
    """Every element folder and declaration, with what is wrong in their shape reported."""
    ex = Exchange(path, shown)
    try:
        inside = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"],
                                capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        inside = None
    if inside is not None and inside.returncode == 0:
        report.add("EXC006", shown, f"the exchange is inside the git repository "
                   f"{inside.stdout.strip()}: whoever commits there commits what waits here, "
                   "credentials included. It belongs outside every repository.")
    for entry in sorted(path.iterdir()):
        if entry.name.startswith(".") or entry.name in LITTER:
            continue
        if entry.name not in (INCOMING, INTEGRATED, SESSIONS) or not entry.is_dir():
            report.add("EXC006", ex.rel(entry), f"the exchange holds `{INCOMING}/`, "
                       f"`{INTEGRATED}/` and `{SESSIONS}/`, and nothing else is read: a file "
                       "here is a file nobody will look for.")
    for stage in (INCOMING, INTEGRATED):
        base = path / stage
        if not base.is_dir():
            continue
        for folder in sorted(base.iterdir()):
            if folder.name.startswith(".") or folder.name in LITTER:
                continue
            if not folder.is_dir() or not ELEMENT.match(folder.name):
                report.add("EXC006", ex.rel(folder), f"`{stage}/` holds one folder per "
                           "element, named by its identifier (`CHG-021/`), with fixed names "
                           "inside. A file named with the element's prefix is the shape this "
                           "replaced: move it into the element's folder, under its fixed name.")
                continue
            ex.elements.append(_element(ex, stage, folder, report))
    sessions = path / SESSIONS
    if sessions.is_dir():
        for f in sorted(sessions.iterdir()):
            if f.name.startswith(".") or f.name in LITTER:
                continue
            if f.is_file() and _declaration(f, ex.rel(f), report):
                ex.declarations.append((f, _day(f.stat().st_mtime)))
            elif not f.is_file():
                report.add("EXC006", ex.rel(f), f"`{SESSIONS}/` holds closing declarations, "
                           "one file per session.")
    return ex


def _element(ex: Exchange, stage: str, folder: Path, report: FindingSink) -> Element:
    allowed = {**DELIVERED, **OWN, **({MARK: "file"} if stage == INTEGRATED else {})}
    entries: dict[str, Path] = {}
    for entry in sorted(folder.iterdir()):
        if entry.name.startswith(".") or entry.name in LITTER:
            continue
        kind = allowed.get(entry.name)
        if kind is None or (kind == "dir") != entry.is_dir():
            hint = (f" `{MARK}` belongs to a folder moved to `{INTEGRATED}/`: this one was "
                    "integrated and not moved." if entry.name == MARK else "")
            report.add("EXC006", ex.rel(entry), "not one of the names an element folder holds: "
                       f"{', '.join(sorted(allowed))}." + hint)
            continue
        entries[entry.name] = entry
    el = Element(folder.name, stage, folder, entries)
    days = [d for d in (_oldest(entries[n]) for n in el.delivered) if d is not None]
    el.oldest = min(days) if days else None
    if BRIEF in entries:
        el.brief = _day(entries[BRIEF].stat().st_mtime)
    if RESOURCES in entries:
        el.resources = resources(entries[RESOURCES], ex.rel(entries[RESOURCES]), report)
    if SESSIONS in entries:
        for f in sorted(entries[SESSIONS].iterdir()):
            if f.name.startswith(".") or f.name in LITTER:
                continue
            if f.is_file():
                _declaration(f, ex.rel(f), report)
            else:
                report.add("EXC006", ex.rel(f), f"`{SESSIONS}/` holds closing declarations, "
                           "one file per session.")
    return el


def standing(arts) -> dict[str, list[tuple[str, bool]]]:
    """What the documents say of each element: its state, and whether that state closes it."""
    out: dict[str, list[tuple[str, bool]]] = {}
    for a in arts:
        if a.type == "change-contract" and isinstance(a.id, str):
            s = str(a.meta.get("status"))
            out.setdefault(a.id, []).append((s, s in CLOSED_CHANGE))
        elif a.type == "open-register":
            for ident, row in as_map(a.meta.get("entries")).items():
                if isinstance(row, dict):
                    s = str(row.get("status"))
                    out.setdefault(str(ident), []).append((s, s in CLOSED_ENTRY))
    return out


def closed(states: dict, ident: str) -> bool:
    """Closed when every document that declares it says so: one open copy keeps it open."""
    return bool(states.get(ident)) and all(c for _, c in states[ident])


def state(states: dict, ident: str) -> str:
    return ", ".join(sorted({s for s, _ in states.get(ident, [])})) or "—"


def _blocks(value) -> list | None:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list) and value and all(isinstance(b, dict) for b in value):
        return value
    return None


def check(ex: Exchange, known: set[str], states: dict, projects: Path, in_history,
          report: FindingSink) -> None:
    """EXC001-EXC005, on what `read` found. `in_history(sha)` is None when there is no history."""
    for el in ex.elements:
        rel = ex.rel(el.path)
        if el.ident not in known and el.ident not in states:   # an entry with no heading
            report.add("EXC001", rel, f"{el.ident} is not an identifier the documentation "
                       "declares: a typo, or an element that was renamed or never written. "
                       "Nothing here can say whether its material was integrated.")
        if el.stage == INCOMING and closed(states, el.ident):
            report.add("EXC002", rel, f"{el.ident} is {state(states, el.ident)} in the "
                       f"documents and its folder is still in `{INCOMING}/`. If its material "
                       f"was integrated, move the folder to `{INTEGRATED}/` with an `{MARK}` "
                       "saying where each part went; if it was not, it is waiting behind a "
                       "state that says it is done.")
        if el.stage == INTEGRATED:
            _integrated(ex, el, in_history, report)
        if closed(states, el.ident):
            for r in el.resources:
                if r.present:
                    still = "still there" if r.kind in ON_DISK else "still listed"
                    report.add("EXC004", ex.rel(el.path / RESOURCES),
                               f"line {r.line}: {r.kind} `{r.shown}` is {still} and "
                               f"{el.ident} is {state(states, el.ident)}. Propose its removal "
                               f"with `{r.shown_command}`, run it on approval, and delete the "
                               "row.")
        for r in el.resources:
            if r.kind != CREDENTIALS:
                continue
            rel_res = ex.rel(el.path / RESOURCES)
            if r.secret:
                report.add("EXC005", rel_res, f"line {r.line}: the row carries a value. The "
                           "list names the path and the keys, never what they hold: this file "
                           "is read by every session and is not a place for a secret.")
            on_disk = _on_disk(r.where)
            if r.present and on_disk is not None and on_disk.resolve().is_relative_to(projects):
                report.add("EXC005", rel_res, f"line {r.line}: a copy of credentials under "
                           f"{projects}, where every repository and the exchange live. It "
                           "belongs in the scratchpad of the session that needs it, and goes "
                           "with the session.")


def _integrated(ex: Exchange, el: Element, in_history, report: FindingSink) -> None:
    rel = ex.rel(el.path / MARK)
    if MARK not in el.entries:
        report.add("EXC003", ex.rel(el.path), f"moved to `{INTEGRATED}/` without an `{MARK}` "
                   "file: nothing says which commit integrated it or where each part went, "
                   "which is the difference between integrated and moved.")
        return
    try:
        blocks = _blocks(yaml.safe_load(el.entries[MARK].read_text(encoding="utf-8")))
    except (yaml.YAMLError, UnicodeError):
        blocks = None
    if blocks is None:
        report.add("EXC003", rel, "does not read as `commit`, `date` and `parts`, or as a "
                   "list of such blocks, one per integration.")
        return
    covered: set[str] = set()
    for n, block in enumerate(blocks, 1):
        where = f"block {n}: " if len(blocks) > 1 else ""
        sha = block.get("commit")
        sha = str(sha) if isinstance(sha, int) else sha      # all digits, unquoted
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-fA-F]{7,40}", sha.strip()):
            report.add("EXC003", rel, f"{where}`commit` is not the commit of the documentation "
                       "that integrated the material.")
        elif in_history is not None and not in_history(sha.strip()):
            report.add("EXC003", rel, f"{where}`commit` {sha.strip()[:12]} is not in the history "
                       "of the documentation: the integration it names is not one anybody can "
                       "read.")
        day = block.get("date")
        if not isinstance(day, date):
            try:
                date.fromisoformat(str(day))
            except ValueError:
                report.add("EXC003", rel, f"{where}`date` is not a day, `AAAA-MM-GG`.")
        parts = block.get("parts")
        # Empty only where nothing was delivered: a brief whose work ended without a delivery.
        if not isinstance(parts, dict) or (not parts and el.delivered):
            report.add("EXC003", rel, f"{where}`parts` does not say where each part went: one "
                       "line per name in the folder, and where its content now lives.")
            continue
        covered |= {str(k).rstrip("/") for k in parts}
    for name in sorted(covered - set(el.entries)):
        report.add("EXC003", rel, f"`parts` names `{name}`, which is not in the folder.")
    for name in el.delivered:
        if name not in covered:
            report.add("EXC003", rel, f"`{name}` is in the folder and `parts` does not say "
                       "where it went.")
