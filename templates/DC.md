---
schema: framework/data-contract/v1
artifact_type: data-contract
lifecycle: living
status: active
id: DC-NNN
version: 1.0.0
products: [product-a]
consumers: [product-b]
owners: [NAME]
created: YYYY-MM-DD
last_review: YYYY-MM-DD HH:MM
classification: internal
---

# DC-NNN · Data contract: name of the dataset or interface

**Question:** what can whoever consumes this data expect, and who answers if it breaks?

**Priority.** The contracts *between the three products* come before the ones facing
outward. They are contracts with yourself six months from now, and they are the ones you
will break silently.

## Schema

| Field | Type | Nullable | Key | PII | Semantics |
|---|---|---|---|---|---|
| | | | PK/FK | yes/no | link to `GLOSSARY` |

## Guarantees

| Guarantee | Value | How it is verified |
|---|---|---|
| Freshness | max N minutes/hours from the event | |
| Completeness | ≥ N% of expected rows | |
| Uniqueness | key unique 100% of the time | |
| Allowed values | enum per field | |

**This is the section the document exists for.** You can work the schema out from the
database in thirty seconds; the guarantees you cannot, they are the only information you
cannot get from anywhere else.

## Update frequency

## Known consumers

Who reads this data. If a product appears here, it must also appear in the complementarity
section of its `PBR`.

## Breaking change policy

- What we consider breaking: removing a field, changing a type, changing the semantics with
  the schema unchanged (the most insidious one, because no automated check detects it)
- Notice owed to consumers
- Length of the dual-write period
- How versioning works

## Version history

| Version | Date | Change | Breaking | `DEC` |
|---|---|---|---|---|

---

## Anti-patterns

- **A schema with no guarantees.** The document loses its only reason to exist.
- **Semantics not linked to the `GLOSSARY`.** This is how the same metric ends up computed
  two different ways in two products.
- **Changing the semantics and leaving the schema alone.** It is the breaking change that no
  automated check detects and that breaks consumers silently.
- **Consumers not listed.** You will not know who to warn, so you will warn nobody.
- **No `DC` between your own products** because "it is all mine". That is exactly the case
  where it is needed most.
