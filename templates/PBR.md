---
schema: framework/product-brief/v1
artifact_type: product-brief
lifecycle: living
status: active
version: 1.0.0
products: [product-a]
owners: [NAME]
created: YYYY-MM-DD
last_review: YYYY-MM-DD HH:MM
derives_from: [PRB-NNN, HYP-NNN, CMT-NNN]
classification: internal
---

# Product brief: Product name

**Question:** what is the current product, for whom, what outcome does it produce, what
behaviors does it support?

**Why it exists.** It is the product counterpart of `ARC`: that document says how the
system is built, this one says what the product is. Without it, reshaping produces only
architectural artifacts and product decisions stay verbal. If the product has already been
sold, this definition today exists only inside pitches: writing it down is the first act.

## One line

What it does, for whom, with what effect.

## Actors

| Role | What they get | How we measure it |
|---|---|---|
| | | |

Distinguish the **user** (uses it) from the **buyer** (pays for it) from the **process
owner** (absorbs the change). They are often three different people with diverging
interests.

## Outcome

What changes in the world if the product works. Not features: effects.
Every outcome has a metric from the `GLOSSARY`, with current value and target.

## Current capabilities

What the product does **today**, not what it will do. Every capability with `status: live |
in-build | shaped | pitched`.

`pitched` is the case to name first: **promised in a commercial document, with no design
behind it.** It is the most dangerous state a capability can have, because to whoever reads
a pitch it is indistinguishable from `live`, and without a word to say so it slips silently
in among the other three. If a row is `pitched`, the `PBR` must say *in which document* it
was promised.

## §Out of scope

What the product does **not** do, deliberately, with the reason. Mandatory section.

It is the section agents read most: it stops them from enthusiastically implementing
something you had assessed and discarded. Every entry with a cross-reference to the `DEC`
that excluded it, where one exists.

## Complementarity with the other products

What this product assumes the other two do, and what it offers them. The contact points
listed here must correspond to an internal `DC`: if there is none, it is an implicit
integration, which is to say a debt.

## Product metrics

Name, definition in `GLOSSARY`, current value, target, who watches it.

## Constraints

Commercial (from `COMMITMENTS`), regulatory, technical, cost.

## Current release

Reference to `REL` and `RLM`. Generated field.

---

## Anti-patterns

- **Listing features instead of outcomes.** A list of features lets nobody decide what to
  cut when cutting is what is needed.
- **Confusing user and buyer.** In B2B products the one who uses and the one who pays want
  different things; a brief that merges them produces a product that satisfies neither.
- **Describing the imagined product.** This document is living: it describes today. The
  future belongs in `RMP`.
- **An empty out of scope.** It means you have not decided anything yet, or that the
  decisions are verbal.
- **Complementarity declared in words without a `DC`.** It is how several products become one
  inseparable product without anyone having decided it.
