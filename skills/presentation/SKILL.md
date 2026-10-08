---
name: presentation
description: >
  Turn the documentation of a product into a short PowerPoint presentation that a
  non-technical reader understands: business people and customers. One presentation per
  product; asked for a suite, it makes one for each. What
  the product is for and for whom, what it does today, how it works in one picture, and a
  roadmap of what is done and what is still to do, with no dates. High level, customer-safe,
  produced as a .pptx. Triggers on "presentazione per il cliente", "fammi le slide per il
  business", "spiega il prodotto a chi non è tecnico", "documentazione semplificata per i
  clienti", "una presentazione del prodotto in PowerPoint", "customer presentation",
  "slides for the business", "explain the product to non-technical stakeholders", "a
  PowerPoint about the product for the client". Do not use for the weekly status update,
  for ingesting decks somebody hands over, or for onboarding people inside the team.
---

# presentation

Read `references/preamble.md`, which sits at `${CLAUDE_PLUGIN_ROOT}`, first.

This skill writes for somebody who will never open the repository: a customer, a sponsor, a
salesperson. They read ten slides at most and repeat what they understood. Everything on a
slide is therefore a statement the project is making outside itself, and the rules below are
all one rule: **say less, and only what the artifacts establish.**

The presentation is not authoritative and has no owner, like the SAL of `business`. Do not
ask who is responsible for it and do not put an owner, an approver or a "prepared by" on it.

## Where it stops and `business` begins

`business` is the weekly SAL: internal, recurring, Markdown, and it carries the needs,
difficulties and requests that people outside development must act on. This skill is the
opposite on each axis: occasional, a `.pptx`, and **always safe to hand to a customer.**
There is no internal variant. Risks, open decisions, requests to the business and anything
that needs a meeting to interpret belong in the SAL; a presentation that carried them would
be a SAL that has left the building.

## What it produces

One immutable snapshot per run, in its own directory:

```
_meta/presentation/PRS-NNN-<product>-YYYY-MM-DD/
  outline.yaml          what each slide says, and the sources it says it from
  diagrams/             the diagram sources and the PNG exported from them, if any
  PRS-NNN-<product>-YYYY-MM-DD.pptx
```

Use the next number in `_meta/presentation/`. Never edit a previous one: a revision of the
outline is a new number, and a `.pptx` retouched by hand afterwards is somebody's copy, not
something this skill reads back. `_meta/presentation/` is outside the artifact set, the
validator does not scan it and the extractor of `start` does not take it for a corpus.
Whether the `.pptx` is committed is the project's choice; the outline is what makes it
reviewable, so it is the part worth keeping.

## 1 · Establish the evidence base

Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:?unset: point it at your framework-data-ai checkout}/skills/audit/scripts/validate.py" --root <project> --emit-index --check
```

Stop on errors: a presentation assembled from documents that contradict each other repeats
the contradiction to a customer, who cannot see it. Read `AGENTS.md`,
`products/<p>/product.yaml`, `product.index.yaml` and the sources in the table below. Read the
open registers too, for one purpose only: to know what must **not** appear as settled.

Ask one question if the task does not answer it: **which customer, if any, is the
presentation for.** It decides the filter in §3. Nothing else is asked; the structure is fixed.

## 2 · The slides, in this order

| Slide | What it says | Authoritative sources |
|---|---|---|
| **Title** | the product's name and its one line | `PBR §One line` |
| **For whom and why** | who uses it, who benefits, what changes for them, and what it deliberately does not do when that reassures | `PBR §Actors`, `§Outcome`, `§Out of scope` |
| **What it does today** | the capabilities that are live, each as something a person can now do | `PBR §Current capabilities` rows with `status: live`, the latest `REL §What changes` |
| **How it works** | a `flow` of two to five steps, named by what they do for the reader | `ARC#current §Components`, `§End-to-end data flow` |
| **Roadmap** | two columns, **Done** and **To do**, no dates | see §4 |
| **Where it is going** | what the product will do once the to-do column is done | `ARC#target`, the perimeter `DEC`, `SD §Scope of the MVP` |

Never more than ten slides. **One presentation per product, always.** Asked for the suite,
make one for each product: two products told on the same slides blur into one, and the reader
cannot tell which of them does what today. Where the products relate, one card in each says so.

**Be specific, within what the sources carry.** Between the fixed slides, add the ones the
sources can fill and that a reader would ask about:

| Slide | What it says | Authoritative sources |
|---|---|---|
| **The problem** | what people do by hand today, step by step, and which step costs most | `PBR §Outcome`, `§Actors` |
| **Questions it answers** | four to six example questions, in the reader's words, of the kinds the product is tested on | `EVP §Dataset`, live rows of `PBR §Current capabilities` |
| **Where it is going** | the decided properties of the target, each as what the reader will be able to rely on | perimeter and design `DEC` records whose increments are `committed` |
| **Your data** | how the customer's data is kept, sent and separated; what holds today and what is decided, each card saying which | `PBR §Constraints`, the `DEC` records on isolation and on what leaves |
| **What it does not do** | the deliberate exclusions that reassure | `PBR §Out of scope` |
| **How it will work** | for a product with no code, the designed flow, titled as designed | `ARC#target`, the design principles |

A card that mixes what exists with what is decided says which is which in its title: "Oggi ·",
"In arrivo ·". Present and future in one slide are fine; present and future in one sentence are
the confusion this skill exists to prevent. A slide with no authoritative source
is **left out**, not filled: a missing "where it is going" says nothing, an invented one says
something false. Where `ARC#target` is unwritten, the last slide goes.

**Prefer `cards` to `bullets`.** A tile with a title and one sentence reads at a glance and
holds a capability, an actor or a principle; bullets are for the rare slide that is a list.
At most five bullets a slide, one line each, and six cards. If a point needs more than that
it is a technical point, and it does not belong here.

## 3 · What never appears

A customer is reading. These stay out in every case, whoever the presentation is for:

- **Risks, open decisions and their defaults, known issues, accepted debt, costs.** `RSK`,
  every `OPEN.md`, `SD §Cost model`, `ARC §Accepted debt`.
- **Promises.** A `pitched` capability, an entry in `COMMITMENTS.md`, anything the commercial
  material claimed. A promise is not a capability, and on a slide it becomes one. If what was
  promised is also a `committed` increment, it appears as that increment and nothing more.
- **Other customers.** Any capability, increment, decision or commitment that names a customer
  other than the one the presentation is for — or any customer at all, when it is for nobody in
  particular. When in doubt, leave the item out and say so in the hand-back.
- **Identifiers and internal names.** No `DEC-012`, no `INC-004`, no component codenames, no
  repository paths, no team members. They live in `outline.yaml` under `sources`, and not in the
  `.pptx` — not even in the speaker notes, which travel with the file.
- **Technology, unless the reader chose it.** "a data warehouse", not the product name of one;
  the exception is a technology the customer asked for or owns.
- **Numbers no artifact measures.** A figure appears only when an artifact defines it and
  carries its current value.

## 4 · The roadmap: done and to do

No weeks, no months, no quarters, no durations, no percentages, no "soon". Two columns, and
each item is named by what it lets somebody do.

| Column | What goes in it |
|---|---|
| **Done** | `RMP` increments `delivered`. `PBR` capabilities with `status: live`. A row with no status is done only if `ARC#current` has the component that does it; a row that says `live` and also says it is unverified is not |
| **To do** | `PBR` capabilities `in-build`; `RMP` increments `committed`, in dependency order; the first delivery a perimeter `DEC` decides |
| **To do, marked "planned"** | `RMP` increments and `PBR` capabilities `shaped`: defined, not decided |
| *nowhere* | `RMP` increments `conditional`; `PBR` capabilities `pitched`; `RMP §Not in roadmap`; any state the table does not name |

The state of an increment is the one in the roadmap's `increments:` when it has them, and
the body table otherwise; the dependency order is the sequence of its `delivery_stages`.

A `conditional` increment shown to a customer, however it is labelled, is the moment a
promise is born: the label is forgotten and the item is remembered. A `shaped` one carries its
mark on the slide, because "decided" and "defined" must not read as equally certain. If the
To do column ends up empty, it says so in one bullet rather than being padded; an empty Done
column renders as "nothing in production yet", which is true and is not padded either.

**When two sources disagree on an item's state, the more cautious one decides.** A capability
`shaped` in the `PBR` whose increment is `conditional` in the `RMP` stays off the roadmap, and
the hand-back names the disagreement: it is a finding for `audit`, not for the slide.

Group increments that serve one outcome into one item, named by that outcome, rather than
dropping some to fit six: "more companies on one system, each seeing only its own data" is
three increments to the team and one thing to the reader.

## 5 · The diagram

"How it works" is a `flow` slide: two to five steps, drawn by the renderer as shapes in the
deck, so whoever presents it can move a box or fix a word in PowerPoint. Each step is named by
what it does for the reader ("collects the orders", not "ingestion-svc"), with one sentence
under it and no technology names; `focal` marks the one step the reader should remember.

A picture made elsewhere goes in an `image` slide only when a flow of boxes cannot say it — a
map, a layered view, a screenshot. Then use `diagram-design` if it is installed, export to PNG
and point the slide at the file under `diagrams/`. A linear sequence is never that case: a PNG of
four boxes is a flow nobody can edit.

## 6 · Propose, write the outline, render

1. **Propose.** A compact table, never the slides: the directory that will be created, the
   customer filter in force, and one row per slide with its sources — and the slides left out,
   with the reason. Write nothing before the user agrees.
2. **Write `outline.yaml`.** The schema is in `scripts/render.py`; every slide but the title
   carries `sources`, the artifact sections it was taken from. Then run:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/presentation/scripts/render.py" <dir>/outline.yaml --check
   ```

   It refuses identifiers and repository paths anywhere on a slide; dates, months, durations
   and percentages on the roadmap; a roadmap item marked anything but planned; a slide with no
   sources; more than ten slides, five bullets or six items a column; and an image that is
   not there. Fix the outline; do not loosen the text to get past it.
3. **Render.** The same command without `--check` writes the `.pptx` next to the outline. Then
   show the user the outline, slide by slide, as the document to review.

## What not to do

- Do not present the target as what exists, or a `shaped` item as decided.
- Do not put on a slide anything an artifact does not say, however plausible.
- Do not produce an internal version with the risks in it; that is `business`.
- Do not use the presentation as a source, or update an artifact from a sentence first written
  in it.
- Do not send, upload or publish the file.

## Handing back

State the directory, the customer filter, which slides were left out and why, every
disagreement between sources that decided an item's absence, and the result of the validator.
Every item you read and
deliberately kept off the slides goes here, one line each, so the person handing the file over
knows what the customer is not seeing.

Then add the two closing blocks required by the preamble.
