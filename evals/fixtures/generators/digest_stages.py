#!/usr/bin/env python3
"""Build the repository the digest's stages are measured on: one product, a roadmap in stages.

    python digest_stages.py <dest>          writes <dest>/borea

`borea` plans the visits of maintenance technicians. Its roadmap orders four increments in
three stages, with the milestone of each stage named and never dated, and the digest draws
its Gantt from them instead of from an order kept by hand. The baseline was written by the
digest script on 06/10; the state file is filled for the workbook of 07/10, which
`tests/selfcheck.py` renders and reads back.

What the case is built to show, each by one item:
- an increment that is the sum of decisions, issues and changes, part done and part to do
  (INC-101), and one whose change predates the roadmap and is listed in `changes` (INC-102);
- a conditional increment, counted like the others (INC-103), and one with nothing under it,
  still to be broken down and out of the estimate (INC-104);
- an item blocked by a wait, which goes to the end of its increment (OD-201);
- an item worked once before the digest and placed by the queue after the next week
  (CHG-303), whose bar, increment and stage start where the queue puts it and not on 06/10;
- an item in no increment, which comes after the stages (KI-021);
- a stage milestone at risk, one in time and one incomplete.

Everything here is synthetic: the product, the people and every number.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
FRAMEWORK = HERE.parents[2]
SCRIPT = FRAMEWORK / "skills" / "digest" / "scripts" / "digest.py"
T = "2026-09-25 10:00"


def fm(**kw) -> str:
    lines = []
    for k, v in kw.items():
        lines.append(f"{k}:{v}" if isinstance(v, str) and "\n" in v else f"{k}: {v}")
    return "---\n" + "\n".join(lines) + "\n---\n\n"


def living(artifact_type: str, **kw) -> dict:
    return dict(schema=f"framework/{artifact_type}/v1", artifact_type=artifact_type,
                lifecycle="living", status="active", **kw)


AGENTS = fm(**living("agents-control-plane"), owners="[lead]", created=T, last_review=T,
            classification="internal") + """\
# Instructions for agents

Read this file first. Then `products/borea/OPEN.md` and `OPEN.md` at the root, then
`products/borea/product.yaml` and `products/borea/RMP.md`.

## Authoritative sources

| Question | Source |
|---|---|
| What the product does and for whom | `products/borea/PBR.md` |
| In which order it is delivered | `products/borea/RMP.md` |
| What is not decided | `products/borea/OPEN.md` |
| What you are authorized to build right now | the change contracts in `products/borea/changes/` |

## Non negotiable rules

1. Do not take decisions listed in an `OPEN.md`: stop and ask.
2. Do not implement a signal. What gets implemented is an approved change contract.
"""

ROOT_OPEN = fm(**living("open-register"), products="[borea]", owners="[lead]", created=T,
               last_review=T, classification="internal", entries="{}") + """\
# Open decisions above the product

# §1 · Open decisions

Nothing is open above the product.

# §2 · Accepted known issues

None.

# §3 · Parking lot

# §4 · Closed decisions

# §5 · Everything open, by product

<!-- generated: open-union -->
Run `validate.py --emit-index` to fill this in.
<!-- /generated -->
"""

PRODUCT = f"""\
schema: framework/product-manifest/v1
artifact_type: product-manifest
lifecycle: living
status: active
products: [borea]
name: Borea
one_liner: Plans the visits of maintenance technicians.
owners: [lead]
created: {T}
last_review: {T}
stage:
  block: B
  phase: BUILD
code:
  monorepo:
    url: git@example.com:borea/borea.git
    contains: the whole product, these documents included
    path: .
"""

PBR = fm(**living("product-brief"), products="[borea]", owners="[lead]", created=T,
         last_review=T, classification="internal") + """\
# Borea · product brief

## One line

Plans the visits of maintenance technicians, so that each visit goes to somebody who can do
it and who can get there in time.

## Actors

The dispatchers who plan; the technicians who visit; the customers who wait for them.

## Outcome

A dispatcher plans a day of visits without a spreadsheet, and the customer knows when the
technician arrives.
"""

SIGNALS = [("SIG-001", "the technicians are kept in a spreadsheet", "CHG-301"),
           ("SIG-002", "visits are booked with no travel time between them", "CHG-302"),
           ("SIG-003", "customers phone to ask when the technician arrives", "CHG-303"),
           ("SIG-004", "the pilot team has nowhere to try a release", "CHG-304"),
           ("SIG-005", "accounting retypes every closed visit", "CHG-305")]

LOG = fm(schema="framework/signal-log/v1", artifact_type="signal-log",
         lifecycle="append-only", status="active", products="[borea]", owners="[lead]",
         created=T, classification="internal") + """\
# Signal log: Borea

## Signals

| ID | Date | Type | Observed | Impact | Who/Where | Linked |
|---|---|---|---|---|---|---|
""" + "".join(f"| {s} | 2026-09-20 | request | {what} | slower planning | dispatchers | {c} |\n"
              for s, what, c in SIGNALS)

ICG = fm(schema="framework/impact-classification/v1", artifact_type="impact-classification",
         lifecycle="immutable", status="accepted", id="ICG-001", products="[borea]",
         owners="[lead]", created="2026-09-22 10:00",
         routing="\n" + "\n".join(f"  {s}: none" for s, _, _ in SIGNALS),
         classification="internal") + """\
# ICG-001 · Triage of cycle 1

<!-- section: intake -->
## Intake

The five signals of the log, raised while setting the product up.

<!-- section: classification -->
## Classification

None of them changes what the product is for or how it is built.

<!-- section: open-questions -->
## Open questions

None.
"""

# id: (title, status, derives_from)
CHANGES = {
    "CHG-301": ("Import the technicians' records", "verified", "[borea:SIG-001, INC-101]"),
    "CHG-302": ("Travel times between visits", "approved", "[borea:SIG-002, INC-101, DEC-210]"),
    # Written before the roadmap had stages: it does not name its increment, and the roadmap
    # lists it under `changes`.
    "CHG-303": ("Text message to the customer", "approved", "[borea:SIG-003]"),
    "CHG-304": ("Acceptance environment", "draft", "[borea:SIG-004, INC-103]"),
    "CHG-305": ("Export to the accounting system", "approved", "[borea:SIG-005]"),
}


def change(cid: str) -> str:
    title, status, derives = CHANGES[cid]
    verified = ("\n## Verification\n\nVerified with the dispatchers on 2026-10-02: the criteria "
                "of point 3 hold.\n" if status == "verified" else "")
    return fm(schema="framework/change-contract/v1", artifact_type="change-contract",
              lifecycle="immutable", status=status, id=cid, products="[borea]",
              owners="[lead]", approvers="[lead]", created="2026-09-23 10:00", icg="ICG-001",
              derives_from=derives, verified_by="null", classification="internal") + f"""\
# {cid} · {title}

<!-- section: what-changes -->
### 1 · What changes

{title}.

<!-- section: what-must-not-change -->
### 2 · What must NOT change

The visits already planned, and who can see them.

<!-- section: how-we-know-it-worked -->
### 3 · How we know it worked

A dispatcher plans a day with it and nothing has to be retyped.
{verified}"""


DEC_210 = fm(schema="framework/decision-record/v1", artifact_type="decision-record",
             lifecycle="immutable", status="accepted", id="DEC-210", scope="architecture",
             products="[borea]", owners="[lead]", approvers="[lead]",
             created="2026-10-01 10:00", derives_from="[OD-200]", supersedes="null",
             classification="internal", leaves_open="[]") + """\
# DEC-210 · One calendar per team

## Context

The teams plan independently, and one calendar for the whole company mixes their slots.

## Decision

Each team has a calendar of its own.

## Alternatives considered

| Alternative | Why discarded |
|---|---|
| One calendar, filtered by team | a missing filter books one team's technician for another |

## Consequences

A technician moving between teams moves between calendars.
"""

OPEN = ("---\nschema: framework/open-register/v1\nartifact_type: open-register\n"
        "lifecycle: living\nstatus: active\nowners: [lead]\n"
        f"created: {T}\nlast_review: {T}\nclassification: internal\nentries:\n"
        "  OD-200:\n    status: decided\n    closed_by: DEC-210\n"
        "  OD-201:\n    status: open\n    cost_to_reverse: high\n"
        "    default_in_force: the dispatcher assigns every visit by hand\n"
        "    trigger: the first day with more than thirty visits\n"
        "  OD-202:\n    status: open\n    cost_to_reverse: low\n"
        "    default_in_force: the customer is told the day before\n"
        "    trigger: the first complaint about a late notice\n"
        "  KI-021:\n    status: open\n---\n\n") + """\
# Open decisions and known issues: Borea

# §1 · Open decisions

## Cost to reverse HIGH: changing it later means redoing work that already exists

### OD-201 · How a visit is assigned to a technician

- **Question:** by hand, by area, or by an optimiser of the travel?

## Cost to reverse LOW: changing it later costs an afternoon

### OD-202 · How early the customer is told

- **Question:** the day before, or two hours before the visit?

# §2 · Accepted known issues

### KI-021 · The day view is slow on large teams

- A team of more than forty technicians waits seconds for the day view.
- Accepted while the pilot team has twelve.
- The dispatchers of the largest teams bear it.
- **Reopening trigger:** the first team of more than forty on the product.
- **Reference:** none yet.

# §3 · Parking lot

# §4 · Closed decisions

- **2026-10-01 · OD-200** → [`DEC-210`](../../decisions/DEC-210-team-calendar.md) · one
  calendar per team.
"""

RMP = fm(**living("roadmap"), version="1.0.0", products="[borea]", owners="[lead]",
         created=T, last_review=T, classification="internal").replace("---\n\n", """\
delivery_stages:
  t1:
    name: Il calendario delle squadre
    after: []
    increments: [INC-101]
    milestone: Prova con la squadra pilota
  t2:
    name: Gli avvisi ai clienti
    after: [t1]
    increments: [INC-102, INC-103]
    milestone: Primo avviso inviato a un cliente
  t3:
    name: L'app per i tecnici
    after: [t2]
    increments: [INC-104]
    milestone: App in prova sul campo
increments:
  INC-101:
    state: committed
    depends_on: []
    requires: [OD-200, OD-201]
    changes: []
  INC-102:
    state: shaped
    depends_on: [INC-101]
    requires: [OD-202]
    changes: [CHG-303]
  INC-103:
    state: conditional
    depends_on: [INC-102]
    requires: []
    changes: []
  INC-104:
    state: conditional
    depends_on: [INC-103]
    requires: []
    changes: []
---

""", 1) + """\
# Progressive implementation roadmap: Borea

**Question:** which increments do we hypothesize, in which order are they delivered, and
which evidence and which decisions do they depend on?

## Delivery stages

### t1 · Il calendario delle squadre

- **Entry criteria:** the technicians' records come from the personnel system.
- **Exit criteria:** the pilot team plans a week with the calendar alone.

### t2 · Gli avvisi ai clienti

- **Entry criteria:** visits have reliable slots.
- **Exit criteria:** a customer receives the slot of the visit without phoning.

### t3 · L'app per i tecnici

- **Entry criteria:** the pilot team asks for it.
- **Exit criteria:** a technician closes a visit from the field.

## Increments

### INC-101 · A calendar per team, with travel times

| Field | Content |
|---|---|
| Expected outcome | a dispatcher plans a day without a spreadsheet |
| Evidence it depends on | none: the pilot team plans by hand today |
| Architecture enabler | `DEC-210` |
| Entry criteria | can start now |
| Exit criteria | a day planned with no two visits overlapping |
| Products involved | borea |

### INC-102 · The customer is told when the technician arrives

| Field | Content |
|---|---|
| Expected outcome | fewer calls asking where the technician is |
| Evidence it depends on | the share of calls that ask it, measured by the dispatchers |
| Architecture enabler | none |
| Entry criteria | INC-101 in use |
| Exit criteria | the first customer notified by the product |
| Products involved | borea |

### INC-103 · An environment where the pilot team tries a release

| Field | Content |
|---|---|
| Expected outcome | a release is tried before every team gets it |
| Evidence it depends on | whether the pilot team can spare a day a month |
| Architecture enabler | none |
| Entry criteria | the systems team grants a server |
| Exit criteria | one release tried there |
| Products involved | borea |

### INC-104 · A phone app for the technicians

| Field | Content |
|---|---|
| Expected outcome | a technician closes a visit from the field |
| Evidence it depends on | whether the technicians carry a company phone |
| Architecture enabler | none |
| Entry criteria | the pilot team asks for it |
| Exit criteria | a visit closed from a phone |
| Products involved | borea |

## §Not in roadmap

The export to the accounting system: it is asked for the second release.
"""


def item(title, what, theme, scope, seen=None, **kw) -> dict:
    out = {"title": title, "what": what, "theme": theme, "scope": scope}
    if seen:
        out["seen"] = seen
    out.update(kw)
    return out


ITEMS = {
    # The increments of the stages: groups, so a title and the confirmed register title.
    "INC-101": {"title": "un calendario per squadra, con i tempi di viaggio",
                "seen": "A calendar per team, with travel times"},
    "INC-102": {"title": "il cliente sa quando arriva il tecnico",
                "seen": "The customer is told when the technician arrives"},
    "INC-103": {"title": "un ambiente di prova per la squadra pilota",
                "seen": "An environment where the pilot team tries a release"},
    "INC-104": {"title": "l'app sul telefono per i tecnici",
                "seen": "A phone app for the technicians"},
    "OD-200": item("un calendario per squadra",
                   "ogni squadra di tecnici ha un proprio calendario, invece di un calendario "
                   "unico per tutta l'azienda.", "architettura", "1.0", size="M",
                   closed_on="2026-10-01", hours_before=4),
    "OD-201": item("come si assegna un intervento al tecnico",
                   "la regola con cui ogni intervento viene affidato a un tecnico: a mano, per "
                   "zona oppure con un calcolo che riduce gli spostamenti.", "architettura",
                   "1.0", "How a visit is assigned to a technician", size="L"),
    "OD-202": item("con quanto anticipo si avvisa il cliente",
                   "quanto tempo prima della visita il cliente riceve l'avviso con l'orario.",
                   "architettura", "1.0", "How early the customer is told", size="S"),
    "KI-021": item("vista del giorno lenta sulle squadre grandi",
                   "con più di quaranta tecnici la vista del giorno impiega secondi ad "
                   "aprirsi.", "sviluppo", "1.0", "The day view is slow on large teams",
                   size="S"),
    "CHG-301": item("anagrafica dei tecnici",
                    "l'elenco dei tecnici con zona e competenze, caricato dal sistema del "
                    "personale invece che a mano.", "sviluppo", "1.0", size="M",
                    closed_on="2026-10-02", hours_before=6),
    "CHG-302": item("tempi di viaggio fra gli interventi",
                    "il calcolo del tempo per andare da un intervento al successivo, così il "
                    "calendario non mette due visite troppo vicine.", "sviluppo", "1.0",
                    "Travel times between visits", size="L"),
    "CHG-303": item("avviso al cliente via SMS",
                    "un messaggio al cliente con il giorno e la fascia oraria della visita.",
                    "sviluppo", "1.0", "Text message to the customer", size="M"),
    "CHG-304": item("ambiente di collaudo",
                    "un ambiente separato dove la squadra pilota prova il prodotto prima che "
                    "arrivi a tutti.", "deploy", "1.0", "Acceptance environment", size="M"),
    "CHG-305": item("esportazione verso il gestionale",
                    "il passaggio automatico degli interventi chiusi al sistema che emette le "
                    "fatture.", "sviluppo", "out", "Export to the accounting system",
                    size="L", out_reason="la chiede l'amministrazione per il secondo rilascio"),
}
BULK = {
    "2026-09-28": ({"architettura": 2}, {"riunioni": 3, "formazione": 1}),
    "2026-09-29": ({"architettura": 2}, {"riunioni": 2, "reportistica": 2}),
    "2026-09-30": ({}, {"supporto": 4, "riunioni": 1}),
    "2026-10-01": ({"sviluppo": 3}, {"riunioni": 2}),
    "2026-10-02": ({"sviluppo": 3}, {"reportistica": 1}),
    "2026-10-05": ({}, {"supporto": 3, "riunioni": 1}),
}
WAITS = [
    {"what": "Elenco delle competenze dei tecnici", "owner": "ufficio operativo",
     "asked": "2026-09-29", "needed_by": "2026-10-09",
     "without": "l'assegnazione automatica sceglie il tecnico solo per zona.",
     "missing": "manca l'elenco delle competenze", "blocks": ["OD-201"]},
    {"what": "Accesso al server di collaudo", "owner": "team sistemi",
     "asked": "2026-10-01", "needed_by": "2026-10-12",
     "without": "la squadra pilota non può provare il prodotto.",
     "missing": "manca l'accesso al server di collaudo", "slows": ["CHG-304"]},
]


def state(stage: str) -> dict:
    days = {d: {k: v for k, v in (("themes", t), ("outside", o)) if v}
            for d, (t, o) in BULK.items()}
    out = {"format": 2, "product": "borea",
           "release": {"name": "1.0", "delivery": "2026-10-16", "start": "2026-09-28"},
           "items": ITEMS, "order": {"todo": ["KI-021"], "out": ["CHG-305"]},
           "days": days, "waits": WAITS}
    if stage == "07":
        # One hour of the day on CHG-303 and not on CHG-302: the day and its theme add up to
        # what they did before, so the pace and every date computed from it stay put.
        days["2026-10-06"] = {"hours": {"CHG-302": 3, "CHG-303": 1, "OD-201": 2},
                              "outside": {"riunioni": 1}}
        out["plan"] = {"2026-10-07": [{"item": "CHG-302", "hours": 4}],
                       "2026-10-08": [{"item": "CHG-302", "hours": 4, "closes": True}]}
        out["milestones"] = [{"stage": "t1", "date": "2026-10-14"},
                             {"stage": "t2", "date": "2026-10-23"},
                             {"stage": "t3", "date": "2026-10-30"}]
    return out


def write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def run(*args, cwd: Path, when: str | None = None) -> str:
    env = dict(os.environ, GIT_AUTHOR_NAME="lead", GIT_AUTHOR_EMAIL="lead@example.com",
               GIT_COMMITTER_NAME="lead", GIT_COMMITTER_EMAIL="lead@example.com")
    if when:
        env.update(GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    r = subprocess.run(list(args), cwd=cwd, env=env, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"{' '.join(args)} failed in {cwd}:\n{r.stdout}\n{r.stderr}")
    return r.stdout.strip()


def commit(root: Path, message: str, when: str) -> None:
    run("git", "add", "-A", cwd=root)
    run("git", "commit", "-q", "-m", message, cwd=root, when=when)


def write_state(store: Path, data: dict) -> None:
    write(store, "state-borea.yaml",
          "# Stato del digest di Borea, scritto dalla skill `digest` con le risposte della "
          "persona.\n" + yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=100))


def build(root: Path) -> None:
    root.mkdir(parents=True)
    run("git", "init", "-q", "-b", "main", cwd=root)
    write(root, ".gitignore", "_meta/digest/\n.remote/\n")
    files = {"AGENTS.md": AGENTS, "OPEN.md": ROOT_OPEN, "products/borea/product.yaml": PRODUCT,
             "products/borea/PBR.md": PBR, "products/borea/LOG.md": LOG,
             "products/borea/cycles/ICG-001-cycle-1.md": ICG,
             "decisions/DEC-210-team-calendar.md": DEC_210,
             "products/borea/OPEN.md": OPEN, "products/borea/RMP.md": RMP}
    for cid in CHANGES:
        files[f"products/borea/changes/{cid}.md"] = change(cid)
    for rel, text in files.items():
        write(root, rel, text)
    run(sys.executable, str(FRAMEWORK / "skills/audit/scripts/validate.py"), "--root",
        str(root), "--emit-index", cwd=root)
    commit(root, "Borea: the registers and the roadmap in stages", "2026-10-05T10:00:00+02:00")

    remote = root / ".remote" / "digest.git"
    remote.mkdir(parents=True)
    run("git", "init", "-q", "--bare", "-b", "main", cwd=remote)
    store = root / "_meta" / "digest"
    store.mkdir(parents=True)
    run("git", "init", "-q", "-b", "main", cwd=store)
    run("git", "remote", "add", "origin", "../../.remote/digest.git", cwd=store)
    for k, v in (("user.name", "lead"), ("user.email", "lead@example.com")):
        run("git", "config", k, v, cwd=store)
    write_state(store, state("06"))
    r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "--product", "borea",
                        "--baseline", "--date", "2026-10-06",
                        "--now", "2026-10-06T08:30:00+02:00"], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"the baseline was refused:\n{r.stdout}\n{r.stderr}")

    write(root, "src/travel.py", '"""Travel time between two visits, in minutes."""\n\n\n'
                                 "def minutes(a: tuple, b: tuple) -> int:\n"
                                 "    return 10 + abs(a[0] - b[0]) + abs(a[1] - b[1])\n")
    commit(root, "CHG-302: travel time between two visits", "2026-10-06T15:00:00+02:00")
    write_state(store, state("07"))


def main() -> int:
    dest = Path(sys.argv[1])
    shutil.rmtree(dest, ignore_errors=True)
    build(dest / "borea")
    return 0


if __name__ == "__main__":
    sys.exit(main())
