#!/usr/bin/env python3
"""Build a realistic, validator-clean framework repository for eval runs.

Usage: python make_fixture.py <dest-dir>
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


D = Path(sys.argv[1])
if D.exists():
    shutil.rmtree(D)

TODAY = "2026-08-07"
NOW = "2026-08-07 09:00"

def fm(**kw):
    def v(x):
        return x
    return "---\n" + "\n".join(f"{k}: {v(val)}" for k, val in kw.items()) + "\n---\n\n"

F = {}

F["AGENTS.md"] = fm(schema="framework/agents-control-plane/v1",
    artifact_type="agents-control-plane", lifecycle="living", status="active",
    owners="[gq]", created="2026-01-12", last_review=review(), classification="internal") + """\
# Instructions for agents

Read this file first. Then `OPEN.md`. Then the `product.yaml` of the product you are
working on.

## Authoritative sources

| Question | Source |
|---|---|
| How the system is built | `products/atlas/ARC.md#current` |
| What shape it is going to have | `products/atlas/ARC.md#target` |
| What is missing to get there | `products/atlas/ARC.md#delta`, ordered by `RMP.md` |
| Why it is built that way | `decisions/DEC-NNN.md` |
| What the product does and for whom | `products/atlas/PBR.md` |
| What a term or a metric means | `GLOSSARY.md` |
| What a piece of data guarantees | `products/atlas/contracts/DC-001-atlas-scores.md` |
| What was promised to a customer | `COMMITMENTS.md` |
| **What is NOT decided** | `OPEN.md` |
| What you are authorized to build right now | `products/atlas/changes/CHG-NNN.md` |

## Non negotiable rules

1. **Do not take decisions listed in `OPEN.md`.** Stop and ask.
2. **Do not implement a signal.** You implement a `CHG` with `status: approved`.
3. **Respect the artifact class.** immutable → new document with `supersedes`;
   append-only → add a linked event; living → edit and update `last_review`.
4. **If a fact is not documented, say so.**

## Mandatory updates

| What you touched | What to update |
|---|---|
| Architecture or dependencies | `ARC.md` **and** a new `DEC` |
| The schema or the meaning of a piece of data | the relevant `DC`, with a version bump |
| An AI component (model, prompt, retrieval) | a new `EVR` |
| A domain term or a metric | `GLOSSARY.md` |

## Real commands

```bash
python -m pytest tests/                 # the project's tests
python skills/audit/scripts/validate.py --root .
```
"""

F["products/atlas/OPEN.md"] = fm(schema="framework/open-register/v1", artifact_type="open-register",
    lifecycle="living", status="active", owners="[gq]", created="2026-01-12",
    last_review=review(), classification="internal") + """\
# Open decisions and known issues

## 1 · Open decisions

| ID | Question | Cost to reverse | Default in force | Owner |
|---|---|---|---|---|
| OD-004 | Do we keep scoring in the warehouse or move it to a service? | high | stay in the warehouse | gq |
| OD-007 | Which retention applies to per-account score history? | medium | 13 months | gq |
| OD-009 | Do EU customer records stay in the eu-west region only? | high | yes, eu-west only | legal |

## 2 · Known issues

| ID | Issue | Workaround |
|---|---|---|
| KI-002 | The nightly scoring job has no per-record retry; a bad row fails the batch | rerun by hand |

## 3 · Parking lot

- Someone floated a per-customer score threshold. Nothing decided.

## 4 · Closed

| ID | Closed by |
|---|---|
| OD-001 | DEC-001 |
"""

F["GLOSSARY.md"] = fm(schema="framework/glossary/v1", artifact_type="glossary",
    lifecycle="living", status="active", owners="[gq]", created="2026-01-12",
    last_review=review(), classification="internal") + """\
# Glossary

| Term | Definition | Does not include |
|---|---|---|
| **churn risk score** | probability in [0,1] that an account does not renew within 90 days, computed nightly by the atlas scorer | manual AE judgement |
| **active account** | an account with at least one product login in the last 30 days | trial accounts |
| **account tenure** | months since the contract start date | time spent in trial |
"""

F["COMMITMENTS.md"] = fm(schema="framework/commitments/v1", artifact_type="commitments",
    lifecycle="living", status="active", owners="[gq]", created="2026-01-12",
    last_review=review(), classification="internal",
    commitments="\n  CMT-001:\n    to: the customer named in the order form\n"
                "    status: open\n    feasibility: feasible\n    products: [atlas]\n"
                # The body carried three rows and the map one, which `REG015` reports:
                # `XP006`, `XP007` and `REF006` read the map, so the two undeclared
                # promises were invisible to every one of them.
                "  CMT-002:\n    to: all EU customers, in the Atlas DPA\n"
                "    status: open\n    feasibility: feasible\n    products: [atlas]\n"
                "  CMT-003:\n    to: Northwind, in the demo deck\n"
                "    status: stated-as-done\n    feasibility: feasible\n"
                "    products: [atlas]\n") + """\
# Commercial commitments made

| ID | Commitment | Where it was said | To whom | Technical constraint that follows |
|---|---|---|---|---|
| CMT-001 | Churn risk scores are refreshed **once per day**, available by 07:00 CET | Atlas order form §3, signed | Northwind, Cerulean | the nightly batch must finish by 06:30 |
| CMT-002 | Customer data of EU accounts is processed and stored in the EU | Atlas DPA §4 | all EU customers | eu-west only, see OD-009 |
| CMT-003 | The score and its top-3 drivers are shown for every scored account | Atlas demo deck, slide 9 | Northwind | the scorer must emit driver attributions |
"""

F["decisions/DEC-001-warehouse-scoring.md"] = fm(
    schema="framework/decision-record/v1", artifact_type="decision-record", leaves_open="[]",
    id="DEC-001", lifecycle="immutable", status="accepted", scope="architecture",
    products="[atlas]", owners="[gq]", created="2026-02-03",
    derives_from="[OD-001]", classification="internal") + """\
# DEC-001 · Scoring runs in the warehouse, nightly

**Context.** We need churn scores for ~40k accounts daily. A streaming service was the
alternative.

**Decision.** The scorer runs as a nightly dbt + Python job inside the warehouse. No
separate serving service.

**Consequences.** Freshness is bounded at 24h. A per-record retry does not exist: the
batch is the unit. Recorded as KI-002.
"""

F["decisions/DEC-002-single-scores-table.md"] = fm(
    schema="framework/decision-record/v1", artifact_type="decision-record", leaves_open="[]",
    id="DEC-002", lifecycle="immutable", status="accepted", scope="architecture",
    products="[atlas]", owners="[gq]", created="2026-03-11",
    classification="internal") + """\
# DEC-002 · One published table, `atlas_scores`, is the only external surface

**Decision.** Everything downstream reads `analytics.atlas_scores`. No consumer reads the
intermediate models. The contract is DC-001.

**Consequences.** A schema change to that table is a breaking change for every consumer
listed in DC-001.
"""

F["products/atlas/product.yaml"] = fm(schema="framework/product-manifest/v1",
    artifact_type="product-manifest", lifecycle="living", status="active",
    products="[atlas]", owners="[gq]", created="2026-01-12", last_review=review(),
    code="\n  backend:\n    url: git@github.com:org/atlas-backend.git\n    contains: the service and its models\n    release_relevant: 'true'",
    classification="internal") + """\
# Atlas · churn risk scoring for the CS team


name: atlas
one_liner: nightly churn risk scores and drivers for every active account
stage: F5
"""

F["products/atlas/PBR.md"] = fm(schema="framework/product-brief/v1",
    artifact_type="product-brief", lifecycle="living", status="active",
    products="[atlas]", owners="[gq]", created="2026-02-20", last_review=review(),
    classification="internal") + """\
# Atlas · product brief

**For whom.** The Customer Success team at Northwind and Cerulean, 12 CSMs.

**The problem.** CSMs find out an account is leaving when it gives notice. PRB-001.

**Outcome we are after.** A CSM opens the risk list each Monday and works the top 20
accounts before renewal. Success looks like: renewal rate on flagged accounts above the
unflagged baseline.

## Capabilities

| Capability | State |
|---|---|
| Nightly churn risk score per active account | live |
| Top-3 drivers per score | live |
| Risk list view, sortable, filterable by owner | live |
| Weekly digest email to each CSM | live |

## Explicitly out of scope

- Automated outreach. Atlas informs, it does not act.
- Scoring of trial and non-active accounts.
- Any real-time or intraday freshness. See CMT-001.

## Constraints

- EU account data stays in eu-west. CMT-002, OD-009.
- The score must remain explainable to a CSM without a data scientist present.
"""

F["products/atlas/ARC.md"] = fm(schema="framework/architecture/v1",
    artifact_type="architecture", lifecycle="living", status="active",
    products="[atlas]", owners="[gq]", created="2026-02-20", last_review=review(),
    verified_code="\n  product.backend: 9f2c1ab", classification="internal") + """\
# Atlas · architecture

<!-- section: current -->
## Current

| Component | What it does | Tech |
|---|---|---|
| `ingest` | pulls product events and CRM records nightly | Airbyte → warehouse |
| `dbt/atlas` | feature models, one row per account per day | dbt |
| `scorer` | trains weekly, scores nightly, emits score + top-3 drivers | Python job on a single VM |
| `analytics.atlas_scores` | the only published table. Contract: DC-001 | warehouse table |
| `atlas-web` | risk list view, reads `atlas_scores` directly | Next.js + read-only warehouse user |
| `digest` | Monday email, reads `atlas_scores` | scheduled Python |

No cache, no API layer, no queue. `atlas-web` queries the warehouse on page load.
Everything runs in eu-west.

<!-- section: target -->
## Target

Same shape, plus a supervised retraining pipeline with a held-out evaluation set so the
weekly retrain stops being a manual notebook run.

<!-- section: delta -->
## Delta

| Missing | Why it matters | RMP entry |
|---|---|---|
| Retraining pipeline with held-out eval | the weekly retrain is a manual notebook, unversioned | RMP-003 |
| Per-record retry on the scoring batch | KI-002, a single bad row fails the night | *(none)* |
"""

F["products/atlas/WF.md"] = fm(schema="framework/workflow/v1",
    artifact_type="workflow", lifecycle="living", status="active",
    products="[atlas]", owners="[gq]", created="2026-02-20", last_review=review(),
    classification="internal") + """\
# Atlas · workflow

<!-- section: current -->
## Current

Monday 08:00 the CSM opens the risk list, sorts by score, picks the top 20 in her book,
and logs a touchpoint in the CRM by hand. The digest email arrives at 07:30 with the same
list.

<!-- section: target -->
## Target

Unchanged for now. The Monday ritual is the workflow.

<!-- section: delta -->
## Delta

Nothing outstanding on the workflow axis.
"""

F["products/atlas/EVP.md"] = fm(schema="framework/evaluation-plan/v1",
    artifact_type="evaluation-plan", lifecycle="living", status="active",
    products="[atlas]", owners="[gq]", created="2026-03-01", last_review=review(),
    classification="internal") + """\
# Atlas · evaluation plan

| Metric | Threshold | Measured how |
|---|---|---|
| AUC on the held-out quarter | >= 0.72 | offline, `eval/holdout_q.py` |
| Precision @ top-20 per CSM book | >= 0.35 | offline |
| Driver agreement with the model | top-3 drivers reproduce >= 0.9 of SHAP order | offline |
| Score staleness at 07:00 CET | 0 days, i.e. yesterday's data present | production check |

Lowering any threshold requires a `DEC`.
"""

F["products/atlas/RSK.md"] = fm(schema="framework/risk-register/v1",
    artifact_type="risk-register", lifecycle="living", status="active",
    products="[atlas]", owners="[gq]", created="2026-03-01", last_review=review(),
    # §state described three risks and there was no map at all, so `REG004` reported
    # the register nothing can read and `XP005` the product whose promises no risk
    # owns -- on a fixture that carries the risk for the signed 07:00 commitment.
    risks="\n  RSK-001:\n    category: organisational\n    state: accepted\n"
          "    likelihood: M\n    impact: H\n"
          "  RSK-002:\n    category: technical\n    state: open\n"
          "    likelihood: M\n    impact: H\n    commitment: CMT-001\n"
          "  RSK-003:\n    category: compliance\n    state: open\n"
          "    likelihood: L\n    impact: H\n    commitment: CMT-002\n",
    classification="internal") + """\
# Atlas · risks

<!-- section: state -->
## State

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| RSK-001 | A CSM reads the score as a decision rather than a prompt | medium | high | the list is advisory, no automated action, stated in PBR |
| RSK-002 | The nightly batch misses 06:30 and the 07:00 commitment breaks | medium | high | alert on batch end time |
| RSK-003 | EU data leaves eu-west through a new dependency | low | severe | CMT-002, review any new component's region |

<!-- section: acceptances -->
## Acceptances

RSK-001 accepted by gq on 2026-03-01: Atlas is advisory by design.

<!-- section: events -->
## Events

| Date | Risk | What happened |
|---|---|---|
| 2026-06-14 | RSK-002 | batch finished 06:52, no breach, no alert fired |
"""

F["products/atlas/RMP.md"] = fm(schema="framework/roadmap/v1",
    artifact_type="roadmap", lifecycle="living", status="active",
    products="[atlas]", owners="[gq]", created="2026-03-01", last_review=review(),
    classification="internal") + """\
# Atlas · roadmap

| ID | Increment | Evidence it depends on | State |
|---|---|---|---|
| RMP-001 | Risk list filterable by CSM owner | DFB-001, CSM interviews | done |
| RMP-002 | Weekly digest email | SIG-003 | done |
| RMP-003 | Retraining pipeline with held-out eval | drift observed in SIG-011 | hypothesised |
| RMP-004 | Export of the risk list for offline work | SIG-014, asked twice | hypothesised |
"""

F["products/atlas/contracts/DC-001-atlas-scores.md"] = fm(
    schema="framework/data-contract/v1", artifact_type="data-contract",
    id="DC-001", lifecycle="living", status="active", version="3",
    products="[atlas]", consumers="[atlas, revops]", owners="[gq]",
    created="2026-03-11", last_review=review(), classification="internal") + """\
# DC-001 · `analytics.atlas_scores`

**Consumers.** `atlas-web`, `digest`, and the RevOps renewal forecast model, which joins
on `cust_id`. RevOps is a different team and does not read this repository.

## Schema

| Column | Type | Meaning |
|---|---|---|
| `cust_id` | int | account id, matches CRM `Account.Id_num` |
| `score_date` | date | the day the score describes |
| `risk_score` | float | churn risk score, see GLOSSARY |
| `driver_1`, `driver_2`, `driver_3` | string | top-3 drivers, ordered |

## Guarantees

- Freshness: yesterday's `score_date` present by 06:30 CET. CMT-001.
- Completeness: one row per active account, no gaps.
- Residency: eu-west only. CMT-002.
- Stability: a column rename or type change is breaking. Consumers get 30 days notice.
"""

F["products/atlas/LOG.md"] = fm(schema="framework/signal-log/v1",
    artifact_type="signal-log", lifecycle="append-only", status="active",
    products="[atlas]", owners="[gq]", created="2026-03-01",
    classification="internal") + """\
# Signal log: Atlas

## Signals

| ID | Date | Type | Observed | Impact | Who/Where | Linked |
|---|---|---|---|---|---|---|
| SIG-011 | 2026-05-02 | drift | AUC on the last quarter fell to 0.74 from 0.79 | medium | offline eval | RMP-003 |
| SIG-014 | 2026-06-02 | request | "Can I get this list into Excel? I work the book on a plane." | low | Northwind CSM | RMP-004 |
| SIG-018 | 2026-06-20 | feedback | Dashboard header reads "Churn Risc" | low | Cerulean CSM | |
| SIG-021 | 2026-06-28 | request | RevOps wants the account id as a string to match their new CRM export | medium | RevOps | |
| SIG-023 | 2026-07-02 | request | Sales asks whether we can advertise hourly refresh in the new deck | medium | Sales | |
| SIG-025 | 2026-07-09 | feedback | Scores "feel wrong" for accounts with under 3 months of history | medium | 3 CSMs | |
| SIG-027 | 2026-07-15 | compliance | Legal: EU accounts need a documented human-review path before any auto-flag | high | Legal | |
| SIG-029 | 2026-07-21 | metric | MOR review: 4 of 12 CSMs have never opened the risk list; the rest work the AE's list | high | MOR | |
| SIG-031 | 2026-07-24 | incident | Nightly batch failed on one malformed row, no scores that day | high | ops | KI-002 |
| SIG-033 | 2026-07-30 | feedback | Northwind's SMB self-serve book was acquired and churned out; the remaining book is enterprise, each with a named CSM who already knows their accounts | high | account team | |

## Analysis

### ANA-029 · on SIG-029

Interviews with 6 CSMs: the ones who do not open Atlas say the AE flags the same accounts
a week earlier from pipeline signals. Nobody has changed an outreach plan because of a
score.
"""

# The previous cycle's triage. Without one the fixture is a project that has never run a
# cycle, every signal reads as fresh, and the whole point of the triage state goes
# untested. This covers the log as it stood on 2026-07-05 and deliberately leaves the six
# July signals unrouted: those are the ones that carry the scenario.
#
# Two of the four routings are here to be exercised rather than to fill the table.
# `SIG-011` is `not-classifiable`, which counts as triaged and must still come back the
# moment a held-out measurement exists: an agent treating "appears in an ICG" as "dealt
# with" gets that one wrong. `SIG-023` is `not-a-candidate`, which is the value that stops
# a signal being re-read every cycle, and the check cannot tell it from an unread one if
# nobody writes it down.
F["products/atlas/cycles/ICG-006.md"] = fm(
    schema="framework/impact-classification/v1",
    artifact_type="impact-classification", lifecycle="immutable", status="accepted",
    id="ICG-006", products="[atlas]", owners="[gq]", created="2026-07-05",
    routing="\n  SIG-011: not-classifiable\n  SIG-014: product\n  SIG-018: none"
            "\n  SIG-023: not-a-candidate",
    impacts="\n  SIG-011: [ai]",
    classification="internal") + """\
# ICG-006 · Triage of cycle 6

`status`: `accepted`

Closed 2026-07-05. Four candidates, no change opened. Recorded here so the next cycle
starts from what is left rather than from the top of the log.

<!-- section: intake -->
## 1 · What was considered

- **From `LOG.md`:** `SIG-011`, `SIG-014`, `SIG-018` and `SIG-023`. `SIG-021` was on the
  log by then and was not reached: the cycle ran short and it stayed unrouted rather than
  being waved through, which is why it is still a candidate.
- **From `RMP.md`:** `RMP-003` and `RMP-004`, both `hypothesised`. Neither was opened.
- **From `ARC#delta`:** no new rows since cycle 5.
- **From the conversation:** nothing raised outside the documents.

<!-- section: classification -->
## 2 · Each candidate, and why

| Candidate | Routing | Impacts | Why, and against which document |
|---|---|---|---|
| `SIG-011` | `not-classifiable` | `ai` | AUC 0.79 to 0.74 over the last quarter. `EVP` measures on the same set the model is tuned against, so the number cannot separate drift from noise. `RMP-003` is the held-out eval that would make it answerable. Comes back the moment a held-out measurement exists. |
| `SIG-014` | `product` | | An export changes what a CSM can do: a row in `PBR` §capabilities and a leg on `WF#current`. No architecture, `atlas-web` already reads `atlas_scores` directly. Sits in `RMP-004`. |
| `SIG-018` | `none` | | Dashboard header reads "Churn Risc". A display string, no capability, no contract, no threshold. `GLOSSARY` defines the term and this is not the definition. Technical `CHG`, still unopened. |
| `SIG-023` | `not-a-candidate` | | Sales asking whether hourly refresh can go in the deck is not a proposal to build hourly refresh. It contradicts `CMT-001` (once per day by 07:00 CET, signed order form §3), `PBR` §out-of-scope and `DEC-001`. Escalated rather than routed: see §3. |

<!-- section: open-questions -->
## 3 · What is unresolved, and what it blocks

- **`SIG-023` is a conflict and it is still open.** Three accepted positions say once per
  day and Sales asked for hourly. The question put to the user was whether this is a
  request to reopen the freshness decision and supersede `DEC-001`, or a request that
  Sales stop saying it. No answer yet. If it comes back as "we want it", it is a decision
  and goes to `resolve`, not to a cycle.
- **`SIG-011` blocks itself through `RMP-003`.** The drift cannot be classified without the
  held-out eval, and the held-out eval is the increment the drift would justify. Somebody
  has to break the loop on the argument that an unmeasurable model is the problem, rather
  than on the size of a number nobody can trust.
- **Neither `RMP-003` nor `RMP-004` was opened.** Cycle 6 was short. Both stay
  `hypothesised` and both are candidates again next cycle.
"""

for rel, text in F.items():
    p = D / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)

print(f"fixture written to {D}")
