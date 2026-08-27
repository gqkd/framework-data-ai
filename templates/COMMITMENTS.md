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
# One row per commitment, where a check can read it. The body below keeps the promise in the
# words that were used, who said it and in what context, how binding the literal wording is,
# and what it would take to build: that is what somebody reads before renegotiating, and no
# field replaces it. These are the parts a machine has to join on.
#
# `status` is the vocabulary explained under §Register, and the two that matter are the two
# that come first. `not-yet-issued` is the promise that exists in a document nobody has
# received. `stated-as-done` is the sentence in the present tense about something that does
# not exist yet.
commitments:
  CMT-001:
    to: the customer who received it, by name
    status: open
    feasibility: feasible-with-reservations
    products: [product-a]              # required: `XP006`. `[all]` when the promise is
                                       # about the whole suite -- every join downstream
                                       # runs through this field, and empty it reaches
                                       # nothing while still reading as filled in
    threshold: the EVP row that measures it, when there is one
  CMT-002:
    to: a prospect, in the deck sent in March
    status: stated-as-done
    feasibility: feasible
    products: [product-a, product-b]
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
| **By whom and when** | Who said it and in what context |
| **Implicit or explicit deadline** | "by the end of the year" is a deadline too |
| **Room for interpretation** | How binding the literal wording is |
| **Technical translation** | What it actually takes to build |
| **Architectural constraint that follows from it** | link to a `DEC` or an `OPEN.md` entry |

**Who received it, the status, the feasibility and the products are in `commitments:` above
and are not rows here.** They were both until 3.0.0, and an empty map under a full body
validated clean while `XP005`, `XP007` and `REF006` -- every check that joins a promise
to anything -- read the map and therefore said nothing. `REG015` reports an entry present in
one half and missing from the other. The vocabularies below describe those fields, and
`§Owed a conversation` selects on them.

**`not yet assessable` is the ordinary state of this file early on**, and it was missing
from the vocabulary for as long as the vocabulary existed. This is the register of promises
made before the thing was built — that is the first sentence of this document — so a row's
honest feasibility is very often that nobody can judge it: the design does not exist, the
decision it depends on has not been taken, or the promise as worded cannot be checked at all.
`blocked_by` beside it names the register entry that has to be decided before the question
can even be asked. Three shades of difficulty and no "not yet" left one legal move, which was
to pick the nearest value and write something false.

`not applicable` is the other one: a promise with no technical content to assess.

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

**The risk row is not the remedy, it is the name of whoever carries this until the
conversation happens** — and it is expected: `RSK.md` lists leaving out the commercial risks
among its anti-patterns, and says an out of reach commitment is the biggest risk in the
project and belongs there too. `XP007` reports an out of reach or `unsatisfiable` row that no
live risk names. The finding is not asking you to mitigate a promise: it is asking who is
answerable for it in the meantime, because an exposure with no owner is one nobody
renegotiates. It also guards something downstream: `ICG` §3 stops a triage on a candidate
that contradicts a promise **still standing**, and passes over one that contradicts a row
already written off — because stopping the build does not make the promise possible, and the
alternative is the same conversation blocking the same candidates in every cycle. That is
only safe if writing a row off cannot make it disappear quietly, and this check is what
makes sure it cannot: written off, and somebody's name on it.

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
