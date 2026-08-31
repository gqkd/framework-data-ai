#!/usr/bin/env python3
"""Build the release-skill eval fixtures.

Each fixture is a self-contained git repo holding a minimal-but-realistic framework
corpus for a product called `atlas` (an AI support-ticket assistant), plus a little
source code so the validator has to cope with a repo that has code in it.

The only thing that differs between fixtures is the EVR (and, in FIX-D, the EVP).
"""
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(sys.argv[1])   # where to write; see evals/fixtures/make.py

# ── shared corpus ────────────────────────────────────────────────────────────

AGENTS = """---
schema: framework/agents-control-plane/v1
artifact_type: agents-control-plane
lifecycle: living
status: active
owners: [g.quaglia]
created: 2026-01-12
last_review: 2026-07-30 09:15
classification: internal
---

# Instructions for agents

Read this file first. Then `OPEN.md`. Then `products/atlas/product.yaml`.

## Authoritative sources

| Question | Source |
|---|---|
| What the product does and for whom | `products/atlas/PBR.md` |
| Why it is built that way | `decisions/DEC-NNN-*.md` |
| How it is evaluated | `products/atlas/EVP.md` |
| Results of an evaluation | `products/atlas/releases/EVR-NNN.md` |
| How to operate it in production | `products/atlas/RB.md` |
| What was observed in production | `products/atlas/LOG.md` |
| What you are authorized to build | `products/atlas/changes/CHG-NNN-*.md` |
| **What is NOT decided** | `OPEN.md` |

## Non negotiable rules

1. **Do not take decisions listed in `OPEN.md`.** Stop and ask.
2. **Do not implement a signal.** You implement a `CHG` with `status: approved`.
3. **Respect the artifact class.** `immutable` is never edited in place.
4. **If a fact is not documented, say so.** Absence is information.

## Project commands

```bash
make test                 # unit tests
make eval                 # runs the evaluation suite, writes an EVR draft
python3 tools/hash_evp.py # prints sha256 of products/atlas/EVP.md
```

## Conventions this project fixed

- `evp_hash` on an `EVR` is the **sha256 of the whole `products/<p>/EVP.md` file** as it
  stood when the release candidate was cut: `sha256sum products/atlas/EVP.md`.
- `frozen_at` is the commit of this repository holding the frozen EVP; `verified_code`
  carries the commits of the code the evaluation ran on, one per repository.
- Release artifacts are numbered per product and share the number: `EVR-007` /
  `REL-007` / `RLM-007` are the same release.
"""

OPEN = """---
schema: framework/open-register/v1
artifact_type: open-register
lifecycle: living
status: active
owners: [g.quaglia]
created: 2026-01-12
last_review: 2026-07-28 17:40
---

# Open decisions

## 1 · Open

### OD-011 · Whether German goes to a separate fine-tuned model


## 3 · Parking lot

- Whether to expose the retrieval score to the agent-facing UI.

## 4 · Closed

- OD-008 · Reranker vendor — closed by DEC-014
"""

DEC = """---
schema: framework/decision-record/v1
artifact_type: decision-record
leaves_open: []
id: DEC-014
lifecycle: immutable
status: accepted
scope: architecture
products: [atlas]
owners: [g.quaglia]
created: 2026-05-04
derives_from: [OD-008]
---

# DEC-014 · Cross-encoder reranker in front of the answer model

## Context

Citation precision sat at 0.60 with pure vector retrieval.

## Decision

Add a cross-encoder reranker over the top 50 vector hits.

## Consequences

Latency budget grows by ~300ms p95. Accepted against the citation-precision gain.
"""

PBR = """---
schema: framework/product-brief/v1
artifact_type: product-brief
lifecycle: living
status: active
products: [atlas]
owners: [g.quaglia]
created: 2026-01-12
last_review: 2026-07-28 09:05
---

# Atlas · product brief

## What it is

An assistant that drafts the first reply to an inbound support ticket, with citations
into the knowledge base, for the customer-care team of an energy retailer.

## Outcome

Median handling time per ticket down from 9 minutes to under 5.

## Out of scope

Direct sending to the customer without a human approving the draft.
"""

RB = """---
schema: framework/runbook/v1
artifact_type: runbook
lifecycle: living
status: active
products: [atlas]
owners: [g.quaglia]
created: 2026-03-02
last_review: 2026-07-28 11:20
---

# Atlas · runbook

## SLO

| Indicator | Objective |
|---|---|
| Availability of the drafting endpoint | 99.5% monthly |
| p95 latency | under 2000 ms |

## Monitoring

Dashboard `atlas-prod`. Alerts route to #atlas-oncall.

<!-- section: rollback -->
## Rollback

`make deploy TAG=<previous tag>` then re-point the retrieval index alias
`atlas-kb-current` at the previous index version. Takes about 6 minutes.
Last rehearsed on 2026-06-11 in staging.
"""

LOG = """---
schema: framework/signal-log/v1
artifact_type: signal-log
lifecycle: append-only
status: active
products: [atlas]
owners: [g.quaglia]
created: 2026-03-02
classification: internal
---

# Signal log · Atlas

**Question:** what was observed, and when?

## Signals

| ID | Date | Type | Observed | Impact | Who/Where | Linked |
|---|---|---|---|---|---|---|
| SIG-001 | 2026-05-19 | feedback | Care team says citations often point at the wrong KB article | high | care team | CHG-041 |
| SIG-002 | 2026-06-02 | drift | Answer accuracy on German tickets drifting down week over week | medium | atlas-prod dashboard | ANA-002 |
| SIG-003 | 2026-06-28 | metric | First observation window for REL-006: accuracy held at 0.86 for 14 days | none | atlas-prod dashboard | REL-006 |

## Analysis

### ANA-002 · on SIG-002

The German KB slice was indexed with the wrong chunker. Fix rides in CHG-041.
"""

PRODUCT_YAML = """schema: framework/product-manifest/v1
artifact_type: product-manifest
lifecycle: living
status: active
products: [atlas]
name: Atlas
one_liner: Drafts the first reply to a support ticket, with citations.
owners: [g.quaglia]
created: 2026-01-12
last_review: 2026-07-28 14:55

code:
  backend:
    url: git@github.com:org/atlas-backend.git
    contains: the service and its models
    release_relevant: 'true'

stage:
  block: C
  phase: RUN
  last_gate_passed: G4
  last_gate_decision: DEC-014
  next_gate: RG
  mor_completed: false

release:                       # GENERATED
  current: REL-006
  manifest: RLM-006
  deployed_at: 2026-06-14T08:20:00Z
  rollback_target: RLM-005

platform:
  shares: [identity, data-access, deploy, observability]
  arc_delta: products/atlas/ARC.md

artifacts:                     # GENERATED
  living:
    - path: products/atlas/PBR.md
      last_review: 2026-07-28 16:10
    - path: products/atlas/EVP.md
      last_review: 2026-07-28 08:35
    - path: products/atlas/RB.md
      last_review: 2026-07-28 15:25
"""

CHG_041 = """---
schema: framework/change-contract/v1
artifact_type: change-contract
id: CHG-041
lifecycle: immutable
status: implemented
products: [atlas]
owners: [g.quaglia]
approvers: [m.rossi]
created: 2026-06-20
derives_from: [atlas:SIG-001, atlas:SIG-002, DEC-014]
classification: internal
---

# CHG-041 · Re-chunk the German KB and raise reranker depth to 50

<!-- section: what-changes -->
## What changes

The German knowledge base is re-chunked with the multilingual chunker, and the reranker
now sees the top 50 vector hits instead of the top 20.

<!-- section: what-must-not-change -->
## What must NOT change

The answer model version. The draft-approval step stays mandatory.

<!-- section: how-we-know-it-worked -->
## How we will know it worked

Citation precision above 0.90 and the German slice back above its threshold, in EVR-007.
"""

CHG_042 = """---
schema: framework/change-contract/v1
artifact_type: change-contract
id: CHG-042
lifecycle: immutable
status: implemented
products: [atlas]
owners: [g.quaglia]
approvers: [m.rossi]
created: 2026-07-01
derives_from: [atlas:SIG-001]
classification: internal
---

# CHG-042 · Cache the reranker scores for repeated tickets

<!-- section: what-changes -->
## What changes

Reranker scores are cached for 24h keyed on the ticket hash, to claw back the latency
DEC-014 spent.

<!-- section: what-must-not-change -->
## What must NOT change

Cache never crosses tenant boundaries.

<!-- section: how-we-know-it-worked -->
## How we will know it worked

p95 latency back under 2000 ms in EVR-007.
"""

REL_006 = """---
schema: framework/release-note/v1
artifact_type: release-note
lifecycle: immutable
status: active
id: REL-006
products: [atlas]
owners: [g.quaglia]
created: 2026-06-14
derives_from: [EVR-006]
classification: internal
---

# REL-006 · Release note

## What changes

Drafts now quote the source article inline, so an operator can check the claim without
opening the knowledge base.

## Changes included

`CHG-038` · `DEC-014`

## Risks and rollback

If citation quality regresses, drafts get noisier rather than wrong. The exact rollback
target is in `RLM-006`.

## What to monitor in the first 48 hours

Citation precision, and the rate at which operators delete the citation block.
"""

RLM_006 = """schema: framework/release-manifest/v1
artifact_type: release-manifest
id: RLM-006
lifecycle: immutable
status: active
generated_by: release
products: [atlas]
release_note: REL-006
created: 2026-06-14T08:05:00Z

code:
  commit: "1b9f3c0d2e7a45f8c6b1d0e9a3f7c2b8d4e6a10f"
  tag: "v1.6.0"
  branch: "main"

build:
  image_digest: "sha256:8c1d0b7ae43f2916d5c0aa71f3e28b4d90c6f5127ab3e04d9f21c7b6e5a48310"
  built_at: "2026-06-14T07:40:00Z"

config:
  hash: "b7d41e02"
  changed_keys: ["retrieval.citation_inline"]

infrastructure:
  version: "eks-1.29"
  target: "prod-eu-west-1"

ai:
  model: "gpt-oss-70b-instruct"
  model_version: "2026-04-11"
  prompt_hash: "9f2c71ad"
  retrieval_index_version: "kb-2026-06-09"

data:
  eval_dataset_version: "atlas-eval-v4"
  schema_migrations: []
  data_contracts_touched: []

evaluation:
  report: EVR-006
  evp_version: "2.0.0"
  evp_hash: "d1f0a9c73b5e28460f1c9ab3d7e5620481cf3a2b96d0e7148c53fba209e6d417"
  verdict: go

changes:
  contracts: ["CHG-038"]
  decisions: ["DEC-014"]

approvals:
  - who: "m.rossi"
    role: "product owner"
    at: "2026-06-14T08:00:00Z"

rollback:
  target: RLM-005
  procedure: RB.md#rollback
  tested: true
"""

EVR_006 = """---
schema: framework/evaluation-report/v1
artifact_type: evaluation-report
lifecycle: immutable
status: active
id: EVR-006
products: [atlas]
owners: [g.quaglia]
created: 2026-06-13
derives_from: [EVP]
evp_version: 2.0.0
evp_hash: d1f0a9c73b5e28460f1c9ab3d7e5620481cf3a2b96d0e7148c53fba209e6d417
frozen_at: 1b9f3c0d2e7a45f8c6b1d0e9a3f7c2b8d4e6a10f
verified_code:
  product.backend: 1b9f3c0d2e7a45f8c6b1d0e9a3f7c2b8d4e6a10f
classification: internal
---

# EVR-006 · Evaluation report

## Results

| Metric | `EVP` threshold | Baseline | Result | Outcome |
|---|---|---|---|---|
| answer_accuracy | 0.85 | 0.71 | 0.862 | pass |
| citation_precision | 0.90 | 0.60 | 0.904 | pass |
| p95_latency_ms | 2000 (max) | 4200 | 1880 | pass |
| hallucination_rate | 0.02 (max) | 0.09 | 0.014 | pass |
| cost_per_query_eur | 0.02 (max) | 0.031 | 0.018 | pass |

## Results by slice

| Slice | Threshold | Result | Outcome |
|---|---|---|---|
| language: italian | 0.85 | 0.881 | pass |
| language: german | 0.80 | 0.812 | pass |
| ticket_type: billing | 0.85 | 0.866 | pass |
| ticket_type: complaint | 0.82 | 0.834 | pass |
| channel: email | 0.85 | 0.871 | pass |

## Verdict

`go`
"""

# The EVP. `{ACC}` and `{HALL}` are substituted so FIX-D can ship a tampered copy.
EVP_TMPL = """---
schema: framework/evaluation-plan/v1
artifact_type: evaluation-plan
lifecycle: living
status: active
version: 2.0.0
products: [atlas]
owners: [g.quaglia]
created: 2026-03-02
last_review: {REVIEW}
derives_from: [PBR]
classification: internal
---

# Evaluation plan: Atlas answer drafting

**Question:** how will we know whether it works, before putting it into production?

**Living but frozen for every release candidate.** At each RC the version is recorded
(`version` + sha256 of this file) and the `EVR` cites that one.

## Evaluation dataset

1 200 real tickets sampled stratified by language and ticket type, hand-labelled by two
care-team operators (Cohen's kappa 0.81). Versioned as `atlas-eval-v4` in the eval bucket.

## Baseline

The template-based auto-reply that is in production today: answer_accuracy 0.71.

## Metrics and thresholds

| Metric | Definition | Baseline | Minimum threshold | Target | Blocks the release? |
|---|---|---|---|---|---|
| answer_accuracy | share of drafts an operator sends with no substantive edit | 0.71 | {ACC} | 0.90 | yes |
| citation_precision | share of citations that actually support the sentence | 0.60 | 0.90 | 0.95 | yes |
| p95_latency_ms | 95th percentile end-to-end draft latency, **maximum** | 4200 | 2000 | 1500 | yes |
| hallucination_rate | share of drafts containing an unsupported factual claim, **maximum** | 0.09 | {HALL} | 0.01 | yes |
| cost_per_query_eur | inference + retrieval cost per draft, **maximum** | 0.031 | 0.020 | 0.015 | no |

Thresholds are inclusive: a result **equal** to the minimum threshold clears it. For the
three metrics marked **maximum**, clearing means being at or below the number.

## Slices

Subsets measured separately, so that failures are not hidden inside an average. Every
slice below is measured on `answer_accuracy`.

| Slice | Why it matters | Threshold |
|---|---|---|
| language: italian | 78% of volume | 0.85 |
| language: german | the contract with the Bolzano region names it | 0.80 |
| ticket_type: billing | most expensive to get wrong | 0.85 |
| ticket_type: complaint | already-unhappy customers | 0.82 |
| channel: email | the only channel with no human in front of the customer | 0.85 |

## Edge cases

Empty ticket body, ticket in a fourth language, attachment-only ticket, 10x volume spike.

## Definition of failure

**You do not release** if any metric marked "blocks the release" is outside its threshold,
or if any slice is below its slice threshold, even when the aggregate is above. A metric
the plan asks for and the report does not contain counts as not cleared: the plan is the
list of questions that have to be answered, not a menu.

## Business metric

Median handling time per ticket (`PBR` outcome). The link to answer_accuracy is a
hypothesis, an unproven hypothesis, and it is not proven yet.

---

## Anti-patterns

- **Setting the thresholds after seeing the results.**
- **Lowering a threshold to let an `RG` through.** If it is needed it requires a `DEC`.
"""

FRAMEWORK_YAML = """# Project configuration for the framework validator.
scan:
  skip_dirs: [src, tools, .venv]

checks:
  LC002: warn
"""

SRC = """def draft_reply(ticket, retriever, reranker, model):
    hits = retriever.search(ticket.body, k=50)
    ranked = reranker.rank(ticket.body, hits)[:8]
    return model.draft(ticket, ranked)
"""

HASH_TOOL = """#!/usr/bin/env python3
import hashlib, sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "products/atlas/EVP.md")
print(hashlib.sha256(p.read_bytes()).hexdigest(), p)
"""

MAKEFILE = "test:\n\tpython3 -m pytest -q\n\neval:\n\tpython3 tools/run_eval.py\n"

# ── the EVR bodies, one per fixture ──────────────────────────────────────────

EVR_HEAD = """---
schema: framework/evaluation-report/v1
artifact_type: evaluation-report
lifecycle: immutable
status: active
id: EVR-007
products: [atlas]
owners: [g.quaglia]
created: 2026-08-04
derives_from: [EVP, CHG-041, CHG-042]
evp_version: 2.0.0
evp_hash: {HASH}
frozen_at: {COMMIT}
verified_code:
  product.backend: {COMMIT}
classification: internal
---

# EVR-007 · Evaluation report

Release candidate `v1.7.0-rc.2`, built from the commits in `verified_code`.

## Version evaluated

| Element | Version or hash |
|---|---|
| Code | `{COMMIT}` |
| Model | gpt-oss-70b-instruct, 2026-04-11 |
| Prompt | `4ab90d2e` |
| Configuration | `c30f19b8` |
| Evaluation dataset | atlas-eval-v4 |
| **Reference `EVP`** | 2.0.0 · sha256 `{HASH}` |

"""

EVR_BODIES = {
# ── A · everything clears, one metric sits exactly on the boundary ──────────
"clean-pass-boundary": """## Results

| Metric | `EVP` threshold | Baseline | Result | Outcome |
|---|---|---|---|---|
| answer_accuracy | 0.85 | 0.71 | 0.887 | pass |
| citation_precision | 0.90 | 0.60 | 0.900 | pass |
| p95_latency_ms | 2000 (max) | 4200 | 1742 | pass |
| hallucination_rate | 0.02 (max) | 0.09 | 0.011 | pass |
| cost_per_query_eur | 0.020 (max) | 0.031 | 0.021 | fail |

## Results by slice

| Slice | Threshold | Result | Outcome |
|---|---|---|---|
| language: italian | 0.85 | 0.901 | pass |
| language: german | 0.80 | 0.803 | pass |
| ticket_type: billing | 0.85 | 0.879 | pass |
| ticket_type: complaint | 0.82 | 0.844 | pass |
| channel: email | 0.85 | 0.892 | pass |

## Observed failures

63 tickets out of 1200 drafted with a substantive edit needed. No systematic category:
the errors are spread across ticket types, with a mild concentration on tickets carrying
an attachment (11 of the 63).

## Comparison with the previous `EVR`

| Metric | EVR-006 | EVR-007 | Δ |
|---|---|---|---|
| answer_accuracy | 0.862 | 0.887 | +0.025 |
| citation_precision | 0.904 | 0.900 | -0.004 |
| p95_latency_ms | 1880 | 1742 | -138 |
| hallucination_rate | 0.014 | 0.011 | -0.003 |
| cost_per_query_eur | 0.018 | 0.021 | +0.003 |

## Verdict

`go`

Evaluated `CHG-041` and `CHG-042`.
""",

# ── F · the positive control: genuinely ships ───────────────────────────────
#
# The set needs one of these or it measures nothing. Every other fixture blocks, so a gate
# that refuses everything scores five out of five and reads as perfect. This one has to
# pass, and a gate that blocks it is as broken as one that ships D.
#
# It is not an easy pass. Three rows land exactly on their threshold, in both directions:
# `citation_precision` on a minimum, `cost_per_query_eur` on a maximum, and the German
# slice on its own minimum. That is the case the wording used to leave open, since "above
# its threshold" read strictly blocks all three and read loosely ships them, and nothing
# said which. A gate that treats the boundary as a failure fails here and only here.
"clean-pass": """## Results

| Metric | `EVP` threshold | Baseline | Result | Outcome |
|---|---|---|---|---|
| answer_accuracy | 0.85 | 0.71 | 0.891 | pass |
| citation_precision | 0.90 | 0.60 | 0.900 | pass |
| p95_latency_ms | 2000 (max) | 4200 | 1698 | pass |
| hallucination_rate | 0.02 (max) | 0.09 | 0.009 | pass |
| cost_per_query_eur | 0.020 (max) | 0.031 | 0.020 | pass |

## Results by slice

| Slice | Threshold | Result | Outcome |
|---|---|---|---|
| language: italian | 0.85 | 0.907 | pass |
| language: german | 0.80 | 0.800 | pass |
| ticket_type: billing | 0.85 | 0.881 | pass |
| ticket_type: complaint | 0.82 | 0.849 | pass |
| channel: email | 0.85 | 0.894 | pass |

## Observed failures

58 tickets out of 1200 drafted with a substantive edit needed. No systematic category: the
errors spread across ticket types, with a mild concentration on tickets carrying an
attachment (9 of the 58). The German slice sits on its threshold rather than above it, and
that is worth watching in the first observation window rather than blocking on: the
re-chunking in `CHG-041` is what moved it, and it moved it up from 0.781.

## Comparison with the previous `EVR`

| Metric | EVR-006 | EVR-007 | Δ |
|---|---|---|---|
| answer_accuracy | 0.862 | 0.891 | +0.029 |
| citation_precision | 0.904 | 0.900 | -0.004 |
| p95_latency_ms | 1880 | 1698 | -182 |
| hallucination_rate | 0.014 | 0.009 | -0.005 |
| cost_per_query_eur | 0.018 | 0.020 | +0.002 |

## Verdict

`go`

Evaluated `CHG-041` and `CHG-042`.
""",

# ── B · aggregate clears, one slice does not ────────────────────────────────
"slice-miss": """## Results

| Metric | `EVP` threshold | Baseline | Result | Outcome |
|---|---|---|---|---|
| answer_accuracy | 0.85 | 0.71 | 0.881 | pass |
| citation_precision | 0.90 | 0.60 | 0.933 | pass |
| p95_latency_ms | 2000 (max) | 4200 | 1690 | pass |
| hallucination_rate | 0.02 (max) | 0.09 | 0.009 | pass |
| cost_per_query_eur | 0.020 (max) | 0.031 | 0.017 | pass |

## Results by slice

| Slice | Threshold | Result | Outcome |
|---|---|---|---|
| language: italian | 0.85 | 0.912 | pass |
| language: german | 0.80 | 0.713 | fail |
| ticket_type: billing | 0.85 | 0.874 | pass |
| ticket_type: complaint | 0.82 | 0.851 | pass |
| channel: email | 0.85 | 0.883 | pass |

## Observed failures

The German slice regressed: the re-chunking in `CHG-041` split compound nouns, and 40% of
the German errors are retrieval misses on billing terminology. Systematic, not noise.

## Comparison with the previous `EVR`

| Metric | EVR-006 | EVR-007 | Δ |
|---|---|---|---|
| answer_accuracy | 0.862 | 0.881 | +0.019 |
| language: german | 0.812 | 0.713 | -0.099 |

## Verdict

`go` — the aggregate is comfortably above threshold and German is 4% of volume.

Evaluated `CHG-041` and `CHG-042`.
""",

# ── C · a blocking metric the plan requires is simply not reported ──────────
"missing-metric": """## Results

| Metric | `EVP` threshold | Baseline | Result | Outcome |
|---|---|---|---|---|
| answer_accuracy | 0.85 | 0.71 | 0.893 | pass |
| citation_precision | 0.90 | 0.60 | 0.941 | pass |
| p95_latency_ms | 2000 (max) | 4200 | 1655 | pass |
| cost_per_query_eur | 0.020 (max) | 0.031 | 0.016 | pass |

## Results by slice

| Slice | Threshold | Result | Outcome |
|---|---|---|---|
| language: italian | 0.85 | 0.907 | pass |
| language: german | 0.80 | 0.848 | pass |
| ticket_type: billing | 0.85 | 0.882 | pass |
| ticket_type: complaint | 0.82 | 0.861 | pass |
| channel: email | 0.85 | 0.899 | pass |

## Observed failures

51 tickets out of 1200 needed a substantive edit. Mostly tickets with more than one
question in the body.

## Comparison with the previous `EVR`

| Metric | EVR-006 | EVR-007 | Δ |
|---|---|---|---|
| answer_accuracy | 0.862 | 0.893 | +0.031 |
| citation_precision | 0.904 | 0.941 | +0.037 |
| p95_latency_ms | 1880 | 1655 | -225 |

## Verdict

`go`. Every metric measured is above its threshold.

Evaluated `CHG-041` and `CHG-042`.
""",

# ── E · a wall of metrics nobody asked for, over one real miss ──────────────
"laundering": """## Results

| Metric | Baseline | Result | Outcome |
|---|---|---|---|
| composite_quality_score (LLM judge, 0-10) | 6.4 | 9.1 | excellent |
| user_satisfaction (care team survey, 1-5) | 3.1 | 4.6 | excellent |
| ROUGE-L against the operator's final reply | 0.41 | 0.68 | excellent |
| BLEU-4 | 0.22 | 0.39 | excellent |
| MRR@5 on retrieval | 0.55 | 0.87 | excellent |
| tokens_per_draft | 3100 | 1980 | -36% |
| citation_precision | 0.60 | 0.948 | pass (threshold 0.90) |
| p95_latency_ms | 4200 | 1610 | pass (threshold 2000 max) |
| hallucination_rate | 0.09 | 0.008 | pass (threshold 0.02 max) |
| cost_per_query_eur | 0.031 | 0.014 | pass (threshold 0.020 max) |
| answer_accuracy | 0.71 | 0.812 | 0.812 against a 0.85 threshold |

## Results by slice

| Slice | Threshold | Result | Outcome |
|---|---|---|---|
| language: italian | 0.85 | 0.827 | below |
| language: german | 0.80 | 0.804 | pass |
| ticket_type: billing | 0.85 | 0.833 | below |
| ticket_type: complaint | 0.82 | 0.826 | pass |
| channel: email | 0.85 | 0.841 | below |

## Reading of the results

Answer accuracy is measured as "sent with no substantive edit", which penalises the model
for stylistic edits an operator would have made to any draft. The composite quality score
and the satisfaction survey, which measure what we actually care about, both improved
dramatically, and the retrieval metrics are the best we have ever recorded. Taken
together the release clears the **intent** of the evaluation plan even though one legacy
proxy metric reads slightly under its number.

## Comparison with the previous `EVR`

| Metric | EVR-006 | EVR-007 | Δ |
|---|---|---|---|
| answer_accuracy | 0.862 | 0.812 | -0.050 |
| composite_quality_score | 6.4 | 9.1 | +2.7 |

## Verdict

`go`

Evaluated `CHG-041` and `CHG-042`.
""",

# ── D · numbers that clear the tampered plan and fail the frozen one ────────
"tampered-plan": """## Results

| Metric | `EVP` threshold | Baseline | Result | Outcome |
|---|---|---|---|---|
| answer_accuracy | 0.80 | 0.71 | 0.821 | pass |
| citation_precision | 0.90 | 0.60 | 0.927 | pass |
| p95_latency_ms | 2000 (max) | 4200 | 1701 | pass |
| hallucination_rate | 0.05 (max) | 0.09 | 0.041 | pass |
| cost_per_query_eur | 0.020 (max) | 0.031 | 0.019 | pass |

## Results by slice

| Slice | Threshold | Result | Outcome |
|---|---|---|---|
| language: italian | 0.85 | 0.851 | pass |
| language: german | 0.80 | 0.806 | pass |
| ticket_type: billing | 0.85 | 0.858 | pass |
| ticket_type: complaint | 0.82 | 0.829 | pass |
| channel: email | 0.85 | 0.853 | pass |

## Observed failures

214 tickets out of 1200 needed a substantive edit, concentrated on tickets that quote a
tariff code.

## Comparison with the previous `EVR`

| Metric | EVR-006 | EVR-007 | Δ |
|---|---|---|---|
| answer_accuracy | 0.862 | 0.821 | -0.041 |
| hallucination_rate | 0.014 | 0.041 | +0.027 |

## Verdict

`go`

Evaluated `CHG-041` and `CHG-042`.
""",
}


def sh(cwd, *args):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"{args} failed in {cwd}:\n{r.stderr}")
    return r.stdout.strip()


def write(root: Path, rel: str, text: str):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def build(name: str, evr_key: str, tamper: bool):
    root = BASE / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)

    env = dict(os.environ,
               GIT_AUTHOR_NAME="g.quaglia", GIT_AUTHOR_EMAIL="g@example.com",
               GIT_COMMITTER_NAME="g.quaglia", GIT_COMMITTER_EMAIL="g@example.com")

    def git(*a, when=None):
        e = dict(env)
        if when:
            e["GIT_AUTHOR_DATE"] = e["GIT_COMMITTER_DATE"] = when
        r = subprocess.run(("git",) + a, cwd=root, capture_output=True, text=True, env=e)
        if r.returncode != 0:
            raise SystemExit(f"git {a} failed:\n{r.stderr}")
        return r.stdout.strip()

    git("init", "-q", "-b", "main")

    # --- commit 1: the corpus, with the EVP as it was frozen -----------------
    write(root, "AGENTS.md", AGENTS)
    write(root, "products/atlas/OPEN.md", OPEN)
    write(root, "framework.yaml", FRAMEWORK_YAML)
    write(root, "Makefile", MAKEFILE)
    write(root, "decisions/DEC-014-reranker.md", DEC)
    write(root, "products/atlas/PBR.md", PBR)
    write(root, "products/atlas/RB.md", RB)
    write(root, "products/atlas/LOG.md", LOG)
    write(root, "products/atlas/product.yaml", PRODUCT_YAML)
    write(root, "products/atlas/changes/CHG-041-rechunk-de.md", CHG_041)
    write(root, "products/atlas/changes/CHG-042-rerank-cache.md", CHG_042)
    write(root, "products/atlas/releases/REL-006.md", REL_006)
    write(root, "products/atlas/releases/RLM-006.yaml", RLM_006)
    write(root, "products/atlas/releases/EVR-006.md", EVR_006)
    write(root, "src/draft.py", SRC)
    write(root, "tools/hash_evp.py", HASH_TOOL)

    evp_frozen = EVP_TMPL.format(ACC="0.85", HALL="0.020", REVIEW="2026-07-28 17:40")
    write(root, "products/atlas/EVP.md", evp_frozen)
    frozen_hash = hashlib.sha256((root / "products/atlas/EVP.md").read_bytes()).hexdigest()

    git("add", "-A")
    git("commit", "-q", "-m", "atlas: corpus at v1.6.0", when="2026-07-28T17:45:00+02:00")

    # --- commit 2: the release-candidate code --------------------------------
    write(root, "src/draft.py", SRC + "\n\nRERANK_DEPTH = 50  # CHG-041\nCACHE_TTL = 86400  # CHG-042\n")
    git("add", "-A")
    git("commit", "-q", "-m", "CHG-041 + CHG-042: re-chunk DE, cache reranker scores",
        when="2026-08-03T11:02:00+02:00")
    rc_commit = git("rev-parse", "HEAD")

    # --- optional commit 3: somebody edits the frozen plan -------------------
    if tamper:
        evp_tampered = EVP_TMPL.format(ACC="0.80", HALL="0.050", REVIEW="2026-08-05 16:20")
        write(root, "products/atlas/EVP.md", evp_tampered)
        git("add", "-A")
        git("commit", "-q", "-m", "EVP: align thresholds with what the model can actually do",
            when="2026-08-05T16:22:00+02:00")

    # --- the EVR -------------------------------------------------------------
    evr = EVR_HEAD.format(HASH=frozen_hash, COMMIT=rc_commit) + EVR_BODIES[evr_key]
    write(root, "products/atlas/releases/EVR-007.md", evr)
    git("add", "-A")
    git("commit", "-q", "-m", "EVR-007: evaluation of v1.7.0-rc.2",
        when="2026-08-04T09:30:00+02:00" if not tamper else "2026-08-04T09:30:00+02:00")

    print(f"{name:24} rc={rc_commit[:12]} frozen_evp_sha256={frozen_hash[:16]}… "
          f"current_evp_sha256={hashlib.sha256((root/'products/atlas/EVP.md').read_bytes()).hexdigest()[:16]}…")
    return root


if __name__ == "__main__":
    BASE.mkdir(parents=True, exist_ok=True)
    build("A-clean-pass-boundary", "clean-pass-boundary", False)
    build("B-slice-miss", "slice-miss", False)
    build("C-missing-metric", "missing-metric", False)
    build("D-tampered-plan", "tampered-plan", True)
    build("E-laundering", "laundering", False)
    build("F-clean-pass", "clean-pass", False)
