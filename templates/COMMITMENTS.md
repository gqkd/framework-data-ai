---
schema: framework/commitments/v1
artifact_type: commitments
lifecycle: living
status: active
products: [product-a, product-b, product-c]
owners: [NAME]
created: YYYY-MM-DD HH:MM
last_review: YYYY-MM-DD HH:MM
classification: confidential
---

# Commercial commitments made

**What it is for.** In a company that sold the idea before building it, these are not
requirements to be gathered: they are constraints that are already in place. They are also
architectural requirements in disguise. "a single experience across the whole suite" is
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
| **Status** | **not yet issued** · **stated as done** · open · met · renegotiated · unsatisfiable |

`not yet issued` is the promise that exists in a document and that nobody has received yet.
It comes first because it is **the only state in which the remedy costs an afternoon
instead of your credibility**: fixing an internal deck is free, renegotiating with a
customer is not. If a row moves from `not yet issued` to `open` without feasibility having
been verified, that is the transition this document exists to intercept.

`stated as done` is the sentence written in the present tense about something that does not
exist. *"Integrated with SAP."* Perfectly feasible, on the roadmap, and not true today.

It is a separate status and not a variant of `open` because the exposure is a different
kind. `open` is a promise outstanding, and the customer knows it is outstanding. This one is
**a false statement of fact that somebody is acting on now**, and the remedy is not a
roadmap entry, it is a correction to a specific person. Sales decks are written in the
present tense as a matter of style, so a corpus ingestion produces these in quantity and
every one of them is a claim somebody currently believes.

Feasibility does not capture it. A `stated as done` row is usually `feasible`, which is
exactly what makes it easy to leave alone: it will be true eventually, and nothing in the
document would have said that in the meantime somebody was told otherwise.

## §Owed a conversation

A separate and mandatory section, for the two cases where the next move is not building
anything. Both go here in plain sight, with the date on which it was said to whoever needs
to hear it, or the date by which it has to be.

| Which rows | What is owed |
|---|---|
| `Feasibility: out of reach` | a renegotiation. It will not be delivered and somebody is planning around it |
| `Status: stated as done` | a correction. It is true in a document and false in the product |

An impossible commitment nobody has renegotiated is the biggest risk in the project. A
commitment written in the present tense about something that does not exist is the most
common one, and the quietest: it needs no decision, breaks no check, and expires only when
somebody acts on it.

Neither belongs to any other document. `RSK` records risks you have accepted; these are
sentences that are wrong, and the remedy is a conversation and not a mitigation.

---

## Anti-patterns

- **Rewriting the promise in requirements language.** You lose the original ambiguity, which
  is precisely the information you need in order to negotiate. Keep the words that were said.
- **Leaving out the embarrassing commitments.** They are the ones this document exists for.
- **Filing a present-tense claim as `open`.** It reads as work outstanding, which is
  comfortable and wrong: the customer is not waiting for it, they think they have it. The
  status has to carry that, because the difference decides whether the next step is a sprint
  or a phone call.
- **Treating it as a sales document.** Every entry generates a technical constraint: if the
  "architectural constraint" column is empty on every row, you have not finished reading it.
- **Not dating it.** A commitment made eight months ago to a prospect who never bought does
  not bind you the way one made last week to a paying customer does.
