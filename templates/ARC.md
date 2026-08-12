---
schema: framework/architecture/v1
artifact_type: architecture
lifecycle: living
status: active
version: 1.0.0
products: [product-a]
owners: [NAME]
created: YYYY-MM-DD HH:MM
last_review: YYYY-MM-DD HH:MM
verified_code:                  # one commit per repository named in product.yaml#code
  product.backend: COMMIT_HASH
classification: internal
---

# Architecture: product name

**Question:** how is the system built right now, what shape will it have when it is
finished, and what exactly separates the two?

**One file, three sections.** A target only means something set against what exists, and
the value is in the delta: separate files would produce two architectures that diverge, and
nobody would be able to say which one the code is supposed to match. For precise references
use the anchors: `ARC.md#target`.

**It starts living at F5**, with the first line of code, not at go-live: design and
implementation diverge long before that. §target is seeded from the `SD` when this file is
born; before F5 the design lives in the `SD` and nowhere else.

**`verified_code` attests §current only.** It records the commits this document was last
checked against. §target has no commit by definition: it describes something nobody has
built yet, and a hash on it would be a claim about a system that does not exist.

**The MVA is not a section here.** It is what §current *is* at the end of the MVP: the
architecture minimally sufficient to support it, decided at G4 and recorded as designed in
the `SD`. The target is **not** "the MVA plus more". An MVA legitimately contains things
the target discards, because it was built to be sufficient now and not to be the
destination. Saying so out loud is the point of having both sections.

**Two different deltas, do not confuse them.** If the products share a substrate, this
*whole file* is the delta against `PLATFORM.md`, and what is shared is documented once,
there. §delta below is a different thing entirely: the distance between what exists and
where this product is going. If there is no `PLATFORM.md`, and there does not have to be,
this file is the whole architecture of the product and only §delta is a delta.

---

<!-- section: current -->
# §current

How the system is built **today**. As built, not as designed. If it does not match the
code, this section is harmful rather than incomplete.

## Components

| Component | Responsibility (one line) | Shared or specific | `DEC` |
|---|---|---|---|

## End-to-end data flow

A diagram. It is the part most often missing and the one that is needed most: if a new
person cannot draw the system on a whiteboard after reading this section, what is usually
missing is the data flow.

## Data states

Where it lives and in what form: raw, curated, serving. With pointers to the `DC`.

## Boundaries

What is ours, what is third party, what belongs to another product. Every boundary towards
another product must correspond to a `DC`.

## Environments

| Environment | Purpose | Relevant differences from production |
|---|---|---|

The differences are the useful part: they are where the bugs that do not reproduce come
from.

## Decisions that explain it

List of the relevant `DEC`. Links only: **how it is** here, **why** in the `DEC`.

---

<!-- section: target -->
# §target

The shape the architecture has when this product is finished. Coarser than §current is
correct: you know the destination better than you know its details, and inventing the
details is how a target becomes fiction nobody revises.

## Components

The same table as §current, in target form. New components, components that disappear,
components that only change responsibility.

## Boundaries in the target

Which boundaries move, and which `DC` are born or die with them. A boundary that appears
here without a `DC` planned against it is the one that will be broken in silence.

## What the target deliberately excludes

Mandatory section. A destination without an edge grows to hold everything anyone ever
proposed, and then it constrains nothing. Naming what is **not** in the target is what
gives the rest of the section its meaning: point to the `DEC` or the `OPEN` entry that
settles each exclusion.

## Decisions that fix the target

The `DEC` that make this a decided destination rather than a preference. A target with no
`DEC` behind it is a wish, and an agent reading it cannot tell which parts are binding.

---

<!-- section: delta -->
# §delta

What separates §current from §target, **structurally**: which components are missing, which
boundaries are not yet drawn, which capability does not exist.

| # | Increment | What it unblocks | Blocked by | `DEC` |
|---|---|---|---|---|

Each row must be nameable as a future `CHG`. If it cannot be, it is not an increment yet:
it is a direction, and it belongs in §target.

**This section says *what* is missing, never *when*.** The order, and the evidence each
increment depends on, are the `RMP`. Repeating the sequencing here would put the same fact
in two places, and the copy that goes stale is always the one nobody read this week.

## Accepted debt, and what pays it off

What §current does knowingly wrong, and which increment settles it. Debt with no row here
is indistinguishable from an oversight after two months, and it is the difference between a
decision and a mistake.

---

## Anti-patterns

- **Becoming the sum of all the `DEC`.** If this file starts explaining the rationale, it
  is duplicating, and it will soon diverge from the `DEC`.
- **Describing the system as designed in §current.** That is what §target is for. A
  §current that describes intentions leaves the product with two targets and no record of
  what was actually built.
- **A §target that is §current with more boxes.** The information is in what changes and in
  what is excluded, not in a longer table.
- **A §delta that repeats the `RMP`.** Structural here, temporal and evidential there. The
  test: if a row would change because a date moved, it does not belong here.
- **Updating §target without updating §delta.** The delta becomes a silent lie, which is
  worse than no delta at all.
- **No data flow.** See above.
- **Duplicating `PLATFORM.md`, where one exists.** If a section is identical in every
  `ARC`, it does not belong in the `ARC`.
