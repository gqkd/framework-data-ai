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
classification: internal
---

# Progressive implementation roadmap: Product name

**Question:** which future increments do we hypothesize, and which evidence do they depend
on?

**Do not confuse it with `IMP`.** This document looks ahead, it is living, and its
increments are an **input** to change intake. `IMP` looks at the current cycle, is replaced
every cycle, and is an **output** of reshaping. Keeping them separate is what stops you
rewriting the plan every time reshaping changes the scope.

## Increments

Every increment has a **maturity state**, which is the useful part of the document:

| State | Meaning |
|---|---|
| `committed` | Decided, with a `DEC`. It will go into a `CHG`. |
| `shaped` | Defined enough to be estimated, not yet decided |
| `conditional` | Depends on evidence we do not have yet |

### INC-NNN · Title

| Field | Content |
|---|---|
| State | committed · shaped · conditional |
| Expected outcome | which `PBR` outcome it moves |
| Depends on | evidence, other increments, `OD` from `OPEN.md` |
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
  the date implies a certainty the state denies.
- **Every increment `committed`.** It means you are not distinguishing, and the roadmap
  goes back to being an ordered wish list.
- **No dependency on evidence.** If no increment depends on something you still have to
  discover, you are not running a data project: you are carrying out an order.
- **Confusing it with `IMP`.** The symptom: the roadmap contains assignments and work
  sequences.
