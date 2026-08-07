#!/usr/bin/env python3
"""
Validator for the Data & AI documentation framework.

One implementation, two entry points: the `framework-audit` skill runs it interactively
and interprets the results, CI runs the same file on every push and blocks the merge on
errors. If the logic lived in the skill's instructions instead, it would drift from the
version that runs in CI, which is the one that counts.

    python validate.py --root path/to/project
    python validate.py --root path/ --json
    python validate.py --root path/ --emit-index
    python validate.py --root path/ --emit-index --check

Exit code 0 when nothing is at `error` level. Warnings never block.

WHAT IT READS, AND WHY NONE OF IT IS HARD CODED HERE:

  schemas/artifact-types.yaml     what each type may be, which sections it must carry,
                                  which files to look at, which id prefixes exist
  schemas/framework/<t>/v1.json   the front matter check itself, generated from the above
  skills/framework-audit/checks.yaml   which checks run, and at what severity

The schemas do the front matter checking rather than Python reimplementing it, so there is
one enforcement path and not two. Everything a schema cannot express, which is everything
about the body and everything that spans more than one file, is below.

A PROJECT CONFIGURES TWO THINGS in `framework.yaml` at its own root. Under `checks:`, the
severities, which is what makes "add a check when the failure it prevents has already
happened once" affordable: one line, not a commit of code. Under `scan:`, which files are
artifacts at all, because a project that also holds code holds a great deal of neither, and
the directories it keeps that code in are not knowable from here. Both extend the framework
defaults. A key that file does not recognise stops the validator rather than being ignored.

Requires pyyaml and jsonschema.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Needs pyyaml:  pip install pyyaml")

try:
    from jsonschema import Draft202012Validator
except ImportError:
    sys.exit("Needs jsonschema:  pip install jsonschema\n"
             "It is not optional: without it the front matter check does not run, and "
             "that is the one check this validator exists to perform.")


FRAMEWORK = Path(__file__).resolve().parents[3]
SCHEMA_DIR = FRAMEWORK / "schemas" / "framework"
REGISTRY = FRAMEWORK / "schemas" / "artifact-types.yaml"
CHECKS = FRAMEWORK / "skills" / "framework-audit" / "checks.yaml"

SECTION_MARK = re.compile(r"<!--\s*section:\s*([a-z0-9-]+)\s*-->")


# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Finding:
    code: str
    path: str
    message: str
    level: str = "warn"

    def line(self) -> str:
        icon = {"error": "x", "warn": "!", "info": "-"}[self.level]
        return f"{icon} [{self.code}] {self.path}\n    {self.message}"


@dataclass
class Artifact:
    path: Path
    rel: str
    meta: dict
    body: str
    ids: set[str] = field(default_factory=set)

    @property
    def id(self) -> str | None:
        return self.meta.get("id")

    @property
    def type(self) -> str | None:
        """The declared `artifact_type`, or None when it is not a plain name.

        Normalised here rather than at each use. `artifact_type: [a, b]` is one stray
        bracket away in a hand written front matter, and almost every use of it downstream
        is a dict or set lookup, which raises on an unhashable value: the validator died on
        the malformed document instead of reporting it, and said nothing about the two
        hundred it had not reached yet. The raw value stays in `meta` for whoever has to
        print it back.
        """
        t = self.meta.get("artifact_type")
        return t if isinstance(t, str) else None


class Report:
    """Collects findings and drops the ones the project has switched off.

    Severity is resolved here rather than at each call site: a check does not get to
    decide how much it matters, because how much it matters is a property of the project
    and not of the check.
    """

    def __init__(self, config: dict):
        self.config = config
        self.findings: list[Finding] = []

    def enabled(self, code: str) -> bool:
        return self.level(code) != "off"

    def level(self, code: str) -> str:
        return (self.config.get(code) or {}).get("level", "warn")

    def add(self, code: str, path: str, message: str) -> None:
        if self.enabled(code):
            self.findings.append(Finding(code, path, message, self.level(code)))


# ─────────────────────────────────────────────────────────────────────────────
# Reading

def as_list(v) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def jsonify(o):
    """YAML gives back date and datetime objects; JSON Schema validates JSON.

    Without this every artifact fails on `created`, which is a correct field, and the
    validator spends its credibility on its own bug.
    """
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    if isinstance(o, dict):
        return {k: jsonify(v) for k, v in o.items()}
    if isinstance(o, list):
        return [jsonify(v) for v in o]
    return o


def is_bare_yaml(text: str) -> bool:
    """A `.yaml` artifact: the whole file is metadata.

    Leading comments and blank lines do not count. A manifest that opens by explaining
    what it is stays a manifest, and without this it would be reported as having no front
    matter at all.
    """
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        return line.startswith("schema:")
    return False


def parse_front_matter(text: str) -> tuple[dict | None, str, str | None]:
    """Returns (meta, body, error)."""
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end == -1:
            return None, text, "front matter opened and never closed"
        raw, body = text[4:end], text[end + 4:]
    elif is_bare_yaml(text):
        raw, body = text, ""
    else:
        return None, text, "no front matter"
    try:
        meta = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        return None, body, f"invalid YAML: {str(e).splitlines()[0]}"
    if not isinstance(meta, dict):
        return None, body, "front matter is not a mapping"
    return meta, body, None


LEVELS = {"error", "warn", "info", "off"}


def normalize_level(v, code: str) -> str:
    """YAML 1.1 reads a bare `off` as the boolean False.

    `checks.yaml` quotes it, but a project's `framework.yaml` is not ours to quote, and a
    check silently reading as enabled because of a YAML quirk is the kind of failure that
    is only discovered by the incident it did not prevent. An unrecognised level stops the
    validator instead of being ignored.
    """
    if v is False:
        return "off"
    v = str(v)
    if v not in LEVELS:
        sys.exit(f"{code}: unknown level {v!r}. One of: {', '.join(sorted(LEVELS))}")
    return v


PROJECT_KEYS = {"checks", "stale_days", "scan"}
SCAN_KEYS = {"skip_dirs", "skip_files", "skip_hidden"}


def load_project(root: Path) -> dict:
    """The project's own `framework.yaml`, with every key it holds recognised.

    An unrecognised key stops the validator instead of being dropped. The check codes
    already behaved this way and the reason carries over one level up unchanged: a `scan:`
    block that reads as applied and is not leaves you with a validator you believe you
    configured, and the first sign of it is CI failing on the very files you excluded.
    """
    path = root / "framework.yaml"
    if not path.exists():
        return {}
    project = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(project, dict):
        sys.exit(f"{path}: the top level has to be a mapping")

    def reject(unknown: list, where: str, allowed: set) -> None:
        if unknown:
            sys.exit(f"{path}: unknown key(s) {', '.join(map(repr, unknown))}{where}. "
                     f"This file holds: {', '.join(sorted(allowed))}.")

    reject(sorted(set(project) - PROJECT_KEYS), "", PROJECT_KEYS)
    scan = project.get("scan") or {}
    if not isinstance(scan, dict):
        sys.exit(f"{path}: `scan` has to be a mapping")
    reject(sorted(set(scan) - SCAN_KEYS), " under `scan`", SCAN_KEYS)
    return project


def load_scan(registry: dict, project: dict) -> dict:
    """The framework's own exclusions, extended by the project's.

    Without this a project cannot be checked at all once it also holds code. `discover`
    reads every `.md` and `.yaml` under the root, and a dbt model, a Kubernetes manifest
    and a CONTRIBUTING.md are each an `FM001`, which is one of the two checks that block.
    The only way out was `FM001: warn`, which switches off the check the validator exists
    to run.

    It extends and does not replace, which is the decision worth stating. The defaults are
    not preferences: `corpus` is source material the framework defines as not-an-artifact,
    `schemas` and `skills` are the framework's own definition. A project that means "also
    skip dbt/" must not be able to mean "and start reporting the corpus" by writing one
    line. The keys are the same ones the registry declares, so there is one vocabulary to
    learn and not two.
    """
    base = registry["scan"]
    scan = project.get("scan") or {}
    return {
        "skip_hidden": bool(scan.get("skip_hidden", base.get("skip_hidden"))),
        "skip_dirs": set(base["skip_dirs"]) | set(as_list(scan.get("skip_dirs"))),
        "skip_files": set(base["skip_files"]) | set(as_list(scan.get("skip_files"))),
    }


def load_config(project: dict) -> tuple[dict, int]:
    """Framework defaults, overlaid with the project's own `framework.yaml`."""
    base = yaml.safe_load(CHECKS.read_text(encoding="utf-8"))
    checks: dict[str, dict] = {}
    for code, spec in (base.get("checks") or {}).items():
        spec = dict(spec or {})
        spec["level"] = normalize_level(spec.get("level", "warn"), code)
        checks[code] = spec

    stale_days = int(project.get("stale_days", base.get("stale_days", 90)))
    for code, override in (project.get("checks") or {}).items():
        if not isinstance(override, dict):     # `LC002: error` is the short form
            override = {"level": override}
        override = dict(override)
        if "level" in override:
            override["level"] = normalize_level(override["level"], code)
        if code not in checks:
            sys.exit(f"framework.yaml overrides {code!r}, which is not a check this "
                     "validator knows. A typo here switches nothing on, silently. "
                     "Run --list-checks for the catalog.")
        checks[code] = {**checks[code], **override}
    return checks, stale_days


def discover(root: Path, scan: dict, registry: dict, report: Report) -> list[Artifact]:
    skip_dirs = scan["skip_dirs"]
    skip_files = scan["skip_files"]
    skip_hidden = scan["skip_hidden"]
    id_re = re.compile(r"\b((?:%s)-\d{3,})\b" % "|".join(registry["id_prefixes"]))

    artifacts = []
    for p in sorted(root.rglob("*")):
        if p.is_dir() or p.suffix not in {".md", ".yaml", ".yml"}:
            continue
        parts = p.relative_to(root).parts
        if skip_hidden and any(part.startswith(".") for part in parts):
            continue
        if any(part in skip_dirs for part in parts[:-1]):
            continue
        if p.name in skip_files:
            continue
        rel = str(p.relative_to(root))
        meta, body, err = parse_front_matter(
            p.read_text(encoding="utf-8", errors="replace"))
        if err:
            report.add("FM001", rel, err)
            continue
        art = Artifact(p, rel, meta, body)
        art.ids = set(id_re.findall(body))
        artifacts.append(art)
    return artifacts


# ─────────────────────────────────────────────────────────────────────────────
# Checks

def check_front_matter(a: Artifact, registry: dict, report: Report) -> None:
    # The registry decides what is a known type, not the filesystem. Building a path out of
    # the declared value and asking whether it exists is how `artifact_type: ../../..` in a
    # front matter turns into a schema lookup somewhere else entirely. The `.exists()` stays
    # for the case the registry names a type whose schema was never generated.
    t = a.type
    schema_file = SCHEMA_DIR / t / "v1.json" if t and t in registry["types"] else None

    if schema_file is None or not schema_file.exists():
        declared = a.meta.get("artifact_type")
        report.add("FM003", a.rel,
                   f"artifact_type {declared!r} has no schema in the registry: new "
                   "template, or a typo? Until it is known, no type specific check runs "
                   "on this file.")
        return

    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(jsonify(a.meta)),
                    key=lambda e: list(e.path))
    for e in errors:
        where = "/".join(map(str, e.path)) or "front matter"
        report.add("FM002", a.rel, f"{where}: {e.message}")


def check_sections(a: Artifact, registry: dict, report: Report) -> None:
    wanted = (registry["types"].get(a.type) or {}).get("sections") or []
    if not wanted:
        return
    found = set(SECTION_MARK.findall(a.body))
    for sid in wanted:
        if sid not in found:
            report.add("SEC001", a.rel,
                       f"mandatory section {sid!r} not found. It is looked up by its "
                       f"marker, `<!-- section: {sid} -->`, not by the heading: if you "
                       "reworded the title the marker should still be above it.")


MOMENT_FORMATS = ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M",
                  "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                  "%Y-%m-%d")


def parse_moment(v) -> datetime | None:
    """An instant, or None if it is not one.

    YAML returns three different types for the same field: `2026-07-29` is a date,
    `2026-07-29 14:30:00` is a datetime, `2026-07-29 14:30` stays a string because
    without seconds it is not a valid YAML timestamp. All three are legitimate.

    No truncation: `2026-07-29 HH:MM` is a half filled field, and letting it pass for
    midnight would turn it into a document reviewed today.
    """
    if isinstance(v, datetime):        # before date: it is a subclass of it
        return v
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day)
    if isinstance(v, str):
        for fmt in MOMENT_FORMATS:
            try:
                return datetime.strptime(v.strip(), fmt)
            except ValueError:
                continue
    return None


def check_lifecycle(a: Artifact, stale_days: int, now: datetime, report: Report) -> None:
    lc = a.meta.get("lifecycle")
    if lc == "living":
        raw = a.meta.get("last_review")
        lr = parse_moment(raw)
        if lr is None and raw not in (None, "", []):
            report.add("LC004", a.rel,
                       f"last_review is {raw!r}, which is not an instant: expected "
                       "'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM'. While it stays like this the "
                       "document never counts as reviewed.")
        elif lr is None:
            report.add("LC001", a.rel,
                       "a living document needs last_review: without it there is no way "
                       "to notice it has gone stale")
        else:
            age = (now - lr).days
            if age > stale_days:
                report.add("LC002", a.rel,
                           f"living document not reviewed for {age} days (threshold "
                           f"{stale_days}). A stale living document is worse than an "
                           "absent one: it gets read as current.")
    elif lc == "immutable" and a.meta.get("last_review") is not None:
        report.add("LC003", a.rel,
                   "an immutable has no last_review: it is not reviewed, it is superseded")


def check_references(arts: list[Artifact], registry: dict, report: Report) -> None:
    id_re = re.compile(r"\b((?:%s)-\d{3,})\b" % "|".join(registry["id_prefixes"]))
    inline_types = set(registry["inline_id_types"])

    by_id: dict[str, Artifact] = {}
    for a in arts:
        if not a.id:
            continue
        if a.id in by_id:
            report.add("ID001", a.rel,
                       f"id {a.id!r} is already used by {by_id[a.id].rel}")
        else:
            by_id[a.id] = a

    # Identifiers defined inside a register rather than by a file of their own.
    inline: set[str] = set()
    for a in arts:
        if a.meta.get("lifecycle") == "append-only" or a.type in inline_types:
            inline |= a.ids
    known = set(by_id) | inline

    for a in arts:
        for ref in as_list(a.meta.get("derives_from")):
            if isinstance(ref, str) and id_re.fullmatch(ref) and ref not in known:
                report.add("REF001", a.rel, f"derives_from points at {ref!r}, which does "
                                            "not exist anywhere in this repository")
        sup = a.meta.get("supersedes")
        if sup and isinstance(sup, str) and id_re.fullmatch(sup):
            if sup not in known:
                report.add("REF002", a.rel, f"supersedes points at {sup!r}, which does "
                                            "not exist")
            else:
                target = by_id.get(sup)
                if target is not None and target.meta.get("status") != "superseded":
                    report.add("REF003", target.rel,
                               f"superseded by {a.id} but status is "
                               f"{target.meta.get('status')!r}: it has to move to "
                               "'superseded', or both documents claim to be current")

    for start in by_id:
        seen, cur = set(), start
        while cur:
            if cur in seen:
                report.add("REF004", by_id[start].rel,
                           f"cyclic supersedence chain starting at {start}")
                break
            seen.add(cur)
            nxt = by_id.get(cur)
            cur = nxt.meta.get("supersedes") if nxt else None


def check_release(arts: list[Artifact], report: Report) -> None:
    for a in arts:
        if a.type != "release-manifest":
            continue
        rb = a.meta.get("rollback") or {}
        if not isinstance(rb, dict):
            continue
        if not rb.get("target"):
            report.add("RLM001", a.rel,
                       "rollback.target is empty: the manifest is useless at the one "
                       "moment it exists for")
        if rb.get("tested") is False:
            report.add("RLM002", a.rel,
                       "rollback.tested is false: an untested rollback procedure is not "
                       "a procedure, it is an intention")


OD_BLOCK = re.compile(r"^###\s+(OD-\d{3,})(.*?)(?=^#{1,3}\s|\Z)", re.M | re.S)
COST_HIGH = re.compile(r"\*\*Cost to reverse:\*\*\s*high", re.I)
NO_DEFAULT = re.compile(r"\*\*Default in force:\*\*\s*none", re.I)


def check_open_register(arts: list[Artifact], report: Report) -> None:
    opens = [a for a in arts if a.type == "open-register"]
    if not opens:
        report.add("OD001", "OPEN.md",
                   "no open register: an agent has no way to know what has not been "
                   "decided, and will fill the gaps itself")
        return

    # Only a `DEC` that *derives from* an entry closes it. A `DEC` names an open entry for
    # three different reasons, and inferring closure from the mere mention would flag all
    # three the same way. A warning that is usually wrong teaches people to dismiss it.
    closed_by: dict[str, str] = {}
    for d in arts:
        if d.type != "decision-record" or d.meta.get("status") != "accepted":
            continue
        for ref in as_list(d.meta.get("derives_from")):
            if isinstance(ref, str) and ref.startswith("OD-"):
                closed_by[ref] = d.id or d.rel

    for a in opens:
        undecided = []
        for m in OD_BLOCK.finditer(a.body):
            od, block = m.group(1), m.group(2)
            if od in closed_by:
                report.add("OD002", a.rel,
                           f"{od} is still listed as open but {closed_by[od]} derives "
                           "from it: move the entry to §4 with a cross reference")
            if COST_HIGH.search(block) and NO_DEFAULT.search(block):
                undecided.append(od)
        if undecided:
            report.add("OD003", a.rel,
                       f"{', '.join(undecided)}: high cost to reverse and no default in "
                       "force. These have to be decided even on incomplete information, "
                       "because the cost of waiting exceeds the cost of being wrong.")


def check_cross_product(arts: list[Artifact], report: Report) -> None:
    products = {p for a in arts for p in as_list(a.meta.get("products"))}

    glossaries = [a for a in arts if a.type == "glossary"]
    if len(glossaries) > 1:
        report.add("XP001", ", ".join(g.rel for g in glossaries),
                   "more than one glossary: it is the file where the complementarity of "
                   "the products is either defined or lost, and it has to be single")

    for a in arts:
        if a.type != "data-contract":
            continue
        for c in as_list(a.meta.get("consumers")):
            if products and c not in products:
                report.add("XP002", a.rel,
                           f"consumer {c!r} matches no known product")

    with_pbr = {p for a in arts if a.type == "product-brief"
                for p in as_list(a.meta.get("products"))}
    for p in sorted(products - with_pbr):
        report.add("XP003", f"products/{p}/",
                   f"product {p!r} has no PBR: its definition exists only somewhere else")


# ─────────────────────────────────────────────────────────────────────────────
# Generated indices

def build_indices(root: Path, arts: list[Artifact]) -> dict[Path, str]:
    out: dict[Path, str] = {}

    decs = sorted((a for a in arts if a.type == "decision-record"), key=lambda a: a.id or "")
    if decs:
        target = root / "decisions" / "INDEX.md"
        rows = ["# Decision index", "",
                "Generated by `validate.py --emit-index`. Do not edit by hand.", "",
                "| ID | Scope | Status | Products | Title | Supersedes |",
                "|---|---|---|---|---|---|"]
        for d in decs:
            title = next((l.lstrip("# ").strip()
                          for l in d.body.splitlines() if l.startswith("# ")), "")
            try:
                href = str(d.path.relative_to(target.parent))
            except ValueError:
                href = "../" + d.rel
            rows.append(
                f"| [{d.id}]({href}) | {d.meta.get('scope', '')} | "
                f"{d.meta.get('status', '')} | "
                f"{', '.join(as_list(d.meta.get('products')))} | {title} | "
                f"{d.meta.get('supersedes') or ''} |")
        out[target] = "\n".join(rows) + "\n"

    edges = sorted({(ref, a.id or a.rel)
                    for a in arts
                    for ref in as_list(a.meta.get("derives_from"))
                    if isinstance(ref, str)})
    if edges:
        rows = ["# Traceability index", "",
                "Generated by `validate.py --emit-index`. Chain: PRB -> HYP -> EVD -> "
                "DEC -> SD -> CHG -> EVR -> RLM -> SIG -> DEC.", "",
                "| From | To |", "|---|---|"]
        rows += [f"| {s} | {t} |" for s, t in edges]
        out[root / "TRACEABILITY.md"] = "\n".join(rows) + "\n"

    return out


# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    # The Windows console is not UTF-8, and without this a character outside the codepage
    # ends the validator with a UnicodeEncodeError instead of with its verdict. A tool
    # that crashes when it has something to say is worse than an absent one.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")

    ap = argparse.ArgumentParser(description="Validate a Data & AI framework repository")
    ap.add_argument("--root", default=".", type=Path)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--emit-index", action="store_true",
                    help="regenerate decisions/INDEX.md and TRACEABILITY.md")
    ap.add_argument("--check", action="store_true",
                    help="with --emit-index: do not write, exit 1 if they are out of date")
    ap.add_argument("--stale-days", type=int, default=None,
                    help="override the staleness threshold from checks.yaml")
    ap.add_argument("--list-checks", action="store_true",
                    help="print every check and the severity in force, then exit")
    args = ap.parse_args()

    root = args.root.resolve()
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    project = load_project(root)
    config, stale_days = load_config(project)
    scan = load_scan(registry, project)
    if args.stale_days is not None:
        stale_days = args.stale_days

    if args.list_checks:
        for code in sorted(config):
            spec = config[code]
            print(f"{spec.get('level', 'warn'):<6} {code}  {spec.get('title', '')}")
        return 0

    report = Report(config)
    now = datetime.now()

    arts = discover(root, scan, registry, report)
    for a in arts:
        check_front_matter(a, registry, report)
        check_sections(a, registry, report)
        check_lifecycle(a, stale_days, now, report)
    check_references(arts, registry, report)
    check_release(arts, report)
    check_open_register(arts, report)
    check_cross_product(arts, report)

    index_written: list[str] = []
    index_stale: list[str] = []
    if args.emit_index:
        for path, text in build_indices(root, arts).items():
            rel = str(path.relative_to(root))
            if args.check:
                if not path.exists() or path.read_text(encoding="utf-8") != text:
                    index_stale.append(rel)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
                index_written.append(rel)

    errors = [f for f in report.findings if f.level == "error"]
    warns = [f for f in report.findings if f.level == "warn"]
    infos = [f for f in report.findings if f.level == "info"]

    if args.json:
        print(json.dumps({
            "artifacts": len(arts),
            "errors": len(errors), "warnings": len(warns), "info": len(infos),
            "generated": index_written, "out_of_date": index_stale,
            "findings": [f.__dict__ for f in report.findings],
        }, indent=2, ensure_ascii=False))
    else:
        print(f"Artifacts scanned: {len(arts)}")
        if index_written:
            print(f"Indices regenerated: {', '.join(index_written)}")
        for rel in index_stale:
            print(f"x {rel}: out of date. Run --emit-index without --check")
        for group, label in ((errors, "ERRORS"), (warns, "WARNINGS"), (infos, "NOTES")):
            if group:
                print(f"\n-- {label} ({len(group)}) " + "-" * 40)
                for f in group:
                    print(f.line())
        if not report.findings and not index_stale:
            print("\nNothing to report.")
        else:
            print(f"\nTotal: {len(errors)} errors | {len(warns)} warnings "
                  f"| {len(infos)} notes")

    return 1 if errors or index_stale else 0


if __name__ == "__main__":
    sys.exit(main())
