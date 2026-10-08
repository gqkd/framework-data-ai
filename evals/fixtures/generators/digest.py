#!/usr/bin/env python3
"""Build the repositories the `digest` skill is measured on: one product, a dated history.

    python digest.py <dest>          writes <dest>/atlas and <dest>/atlas-asks

`atlas` is the documentation of one product as it stands on the morning of 09/10/2026, with its
history in git and the digest's store beside it. The project started on 22/09; the days up to
05/10 were rebuilt in bulk when the digest was adopted, and the baseline was written by the
digest script itself on 06/10 at 08:30. On 06/10 a decision closed `OD-114` and two changes
were verified; the digest of 07/10 was rendered at 08:30, again by the script; on 07/10 a known
issue was resolved, and on 08/10 `OD-098` was split in two, `OD-116` was decided and with it
`CHG-021` left the release. The state file is filled for the digest of 09/10, and rendering
it must give, cell by cell, the reference workbook `tests/fixtures/digest/`, which is what
`tests/selfcheck.py` asserts.

`atlas-asks` is the same morning before anybody answered: one more known issue in the register
that the state file does not classify, the two new entries of the split unclassified, and
neither the hours of 07/10 and 08/10 nor the plan declared. It is what the behaviour case runs
on, and what the skill has to ask about.

WHY GENERATED AND NOT STATIC. The baseline and the digest of 07/10 are the script's own output,
so they are produced by the script at build time rather than copied in by hand and left behind
the first time the snapshot format moves; and the worked-on list the skill proposes comes from
`git log`, which a directory of files does not have. The store `_meta/digest/` is a git
repository of its own whose remote is a bare repository in `.remote/`, a relative path, so that
a copy of the fixture pushes into its own copy and never into this one.

Everything here is synthetic: the product, the people and every number.
"""


from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
FRAMEWORK = HERE.parents[2]
SCRIPT = FRAMEWORK / "skills" / "digest" / "scripts" / "digest.py"
REVIEW = "2026-09-30 10:00"


def fm(**kw) -> str:
    lines = []
    for k, v in kw.items():
        if isinstance(v, str) and "\n" in v:
            lines.append(f"{k}:{v}")
        else:
            lines.append(f"{k}: {v}")
    return "---\n" + "\n".join(lines) + "\n---\n\n"


def living(artifact_type: str, **kw) -> dict:
    return dict(schema=f"framework/{artifact_type}/v1", artifact_type=artifact_type,
                lifecycle="living", status="active", **kw)


AGENTS = fm(**living("agents-control-plane"), owners="[lead]", created=REVIEW,
            last_review=REVIEW, classification="internal") + """\
# Instructions for agents

Read this file first. Then `products/atlas/OPEN.md` and `OPEN.md` at the root, then
`products/atlas/product.yaml`.

## Authoritative sources

| Question | Source |
|---|---|
| Where the code is | `products/atlas/product.yaml` under `code:` |
| Why it is built that way | the decision records in `decisions/` |
| What the product does and for whom | `products/atlas/PBR.md` |
| What is not decided | `products/atlas/OPEN.md` |
| What you are authorized to build right now | the change contracts in `products/atlas/changes/` |

## Non negotiable rules

1. Do not take decisions listed in an `OPEN.md`: stop and ask.
2. Do not implement a signal. What gets implemented is an approved change contract.

## Commands

```bash
python3 ../framework-data-ai/skills/audit/scripts/validate.py --root .
```
"""

ROOT_OPEN = fm(**living("open-register"), products="[atlas]", owners="[lead]", created=REVIEW,
               last_review=REVIEW, classification="internal", entries="{}") + """\
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

PRODUCT = """\
schema: framework/product-manifest/v1
artifact_type: product-manifest
lifecycle: living
status: active
products: [atlas]
name: Atlas
one_liner: Answers questions about a customer's own metrics in plain language.
owners: [lead]
created: 2026-09-30 10:00
last_review: 2026-09-30 10:00
stage:
  block: B
  phase: BUILD
release:
  current: REL-001
  manifest: RLM-001
  deployed_at: 2026-10-05
  rollback_target: null
code:
  monorepo:
    url: git@example.com:atlas/atlas.git
    contains: the whole product, these documents included
    path: .
"""

PBR = fm(**living("product-brief"), products="[atlas]", owners="[lead]", created=REVIEW,
         last_review=REVIEW, classification="internal") + """\
# Atlas · product brief

## One line

Answers questions about a customer's own metrics in plain language, and each customer sees
only its own data.

## Actors

Analysts at the customer, who ask; the customer's administrator, who decides who may ask.

## Outcome

An analyst gets a number from a defined metric without writing a query.
"""

EVP = fm(**living("evaluation-plan"), version="1.0.0", products="[atlas]", owners="[lead]",
         created=REVIEW, last_review=REVIEW, derives_from="[PBR]",
         classification="internal") + """\
# Evaluation plan: Atlas

## Evaluation dataset

Two hundred questions written by the functional team, each with the metric it asks for.

## Baseline

The analysts' own queries, on the same questions.

## Metrics and thresholds

| Metric | Definition | Baseline | Minimum threshold | Target | Blocks the release? |
|---|---|---|---|---|---|
| metric resolution | share of questions mapped to the metric they ask for | 0.80 | 0.90 | 0.95 | yes |
"""




ICG = fm(schema="framework/impact-classification/v1", artifact_type="impact-classification",
         lifecycle="immutable", status="accepted", id="ICG-001", products="[atlas]",
         owners="[lead]", created="2026-09-02 10:00",
         routing="\n" + "\n".join(f"  SIG-00{i}: none" for i in range(1, 9)),
         classification="internal") + """\
# ICG-001 · Triage of cycle 1

<!-- section: intake -->
## Intake

The eight signals of the log, all raised while setting the product up.

<!-- section: classification -->
## Classification

None of them changes what the product is for or how it is built: each is a technical change
inside the architecture already decided.

<!-- section: open-questions -->
## Open questions

None.
"""

CHANGES = {
    # id: (slug, register title, signal, extra derives_from, created)
    "CHG-012": ("monorepo", "Single repository", "SIG-001", "", "2026-09-03 10:00"),
    "CHG-015": ("external-login", "Login through an external identity provider", "SIG-002",
                "", "2026-09-03 10:10"),
    "CHG-017": ("token-exchange", "Token exchange at login", "SIG-003", "",
                "2026-09-03 10:20"),
    "CHG-018": ("tenant-isolation", "Per-tenant data isolation", "SIG-004", ", DEC-019",
                "2026-09-03 10:30"),
    "CHG-019": ("release-pipeline", "Release pipeline", "SIG-005", "", "2026-09-03 10:40"),
    "CHG-021": ("loading-notice", "Loading-in-progress notice", "SIG-006", "",
                "2026-09-03 10:50"),
    "CHG-022": ("version-tags", "Version tags trigger builds", "SIG-007", "",
                "2026-09-03 11:00"),
    "CHG-024": ("first-preprod", "First release to preprod", "SIG-008", "",
                "2026-09-03 11:10"),
}


def change(cid: str, status: str) -> str:
    slug, title, sig, extra, created = CHANGES[cid]
    verified = ("\n## Verification\n\nVerified in the development environment after the "
                "deployment of REL-001 (RLM-001): the criteria of point 3 hold.\n"
                if status == "verified" else "")
    return fm(schema="framework/change-contract/v1", artifact_type="change-contract",
              lifecycle="immutable", status=status, id=cid, products="[atlas]",
              owners="[lead]", approvers="[lead]", created=created, icg="ICG-001",
              derives_from=f"[atlas:{sig}{extra}]", verified_by="null",
              classification="internal") + f"""\
# {cid} · {title}

<!-- section: what-changes -->
### 1 · What changes

{title}, as the signal {sig} asks.

<!-- section: what-must-not-change -->
### 2 · What must NOT change

The answers already given to every customer, and the data each one can see.

<!-- section: how-we-know-it-worked -->
### 3 · How we know it worked

The product's tests pass, and the scenario of {sig} no longer happens.
{verified}"""


DEC_020 = fm(schema="framework/decision-record/v1", artifact_type="decision-record",
             lifecycle="immutable", status="accepted", id="DEC-019", scope="architecture",
             products="[atlas]", owners="[lead]", approvers="[lead]",
             created="2026-09-01 15:00", derives_from="[]", supersedes="null",
             classification="internal", leaves_open="[]") + """\
# DEC-019 · One datastore per tenant

## Context

Customers must not see each other's data, and a filter applied to a shared store fails open.

## Decision

Each customer has a datastore of its own.

## Alternatives considered

| Alternative | Why discarded |
|---|---|
| One store, filtered per customer | one missing filter exposes every customer |

## Consequences

Isolation holds by construction. Each new customer costs a store to provision.
"""

DEC_027 = fm(schema="framework/decision-record/v1", artifact_type="decision-record",
             lifecycle="immutable", status="accepted", id="DEC-026", scope="architecture",
             products="[atlas]", owners="[lead]", approvers="[lead]",
             created="2026-10-06 11:00", derives_from="[OD-114]", supersedes="null",
             classification="internal", leaves_open="[]") + """\
# DEC-026 · A fixed rule maps a question to a defined metric

## Context

The same question was answered from two different metrics depending on how it was phrased.

## Decision

A question is mapped to a metric of the glossary by a fixed rule, applied before any query.

## Alternatives considered

| Alternative | Why discarded |
|---|---|
| Let the model choose the metric | the same question gets different numbers |

## Consequences

A question no metric covers gets no number, which is what OD-109 is about.
"""



def signal_log(resolved: bool) -> str:
    """The log; on 07/10 it records what resolved KI-013, which the register then names."""
    row = ("| SIG-009 | 2026-10-07 | observation | long questions answer again after the "
           "platform's time limit was raised | none | infrastructure team | KI-013 |\n"
           if resolved else "")
    return fm(schema="framework/signal-log/v1", artifact_type="signal-log",
              lifecycle="append-only", status="active", products="[atlas]", owners="[lead]",
              created=REVIEW, classification="internal") + """\
# Signal log: Atlas

## Signals

| ID | Date | Type | Observed | Impact | Who/Where | Linked |
|---|---|---|---|---|---|---|
| SIG-001 | 2026-09-01 | request | three repositories drift apart at every release | slower releases | team | CHG-012 |
| SIG-002 | 2026-09-01 | request | passwords are stored by the product itself | security review | team | CHG-015 |
| SIG-003 | 2026-09-01 | request | the session does not say which customer a user belongs to | data exposure | team | CHG-017 |
| SIG-004 | 2026-09-01 | request | all customers share one datastore | data exposure | team | CHG-018 |
| SIG-005 | 2026-09-01 | request | every deployment is done by hand | errors at release | team | CHG-019 |
| SIG-006 | 2026-09-01 | feedback | answers during a data load are incomplete | wrong numbers | pilot customer | CHG-021 |
| SIG-007 | 2026-09-01 | request | builds are started by hand | errors at release | team | CHG-022 |
| SIG-008 | 2026-09-01 | request | nothing is tested in a production-like environment | errors in production | team | CHG-024 |
""" + row


ICG_2 = fm(schema="framework/impact-classification/v1", artifact_type="impact-classification",
           lifecycle="immutable", status="accepted", id="ICG-002", products="[atlas]",
           owners="[lead]", created="2026-10-07 16:00", routing="\n  SIG-009: none",
           classification="internal") + """\
# ICG-002 · Triage of cycle 2

<!-- section: intake -->
## Intake

One signal: long questions answer again since the platform's time limit was raised.

<!-- section: classification -->
## Classification

It changes nothing in the product: it records why a known issue is resolved.

<!-- section: open-questions -->
## Open questions

None.
"""


DEC_036 = fm(schema="framework/decision-record/v1", artifact_type="decision-record",
             lifecycle="immutable", status="accepted", id="DEC-036", scope="product",
             products="[atlas]", owners="[lead]", approvers="[lead]",
             created="2026-10-08 12:00", derives_from="[OD-116]", supersedes="null",
             classification="internal", leaves_open="[]") + """\
# DEC-036 · The loading notice moves to the next release

## Context

The question whether the loading notice ships with release 1.0 had no answer by the day it
was needed, and the release has no room for it.

## Decision

The loading notice ships with the release after 1.0. Until then an answer given during a
data load says that the data are being loaded.

## Alternatives considered

| Alternative | Why discarded |
|---|---|
| Keep it in release 1.0 | it does not fit before the agreed delivery |

## Consequences

`CHG-021` leaves release 1.0 and stays approved for the next one.
"""

# The register's entries, as rows of its front matter and as headings of its body, by stage:
# "06" is 05/10 and the morning of 06/10, "07" is after the work of 06/10, "09" after the work
# of 07/10 and 08/10.
ROWS = {
    "OD-076": """
  OD-076:
    status: open
    cost_to_reverse: medium
    default_in_force: the browser keeps the access token
    trigger: the security review of the first customer release""",
    "OD-098": """
  OD-098:
    status: open
    cost_to_reverse: high
    default_in_force: the current loading tool stays
    trigger: the first data source the tool cannot read""",
    "OD-098-split": """
  OD-098:
    status: superseded""",
    "OD-109": """
  OD-109:
    status: open
    cost_to_reverse: low
    default_in_force: a question with no defined metric gets no answer
    trigger: the metric glossary arriving from the functional team""",
    "OD-114": """
  OD-114:
    status: open
    cost_to_reverse: low
    default_in_force: the model chooses the metric
    trigger: the first two answers to one question that disagree""",
    "OD-114-decided": """
  OD-114:
    status: decided
    closed_by: DEC-026""",
    "OD-115": """
  OD-115:
    status: open
    cost_to_reverse: low
    default_in_force: the raw message of the service reaches the user
    trigger: the first release a customer uses""",
    "OD-116": """
  OD-116:
    status: open
    cost_to_reverse: low
    default_in_force: the loading notice is part of release 1.0
    trigger: the project lead reviewing the scope of release 1.0""",
    "OD-116-decided": """
  OD-116:
    status: decided
    closed_by: DEC-036""",
    "OD-120": """
  OD-120:
    status: open
    cost_to_reverse: medium
    default_in_force: the loader reads the two formats it reads today
    trigger: the first source in another format""",
    "OD-121": """
  OD-121:
    status: open
    cost_to_reverse: medium
    default_in_force: the data are loaded every night
    trigger: a customer asking for fresher data""",
    "KI-013": """
  KI-013:
    status: open""",
    "KI-013-resolved": """
  KI-013:
    status: decided
    closed_by: SIG-009""",
    "KI-014": """
  KI-014:
    status: open""",
}
STAGE_ROWS = {
    "06": ["OD-076", "OD-098", "OD-109", "OD-114", "OD-116"],
    "07": ["OD-076", "OD-098", "OD-109", "OD-114-decided", "OD-115", "OD-116", "KI-013"],
    "09": ["OD-076", "OD-098-split", "OD-109", "OD-114-decided", "OD-115", "OD-116-decided",
           "OD-120", "OD-121", "KI-013-resolved"],
}

H_076 = """### OD-076 · Where the access token is kept

- **Question:** does the access token stay in the browser, or move to a component on the
  server?
- **The problem the default introduces:** a script running in the browser can read it.
"""
H_076_NOTES = H_076 + """\
- **Notes:** a component on the server would hold the token and give the browser a session
  cookie only; it waits for the security review.
"""
H_098 = """### OD-098 · Keep or replace the data loading tool

- **Question:** does the tool that loads the customers' data stay, or is it replaced by code
  of our own?
- **The problem the default introduces:** two of the planned sources are not supported.
"""
H_109 = """### OD-109 · How to answer a question no metric covers

- **Question:** refuse, warn, or answer anyway when no defined metric fits?
"""
H_114 = """### OD-114 · Which rule maps a question to a defined metric

- **Question:** does the model choose the metric, or a fixed rule?
"""
H_115 = """### OD-115 · What an error shows to the user

- **Question:** which details of a failure reach the user, and which stay in the logs?
"""
H_116 = """### OD-116 · Whether the loading notice stays in release 1.0

- **Question:** does the loading notice ship with release 1.0, or with the next one?
"""
H_120 = """### OD-120 · Which file formats the loader reads

- **Question:** which formats of the customers' files does the loader have to read?
- **The problem the default introduces:** two of the planned sources send another format.
"""
H_121 = """### OD-121 · How often the customers' data is loaded

- **Question:** once a night, several times a day, or as the data arrive?
- **The problem the default introduces:** an answer can be a day old.
"""
KI_013 = """### KI-013 · Long questions exceed the timeout

- Questions that need many calculation steps exceed the time limit, and no answer arrives.
- Accepted while the pilot uses short questions only.
- The analysts asking long questions bear it.
- **Reopening trigger:** a pilot user asking a question with more than three steps.
- **Reference:** none yet.
"""
KI_014 = """### KI-014 · Exports time out on large tenants

- An export of more than a year of data stops before it ends.
- Accepted while no customer exports a full year.
- The administrators of the two largest customers bear it.
- **Reopening trigger:** the first export request covering a full year.
- **Reference:** none yet.
"""
CLOSED = {
    "OD-114": "- **2026-10-06 · OD-114** → [`DEC-026`](../../decisions/DEC-026-metric-"
              "resolution.md) · a fixed rule maps a question to a metric.\n",
    "KI-013": "- **2026-10-07 · KI-013** → `SIG-009` · the platform's time limit was raised, and "
              "long questions answer again.\n",
    # Superseded and not decided, so it keeps its heading: only a decided entry may leave the
    # body for a line here.
    "OD-098": "### OD-098 · Keep or replace the data loading tool\n\n- **Superseded on "
              "2026-10-08** by OD-120 and OD-121: which formats the loader reads, and how often "
              "it runs, are decided apart.\n",
    "OD-116": "- **2026-10-08 · OD-116** → [`DEC-036`](../../decisions/DEC-036-loading-notice-"
              "scope.md) · the loading notice moves to the next release.\n",
}


def product_open(stage: str, review: str = f"last_review: {REVIEW}", ki_014: bool = False,
                 notes_076: bool = False) -> str:
    rows = "".join(ROWS[k] for k in STAGE_ROWS[stage]) + (ROWS["KI-014"] if ki_014 else "")
    high = [H_098] if stage != "09" else []
    medium = [H_076_NOTES if notes_076 else H_076] + ([H_120, H_121] if stage == "09" else [])
    low = [H_109] + ([H_114] if stage == "06" else [H_115]) + ([H_116] if stage != "09" else [])
    known = [KI_013] if stage == "07" else []
    known += [KI_014] if ki_014 else []
    closed = {"06": [], "07": ["OD-114"], "09": ["OD-114", "KI-013", "OD-098", "OD-116"]}[stage]
    head = ("---\nschema: framework/open-register/v1\nartifact_type: open-register\n"
            "lifecycle: living\nstatus: active\nowners: [lead]\n"
            f"created: {REVIEW}\n{review}\nclassification: internal\nentries:{rows}\n---\n\n")
    return head + f"""\
# Open decisions and known issues: Atlas

# §1 · Open decisions

## Cost to reverse HIGH: changing it later means redoing work that already exists

{chr(10).join(high) if high else "None." + chr(10)}
## Cost to reverse MEDIUM: changing it later costs a migration, not a rewrite

{chr(10).join(medium)}
## Cost to reverse LOW: changing it later costs an afternoon

{chr(10).join(low)}
# §2 · Accepted known issues
{"".join(chr(10) + k for k in known)}
# §3 · Parking lot

# §4 · Closed decisions
{"".join(chr(10) + CLOSED[k] for k in closed)}"""


RMP = fm(**living("roadmap"), version="1.0.0", products="[atlas]", owners="[lead]",
         created=REVIEW, last_review=REVIEW, classification="internal") + """\
# Progressive implementation roadmap: Atlas

## Increments

### INC-040 · A shared token service for every product

| Field | Content |
|---|---|
| State | conditional |
| Expected outcome | one place issues the access tokens of every product |
| Depends on | evidence that a second product needs the same tokens |
| Architecture enabler | a decision on a shared substrate, not taken |
| Entry criteria | a second product in development |
| Exit criteria | both products log in through it |
| Products involved | atlas only, today |

### INC-041 · Anomaly detection on customer metrics

| Field | Content |
|---|---|
| State | shaped |
| Expected outcome | an analyst is told when a value leaves its usual range |
| Depends on | three months of history per customer |
| Architecture enabler | none |
| Entry criteria | release 1.0 in production |
| Exit criteria | a pilot customer receives the alerts |
| Products involved | atlas |

## §Not in roadmap

Nothing yet.
"""


def releases(evp_hash: str, commit: str) -> dict[str, str]:
    evr = fm(schema="framework/evaluation-report/v1", artifact_type="evaluation-report",
             lifecycle="immutable", status="active", id="EVR-001", products="[atlas]",
             owners="[lead]", created="2026-10-05 15:00", derives_from="[EVP]",
             evp_version="1.0.0", evp_hash=evp_hash, frozen_at=commit,
             verified_code=f"\n  product.monorepo: {commit}",
             classification="internal") + """\
# EVR-001 · Evaluation report

## Version evaluated

| Element | Version or hash |
|---|---|
| Code | the commit in `verified_code` |
| **Reference `EVP`** | 1.0.0 and the hash above |

## Results

| Metric | `EVP` threshold | Baseline | Result | Outcome |
|---|---|---|---|---|
| metric resolution | 0.90 | 0.80 | 0.91 | pass |

## Verdict

`go`, for the development environment only.
"""
    rel = fm(schema="framework/release-note/v1", artifact_type="release-note",
             lifecycle="immutable", status="active", id="REL-001", products="[atlas]",
             owners="[lead]", created="2026-10-05 16:00",
             derives_from="[CHG-012, CHG-015, CHG-017, CHG-019, EVR-001]",
             classification="internal") + """\
# REL-001 · First build in the development environment

## What changes

The product runs from one repository, users log in through the external provider, and a
release reaches the development environment without manual steps.

## Changes included

`CHG-012` · `CHG-015` · `CHG-017` · `CHG-019`

## Risks and rollback

The development environment holds synthetic data only. Rollback redeploys the previous build.
"""
    rlm = f"""\
# RLM-001 · Release manifest. Machine-readable, immutable.
schema: framework/release-manifest/v1
artifact_type: release-manifest
id: RLM-001
lifecycle: immutable
status: active
generated_by: release
products: [atlas]
release_note: REL-001
created: 2026-10-05T14:00:00Z
code:
  commit: {commit}
  tag: v0.1.0
  branch: main
infrastructure:
  target: development
evaluation:
  report: EVR-001
  evp_version: 1.0.0
  evp_hash: {evp_hash}
  verdict: go
changes:
  contracts: [CHG-012, CHG-015, CHG-017, CHG-019]
  decisions: [DEC-019]
approvals:
  - who: lead
    role: tech
    at: 2026-10-05T13:55:00Z
rollback:
  target: none, the first build in this environment
  procedure: redeploy the previous development build
  tested: true
"""
    return {"products/atlas/releases/EVR-001-dev-build.md": evr,
            "products/atlas/releases/REL-001-dev-build.md": rel,
            "products/atlas/releases/RLM-001-dev-build.yaml": rlm}



# THE STATE FILE, AS THE SKILL WOULD HAVE WRITTEN IT. The Italian is the workbook's: every
# title, description and reason here is printed as it stands.

def item(title, what, theme, scope, seen=None, **kw) -> dict:
    out = {"title": title, "what": what, "theme": theme, "scope": scope}
    if seen:
        out["seen"] = seen
    out.update(kw)
    return out


def items_06() -> dict:
    """The classification confirmed at the baseline, on the morning of 06/10."""
    return {
        "OD-076": item(
            "custodia del permesso di accesso lato server",
            "spostare la custodia del permesso dal browser a un componente lato server, per "
            "ridurre l'esposizione in caso di attacco al browser.",
            "architettura", "out", "Where the access token is kept",
            out_reason="miglioria di sicurezza prevista dopo il rilascio"),
        "OD-098": item(
            "tenere o sostituire lo strumento di caricamento dati",
            "se lo strumento che oggi carica i dati resta o viene sostituito da codice proprio. "
            "Tocca tutto il percorso dei dati, per questo va spezzata prima di poterla stimare.",
            "architettura", "1.0", "Keep or replace the data loading tool", size="XL"),
        "OD-109": item(
            "risposta alle domande non coperte",
            "come si comporta il sistema davanti a una domanda a cui non sa rispondere con un "
            "numero garantito: rifiuta, avvisa o risponde comunque.",
            "architettura", "1.0", "How to answer a question no metric covers", size="L"),
        "OD-114": item(
            "come il sistema capisce quale indicatore gli viene chiesto",
            "la regola con cui una domanda in linguaggio naturale viene ricondotta a un "
            "indicatore definito, da cui dipende che il numero in risposta sia quello giusto.",
            "architettura", "1.0", "Which rule maps a question to a defined metric", size="S"),
        "OD-116": item(
            "se l'avviso di caricamento resta nel rilascio",
            "la scelta se l'avviso di caricamento in corso entra in questo rilascio o nel "
            "successivo.",
            "sviluppo", "out", "Whether the loading notice stays in release 1.0",
            out_reason="è una scelta sul perimetro, la prende il responsabile di progetto"),
        "DEC-019": item(
            "un archivio dati per cliente",
            "ogni cliente ha un archivio fisicamente separato, invece di un archivio unico "
            "filtrato per cliente.",
            "architettura", "1.0", size="XL", closed_on="2026-09-29", hours_before=14),
        "CHG-012": item(
            "repository unica",
            "il codice di più repository separate riunito in una sola, con una struttura che "
            "permette di estrarne un componente senza riscriverlo.",
            "sviluppo", "1.0", size="L", closed_on="2026-09-24", hours_before=12),
        "CHG-015": item(
            "login con servizio esterno",
            "l'autenticazione degli utenti affidata a un servizio esterno specializzato, invece "
            "di gestire le password in proprio.",
            "sviluppo", "1.0", size="L", closed_on="2026-10-01", hours_before=8),
        "CHG-017": item(
            "scambio del permesso di accesso al login",
            "dopo il login il sistema rilascia un proprio permesso che indica a quale cliente "
            "appartiene l'utente, ed è ciò che impedisce a un cliente di vedere i dati di un "
            "altro.",
            "sviluppo", "1.0", "Token exchange at login", size="M"),
        "CHG-018": item(
            "isolamento dei dati per cliente",
            "ogni cliente ha un archivio dati separato e il sistema apre solo quello indicato "
            "dal permesso di accesso dell'utente.",
            "sviluppo", "1.0", "Per-tenant data isolation", size="L"),
        "CHG-019": item(
            "flusso di rilascio",
            "la sequenza fissa di passi con cui una versione del codice arriva in un ambiente, "
            "senza interventi manuali che cambiano ogni volta.",
            "deploy", "1.0", "Release pipeline", size="S"),
        "CHG-021": item(
            "avviso di caricamento in corso",
            "quando un caricamento dati è in corso la richiesta attende per un tempo limitato e "
            "poi avvisa l'utente di riprovare, invece di restituire dati incompleti.",
            "sviluppo", "1.0", "Loading-in-progress notice", size="M"),
        "CHG-022": item(
            "etichette di versione per il rilascio",
            "l'etichetta di versione che fa partire in automatico la costruzione e il rilascio "
            "in un ambiente.",
            "deploy", "1.0", "Version tags trigger builds", size="S"),
        "CHG-024": item(
            "primo rilascio in preprod",
            "la prima installazione della nuova versione nell'ambiente di prova che replica la "
            "produzione, dove si verifica prima di rilasciare.",
            "deploy", "1.0", "First release to preprod", size="M"),
        "INC-040": item(
            "servizio condiviso per i permessi di accesso",
            "un unico servizio che rilascia i permessi per tutti i prodotti, al posto del modulo "
            "interno a un solo prodotto.",
            "sviluppo", "out", "A shared token service for every product",
            out_reason="serve quando ci sarà un secondo prodotto"),
        "INC-041": item(
            "rilevamento delle anomalie",
            "segnalazione automatica dei valori che si discostano dall'andamento atteso.",
            "sviluppo", "out", "Anomaly detection on customer metrics",
            out_reason="previsto nell'architettura futura"),
        "EVR-001": {"scope": "out"},
    }


def items_07() -> dict:
    items = items_06()
    items["OD-114"]["closed_on"] = "2026-10-06"
    items["CHG-017"]["closed_on"] = "2026-10-06"
    items["CHG-019"]["closed_on"] = "2026-10-06"
    items["OD-115"] = item(
        "formato dei messaggi di errore",
        "cosa vede l'utente quando una richiesta non va a buon fine, e quali dettagli tecnici "
        "restano solo nei log.",
        "architettura", "1.0", "What an error shows to the user", size="S")
    items["KI-013"] = item(
        "tempo massimo superato sulle domande lunghe",
        "le domande che richiedono molti passaggi di calcolo superano il tempo massimo e "
        "l'utente non riceve risposta.",
        "sviluppo", "1.0", "Long questions exceed the timeout", size="M")
    return items


def items_09() -> dict:
    items = items_07()
    items["KI-013"].update(
        closed_on="2026-10-07",
        what="le domande che richiedono molti passaggi di calcolo superavano il tempo massimo e "
             "l'utente non riceveva risposta.")
    items["OD-098"]["split_into"] = ["OD-120", "OD-121"]
    items["OD-120"] = item(
        "formati dei dati in ingresso",
        "quali formati di file lo strumento di caricamento deve saper leggere.",
        "architettura", "1.0", "Which file formats the loader reads", size="L")
    items["OD-121"] = item(
        "frequenza dei caricamenti",
        "ogni quanto vengono caricati i dati dei clienti, e quindi quanto sono recenti.",
        "architettura", "1.0", "How often the customers' data is loaded", size="L")
    items["OD-116"]["closed_on"] = "2026-10-08"
    items["CHG-021"].update(scope="out",
                            out_reason="decisione presa su OD-116, passa al rilascio successivo")
    return items


# The days before the baseline, rebuilt in bulk by column: the hours on the product by theme,
# the hours outside it by category. Saturday and Sunday appear only when somebody worked.
BULK = {
    "2026-09-22": ({"sviluppo": 4}, {"riunioni": 2, "solleciti": 2}),
    "2026-09-23": ({"sviluppo": 4}, {"riunioni": 1, "solleciti": 2, "formazione": 1}),
    "2026-09-24": ({"sviluppo": 4}, {"supporto": 3, "riunioni": 1}),
    "2026-09-25": ({"architettura": 3}, {"supporto": 4, "riunioni": 2}),
    "2026-09-26": ({"architettura": 3}, {}),
    "2026-09-28": ({"architettura": 4}, {"supporto": 4, "riunioni": 1}),
    "2026-09-29": ({"architettura": 4}, {"reportistica": 3, "riunioni": 1, "formazione": 1}),
    "2026-09-30": ({"sviluppo": 4}, {"reportistica": 2, "riunioni": 1, "solleciti": 1}),
    "2026-10-01": ({"sviluppo": 4}, {"supporto": 3, "riunioni": 1}),
    "2026-10-02": ({}, {"supporto": 5, "riunioni": 2, "formazione": 1}),
    "2026-10-03": ({}, {"reportistica": 4}),
    "2026-10-04": ({}, {"supporto": 3}),
    "2026-10-05": ({}, {"supporto": 4, "reportistica": 3, "riunioni": 1}),
}
DAYS_BY_ITEM = {
    "2026-10-06": ({"OD-114": 5, "CHG-017": 3, "CHG-019": 1.5},
                   {"riunioni": 1, "formazione": 0.5}),
    "2026-10-07": ({"KI-013": 2},
                   {"supporto": 2, "reportistica": 1, "riunioni": 1, "formazione": 1.5}),
    "2026-10-08": ({"CHG-018": 4, "OD-076": 1}, {"riunioni": 1, "solleciti": 1}),
}


def days(until: str) -> dict:
    out = {}
    for d, (themes, outside) in BULK.items():
        out[d] = {k: v for k, v in (("themes", themes), ("outside", outside)) if v}
    for d, (hours, outside) in DAYS_BY_ITEM.items():
        if d < until:
            out[d] = {"hours": hours, "outside": outside}
    return out


WAITS = [
    {"what": "Risposta sul registro delle immagini", "owner": "team infrastruttura",
     "asked": "2026-10-01", "needed_by": "2026-10-07",
     "without": "le versioni non si possono costruire e rilasciare in automatico.",
     "missing": "manca la risposta sul registro delle immagini", "blocks": ["CHG-022"]},
    {"what": "Ambiente preprod", "owner": "team infrastruttura",
     "asked": "2026-09-25", "needed_by": "2026-10-09",
     "without": "le modifiche non si possono verificare né chiudere, e la stima non vale più.",
     "missing": "manca l'ambiente preprod", "blocks": ["CHG-024"]},
    {"what": "Domande di benchmark", "owner": "team funzionale",
     "asked": "2026-09-22", "needed_by": "2026-10-10",
     "without": "la qualità delle risposte non si può valutare in modo oggettivo prima del "
                "rilascio."},
    {"what": "Glossario delle metriche", "owner": "team funzionale",
     "asked": "2026-09-22", "needed_by": "2026-10-10",
     "without": "gli indicatori restano definiti a ipotesi e vanno rivisti dopo il rilascio.",
     "missing": "manca il glossario delle metriche", "slows": ["OD-109"]},
    {"what": "Decisione sull'avviso di caricamento", "owner": "responsabile di progetto",
     "asked": "2026-10-06", "needed_by": "2026-10-09",
     "without": "l'avviso resta nel rilascio senza che nessuno l'abbia scelto."},
]
MILESTONES = [{"name": "Demo al team funzionale", "date": "2026-10-15"}]


def state(stage: str) -> dict:
    """The state file as it stands before the digest of a day: 06, 07 or 09."""
    out = {"format": 2, "product": "atlas",
           "release": {"name": "1.0", "delivery": "2026-10-13", "start": "2026-09-22"}}
    waits = [dict(w) for w in WAITS]
    if stage == "06":
        out["items"] = items_06()
        out["order"] = {"todo": ["CHG-018", "OD-098", "OD-109", "OD-114", "CHG-017", "CHG-019",
                                 "CHG-021", "CHG-022", "CHG-024"],
                        "out": ["OD-076", "OD-116", "INC-040", "INC-041"]}
        out["days"] = days("2026-10-06")
    elif stage == "07":
        out["items"] = items_07()
        out["order"] = {"todo": ["CHG-018", "OD-098", "OD-109", "OD-115", "KI-013", "CHG-021",
                                 "CHG-022", "CHG-024"],
                        "out": ["OD-076", "OD-116", "INC-040", "INC-041"]}
        out["days"] = days("2026-10-07")
        out["plan"] = {"2026-10-07": [{"item": "KI-013", "hours": 2, "closes": True},
                                      {"item": "CHG-018", "hours": 3}],
                       "2026-10-08": [{"item": "CHG-018", "hours": 4}]}
        out["milestones"] = MILESTONES
    else:
        out["items"] = items_09()
        out["order"] = {"todo": ["CHG-018", "OD-120", "OD-121", "OD-109", "OD-115", "CHG-022",
                                 "CHG-024"],
                        "out": ["CHG-021", "OD-076", "INC-040", "INC-041"]}
        out["days"] = days("2026-10-09")
        out["plan"] = {"2026-10-09": [{"item": "CHG-018", "hours": 5}],
                       "2026-10-12": [{"item": "CHG-018", "hours": 2, "closes": True},
                                      {"item": "OD-120", "hours": 3}]}
        out["milestones"] = MILESTONES
        waits[4]["resolved"] = True
    out["waits"] = waits
    return out


def write_state(store: Path, data: dict) -> None:
    write(store, "state-atlas.yaml",
          "# Stato del digest di Atlas: ciò che la persona ha dichiarato, scritto dalla skill\n"
          "# `digest` con le sue risposte. Ore, taglie, perimetro, date e attese non stanno "
          "negli artefatti.\n" + yaml.safe_dump(data, allow_unicode=True, sort_keys=False,
                                                width=100))


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


def commit(root: Path, message: str, when: str) -> str:
    run("git", "add", "-A", cwd=root)
    run("git", "commit", "-q", "-m", message, cwd=root, when=when)
    return run("git", "rev-parse", "HEAD", cwd=root)


def index(root: Path) -> None:
    run(sys.executable, str(FRAMEWORK / "skills/audit/scripts/validate.py"), "--root",
        str(root), "--emit-index", cwd=root)


def render(root: Path, day: str, *extra: str) -> None:
    r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "--product", "atlas",
                        "--date", day, "--now", f"{day}T08:30:00+02:00", *extra],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"the digest of {day} was refused:\n{r.stdout}\n{r.stderr}")


def reread(root: Path, register: str, day: str, scope: str) -> None:
    """A register edited after its last reading is read again, in a commit of its own."""
    write(root, "products/atlas/OPEN.md", register)
    top = root / "OPEN.md"
    text = top.read_text(encoding="utf-8")
    start = text.index("last_review:")
    end = text.index("classification:", start)
    top.write_text(text[:start] + f"last_review: {day} 17:46\nreview_scope: the composed view "
                   f"of what is open, after {scope}\n" + text[end:], encoding="utf-8")
    commit(root, "The open registers reread", f"{day}T17:50:00+02:00")
    index(root)
    if run("git", "status", "--porcelain", cwd=root):
        commit(root, "indices regenerated", f"{day}T17:55:00+02:00")


def build(root: Path, asks: bool) -> None:
    root.mkdir(parents=True)
    run("git", "init", "-q", "-b", "main", cwd=root)
    write(root, ".gitignore", "_meta/digest/\n.remote/\n")
    files = {"AGENTS.md": AGENTS, "OPEN.md": ROOT_OPEN, "products/atlas/product.yaml": PRODUCT,
             "products/atlas/PBR.md": PBR, "products/atlas/EVP.md": EVP,
             "products/atlas/LOG.md": signal_log(False), "products/atlas/RMP.md": RMP,
             "products/atlas/cycles/ICG-001-cycle-1.md": ICG,
             "decisions/DEC-019-tenant-datastore.md": DEC_020,
             "products/atlas/OPEN.md": product_open("06")}
    status_05 = {"CHG-012": "verified", "CHG-015": "verified", "CHG-017": "implemented",
                 "CHG-019": "implemented", "CHG-018": "approved", "CHG-021": "approved",
                 "CHG-022": "approved", "CHG-024": "approved"}
    for cid, st in status_05.items():
        files[f"products/atlas/changes/{cid}-{CHANGES[cid][0]}.md"] = change(cid, st)
    for rel, text in files.items():
        write(root, rel, text)
    index(root)
    first = commit(root, "Atlas: the register before the development release",
                   "2026-10-05T14:00:00+02:00")
    evp_hash = hashlib.sha256((root / "products/atlas/EVP.md").read_bytes()).hexdigest()
    for rel, text in releases(evp_hash, first).items():
        write(root, rel, text)
    index(root)
    commit(root, "REL-001: first build in the development environment",
           "2026-10-05T16:00:00+02:00")

    # The store: a repository of its own, pushing to a bare one beside it.
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
    render(root, "2026-10-06", "--baseline")

    # 06/10, through the day.
    write(root, "decisions/DEC-026-metric-resolution.md", DEC_027)
    write(root, "products/atlas/OPEN.md", product_open("07"))
    index(root)
    commit(root, "OD-114 decided by DEC-026: a fixed rule maps a question to a metric",
           "2026-10-06T11:00:00+02:00")
    for cid, when in (("CHG-017", "15:00"), ("CHG-019", "16:00")):
        write(root, f"products/atlas/changes/{cid}-{CHANGES[cid][0]}.md",
              change(cid, "verified"))
        commit(root, f"{cid} verified in the development environment",
               f"2026-10-06T{when}:00+02:00")
    reread(root, product_open("07", "last_review: 2026-10-06 17:45\nreview_scope: the whole "
                                    "register, after the decision on the metric rule and the "
                                    "two new entries"),
           "2026-10-06", "the new entries of the product register")
    write_state(store, state("07"))
    render(root, "2026-10-07")

    # 07/10 and 08/10.
    write(root, "products/atlas/LOG.md", signal_log(True))
    write(root, "products/atlas/cycles/ICG-002-cycle-2.md", ICG_2)
    write(root, "products/atlas/OPEN.md", product_open("07").replace(
        ROWS["KI-013"], ROWS["KI-013-resolved"]).replace("\n" + KI_013, "").replace(
        CLOSED["OD-114"], CLOSED["OD-114"] + "\n" + CLOSED["KI-013"]))
    commit(root, "KI-013 resolved: the platform's time limit was raised",
           "2026-10-07T16:00:00+02:00")
    split = product_open("09", ki_014=asks).replace(ROWS["OD-116-decided"], ROWS["OD-116"])
    split = split.replace("\n" + CLOSED["OD-116"], "").replace(
        "## Cost to reverse LOW: changing it later costs an afternoon\n\n" + H_109 + "\n" + H_115,
        "## Cost to reverse LOW: changing it later costs an afternoon\n\n" + H_109 + "\n" + H_115
        + "\n" + H_116)
    write(root, "products/atlas/OPEN.md", split)
    commit(root, "OD-098 split into OD-120 and OD-121, decided apart",
           "2026-10-08T10:00:00+02:00")
    write(root, "decisions/DEC-036-loading-notice-scope.md", DEC_036)
    write(root, "products/atlas/OPEN.md", product_open("09", ki_014=asks))
    index(root)
    commit(root, "OD-116 decided by DEC-036: the loading notice moves to the next release",
           "2026-10-08T12:00:00+02:00")
    write(root, "src/tenant.py", '"""The datastore of a request is the one its token names."""'
                                 "\n\n\ndef datastore(token: dict) -> str:\n"
                                 '    return f"atlas-{token[\'tenant\']}"\n')
    commit(root, "CHG-018: open the datastore the access token names",
           "2026-10-08T15:00:00+02:00")
    write(root, "products/atlas/OPEN.md", product_open("09", ki_014=asks, notes_076=True))
    commit(root, "OD-076: notes on keeping the token on the server",
           "2026-10-08T16:30:00+02:00")
    reread(root, product_open("09", "last_review: 2026-10-08 17:45\nreview_scope: the whole "
                                    "register, after the split of OD-098 and the decision on "
                                    "the loading notice", ki_014=asks, notes_076=True),
           "2026-10-08", "the split and the decision of 08/10")

    if not asks:
        write_state(store, state("09"))


def main() -> int:
    dest = Path(sys.argv[1])
    shutil.rmtree(dest, ignore_errors=True)
    build(dest / "atlas", asks=False)
    build(dest / "atlas-asks", asks=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
