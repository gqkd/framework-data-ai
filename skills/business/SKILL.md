---
name: business
description: >
  Produce a weekly business status update (SAL) for one product or the whole suite: what the
  product does today, what is left to do, where it is going and what the target is, and which
  needs and difficulties have to be faced — including the decisions or actions required from
  people outside development. Non-technical register for sponsors,
  product owners, operations, commercial teams, management and steering meetings. Triggers on
  "SAL settimanale", "aggiornamento settimanale", "stato avanzamento lavori", "dove siamo
  con il progetto", "aggiornamento per il management", "azioni richieste al business",
  "weekly status update", "steering update", "project status for management", "what changed
  this week". Also use for a non-technical product update that must distinguish current state,
  direction and target. Do not use for engineering cycle planning or release approval.
---

# business

Read `references/preamble.md`, which sits at `${CLAUDE_PLUGIN_ROOT}`, first.

This skill writes for the people who steer, fund, enable, adopt or sell the product, not for
the people implementing it. Produce a decision-ready weekly update: enough product context to
understand the movement, and enough precision to act without reading the technical artifacts.

The SAL is not authoritative and has no owner. Do not ask who is responsible for it and do
not add `owner`, `owners`, `a cura di`, `approvato da` or an equivalent field. The
authoritative sources retain their own owners; the SAL only retells them and introduces no
new claim.

## What it produces

Create one immutable snapshot per run:

- `_meta/business/SAL-NNN-<product>-YYYY-MM-DD.md` for one product;
- `_meta/business/SAL-NNN-suite-YYYY-MM-DD.md` for the suite.

Use the next number in the directory. Never edit a previous SAL. The date identifies the
snapshot; it is not a delivery commitment. `_meta/business/` is outside the artifact set and
nothing in it becomes a source for another document.

Before writing, show a compact proposal naming the new file, its scope and which source
sections can support it. Write only after approval, as required by the preamble.

**Each SAL stands on its own.** It is not a delta against the previous one and it does not
reconstruct history: nothing in the repository records what an earlier update said, so a
"what changed this week" section would be composed rather than derived — which is the one
thing this skill must never do. The SAL answers four questions and no others: **what exists,
what is left to do, where the product is going, and which needs and difficulties have to be
faced.**

## 1 · Establish the evidence base

Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:?unset: point it at your framework-data-ai checkout}/skills/audit/scripts/validate.py" --root <project> --emit-index --check
```

Stop on errors. Regenerate stale indices before composing the update. Read `AGENTS.md`, the
binding open registers, `products/<p>/product.yaml`, `product.index.yaml` and
`decisions/INDEX.md`. Then read the sources required by the table below.

Every statement is verified against the current authoritative artifacts. An earlier SAL is
not a source: it is an earlier retelling, and a claim carried forward from one is a claim
nobody checked.

## 2 · Write these sections in this order

| Section | Authoritative sources |
|---|---|
| **Header** — scope and snapshot date. No owner, no comparison baseline | filename |
| **1 · Stato di sintesi** — where the product is, where it is going, and the single most important condition for progress | `PBR`, current `ARC`, `RMP`, open registers, `RSK` |
| **2 · What there is today** — the capabilities available now and the value they produce, then the current architecture in one diagram | live rows in `PBR`, latest `REL`; `ARC#current` §components, §data flow |
| **3 · What is left to do** — the blocks of the decided release perimeter, each in terms of what it lets a customer be told; and the activities delivered by people as a declared service | the perimeter `DEC`, `SD §Scope of the MVP`; service `DEC` records and `PBR §out of scope` |
| **4 · Where we are going** — what the target product will do, the target architecture in one diagram, and the roadmap in ordered phases with their maturity | `ARC#target`, the perimeter `DEC`, `RMP` |
| **5 · Needs and difficulties** — what has to be faced, each with its business consequence, how it is handled today, and what changes it. Needs that require somebody outside development are named as such, with the role | `RSK`, known issues, open decisions with the default in force; data feasibility and contracts where relevant |
| **Internal sources** — the artifact identifiers used | every source actually used |

If a section has no authoritative source, say so in one sentence and do not fill it by
inference. **Where the target sections of `ARC` are unwritten, draw what is written and stop
there**: completing them by plausible extension is inventing the product.

## 3 · Make challenges useful to the business

Do not copy a technical risk register. Translate only challenges that can change scope,
adoption, value, cost, assurance or the order of work.

For each challenge state:

- the consequence somebody outside development can recognize;
- what is being done or what default is currently in force;
- the observable condition that resolves, worsens or reopens it;
- the required non-development contribution, if one exists.

Do not label ordinary engineering work as a request to the business. A need is addressed to
somebody outside development only when an external actor must decide, provide, approve,
validate or adopt something — and then it says which role, what is needed, why, when it bites
and what happens if it does not arrive. Use roles documented by the project; do not invent
names or assign personal accountability.

## 4 · Translate the roadmap

- Keep phases in dependency order and name each by the business outcome it unlocks.
- Distinguish the first release from what follows it.
- Preserve maturity: committed, shaped and conditional must not read as equally certain.
- Use dates only when an authoritative plan or commitment carries them. Never create a
  quarter, deadline, duration or percentage of completion.

## 5 · Writing rules

- **A promise is not a capability.** What the material has claimed does not belong here in
  any form: not as something delivered, not as something owed, not as a gap. This document
  carries what the artifacts establish about the product — what exists, what is planned, what
  has to be faced. Where a claim needs assessing, that happens with whoever governs the
  product and not in a status update.
- Lead with what the product does and what is being built, not with architecture.
- Use plain business language; keep identifiers out of the prose and put them in the footer.
- Distinguish **available now**, **in progress**, **decided next**, and **conditional**.
- Include a number only when an authoritative source defines and measures it.
- Mention technical detail only when it explains a business consequence or a dependency.
- Keep architecture diagrams optional, with at most six boxes named by function.
- State unchanged status only when it matters to a decision; do not pad the update.
- Do not infer that absence of a new log entry means no work happened.
- Do not state team capacity, immediacy, headcount or confidence without a source.
- Do not publish or send the file.

## Suite SAL

Compose the same sections across products. Keep different product states separate; never
invent a single progress percentage for the suite. Put shared needs and difficulties first,
then the product-specific ones. Discuss shared architecture only where it changes a business
dependency or an outcome.

## What not to do

- Do not present the target as current state.
- Do not turn unresolved choices into decisions.
- Do not use the SAL as evidence or update artifacts from statements first written in it.
- Do not add a document owner or a person responsible for the document's assertions.
- Do not manufacture movement, or a comparison with an earlier update, that the sources do
  not carry.

## Handing back

State the scope, which sections had no source or only a partial one, and the result of the
validator. Anything you read and deliberately left out of the file goes here instead, in one
line each.

Then add the two closing blocks required by the preamble. In the next-steps block, derive
actions from section 5 and the open registers; recommend the highest-cost actionable item
rather than inventing a generic meeting.
