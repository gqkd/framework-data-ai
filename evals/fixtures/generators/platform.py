#!/usr/bin/env python3
"""Three products on one substrate, and a change that reaches all of them.

Usage: python platform.py <dest-dir>

WHAT THIS FIXTURE IS FOR. Every other repository here is one product, where a change
touches two or three files and "propose a diff and wait" is a diff somebody reads. The
rule the framework rests on is that autonomy is inversely proportional to the breadth of
the cascade, and nothing here has ever put a wide one in front of it. A proposal spanning
a dozen documents across three products is either something a person can act on or a wall
of text that gets approved unread, and approved-unread is worse than no proposal: it
launders an agent's confidence into a human decision.

THE CHANGE. Legal requires pseudonymisation of EU customer identifiers. `customer_id` is
an integer today, published by the shared contract that all three products read, and named
in a signed commitment. Making it opaque reaches, at least:

    DEC-002        contradicted, needs a platform-scope decision that supersedes it
    PLATFORM.md    #current, #target and #delta
    DC-001         schema, a version bump, and notice to three consumers
    atlas ARC      reads the column
    orion ARC      reads the column and joins on it
    vega ARC       renders it to end users
    GLOSSARY       what "cliente" identifies stops being a number
    COMMITMENTS    CMT-002 promises the id in a customer-facing export
    vega RSK       an accepted risk was accepted on the old identifier
    platform/OPEN.md  OD-002 asks this question and would close
    atlas LOG      the signal itself

Eleven documents, three of them owned by different products. The skill under test has to
propose that without either drowning the reader or quietly starting to write.

WHAT IT ALSO EXPOSES, AND ON PURPOSE. `data-contract` has one path in the registry,
`products/<p>/contracts/DC-NNN.md`. There is nowhere for a contract the *substrate*
publishes and three products consume, so this fixture puts the shared one under `atlas`,
which is what a real project is forced to do. That makes one product the owner of
something shared, and it is visible in the fixture rather than argued about here.
"""

import re
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

import sys
from pathlib import Path

D = Path(sys.argv[1])
NOW, TODAY = "2026-08-09 09:00", "2026-08-09"

# Read from the registry rather than written as a literal, for the reason `audit.py` states
# and this fixture has now demonstrated twice: a version frozen here became an `FW001` the
# day the framework moved, on the fixture whose baseline is zero warnings, and it would have
# done it again the day the version stopped being a single number.
REGISTRY = Path(__file__).resolve().parents[3] / "schemas" / "artifact-types.yaml"
VERSION = re.search(r"^version:\s*[\"']?([\d.]+)", REGISTRY.read_text(encoding="utf-8"), re.M).group(1)


def fm(**kw):
    return "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"


F = {}

F["framework.yaml"] = f"""\
framework_version: {VERSION}

scan:
  skip_dirs: [dbt, infra]
"""

F["AGENTS.md"] = fm(
    schema="framework/agents-control-plane/v1", artifact_type="agents-control-plane",
    lifecycle="living", status="active", owners="[g.quaglia]", created="2026-01-08",
    last_review=review(), classification="internal") + """\
# Instructions for agents

Read this, then `OPEN.md`, then the `product.yaml` of the product you are working on. This
repository holds three products on one substrate: read `PLATFORM.md` before anything that
crosses between them.

## Authoritative sources

| Question | Source |
|---|---|
| What the three products share | `PLATFORM.md` |
| How one product is built | `products/<p>/ARC.md#current` |
| What a piece of published data guarantees | the `DC` that publishes it |
| Why it is built that way | `decisions/DEC-NNN.md` |
| What a term means | `GLOSSARY.md` |
| What was promised to a customer | `COMMITMENTS.md` |
| **What is not decided** | `OPEN.md` |

## Non negotiable rules

1. **A change to the substrate is not a change to one product.** `PLATFORM.md` and every
   `ARC` that depends on it move together, or the repository describes a system that does
   not exist.
2. **Do not take decisions listed in `OPEN.md`.** Stop and ask.
3. **A `DC` with more than one consumer cannot be changed by one consumer.**
4. **A contradiction you find while answering a question goes in the parking lot of
   `OPEN.md`, one line, before you answer.** It is the one write that needs no permission,
   and it is the difference between a discovery and a remark.

## Real commands

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/audit/scripts/validate.py --root .
```
"""

F["PLATFORM.md"] = fm(
    schema="framework/platform-architecture/v1", artifact_type="platform-architecture",
    lifecycle="living", status="active", owners="[g.quaglia]", created="2026-01-20",
    last_review=review(), verified_code="\n  product.backend: 4c1f9ae", classification="internal") + """\
# Shared substrate

**Question:** what do the three products share, and who may change it?

## Current

| Component | What it is | Who depends on it |
|---|---|---|
| `warehouse` | one BigQuery project, `analytics` dataset | atlas, orion, vega |
| `identity` | the customer master, published as `analytics.customer` | atlas, orion, vega |
| `auth` | one OIDC tenant | vega only, today |

`customer_id` is a 64-bit integer, assigned by the CRM sync and carried unchanged through
every downstream table. Every product joins on it. `DEC-002` records why.

## Target

Unchanged, except that identity is expected to grow a pseudonymisation boundary for EU
subjects. Nothing is decided: see `OD-002`.

## Delta

| Missing | Blocked by |
|---|---|
| A pseudonymisation boundary in `identity` | `OD-002`, and a `DEC` that supersedes `DEC-002` |
| An owner for `analytics.customer` that is not a product team | `OD-003` |
"""

F["GLOSSARY.md"] = fm(
    schema="framework/glossary/v1", artifact_type="glossary", lifecycle="living",
    status="active", owners="[g.quaglia]", created="2026-01-08", last_review=review(),
    classification="internal") + """\
# Glossary

| Term | Definition | Does not include |
|---|---|---|
| **cliente** | a legal entity with a contract, identified by `customer_id`, an integer assigned by the CRM | prospects, and the branches of a customer, which share one `customer_id` |
| **cliente attivo** | a cliente with at least one login in the last 90 days | trial accounts |
| **soggetto EU** | a natural person whose data is processed under the DPA, which for us means every contact row attached to a cliente in the EU | the cliente itself, which is a legal entity |
"""

F["COMMITMENTS.md"] = fm(
    schema="framework/commitments/v1", artifact_type="commitments", lifecycle="living",
    status="active", owners="[g.quaglia]", created="2026-02-02", last_review=review(),
    classification="confidential",
    commitments="\n  CMT-001:\n    to: Northwind\n    status: open\n"
                "    feasibility: feasible\n    products: [atlas]\n"
                "  CMT-002:\n    to: Northwind, Cerulean\n    status: open\n"
                "    feasibility: feasible\n    products: [vega]\n"
                "  CMT-003:\n    to: every EU customer\n    status: open\n"
                "    feasibility: feasible-with-reservations\n"
                "    products: [atlas, vega, lyra]\n") + """\
# Commercial commitments made

| ID | Commitment | Where it was said | To whom | Technical constraint that follows |
|---|---|---|---|---|
| CMT-001 | Churn scores refreshed once per day, available by 07:00 CET | Atlas order form §3, signed | Northwind | the nightly batch finishes by 06:30 |
| CMT-002 | The customer export carries **the same customer id the customer sees in their own CRM** | Vega order form §5, signed 2026-04-11 | Northwind, Cerulean | `customer_id` in the export is the CRM integer, not an internal surrogate |
| CMT-003 | Personal data of EU subjects is processed in the EU and pseudonymised at rest | Group DPA §4, countersigned | all EU customers | the DPA names pseudonymisation; today only residency is implemented |
"""

# The registers, and the reason this fixture is where the arrangement shows. Both open
# entries here are about the substrate -- a shared identity, a shared table -- so they live
# in `platform/OPEN.md` and bind all three products without naming any of them. Each
# product keeps a register of its own for what is only its, and the root holds the parking
# lot and the region `--emit-index` fills with the union.
#
# `platform/` is beside `products/` and not inside it. Inside, the substrate would become a
# product: the list of products is the union of every `products:` field in the repository,
# so one `products: [platform]` earns it an `XP003` asking for a `PBR` and a `stage.phase`
# saying which phase of discovery a substrate is in. And `products:` absent on an entry
# means every product, which is what a substrate decision is.
F["OPEN.md"] = fm(
    schema="framework/open-register/v1", artifact_type="open-register", lifecycle="living",
    status="active", owners="[g.quaglia]", created="2026-01-08", last_review=review(),
    classification="internal") + """\
# Open decisions and known issues

# §3 · Parking lot

- Somebody suggested a per-product identity. Nothing decided.

# §5 · Everything open, by product

<!-- generated: open-union -->
Run `validate.py --emit-index` to fill this in.
<!-- /generated -->
"""

F["platform/OPEN.md"] = fm(
    schema="framework/open-register/v1", artifact_type="open-register", lifecycle="living",
    status="active", owners="[g.quaglia]", created="2026-01-08", last_review=review(),
    products="[atlas, orion, vega]",
    entries="\n  OD-002:\n    status: open\n    cost_to_reverse: high\n"
            "    default_in_force: customer_id is shown in the orion UI today\n"
            "  OD-003:\n    status: open\n    cost_to_reverse: medium\n"
            "    default_in_force: the atlas team maintains it, unasked",
    classification="internal") + """\
# Open decisions and known issues of the substrate

# §1 · Open decisions

## Cost to reverse HIGH: changing it later means redoing work that already exists

### OD-002 · How EU subjects are pseudonymised in the shared identity

- **Question:** does `customer_id` become opaque for everyone, or does a second
  pseudonymous key live beside it for EU subjects only?
- **Cost to reverse:** high. Every product joins on this column and one of them shows it
  to customers.
- **Default in force:** none. `CMT-003` is signed and the DPA names pseudonymisation,
  which today is not implemented.
- **Depends on:** nothing. It is the blocker, not the blocked.
- **Trigger:** the DPA audit.

### OD-003 · Who owns `analytics.customer`

- **Question:** the shared customer table sits under `products/atlas/contracts/` because
  the framework has nowhere else to put a contract, and atlas is one of its three
  consumers rather than its owner.
- **Cost to reverse:** medium.
- **Default in force:** atlas owns it by accident of where the file lives.

# §2 · Accepted known issues

### KI-001 · Vega renders `customer_id` in the UI

- Accepted 2026-05-02: it is the number customers recognise from their own CRM, which is
  the point of `CMT-002`.
- **Reopens if:** the identifier stops being the CRM integer.

# §4 · Closed decisions

- **2026-01-22 · OD-001** -> [`DEC-001`](../decisions/DEC-001-shared-warehouse.md) · one warehouse
"""

# One each, and the numbering continues from the substrate's rather than restarting: three
# registers that each began at OD-001 would make every `depends_on` naming one of them
# resolve to whichever file was read last. `REG007` reports the restart.
def _product_open(prod: str, num: str, title: str, body: str, cost: str, default: str):
    F[f"products/{prod}/OPEN.md"] = fm(
        schema="framework/open-register/v1", artifact_type="open-register",
        lifecycle="living", status="active", owners="[g.quaglia]", created="2026-01-08",
        last_review=review(), products=f"[{prod}]",
        entries=f"\n  {num}:\n    status: open\n    cost_to_reverse: {cost}\n"
                f"    default_in_force: {default}",
        classification="internal") + (
        f"# Open decisions and known issues · {prod}\n\n"
        f"# §1 · Open decisions\n\n### {num} · {title}\n\n{body}\n")


_product_open("atlas", "OD-004", "Whether the nightly batch moves to hourly",
              "- **Question:** `CMT-001` promises 07:00 CET. Hourly would make the promise "
              "cheap to keep and the warehouse bill three times larger.\n"
              "- **Default in force:** nightly, and it has met 07:00 every day this year.",
              "medium", "nightly, and it has met 07:00 every day this year")
_product_open("orion", "OD-005", "Which of the two dashboards is the product",
              "- **Question:** the operations view and the executive view were built for "
              "two buyers and only one is sold.\n"
              "- **Default in force:** both are maintained.",
              "low", "both are maintained")
_product_open("vega", "OD-006", "Whether the export is a file or an API",
              "- **Question:** customers pull a CSV today. Three have asked for an "
              "endpoint.\n"
              "- **Default in force:** the nightly CSV drop.",
              "medium", "the nightly CSV drop")

F["decisions/DEC-001-shared-warehouse.md"] = fm(
    schema="framework/decision-record/v1", artifact_type="decision-record", leaves_open="[]",
    id="DEC-001", lifecycle="immutable", status="accepted", scope="platform",
    products="[atlas, orion, vega]", owners="[g.quaglia]", created="2026-01-22",
    derives_from="[OD-001]", classification="internal") + """\
# DEC-001 · One warehouse for all three products

**Decision.** A single BigQuery project. No product gets its own.

**Consequences.** A schema change in the shared dataset is a change for three teams.
"""

F["decisions/DEC-002-customer-id-integer.md"] = fm(
    schema="framework/decision-record/v1", artifact_type="decision-record", leaves_open="[]",
    id="DEC-002", lifecycle="immutable", status="accepted", scope="platform",
    products="[atlas, orion, vega]", owners="[g.quaglia]", created="2026-02-14",
    classification="internal") + """\
# DEC-002 · `customer_id` is the CRM integer, carried unchanged

**Context.** The CRM assigns a 64-bit integer per legal entity. We considered minting our
own surrogate key at the warehouse boundary.

**Decision.** The CRM integer is the identifier, end to end. No surrogate, no mapping
table, no per-product key.

**Consequences.** Joins are cheap and every product means the same thing by "customer".
Customers recognise the number, which `CMT-002` then promised them in writing. And the
identifier is a business key we do not control: if it ever has to change shape, it changes
in the warehouse, in three architectures, in one signed commitment and in the UI at once.
There is no indirection to absorb it.
"""

# ── atlas · owns the shared contract by accident of path ─────────────────────

F["products/atlas/product.yaml"] = fm(
    schema="framework/product-manifest/v1", artifact_type="product-manifest",
    lifecycle="living", status="active", products="[atlas]", owners="[g.quaglia]",
    code="\n  backend:\n    url: git@github.com:org/atlas-backend.git\n    contains: the service and its models\n    release_relevant: 'true'",
    created="2026-01-08", last_review=review(), classification="internal") + """\

name: atlas
one_liner: churn risk scores for the CS team
stage: F6
"""

F["products/atlas/PBR.md"] = fm(
    schema="framework/product-brief/v1", artifact_type="product-brief", lifecycle="living",
    status="active", products="[atlas]", owners="[g.quaglia]", created="2026-02-01",
    last_review=review(), classification="internal") + """\
# Atlas · product brief

**For whom.** The CS team at Northwind and Cerulean.

**Outcome.** A CSM works the risk list before renewal.

## Capabilities

| Capability | State |
|---|---|
| Nightly churn score per cliente attivo | live |
| Top-3 drivers | live |
"""

F["products/atlas/ARC.md"] = fm(
    schema="framework/architecture/v1", artifact_type="architecture", lifecycle="living",
    status="active", products="[atlas]", owners="[g.quaglia]", created="2026-02-10",
    last_review=review(), verified_code="\n  product.backend: 4c1f9ae", classification="internal") + """\
# Atlas · architecture

<!-- section: current -->
## Current

| Component | Notes |
|---|---|
| `scorer` | nightly dbt + Python in the shared warehouse |
| `atlas_scores` | published table, keyed on `customer_id` (int64) |

Reads `analytics.customer` from the substrate. Joins on `customer_id`.

<!-- section: target -->
## Target

Unchanged.

<!-- section: delta -->
## Delta

| Missing | RMP entry |
|---|---|
| Held-out evaluation set | RMP-003 |
"""

F["products/atlas/contracts/DC-001-customer.md"] = fm(
    schema="framework/data-contract/v1", artifact_type="data-contract", lifecycle="living",
    status="active", products="[atlas]", owners="[g.quaglia]", created="2026-02-14",
    version="3", consumers="[atlas, orion, vega]", last_review=review(),
    classification="internal") + """\
# DC-001 · `analytics.customer`

**This contract is the substrate's, not atlas's.** It lives here because the framework has
one path for a data contract and it is under a product. See `OD-003`.

## Schema

| Column | Type | Meaning |
|---|---|---|
| `customer_id` | INT64 | the CRM identifier, per `DEC-002` |
| `legal_name` | STRING | |
| `country` | STRING | ISO-3166-1 alpha-2 |
| `is_eu_subject` | BOOL | derived from `country` |

## Guarantees

- **Stability:** a column rename or type change is breaking. Consumers get **30 days**
  notice. `customer_id` in particular is joined on by every consumer.
- **Freshness:** refreshed hourly from the CRM.

## Consumers

`atlas`, `orion`, `vega`. None of them is the owner.
"""

F["products/atlas/LOG.md"] = fm(
    schema="framework/signal-log/v1", artifact_type="signal-log", lifecycle="append-only",
    status="active", products="[atlas]", owners="[g.quaglia]", created="2026-03-01",
    classification="internal") + """\
# Signal log

## Signals

| ID | Date | Type | Observed | Impact | Who/Where |
|---|---|---|---|---|---|
| SIG-041 | 2026-08-06 | compliance | Legal: the DPA audit on 31/10 will check pseudonymisation of EU subjects, which `CMT-003` promises and nothing implements | high | Legal |
"""

# ── orion ────────────────────────────────────────────────────────────────────

F["products/orion/product.yaml"] = fm(
    schema="framework/product-manifest/v1", artifact_type="product-manifest",
    lifecycle="living", status="active", products="[orion]", owners="[m.rossi]",
    created="2026-03-04", last_review=review(), classification="internal") + """\

name: orion
one_liner: demand forecasting for the supply chain team
stage: F5
"""

F["products/orion/PBR.md"] = fm(
    schema="framework/product-brief/v1", artifact_type="product-brief", lifecycle="living",
    status="active", products="[orion]", owners="[m.rossi]", created="2026-03-04",
    last_review=review(), classification="internal") + """\
# Orion · product brief

**For whom.** The supply chain team at Northwind.

**Outcome.** A buyer sees next month's demand per cliente before placing orders.
"""

F["products/orion/ARC.md"] = fm(
    schema="framework/architecture/v1", artifact_type="architecture", lifecycle="living",
    status="active", products="[orion]", owners="[m.rossi]", created="2026-03-10",
    last_review=review(), verified_code="\n  product.backend: 4c1f9ae", classification="internal") + """\
# Orion · architecture

<!-- section: current -->
## Current

| Component | Notes |
|---|---|
| `forecaster` | weekly job in the shared warehouse |

Joins `analytics.customer` to the order history on `customer_id`. The join is the hot path:
the feature build is a single query over three years of orders.

<!-- section: target -->
## Target

Unchanged.

<!-- section: delta -->
## Delta

Nothing structural outstanding.
"""

# ── vega · the one that shows the identifier to customers ────────────────────

F["products/vega/product.yaml"] = fm(
    schema="framework/product-manifest/v1", artifact_type="product-manifest",
    lifecycle="living", status="active", products="[vega]", owners="[a.bianchi]",
    created="2026-04-02", last_review=review(), classification="internal") + """\

name: vega
one_liner: the customer-facing portal
stage: F6
"""

F["products/vega/PBR.md"] = fm(
    schema="framework/product-brief/v1", artifact_type="product-brief", lifecycle="living",
    status="active", products="[vega]", owners="[a.bianchi]", created="2026-04-02",
    last_review=review(), classification="internal") + """\
# Vega · product brief

**For whom.** The customer's own operations staff, outside our organisation.

**Outcome.** A customer reconciles our export against their CRM without asking us.

## Capabilities

| Capability | State |
|---|---|
| CSV export of their own records, keyed on the id they know | live |
| Usage dashboard | live |
"""

F["products/vega/ARC.md"] = fm(
    schema="framework/architecture/v1", artifact_type="architecture", lifecycle="living",
    status="active", products="[vega]", owners="[a.bianchi]", created="2026-04-08",
    last_review=review(), verified_code="\n  product.backend: 4c1f9ae", classification="internal") + """\
# Vega · architecture

<!-- section: current -->
## Current

| Component | Notes |
|---|---|
| `portal` | reads `analytics.customer` directly |
| `export` | writes the CSV the customer downloads, `customer_id` as the first column |

The identifier is rendered to end users, outside our organisation, and appears in files
customers have already downloaded and stored.

<!-- section: target -->
## Target

Unchanged.

<!-- section: delta -->
## Delta

Nothing structural outstanding.
"""

# The commitment that binds every product also creates exposure in every product, which is
# what `XP005` says: a promise made before the thing exists leaves a risk somebody owns and
# an entry in a register. `CMT-003` is the DPA, and it reaches atlas exactly as it reaches
# vega.
F["products/atlas/RSK.md"] = fm(
    schema="framework/risk-register/v1", artifact_type="risk-register", lifecycle="living",
    status="active", products="[atlas]", owners="[m.rossi]", created="2026-04-08",
    last_review=review(), classification="internal",
    risks="\n  RSK-002:\n    category: compliance\n    state: open\n"
          "    likelihood: M\n    impact: H\n    commitment: CMT-003\n"
          "  RSK-003:\n    category: technical\n    state: open\n"
          "    likelihood: M\n    impact: M\n    commitment: CMT-001\n"
          "  RSK-004:\n    category: commercial\n    state: open\n"
          "    likelihood: M\n    impact: M\n    commitment: none\n") + """\
# Atlas · risks

<!-- section: state -->
## State

| ID | Risk | Category | L | I | Mitigation |
|---|---|---|---|---|---|
| RSK-002 | `customer_id` is pseudonymised nowhere, and the DPA says it is | compliance | M | H | blocked on the substrate decision in `platform/OPEN.md` |
| RSK-003 | The nightly batch has no margin before 06:30 | technical | M | M | none yet: the scoring job has not been measured since the rewrite |
| RSK-004 | The second customer is assumed and has not been interviewed | commercial | M | M | nobody promised this to anybody: it is what the roadmap is built on |

<!-- section: acceptances -->
## Acceptances

Nothing accepted. Both are open, and the first is somebody else's to close.

<!-- section: events -->
## Events

| Date | `RSK` | Event | `SIG` | Consequence |
|---|---|---|---|---|
| | | | | |
"""

F["products/vega/RSK.md"] = fm(
    schema="framework/risk-register/v1", artifact_type="risk-register", lifecycle="living",
    status="active", products="[vega]", owners="[a.bianchi]", created="2026-04-08",
    last_review=review(), classification="internal",
    risks="\n  RSK-001:\n    category: compliance\n    state: accepted\n"
          "    likelihood: L\n    impact: M\n    commitment: CMT-002\n") + """\
# Vega · risks

<!-- section: state -->
## State

| ID | Risk | Category | L | I | Mitigation |
|---|---|---|---|---|---|
| RSK-001 | The export exposes an internal identifier | compliance | L | M | accepted: it is the customer's own CRM id, not ours. See acceptance below |

<!-- section: acceptances -->
## Acceptances

### RSK-001 accepted on 2026-04-20

Accepted because `customer_id` is the identifier the customer already holds, so exporting
it discloses nothing they do not have. **This acceptance depends on the identifier being
the CRM integer.** If it becomes an internal surrogate, the reasoning inverts: we would be
publishing an identifier of ours, and the acceptance has to be retaken.

<!-- section: events -->
## Events

None.
"""

for rel, text in F.items():
    p = D / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

print(f"platform fixture: {len(F)} files, 3 products, written to {D}")
