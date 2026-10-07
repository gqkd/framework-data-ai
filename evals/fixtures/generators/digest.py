#!/usr/bin/env python3
"""Build the repositories the `digest` skill is measured on: one product, a dated history.

    python digest.py <dest>          writes <dest>/atlas and <dest>/atlas-asks

`atlas` is the documentation of one product as it stands on the morning of 07/10/2026, with
its history in git: the register as it was on 05/10, a development release that evening, the
baseline of the digest written by the digest script itself on 06/10 at 08:30, the work of
06/10 committed through the day, and the state file filled for the digest of 07/10. Rendering
that digest must give `tests/fixtures/digest/DIG-002-atlas-2026-10-07.txt` character for
character, which is what `tests/selfcheck.py` asserts.

`atlas-asks` is the same morning before anybody answered: one more known issue in the register
that the state file does not classify, and neither the hours of 06/10 nor the plan declared.
It is what the behaviour case runs on, and what the skill has to ask about.

WHY GENERATED AND NOT STATIC. The baseline is the script's own output, so it is produced by
the script at build time rather than copied in by hand and left behind the first time the
snapshot format moves; and the worked-on list the skill proposes comes from `git log`, which a
directory of files does not have. The store `_meta/digest/` is a git repository of its own
whose remote is a bare repository in `.remote/`, a relative path, so that a copy of the fixture
pushes into its own copy and never into this one.

Everything here is synthetic: the product, the people and every number.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

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

LOG = fm(schema="framework/signal-log/v1", artifact_type="signal-log",
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

OPEN_ROWS_BASE = """
  OD-076:
    status: open
    cost_to_reverse: medium
    default_in_force: the browser keeps the access token
    trigger: the security review of the first customer release
  OD-098:
    status: open
    cost_to_reverse: high
    default_in_force: the current loading tool stays
    trigger: the first data source the tool cannot read
  OD-109:
    status: open
    cost_to_reverse: low
    default_in_force: a question with no defined metric gets no answer
    trigger: the metric glossary arriving from the functional team"""
OPEN_ROW_114_OPEN = """
  OD-114:
    status: open
    cost_to_reverse: low
    default_in_force: the model chooses the metric
    trigger: the first two answers to one question that disagree"""
OPEN_ROW_114_DECIDED = """
  OD-114:
    status: decided
    closed_by: DEC-026"""
OPEN_ROW_115 = """
  OD-115:
    status: open
    cost_to_reverse: low
    default_in_force: the raw message of the service reaches the user
    trigger: the first release a customer uses"""
OPEN_ROW_116 = """
  OD-116:
    status: open
    cost_to_reverse: low
    default_in_force: the loading notice is part of release 1.0
    trigger: the project lead reviewing the scope of release 1.0"""
OPEN_ROW_KI = """
  KI-013:
    status: open"""
OPEN_ROW_KI_014 = """
  KI-014:
    status: open"""

H_082 = """### OD-076 · Where the access token is kept

- **Question:** does the access token stay in the browser, or move to a component on the
  server?
- **The problem the default introduces:** a script running in the browser can read it.
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


def product_open(day: str, ki_014: bool = False) -> str:
    rows = OPEN_ROWS_BASE
    if day == "06":
        rows += OPEN_ROW_114_OPEN + OPEN_ROW_116
    else:
        rows += OPEN_ROW_114_DECIDED + OPEN_ROW_115 + OPEN_ROW_116 + OPEN_ROW_KI
        rows += OPEN_ROW_KI_014 if ki_014 else ""
    low = [H_109] + ([H_114] if day == "06" else [H_115]) + [H_116]
    known = "" if day == "06" else "\n" + KI_013 + ("\n" + KI_014 if ki_014 else "")
    closed = ("" if day == "06" else
              "\n- **2026-10-06 · OD-114** → [`DEC-026`](../../decisions/DEC-026-metric-"
              "resolution.md) · a fixed rule maps a question to a metric.\n")
    review = (f"last_review: {REVIEW}" if day == "06" else
              "last_review: 2026-10-06 17:45\nreview_scope: the whole register, after the "
              "decision on the metric rule and the two new entries")
    head = ("---\nschema: framework/open-register/v1\nartifact_type: open-register\n"
            "lifecycle: living\nstatus: active\nowners: [lead]\n"
            f"created: {REVIEW}\n{review}\nclassification: internal\nentries:{rows}\n---\n\n")
    return head + f"""\
# Open decisions and known issues: Atlas

# §1 · Open decisions

## Cost to reverse HIGH: changing it later means redoing work that already exists

{H_098}
## Cost to reverse MEDIUM: changing it later costs a migration, not a rewrite

{H_082}
## Cost to reverse LOW: changing it later costs an afternoon

{chr(10).join(low)}
# §2 · Accepted known issues
{known}
# §3 · Parking lot

# §4 · Closed decisions
{closed}"""


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


# THE STATE FILE, AS THE SKILL WOULD HAVE WRITTEN IT. The Italian is the digest's: every
# title and description here is printed as it stands.
ITEMS_BASE = """\
  OD-076:
    title: custodia del permesso di accesso lato server
    what: >-
      spostare la custodia del permesso dal browser a un componente lato server, per ridurre
      l'esposizione in caso di attacco al browser.
    theme: architettura
    scope: out
    seen: Where the access token is kept
  OD-098:
    title: tenere o sostituire lo strumento di caricamento dati
    what: >-
      se lo strumento che oggi carica i dati resta nell'architettura o viene sostituito da
      codice proprio. Tocca tutto il percorso dei dati, per questo va spezzata prima di poterla
      stimare meglio.
    theme: architettura
    scope: "1.0"
    size: XL
    seen: Keep or replace the data loading tool
  OD-109:
    title: risposta alle domande non coperte
    what: >-
      come si comporta il sistema davanti a una domanda a cui non sa rispondere con un numero
      garantito: rifiuta, avvisa o risponde comunque.
    theme: architettura
    scope: "1.0"
    size: M
    seen: How to answer a question no metric covers
  OD-114:
    title: come il sistema capisce quale indicatore gli viene chiesto
    what: >-
      la regola con cui una domanda in linguaggio naturale viene ricondotta a un indicatore
      definito, da cui dipende che il numero in risposta sia quello giusto.
    theme: architettura
    scope: "1.0"
    size: S
    seen: Which rule maps a question to a defined metric
  OD-116:
    title: se CHG-021, avviso di caricamento in corso, resta nel perimetro
    what: >-
      la scelta se l'avviso di caricamento in corso resta in questo rilascio o passa al
      successivo.
    theme: sviluppo
    scope: out
    seen: Whether the loading notice stays in release 1.0
  DEC-019:
    title: un archivio dati per cliente
    what: >-
      ogni cliente ha un archivio fisicamente separato, invece di un archivio unico filtrato
      per cliente.
    theme: architettura
    scope: "1.0"
    hours_before: 14
  CHG-012:
    title: repository unica
    what: >-
      il codice di più repository separate riunito in una sola, con una struttura che
      permette di estrarne un componente senza riscriverlo.
    theme: sviluppo
    scope: "1.0"
    hours_before: 12
  CHG-015:
    title: login con servizio esterno
    what: >-
      l'autenticazione degli utenti affidata a un servizio esterno specializzato, invece di
      gestire le password in proprio.
    theme: sviluppo
    scope: "1.0"
    hours_before: 8
  CHG-017:
    title: scambio del permesso di accesso al login
    what: >-
      dopo il login il sistema rilascia un proprio permesso che indica a quale cliente
      appartiene l'utente, ed è ciò che impedisce a un cliente di vedere i dati di un altro.
    theme: sviluppo
    scope: "1.0"
    size: M
    seen: Token exchange at login
  CHG-018:
    title: isolamento dei dati per cliente
    what: >-
      ogni cliente ha un archivio dati separato e il sistema apre solo quello indicato dal
      permesso di accesso dell'utente.
    theme: sviluppo
    scope: "1.0"
    size: L
    seen: Per-tenant data isolation
  CHG-019:
    title: flusso di rilascio
    what: >-
      la sequenza fissa di passi con cui una versione del codice arriva in un ambiente, senza
      interventi manuali che cambiano ogni volta.
    theme: infrastruttura
    scope: "1.0"
    size: S
    seen: Release pipeline
  CHG-021:
    title: avviso di caricamento in corso
    what: >-
      quando un caricamento dati è in corso la richiesta attende per un tempo limitato e poi
      avvisa l'utente di riprovare, invece di restituire dati incompleti.
    theme: sviluppo
    scope: "1.0"
    size: M
    seen: Loading-in-progress notice
  CHG-022:
    title: etichette di versione per il rilascio
    what: >-
      l'etichetta di versione che fa partire in automatico la costruzione e il rilascio in un
      ambiente.
    theme: infrastruttura
    scope: "1.0"
    size: S
    seen: Version tags trigger builds
  CHG-024:
    title: primo rilascio in preprod
    what: >-
      la prima installazione della nuova versione nell'ambiente di prova che replica la
      produzione, dove si verifica prima di rilasciare.
    theme: infrastruttura
    scope: "1.0"
    size: M
    seen: First release to preprod
  INC-040:
    title: servizio condiviso per i permessi di accesso
    what: >-
      un unico servizio che rilascia i permessi per tutti i prodotti, al posto del modulo
      interno a un solo prodotto.
    theme: sviluppo
    scope: out
    seen: A shared token service for every product
  INC-041:
    title: rilevamento delle anomalie
    what: >-
      segnalazione automatica dei valori che si discostano dall'andamento atteso.
    theme: sviluppo
    scope: out
    seen: Anomaly detection on customer metrics
  EVR-001:
    scope: out
"""
ITEMS_NEW = """\
  OD-115:
    title: formato dei messaggi di errore
    what: >-
      cosa vede l'utente quando una richiesta non va a buon fine, e quali dettagli tecnici
      restano solo nei log.
    theme: architettura
    scope: "1.0"
    size: S
    seen: What an error shows to the user
  KI-013:
    title: tempo massimo superato sulle domande lunghe
    what: >-
      le domande che richiedono molti passaggi di calcolo superano il tempo massimo e l'utente
      non riceve risposta.
    theme: sviluppo
    scope: "1.0"
    size: M
    seen: Long questions exceed the timeout
"""
WAITS = """\
waits:
  - what: Risposta sul registro delle immagini
    owner: team infrastruttura
    asked: 2026-10-01
    needed_by: 2026-10-07
    without: le versioni non si possono costruire e rilasciare in automatico.
    missing: manca la risposta sul registro delle immagini
    blocks: [CHG-022]
  - what: Ambiente preprod
    owner: team infrastruttura
    asked: 2026-09-25
    needed_by: 2026-10-09
    without: le modifiche non si possono verificare né chiudere.
    missing: manca preprod
    blocks: [CHG-024]
  - what: Domande di benchmark
    owner: team funzionale
    asked: 2026-09-22
    needed_by: 2026-10-10
    without: la qualità non si può valutare in modo oggettivo.
    note: blocca la valutazione al rilascio
  - what: Glossario delle metriche
    owner: team funzionale
    asked: 2026-09-22
    needed_by: 2026-10-10
    without: gli indicatori restano definiti a ipotesi e vanno rivisti dopo.
    slows: [OD-109]
"""
HEAD = """\
# Stato del digest di Atlas: ciò che la persona ha dichiarato, scritto dalla skill `digest`
# con le sue risposte. Ore, taglie, perimetro e attese non stanno negli artefatti.
product: atlas
standard_hours: 8
release:
  name: "1.0"
  delivery: 2026-10-13
items:
"""
REQUESTS = """\
requests:
  OD-116:
    to: responsabile di progetto
    by: 2026-10-09
    fallback: lo tolgo dal perimetro.
"""
PLAN = """\
plan:
  2026-10-07: [CHG-018, CHG-022]
  2026-10-08: [CHG-018, CHG-021]
"""
PERIODS = """\
periods:
  2026-10-06:
    hours:
      OD-114: 5
      CHG-017: 3
      CHG-019: 1.5
    outside:
      Riunioni di stato: 1
      Formazione di un junior: 0.5
"""


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


def build(root: Path, asks: bool) -> None:
    root.mkdir(parents=True)
    run("git", "init", "-q", "-b", "main", cwd=root)
    write(root, ".gitignore", "_meta/digest/\n.remote/\n")
    files = {"AGENTS.md": AGENTS, "OPEN.md": ROOT_OPEN, "products/atlas/product.yaml": PRODUCT,
             "products/atlas/PBR.md": PBR, "products/atlas/EVP.md": EVP,
             "products/atlas/LOG.md": LOG, "products/atlas/RMP.md": RMP,
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
    write(store, "state-atlas.yaml", HEAD + ITEMS_BASE + WAITS)
    r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "--product", "atlas",
                        "--baseline", "--date", "2026-10-06",
                        "--now", "2026-10-06T08:30:00+02:00"],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"the baseline was refused:\n{r.stdout}\n{r.stderr}")

    # 06/10, through the day.
    write(root, "decisions/DEC-026-metric-resolution.md", DEC_027)
    write(root, "products/atlas/OPEN.md", product_open("07", ki_014=asks).replace(
        "last_review: 2026-10-06 17:45\nreview_scope: the whole register, after the decision "
        "on the metric rule and the two new entries", f"last_review: {REVIEW}"))
    index(root)
    commit(root, "OD-114 decided by DEC-026: a fixed rule maps a question to a metric",
           "2026-10-06T11:00:00+02:00")
    for cid, when in (("CHG-017", "15:00"), ("CHG-019", "16:00")):
        write(root, f"products/atlas/changes/{cid}-{CHANGES[cid][0]}.md",
              change(cid, "verified"))
        commit(root, f"{cid} verified in the development environment",
               f"2026-10-06T{when}:00+02:00")
    # The register was edited after its last reading, so the reading is redone and attested
    # in a commit that touches the attestation block alone.
    write(root, "products/atlas/OPEN.md", product_open("07", ki_014=asks))
    top = root / "OPEN.md"
    top.write_text(top.read_text(encoding="utf-8").replace(
        f"last_review: {REVIEW}", "last_review: 2026-10-06 17:46\nreview_scope: the composed "
        "view of what is open, after the new entries of the product register", 1),
        encoding="utf-8")
    commit(root, "The open registers reread", "2026-10-06T17:50:00+02:00")
    index(root)
    if run("git", "status", "--porcelain", cwd=root):
        commit(root, "indices regenerated", "2026-10-06T17:55:00+02:00")

    state = HEAD + ITEMS_BASE + ITEMS_NEW + WAITS + REQUESTS
    if not asks:
        state += PLAN + PERIODS
    write(store, "state-atlas.yaml", state)


def main() -> int:
    dest = Path(sys.argv[1])
    shutil.rmtree(dest, ignore_errors=True)
    build(dest / "atlas", asks=False)
    build(dest / "atlas-asks", asks=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
