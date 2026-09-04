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

import collections
import importlib.util
import io
import json
import re
import subprocess
import sys
import tempfile
import types
import zipfile
from datetime import date, datetime
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = yaml.safe_load((ROOT / "schemas" / "artifact-types.yaml").read_text())
CHECKS = yaml.safe_load((ROOT / "skills" / "audit" / "checks.yaml").read_text())
VALIDATE = ROOT / "skills" / "audit" / "scripts" / "validate.py"
EXTRACT = ROOT / "skills" / "start" / "scripts" / "extract.py"
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
    # Every script the skills ship, not only the validator. `audit` carries two now, and a
    # union across them is the honest shape of the guard: a skill that names a flag has to
    # be naming one that something it ships accepts. What the union gives up is telling a
    # `migrate.py` flag written against `validate.py` from a correct one, which is a typo
    # this cannot see and a reader can.
    known_flags = {f for script in sorted((ROOT / "skills").rglob("scripts/*.py"))
                   for f in re.findall(r'"(--[a-z-]+)"', script.read_text())}
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
        # `entries:` is what REG002 and REG003 read. Without it the register is reported by
        # REG004, which is the point: a register they cannot read used to report clean.
        "OPEN.md": fm(schema="framework/open-register/v1", artifact_type="open-register",
                      lifecycle="living", status="active", owners="[owner]",
                      created="2026-01-01", last_review="2026-01-01 09:00",
                      entries="\n  OD-001:\n    status: open\n"
                              "    cost_to_reverse: low\n"
                              # At the root, who an entry binds has no other answer, so
                              # `REG011` asks for one. `[all]` in a repository of one
                              # product is not the same claim as naming that product: it
                              # says the entry binds whatever this repository grows.
                              "    products: [all]\n"
                              "    default_in_force: nothing is scheduled\n")
        # THE BODY CARRIES THE ID TOO, AND `REG015` IS WHY. The map holds the fields a check
        # reads and the body holds the reasoning; an entry present in one half and absent
        # from the other is half a row, and this minimal repository has to be a correct one
        # in both directions.
        + "# Open\n\n## Cost to reverse LOW\n\n### OD-001 - the one open question\n",
        "decisions/DEC-001-slug.md": fm(
            schema="framework/decision-record/v1", artifact_type="decision-record",
            id="DEC-001", lifecycle="immutable", status="accepted", scope="architecture",
            products="[alpha]", owners="[owner]", created="2026-01-01",
            leaves_open="[]") + "# DEC-001\n",
        "products/alpha/PBR.md": fm(
            schema="framework/product-brief/v1", artifact_type="product-brief",
            lifecycle="living", status="active", products="[alpha]", owners="[owner]",
            created="2026-01-01", last_review="2026-01-01 09:00") + "# Brief\n",
        # A correct repository says which framework it was written against. Read from the
        # registry rather than written as 1, so this stays true through a bump instead of
        # becoming the first thing that breaks on the day one happens.
        "framework.yaml": f"framework_version: {REGISTRY['version']}\n",
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


@check("every open entry reaches the generated view, in every shape it is allowed to declare")
def _every_entry_reaches_the_view():
    # THE GENERAL FORM OF A BUG THAT SHIPPED. `REG011` made one state illegal -- an entry at
    # the root naming no products -- and the generator's last section was selecting on
    # exactly that state, so the more a repository obeyed the check, the emptier the view
    # became. Nothing looked wrong: the register was right, the check was satisfied, and
    # `§5` said there was nothing above the products.
    #
    # So the invariant, rather than the instance: an entry that is open is in the view,
    # whatever legal shape it declares and wherever it is filed. A state added later that
    # the generator does not know about fails here, on the day it is added, instead of on
    # the day somebody finishes migrating to it.
    fm = lambda body: ("---\nschema: framework/open-register/v1\n"
                       "artifact_type: open-register\nlifecycle: living\nstatus: active\n"
                       "owners: [o]\ncreated: 2026-01-01 09:00\n"
                       "last_review: 2026-08-01 09:00\n" + body + "---\n\n# Open\n")
    man = lambda p, m: ("schema: framework/product-manifest/v1\n"
                        "artifact_type: product-manifest\nlifecycle: living\n"
                        "status: active\n"
                        f"products: [{p}]\nname: {p}\none_liner: A thing.\n"
                        "owners: [o]\ncreated: 2026-01-01 09:00\n"
                        f"last_review: 2026-01-01 09:{m}\nstage:\n  phase: F5\n  block: A\n")
    entry = lambda od, extra="": (f"  {od}:\n    status: open\n    cost_to_reverse: low\n"
                                  f"    default_in_force: nothing\n{extra}")

    # One entry per legal shape, and the shape is the point of each.
    shapes = {
        "OD-001": "declaring `[all]` at the root",
        "OD-002": "naming one product at the root",
        "OD-003": "naming no products at the root, which is legal and reported",
        "OD-004": "filed in the substrate's register",
        "OD-005": "filed in a product's own register",
    }
    files = {
        "framework.yaml": f"framework_version: {REGISTRY['version']}\n",
        "products/alpha/product.yaml": man("alpha", "10"),
        "products/beta/product.yaml": man("beta", "20"),
        "OPEN.md": fm("entries:\n"
                      + entry("OD-001", "    products: [all]\n")
                      + entry("OD-002", "    products: [beta]\n")
                      + entry("OD-003"))
        + "\n<!-- generated: open-union -->\nx\n<!-- /generated -->\n",
        "platform/OPEN.md": fm("entries:\n" + entry("OD-004")),
        "products/alpha/OPEN.md": fm("entries:\n" + entry("OD-005")),
        "products/beta/OPEN.md": fm("entries: {}\n"),
        # A decision that left something open whose entry nobody has written. It has no
        # register row by definition, so the view is the only place it can surface.
        "decisions/DEC-001-x.md": (
            "---\nschema: framework/decision-record/v1\n"
            "artifact_type: decision-record\nid: DEC-001\nlifecycle: immutable\n"
            "status: accepted\nscope: architecture\nproducts: [alpha]\nowners: [o]\n"
            "created: 2026-01-01 09:00\nleaves_open: [unregistered]\n---\n\n# DEC-001\n"),
    }

    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for rel, text in files.items():
            f = root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text)
        r = subprocess.run([sys.executable, str(VALIDATE), "--root", str(root),
                            "--emit-index"], capture_output=True, text=True)
        if r.returncode not in (0, 1):
            return [f"--emit-index failed: {r.stderr.strip() or r.stdout.strip()}"]

        union = (root / "OPEN.md").read_text()
        region = union.split("<!-- generated: open-union -->", 1)[-1]
        for od, why in sorted(shapes.items()):
            if od not in region:
                problems.append(f"{od}, {why}, does not appear anywhere in the generated "
                                "union. An entry that is open and invisible in the view is "
                                "the failure this view exists to prevent, and it reads as "
                                "nothing being open")

        # And the two the union has to keep apart, or the section stops meaning anything.
        tail = region.split("## Bound to no single product", 1)
        if len(tail) != 2:
            problems.append("the union has no section for what binds no single product")
        else:
            for od, want in (("OD-001", True), ("OD-003", True), ("OD-004", True),
                             ("OD-002", False), ("OD-005", False)):
                if (od in tail[1]) != want:
                    problems.append(
                        f"{od} is {'missing from' if want else 'listed under'} what binds no "
                        "single product, and it is the opposite of what it declares")

        # WHO ELSE READS THIS STATE -- the question the catalog now tells you to ask before
        # adding a check. A question with no entry cannot appear in a view built from
        # registers, so the view names the decision that declares one.
        r = subprocess.run([sys.executable, str(VALIDATE), "--root", str(root),
                            "--emit-index"], capture_output=True, text=True)
        idx = (root / "products" / "alpha" / "product.index.yaml")
        if idx.exists() and "open_unregistered: [DEC-001]" not in idx.read_text():
            problems.append("the derived view does not name the decision that declares an "
                            "unregistered open point, so 'what is open for this product' "
                            "still means 'what is open and already written down'")

        alpha = (root / "products" / "alpha" / "product.index.yaml").read_text()
        for od, want in (("OD-001", True), ("OD-003", True), ("OD-004", True),
                         ("OD-005", True), ("OD-002", False)):
            if (od in alpha) != want:
                problems.append(
                    f"alpha's derived view {'is missing' if want else 'holds'} {od}, which "
                    "is the opposite of what that entry binds")
    return problems


@check("the vocabularies have a value for the day the question is first asked")
def _vocabularies_cover_not_yet():
    # Three enums were extended on the same day and the omissions were all on one axis: the
    # answer on the day nobody has done the work yet. A vocabulary without it makes omission
    # the honest move, and an omitted field is invisible -- a risk with no likelihood drops
    # out of every ordering, a promise with no feasibility reads as unexamined rather than
    # unexaminable. This asserts the values exist, so removing one is a decision somebody
    # takes rather than a line somebody deletes.
    want = {
        ("risk-register", "risks", "category"): {"security", "organisational"},
        ("risk-register", "risks", "likelihood"): {"C"},
        ("commitments", "commitments", "feasibility"): {"not-yet-assessable",
                                                        "not-applicable"},
        ("open-register", "entries", "status"): {"parked"},
        ("operational-stack", "stack", "status"): {"dropped"},
    }
    problems = []
    for (type_name, field, key), values in sorted(want.items()):
        spec = REGISTRY["types"].get(type_name, {})
        enums = ((spec.get("maps") or {}).get(field, {}).get("fields", {}).get("enums") or {})
        have = set(enums.get(key) or [])
        missing = values - have
        if missing:
            problems.append(
                f"{type_name}.{field}.{key} has no {', '.join(sorted(missing))}. Every one of "
                "these is the answer on the day the question is first asked -- not decided, "
                "not measurable, not applicable, already true -- and a vocabulary without it "
                "leaves two moves: omit the field, which takes the row out of everything "
                "that reads it, or pick the nearest value, which writes something false that "
                "nothing will contradict")
    return problems


@check("a promise and the risk it creates can be joined, now that both are readable")
def _commitments_and_risks():
    # Two markdown tables until 2.1.0, which is why neither of these could be reported: a
    # product carrying commitments and no risk register at all, and a commercial risk about
    # a claim the commitments register does not contain. A check cannot join two tables it
    # cannot read, and the fix was the same one `OPEN.md` and `STACK.md` already had.
    fm = lambda **kw: "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"

    def repo(cmts: str, risks: str | None) -> dict:
        files = {
            "framework.yaml": f"framework_version: {REGISTRY['version']}\n",
            "products/alpha/product.yaml": (
                "schema: framework/product-manifest/v1\n"
                "artifact_type: product-manifest\nlifecycle: living\nstatus: active\n"
                "products: [alpha]\nname: alpha\none_liner: A thing.\nowners: [o]\n"
                "created: 2026-01-01 09:00\nlast_review: 2026-01-01 09:00\n"
                "stage:\n  phase: F5\n  block: A\n"),
            "COMMITMENTS.md": fm(schema="framework/commitments/v1",
                                 artifact_type="commitments", lifecycle="living",
                                 status="active", owners="[o]", products="[alpha]",
                                 created="2026-01-01 09:00",
                                 last_review="2026-08-01 09:00",
                                 commitments=cmts) + "# Commitments\n",
        }
        if risks is not None:
            files["products/alpha/RSK.md"] = fm(
                schema="framework/risk-register/v1", artifact_type="risk-register",
                lifecycle="living", status="active", products="[alpha]", owners="[o]",
                created="2026-01-01 09:00", last_review="2026-08-01 09:30",
                risks=risks) + ("# Risks\n\n<!-- section: state -->\n## State\n\n"
                                "<!-- section: acceptances -->\n## Acceptances\n\n"
                                "<!-- section: events -->\n## Events\n")
        return files

    one = ("\n  CMT-001:\n    to: a customer\n    status: open\n"
           "    products: [alpha]\n")
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        def codes(files) -> set[str]:
            for stale in root.rglob("*.md"):
                stale.unlink()
            for rel, text in files.items():
                f = root / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(text)
            r = subprocess.run([sys.executable, str(VALIDATE), "--root", str(root),
                                "--json"], capture_output=True, text=True)
            return {f["code"] for f in json.loads(r.stdout)["findings"]}

        if "XP005" not in codes(repo(one, None)):
            problems.append("a product carrying a commitment and no risk register was not "
                            "reported: the exposure lives only in the sentence that made it")
        if "XP005" in codes(repo(one, "\n  RSK-001:\n    category: technical\n"
                                      "    state: open\n")):
            problems.append("a product with a risk register was reported, so the check is "
                            "asking for something other than the register")

        # A PROMISE NOBODY HAS RECEIVED IS NOT AN EXPOSURE. Counting it put a number in the
        # finding that did not survive being checked, and a reader who verifies one row and
        # finds it was never said to anybody stops believing the rest.
        withheld = ("\n  CMT-002:\n    to: nobody yet, it is in the deck\n"
                    "    status: not-yet-issued\n    products: [alpha]\n")
        if "XP005" in codes(repo(withheld, None)):
            problems.append("a product whose only commitment is `not-yet-issued` was "
                            "reported: nothing has been said to anybody, so there is no "
                            "exposure for a risk register to hold")
        def findings(files, code):
            codes(files)
            r = subprocess.run([sys.executable, str(VALIDATE), "--root", str(root),
                                "--json"], capture_output=True, text=True)
            return [f["message"] for f in json.loads(r.stdout)["findings"]
                    if f["code"] == code]

        msg = findings(repo(one + withheld, None), "XP005")
        if not msg:
            problems.append("a product with one commitment made and one not yet issued was "
                            "not reported at all")
        elif "1 commitment(s)" not in msg[0] or "CMT-002" in msg[0].split("--")[1]:
            problems.append(f"the finding counts the promise nobody has received: {msg[0]}")

        # A commitment that names nobody is paired with nothing, and the row still reads as
        # filled in. And `[all]` used to be read as a product called `all`, which no
        # repository has, so a promise about the whole suite bound nothing at all.
        nameless = "\n  CMT-003:\n    to: a customer\n    status: open\n"
        if "XP006" not in codes(repo(nameless, None)):
            problems.append("a commitment naming no products was not reported: nothing can "
                            "pair it with a risk register, a derived view or the check that "
                            "asks whether its exposure has a home")
        binds_all = ("\n  CMT-004:\n    to: everybody\n    status: open\n"
                     "    products: [all]\n")
        if "XP005" not in codes(repo(binds_all, None)):
            problems.append("a commitment declaring `[all]` bound nothing: read as a product "
                            "named `all`, a promise about the whole suite reached no product "
                            "and no check")
        if "XP005" in codes(repo(binds_all, "\n  RSK-001:\n    category: technical\n"
                                            "    state: open\n")):
            problems.append("a commitment declaring `[all]` was still reported after the one "
                            "product in the repository got a risk register")

        commercial = "\n  RSK-001:\n    category: commercial\n    state: open\n"
        if "REF006" not in codes(repo(one, commercial)):
            problems.append("a commercial risk naming no commitment was not reported: a "
                            "claim tracked as a risk and promised nowhere cannot be "
                            "renegotiated, because there is no promise to renegotiate")
        if "REF006" in codes(repo(one, commercial + "    commitment: CMT-001\n")):
            problems.append("a commercial risk naming a declared commitment was reported")
        if "REF006" not in codes(repo(one, commercial + "    commitment: CMT-404\n")):
            problems.append("a risk naming a commitment no register declares was not "
                            "reported: the promise it is about cannot be found")
        # THE CLASS THE FIRST VERSION WAS WRONG ABOUT. A commercial risk that is not about
        # a promise -- and without a way to say so, the only way to stop the check asking was
        # to file the risk under a category that was false.
        if "REF006" in codes(repo(one, commercial + "    commitment: none\n")):
            problems.append("a commercial risk declaring `commitment: none` was reported. "
                            "Not every commercial exposure is a promise, and if the honest "
                            "answer is unavailable the cheap repair is a wrong category")
        if "REF006" in codes(repo(one, "\n  RSK-001:\n    category: commercial\n"
                                       "    state: closed\n")):
            problems.append("a closed commercial risk was reported: the promise behind it "
                            "stopped mattering, and asking for it is asking about history")

        # THE PROMISE THAT CANNOT BE KEPT, AND WHO CARRIES IT UNTIL SOMEBODY SAYS SO.
        # `XP007` is the half of a carve-out: `ICG` §3 passes over a candidate that
        # contradicts a promise already written off *when a risk owns it*, so that the share
        # of commercial promises that were never buildable stops holding up every candidate
        # that touches them. With nothing reporting the rows nobody owns, that carve-out
        # would be a hole -- an unowned promise reads exactly like a live one.
        beyond = ("\n  CMT-010:\n    to: a customer\n    status: open\n"
                  "    feasibility: out-of-reach\n    products: [alpha]\n")
        owner = ("\n  RSK-001:\n    category: commercial\n    state: open\n"
                 "    commitment: CMT-010\n")
        if "XP007" not in codes(repo(beyond, "\n  RSK-001:\n    category: technical\n"
                                             "    state: open\n")):
            problems.append("a commitment out of reach that no risk names was not reported: "
                            "the renegotiation it is owed has nobody on the hook for it")
        if "XP007" in codes(repo(beyond, owner)):
            problems.append("a commitment out of reach whose exposure a risk owns was "
                            "reported: the owner is what the check asks for, and reporting "
                            "it anyway is what makes a triage stop on the same promise every "
                            "cycle")
        # A risk that is over is not an owner. Same pair `REF006` excludes, and the same
        # reason: the row stopped being about anything.
        if "XP007" not in codes(repo(beyond, owner.replace("state: open",
                                                           "state: closed"))):
            problems.append("a closed risk was read as the owner of an exposure that is "
                            "still in the register")
        # The three states where nothing is owed. `not-yet-issued` was said to nobody --
        # `XP005` already declines to count it -- and the other two are rows where the
        # conversation has happened.
        for status, why in [
            ("not-yet-issued", "the promise is in a deck nobody has received, so there is "
                               "no exposure and the remedy is an internal edit"),
            ("renegotiated", "the conversation this check asks for has already happened"),
            ("met", "the promise was kept"),
        ]:
            quiet = beyond.replace("status: open", f"status: {status}")
            if "XP007" in codes(repo(quiet, "\n  RSK-001:\n    category: technical\n"
                                            "    state: open\n")):
                problems.append(f"a `{status}` commitment out of reach was reported: {why}")
        # `unsatisfiable` is the status saying it will not be delivered, and it is the same
        # question from the other side: somebody still has to carry it until the customer
        # has been told.
        wont = beyond.replace("status: open", "status: unsatisfiable").replace(
            "    feasibility: out-of-reach\n", "")
        if "XP007" not in codes(repo(wont, "\n  RSK-001:\n    category: technical\n"
                                           "    state: open\n")):
            problems.append("an `unsatisfiable` commitment that no risk names was not "
                            "reported: the status says it will not be delivered and nobody "
                            "is answerable for having said it")
        if "XP007" in codes(repo("\n  CMT-011:\n    to: a customer\n    status: open\n"
                                 "    feasibility: feasible\n    products: [alpha]\n",
                                 "\n  RSK-001:\n    category: technical\n"
                                 "    state: open\n")):
            problems.append("a feasible commitment was reported: the check is about promises "
                            "declared beyond reach, not about promises with no risk")
    return problems


@check("a shallow framework checkout is not read as a pin that was never true")
def _shallow_checkout():
    # `actions/checkout` clones one commit by default, and the workflow this framework ships
    # checks the framework out that way. In a shallow clone almost every commit is absent, so
    # "this framework does not contain your pin" is true of nearly everything and means
    # nothing -- and it is the more confident of the two messages, which is the wrong way
    # round.
    #
    # The helpers are exercised directly against a shallow clone rather than by running the
    # validator inside it: a clone carries the committed code, and a fix asserted through one
    # cannot fail until after it is committed.
    x = _load(VALIDATE, "validate")
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        clone = Path(tmp) / "shallow"
        r = subprocess.run(["git", "clone", "--depth", "1", "-q", f"file://{ROOT}",
                            str(clone)], capture_output=True, text=True)
        if r.returncode != 0:
            return ["a shallow clone could not be made here, so the check is not running"]
        old = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD~3"],
                             capture_output=True, text=True).stdout.strip()
        real = x.FRAMEWORK
        try:
            x.FRAMEWORK = clone
            if not x.framework_is_shallow():
                problems.append("a one-commit clone was not recognised as shallow, so a pin "
                                "it cannot contain reads as a pin that was never true")
            if x.framework_has(old) is not False:
                problems.append("a commit absent from a shallow clone was reported as "
                                "present, which is the fact the message turns on")
        finally:
            x.FRAMEWORK = real
        if x.framework_is_shallow():
            problems.append("this checkout was called shallow, so the distinction collapses "
                            "the other way and a pin that is genuinely wrong stops being "
                            "reported as wrong")
        if x.framework_has(old) is not True:
            problems.append(f"{old[:12]} is in this repository's history and was reported "
                            "absent")
    return problems


@check("the suite that asks git for history is run in a checkout that has one")
def _ci_fetches_history():
    # THE RED THAT IS ABOUT THE CLONE AND NOT ABOUT THE FRAMEWORK. Two checks above ask git
    # for commits that are not HEAD, and `actions/checkout` clones one commit unless it is
    # told otherwise. The workflow was never told, so every push for a week ended in four
    # problems that could not be fixed in the repository, because they were not about it.
    # That state is worse than having no CI: a red that nobody can act on is a red nobody
    # reads, and it is where a real failure arrives unnoticed.
    #
    # Asserted here rather than left to the next person reading the workflow, because this
    # file is the thing that goes red and the workflow is the thing that has to change: the
    # two are a day apart in a directory nobody opens twice.
    wf = ROOT / ".github" / "workflows" / "framework.yml"
    if not wf.exists():
        return [".github/workflows/framework.yml is gone: this suite runs nowhere, and a "
                "suite that runs nowhere reports nothing"]
    jobs = (yaml.safe_load(wf.read_text()) or {}).get("jobs") or {}
    problems, ran = [], False
    for name, job in jobs.items():
        steps = (job or {}).get("steps") or []
        if not any("selfcheck.py" in str(s.get("run", "")) for s in steps):
            continue
        ran = True
        depths = [(s.get("with") or {}).get("fetch-depth") for s in steps
                  if str(s.get("uses", "")).startswith("actions/checkout")]
        if not depths:
            problems.append(f"{name}: runs this suite and checks nothing out")
        elif 0 not in depths:
            problems.append(f"{name}: checks out with `fetch-depth: {depths[0]!r}` and runs "
                            "a suite that asks git for commits before HEAD. One commit is "
                            "the default, `HEAD~3` is absent in a one-commit clone, and the "
                            "pin checks then report the checkout instead of the framework")
    if not ran:
        problems.append("no job in the workflow runs tests/selfcheck.py: whatever is red on "
                        "a push, it is not this file")
    return problems


@check("the pull request body reaches the check as somebody wrote it")
def _pr_body_is_not_expanded():
    # `printf '%b'` expands backslash escapes in text somebody else wrote, and `\c` truncates
    # everything after it: a body carrying one would lose the line citing the contract, and
    # the gate would report a correct pull request for not citing one.
    wf = ROOT / "ci" / "pull-request.yml"
    if not wf.exists():
        return ["ci/pull-request.yml is gone: the gate has no way to be switched on"]
    text = wf.read_text(encoding="utf-8")
    problems = []
    if "printf '%b'" in text or 'printf "%b"' in text:
        problems.append("the workflow writes the pull request body with `printf %b`, which "
                        "expands escapes in text somebody else wrote -- `\\c` truncates the "
                        "rest, and what is lost is the line naming the change contract")
    if "$PR_TEXT" in text and "env:" not in text:
        problems.append("the body reaches the shell without going through the environment: "
                        "a backtick in a description becomes a command")
    return problems


@check("a pin that was never true is told apart from a checkout that moved")
def _pin_shapes():
    # Both produce a hash that does not match, and the two need opposite responses: one is a
    # migration to read, the other is a line nobody ever verified. And git resolves an
    # uppercase hash as readily as a lowercase one, so rejecting it was a finding about
    # somebody's shift key.
    problems = []
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short=12", "HEAD"],
                          capture_output=True, text=True)
    if head.returncode != 0:
        return ["git history is not available here, so the check is not running"]
    now = head.stdout.strip()
    old = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short=12", "HEAD~3"],
                         capture_output=True, text=True).stdout.strip()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        def message(pin: str) -> str:
            (root / "framework.yaml").write_text(
                f"framework_version: {REGISTRY['version']}\nframework_commit: {pin}\n")
            r = subprocess.run([sys.executable, str(VALIDATE), "--root", str(root),
                                "--json"], capture_output=True, text=True)
            found = [f["message"] for f in json.loads(r.stdout)["findings"]
                     if f["code"] == "FW003"]
            return found[0] if found else ""

        if message(now):
            problems.append("a pin at the commit being run was reported")
        if message(now.upper()):
            problems.append("a pin written in uppercase was reported: git resolves it, and a "
                            "field that refuses what the tool accepts is a finding about a "
                            "shift key")
        moved = message(old)
        if "no such commit" in moved or not moved:
            problems.append(f"a pin at an older commit of this framework said {moved[:60]!r}: "
                            "the checkout moved, and that is a migration to read")
        never = message("deadbeefcafe")
        if "no such commit" not in never:
            problems.append("a pin at a commit this framework does not have was reported as a "
                            "checkout that moved, which sends somebody looking for a "
                            "migration that never happened")
        if not message("main"):
            problems.append("a branch name was accepted as a pin: both a branch and a tag "
                            "move, which is the state the field exists to leave")
    return problems


@check("the pull request gate reads what somebody wrote, not what the template says")
def _pr_gate_reads_assertions():
    # The template ships with `no-chg: typo in a comment` inside an HTML comment, as the
    # instruction for writing one. A pull request that keeps the template carried that line
    # into its body, matched the exemption, and turned `PR001` off -- so the gate was silent
    # by default in every repository using the template it comes with.
    #
    # Fenced blocks and quotes go with it. `git log --grep CHG-041` in a snippet is not a
    # change contract being cited, and a quoted line is somebody quoting.
    fm = lambda **kw: "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"
    template = (ROOT / "ci" / "PULL_REQUEST_TEMPLATE.md")
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "framework.yaml").write_text(f"framework_version: {REGISTRY['version']}\n")
        (root / "products" / "alpha").mkdir(parents=True)
        (root / "products" / "alpha" / "product.yaml").write_text(
            "schema: framework/product-manifest/v1\nartifact_type: product-manifest\n"
            "lifecycle: living\nstatus: active\nproducts: [alpha]\nname: alpha\n"
            "one_liner: A thing.\nowners: [o]\ncreated: 2026-01-01 09:00\n"
            "last_review: 2026-01-01 09:00\nstage:\n  phase: F5\n  block: A\n")
        empty = root / "changed.txt"
        empty.write_text("")

        def codes(pr_text: str) -> set[str]:
            r = subprocess.run([sys.executable, str(VALIDATE), "--root", str(root),
                                "--pr-text", pr_text, "--changed-files", str(empty),
                                "--json"], capture_output=True, text=True)
            return {f["code"] for f in json.loads(r.stdout)["findings"]}

        cases = [
            (template.read_text(encoding="utf-8") if template.exists() else "",
             True, "the template kept unedited, whose own comment shows how to write "
                   "`no-chg:`"),
            ("Fix a typo\n\nno-chg: prose only", False,
             "an exemption somebody wrote"),
            ("> no-chg: <reason>", True, "an exemption inside a quote"),
            ("Fix\n\n```\nno-chg: example\n```", True,
             "an exemption inside a fenced block"),
            ("Fix\n\n```bash\ngit log --grep CHG-041\n```", True,
             "a change contract named inside a fenced block"),
        ]
        for pr_text, want, what in cases:
            got = "PR001" in codes(pr_text)
            if got != want:
                problems.append(f"{what}: PR001 was {'not ' if want else ''}reported")
    return problems


@check("a malformed map is reported and does not take the run down with it")
def _malformed_maps_survive():
    # `terms: [Freshness, Tenant]` is one bracket away from two rows under `terms:`, and it
    # killed the validator: `.items()` on a list raises, the process died on the malformed
    # document, and nothing was said about everything it had not reached. `entries:` has been
    # guarded since the same thing happened to it; three maps added in one week were not,
    # because each was written by copying the line above it.
    #
    # The schema already reports the shape -- that is what `FM002` is -- so what is asserted
    # here is that the run finishes and says so.
    shapes = {
        "glossary": ("GLOSSARY.md", "terms", "[Freshness, Tenant]", ""),
        "commitments": ("COMMITMENTS.md", "commitments", "[CMT-001]", "products: [alpha]\n"),
        "risk-register": ("products/alpha/RSK.md", "risks", "[RSK-001]", "products: [alpha]\n"),
        "open-register": ("OPEN.md", "entries", "[OD-001]", ""),
        "operational-stack": ("STACK.md", "stack", "[postgres]", ""),
    }
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "framework.yaml").write_text(f"framework_version: {REGISTRY['version']}\n")
        for atype, (rel, field, value, extra) in sorted(shapes.items()):
            f = root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(f"---\nschema: framework/{atype}/v1\n"
                         f"artifact_type: {atype}\nlifecycle: living\nstatus: active\n"
                         f"owners: [o]\n{extra}created: 2026-01-01 09:00\n"
                         f"last_review: 2026-08-01 09:00\n{field}: {value}\n---\n\n# X\n")
            r = subprocess.run([sys.executable, str(VALIDATE), "--root", str(root),
                                "--json"], capture_output=True, text=True)
            if not r.stdout.strip():
                problems.append(f"{field} written as a list took the validator down: "
                                f"{(r.stderr or '').strip().splitlines()[-1:] or '(silence)'}. "
                                "Every artifact it had not reached goes unreported with it")
            elif "FM002" not in {x["code"] for x in json.loads(r.stdout)["findings"]}:
                problems.append(f"{field} written as a list was neither reported nor fatal, "
                                "so the field reads as filled in and nothing looks at it")
            f.unlink()
    return problems


@check("a citation to a term, and a decision that says what it left open, both resolve")
def _references_with_a_second_end():
    # Two pairs that had one end each. A data contract sending a reader to the glossary for
    # what a column means, and a decision declaring in its prose that something stays open:
    # both were references, and nothing resolved either of them.
    fm = lambda **kw: "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"

    def repo(terms: str, cite: str, leaves: str | None, sections: str = "") -> dict:
        dec = {"schema": "framework/decision-record/v1",
               "artifact_type": "decision-record", "id": "DEC-001",
               "lifecycle": "immutable", "status": "accepted", "scope": "architecture",
               "products": "[alpha]", "owners": "[o]", "created": "2026-01-01"}
        if leaves is not None:
            dec["leaves_open"] = leaves
        return {
            "framework.yaml": f"framework_version: {REGISTRY['version']}\n",
            "OPEN.md": fm(schema="framework/open-register/v1",
                          artifact_type="open-register", lifecycle="living",
                          status="active", owners="[o]", created="2026-01-01 09:00",
                          last_review="2026-08-01 09:00",
                          entries="\n  OD-001:\n    status: open\n"
                                  "    cost_to_reverse: low\n    products: [all]\n"
                                  "    default_in_force: nothing\n") + "# Open\n",
            "GLOSSARY.md": fm(schema="framework/glossary/v1", artifact_type="glossary",
                              lifecycle="living", status="active", owners="[o]",
                              created="2026-01-01 09:00", last_review="2026-08-01 09:10",
                              terms=terms) + "# Glossary\n\n" + sections,
            "decisions/DEC-001-slug.md": fm(**dec) + "# DEC-001\n",
            "products/alpha/contracts/DC-001-x.md": fm(
                schema="framework/data-contract/v1", artifact_type="data-contract",
                id="DC-001", lifecycle="living", status="active", products="[alpha]",
                consumers="[alpha]", owners="[o]", created="2026-01-01 09:00",
                last_review="2026-08-01 09:20") + f"# DC-001\n\n{cite}\n",
        }

    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        def codes(files) -> set[str]:
            for stale in root.rglob("*.md"):
                stale.unlink()
            for rel, text in files.items():
                f = root / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(text)
            r = subprocess.run([sys.executable, str(VALIDATE), "--root", str(root),
                                "--json"], capture_output=True, text=True)
            return {f["code"] for f in json.loads(r.stdout)["findings"]}

        defined = "\n  Freshness:\n    kind: metric\n"
        blocked = "\n  Freshness:\n    kind: metric\n    blocked_by: OD-001\n"
        stale_block = "\n  Freshness:\n    kind: metric\n    blocked_by: OD-404\n"

        if "REF005" not in codes(repo(defined, "`GLOSSARY §Tenant` is the unit", "[]")):
            problems.append("a citation to a term no glossary declares was not reported: it "
                            "reads as defined, and the reader stops looking")
        # A CITATION IN A TABLE CELL, and one that points at a section of the glossary
        # rather than a term. The first ran to the end of the row and produced a finding
        # naming a string with a pipe in it; the second is the one form of reference that
        # cannot be wrong, and it resolved to no term by construction.
        if "REF005" in codes(repo(defined,
                                  "| field | `GLOSSARY §Freshness` | routed |", "[]")):
            problems.append("a citation inside a table cell was reported: the match ran past "
                            "the cell and the term it names is not what the document wrote")
        # A section of the glossary, which is a reference that resolves by construction --
        # and the section sign is what makes it one. Without requiring it, the exemption
        # covered every heading in the file and handed back the hole `terms:` was added to
        # close: a word defined only as `### Freshness` in the body resolved a citation.
        if "REF005" in codes(repo(defined, "see `GLOSSARY §Domain terms`", "[]",
                                  sections="## §Domain terms\n")):
            problems.append("a citation naming a section of the glossary was reported: "
                            "pointing a reader at one is a reference that resolves by "
                            "construction, and a check that only knows terms reports the one "
                            "form that cannot be wrong")
        if "REF005" not in codes(repo(defined, "see `GLOSSARY §Tenant`", "[]",
                                      sections="### Tenant\n")):
            problems.append("a term written only as a heading in the glossary body resolved "
                            "a citation. That is resolving against prose headings, which is "
                            "what `terms:` exists to stop -- two checks here went quiet for "
                            "it once already")

        if "REF005" in codes(repo(defined, "`GLOSSARY §Freshness` is the unit", "[]")):
            problems.append("a citation to a declared term was reported, so the field cannot "
                            "be answered")
        if "REF005" in codes(repo(blocked, "`GLOSSARY §Freshness` is the unit", "[]")):
            problems.append("a citation to a term declared blocked by an open entry was "
                            "reported: the gap is written down, which is the difference "
                            "between a word waiting on a decision and a word nobody defined")
        # `kind` unless `blocked_by`. A term can be blocked precisely because nobody knows
        # yet whether it is a metric or a domain concept, and requiring `kind` there makes
        # the writer choose the thing `blocked_by` exists to avoid choosing.
        bare_block = "\n  Freshness:\n    blocked_by: OD-001\n"
        if "FM002" in codes(repo(bare_block, "# nothing cited here", "[]")):
            problems.append("a term declaring only `blocked_by` was rejected by the schema: "
                            "the word is used, is not defined, and what kind of thing it is "
                            "may be part of what the decision has to settle")
        if "FM002" not in codes(repo("\n  Freshness: {}\n", "# nothing cited here", "[]")):
            problems.append("a term declaring neither `kind` nor `blocked_by` was accepted, "
                            "so an empty row passes as a definition")

        if "REF005" not in codes(repo(stale_block, "# nothing cited here", "[]")):
            problems.append("a term blocked by an entry no register declares was not "
                            "reported, so the reason the word has no definition points at "
                            "nothing")

        if "REG012" not in codes(repo(defined, "# nothing cited here", None)):
            problems.append("a decision saying nothing about what it leaves open was not "
                            "reported: `[]` is a statement and silence is a gap")
        if "REG012" in codes(repo(defined, "# nothing cited here", "[]")):
            problems.append("a decision declaring `leaves_open: []` was reported, so there "
                            "is no way to say a decision settled everything it touched")
        if "REG012" in codes(repo(defined, "# nothing cited here", "[OD-001]")):
            problems.append("a decision naming an entry a register declares was reported")
        # THE THIRD STATE. A decision that left something open whose entry nobody has
        # written is neither a list nor a silence, and written as a silence it produced the
        # finding for "nobody looked" on a decision where somebody had looked and said so.
        if "REG014" not in codes(repo(defined, "# nothing cited here", "[unregistered]")):
            problems.append("a decision declaring `[unregistered]` was not reported: the "
                            "debt is acknowledged and the question is still one nobody can "
                            "find, rank or count")
        if "REG012" in codes(repo(defined, "# nothing cited here", "[unregistered]")):
            problems.append("`unregistered` was resolved as an entry id, so the reserved "
                            "word reads as a dangling reference and the two states collapse "
                            "back into one")
        both = codes(repo(defined, "# nothing cited here", "[OD-001, unregistered]"))
        if "REG014" not in both or "REG012" in both:
            problems.append("a decision naming a real entry and an unregistered one was not "
                            "reported as the second and only the second: the ids it does "
                            "know are not the part that is missing")

        if "REG012" not in codes(repo(defined, "# nothing cited here", "[OD-404]")):
            problems.append("a decision leaving an entry open that no register declares was "
                            "not reported: the open half of a decision is only open if "
                            "somebody can find it")
    return problems


@check("a review of six documents in one minute is reported, and a day one set is not")
def _review_batches():
    # `last_review` attests a reading, and no check can verify one. What a check can see is
    # the shape the false version takes, and it took it in a real repository: six living
    # documents stamped with the same minute by a run, one of them carrying a notice at the
    # top saying it still had to be reread in full. Both directions are asserted here,
    # because the false positive is what would get this switched off -- `start` writes a
    # whole day one set in one session and every document is born attesting itself.
    fm = lambda **kw: "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"

    def repo(n: int, review, created="2026-01-01 09:00") -> dict:
        out = {"framework.yaml": f"framework_version: {REGISTRY['version']}\n"}
        for i in range(n):
            out[f"products/p{i}/PBR.md"] = fm(
                schema="framework/product-brief/v1", artifact_type="product-brief",
                lifecycle="living", status="active", products=f"[p{i}]", owners="[o]",
                created=created,
                last_review=review(i) if callable(review) else review) + "# Brief\n"
        return out

    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        def codes(files) -> set[str]:
            for stale in (root / "products").rglob("*.md"):
                stale.unlink()
            for rel, text in files.items():
                f = root / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(text)
            r = subprocess.run([sys.executable, str(VALIDATE), "--root", str(root),
                                "--json"], capture_output=True, text=True)
            return {f["code"] for f in json.loads(r.stdout)["findings"]}

        if "LC005" not in codes(repo(3, "2026-08-01 09:00")):
            problems.append("three living documents attesting the same minute were not "
                            "reported: one minute is not a reading of three documents, and "
                            "this is the only part of the claim a script can hold")
        if "LC005" in codes(repo(2, "2026-08-01 09:00")):
            problems.append("two documents finishing in the same minute were reported: that "
                            "is a person, and a check that fires on it gets switched off")
        if "LC005" in codes(repo(4, "2026-08-01 09:00", created="2026-08-01 09:00")):
            problems.append("a day one set was reported: `start` writes the first documents "
                            "in one session and each is born with `created` and "
                            "`last_review` equal, which is a creation and not a reading")
        # Midnight is an instant, and testing for it made the check blind to the one value
        # a script would write. A full timestamp comes back a `datetime` rather than a
        # string, which is the other half of the same discrimination.
        if "LC005" not in codes(repo(3, "2026-08-01 00:00")):
            problems.append("three documents attesting midnight were not reported: `00:00` is "
                            "an instant, and the check was reading the clock instead of "
                            "whether a time was stated at all")
        if "LC005" not in codes(repo(3, "2026-08-01 09:00:00")):
            problems.append("three documents attesting the same second were not reported: "
                            "with seconds the value parses to a `datetime` and stopped being "
                            "a string, which is not a fact about the review")
        if "LC005" in codes(repo(4, "2026-08-01")):
            problems.append("four documents carrying a bare date were reported: a date with "
                            "no minute says nothing about how long the reading took")
        if "LC005" in codes(repo(4, lambda i: f"2026-08-01 09:{10 + i * 7:02d}")):
            problems.append("four documents each with their own instant were reported, so "
                            "the check is counting documents rather than a shared minute")
    return problems


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


@check("a change cites the decision and the evaluation its classification demands")
def _change_contracts():
    # `CHG001` and `CHG002` were catalogued and off from the day they were written, because
    # the routing they needed existed only as prose in the `CHG` body and the recovered
    # version matched words in it. The `ICG` made the join a lookup instead.
    #
    # Both bind on `status`, and that is the half worth testing: the artifacts arrive in an
    # order. A `DEC` precedes the contract, an `EVR` follows the build. A check that
    # demanded either at `draft` would forbid the order the framework prescribes, and would
    # be switched off within a week for crying wolf on correct documents.
    fm = lambda **kw: "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"
    sections = ("<!-- section: what-changes -->\n## A\n"
                "<!-- section: what-must-not-change -->\n## B\n"
                "<!-- section: how-we-know-it-worked -->\n## C\n")

    base = {
        "OPEN.md": fm(schema="framework/open-register/v1", artifact_type="open-register",
                      lifecycle="living", status="active", owners="[o]",
                      created="2026-01-01", last_review="2026-01-01 09:00") + "# Open\n",
        "products/p/cycles/ICG-001.md": fm(
            schema="framework/impact-classification/v1",
            artifact_type="impact-classification", lifecycle="immutable",
            status="accepted", id="ICG-001", products="[p]", owners="[o]",
            created="2026-01-01",
            routing="\n  SIG-001: architecture",
            impacts="\n  SIG-001: [architecture, ai]")
        + "# ICG-001\n\n<!-- section: intake -->\n## I\n"
          "<!-- section: classification -->\n## C\n"
          "<!-- section: open-questions -->\n## O\n",
        "decisions/DEC-001.md": fm(
            schema="framework/decision-record/v1", artifact_type="decision-record",
            id="DEC-001", lifecycle="immutable", status="accepted", scope="architecture",
            products="[p]", owners="[o]", created="2026-01-01") + "# DEC-001\n",
        "products/p/releases/EVR-001.md": fm(
            schema="framework/evaluation-report/v1", artifact_type="evaluation-report",
            id="EVR-001", lifecycle="immutable", status="final", products="[p]",
            owners="[o]", created="2026-01-01") + "# EVR-001\n",
    }

    def chg(status, derives, verified_by="null", icg="ICG-001"):
        meta = dict(schema="framework/change-contract/v1",
                    artifact_type="change-contract", lifecycle="immutable",
                    status=status, id="CHG-001", products="[p]", owners="[o]",
                    created="2026-01-01", derives_from=derives, verified_by=verified_by)
        if icg:
            meta["icg"] = icg
        return fm(**meta) + "# CHG-001\n\n" + sections

    def codes(chg_text):
        files = dict(base, **{"products/p/changes/CHG-001.md": chg_text})
        with tempfile.TemporaryDirectory() as tmp:
            for rel, text in files.items():
                f = Path(tmp) / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(text)
            r = subprocess.run(
                [sys.executable, str(VALIDATE), "--root", tmp, "--json",
                 "--stale-days", "36500"], capture_output=True, text=True)
            if r.returncode not in (0, 1) or not r.stdout.strip():
                return None
            return {f["code"] for f in json.loads(r.stdout)["findings"]
                    if f["code"].startswith("CHG")}

    cases = [
        ("verified, nothing cited", chg("verified", "[SIG-001]"), {"CHG001", "CHG002"}),
        ("verified, both cited",
         chg("verified", "[SIG-001, DEC-001]", "EVR-001"), set()),
        ("implemented, no EVR yet", chg("implemented", "[SIG-001, DEC-001]"), set()),
        ("approved, no DEC", chg("approved", "[SIG-001]"), {"CHG002"}),
        ("draft, no DEC", chg("draft", "[SIG-001]"), set()),
        ("verified_by names something that is not an EVR",
         chg("verified", "[SIG-001, DEC-001]", "DEC-001"), {"CHG001"}),
        # The escape, and the case that used to expect silence here. A change that names no
        # classification cleared both of the checks written for it, and the expectation
        # recorded in this list was the proof that the hole was deliberate rather than
        # accidental. CHG003 is what closes it, and the direction is the reason it exists:
        # without it these checks question whoever filled `icg` in and say nothing at all
        # to whoever left it out.
        ("verified with no icg: nothing to look up, and that is the finding",
         chg("verified", "[SIG-001]", icg=None), {"CHG003"}),
        ("approved with no icg, which is where authorization starts",
         chg("approved", "[SIG-001]", icg=None), {"CHG003"}),
        # A proposal written before its triage is the order the framework prescribes.
        ("draft with no icg is a change waiting to be classified, not one that dodged it",
         chg("draft", "[SIG-001]", icg=None), set()),
        ("icg naming a classification that does not exist",
         chg("approved", "[SIG-001, DEC-001]", icg="ICG-404"), {"CHG003"}),
    ]
    problems = []
    for what, text, want in cases:
        got = codes(text)
        if got is None:
            problems.append(f"{what}: the validator did not complete")
        elif got != want:
            problems.append(f"{what}: expected {sorted(want) or 'nothing'}, got "
                            f"{sorted(got) or 'nothing'}")
    return problems


@check("a repository says which framework it was written against, or is told it does not")
def _framework_version():
    # The point is telling a migration from a mistake. When the registry moves, findings
    # appear in repositories nobody touched, and without this line there is nothing to
    # distinguish "the rules changed" from "we did this wrong" — which need opposite
    # responses. Guessing wrong at that a few times is how a team stops reading the
    # validator.
    current = REGISTRY["version"]
    fm = lambda **kw: "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"
    base = {"OPEN.md": fm(schema="framework/open-register/v1",
                          artifact_type="open-register", lifecycle="living",
                          status="active", owners="[owner]", created="2026-01-01",
                          last_review="2026-01-01 09:00") + "# Open\n"}

    def codes(config: str | None):
        files = dict(base)
        if config is not None:
            files["framework.yaml"] = config
        with tempfile.TemporaryDirectory() as tmp:
            for rel, text in files.items():
                (Path(tmp) / rel).write_text(text)
            r = subprocess.run(
                [sys.executable, str(VALIDATE), "--root", tmp, "--json",
                 "--stale-days", "36500"], capture_output=True, text=True)
            # Exit 1 is how the validator reports findings, so it cannot also mean
            # "crashed", and a traceback exits 1 too. Unparseable output is the only
            # thing that tells them apart. Without this the test still catches a
            # regression, by exploding on empty stdout, and a selfcheck that crashes
            # says less than one that names what broke.
            if r.returncode not in (0, 1) or not r.stdout.strip():
                last = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "?"
                return None, last
            return {(f["code"], f["level"]) for f in json.loads(r.stdout)["findings"]
                    if f["code"].startswith("FW")}, None

    major, minor, _ = current.split(".")
    problems = []
    cases = [
        (None, {("FW002", "info")}, "no framework.yaml at all"),
        ("checks:\n  LC002: warn\n", {("FW002", "info")}, "a config with no version"),
        (f"framework_version: {current}\n", set(), "the current version"),
        (f'framework_version: "{current}"\n', set(), "the current version, quoted"),
        (f"framework_version: {int(major) + 1}.0.0\n", {("FW001", "warn")},
         "a major ahead"),
        (f"framework_version: {major}.{int(minor) + 1}.0\n", {("FW001", "warn")},
         "a minor ahead"),
        # A PATCH IS SILENT, AND ASSERTED IN BOTH DIRECTIONS. By this registry's own
        # definition a patch is wording, a message, a fixture: nothing a repository has to
        # act on. Reported, it asks every project to edit a line whenever a sentence here is
        # rephrased, and a finding whose correct response is "change the number until it
        # stops" is one people learn to clear without reading -- on the check that has to be
        # believed the day the rules really do move.
        (f"framework_version: {major}.{minor}.0\n", set(), "a patch behind"),
        (f"framework_version: {major}.{minor}.99\n", set(), "a patch ahead"),
        # The two YAML traps, and they are the reason the version is a string. `1.1` is a
        # decimal and `2` is a whole number, so neither is comparable with a version, and
        # both are what somebody reaches for when shortening it. Quoting, which used to be
        # the trap, is now fine: the value was always meant to be a string.
        (f"framework_version: {major}.{minor}\n", {("FW001", "warn")},
         "two components, which YAML reads as a decimal"),
        (f"framework_version: {major}\n", {("FW001", "warn")},
         "one component, which YAML reads as a whole number"),
    ]
    for config, want, what in cases:
        got, crash = codes(config)
        if crash:
            problems.append(f"{what}: the validator did not complete: {crash}")
        elif got != want:
            problems.append(f"{what}: expected {sorted(want) or 'nothing'}, got "
                            f"{sorted(got) or 'nothing'}")

    # A malformed version has to be told apart from a real skew in the text, not only in
    # the code: reported as a mismatch it sends somebody looking for a migration that does
    # not exist, which is the confusion this check was added to remove rather than cause.
    with tempfile.TemporaryDirectory() as tmp:
        for rel, text in base.items():
            (Path(tmp) / rel).write_text(text)
        (Path(tmp) / "framework.yaml").write_text(f"framework_version: {major}.{minor}\n")
        r = subprocess.run([sys.executable, str(VALIDATE), "--root", tmp, "--json",
                            "--stale-days", "36500"], capture_output=True, text=True)
        msg = next((f["message"] for f in json.loads(r.stdout)["findings"]
                    if f["code"] == "FW001"), "")
        if "three" not in msg and "dots" not in msg:
            problems.append("a version with two components is reported as a version "
                            f"mismatch rather than as a malformed one: {msg[:80]}")

    # `1.10.0` is after `1.9.0`, and string comparison says the opposite. It is the first
    # place a version made of three parts goes wrong quietly, and it goes wrong in the
    # flattering direction: a repository nine minors behind reads as ahead of the framework,
    # which nobody migrates.
    v = _load(VALIDATE, "validate")
    if not (v.semver("1.9.0") < v.semver("1.10.0")):
        problems.append("1.10.0 does not sort after 1.9.0: the version is being compared "
                        "as text, so a repository behind reads as one ahead")
    for bad in ("2", "1.1", "", "v1.1.0", "1.1.0-rc1"):
        if v.semver(bad) is not None:
            problems.append(f"{bad!r} parses as a version and should not")

    # An unrecognised key stops the validator, by design, so the new one has to be on the
    # allowed list or every project that adopts it cannot run the checks at all.
    got, crash = codes(f"framework_version: {current}\nstale_days: 30\n")
    if crash:
        problems.append(f"`framework_version` beside another key is rejected: {crash}")
    return problems


@check("a signal set aside and a signal nobody read are told apart")
def _triage_state_is_derivable():
    # `LOG` is append-only, so no row can ever be marked handled, and triage state had
    # nowhere to live: every cycle re-read the whole log and guessed. It is derived from
    # the `ICG` now, which is only sound if a signal examined and dismissed counts as
    # examined. That is what `not-a-candidate` is for, and if it stopped counting the
    # check would nag forever about signals somebody already dealt with, which is how a
    # check gets switched off.
    fm = lambda **kw: "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"
    log = fm(schema="framework/signal-log/v1", artifact_type="signal-log",
             lifecycle="append-only", status="active", products="[alpha]",
             owners="[owner]", created="2026-01-01") \
        + "# Log\n\n| SIG-001 | drift |\n| SIG-002 | request |\n"

    def icg(**routing):
        head = fm(schema="framework/impact-classification/v1",
                  artifact_type="impact-classification", lifecycle="immutable",
                  status="accepted", id="ICG-001", products="[alpha]", owners="[owner]",
                  created="2026-01-01",
                  routing="\n" + "\n".join(f"  {k}: {v}" for k, v in routing.items()))
        return head + "# ICG-001\n\n<!-- section: intake -->\n## I\n" \
                      "<!-- section: classification -->\n## C\n" \
                      "<!-- section: open-questions -->\n## O\n"

    def run(files):
        with tempfile.TemporaryDirectory() as tmp:
            for rel, text in files.items():
                p = Path(tmp) / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text)
            r = subprocess.run(
                [sys.executable, str(VALIDATE), "--root", tmp, "--json",
                 "--stale-days", "36500"], capture_output=True, text=True)
            if r.returncode not in (0, 1):
                return None
            return [f for f in json.loads(r.stdout)["findings"] if f["code"] == "ICG001"]

    problems = []
    base = "products/alpha/LOG.md"
    cyc = "products/alpha/cycles/ICG-001.md"

    got = run({base: log})
    if got is None:
        return ["the validator crashed on a log with no impact classification"]
    if len(got) != 1:
        problems.append("a log with no ICG at all raised no ICG001: nothing in the "
                        "repository has been triaged and the check says so nowhere")
    elif "SIG-001" not in got[0]["message"] or "SIG-002" not in got[0]["message"]:
        problems.append(f"ICG001 does not name the untriaged signals: {got[0]['message']}")

    got = run({base: log, cyc: icg(**{"SIG-001": "architecture"})})
    if not got or "SIG-002" not in got[0]["message"]:
        problems.append("SIG-002 appears in no ICG and was not reported")
    elif "SIG-001" in got[0]["message"]:
        problems.append("SIG-001 was classified and is still reported as untriaged")

    got = run({base: log, cyc: icg(**{"SIG-001": "architecture",
                                      "SIG-002": "not-a-candidate"})})
    if got:
        problems.append("a signal routed `not-a-candidate` is still counted as never "
                        f"looked at: {got[0]['message']}. Examined and set aside is a "
                        "decision, and re-reporting it forever is how the check dies")
    return problems


@check("a gate verdict has a closed vocabulary, and so do the keys it is filed under")
def _maps_are_constrained():
    # `maps` exists so a document can carry a value per identifier as front matter instead
    # of as a table somebody has to read. It is worth nothing if anything validates: a
    # field with an open vocabulary is prose with a colon in it, and an open key is worse,
    # because the keys are what the rest of the framework joins on.
    #
    # Three shapes, and each is checked both ways. `one_of` is one value per key,
    # `any_of` a set, `fields` a record: the code map needs the third, because a
    # repository is a URL and a sentence saying what is in it, not a single word.
    typed = {n: s for n, s in REGISTRY["types"].items() if s.get("maps")}
    if not typed:
        return ["no type declares `maps`: this check is no longer running"]

    ids = "|".join(REGISTRY["id_prefixes"])
    problems = []
    for name, spec in typed.items():
        schema = json.loads((ROOT / "schemas" / "framework" / name / "v1.json")
                            .read_text(encoding="utf-8"))
        v = Draft202012Validator(schema)
        for field, rule in spec["maps"].items():
            # A key the pattern accepts, and some it must not. The accepted one is found
            # rather than assumed: `keys` is an arbitrary pattern, and hardcoding one shape
            # of nickname meant the check broke the first time a map keyed its rows on
            # identifiers instead.
            # THE ONE MAP WHOSE KEYS ARE NOT IDENTIFIERS. A glossary is keyed on the words
            # the business uses -- "Active customer", "Freshness", "Frontend" -- and there
            # is no vocabulary to close: any name a person writes is a name they write.
            # What protects a citation from a typo is not the pattern but `REF005`, which
            # resolves `GLOSSARY §Term` against these keys with case and whitespace
            # normalised and reports the ones that find nothing.
            if (name, field) == ("glossary", "terms"):
                continue

            pattern = rule.get("keys")
            candidates = ["SIG-001", "OD-001", "CMT-001", "RSK-001", "frontend",
                          "query-engine", "product.backend", "platform.access"]
            if pattern:
                accepted = [k for k in candidates if re.match(pattern, k)]
                if not accepted:
                    problems.append(f"{name}.{field}: the `keys` pattern accepts none of "
                                    f"{candidates}. Add one this check can use, or the map "
                                    "is not being checked at all")
                    continue
                good_key = accepted[0]
                bad_keys = [k for k in candidates if k not in accepted][:2] + ["Frontend"]
            else:
                good_key, bad_keys = "SIG-001", ["banana", "SIG_001"]

            if "one_of" in rule:
                ok_val, bad_vals = rule["one_of"][0], ["not-a-real-outcome"]
            elif "any_of" in rule:
                ok_val, bad_vals = [rule["any_of"][0]], [["not-a-real-outcome"], []]
            elif "scalar" in rule:
                # One constrained string per key. The commit map needs it: a hash is a
                # value, not a record.
                ok_val = "9a734ce" if rule["scalar"] else "anything"
                bad_vals = ["", "not a commit at all"] if rule["scalar"] else [""]
            elif "fields" in rule:
                req = list(rule["fields"]["required"])
                enums = rule["fields"].get("enums") or {}
                # A field of the record may carry its own closed vocabulary, so the legal
                # entry cannot be built out of a filler string for every key.
                def legal(k, _e=enums):
                    return _e[k][0] if k in _e else "x"
                ok_val = {k: legal(k) for k in req}
                bad_vals = [{}, dict(ok_val, surprise="x")]
                if len(req) > 1:
                    bad_vals.append({req[0]: legal(req[0])})   # one required key missing
                for k, values in enums.items():
                    if k in req:
                        bad_vals.append(dict(ok_val, **{k: "not-in-the-vocabulary"}))
                    if not values:
                        problems.append(f"{name}.{field}.enums.{k}: empty vocabulary")
            else:
                problems.append(f"{name}.{field}: declares no value shape")
                continue

            base = {"schema": f"framework/{name}/v1", "artifact_type": name,
                    "lifecycle": spec["lifecycle"], "status": spec["status"][0],
                    "owners": ["someone"], "created": "2026-01-01"}
            if spec.get("products") == "exactly-one":
                base["products"] = ["alpha"]
            # The type's own required fields, or the document under test fails on those
            # instead of on the map, and the check stops being about the map.
            for f2 in spec.get("required", []):
                if f2 not in base and f2 not in spec["maps"]:
                    base[f2] = "something"
            for f2, values in (spec.get("enums") or {}).items():
                base[f2] = values[0]
            for f2, r2 in spec["maps"].items():
                if not r2.get("required"):
                    continue
                k2 = "SIG-001" if not r2.get("keys") else "frontend"
                if "one_of" in r2:
                    base[f2] = {k2: r2["one_of"][0]}
                elif "any_of" in r2:
                    base[f2] = {k2: [r2["any_of"][0]]}
                else:
                    base[f2] = {k2: {k: "x" for k in r2["fields"]["required"]}}

            if not v.is_valid(dict(base, **{field: {good_key: ok_val}})):
                err = next(v.iter_errors(dict(base, **{field: {good_key: ok_val}}))).message
                problems.append(f"{name}.{field}: rejected a legal entry: {err}")
            for bad in bad_vals:
                if v.is_valid(dict(base, **{field: {good_key: bad}})):
                    problems.append(f"{name}.{field}: accepted {bad!r} as a value, so the "
                                    "shape is open and the field is prose with a colon")
            for bad in bad_keys:
                if v.is_valid(dict(base, **{field: {bad: ok_val}})):
                    problems.append(f"{name}.{field}: accepted {bad!r} as a key, so a "
                                    "mistyped name passes and joins on nothing")
    return problems


@check("a key one letter from a field that is read is reported, and a real field is not")
def _key_typos():
    # Declaring a field types its value and not its name, so `supercedes:` is an unknown key
    # and an unknown key is silence: the document validates, every check reading `supersedes`
    # sees nothing, and the line sits there looking right. Both directions matter here more
    # than usual, because the check works on a similarity and the false positive is a
    # legitimate field somebody chose.
    fm = lambda **kw: "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"

    def dec(n: str, extra: dict) -> str:
        return fm(schema="framework/decision-record/v1", artifact_type="decision-record",
                  id=n, lifecycle="immutable", status="accepted", scope="architecture",
                  products="[alpha]", owners="[o]", created="2026-01-01 09:00",
                  leaves_open="[]", **extra) + f"# {n}\n"

    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "framework.yaml").write_text(f"framework_version: {REGISTRY['version']}\n")
        (root / "decisions").mkdir()

        def codes(docs: dict) -> set[str]:
            for f in (root / "decisions").glob("*.md"):
                f.unlink()
            for n, extra in docs.items():
                (root / "decisions" / f"{n}-x.md").write_text(dec(n, extra))
            r = subprocess.run([sys.executable, str(VALIDATE), "--root", str(root),
                                "--json"], capture_output=True, text=True)
            return {f["code"] for f in json.loads(r.stdout)["findings"]}

        cases = [
            ({"DEC-001": {"supercedes": "DEC-002"}}, True, "`supercedes` for `supersedes`"),
            ({"DEC-001": {"owner": "[maria]"}}, True, "`owner` for `owners`"),
            ({"DEC-001": {"product": "alpha"}}, True,
             "`product` for `products`, which this framework renamed once for this reason"),
            ({"DEC-001": {"supersedes": "DEC-002"}}, False, "the field spelled right"),
            ({"DEC-001": {"approvers": "[g]"}}, False,
             "a field nothing declares and nothing resembles"),
            # A typo somebody copies is likelier than one somebody makes once, so repetition
            # must not turn it into vocabulary.
            ({"DEC-001": {"supercedes": "DEC-002"}, "DEC-002": {"supercedes": "DEC-001"}},
             True, "the same typo in two documents"),
            ({"DEC-001": {"approvers": "[g]"}, "DEC-002": {"approvers": "[m]"}}, False,
             "a real field in two documents"),
        ]
        for docs, want, what in cases:
            got = "FM006" in codes(docs)
            if got != want:
                problems.append(f"{what}: FM006 was {'not ' if want else ''}reported")
    return problems


@check("supersedes is a declared field with a shape, and not a convention")
def _supersedes_is_typed():
    # It was read by the validator and written in a template for weeks without being in any
    # schema, so `supersedes: 12` and `supersedes: {id: DEC-004}` were as legal as the thing
    # anybody meant, and the shape was whatever the last person wrote. Declared on every type
    # whose `status` can reach `superseded`, because those are the documents that can be
    # replaced.
    #
    # The three legal forms are all in use and none is a mistake: absent, one id, several.
    # `null` stays legal because the template writes it -- a field shown as existing and
    # holding nothing is how the templates say "this is yours to fill in".
    problems = []
    for name, spec in REGISTRY["types"].items():
        if "superseded" not in (spec.get("status") or []):
            continue
        if "supersedes" not in (spec.get("id_fields") or []):
            problems.append(f"{name} can reach `status: superseded` and does not declare "
                            "`supersedes`: the field that says what replaced it is a "
                            "convention there, and a convention has no shape")
            continue
        schema = json.loads((ROOT / "schemas" / "framework" / name / "v1.json")
                            .read_text(encoding="utf-8"))
        prop = schema["properties"].get("supersedes")
        if not prop or "oneOf" not in prop:
            problems.append(f"{name}: `supersedes` is declared in the registry and absent "
                            "or untyped in the generated schema")
            continue
        # The property on its own, and not a whole document with a `supersedes` in it: a
        # synthetic `ICG` missing its required maps is invalid for reasons that have nothing
        # to do with this field, and a probe that cannot tell the two apart reports the
        # field as broken on every type whose front matter is hard to fake.
        v = Draft202012Validator(prop)
        legal = [None, "DEC-004", ["DEC-004", "DEC-007"], "DEC-NNN"]
        illegal = [12, {"id": "DEC-004"}, "DEC4", "XYZ-001", ["DEC-004", "DEC-004"], []]
        for value in legal:
            if not v.is_valid(value):
                problems.append(f"{name}: rejected {value!r}, which is one of the forms in "
                                "use -- absent, one id, several, and the `null` a template "
                                "writes to show the field is yours to fill in")
        for value in illegal:
            if v.is_valid(value):
                problems.append(f"{name}: accepted {value!r} as a supersedes, so the field "
                                "is declared and still shapeless")
    return problems


@check("supersedes reads as a list, and a diamond is not a cycle")
def _supersedes_takes_a_list():
    # `supersedes: [DEC-001, DEC-004]` is how anyone replacing two decisions at once would
    # write it, and `derives_from` beside it already takes a list. The string-only read cost
    # twice: REF002 and REF003 skipped the list form without a word, so two documents could
    # both claim to be current, and then the cycle walk died on an unhashable type, which
    # takes the whole gate down with no verdict at all.
    fm = lambda **kw: "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"
    def dec(i, **extra):
        meta = dict(schema="framework/decision-record/v1",
                    artifact_type="decision-record", id=i, lifecycle="immutable",
                    status="accepted", scope="architecture", products="[alpha]",
                    owners="[owner]", created="2026-01-01")
        meta.update(extra)                      # so a case can set its own status
        return fm(**meta) + f"# {i}\n"

    def codes(files):
        with tempfile.TemporaryDirectory() as tmp:
            for name, text in files.items():
                p = Path(tmp) / "decisions" / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text)
            r = subprocess.run(
                [sys.executable, str(VALIDATE), "--root", tmp, "--json",
                 "--stale-days", "36500"], capture_output=True, text=True)
            if r.returncode not in (0, 1) or not r.stdout.strip():
                last = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "?"
                return None, last
            return [f["code"] for f in json.loads(r.stdout)["findings"]], None

    problems = []

    # Two at once. Both targets are still `accepted`, so both have to be reported.
    got, crash = codes({"DEC-001.md": dec("DEC-001"), "DEC-002.md": dec("DEC-002"),
                        "DEC-003.md": dec("DEC-003", supersedes="[DEC-001, DEC-002]")})
    if crash:
        problems.append(f"a list-valued supersedes brought the validator down: {crash}")
    elif got.count("REF003") != 2:
        problems.append(f"supersedes: [DEC-001, DEC-002] reported REF003 "
                        f"{got.count('REF003')} times out of 2: the list form is being "
                        "read past in silence, and both documents still read as current")

    # A cycle written with lists is still a cycle.
    got, crash = codes({"DEC-001.md": dec("DEC-001", supersedes="[DEC-002]"),
                        "DEC-002.md": dec("DEC-002", supersedes="[DEC-001]")})
    if crash:
        problems.append(f"a cyclic supersedence chain crashed the validator: {crash}")
    elif "REF004" not in got:
        problems.append("DEC-001 and DEC-002 supersede each other and REF004 did not fire")

    # A diamond is not a cycle. DEC-004 replaces two decisions that both replaced DEC-001,
    # so the walk meets DEC-001 twice by different routes. Nothing here loops, and a plain
    # visited set would call that meeting a loop and report a cycle that is not there.
    got, crash = codes({
        "DEC-001.md": dec("DEC-001", status="superseded"),
        "DEC-002.md": dec("DEC-002", status="superseded", supersedes="[DEC-001]"),
        "DEC-003.md": dec("DEC-003", status="superseded", supersedes="[DEC-001]"),
        "DEC-004.md": dec("DEC-004", supersedes="[DEC-002, DEC-003]")})
    if crash:
        problems.append(f"a branching supersedence chain crashed the validator: {crash}")
    elif "REF004" in got:
        problems.append("two decisions replaced by the same later one were reported as a "
                        "cyclic chain: the walk is confusing a diamond with a loop")

    # The scalar form is what FRAMEWORK.md writes, and it has to keep working.
    got, crash = codes({"DEC-001.md": dec("DEC-001"),
                        "DEC-002.md": dec("DEC-002", supersedes="DEC-001")})
    if crash or "REF003" not in (got or []):
        problems.append("supersedes as a bare string stopped being checked")

    return problems


@check("the extractor says which documents gave it nothing")
def _extract_reports_its_gaps():
    # The other executable in this repository, and until now the one nothing ran. It is
    # allowed to fail on a document: a scanned PDF has no text layer and that is not a bug.
    # What it is not allowed to do is leave the failure only in `inventory.json`, because
    # the corpus then reads as complete to whoever classifies it. Nothing here needs
    # markitdown or python-docx: plain files that yield no text exercise the same path.
    corpus = {
        "offerta.md": "# Offerta\n\nRefresh orario dei dati, non giornaliero.\n",
        "empty.md": "",
        "whitespace.txt": "   \n\t\n",
        "notes.rst": "unsupported extension, must not be counted as ingested\n",
    }
    problems = []

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "corpus"
        src.mkdir()
        for name, text in corpus.items():
            (src / name).write_text(text, encoding="utf-8")
        out = Path(tmp) / "out"

        r = subprocess.run([sys.executable, str(EXTRACT), str(src), "-o", str(out)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return [f"the extractor exited {r.returncode} on a readable corpus: "
                    f"{r.stderr.strip().splitlines()[-1] if r.stderr.strip() else ''}"]

        md = (out / "extract.md").read_text(encoding="utf-8")
        inv = json.loads((out / "inventory.json").read_text(encoding="utf-8"))

        if "Refresh orario" not in md:
            problems.append("the one document with text is missing from extract.md")
        if "offerta.md" not in md:
            problems.append("a block in extract.md does not name the file it came from: "
                            "provenance is the whole point of the extraction")
        for name in ("empty.md", "whitespace.txt"):
            if name not in md:
                problems.append(f"{name} produced no text and extract.md does not say so: "
                                "the gap is only in inventory.json, where nobody looks")

        listed = {d["source"] for d in inv["documents"]}
        if listed != {"offerta.md", "empty.md", "whitespace.txt"}:
            problems.append(f"inventory.json accounts for {sorted(listed)}: every handled "
                            "document belongs there, and nothing else does")

        # An empty corpus is a failure and has to be one: a caller that reads exit 0 goes on
        # to classify an extraction that never happened.
        empty = Path(tmp) / "empty-dir"
        empty.mkdir()
        e = subprocess.run([sys.executable, str(EXTRACT), str(empty), "-o", str(out)],
                           capture_output=True, text=True)
        if e.returncode == 0:
            problems.append("the extractor exited 0 on a corpus with nothing in it")

        f = Path(tmp) / "not-a-directory.md"
        f.write_text("x", encoding="utf-8")
        o = subprocess.run([sys.executable, str(EXTRACT), str(src), "-o", str(f)],
                           capture_output=True, text=True)
        if o.returncode == 0 or "Traceback" in o.stderr:
            problems.append("-o pointed at a file should say so and stop, not raise: "
                            f"rc={o.returncode}, stderr={o.stderr.strip()[:80]!r}")

    # The text-poor pages branch, reached through the pure builder. Every format that can
    # set `visual_review` goes through poppler, markitdown or LibreOffice, none of which a
    # bare CI runner has, so driving the CLI would leave this untested wherever it matters.
    x = _load(EXTRACT, "extract")
    seen = x.build_extract_md(
        2, [x.Block("deck.pdf", "page 1", "Architettura")],
        [], [x.DocInfo("deck.pdf", "pdf", units=9, visual_review=[2, 3, 4])])
    if "deck.pdf" not in seen or "2, 3, 4" not in seen:
        problems.append("a document with text-poor pages is not named in extract.md with "
                        "its page numbers: the warning lives only on stdout again")

    quiet = x.build_extract_md(1, [x.Block("a.md", "document", "hi")], [],
                               [x.DocInfo("a.md", "md", units=1)])
    if "look at" in quiet or "produced no text" in quiet:
        problems.append("extract.md warns about a corpus that had nothing wrong with it")

    return problems


@check("the corpus is found by what is in a folder, not by what the folder is called")
def _corpus_is_found_by_content():
    # `start` has to know where the client's documents are before it can move them, and the
    # answer is not knowable in advance: corpus, docs, documenti, a folder named after the
    # customer, or loose at the root. Matching names works for the first two and fails
    # silently on the rest, and a silent failure here builds a repository around a corpus
    # nobody read.
    x = _load(EXTRACT, "extract")
    problems = []

    def build(tmp: Path, files: dict[str, str]):
        for rel, text in files.items():
            f = tmp / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding="utf-8")

    artifact = ("---\nschema: framework/glossary/v1\nartifact_type: glossary\n"
                "lifecycle: living\nstatus: active\nowners: [o]\n"
                "created: 2026-01-01 09:00\n---\n\n# Glossary\n")

    cases = [
        ("a folder nobody would have guessed the name of",
         {"Materiale Cliente 2026/offerta.pdf": "%PDF-1.4\n",
          "Materiale Cliente 2026/note.txt": "appunti"},
         [("Materiale Cliente 2026", 1, 1)]),
        # The case a location rule cannot survive: the corpus sits beside the artifacts.
        ("a corpus loose at the root of a scaffolded repository",
         {"GLOSSARY.md": artifact, "OPEN.md": artifact,
          "products/alpha/PBR.md": artifact, "deck.pdf": "%PDF-1.4\n"},
         [(".", 1, 0)]),
        # Output of a previous run. Counting it would make every second run find a corpus.
        ("the extractor's own output",
         {"_meta/corpus/alpha/deck.pdf": "%PDF-1.4\n",
          "_meta/extract/extract.md": "# Business corpus extraction\n",
          "_meta/extract/alpha/extract.md": "# Business corpus extraction\n"},
         [("_meta/corpus/alpha", 1, 0)]),
        ("a project with code and no documents", {"src/app.py": "x = 1\n"}, []),
    ]
    for what, files, want in cases:
        with tempfile.TemporaryDirectory() as tmp:
            build(Path(tmp), files)
            got = x.find_corpus(Path(tmp))
        if got != want:
            problems.append(f"{what}: found {got}, expected {want}")

    # Two folders of documents is the one case that has to stop and ask. The runner-up is
    # usually last quarter's version of the same deck, and which is current is not a thing
    # a file count knows.
    with tempfile.TemporaryDirectory() as tmp:
        build(Path(tmp), {"corpus/a.pdf": "%PDF-1.4\n", "corpus/b.pdf": "%PDF-1.4\n",
                          "vecchi/c.pptx": "PK\x03\x04"})
        strong = [g for g in x.group_corpus(x.find_corpus(Path(tmp))) if g["documents"]]
    if len(strong) != 2:
        problems.append(f"two folders of documents came back as {len(strong)} candidate(s): "
                        "the skill decides whether to ask on this count")

    # One corpus filed by kind. Reported as three candidates it forces a question with no
    # right answer, and the answer to it would be wrong however it was given: they are all
    # the corpus. The extractor reads a directory recursively, so the group is usable as-is.
    with tempfile.TemporaryDirectory() as tmp:
        build(Path(tmp), {"docs/contracts/a.pdf": "%PDF", "docs/contracts/b.pdf": "%PDF",
                          "docs/decks/c.pptx": "PK", "docs/spreadsheets/d.xlsx": "PK"})
        got = x.group_corpus(x.find_corpus(Path(tmp)))
    if len(got) != 1 or got[0]["path"] != "docs" or got[0]["documents"] != 4:
        problems.append(f"a corpus split across docs/contracts, docs/decks and "
                        f"docs/spreadsheets came back as {[g['path'] for g in got]}")
    elif len(got[0]["children"]) != 3:
        problems.append("the group hid the subdirectories it gathered: one of them being an "
                        "older version of another is exactly what a person has to be shown")
    return problems


@check("an exclusion names a path when a bare name would be too blunt")
def _skips_are_scoped():
    # `_meta/extract` holds the extractor's output and no source document. Written as
    # `extract` it would also exclude the extraction step of every ETL project that keeps
    # one in a directory of that name, which is the mistake the registry already warns
    # about in the paragraph above the list. Bare names still work, and have to: `corpus`
    # means the same thing wherever it turns up.
    #
    # `_meta/business` is the second one of these and the temptation was stronger, because
    # `business` reads like a word no Data/AI project would use for artifacts -- and a
    # `business/` directory of domain models is exactly what several of them keep. The skill
    # writes under `_meta/`, so the narrow form costs nothing and the broad one would have
    # hidden somebody's documents from every check in the catalog.
    x = _load(VALIDATE, "validate")
    skips = set(x.REGISTRY_SCAN["skip_dirs"]) if hasattr(x, "REGISTRY_SCAN") \
        else set(yaml.safe_load((ROOT / "schemas" / "artifact-types.yaml")
                                .read_text())["scan"]["skip_dirs"])
    problems = []
    for parts, want, what in [
        (("_meta", "extract"), True, "the extractor's own output directory"),
        (("_meta", "extract", "gamma"), True, "a per-product folder inside it"),
        (("extract",), False, "an ETL directory called extract at the root"),
        (("pipelines", "extract"), False, "an extract step nested in a project's pipelines"),
        (("_meta", "business"), True, "where the `business` skill writes its updates"),
        (("_meta", "business", "archive"), True, "a folder somebody made inside it"),
        (("business",), False, "a project's own business directory at the root"),
        (("products", "alpha", "business"), False, "the same name under a product, which no "
                                                   "skill writes and nothing may hide"),
        (("_meta", "corpus"), True, "the corpus under _meta"),
        (("products", "alpha", "corpus"), True, "a corpus left where older repos keep it"),
        (("_meta",), False, "_meta itself, which can hold artifacts and must be scanned"),
        (("products", "alpha"), False, "an ordinary product directory"),
    ]:
        if x.skipped_dir(parts, skips) != want:
            problems.append(
                f"{what} ({'/'.join(parts)}) was {'not ' if want else ''}excluded"
                + ("" if want else ": an exclusion that protects the framework's "
                   "convenience is paid for by everyone using it"))
    return problems


@check("nothing anybody copies writes a scalar where the schema wants a list")
def _examples_agree_with_the_schema():
    # A template's front matter is validated against its own schema by the check above. Its
    # *body* is not, and neither is a fenced example in a skill, and both get copied: an
    # agent following `used_by: product-a` in a snippet produces a document that fails
    # `FM002`, and the failure surfaces in somebody's project rather than here.
    #
    # It happened. `depends_on` and `used_by` became lists in the registry and the templates
    # kept writing them as scalars for the minutes between the two edits, and a real run
    # landed in that window -- the plugin is a symlink to this working tree, so there is no
    # copy to be stale. Eighteen findings in a project because of a shape written in a file
    # that no check reads.
    want_list: set[str] = set()
    for spec in REGISTRY["types"].values():
        for field, rule in (spec.get("maps") or {}).items():
            want_list.update(rule.get("fields", {}).get("lists") or [])
            if "any_of" in rule:
                want_list.add(field)
    if not want_list:
        return ["no field is declared as a list: this check is no longer running"]

    # `key: value` where value is neither a flow sequence, a block sequence, nor a comment.
    scalar = re.compile(r"^\s*([a-z_]+):[ \t]*([^\s\[#][^#]*?)\s*$")
    problems = []
    for p in sorted(ROOT.rglob("*")):
        rel = p.relative_to(ROOT)
        # `schemas/` states the constraints rather than demonstrating them:
        # `products: exactly-one` in the registry is a cardinality declaration and not
        # a field somebody copies into a document.
        if p.suffix not in (".md", ".yaml", ".yml") or "build" in rel.parts:
            continue
        if rel.parts[0] in ("schemas", "tests"):
            continue
        if any(part.startswith(".") for part in rel.parts):
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            m = scalar.match(line)
            if m and m.group(1) in want_list:
                problems.append(f"{rel}:{i}: `{line.strip()}` — the schema wants a list here, "
                                "and whoever copies this line gets an FM002 in their project")
    return problems


@check("a document that says it was decided has to name the decision")
def _claims_carry_their_record():
    # Two documents make the same claim in a field and used to make it unbacked. A stack row
    # saying `chosen` with no `decided_in` reads as a decision nobody can find, which is the
    # ambiguity the stack was added to remove, arriving back through the field meant to
    # remove it. An open register entry with no `default_in_force` is the same shape: the file
    # calls that field mandatory in its own instructions and nothing was reading it except
    # REG003, and only on a high cost entry.
    def repo(files):
        with tempfile.TemporaryDirectory() as tmp:
            for rel, text in files.items():
                f = Path(tmp) / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(text)
            r = subprocess.run([sys.executable, str(VALIDATE), "--root", tmp, "--json",
                                "--stale-days", "36500"], capture_output=True, text=True)
            if r.returncode not in (0, 1) or not r.stdout.strip():
                return None
            return {f["code"] for f in json.loads(r.stdout)["findings"]}

    def stack(rows: str) -> str:
        return ("---\nschema: framework/operational-stack/v1\n"
                "artifact_type: operational-stack\nlifecycle: living\nstatus: active\n"
                "owners: [o]\ncreated: 2026-01-01 09:00\nlast_review: 2026-01-01 09:00\n"
                + rows + "---\n\n# Stack\n\n<!-- section: chosen -->\n## Chosen\n"
                "<!-- section: unratified -->\n## Unratified\n"
                "<!-- section: ruled-out -->\n## Ruled out\n")

    dec = ("---\nschema: framework/decision-record/v1\nartifact_type: decision-record\n"
           "id: DEC-001\nlifecycle: immutable\nstatus: accepted\nscope: architecture\n"
           "owners: [o]\ncreated: 2026-01-01 09:00\n---\n\n# DEC-001\n")
    draft = dec.replace("id: DEC-001", "id: DEC-002").replace("accepted", "proposed")
    second = dec.replace("DEC-001", "DEC-003")

    problems = []
    # Every `decided_in` here is bracketed, and that is the point of the case rather than a
    # detail of it. 2.8.8 declared the field a list and this block kept writing scalars, so
    # nothing ran the check against the shape the schema now requires -- and the check was
    # reading the raw value into a set membership test, which a list cannot survive. The
    # first repository to write one lost the report and the generated index with it. A test
    # that exercises a field in the shape no document is allowed to carry is not exercising
    # it.
    for rows, want, what in [
        ("stack:\n  db:\n    tool: PostgreSQL\n    status: chosen\n    decided_in: [DEC-001]\n",
         False, "a chosen tool naming an accepted decision"),
        ("stack:\n  db:\n    tool: PostgreSQL\n    status: chosen\n"
         "    decided_in: [DEC-001, DEC-003]\n",
         False, "a chosen tool ratified by two accepted decisions, which is what the list is for"),
        ("stack:\n  db:\n    tool: PostgreSQL\n    status: chosen\n"
         "    decided_in: [DEC-001, DEC-404]\n",
         True, "a list whose second entry is a decision that does not exist"),
        # The shape a repository carries between reading the migration note and finishing it.
        # It is an `FM002` and it has to stay one: a traceback out of `main()` takes the
        # report, and `--emit-index` shares that entry point.
        ("stack:\n  db:\n    tool: PostgreSQL\n    status: chosen\n    decided_in: DEC-001\n",
         False, "the pre-2.8.8 scalar, which is a schema finding and must not be a crash"),
        ("stack:\n  db:\n    tool: PostgreSQL\n    status: chosen\n",
         True, "a chosen tool naming no decision at all"),
        ("stack:\n  db:\n    tool: PostgreSQL\n    status: unratified\n    decided_in: [DEC-001]\n",
         True, "an unratified tool that names a decision, hiding one that was taken"),
        ("stack:\n  db:\n    tool: PostgreSQL\n    status: chosen\n    decided_in: [DEC-404]\n",
         True, "a decision that does not exist"),
        ("stack:\n  db:\n    tool: PostgreSQL\n    status: chosen\n    decided_in: [DEC-002]\n",
         True, "a decision that was never accepted"),
        ("stack:\n  db:\n    tool: PostgreSQL\n    status: unratified\n",
         False, "an unratified tool, which is the honest state and must stay quiet"),
        # The state the vocabulary did not have: tried, not in use, nobody decided. With
        # three values the only way to file it was `ruled-out` with nothing to name, and a
        # real repository wrote two of those -- so the check reported a document whose only
        # fault was that the words ran out.
        ("stack:\n  db:\n    tool: PostgreSQL\n    status: dropped\n",
         False, "an abandoned experiment nobody decided against, which is what `dropped` is"),
        ("stack:\n  db:\n    tool: PostgreSQL\n    status: dropped\n    decided_in: [DEC-001]\n",
         True, "a dropped tool naming a decision, which is a decision filed as an accident"),
    ]:
        got = repo({"STACK.md": stack(rows), "decisions/DEC-001.md": dec,
                    "decisions/DEC-002.md": draft, "decisions/DEC-003.md": second})
        if got is None:
            problems.append(f"the validator crashed on {what}")
        elif ("STK001" in got) != want:
            problems.append(f"{what} was {'not ' if want else ''}reported")

    def register(entries: str) -> str:
        return ("---\nschema: framework/open-register/v1\nartifact_type: open-register\n"
                "lifecycle: living\nstatus: active\nowners: [o]\n"
                "created: 2026-01-01 09:00\nlast_review: 2026-01-01 09:00\n"
                + entries + "---\n\n# Open\n")

    for entries, want, what in [
        ("entries:\n  OD-001:\n    status: open\n    cost_to_reverse: medium\n"
         "    default_in_force: the nightly job, unasked\n",
         False, "an entry with a cost and a default"),
        ("entries:\n  OD-001:\n    status: open\n    cost_to_reverse: medium\n",
         True, "a medium cost entry with no default, which used to pass"),
        ("entries:\n  OD-001:\n    status: open\n    default_in_force: none\n",
         True, "an entry with no cost to reverse, which is what orders the file"),
        ("entries:\n  OD-001:\n    status: decided\n    cost_to_reverse: low\n"
         "    default_in_force: none\n",
         True, "a decided entry naming no closed_by"),
        ("entries:\n  OD-001:\n    status: open\n    cost_to_reverse: low\n"
         "    default_in_force: none\n    depends_on: [OD-404]\n",
         True, "a dependency on an entry the register does not declare"),
        # A known issue is not a choice: it has no default in force and no cost to reverse.
        ("entries:\n  KI-001:\n    status: open\n", False, "a known issue"),
    ]:
        got = repo({"OPEN.md": register(entries)})
        if got is None:
            problems.append(f"the validator crashed on {what}")
        elif ("REG005" in got) != want:
            problems.append(f"{what} was {'not ' if want else ''}reported")
    return problems


@check("an attestation names repositories that exist, and leaves none of them out")
def _attestation_is_complete():
    # `verified_against` was one hash answering two questions, and the release skill had
    # both twenty lines apart: `git show <verified_against>:.../EVP.md` needs a commit of
    # this repository, and "the commit the evaluation actually ran on" is a commit of the
    # code. One repository made those the same thing. Five do not.
    def manifest(code: str) -> str:
        return ("schema: framework/product-manifest/v1\n"
                "artifact_type: product-manifest\nlifecycle: living\nstatus: active\n"
                "products: [alpha]\nname: Alpha\none_liner: A thing.\n"
                "owners: [o]\ncreated: 2026-01-01 09:00\nlast_review: 2026-01-01 09:00\n"
                "stage:\n  phase: F5\n  block: B\n" + code)

    def arc(attested: str) -> str:
        return ("---\nschema: framework/architecture/v1\nartifact_type: architecture\n"
                "lifecycle: living\nstatus: active\nproducts: [alpha]\nowners: [o]\n"
                "created: 2026-01-01 09:00\nlast_review: 2026-01-01 09:00\n"
                + attested + "---\n\n# Alpha\n\n"
                "<!-- section: current -->\n## Current\n\n"
                "<!-- section: target -->\n## Target\n\n"
                "<!-- section: delta -->\n## Delta\n")

    def codes(files):
        with tempfile.TemporaryDirectory() as tmp:
            for rel, text in files.items():
                f = Path(tmp) / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(text)
            r = subprocess.run([sys.executable, str(VALIDATE), "--root", tmp, "--json",
                                "--stale-days", "36500"], capture_output=True, text=True)
            if r.returncode not in (0, 1) or not r.stdout.strip():
                return None
            return {f["code"] for f in json.loads(r.stdout)["findings"]}

    two = ("code:\n  backend:\n    url: git@e.com:o/be.git\n    contains: api\n"
           "    release_relevant: 'true'\n"
           "  frontend:\n    url: git@e.com:o/fe.git\n    contains: ui\n"
           "    release_relevant: 'true'\n")
    problems = []
    for attested, want, what in [
        ("verified_code:\n  product.backend: 9a734ce\n  product.frontend: 2b8d5a1\n",
         set(), "both release-relevant repositories attested"),
        ("verified_code:\n  product.backend: 9a734ce\n",
         {"VER002"}, "one release-relevant repository left out"),
        ("verified_code:\n  product.backend: 9a734ce\n  product.database: 711dc90\n",
         {"VER001", "VER002"}, "a repository no code map declares"),
    ]:
        got = codes({"products/alpha/product.yaml": manifest(two),
                     "products/alpha/ARC.md": arc(attested)})
        if got is None:
            problems.append(f"the validator crashed on {what}")
        elif {c for c in got if c.startswith("VER")} != want:
            problems.append(
                f"{what}: reported {sorted(c for c in got if c.startswith('VER'))}, "
                f"expected {sorted(want)}"
                + ("" if want else ". A complete attestation must be silent")
                + (". An attestation covering part of the system reads as covering all of "
                   "it, which is the failure a single hash had" if "VER002" in want else ""))

    # Nothing declared release-relevant means nothing is owed: the framework does not get to
    # invent the standard it then enforces.
    one = "code:\n  backend:\n    url: git@e.com:o/be.git\n    contains: api\n"
    got = codes({"products/alpha/product.yaml": manifest(one),
                 "products/alpha/ARC.md": arc("verified_code:\n  product.backend: 9a734ce\n")})
    if got and "VER002" in got:
        problems.append("a project that marked no repository `release_relevant` was told its "
                        "attestation was incomplete against a list it never wrote")
    return problems


@check("the derived view of a product is generated, and its drift is reported")
def _manifest_is_derived():
    # `product.yaml` carried sections marked GENERATED and kept by hand, so "which decisions
    # are open" had two answers: the register, and a list beside it. The stale one is what an
    # agent reads first, because AGENTS.md sends it to the manifest.
    #
    # A separate generated file rather than sections rewritten inside `product.yaml`, which
    # is authoritative and full of comments carrying the reasoning behind each field.
    base = {
        "framework.yaml": f"framework_version: {REGISTRY['version']}\n",
        "products/alpha/product.yaml": (
            "schema: framework/product-manifest/v1\n"
            "artifact_type: product-manifest\nlifecycle: living\nstatus: active\n"
            "products: [alpha]\nname: Alpha\none_liner: A thing.\n"
            "owners: [o]\ncreated: 2026-01-01 09:00\nlast_review: 2026-01-01 09:00\n"
            "stage:\n  phase: F1\n  block: A\n"),
        "OPEN.md": ("---\nschema: framework/open-register/v1\n"
                    "artifact_type: open-register\nlifecycle: living\nstatus: active\n"
                    "owners: [o]\ncreated: 2026-01-01 09:00\n"
                    "last_review: 2026-01-01 09:00\n"
                    "entries:\n  OD-001:\n    status: open\n    cost_to_reverse: low\n"
                    "  OD-002:\n    status: decided\n    cost_to_reverse: low\n"
                    "    closed_by: DEC-001\n---\n\n# Open\n"),
    }
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        for rel, text in base.items():
            f = Path(tmp) / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text)
        out = Path(tmp) / "products" / "alpha" / "product.index.yaml"

        r = subprocess.run([sys.executable, str(VALIDATE), "--root", tmp, "--emit-index",
                            "--stale-days", "36500"], capture_output=True, text=True)
        if not out.exists():
            return [f"--emit-index wrote no derived view: {r.stdout.strip()[-160:]}"]
        text = out.read_text()
        if GENERATED_MARK not in text:
            problems.append("the derived view carries no generated marker, so nothing "
                            "protects a hand-written file at that path from being replaced")
        if "OD-001" not in text or "OD-002" in text:
            problems.append("`open_decisions` is not what the register says is open: "
                            f"{[l for l in text.splitlines() if 'open_decisions' in l]}")

        # Drift has to be reported without writing, or CI cannot tell a stale file from a
        # fresh one, and a generated file nobody regenerates is worse than a hand-written
        # one because everybody assumes something keeps it true.
        out.write_text(text.replace("OD-001", "OD-999"))
        r = subprocess.run([sys.executable, str(VALIDATE), "--root", tmp, "--emit-index",
                            "--check", "--stale-days", "36500"], capture_output=True, text=True)
        if r.returncode == 0:
            problems.append("--emit-index --check exited 0 on a derived view that had been "
                            "edited by hand")
        if out.read_text() == text:
            problems.append("--check rewrote the file it was asked only to compare")
    return problems


@check("a repository shared by two products has one home, and only one")
def _shared_code_has_one_home():
    # The case this framework is about to be used on: one product across five repositories,
    # and two more products sharing the layer everybody signs in through. A per-product map
    # has nowhere to put the shared one, so the substrate carries `code:` too — and the way
    # that arrangement fails is a repository written into both, agreeing on the day it is
    # written and diverging afterwards.
    # The key of a `code:` entry is what this file calls the repository; the URL is which
    # repository it is. Keyed on the key, the check fired on two products that each own a
    # `backend` and stayed silent on one repository entered as `identity` here and `auth`
    # there -- and the second is how the duplication actually arises, because two teams
    # naming the same thing each use their own word.
    problems = []
    v = _load(VALIDATE, "validate")
    same = "github.com/org/repo"
    for url, want in [
        ("git@github.com:org/repo.git", same),
        ("ssh://git@github.com/org/repo.git", same),
        ("https://github.com/org/repo.git", same),
        ("https://GitHub.com/org/repo/", same),
        ("git@github.com:org/repo", same),
        # A port belongs to the address. Converted as if it were an scp-style path it became
        # a directory, and a self-hosted GitLab stopped comparing equal to itself.
        ("https://gitlab.self.hosted:8443/grp/repo.git", "gitlab.self.hosted:8443/grp/repo"),
    ]:
        if v.canonical_repo(url) != want:
            problems.append(f"{url} canonicalised to {v.canonical_repo(url)!r}, not {want!r}")

    def manifest(product: str, code: str) -> str:
        return ("schema: framework/product-manifest/v1\n"
                "artifact_type: product-manifest\n"
                "lifecycle: living\nstatus: active\n"
                f"products: [{product}]\nname: {product.title()}\n"
                "one_liner: A thing that does a thing.\n"
                "owners: [Someone]\ncreated: 2026-01-01 09:00\n"
                "last_review: 2026-01-01 09:00\n"
                "stage:\n  phase: F4\n  block: B\n" + code)

    shared = ("code:\n  access:\n    url: git@example.com:org/access.git\n"
              "    contains: sign-in and tenancy\n")
    platform = ("---\nschema: framework/platform-architecture/v1\n"
                "artifact_type: platform-architecture\nlifecycle: living\nstatus: active\n"
                "products: [alpha, beta]\nowners: [Someone]\n"
                "created: 2026-01-01 09:00\nlast_review: 2026-01-01 09:00\n"
                + shared + "---\n\n# Substrate\n")

    def codes(files):
        with tempfile.TemporaryDirectory() as tmp:
            for rel, text in files.items():
                f = Path(tmp) / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(text)
            r = subprocess.run([sys.executable, str(VALIDATE), "--root", tmp, "--json",
                                "--stale-days", "36500"], capture_output=True, text=True)
            if r.returncode not in (0, 1) or not r.stdout.strip():
                return None
            return {f["code"] for f in json.loads(r.stdout)["findings"]}

    own = ("code:\n  frontend:\n    url: git@example.com:org/alpha-fe.git\n"
           "    contains: the app\n")

    # Declared once on the substrate, used by both: the arrangement working.
    got = codes({"PLATFORM.md": platform,
                 "products/alpha/product.yaml": manifest("alpha", own),
                 "products/beta/product.yaml": manifest("beta", "")})
    if got is None:
        problems.append("the validator crashed on a substrate declaring shared code")
    elif "XP004" in got:
        problems.append("a repository declared once on the platform was reported as a "
                        "duplicate: the substrate is where a shared repository belongs")

    # The same repository written into a product as well. One question, two answers.
    got = codes({"PLATFORM.md": platform,
                 "products/alpha/product.yaml": manifest("alpha", shared),
                 "products/beta/product.yaml": manifest("beta", "")})
    if got is None:
        problems.append("the validator crashed on a repository declared twice")
    elif "XP004" not in got:
        problems.append("a repository declared by both the platform and a product was not "
                        "reported: the two entries agree today and one of them gets fixed")

    # And between two products, with no platform in the repository at all.
    got = codes({"products/alpha/product.yaml": manifest("alpha", shared),
                 "products/beta/product.yaml": manifest("beta", shared)})
    if got is None:
        problems.append("the validator crashed on two products claiming one repository")
    elif "XP004" not in got:
        problems.append("two products declaring the same repository were not reported, "
                        "which is the duplication the platform map exists to avoid")

    # The two cases that separate an identity from a nickname, and the reason the check was
    # rewritten. Without them a version keyed on the map key passes this whole block, which
    # is what it did.
    def entry(key: str, url: str) -> str:
        return f"code:\n  {key}:\n    url: {url}\n    contains: stuff\n"

    got = codes({"products/alpha/product.yaml":
                 manifest("alpha", entry("backend", "git@example.com:org/alpha-be.git")),
                 "products/beta/product.yaml":
                 manifest("beta", entry("backend", "git@example.com:org/beta-be.git"))})
    if got is None:
        problems.append("the validator crashed on two products that each own a `backend`")
    elif "XP004" in got:
        problems.append("two products that each call their own repository `backend` were "
                        "reported as sharing one: the key is what a file calls a repository, "
                        "not which repository it is")

    got = codes({"products/alpha/product.yaml":
                 manifest("alpha", entry("identity", "git@example.com:org/access.git")),
                 "products/beta/product.yaml":
                 manifest("beta", entry("auth", "https://example.com/org/access.git"))})
    if got is None:
        problems.append("the validator crashed on one repository under two nicknames")
    elif "XP004" not in got:
        problems.append("one repository entered as `identity` under one product and `auth` "
                        "under another was not reported. This is how the duplication "
                        "actually arises: each side calls it what it calls it, and a check "
                        "keyed on the name catches only the tidy case")
    return problems


@check("a product in discovery is not reported for lacking what discovery has not reached")
def _early_products_are_not_findings():
    # Block A is elastic on purpose. A product at F1 has no brief because it has not got
    # there, and reporting that is the framework asking somebody to backfill a document
    # they had no grounds to write. What separates "early" from "undocumented" is the stage
    # the manifest declares, so a product with no manifest at all still has to be reported:
    # nothing said which of the two it was.
    def manifest(phase: str | None) -> str:
        stage = f"stage:\n  phase: {phase}\n  block: A\n" if phase else ""
        return ("schema: framework/product-manifest/v1\n"
                "artifact_type: product-manifest\n"
                "lifecycle: living\nstatus: active\n"
                "products: [alpha]\nname: Alpha\n"
                "one_liner: A thing that does a thing.\n"
                "owners: [Someone]\ncreated: 2026-01-01 09:00\n"
                "last_review: 2026-01-01 09:00\n" + stage)

    def codes(files):
        with tempfile.TemporaryDirectory() as tmp:
            for rel, text in files.items():
                f = Path(tmp) / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(text)
            r = subprocess.run([sys.executable, str(VALIDATE), "--root", tmp, "--json",
                                "--stale-days", "36500"], capture_output=True, text=True)
            if r.returncode not in (0, 1) or not r.stdout.strip():
                return None
            return {f["code"] for f in json.loads(r.stdout)["findings"]}

    problems = []
    for phase, want, why in [
        ("F1", False, "a product in signal and framing"),
        ("F3", False, "a product in solution discovery"),
        ("F4", True, "a product shaping its MVP, which is where the brief belongs"),
        ("BUILD", True, "a product being built"),
        (None, True, "a product whose manifest declares no stage at all"),
    ]:
        got = codes({"products/alpha/product.yaml": manifest(phase)})
        if got is None:
            problems.append(f"the validator crashed on {why}")
        elif ("XP003" in got) != want:
            problems.append(
                f"{why} {'was not' if want else 'was'} reported for having no PBR"
                + ("" if want else ": discovery is elastic and this is the check telling a "
                   "project it is doing it wrong"))
    return problems


@check("the plugin and the framework ship one version, and it is the same number")
def _one_version():
    # They are one number by decision, reversing a note in the registry that said the
    # framework's version was not the plugin's. The decision only holds if something keeps
    # them equal: two files that are supposed to agree and are edited by hand are two files
    # that disagree, which is the failure this whole framework is a set of arguments about.
    # `claude plugin validate` already refuses a `plugin.json` and a marketplace entry that
    # disagree; this is the third corner of that triangle, which it has no way to see.
    problems = []
    registry = REGISTRY["version"]
    for rel, read in (
        (".claude-plugin/plugin.json", lambda d: d["version"]),
        (".claude-plugin/marketplace.json", lambda d: d["plugins"][0]["version"]),
    ):
        declared = read(json.loads((ROOT / rel).read_text()))
        if declared != registry:
            problems.append(
                f"{rel} declares {declared!r} and schemas/artifact-types.yaml declares "
                f"{registry!r}. One artifact, one version: whichever is right, the other "
                "answers 'what am I running' with a number nobody set")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(registry)):
        problems.append(f"the registry version is {registry!r}, which is not three numbers "
                        "separated by dots: a plugin manifest cannot carry it")
    return problems


@check("nothing states the framework's version except the registry that defines it")
def _version_is_not_restated():
    # `start` wrote a literal version into every repository it set up, in an example whose
    # own next paragraph says to read the number from the registry. The framework moved and
    # the skill kept seeding a value that was already wrong -- an `FW001` on day one, in the
    # file whose whole job is to tell a migration from a mistake, produced by the skill that
    # creates the file.
    #
    # The literal is not quoted anywhere in this comment, and that is this check working on
    # itself rather than an accident of wording: an exemption for the file that holds the
    # rule is the first hole anybody widens.
    #
    # It is the same failure as the count in prose, with a longer fuse: nothing is wrong on
    # the day it is written, and nothing reports it on the day it becomes wrong. So the
    # rule is the flat one -- no literal anywhere but the registry. An example writes `N`,
    # and an `N` that reaches a real `framework.yaml` is an `FW001` saying it is a string
    # and not a whole number, which is a sentence a stale number never produces.
    literal = re.compile(r"framework_version:\s*['\"]?(\d[\d.]*)")
    skip = {"build", "__pycache__", ".git", "node_modules"}
    problems = []
    for path in sorted(ROOT.rglob("*")):
        if path.suffix not in (".md", ".py", ".yaml") or not path.is_file():
            continue
        if set(path.relative_to(ROOT).parts) & skip:
            continue
        if path == ROOT / "schemas" / "artifact-types.yaml":
            continue          # the one place the number is defined
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            m = literal.search(line)
            # Inside a test, a version built from the registry is the point of the test:
            # `f"framework_version: {current + 1}"` has no literal for this to find, and a
            # bare digit in one would be the same defect as anywhere else.
            if m:
                problems.append(
                    f"{path.relative_to(ROOT)}:{n} writes framework_version {m.group(1)} "
                    "as a literal. Read it from `version:` in schemas/artifact-types.yaml, "
                    "or write `N` if it is an example: this is the line that goes wrong "
                    "silently the day the framework moves")
    return problems


@check("every product owns its register, and the root composes them without copying them")
def _registers_are_per_product():
    # The arrangement the framework now asks for: one register per product, one for the
    # substrate, one at the root for what belongs to no single product, and a generated
    # union under the last. Six things have to hold at once and each of them used to fail
    # in the direction that reads as "nothing is open".
    fm = lambda body: ("---\nschema: framework/open-register/v1\n"
                       "artifact_type: open-register\nlifecycle: living\nstatus: active\n"
                       "owners: [o]\ncreated: 2026-01-01 09:00\n"
                       "last_review: 2026-01-01 09:00\n" + body + "---\n\n# Open\n")
    man = lambda p: ("schema: framework/product-manifest/v1\n"
                     "artifact_type: product-manifest\nlifecycle: living\nstatus: active\n"
                     f"products: [{p}]\nname: {p}\none_liner: A thing.\n"
                     "owners: [o]\ncreated: 2026-01-01 09:00\nlast_review: 2026-01-01 09:00\n"
                     "stage:\n  phase: F5\n  block: A\n")
    base = {
        "framework.yaml": f"framework_version: {REGISTRY['version']}\n",
        "products/alpha/product.yaml": man("alpha"),
        "products/beta/product.yaml": man("beta"),
        # No `entries:`, and that is legal here and nowhere else: the root of a repository
        # that files per product is a view plus a parking lot. The marker is what says so.
        "OPEN.md": fm("") + "\n<!-- generated: open-union -->\nx\n<!-- /generated -->\n",
        "platform/OPEN.md": fm("entries:\n  OD-001:\n    status: open\n"
                               "    cost_to_reverse: high\n"
                               "    default_in_force: one database for everyone\n"),
        # `depends_on` reaches into the substrate's register, which is the ordinary case
        # once the entries are filed per product and used to be reported as dangling.
        "products/alpha/OPEN.md": fm("entries:\n  OD-002:\n    status: open\n"
                                     "    cost_to_reverse: low\n"
                                     "    default_in_force: three retries\n"
                                     "    depends_on: [OD-001]\n"),
    }
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for rel, text in base.items():
            f = root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text)

        run = lambda *extra: subprocess.run(
            [sys.executable, str(VALIDATE), "--root", str(root), "--json",
             "--stale-days", "36500", *extra], capture_output=True, text=True)
        r = run("--emit-index")
        if r.returncode not in (0, 1):
            return [f"the validator crashed: {r.stderr.strip().splitlines()[-1]}"]
        codes = [f["code"] for f in json.loads(r.stdout)["findings"]]

        if "REG006" not in codes:
            problems.append("a product directory with no register of its own was not "
                            "reported: an agent sent to work there reads no register and "
                            "concludes nothing is open")
        if "REG004" in codes:
            problems.append("the register at the root was reported for holding no "
                            "`entries:` while carrying the union marker, and the reliable "
                            "way to clear that is to paste the entries back in")
        if "REG005" in codes:
            problems.append("a `depends_on` reaching another register was reported as "
                            f"dangling: {[f['message'] for f in json.loads(r.stdout)['findings'] if f['code'] == 'REG005']}")

        # Attribution comes from the directory. Reading it off `products:` -- absent in a
        # product's own register, because the directory already said it -- put alpha's
        # entries into beta's derived view, and that view is where AGENTS.md sends an agent.
        beta = (root / "products" / "beta" / "product.index.yaml").read_text()
        if "OD-002" in beta:
            problems.append("an entry filed in alpha's register reached beta's derived "
                            "view: scope is being read off `products:` and not off where "
                            "the register sits")
        if "OD-001" not in beta:
            problems.append("a substrate entry is missing from a product's derived view: "
                            "the decisions that bind every product are the ones a product "
                            "cannot see it is waiting on")

        union = (root / "OPEN.md").read_text()
        if "## alpha" not in union or "## beta" not in union:
            problems.append("the union at the root has no heading per product")
        if "OD-001" not in union or "OD-002" not in union:
            problems.append("the union does not hold every open entry")
        if "entries:" in union.split("---")[1]:
            problems.append("the union grew an `entries:` map, so every check that reads "
                            "one now reports each entry twice and `depends_on` has two "
                            "rows with the same id to resolve against")

        # `all` IS A WORD AND NOT A PRODUCT, and the two halves of that sentence used to
        # live in different functions: `binds` knew it, the generator did not, and the union
        # grew a `## all` heading for a product no repository has. Worse, the last section
        # selected the entries that named nothing -- the exact state `REG011` exists to
        # remove -- so the more a repository answered the new check, the emptier the section
        # holding what binds everything became.
        (root / "products" / "beta" / "OPEN.md").write_text(fm("entries: {}\n"))
        (root / "OPEN.md").write_text(
            fm("entries:\n  OD-009:\n    status: open\n    cost_to_reverse: high\n"
               "    products: [all]\n    default_in_force: one database for everyone\n"
               "  OD-010:\n    status: open\n    cost_to_reverse: low\n"
               "    products: [alpha]\n    default_in_force: nothing\n")
            + "\n<!-- generated: open-union -->\nx\n<!-- /generated -->\n")
        run("--emit-index")
        union = (root / "OPEN.md").read_text()
        if "## all" in union:
            problems.append("the union grew a heading for `all`, which is the word an entry "
                            "uses to say it binds every product and not the name of one")
        tail = union.split("## Bound to no single product", 1)
        if len(tail) != 2:
            problems.append("the union lost the section for what binds no single product")
        else:
            if "OD-009" not in tail[1]:
                problems.append("an entry declaring `[all]` is missing from the section for "
                                "what binds no single product. That section used to hold the "
                                "entries naming nothing, which is the state `REG011` removes: "
                                "answer the check and the section empties itself")
            if "OD-010" in tail[1]:
                problems.append("an entry naming one product appeared under what binds no "
                                "single product")
        for prod in ("## alpha", "## beta"):
            block = union.split(prod, 1)[1].split("\n## ", 1)[0]
            if "OD-009" not in block:
                problems.append(f"an entry declaring `[all]` is missing from {prod.strip()}")

        # The prose outside the markers is not the generator's to touch.
        (root / "OPEN.md").write_text(union.replace("# Open", "# Open\n\nMine, by hand."))
        run("--emit-index")
        if "Mine, by hand." not in (root / "OPEN.md").read_text():
            problems.append("--emit-index rewrote prose outside the region markers")

        # A duplicate id is the failure a per-product register invites: each one starts at
        # 001 unless something says otherwise, and the collision resolves itself silently.
        (root / "products" / "beta" / "OPEN.md").write_text(
            fm("entries:\n  OD-002:\n    status: open\n    cost_to_reverse: low\n"
               "    default_in_force: three retries\n"))
        codes = [f["code"] for f in json.loads(run().stdout)["findings"]]
        if "REG007" not in codes:
            problems.append("two registers declaring the same entry id were not reported, "
                            "so a `depends_on` naming it resolves to whichever was read last")

        # A product may genuinely have nothing open, and it still has to have a register.
        # `entries: {}` is how it says so: refusing it would leave inventing an entry as the
        # only way to satisfy both checks, and an entry invented to clear a finding is the
        # failure everything here is arranged against. Absent `entries:` stays a finding,
        # because the two are different claims -- read and nothing found, versus nobody
        # filled this in.
        empty = root / "products" / "beta" / "OPEN.md"
        empty.write_text(fm("entries: {}\n"))
        out = json.loads(run().stdout)
        stated = [f for f in out["findings"] if f["code"] in ("REG004", "FM002")
                  and f["path"].endswith("beta/OPEN.md")]
        if stated:
            problems.append("a register declaring `entries: {}` was reported "
                            f"({[f['code'] for f in stated]}): a product with nothing open "
                            "has no way left to have a register except inventing an entry")
        empty.write_text(fm(""))
        silent = [f["code"] for f in json.loads(run().stdout)["findings"]
                  if f["code"] == "REG004" and f["path"].endswith("beta/OPEN.md")]
        if not silent:
            problems.append("a register with no `entries:` at all was not reported, so "
                            "'nobody filled this in' and 'there is nothing open' now read "
                            "the same")

        (root / "products" / "beta" / "OPEN.md").write_text(
            fm("entries:\n  OD-003:\n    status: open\n    cost_to_reverse: low\n"
               "    default_in_force: three retries\n    products: [alpha]\n"))
        codes = [f["code"] for f in json.loads(run().stdout)["findings"]]
        if "REG008" not in codes:
            problems.append("an entry in beta's register naming alpha was not reported: a "
                            "person reading the directory and the derived view disagree "
                            "about who it is about, and neither is told")

        # `trigger` replaced `deadline` in 2.0.0, and the point of the rename is the value
        # rather than the key: what closes the window is an event, and a date on its own is
        # a number somebody picked. Both spellings of a bare date are asserted, because YAML
        # hands back a `date` object for the unquoted form and a string for the quoted one,
        # and a check that only saw the string would be silent on the spelling everybody
        # actually writes.
        entry = lambda trg: fm("entries:\n  OD-004:\n    status: open\n"
                               "    cost_to_reverse: high\n"
                               "    default_in_force: none\n"
                               f"    trigger: {trg}\n")
        for written in ("2026-09-30", '"2026-09-30"', "2026-09-30."):
            (root / "products" / "beta" / "OPEN.md").write_text(entry(written))
            codes = [f["code"] for f in json.loads(run().stdout)["findings"]]
            if "REG009" not in codes:
                problems.append(f"a trigger written as {written} was not reported. A date "
                                "does not force a decision by arriving, and the entry it "
                                "sits on is one nobody has taken")

        # A date beside the event is the same finding. It reads as the careful version --
        # here is the event, and here is when it falls -- and the date is the half that gets
        # quoted back by somebody who never opened the register, on an entry whose whole
        # content is that nobody has decided.
        for written in ("the external audit, 2026-10-31", "Q4 2026", "the audit on 31/10/2026"):
            (root / "products" / "beta" / "OPEN.md").write_text(entry(written))
            codes = [f["code"] for f in json.loads(run().stdout)["findings"]]
            if "REG009" not in codes:
                problems.append(f"a trigger reading {written!r} was not reported: a date "
                                "beside an event is still a date on an undecided entry")

        # And the shape that must stay silent, because a check that reports the thing the
        # template asks for is a check somebody turns off.
        for written in ("before the second customer", "the external audit"):
            (root / "products" / "beta" / "OPEN.md").write_text(entry(written))
            codes = [f["code"] for f in json.loads(run().stdout)["findings"]]
            if "REG009" in codes:
                problems.append(f"a trigger reading {written!r} was reported: the check is "
                                "matching prose rather than digits")

        # Who an entry at the root binds: `[all]` is a statement, absence is a gap, and
        # before this they were written identically. The root register of this fixture is
        # the one with no `entries:` at all, so the entry is added here and removed after.
        rootreg = root / "OPEN.md"
        keep = rootreg.read_text()
        entry_at_root = lambda decl: (
            fm("entries:\n  OD-009:\n    status: open\n    cost_to_reverse: low\n"
               f"    default_in_force: nothing\n{decl}")
            + "\n<!-- generated: open-union -->\nx\n<!-- /generated -->\n")
        for decl, want in (("", True),
                           ("    products: [all]\n", False),
                           ("    products: [alpha]\n", False),
                           ("    products: [all, alpha]\n", True)):
            rootreg.write_text(entry_at_root(decl))
            codes = [f["code"] for f in json.loads(run().stdout)["findings"]]
            if want and "REG011" not in codes:
                problems.append(f"an entry at the root declaring {decl.strip() or 'nothing'} "
                                "was not reported: it binds every product by rule, and "
                                "nothing distinguishes that from nobody having asked")
            if not want and "REG011" in codes:
                problems.append(f"an entry at the root declaring {decl.strip()} was "
                                "reported, so the field cannot be answered")
        # Answering the question and still being in the wrong file. `REG011` asks who an
        # entry binds; `REG013` is about what the root register is for, and green on the
        # first has never implied the second -- which is how seventeen entries came to sit
        # at the root of a real repository, each naming one product, all of them reported by
        # nothing.
        for decl, want, why in (("    products: [alpha]\n", True,
                                 "an entry at the root binding one product that has a "
                                 "register of its own"),
                                ("    products: [all]\n", False,
                                 "an entry binding every product, which is what the root is "
                                 "for"),
                                ("    products: [alpha, beta]\n", False,
                                 "an entry binding two products, which belongs to neither "
                                 "register"),
                                ("    products: [gamma]\n", False,
                                 "an entry naming a product with no directory anywhere, "
                                 "which has nowhere to be moved to")):
            rootreg.write_text(entry_at_root(decl))
            codes = [f["code"] for f in json.loads(run().stdout)["findings"]]
            if ("REG013" in codes) != want:
                problems.append(f"{why} was {'not ' if want else ''}reported")
        rootreg.write_text(keep)

        # And the state the register is written for: a repository with a register and no
        # products yet. Asking which products an entry binds has no available answer there.
        rootreg.write_text(entry_at_root(""))
        for man in (root / "products").glob("*/product.yaml"):
            man.rename(man.with_suffix(".yaml.parked"))
        codes = [f["code"] for f in json.loads(run().stdout)["findings"]]
        for man in (root / "products").glob("*/product.yaml.parked"):
            man.rename(man.with_suffix("").with_suffix(".yaml"))
        if "REG011" in codes:
            problems.append("an entry at the root was asked which products it binds in a "
                            "repository that declares none: at day one the register is the "
                            "file that exists and the products are what has not been "
                            "created yet")
        rootreg.write_text(keep)

        # The manifest answering a question that moved. Absent from the template now, and a
        # repository that kept the field keeps a second answer that nothing recomputes.
        man_path = root / "products" / "alpha" / "product.yaml"
        original = man_path.read_text()
        for field_name in ("open_decisions: [OD-001]", "open_risks: []", "active_changes: []"):
            man_path.write_text(original + field_name + "\n")
            codes = [f["code"] for f in json.loads(run().stdout)["findings"]]
            if "FM005" not in codes:
                problems.append(f"a manifest carrying `{field_name.split(':')[0]}` was not "
                                "reported: it is derived now, and a hand written copy of a "
                                "derived answer is the one that goes stale unnoticed")
        man_path.write_text(original)

        # A date in a heading, which `REG009` structurally cannot see: it reads the
        # `trigger` of an entry, and a heading belongs to no entry while binding every one
        # filed under it. This framework shipped one in its own template.
        head = lambda h: (fm("entries:\n  OD-004:\n    status: open\n"
                             "    cost_to_reverse: high\n"
                             "    default_in_force: none\n"
                             "    trigger: before the second customer\n")
                          + f"\n{h}\n\n### OD-004 - A choice\n")
        for written in ("## Cost to reverse MEDIUM: decide by 2026-09-30",
                        "## Decide these in Q4 2026",
                        "### OD-004 - move by 30/09/2026"):
            (root / "products" / "beta" / "OPEN.md").write_text(head(written))
            codes = [f["code"] for f in json.loads(run().stdout)["findings"]]
            if "REG010" not in codes:
                problems.append(f"a heading reading {written!r} was not reported. It binds "
                                "every entry under it and no `trigger` records it, so "
                                "nothing will ever report it going stale")

        # A `#` inside a fenced block is a comment in somebody's example. A bash snippet
        # saying `# rigenerato il 2026-09-30` was reported as a heading carrying a date, and
        # a false finding costs the trip to the document.
        for written in ("~~~bash\n# rigenerato il 2026-09-30\n~~~",
                        "```bash\n# rigenerato il 2026-09-30\n```",
                        "```yaml\n# entro il 2026-09-30\nentries: {}\n```"):
            (root / "products" / "beta" / "OPEN.md").write_text(head(written))
            codes = [f["code"] for f in json.loads(run().stdout)["findings"]]
            if "REG010" in codes:
                problems.append("a comment inside a fenced block was reported as a heading "
                                "carrying a date: it is somebody's example, and the finding "
                                "sends a reader to a document that was right")

        for written in ("## Cost to reverse MEDIUM: changing it later costs a migration",
                        "## Cost to reverse HIGH"):
            (root / "products" / "beta" / "OPEN.md").write_text(head(written))
            codes = [f["code"] for f in json.loads(run().stdout)["findings"]]
            if "REG010" in codes:
                problems.append(f"a heading reading {written!r} was reported: the check is "
                                "matching headings rather than dates in them")

        # `decide_with`: the pairing an ordering cannot express. Same resolution as
        # `depends_on`, because a pairing with an entry nobody can find reads as one that
        # was honoured, and the self reference on top -- a field that looks filled in and
        # binds the entry to nothing.
        pair = lambda peer: fm("entries:\n  OD-004:\n    status: open\n"
                               "    cost_to_reverse: high\n"
                               "    default_in_force: none\n"
                               f"    decide_with: [{peer}]\n")
        for peer, why in (("OD-404", "an entry no register declares"),
                          ("OD-004", "itself")):
            (root / "products" / "beta" / "OPEN.md").write_text(pair(peer))
            codes = [f["code"] for f in json.loads(run().stdout)["findings"]]
            if "REG005" not in codes:
                problems.append(f"an entry to be decided with {why} was not reported, so "
                                "the register vouches for a pairing that binds it to "
                                "nothing")
        (root / "products" / "beta" / "OPEN.md").write_text(pair("OD-001"))
        codes = [f["code"] for f in json.loads(run().stdout)["findings"]]
        if "REG005" in codes:
            problems.append("a `decide_with` naming an entry that exists in another "
                            "register was reported: the pairing reaches across registers "
                            "by design, exactly as `depends_on` does")
    return problems


@check("the extractor keeps the provenance the converter throws away")
def _extract_keeps_provenance():
    # anydoc has no slide and no page in its document model: a whole deck comes back as one
    # flat stream. Everything that puts a claim back on slide 4 is written here, so it is
    # this repository's to test. All three pieces are pure, which is the point: a CI runner
    # with no converter installed still checks the part that would silently degrade.
    x = _load(EXTRACT, "extract")
    problems = []

    def deck(n: int) -> bytes:
        ids = "".join(f'<p:sldId id="{255 + i}" r:id="rId{i}"/>' for i in range(1, n + 1))
        pres = ('<?xml version="1.0"?><p:presentation xmlns:p="x">'
                f"<p:sldIdLst>{ids}</p:sldIdLst></p:presentation>")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("ppt/presentation.xml", pres)
            for i in range(1, n + 1):
                z.writestr(f"ppt/slides/slide{i}.xml", f"<p:sld>slide {i}</p:sld>")
        return buf.getvalue()

    # Lazy, and asserted as lazy. Every slice is a whole copy of the package, so returning
    # them together costs deck size times slide count: forty slides of a thirty megabyte
    # deck wanted more than a gigabyte. Checking only the slices would pass again the day
    # somebody collects them into a list, which is what this used to do while its own
    # docstring claimed one existed at a time.
    produced = x.slice_pptx(deck(3))
    if not isinstance(produced, types.GeneratorType):
        problems.append("slice_pptx stopped being lazy: each slice is a full copy of the "
                        "package, and holding all of them is deck size times slide count")
    slices = list(produced)
    if len(slices) != 3:
        problems.append(f"a three slide deck sliced into {len(slices)} packages: without "
                        "one per slide, every claim in a deck is located to the file and "
                        "checking it means reading the deck")
    for i, s in enumerate(slices, 1):
        z = zipfile.ZipFile(io.BytesIO(s))
        if (kept := z.read("ppt/presentation.xml").decode().count("<p:sldId ")) != 1:
            problems.append(f"slice {i} kept {kept} slides in its running order: the split "
                            "did not split, and the numbers it reports are wrong")
        # The trap: writestr stamps the offset of the copy onto the ZipInfo it is handed,
        # so copying by ZipInfo corrupts the source archive and every slice after the first
        # comes back short. Slice 3 having all four parts is the assertion.
        if len(z.namelist()) != 4:
            problems.append(f"slice {i} lost parts of the package: {z.namelist()}")

    if list(x.slice_pptx(b"PPT legacy binary, not a zip")):
        problems.append("something that is not a package was sliced anyway: the caller "
                        "reads an empty list as its cue to convert the file whole")

    # In the report the provenance line is itself a heading. A `# Title` arriving inside a
    # block would outrank it, and the boundary between one document and the next is what
    # tells a classifier which file a claim came from.
    body = x.demote("# Title\n\n```\n# not a heading\n```\n\n## Section")
    if not ("\n" + body).count("\n### Title") or "#### Section" not in body:
        problems.append("a heading inside a block was not demoted below the provenance "
                        "heading: extract.md stops saying where a document ends")
    if "\n# not a heading" not in body:
        problems.append("a comment inside a code fence was rewritten as a heading")

    # Found on a deck built to look like a real one. The slide was the architecture diagram
    # with the word "Architettura" on it, and it went unflagged because the speaker note
    # underneath carried it over the threshold. The question the threshold answers is
    # whether the slide is a picture, and a picture with a talkative presenter is one.
    drawn = "Architettura\n\n> Nota del relatore che spiega a voce tutta l'architettura."
    if x.on_slide_chars(drawn) >= 40:
        problems.append("speaker notes count towards the text on a slide: a diagram with a "
                        "chatty note under it stops being flagged, and that is the slide "
                        "the whole visual review exists to catch")
    if x.on_slide_chars("Prezzi 2026 per fascia di volume, con sconti a scaglioni") < 40:
        problems.append("a slide with a sentence on it was called text-poor")

    # A deck exported to PDF, told apart by the geometry poppler already reports. Both
    # halves are pure so a runner with no poppler still checks them, which is where it
    # matters: the branch only runs on a machine that has it.
    for meta, want, what in [
        ("Pages:  9\nPage size:       960 x 540 pts\n", True, "a 16:9 deck"),
        ("Pages:  9\nPage size:       720 x 540 pts\n", True, "a 4:3 deck"),
        ("Pages:  5\nPage size:       595.25 x 842 pts (A4)\n", False, "an A4 report"),
        # Landscape A4 is 1.41 and 4:3 is 1.33, so no ratio separates them. Included on
        # purpose: the flag feeds a measure taken against the document's own pages, and a
        # dense report has nothing thin against its own median, so the cost is nil.
        ("Pages:  5\nPage size:       842 x 595.25 pts\n", True, "a landscape A4"),
        ("Pages:  5\n", False, "a PDF whose geometry pdfinfo did not report"),
    ]:
        if x.is_deck(meta) != want:
            problems.append(f"{what} was {'not ' if want else ''}read as a presentation: "
                            "on a slide a thin page is a diagram, and on a report it is a "
                            "short page, and the two want opposite responses")

    # The distribution measured off the deck that prompted this. Page 7 was the only one a
    # forty character threshold caught; 1, 5 and 8 are the ones it missed, and 5 is the
    # slide naming the source systems and promising real time, all of it inside screenshots.
    got = x.thin_against_median({1: 120, 2: 1589, 3: 1248, 4: 1111, 5: 474,
                                 6: 1055, 7: 11, 8: 267, 9: 2185})
    if got != [1, 5, 7, 8]:
        problems.append(f"the thin pages of a real deck came back as {got}, not [1, 5, 7, 8]")
    if x.thin_against_median({1: 900, 2: 1000, 3: 1100}):
        problems.append("a deck with even pages had some of them called thin: the measure "
                        "is against the document's own pages, so an even one flags nothing")
    if x.thin_against_median({}):
        problems.append("an empty page table produced flagged pages")

    blocks = x.split_on_headings("req.docx", "intro\n\n# One\n\nalpha\n\n## Two\n\nbeta")
    if (got := [b.locator for b in blocks]) != ["preamble", "§ One", "§ Two"]:
        problems.append(f"sections came back located as {got}: a heading is the only "
                        "locator a document with no pages has")
    joined = "".join(b.text for b in blocks)
    if any(w not in joined for w in ("intro", "alpha", "beta")):
        problems.append("splitting a document on its headings dropped text from it")

    return problems



@check("a count of findings written in prose is the count the fixture produces")
def _fixture_counts_are_measured():
    # Three times the number of findings in `audit/dirty-repo` was written into prose and
    # three times it went stale: eleven, then thirteen against a fixture producing twelve,
    # then thirteen again on the day `REG006` was added, when thirteen was already the count
    # before it. Every one of those was written in a file whose subject is documents going
    # out of date, and nothing reported any of them.
    #
    # The count stays in prose rather than being deleted, because "four errors and fourteen
    # warnings, by construction" is what tells a reader the fixture is planted and not
    # merely dirty, and a pointer to a command they have to run says much less. What was
    # missing is the thing that makes a number in prose safe: something that reads it.
    #
    # The fixture is the authority, not this file. It is built into a temporary directory
    # and measured, so the check cannot be cleared by editing a number here.
    words = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
             "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
             "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
             "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20}
    # Past twenty the fixture kept growing and the vocabulary did not, so the sentence
    # stopped matching and this check reported that nobody states the count any more --
    # correct, and for the wrong reason. The compound forms first in the alternation, or
    # `twenty` matches the first half of `twenty-one` and the number reads as 20.
    words.update({f"twenty-{w}": 20 + n for w, n in
                  (("one", 1), ("two", 2), ("three", 3), ("four", 4), ("five", 5),
                   ("six", 6), ("seven", 7), ("eight", 8), ("nine", 9))})
    words["thirty"] = 30
    ordered = sorted(words, key=len, reverse=True)
    stated = re.compile(r"\b(" + "|".join(ordered) + r")\s+errors?\s+and\s+"
                        r"(" + "|".join(ordered) + r")\s+warnings?\b", re.I)

    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        gen = ROOT / "evals" / "fixtures" / "generators" / "audit.py"
        r = subprocess.run([sys.executable, str(gen), tmp],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return [f"the audit fixture would not build, so its documented count cannot be "
                    f"checked: {r.stderr.strip() or r.stdout.strip()}"]

        measured = {}
        for name in ("dirty-repo", "clean-repo"):
            v = subprocess.run([sys.executable, str(VALIDATE), "--root",
                                str(Path(tmp) / name), "--json"],
                               capture_output=True, text=True)
            try:
                d = json.loads(v.stdout)
            except json.JSONDecodeError:
                problems.append(f"the validator returned nothing readable on {name}")
                continue
            measured[name] = (d["errors"], d["warnings"])

        # The fixture that must report nothing. Its README says a checker finding something
        # here is inventing, which is a claim about output and belongs with the other one.
        if measured.get("clean-repo", (0, 0)) != (0, 0):
            e, w = measured["clean-repo"]
            problems.append(f"audit/clean-repo reports {e} error(s) and {w} warning(s). "
                            "Its whole description is that anything reported there is "
                            "invented, and a fixture that contradicts its own description "
                            "teaches you to read past its output")

        if "dirty-repo" not in measured:
            return problems
        want = measured["dirty-repo"]

        found = 0
        for rel in ("evals/fixtures/README.md", "evals/behaviour/audit/cases.yaml"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            for m in stated.finditer(text):
                found += 1
                got = (words[m.group(1).lower()], words[m.group(2).lower()])
                line = text[:m.start()].count("\n") + 1
                if got != want:
                    problems.append(
                        f"{rel}:{line} says {got[0]} errors and {got[1]} warnings; "
                        f"audit/dirty-repo produces {want[0]} and {want[1]}. Either the "
                        "fixture changed and the sentence did not, or the sentence was "
                        "wrong when it was written")
        if not found:
            problems.append(
                "no file states what audit/dirty-repo produces any more. The count is "
                "what tells a reader the fixture is planted rather than merely dirty; if "
                "it is gone on purpose, this check is what has to go with it")
    return problems


@check("a change set is checked against the contract that authorizes it")
def _pull_request_binding():
    # The four `PR` checks are the only ones that read something outside the repository,
    # and that is what this pins: they must stay silent without that context. A check that
    # fired on a plain `--root` run would report every desk in the project as unauthorized
    # work, and would be switched off within the day.
    def fm(**kw):
        return "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"

    chg = lambda status: fm(
        schema="framework/change-contract/v1", artifact_type="change-contract",
        lifecycle="immutable", status=status, id="CHG-001", owners="[o]",
        created="2026-01-01 09:00", icg="ICG-001", derives_from="[SIG-001]") + (
        "<!-- section: what-changes -->\n# 1\n"
        "<!-- section: what-must-not-change -->\n# 2\n"
        "<!-- section: how-we-know-it-worked -->\n# 3\n")

    icg = fm(schema="framework/impact-classification/v1",
             artifact_type="impact-classification", lifecycle="immutable",
             status="accepted", id="ICG-001", owners="[o]", created="2026-01-01 09:00",
             routing="\n  SIG-001: architecture",
             impacts="\n  SIG-001: [data]") + (
        "<!-- section: intake -->\n# 1\n<!-- section: classification -->\n# 2\n"
        "<!-- section: open-questions -->\n# 3\n")

    dc = fm(schema="framework/data-contract/v1", artifact_type="data-contract",
            lifecycle="living", status="active", id="DC-001", owners="[o]",
            created="2026-01-01 09:00", last_review="2026-01-01 09:00", version="1.0.0",
            products="[alpha]", consumers="[alpha]") + "# DC\n"

    def run(status, text=None, changed=None):
        with tempfile.TemporaryDirectory() as tmp:
            for rel, body in {"CHG-001.md": chg(status), "ICG-001.md": icg,
                              "products/alpha/DC-001.md": dc}.items():
                f = Path(tmp) / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(body)
            extra = [] if text is None else ["--pr-text", text]
            if changed is not None:
                cf = Path(tmp) / "changed.txt"
                cf.write_text("\n".join(changed))
                extra += ["--changed-files", str(cf)]
            r = subprocess.run(
                [sys.executable, str(VALIDATE), "--root", tmp, "--json",
                 "--stale-days", "36500", *extra], capture_output=True, text=True)
            if r.returncode not in (0, 1) or not r.stdout.strip():
                return None
            return {f["code"] for f in json.loads(r.stdout)["findings"]
                    if f["code"].startswith("PR")}

    problems = []
    for want, args, what in [
        (set(), dict(status="approved"),
         "no pull request context at all, which must report nothing"),
        ({"PR001"}, dict(status="approved", text="tidy up the logging"),
         "a change set citing no contract"),
        (set(), dict(status="approved", text="tidy up\n\nno-chg: a typo in a comment"),
         "the declared exception, with its reason"),
        ({"PR001"}, dict(status="approved", text="tidy up\n\nno-chg:"),
         "the exception with no reason, which is the check deleted with extra steps"),
        ({"PR002"}, dict(status="approved", text="implements CHG-404"),
         "a contract that is not in the repository"),
        ({"PR003"}, dict(status="draft", text="implements CHG-001"),
         "implementing a draft"),
        ({"PR003"}, dict(status="rolled-back", text="implements CHG-001"),
         "citing a contract that was rolled back"),
        (set(), dict(status="approved", text="implements CHG-001"),
         "an approved contract with no diff supplied: PR004 cannot run and must not guess"),
        ({"PR004"}, dict(status="approved", text="implements CHG-001",
                         changed=["src/app.py"]),
         "a data impact whose change set touches no data contract"),
        (set(), dict(status="approved", text="implements CHG-001",
                     changed=["src/app.py", "products/alpha/DC-001.md"]),
         "the same change set once the contract moves with it"),
        (set(), dict(status="approved", text="implements CHG-001",
                     changed=["./products/alpha/DC-001.md"]),
         "a diff that writes its paths with a leading ./"),
    ]:
        got = run(**args)
        if got is None:
            problems.append(f"the validator crashed on {what}")
        elif got != want:
            problems.append(f"{what}: expected {sorted(want) or 'nothing'}, got "
                            f"{sorted(got) or 'nothing'}")
    return problems


@check("the migration tool reconstructs the version a project pins")
def _migration_is_executable():
    # `P-16` is a procedure nobody can execute unless the old validator can be got hold of.
    # It is not kept anywhere: it is rebuilt from this repository's history, at the commit
    # where the registry last declared the version the project pinned. So what this asserts
    # is the one thing that would silently stop being true -- that every version this
    # framework has ever declared is still reachable, and that the note explaining it is
    # still beside the number.
    migrate = _load(ROOT / "skills" / "audit" / "scripts" / "migrate.py", "migrate")
    registry = (ROOT / "schemas" / "artifact-types.yaml").read_text(encoding="utf-8")
    notes = {to for _, to, _ in migrate.migration_notes(registry)}
    problems = []

    # A check reports the same code on the same file many times -- one per entry of a
    # register, one per unresolved citation. Keyed on the pair alone, three findings and
    # five findings are the same key, and a version that made a check noisier on a file it
    # already reported would come out of the tool as "nothing new".
    seen = collections.Counter()
    keys = [migrate.key({"code": "REG005", "path": "OPEN.md"}, seen) for _ in range(3)]
    if len(set(keys)) != 3:
        problems.append("three findings with the same code and path collapse to "
                        f"{len(set(keys))} key(s): a check getting noisier would read as "
                        "nothing having changed")

    # The two the tool clears by writing a number rather than by anybody editing a
    # document. They are separated in the report and skipped by the adopt gate, and those
    # two have to be the same list: when they were not, the report told the reader to go
    # and fix something that `--adopt` was already ignoring.
    # A PROJECT THAT PINS HAS TO BE ABLE TO ADOPT. `FW003` fires the moment the framework
    # moves past the pin, it landed in NEW, `--adopt` refuses while NEW is non-empty, and the
    # only thing that clears `FW003` is `--adopt` writing the pin. Pinning made adopting
    # impossible, and the way out was deleting the pin -- the field's purpose undone by the
    # tool that exists to move it. Asserted end to end, because the deadlock was invisible in
    # every list: each name was a real check and each check was in the catalog.
    with tempfile.TemporaryDirectory() as tmp:
        proj = Path(tmp)
        # A commit whose registry declares a version BEHIND this one, found rather than
        # counted back to: one of the numbers in this history was declared and withdrawn, so
        # `HEAD~4` picked a project that was ahead of the framework and the tool refused it
        # for the right reason -- which tested the refusal instead of the deadlock.
        # NOT WHILE THE BUMP IS UNCOMMITTED. Between editing `version:` and committing it,
        # the number in the working tree belongs to no commit, and everything downstream of
        # that -- what `--adopt` writes, which commit declares what -- describes a framework
        # state no consumer can be in. This check went red exactly there, on every bump, and
        # a check that is red while you work is one you commit through.
        head_registry = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"HEAD:{migrate.REGISTRY_REL}"],
            capture_output=True, text=True)
        committed = (migrate.registry_version(head_registry.stdout)
                     if head_registry.returncode == 0 else None)
        if committed != REGISTRY["version"]:
            return problems + [f"NOT RUN: the working tree declares "
                               f"{REGISTRY['version']} and the last commit declares "
                               f"{committed}. Commit the bump and run this again -- what "
                               "`--adopt` writes cannot be asserted against a version no "
                               "commit has."]

        now = migrate.semver(REGISTRY["version"])
        old_commit = old_version = None
        for sha in subprocess.run(["git", "-C", str(ROOT), "rev-list", "-40", "HEAD"],
                                  capture_output=True, text=True).stdout.split():
            v = migrate.registry_version(subprocess.run(
                ["git", "-C", str(ROOT), "show", f"{sha}:{migrate.REGISTRY_REL}"],
                capture_output=True, text=True).stdout)
            sv = migrate.semver(v) if v else None
            if sv and now and sv < now:
                old_commit, old_version = sha, v
                break
        if old_version:
            cfg = proj / "framework.yaml"
            cfg.write_text(f'framework_version: "{old_version}"\n'
                           f'framework_commit: "{old_commit}"\n')
            subprocess.run([sys.executable,
                            str(ROOT / "skills" / "audit" / "scripts" / "migrate.py"),
                            "--root", str(proj), "--adopt"],
                           capture_output=True, text=True)
            after = cfg.read_text()
            if REGISTRY["version"] not in after:
                problems.append("a project that pins could not adopt: `FW003` is what the "
                                "pin produces when the framework moves, and if it counts as "
                                "migration work the only way to adopt is to stop pinning")
            elif old_commit[:12] in after:
                problems.append("adopting moved the version and left the pin behind, which "
                                "is `FW003` for the rest of the week")

    for code in migrate.ADOPT_CLEARS:
        if code not in CHECKS["checks"]:
            problems.append(f"migrate.py treats {code} as cleared by --adopt, and it is "
                            "not in the catalog")

    log = subprocess.run(["git", "log", "--format=%H", "--", "schemas/artifact-types.yaml"],
                         cwd=ROOT, capture_output=True, text=True)
    if log.returncode != 0:
        return ["git history is not available here, so the check is not running"]

    seen = []
    for sha in log.stdout.split():
        show = subprocess.run(["git", "show", f"{sha}:schemas/artifact-types.yaml"],
                              cwd=ROOT, capture_output=True, text=True)
        v = migrate.registry_version(show.stdout) if show.returncode == 0 else None
        if v and v not in seen:
            seen.append(v)

    for v in seen:
        if migrate.semver(v) is None:
            continue          # the integers this file used before it carried three numbers
        sha, why = migrate.commit_declaring(v, ROOT)
        if sha is None:
            problems.append(f"{v}: {why}")
        # THE CURRENT VERSION USED TO BE EXEMPT, AND THAT IS WHERE A MALFORMED NOTE HIDES.
        # The parser wants a full stop after the number; a note written with a comma is not
        # a note, and nothing said so until the next bump made it somebody else's problem --
        # by which time the note that explains the version a project is pinned to is the one
        # that silently does not exist. The note is written with the bump, so it can be
        # required with the bump.
        if v not in notes:
            problems.append(f"{v}: no `X -> {v}` note in the registry. The number moved and "
                            "nothing says what it asks a project to do, which is the half "
                            "of `FW001` a version comparison cannot supply")
    return problems


@check("a run that could not have read the repository says so instead of reporting it clean")
def _wrong_arguments_are_not_a_clean_report():
    # `audit/SKILL.md` has said from its first version that "running it against the wrong
    # directory produces a clean report, and a clean report on the wrong repository is worse
    # than an error". Nothing enforced it. Pointed at a path that is not there, the validator
    # scanned nothing, said the repository declares no framework version, and exited 0 --
    # three true sentences whose only available reading was that the project is fine.
    #
    # The other half is the same failure with a stack trace on top: `framework.yaml` is the
    # first file read, so a stray quote in it killed both tools before either had looked at a
    # document, with a message naming a unicode string and no path at all.
    migrate = ROOT / "skills" / "audit" / "scripts" / "migrate.py"
    problems = []

    def run(script, *args):
        r = subprocess.run([sys.executable, str(script), *args],
                           capture_output=True, text=True)
        return r.returncode, (r.stdout + r.stderr)

    with tempfile.TemporaryDirectory() as tmp:
        missing = str(Path(tmp) / "not-here")
        broken = Path(tmp) / "broken"
        broken.mkdir()
        # The version is `N` because a literal one here is the defect `_version_is_not_restated`
        # exists to catch, and it caught this line. What is being tested is a quote that never
        # closes; which number it fails to close is not part of it.
        (broken / "framework.yaml").write_text('framework_version: "N\nchecks: [\n')

        for script, args, what in [
            (VALIDATE, ["--root", missing], "the validator pointed at no directory"),
            (migrate, ["--root", missing], "the migration tool pointed at no directory"),
            (migrate, ["--root", str(broken), "--framework", tmp],
             "a --framework that holds no registry"),
            (VALIDATE, ["--root", str(broken)],
             "a framework.yaml that does not parse, read by the validator"),
            (migrate, ["--root", str(broken)],
             "a framework.yaml that does not parse, read by the migration tool"),
        ]:
            code, out = run(script, *args)
            if code == 0:
                problems.append(f"{what}: exited 0. Nothing distinguishes it from a run "
                                "that had something to check and found it correct")
            if "Traceback" in out:
                problems.append(f"{what}: died with a traceback rather than a sentence")
            # The path is what turns the message into a repair. Either of the two directories
            # involved will do: what must not happen is a message that names neither.
            if not any(p in out for p in (missing, str(broken), tmp)):
                problems.append(f"{what}: the message names no path, so it says which of "
                                f"the two arguments was wrong to nobody: {out.strip()[:120]}")
    return problems


@check("a pinned framework commit is checked against the one doing the checking")
def _the_pin_is_read():
    # An unchecked pin is a comment, and this is the whole value of the field: a project
    # that writes the commit down is claiming its report was produced by that code, and
    # nothing but this compares the claim with the process actually running.
    #
    # The two silences are asserted as hard as the two findings. No pin at all is the normal
    # state and must stay quiet, or the field becomes a checklist item; and a framework
    # installed rather than cloned has no history to ask, where unverifiable is a different
    # claim from violated -- that one cannot be exercised here, because this repository is
    # always a checkout when the self check runs, so it is stated rather than tested.
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                          capture_output=True, text=True)
    if head.returncode != 0:
        return ["git history is not available here, so the check is not running"]
    sha = head.stdout.strip()
    version = REGISTRY["version"]
    problems = []

    def codes(config: str):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "framework.yaml").write_text(config)
            r = subprocess.run([sys.executable, str(VALIDATE), "--root", tmp, "--json",
                                "--stale-days", "36500"], capture_output=True, text=True)
            if r.returncode not in (0, 1) or not r.stdout.strip():
                return None
            return {f["code"] for f in json.loads(r.stdout)["findings"]}

    declared = f'framework_version: "{version}"\n'
    for config, want, what in [
        (declared, False, "a project that pins nothing, which is the ordinary state"),
        (declared + f'framework_commit: "{sha}"\n', False, "a pin that is being honoured"),
        (declared + f'framework_commit: "{sha[:10]}"\n', False, "the same pin, abbreviated"),
        (declared + 'framework_commit: "0123456789abcdef"\n', True,
         "a pin naming a commit that is not the one running"),
        (declared + 'framework_commit: "main"\n', True,
         "a branch name, which is a pin that moves and therefore not a pin"),
    ]:
        got = codes(config)
        if got is None:
            problems.append(f"the validator crashed on {what}")
        elif ("FW003" in got) != want:
            problems.append(f"{what} was {'not ' if want else ''}reported")
    return problems

@check("a register's two halves carry the same ids, and a generated view is not one of them")
def _register_halves():
    # THE FAILURE THAT PUT THIS HERE WAS A SILENCE, AND SILENCES ARE WHAT THIS SUITE IS FOR.
    # Until 3.0.0 the three registers kept a map in front matter and repeated its fields in
    # the body, and `risks: {}` under a full §state table validated clean: every check that
    # joins risks reads the map, so all of them went quiet at once while the document still
    # showed the rows to a person. Four ways of looking, all at the blank half.
    #
    # The repair was to stop keeping the fields twice, so what is asserted is what is left:
    # the same ids in both halves, and the three exemptions that make the check survivable --
    # a generated view is not the body, a decided entry keeps its row and loses its prose,
    # and either body shape counts.
    def repo(files: dict[str, str]) -> set[str] | None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "framework.yaml").write_text(
                f"framework_version: {REGISTRY['version']}\n")
            for rel, text in files.items():
                f = root / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(text)
            r = subprocess.run([sys.executable, str(VALIDATE), "--root", str(root),
                                "--json", "--stale-days", "36500"],
                               capture_output=True, text=True)
            if not r.stdout.strip():
                return None
            return {f["code"] for f in json.loads(r.stdout)["findings"]}

    def rsk(risks: str, body: str) -> dict[str, str]:
        return {"products/alpha/product.yaml":
                    ("---\nschema: framework/product-manifest/v1\n"
                     "artifact_type: product-manifest\nlifecycle: living\nstatus: active\n"
                     "products: [alpha]\nowners: [o]\ncreated: 2026-01-01 09:00\n"
                     "last_review: 2026-08-01 09:00\n---\n\n# alpha\n"),
                "products/alpha/RSK.md":
                    ("---\nschema: framework/risk-register/v1\n"
                     "artifact_type: risk-register\nlifecycle: living\nstatus: active\n"
                     "products: [alpha]\nowners: [o]\ncreated: 2026-01-01 09:00\n"
                     "last_review: 2026-08-01 09:00\n" + risks + "---\n\n# Risks\n\n"
                     "<!-- section: state -->\n## State\n\n"
                     "| ID | Risk | Mitigation | Owner | Reviewed |\n|---|---|---|---|---|\n"
                     + body)}

    one = "risks:\n  RSK-001:\n    category: technical\n    state: open\n"
    row = "| RSK-001 | the thing | the mitigation | o | 2026-08-01 |\n"
    problems = []

    for what, files, want in [
        ("a risk in the map and in §state", rsk(one, row), False),
        ("a map with a row §state does not carry", rsk(one, ""), True),
        ("a §state row the map does not declare", rsk("risks: {}\n", row), True),
        ("an empty map under an empty §state", rsk("risks: {}\n", ""), False),
    ]:
        got = repo(files)
        if got is None:
            problems.append(f"the validator produced nothing on {what}")
        elif ("REG015" in got) != want:
            problems.append(f"{what} was {'not ' if want else ''}reported")

    # `risks:` absent entirely is `REG004` and not `REG015`: there is no map to compare, and
    # the finding has to say the register is unreadable rather than that a row is missing.
    got = repo(rsk("", row))
    if got is not None:
        if "REG004" not in got:
            problems.append("a risk register with no `risks:` at all was not reported by REG004")
        if "REG015" in got:
            problems.append("a register with no map was reported as a half-written row, "
                            "which sends somebody to add a row rather than the map")

    # THE GENERATED UNION IS NOT THE BODY OF THE REGISTER IT SITS IN. `--emit-index` composes
    # every register in the repository into §5 at the root, ids in the first column, and
    # those entries belong to the registers under each product. Read as body, the root
    # register would be reported for entries it correctly does not declare -- a finding on
    # exactly the arrangement the framework asks for.
    union = ("---\nschema: framework/open-register/v1\nartifact_type: open-register\n"
             "lifecycle: living\nstatus: active\nowners: [o]\ncreated: 2026-01-01 09:00\n"
             "last_review: 2026-08-01 09:00\nentries:\n  OD-001:\n    status: open\n"
             "    cost_to_reverse: low\n    products: [all]\n"
             "    default_in_force: nothing\n---\n\n# Open\n\n"
             "### OD-001 - the one at the root\n\n"
             "<!-- generated: open-union -->\n"
             "| ID | Register |\n|---|---|\n| OD-014 | products/alpha/OPEN.md |\n"
             "<!-- /generated -->\n")
    got = repo({"OPEN.md": union})
    if got is not None and "REG015" in got:
        problems.append("an id inside the generated union was read as the root register's "
                        "own body, so the composed view reports the registers it composes")

    # A decided entry keeps its row in the map and loses its prose from §1, which is the one
    # document in the framework that is supposed to get shorter.
    decided = ("---\nschema: framework/open-register/v1\nartifact_type: open-register\n"
               "lifecycle: living\nstatus: active\nowners: [o]\ncreated: 2026-01-01 09:00\n"
               "last_review: 2026-08-01 09:00\nentries:\n  OD-001:\n    status: decided\n"
               "    cost_to_reverse: low\n    products: [all]\n"
               "    default_in_force: nothing\n    closed_by: DEC-001\n---\n\n# Open\n\n"
               "# §4 - closed\n\n- 2026-02-01 OD-001 -> DEC-001\n")
    got = repo({"OPEN.md": decided})
    if got is not None and "REG015" in got:
        problems.append("a decided entry was reported for having left §1, which is what "
                        "taking a decision is supposed to do")

    # EITHER BODY SHAPE COUNTS, AND THIS IS THE ONE THE HEADING BRANCH TOLERATES. An open
    # register writing its entries as a table instead of `### OD-001 - title` is the shape
    # `rows_of` exists for, and the prefix filter must not take it away: the ids in that
    # first column are the ones this type declares.
    as_table = ("---\nschema: framework/open-register/v1\nartifact_type: open-register\n"
                "lifecycle: living\nstatus: active\nowners: [o]\ncreated: 2026-01-01 09:00\n"
                "last_review: 2026-08-01 09:00\nentries:\n  OD-001:\n    status: open\n"
                "    cost_to_reverse: low\n    products: [all]\n"
                "    default_in_force: nothing\n---\n\n# Open\n\n"
                "| ID | Question |\n|---|---|\n| OD-001 | the one written as a row |\n")
    got = repo({"OPEN.md": as_table})
    if got is not None and "REG015" in got:
        problems.append("an open register writing its entries as a table was reported, so "
                        "the shape `rows_of` exists for is the shape that fails")

    # And a row the map does not declare is still reported, or the tolerated shape would be
    # a way to stop being checked rather than a way to write the register.
    got = repo({"OPEN.md": as_table + "| OD-002 | the row nothing declares |\n"})
    if got is not None and "REG015" not in got:
        problems.append("a table row the map does not declare was not reported, so the "
                        "tolerated shape is a way out of the check")

    # A FOREIGN PREFIX IN A FIRST CELL IS A CITATION AND NOT A HALF-WRITTEN ENTRY, AND THE
    # COST IS ASSERTED HERE RATHER THAN LEFT IMPLICIT. `entries:` is schema-forbidden to
    # hold a `DEC`, so a `DEC` in the body can only be cited -- and the same silence covers
    # a mistyped prefix, which is what this filter is paid for.
    got = repo({"OPEN.md": as_table + "| DEC-001 | the decision this row argues about |\n"})
    if got is not None and "REG015" in got:
        problems.append("a `DEC` cited in the first cell of a table was read as an entry "
                        "the map is missing, which `entries:` cannot hold")
    return problems


@check("a reference to a per-product identifier names the product")
def _qualified_references():
    # `DEC` lives at the root and its template prescribes `derives_from: [..., SIG-NNN]`,
    # while signal logs are one per product: two products numbering their signals from 001
    # made every such reference ambiguous, and it resolved itself -- whichever register was
    # read last won. From 3.0.0 the reference names the product and the *declaration* does
    # not, which is the asymmetry worth asserting: a log under `products/alpha/` has already
    # said whose its rows are by sitting there.
    def repo(dec_ref: str, dec_products: str = "[alpha]") -> set[str] | None:
        files = {
            "products/alpha/product.yaml":
                ("---\nschema: framework/product-manifest/v1\n"
                 "artifact_type: product-manifest\nlifecycle: living\nstatus: active\n"
                 "products: [alpha]\nowners: [o]\ncreated: 2026-01-01 09:00\n"
                 "last_review: 2026-08-01 09:00\n---\n\n# alpha\n"),
            # The declaration, bare, in the register whose directory says whose it is.
            "products/alpha/LOG.md":
                ("---\nschema: framework/signal-log/v1\nartifact_type: signal-log\n"
                 "lifecycle: append-only\nstatus: active\nproducts: [alpha]\n"
                 "owners: [o]\ncreated: 2026-01-01 09:00\n---\n\n# Log\n\n"
                 "| ID | What |\n|---|---|\n| SIG-001 | the observation |\n"),
            "decisions/DEC-001-slug.md":
                ("---\nschema: framework/decision-record/v1\n"
                 "artifact_type: decision-record\nid: DEC-001\nlifecycle: immutable\n"
                 "status: accepted\nscope: architecture\n"
                 f"products: {dec_products}\nowners: [o]\ncreated: 2026-01-01 09:00\n"
                 f"derives_from: [{dec_ref}]\nleaves_open: []\n---\n\n# DEC-001\n"),
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "framework.yaml").write_text(
                f"framework_version: {REGISTRY['version']}\n")
            for rel, text in files.items():
                f = root / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(text)
            r = subprocess.run([sys.executable, str(VALIDATE), "--root", str(root),
                                "--json", "--stale-days", "36500"],
                               capture_output=True, text=True)
            if not r.stdout.strip():
                return None
            return {f["code"] for f in json.loads(r.stdout)["findings"]}

    problems = []
    cases = [
        # the reference, the code that must appear, the code that must not, what it is
        ("alpha:SIG-001", None, {"FM002", "REF001", "REF007", "REF008"},
         "a qualified reference to a signal its product declares"),
        ("SIG-001", "FM002", set(),
         "a bare reference to a signal, which the schema's reference pattern rejects"),
        ("beta:SIG-001", "REF007", set(),
         "a qualifier naming a product this repository does not have"),
        ("alpha:SIG-404", "REF001", {"REF007"},
         "a qualified reference to a signal that product's register does not declare"),
    ]
    for ref, want, forbidden, what in cases:
        got = repo(ref)
        if got is None:
            problems.append(f"the validator produced nothing on {what}")
            continue
        if want and want not in got:
            problems.append(f"{what} was not reported by {want}: got {sorted(got)}")
        for code in forbidden & got:
            problems.append(f"{what} was reported by {code}, which is a different claim")

    # THE QUALIFIER AGAINST `products:`, WHICH IS THE HALF NO PATTERN CAN SEE. A decision
    # resolving a signal in a product it does not claim to bind is either missing a product
    # from the field every downstream view is built from, or citing a signal copied out of
    # another document.
    got = repo("alpha:SIG-001", dec_products="[gamma]")
    if got is not None and "REF008" not in got:
        problems.append("a qualifier outside the document's own `products:` was not reported")
    got = repo("alpha:SIG-001", dec_products="[all]")
    if got is not None and "REF008" in got:
        problems.append("`products: [all]` was read as naming no product, so a decision "
                        "that binds every product cannot cite any product's signal")
    return problems


@check("the eval case files load, and the counts the README prints come from the same parse")
def _eval_cases_load():
    # THE MEASURING EQUIPMENT TURNS ON. This is not a check about the semantics of a
    # document, which is what the rest of this suite is for and what the freeze covers: it is
    # a check that the instruments switch on, and it is here because they did not. `business`
    # arrived in 2.8.11 carrying `per il management: dove siamo` as an unquoted scalar, so
    # `yaml.safe_load` at `evals/trigger/run.py:177` raised, the runner died before reaching
    # a model, and it did so on every skill rather than only on the new one. It stayed broken
    # for four days and nothing could have said so: the eval suite needs a model, which is
    # why it is not in CI, and the cost of that is a data file whose breakage is invisible
    # until somebody runs it by hand. Parsing needs no model.
    #
    # AND THE NUMBERS FALL OUT OF THE SAME PARSE. `evals/README.md` states how many prompts
    # there are and, in the results table, how many cases each skill has as the denominator
    # of its score. Both were written by hand and both were wrong the moment the set grew --
    # it said 112 while holding 118. A number in prose that nothing derives is the thing this
    # framework spends its own rules forbidding, and this is the cheap half of deriving it:
    # not generating the line, but failing when it stops being true.
    problems = []
    trigger = ROOT / "evals" / "trigger" / "cases.yaml"
    files = [trigger, ROOT / "evals" / "trigger" / "fixtures.yaml"]
    files += sorted((ROOT / "evals" / "behaviour").glob("*/cases.yaml"))

    loaded = {}
    for f in files:
        rel = f.relative_to(ROOT)
        try:
            loaded[rel] = yaml.safe_load(f.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            mark = getattr(e, "problem_mark", None)
            where = f" at line {mark.line + 1}" if mark else ""
            problems.append(f"{rel} does not parse{where}: {getattr(e, 'problem', e)}. "
                            "The runner loads it with `yaml.safe_load` and dies here, on "
                            "every case rather than the one that broke it. An unquoted "
                            "value containing `: ` is the way this has happened.")
    if problems:
        return problems                      # counts cannot be read from a file that broke

    # The shape the runners actually index into, asserted per file rather than assumed.
    for rel, doc in loaded.items():
        if rel.name == "fixtures.yaml":
            if not isinstance(doc, dict) or not isinstance(doc.get("fixtures"), dict):
                problems.append(f"{rel}: no `fixtures:` map, which `run.py --fixtures` reads")
            continue
        cases = doc.get("cases") if isinstance(doc, dict) else None
        if not isinstance(cases, list) or not cases:
            problems.append(f"{rel}: no `cases:` list")
            continue
        # THE TWO RUNNERS INDEX DIFFERENTLY, AND THE CHECK ASKS WHAT EACH ONE READS. A
        # behaviour case names a `fixture` and may inherit the prompt from the file --
        # `behaviour/run.py:197` does `c.setdefault("prompt", spec.get("prompt"))` -- while a
        # trigger case carries its own prompt and the label to score it against. Asserting
        # one shape over both reported six correct files as broken, which is the failure this
        # check is supposed to be the opposite of.
        behaviour = rel.parts[1] == "behaviour"
        for i, c in enumerate(cases):
            if not isinstance(c, dict):
                problems.append(f"{rel}: case {i + 1} is not a mapping")
                continue
            where = c.get("prompt") or c.get("fixture") or f"case {i + 1}"
            if behaviour:
                if "fixture" not in c:
                    problems.append(f"{rel}: case {i + 1} names no `fixture`, which is the "
                                    "repository the run happens in and its name")
                if not (c.get("prompt") or doc.get("prompt")):
                    problems.append(f"{rel}: {where!r} has no `prompt`, on the case or on "
                                    "the file it inherits from")
            else:
                if "prompt" not in c:
                    problems.append(f"{rel}: case {i + 1} has no `prompt`")
                elif "expect" not in c:
                    problems.append(f"{rel}: {str(where)[:40]!r} has no `expect`, so a run "
                                    "of it cannot be scored either way")
    if problems:
        return problems

    cases = loaded[trigger.relative_to(ROOT)]["cases"]
    readme = (ROOT / "evals" / "README.md").read_text(encoding="utf-8")

    stated = re.search(r"holds (\d+) prompts", readme)
    if not stated:
        problems.append("evals/README.md no longer says how many prompts the set holds, in "
                        "the form `holds N prompts`, so nothing here can be compared")
    elif int(stated.group(1)) != len(cases):
        problems.append(f"evals/README.md says the set holds {stated.group(1)} prompts and "
                        f"`cases.yaml` holds {len(cases)}")

    # The denominator of each row of the results table is that skill's case count. A row
    # whose denominator has drifted is a score being read against a set that no longer
    # exists, which is how 112 survived a set of 118.
    per_skill = collections.Counter(c.get("expect") for c in cases)
    for label, expect in [(r"`(\w+)`", None), (r"negatives", "none")]:
        for m in re.finditer(r"^\| " + label + r" \| (\d+)/(\d+) \|", readme, re.M):
            skill = expect or m.group(1)
            denom = int(m.group(len(m.groups())))
            if skill not in per_skill and expect is None:
                continue                     # a row about something that is not a skill
            if denom != per_skill[skill]:
                problems.append(
                    f"evals/README.md scores {skill!r} out of {denom} and `cases.yaml` "
                    f"labels {per_skill[skill]} case(s) with that `expect`")
    return problems


# The repository every annotation check below is run against: two living documents that go
# stale on demand, one file whose front matter does not parse, and nothing else. Two
# warnings on two different paths and one error, which is the smallest shape that can
# exercise a join, a stale entry and a refusal at once.
def _annotation_fixture(tmp: Path, annotations: str | None = None,
                        at: str = ".framework/expected-findings.yaml",
                        also: dict[str, str] | None = None) -> None:
    fm = lambda **kw: "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"
    files = {
        "framework.yaml": f"framework_version: {REGISTRY['version']}\n",
        "OPEN.md": fm(schema="framework/open-register/v1", artifact_type="open-register",
                      lifecycle="living", status="active", owners="[owner]",
                      created="2026-01-01", last_review="2026-01-01 09:00",
                      entries="\n  OD-001:\n    status: open\n"
                              "    cost_to_reverse: low\n    products: [all]\n"
                              "    default_in_force: nothing is scheduled\n")
                   + "# Open\n\n## Cost to reverse LOW\n\n### OD-001 - the one question\n",
        "products/alpha/PBR.md": fm(
            schema="framework/product-brief/v1", artifact_type="product-brief",
            lifecycle="living", status="active", products="[alpha]", owners="[owner]",
            created="2026-01-01", last_review="2026-01-01 09:00") + "# Brief\n",
        # Front matter that does not parse, which is `FM001` and an error. The one thing an
        # annotation is not allowed to touch needs to be present to be refused.
        "broken.md": "---\nartifact_type: [oops\n---\n\n# broken\n",
    }
    if annotations is not None:
        files[at] = annotations
    files.update(also or {})
    for rel, text in files.items():
        f = tmp / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")


def _annotated_run(annotations: str | None, **kw) -> tuple[dict | None, str]:
    """The validator over that repository, as parsed JSON and whatever went to stderr."""
    with tempfile.TemporaryDirectory() as tmp:
        _annotation_fixture(Path(tmp), annotations, **kw)
        r = subprocess.run([sys.executable, str(VALIDATE), "--root", tmp, "--json",
                            "--stale-days", "0"], capture_output=True, text=True)
        if r.returncode not in (0, 1) or not r.stdout.strip():
            return None, r.stderr
        return json.loads(r.stdout), r.stderr


ANNOTATES_A_WARNING = """expected:
  - code: LC002
    path: OPEN.md
    reason: >
      the register is read at every cycle and the date is what nobody moves.
    clears_when: >
      the next reading of the register, stamped with the instant it finished.
"""


@check("a finding a project has examined is reported, annotated, and never reclassified")
def _annotations_are_read():
    # THE POINT OF THE MECHANISM IS THE OPPOSITE OF SILENCING, AND THAT IS WHAT IS ASSERTED
    # HERE. A project already had two ways to make a finding go away -- lower the severity,
    # widen the scan -- and `audit/SKILL.md` forbids both because the finding stops being
    # reported and nothing records that anybody decided. So the annotated finding has to
    # still be in `findings`, still at `warn`, and carrying the two sentences; if any of
    # those three slipped, this would have become the third way rather than the alternative
    # to them.
    problems = []
    plain, _ = _annotated_run(None)
    if plain is None:
        return ["the validator crashed on a repository with no annotation file"]
    if plain["warnings"] != 2 or plain["errors"] != 1:
        return [f"the fixture no longer produces 2 warnings and 1 error: "
                f"{plain['errors']} error(s), {plain['warnings']} warning(s)"]
    if plain["annotated"] != 0 or plain["unannotated"] != 2:
        problems.append(f"with no file at all the counts read {plain['annotated']} "
                        f"annotated and {plain['unannotated']} unannotated")
    if any("accepted" in f for f in plain["findings"]):
        problems.append("a finding carries an `accepted` key in a repository that has "
                        "annotated nothing: the key has to be absent, not null, or every "
                        "consumer of this output grows a branch it never needed")

    got, _ = _annotated_run(ANNOTATES_A_WARNING)
    if got is None:
        return problems + ["the validator crashed on a repository with an annotation"]
    marked = [f for f in got["findings"] if f.get("accepted")]
    if len(marked) != 1 or marked[0]["code"] != "LC002" or marked[0]["path"] != "OPEN.md":
        problems.append(f"the annotation matched {len(marked)} finding(s) instead of the "
                        "one it names")
    elif marked[0]["level"] != "warn":
        problems.append(f"the annotated finding is now at {marked[0]['level']!r}. It stays "
                        "at `warn`: a project checking its own warnings keys on `level`, "
                        "and a finding that quietly became something else drops out of that "
                        "check without a word")
    elif not marked[0]["accepted"].get("clears_when"):
        problems.append("the annotation reached the finding without what clears it")
    if got["warnings"] != 2:
        problems.append(f"annotating one warning changed the warning count to "
                        f"{got['warnings']}: the count is of what was reported, not of "
                        "what is still unexplained")
    if (got["annotated"], got["unannotated"]) != (1, 1):
        problems.append(f"the counts read {got['annotated']} annotated and "
                        f"{got['unannotated']} unannotated, and the fixture has one of each")
    if any(f["code"].startswith("AN") for f in got["findings"]):
        problems.append("a correct annotation produced an `AN` finding")
    return problems


@check("an annotation that explains nothing, or explains away an error, is refused")
def _annotations_are_policed():
    # The two ways this file rots, and both are errors because the file is load-bearing on
    # every run now rather than only during a migration. A stale entry is a reason left
    # standing for a finding that is gone, which the next reader takes as current; an
    # annotation on an `error` is the level that blocks being talked out of blocking, one
    # project at a time.
    problems = []
    stale, _ = _annotated_run("""expected:
  - code: REG005
    path: nowhere.md
    reason: >
      a finding that is not reported here.
    clears_when: >
      nothing, which is the whole problem.
""")
    if stale is None:
        return ["the validator crashed on a stale annotation"]
    an001 = [f for f in stale["findings"] if f["code"] == "AN001"]
    if len(an001) != 1:
        problems.append(f"a stale annotation produced {len(an001)} AN001")
    elif an001[0]["level"] != "error":
        problems.append(f"AN001 is at {an001[0]['level']!r}. It is the one line that keeps "
                        "this file from becoming a list of permanent exemptions with a "
                        "better name, and a warning is not that line")

    on_error, _ = _annotated_run("""expected:
  - code: FM001
    path: broken.md
    reason: >
      an error, which this must not be able to explain away.
    clears_when: >
      the front matter parsing.
""")
    if on_error is None:
        return problems + ["the validator crashed on an annotation naming an error"]
    if not [f for f in on_error["findings"] if f["code"] == "AN002"]:
        problems.append("an annotation on an `error` finding was accepted or ignored. "
                        "Ignoring is the worse of the two: the project believes it has "
                        "annotated and finds out when the gate stays red")
    if [f for f in on_error["findings"] if f["code"] == "FM001" and f.get("accepted")]:
        problems.append("the error was marked as accepted anyway")

    strict, _ = _annotated_run("require_all: true\n" + ANNOTATES_A_WARNING)
    if strict is None:
        return problems + ["the validator crashed with require_all"]
    an003 = [f for f in strict["findings"] if f["code"] == "AN003"]
    if len(an003) != 1 or an003[0]["path"] != "products/alpha/PBR.md":
        problems.append(f"`require_all` reported {len(an003)} unannotated warning(s), and "
                        "the fixture leaves exactly one")
    loose, _ = _annotated_run(ANNOTATES_A_WARNING)
    if loose and any(f["code"] == "AN003" for f in loose["findings"]):
        problems.append("AN003 fired without `require_all`: permissive is the default, and "
                        "a check that reddened every repository on arrival would be off in "
                        "a week")
    return problems


@check("the annotation file has one home, is never an artifact, and says so on stderr")
def _the_annotation_file_has_one_home():
    # Where this file sits was forced rather than chosen: it has to be readable by the
    # tooling arriving and invisible to every validator already released, and a hidden path
    # is the only slot with that property. Which makes two things worth asserting: that a
    # project cannot turn it back into an artifact, and that the move from the place the
    # first project had to invent is announced rather than silent.
    problems = []
    # THE GRACE PERIOD ENDED WHERE THE NOTE SAID IT WOULD, AND SAYING SO IS THE HALF THAT
    # STAYS. 3.1.0 read the old path and wrote down that 3.2.0 would stop; a note that says
    # when something ends is a promise or it is decoration. What must not happen is the
    # silent version: a file sitting in a repository doing nothing, discovered six months
    # later by somebody wondering why an annotation stopped applying.
    legacy, err = _annotated_run(ANNOTATES_A_WARNING, at=".claude/expected-findings.yaml")
    if legacy is None:
        return ["the validator crashed on a repository carrying only the old path"]
    if [f for f in legacy["findings"] if f.get("accepted")]:
        problems.append("the old path is still being read, and the version note says it is "
                        "not: one of the two is wrong and the note is the promise")
    if ".claude" not in err:
        problems.append("a file at the old path was ignored in silence. It has to be "
                        "reported precisely because it is not read any more: nothing in it "
                        "is applying, and that is invisible from the report otherwise")

    both, err = _annotated_run(ANNOTATES_A_WARNING, also={
        ".claude/expected-findings.yaml": """expected:
  - code: LC002
    path: products/alpha/PBR.md
    reason: >
      an annotation in the file that is not read.
    clears_when: >
      nothing.
"""})
    if both is None:
        problems.append("the validator crashed with both files present")
    else:
        marked = {f["path"] for f in both["findings"] if f.get("accepted")}
        if marked != {"OPEN.md"}:
            problems.append(f"with both files present the annotations applied were "
                            f"{sorted(marked)}: only the new path is read")
        if ".claude" not in err:
            problems.append("the leftover file was ignored in silence, which is how a "
                            "project ends up editing the one that is not read")

    # `skip_hidden: false` is a legal thing for a project to write, and it is what would
    # otherwise turn this file into an `FM001`, at `error`, on the run it exists to inform.
    exposed, _ = _annotated_run(
        ANNOTATES_A_WARNING,
        also={"framework.yaml": f"framework_version: {REGISTRY['version']}\n"
                                "scan:\n  skip_hidden: false\n"})
    if exposed is None:
        problems.append("the validator crashed with skip_hidden: false")
    elif [f for f in exposed["findings"] if "expected-findings" in f["path"]]:
        problems.append("the annotation file was reported as a document once the project "
                        "stopped skipping hidden paths. The validator reads it by an "
                        "explicit path, and that alone does not stop `discover` finding it: "
                        "`scan.skip_files` is the half that holds, because `load_scan` "
                        "unions and never subtracts")
    return problems


@check("the pin is said at the moment the framework is invoked, not only in the report")
def _the_pin_is_said_before_the_scan():
    # `FW003` reports this and cannot be relied on to: a project whose own gate runs the
    # validator of the version it declares stops running that gate the moment the checkout
    # moves, correctly, and the thing that makes it refuse is the divergence itself. So the
    # report carrying the finding is the one nobody is running, and it is not being run
    # because the fault is present. The line on stderr is the same fact said where the
    # circularity cannot swallow it.
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                          capture_output=True, text=True)
    if head.returncode != 0:
        return ["git history is not available here, so the check is not running"]
    problems = []
    declared = f"framework_version: {REGISTRY['version']}\n"
    for config, want, what in [
        (declared, False, "a project that pins nothing"),
        (declared + f'framework_commit: "{head.stdout.strip()}"\n', False,
         "a pin that is being honoured"),
        (declared + 'framework_commit: "0123456789abcdef"\n', True,
         "a pin naming a commit that is not the one running"),
    ]:
        with tempfile.TemporaryDirectory() as tmp:
            _annotation_fixture(Path(tmp), also={"framework.yaml": config})
            r = subprocess.run([sys.executable, str(VALIDATE), "--root", tmp, "--json",
                                "--stale-days", "0"], capture_output=True, text=True)
        said = "this checkout is at" in r.stderr
        if said != want:
            problems.append(f"{what} was {'not ' if want else ''}announced on stderr")
        # The line has to be on stderr and nowhere else. stdout carries the JSON every
        # caller parses, `migrate.py` included, so a line printed there would break the
        # tool the message exists to send somebody to.
        try:
            json.loads(r.stdout)
        except json.JSONDecodeError:
            problems.append(f"stdout stopped being JSON for {what}: the line went to the "
                            "stream the callers parse")
    return problems


def _vocabulary_repo(tmp: Path, entries: str, extra: dict[str, str] | None = None) -> None:
    """A root register with a product beside it, which is what `REG011` needs to ask at all."""
    fm = lambda **kw: "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"
    files = {
        "framework.yaml": f"framework_version: {REGISTRY['version']}\n",
        "OPEN.md": fm(schema="framework/open-register/v1", artifact_type="open-register",
                      lifecycle="living", status="active", owners="[owner]",
                      created="2026-01-01", last_review="2026-01-01 09:00",
                      entries=entries)
                   + "# Open\n\n<!-- generated: open-union -->\n\n<!-- /generated -->\n",
        "products/alpha/product.yaml": fm(
            schema="framework/product-manifest/v1", artifact_type="product-manifest",
            lifecycle="living", status="active", products="[alpha]", owners="[owner]",
            created="2026-01-01", last_review="2026-01-01 09:00",
            stage="\n  phase: F4\n  since: 2026-01-01"),
    }
    files.update(extra or {})
    for rel, text in files.items():
        f = tmp / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")


def _vocabulary_run(entries: str, extra: dict[str, str] | None = None, emit: bool = False):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _vocabulary_repo(root, entries, extra)
        args = ["--emit-index"] if emit else []
        r = subprocess.run([sys.executable, str(VALIDATE), "--root", tmp, "--json",
                            "--stale-days", "36500", *args], capture_output=True, text=True)
        if r.returncode not in (0, 1) or not r.stdout.strip():
            return None, ""
        return json.loads(r.stdout), (root / "OPEN.md").read_text(encoding="utf-8")


BINDS_NOTHING = """
  OD-001:
    status: open
    cost_to_reverse: low
    products: [all]
    default_in_force: nothing is scheduled
  KI-002:
    status: open
    cost_to_reverse: low
    products: [none]
    default_in_force: the tooling defect stands
"""


@check("an entry that binds no product says so, and reaches the view without reaching a product")
def _binds_no_product():
    # `[none]` IS THE FOURTH ANSWER AND THE ONE THIS FILE'S OWN NOTE NAMED WITHOUT GIVING IT
    # A VALUE: "not decided, not measurable, not applicable, not ours". The last one is the
    # entry whose subject is the repository or the tooling it is checked with, and the two
    # ways of writing it before were both wrong -- `[all]` says something untrue in the field
    # everything joins on, absence says the thing `REG011` exists to remove.
    #
    # The half that is easy to get wrong is not the check, it is the view. An entry that
    # binds nothing and appears nowhere would validate, satisfy every check, and be missing
    # from the only composed list of what is open, which is the same disappearance from the
    # other side.
    problems = []
    got, open_md = _vocabulary_run(BINDS_NOTHING, emit=True)
    if got is None:
        return ["the validator crashed on a register carrying `[none]`"]
    if [f for f in got["findings"] if f["code"] in ("REG011", "REG013")]:
        problems.append("`[none]` was reported as a missing or misfiled answer: it is an "
                        "answer, and the whole point is that it is a different one from "
                        "`[all]` and from silence")
    region = open_md.split("<!-- generated: open-union -->", 1)[-1]
    if "## Bound to no product at all" not in region:
        problems.append("the generated union has no section for entries that bind nothing, "
                        "so an entry saying its subject is not a product is absent from the "
                        "one view that composes what is open")
    else:
        tail = region.split("## Bound to no product at all", 1)[1]
        if "KI-002" not in tail:
            problems.append("the entry that binds nothing did not reach its own section")
        if "KI-002" in region.split("## Bound to no product at all", 1)[0]:
            problems.append("the entry that binds nothing also appears under a product or "
                            "among the ones that bind every product, which is the finding "
                            "this value exists to remove, moved by a metre")
    if "## none" in region:
        problems.append("`none` was emitted as a product heading. It is a word, not a "
                        "product, and this is the shape `all` had before it was one")

    # A reserved word answers how many products are bound, so it cannot share the field.
    beside = _vocabulary_run(BINDS_NOTHING.replace("products: [none]",
                                                   "products: [none, alpha]"))[0]
    if beside is None or not [f for f in beside["findings"] if f["code"] == "REG011"]:
        problems.append("a reserved word sitting beside a named product was not reported, "
                        "and the reader has to guess which half was the afterthought")

    # And a product that carries one of the two names makes every use of the field ambiguous.
    fm = lambda **kw: "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"
    named = _vocabulary_run(BINDS_NOTHING, extra={"products/none/product.yaml": fm(
        schema="framework/product-manifest/v1", artifact_type="product-manifest",
        lifecycle="living", status="active", products="[none]", owners="[owner]",
        created="2026-01-01", last_review="2026-01-01 09:00",
        stage="\n  phase: F4\n  since: 2026-01-01")})[0]
    said = [f for f in (named or {}).get("findings", []) if f["code"] == "XP008"]
    if named is None or not said:
        problems.append("a product actually called `none` was not reported, so every "
                        "`products:` naming it says two things and nothing says which")
    elif "open_decisions" not in said[0]["message"]:
        # The check is `warn`, so the message carries the whole weight. What it costs is a
        # silent disappearance -- no heading in the generated union, an empty derived view --
        # and a warning that says only "reserved word" gets read as a naming preference by
        # somebody who then never connects the missing section to it.
        problems.append("XP008 says the name is reserved and not what it costs. A warning "
                        "whose damage is a product vanishing from the composed view has to "
                        "name the damage: whoever reads it is deciding what ignoring it "
                        "costs them")
    return problems


COMMITMENTS_WITH = """---
schema: framework/commitments/v1
artifact_type: commitments
lifecycle: living
status: active
owners: [owner]
products: [alpha]
created: 2026-01-01
last_review: 2026-01-01 09:00
commitments:
  CMT-001:
    to: the committee
    status: open
    products: [alpha]
    unanswerable:
      feasibility:
        reason: >
          each capability is buildable alone and the set is not.
        settled_by: >
          the decision on the scope.
%s
---

# Commitments

### CMT-001 - the one that cannot be answered yet
%s
"""


def _commitments(rows: str = "", headings: str = ""):
    return {"COMMITMENTS.md": COMMITMENTS_WITH % (rows, headings)}


@check("a field left empty on purpose is declared, counted, and cannot be declared and filled")
def _unanswerable_is_declared_and_guarded():
    # The registry's note on closed vocabularies describes this failure and left it without a
    # repair for as long as it has existed: the careful writer omits the field, and the
    # omission is the honest thing to write and the most invisible one. What is asserted here
    # is that declaring it is visible -- the count -- and that the declaration cannot outlive
    # the state it describes, which is the only part of the rule a script can hold. Whether
    # the event in `settled_by` has happened is not knowable from here, and `REG009` says the
    # same about a trigger one field over.
    problems = []
    clean = _vocabulary_run(BINDS_NOTHING, extra=_commitments())[0]
    if clean is None:
        return ["the validator crashed on a record carrying `unanswerable`"]
    if clean["unanswerable"] != 1:
        problems.append(f"the report counts {clean['unanswerable']} declared field(s) and "
                        "the fixture declares one: the count is what makes a deliberate "
                        "emptiness visible, and without it this is an omission again")
    if [f for f in clean["findings"] if f["code"].startswith("UNA")]:
        problems.append("a correct declaration produced a finding")

    both = _vocabulary_run(BINDS_NOTHING, extra=_commitments(
        rows="""    feasibility: feasible"""))[0]
    if both is None or not [f for f in both["findings"] if f["code"] == "UNA001"]:
        problems.append("a field declared unanswerable and filled in anyway was accepted. "
                        "That is the declaration outliving its own state, and it is the one "
                        "half of the rule a check can see")
    elif [f for f in both["findings"] if f["code"] == "UNA001"][0]["level"] != "error":
        problems.append("UNA001 is not an error. It is to this what AN001 is to the "
                        "annotation file: without it the key is a permit not to answer")

    for swap, what in (("      fesibility:", "a field the map does not have"),
                       ("      status:", "a field the map requires")):
        got = _vocabulary_run(BINDS_NOTHING, extra={
            "COMMITMENTS.md": COMMITMENTS_WITH.replace("      feasibility:", swap)
                              % ("", "")})[0]
        if got is None or not [f for f in got["findings"] if f["code"] == "UNA002"]:
            problems.append(f"{what} was accepted as a declaration: it reads as an answer "
                            "given, and the field it was meant for is still silent")

    dated = _vocabulary_run(BINDS_NOTHING, extra={
        "COMMITMENTS.md": COMMITMENTS_WITH.replace(
            "          the decision on the scope.",
            "          2026-12-31, the end of the year.") % ("", "")})[0]
    if dated is None or not [f for f in dated["findings"] if f["code"] == "UNA003"]:
        problems.append("a date in `settled_by` was accepted. It takes the event after "
                        "which the field would have a true value, for the reason REG009 "
                        "gives one field over")
    return problems


@check("every artifact sits where the registry says its type lives, and the patterns parse")
def _placement_is_declared_and_true():
    # THE INVARIANT THAT CATCHES THE CLASS INSTEAD OF THE INSTANCE, which is the rule this
    # suite is written to. Two of the thirty placements were false about this repository's own
    # files -- `CHG-NNN.md` and `DC-NNN.md`, while every real one carries a slug -- and they
    # were false for months, because the field was read by one line of the generator and by
    # nothing else. Writing the patterns out found twelve more of the same mistake.
    #
    # So what is asserted is not "those two are fixed", it is that no fixture artifact sits
    # anywhere its type does not describe. That fails on the day somebody writes a placement
    # that does not match the files, and it fails on the day somebody files a document
    # somewhere new without saying so in the registry, which are the two directions the
    # mistake arrives from.
    v = _load(VALIDATE, "validate")
    problems = []
    for name, spec in sorted(REGISTRY["types"].items()):
        where = spec.get("path")
        if not isinstance(where, list) or not where:
            problems.append(f"{name}: `path` is {where!r} and has to be a list of placements. "
                            "As a string it was a sentence, and a sentence is what nothing "
                            "could read")
            continue
        for one in where:
            try:
                v.placement_pattern(one)
            except re.error as e:
                problems.append(f"{name}: {one!r} does not compile as a placement: {e}")
        if "path_not_enforced" in spec and not str(spec["path_not_enforced"]).strip():
            problems.append(f"{name}: declares `path_not_enforced` with no reason. The point "
                            "of the key is the reason: without it, it is the check switched "
                            "off for one type and nothing saying why")

    roots = sorted(p.parent for p in (ROOT / "evals" / "fixtures").rglob("AGENTS.md"))
    if not roots:
        return problems + ["no fixture roots found: the check is not running"]
    seen = 0
    for root in roots:
        scan = v.load_scan(REGISTRY, v.load_project(root))
        for a in v.discover(root, scan, REGISTRY, v.Report({})):
            spec = REGISTRY["types"].get(a.type or "")
            if not spec or not spec.get("path") or spec.get("path_not_enforced"):
                continue
            seen += 1
            rel = a.rel.replace("\\", "/")
            if not any(v.placement_pattern(one).match(rel) for one in spec["path"]):
                problems.append(
                    f"{root.name}/{rel}: a {a.type} sits where the registry does not say one "
                    f"lives ({' or '.join(spec['path'])}). Either the file is misfiled or the "
                    "placement is wrong, and the second is how this field came to be false "
                    "about two types for months")
    if seen < 100:
        problems.append(f"only {seen} typed artifacts were examined: the fixtures are not "
                        "built, so this ran against almost nothing")
    return problems


@check("a document that declares a type in the wrong place is reported, and an exempt type is not")
def _misplaced_artifact_is_reported():
    # The case, rebuilt: a derived planning document in a working directory, declaring
    # `artifact_type: roadmap`, `living`, a product, and a `last_review` fresher than the real
    # roadmap's. Everything about it validated. It was counted as an artifact and it came out
    # first in the derived view of that product, because that list is ordered by path and a
    # working directory sorts before `products/`.
    v = _load(VALIDATE, "validate")
    fm = lambda **kw: "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"
    stray = fm(schema="framework/roadmap/v1", artifact_type="roadmap", lifecycle="living",
               status="active", products="[alpha]", owners="[owner]", created="2026-01-01",
               last_review="2026-01-01 09:00") + "# A draft derived from the real roadmap\n"
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for rel, text in {
            "framework.yaml": f"framework_version: {REGISTRY['version']}\n",
            "products/alpha/RMP.md": stray,
            "_work/planning/draft.md": stray,
        }.items():
            f = root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding="utf-8")
        r = subprocess.run([sys.executable, str(VALIDATE), "--root", tmp, "--json",
                            "--stale-days", "36500"], capture_output=True, text=True)
        if r.returncode not in (0, 1) or not r.stdout.strip():
            return ["the validator crashed on a misplaced artifact"]
        got = json.loads(r.stdout)
    said = [f for f in got["findings"] if f["code"] == "LOC001"]
    if len(said) != 1 or said[0]["path"] != "_work/planning/draft.md":
        problems.append(f"the misplaced roadmap produced {len(said)} LOC001, and the one in "
                        "`products/alpha/` must not be among them: a check that reports the "
                        "correct file too is a check that gets switched off")
    elif "roadmap" not in said[0]["message"]:
        problems.append("the finding does not name the type, so a reader cannot tell which "
                        "of the two claims about the file is the wrong one")

    # A type the registry declares unenforceable is skipped, and counted rather than silent.
    fake = {"types": {"roadmap": {**REGISTRY["types"]["roadmap"],
                                  "path_not_enforced": "a reason"}}}
    rep = v.Report({})
    art = v.Artifact(Path("x"), "anywhere/else.md",
                     {"artifact_type": "roadmap"}, "")
    exempt = v.check_placement([art], fake, rep)
    if rep.findings:
        problems.append("a type declared `path_not_enforced` was still reported: the key is "
                        "the framework saying it cannot write the pattern, and reporting "
                        "anyway makes the declaration a comment")
    if exempt != 1:
        problems.append(f"the count of unenforced types came back {exempt}: the report says "
                        "how many types the check does not run on, or the hole is invisible")
    return problems


# ─────────────────────────────────────────────────────────────────────────────

print()
if failures:
    print(f"{len(failures)} problem(s).")
    sys.exit(1)
print("The framework is consistent with itself.")
