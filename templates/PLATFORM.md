---
schema: framework/platform-architecture/v1
artifact_type: platform-architecture
lifecycle: living
status: draft
version: 0.1.0
products: [product-a, product-b, product-c]
owners: [NAME]
created: YYYY-MM-DD
last_review: YYYY-MM-DD HH:MM
classification: internal
---

# Shared substrate architecture

> **Do not create this file until you have decided to share a substrate.**
>
> Having several products does not require one. N products managed in the same framework
> with nothing technical in common is a normal configuration: one `GLOSSARY.md`, one
> `decisions/`, one `OPEN.md`, and a full `ARC` each. That is not a degraded setup, it is a
> different one, and often the right one.
>
> An empty `PLATFORM.md` created in advance is worse than no file. It collects whatever has
> not found a home yet, and the substrate ends up defined by what accumulated in it instead
> of by a decision. While the question is open it belongs in `OPEN.md` as an entry with its
> cost to reverse. If the answer turns out to be no, delete this file and record that `DEC`
> too: a substrate that exists because nobody decided against it is the expensive case.

**Question:** what is common to the products, and with what guarantees can each of them
rely on it?

**Why it exists.** Several products built by a team smaller than their number do not have
the problem one team per product has. They have the problem of maintenance surface. This
document is the answer: one substrate described once, plus a short `ARC` per product that
declares only the **delta**. Without it, every `ARC` redescribes identity, deployment and
observability, the descriptions drift apart, and the drift surfaces at the first refactor.

That reasoning has a condition attached, and it is the ratio between people and products,
not their number. With one team per product a shared substrate can easily cost more in
coordination than it saves in duplication. With fewer people than products it starts to
pay.

**It is born with the decision that creates it**, not on day one, and from that moment it
can carry empty sections whose contents are deferred to `OPEN.md`. This is unlike `ARC`,
which is born in F5 with the first line of code: here the empty sections are information,
because they say what has not been decided yet.

> The exact scope is a further decision, separate from the one to have a substrate at all.
> While it is open, name the `OD-NNN` entry here, and let this document list the candidates
> rather than treat them as assigned.

## Scope

What is platform and what is not. There is a single boundary line:

> If it changes because the business of **one** product changes, it is not platform.

| Component | Platform | Reason | `DEC` |
|---|---|---|---|
| Identity and authorization | yes / no / to be decided | | |
| Data access and migrations | | | |
| Deployment and infrastructure | | | |
| Observability and logging | | | |
| API and error conventions | | | |
| AI evaluation layer | | | |
| Domain logic | **no** | it changes with one product's business | |

## Components

One per row: what it does, what it guarantees to whoever uses it, where the code lives.

| Component | Guarantee offered | Path | Status |
|---|---|---|---|
| | | | live · in-build · shaped |

## Contracts towards the products

What a product is allowed to assume. **Every row is a commitment**: breaking one breaks
every product at once, and that is why internal data contracts come before external ones.

| Contract | Consumers | `DC` | How it breaks |
|---|---|---|---|
| | | | |

## Tenancy and identity model

The most expensive decision in the whole project to reverse: it touches schema,
authorization, billing and data migration. If it is still open, write the pointer to
the `OD-NNN` entry here along with **the default in force**, not a description of how it
might turn out.

## Constraints the platform imposes

What a product **cannot** do by virtue of sitting on top of it. An unwritten constraint
gets discovered by violating it.

## Separability

The products are meant to be sellable individually. For each one: what it takes to run it
alone, and what prevents that today.

| Product | Runs alone | What ties it to the others |
|---|---|---|
| | yes / no | |

This section is the guard against deciding separability by accident. Absent a decision,
the de facto default becomes the shared database, which makes the products inseparable
without anyone having chosen that.

## Decisions that bind every product

Pointers only, to the `DEC` records with `scope: platform`. Generated from front matter
once the tooling exists; written by hand until then.

---

## Anti-patterns

- **Describing the platform you would like.** This document is living: it describes what
  exists today. The imagined substrate belongs in `RMP` or in an `OPEN.md` entry.
- **Empty scope but full components.** It means you are accumulating shared code without
  having decided what deserves to be shared. That is how domain logic ends up in the
  platform and the products become inseparable.
- **Repeating the content of an `ARC` here.** The platform says what is common; the domain
  delta lives in the product's `ARC`. Repeating it guarantees two versions that diverge.
- **A separability section filled in from memory.** "Yes, it runs alone" has to be verified
  by trying to start it, not by reasoning about it. Until you have tried, the value is "not
  verified".
- **Contracts towards the products without the "how it breaks" column.** A contract whose
  failure mode you do not know is not a contract, it is a hope.
