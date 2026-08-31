---
schema: framework/open-register/v1
artifact_type: open-register
lifecycle: living
status: active
products: [retail-forecast, store-ops]
owners: [g.quaglia]
created: 2026-03-02
last_review: 2026-07-30 11:20
classification: internal
# Derived from the entries below, so the two cannot disagree about anything a
# check reads. Where a heading and a cost contradict each other, that is the
# defect this fixture is built around and it is preserved.
entries:
  OD-002:
    status: open
    products: [all]
    cost_to_reverse: high
    default_in_force: none
  OD-005:
    status: open
    products: [all]
    cost_to_reverse: high
    default_in_force: a single Postgres instance one engineer set up for the pilot, which
    depends_on: [OD-008]
  OD-004:
    status: open
    products: [all]
    cost_to_reverse: high
    depends_on: [OD-007]
  OD-007:
    status: open
    products: [all]
    cost_to_reverse: high
    default_in_force: none
  OD-001:
    status: open
    products: [retail-forecast]
    cost_to_reverse: medium
    default_in_force: a CSV dropped on an SFTP server by hand every Monday by an analyst
  OD-008:
    status: open
    products: [all]
    cost_to_reverse: medium
    default_in_force: a crontab on the pilot VM, edited over SSH
  OD-003:
    status: open
    products: [retail-forecast]
    cost_to_reverse: medium
    default_in_force: whatever the first dbt model happened to do, which is grain first
  OD-006:
    status: open
    products: [store-ops]
    cost_to_reverse: low
    default_in_force: a Metabase trial one of us started
  OD-009:
    status: open
    products: [retail-forecast]
    cost_to_reverse: high
    default_in_force: none, because there is no retraining at all yet
    depends_on: [OD-011]
  KI-001:
    status: open
    products: [all]
    cost_to_reverse: low
---

# Open decisions and known issues

# §1 · Open decisions

## Cost to reverse HIGH: changing it later means redoing work that already exists

### OD-002 · One identity provider for both products, or one per product

- **Question:** do `retail-forecast` and `store-ops` authenticate against a single provider,
  or does each product keep its own?
- **The problem the default introduces:** the two teams are each about to wire their own
  login, and the first one that ships makes the choice for everybody.

### OD-005 · Where the curated layer lives

- **Question:** managed warehouse (BigQuery / Snowflake) or a lakehouse on the client's own
  object storage?
  currently holds both raw and curated tables in the same schema.
- **The problem the default introduces:** every model written against it now will have to be
  rewritten, and the client's DPO has not seen where the data sits.
- **Leaning:** managed warehouse, because nobody here wants to operate storage.
  while it sits on a pilot VM.

### OD-004 · One tenancy model for both products, or one each

- **Question:** is a store a tenant, is the chain a tenant, or is there no tenancy at all
  and everything is one installation per customer?
- **The problem the default introduces:** the pilot is single-customer, so the question
  never comes up, and it will come up on the day a second chain signs.

### OD-007 · One repository for both products or one repository each

- **Question:** monorepo with a shared package, or two repositories with a published
  internal library?
- **The problem the default introduces:** the shared forecasting utilities are currently
  copy-pasted between two branches of the same repository, and they have already diverged.

### OD-001 · How forecast output reaches the buyers' ordering system

- **Question:** a synchronous API the ordering system calls, or a nightly file export it
  picks up?
- **The problem the default introduces:** it works, and because it works nobody is
  measuring how late it is.

## Cost to reverse MEDIUM: changing it later costs a migration, not a rewrite

### OD-008 · Which orchestrator runs the weekly pipeline

- **Question:** Airflow on the client's Kubernetes, a managed scheduler, or keep cron?
- **The problem the default introduces:** nobody can tell whether last Sunday's run
  succeeded without logging into the box.

### OD-003 · Naming convention for the marts

- **Question:** do mart tables carry the business domain first or the grain first?
- **The problem the default introduces:** two more models a week get written against a
  convention nobody agreed.

## Cost to reverse LOW: changing it later costs an afternoon

### OD-006 · Which BI tool the store-ops digest is rendered in

- **Question:** Metabase, Superset, or a rendered HTML mail with no BI tool at all?

### OD-009 · Whether the override feedback loop retrains the model automatically

- **Question:** does a buyer override feed the next training run automatically, or does
  somebody approve the batch first?
- **The problem the default introduces:** the overrides are being written to a table nobody
  reads, and the longer that goes on the more the model looks accidentally wrong.

---

# §2 · Accepted known issues

### KI-001 · The pilot VM has no backup

- The Postgres instance holding the pilot data is not backed up.
- We accept it because the pilot data is regenerable from the client's exports.
- **Reopening trigger:** the first time a buyer's override is stored only there.
- **Reference:** none yet.

---

# §3 · Parking lot

- Should the digest be a Teams message instead of a mail.
- Somebody suggested we could sell the forecast to the supplier side too.

---

# §4 · Closed decisions

- **2026-03-10 · OD-010** → [`DEC-001`](decisions/DEC-001-python-stack.md) · the whole
  forecasting stack is Python.
