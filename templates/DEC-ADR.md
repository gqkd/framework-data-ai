---
schema: framework/decision-record/v1
artifact_type: decision-record
lifecycle: immutable
status: proposed
id: DEC-NNN
scope: architecture
products: [product-a, product-b]
owners: [NAME]
approvers: [NAME]
created: YYYY-MM-DD
derives_from: [HYP-NNN, EVD-NNN, SIG-NNN]
supersedes: null
classification: internal
---

# DEC-NNN · Decision title, in the active voice

**Question:** which decision was made, why, at that moment, and which alternatives were
discarded?

`status`: `proposed | accepted | superseded`

## Why a single document type for product and architecture

Historically the ADR records architectural decisions. But giving up on a product, choosing a
segment, accepting a commercial risk or setting a priority are decisions just as worth
recording as the choice of a database, and they are often more expensive.

A separate register for product decisions means that the **cross-product** ones, the most
expensive ones, have no home and end up in the register of whichever product you happened to
be working on that day.

So: **one document type, one numbering, one folder.** The `scope` field determines the
nature of the decision:

| `scope` | What it records | Examples |
|---|---|---|
| `product` | Decisions about what we build, for whom, at what priority | outcome of a gate · pivot · stop · segment choice · MVP scope · acceptance of a commercial risk |
| `architecture` | Decisions about how the system is built | choice of a datastore · integration style · boundary between components · deployment model |
| `platform` | Decisions that constrain every product | tenancy · identity · shared substrate · conventions |

`scope: architecture` is the classic ADR: a specialization, not a different document. A
`DEC` with `scope: platform` must list all the products in `products`.

## Context

The **constraint** that made a decision necessary. Not the chronicle of how we got there:
the force that left no choice but to choose.

## Decision

Active voice, present tense. *"We use X for Y."*

## Alternatives considered

| Alternative | Why discarded |
|---|---|

If the alternatives look obviously worse, you did not consider them: you built them so the
choice you had already made would win. It is the most common and most recognizable
anti-pattern.

## Consequences

What becomes easier. What becomes harder. **What becomes impossible.** Include the
uncomfortable consequences: they are the ones the document will be reread for.

## Review condition

*Optional but very useful.* If the decision is deliberately provisional, the observable
condition that puts it back on the table. A provisional decision with a review condition is
a decision; without a condition it is a deferral in disguise, and it belongs in `OPEN.md`.

---

## Anti-patterns

- **Written after the fact to justify.** You can always tell: the alternatives are straw
  men.
- **Editing it.** It is immutable. If the decision changes, you write a new one with
  `supersedes` and move the old one to `status: superseded`.
- **Context that tells the story instead of the constraint.** Whoever reads this a year from
  now wants to know what was forcing your hand, not who was in the meeting.
- **No negative consequences.** Every decision has some. Leaving them out makes the document
  useless exactly when it is needed, which is when someone is on the receiving end of one.
- **One `DEC` for every tiny choice.** Record what would be expensive to rediscover. If the
  choice can be reversed in an afternoon, it does not need a `DEC`.
