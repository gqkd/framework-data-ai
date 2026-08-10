#!/usr/bin/env python3
"""Build fixture repositories for evaluating the `audit` skill.

Recipe follows tests/selfcheck.py::_clean_repo, extended.
"""
import shutil
import sys
from pathlib import Path

BASE = Path(sys.argv[1])   # where to write; see evals/fixtures/make.py


def fm(**kw):
    return "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"


def write(root, files):
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# Fixture CLEAN: a small but non-trivial repository that should report nothing.
# Dates are recent so LC002 does not fire.

CLEAN = {
    "OPEN.md": fm(schema="framework/open-register/v1", artifact_type="open-register",
                  lifecycle="living", status="active", owners="[maria]",
                  products="[atlas]",
                  created="2026-01-01", last_review="2026-08-01 09:00")
    + """# Open decisions and known issues

# §1 · Open decisions

## Cost to reverse MEDIUM

### OD-004 · Which warehouse for the gold layer

- **Question:** Snowflake or BigQuery for the gold layer?
- **Cost to reverse:** medium.
- **Default in force:** BigQuery, because the landing zone is already there.
- **Deadline:** 2026-10-01.

# §4 · Decided, moved out

- OD-001 -> DEC-001
""",
    "GLOSSARY.md": fm(schema="framework/glossary/v1", artifact_type="glossary",
                      lifecycle="living", status="active", owners="[maria]",
                      products="[atlas]",
                      created="2026-01-01", last_review="2026-08-01 09:00")
    + "# Glossary\n\n**Active customer** - a customer with at least one order in 90 days.\n",
    "AGENTS.md": fm(schema="framework/agents-control-plane/v1",
                    artifact_type="agents-control-plane",
                    lifecycle="living", status="active", owners="[maria]",
                    created="2026-01-01", last_review="2026-08-01 09:00")
    + "# Control plane\n\nRead OPEN.md before any structural decision.\n",
    "decisions/DEC-001-warehouse.md": fm(
        schema="framework/decision-record/v1", artifact_type="decision-record",
        id="DEC-001", lifecycle="immutable", status="accepted", scope="architecture",
        products="[atlas]", owners="[maria]", derives_from="OD-001",
        created="2026-02-10")
    + "# DEC-001 - Landing zone on BigQuery\n\nWe land raw extracts in BigQuery.\n",
    "products/atlas/product.yaml": (
        "schema: framework/product-manifest/v1\n"
        "artifact_type: product-manifest\n"
        "lifecycle: living\n"
        "status: active\n"
        "products: [atlas]\n"
        "owners: [maria]\n"
        "created: 2026-01-01\n"
        "last_review: 2026-08-01 09:00\n"),
    "products/atlas/PBR.md": fm(
        schema="framework/product-brief/v1", artifact_type="product-brief",
        lifecycle="living", status="active", products="[atlas]", owners="[maria]",
        created="2026-01-01", last_review="2026-08-01 09:00")
    + "# Atlas - product brief\n\nAtlas answers: which customers are about to churn.\n",
    "products/atlas/ARC.md": fm(
        schema="framework/architecture/v1", artifact_type="architecture",
        lifecycle="living", status="active", products="[atlas]", owners="[maria]",
        verified_against="9f2ab41", created="2026-03-01",
        last_review="2026-08-01 09:00")
    + """# Atlas - architecture

<!-- section: current -->
## 1 - Current

Ingestion into BigQuery, dbt models, a scoring job.

<!-- section: target -->
## 2 - Target

Same, plus a feature store.

<!-- section: delta -->
## 3 - Delta

The feature store does not exist yet.
""",
    "products/atlas/changes/CHG-001-scoring.md": fm(
        schema="framework/change-contract/v1", artifact_type="change-contract",
        id="CHG-001", lifecycle="immutable", status="approved", products="[atlas]",
        owners="[maria]", derives_from="DEC-001", created="2026-04-01")
    + """# CHG-001 - Rewrite the scoring job

<!-- section: what-changes -->
## 1 - What changes

The scoring job moves from pandas to SQL.

<!-- section: what-must-not-change -->
## 2 - What must NOT change

The output table schema, and the daily 06:00 SLA.

<!-- section: how-we-know-it-worked -->
## 3 - How we know it worked

Row counts match for 7 consecutive days.
""",
}


# ─────────────────────────────────────────────────────────────────────────────
# Fixture DIRTY: the same shape, with planted defects.
#
#  1. FM001  dbt schema file with no front matter          (models/schema.yml)
#  2. FM001  CONTRIBUTING.md, prose that is not an artifact
#  3. FM002  PBR missing `owners`
#  4. FM002  DEC-002 declared `lifecycle: living` (must be immutable)
#  5. FM003  artifact_type: architecture-doc  (not in the registry)
#  6. LC002  GLOSSARY last_review 2024-01-05, far past stale_days
#  7. LC003  immutable EVD carrying last_review
#  8. REF001 CHG-002 derives_from DEC-999, which does not exist
#  9. REF003 DEC-001 superseded by DEC-003 but still `accepted`
# 10. SEC001 CHG-002 missing `what-must-not-change`
# 11. OD002  OD-004 still open, DEC-004 derives from it and is accepted
# 12. OD003  OD-005 high cost, no default in force
# 13. RLM002 release manifest with rollback.tested false
# 14. XP002  data contract consumer `orion` matches no product
#
# Plus a trap the validator CANNOT see: DEC-002 is an accepted immutable whose
# body was edited after acceptance (git history shows it). Nothing reports this.

DIRTY = {
    "framework.yaml": "checks:\n  LC002: warn\n",
    "CONTRIBUTING.md": "# Contributing\n\nOpen a PR against `main`. Run the tests.\n",

    # Hand-maintained, despite the names. Both are in `skip_files`, so the validator
    # never looks at them and the report gives no clue that they are not generated.
    "TRACEABILITY.md": """# Traceability, maintained by hand

Written by Maria in March 2026. The generator does not know about the supplier-side
lineage, so this file also records where each source system enters the chain.

| From | To | Note |
|---|---|---|
| SAP.KNA1 | DEC-001 | source of the customer master, contract with Finance |
| OD-001 | DEC-001 | |
| Salesforce.Account | DC-001 | the only field-level mapping we have |
""",
    "decisions/INDEX.md": """# Decision index

Hand maintained. The extra column is the reason it is hand maintained: it records why
each decision still matters, which no generator can produce.

| ID | Title | Why it still matters |
|---|---|---|
| DEC-001 | BigQuery landing | superseded by DEC-003, kept for the 2026 audit |
| DEC-002 | Hash PII on landing | the DPO signed off on this wording specifically |
""",
    "models/schema.yml": (
        "version: 2\n\nmodels:\n  - name: dim_customer\n    columns:\n"
        "      - name: customer_id\n        tests: [unique, not_null]\n"),
    "OPEN.md": fm(schema="framework/open-register/v1", artifact_type="open-register",
                  lifecycle="living", status="active", owners="[maria]",
                  products="[atlas]",
                  created="2026-01-01", last_review="2026-08-01 09:00")
    + """# Open decisions and known issues

# §1 · Open decisions

## Cost to reverse HIGH: decide before the first line of code

### OD-005 · Do we retain raw PII in the landing zone

- **Question:** retain raw PII for 30 days, or hash on landing?
- **Cost to reverse:** high.
- **Default in force:** none.
- **The problem the default introduces:** nobody knows what is in the bucket today.
- **Deadline:** 2026-09-01.

## Cost to reverse MEDIUM: decide within the first month

### OD-004 · Which warehouse for the gold layer

- **Question:** Snowflake or BigQuery for the gold layer?
- **Cost to reverse:** medium.
- **Default in force:** BigQuery, because the landing zone is already there.
- **Deadline:** 2026-10-01.

# §4 · Decided, moved out

- OD-001 -> DEC-001
""",
    "GLOSSARY.md": fm(schema="framework/glossary/v1", artifact_type="glossary",
                      lifecycle="living", status="active", owners="[maria]",
                      products="[atlas]",
                      created="2024-01-01", last_review="2024-01-05 09:00")
    + """# Glossary

**Active customer** - a customer with at least one order in 90 days.

**Churn** - no order in 180 days. NOTE: the scoring job uses 120 days, not 180.
""",
    "AGENTS.md": fm(schema="framework/agents-control-plane/v1",
                    artifact_type="agents-control-plane",
                    lifecycle="living", status="active", owners="[maria]",
                    created="2026-01-01", last_review="2026-08-01 09:00")
    + "# Control plane\n\nRead OPEN.md before any structural decision.\n",

    # 4. FM002: lifecycle living on a decision-record
    "decisions/DEC-002-pii.md": fm(
        schema="framework/decision-record/v1", artifact_type="decision-record",
        id="DEC-002", lifecycle="living", status="accepted", scope="platform",
        products="[atlas]", owners="[maria]", created="2026-02-20")
    + "# DEC-002 - Hash PII on landing\n\nWe hash email and phone at landing time.\n"
      "\n(Edited 2026-06-11: also applies to the CRM extract.)\n",

    # 9. REF003: DEC-001 superseded by DEC-003 but still accepted
    "decisions/DEC-001-warehouse.md": fm(
        schema="framework/decision-record/v1", artifact_type="decision-record",
        id="DEC-001", lifecycle="immutable", status="accepted", scope="architecture",
        products="[atlas]", owners="[maria]", derives_from="OD-001",
        created="2026-02-10")
    + "# DEC-001 - Landing zone on BigQuery\n\nWe land raw extracts in BigQuery.\n",
    "decisions/DEC-003-warehouse-snowflake.md": fm(
        schema="framework/decision-record/v1", artifact_type="decision-record",
        id="DEC-003", lifecycle="immutable", status="accepted", scope="architecture",
        products="[atlas]", owners="[maria]", supersedes="DEC-001",
        created="2026-05-02")
    + "# DEC-003 - Move the gold layer to Snowflake\n\nSupersedes DEC-001.\n",

    # 11. OD002: DEC-004 derives from OD-004, still listed open
    "decisions/DEC-004-gold-layer.md": fm(
        schema="framework/decision-record/v1", artifact_type="decision-record",
        id="DEC-004", lifecycle="immutable", status="accepted", scope="architecture",
        products="[atlas]", owners="[maria]", derives_from="OD-004",
        created="2026-06-01")
    + "# DEC-004 - Gold layer on BigQuery\n\nClosing OD-004.\n",

    "products/atlas/product.yaml": (
        "schema: framework/product-manifest/v1\n"
        "artifact_type: product-manifest\n"
        "lifecycle: living\n"
        "status: active\n"
        "products: [atlas]\n"
        "owners: [maria]\n"
        "created: 2026-01-01\n"
        "last_review: 2026-08-01 09:00\n"),

    # 3. FM002: PBR missing `owners`
    "products/atlas/PBR.md": fm(
        schema="framework/product-brief/v1", artifact_type="product-brief",
        lifecycle="living", status="active", products="[atlas]",
        created="2026-01-01", last_review="2026-08-01 09:00")
    + "# Atlas - product brief\n\nAtlas answers: which customers are about to churn.\n",

    # 5. FM003: unknown artifact_type
    "products/atlas/ARC.md": fm(
        schema="framework/architecture/v1", artifact_type="architecture-doc",
        lifecycle="living", status="active", products="[atlas]", owners="[maria]",
        verified_against="9f2ab41", created="2026-03-01",
        last_review="2026-08-01 09:00")
    + """# Atlas - architecture

<!-- section: current -->
## 1 - Current

Ingestion into BigQuery, dbt models, a scoring job.

<!-- section: target -->
## 2 - Target

Same, plus a feature store.

<!-- section: delta -->
## 3 - Delta

The feature store does not exist yet.
""",

    # 7. LC003: immutable with last_review
    "initiatives/churn/EVD-001.md": fm(
        schema="framework/evidence-brief/v1", artifact_type="evidence-brief",
        id="EVD-001", lifecycle="immutable", status="active", products="[atlas]",
        owners="[maria]", created="2026-01-20", last_review="2026-08-01 09:00")
    + "# EVD-001 - Churn costs 1.4M a year\n\nFrom the 2025 revenue extract.\n",

    # 8. REF001 + 10. SEC001
    "products/atlas/changes/CHG-002-features.md": fm(
        schema="framework/change-contract/v1", artifact_type="change-contract",
        id="CHG-002", lifecycle="immutable", status="approved", products="[atlas]",
        owners="[maria]", derives_from="DEC-999", created="2026-06-15")
    + """# CHG-002 - Add the feature store

<!-- section: what-changes -->
## 1 - What changes

Features move into a Feast store.

<!-- section: how-we-know-it-worked -->
## 3 - How we know it worked

Scoring latency stays under 200ms p95.
""",

    # 13. RLM002
    "products/atlas/releases/RLM-001.yaml": (
        "schema: framework/release-manifest/v1\n"
        "artifact_type: release-manifest\n"
        "id: RLM-001\n"
        "lifecycle: immutable\n"
        "status: active\n"
        "generated_by: release\n"
        "products: [atlas]\n"
        "created: 2026-06-20T10:00:00Z\n"
        "code:\n"
        "  commit: 9f2ab41\n"
        "rollback:\n"
        "  target: v1.3.2\n"
        "  tested: false\n"),

    # 14. XP002
    "products/atlas/contracts/DC-001-scores.md": fm(
        schema="framework/data-contract/v1", artifact_type="data-contract",
        id="DC-001", lifecycle="living", status="active", products="[atlas]",
        consumers="[atlas, orion]", owners="[maria]",
        created="2026-04-10", last_review="2026-08-01 09:00")
    + "# DC-001 - churn_scores\n\nOne row per customer per day.\n",
}


def main():
    if BASE.exists():
        shutil.rmtree(BASE)
    write(BASE / "clean-repo", CLEAN)
    write(BASE / "dirty-repo", DIRTY)
    print(f"wrote {BASE}")


if __name__ == "__main__":
    main()
