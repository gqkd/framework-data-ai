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
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path, PurePosixPath

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

# A date inside a trigger, in any of the shapes one gets written in: `2026-09-30`, the
# same thing quoted or with the full stop a prose bullet leaves behind, `30/09/2026`,
# `Q4 2026`, `end of 2026`. The year is what all of them have in common, so the year is
# what is matched, plus the day-first forms that carry no four digit year at all. YAML
# hands back a `date` object for the unquoted ISO form, and that is caught before any
# matching happens.
#
# WHAT IT DOES NOT CATCH, and this is a limit rather than an omission: "by the end of the
# quarter", "within a month". Those are time expressions with no digits in them, and a
# check that tried to match them would have to match prose. The template says an event, the
# skill says an event, and this catches the half that can be caught without guessing.
# The value that says "every product, including the ones that do not exist yet". A list of
# names says the same thing until somebody adds a product, and then it quietly says less --
# which is the failure this word exists to prevent, and the reason it is not spelled by
# listing everybody.
ALL_PRODUCTS = "all"

# The third state of `leaves_open`, and the one a real repository needed four times in a
# week: this decision did not settle everything, and what it left is not in any register
# yet. A list of ids says where to look. Absence says nobody looked. This says somebody
# looked, found something, and has not written the entry -- which is a debt, and reads
# nothing like the other two.
UNREGISTERED = "unregistered"

# `commitment: none` on a risk. Same shape as the two above, and needed for the same reason:
# a commercial risk is not always about a promise. An untested market hypothesis, a
# comparison drawn against the wrong competitor set, an intellectual property transfer
# nobody completed -- all commercial exposures, none of them a claim made to anybody. Before
# this the only way to stop the check asking was to file the risk under a category that was
# not true, which is the repair `audit/SKILL.md` spends half a page warning against.
NO_COMMITMENT = "none"

DATE_IN_TEXT = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)"
                          r"|(?<!\d)\d{1,2}[/.]\d{1,2}[/.]\d{2,4}(?!\d)")


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

def as_map(v) -> dict:
    """A front matter map, or an empty one when what is there is not a map.

    `terms: [Freshness, Tenant]` is one bracket away from `terms:` with two rows under it,
    and it killed the validator: `.items()` on a list raises, the process died on the
    malformed document, and nothing was said about the two hundred artifacts it had not
    reached. The schema already reports the shape -- that is what `FM002` is -- so the job
    here is only to let the run finish and report it.

    `entries:` has been guarded since the same thing happened to it. Three maps added in one
    week were not, because each was written by copying the line above it, which is how a
    lesson stays learned in one place.
    """
    return v if isinstance(v, dict) else {}


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


PROJECT_KEYS = {"checks", "stale_days", "scan", "framework_version",
                "framework_commit"}
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
    try:
        project = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        # A traceback here is the worst place for one: this file is the first thing read,
        # so a stray quote in it makes the validator die before it has looked at a single
        # document, with a message about a unicode string and no filename in it. The other
        # failures in this function exit with the path and the repair; so does this one now.
        sys.exit(f"{path}: does not parse as YAML.\n"
                 f"{str(e).strip()}")
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


# How many living documents have to share one instant before it stops being a coincidence.
# Two is a person who finished the second one in the same minute, which happens. Three is a
# batch, and a batch is not a reading.
SAME_INSTANT_FLOOR = 3


def check_review_batches(arts: list[Artifact], report: Report) -> None:
    """Living documents attesting the same review instant.

    `last_review` says a person read this document and found it still true, and no check
    can verify a reading. What a check can see is the shape the false version takes: six
    living documents in one repository stamped with the same minute, one of them carrying a
    notice at the top saying it still had to be reread in full. That did not happen at
    19:36 to six documents at once, and it is the only fact here a script can hold.

    Timed to the minute rather than to the day, because a day is a plausible unit for real
    work: reading four documents on a Tuesday is a Tuesday. Reading four in one minute is a
    field edit.
    """
    by_instant: dict[str, list[str]] = {}
    for a in arts:
        if a.meta.get("lifecycle") != "living":
            continue
        lr = parse_moment(a.meta.get("last_review"))
        # A bare date carries no minute, so it cannot say anything about batching: two
        # documents reviewed on the same day are two documents reviewed on the same day.
        if lr is None or lr.hour == lr.minute == 0:
            continue
        # A DAY ONE SET IS A CREATION AND NOT A REVIEW. `start` writes the whole first
        # set in one session, legitimately, and every document is born with `created` and
        # `last_review` at the same instant -- there is nothing to have reread, because
        # nothing existed before. Counting those would make this check fire on every
        # repository the framework itself creates, on its first day, which is the shortest
        # path to it being switched off.
        if parse_moment(a.meta.get("created")) == lr:
            continue
        by_instant.setdefault(lr.strftime("%Y-%m-%d %H:%M"), []).append(a.rel)

    for instant, rels in sorted(by_instant.items()):
        if len(rels) < SAME_INSTANT_FLOOR:
            continue
        listed = ", ".join(sorted(rels))
        report.add("LC005", sorted(rels)[0],
                   f"{len(rels)} living documents attest the same review instant "
                   f"({instant}): {listed}. `last_review` is a claim that somebody read the "
                   "document and found it still true, and one minute is not enough for all "
                   "of them. If they really were read, the instant each reading finished is "
                   "the honest value; if the date was written to clear `LC002`, the warning "
                   "was doing its job and this is what replaced it.")


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




UNION_MARK = "<!-- generated: open-union -->"


def product_dirs(arts: list[Artifact]) -> dict[Path, tuple[str, str]]:
    """Where each product's documents live, read off its manifest: dir -> (product, rel).

    The directory and not the `products:` field, because that is how a register declares
    its scope now. In `products/<p>/OPEN.md` the field is redundant and nobody writes it:
    the entry is about that product by virtue of where it was filed, the same way an entry
    in `platform/OPEN.md` is about the substrate. Reading scope off the field instead put
    every unlabelled entry of every register into every product's derived view, which is
    the one direction this must not fail in: `AGENTS.md` sends an agent to that view first.
    """
    out: dict[Path, tuple[str, str]] = {}
    for m in arts:
        if m.type != "product-manifest":
            continue
        p = next(iter(as_list(m.meta.get("products"))), None)
        if p:
            out[m.path.parent] = (p, str(PurePosixPath(m.rel).parent))
    return out


# What `product.index.yaml` now answers, and what a manifest used to answer by hand while
# claiming to be generated. Kept as a list rather than folded into the schema because these
# are not illegal fields -- they are answers that have moved, and the finding has to say
# where they moved to.
MOVED_TO_INDEX = {
    "open_decisions": "the registers, composed by `--emit-index`",
    "open_risks": "`RSK.md` §state, which is where a risk is actually written",
    "active_changes": "the `CHG` records themselves",
}


# `GLOSSARY §Tenant`, with or without the backticks around the file name. The section sign
# is the whole convention and it is worth one: "see the glossary" is not a reference, it is
# a gesture, and nothing can resolve it.
# The pipe is in the stop set because a citation is very often written inside a table cell,
# and without it the match ran to the end of the row: a document citing a term in a column
# produced a finding naming `'Metriche | routed |'`, which resolves to nothing for a reason
# that has nothing to do with the glossary.
GLOSSARY_CITE = re.compile(r"GLOSSARY`?\s*§\s*([^`\n,.;:)\]|]+)")

# `§Metrics`, `§Domain terms` -- the headings of the glossary itself, and the section sign is
# required. Pointing a reader at a section is a legitimate citation and resolves to no term
# by construction, so a check that only knows terms would report the one form of reference
# that cannot be wrong.
#
# WITHOUT THE `§` THIS EXEMPTED EVERY HEADING IN THE FILE, which handed back the hole the
# `terms:` map was added to close: a word defined only as `### Freshness` in the body, absent
# from the map, resolved a citation and reported nothing. That is resolving against prose
# headings, which two checks here already went quiet for once.
GLOSSARY_SECTION = re.compile(r"^#{1,6}\s*§\s*(.+?)\s*$", re.M)


def declared_entries(arts: list[Artifact]) -> set[str]:
    """Every entry id any register in the repository declares."""
    return {od for a in arts if a.type == "open-register"
            for od in (a.meta.get("entries") or {})}


def check_glossary_terms(arts: list[Artifact], report: Report) -> None:
    """A term cited by a document and defined by nobody.

    The pair whose second end nothing resolved. A data contract sending a reader to the
    glossary for what a column means is a reference exactly like `derives_from`, and a
    contract citing three terms that the glossary does not contain reads as defined and is
    not -- which is more expensive than citing nothing, because the reader stops looking.

    Resolved against `terms:` and not against the `###` headings of the body, because this
    framework has already been bitten once by an index built on prose: two checks read
    headings and lines, somebody reworded a label, and both went quiet reporting nothing.
    """
    glossaries = [a for a in arts if a.type == "glossary"]
    declared: dict[str, tuple[str, dict]] = {}
    sections: set[str] = set()
    for g in glossaries:
        for name, row in as_map(g.meta.get("terms")).items():
            declared[str(name).strip().lower()] = (g.rel, row if isinstance(row, dict) else {})
        sections |= {m.group(1).strip().lower()
                     for m in GLOSSARY_SECTION.finditer(g.body)}

    known = declared_entries(arts)
    for term, (rel, row) in sorted(declared.items()):
        blocked = row.get("blocked_by")
        if blocked and blocked not in known:
            report.add("REF005", rel,
                       f"the term {term!r} says its definition is blocked by {blocked!r}, "
                       "which no register in this repository declares. Either the decision "
                       "was taken and the term is waiting on nothing, or the id is a typo "
                       "and the reason this word has no definition is not written down "
                       "anywhere.")

    for a in arts:
        if a.type == "glossary":
            continue
        for m in GLOSSARY_CITE.finditer(a.body):
            name = " ".join(m.group(1).split()).strip("*_`")
            if name.lower() in sections:
                continue
            if not glossaries:
                report.add("REF005", a.rel,
                           f"this document sends a reader to the glossary for {name!r} and "
                           "there is no glossary in this repository.")
            elif not declared:
                report.add("REF005", a.rel,
                           f"this document cites {name!r} and no glossary declares any "
                           "`terms:`, so nothing can say whether the word is defined. The "
                           "definitions may well be in the body; what is missing is the "
                           "half a reference can be resolved against.")
            elif name.lower() not in declared:
                report.add("REF005", a.rel,
                           f"this document cites {name!r} and no glossary declares it. A "
                           "citation that resolves to nothing is worse than none: the "
                           "reader stops looking, and the word goes on meaning whatever "
                           "each document assumed.")


def check_decisions_leave_open(arts: list[Artifact], report: Report) -> None:
    """What a decision did not settle, named where it can be counted.

    A `DEC` that says in its prose that something remains explicitly open leaves a question
    that no register holds and no count of open decisions includes. `leaves_open: []` is the
    answer when there is nothing, and it is a different claim from the field being absent --
    the third time this repository has had to buy that distinction, after `entries: {}` and
    `products: [all]`.
    """
    known = declared_entries(arts)
    for a in arts:
        if a.type != "decision-record" or a.meta.get("status") == "superseded":
            continue
        if "leaves_open" not in a.meta:
            report.add("REG012", a.rel,
                       "this decision does not say what it leaves open. `leaves_open: []` "
                       "is the answer when it settles everything it touched, "
                       f"`[{UNREGISTERED}]` when it left something nobody has written down "
                       "yet, and both are different statements from saying nothing: a "
                       "question a decision names in its prose and no register holds is a "
                       "question nobody is counting.")
            continue
        declared = as_list(a.meta.get("leaves_open"))
        if UNREGISTERED in declared:
            others = [od for od in declared if od != UNREGISTERED]
            also = f" It also names {', '.join(others)}." if others else ""
            report.add("REG014", a.rel,
                       "this decision leaves something open that no register holds, and "
                       f"says so.{also} The debt is declared and that is the whole "
                       "difference from the silence next door -- but it is still a question "
                       "nobody can find, nothing ranks by cost to reverse, and no count of "
                       "what is open includes. Write the entry and name it here.")
        for od in declared:
            if od == UNREGISTERED:
                continue
            if od not in known:
                report.add("REG012", a.rel,
                           f"this decision leaves {od!r} open and no register declares it. "
                           "The open half of a decision is only open if somebody can find "
                           "it, and a register is where it gets looked for. If the entry "
                           f"has not been written yet, `{UNREGISTERED}` is how to say so.")


def check_commitments_and_risks(arts: list[Artifact], report: Report) -> None:
    """The pair that had no second end because neither register could be read.

    A commitment beyond what exists yet is supposed to produce a risk and an open entry.
    Both halves were markdown tables until now, so nothing could join them, and in a real
    repository the two failures showed up together: a product carrying eleven commitments
    and no risk register at all, and -- in another product -- a commercial risk tracking a
    claim that the commitments file did not contain. A risk with no promise behind it is a
    risk nobody will renegotiate, because there is nothing to renegotiate.
    """
    cmts = {cid: (a.rel, row)
            for a in arts if a.type == "commitments"
            for cid, row in as_map(a.meta.get("commitments")).items()
            if isinstance(row, dict)}
    risk_files = [a for a in arts if a.type == "risk-register"]

    # Which products have a risk register, read off the directory the register sits in,
    # the same way a register's scope is read everywhere else here.
    dirs = product_dirs(arts)
    covered = {dirs[a.path.parent][0] for a in risk_files if a.path.parent in dirs}

    # A PROMISE NOBODY HAS RECEIVED CREATES NO EXPOSURE, AND COUNTING IT WEAKENS THE
    # FINDING RATHER THAN STRENGTHENING IT. `not-yet-issued` is the row that exists in an
    # internal document and has been said to nobody -- the state `COMMITMENTS.md` puts first
    # because it is the only one where the remedy costs an afternoon. There is no risk to
    # own yet. A finding that counted it invited the obvious check, and whoever checked
    # found one of the eleven had never been said to anybody and began doubting the other
    # ten: a number that does not survive being verified takes the argument down with it.
    promised: dict[str, list[str]] = {}
    withheld: dict[str, list[str]] = {}
    for cid, (rel, row) in sorted(cmts.items()):
        bucket = withheld if row.get("status") == "not-yet-issued" else promised
        for prod in as_list(row.get("products")):
            bucket.setdefault(prod, []).append(cid)

    for prod in sorted(set(promised) | set(withheld)):
        ids = promised.get(prod, [])
        if not ids or prod in covered or prod not in {p for p, _ in dirs.values()}:
            continue
        held = withheld.get(prod, [])
        aside = (f" ({len(held)} more are `not-yet-issued` and are not counted: nothing has "
                 "been said to anybody yet, so there is no exposure to own.)" if held else "")
        report.add("XP005", f"products/{prod}/RSK.md",
                   f"{prod!r} carries {len(ids)} commitment(s) that have been made -- "
                   f"{', '.join(sorted(ids))} -- and has no risk register.{aside} A promise "
                   "made before the thing exists is the ordinary case here and it is "
                   "supposed to leave two marks: a risk somebody owns and an entry in the "
                   "register. With no `RSK.md` the first one has nowhere to be, and the "
                   "exposure lives only in the sentence that created it.")

    for a in arts:
        if a.type != "risk-register":
            continue
        for rid, row in sorted(as_map(a.meta.get("risks")).items()):
            if not isinstance(row, dict):
                continue
            named = row.get("commitment")
            if named and named != NO_COMMITMENT and named not in cmts:
                report.add("REF006", a.rel,
                           f"{rid} names {named!r}, which no commitments register declares. "
                           "The risk is about a promise nobody can find, so nothing can be "
                           "renegotiated and nothing can be closed by the promise changing.")
            elif not named and row.get("category") == "commercial" \
                    and row.get("state") not in ("closed", "expired"):
                # ASKS, AND DOES NOT ASSERT. This used to say the risk was a claim recorded
                # as a promise nowhere, which is false of every commercial risk that is not
                # about a promise -- and there is no category for those, so the only way to
                # silence it was to file the risk under something untrue. Two readings, and
                # the field can now hold either answer.
                report.add("REF006", a.rel,
                           f"{rid} is a commercial risk and says nothing about a promise. "
                           "Either somebody promised this and the commitments register does "
                           "not have it -- in which case the exposure cannot be "
                           "renegotiated, because there is no record of a promise to "
                           f"renegotiate -- or it is an exposure nobody promised, and "
                           f"`commitment: {NO_COMMITMENT}` says so. The two are different "
                           "risks with different remedies, and silence reads as the first.")


def check_manifest_derived_fields(arts: list[Artifact], report: Report) -> None:
    """A manifest answering a question something else now answers.

    These three were marked GENERATED in the template for months with a note underneath
    admitting nothing generated them, so they were hand written and read as derived: the
    worst of both, because a section labelled generated is a section nobody rereads. They
    are derived now, in `product.index.yaml`, and a manifest that still carries them is a
    second answer to a question that has one -- which is exactly how a repository ends up
    telling three different stories about which entries belong to which product.
    """
    for a in arts:
        if a.type != "product-manifest":
            continue
        for field_name, where in sorted(MOVED_TO_INDEX.items()):
            if field_name in a.meta:
                report.add("FM005", a.rel,
                           f"`{field_name}` is still in this manifest. It is derived now, "
                           f"and the authority is {where}; `product.index.yaml` beside this "
                           "file holds the computed answer. Two answers to one question, "
                           "and the hand written one is the one that goes stale without "
                           "anybody noticing, because the label says it is generated.")


def check_open_register(arts: list[Artifact], report: Report) -> None:
    opens = [a for a in arts if a.type == "open-register"]
    if not opens:
        report.add("REG001", "OPEN.md",
                   "no open register: an agent has no way to know what has not been "
                   "decided, and will fill the gaps itself")
        return

    # One register per product, at the product's own root. It is not a convenience: the
    # register is the file an agent reads before deciding anything, and an agent working on
    # one product reads the one beside the product. A product without one has its open
    # questions filed under somebody else's heading, or nowhere.
    dirs = product_dirs(arts)
    held = {a.path.parent for a in opens}
    for d, (prod, rel) in sorted(dirs.items(), key=lambda kv: kv[1][0]):
        if d not in held:
            report.add("REG006", f"{rel}/OPEN.md",
                       f"product {prod!r} has no open register of its own. Whatever is "
                       "undecided about it is filed in another product's register or in "
                       "none, and an agent sent to work on this product finds a directory "
                       "that says nothing is open.")

    # A date in a heading binds every entry filed under it, and no field of any entry
    # records it. The tier headings of this framework's own template used to read "decide
    # within the first month", which put a term of time on sixteen entries at once in the
    # first repository that copied them -- and `REG009` could not see it, because it reads
    # the `trigger` of an entry and a heading belongs to no entry.
    #
    # Headings only, and that is what makes this checkable rather than a guess at prose: a
    # line starting with `#` is a structure a person wrote on purpose, and a date in one is
    # addressed to whoever files an entry underneath it.
    for a in opens:
        # A `#` inside a fenced block is a comment in somebody's example, not a heading, and
        # a bash snippet saying `# rigenerato il 2026-09-30` was reported as a heading
        # carrying a date. A false finding costs the trip to the document, and the second
        # trip is the one where somebody stops reading the output.
        fenced = False
        for i, line in enumerate(a.body.splitlines(), 1):
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if fenced:
                continue
            if line.startswith("#") and DATE_IN_TEXT.search(line):
                report.add("REG010", a.rel,
                           f"a heading carries a date: {line.strip()[:70]!r}. It applies to "
                           "every entry filed under it and belongs to none of them, so no "
                           "`trigger` records it and nothing will report it going stale. A "
                           "heading says what a group of entries have in common -- what "
                           "changing your mind costs -- and when each of them has to be "
                           "decided is the `trigger` of that entry.")

    # Numbering is one sequence across every register in the repository. `depends_on` and
    # the `derives_from` of a `DEC` resolve an entry by its id alone, so two registers that
    # both start at `OD-001` make those references ambiguous, and the ambiguity resolves
    # itself silently: whichever file was read last wins.
    where: dict[str, str] = {}
    for a in opens:
        rows = a.meta.get("entries")
        for od in rows if isinstance(rows, dict) else ():
            if od in where:
                report.add("REG007", a.rel,
                           f"{od} is also declared by {where[od]}. Entry ids are one "
                           "sequence across every register here, because `depends_on` and "
                           "the `derives_from` of a `DEC` name an entry by its id and "
                           "nothing else. Continue the numbering instead of restarting it, "
                           "and keep the old label in the prose beside the heading.")
            else:
                where[od] = a.rel

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
        # or reformatting the bullet switched them off silently -- and a silent REG003 reads
        # as "nothing high-cost is undecided", which is the answer somebody wanted.
        entries = a.meta.get("entries")
        if not isinstance(entries, dict):
            # One register is allowed to hold no entries, and only one: the union at the
            # root of a repository that files its entries per product. It carries the
            # marker that says so, the marker is what `--emit-index` writes into, and a
            # repository with a single register does not qualify however it is marked.
            # Without this the file that gathers every other register would be reported for
            # being what it is, and the reliable way to clear that finding is to paste the
            # entries back in, which is the divergence the union exists to remove.
            if not (UNION_MARK in a.body and len(opens) > 1):
                report.add("REG004", a.rel,
                           "no `entries:` in the front matter. The body may say anything "
                           "it likes and REG002 and REG003 have nothing to read, so this "
                           "register reports clean however it is filled in.")
            continue

        # What this register is about, read off where it sits. An entry in a product's
        # register that names a different product is filed under the wrong heading: a
        # person reading that directory takes it for the directory's, and the derived view
        # attributes it elsewhere, so the two disagree with nobody being told.
        scope = dirs.get(a.path.parent, (None, None))[0]

        undecided = []
        for od, row in sorted(entries.items()):
            if not isinstance(row, dict):
                continue

            # The register's own instructions call `Default in force` mandatory, and until
            # now only `REG003` looked at it and only on a high cost entry. A medium one with
            # no default passed, which is the field the whole file is built around: a
            # decision not taken does not mean nothing is happening, and naming what is
            # happening is what turns a worry into a decidable question.
            #
            # `OD-` only. A known issue has no default in force and no cost to reverse:
            # those are properties of a choice, and a `KI` is not one.
            if od.startswith("OD-"):
                if row.get("status") == "open" and not str(row.get("default_in_force") or "").strip():
                    report.add("REG005", a.rel,
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
                    report.add("REG005", a.rel,
                               f"{od} is open and declares no `cost_to_reverse`. It is what "
                               "orders this register, and an entry without it is filed "
                               "nowhere.")

            # What forces the decision, and a date on its own does not force anything. The
            # field was called `deadline` until 2.0.0, and a field named for a date collects
            # dates: an end of quarter that reads as a commitment and was picked because the
            # line had to say something. A date inside a trigger is legitimate and stays
            # silent -- "the external audit, 2026-10-31" says what arrives on the day. A bare
            # does not, and the entry it sits on is by definition one nobody has decided.
            if row.get("status") == "open":
                trg = row.get("trigger")
                if isinstance(trg, (date, datetime)) or (
                        isinstance(trg, str) and DATE_IN_TEXT.search(trg)):
                    report.add("REG009", a.rel,
                               f"{od} has a date in its `trigger`. A date does not force a "
                               "decision by arriving; something does, and the entry is open "
                               "precisely because nobody has decided when. Name the event "
                               "and drop the date: the second customer, the first line of "
                               "code written against it, the contract, or another entry in "
                               "this register -- `depends_on` for one before the other, "
                               "`decide_with` for two that have to be taken together.")
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
                    report.add("REG005", a.rel,
                               f"{od} is `decided` and names no `closed_by`. The decision "
                               "exists somewhere and nothing here points at it, so the "
                               "reasoning has to be found again by whoever asks next.")
                elif not od.startswith("OD-"):
                    pass
                elif dec is None:
                    report.add("REG005", a.rel,
                               f"{od} is `decided` and names {named!r}, which is not a "
                               "decision in this repository. The entry reads as settled and "
                               "the reasoning cannot be reached, which is the state naming "
                               "nothing at all would have left it in.")
                elif dec.meta.get("status") != "accepted":
                    report.add("REG005", a.rel,
                               f"{od} is `decided` and names {named!r}, whose status is "
                               f"{dec.meta.get('status')!r}. An entry closed on a decision "
                               "still in draft, or on one already superseded, is not closed.")
                elif od not in as_list(dec.meta.get("derives_from")):
                    # The two checks disagree about one fact, and one of them is silent.
                    # `REG002` reads closure off `derives_from` and nothing else, on purpose,
                    # so a `decided` entry whose decision does not name it is one `REG002`
                    # could never have caught had the status been left `open`. The chain in
                    # `TRACEABILITY.md` is built from the same field, so the closure is
                    # missing from the graph too.
                    report.add("REG005", a.rel,
                               f"{od} says it was closed by {named}, and {named} does not "
                               f"name {od} in `derives_from`. Closure is read off that field "
                               "everywhere else here -- by `REG002`, and by the traceability "
                               "chain -- so as written this entry is closed in one direction "
                               "only, and invisible in the other.")
            # Against every register and not against this one. Once the entries are filed
            # per product, an entry waiting on a substrate decision is the ordinary case
            # and its `depends_on` points at another file by design. Resolving it locally
            # reported each of those as a dangling reference -- a check firing on the
            # arrangement the framework asks for, which is how a check gets switched off.
            for dep in as_list(row.get("depends_on")):
                if dep not in where:
                    report.add("REG005", a.rel,
                               f"{od} depends on {dep!r}, which no register in this "
                               "repository declares. Either it was decided and the "
                               "dependency is stale, or it is a typo and this entry is "
                               "waiting for nothing.")

            # `decide_with` is the relation `depends_on` cannot express: two entries that
            # have to be taken in one sitting because deciding either alone decides the
            # other by implication. Same resolution, because the failure is the same -- a
            # pairing with an entry nobody can find reads as a pairing that was honoured.
            # Naming itself is reported separately: it looks like a filled-in field and
            # binds the entry to nothing, which is the shape that survives a review.
            for peer in as_list(row.get("decide_with")):
                if peer == od:
                    report.add("REG005", a.rel,
                               f"{od} names itself in `decide_with`. The field says which "
                               "other entry has to be decided in the same sitting, and an "
                               "entry paired with itself is an empty field that reads as a "
                               "full one.")
                elif peer not in where:
                    report.add("REG005", a.rel,
                               f"{od} is to be decided with {peer!r}, which no register in "
                               "this repository declares. Either it was decided and the "
                               "pairing is stale, or it is a typo and this entry is paired "
                               "with nothing.")

            stray = [p for p in as_list(row.get("products")) if p != scope]
            if scope and stray:
                report.add("REG008", a.rel,
                           f"{od} sits in the register of {scope!r} and declares "
                           f"{', '.join(map(repr, stray))}. A register scoped to a product "
                           "is about that product: an entry belonging to another one goes "
                           "in that product's register, and one belonging to several goes "
                           "in the register at the root, where naming them is what the "
                           "field is for.")
            # THE ROOT REGISTER IS WHERE NOTHING ELSE ANSWERS THE QUESTION. Under
            # `products/<p>/` the directory says who an entry is about, which is why the
            # field is normally left off and `REG008` reports one that contradicts it. At
            # the root there is no directory to ask, and an entry with no `products:` binds
            # every product by rule -- indistinguishable from an entry nobody asked the
            # question about. Both look like silence, and one of them is a decision.
            #
            # The same distinction `entries: {}` bought against an absent `entries:`: read
            # and there is nothing, versus nobody filled this in. `products: [all]` is the
            # statement; nothing is the gap.
            #
            # NOT ASKED BEFORE THERE ARE PRODUCTS TO NAME. A repository at day one has a
            # register and no `product.yaml` anywhere -- that is the state `start` is
            # written for, and the whole point of the register is that it fills up before
            # the products do. Asking which products an entry binds when the repository
            # declares none is a question with no available answers, and `[all]` there says
            # nothing. Same shape as not reporting a product in discovery for lacking what
            # discovery has not reached.
            if a.rel == "OPEN.md" and dirs:
                named = as_list(row.get("products"))
                if not named:
                    report.add("REG011", a.rel,
                               f"{od} sits in the register at the root and names no "
                               "`products:`. It binds every product in this repository, "
                               "which may be what somebody meant or may be a question "
                               "nobody asked -- and the two are written identically. Name "
                               "the products it binds, or `[all]` when it really is all of "
                               "them.")
                elif len(named) == 1 and named[0] != ALL_PRODUCTS \
                        and named[0] in {prod for prod, _ in dirs.values()}:
                    # WHAT THE ROOT REGISTER IS FOR, WRITTEN TWICE AND ENFORCED NOWHERE.
                    # `FRAMEWORK.md` says it keeps the entries that belong to no single
                    # product; `REG008` says an entry belonging to one goes in that
                    # product's register. Neither could see this, because `REG008` only
                    # looks inside `products/<p>/` and at the root there is no directory to
                    # contradict. So a green `REG011` came to mean the question was
                    # answered, which is not the same as the answer implying the entry is
                    # where it belongs -- a check that a field is filled in is not a check
                    # that the value is right.
                    #
                    # Only when the product has a directory. An entry naming a product that
                    # has no register anywhere has nowhere to be moved to, and asking is
                    # asking for something impossible; `REG006` is the finding for that,
                    # and it is about the product rather than the entry.
                    report.add("REG013", a.rel,
                               f"{od} sits in the register at the root and binds "
                               f"{named[0]!r} alone. The root is for what belongs to no "
                               "single product; this belongs beside the product, in "
                               f"`products/{named[0]}/OPEN.md`, which is the file an agent "
                               "working on it reads first. Moving it costs a cut and a "
                               "paste: ids are one sequence across every register here, so "
                               "the entry keeps its number and every `depends_on` and "
                               "`derives_from` naming it still resolves.")
                elif ALL_PRODUCTS in named and len(named) > 1:
                    others = [p for p in named if p != ALL_PRODUCTS]
                    report.add("REG011", a.rel,
                               f"{od} declares `[{ALL_PRODUCTS}]` and also names "
                               f"{', '.join(map(repr, others))}. Either it binds everything "
                               "or it binds those, and as written the reader has to guess "
                               "which half was the afterthought.")

            if od in closed_by and row.get("status") == "open":
                report.add("REG002", a.rel,
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
            report.add("REG003", a.rel,
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


# ─────────────────────────────────────────────────────────────────────────────
# The pull request

CHG_IN_TEXT = re.compile(r"\bCHG-\d{3,}\b")

# The declared exception, and it is declared on purpose. A gate with no honest way out is
# a gate somebody deletes from the workflow file the first Friday it blocks a typo, and
# what goes with it is the check that mattered. `no-chg:` costs a sentence, appears in the
# pull request where a reviewer reads it, and stays in the history. What it must never be
# is silent: a reason is required, because "no-chg" alone is the same thing as deleting
# the check with extra steps.
NO_CHG = re.compile(r"^[ \t>*-]*no-chg:[ \t]*(\S.*)$", re.M | re.I)

# What each impact obliges the change set to touch. `ai` is deliberately absent: the `EVR`
# is written at the release gate, after the build, so demanding it in the pull request that
# builds the thing would forbid the order the framework prescribes. `CHG001` asks for it at
# `verified`, which is where it belongs.
IMPACT_OBLIGES = {
    "architecture": ("architecture", "an `ARC`"),
    "data": ("data-contract", "the `DC`"),
    "risk-compliance": ("risk-register", "`RSK`"),
}

AUTHORIZED_FOR_A_PR = ("approved", "implemented", "verified")


def check_pull_request(arts: list[Artifact], pr_text: str | None,
                       changed: set[str] | None, report: Report) -> None:
    """The change set against the contract that authorizes it.

    Everything else in this file reads the documents. This reads the documents against
    something outside them -- what a pull request says it is doing, and which files it
    touches -- and that is why it runs only when the caller supplies both, rather than on
    every invocation. A check that cannot see the change set has to stay quiet about it:
    reporting "no `CHG`" on a plain `--root` run would fire on every desk in the project.

    The join it makes is the one the framework already describes and nothing enforced. A
    `CHG` is what turns a signal into a mandate with boundaries; `status: approved` is what
    says the mandate exists. Until now the only thing standing between a `draft` and a
    merge was somebody remembering, and the template's own anti-pattern list says what that
    costs: "if this happens systematically, the `status` field is doing nothing".

    `PR004` is the other half, and it is the one that recovers a rule that had no home.
    "Touch data or schema and the `DC` is versioned" used to live in a process document of
    its own, which was folded into the cycle; the obligation survives here, as a question
    about the diff rather than about the prose. The `ICG` says what the candidate touches,
    the diff says what was touched, and the two disagreeing is a contract that moved
    without anybody versioning it.
    """
    if pr_text is None:
        return

    ids = sorted(set(CHG_IN_TEXT.findall(pr_text)))
    if not ids:
        exempt = NO_CHG.search(pr_text)
        if not exempt:
            report.add("PR001", "pull request",
                       "names no change contract, and carries no `no-chg:` line saying "
                       "why. A signal, a request, an `RMP` increment and a good idea are "
                       "not authorizations: the one authorization this framework has is a "
                       "`CHG` with `status: approved`. Cite it, or write `no-chg: <reason>` "
                       "and let the reason be read.")
        return

    by_id = {a.id: a for a in arts if a.id}
    by_rel = {a.rel: a for a in arts}
    icgs = {a.id: a for a in arts if a.type == "impact-classification"}
    touched = {by_rel[p].type for p in (changed or set()) if p in by_rel}

    for cid in ids:
        a = by_id.get(cid)
        if a is None or a.type != "change-contract":
            what = (f"is a {a.type!r} and not a change contract" if a is not None
                    else "is not in this repository")
            report.add("PR002", "pull request",
                       f"cites {cid}, which {what}. Either the identifier is a typo, or "
                       "the contract lives somewhere this repository cannot see -- and a "
                       "mandate nobody can read is not a mandate.")
            continue

        status = a.meta.get("status")
        if status not in AUTHORIZED_FOR_A_PR:
            why = ("was rolled back: whatever it authorized has been taken out again, so "
                   "it cannot authorize this" if status == "rolled-back" else
                   f"is `{status}`, which is a proposal and not a mandate. The boundary "
                   "between an idea and authorized work is this field, and merging across "
                   "it is how the field stops meaning anything")
            report.add("PR003", a.rel,
                       f"{cid} is cited by a change set that is being merged, and it {why}.")
            continue

        if changed is None:
            continue

        icg = icgs.get(a.meta.get("icg"))
        impacts_map = icg.meta.get("impacts") if icg is not None else None
        if not isinstance(impacts_map, dict):
            continue
        impacts: set[str] = set()
        for ref in as_list(a.meta.get("derives_from")):
            for i in as_list(impacts_map.get(ref)):
                if isinstance(i, str):
                    impacts.add(i)

        for impact in sorted(impacts):
            if impact not in IMPACT_OBLIGES:
                continue
            wanted_type, what = IMPACT_OBLIGES[impact]
            if wanted_type in touched:
                continue
            extra = (" A data contract that changed without its version moving is a "
                     "promise broken silently: the consumers are reading the old one and "
                     "nothing tells them to stop." if impact == "data" else "")
            report.add("PR004", a.rel,
                       f"{icg.id} classifies this change as touching `{impact}`, and the "
                       f"change set does not touch {what}. Either the classification was "
                       f"wrong, or the update is missing.{extra}")

SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def semver(v) -> tuple[int, int, int] | None:
    """`"1.2.3"` as a comparable triple, or None when it is not one.

    A string and never a number, which is the whole reason this exists. The framework's
    version and the plugin's are one number now, so it carries the plugin's shape: YAML
    turns `2` into an int and `1.1` into a float, and comparing either with `"1.1.0"` is
    either a crash or a silent False. Parsing to a triple makes `1.10.0` sort after
    `1.9.0`, which string comparison gets backwards and which is the first place this would
    have gone wrong without being noticed.
    """
    m = SEMVER.match(v.strip()) if isinstance(v, str) else None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


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
    # Three numbers separated by dots, and YAML has a trap on each side of that. `2` comes
    # back an int and `1.1` comes back a float, so both of the shapes somebody reaches for
    # when shortening it stop being comparable to the registry's value -- and a version that
    # cannot be compared is reported as a skew, which sends somebody looking for a migration
    # that does not exist. That is the confusion this check exists to remove rather than
    # cause, so the shape is stated and the two near misses are named.
    want, got = semver(current), semver(declared)
    if got is None:
        report.add("FW001", "framework.yaml",
                   f"framework_version is {declared!r}, which is not three numbers "
                   f"separated by dots. Write `framework_version: {current}`. In YAML a "
                   f"bare {current.split('.')[0]} reads as a whole number and a bare "
                   f"{'.'.join(current.split('.')[:2])} reads as a decimal, and neither can "
                   f"be compared with a version: until this line has all three parts it "
                   f"says nothing about which framework the repository was written against.")
        return
    # A PATCH IS SILENT, AND THAT IS THE WHOLE POINT OF HAVING THREE NUMBERS. This check
    # exists to tell "the rules moved" from "we did this wrong", and by the registry's own
    # definition a patch is wording, a message, a fixture -- nothing a repository has to do
    # anything about. Reporting it asked every project on earth to edit a line each time a
    # sentence was rephrased here, and a finding whose correct response is "change the number
    # to make it stop" is a finding people learn to clear without reading.
    if got[:2] != want[:2]:
        direction = "behind" if got < want else "ahead of"
        report.add("FW001", "framework.yaml",
                   f"declares framework_version {declared!r} and the framework is at "
                   f"{current!r}, so this repository is {direction} it. Findings below "
                   f"may be the rules having moved rather than the documents being "
                   f"wrong. Read the registry's `version` comment for what a bump means, "
                   f"then either migrate and update this line, or pin the framework.")


COMMIT = re.compile(r"^[0-9a-f]{7,40}$")


def framework_head() -> str | None:
    """The commit this framework checkout is actually at, or None when it cannot be asked.

    None is not a failure and must not be reported as one: a framework installed as a plugin
    rather than cloned has no history, and the pin is unverifiable there in a way that says
    nothing about whether it is being honoured. Where the pin matters -- a CI job, which gets
    the framework by checking it out -- git is there.
    """
    try:
        r = subprocess.run(["git", "-C", str(FRAMEWORK), "rev-parse", "HEAD"],
                           capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() or None if r.returncode == 0 else None


def check_framework_pin(project: dict, report: Report) -> None:
    """A repository that pins a commit, against the commit it is being checked by.

    `framework_version` answers "which rules was this written against". It does not bind:
    two machines can declare the same number and run different code, and the run that
    produced a green report cannot be reproduced from what the repository records. A project
    that wants that writes the commit down, and this is what makes writing it down mean
    something -- an unchecked pin is a comment.

    It stays optional, and silence when it is absent is the correct behaviour rather than a
    gap: pinning costs a deliberate bump for every fix, which is a price a project with one
    developer and no CI has no reason to pay yet.
    """
    pinned = project.get("framework_commit")
    if pinned is None:
        return
    if not isinstance(pinned, str) or not COMMIT.match(pinned.strip()):
        report.add("FW003", "framework.yaml",
                   f"framework_commit is {pinned!r}, which is not a commit. It takes the "
                   "hash the framework is pinned at, seven characters or more. A branch or "
                   "a tag name is not enough: both move, and a pin that moves is the state "
                   "this field exists to leave.")
        return
    pinned = pinned.strip()
    head = framework_head()
    if head is None or head.startswith(pinned):
        return
    report.add("FW003", "framework.yaml",
               f"pins the framework at {pinned}, and the framework being run is at "
               f"{head[:12]}. Either the checkout moved under this repository -- in which "
               "case the report you are reading was not produced by the rules this project "
               "declares -- or the pin was left behind by a migration. "
               "`migrate.py --adopt` writes both lines together.")


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
        for cap, row in sorted(as_map(a.meta.get("stack")).items()):
            if not isinstance(row, dict):
                continue
            status, dec = row.get("status"), row.get("decided_in")
            if status in ("chosen", "ruled-out") and not dec:
                report.add("STK001", a.rel,
                           f"{cap!r} is {status!r} and names no `decided_in`. It reads as a "
                           "decision and there is no record of one. `unratified` is for a "
                           "tool in use that nobody chose, and `dropped` for one that was "
                           "tried, is not in use, and that nobody decided against.")
            elif status == "dropped" and dec:
                # The word exists for the abandonment nobody ratified. With a decision
                # behind it the row is `ruled-out`, and calling it dropped files a decision
                # as an accident -- which is the direction that loses the reasoning.
                report.add("STK001", a.rel,
                           f"{cap!r} is `dropped` and names {dec!r}. `dropped` is what was "
                           "abandoned without anybody deciding; with a decision behind it "
                           "the row is `ruled-out`, and the reasoning stays reachable.")
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

# A region inside a document somebody else writes, rather than a file of its own. The
# markers are the boundary and they are also the permission: outside them the prose is
# untouched, and a file without them is not written to at all. `schemas/generate.py` reads
# the same shape for the catalog tables in `FRAMEWORK.md`, and the two agree on purpose --
# a second marker convention is a second thing to learn before you can trust either.
REGION = re.compile(r"(?P<open><!-- generated: (?P<name>[a-z-]+) -->\n)"
                    r".*?"
                    r"(?P<close>\n<!-- /generated -->)", re.S)

# `§1` is grouped by this and by nothing else, because it is the cost that says which entry
# to look at first. A view that reordered them would be a different file with the same
# content, and the ordering is the content.
COST_ORDER = {"high": 0, "medium": 1, "low": 2}


def binds(prod: str, row: dict, scope: str | None) -> bool:
    """Whether an open entry is one `prod` has to care about."""
    if scope is not None:
        return scope == prod
    named = as_list(row.get("products"))
    # Silence still binds every product, and `REG011` reports it rather than this changing
    # its meaning: a repository written before the reserved word means what it meant, and a
    # composition rule that changes under a document nobody edited is the one kind of
    # migration that cannot be reviewed.
    return ALL_PRODUCTS in named or prod in named or not named


def build_regions(root: Path, arts: list[Artifact]) -> dict[Path, dict[str, str]]:
    """The generated regions, by the file that holds them and the name of the region.

    One region so far. The register at the root gathers every other one under a heading per
    product, because three registers ordered by cost to reverse do not compose into one
    ordered list and nothing else composes them: without this view there is no such thing
    as "the most expensive decision still open", there are three of them and nothing says
    which comes first. It is a view and not a register -- no `entries:`, no second copy of
    a row for a check to report twice -- and every line names the file that owns it.
    """
    opens = [a for a in arts if a.type == "open-register"]
    target = root / "OPEN.md"
    if not any(a.path == target for a in opens):
        return {}

    dirs = product_dirs(arts)
    rows = [(od, row, dirs.get(a.path.parent, (None, None))[0], a.rel)
            for a in opens
            for od, row in as_map(a.meta.get("entries")).items()
            if isinstance(row, dict) and row.get("status") == "open"]

    def cell(v) -> str:
        # An absent field reads as an em dash and never as `None`. A table saying a
        # trigger is `None` is a table nobody trusts the rest of.
        v = " ".join(str(v).split()).replace("|", "\\|") if v is not None else ""
        return (v[:57] + "...") if len(v) > 60 else (v or "—")

    def table(sel) -> list[str]:
        chosen = sorted((r for r in rows if sel(r)),
                        key=lambda r: (COST_ORDER.get(r[1].get("cost_to_reverse"), 3), r[0]))
        if not chosen:
            return ["Nothing open.", ""]
        out = ["| Entry | Cost to reverse | Default in force | Trigger | Register |",
               "|---|---|---|---|---|"]
        out += [f"| `{od}` | {cell(row.get('cost_to_reverse'))} "
                f"| {cell(row.get('default_in_force'))} | {cell(row.get('trigger'))} "
                f"| [`{rel}`]({rel}) |" for od, row, _, rel in chosen]
        return out + [""]

    # `all` is a word, not a product. It was reaching this set through the entries that
    # name it, and the generator emitted `## all` -- a heading for a product no repository
    # has. `binds` knew better and this did not, which is what happens when one rule is
    # written in two places.
    products = sorted(({scope for _, _, scope, _ in rows if scope} |
                       {p for _, row, scope, _ in rows if not scope
                        for p in as_list(row.get("products"))} |
                       {p for p, _ in dirs.values()}) - {ALL_PRODUCTS})

    lines = [f"*{GENERATED_MARK}. Edit the register named in the last column, never this "
             "table: the next run overwrites whatever is between the markers.*", "",
             "One heading per product, holding **everything that binds it** wherever it is "
             "filed — its own register, the substrate's, and the entries below that name "
             "no product in particular. A shared entry appears under every product it "
             "binds, once per product, and the last column says which single file owns it. "
             "Ordered by cost to reverse, which is the order they have to be decided in.",
             ""]
    for p in products:
        lines += [f"## {p}", ""] + table(lambda r, p=p: binds(p, r[1], r[2]))
    lines += ["## Bound to no single product", "",
              "The substrate, and everything above the products: they appear under every "
              "heading above as well, and this is where they are counted once.", ""]
    # WHAT THIS SECTION IS FOR, AND THE STATE IT USED TO READ. It held the entries that
    # named no product, and `REG011` exists to get rid of exactly that silence: the more a
    # repository answers the new check, the emptier this got, until the section that holds
    # what binds everything said "Nothing open" in a repository where twenty entries bind
    # everything. `[all]` is the answer those entries now give, and it belongs here -- which
    # is what the sentence above it has always described.
    lines += table(lambda r: r[2] is None
                   and (not as_list(r[1].get("products"))
                        or ALL_PRODUCTS in as_list(r[1].get("products"))))
    return {target: {"open-union": "\n".join(lines).rstrip()}}


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
    # Scoped per product, and the scope comes from two places because the registers do.
    # An entry in `products/<p>/OPEN.md` is about `p` by virtue of sitting there, and the
    # `products:` field is left off: reading only the field put every entry of every
    # product's register into every product's view. Elsewhere -- the root, the substrate --
    # the field is what says who is bound, and naming nobody means all of them, which is
    # the common case: "do these products share a substrate" belongs to every one of them.
    dirs = product_dirs(arts)
    open_entries = [(od, row, dirs.get(a.path.parent, (None, None))[0])
                    for a in arts if a.type == "open-register"
                    for od, row in as_map(a.meta.get("entries")).items()
                    if isinstance(row, dict) and row.get("status") == "open"]

    for man in (a for a in arts if a.type == "product-manifest"):
        prod = next(iter(as_list(man.meta.get("products"))), None)
        if not prod:
            continue
        open_now = sorted(od for od, row, scope in open_entries
                          if binds(prod, row, scope))
        mine = [a for a in arts if prod in as_list(a.meta.get("products"))]
        unregistered = sorted(a.id for a in mine if a.type == "decision-record" and a.id
                              and a.meta.get("status") != "superseded"
                              and UNREGISTERED in as_list(a.meta.get("leaves_open")))
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
                 # WHO ELSE READS THIS STATE. `leaves_open: [unregistered]` says a decision
                 # left something open that has no entry, and an open question with no entry
                 # cannot appear in a view built from registers -- which is precisely the
                 # complaint that produced the state: a question nobody counts. So the
                 # derived view carries the decisions that declare one, and "what is open
                 # for this product" stops meaning "what is open and already written down".
                 "open_unregistered: [" + ", ".join(unregistered) + "]",
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
    # The pull request context. Supplied by CI, absent everywhere else, and the `PR*`
    # checks stay quiet without it: see check_pull_request.
    ap.add_argument("--pr-text",
                    help="the pull request's title and body, for the CHG it cites")
    ap.add_argument("--pr-text-file", type=Path,
                    help="the same, read from a file. `-` reads standard input")
    ap.add_argument("--changed-files", type=Path,
                    help="a file of paths the change set touches, one per line, relative "
                         "to --root. `-` reads standard input")
    args = ap.parse_args()

    root = args.root.resolve()
    # The skill has said for as long as it has existed that "running it against the wrong
    # directory produces a clean report, and a clean report on the wrong repository is worse
    # than an error". Nothing enforced it: pointed at a path that is not there, the
    # validator scanned nothing, reported that the repository does not declare a framework
    # version, and exited 0. Every one of those sentences was true and the conclusion a
    # reader draws from them -- this repository is fine -- was not.
    if not root.is_dir():
        sys.exit(f"{root}: no such directory. `--root` is the project being checked, not "
                 "the framework and not a file.")
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    project = load_project(root)
    config, stale_days = load_config(project)
    scan = load_scan(registry, project)
    if args.stale_days is not None:
        stale_days = args.stale_days

    def read(arg: Path | None) -> str | None:
        if arg is None:
            return None
        return sys.stdin.read() if str(arg) == "-" else arg.read_text(encoding="utf-8")

    pr_text = args.pr_text if args.pr_text is not None else read(args.pr_text_file)
    lines = read(args.changed_files)
    # Relative to `--root`, and normalised the two ways a diff writes them: `./` from find,
    # backslashes from a Windows checkout. A path that does not match an artifact is code,
    # and code is not what this reads.
    changed_files = None if lines is None else {
        l.strip().replace("\\", "/").removeprefix("./")
        for l in lines.splitlines() if l.strip()}

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
    check_pull_request(arts, pr_text, changed_files, report)
    check_framework_version(root, project, registry, report)
    check_framework_pin(project, report)
    check_open_register(arts, report)
    check_manifest_derived_fields(arts, report)
    check_review_batches(arts, report)
    check_glossary_terms(arts, report)
    check_decisions_leave_open(arts, report)
    check_commitments_and_risks(arts, report)
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

        # Regions, not files. There is no refusal to make here and no `hand_maintained`
        # list: the markers are the opt in, and a document without them is left exactly as
        # it is. That asymmetry with the files above is the point -- a whole generated file
        # exists because a generator made it, and a region exists because somebody wrote
        # the two markers into a document that is theirs.
        for path, regions in build_regions(root, arts).items():
            if not path.exists():
                continue
            current = path.read_text(encoding="utf-8")
            if not REGION.search(current):
                continue
            rewritten = REGION.sub(
                lambda m: (m.group("open") + regions[m.group("name")] + m.group("close"))
                if m.group("name") in regions else m.group(0), current)
            if rewritten == current:
                continue
            rel = str(path.relative_to(root))
            if args.check:
                index_stale.append(rel)
            else:
                path.write_text(rewritten, encoding="utf-8")
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
