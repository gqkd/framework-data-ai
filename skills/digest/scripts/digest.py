#!/usr/bin/env python3
"""Compute one product's daily digest from the registers and the state file, and print it.

    python3 digest.py --root <project> --product atlas --inventory
    python3 digest.py --root <project> --product atlas --check
    python3 digest.py --root <project> --product atlas
    python3 digest.py --root <project> --product atlas --baseline
    python3 digest.py --root <project> --init-store git@github.com:<owner>/<name>.git

THE REGISTERS SAY WHAT EXISTS, THE STATE FILE SAYS WHAT A PERSON DECLARED, THE DIGEST IS WHAT
FOLLOWS FROM THE TWO. Hours, sizes, themes, the perimeter of a release, waits on other people
and the plan for tomorrow have no source among the artifacts and must not acquire one there,
so they live in a file the person fills through the `digest` skill. Every number printed
comes from the registers, from that file, or from an earlier snapshot; none is composed.

WHERE THINGS LIVE. `_meta/digest/` is a clone of a private repository, kept out of the
documentation repository by its `.gitignore`: the hours somebody works are not documentation,
and the series must not be lost with one laptop. It holds

    state-<product>.yaml                    what the person declared, one file per product
    DIG-NNN-<product>-YYYY-MM-DD/
        DIG-NNN-<product>-YYYY-MM-DD.txt    the digest, as it is sent
        frozen.yaml                         what it was computed from, for the next one

NNN is one sequence across the products, as `PRS` and `SAL` are. A snapshot is never edited:
each one carries the hash of the one before it, and a second digest on the same date takes a
new number and replaces the first as the digest of the day. Rendering commits and pushes the
store, and refuses to push to a remote GitHub does not report as private.

WHAT IS REFUSED, BEFORE ANYTHING IS WRITTEN. `--check` lists every reason, and rendering runs
it first: an identifier in the registers that the state file does not classify; a classified
one that left the registers without being closed; an open item whose title in the register
changed since it was confirmed; a field the digest would have to print and nobody declared;
the hours of the period, or the plan of a day it prints, not declared; a planned item that is
closed, excluded, or a `CHG` still in `draft`; the hours of a past period edited after they
were frozen; an earlier snapshot whose hash no longer matches; a description carrying the
register's jargon or more than two sentences; a long dash anywhere; a register status this
file does not map; a digest dated on a weekend. Fix the state file or the registers, never
this file to get past it.

WHAT THE CANONICAL FORMAT DOES NOT SHOW STAYS OUT OF THE DIGEST. An item worked and not
closed, hours on items outside the perimeter, an item re-estimated or split: the digest
prints only the lines the canonical example has, and the lines it would need for these are
listed after it, ready to paste, together with every value it printed in a form the example
does not show. They are recorded in `frozen.yaml` as `additions` and `provisional`.

Exit codes: 0 done, 1 refused, 2 cannot run, 3 written and committed but not pushed.
Needs PyYAML and jsonschema (it reads the registers through the validator) and `git`;
`gh` only to verify that a GitHub remote is private.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import math
import re
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
STORE = Path("_meta") / "digest"
WIDTH = 74                      # the width the canonical example wraps at, measured on it
OUT = "out"

THEMES = {"architettura": "Architettura", "sviluppo": "Sviluppo",
          "infrastruttura": "Infrastruttura"}
SIZES = {"S": (1, 2), "M": (3, 5), "L": (6, 12), "XL": (13, 40)}

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
KIND_ORDER = {"DEC": 0, "OD": 0, "CHG": 1, "KI": 2, "EVR": 3}
DONE_LABEL = {0: "decisioni prese", 1: "implementazioni fatte", 2: "problemi risolti",
              3: "valutazioni fatte"}

STATE_KEYS = {"product", "standard_hours", "release", "items", "waits", "requests", "plan",
              "periods"}
RELEASE_KEYS = {"name", "delivery", "commitment"}
ITEM_KEYS = {"title", "what", "theme", "scope", "size", "seen", "hours_before", "excluded",
             "split_into", "gone"}
WAIT_KEYS = {"what", "owner", "asked", "needed_by", "without", "missing", "blocks", "slows",
             "note", "resolved"}
REQUEST_KEYS = {"to", "by", "fallback"}
PERIOD_KEYS = {"hours", "outside"}

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
# Never broken across two lines: the size with its hours, and a range with its unit.
UNBREAKABLE = [re.compile(r"[Tt]aglia (?:S|M|L|XL)(?:: \d+(?:,\d+)? h)?[.,;]?"),
               re.compile(r"\d+(?:,\d+)? a \d+(?:,\d+)? h[.,;)]?"),
               re.compile(r"dal \d{2}/\d{2} al \d{2}/\d{2}[.,;]?")]


class Refusal(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


# ─────────────────────────────────────────────────────────────────────────────
# Numbers, dates and lines

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
    s = format(dec(x).normalize(), "f")
    return s


def hours(x: Fraction) -> str:
    """For the digest: a decimal comma, and decimals only when there are some."""
    return plain(x).replace(".", ",")


def one_decimal(x: Fraction) -> str:
    d = dec(x).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return format(d.normalize(), "f").replace(".", ",")


def span(r: tuple[Fraction, Fraction]) -> str:
    return f"{hours(r[0])} a {hours(r[1])} h"


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


def nth_working(start: date, n: int) -> date:
    """The n-th working day counting `start` as the first, or `start` when n is 0."""
    d, count = start, 1
    while count < n:
        d = next_working(d)
        count += 1
    return d


def working_days(a: date, b: date) -> int:
    return sum(1 for i in range((b - a).days + 1) if working_day(a + timedelta(days=i)))


def voci(n: int) -> str:
    return "1 voce" if n == 1 else f"{n} voci"


def agree(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def lower_first(s: str) -> str:
    """`Ambiente preprod` -> `ambiente preprod`, but `API esterne` stays as it is."""
    return s[0].lower() + s[1:] if len(s) > 1 and s[1].islower() else s


def tokens(s: str) -> list[str]:
    out, i = [], 0
    while i < len(s):
        for rx in UNBREAKABLE:
            m = rx.match(s, i)
            if m and (m.end() == len(s) or s[m.end()] == " "):
                out.append(m.group())
                i = m.end()
                break
        else:
            j = s.find(" ", i)
            j = len(s) if j == -1 else j
            out.append(s[i:j])
            i = j
        while i < len(s) and s[i] == " ":
            i += 1
    return out


def wrap(line: str) -> list[str]:
    """Greedy, at WIDTH, continuing under a two-space indent: the canonical example's own rule."""
    if len(line) <= WIDTH:
        return [line]
    lead = "- " if line.startswith("- ") else "  " if line.startswith("  ") else ""
    parts = tokens(line[len(lead):])
    out = [lead + parts[0]]
    for t in parts[1:]:
        if len(out[-1]) + 1 + len(t) <= WIDTH:
            out[-1] += " " + t
        else:
            out.append("  " + t)
    return out


def text_of(lines: list[str]) -> str:
    return "\n".join(w for line in lines for w in wrap(line)) + "\n"


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

    @property
    def txt(self) -> Path:
        return self.path / f"{self.path.name}.txt"

    def digest(self) -> str:
        h = hashlib.sha256((self.path / "frozen.yaml").read_bytes())
        h.update(b"\n\0\n")
        h.update(self.txt.read_bytes() if self.txt.exists() else b"")
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
    """The digest of the latest earlier day: a later number on one date replaces an earlier one."""
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


def periods_of(state: dict) -> dict[date, dict]:
    return {as_date(k): v for k, v in (state.get("periods") or {}).items()
            if as_date(k) is not None}


def plan_of(state: dict) -> dict[date, list]:
    return {as_date(k): v for k, v in (state.get("plan") or {}).items()
            if as_date(k) is not None}


def hours_map(block) -> dict[str, Fraction]:
    out = {}
    for k, val in ((block or {}).get("hours") or {}).items():
        out[str(k)] = num(val)
    return out


def outside_map(block) -> dict[str, Fraction]:
    out = {}
    for k, val in ((block or {}).get("outside") or {}).items():
        out[str(k)] = num(val)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# The computation

@dataclass
class Item:
    """One item as it stands on the digest's date, read from the registers and the state."""
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
    hours: Fraction = Fraction(0)      # all declared, before and in every period

    def rng(self) -> tuple[Fraction, Fraction]:
        lo, hi = SIZES[self.size]
        return Fraction(lo), Fraction(hi)


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
    additions: list = field(default_factory=list)
    provisional: list = field(default_factory=list)
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
    """Every reason not to print. Empty means the digest can be computed and written."""
    P = ctx.problems
    when = ctx.when
    if not working_day(when):
        P.append(f"{when} is a {when.strftime('%A')}: a digest is of a working day")
    state = ctx.state
    if state is None:
        return P
    for k in sorted(set(state) - STATE_KEYS):
        P.append(f"unknown key {k!r} at the top of the state file: nothing reads it")
    if state.get("product") not in (None, ctx.product):
        P.append(f"the state file says product {state.get('product')!r}, this is {ctx.product!r}")
    try:
        if num(state.get("standard_hours")) <= 0:
            raise ValueError
    except (ValueError, TypeError, ZeroDivisionError):
        P.append("`standard_hours` is the length of a normal working day, a positive number")
    release = state.get("release") or {}
    if not isinstance(release, dict) or not release.get("name"):
        P.append("`release.name` is the release the perimeter is measured against")
        release = {}
    for k in sorted(set(release) - RELEASE_KEYS):
        P.append(f"unknown key {k!r} under `release`")
    if as_date(release.get("delivery")) is None:
        P.append("`release.delivery` is the agreed delivery date, YYYY-MM-DD")
    rel = str(release.get("name", ""))

    later = [s for s in ctx.snaps if s.product == ctx.product and s.date > when]
    if later:
        P.append(f"{later[-1].name} is later than {when}: a digest cannot go back in time")
    if ctx.baseline and ctx.prev:
        P.append(f"there is already {ctx.prev.name}: the baseline is the first run, once")
    if not ctx.baseline and not ctx.prev:
        P.append("no earlier digest for this product: the first run is --baseline")

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
            continue                      # reported above as not a mapping
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
        if a in rows and set(rows[a]) - {"hours_before"}:
            ctx.notes.append(f"{a} decides {ctx.alias[a]}: they are one item, and the row of "
                             f"{a} counts only for its hours")

    for vid, vo in ctx.voci.items():
        it = items.get(vid)
        if it and vo.title and it.state == "open" and not it.excluded:
            seen = (rows[vid].get("seen") or "").strip()
            if seen != vo.title.strip():
                P.append(f"{vid} is titled {vo.title!r} in {vo.file} and was confirmed as "
                         f"{seen!r}: confirm its classification again")

    # Hours: every period, the past ones as they were frozen.
    periods = periods_of(state)
    per_item: dict[str, Fraction] = {}
    declared_hours: dict[date, dict] = {}       # every period that parses, read once
    for d, block in periods.items():
        if not isinstance(block, dict) or set(block) - PERIOD_KEYS:
            P.append(f"period {d}: it holds `hours` and `outside`, and nothing else")
            continue
        try:
            hm, om = hours_map(block), outside_map(block)
        except (ValueError, ZeroDivisionError) as e:
            P.append(f"period {d}: {e}")
            continue
        declared_hours[d] = hm
        for k, val in list(hm.items()) + list(om.items()):
            if val < 0:
                P.append(f"period {d}: {k} has {val} hours")
        for k, val in hm.items():
            target = ctx.alias.get(k, k)
            if target not in items:
                P.append(f"period {d}: hours on {k}, which is not an item of {ctx.product}")
                continue
            if items[target].excluded and val:
                P.append(f"period {d}: hours on {k}, which is excluded from the digest; declare "
                         "the time as an activity outside the register if it has to show")
            per_item[target] = per_item.get(target, Fraction(0)) + val
    for i, it in items.items():
        row = rows.get(i) or {}
        before = Fraction(0)
        if row.get("hours_before") is not None:
            try:
                before = num(row["hours_before"])
            except (ValueError, ZeroDivisionError):
                P.append(f"{i}: `hours_before` is a number of hours")
        for a in it.aliases:
            if isinstance(rows.get(a), dict) and rows[a].get("hours_before") is not None:
                try:
                    before += num(rows[a]["hours_before"])
                except (ValueError, ZeroDivisionError):
                    P.append(f"{a}: `hours_before` is a number of hours")
        it.hours = before + per_item.get(i, Fraction(0))
    ctx.items = items

    for s in chain(ctx.snaps, ctx.prev):
        fr = s.frozen
        prev_ref = fr.get("previous") or {}
        if prev_ref.get("dir"):
            target = next((x for x in ctx.snaps if x.name == prev_ref["dir"]), None)
            if target is None or target.digest() != prev_ref.get("sha256"):
                P.append(f"{prev_ref['dir']} no longer matches the hash {s.name} recorded for "
                         "it: a snapshot is never edited")
        period = fr.get("period")
        if period:
            d = as_date(period.get("from"))
            block = periods.get(d)
            try:
                frozen_h = {k: num(x) for k, x in (period.get("hours") or {}).items()}
                frozen_o = {k: num(x) for k, x in (period.get("outside") or {}).items()}
                same = (isinstance(block, dict) and hours_map(block) == frozen_h
                        and outside_map(block) == frozen_o)
            except (ValueError, ZeroDivisionError):
                same = False
            if not same:
                P.append(f"the hours of the period from {d} are not the ones {s.name} froze: "
                         "a past period is not edited")

    others = [p for p in (ctx.root / STORE).glob("state-*.yaml")
              if p.name != f"state-{ctx.product}.yaml"]
    for p in others:
        try:
            other = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        for d, block in periods_of(other).items():
            mine = periods.get(d)
            if not mine or not isinstance(block, dict) or not isinstance(mine, dict):
                continue
            both = set((block.get("hours") or {})) & set((mine.get("hours") or {}))
            for i in sorted(both):
                P.append(f"period {d}: hours on {i} in this state file and in {p.name}; the "
                         "hours of one item in one period are declared once")

    # What every item needs, for what will be printed about it.
    period_from = ctx.prev.date if ctx.prev and not ctx.baseline else None
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
        shown = it.state == "open" or (it.state == "closed" and in_scope)
        if it.state == "open" and it.scope not in (rel, OUT):
            P.append(f"{i} is open and scoped to {it.scope!r}, not to the current release "
                     f"{rel!r}: assign it to {rel!r} or to `{OUT}`")
        if shown:
            for k in ("title", "what", "theme"):
                if not row.get(k):
                    P.append(f"{i}: no `{k}`, and the digest prints it")
        if it.state == "open" and in_scope and not row.get("size"):
            P.append(f"{i}: open in the perimeter with no `size`")
        if it.state == "closed" and in_scope:
            declared = row.get("hours_before") is not None or any(
                k in hm for hm in declared_hours.values() for k in [i, *it.aliases])
            if not declared:
                P.append(f"{i}: closed in the perimeter with no hours declared, before or in "
                         "any period. No number is invented: declare them, 0 included")
            closed_now = not ctx.baseline and (prev_voci.get(i) or {}).get("state") != "closed"
            if closed_now and not row.get("size"):
                P.append(f"{i}: closed in this period with no `size`, which the activity prints")
        for k in ("title", "what"):
            if row.get(k) and DASHES.search(str(row[k])):
                P.append(f"{i}: a long dash in `{k}`; use a comma or two sentences")
        if row.get("title") and str(row["title"]).rstrip().endswith("."):
            P.append(f"{i}: the title ends with a full stop, which the digest adds")
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

    if not ctx.baseline:
        nxt = next_working(when)
        plan = plan_of(state)
        for d in (when, nxt):
            if d not in plan:
                P.append(f"no plan for {d}: the digest prints it, `[]` if nothing is planned")
                continue
            for i in plan[d] or []:
                it = items.get(str(i))
                if it is None:
                    P.append(f"plan {d}: {i} is not an item; a decision that closes an entry is "
                             "planned under the entry's identifier")
                elif it.state != "open":
                    P.append(f"plan {d}: {i} is {it.state}")
                elif it.excluded:
                    P.append(f"plan {d}: {i} is excluded from the digest")
                elif ctx.voci.get(str(i)) and ctx.voci[str(i)].status == "draft":
                    P.append(f"plan {d}: {i} is a `CHG` in draft, and a draft is not a mandate "
                             "to build. Approve it first, or plan the work that approves it")
        if period_from and period_from not in periods:
            P.append(f"no hours for the period from {period_from}: declare them, an empty "
                     "block if nothing was worked")

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
        if w.get("blocks") and not w.get("missing") and not w.get("resolved"):
            P.append(f"{label}: blocks something and has no `missing`, what the blocked item "
                     "lacks")
        for k in ("blocks", "slows"):
            for i in w.get(k) or []:
                if str(i) not in items:
                    P.append(f"{label}: `{k}` names {i}, which is not an item")
        for k in ("what", "owner", "without", "missing", "note"):
            if w.get(k) and DASHES.search(str(w[k])):
                P.append(f"{label}: a long dash in `{k}`")

    requests = state.get("requests") or {}
    for i, r in (requests.items() if isinstance(requests, dict) else []):
        it = items.get(str(i))
        if it is None or it.kind != "OD" or it.state != "open":
            P.append(f"request {i}: a decision asked of somebody is an open `OD` in a register, "
                     "and this is not one")
        if not isinstance(r, dict):
            continue
        for k in sorted(set(r) - REQUEST_KEYS):
            P.append(f"request {i}: unknown key {k!r}")
        for k in ("to", "fallback"):
            if not r.get(k):
                P.append(f"request {i}: no `{k}`")
        if as_date(r.get("by")) is None:
            P.append(f"request {i}: `by` is a date")

    for k, val in ((state.get("periods") or {}).items()):
        if as_date(k) is None:
            P.append(f"period {k!r}: the key is the first day of the period, YYYY-MM-DD")
    for k in (state.get("plan") or {}):
        if as_date(k) is None:
            P.append(f"plan {k!r}: the key is a date, YYYY-MM-DD")
    return P


def _item(i, kind, st, row, closer, children, aliases) -> Item:
    return Item(i, kind, st, None if row.get("scope") is None else str(row.get("scope")),
                row.get("theme"), row.get("size"), row.get("title"), row.get("what"),
                bool(row.get("excluded")), closer, list(children) + list(row.get("split_into") or []),
                list(aliases))


# ─────────────────────────────────────────────────────────────────────────────
# The digest

@dataclass
class Numbers:
    rel: str
    remaining: list            # items in the perimeter, open
    closed: list               # closed in the perimeter
    outside: list              # open outside the perimeter
    groups: dict
    rem: tuple
    rem_prev: tuple | None
    period: dict | None
    window: dict | None


def split_parent(it: Item) -> bool:
    return it.state in ("replaced",) or bool(it.children and it.state == "open")


def compute(ctx: Context) -> Numbers:
    state = ctx.state
    rel = str(state["release"]["name"])
    items = ctx.items

    def in_rem(it: Item) -> bool:
        return (it.state == "open" and it.scope == rel and not it.excluded
                and not split_parent(it))

    remaining = [it for it in items.values() if in_rem(it)]
    closed = [it for it in items.values()
              if it.state == "closed" and it.scope == rel and not it.excluded]
    outside = [it for it in items.values()
               if it.state == "open" and it.scope == OUT and not it.excluded
               and not split_parent(it)]
    rem = (sum((it.rng()[0] for it in remaining), Fraction(0)),
           sum((it.rng()[1] for it in remaining), Fraction(0)))

    groups = {"chiuse": [], "aggiunte": [], "uscite": [], "ristimate": [], "spezzate": [],
              "nuove": [], "born_closed": [], "closed_now": []}
    rem_prev = None
    period = None
    window = None
    if ctx.prev and not ctx.baseline:
        fr = ctx.prev.frozen
        prev_rel = str((fr.get("release") or {}).get("name"))
        pv = fr.get("voci") or {}

        def prev_rng(i):
            lo, hi = SIZES[pv[i]["size"]]
            return Fraction(lo), Fraction(hi)

        P_ids = {i for i, x in pv.items()
                 if x.get("state") == "open" and str(x.get("scope")) == prev_rel
                 and not x.get("excluded") and not x.get("split")}
        N_ids = {it.id for it in remaining}
        rem_prev = (sum((prev_rng(i)[0] for i in P_ids), Fraction(0)),
                    sum((prev_rng(i)[1] for i in P_ids), Fraction(0)))
        children_of = {}
        for i in P_ids:
            it = items.get(i)
            if it is not None and split_parent(it):
                for c in it.children:
                    children_of[c] = i
        d_lo = d_hi = Fraction(0)
        for i in sorted(P_ids, key=sort_id):
            it = items.get(i)
            if i in N_ids:
                lo, hi = it.rng()
                plo, phi = prev_rng(i)
                if (lo, hi) != (plo, phi):
                    groups["ristimate"].append((i, (lo - plo, hi - phi)))
            elif it is not None and it.state == "closed":
                groups["chiuse"].append((i, prev_rng(i)))
            elif it is not None and split_parent(it):
                kids = [c for c in it.children if c in N_ids and c not in P_ids]
                lo = sum((items[c].rng()[0] for c in kids), Fraction(0)) - prev_rng(i)[0]
                hi = sum((items[c].rng()[1] for c in kids), Fraction(0)) - prev_rng(i)[1]
                groups["spezzate"].append((i, (lo, hi), kids))
            else:
                groups["uscite"].append((i, prev_rng(i)))
        for i in sorted(N_ids - P_ids, key=sort_id):
            if children_of.get(i) in P_ids:
                continue
            groups["aggiunte"].append((i, items[i].rng()))
            if i not in pv:
                groups["nuove"].append(i)
        for it in items.values():
            if it.state == "closed" and (pv.get(it.id) or {}).get("state") != "closed":
                groups["closed_now"].append(it.id)
                if it.id not in P_ids:
                    groups["born_closed"].append(it.id)
        lo = (rem_prev[0] - sum(r[0] for _, r in groups["chiuse"])
              - sum(r[0] for _, r in groups["uscite"])
              + sum(r[0] for _, r in groups["aggiunte"])
              + sum(dl[0] for _, dl in groups["ristimate"])
              + sum(dl[0] for _, dl, _ in groups["spezzate"]))
        hi = (rem_prev[1] - sum(r[1] for _, r in groups["chiuse"])
              - sum(r[1] for _, r in groups["uscite"])
              + sum(r[1] for _, r in groups["aggiunte"])
              + sum(dl[1] for _, dl in groups["ristimate"])
              + sum(dl[1] for _, dl, _ in groups["spezzate"]))
        if (lo, hi) != rem:
            raise Refusal([f"the reconciliation does not add up: from {span(rem_prev)} the "
                           f"movements give {span((lo, hi))} and what remains is {span(rem)}. "
                           "This is a defect in the computation or in a snapshot, never a "
                           "number to correct by hand"])

        start, end = ctx.prev.date, ctx.when - timedelta(days=1)
        block = periods_of(state).get(start) or {}
        hm, om = hours_map(block), outside_map(block)

        def scope_of(k):
            it = items.get(ctx.alias.get(k, k))
            return it.scope if it else None

        per = sum((h for k, h in hm.items() if scope_of(k) == rel), Fraction(0))
        oth = sum(hm.values(), Fraction(0)) - per
        period = {"from": start, "to": end, "working_days": working_days(start, end),
                  "hours": hm, "outside": om, "perimeter_hours": per,
                  "outside_hours": sum(om.values(), Fraction(0)), "other_hours": oth}
        window = rate_window(ctx, period)
    return Numbers(rel, remaining, closed, outside, groups, rem, rem_prev, period, window)


def rate_window(ctx: Context, current: dict) -> dict:
    """The most recent periods with hours, whole, until they cover five working days."""
    periods = [current]
    for s in chain(ctx.snaps, ctx.prev):
        p = s.frozen.get("period")
        if p:
            periods.append({"working_days": int(p.get("working_days", 0)),
                            "perimeter_hours": num(p.get("perimeter_hours", 0)),
                            "outside_hours": num(p.get("outside_hours", 0)),
                            "other_hours": num(p.get("other_hours", 0))})
    days, per, out = 0, Fraction(0), Fraction(0)
    for p in periods:
        if p["perimeter_hours"] + p["outside_hours"] + p["other_hours"] == 0:
            continue                          # a period nobody worked is not data
        days += p["working_days"]
        per += p["perimeter_hours"]
        out += p["outside_hours"]
        if days >= 5:
            break
    std = num(ctx.state["standard_hours"])
    rate = per / days if days else None
    normal = std - out / days if days else None
    return {"days": days, "rate": rate, "normal": normal}


def render(ctx: Context, n: Numbers) -> str:
    state, items, when = ctx.state, ctx.items, ctx.when
    rows = state.get("items") or {}
    rel = n.rel
    add, prov = ctx.additions.append, ctx.provisional.append
    waits = [w for w in (state.get("waits") or []) if not w.get("resolved")]
    waits.sort(key=lambda w: (as_date(w["needed_by"]), str(w["what"])))
    blocked = {str(i): w for w in waits for i in (w.get("blocks") or [])}
    blockers = {}
    for w in waits:
        for i in (w.get("blocks") or []) + (w.get("slows") or []):
            blockers.setdefault(str(i), []).append(w)
    plan = plan_of(state)
    nxt = next_working(when)
    g = n.groups

    def title(i):
        return str(rows.get(i, {}).get("title") or items[i].title or i)

    def what(i):
        return f"  Cos'è: {rows[i]['what']}"

    def tema(i):
        return THEMES[items[i].theme]

    def by_theme(lst):
        return [(t, [it for it in lst if it.theme == t]) for t in THEMES]

    if n.period["from"] == n.period["to"]:
        when_added = f"il {dm(n.period['from'])}"
        sec2 = f"2. ATTIVITÀ {dmy(n.period['from'])}, a consuntivo"
    else:
        when_added = f"dal {dm(n.period['from'])} al {dm(n.period['to'])}"
        sec2 = (f"2. ATTIVITÀ DAL {dmy(n.period['from'])} AL {dmy(n.period['to'])}, "
                "a consuntivo")

    L = [f"{ctx.name.upper()}, digest del {dmy(when)}", "", "1. SINTESI",
         f"Consegna concordata: {dm(as_date(state['release']['delivery']))}"]
    parts = []
    for count, sing, plur in ((len(n.closed), "chiusa", "chiuse"),
                              (len(n.remaining), "aperta", "aperte")):
        if count:
            parts.append(agree(count, sing, plur))
        else:
            parts.append(f"nessuna {sing}")
            prov(f"«nessuna {sing}» nella sintesi: l'esempio non mostra il caso zero")
    k = len(g["aggiunte"])
    if k:
        parts.append(f"{agree(k, 'aggiunta', 'aggiunte')} {when_added}")
    else:
        parts.append(f"nessuna aggiunta {when_added}")
        prov(f"«nessuna aggiunta {when_added}» nella sintesi")
    if n.period["from"] != n.period["to"]:
        prov(f"«{when_added}» nella sintesi: l'esempio mostra un periodo di un giorno solo")
    L.append("Voci nel perimetro: " + ", ".join(parts))

    total_closed = sum((it.hours for it in n.closed), Fraction(0))
    L.append(f"Monte ore chiuso: {hours(total_closed)} h")
    for t, lst in by_theme(n.closed):
        if lst:
            L.append(f"  {THEMES[t]}: {voci(len(lst))}, "
                     f"{hours(sum((it.hours for it in lst), Fraction(0)))} h")
        else:
            L.append(f"  {THEMES[t]}: nessuna")
            prov(f"«{THEMES[t]}: nessuna» sotto il monte ore chiuso")
    L.append(f"Monte ore rimasto: {span(n.rem)}")
    for t, lst in by_theme(n.remaining):
        if not lst:
            L.append(f"  {THEMES[t]}: nessuna")
            prov(f"«{THEMES[t]}: nessuna» sotto il monte ore rimasto")
            continue
        r = (sum((it.rng()[0] for it in lst), Fraction(0)),
             sum((it.rng()[1] for it in lst), Fraction(0)))
        line = f"  {THEMES[t]}: {voci(len(lst))}, {span(r)}"
        notes = []
        xl = [it for it in lst if it.size == "XL"]
        if xl:
            notes.append(f"{voci(len(xl))} XL, "
                         f"{span((Fraction(13 * len(xl)), Fraction(40 * len(xl))))}, da spezzare")
        b = [it for it in lst if it.id in blocked]
        if b:
            notes.append(agree(len(b), "bloccata", "bloccate"))
        if notes:
            line += " (" + "; ".join(notes) + ")"
            if len(notes) > 1:
                prov(f"«{'; '.join(notes)}» sulla riga di {THEMES[t]}: l'esempio non mostra "
                     "una voce XL e una bloccata nello stesso tema")
        L.append(line)

    L.append(f"Dal {dm(ctx.prev.date)} al {dm(when)}")
    L.append(f"  Rimasto al {dm(ctx.prev.date)}: {span(n.rem_prev)}")

    def movement(lst, sign):
        if not lst:
            return "nessuna"
        lo = sum(r[0] for _, r in lst)
        hi = sum(r[1] for _, r in lst)
        return f"{voci(len(lst))}, {sign} {hours(lo)} a {hours(hi)} h"

    L.append(f"  Chiuse: {movement(g['chiuse'], 'meno')}")
    L.append(f"  Aggiunte: {movement(g['aggiunte'], 'più')}")
    L.append(f"  Uscite senza chiusura: {movement(g['uscite'], 'meno')}")
    moved = [(i, dl) for i, dl in g["ristimate"]] + [(i, dl) for i, dl, _ in g["spezzate"]]
    if not moved:
        L.append("  Ristimate o spezzate: nessuna")
    else:
        lo = sum(dl[0] for _, dl in moved)
        hi = sum(dl[1] for _, dl in moved)
        if lo >= 0 and hi >= 0:
            L.append(f"  Ristimate o spezzate: {voci(len(moved))}, più {hours(lo)} a {hours(hi)} h")
        elif lo <= 0 and hi <= 0:
            L.append(f"  Ristimate o spezzate: {voci(len(moved))}, "
                     f"meno {hours(-lo)} a {hours(-hi)} h")
        else:
            def signed(x):
                return f"più {hours(x)} h" if x >= 0 else f"meno {hours(-x)} h"
            L.append(f"  Ristimate o spezzate: {voci(len(moved))}, minimo {signed(lo)}, "
                     f"massimo {signed(hi)}")
            prov("«minimo … massimo …» su Ristimate o spezzate: i due estremi vanno in versi "
                 "opposti, e l'esempio non lo mostra")
    L.append(f"  Rimasto al {dm(when)}: {span(n.rem)}")

    L.append("Stima di consegna")
    w = n.window
    for label, per_day, empty in (("a ritmo attuale", w["rate"], "nessuna ora sul perimetro"),
                                  ("a orario normale", w["normal"], "nessuna ora disponibile")):
        if not per_day or per_day <= 0:
            L.append(f"  {label}: {empty}, non stimabile")
            prov(f"«{label}: {empty}, non stimabile»")
            continue
        d1 = nth_working(when, math.ceil(n.rem[0] / per_day))
        d2 = nth_working(when, math.ceil(n.rem[1] / per_day))
        L.append(f"  {label} ({one_decimal(per_day)} h/giorno): tra il {dm(d1)} e il {dm(d2)}")
    L.append("Condizioni della stima")
    if not waits:
        L.append("Nessuna.")
        prov("«Nessuna.» sotto le condizioni della stima")
    for wt in waits:
        L.append(f"- {wt['what']} entro il {dm(as_date(wt['needed_by']))}.")
        L.append(f"  Senza: {wt['without']}")
    if n.outside:
        L.append(f"Fuori perimetro: {agree(len(n.outside), 'voce aperta, non stimata', 'voci aperte, non stimate')}.")
    else:
        L.append("Fuori perimetro: nessuna voce aperta.")
        prov("«Fuori perimetro: nessuna voce aperta.»")

    # 2 · what happened in the period
    L += ["", sec2]
    per = n.period
    closed_now = [items[i] for i in g["closed_now"]
                  if items[i].scope == rel and not items[i].excluded]
    in_scope_closed = {it.id for it in closed_now}
    total = per["perimeter_hours"] + per["other_hours"] + per["outside_hours"]
    new_in = [i for i in g["nuove"]]
    body = []
    period_hours = {}
    for k, h in per["hours"].items():
        target = ctx.alias.get(k, k)
        period_hours[target] = period_hours.get(target, Fraction(0)) + h
    if total or closed_now or new_in or g["uscite"]:
        body.append(f"{hours(total)} h: {hours(per['perimeter_hours'])} sul perimetro, "
                    f"{hours(per['outside_hours'])} fuori registro")
        if per["other_hours"]:
            on = [i for i in period_hours if items[i].scope != rel and period_hours[i]]
            add({"where": "2 · la riga delle ore",
                 "text": f"{hours(per['other_hours'])} h su voci fuori perimetro "
                         f"({', '.join(sorted(on, key=sort_id))}): il totale le conta, le due "
                         "parti no"})
        for t, lst in by_theme(sorted(closed_now, key=lambda it: sort_id(it.id))):
            if not lst:
                continue
            body.append(THEMES[t])
            for it in lst:
                closer = f" con {it.closer}" if it.closer else ""
                body.append(f"- {it.id}, {title(it.id)}. Chiusa{closer}.")
                body.append(what(it.id))
                body.append(f"  Taglia {it.size}: "
                            f"{hours(period_hours.get(it.id, Fraction(0)))} h.")
        if per["outside"]:
            body.append("Fuori registro")
            for k, h in per["outside"].items():
                body.append(f"- {k}: {hours(h)} h.")
        if new_in:
            body.append("Voci nuove emerse")
            for i in sorted(new_in, key=sort_id):
                body.append(f"- {i}, {title(i)}. {tema(i)}, taglia {items[i].size}.")
                body.append(what(i))
        if g["uscite"]:
            body.append("Voci uscite")
            hidden = 0
            for i, _ in sorted(g["uscite"], key=lambda x: sort_id(x[0])):
                it = items.get(i)
                if it is None or it.excluded:
                    hidden += 1
                    continue
                reason = ("Tolta dal perimetro." if it.state == "open" else
                          "Annullata." if it.kind == "CHG" else
                          "Tolta dal registro." if (rows.get(i) or {}).get("gone") else
                          "Sostituita.")
                body.append(f"- {i}, {title(i)}. {reason}")
                if (rows.get(i) or {}).get("what"):
                    body.append(what(i))
                prov(f"«{reason}» per {i} sotto «Voci uscite»: la sezione è approvata, "
                     "il motivo è una forma proposta")
            if hidden:
                body.append(f"- {agree(hidden, 'voce esclusa', 'voci escluse')} dal digest.")
                prov("«… esclusa dal digest.» sotto «Voci uscite»")
    else:
        body.append("Nessuna.")
    L += body

    # What happened and the canonical format has no line for: listed, not printed.
    for i, h in sorted(period_hours.items(), key=lambda x: sort_id(x[0])):
        it = items[i]
        if h and it.state == "open" and it.scope == rel and not it.excluded:
            add({"where": f"2 · sotto {THEMES.get(it.theme, '?')}",
                 "text": f"- {i}, {title(i)}. In corso.\n{what(i)}\n"
                         f"  Taglia {it.size}: {hours(h)} h."})
    for i in sorted(g["closed_now"], key=sort_id):
        it = items[i]
        if i not in in_scope_closed and not it.excluded:
            add({"where": "2 · voci chiuse fuori perimetro",
                 "text": f"- {i}, {title(i)}. Chiusa."})
    for it in sorted(n.outside, key=lambda x: sort_id(x.id)):
        if ctx.prev and it.id not in (ctx.prev.frozen.get("voci") or {}):
            add({"where": "2 · Voci nuove emerse",
                 "text": f"- {it.id}, {title(it.id)}. {tema(it.id)}, fuori perimetro.\n"
                         f"{what(it.id)}"})
    for i, _ in g["aggiunte"]:
        if i not in g["nuove"]:
            before = (ctx.prev.frozen.get("voci") or {}).get(i) or {}
            why = "Riaperta." if before.get("state") == "closed" else "Entrata nel perimetro."
            add({"where": "2 · Voci entrate nel perimetro", "text": f"- {i}, {title(i)}. {why}"})
    for i, dl in g["ristimate"]:
        was = (ctx.prev.frozen.get("voci") or {})[i]["size"]
        add({"where": "2 · Voci ristimate o spezzate",
             "text": f"- {i}, {title(i)}. Da {was} a {items[i].size}."})
    for i, dl, kids in g["spezzate"]:
        add({"where": "2 · Voci ristimate o spezzate",
             "text": f"- {i}, {title(i)}. Diventata {' e '.join(kids) or 'nessuna voce'}."})
    prev_v = (ctx.prev.frozen.get("voci") or {})
    for i, x in sorted(prev_v.items(), key=lambda x: sort_id(x[0])):
        it = items.get(i)
        if x.get("state") == "closed" and it is not None and it.state != "closed":
            add({"where": "Allegato C", "text": f"- {i}, {title(i)}. Annullata, esce dal "
                                                f"fatto ({hours(it.hours)} h)."})

    # 3 and 4 · the plan
    for number, d in ((3, when), (4, nxt)):
        L += ["", f"{number}. ATTIVITÀ {dmy(d)}, in programma"]
        shown = 0
        for i in plan.get(d) or []:
            i = str(i)
            it = items[i]
            if it.scope != rel:
                add({"where": f"{number} · in programma",
                     "text": f"- {i}, {title(i)}. {tema(i)}, fuori perimetro."})
                continue
            cont = ", prosecuzione" if number == 4 and i in [str(x) for x in plan.get(when) or []] else ""
            L.append(f"- {i}, {title(i)}{cont}. {tema(i)}, taglia {it.size}.")
            L.append(what(i))
            for wt in blockers.get(i, []):
                L.append(f"  Dipende da: {lower_first(str(wt['what']))}, {wt['owner']}.")
            shown += 1
        if not shown:
            L.append("Nessuna.")

    # 5 · waits
    L += ["", "5. IN ATTESA DA ALTRI"]
    if not waits:
        L.append("Nessuna.")
    for wt in waits:
        asked = as_date(wt["asked"])
        days = (when - asked).days
        L.append(f"- {wt['what']}. Owner: {wt['owner']}.")
        L.append(f"  Richiesto il {dm(asked)}, {agree(days, 'giorno', 'giorni')} di attesa. "
                 f"Serve entro il {dm(as_date(wt['needed_by']))}.")
        stops = sorted((str(i) for i in wt.get("blocks") or []
                        if str(i) in {it.id for it in n.remaining}), key=sort_id)
        if stops:
            L.append(f"  Voci bloccate: {', '.join(stops)}.")
        else:
            note = f", {wt['note']}" if wt.get("note") else ""
            L.append(f"  Voci bloccate: nessuna nel perimetro{note}.")
        slows = sorted((str(i) for i in wt.get("slows") or []
                        if str(i) in {it.id for it in n.remaining}), key=sort_id)
        if slows:
            L.append(f"  Voci rallentate: {', '.join(slows)}.")

    # 6 · decisions asked of others: open entries, with who and by when
    L += ["", "6. DECISIONI RICHIESTE"]
    requests = state.get("requests") or {}
    if not requests:
        L.append("Nessuna.")
    for i, r in sorted(requests.items(), key=lambda x: (as_date(x[1]["by"]), sort_id(str(x[0])))):
        i = str(i)
        L.append(f"- {i}, {title(i)}.")
        L.append(what(i))
        L.append(f"  A chi: {r['to']}. Entro: {dm(as_date(r['by']))}.")
        L.append(f"  Se non arriva: {r['fallback']}")

    # Annex A · to do in the perimeter
    planned = [str(x) for x in (plan.get(when) or [])] + [str(x) for x in (plan.get(nxt) or [])]

    def order_a(it):
        if it.id in planned:
            return (0, planned.index(it.id), 0, sort_id(it.id))
        return (1, 0, list(SIZES).index(it.size), sort_id(it.id))

    L += ["", f"ALLEGATO A. DA FARE NEL PERIMETRO "
              f"({voci(len(n.remaining))}, {span(n.rem)})" if n.remaining else
          "ALLEGATO A. DA FARE NEL PERIMETRO (nessuna voce)"]
    if not n.remaining:
        L.append("Nessuna.")
        prov("«(nessuna voce)» e «Nessuna.» nell'allegato A")
    for t, lst in by_theme(n.remaining):
        if not lst:
            continue
        r = (sum((it.rng()[0] for it in lst), Fraction(0)),
             sum((it.rng()[1] for it in lst), Fraction(0)))
        L.append(f"{THEMES[t]} ({voci(len(lst))}, {span(r)})")
        for it in sorted(lst, key=order_a):
            stop = [wt for wt in waits if it.id in [str(x) for x in wt.get("blocks") or []]]
            tail = (". Bloccata: " + "; ".join(str(wt["missing"]) for wt in stop) + "."
                    if stop else "")
            if len(stop) > 1:
                prov(f"più motivi di blocco su {it.id}, separati da «; »")
            L.append(f"- {it.id}, {title(it.id)}. {it.size}{tail}")
            L.append(what(it.id))

    # Annex B · to do outside the perimeter
    L += ["", f"ALLEGATO B. DA FARE FUORI PERIMETRO "
              f"({agree(len(n.outside), 'voce, non stimata', 'voci, non stimate')})"
          if n.outside else "ALLEGATO B. DA FARE FUORI PERIMETRO (nessuna voce)"]
    if not n.outside:
        L.append("Nessuna.")
        prov("«(nessuna voce)» e «Nessuna.» nell'allegato B")
    for it in sorted(n.outside, key=lambda x: (list(THEMES).index(x.theme), sort_id(x.id))):
        L.append(f"- {it.id}, {title(it.id)}. {tema(it.id)}.")
        L.append(what(it.id))

    # Annex C · done
    done_total = sum((it.hours for it in n.closed), Fraction(0))
    L += ["", f"ALLEGATO C. FATTO ({voci(len(n.closed))}, {hours(done_total)} h)"
          if n.closed else "ALLEGATO C. FATTO (nessuna voce)"]
    if not n.closed:
        L.append("Nessuna.")
        prov("«(nessuna voce)» e «Nessuna.» nell'allegato C")

    def kind_of(it):
        return KIND_ORDER.get(it.closer.split("-")[0] if it.kind == "OD" and it.closer
                              else it.kind, 0)

    for t in THEMES:
        lst = [it for it in n.closed if it.theme == t]
        for k in sorted({kind_of(it) for it in lst}):
            sub = sorted((it for it in lst if kind_of(it) == k),
                         key=lambda it: sort_id(it.closer if it.kind == "OD" and it.closer
                                                else it.id))
            if k >= 2:
                prov(f"«{THEMES[t]}, {DONE_LABEL[k]}» nell'allegato C")
            L.append(f"{THEMES[t]}, {DONE_LABEL[k]} ({voci(len(sub))}, "
                     f"{hours(sum((it.hours for it in sub), Fraction(0)))} h)")
            for it in sub:
                if it.kind == "OD" and it.closer:
                    L.append(f"- {it.closer}, {title(it.id)}. Chiude {it.id}. {hours(it.hours)} h")
                else:
                    L.append(f"- {it.id}, {title(it.id)}. {hours(it.hours)} h")
                L.append(what(it.id))
    out = text_of(L)
    if DASHES.search(out):
        raise Refusal(["the digest would carry a long dash"])
    return out


def render_baseline(ctx: Context) -> tuple[str, Numbers]:
    state, items = ctx.state, ctx.items
    rel = str(state["release"]["name"])
    remaining = [it for it in items.values() if it.state == "open" and it.scope == rel
                 and not it.excluded and not split_parent(it)]
    closed = [it for it in items.values() if it.state == "closed" and it.scope == rel
              and not it.excluded]
    outside = [it for it in items.values() if it.state == "open" and it.scope == OUT
               and not it.excluded and not split_parent(it)]
    rem = (sum((it.rng()[0] for it in remaining), Fraction(0)),
           sum((it.rng()[1] for it in remaining), Fraction(0)))
    lines = [f"{ctx.name.upper()}, linea di base del {dmy(ctx.when)}",
             "Non si invia: il primo digest è quello del prossimo giorno lavorativo.",
             f"Voci nel perimetro: {agree(len(closed), 'chiusa', 'chiuse')}, "
             f"{agree(len(remaining), 'aperta', 'aperte')}",
             f"Monte ore chiuso: {hours(sum((it.hours for it in closed), Fraction(0)))} h",
             f"Monte ore rimasto: {span(rem)}",
             f"Fuori perimetro: {agree(len(outside), 'voce aperta', 'voci aperte')}"]
    n = Numbers(rel, remaining, closed, outside, {}, rem, None, None, None)
    return text_of(lines), n


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


def write_snapshot(ctx: Context, text: str, n: Numbers) -> tuple[Snap, str]:
    store = ctx.root / STORE
    number = max((s.number for s in ctx.snaps), default=0) + 1
    name = f"DIG-{number:03d}-{ctx.product}-{ctx.when.isoformat()}"
    path = store / name
    path.mkdir(parents=True)
    frozen = {
        "digest": f"DIG-{number:03d}",
        "product": ctx.product,
        "date": ctx.when.isoformat(),
        "at": (ctx.now or datetime.now().astimezone()).isoformat(timespec="seconds"),
        "baseline": ctx.baseline,
        "previous": ({"dir": ctx.prev.name, "sha256": ctx.prev.digest()} if ctx.prev else None),
        "release": {"name": n.rel,
                    "delivery": as_date(ctx.state["release"]["delivery"]).isoformat()},
        "remaining": [plain(n.rem[0]), plain(n.rem[1])],
        "voci": {i: {"kind": it.kind, "state": it.state, "scope": it.scope,
                     "theme": it.theme, "size": it.size, "excluded": it.excluded,
                     "split": split_parent(it), "closer": it.closer,
                     "children": it.children, "hours": plain(it.hours)}
                 for i, it in sorted(ctx.items.items(), key=lambda x: sort_id(x[0]))},
    }
    if n.period:
        p = n.period
        frozen["period"] = {
            "from": p["from"].isoformat(), "to": p["to"].isoformat(),
            "working_days": p["working_days"],
            "perimeter_hours": plain(p["perimeter_hours"]),
            "outside_hours": plain(p["outside_hours"]),
            "other_hours": plain(p["other_hours"]),
            "hours": {k: plain(x) for k, x in p["hours"].items()},
            "outside": {k: plain(x) for k, x in p["outside"].items()},
        }
        frozen["rate"] = {k: (plain(x) if isinstance(x, Fraction) else x)
                          for k, x in n.window.items()}
    frozen["additions"] = ctx.additions
    frozen["provisional"] = ctx.provisional
    frozen["sources_disagree"] = ctx.notes
    (path / "frozen.yaml").write_text(
        "# Written by skills/digest/scripts/digest.py. Never edited: the next digest checks "
        "its hash.\n" + yaml.safe_dump(frozen, allow_unicode=True, sort_keys=False),
        encoding="utf-8")
    (path / f"{name}.txt").write_text(text, encoding="utf-8")
    return Snap(number, ctx.product, ctx.when, path), name


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


HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
FILE = re.compile(r"^diff --git a/(.+?) b/(.+)$")


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
    """Which items the commits since the last digest name: a proposal, never a measurement.

    In the documents, the identifiers on the lines a commit changed; in the code, the ones its
    message cites. P-07 binds a change to the text of a pull request, not to a commit, so
    nothing here is certain, and the person writes the hours.
    """
    rx = ids_regex()
    registry = yaml.safe_load((FRAMEWORK / "schemas" / "artifact-types.yaml")
                              .read_text(encoding="utf-8"))
    skip = set(registry["scan"]["skip_files"])
    mine = set(ctx.voci) | set(ctx.alias)
    found: dict[str, list] = {}
    loose, repos = [], repositories(ctx)
    for repo in repos:
        if not repo.get("read"):
            continue
        docs = repo["pathspec"] is not None
        cmd = ["log", "--all", f"--since={since}", "--format=%x1e%h%x1f%s%x1f%b%x1f"]
        if docs:
            cmd += ["-p", "-U0", "--no-ext-diff", "--no-color", "--", repo["pathspec"]]
        where = Path(repo["path"])
        r = git(*cmd, cwd=where)
        for record in r.stdout.split("\x1e")[1:]:
            parts = record.split("\x1f")
            sha, subject, body = parts[0], parts[1], parts[2]
            text = subject + "\n" + body
            if docs and len(parts) > 3:
                text += "\n" + changed_text(where, sha, parts[3], skip)
            hits = {ctx.alias.get(i, i) for i in rx.findall(text) if i in mine}
            for i in hits:
                found.setdefault(i, []).append(f"{repo['name']} {sha} {subject}")
            if not hits and not docs:
                loose.append(f"{repo['name']} {sha} {subject}")
    return found, loose, repos


def inventory(ctx: Context) -> dict:
    rows = (ctx.state or {}).get("items") or {}
    prev_v = (ctx.prev.frozen.get("voci") or {}) if ctx.prev else {}
    out = {"product": ctx.product, "date": ctx.when.isoformat(),
           "previous": ({"digest": ctx.prev.name, "date": ctx.prev.date.isoformat()}
                        if ctx.prev else None)}
    if ctx.prev:
        end = ctx.when - timedelta(days=1)
        out["period"] = {"from": ctx.prev.date.isoformat(), "to": end.isoformat(),
                         "working_days": working_days(ctx.prev.date, end)}
    out["unclassified"] = [{"id": i, "kind": vo.kind, "status": vo.status, "title": vo.title,
                            "file": vo.file}
                           for i, vo in sorted(ctx.voci.items(), key=lambda x: sort_id(x[0]))
                           if i not in rows]
    out["changed"] = [{"id": i, "confirmed_as": rows[i].get("seen"), "now": vo.title}
                      for i, vo in ctx.voci.items()
                      if i in rows and vo.title and vo.state == "open"
                      and (rows[i].get("seen") or "").strip() != vo.title.strip()]
    out["closed_since"] = sorted((i for i, vo in ctx.voci.items() if vo.state == "closed"
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
    if ctx.prev:
        since = ctx.prev.frozen.get("at") or ctx.prev.date.isoformat()
        found, loose, repos = worked(ctx, str(since))
        out["worked"] = {i: ev for i, ev in sorted(found.items(), key=lambda x: sort_id(x[0]))}
        out["commits_without_an_item"] = loose
        out["repositories"] = repos
    waits = [w for w in ((ctx.state or {}).get("waits") or []) if isinstance(w, dict)
             and not w.get("resolved")]
    out["waits_open"] = [{"what": w.get("what"), "owner": w.get("owner"),
                          "days": (ctx.when - as_date(w["asked"])).days
                          if as_date(w.get("asked")) else None,
                          "needed_by": str(w.get("needed_by"))} for w in waits]
    out["store"] = store_status(ctx.root)
    return out


# ─────────────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", type=Path, default=Path("."), help="the project's documents")
    ap.add_argument("--product", help="the product; optional when there is one")
    ap.add_argument("--date", help="the digest's date, YYYY-MM-DD; default today")
    ap.add_argument("--now", help="the instant recorded in the snapshot, ISO 8601; default "
                                  "now. For fixtures, whose history is dated")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="list every reason not to print")
    mode.add_argument("--inventory", action="store_true",
                      help="what the skill asks about: new, changed, closed, worked")
    mode.add_argument("--baseline", action="store_true",
                      help="the first run: freeze the state, print nothing to send")
    mode.add_argument("--init-store", metavar="URL",
                      help="clone the private repository into _meta/digest")
    a = ap.parse_args(argv)
    if a.init_store:
        return init_store(a.root, a.init_store)
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
        if a.baseline:
            text, n = render_baseline(ctx)
        else:
            n = compute(ctx)
            text = render(ctx, n)
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
    snap, name = write_snapshot(ctx, text, n)
    pushed, how = commit_and_push(ctx.root, f"{name}")
    print(text, end="")
    print("\n----- fuori dal digest -----")
    if ctx.additions:
        print("Righe che il formato non ha, da aggiungere a mano se servono:")
        for x in ctx.additions:
            print(f"[{x['where']}]\n{text_of(x['text'].splitlines())}", end="")
    if ctx.provisional:
        print("Forme che l'esempio non mostra, usate in questo digest:")
        for x in ctx.provisional:
            print(f"- {x}")
    if ctx.notes:
        print("Fonti in disaccordo:")
        for x in ctx.notes:
            print(f"- {x}")
    print(f"{snap.path.relative_to(ctx.root)} · {how}")
    return 0 if pushed else 3


if __name__ == "__main__":
    sys.exit(main())
