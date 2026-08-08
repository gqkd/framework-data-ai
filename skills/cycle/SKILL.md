---
name: cycle
description: >
  Open a development cycle: take the signals and roadmap increments that are candidates,
  classify their impact through the ICG gate, reshape the product and architecture where
  the classification says to, write the change contracts that authorize the work, plan the
  cycle, and produce a brief per change that a coding agent can execute. Use when deciding
  what to build next and when authorizing work. Triggers on "cosa facciamo in questo ciclo",
  "cosa costruiamo adesso", "apriamo un ciclo", "prossimo sprint", "devo aggiungere",
  "apriamo un change", "pianifica il ciclo", "dammi i task per gli agenti", "what do we
  build next", "open a change", "plan this cycle", "give me the agent tasks". Use it
  whenever work is about to start on something that is not already an approved CHG.
---

# cycle

Read `references/preamble.md`, which sits at `${CLAUDE_PLUGIN_ROOT}`, first.

This skill implements the stretch of the loop that is easy to run in the wrong order:
**intake → triage → `ICG` → reshaping → `CHG` → `IMP` → briefs.** The plan comes *after* the
reshaping, not before. If you write the plan first and the reshaping then changes the scope,
the plan is already obsolete and everyone keeps reading it.

## Step 1 · Intake

Gather the candidates. Three documents hold them:

- **`LOG.md`** — signals: incidents, drift, feedback, requests, metrics, compliance.
- **`RMP.md`** — the increments already hypothesised, with the evidence each depends on.
- **`ARC#delta`**, once the architecture has a target: the structural increments that
  separate what is built from where it is going. `#delta` says *what* is missing, `RMP` says
  in what order and on what evidence. If a delta row has no corresponding `RMP` entry, that
  is worth surfacing: it means something structural is missing from the plan.

And a fourth source that is not a document: **the user, in the conversation that opened the
cycle.** "We also need to upgrade pandas" is a candidate and it is nowhere in `LOG.md`.
Take it, and before classifying it write it where it belongs, because a candidate that
exists only in a chat window is one nobody can audit afterwards: a request or an incident
is a `SIG` appended to `LOG.md`, an increment is an `RMP` row. Appending a `SIG` is one of
the two things the preamble lets you do without asking.

A signal is a candidate, not a mandate. Nothing here is authorized yet.

`LOG.md` records no triage state, and being append-only it could not carry one, so nothing
distinguishes a signal already worked from one nobody has read. Until it does, say which
signals you took and from what point, rather than implying the log was swept.

## Step 2 · Triage and the `ICG`

For each candidate, classify the impact. Read `PBR`, `ARC`, the relevant `DC`, `EVP` and
`RSK` before proposing a classification: the question "does it touch the architecture" is
too narrow, because a change can leave the architecture untouched and still invalidate an
outcome, a price, a data contract or the risk profile.

Read `COMMITMENTS.md` and the accepted `DEC` records too. They are where the hardest calls
are settled and neither is visible from the five above. A candidate that contradicts a
signed commitment is not a change to classify, and a candidate that contradicts an accepted
decision needs a `DEC` that supersedes rather than a `CHG` — an agent reading only `ARC`
would file it as a routine increment and never see either.

When a candidate contradicts something already written, that is a conflict, and
`references/routing-table.md` §4 says what to do with one: show both versions with their
provenance and ask which holds. Do not resolve it inside the classification.

| Outcome | Path |
|---|---|
| No structural impact | technical `CHG`, straight to `IMP` |
| Product impact | product reshaping → `PBR`, `WF` |
| Architecture impact | architecture reshaping → `ARC`, `DEC` |
| Both | joint reshaping |
| Solution hypothesis invalidated | re-entry into F3. **Not** a `CHG` |
| Problem or segment invalidated | re-entry into F2. **Not** a `CHG` |

**Propose the classification, do not decide it.** An `ICG` decided automatically is a gate
that does not exist. The last two rows especially: if the hypothesis is invalidated, the
honest outcome is that this is not a change, it is discovery starting again, and saying so
is more valuable than producing a change contract that pretends otherwise.

## Step 3 · Reshaping, before the plan

Where the classification says to reshape, update the documents first: `PBR` `WF` `ARC`
`EVP` `DC` `RSK` `DEC` `RMP`, whichever apply. This is the same document set F4 produces,
because reshaping and initial shaping are the same operation at different times.

If the reshaping requires a decision nobody has taken, stop and hand off to `resolve`. Do
not decide it here to keep the cycle moving.

## Step 4 · The change contract

One `CHG` per authorized change. Three sections are mandatory and the middle one is the
reason this document exists:

**What changes.** The mandate, concretely.

**What must NOT change.** The most valuable thing in the framework, and the one a person
writes worst. You can read `ARC`, the `DC` and `EVP` and find the contracts this change
risks breaking that nobody has named: consumers of a dataset whose schema is about to move,
a threshold that will drift, a boundary another product depends on. Fill it from those
documents, then ask the user what else.

**How we know it worked.** The acceptance criterion, in terms that can be checked. Not "it
works" but what is observed, measured or asserted.

A `CHG` starts at `status: draft` and becomes `approved` when the user approves it. Only an
approved one authorizes anything.

## Step 5 · The cycle plan

`IMP` says how the approved contracts get executed this cycle. It is living and replaced
each cycle, and it is an output of the reshaping, never an input. Include what is
**excluded** this cycle: a plan that lists only what is in is one somebody will read as
open-ended.

## Step 6 · The agent brief

For each approved `CHG`, produce the brief that lets a coding agent execute it without
inventing anything. Everything in it already exists: the brief assembles, it does not
compose.

```
Mandate            CHG-NNN §what-changes
Guardrails         CHG-NNN §what-must-not-change
                   OPEN.md, the decisions it may not take
Context            AGENTS.md authoritative sources, resolved for this product
                   ARC#current, the relevant DC, GLOSSARY
Done when          CHG-NNN §how-we-know-it-worked
                   the artifacts in AGENTS.md "mandatory updates" are updated
                   the validator passes with no errors
                   a new EVR, if an AI component was touched
```

Two levels of evaluation exist and merging them is a costly mistake. **Task acceptance** is
`CHG §how-we-know-it-worked` plus the validator plus the project's tests: did this change
get done correctly. **Product evaluation** is `EVR` against `EVP` at the release gate: is
the product good enough to ship. An agent that thinks passing the model eval means the task
is done, or a release gate that fires on every micro-task, is the result of collapsing them.
They meet at exactly one point, already written in `AGENTS.md`: touching an AI component
requires a new `EVR`.

## What you must not do

**Do not authorize what was not classified.** A `CHG` with no `ICG` behind it is a change
whose blast radius nobody assessed.

**Do not write a `CHG` for an invalidated hypothesis.** That routing means re-entry into
discovery. Producing a change contract instead is how a product keeps getting built on a
premise that was already disproved.

**Do not leave "what must NOT change" thin because it is hard.** It is the section that
stops an agent from optimising what you asked for and breaking what you did not name, and
it is the most expensive gap in the framework.
