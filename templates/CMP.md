---
schema: framework/competitor-comparison/v1
artifact_type: competitor-comparison
lifecycle: immutable
status: active
id: CMP-NNN
products: [product-a]
owners: [NAME]
created: YYYY-MM-DD HH:MM
derives_from: [HYP-NNN]
classification: internal
---

# CMP-NNN · Comparison · build, buy or adapt

**Question:** do we build, buy or adapt?

**Note on the class:** immutable and dated. The market changes: a comparison from two years
ago gets redone, not touched up.

## Criteria, defined before looking at the options

| # | Criterion | Weight | Minimum acceptable threshold |
|---|---|---|---|
| 1 | | | |

**Defining them first is the entire value of the document.** Criteria chosen after seeing
the options are rationalization, and you can recognize them because they line up
suspiciously well with the winner's strengths.

## Options

| Option | Coverage | Entry cost | Steady-state cost | Lock-in | Where the data lives | Integration effort | Maturity |
|---|---|---|---|---|---|---|---|
| Do nothing | | | | | | | |
| In-house build | | | | | | | |
| Vendor A | | | | | | | |

The **"do nothing"** and **"in-house build"** rows are mandatory: they are what turns the
table from a shopping list into a decision.

## Verdict

One line, with the criterion that decided it. Pointer to the `DEC`.

---

## Anti-patterns

- **Criteria defined after the options.** See above.
- **No "build" row.** Without it you have not compared anything: you have picked a vendor.
- **No "do nothing" row.** That is the option you are really competing against.
- **Functional coverage as the only criterion.** Steady-state cost and lock-in decide more
  often, and later.
- **Not dating it.** A comparison with no date will be reused when it is no longer worth
  anything.
