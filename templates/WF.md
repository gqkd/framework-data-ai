---
schema: framework/workflow/v1
artifact_type: workflow
lifecycle: living
status: active
version: 1.0.0
products: [product-a]
owners: [NAME]
created: YYYY-MM-DD HH:MM
last_review: YYYY-MM-DD HH:MM
derives_from: [PRB-NNN]
classification: internal
---

# Workflow: Process name

**Question:** how does the process work today, how will it work, and what exactly changes?

**One file, three sections.** The target only makes sense set against the current state,
and the value is in the delta: separate files would produce two diagrams that diverge. For
precise references use the anchors: `WF.md#target`.

---

<!-- section: current -->
# §current

How it **really** works today, shortcuts included.

## Steps

| # | Who | What they do | Systems and files touched | Where the data originates |
|---|---|---|---|---|
| 1 | | | real names: which table, which Excel file, which folder | created / copied |

The systems column wants the **real names**. It is the data → system map, and for an agent
it is the only source that tells it where a piece of information lives.

## Pain points

Numbered, each with a pointer to the evidence in `EVD` that documents it.

## Existing workarounds

The shadow Excel files, the copy-paste, the chat messages. They are the most informative
part of the document, not the embarrassment to leave out: a workaround is a requirement
somebody has already implemented by hand.

---

<!-- section: target -->
# §target

## Steps

The same table as the current state, in target form.

## What stays manual, and why

Mandatory section. A deliberate choice, not an omission. In AI systems *where the human
sits* is one of the most expensive decisions to change later: point to the `DEC` that
fixes it.

## Impact on roles

Who, from tomorrow, does something different. Who loses a piece of work. Who gains one.

## Requirements that follow from it

---

<!-- section: delta -->
# §delta

Step by step: what disappears, what appears, what only changes actor. It can be generated,
but keeping it explicit is useful because it is what gets read in a review.

---

## Anti-patterns

- **Describing the official process instead of the real one.** If §current looks tidy, you
  did not observe it: you asked the person who designed it.
- **Generic systems.** "The CRM" is no use to anyone. What is needed is which table.
- **No rows in "what stays manual".** It means you are promising total automation, and it
  is not true.
- **Updating §target without updating §delta.** The delta becomes a silent lie, which is
  worse than no delta at all.
