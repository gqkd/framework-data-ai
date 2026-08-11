---
schema: framework/evaluation-plan/v1
artifact_type: evaluation-plan
lifecycle: living
status: active
version: 1.0.0
products: [product-a]
owners: [NAME]
created: YYYY-MM-DD HH:MM
last_review: YYYY-MM-DD HH:MM
derives_from: [HYP-NNN, PBR]
classification: internal
---

# Evaluation plan: component name

**Question:** how will we know whether it works, before putting it into production?

**Living but frozen for every release candidate.** At each RC the version is recorded
(`version` + file hash) and the `EVR` cites that one. The freeze is what stops the
thresholds being touched up after the results have been seen, which is how an evaluation
plan turns into a ritual.

## Evaluation dataset

- How it is built, with what selection criterion
- Size
- Who labeled it, and with what level of agreement if more than one person did
- Where it is versioned
- How it is updated, and with what caution: widening the dataset changes the historical numbers

## Baseline

What we compare against: a trivial rule, the current process, a human operator.
**Mandatory field.** Without a baseline you are not evaluating, you are describing: "85%
accuracy" means nothing until you know the trivial rule scores 83%.

## Metrics and thresholds

| Metric | Definition | Baseline | Minimum threshold | Target | Blocks the release? |
|---|---|---|---|---|---|
| | link to `GLOSSARY` | | number | number | yes/no |

Numeric thresholds. "Good" is not a threshold.

## Slices

Subsets measured separately, so that failures are not hidden inside an average.
The threshold may differ for each one, and it must be stated.

| Slice | Why it matters | Threshold |
|---|---|---|

## Edge cases

Expected behavior under out-of-distribution conditions: empty input, unexpected
language, anomalous volume, missing data.

## Definition of failure

Under what conditions **you do not release**, even if the average is above threshold.

## Business metric

Which `PBR` outcome the technical metrics point at, and with what hypothesised link.
If the link is not proven, say so: it is a hypothesis, and it belongs to `HYP`.

---

## Anti-patterns

- **Setting the thresholds after seeing the results.** Writing them first is the entire
  value of the document; everything else is bookkeeping.
- **No baseline.** The most omitted field and the most decisive.
- **Aggregate metrics only.** Averages hide exactly the failures that matter.
- **Lowering a threshold to let an `RG` through.** If it is needed, it is a product
  decision and it requires a `DEC` with the reason, not a silent edit.
- **An evaluation dataset that grows without recording the version.** It makes historical
  comparisons meaningless.
