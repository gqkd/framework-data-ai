---
schema: framework/commitments/v1
artifact_type: commitments
lifecycle: living
status: active
products: [product-a, product-b, product-c]
owners: [NAME]
created: YYYY-MM-DD
last_review: YYYY-MM-DD HH:MM
classification: confidential
---

# Commercial commitments made

**What it is for.** In a company that sold the idea before building it, these are not
requirements to be gathered: they are constraints that are already in place. They are also
architectural requirements in disguise. "a single experience across the three products" is
a tenancy decision, not a marketing line.

**Why it is the first document to write.** You will discover these constraints anyway. The
choice is whether to discover them now or at the worst possible moment, which is when they
are expensive to satisfy.

## Register

One entry per commitment. `CMT-NNN`.

### CMT-001 · Commitment title

| Field | Content |
|---|---|
| **What was promised** | The words used, as faithfully as possible |
| **To whom** | Customer, prospect, investor, partner |
| **By whom and when** | Who said it and in what context |
| **Products involved** | |
| **Implicit or explicit deadline** | "by the end of the year" is a deadline too |
| **Room for interpretation** | How binding the literal wording is |
| **Technical translation** | What it actually takes to build |
| **Feasibility** | feasible · feasible with reservations · **out of reach** |
| **Architectural constraint that follows from it** | link to a `DEC` or an `OPEN.md` entry |
| **Status** | **not yet issued** · open · met · renegotiated · unsatisfiable |

`not yet issued` is the promise that exists in a document and that nobody has received yet.
It comes first because it is **the only state in which the remedy costs an afternoon
instead of your credibility**: fixing an internal deck is free, renegotiating with a
customer is not. If a row moves from `not yet issued` to `open` without feasibility having
been verified, that is the transition this document exists to intercept.

## §Out of reach

A separate and mandatory section. Commitments with `Feasibility: out of reach` go here, in
plain sight, with the date on which it was communicated to whoever made the promise, or the
date by which it must be communicated.

An impossible commitment that nobody has renegotiated yet is the biggest risk in the
project, and it belongs to no other document.

---

## Anti-patterns

- **Rewriting the promise in requirements language.** You lose the original ambiguity, which
  is precisely the information you need in order to negotiate. Keep the words that were said.
- **Leaving out the embarrassing commitments.** They are the ones this document exists for.
- **Treating it as a sales document.** Every entry generates a technical constraint: if the
  "architectural constraint" column is empty on every row, you have not finished reading it.
- **Not dating it.** A commitment made eight months ago to a prospect who never bought does
  not bind you the way one made last week to a paying customer does.
