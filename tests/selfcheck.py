#!/usr/bin/env python3
"""
The framework checked against itself.

    python tests/selfcheck.py

The validator skips `templates/` and `schemas/`, for good reasons written down in the
registry, and the cost of that is real: nothing was checking the templates that everything
else is validated against, which is how `RLM.yaml` went without `status` and `owners`
without anybody noticing. This file is what closes that hole. It runs in CI.

No pytest: one dependency fewer, and the output is meant to be read by a person who has
just broken something.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = yaml.safe_load((ROOT / "schemas" / "artifact-types.yaml").read_text())
CHECKS = yaml.safe_load((ROOT / "skills" / "audit" / "checks.yaml").read_text())
VALIDATE = ROOT / "skills" / "audit" / "scripts" / "validate.py"
GENERATE = ROOT / "schemas" / "generate.py"

SECTION_MARK = re.compile(r"<!--\s*section:\s*([a-z0-9-]+)\s*-->")
PLACEHOLDERS = set(REGISTRY["placeholders"]["enforced"])


def _load(path: Path, name: str):
    """Import the validator so its constants are read, never restated here."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    # Registered before it runs: @dataclass resolves annotations through sys.modules, and
    # without this the import dies on the first decorated class.
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


GENERATED_MARK = _load(VALIDATE, "validate").GENERATED_MARK

failures: list[str] = []


def check(name: str):
    """Decorator that runs a check and records what it said."""
    def wrap(fn):
        problems = fn() or []
        mark = "ok  " if not problems else "FAIL"
        print(f"{mark} {name}")
        for p in problems:
            print(f"       {p}")
            failures.append(f"{name}: {p}")
        return fn
    return wrap


def jsonify(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    if isinstance(o, dict):
        return {k: jsonify(v) for k, v in o.items()}
    if isinstance(o, list):
        return [jsonify(v) for v in o]
    return o


def front_matter(text: str) -> dict:
    if text.startswith("---\n"):
        return yaml.safe_load(text[4:text.find("\n---", 4)])
    return yaml.safe_load(text)


def templates() -> dict[str, Path]:
    out = {}
    for p in sorted((ROOT / "templates").iterdir()):
        if p.suffix not in (".md", ".yaml") or p.name == "README.md":
            continue
        m = re.search(r"^artifact_type: (\S+)", p.read_text(), re.M)
        if m:
            out[m.group(1)] = p
    return out


TPL = templates()


# ─────────────────────────────────────────────────────────────────────────────

@check("the generated schemas match the registry")
def _schemas_fresh():
    r = subprocess.run([sys.executable, str(GENERATE), "--check"],
                       capture_output=True, text=True)
    return [] if r.returncode == 0 else [l for l in r.stdout.splitlines() if l.strip()]


@check("every type has a template and every template has a type")
def _types_match():
    reg, tpl = set(REGISTRY["types"]), set(TPL)
    return ([f"{t}: in the registry, no template" for t in sorted(reg - tpl)]
            + [f"{t}: has a template, not in the registry" for t in sorted(tpl - reg)])


@check("every template validates against its own schema")
def _templates_validate():
    problems = []
    for t, p in TPL.items():
        schema = json.loads((ROOT / "schemas" / "framework" / t / "v1.json").read_text())
        for e in Draft202012Validator(schema).iter_errors(jsonify(front_matter(p.read_text()))):
            # A template is allowed to fail on exactly one thing: carrying its own
            # placeholder in a field that must be filled in. That is what a template is.
            # Anything else means the template contradicts the registry.
            if any(ph in str(e.message) for ph in PLACEHOLDERS):
                continue
            where = "/".join(map(str, e.path)) or "front matter"
            problems.append(f"{p.name}: {where}: {e.message}")
    return problems


@check("every mandatory section has exactly one marker, above a heading")
def _markers():
    problems = []
    for t, spec in REGISTRY["types"].items():
        wanted = spec.get("sections") or []
        body = TPL[t].read_text() if wanted else ""
        found = SECTION_MARK.findall(TPL[t].read_text())
        if not wanted and found:
            problems.append(f"{TPL[t].name}: has markers, the registry declares no sections")
            continue
        for sid in wanted:
            n = found.count(sid)
            if n != 1:
                problems.append(f"{TPL[t].name}: marker {sid!r} appears {n} times")
                continue
            following = body.split(f"<!-- section: {sid} -->\n", 1)[1].splitlines()[0]
            if not following.startswith("#"):
                problems.append(f"{TPL[t].name}: {sid!r} does not sit above a heading")
        for extra in set(found) - set(wanted):
            problems.append(f"{TPL[t].name}: marker {extra!r} is not in the registry")
    return problems


@check("every check the validator emits is in the catalog, and the reverse")
def _catalog_matches_code():
    emitted = set(re.findall(r'report\.add\(\s*"([A-Z]{2,3}\d{3})"', VALIDATE.read_text()))
    catalogued = set(CHECKS["checks"])
    off = {c for c, s in CHECKS["checks"].items()
           if s.get("level") in ("off", False)}

    problems = [f"{c}: emitted by the validator, absent from checks.yaml"
                for c in sorted(emitted - catalogued)]
    # A catalogued check that nothing emits is a promise the validator does not keep,
    # unless it is switched off and says why.
    for c in sorted(catalogued - emitted - off):
        problems.append(f"{c}: in checks.yaml, never emitted, and not switched off")
    for c in sorted((catalogued - emitted) & off):
        if not CHECKS["checks"][c].get("blocked_by"):
            problems.append(f"{c}: off and unimplemented, with no `blocked_by` saying why")
    return problems


@check("every artifact is listed by the phase FRAMEWORK.md §5 says produces it")
def _phases_agree():
    # §5 tells the lifecycle as a narrative, §7 tabulates `born_in` per artifact, and the
    # mermaid draws it. Three tellings of one fact, and they had already drifted: `RSK`,
    # `RMP` and `LOG` were each born in a phase whose row did not mention them.
    #
    # The assertion runs one way only, §5 must contain what §7 says is born there, and
    # never the reverse: `WF` legitimately appears in two rows because its sections are
    # written at different times, and `EVR` appears under F6 although it is born at the
    # release gate. A diagram composes, a normative table enumerates, so the mermaid is
    # not asserted here either.
    fw = (ROOT / "FRAMEWORK.md").read_text()
    rows = dict(re.findall(r"\| \*\*(F\d) · [^|]*\*\* \| ([^|]+) \|", fw))
    problems = []
    for phase, cell in rows.items():
        listed = set(re.findall(r"`([A-Za-z.]+)(?:\s+§\w+)?`", cell))
        for spec in REGISTRY["types"].values():
            if spec.get("born_in") == phase and spec["id"] not in listed:
                problems.append(f"§5 {phase} does not list {spec['id']}, which §7 says is "
                                f"born there")
    if not rows:
        problems.append("no phase rows found in §5: the check is not running")
    return problems


@check("every skill only names checks, flags and files that exist")
def _skill_references():
    # Runs over every skill, not just the one that owns the validator. A skill is prose
    # that an agent executes, and prose naming a flag the validator does not accept fails
    # at the moment somebody is trusting it. The three things checked here are the ones
    # that go stale silently: the name that has to match the directory or the skill never
    # resolves, a check code that was renamed, and a flag that never existed.
    known_flags = set(re.findall(r'"(--[a-z-]+)"', VALIDATE.read_text()))
    problems = []

    skills = sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").exists())
    if not skills:
        return ["no skills found under skills/: the check is not running"]

    for d in skills:
        skill = d / "SKILL.md"
        text = skill.read_text()
        head = (yaml.safe_load(text[4:text.find("\n---", 4)])
                if text.startswith("---\n") else {})
        if head.get("name") != d.name:
            problems.append(f"{d.name}: name is {head.get('name')!r}, the directory is "
                            f"{d.name!r}: the skill will not resolve")
        if not head.get("description"):
            problems.append(f"{d.name}: no description, so it never triggers")

        body = text[text.find("\n---", 4):]
        for code in sorted(set(re.findall(r"`([A-Z]{2,3}\d{3})`", body))):
            if code not in CHECKS["checks"]:
                problems.append(f"{d.name}: names {code}, which is not in the catalog")
        for flag in sorted(set(re.findall(r"`(--[a-z-]+)`", body))):
            if flag not in known_flags:
                problems.append(f"{d.name}: names {flag}, which the validator does not "
                                "accept")
        # A skill that points at a reference or a script it does not carry is a skill that
        # stops halfway through, at the point where the agent goes looking for the file.
        for ref in sorted(set(re.findall(r"`((?:references|scripts)/[\w./-]+)`", body))):
            if not (d / ref).exists() and not (ROOT / ref).exists():
                problems.append(f"{d.name}: points at {ref}, which does not exist")
    return problems


@check("the validator reports nothing on a minimal correct repository")
def _clean_repo():
    fm = lambda **kw: "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"
    files = {
        "OPEN.md": fm(schema="framework/open-register/v1", artifact_type="open-register",
                      lifecycle="living", status="active", owners="[owner]",
                      created="2026-01-01", last_review="2026-01-01 09:00") + "# Open\n",
        "decisions/DEC-001-slug.md": fm(
            schema="framework/decision-record/v1", artifact_type="decision-record",
            id="DEC-001", lifecycle="immutable", status="accepted", scope="architecture",
            products="[alpha]", owners="[owner]", created="2026-01-01") + "# DEC-001\n",
        "products/alpha/PBR.md": fm(
            schema="framework/product-brief/v1", artifact_type="product-brief",
            lifecycle="living", status="active", products="[alpha]", owners="[owner]",
            created="2026-01-01", last_review="2026-01-01 09:00") + "# Brief\n",
    }
    with tempfile.TemporaryDirectory() as tmp:
        for rel, text in files.items():
            p = Path(tmp) / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        r = subprocess.run(
            [sys.executable, str(VALIDATE), "--root", tmp, "--json", "--stale-days", "36500"],
            capture_output=True, text=True)
        if r.returncode not in (0, 1):
            return [f"the validator crashed: {r.stderr.strip().splitlines()[-1]}"]
        out = json.loads(r.stdout)
        return [f"{f['code']} {f['path']}: {f['message']}" for f in out["findings"]]


@check("--emit-index refuses to overwrite an index somebody maintains by hand")
def _emit_index_refuses():
    # `--emit-index` writes only what front matter can express, and the reason a project
    # keeps one of these files by hand is always the part it cannot: a column for why a
    # decision still matters, a row for where a source system enters the chain. The skill
    # used to list this under "apply without asking", which is how an agent deletes that
    # content while believing it is tidying up. The marker is the permission to overwrite.
    fm = lambda **kw: "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"
    dec = fm(schema="framework/decision-record/v1", artifact_type="decision-record",
             id="DEC-001", lifecycle="immutable", status="accepted", scope="architecture",
             products="[alpha]", owners="[owner]", created="2026-01-01") + "# DEC-001\n"
    by_hand = "# Decision index\n\nHand maintained.\n\n| ID | Why it still matters |\n"
    problems = []

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "decisions").mkdir(parents=True)
        (root / "decisions" / "DEC-001-slug.md").write_text(dec)
        index = root / "decisions" / "INDEX.md"
        index.write_text(by_hand)

        run = lambda *extra: subprocess.run(
            [sys.executable, str(VALIDATE), "--root", str(root), "--json",
             "--emit-index", "--stale-days", "36500", *extra],
            capture_output=True, text=True)

        r = run()
        if index.read_text() != by_hand:
            problems.append("--emit-index overwrote a hand maintained decisions/INDEX.md")
        if r.returncode == 0:
            problems.append("--emit-index refused the write and still exited 0: a caller "
                            "cannot tell the file was not regenerated")
        if r.returncode in (0, 1):
            rel = "decisions/INDEX.md"
            if rel not in json.loads(r.stdout).get("hand_maintained", []):
                problems.append(f"{rel} was not reported under hand_maintained")

        # --check must not call it out of date: that wording is an instruction to run the
        # overwrite, which is the thing being prevented.
        c = run("--check")
        if c.returncode in (0, 1):
            out = json.loads(c.stdout)
            if "decisions/INDEX.md" in out.get("out_of_date", []):
                problems.append("--emit-index --check reports a hand maintained index as "
                                "out of date, which points the reader at the overwrite")

        # The marker is what grants permission, so a generated file still regenerates.
        index.write_text(GENERATED_MARK + "\nstale\n")
        run()
        if GENERATED_MARK not in index.read_text() or "stale" in index.read_text():
            problems.append("a marked index was not regenerated: the guard is too wide")

    return problems


@check("a register vouches for the identifiers it declares, not the ones it mentions")
def _inline_ids_are_scoped():
    # Both directions, because this check exists to hold a line between them. A register
    # has to vouch for its own entries or every OD reference reads as dangling; it must not
    # vouch for the identifiers it merely cites, or REF001 is cleared by writing a sentence
    # about the missing document, which is precisely what the skill tells you to do.
    fm = lambda **kw: "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"
    dec = lambda i, **extra: fm(
        schema="framework/decision-record/v1", artifact_type="decision-record", id=i,
        lifecycle="immutable", status="accepted", scope="architecture",
        products="[alpha]", owners="[owner]", created="2026-01-01", **extra) + f"# {i}\n"

    files = {
        # Declares OD-001 and KI-001; cites DEC-999, which it does not own.
        "OPEN.md": fm(schema="framework/open-register/v1", artifact_type="open-register",
                      lifecycle="living", status="active", owners="[owner]",
                      created="2026-01-01", last_review="2026-01-01 09:00")
        + "# Open\n\n- OD-001 - where the landing zone goes\n- KI-001 - nightly job is "
          "flaky\n\nDEC-999 was never written, and this sentence must not make it exist.\n",
        # Resolves against an entry inside the register: this is the case the loose rule
        # was there to serve, and it has to keep working.
        "decisions/DEC-001-slug.md": dec("DEC-001", derives_from="OD-001"),
        # Resolves against nothing at all.
        "decisions/DEC-002-slug.md": dec("DEC-002", derives_from="DEC-999"),
    }

    with tempfile.TemporaryDirectory() as tmp:
        for rel, text in files.items():
            p = Path(tmp) / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        r = subprocess.run(
            [sys.executable, str(VALIDATE), "--root", tmp, "--json",
             "--stale-days", "36500"], capture_output=True, text=True)
        if r.returncode not in (0, 1):
            return [f"the validator crashed: {r.stderr.strip().splitlines()[-1]}"]
        ref001 = {f["path"] for f in json.loads(r.stdout)["findings"]
                  if f["code"] == "REF001"}

    problems = []
    if "decisions/DEC-001-slug.md" in ref001:
        problems.append("OD-001 is declared as an entry in OPEN.md and was still reported "
                        "dangling: the register no longer vouches for its own entries")
    if "decisions/DEC-002-slug.md" not in ref001:
        problems.append("DEC-999 exists nowhere, yet REF001 did not fire: naming it in the "
                        "prose of a register is enough to clear the finding")
    return problems


# ─────────────────────────────────────────────────────────────────────────────

print()
if failures:
    print(f"{len(failures)} problem(s).")
    sys.exit(1)
print("The framework is consistent with itself.")
