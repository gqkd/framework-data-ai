#!/usr/bin/env python3
"""
Validator for the Data & AI documentation framework.

One implementation, two entry points: the `audit` skill runs it interactively
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
  skills/audit/checks.yaml        which checks run, and at what severity

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
CHECKS = FRAMEWORK / "skills" / "audit" / "checks.yaml"

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


PROJECT_KEYS = {"checks", "stale_days", "scan", "framework_version"}
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


def canonical_repo(url: str) -> str:
    """One repository, one string, whichever way somebody wrote the remote.

    The three forms below are the same repository and compare unequal as text:

        git@github.com:org/repo.git
        ssh://git@github.com/org/repo.git
        https://github.com/org/repo.git

    This matters because the key of a `code:` entry is a local nickname and not an identity.
    Two products calling their own repository `backend` are not sharing one; the same
    repository entered as `identity` under one product and `auth` under another is. Keyed on
    the nickname, a check meant to catch a repository described twice reports the first case
    and passes the second -- and the second is how the duplication actually arises, because
    two teams naming the same thing each use their own word for it.

    An address this cannot parse comes back stripped and lowercased rather than empty. Two
    identical unparseable strings are still one repository, and losing that would trade a
    wrong answer for no answer.
    """
    s = str(url).strip().rstrip("/")
    s = re.sub(r"^[a-z+]+://", "", s, flags=re.I)      # scheme, if any
    s = re.sub(r"^[^/@]+@", "", s)                     # user, git@ and the rest
    # scp-style `host:path`, but not `host:port/path`: a port is part of the address and a
    # self-hosted GitLab on 8443 would otherwise have it turned into a directory.
    if re.match(r"^[^/]+:(?!\d+(?:/|$))[^/]", s):
        s = s.replace(":", "/", 1)
    s = re.sub(r"\.git$", "", s, flags=re.I)
    host, _, path = s.partition("/")
    return f"{host.lower()}/{path}" if path else s.lower()


def skipped_dir(parts: tuple[str, ...], skip_dirs: set[str]) -> bool:
    """Whether a document sitting in these directories is excluded from the scan.

    An entry with no slash matches a directory of that name at any depth, which is what
    `corpus` and `node_modules` want: they mean the same thing wherever they turn up.

    An entry with a slash is a path from the root, and exists because a bare name is
    sometimes too blunt to be safe. `_meta/extract` is the extractor's output and holds no
    source document; `extract` on its own would silently exclude the extraction step of
    every ETL project that keeps one in a directory of that name. The registry already
    states the principle it took a mistake to learn -- an exclusion that protects the
    framework's convenience is paid for by everyone using it -- and until now it could only
    be honoured by choosing awkward names.
    """
    if any(part in skip_dirs for part in parts):
        return True
    rel = "/".join(parts)
    return any("/" in s and (rel == s or rel.startswith(s + "/")) for s in skip_dirs)


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
        if skipped_dir(parts[:-1], skip_dirs):
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
        # Every identifier in the body, not only the ones in a declaring position. That is
        # looser than it looks like it should be, and the looseness is deliberate.
        #
        # A register does distinguish declaring an entry from citing one, but it does so in
        # prose, not in layout. `OPEN.md §4` closes an entry with
        # `- **2026-05-12 · OD-000** -> DEC-001`, and states a dependency with
        # `- **Depends on:** OD-011.` Both are list items carrying an identifier after some
        # text, and the only thing separating them is that one prefix is a date and the
        # other is a field label. Keying a check on that is a heuristic that will misfire,
        # and a check that misfires on correct documents gets switched off within a week,
        # which costs more than the hole it closed.
        #
        # The hole is therefore known and bounded: inside a register, an identifier of a
        # prefix that register declares is treated as existing even when it is only being
        # cited. `inline_id_declarations` keeps that from spreading to every other prefix,
        # which is where it did real damage. Closing the rest wants the registers to mark
        # their entries, not the validator to guess at them.
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


def check_placeholders(a: Artifact, registry: dict, report: Report) -> None:
    """A field still holding the value the template shipped with.

    The schemas reject the two `enforced` sentinels, and that is as far as they reach: they
    reject a plain string in a required field, and the fields this actually happens to are
    not that. `owners` is a list, so `[NAME]` clears its `minItems`. `created` carries no
    format on purpose, so `YYYY-MM-DD HH:MM` clears it too. `derives_from: [PRB-NNN]` is
    not something `REF001` can report, because `PRB-NNN` never matched the identifier
    pattern that check resolves against. A `verified_code: {backend: COMMIT_HASH}` sits
    inside a map, where the value rule is the map's and not `non_placeholder`.

    So the whole day one set copied out of `templates/` validates, and the registry says
    two lines above its own list what that costs: a placeholder that reaches a real
    repository reads as a real value to anything that does not know the template. `owners`
    names somebody to ask, `derives_from` names a document that exists, and neither is
    true.

    It cannot be fixed in the schemas. Every template ships `owners: [NAME]`, and the
    templates have to validate against their own schemas -- they are the thing people copy,
    and one that fails the check it teaches is worse than a permissive pattern. So this is
    a check on repositories, where `templates/` is not looked at anyway.

    At `warn`, and deliberately: a half filled scaffold is a normal state to be in for an
    hour. It is the state nobody comes back to that costs, and a warning is what says so.

    `last_review` is left to `LC004`, which already reports the same value and says more
    about it. Two findings on one field is how both get skimmed.
    """
    sentinels = set(registry["placeholders"]["enforced"])
    sentinels |= set(registry["placeholders"].get("other") or [])
    # `NNN` reaches a front matter attached to a prefix, never on its own: the templates
    # carry `derives_from: [PRB-NNN]` and `id: DEC-NNN`, and matching the bare sentinel
    # found neither. Built from the registry's own prefixes rather than from any `-NNN`,
    # which is the same shape the generated schemas already allow as a map key.
    unfilled_id = re.compile(r"^(?:%s)-NNN$" % "|".join(registry["id_prefixes"]))

    def walk(value, where: str) -> None:
        if isinstance(value, str):
            v = value.strip()
            if v in sentinels or unfilled_id.match(v):
                report.add("FM004", a.rel,
                           f"{where} is still the template's {v!r}. In a repository that "
                           "reads as a filled field to anything that did not copy the "
                           "template: a person to ask, a date, a document that exists. "
                           "Fill it, or delete the field if it does not apply here.")
        elif isinstance(value, dict):
            for k, v in value.items():
                walk(v, f"{where}/{k}")
        elif isinstance(value, list):
            for i, v in enumerate(value):
                walk(v, f"{where}[{i}]")

    for field, value in a.meta.items():
        if field == "last_review":
            continue
        walk(value, str(field))


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
    inline_decl = registry["inline_id_declarations"]

    by_id: dict[str, Artifact] = {}
    for a in arts:
        if not a.id:
            continue
        if a.id in by_id:
            report.add("ID001", a.rel,
                       f"id {a.id!r} is already used by {by_id[a.id].rel}")
        else:
            by_id[a.id] = a

    # Identifiers defined inside a register rather than by a file of their own. Only the
    # prefixes that register actually declares: a register cites far more identifiers than
    # it owns, and accepting all of them let a document vouch for a reference simply by
    # mentioning it. That failed in the direction nobody looks, silently clearing a
    # finding, and it fired exactly when someone followed the REF001 guidance to write in
    # prose that the target was missing.
    inline: set[str] = set()
    for a in arts:
        prefixes = inline_decl.get(a.type or "")
        if prefixes:
            inline |= {i for i in a.ids if i.split("-", 1)[0] in prefixes}
    known = set(by_id) | inline
    sup_edges: dict[str, list[str]] = {}

    for a in arts:
        for ref in as_list(a.meta.get("derives_from")):
            if isinstance(ref, str) and id_re.fullmatch(ref) and ref not in known:
                report.add("REF001", a.rel, f"derives_from points at {ref!r}, which does "
                                            "not exist anywhere in this repository")
        # One decision replacing two earlier ones is an ordinary thing to write, and
        # `supersedes: [DEC-001, DEC-004]` is how anyone would write it: `derives_from`
        # in the same front matter already takes a list. It used to be read only when it
        # was a bare string, so the list form skipped REF002 and REF003 in silence and
        # then killed the cycle walk with an unhashable type.
        for sup in as_list(a.meta.get("supersedes")):
            if not (isinstance(sup, str) and id_re.fullmatch(sup)):
                continue
            sup_edges.setdefault(a.id, []).append(sup)
            if sup not in known:
                report.add("REF002", a.rel, f"supersedes points at {sup!r}, which does "
                                            "not exist")
                continue
            target = by_id.get(sup)
            if target is not None and target.meta.get("status") != "superseded":
                report.add("REF003", target.rel,
                           f"superseded by {a.id} but status is "
                           f"{target.meta.get('status')!r}: it has to move to "
                           "'superseded', or both documents claim to be current")

    # Depth first, colouring what is on the current path. An edge back into the path is a
    # cycle; an edge into something already finished is not. The difference only shows up
    # once supersedes can branch: two decisions replaced by the same later one meet again
    # further up, and a plain visited set would call that meeting a loop.
    on_path, done = set(), set()
    for root in by_id:
        if root in done:
            continue
        stack = [(root, iter(sup_edges.get(root, ())))]
        on_path.add(root)
        while stack:
            node, edges = stack[-1]
            nxt = next(edges, None)
            if nxt is None:
                on_path.discard(node)
                done.add(node)
                stack.pop()
            elif nxt in on_path:
                report.add("REF004", by_id[nxt].rel,
                           f"cyclic supersedence chain through {nxt}")
            elif nxt not in done and nxt in by_id:
                on_path.add(nxt)
                stack.append((nxt, iter(sup_edges.get(nxt, ()))))


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
    decisions: dict[str, Artifact] = {}
    for d in arts:
        if d.type != "decision-record":
            continue
        if d.id:
            decisions[d.id] = d
        if d.meta.get("status") != "accepted":
            continue
        for ref in as_list(d.meta.get("derives_from")):
            if isinstance(ref, str) and ref.startswith("OD-"):
                closed_by[ref] = d.id or d.rel

    for a in opens:
        # Read out of `entries:` in the front matter, not out of the prose. Both of these
        # used to match `- **Cost to reverse:** high` in the body, so translating the label
        # or reformatting the bullet switched them off silently -- and a silent OD003 reads
        # as "nothing high-cost is undecided", which is the answer somebody wanted.
        entries = a.meta.get("entries")
        if not isinstance(entries, dict):
            report.add("OD004", a.rel,
                       "no `entries:` in the front matter. The body may say anything it "
                       "likes and OD002 and OD003 have nothing to read, so this register "
                       "reports clean however it is filled in.")
            continue

        undecided = []
        for od, row in sorted(entries.items()):
            if not isinstance(row, dict):
                continue

            # The register's own instructions call `Default in force` mandatory, and until
            # now only `OD003` looked at it and only on a high cost entry. A medium one with
            # no default passed, which is the field the whole file is built around: a
            # decision not taken does not mean nothing is happening, and naming what is
            # happening is what turns a worry into a decidable question.
            #
            # `OD-` only. A known issue has no default in force and no cost to reverse:
            # those are properties of a choice, and a `KI` is not one.
            if od.startswith("OD-"):
                if row.get("status") == "open" and not str(row.get("default_in_force") or "").strip():
                    report.add("OD005", a.rel,
                               f"{od} is open and names no `default_in_force`. Something is "
                               "happening in the absence of this decision; write it, and "
                               "write `none` when the honest answer is that nothing is.")
                # While it is open, and not after. `cost_to_reverse` is what orders §1, and
                # an entry that has been decided is not in that queue any more: the field
                # was already spent. Asked of a `decided` row it made the documented
                # closure -- write the `DEC`, move the entry to §4 -- report a finding for
                # having been carried out, which is the one direction a check must never
                # fail in.
                if row.get("status") == "open" and not row.get("cost_to_reverse"):
                    report.add("OD005", a.rel,
                               f"{od} is open and declares no `cost_to_reverse`. It is what "
                               "orders this register, and an entry without it is filed "
                               "nowhere.")
            if row.get("status") == "decided":
                # Resolved, and not only present. A `closed_by` naming a decision that does
                # not exist has the identical consequence to naming none -- the reasoning
                # cannot be reached -- and it reads better, which makes it worse. Same shape
                # `STK001` already applies to `decided_in`: the record has to exist and be
                # accepted.
                #
                # `OD-` only. The register's own template says a `KI` links a `CHG`, a `DEC`
                # or a `SIG`, so resolving a known issue's closer as a decision record would
                # report the two thirds of that sentence that are not one.
                named = row.get("closed_by")
                dec = decisions.get(named) if isinstance(named, str) else None
                if not named:
                    report.add("OD005", a.rel,
                               f"{od} is `decided` and names no `closed_by`. The decision "
                               "exists somewhere and nothing here points at it, so the "
                               "reasoning has to be found again by whoever asks next.")
                elif not od.startswith("OD-"):
                    pass
                elif dec is None:
                    report.add("OD005", a.rel,
                               f"{od} is `decided` and names {named!r}, which is not a "
                               "decision in this repository. The entry reads as settled and "
                               "the reasoning cannot be reached, which is the state naming "
                               "nothing at all would have left it in.")
                elif dec.meta.get("status") != "accepted":
                    report.add("OD005", a.rel,
                               f"{od} is `decided` and names {named!r}, whose status is "
                               f"{dec.meta.get('status')!r}. An entry closed on a decision "
                               "still in draft, or on one already superseded, is not closed.")
                elif od not in as_list(dec.meta.get("derives_from")):
                    # The two checks disagree about one fact, and one of them is silent.
                    # `OD002` reads closure off `derives_from` and nothing else, on purpose,
                    # so a `decided` entry whose decision does not name it is one `OD002`
                    # could never have caught had the status been left `open`. The chain in
                    # `TRACEABILITY.md` is built from the same field, so the closure is
                    # missing from the graph too.
                    report.add("OD005", a.rel,
                               f"{od} says it was closed by {named}, and {named} does not "
                               f"name {od} in `derives_from`. Closure is read off that field "
                               "everywhere else here -- by `OD002`, and by the traceability "
                               "chain -- so as written this entry is closed in one direction "
                               "only, and invisible in the other.")
            for dep in as_list(row.get("depends_on")):
                if dep not in entries:
                    report.add("OD005", a.rel,
                               f"{od} depends on {dep!r}, which this register does not "
                               "declare. Either it was decided and the dependency is stale, "
                               "or it is a typo and this entry is waiting for nothing.")
            if od in closed_by and row.get("status") == "open":
                report.add("OD002", a.rel,
                           f"{od} is still `status: open` but {closed_by[od]} derives from "
                           "it: set it `decided`, name the decision in `closed_by`, and "
                           "move the entry to §4 with a cross reference")
            # `none` however it is qualified: an entry saying "none, because there is no
            # retraining yet" states that nothing is happening, with its reason. Reading only
            # an exact match let that one through, and it is the entry this check exists for.
            # The looseness errs towards reporting an entry that does have a default, which is
            # the cheap direction: the other one hides the most expensive combination there is.
            default = str(row.get("default_in_force") or "none").strip().lower()
            if (row.get("status") == "open" and row.get("cost_to_reverse") == "high"
                    and (not default or re.match(r"none\b", default))):
                undecided.append(od)
        if undecided:
            report.add("OD003", a.rel,
                       f"{', '.join(undecided)}: high cost to reverse and no default in "
                       "force. These have to be decided even on incomplete information, "
                       "because the cost of waiting exceeds the cost of being wrong.")


def check_change_contracts(arts: list[Artifact], report: Report) -> None:
    """What an `ICG` said a change touches, against what the change actually cites.

    These two were catalogued and switched off from the day they were written, because the
    only place the routing existed was prose inside the `CHG` body, and the recovered
    version matched words in it. Matching prose is the fragility the section markers were
    introduced to remove, so putting it back for two checks was never worth it.

    The `ICG` made the join possible. A `CHG` names the classification it came from in
    `icg` and its candidate in `derives_from`, and the classification records what that
    candidate touches in `impacts`. So the question is a lookup and not a search.

    Both bind on `status` rather than on existence, because the artifacts arrive in an
    order. A `DEC` precedes the contract: the reshaping happens before the change is
    authorized, so an approved `CHG` should already cite one. An `EVR` follows the build,
    so demanding it earlier than `verified` would forbid the order the framework
    prescribes.

    A `CHG` with no `icg` is not reported by either of them, and is reported by `CHG003`
    instead. Keeping it separate is what stops the first two from being about something
    other than their titles, and `CHG003` is a check of its own because the gap it names is
    not a missing `EVR` or a missing `DEC`: it is the join itself being absent, which is
    how both of the others come back clean without having looked at anything.
    """
    by_id = {a.id: a for a in arts if a.id}
    icgs = {a.id: a for a in arts if a.type == "impact-classification"}
    AUTHORIZED = ("approved", "implemented", "verified", "rolled-back")

    for a in arts:
        if a.type != "change-contract":
            continue
        icg = icgs.get(a.meta.get("icg"))
        if icg is None:
            # From `approved` onwards only. Writing the proposal before the triage that
            # classifies it is the order the framework prescribes, so a `draft` with no
            # classification is a change waiting for one, not a change that dodged it.
            if a.meta.get("status") in AUTHORIZED:
                named = a.meta.get("icg")
                why = (f"names {named!r}, which is not an impact classification in this "
                       "repository" if named else "names no impact classification")
                report.add("CHG003", a.rel,
                           f"authorized at {a.meta.get('status')!r} and {why}. Nothing "
                           "says what this change touches, so CHG001 and CHG002 pass "
                           "without looking: the report is green because the question was "
                           "never asked. Classify it in an `ICG`, `routing: none` included.")
            continue
        impacts_map = icg.meta.get("impacts")
        if not isinstance(impacts_map, dict):
            continue

        # Every candidate this change derives from, and everything they touch between them.
        touches: set[str] = set()
        for ref in as_list(a.meta.get("derives_from")):
            for i in as_list(impacts_map.get(ref)):
                if isinstance(i, str):
                    touches.add(i)

        status = a.meta.get("status")
        if "ai" in touches and status == "verified":
            evr = a.meta.get("verified_by")
            target = by_id.get(evr) if isinstance(evr, str) else None
            if target is None or target.type != "evaluation-report":
                named = f"{evr!r}, which is not an evaluation report in this repository" \
                    if evr else "nothing in `verified_by`"
                report.add("CHG001", a.rel,
                           f"{icg.id} says this touches an AI component, and the change is "
                           f"`verified` citing {named}. Touching a model, a prompt or a "
                           "retrieval index and calling it done without an evaluation "
                           "report means nobody measured what it did.")
        if "architecture" in touches and status in ("approved", "implemented", "verified"):
            decs = [r for r in as_list(a.meta.get("derives_from"))
                    if isinstance(r, str) and (by_id.get(r) is not None
                                               and by_id[r].type == "decision-record")]
            if not decs:
                report.add("CHG002", a.rel,
                           f"{icg.id} says this touches the architecture, and the change is "
                           f"`{status}` without a decision record in `derives_from`. The "
                           "architecture moved and the reason it moved is written nowhere, "
                           "which is the question a `DEC` exists to answer.")


def check_framework_version(root: Path, project: dict, registry: dict,
                            report: Report) -> None:
    """Which version of the framework this repository was written against.

    Without it, the day the framework moves under a project there is no way to tell "the
    rules changed" from "we did this wrong", and those two need opposite responses. The
    first is a migration and somebody else's fault; the second is a repair. Guessing
    between them is how a team decides the validator is unreliable and stops reading it.

    A mismatch warns rather than blocks, and that direction matters: the moment the
    registry moves is exactly when a project most needs to be able to run the validator
    and see what it says. A gate that fails closed on a version bump gets bypassed on the
    day it was supposed to help.
    """
    declared = project.get("framework_version")
    current = registry.get("version")
    if declared is None:
        report.add("FW002", "framework.yaml",
                   f"no `framework_version`. This repository does not record which "
                   f"version of the framework it was written against, so when the rules "
                   f"change nothing here will distinguish a migration from a mistake. "
                   f"The framework is at {current}.")
        return
    # A quoted number in YAML is a string, and `"1" != 1`. Reported as a version skew it
    # sends somebody looking for a migration that does not exist, which is the confusion
    # this check was added to remove rather than cause.
    if not isinstance(declared, int):
        report.add("FW001", "framework.yaml",
                   f"framework_version is {declared!r}, which is "
                   f"{type(declared).__name__} and not a whole number. In YAML a quoted "
                   f"value is a string: write `framework_version: {current}` without "
                   f"quotes. Until it is a number this says nothing about which framework "
                   f"the repository was written against.")
        return
    if declared != current:
        direction = "behind" if declared < current else "ahead of"
        report.add("FW001", "framework.yaml",
                   f"declares framework_version {declared!r} and the framework is at "
                   f"{current!r}, so this repository is {direction} it. Findings below "
                   f"may be the rules having moved rather than the documents being "
                   f"wrong. Read the registry's `version` comment for what a bump means, "
                   f"then either migrate and update this line, or pin the framework.")


def check_triage(arts: list[Artifact], report: Report) -> None:
    """Which signals has nobody looked at.

    `LOG` is append-only, so a row cannot be marked handled and triage state was simply
    unrecorded: every cycle re-read the whole log and guessed which entries were new. It
    lives in the `ICG` now, where every candidate examined appears in `routing`, including
    the ones that turned out not to be candidates at all. So the question becomes a set
    difference, and the answer stops depending on who is doing the reading.

    One finding per log rather than one per signal. Adopting the framework on a project
    that already has a log means every entry predates the first `ICG`, and a wall of
    identical warnings on day one is how a check gets switched off before it is understood.
    """
    logs = [a for a in arts if a.type == "signal-log"]
    if not logs:
        return

    triaged: set[str] = set()
    for a in arts:
        if a.type == "impact-classification":
            routing = a.meta.get("routing")
            if isinstance(routing, dict):
                triaged |= {k for k in routing if isinstance(k, str)}

    for log in logs:
        untriaged = sorted(i for i in log.ids if i.startswith("SIG-") and i not in triaged)
        if not untriaged:
            continue
        shown = ", ".join(untriaged[:8]) + (" ..." if len(untriaged) > 8 else "")
        never = "no impact classification exists in this repository" if not triaged \
            else "no impact classification lists them"
        report.add("ICG001", log.rel,
                   f"{len(untriaged)} signal(s) that {never}: {shown}. A signal nobody "
                   "triaged is not the same as one triaged and set aside, and only the "
                   "second is a decision. Route them in the next `ICG`, including as "
                   "`not-a-candidate`, which is what stops the next cycle re-reading them.")


def check_stack(arts: list[Artifact], report: Report) -> None:
    """What a stack entry's `status` claims, against what it carries.

    The template says a `chosen` row names the decision that chose it and an `unratified`
    row is one nobody decided. The schema requires neither, so `status: chosen` with nothing
    behind it validates -- which is the ambiguity this artifact was added to remove, arriving
    back through the field that was supposed to remove it.
    """
    accepted = {a.id for a in arts
                if a.type == "decision-record" and a.meta.get("status") == "accepted" and a.id}
    known_dec = {a.id for a in arts if a.type == "decision-record" and a.id}
    products = {p for a in arts for p in as_list(a.meta.get("products"))}

    for a in arts:
        if a.type != "operational-stack":
            continue
        for cap, row in sorted((a.meta.get("stack") or {}).items()):
            if not isinstance(row, dict):
                continue
            status, dec = row.get("status"), row.get("decided_in")
            if status in ("chosen", "ruled-out") and not dec:
                report.add("STK001", a.rel,
                           f"{cap!r} is {status!r} and names no `decided_in`. It reads as a "
                           "decision and there is no record of one, which is what "
                           "`unratified` is for: a tool in use that nobody chose.")
            elif status == "unratified" and dec:
                report.add("STK001", a.rel,
                           f"{cap!r} is `unratified` and names {dec!r}. If the decision "
                           "exists the row is `chosen`; leaving it unratified hides a "
                           "decision that was taken.")
            if dec and dec not in known_dec:
                report.add("STK001", a.rel,
                           f"{cap!r} names {dec!r}, which is not a decision in this "
                           "repository. The tool is presented as chosen and the reasoning "
                           "cannot be reached.")
            elif dec and dec not in accepted:
                report.add("STK001", a.rel,
                           f"{cap!r} names {dec!r}, which is not accepted. A tool chosen on "
                           "a decision still in draft or already superseded is a tool whose "
                           "reason has moved.")
            for p in as_list(row.get("used_by")):
                if products and p not in products:
                    report.add("STK001", a.rel,
                               f"{cap!r} says it is used by {p!r}, which matches no product "
                               "here. Either the product is undocumented or the name is a "
                               "typo, and both leave the row addressed to nobody.")


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

    # A product still in Block A is not missing its brief, it has not reached it. Discovery
    # is elastic on purpose (FRAMEWORK.md §5), and a check that reports a product for being
    # early is the framework asking a project to backfill a document nobody had the grounds
    # to write. The stage the manifest declares is what tells the two apart; a product with
    # no manifest at all is reported, because then nothing said which it was.
    # A repository belongs to one product or to the substrate, never to both and never to
    # two products. The map is the answer to "where is the code", and two answers to one
    # question is the state this framework exists to prevent: the copies are written on the
    # same day and describe the same repository, and then one of them is updated.
    # Keyed on the canonicalised remote, never on the entry's key: the key is what this file
    # calls the repository and the URL is which repository it is.
    declared: dict[str, list[str]] = {}
    for a in arts:
        if a.type not in ("product-manifest", "platform-architecture"):
            continue
        code = a.meta.get("code")
        if not isinstance(code, dict):
            continue
        for key, entry in code.items():
            url = entry.get("url") if isinstance(entry, dict) else None
            if isinstance(url, str) and url.strip():
                declared.setdefault(canonical_repo(url), []).append(f"{a.rel} as {key!r}")
    for repo, where in sorted(declared.items()):
        if len(where) > 1:
            report.add("XP004", repo,
                       f"one repository declared in {len(where)} places: {'; '.join(sorted(where))}. "
                       "A repository shared by several products belongs to `code:` in "
                       "`PLATFORM.md`, and one that serves a single product to that "
                       "product's manifest. Two entries are two descriptions of one "
                       "repository, and only one of them gets corrected. The names differ "
                       "and the remote does not, which is how this arises: each side calls "
                       "it what it calls it.")

    # What `verified_code` is allowed to name, and what it must not leave out. Built from
    # both maps and qualified the way the field is keyed, because a product and the platform
    # may each own a `backend` and an attestation cannot be ambiguous about which it ran on.
    known: set[str] = set()
    # Per product, never global. Built globally, this asked the `ARC` of one product to
    # attest another product's backend -- a false positive on every repository holding more
    # than one product, which is the arrangement the code map exists for.
    owed: dict[str, set[str]] = {}
    for a in arts:
        if a.type == "product-manifest":
            scope = "product"
        elif a.type == "platform-architecture":
            scope = "platform"
        else:
            continue
        code = a.meta.get("code")
        if not isinstance(code, dict):
            continue
        for key, entry in code.items():
            qualified = f"{scope}.{key}"
            known.add(qualified)
            if not isinstance(entry, dict) or str(entry.get("release_relevant")).lower() != "true":
                continue
            if scope == "product":
                for p in as_list(a.meta.get("products")):
                    owed.setdefault(p, set()).add(qualified)
            else:
                # A shared repository has to say whose release it is part of. Nothing else
                # can: the substrate serves several products and only some of them may ship
                # against a given change. `used_by` is that statement, and without it no
                # attestation can be required -- which is a hole, so it is reported rather
                # than left to be discovered by the release it failed to cover.
                users = as_list(entry.get("used_by"))
                if not users:
                    report.add("VER003", a.rel,
                               f"{key!r} is `release_relevant` and names no `used_by`. No "
                               "product claims it, so no evaluation can be required to "
                               "attest it, and a shared component ships unmeasured while "
                               "every report reads as complete. List the products that go "
                               "through it.")
                for p in users:
                    # The names, not only their presence. A typo here reproduces exactly the
                    # failure `VER002` was written to prevent, and it arrives through the
                    # field that feeds `VER002`: `owed` gets a key no document will ever
                    # claim, so nothing is required of anybody and the report comes back
                    # clean. `STK001` already applies this test to `used_by` on a stack row,
                    # which is the same field answering the same question -- it was checked
                    # in one file and not in the other.
                    if products and p not in products:
                        report.add("VER003", a.rel,
                                   f"{key!r} says it is used by {p!r}, which matches no "
                                   "product here. Either that product is undocumented or "
                                   "the name is a typo, and in both cases nothing owes this "
                                   "repository an attestation: it ships unmeasured while "
                                   "every report reads as complete, which is what "
                                   "`release_relevant` was supposed to prevent.")
                    owed.setdefault(p, set()).add(qualified)

    for a in arts:
        attested = a.meta.get("verified_code")
        if not isinstance(attested, dict):
            continue
        for key in sorted(set(attested) - known):
            report.add("VER001", a.rel,
                       f"{key!r} is attested here and is in no `code:` map. Either the "
                       "repository is not recorded anywhere, in which case the commit "
                       "points at something this repository cannot resolve, or the key is a "
                       "typo and a repository that was measured is not represented.")
        # Only what this document's own products owe. A project that has marked nothing
        # `release_relevant` owes nothing: the framework does not get to invent the standard
        # it then enforces.
        mine: set[str] = set()
        for p in as_list(a.meta.get("products")):
            mine |= owed.get(p, set())
        for key in sorted(mine - set(attested)):
            report.add("VER002", a.rel,
                       f"{key!r} is marked `release_relevant` for this product and carries "
                       "no commit here. The attestation covers part of the system and reads "
                       "as covering all of it, which is the failure a single hash had and "
                       "the reason this field became a map.")

    early = {p for a in arts if a.type == "product-manifest"
             for p in as_list(a.meta.get("products"))
             if str((a.meta.get("stage") or {}).get("phase", "")).upper() in {"F1", "F2", "F3"}}
    with_pbr = {p for a in arts if a.type == "product-brief"
                for p in as_list(a.meta.get("products"))}
    for p in sorted(products - with_pbr - early):
        report.add("XP003", f"products/{p}/",
                   f"product {p!r} has no PBR: its definition exists only somewhere else")


# ─────────────────────────────────────────────────────────────────────────────
# Generated indices

# The line that says a file at one of these paths was produced here. It is also the
# permission to overwrite it, which is why it has one definition and not three: a marker
# that drifts from the text it is matched against protects nothing. See the refusal in
# main().
GENERATED_MARK = "Generated by `validate.py --emit-index`"


def build_indices(root: Path, arts: list[Artifact]) -> dict[Path, str]:
    out: dict[Path, str] = {}

    decs = sorted((a for a in arts if a.type == "decision-record"), key=lambda a: a.id or "")
    if decs:
        target = root / "decisions" / "INDEX.md"
        rows = ["# Decision index", "",
                f"{GENERATED_MARK}. Do not edit by hand.", "",
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

    # The derived half of `product.yaml`, in a file of its own rather than as sections
    # rewritten inside it. `product.yaml` is authoritative and full of comments carrying the
    # reasoning behind each field; rewriting parts of it while preserving those is a swamp,
    # and the sections marked GENERATED there were being kept by hand and going stale. A
    # separate file is the same answer the decision index already uses.
    #
    # Only what is derivable without judgement. `open_decisions` comes from the register's
    # own `entries:`, not from a list somebody maintains beside it, which is the duplication
    # this removes: two answers to "what is still open", and the stale one is the one an
    # agent reads first because `AGENTS.md` sends it to the manifest.
    # Scoped per product. There is one register at the root and it holds entries of
    # different scope, so collecting every open entry once put a decision about one product
    # into the derived view of another -- and this file is what `AGENTS.md` sends an agent to
    # first. An entry naming no product concerns all of them, which is the common case: "do
    # these products share a substrate" belongs to every one of them.
    open_entries = [(od, row) for a in arts if a.type == "open-register"
                    for od, row in (a.meta.get("entries") or {}).items()
                    if isinstance(row, dict) and row.get("status") == "open"]

    for man in (a for a in arts if a.type == "product-manifest"):
        prod = next(iter(as_list(man.meta.get("products"))), None)
        if not prod:
            continue
        open_now = sorted(od for od, row in open_entries
                          if prod in as_list(row.get("products"))
                          or not as_list(row.get("products")))
        mine = [a for a in arts if prod in as_list(a.meta.get("products"))]
        changes = sorted(a.id for a in mine if a.type == "change-contract"
                         and a.meta.get("status") in ("approved", "implemented") and a.id)
        releases = sorted(a.id for a in mine if a.type == "release-note" and a.id)
        living = sorted(f"{a.rel} ({a.meta.get('last_review') or 'never reviewed'})"
                        for a in mine if a.meta.get("lifecycle") == "living")
        lines = [f"# {GENERATED_MARK}. Do not edit by hand.",
                 "#",
                 "# The derived view of this product. `product.yaml` beside it is authoritative",
                 "# and hand written; everything here is recomputed from the artifacts, so a",
                 "# disagreement between the two is this file being out of date and never the",
                 "# other way round.",
                 "generated_by: validate.py --emit-index",
                 f"product: {prod}",
                 f"current_release: {releases[-1] if releases else 'null'}",
                 "open_decisions: [" + ", ".join(open_now) + "]",
                 "active_changes: [" + ", ".join(changes) + "]",
                 "living_artifacts:"]
        lines += [f"  - {x}" for x in living] or ["  []"]
        out[man.path.parent / "product.index.yaml"] = "\n".join(lines) + "\n"

    edges = sorted({(ref, a.id or a.rel)
                    for a in arts
                    for ref in as_list(a.meta.get("derives_from"))
                    if isinstance(ref, str)})
    if edges:
        rows = ["# Traceability index", "",
                f"{GENERATED_MARK}. Chain: PRB -> HYP -> EVD -> "
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
        check_placeholders(a, registry, report)
        check_sections(a, registry, report)
        check_lifecycle(a, stale_days, now, report)
    check_references(arts, registry, report)
    check_release(arts, report)
    check_change_contracts(arts, report)
    check_framework_version(root, project, registry, report)
    check_open_register(arts, report)
    check_triage(arts, report)
    check_stack(arts, report)
    check_cross_product(arts, report)

    index_written: list[str] = []
    index_stale: list[str] = []
    index_protected: list[str] = []
    if args.emit_index:
        for path, text in build_indices(root, arts).items():
            rel = str(path.relative_to(root))
            # A file sitting at a generated path without the marker was written by a
            # person. Regenerating it is not an update, it is a deletion: the generator
            # reproduces only what it can derive from front matter, and the reason someone
            # kept the file by hand is precisely the part it cannot derive. Refuse, name
            # the file, and let a person decide. Calling this "out of date" under --check
            # would be worse than useless: it would push them towards the overwrite.
            if path.exists() and GENERATED_MARK not in path.read_text(encoding="utf-8"):
                index_protected.append(rel)
                continue
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
            "hand_maintained": index_protected,
            "findings": [f.__dict__ for f in report.findings],
        }, indent=2, ensure_ascii=False))
    else:
        print(f"Artifacts scanned: {len(arts)}")
        if index_written:
            print(f"Indices regenerated: {', '.join(index_written)}")
        for rel in index_stale:
            print(f"x {rel}: out of date. Run --emit-index without --check")
        for rel in index_protected:
            print(f"x {rel}: not regenerated. It carries no \"{GENERATED_MARK}\" line, so "
                  "it is maintained by hand and regenerating it would drop whatever it "
                  "holds that front matter cannot express. Move that content elsewhere "
                  "first, or delete the file if it is genuinely derived.")
        for group, label in ((errors, "ERRORS"), (warns, "WARNINGS"), (infos, "NOTES")):
            if group:
                print(f"\n-- {label} ({len(group)}) " + "-" * 40)
                for f in group:
                    print(f.line())
        if not report.findings and not index_stale and not index_protected:
            print("\nNothing to report.")
        else:
            print(f"\nTotal: {len(errors)} errors | {len(warns)} warnings "
                  f"| {len(infos)} notes")

    # A refusal counts as a failure when a write was asked for and did not happen: a caller
    # that got exit 0 would carry on believing the file had been regenerated. Under
    # --check it does not, because a deliberately hand maintained index is a state a
    # project is allowed to be in, and a check that can never go green gets switched off.
    refused_a_write = index_protected and not args.check
    return 1 if errors or index_stale or refused_a_write else 0


if __name__ == "__main__":
    sys.exit(main())
