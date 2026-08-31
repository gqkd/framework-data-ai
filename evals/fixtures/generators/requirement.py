#!/usr/bin/env python3
"""Build a minimal-but-realistic framework repository to run the `requirement` skill against.

Recipe follows tests/selfcheck.py::_clean_repo, expanded so that every destination the
routing table can name actually exists in the fixture.
"""
import sys, shutil
from pathlib import Path
import itertools
from datetime import datetime, timedelta

# Every document here used to carry the same review instant, which is a claim that somebody
# read the whole set in one minute -- the exact shape `LC005` reports, planted by the
# generator in every fixture at once. Successive instants instead: a fixture that trips a
# check it did not mean to plant teaches you to read past its output.
_REVIEW_STEP = itertools.count()


def review() -> str:
    return (datetime(2026, 8, 1, 9, 0)
            + timedelta(minutes=17 * next(_REVIEW_STEP))).strftime("%Y-%m-%d %H:%M")


OUT = Path(sys.argv[1])
if OUT.exists():
    shutil.rmtree(OUT)

D = "2026-06-01"
T = "2026-06-01 09:00"


def fm(**kw):
    return "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"


FILES = {}

FILES["AGENTS.md"] = fm(
    schema="framework/agents-control-plane/v1", artifact_type="agents-control-plane",
    lifecycle="living", status="active", owners="[g.quaglia]", created=D,
    last_review=review(), classification="internal") + """# Instructions for agents

Read this file first. Then `OPEN.md`. Then the `product.yaml` of the product you are
working on.

## Authoritative sources

| Question | Source |
|---|---|
| How the system is built | `products/riconciliazione/ARC.md#current` |
| What shape it is going to have | `products/riconciliazione/ARC.md#target` |
| What is missing to get there | `products/riconciliazione/ARC.md#delta`, ordered by `RMP.md` |
| Why it is built that way | `decisions/DEC-NNN.md` |
| What the product does and for whom | `products/riconciliazione/PBR.md` |
| What a term or a metric means | `GLOSSARY.md` |
| What a piece of data guarantees | `products/riconciliazione/contracts/DC-001-vendite.md` |
| What was promised to a customer | `COMMITMENTS.md` |
| **What is NOT decided** | `OPEN.md` |
| What you are authorized to build right now | `products/riconciliazione/changes/CHG-NNN.md` |

## Non negotiable rules

1. **Do not take decisions listed in `OPEN.md`.**
2. **Do not implement a signal.**
3. **Respect the artifact class.** immutable -> supersede; append-only -> add an event;
   living -> edit and update `last_review`.
4. **If a fact is not documented, say so.**

## Mandatory updates

| What you touched | What to update |
|---|---|
| Architecture or dependencies | `ARC.md` **and** a new `DEC` |
| The meaning of a piece of data | the relevant `DC`, with a version bump |
| A domain term or a metric | `GLOSSARY.md` |
| A risk, or you introduced one | `RSK.md §state` |

## Commands

```bash
python3 skills/audit/scripts/validate.py --root .
```

## Sensitive data

Do not put real customer data in examples. PII fields are marked `pii: true` in the `DC`.

## Escalation, stop and ask

The decision is listed in `OPEN.md` - no approved `CHG` covers the work - the work would
require modifying an `immutable`.
"""

FILES["products/riconciliazione/OPEN.md"] = fm(
    schema="framework/open-register/v1", artifact_type="open-register",
    lifecycle="living", status="active", products="[riconciliazione]",
    owners="[g.quaglia]", created=D, last_review=review(),
    classification="internal") + """# Open decisions and known issues

# §1 · Open decisions

## Cost to reverse HIGH: changing it later means redoing work that already exists

### OD-001 · Which orchestrator runs the nightly pipeline

- **Question:** Airflow already in house, or the managed scheduler of the cloud provider?
- **The problem the default introduces:** no retry, no lineage, failures are silent.

## Cost to reverse MEDIUM: changing it later costs a migration, not a rewrite

### OD-002 · Tenancy model of the reconciliation product

- **Question:** one database per customer, or one shared database with a tenant column?
- **The problem the default introduces:** the second customer forces a migration.

# §2 · Accepted known issues

### KI-001 · The reconciliation report is recomputed from scratch every night

- Full recompute takes 40 minutes and grows linearly.
- We accept it because the window is 6 hours wide.
- **Reopening trigger:** the run exceeds 3 hours.
- **Reference:** none yet.

# §3 · Parking lot

- Consider splitting the reporting module out of the monolith.

# §4 · Closed decisions

- **2026-05-12 · OD-000** -> [`DEC-001`](decisions/DEC-001-postgres.md) · Postgres chosen
  as the primary datastore.
"""

FILES["GLOSSARY.md"] = fm(
    schema="framework/glossary/v1", artifact_type="glossary", lifecycle="living",
    status="active", products="[riconciliazione]", owners="[g.quaglia]", created=D,
    last_review=review(), classification="internal") + """# Glossary and metrics dictionary

## §Domain terms

### Cliente attivo

- **Definition:** an account that has performed at least one login in the last 90 days.
- **Does not include:** accounts created and never logged into; accounts of internal staff.
- **Banned synonyms:** "utente vivo", "customer in essere".
- **Used in:** riconciliazione (PBR, EVP).
- **Owner of the definition:** g.quaglia

### Riconciliazione

- **Definition:** the matching of a bank movement to one accounting entry.
- **Does not include:** partial matches spread over several entries.
- **Banned synonyms:** "quadratura".
- **Used in:** riconciliazione (PBR, WF).
- **Owner of the definition:** g.quaglia

## §Metrics

### Tempo medio di riconciliazione

- **Definition in words:** how long an operator takes to close one reconciliation.
- **Formula:** sum(closed_at - opened_at) / count(closed reconciliations)
- **Source:** `DC-001`
- **Time window:** calendar month.
- **Exclusions:** test accounts.
- **Do not confuse with:** the end to end pipeline duration.
- **Owner of the definition:** g.quaglia
- **Products that compute it:** riconciliazione
"""

FILES["COMMITMENTS.md"] = fm(
    schema="framework/commitments/v1", artifact_type="commitments", lifecycle="living",
    status="active", products="[riconciliazione]", owners="[g.quaglia]", created=D,
    last_review=review(), classification="confidential",
    commitments="\n  CMT-001:\n    to: Cliente Bianchi SpA\n    status: open\n"
                "    feasibility: feasible-with-reservations\n"
                "    products: [riconciliazione]\n") + """# Commercial commitments made

## Register

### CMT-001 · 30% reduction in reconciliation time

| Field | Content |
|---|---|
| **What was promised** | "riduzione del 30% del tempo di riconciliazione entro fine anno" |
| **To whom** | Cliente Bianchi SpA |
| **By whom and when** | Sales, 2026-04-18, in the commercial offer |
| **Products involved** | riconciliazione |
| **Implicit or explicit deadline** | end of 2026 |
| **Room for interpretation** | "tempo di riconciliazione" is the operator time, not the pipeline |
| **Technical translation** | median operator time from 12 to 8.4 minutes |
| **Feasibility** | feasible with reservations |
| **Architectural constraint that follows from it** | `OD-001` |
| **Status** | open |

## §Out of reach

None recorded.
"""

FILES["ING.md"] = fm(
    schema="framework/ingestion-register/v1", artifact_type="ingestion-register",
    lifecycle="append-only", status="active", products="[riconciliazione]",
    owners="[g.quaglia]", created=D,
    classification="confidential") + """# Business corpus ingestion log

<!-- section: claims -->
## §claims

| ID | Document | Position | Verbatim | Type | Destination | Outcome |
|---|---|---|---|---|---|---|
| ING-001 | offerta-bianchi.pptx | slide 4 | "riduzione del 30% del tempo di riconciliazione" | numeric target | `CMT-001` + `EVP` threshold | routed |

<!-- section: contradictions -->
## §contradictions

| ID | Claim A | Source A | Claim B | Source B | Nature | Where it went |
|---|---|---|---|---|---|---|

<!-- section: to-review -->
## §to review

| Document | Pages | Reviewed | What it contained |
|---|---|---|---|
| offerta-bianchi.pptx | 7 | yes | three box diagram, no new constraint |

## §tally

- Documents processed: 1
- Claims classified: 1
- Routed / rejected / deferred: 1 / 0 / 0
- **Contradictions found:** 0
- **Commitments that turned out to be out of reach:** 0
"""

FILES["decisions/DEC-001-postgres.md"] = fm(
    schema="framework/decision-record/v1", artifact_type="decision-record", leaves_open="[]",
    id="DEC-001", lifecycle="immutable", status="accepted", scope="architecture",
    products="[riconciliazione]", owners="[g.quaglia]", created="2026-05-12",
    derives_from="[OD-000]",
    classification="internal") + """# DEC-001 · Postgres as the primary datastore

## Context

The reconciliation product needs one transactional store for movements and entries.

## Decision

**Postgres 16 is the primary datastore.** Every persistent piece of state lives there.
No second operational database is introduced without a `DEC` that supersedes this one.

## Consequences

- One backup and restore procedure.
- Joins across movements and entries stay in SQL.
- Document shaped payloads are stored as `jsonb`, not in a second engine.
"""

FILES["products/riconciliazione/product.yaml"] = """schema: framework/product-manifest/v1
artifact_type: product-manifest
lifecycle: living
status: active
products: [riconciliazione]
name: Riconciliazione
one_liner: Matches bank movements to accounting entries for mid-size finance teams.
owners: [g.quaglia]
created: 2026-06-01
last_review: 2026-06-01 09:00
classification: internal
"""

FILES["products/riconciliazione/PBR.md"] = fm(
    schema="framework/product-brief/v1", artifact_type="product-brief",
    lifecycle="living", status="active", version="1.0.0",
    products="[riconciliazione]", owners="[g.quaglia]", created=D, last_review=review(),
    classification="internal") + """# Product brief: Riconciliazione

## One line

It matches bank movements to accounting entries so a finance team closes the month faster.

## Actors

- Operatore contabile: works the reconciliation queue.
- Responsabile amministrativo: signs off the month.

## Capabilities

| Capability | Outcome |
|---|---|
| Automatic matching on amount and date | fewer manual matches |
| Manual reconciliation queue | the residual gets closed |
| Monthly closing report | the month can be signed off |

## Out of scope

- Payment execution. We read movements, we never move money.
- Accounting bookkeeping itself. We write back a match, not an entry.

## Constraints

- The bank file format is imposed by the bank and we do not negotiate it.
"""

FILES["products/riconciliazione/ARC.md"] = fm(
    schema="framework/architecture/v1", artifact_type="architecture",
    lifecycle="living", status="draft", version="1.0.0",
    products="[riconciliazione]", owners="[g.quaglia]", created=D, last_review=review(),
    classification="internal") + """# Architecture: Riconciliazione

<!-- section: current -->
# §current

| Component | Technology | Responsibility |
|---|---|---|
| ingestion | Python job on a VM, cron | reads the bank file, loads it |
| store | Postgres 16 | movements, entries, matches |
| matcher | Python service | amount+date matching |
| ui | React SPA | the reconciliation queue |

All components run in the eu-west-1 region.

<!-- section: target -->
# §target

Same components, with the ingestion job moved under a real orchestrator once `OD-001` is
decided, and the matcher split from the API.

<!-- section: delta -->
# §delta

| Gap | Blocked by |
|---|---|
| no orchestrator | `OD-001` |
| matcher is not split | nothing, not prioritised |
"""

FILES["products/riconciliazione/WF.md"] = fm(
    schema="framework/workflow/v1", artifact_type="workflow", lifecycle="living",
    status="active", version="1.0.0", products="[riconciliazione]",
    owners="[g.quaglia]", created=D, last_review=review(),
    classification="internal") + """# Workflow: monthly reconciliation

<!-- section: current -->
# §current

## Steps

1. The bank drops the movements file **once a night, in a batch that lands at 02:00**.
2. The cron job loads it into Postgres between 02:10 and 02:40.
3. The matcher runs and produces automatic matches.
4. From 09:00 the operator works the residual queue by hand.
5. At month end the responsabile signs the closing report.

The data an operator sees during the day is therefore **at most 24 hours old**, and never
fresher than the 02:00 batch.

<!-- section: target -->
# §target

Same steps, with step 4 shortened by better automatic matching.

<!-- section: delta -->
# §delta

| Gap | Note |
|---|---|
| automatic match rate is 61%, target 80% | matcher rules are naive |
"""

FILES["products/riconciliazione/EVP.md"] = fm(
    schema="framework/evaluation-plan/v1", artifact_type="evaluation-plan",
    lifecycle="living", status="active", version="1.0.0",
    products="[riconciliazione]", owners="[g.quaglia]", created=D, last_review=review(),
    classification="internal") + """# Evaluation plan: matcher

## Evaluation dataset

2 400 hand labelled movement/entry pairs from three closed months, versioned in `evals/`.

## Thresholds

| Metric | Threshold | Why this value |
|---|---|---|
| automatic match precision | >= 0.98 | a wrong match costs an accounting correction |
| automatic match rate | >= 0.80 | below this the operator time promise does not hold |
| median operator time | <= 8.4 min | it is what `CMT-001` translates to |

## Gate

An RC that does not clear every threshold does not ship.
"""

FILES["products/riconciliazione/RSK.md"] = fm(
    schema="framework/risk-register/v1", artifact_type="risk-register",
    lifecycle="living", status="active", version="1.0.0",
    products="[riconciliazione]", owners="[g.quaglia]", created=D, last_review=review(),
    classification="confidential",
    risks="\n  RSK-001:\n    category: data\n    state: open\n"
          "    likelihood: M\n    impact: H\n"
          "  RSK-002:\n    category: technical\n    state: accepted\n"
          "    likelihood: H\n    impact: M\n") + """# Risk and compliance register: Riconciliazione

<!-- section: state -->
# §state

| ID | Risk | Category | Likelihood | Impact | State | Mitigation | Owner | Reviewed |
|---|---|---|---|---|---|---|---|---|
| RSK-001 | The bank changes the file layout without notice | data | M | H | open | schema check on load, load fails loudly | g.quaglia | 2026-06-01 |
| RSK-002 | The nightly cron fails silently and nobody notices | technical | H | M | open | none yet, depends on `OD-001` | g.quaglia | 2026-06-01 |

## Compliance

| Processing | Legal basis | Retention | Non-EU | Automated decision | `DC` |
|---|---|---|---|---|---|
| bank movements of the customer | contract | 10 years | no | no | `DC-001` |

<!-- section: acceptances -->
# §acceptances

### RSK-002 accepted on 2026-05-20

Accepted by g.quaglia because the closing window is wide enough to catch a failure by
hand. Lapses when the product has more than one customer.

<!-- section: events -->
# §events

| Date | `RSK` | Event | `SIG` | Consequence |
|---|---|---|---|---|
"""

FILES["products/riconciliazione/LOG.md"] = fm(
    schema="framework/signal-log/v1", artifact_type="signal-log",
    lifecycle="append-only", status="active", products="[riconciliazione]",
    owners="[g.quaglia]", created=D, classification="internal") + """# Signal log: Riconciliazione

## Signals

| ID | Date | Type | Observed | Impact | Who/Where | Linked |
|---|---|---|---|---|---|---|
| SIG-001 | 2026-05-22 | feedback | The queue sorting is not obvious | low | Bianchi, call | |

## Analysis

## Verbatim feedback

### SIG-001

> "non si capisce con che criterio e' ordinata la coda"
"""

FILES["products/riconciliazione/RMP.md"] = fm(
    schema="framework/roadmap/v1", artifact_type="roadmap", lifecycle="living",
    status="active", version="1.0.0", products="[riconciliazione]",
    owners="[g.quaglia]", created=D, last_review=review(),
    classification="internal") + """# Progressive implementation roadmap: Riconciliazione

## Increments

| Increment | State | Depends on |
|---|---|---|
| better matching rules | `committed` | nothing |
| orchestrated ingestion | `hypothesised` | `OD-001` |
"""

FILES["products/riconciliazione/contracts/DC-001-vendite.md"] = fm(
    schema="framework/data-contract/v1", artifact_type="data-contract",
    lifecycle="living", status="active", id="DC-001", version="1.0.0",
    products="[riconciliazione]", owners="[g.quaglia]", created=D, last_review=review(),
    classification="internal") + """# DC-001 · Data contract: bank movements

## Schema

| Field | Type | Nullable | Key | PII | Semantics |
|---|---|---|---|---|---|
| movement_id | string | no | PK | no | identifier given by the bank |
| value_date | date | no | | no | date the bank settles the movement |
| amount | decimal(12,2) | no | | no | signed, in euro |
| counterparty | string | yes | | yes | free text from the bank |
| cliente_id | string | no | FK | no | see `GLOSSARY` "Cliente attivo" |

## Guarantees

- **Freshness:** the dataset is complete up to D-1 and available **by 06:00 every day**.
  There is no intraday delivery.
- **Completeness:** every movement settled on D-1 is present.
- **Residency:** the data is stored in eu-west-1 and never leaves it.
- **Breaking change notice:** 30 days to consumers.

## Consumers

- the matcher service
"""


for rel, text in FILES.items():
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

print(f"wrote {len(FILES)} files to {OUT}")
