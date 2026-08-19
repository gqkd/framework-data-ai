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
        + "# Open\n",
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
    return problems


@check("a citation to a term, and a decision that says what it left open, both resolve")
def _references_with_a_second_end():
    # Two pairs that had one end each. A data contract sending a reader to the glossary for
    # what a column means, and a decision declaring in its prose that something stays open:
    # both were references, and nothing resolved either of them.
    fm = lambda **kw: "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"

    def repo(terms: str, cite: str, leaves: str | None) -> dict:
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
                              terms=terms) + "# Glossary\n",
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
        if "REF005" in codes(repo(defined, "see `GLOSSARY §Glossary`", "[]")):
            problems.append("a citation naming a heading of the glossary was reported: "
                            "pointing a reader at a section is a reference that resolves by "
                            "construction, and a check that only knows terms reports the one "
                            "form that cannot be wrong")

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

    problems = []
    for rows, want, what in [
        ("stack:\n  db:\n    tool: PostgreSQL\n    status: chosen\n    decided_in: DEC-001\n",
         False, "a chosen tool naming an accepted decision"),
        ("stack:\n  db:\n    tool: PostgreSQL\n    status: chosen\n",
         True, "a chosen tool naming no decision at all"),
        ("stack:\n  db:\n    tool: PostgreSQL\n    status: unratified\n    decided_in: DEC-001\n",
         True, "an unratified tool that names a decision, hiding one that was taken"),
        ("stack:\n  db:\n    tool: PostgreSQL\n    status: chosen\n    decided_in: DEC-404\n",
         True, "a decision that does not exist"),
        ("stack:\n  db:\n    tool: PostgreSQL\n    status: chosen\n    decided_in: DEC-002\n",
         True, "a decision that was never accepted"),
        ("stack:\n  db:\n    tool: PostgreSQL\n    status: unratified\n",
         False, "an unratified tool, which is the honest state and must stay quiet"),
        # The state the vocabulary did not have: tried, not in use, nobody decided. With
        # three values the only way to file it was `ruled-out` with nothing to name, and a
        # real repository wrote two of those -- so the check reported a document whose only
        # fault was that the words ran out.
        ("stack:\n  db:\n    tool: PostgreSQL\n    status: dropped\n",
         False, "an abandoned experiment nobody decided against, which is what `dropped` is"),
        ("stack:\n  db:\n    tool: PostgreSQL\n    status: dropped\n    decided_in: DEC-001\n",
         True, "a dropped tool naming a decision, which is a decision filed as an accident"),
    ]:
        got = repo({"STACK.md": stack(rows), "decisions/DEC-001.md": dec,
                    "decisions/DEC-002.md": draft})
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

# ─────────────────────────────────────────────────────────────────────────────

print()
if failures:
    print(f"{len(failures)} problem(s).")
    sys.exit(1)
print("The framework is consistent with itself.")
