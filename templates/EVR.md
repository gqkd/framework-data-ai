---
schema: framework/evaluation-report/v1
artifact_type: evaluation-report
lifecycle: immutable
status: active
id: EVR-NNN
products: [product-a]
owners: [NAME]
created: YYYY-MM-DD HH:MM
derives_from: [EVP]
evp_version: 1.2.0
evp_hash: SHA_OF_THE_EVP_FILE
verified_against: COMMIT_HASH
classification: internal
---

# EVR-NNN · Evaluation report

**Question:** what did the evaluation produce, compared with the thresholds **declared
beforehand**?

**It serves the `RG` gate.** One per release candidate, including the first. Immutable:
never rewritten.

## Version evaluated

| Element | Version or hash |
|---|---|
| Code | commit |
| Model | name and version |
| Prompt | hash or tag |
| Configuration | |
| Evaluation dataset | version |
| **Reference `EVP`** | version + hash |

**Without these fields the report is not an eval, it is a number.** The reference to the
frozen `EVP` is what makes it verifiable that the thresholds were not touched up
afterwards.

## Results

| Metric | `EVP` threshold | Baseline | Result | Outcome |
|---|---|---|---|---|
| | | | | pass / fail |

## Results by slice

| Slice | Threshold | Result | Outcome |
|---|---|---|---|

## Observed failures

Not just how many: **of what nature**. A systematic error on one category is a different
problem from distributed noise, even at the same metric value.

## Comparison with the previous `EVR`

| Metric | Previous | Current | Δ |
|---|---|---|---|

The historical series of these reports is the memory of the system's quality, and it is
the only instrument that lets you notice a slow degradation. That is how AI systems decay
in practice.

## Verdict

`go` · `no-go` → **rework**, not rollback: it is not in production yet.

Cross-reference to the `CHG` items evaluated.

---

## Anti-patterns

- **No reference to the exact version.** The most serious defect: it makes the report
  unusable for any comparison.
- **No reference to the frozen `EVP`.** There is no way to verify that the thresholds
  were the ones set before.
- **Aggregate metrics only.** The slices are the part that uncovers the problems.
- **A `go` verdict with a slice below threshold, and no `DEC` giving the reason.** That
  is how a gate turns into a ritual.
