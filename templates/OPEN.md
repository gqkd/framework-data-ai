---
schema: framework/open-register/v1
artifact_type: open-register
lifecycle: living
status: active
products: [product-a, product-b, product-c]
owners: [NAME]
created: YYYY-MM-DD HH:MM
last_review: YYYY-MM-DD HH:MM
classification: internal
# The two facts a check needs, per entry. The body below is where the reasoning goes: the
# question, the alternatives and what the default costs are what somebody reads while
# deciding, and no field replaces them. `REG002` and `REG003` read this map and nothing else,
# because they used to match the prose and went quiet the first time a label was reworded.
entries:
  OD-001:
    status: open
    cost_to_reverse: high
    default_in_force: none            # `none` is a legitimate value. Absent is not
    trigger: the event after which this can no longer be deferred. Never a date, in
             any form and not even beside the event -- `REG009`
    decide_with: [OD-004]             # entries that have to be decided in one sitting.
                                      # Write it on both of them
    products: [product-a]             # REQUIRED in the register at the root, where nothing
                                      # else answers the question -- `[all]` when it really
                                      # binds every product, including ones not created
                                      # yet, and the names when it binds some. Absence is
                                      # `REG011`: it binds everything by rule, and reads
                                      # exactly like a question nobody asked. In a
                                      # product's own register the directory already said
                                      # it, and naming another product there is `REG008`
  OD-002:
    status: open
    cost_to_reverse: medium
    default_in_force: whatever is already happening today
    depends_on: [OD-001]
  OD-003:
    status: open
    cost_to_reverse: low
    default_in_force: whatever is already happening today
  KI-001:                             # a known issue has no default and no cost to reverse:
    status: open                      # those are properties of a choice, and this is not one
---

# Open decisions and known issues

**What it is for.** It holds everything that is still undecided or knowingly broken. It is
the information no other document in the framework contains: `decisions/` records what has
been *decided*, `ARC` how the system is built, `RSK` what can go wrong. Only this file says
**what has not been chosen yet**. Without it, an agent fills the gap with a plausible
assumption and implements it with conviction.

**It is the only document in the framework that gets shorter.** When a decision is taken,
the entry leaves `§1` and becomes a `DEC-NNN`, leaving one cross-reference line in `§4`. If
the file never gets shorter, you are accumulating instead of deciding.

That is about the **body**. The row in `entries:` stays, moved to `status: decided` with its
`closed_by`, because it is what the `depends_on` of other entries resolve against and
because the front matter is the only part of this file a check can read. Drop the row when
nothing depends on it any more.

**One per product, and the entry lives in the register of the thing it is about.** There
are three placements and one rule:

| The entry is about | It is filed in |
|---|---|
| one product | `products/<p>/OPEN.md` — **mandatory**, one per product. `REG006` |
| the shared substrate | `platform/OPEN.md`, if you decided to have one. See `PLATFORM.md` |
| no single product | `OPEN.md` at the root — including "do we share a substrate at all" |

The reason it is per product and not per repository: this is the file an agent reads before
deciding anything, and an agent working on one product has to find it beside that product.
It is also how you read it yourself. Sitting down to work through what is open on one
product should not mean filtering out three other products first, and a register you have
to filter is a register you skim.

The reason the root still exists: the entries that name no product do not belong to any of
them, and filed per product they end up in whichever register you happened to have open
that day. "Do these products share a substrate" is the clearest case — it cannot live in
`platform/OPEN.md`, because whether that file exists is what the entry is about.

**Scope is read off the directory, not off `products:`.** In `products/<p>/OPEN.md` the
field is left off: the entry is about `p` by virtue of sitting there. An entry that names a
different product is filed under the wrong heading — `REG008` — and one that binds several
belongs at the root, where naming them is what the field is for.

**Numbering is one sequence across all three.** `depends_on` and the `derives_from` of a
`DEC` name an entry by its id and nothing else, so two registers that both start at
`OD-001` make every reference to either one ambiguous, and the ambiguity resolves itself
silently. `REG007` reports it. A register adopted from before the framework continues the
numbering and keeps its old labels in the prose beside the heading — `### OD-033 · (was
K7) Title` — because the id is what a check resolves and the label is what a person
recognises.

**`§5` at the root is generated, and it is the only part of any of these files that is.**
Three registers ordered by cost to reverse do not compose into one ordered list, and
nothing else composes them: without that view there is no such thing as "the most expensive
thing still open", there are three of them and nothing says which comes first.

## How to use it

1. **An agent reads this file before taking any structural decision.** If the choice it
   needs is listed here as open, it does not take it: it raises it.
2. **The `Default in force` field is mandatory.** A decision not taken does not mean the
   absence of behavior: something is already happening, even if that something is
   "nothing". Writing down what it is is the difference between a deliberate deferral and a
   hole.
3. **The cost to reverse drives urgency, not importance.** High-cost entries have to be
   decided even on incomplete information, because the cost of waiting exceeds the cost of
   getting it wrong. Low-cost ones can be deferred as long as you like.
4. **When you decide:** write the `DEC`, replace the entry in `§1` with a cross-reference
   line in `§4`, delete the rest of the prose. In `entries:`, set `status: decided` and
   `closed_by`, and leave the row: deleting it turns every `depends_on` pointing at it into
   a dangling reference, which reads as a typo rather than as a decision taken.

---

# §1 · Open decisions

Grouped by cost to reverse, not by topic: it is the cost that tells you which ones to look
at first. The heading says what changing your mind costs, and nothing about when to decide
-- a tier is a price, and a price has no calendar. When each entry has to be decided is its
own `trigger`, which names an event, and `REG009` and `REG010` report a date written in
either place.

**The heading is navigation, and `cost_to_reverse` on the entry is what anything reads.**
This is the one repetition 3.0.0 left in place, deliberately: the grouping is the reading
order of the document, and the generated `§5` at the root composes the same field across
three registers into the only list that answers "what is the most expensive thing still
open". Removing it would leave this section unordered to close a duplication nobody has ever
got wrong. If the two ever disagree, the field is right.

## Cost to reverse HIGH: changing it later means redoing work that already exists

### OD-001 · Title of the decision, in the form of a choice

- **Question:** the actual choice, phrased as a question with at least two answers.
- **The problem the default introduces:** why leaving it open costs something. The default
  itself is a field in `entries:` above, not a line here: when nothing really is happening
  it is `none`, and together with a high cost that is the most expensive combination there
  is, which the validator flags for you.
- **Leaning:** the direction we lean toward, and why. Optional, and it is not a decision:
  it is there so you do not start the reasoning over from scratch in two weeks.
- **What the alternatives cost:** the comparison somebody will want in two weeks, and the
  one thing no field can hold.

**`trigger`, `depends_on` and `decide_with` are fields of the entry above and are not
bullets here.** They were both until 3.0.0, which is the same duplication `default_in_force`
was pulled out of one version earlier and for the same reason: the checks read the map, so a
bullet rewritten or translated changed nothing and looked like it had. `REG009` reads
`trigger`, `REG005` resolves `depends_on` and `decide_with`, and this section is where the
reasoning lives -- the question, the leaning, and what the alternatives cost.

## Cost to reverse MEDIUM: changing it later costs a migration, not a rewrite

### OD-002 · Title

- **Question:**
- **The problem the default introduces:**

## Cost to reverse LOW: changing it later costs an afternoon

### OD-003 · Title

- **Question:**

---

# §2 · Accepted known issues

Real problems we have chosen not to fix now. **Every entry has a trigger that reopens it:**
without a trigger it is not an accepted problem, it is a forgotten one.

### KI-001 · Title

- What is broken or missing, in one line.
- Why we accept it for now.
- Who or what bears the effect.
- **Reopening trigger:** the observable condition that makes fixing it necessary.
- **Reference:** whatever records that it was dealt with. A `CHG`, a `DEC` or a `SIG` when
  there is one; a commit, or a line of `LOG.md`, when the thing was a file operation and
  there was never a decision to write. `closed_by` on a `KI` is free text and no check
  resolves it -- on an `OD-` it must name an accepted `DEC` and `REG005` says so, because a
  decision that cannot be reached is a decision nobody can revisit. A known issue is not a
  choice, and demanding a decision record for having deleted two files is how a rule gets
  worked around instead of followed.

---

# §3 · Parking lot

Ideas and questions that have surfaced and are not yet qualified. They are not open
decisions: they are things to look at. One line each, no format. If one sits here for three
months without anyone touching it, delete it. A parking lot that never empties is a second
backlog nobody reads.

---

# §4 · Closed decisions

One line per closed entry, with the date and the `DEC` that closed it. Do not copy the
content across: it lives in the `DEC`.

- **YYYY-MM-DD · OD-NNN** → [`DEC-NNN`](decisions/DEC-NNN-slug.md) · one line on what was
  decided. If the decision closed the entry only in part, say so here and open the
  remaining part as a new entry in `§1`, with a new number.

---

# §5 · Everything open, by product

**Only in the register at the root, and only between the markers.** Delete this whole
section from a product's register and from the substrate's: it is the composition, and a
composition inside one of the things being composed is a second copy that goes stale.

Written by `validate.py --emit-index`. The markers are the boundary and they are also the
permission: everything outside them is yours, and a file that does not carry them is not
written to at all. Do not edit between them — the next run overwrites it, and the last
column of every row says which register owns the entry.

It holds no `entries:` of its own, and that is deliberate rather than an omission. A second
copy of a row is a second thing for `REG002`, `REG003` and `REG005` to report, and two rows
with the same id for a `depends_on` to resolve against.

<!-- generated: open-union -->
Run `validate.py --emit-index` to fill this in.
<!-- /generated -->

---

## Anti-patterns

- **Omitting `Default in force`.** This is the error that makes the whole file useless.
  "Not decided" sounds like "nothing is happening", and instead something is already
  happening: usually the implicit choice made by whoever wrote the first piece of code.
- **Using the cost to reverse to say how important the decision is.** They are different
  things. A choice that matters little but is expensive to overturn has to be decided
  before an important, reversible one.
- **Leaving the entry in `§1` after writing the `DEC`.** The register then says that
  something is open which is closed, and an agent will stop to ask permission for a
  decision already taken. The validator catches it, but only if the `DEC` declares it in
  `derives_from`.
- **Putting an `OD-NNN` into the `derives_from` of a `DEC` that does not close it.** A
  `DEC` names an open entry for three different reasons (it closes it, it depends on it, or
  it opens a narrower one) and `derives_from` means the first. For the other two, the
  cross-reference goes in prose.
- **Recording risks here.** A risk is something that can go wrong and it belongs in `RSK`;
  an open decision is something that has to be chosen. If the entry does not have at least
  two possible answers, it does not belong in this file.
- **Letting it grow.** A register that gets longer at every session and never gets shorter
  is not a decision register: it is the proof that no decisions are being taken.
- **Restarting the numbering in each register.** It is the one thing that looks tidier and
  breaks the references. Three `OD-001` make every `depends_on` naming one of them
  ambiguous, and nothing raises its voice: whichever file was read last wins.
- **Editing `§5` instead of the register it names.** The edit survives until the next
  `--emit-index` and disappears without anybody being told, which is worse than not having
  made it. The last column exists so there is never a reason to.
