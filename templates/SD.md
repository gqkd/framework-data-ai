---
schema: framework/solution-design/v1
artifact_type: solution-design
lifecycle: immutable
status: active
id: SD-NNN
products: [product-a]
owners: [NAME]
created: YYYY-MM-DD
derives_from: [HYP-NNN, DFB-NNN, PBR]
classification: internal
---

# SD-NNN · Solution design and MVA

**Question:** what are we building, with which components, and what have we deliberately
deferred?

**Note on the class:** immutable. It is the snapshot of the design at gate G4. From F5
onwards the current truth lives in `ARC`, which starts living with the first line of code:
design and implementation diverge long before go-live.

## Scope of the MVP

One sentence.

## §Out of scope

Explicit, with the reason and a pointer to the `DEC` where one exists. Mandatory section,
and the one agents read most.

## Components and data flow

End-to-end diagram. For each component: its responsibility in one line.

## Technology choices

| Choice | `DEC` | In the MVA? |
|---|---|---|
| | DEC-NNN | yes/no |

**What** here, **why** in the `DEC`. If this table explains the reasoning, it is
duplicating.

## MVA: Minimum Viable Architecture

The architectural decisions that are **irreversible or expensive to reverse** and have to
be taken now. Not the ideal architecture: the minimum subset.

| Decision | Why now | Cost to reverse | `DEC` |
|---|---|---|---|

Test: if a decision can be changed in a week, it does not belong in the MVA.

## Accepted debt

| Debt | Why we accept it | Re-entry trigger |
|---|---|---|

The trigger is mandatory: without it, this is not accepted debt but forgotten debt. If the
debt spans more than one artifact, its home is `OPEN.md §2`.

## Cost model

Cost per unit (query, inference, token, GB) and estimated steady-state cost. In AI systems
cost is a non-functional requirement, not a budget line item.

---

## Anti-patterns

- **An MVA that includes everything "just to be safe".** If the MVA coincides with the
  ideal architecture, you have not done the selection that is the only purpose of the
  concept.
- **Empty out of scope.** An agent will read the absence as an oversight and implement it.
- **Debt with no trigger.**
- **No cost model.** In AI projects, the unit cost discovered in production is the most
  common cause of a forced redesign.
- **Updating it after G4.** It is immutable: from there on you update `ARC`.
