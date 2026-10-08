#!/usr/bin/env python3
"""Compute one product's daily status from the registers and the state file, as an Excel file.

    python3 digest.py --root <project> --product atlas --inventory
    python3 digest.py --root <project> --product atlas --check
    python3 digest.py --root <project> --product atlas [--copy-to <dir>]
    python3 digest.py --root <project> --product atlas --baseline
    python3 digest.py --root <project> --product atlas --migrate
    python3 digest.py --root <project> --init-store git@github.com:<owner>/<name>.git

THE REGISTERS SAY WHAT EXISTS, THE STATE FILE SAYS WHAT A PERSON DECLARED, THE WORKBOOK IS WHAT
FOLLOWS FROM THE TWO. Hours, sizes, themes, the perimeter of a release, closing dates, waits on
other people, the plan of the next days and the milestones have no source among the artifacts
and must not acquire one there, so they live in a file the person fills through the `digest`
skill. This script computes every number the workbook shows and writes it beside the formula
that derives it, so the file reads the same in a preview that does not recalculate and in a
spreadsheet that does.

WHERE THINGS LIVE. `_meta/digest/` is a clone of a private repository, kept out of the
documentation repository by its `.gitignore`. It holds

    state-<product>.yaml                    what the person declared, one file per product
    DIG-NNN-<product>-YYYY-MM-DD/
        DIG-NNN-<product>-YYYY-MM-DD.xlsx   the workbook, as it is sent
        frozen.yaml                         what it was computed from, for the next one

NNN is one sequence across the products. A snapshot is never edited: each one carries the hash
of the one before it, and freezes every day up to the day before its date, both as declared and
as counted, so a classification changed today never rewrites the hours of a day already sent.

THE STATE FILE, FORMAT 2:

    format: 2
    product: atlas
    release: {name: "1.0", delivery: 2026-10-13, start: 2026-09-22, commitment: null}
    items:                      # per identifier: title, what, theme, scope, size, seen,
      CHG-018: {...}            # closed_on, out_reason, hours_before, excluded, split_into, gone
    order: {todo: [...], out: [...]}        # the rows of the two lists, in the order shown
    days:                       # per date: hours per item and per category outside the product,
      2026-10-08: {hours: {CHG-018: 4}, outside: {riunioni: 1}}
      2026-09-22: {themes: {sviluppo: 4}, outside: {riunioni: 2}}   # a day rebuilt in bulk
    waits: [{what, owner, asked, needed_by, without, missing, blocks, slows, resolved}]
    plan: {2026-10-09: [{item: CHG-018, hours: 5}], 2026-10-12: [{item: CHG-018, hours: 2,
           closes: true}]}
    milestones: [{name: Demo al team funzionale, date: 2026-10-15}]

WHAT IS REFUSED, BEFORE ANYTHING IS WRITTEN. `--check` lists every reason, and rendering runs it
first: an identifier the state file does not classify; a classified one gone from the registers
without closing; an open item whose title changed since it was confirmed; a field the workbook
prints and nobody declared; a working day of the period with no hours declared, or hours on a
day not yet over or before the project started; hours on an item of the perimeter with no theme;
a category that is not one of the five; a day already frozen edited after the fact; an earlier
snapshot whose hash no longer matches; the days rebuilt in bulk not adding up, theme by theme,
to the hours declared on the items; a planned item closed, excluded, without hours or a `CHG` in
`draft`; the two lists not holding exactly the open items; a description with the register's
jargon or more than two sentences; a long dash; a status this file does not map; a date on a
weekend. Fix the state file or the registers, never this file to get past it.

Exit codes: 0 done, 1 refused, 2 cannot run, 3 written and committed but not pushed.
Needs PyYAML, jsonschema (the registers are read through the validator), XlsxWriter and `git`;
`gh` only to verify that a GitHub remote is private.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import math
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from pathlib import Path

import yaml

FRAMEWORK = Path(__file__).resolve().parents[3]
VALIDATE = FRAMEWORK / "skills" / "audit" / "scripts" / "validate.py"
WORKBOOK = Path(__file__).resolve().parent / "workbook.py"
STORE = Path("_meta") / "digest"
OUT = "out"
FORMAT = 2

THEMES = {"architettura": "Architettura", "sviluppo": "Sviluppo", "deploy": "Deploy"}
# What a snapshot written before 4.2.0 calls a theme, read as what it is called now.
OLD_THEMES = {"infrastruttura": "deploy"}
# A size is a range of hours, S 1 to 2, M 3 to 5, L 6 to 12, XL 13 to 40, and the estimate counts
# every item at the top of its range: one number, on the side of caution, the same in every
# cell and on the Gantt.
SIZES = {"S": 2, "M": 5, "L": 12, "XL": 40}
# The hours outside the product, in five categories and in this order, which is the order of
# the columns of the day-by-day table. Their labels are the workbook's, in `workbook.py`.
CATEGORIES = ("supporto", "reportistica", "riunioni", "solleciti", "formazione")
# A day rebuilt in bulk declares its hours by column, not by item.
BULK_KEYS = {"architettura", "sviluppo", "deploy", OUT}

# WHAT EACH REGISTER STATUS MEANS FOR THE DIGEST. The registry declares which statuses exist
# and not which of them mean done, so the reading lives here, and `tests/selfcheck.py`
# asserts that every status the registry declares for these types is mapped: a status added
# there breaks the test, not the digest in silence. A `CHG` is closed at `verified` and not
# before, which is the Definition of Done of `templates/AGENTS.md`. An `INC` has no status a
# script can read: it is open until a `CHG` derives from it, and then the `CHG` replaces it.
STATES = {
    "open-register": {"open": "open", "parked": "open", "decided": "closed",
                      "superseded": "gone"},
    "decision-record": {"proposed": "open", "accepted": "closed", "superseded": "closed"},
    "change-contract": {"draft": "open", "approved": "open", "implemented": "open",
                        "verified": "closed", "rolled-back": "gone"},
    "evaluation-report": {"active": "closed"},
}

STATE_KEYS = {"format", "product", "release", "items", "order", "days", "waits", "plan",
              "milestones"}
RELEASE_KEYS = {"name", "delivery", "start", "commitment"}
ITEM_KEYS = {"title", "what", "theme", "scope", "size", "seen", "closed_on", "out_reason",
             "hours_before", "excluded", "split_into", "gone"}
WAIT_KEYS = {"what", "owner", "asked", "needed_by", "without", "missing", "blocks", "slows",
             "resolved"}
DAY_KEYS = {"hours", "outside", "themes"}
PLAN_KEYS = {"item", "hours", "closes"}
MILESTONE_KEYS = {"name", "date"}
ORDER_KEYS = {"todo", "out"}

SNAPSHOT = re.compile(r"^DIG-(\d{3,})-(.+)-(\d{4}-\d{2}-\d{2})$")
HEADING_ID = re.compile(r"^#{1,6}\s+\**([A-Z]{2,4}-\d{3,})\**\s*[·:\-–—]?\s*(.*?)\s*$")
GENERATED = re.compile(r"<!-- generated:.*?-->.*?<!-- /generated -->", re.S)
# The register's jargon, in a sentence written for somebody who will never open it.
JARGON = [(re.compile(r"\b[A-Z]{2,4}-\d{2,}\b"), "an identifier"),
          (re.compile(r"§"), "a section anchor"),
          (re.compile(r"`"), "a backtick"),
          (re.compile(r"#[a-z]"), "an anchor"),
          (re.compile(r"\b[a-z]+_[a-z_]+\b"), "a field name")]
DASHES = re.compile(r"[—–]")
SENTENCE_END = re.compile(r"[.!?](?:\s|$)")


class Refusal(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


# ─────────────────────────────────────────────────────────────────────────────
# Numbers and dates, with the spreadsheet's own rules

def num(v) -> Fraction:
    """A number of hours as declared: 5, 1.5, "1,5". Never a float, so 76/9,5 stays exact."""
    if isinstance(v, bool) or v is None:
        raise ValueError(f"{v!r} is not a number of hours")
    if isinstance(v, (int, float)):
        return Fraction(str(v))
    return Fraction(str(v).strip().replace(",", "."))


def dec(x: Fraction) -> Decimal:
    return Decimal(x.numerator) / Decimal(x.denominator)


def plain(x: Fraction) -> str:
    """For frozen.yaml: exact, with a dot."""
    return format(dec(x).normalize(), "f")


def hours(x: Fraction) -> str:
    """For a sentence: a decimal comma, and decimals only when there are some."""
    return plain(x).replace(".", ",")


def ore(x: Fraction, past: str = "") -> str:
    """«5 ore», «1 ora», «1,5 ore»; with `past`, «1 ora già lavorata»."""
    if x == 1:
        return "1 ora" + (f" già {past}a" if past else "")
    return f"{hours(x)} ore" + (f" già {past}e" if past else "")


def excel_round(x: Fraction, digits: int) -> Fraction:
    """ROUND as a spreadsheet does it: half away from zero, on the decimal value."""
    q = Decimal(1).scaleb(-digits)
    return Fraction(dec(x).quantize(q, rounding=ROUND_HALF_UP))




def as_date(v) -> date | None:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        try:
            return date.fromisoformat(v.strip())
        except ValueError:
            return None
    return None


def dm(d: date) -> str:
    return d.strftime("%d/%m")


def dmy(d: date) -> str:
    return d.strftime("%d/%m/%Y")




def working_day(d: date) -> bool:
    return d.weekday() < 5


def next_working(d: date) -> date:
    d += timedelta(days=1)
    while not working_day(d):
        d += timedelta(days=1)
    return d


def workday(start: date, n: int) -> date:
    """WORKDAY(start, n): the n-th working day after `start`, or before it when n < 0."""
    d, step, left = start, (1 if n >= 0 else -1), abs(n)
    while left:
        d += timedelta(days=step)
        if working_day(d):
            left -= 1
    return d


def networkdays(a: date, b: date) -> int:
    """NETWORKDAYS(a, b): working days from a to b, both included, negative when b < a."""
    if b < a:
        return -networkdays(b, a)
    return sum(1 for i in range((b - a).days + 1) if working_day(a + timedelta(days=i)))




def sort_id(i: str) -> tuple[str, int]:
    prefix, _, n = i.partition("-")
    return prefix, int(n) if n.isdigit() else 0




# ─────────────────────────────────────────────────────────────────────────────
# The registers

def load_validator():
    """`validate.py` as a module: one discovery, one scan, one rule for what binds a product."""
    name = "_framework_digest_validate"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, VALIDATE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod          # before it runs: @dataclass resolves through sys.modules
    spec.loader.exec_module(mod)
    return mod


@dataclass
class Entry:
    id: str
    kind: str
    type: str
    status: str | None
    title: str | None
    file: str
    closed_by: str | None = None
    derives_from: list = field(default_factory=list)


@dataclass
class Voce:
    id: str
    kind: str
    state: str                       # open, closed, gone, replaced
    status: str | None
    title: str | None                # the register's, when it still has one
    file: str | None
    closer: str | None = None        # the record that closed it, printed beside it
    aliases: list = field(default_factory=list)
    children: list = field(default_factory=list)


def heading_titles(body: str) -> dict[str, str]:
    out = {}
    for line in GENERATED.sub("", body).splitlines():
        m = HEADING_ID.match(line)
        if m and m.group(1) not in out:
            out[m.group(1)] = m.group(2).strip().strip("*").strip()
    return out


def bare(ref) -> str:
    return str(ref).split(":", 1)[-1].strip()


@dataclass
class Registers:
    entries: dict
    broken: list
    duplicated: list
    manifest: object
    arts: list
    product_name: str


def discover(root: Path, v) -> tuple[list, list]:
    """Every artifact the validator would look at, and the files whose front matter is broken."""
    registry = yaml.safe_load(v.REGISTRY.read_text(encoding="utf-8"))
    try:
        project = v.load_project(root)
    except SystemExit as e:          # an unknown key or bad YAML in framework.yaml
        raise Refusal([str(e.code)])
    report = v.Report({})
    arts = v.discover(root, v.load_scan(registry, project), registry, report)
    return arts, [f"{f.path}: {f.message}" for f in report.findings if f.code == "FM001"]


def read_registers(arts: list, broken: list, product: str, v) -> Registers:
    dirs = v.product_dirs(arts)
    manifest = next((a for a in arts if a.type == "product-manifest"
                     and product in v.as_list(a.meta.get("products"))), None)
    entries: dict[str, Entry] = {}
    duplicated = []

    def add(e: Entry):
        if e.id in entries:
            duplicated.append(f"{e.id} is declared in {entries[e.id].file} and in {e.file}")
        entries[e.id] = e

    for a in arts:
        mine = product in v.as_list(a.meta.get("products"))
        if a.type == "open-register":
            scope = dirs.get(a.path.parent, (None, None))[0]
            titles = heading_titles(a.body)
            for key, row in v.as_map(a.meta.get("entries")).items():
                if isinstance(row, dict) and v.binds(product, row, scope):
                    add(Entry(str(key), str(key).split("-")[0], a.type, row.get("status"),
                              titles.get(key), a.rel, closed_by=row.get("closed_by")))
        elif a.type in ("decision-record", "change-contract", "evaluation-report") and a.id:
            if not (mine or (a.type == "decision-record"
                             and "all" in v.as_list(a.meta.get("products")))):
                continue
            title = next((m.group(2) for line in a.body.splitlines()
                          if line.startswith("# ") and (m := HEADING_ID.match(line))), None)
            add(Entry(a.id, a.id.split("-")[0], a.type, a.meta.get("status"), title, a.rel,
                      derives_from=[bare(r) for r in v.as_list(a.meta.get("derives_from"))]))
        elif a.type == "roadmap" and mine:
            for key, title in heading_titles(a.body).items():
                if key.startswith("INC-"):
                    add(Entry(key, "INC", a.type, None, title, a.rel))
    name = str(manifest.meta.get("name") or product) if manifest else product
    return Registers(entries, broken, duplicated, manifest, arts, name)


def build_voci(reg: Registers, known: set[str]) -> tuple[dict[str, Voce], dict[str, str], list, list]:
    """The items of the digest, and the identifiers that are another name for one of them.

    An `OD` decided by a `DEC` is one item, not two: the hours spent deciding are counted once,
    the activity names it by the entry worked on, and what is done names it by the decision.
    The link is `closed_by` on the entry, which is how the register closes one, and the
    `derives_from` of the `DEC` when that is all there is. `known` holds the identifiers an
    earlier snapshot or the state file still names, so an entry whose row the register dropped
    after deciding it keeps its decision.
    """
    E = reg.entries
    decs = {k: e for k, e in E.items() if e.kind == "DEC"}
    alias: dict[str, str] = {}
    voci: dict[str, Voce] = {}
    unknown, disagree = [], []

    def state_of(e: Entry) -> str | None:
        return STATES[e.type].get(e.status) if e.type in STATES else None

    ods = {k for k, e in E.items() if e.kind == "OD"}
    ods |= {r for d in decs.values() for r in d.derives_from
            if r.startswith("OD-") and r in known}
    for od in sorted(ods, key=sort_id):
        e = E.get(od)
        closer = e.closed_by if e and e.closed_by in decs else None
        if closer is None:
            named = sorted((d for d in decs.values() if od in d.derives_from),
                           key=lambda d: (state_of(d) != "closed", sort_id(d.id)))
            closer = named[0].id if named else None
        if e is None and closer is None:
            continue
        if e is not None and state_of(e) is None:
            unknown.append(f"{od} has status {e.status!r} in {e.file}")
            continue
        row = state_of(e) if e else None
        dec_state = state_of(decs[closer]) if closer else None
        if row == "gone":
            state = "gone"
        elif closer is None:
            state = row
        elif e is None:
            state = "closed" if dec_state == "closed" else "open"
        else:
            # Both say closed, or it is not closed: the more cautious of two sources decides.
            state = "closed" if row == "closed" and dec_state == "closed" else "open"
            if row != dec_state and not (row == "open" and dec_state == "open"):
                disagree.append(f"{od} is {e.status} in {e.file} and {closer} is "
                                f"{decs[closer].status}: counted as {state}")
        voci[od] = Voce(od, "OD", state, e.status if e else None, e.title if e else None,
                        e.file if e else None, closer=closer)
        if closer:
            alias.setdefault(closer, od)
            voci[od].aliases.append(closer)

    for k, e in E.items():
        if e.kind == "OD" or (e.kind == "DEC" and k in alias):
            continue
        if e.kind == "INC":
            kids = sorted((c.id for c in E.values() if c.kind == "CHG" and k in c.derives_from),
                          key=sort_id)
            voci[k] = Voce(k, "INC", "replaced" if kids else "open", None, e.title, e.file,
                           children=kids)
            continue
        st = state_of(e)
        if st is None:
            unknown.append(f"{k} has status {e.status!r} in {e.file}")
            continue
        closer = e.closed_by if e.kind == "KI" and e.closed_by in E else None
        voci[k] = Voce(k, e.kind, st, e.status, e.title, e.file, closer=closer)
    return voci, alias, unknown, disagree



# ─────────────────────────────────────────────────────────────────────────────
# The store: the state file and the snapshots

@dataclass
class Snap:
    number: int
    product: str
    date: date
    path: Path
    _frozen: dict | None = None

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def frozen(self) -> dict:
        if self._frozen is None:
            self._frozen = yaml.safe_load(
                (self.path / "frozen.yaml").read_text(encoding="utf-8")) or {}
        return self._frozen

    def sent(self) -> list[Path]:
        """The file that was sent: a text before 4.2.0, a workbook after."""
        return [p for p in (self.path / f"{self.name}.txt", self.path / f"{self.name}.xlsx")
                if p.exists()]

    def digest(self) -> str:
        h = hashlib.sha256((self.path / "frozen.yaml").read_bytes())
        h.update(b"\n\0\n")
        for p in self.sent():
            h.update(p.read_bytes())
        return h.hexdigest()


def snapshots(store: Path) -> list[Snap]:
    out = []
    if store.is_dir():
        for p in store.iterdir():
            m = SNAPSHOT.match(p.name)
            if p.is_dir() and m and (p / "frozen.yaml").exists():
                out.append(Snap(int(m.group(1)), m.group(2), date.fromisoformat(m.group(3)), p))
    return sorted(out, key=lambda s: (s.date, s.number))


def previous_of(snaps: list[Snap], product: str, when: date) -> Snap | None:
    """The snapshot of the latest earlier day: a later number on one date replaces an earlier."""
    mine = [s for s in snaps if s.product == product and s.date < when]
    return max(mine, key=lambda s: (s.date, s.number)) if mine else None


def chain(snaps: list[Snap], start: Snap | None) -> list[Snap]:
    by_name = {s.name: s for s in snaps}
    out, s = [], start
    while s is not None and s not in out:
        out.append(s)
        prev = (s.frozen.get("previous") or {}).get("dir")
        s = by_name.get(prev) if prev else None
    return out


def frozen_theme(v: dict) -> str | None:
    t = v.get("theme")
    return OLD_THEMES.get(t, t)


def read_state(store: Path, product: str) -> tuple[dict | None, str | None]:
    path = store / f"state-{product}.yaml"
    if not path.exists():
        return None, f"{path} does not exist: the first run declares it, with --baseline"
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        return None, f"{path} does not parse: {str(e).splitlines()[0]}"
    if not isinstance(data, dict):
        return None, f"{path}: the top level is not a mapping"
    return data, None


def dated(mapping) -> dict:
    return {as_date(k): v for k, v in (mapping or {}).items() if as_date(k) is not None}


def canonical_day(entry) -> dict:
    """A day as declared, in one spelling, so a frozen day and a declared one compare."""
    out = {}
    for k in ("hours", "outside", "themes"):
        m = (entry or {}).get(k) or {}
        if m:
            out[k] = {str(i): plain(num(h)) for i, h in sorted(m.items(), key=lambda x: str(x[0]))}
    return out


# ─────────────────────────────────────────────────────────────────────────────
# The items, as of the digest's date

@dataclass
class Item:
    id: str
    kind: str
    state: str
    scope: str | None
    theme: str | None
    size: str | None
    title: str | None
    what: str | None
    excluded: bool
    closer: str | None
    children: list
    aliases: list
    closed_on: date | None = None
    out_reason: str | None = None
    hours: Fraction = Fraction(0)        # all declared: before the detail and in every day
    before: Fraction = Fraction(0)
    first_day: date | None = None

    def top(self) -> Fraction:
        """The hours the estimate counts for this item: the top of its size."""
        return Fraction(SIZES[self.size])

    @property
    def shown_id(self) -> str:
        return self.closer if self.kind == "OD" and self.closer and self.state == "closed" \
            else self.id


def _item(i, kind, st, row, closer, children, aliases) -> Item:
    return Item(i, kind, st, None if row.get("scope") is None else str(row.get("scope")),
                row.get("theme"), row.get("size"), row.get("title"), row.get("what"),
                bool(row.get("excluded")), closer,
                list(children) + list(row.get("split_into") or []), list(aliases),
                closed_on=as_date(row.get("closed_on")), out_reason=row.get("out_reason"))


def split_parent(it: Item) -> bool:
    """An item that other items took the place of: an `INC` a `CHG` derives from, or an entry
    split in two, whether the register still has it open or already superseded it."""
    return it.state == "replaced" or bool(it.children and it.state in ("open", "gone"))


@dataclass
class Context:
    root: Path
    product: str
    when: date
    name: str
    reg: Registers
    voci: dict
    alias: dict
    state: dict | None
    snaps: list
    prev: Snap | None
    baseline: bool
    problems: list = field(default_factory=list)
    notes: list = field(default_factory=list)      # disagreements between sources
    items: dict = field(default_factory=dict)
    days: dict = field(default_factory=dict)
    now: datetime | None = None


def prepare(root: Path, product: str | None, when: date, baseline: bool) -> Context:
    v = load_validator()
    root = root.resolve()
    arts, broken = discover(root, v)
    products = sorted({p for p, _ in v.product_dirs(arts).values()})
    if product is None:
        if len(products) != 1:
            raise Refusal([f"say which product with --product: {', '.join(products) or 'none'}"])
        product = products[0]
    elif product not in products:
        raise Refusal([f"{product!r} has no products/<p>/product.yaml here; "
                       f"the products are {', '.join(products) or 'none'}"])
    reg = read_registers(arts, broken, product, v)
    store = root / STORE
    state, err = read_state(store, product)
    snaps = snapshots(store)
    prev = previous_of(snaps, product, when)
    known = set((state or {}).get("items") or {})
    if prev:
        known |= set(prev.frozen.get("voci") or {})
    voci, alias, unknown, disagree = build_voci(reg, known)
    ctx = Context(root, product, when, reg.product_name, reg, voci, alias, state, snaps, prev,
                  baseline, notes=disagree)
    ctx.problems += [f"front matter that does not parse, so its entries cannot be read: {b}"
                     for b in reg.broken]
    ctx.problems += reg.duplicated
    ctx.problems += [f"{u}, which the digest does not map to open or closed" for u in unknown]
    if err:
        ctx.problems.append(err)
    return ctx


def check(ctx: Context) -> list[str]:
    """Every reason not to write the workbook. Empty means it can be computed and written."""
    P = ctx.problems
    when = ctx.when
    if not working_day(when):
        P.append(f"{when} is a {when.strftime('%A')}: a digest is of a working day")
    state = ctx.state
    if state is None:
        return P
    if state.get("format") != FORMAT:
        P.append("the state file is in the format of 4.1.0: run --migrate, then declare what "
                 "it lists")
        return P
    for k in sorted(set(state) - STATE_KEYS):
        P.append(f"unknown key {k!r} at the top of the state file: nothing reads it")
    if state.get("product") not in (None, ctx.product):
        P.append(f"the state file says product {state.get('product')!r}, this is {ctx.product!r}")
    release = state.get("release") or {}
    if not isinstance(release, dict) or not release.get("name"):
        P.append("`release.name` is the release the perimeter is measured against")
        release = {}
    for k in sorted(set(release) - RELEASE_KEYS):
        P.append(f"unknown key {k!r} under `release`")
    if as_date(release.get("delivery")) is None:
        P.append("`release.delivery` is the agreed delivery date, YYYY-MM-DD")
    start = as_date(release.get("start"))
    if start is None:
        P.append("`release.start` is the first day of the project, YYYY-MM-DD")
    elif start >= when:
        P.append(f"`release.start` is {start}: the project starts before the digest's date")
    rel = str(release.get("name", ""))

    mine = [s for s in ctx.snaps if s.product == ctx.product]
    later = [s for s in mine if s.date > when]
    if later:
        P.append(f"{later[-1].name} is later than {when}: a digest cannot go back in time")
    if ctx.baseline and ctx.prev:
        P.append(f"there is already {ctx.prev.name}: the baseline is the first run, once")
    if not ctx.baseline and not ctx.prev:
        P.append("no earlier digest for this product: the first run is --baseline")
    first_snapshot = min((s.date for s in mine), default=when)

    rows = state.get("items") or {}
    if not isinstance(rows, dict):
        P.append("`items` is a mapping from identifier to what was declared about it")
        rows = {}
    for i, row in rows.items():
        if not isinstance(row, dict):
            P.append(f"{i}: its row is not a mapping")
            continue
        for k in sorted(set(row) - ITEM_KEYS):
            P.append(f"{i}: unknown key {k!r}")

    prev_voci = (ctx.prev.frozen.get("voci") or {}) if ctx.prev else {}
    # The items, as of today. A row that names an identifier the registers no longer carry is
    # history when the earlier snapshot already had it closed, and a declared exit when the
    # row says `gone`; otherwise it is an item leaving in silence, which is refused.
    items: dict[str, Item] = {}
    for vid, vo in ctx.voci.items():
        row = rows.get(vid)
        if row is None:
            title = f" ({vo.title})" if vo.title else ""
            P.append(f"{vid}{title}, in {vo.file}, has no row in the state file: classify it")
            continue
        if not isinstance(row, dict):
            continue
        items[vid] = _item(vid, vo.kind, vo.state, row, vo.closer, vo.children, vo.aliases)
    for i, row in rows.items():
        if i in ctx.voci or i in ctx.alias or not isinstance(row, dict):
            continue
        before = prev_voci.get(i) or {}
        if before.get("state") in ("closed", "gone", "replaced"):
            items[i] = _item(i, before.get("kind", i.split("-")[0]), before["state"], row,
                             before.get("closer"), before.get("children") or [], [])
        elif row.get("gone"):
            items[i] = _item(i, i.split("-")[0], "gone", row, None, [], [])
        else:
            P.append(f"{i} is in the state file and no longer in the registers, and nothing says "
                     "it was closed: write `gone` with the reason, or restore the entry")
    for i, before in prev_voci.items():
        if i not in items and i not in rows and before.get("state") not in (
                "closed", "gone", "replaced"):
            P.append(f"{i} was in {ctx.prev.name} and is now in neither the registers nor the "
                     "state file: an item cannot leave in silence")
    for a in ctx.alias:
        if a in rows and isinstance(rows[a], dict) and set(rows[a]) - {"hours_before"}:
            ctx.notes.append(f"{a} decides {ctx.alias[a]}: they are one item, and the row of "
                             f"{a} counts only for its hours")
    for vid, vo in ctx.voci.items():
        it = items.get(vid)
        if it and vo.title and it.state == "open" and not it.excluded:
            seen = (rows[vid].get("seen") or "").strip()
            if seen != vo.title.strip():
                P.append(f"{vid} is titled {vo.title!r} in {vo.file} and was confirmed as "
                         f"{seen!r}: confirm its classification again")

    # Hours, day by day. A day is either rebuilt in bulk, by column, or declared by item.
    raw_days = state.get("days") or {}
    if not isinstance(raw_days, dict):
        P.append("`days` is a mapping from date to the hours of that day")
        raw_days = {}
    for k in raw_days:
        if as_date(k) is None:
            P.append(f"day {k!r}: the key is a date, YYYY-MM-DD")
    days = dated(raw_days)
    per_item: dict[str, Fraction] = {}
    first_day: dict[str, date] = {}
    bulk = {k: Fraction(0) for k in BULK_KEYS}
    any_bulk = False
    for d in sorted(days):
        entry = days[d] if days[d] is not None else {}
        if not isinstance(entry, dict) or set(entry) - DAY_KEYS:
            P.append(f"day {d}: it holds `hours` and `outside`, or `themes` and `outside` for a "
                     "day rebuilt in bulk")
            continue
        if d >= when:
            P.append(f"day {d}: hours on a day that is not over yet")
        if start and d < start:
            P.append(f"day {d}: before `release.start`, so no table of the workbook has it")
        if entry.get("themes") and entry.get("hours"):
            P.append(f"day {d}: rebuilt in bulk and declared by item at once; one or the other")
        if entry.get("themes") and d >= first_snapshot:
            P.append(f"day {d}: only the days before the first digest are rebuilt in bulk; "
                     "after it, the hours are declared by item")
        try:
            hm = {str(k): num(h) for k, h in (entry.get("hours") or {}).items()}
            om = {str(k): num(h) for k, h in (entry.get("outside") or {}).items()}
            tm = {str(k): num(h) for k, h in (entry.get("themes") or {}).items()}
        except (ValueError, ZeroDivisionError) as e:
            P.append(f"day {d}: {e}")
            continue
        for k, h in list(hm.items()) + list(om.items()) + list(tm.items()):
            if h < 0:
                P.append(f"day {d}: {k} has {h} hours")
        for k in om:
            if k not in CATEGORIES:
                P.append(f"day {d}: {k!r} is not a category outside the product; the categories "
                         f"are {', '.join(CATEGORIES)}")
        for k, h in tm.items():
            if k not in BULK_KEYS:
                P.append(f"day {d}: {k!r} is not a column of a day rebuilt in bulk; they are "
                         f"{', '.join(sorted(BULK_KEYS))}")
            else:
                bulk[k] += h
                any_bulk = True
        for k, h in hm.items():
            target = ctx.alias.get(k, k)
            if target not in items:
                P.append(f"day {d}: hours on {k}, which is not an item of {ctx.product}")
                continue
            per_item[target] = per_item.get(target, Fraction(0)) + h
            if h and target not in first_day:
                first_day[target] = d
    ctx.days = days

    for i, it in items.items():
        row = rows.get(i) if isinstance(rows.get(i), dict) else {}
        before = Fraction(0)
        for r in [row] + [rows.get(a) for a in it.aliases if isinstance(rows.get(a), dict)]:
            if r.get("hours_before") is not None:
                try:
                    before += num(r["hours_before"])
                except (ValueError, ZeroDivisionError):
                    P.append(f"{i}: `hours_before` is a number of hours")
        it.before = before
        it.hours = before + per_item.get(i, Fraction(0))
        it.first_day = first_day.get(i)
        if it.hours and not it.excluded and it.scope != OUT and it.theme not in THEMES:
            P.append(f"{i}: hours declared on it and no `theme`, so no column of the "
                     "workbook counts them")
    ctx.items = items

    # The days rebuilt in bulk and the hours declared on the items must tell the same story.
    if any_bulk or any(it.before for it in items.values()):
        declared = {k: Fraction(0) for k in BULK_KEYS}
        for it in items.values():
            if it.before:
                col = OUT if (it.excluded or it.scope == OUT) else it.theme
                if col in declared:
                    declared[col] += it.before
        for k in sorted(BULK_KEYS):
            if declared[k] != bulk[k]:
                P.append(f"the days rebuilt in bulk give {hours(bulk[k])} h to {k} and the items "
                         f"declare {hours(declared[k])} h before the detail: the two have to "
                         "agree")

    # Every working day of the period is declared, an empty day included.
    if start:
        lo = ctx.prev.date if ctx.prev and not ctx.baseline else start
        d = lo
        while d < when:
            if working_day(d) and d >= start and d not in days:
                P.append(f"no hours declared for {d}: declare them, `{{}}` if nothing was "
                         "worked")
            d += timedelta(days=1)

    for s in chain(ctx.snaps, ctx.prev):
        prev_ref = s.frozen.get("previous") or {}
        if prev_ref.get("dir"):
            target = next((x for x in ctx.snaps if x.name == prev_ref["dir"]), None)
            if target is None or target.digest() != prev_ref.get("sha256"):
                P.append(f"{prev_ref['dir']} no longer matches the hash {s.name} recorded for "
                         "it: a snapshot is never edited")
    if ctx.prev and ctx.prev.frozen.get("format") == FORMAT:
        frozen_days = dated(ctx.prev.frozen.get("days"))
        for d in sorted(set(frozen_days) | {d for d in days if d < ctx.prev.date}):
            try:
                same = canonical_day(days.get(d)) == (frozen_days.get(d) or {})
            except (ValueError, ZeroDivisionError):
                same = False
            if not same:
                P.append(f"day {d} is not the one {ctx.prev.name} froze: a day already sent is "
                         "not edited")

    others = [p for p in (ctx.root / STORE).glob("state-*.yaml")
              if p.name != f"state-{ctx.product}.yaml"]
    for p in others:
        try:
            other = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        for d, entry in dated(other.get("days")).items():
            mine_day = days.get(d)
            if not isinstance(entry, dict) or not isinstance(mine_day, dict):
                continue
            for i in sorted(set(entry.get("hours") or {}) & set(mine_day.get("hours") or {})):
                P.append(f"day {d}: hours on {i} in this state file and in {p.name}; the hours "
                         "of one item on one day are declared once")

    # What every item needs, for what the workbook prints about it.
    for i, it in items.items():
        row = rows.get(i) if isinstance(rows.get(i), dict) else {}
        if it.excluded:
            continue
        if row.get("theme") is not None and row.get("theme") not in THEMES:
            P.append(f"{i}: theme {row.get('theme')!r} is one of {', '.join(THEMES)}")
        if row.get("size") is not None and row.get("size") not in SIZES:
            P.append(f"{i}: size {row.get('size')!r} is one of {', '.join(SIZES)}")
        if it.scope is None:
            P.append(f"{i}: no `scope`, the release name ({rel}) or `{OUT}`")
            continue
        in_scope = it.scope == rel
        if it.state == "open" and it.scope not in (rel, OUT):
            P.append(f"{i} is open and scoped to {it.scope!r}, not to the current release "
                     f"{rel!r}: assign it to {rel!r} or to `{OUT}`")
        shown = it.state == "open" or (it.state == "closed" and in_scope)
        if shown:
            for k in ("title", "what", "theme"):
                if not row.get(k):
                    P.append(f"{i}: no `{k}`, and the workbook prints it")
        if in_scope and it.state in ("open", "closed") and not row.get("size"):
            P.append(f"{i}: in the perimeter with no `size`, and the workbook prints its "
                     "estimated hours")
        if it.state == "closed" and in_scope:
            if it.closed_on is None:
                P.append(f"{i}: closed in the perimeter with no `closed_on`")
            elif it.closed_on > when:
                P.append(f"{i}: closed on {it.closed_on}, after the digest's date")
        if it.state == "open" and it.scope == OUT and not row.get("out_reason"):
            P.append(f"{i}: outside the perimeter with no `out_reason`, which the workbook "
                     "prints as why")
        for k in ("title", "what", "out_reason"):
            if row.get(k) and DASHES.search(str(row[k])):
                P.append(f"{i}: a long dash in `{k}`; use a comma or two sentences")
        if row.get("title") and str(row["title"]).rstrip().endswith("."):
            P.append(f"{i}: the title ends with a full stop")
        what = str(row.get("what") or "")
        if what:
            for rx, kind in JARGON:
                if rx.search(what):
                    P.append(f"{i}: the description carries {kind} ({rx.search(what).group()!r}); "
                             "it is written for somebody who never opens the register")
            if len(SENTENCE_END.findall(what)) > 2:
                P.append(f"{i}: the description has more than two sentences")
            if not what.rstrip().endswith((".", "!", "?")):
                P.append(f"{i}: the description does not end with a full stop")
        for child in row.get("split_into") or []:
            if child not in items:
                P.append(f"{i} is split into {child}, which is not an item")
        if row.get("split_into") and it.state == "closed":
            P.append(f"{i} is closed and split: one or the other")

    # The two lists hold exactly the open items, in the order the person chose.
    todo = {i for i, it in items.items() if it.state == "open" and it.scope == rel
            and not it.excluded and not split_parent(it)}
    out = {i for i, it in items.items() if it.state == "open" and it.scope == OUT
           and not it.excluded and not split_parent(it)}
    order = state.get("order") or {}
    if not isinstance(order, dict):
        P.append("`order` holds `todo` and `out`, the rows of the two lists in order")
        order = {}
    for k in sorted(set(order) - ORDER_KEYS):
        P.append(f"unknown key {k!r} under `order`")
    for key, expected in (("todo", todo), ("out", out)):
        listed = [str(x) for x in (order.get(key) or [])]
        if len(set(listed)) != len(listed):
            P.append(f"`order.{key}` names an item twice")
        missing = sorted(expected - set(listed), key=sort_id)
        extra = [x for x in listed if x not in expected]
        if missing:
            P.append(f"`order.{key}` does not list {', '.join(missing)}: add them where they "
                     "belong, at the end if nobody said otherwise")
        if extra:
            P.append(f"`order.{key}` lists {', '.join(extra)}, which no longer belong there")

    if not ctx.baseline:
        nxt = next_working(when)
        plan = dated(state.get("plan"))
        for k in (state.get("plan") or {}):
            if as_date(k) is None:
                P.append(f"plan {k!r}: the key is a date, YYYY-MM-DD")
        for d in (when, nxt):
            if d not in plan:
                P.append(f"no plan for {d}: the workbook prints it, `[]` if nothing is planned")
                continue
            for e in plan[d] or []:
                if not isinstance(e, dict) or set(e) - PLAN_KEYS:
                    P.append(f"plan {d}: {e!r} is {{item, hours, closes}}")
                    continue
                i = str(e.get("item"))
                it = items.get(i)
                try:
                    h = num(e.get("hours"))
                except (ValueError, ZeroDivisionError):
                    h = Fraction(0)
                if h <= 0:
                    P.append(f"plan {d}: {i} has no hours; the workbook prints how many")
                if it is None:
                    P.append(f"plan {d}: {i} is not an item; a decision that closes an entry is "
                             "planned under the entry's identifier")
                elif it.state != "open":
                    P.append(f"plan {d}: {i} is {it.state}")
                elif it.excluded:
                    P.append(f"plan {d}: {i} is excluded from the digest")
                elif ctx.voci.get(i) and ctx.voci[i].status == "draft":
                    P.append(f"plan {d}: {i} is a `CHG` in draft, and a draft is not a mandate "
                             "to build. Approve it first, or plan the work that approves it")
                if not isinstance(e.get("closes", False), bool):
                    P.append(f"plan {d}: `closes` on {i} is true or false")
        milestones = state.get("milestones")
        if milestones is None:
            P.append("no `milestones`: the Gantt shows them; declare them, `[]` if there are "
                     "none")
        elif not isinstance(milestones, list):
            P.append("`milestones` is a list of {name, date}")
        else:
            for m in milestones:
                if not isinstance(m, dict) or set(m) - MILESTONE_KEYS or not m.get("name") \
                        or as_date(m.get("date")) is None:
                    P.append(f"milestone {m!r} is {{name, date}}")
                elif DASHES.search(str(m["name"])):
                    P.append(f"milestone {m['name']!r}: a long dash")

    waits = state.get("waits") or []
    if not isinstance(waits, list):
        P.append("`waits` is a list")
        waits = []
    for n, w in enumerate(waits, 1):
        if not isinstance(w, dict):
            P.append(f"wait {n}: not a mapping")
            continue
        label = w.get("what") or f"wait {n}"
        for k in sorted(set(w) - WAIT_KEYS):
            P.append(f"{label}: unknown key {k!r}")
        for k in ("what", "owner", "without"):
            if not w.get(k):
                P.append(f"{label}: no `{k}`")
        for k in ("asked", "needed_by"):
            if as_date(w.get(k)) is None:
                P.append(f"{label}: `{k}` is a date, YYYY-MM-DD")
        if (w.get("blocks") or w.get("slows")) and not w.get("missing") \
                and not w.get("resolved"):
            P.append(f"{label}: blocks or slows something and has no `missing`, what the item "
                     "lacks")
        for k in ("blocks", "slows"):
            for i in w.get(k) or []:
                if str(i) not in items:
                    P.append(f"{label}: `{k}` names {i}, which is not an item")
        for k in ("what", "owner", "without", "missing"):
            if w.get(k) and DASHES.search(str(w[k])):
                P.append(f"{label}: a long dash in `{k}`")
    return P


# ─────────────────────────────────────────────────────────────────────────────
# What the workbook shows

@dataclass
class Model:
    name: str
    when: date
    prev_date: date
    delivery: date
    start: date
    next_update: date
    rel: str
    prev_label: str
    this_label: str
    plan_rows: list
    todo: list
    done: list
    out: list
    status: dict          # id -> the Stato of its row
    waits: list
    prev_closed: dict
    this_closed: dict
    prev_open: dict
    table: list
    milestones: list
    changes: list


def period_label(a: date, b: date) -> str:
    if a == b:
        return dm(a)
    if (b - a).days == 1:
        return f"{dm(a)} e {dm(b)}"
    return f"dal {dm(a)} al {dm(b)}"


def day_row(d: date, entry: dict, items: dict, alias: dict) -> list:
    """One row of the day-by-day table: date, the four columns, the five categories."""
    cols = {k: Fraction(0) for k in BULK_KEYS}
    for k, h in ((entry or {}).get("themes") or {}).items():
        cols[k] += num(h)
    for k, h in ((entry or {}).get("hours") or {}).items():
        it = items[alias.get(str(k), str(k))]
        col = OUT if (it.excluded or it.scope == OUT) else it.theme
        cols[col] += num(h)
    cats = [num(((entry or {}).get("outside") or {}).get(c, 0)) for c in CATEGORIES]
    return [d, cols["architettura"], cols["sviluppo"], cols["deploy"], cols[OUT], *cats]


def wait_status(w: dict, when: date) -> str:
    e = as_date(w["needed_by"])
    if e < when:
        n = (when - e).days
        return f"SCADUTA da {n} {'giorno' if n == 1 else 'giorni'}"
    if e == when:
        return "Scade oggi"
    n = (e - when).days
    return f"Entro {n} {'giorno' if n == 1 else 'giorni'}"


def build_model(ctx: Context) -> Model:
    state, items, when = ctx.state, ctx.items, ctx.when
    rel = str(state["release"]["name"])
    start = as_date(state["release"]["start"])
    delivery = as_date(state["release"]["delivery"])
    order = state.get("order") or {}
    waits = sorted((w for w in state.get("waits") or [] if not w.get("resolved")),
                   key=lambda w: (as_date(w["needed_by"]), str(w["what"])))
    todo = [items[str(i)] for i in order.get("todo") or []]
    out = [items[str(i)] for i in order.get("out") or []]
    theme_rank = list(THEMES)
    done = sorted((it for it in items.values() if it.state == "closed" and it.scope == rel
                   and not it.excluded),
                  key=lambda it: (it.closed_on, theme_rank.index(it.theme), sort_id(it.shown_id)))

    status = {}
    for it in todo:
        stop = [w for w in waits if it.id in [str(x) for x in w.get("blocks") or []]]
        slow = [w for w in waits if it.id in [str(x) for x in w.get("slows") or []]]
        worked = f"{ore(it.hours, 'lavorat')}" if it.hours else ""
        if stop:
            s = "Bloccata: " + "; ".join(str(w["missing"]) for w in stop)
        elif slow:
            s = "Rallentata: " + "; ".join(str(w["missing"]) for w in slow)
        elif it.hours:
            s = f"In corso: {worked}"
        else:
            s = "Da iniziare"
        if (stop or slow) and it.hours:
            s += f"; {worked}"
        status[it.id] = s
    for it in done:
        word = "Risolto" if it.kind == "KI" else "Chiusa"
        s = f"{word} il {dm(it.closed_on)}"
        if it.kind == "OD" and it.closer:
            s += f", chiude {it.id}"
        status[it.shown_id] = s

    prev_voci = (ctx.prev.frozen.get("voci") or {}) if ctx.prev else {}
    history = chain(ctx.snaps, ctx.prev)

    def out_since(it: Item) -> date | None:
        if (prev_voci.get(it.id) or {}).get("scope") not in (None, OUT):
            return when
        later = None
        for s in history:                      # newest first
            v = (s.frozen.get("voci") or {}).get(it.id) or {}
            if v.get("scope") == OUT:
                later = s.date
            elif v.get("scope") is not None:
                return later
        return None

    for it in out:
        since = out_since(it)
        status[it.id] = ("Fuori perimetro" + (f" dal {dm(since)}" if since else "")
                         + f": {it.out_reason}")

    plan = dated(state.get("plan"))
    nxt = next_working(when)
    entries = [(d, e) for d in (when, nxt) for e in plan.get(d) or []]
    plan_rows = []
    for k, (d, e) in enumerate(entries):
        it = items[str(e["item"])]
        h = num(e["hours"])
        earlier = any(str(x["item"]) == it.id for _, x in entries[:k])
        closing_later = next((dd for dd, x in entries[k + 1:]
                              if str(x["item"]) == it.id and x.get("closes")), None)
        if e.get("closes"):
            phrase = "chiusura"
        else:
            phrase = "prosegue" if (it.hours or earlier) else "inizio"
            if closing_later:
                phrase += f", chiusura prevista il {dm(closing_later)}"
            elif phrase == "inizio":
                phrase += ", prosegue nei giorni successivi"
        plan_rows.append({"item": it, "status": f"In programma il {dm(d)}, {ore(h)}: {phrase}"})

    prev_date = ctx.prev.date
    pf = ctx.prev.frozen
    if pf.get("baseline"):
        prev_label = "linea di base"
    else:
        p = pf.get("period") or {}
        prev_label = period_label(as_date(p.get("from")), as_date(p.get("to")))

    def by_theme(ids_states) -> dict:
        out_ = {t: 0 for t in THEMES}
        for t in ids_states:
            if t in out_:
                out_[t] += 1
        return out_

    pp = chain(ctx.snaps, ctx.prev)[1:2]
    pp_voci = (pp[0].frozen.get("voci") or {}) if pp else {}
    p_rel = str((pf.get("release") or {}).get("name"))
    prev_closed = by_theme(frozen_theme(v) for i, v in prev_voci.items()
                           if v.get("state") == "closed" and str(v.get("scope")) == p_rel
                           and not v.get("excluded") and not pf.get("baseline")
                           and (pp_voci.get(i) or {}).get("state") != "closed")
    this_closed = by_theme(it.theme for it in done
                           if (prev_voci.get(it.id) or {}).get("state") != "closed")
    prev_open = by_theme(frozen_theme(v) for v in prev_voci.values()
                         if v.get("state") == "open" and str(v.get("scope")) == p_rel
                         and not v.get("excluded") and not v.get("split"))

    frozen_table = {}
    if pf.get("format") == FORMAT:
        for r in pf.get("table") or []:
            frozen_table[as_date(r[0])] = [as_date(r[0])] + [num(x) for x in r[1:]]
    table = []
    d = start
    while d < when:
        table.append(frozen_table.get(d) or day_row(d, ctx.days.get(d) or {}, items, ctx.alias))
        d += timedelta(days=1)

    milestones = sorted(((str(m["name"]), as_date(m["date"]))
                         for m in state.get("milestones") or []), key=lambda x: (x[1], x[0]))

    changes = []
    for it in items.values():
        before = prev_voci.get(it.id)
        if before is None:
            changes.append(f"nuova: {it.id}")
            continue
        if it.state == "closed" and before.get("state") != "closed" and it.scope == rel:
            changes.append(f"chiusa: {it.shown_id}")
        if split_parent(it) and not before.get("split"):
            changes.append(f"spezzata: {it.id} in {', '.join(it.children)}")
        if it.state == "open" and before.get("state") == "open" and it.size and \
                before.get("size") and it.size != before.get("size"):
            changes.append(f"ristimata: {it.id} da {before['size']} a {it.size}")
        if it.state == "open" and it.scope == OUT and before.get("scope") not in (None, OUT):
            changes.append(f"uscita dal perimetro: {it.id}")
        if it.state == "open" and it.scope == rel and before.get("scope") == OUT:
            changes.append(f"entrata nel perimetro: {it.id}")
    this_label = period_label(prev_date, when - timedelta(days=1))
    return Model(ctx.name, when, prev_date, delivery, start, nxt, rel, prev_label, this_label,
                 plan_rows,
                 todo, done, out, status, waits, prev_closed, this_closed, prev_open, table,
                 milestones, sorted(changes))


def figures(m: Model) -> dict:
    """Every number the workbook shows, computed here and written beside its formula."""
    F: dict = {}
    when, start = m.when, m.start
    y = when - timedelta(days=1)
    windows = [("Ultimi 3 giorni lavorativi", workday(when, -3), y),
               ("Ultimi 7 giorni", when - timedelta(days=7), y),
               ("Ultimi 30 giorni", when - timedelta(days=30), y),
               ("Dall'inizio del progetto", start, y)]
    F["windows"] = []
    for label, a, b in windows:
        sel = [r for r in m.table if a <= r[0] <= b]
        cols = [sum((r[i] for r in sel), Fraction(0)) for i in range(1, 10)]
        arch, svil, dep, out_ = cols[:4]
        outside = sum(cols[4:], Fraction(0))
        tot = arch + svil + dep + out_ + outside
        nd = networkdays(max(a, start), b)
        avg = (arch + svil + dep) / nd if nd > 0 else Fraction(0)
        F["windows"].append({"label": label, "from": a, "to": b, "tot": tot, "arch": arch,
                             "svil": svil, "dep": dep, "out": out_, "outside": outside,
                             "avg": avg, "cats": cols[4:]})
    for wd in F["windows"]:
        t = wd["tot"]
        wd["pct"] = [x / t if t else Fraction(0)
                     for x in (wd["arch"], wd["svil"], wd["dep"], wd["out"], wd["outside"])]
    w3, w7, _, w0 = F["windows"]

    nd3 = networkdays(w3["from"], w3["to"])
    D = excel_round(w3["tot"] / nd3, 1) if nd3 else Fraction(0)
    E = excel_round(w3["out"] / nd3, 1) if nd3 else Fraction(0)
    Fo = excel_round(w3["outside"] / nd3, 1) if nd3 else Fraction(0)
    G = excel_round(D - E - Fo, 1)
    C = sum((it.top() for it in m.todo), Fraction(0))
    if G <= 0:
        H = I = J = "non stimabile"
    else:
        H = math.ceil(excel_round(C / G, 9))
        I = workday(when - timedelta(days=1), max(1, H))
        J = networkdays(m.delivery + timedelta(days=1), I) if I > m.delivery else 0
    F["case"] = {"B": len(m.todo), "C": C, "D": D, "E": E, "F": Fo, "G": G, "H": H, "I": I,
                 "J": J}
    F["B4"] = dmy(m.delivery)
    F["B5"] = f"il {dm(I)}" if isinstance(I, date) else "non stimabile"
    if not isinstance(J, int):
        F["B6"] = "non stimabile"
    elif J == 0:
        F["B6"] = "nessuno"
    else:
        F["B6"] = f"{J} {'giorno lavorativo' if J == 1 else 'giorni lavorativi'}"
    statuses = [wait_status(w, when) for w in m.waits]
    late = sum(1 for s in statuses if s.startswith("SCADUTA") or s == "Scade oggi")
    F["wait_status"] = statuses
    n = len(m.waits)
    F["B7"] = ("non dipende da richieste ad altri." if not n else
               ("arriva in tempo l'unica cosa richiesta" if n == 1 else
                f"arrivano in tempo le {n} cose richieste") + " ad altri (punto 3). Oggi "
               + ("nessuna è scaduta." if late == 0 else "1 è scaduta o scade oggi."
                  if late == 1 else f"{late} sono scadute o scadono oggi."))
    r0 = [excel_round(x, 0) for x in (w0["arch"], w0["svil"], w0["dep"], w0["out"],
                                      w0["outside"])]
    pct0 = excel_round(w0["pct"][4] * 100, 0)
    F["B8"] = (f"Dall'inizio del progetto {hours(sum(r0, Fraction(0)))} ore lavorate: "
               f"{hours(r0[0])} architettura, {hours(r0[1])} sviluppo, {hours(r0[2])} deploy, "
               f"{hours(r0[3])} fuori perimetro, {hours(r0[4])} fuori dal prodotto "
               f"({hours(pct0)}%: riunioni, reportistica, supporto, formazione).")

    F["themes"] = {}
    for t in THEMES:
        lst = [it for it in m.todo if it.theme == t]
        top = sum((it.top() for it in lst), Fraction(0))
        F["themes"][t] = {"done": sum(1 for it in m.done if it.theme == t),
                          "prev_closed": m.prev_closed[t], "this_closed": m.this_closed[t],
                          "todo": len(lst), "delta": len(lst) - m.prev_open[t],
                          "est": f"{hours(top)} ore", "top": top}
    F["est_total"] = f"{hours(C)} ore"

    nd_deliv = max(1, networkdays(when, m.delivery))
    nd7 = networkdays(w7["from"], w7["to"])
    rate7 = w7["tot"] / nd7 if nd7 else Fraction(0)
    share = min(Fraction(1), (C / nd_deliv) / rate7) if C and rate7 else Fraction(0)
    optimal = [share * F["themes"][t]["top"] / C if C and rate7 else Fraction(0)
               for t in THEMES]
    o7, x7 = w7["pct"][3], w7["pct"][4]
    rest = Fraction(1) - (min(Fraction(1), (C / nd_deliv) / rate7) if rate7 else 0)
    optimal += [rest * o7 / (o7 + x7) if (o7 + x7) else Fraction(0),
                rest * x7 / (o7 + x7) if (o7 + x7) else Fraction(0)]
    F["now_share"] = list(w7["pct"])
    F["optimal"] = optimal
    F["share_release"] = share

    # The Gantt: what is done where it happened, what is left in a row at the estimate's pace,
    # each item for the top of its size, so the last one ends on the date of point 2.
    gantt = []
    for it in m.done:
        gantt.append({"kind": "done", "item": it, "start": it.first_day or it.closed_on,
                      "end": it.closed_on})
    cum = Fraction(0)
    for it in m.todo:
        if G > 0:
            sched = workday(when - timedelta(days=1), math.floor(excel_round(cum / G, 9)) + 1)
            end = workday(when - timedelta(days=1),
                          max(1, math.ceil(excel_round((cum + it.top()) / G, 9))))
        else:
            sched = end = None
        started = it.first_day if it.first_day and it.first_day < when else None
        gantt.append({"kind": "todo", "item": it, "start": started or sched, "end": end,
                      "started": started is not None})
        cum += it.top()
    for name, d in m.milestones:
        gantt.append({"kind": "milestone", "name": name, "date": d})
    gantt.append({"kind": "delivery", "name": "Consegna concordata", "date": m.delivery})
    ends = [g["end"] for g in gantt if g["kind"] in ("todo", "done") and g["end"]]
    ends += [g["date"] for g in gantt if g["kind"] in ("milestone", "delivery")]
    first = workday(start - timedelta(days=1), 1)
    last = max(ends + [when])
    cols = []
    d = first
    while d <= last:
        cols.append(d)
        d = workday(d, 1)
    F["gantt"] = gantt
    F["gantt_days"] = cols
    return F


def summary(m: Model, F: dict) -> str:
    """What the skill shows in the conversation: the first block of the summary sheet."""
    lines = [f"{m.name.upper()} · stato del rilascio al {dmy(m.when)}",
             f"Consegna concordata: {F['B4']}",
             f"Consegna prevista oggi: {F['B5']}",
             f"Ritardo: {F['B6']}",
             f"La previsione vale solo se {F['B7']}",
             f"Dove va il tempo: {F['B8']}"]
    if m.changes:
        lines.append("Cambiato dall'aggiornamento precedente:")
        lines += [f"- {c}" for c in m.changes]
    return "\n".join(lines) + "\n"


def load_workbook_module():
    name = "_framework_digest_workbook"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, WORKBOOK)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ─────────────────────────────────────────────────────────────────────────────
# Writing, committing, pushing

def git(*args, cwd: Path, check: bool = False) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip() or r.stdout.strip()}")
    return r


def is_local(url: str) -> bool:
    return (url.startswith(("/", "./", "../", "file://"))
            or (not re.match(r"^[\w.+-]+://", url) and ":" not in url))


def private(url: str) -> tuple[bool, str]:
    """Whether a remote is private, as GitHub reports it. A local path publishes nothing."""
    if is_local(url):
        return True, "a local path: nothing leaves the machine"
    try:
        r = subprocess.run(["gh", "repo", "view", url, "--json", "isPrivate", "-q", ".isPrivate"],
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, f"cannot ask GitHub whether {url} is private ({e}); `gh` is needed"
    if r.returncode:
        return False, f"cannot ask GitHub whether {url} is private: {r.stderr.strip()}"
    if r.stdout.strip() != "true":
        return False, f"{url} is not private: the hours somebody works do not go there"
    return True, "private"


def store_status(root: Path) -> dict:
    store = root / STORE
    out = {"path": str(STORE), "exists": store.is_dir(), "git": False, "origin": None,
           "ignored": None}
    if store.is_dir() and (store / ".git").exists():
        out["git"] = True
        r = git("remote", "get-url", "origin", cwd=store)
        out["origin"] = r.stdout.strip() or None
    top = git("rev-parse", "--show-toplevel", cwd=root)
    if top.returncode == 0:
        out["ignored"] = git("check-ignore", "-q", f"{STORE.as_posix()}/frozen.probe",
                             cwd=root).returncode == 0
    return out


def freeze(ctx: Context, m: Model | None, path: Path, number: int) -> None:
    items = ctx.items
    rel = str(ctx.state["release"]["name"])
    frozen = {
        "format": FORMAT,
        "digest": f"DIG-{number:03d}",
        "product": ctx.product,
        "date": ctx.when.isoformat(),
        "at": (ctx.now or datetime.now().astimezone()).isoformat(timespec="seconds"),
        "baseline": ctx.baseline,
        "previous": ({"dir": ctx.prev.name, "sha256": ctx.prev.digest()} if ctx.prev else None),
        "release": {"name": rel,
                    "delivery": as_date(ctx.state["release"]["delivery"]).isoformat(),
                    "start": as_date(ctx.state["release"]["start"]).isoformat()},
        "period": (None if ctx.baseline else
                   {"from": ctx.prev.date.isoformat(),
                    "to": (ctx.when - timedelta(days=1)).isoformat()}),
        "voci": {i: {"kind": it.kind, "state": it.state, "scope": it.scope, "theme": it.theme,
                     "size": it.size, "excluded": it.excluded, "split": split_parent(it),
                     "closer": it.closer, "children": it.children, "hours": plain(it.hours),
                     "closed_on": it.closed_on.isoformat() if it.closed_on else None}
                 for i, it in sorted(items.items(), key=lambda x: sort_id(x[0]))},
        "days": {d.isoformat(): canonical_day(e)
                 for d, e in sorted(ctx.days.items()) if d < ctx.when},
    }
    table = m.table if m else [
        day_row(d, ctx.days.get(d) or {}, items, ctx.alias)
        for d in (as_date(ctx.state["release"]["start"]) + timedelta(days=k)
                  for k in range((ctx.when - as_date(ctx.state["release"]["start"])).days))]
    frozen["table"] = [[r[0].isoformat()] + [plain(x) for x in r[1:]] for r in table]
    frozen["sources_disagree"] = ctx.notes
    (path / "frozen.yaml").write_text(
        "# Written by skills/digest/scripts/digest.py. Never edited: the next digest checks "
        "its hash.\n" + yaml.safe_dump(frozen, allow_unicode=True, sort_keys=False),
        encoding="utf-8")


def commit_and_push(root: Path, message: str) -> tuple[bool, str]:
    store = root / STORE
    git("add", "-A", cwd=store, check=True)
    r = git("commit", "-q", "-m", message, cwd=store)
    if r.returncode and "nothing to commit" not in (r.stdout + r.stderr):
        return False, f"commit failed: {r.stderr.strip() or r.stdout.strip()}"
    url = git("remote", "get-url", "origin", cwd=store).stdout.strip()
    ok, why = private(url)
    if not ok:
        return False, f"committed in {STORE}, not pushed: {why}"
    r = git("push", "-q", "-u", "origin", "HEAD", cwd=store)
    if r.returncode:
        return False, f"committed in {STORE}, not pushed: {r.stderr.strip()}"
    return True, f"committed and pushed to {url}"


def init_store(root: Path, url: str) -> int:
    root = root.resolve()
    store = root / STORE
    if (store / ".git").exists():
        origin = git("remote", "get-url", "origin", cwd=store).stdout.strip()
        print(f"{STORE} is already a repository, origin {origin or 'none'}")
        return 0
    if store.exists() and any(store.iterdir()):
        print(f"{STORE} exists and is not a repository: move its contents into a clone of "
              f"{url}, or remove it", file=sys.stderr)
        return 1
    if is_local(url) and not url.startswith(("/", "file://")):
        url = str((root / url).resolve())          # relative to the project, not to the shell
    ok, why = private(url)
    if not ok:
        print(why, file=sys.stderr)
        return 1
    store.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["git", "clone", "-q", url, str(store)], capture_output=True, text=True)
    if r.returncode:
        print(f"git clone {url}: {r.stderr.strip()}", file=sys.stderr)
        return 2
    print(f"cloned {url} into {STORE} ({why})")
    if git("rev-parse", "--show-toplevel", cwd=root).returncode == 0:
        probe = f"{STORE.as_posix()}/frozen.probe"
        if git("check-ignore", "-q", probe, cwd=root).returncode != 0:
            gi = root / ".gitignore"
            before = gi.read_text(encoding="utf-8") if gi.exists() else ""
            gi.write_text(before + ("" if not before or before.endswith("\n") else "\n")
                          + f"{STORE.as_posix()}/\n", encoding="utf-8")
            print(f"added {STORE.as_posix()}/ to .gitignore: the hours stay out of the "
                  "documentation repository")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# The inventory: what the skill asks about

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
FILE = re.compile(r"^diff --git a/(.+?) b/(.+)$")


def ids_regex() -> re.Pattern:
    registry = yaml.safe_load((FRAMEWORK / "schemas" / "artifact-types.yaml")
                              .read_text(encoding="utf-8"))
    return re.compile(r"\b((?:%s)-\d{3,})\b" % "|".join(registry["id_prefixes"]))


def repositories(ctx: Context) -> list[dict]:
    v = load_validator()
    out, seen = [], set()

    def add(name, where: Path, pathspec: str | None):
        if not where.is_dir():
            out.append({"name": name, "read": False, "why": f"{where} is not checked out here"})
            return
        top = git("rev-parse", "--show-toplevel", cwd=where)
        if top.returncode:
            out.append({"name": name, "read": False, "why": f"{where} is not a git repository"})
            return
        t = top.stdout.strip()
        if t in seen:
            return
        seen.add(t)
        out.append({"name": name, "read": True, "path": t, "pathspec": pathspec})

    root = ctx.root
    top = git("rev-parse", "--show-toplevel", cwd=root)
    if top.returncode == 0:
        rel = str(root.resolve().relative_to(Path(top.stdout.strip()).resolve())) or "."
        add("documents", root, rel)
    else:
        out.append({"name": "documents", "read": False, "why": "not a git repository"})
    man = ctx.reg.manifest
    for key, c in (v.as_map(man.meta.get("code")) if man else {}).items():
        if not isinstance(c, dict):
            continue
        if not c.get("path"):
            out.append({"name": f"product.{key}", "read": False,
                        "why": "no `path` in product.yaml: nobody clones it here"})
            continue
        add(f"product.{key}", (root / str(c["path"])).resolve(), None)
    for a in ctx.reg.arts:
        if a.type != "platform-architecture":
            continue
        for key, c in v.as_map(a.meta.get("code")).items():
            if isinstance(c, dict) and ctx.product in v.as_list(c.get("used_by")):
                if not c.get("path"):
                    out.append({"name": f"platform.{key}", "read": False,
                                "why": "no `path` in PLATFORM.md"})
                    continue
                add(f"platform.{key}", (root / str(c["path"])).resolve(), None)
    return out


def generated_lines(repo: Path, rev: str, path: str) -> set[int]:
    """The line numbers of `path` at `rev` that a generator wrote, between its markers."""
    r = git("show", f"{rev}:{path}", cwd=repo)
    if r.returncode:
        return set()
    out, inside = set(), False
    for n, line in enumerate(r.stdout.splitlines(), 1):
        if line.startswith("<!-- generated:"):
            inside = True
        if inside:
            out.add(n)
        if line.startswith("<!-- /generated"):
            inside = False
    return out


def changed_text(repo: Path, sha: str, diff: str, skip: set[str]) -> str:
    """The lines a commit added or removed in the documents, without what a generator wrote.

    A regenerated index names every open entry and every active change, so a commit that only
    ran `--emit-index` would otherwise propose the whole register as worked on.
    """
    out, path, old_n, new_n = [], None, 0, 0
    gen_old: set[int] = set()
    gen_new: set[int] = set()
    for line in diff.splitlines():
        m = FILE.match(line)
        if m:
            path = m.group(2)
            if Path(path).name in skip:
                path = None
                continue
            gen_old = generated_lines(repo, f"{sha}^", path)
            gen_new = generated_lines(repo, sha, path)
            continue
        if path is None:
            continue
        h = HUNK.match(line)
        if h:
            old_n, new_n = int(h.group(1)), int(h.group(3))
            continue
        if line.startswith(("+++", "---")):
            continue
        if line.startswith("+"):
            if new_n not in gen_new:
                out.append(line[1:])
            new_n += 1
        elif line.startswith("-"):
            if old_n not in gen_old:
                out.append(line[1:])
            old_n += 1
    return "\n".join(out)


def worked(ctx: Context, since: str) -> tuple[dict, list, list]:
    """Which items the commits since the last digest name, day by day: a proposal only.

    In the documents, the identifiers on the lines a commit changed; in the code, the ones its
    message cites. P-07 binds a change to the text of a pull request, not to a commit, so
    nothing here is certain, and the person writes the hours.
    """
    rx = ids_regex()
    registry = yaml.safe_load((FRAMEWORK / "schemas" / "artifact-types.yaml")
                              .read_text(encoding="utf-8"))
    skip = set(registry["scan"]["skip_files"])
    mine = set(ctx.voci) | set(ctx.alias)
    found: dict[str, dict[str, list]] = {}
    loose, repos = [], repositories(ctx)
    for repo in repos:
        if not repo.get("read"):
            continue
        docs = repo["pathspec"] is not None
        cmd = ["log", "--all", f"--since={since}", "--format=%x1e%h%x1f%as%x1f%s%x1f%b%x1f"]
        if docs:
            cmd += ["-p", "-U0", "--no-ext-diff", "--no-color", "--", repo["pathspec"]]
        where = Path(repo["path"])
        r = git(*cmd, cwd=where)
        for record in r.stdout.split("\x1e")[1:]:
            parts = record.split("\x1f")
            sha, day, subject, body = parts[0], parts[1], parts[2], parts[3]
            text = subject + "\n" + body
            if docs and len(parts) > 4:
                text += "\n" + changed_text(where, sha, parts[4], skip)
            hits = {ctx.alias.get(i, i) for i in rx.findall(text) if i in mine}
            for i in hits:
                found.setdefault(day, {}).setdefault(i, []).append(
                    f"{repo['name']} {sha} {subject}")
            if not hits and not docs:
                loose.append(f"{repo['name']} {day} {sha} {subject}")
    return found, loose, repos


def inventory(ctx: Context) -> dict:
    state = ctx.state or {}
    rows = state.get("items") or {}
    prev_v = (ctx.prev.frozen.get("voci") or {}) if ctx.prev else {}
    out = {"product": ctx.product, "date": ctx.when.isoformat(),
           "state_format": state.get("format"),
           "previous": ({"digest": ctx.prev.name, "date": ctx.prev.date.isoformat()}
                        if ctx.prev else None)}
    days = dated(state.get("days"))
    if ctx.prev:
        lo, d, need = ctx.prev.date, ctx.prev.date, []
        while d < ctx.when:
            if d not in days and working_day(d):
                need.append(d.isoformat())
            d += timedelta(days=1)
        out["period"] = {"from": lo.isoformat(),
                         "to": (ctx.when - timedelta(days=1)).isoformat(),
                         "working_days_without_hours": need}
    out["unclassified"] = [{"id": i, "kind": vo.kind, "status": vo.status, "title": vo.title,
                            "file": vo.file}
                           for i, vo in sorted(ctx.voci.items(), key=lambda x: sort_id(x[0]))
                           if i not in rows]
    out["changed"] = [{"id": i, "confirmed_as": rows[i].get("seen"), "now": vo.title}
                      for i, vo in ctx.voci.items()
                      if isinstance(rows.get(i), dict) and vo.title and vo.state == "open"
                      and (rows[i].get("seen") or "").strip() != vo.title.strip()]
    closed = sorted((i for i, vo in ctx.voci.items() if vo.state == "closed"
                     and (prev_v.get(i) or {}).get("state") not in (None, "closed")),
                    key=sort_id)
    out["new_since"] = sorted((i for i in ctx.voci if ctx.prev and i not in prev_v), key=sort_id)
    out["vanished"] = sorted((i for i in rows if i not in ctx.voci and i not in ctx.alias
                              and (prev_v.get(i) or {}).get("state") not in
                              ("closed", "gone", "replaced")
                              and not (rows[i] or {}).get("gone")), key=sort_id)
    out["replaced"] = {i: vo.children for i, vo in ctx.voci.items() if vo.state == "replaced"
                       and (prev_v.get(i) or {}).get("state") != "replaced"}
    out["aliases"] = {a: od for a, od in sorted(ctx.alias.items())}
    out["sources_disagree"] = ctx.notes
    proposed_close = {}
    if ctx.prev:
        since = ctx.prev.frozen.get("at") or ctx.prev.date.isoformat()
        found, loose, repos = worked(ctx, str(since))
        out["worked_by_day"] = {
            d: {i: ev for i, ev in sorted(x.items(), key=lambda y: sort_id(y[0]))}
            for d, x in sorted(found.items())}
        out["commits_without_an_item"] = loose
        out["repositories"] = repos
        for d, x in sorted(found.items()):
            for i in x:
                proposed_close[i] = d
    out["closed_since"] = [{"id": i, "proposed_closed_on": proposed_close.get(i)}
                           for i in closed]
    waits = [w for w in (state.get("waits") or []) if isinstance(w, dict)
             and not w.get("resolved")]
    out["waits_open"] = [{"what": w.get("what"), "owner": w.get("owner"),
                          "status": wait_status(w, ctx.when)
                          if as_date(w.get("needed_by")) else None} for w in waits]
    out["milestones_declared"] = state.get("milestones") is not None
    out["store"] = store_status(ctx.root)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# From the state file of 4.1.0

CATEGORY_HINTS = [("riunion", "riunioni"), ("formazion", "formazione"), ("junior", "formazione"),
                  ("sollecit", "solleciti"), ("access", "solleciti"),
                  ("report", "reportistica"), ("presentazion", "reportistica"),
                  ("support", "supporto"), ("demo", "supporto"), ("produzion", "supporto")]


def category_of(name: str) -> str | None:
    low = name.lower()
    return next((c for hint, c in CATEGORY_HINTS if hint in low), None)


def migrate(root: Path, product: str | None) -> int:
    """Rewrite a 4.1.0 state file as format 2: what is mechanical, converted; the rest, listed.

    Every conversion here is deterministic, and every one that is not is left for the person:
    a period of several days cannot be split into days by a script, a plan has no hours, a
    closing date and a reason for being outside the perimeter were never asked. The check
    refuses until they are declared, and lists them.
    """
    root = root.resolve()
    store = root / STORE
    if product is None:
        found = sorted(p.name[len("state-"):-len(".yaml")] for p in store.glob("state-*.yaml"))
        if len(found) != 1:
            print(f"say which product with --product: {', '.join(found) or 'none'}",
                  file=sys.stderr)
            return 2
        product = found[0]
    path = store / f"state-{product}.yaml"
    data, err = read_state(store, product)
    if err:
        print(err, file=sys.stderr)
        return 2
    if data.get("format") == FORMAT:
        print(f"{path.name} is already format {FORMAT}")
        return 0
    report = []
    new: dict = {"format": FORMAT, "product": data.get("product") or product}
    release = dict(data.get("release") or {})
    release.setdefault("start", None)
    new["release"] = release
    if release.get("start") is None:
        report.append("release.start: the first day of the project, to declare")
    items = {}
    for i, row in (data.get("items") or {}).items():
        row = dict(row or {})
        if row.get("theme") in OLD_THEMES:
            report.append(f"{i}: theme {row['theme']} is now {OLD_THEMES[row['theme']]}")
            row["theme"] = OLD_THEMES[row["theme"]]
        items[i] = row
    new["items"] = items
    ends = {}
    for s in snapshots(store):
        p = s.frozen.get("period") if s.product == product else None
        if p:
            ends[as_date(p["from"])] = as_date(p["to"])
    days, mapped = {}, {}
    for k, block in (data.get("periods") or {}).items():
        d = as_date(k)
        if d is None or not isinstance(block, dict):
            continue
        end = ends.get(d)
        outside = {}
        for name, h in (block.get("outside") or {}).items():
            c = category_of(str(name)) or str(name)
            mapped[str(name)] = c
            outside[c] = outside.get(c, 0) + h
        entry = {"hours": dict(block.get("hours") or {}), "outside": outside}
        if end == d:
            days[d] = entry
        else:
            report.append(f"the period from {d} to {end or 'the day before the next digest'} "
                          "covers several days: split its hours by day under `days`")
            days[d] = entry
    for name, c in sorted(mapped.items()):
        report.append(f"outside the register: {name!r} counted as {c!r}"
                      + ("" if c in CATEGORIES else ", which is not a category: choose one"))
    new["days"] = {d.isoformat(): e for d, e in sorted(days.items())}
    waits = []
    for w in data.get("waits") or []:
        w = dict(w or {})
        if w.pop("note", None):
            report.append(f"wait {w.get('what')!r}: its note has no place in the workbook")
        waits.append(w)
    new["waits"] = waits
    for i, r in (data.get("requests") or {}).items():
        report.append(f"requests: the decision on {i} asked of {r.get('to')} by {r.get('by')} "
                      "has no section in the workbook; if it is still pending, declare it as a "
                      "wait")
    if data.get("standard_hours") is not None:
        report.append("standard_hours: no longer used, the estimate subtracts the real averages")
    report.append("order.todo and order.out: the rows of the two lists, to declare")
    report.append("plan: the next two working days, with the hours and whether each closes")
    report.append("milestones: to declare, `[]` if there are none")
    report.append("days: every day from release.start to the day before the first digest, "
                  "rebuilt in bulk by theme and category, adding up theme by theme to the "
                  "hours_before of the items")
    report.append("then --check lists what each item still needs: size, closed_on, out_reason")
    path.write_text(
        "# Stato del digest: ciò che la persona ha dichiarato, scritto dalla skill `digest`.\n"
        + yaml.safe_dump(new, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"{path.name} rewritten in format {FORMAT}.")
    for line in report:
        print(f"- {line}")
    return 0


# ─────────────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", type=Path, default=Path("."), help="the project's documents")
    ap.add_argument("--product", help="the product; optional when there is one")
    ap.add_argument("--date", help="the digest's date, YYYY-MM-DD; default today")
    ap.add_argument("--now", help="the instant recorded in the snapshot, ISO 8601; default "
                                  "now. For fixtures, whose history is dated")
    ap.add_argument("--copy-to", type=Path, help="also copy the workbook into this directory")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="list every reason not to write")
    mode.add_argument("--inventory", action="store_true",
                      help="what the skill asks about: new, changed, closed, worked, by day")
    mode.add_argument("--baseline", action="store_true",
                      help="the first run: freeze the state, write nothing to send")
    mode.add_argument("--migrate", action="store_true",
                      help="rewrite a state file of 4.1.0 in the current format")
    mode.add_argument("--init-store", metavar="URL",
                      help="clone the private repository into _meta/digest")
    a = ap.parse_args(argv)
    if a.init_store:
        return init_store(a.root, a.init_store)
    if a.migrate:
        return migrate(a.root, a.product)
    try:
        when = date.fromisoformat(a.date) if a.date else date.today()
    except ValueError:
        print(f"--date {a.date!r} is YYYY-MM-DD", file=sys.stderr)
        return 2
    try:
        ctx = prepare(a.root, a.product, when, a.baseline)
        ctx.now = datetime.fromisoformat(a.now) if a.now else None
        if a.inventory:
            print(yaml.safe_dump(inventory(ctx), allow_unicode=True, sort_keys=False), end="")
            return 0
        problems = check(ctx)
        if problems:
            raise Refusal(problems)
        m = None if a.baseline else build_model(ctx)
        F = None if a.baseline else figures(m)
    except Refusal as r:
        for p in r.problems:
            print(p)
        return 1
    if a.check:
        print("ok")
        return 0

    st = store_status(ctx.root)
    setup = []
    if not st["git"] or not st["origin"]:
        setup.append(f"{STORE} is not a clone of a private repository: run --init-store first")
    if st["ignored"] is False:
        setup.append(f"{STORE} is not ignored by the documentation repository: the hours would "
                     "end up in it. Add it to .gitignore, or run --init-store")
    if setup:
        for p in setup:
            print(p)
        return 1
    number = max((s.number for s in ctx.snaps), default=0) + 1
    name = f"DIG-{number:03d}-{ctx.product}-{ctx.when.isoformat()}"
    path = ctx.root / STORE / name
    path.mkdir(parents=True)
    if a.baseline:
        # Nothing to send: the baseline is what the first workbook compares itself with.
        rel = str(ctx.state["release"]["name"])
        rest = [it for it in ctx.items.values() if it.state == "open" and it.scope == rel
                and not it.excluded and not split_parent(it)]
        top = sum((it.top() for it in rest), Fraction(0))
        text = (f"{ctx.name.upper()}, linea di base del {dmy(ctx.when)}\n"
                "Non si invia: il primo aggiornamento è quello del prossimo giorno lavorativo.\n"
                f"Voci da fare nel perimetro: {len(rest)}, {hours(top)} ore\n")
        freeze(ctx, None, path, number)
        out_file = None
    else:
        text = summary(m, F)
        out_file = path / f"{name}.xlsx"
        load_workbook_module().write(m, F, out_file, ctx.now or datetime.now().astimezone())
        freeze(ctx, m, path, number)
    pushed, how = commit_and_push(ctx.root, name)
    print(text, end="")
    if ctx.notes:
        print("Fonti in disaccordo:")
        for x in ctx.notes:
            print(f"- {x}")
    if out_file and a.copy_to:
        a.copy_to.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out_file, a.copy_to / out_file.name)
        print(f"copia: {a.copy_to / out_file.name}")
    print(f"{path.relative_to(ctx.root)} · {how}")
    return 0 if pushed else 3


if __name__ == "__main__":
    sys.exit(main())
