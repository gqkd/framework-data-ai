---
schema: framework/data-feasibility/v1
artifact_type: data-feasibility
lifecycle: immutable
status: active
id: DFB-NNN
products: [product-a]
owners: [NAME]
created: YYYY-MM-DD HH:MM
derives_from: [HYP-NNN]
classification: internal
---

# DFB-NNN · Data feasibility brief

**Question:** do the data we need exist, are they accessible, and are they good enough?

**Why it is the cheapest gate in the framework.** Two days here save months. It is the
document most data projects skip, and it is the reason most data projects slip.

**Note on the class:** immutable in its verdict. The inventory of sources *graduates* into
the `DC` artifacts of phase F4, so this document is not left to be maintained.

## Sources

| Source | System | Owner | Access | Freshness | Volume | History | PII |
|---|---|---|---|---|---|---|---|
| | | | how it is obtained | actual latency | rows/GB | since when | yes/no |

## Observed quality

**Observed, not declared.** Numbers obtained by querying the data, with the query or the
script attached.

| Source | Completeness | Duplicates | Null keys | Anomalies | Sample |
|---|---|---|---|---|---|
| | % | % | % | | n rows, period |

## Gaps

What is missing, what it would cost to have it, and who would have to produce it.

## Compliance

Legal basis for the processing · retention · transfers outside the EU · automated
decisions. Every entry generates a row in `RSK §state`.

## Verdict

`feasible` · `feasible with reservation` · `not feasible now`

With the reservation or the blocker expressed as an observable condition.
Cross-reference to the `DEC` of gate G3.

---

## Anti-patterns

- **Filling it in by reading the schema documentation.** The whole value lies in having
  looked at the data. If you have not run a query, you have not written a `DFB`.
- **Quality "good".** You need a percentage, not an adjective.
- **Freshness as declared by the data provider.** Measure it.
- **A "feasible" verdict with unquantified gaps.** A gap without an estimated cost is a
  deferred verdict, not a verdict.
- **Leaving out compliance because "it is internal data".** Internal data contains
  personal data of employees and customers.
