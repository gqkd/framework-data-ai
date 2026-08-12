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
# deciding, and no field replaces them. `OD002` and `OD003` read this map and nothing else,
# because they used to match the prose and went quiet the first time a label was reworded.
entries:
  OD-001:
    status: open
    cost_to_reverse: high
    default_in_force: none
    deadline: YYYY-MM-DD
  OD-002:
    status: open
    cost_to_reverse: medium
    default_in_force: whatever is already happening today
    depends_on: OD-001
  OD-003:
    status: open
    cost_to_reverse: low
    default_in_force: whatever is already happening today
  KI-001:
    status: open
    cost_to_reverse: low
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

**One per repository, at the root.** If a product needs its own technical register (because
it already had one before adopting the framework, or because its entries are too many and
too specific) it can live in `products/<p>/OPEN.md`, but then `AGENTS.md` must say
explicitly which of the two answers which question. Two registers without that line are two
registers that diverge.

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
4. **When you decide:** write the `DEC`, replace the entry with a cross-reference line in
   `§4`, delete the rest.

---

# §1 · Open decisions

Grouped by cost to reverse, not by topic: it is the cost that tells you which ones to look
at first.

## Cost to reverse HIGH: decide before the first line of code

### OD-001 · Title of the decision, in the form of a choice

- **Question:** the actual choice, phrased as a question with at least two answers.
- **The problem the default introduces:** why leaving it open costs something. The default
  itself is a field in `entries:` above, not a line here: when nothing really is happening
  it is `none`, and together with a high cost that is the most expensive combination there
  is, which the validator flags for you.
- **Depends on:** other `OD-NNN` entries that have to be decided first, if there are any.
- **Leaning:** the direction we lean toward, and why. Optional, and it is not a decision:
  it is there so you do not start the reasoning over from scratch in two weeks.
- **Deadline:** a date, or an observable event.

## Cost to reverse MEDIUM: decide within the first month

### OD-002 · Title

- **Question:**
- **The problem the default introduces:**
- **Deadline:**

## Cost to reverse LOW: defer them as long as you like

### OD-003 · Title

- **Question:**
- **Trigger:** the condition that makes it urgent. On a low-cost entry the trigger replaces
  the deadline: there is no date by which to decide it, there is an event after which it
  can no longer be deferred.

---

# §2 · Accepted known issues

Real problems we have chosen not to fix now. **Every entry has a trigger that reopens it:**
without a trigger it is not an accepted problem, it is a forgotten one.

### KI-001 · Title

- What is broken or missing, in one line.
- Why we accept it for now.
- Who or what bears the effect.
- **Reopening trigger:** the observable condition that makes fixing it necessary.
- **Reference:** the linked `CHG` / `DEC` / `SIG`.

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
