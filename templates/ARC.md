---
schema: framework/architecture/v1
artifact_type: architecture
lifecycle: living
status: active
version: 1.0.0
products: [product-a]
owners: [NAME]
created: YYYY-MM-DD
last_review: YYYY-MM-DD HH:MM
verified_against: COMMIT_HASH
classification: internal
---

# Architecture: product name

**Question:** how is the system built right now?

**It starts living at F5**, with the first line of code, not at go-live: design and
implementation diverge long before that. The `verified_against` field records the commit
this document was last verified against.

**Structure when there is more than one product:** this file holds the **delta** against
`PLATFORM.md`.
What is shared is documented once, there.

## Components

| Component | Responsibility (one line) | Shared or specific | `DEC` |
|---|---|---|---|

## End-to-end data flow

A diagram. It is the part most often missing and the one that is needed most: if a new
person cannot draw the system on a whiteboard after reading this document, what is usually
missing is the data flow.

## Data states

Where it lives and in what form: raw, curated, serving. With pointers to the `DC`.

## Boundaries

What is ours, what is third party, what belongs to the other two products. Every boundary
towards another product must correspond to a `DC`.

## Environments

| Environment | Purpose | Relevant differences from production |
|---|---|---|

The differences are the useful part: they are where the bugs that do not reproduce come
from.

## Decisions that explain this architecture

List of the relevant `DEC`. Links only: **how it is** here, **why** in the `DEC`.

---

## Anti-patterns

- **Becoming the sum of all the `DEC`.** If `ARC` starts explaining the rationale, it is
  duplicating, and it will soon diverge from the `DEC`.
- **Describing the system as designed instead of the one that was built.** This one is
  living: if it does not match the code, it is harmful, not incomplete.
- **No data flow.** See above.
- **Duplicating `PLATFORM.md`.** If a section is identical in every `ARC`, it does not
  belong in the `ARC`.
- **`verified_against` never updated.** It is the only way to know how far you can trust
  this.
