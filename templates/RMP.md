---
schema: framework/roadmap/v1
artifact_type: roadmap
lifecycle: living
status: active
version: 1.0.0
products: [product-a]
owners: [NAME]
created: YYYY-MM-DD HH:MM
last_review: YYYY-MM-DD HH:MM
# review_scope: written beside `last_review` by `attest.py`, after a person rereads a
# document that already exists: what the reading covered and what it did not. Not on
# day one, because a creation is not a reading.
classification: internal
# THE ORDER OF DELIVERY, WHERE A SCRIPT CAN READ IT. Optional: a roadmap without these two
# maps is valid and nothing reports it. With them, the daily digest draws its Gantt from
# here instead of from an order somebody keeps by hand. No dates anywhere in this file: the
# date of a milestone is declared in the digest's state.
#
# `delivery_stages`: the biggest container, in a sequence. A stage waits for the stages in
# its `after`, and two stages that do not wait for each other may run side by side. Ids are
# short lowercase slugs: `t1`, `t2`, `t2a`.
delivery_stages:
  t1:
    name: What the first stage makes possible
    after: []
    increments: [INC-NNN]
    milestone: The milestone that closes it, named and never dated
  # t2:
  #   name: What the second stage makes possible
  #   after: [t1]
  #   increments: [INC-NNN]
#
# `increments`: one row per `### INC-NNN` below. An increment has no size of its own: it is
# worth the sum of what composes it, the `OD` and `KI` it `requires`, which are resolved
# first, and the `CHG` that realise it. A `CHG` names its increment in its own
# `derives_from`; `changes` lists only the older ones that do not, because a `CHG` cannot be
# edited after approval. `depends_on` names the increments that have to come first.
increments:
  INC-NNN:
    state: committed            # committed · shaped · conditional · delivered
    depends_on: []
    requires: [OD-NNN, KI-NNN]
    changes: []
---

# Progressive implementation roadmap: Product name

**Question:** which increments do we hypothesize, in which order are they delivered, and
which evidence and which decisions do they depend on?

**Do not confuse it with `IMP`.** This document looks ahead, it is living, and its
increments are an **input** to change intake. `IMP` looks at the current cycle, is replaced
every cycle, and is an **output** of reshaping. Keeping them separate is what stops you
rewriting the plan every time reshaping changes the scope. The stages order the
increments across cycles; which changes a cycle executes, and with what intermediate
compatibility, is the `IMP`'s.

## Delivery stages

One paragraph per stage, for what the front matter cannot say: when a stage can start and
when it is finished, written as criteria somebody can check. Do not repeat which increments
it holds or what it comes after: that is in the front matter, and a second copy here is the
one that goes stale.

### t1 · What the first stage makes possible

- **Entry criteria:** what has to be true before it starts.
- **Exit criteria:** what is true when it is finished, and what closes its milestone.

## Increments

Every increment has a **maturity state**, which is the useful part of the document. It is
written in `increments:` above, beside what the increment depends on, and nowhere else:

| State | Meaning |
|---|---|
| `committed` | Decided, with a `DEC`. It will go into a `CHG`. |
| `shaped` | Defined enough to be estimated, not yet decided |
| `conditional` | Depends on evidence we do not have yet |
| `delivered` | Everything that composes it is closed |

### INC-NNN · Title

| Field | Content |
|---|---|
| Expected outcome | which `PBR` outcome it moves |
| Evidence it depends on | what we still have to discover before it is worth doing; the increments and the decisions it waits for are in `increments:` above |
| Architecture enabler | what must exist first, with a pointer to a `DEC` |
| Entry criteria | when it can start |
| Exit criteria | when it is finished |
| Products involved | if it touches more than one, it requires a `DEC` with `scope: platform` |

## §Not in roadmap

What we have decided not to do, with the reason. It saves re-explaining the same choice
every month and it tells an agent that the absence is deliberate.

---

## Anti-patterns

- **Treating it as a plan with dates.** A `conditional` increment with a date is a lie:
  the date implies a certainty the state denies. The order is here; the dates are computed
  by the digest from the hours, and the date of a milestone is declared in its state.
- **Every increment `committed`.** It means you are not distinguishing, and the roadmap
  goes back to being an ordered wish list.
- **No dependency on evidence.** If no increment depends on something you still have to
  discover, you are not running a data project: you are carrying out an order.
- **Confusing it with `IMP`.** The symptom: the roadmap contains assignments, or the order
  of the changes inside one cycle. Ordering the increments across cycles is what the
  stages are for.
- **An increment with nothing under it.** Until its decisions, issues and changes are
  written, it is worth zero hours, and the digest says it is still to be broken down.
