---
name: requirement
description: >
  Bring new information into the Data & AI documentation framework: a functional
  requirement, a decision taken, a definition, a commitment, a constraint, a customer
  request, an incident, or a correction of something already written. Classifies it, writes
  it into its one authoritative document, propagates the linked updates, and flags
  contradictions with what is already there. Use whenever the user states something worth
  recording, even when they name no file at all. Triggers on "abbiamo deciso", "il cliente
  vuole", "hanno chiesto", "aggiungi che", "registra che", "un cliente attivo è", "in realtà
  il dato arriva ogni ora", "non possiamo far uscire i dati dall'UE", "serve anche che",
  "requisito", "aggiungi questo requisito", "we decided", "the customer wants", "add that",
  "record that", "actually it works like this", "new requirement". Use it also when the user
  asks to update the documentation after a conversation, or to fix the files because
  something changed.
---

# requirement

Read `references/preamble.md`, which sits at `${CLAUDE_PLUGIN_ROOT}`, first, then
`references/routing-table.md`, which holds the classification, the cascade and the conflict
rules. Read it every time. Do not work from memory of it and do not restate it here: it is
the file that keeps this skill and `start` writing to the same places.

The name says "requirement" because that is what you will mostly be feeding it early on.
The operation is wider: **information comes in, gets classified, gets written to its one
authoritative source, and everything that must change with it changes in the same pass.**
A requirement, a decision, a definition and an incident are the same operation with
different destinations.

## The three ideas that make this work

**Classify on epistemic strength, not on subject.** "The system processes 10M rows a day"
can mean *we promised it*, *we believe it will be needed*, or *we measured it*. Three
things with the same shape and three different destinations. When the context does not tell
them apart, ask. It is the question that pays best.

**The cascade is the point of the skill.** Writing to one file is easy. Writing to the right
four is why this exists. A `DEC` with `scope: architecture` forces `ARC` in the same pass; a
glossary entry for a term that is also a field of a `DC` forces that contract to bump; a
commitment out of technical reach opens a row in `RSK` and an entry in `OPEN`. The cascade
table in the routing table is not advisory.

**Autonomy shrinks as the cascade widens.** One append-only destination with no ambiguity:
write it. More than one file, an immutable involved, a conflict detected, an ambiguous
classification: propose and wait. The cascade is exactly where an agent's confidence exceeds
its accuracy.

## Where functional requirements actually go

This framework has no requirements specification, deliberately: `FRAMEWORK.md §1` lists it
among the documents it refuses to have. That is not an omission to work around. A
requirement is never one kind of thing, and collecting them in one list is what makes them
unmaintainable. Route by what the requirement *is*:

| The requirement is really… | It goes to |
|---|---|
| something promised to a customer | `COMMITMENTS.md`, plus the technical constraint it implies |
| a behaviour of the product | `PBR.md` capability, and `WF.md#target` for the process |
| a guarantee about data | the relevant `DC`, in its **guarantees**, not only its schema |
| a quality threshold | `EVP.md`, and `COMMITMENTS` too if it was promised |
| a structural property of the system | `ARC.md#target`, and `#delta` if it is not there yet |
| a thing we must not do | `PBR` out of scope, or `RSK#state` if it is a constraint |
| something nobody has decided | `OPEN.md` as an `OD`, with its cost to reverse |

If a statement does not fit any row, that is information: it is probably reasoning rather
than a requirement, and it belongs in the parking lot or nowhere.

## Discrepancies

Finding a contradiction is the most valuable thing this skill does, and it is worth more
than the write it was asked for. Before writing, check the six places conflicts hide, listed
in the routing table §4: data guarantees, definitions, commitments, decisions, out of scope,
and open decisions.

Where the contradiction gets recorded depends on where it came from:

- **Between two corpus documents** → `ING.md#contradictions`, with both sources.
- **Between new information and an existing document** → stop and show both versions with
  their provenance. If the user resolves it, write the resolution. If they cannot resolve it
  now, it becomes an `OD` in `OPEN.md`: an unresolved contradiction is an open decision, and
  leaving it only in the chat means it will be rediscovered by an incident.
- **Against an `accepted` `DEC`** → this is not new information. It is a change of decision,
  and it needs a new `DEC` that supersedes the old one. Say that out loud rather than
  quietly editing.

Do not resolve a conflict by taking the more recent statement. In a business corpus the
most recent document is often the sales deck, which is the least reliable one about facts.

## Do not record sentence by sentence

A conversation is largely reasoning out loud. Filing every claim produces a log of noise in
which the real facts become unfindable, and since that log is what an agent works from, the
damage spreads. Track what looks recordable and present the sweep when the conversation
reaches a resting point, in the form shown in the routing table §6.

Two things are written immediately without waiting for the sweep: an **incident**, because
its value depends on the exact time, and a commitment that has just turned out to be **out
of technical reach**, because it is the most urgent thing in the project the moment it
surfaces.

## What you must not do

**Do not turn a request into a mandate.** "The customer wants Excel export" is a `SIG` in
`LOG`, and at most a conditional increment in `RMP`. It does not become a `CHG` and does not
get built. That path runs through intake, triage and the `ICG`, which is the `cycle` skill.
Skipping it is how a product becomes the sum of the last things anyone asked for.

**Do not close an `OPEN.md` entry as a side effect.** If the information you were given
happens to settle an open question, say so and let the user decide. Closing it is a
decision, and it belongs to `resolve`.

**Do not edit an immutable to correct it.** A `PRB` that turned out wrong still records what
we believed then, and that is the only thing that makes it reconstructible why a decision
looked sensible. Write a new one that supersedes it.

## Handing back

Say where each thing went and why that destination, what the cascade obliged beyond the file
you were asked about, **what you found that contradicts something already written**, and what
you deliberately did not record. Then run the validator: the cascade is where a write goes
wrong, and it is what notices that a `DEC` moved and its `ARC` did not.

**Then the two closing blocks the preamble describes, and they go last:** what changed in
plain words, one line per file, and what to do next with what each option buys and costs. The
rows are derived — a conflict you could not resolve is an `OPEN.md` entry somebody has to
work, a statement that would close an open entry is `resolve`'s to take, and a request filed
as a `SIG` is not authorized to be built until a cycle classifies it. If the whole write was
one appended `SIG`, one row is the correct length.
