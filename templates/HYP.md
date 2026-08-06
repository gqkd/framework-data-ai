---
schema: framework/hypothesis/v1
artifact_type: hypothesis
lifecycle: immutable
status: open
id: HYP-NNN
products: [product-a]
owners: [NAME]
created: YYYY-MM-DD
derives_from: [PRB-NNN]
classification: internal
---

# HYP-NNN · Title of the hypothesis

**Question:** what do we believe is true, and how will we find out we were wrong?

`status`: `open | confirmed | refuted | partially-confirmed`

## The hypothesis

> We believe that **[intervention]** for **[whom]** produces **[measurable effect]**.

One sentence. If it does not fit into one sentence, they are several hypotheses and must
be separated.

## Assumptions, ordered by risk

| # | Assumption | Risk if false | How it is tested | Cost of the test |
|---|---|---|---|---|
| 1 | | | | |

**The order is the part that matters.** The first assumption in the list is what you go
and test first: this table steers the whole of phase 2, more than any other document.

## What would make us abandon the hypothesis

An observable condition. If you cannot write it, you do not have a hypothesis.

## Initial confidence

`high | medium | low`, with one line of reasoning.

## Outcome

*Filled in at the gate.* Confirmed, refuted, partially. Cross-reference to `EVD` and to
the `DEC` of the gate.

---

## Anti-patterns

- **A hypothesis that cannot be falsified.** "Improve the user experience" is not a
  hypothesis: it is a wish. The test is whether you can write down what would refute it.
- **Unordered assumptions.** A flat list does not tell you where to start, and you will
  start with the easiest one instead of the riskiest.
- **An effect that cannot be measured.** If the effect has no metric in `GLOSSARY`, add
  it before proceeding.
- **A single hypothesis for a complex problem.** If you have only one, you have probably
  already decided and are documenting after the fact.
