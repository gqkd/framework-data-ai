---
name: resolve
description: >
  Work through the open decisions in OPEN.md, in cost-to-reverse order, and close them: one
  decision at a time, each producing a DEC and the document updates that follow from it.
  This is also how the product and its architecture get defined for the first time, because
  at that stage almost everything worth writing is blocked by a decision nobody has taken.
  Use at the start of real work on a project, and any time the open register has grown.
  Triggers on "risolviamo gli open", "cosa devo decidere", "quali decisioni sono aperte",
  "sblocchiamo il progetto", "definiamo il prodotto", "definiamo l'architettura", "cosa
  mettiamo nell'MVP", "qual è la MVA", "let's resolve the open decisions", "what do I need
  to decide", "let's define the product", "what goes in the MVP".
---

# resolve

Read `references/preamble.md` at the plugin root first, and
`references/routing-table.md` for the cascade each decision triggers.

`OPEN.md` is the work queue and it is already ordered. §1 groups entries by cost to reverse:
HIGH decide before the first line of code, MEDIUM within the first month, LOW defer as long
as you like. You do not need to invent a priority.

## The order to work in

1. **Anything the validator reports as `OD003`** — high cost to reverse *and* no default in
   force. This is the most expensive combination there is, and it has to be decided even on
   incomplete information, because the cost of waiting exceeds the cost of being wrong.
2. **§1 HIGH**, in the order the register lists them, respecting `Depends on`.
3. **§1 MEDIUM.**
4. **§1 LOW** only if the user asks. Deferring these is the correct behaviour, not
   procrastination.

Run the validator first to get the `OD003` list rather than reading the file and judging by
eye.

## One decision at a time

For each entry, in this shape:

**Restate the choice.** In the form of a choice, not a topic: not "authentication" but "one
identity provider for all products, or one per product". If the entry is not phrased as a
choice, it is not decidable, and rewriting it is the first thing to do.

**Say what is happening today.** `Default in force` is the field the template calls the one
whose absence makes the whole file useless. A decision not taken does not mean nothing is
happening: something is happening by default, and often the default is the decision nobody
noticed making.

**Give the cost to reverse, concretely.** Not "high" but what it would take: a migration, a
renegotiation, a rewrite of two components. This is what makes the user able to decide fast
on thin information, which is the whole point of the register.

**Lay out the options with what each one forecloses.** Two or three, not seven. For each,
the thing it makes impossible later, because that is the part that is invisible at decision
time and expensive afterwards.

**Ask. Do not decide.** This is the rule the framework exists to enforce: an agent that
fills an open decision with a plausible assumption and implements it with conviction is the
single most damaging thing in a documented repository. If the user says "you choose", the
correct answer is a recommendation with its reason, still asked as a question.

**If the information is missing**, say what would settle it and how expensive it is to get.
Sometimes the honest outcome is that the entry stays open with a smaller question attached
to it.

## When a decision is taken

Every closed entry produces a `DEC` and a cascade. Propose the whole set as a table before
writing any of it, in the form the preamble describes.

The `DEC` carries `derives_from: [OD-NNN]`. This is not decoration: it is what the validator
uses to notice the entry is still listed as open, and it is what makes the register
self-checking.

| `scope` | The decision is about | And you must also update |
|---|---|---|
| `product` | what we build, for whom, with what priority | `PBR`, and `RMP` if it moves an increment |
| `architecture` | how the system is built | `ARC#current` if it is already built, `#target` if it moves the destination, `#delta` either way |
| `platform` | what constrains every product | every product listed in `products`, and `PLATFORM.md` if one exists |

Then the entry **moves** from `OPEN.md` §1 to §4 with a cross reference to the `DEC`. It
does not get deleted. An entry deleted outright takes with it the fact that the question was
ever asked, and the next person re-derives it from scratch.

## Defining the product for the first time

At the beginning, most of what has to be written is blocked by an open decision, which is
why this skill is also how Block B gets shaped. Working the register produces the decisions;
the cascade produces the documents.

Two things are **not** decisions and will not fall out of the register. Write them
explicitly, and say you are doing it:

- **`PBR`** — what the product is, for whom, what outcome it produces. It comes from the
  corpus and from the user, not from a choice between options.
- **`EVP`** — the thresholds that say when quality is good enough. Designing them is an act
  of writing, not a decision between alternatives. Do not invent numbers: a threshold nobody
  argued over will be quietly lowered the first time it fails.

And one distinction to keep sharp while you work, because it is the most consequential thing
in the architecture:

> **`ARC#current` is what is built. `ARC#target` is where it is going. The MVA is what
> `#current` is at the end of the MVP.** The target is not the MVA plus more: an MVA
> legitimately contains things the target discards, because it was built to be sufficient
> now rather than to be the destination. When a decision is "for now", say which of the two
> it belongs to.

## Handing back

Say what got decided, what got written, what moved to §4, and **what is still open and
why**. An entry left open on purpose, with the reason and what would settle it, is a good
outcome. A register emptied in one session usually means somebody decided things that were
not theirs to decide.

Close by running the validator. If `OD002` fires, an entry you closed did not move to §4.
