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

`LOG.md` records no triage state and, being append-only, could never carry one: a row
cannot be marked handled. So the state lives in the `ICG`, and every signal you read goes
into its `routing` even when it goes nowhere, as `not-a-candidate`. That is the only thing
separating a signal nobody has read from one somebody read and set aside, and `ICG001`
reports the first. Leave a signal out because it was obviously nothing and every cycle from
now on will read it again.

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

**Signed, and still standing.** Read the row before you stop on it. What stops a
classification is a promise still standing: issued, and not written off. `not-yet-issued`
was said to nobody; `renegotiated` and `met` are closed conversations; and a row that is
`unsatisfiable` or whose `feasibility` is `out-of-reach` is a promise this project has
already judged it will not deliver — owed a conversation with whoever received it, and not
a boundary on the build, because stopping the candidate does not make the promise possible.
Cite it in the `ICG` with the risk that owns the exposure and classify the candidate; where
no risk owns it, `XP007` reports that, and it is a finding about responsibility rather than
a reason to stop. The share of commercial promises that were never buildable is small and it
is never zero, and a triage that treats each of them as binding stops the same candidates
every cycle, on a call that has to be made once.

When a candidate contradicts something already written, that is a conflict, and
`references/routing-table.md` §4 says what to do with one: show both versions with their
provenance and ask which holds. Do not resolve it inside the classification.

The classification has two halves and they are not the same question. **Routing** is where
the candidate goes, and there is one answer per candidate. **Impacts** are what it touches
on the way, and one candidate can touch several.

| `routing` | Path |
|---|---|
| `none` | no structural impact: technical `CHG`, straight to `IMP` |
| `product` | product reshaping → `PBR`, `WF` |
| `architecture` | architecture reshaping → `ARC`, `DEC` |
| `both` | joint reshaping |
| `hypothesis-invalidated` | re-entry into F3. **Not** a `CHG` |
| `problem-invalidated` | re-entry into F2. **Not** a `CHG` |
| `not-classifiable` | the evidence to decide does not exist yet |
| `not-a-candidate` | looked at, and it is not a change proposal at all |

| `impacts` | What it obliges |
|---|---|
| `architecture` | an updated `ARC` **and** a `DEC` |
| `data` | a `DC` version bump and notice to its consumers |
| `ai` | a new `EVR` |
| `risk-compliance` | a line in `RSK §state` |

A data contract breaking with no product and no architecture movement routes `none` and
carries `data`. Filing it as an architecture change because that was the closest available
word is how the obligation attached to it gets lost.

`not-classifiable` is the honest answer to the most common thing at triage: a candidate
nobody has measured. Three people saying a number feels wrong is not an invalidated
hypothesis, and it is not a bug either. Say what measurement would settle it and route it
there. Forcing it into one of the other rows either closes a real signal or tears up a
working product.

**Write the `ICG`.** One per cycle, at `products/<p>/cycles/ICG-NNN.md`, from
`templates/ICG.md`. It carries `routing` and `impacts` in its front matter, keyed by
candidate, plus what was considered and what is unresolved. This is what makes the gate a
gate: before it existed the classification survived only inside the `CHG` documents that
came out of it, so a candidate routed back into discovery, and every triage a user stopped
after reading, left nothing behind at all.

**Propose the classification, do not decide it.** The `ICG` is written `status: proposed`
and becomes `accepted` when the user says so. A gate crossed automatically is a gate that
does not exist. The two invalidation rows especially: if the hypothesis is invalidated, the
honest outcome is that this is not a change, it is discovery starting again, and saying so
is more valuable than producing a change contract that pretends otherwise.

## Step 3 · Reshaping, before the plan

Where the classification says to reshape, update the documents first: `PBR` `WF` `ARC`
`EVP` `DC` `RSK` `DEC` `RMP`, whichever apply. This is the same document set F4 produces,
because reshaping and initial shaping are the same operation at different times.

If the reshaping requires a decision nobody has taken, stop and hand off to `resolve`. Do
not decide it here to keep the cycle moving.

## Step 4 · The change contract

One `CHG` per authorized change, and each one names the `ICG` it came from in its `icg`
field. That link is the whole reason the routing is a field: it is what lets a check ask
whether a change declaring an AI impact cites an `EVR`, instead of a person remembering to.

Three sections are mandatory and the middle one is the reason this document exists:

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
                   products/<p>/OPEN.md and platform/OPEN.md, the decisions it may not take
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

## Handing back

Say what was classified and how each candidate was routed, including the ones routed
`not-a-candidate` and the ones that came back `not-classifiable` with the measurement that
would settle them. Then which documents the reshaping moved, which `CHG` are `approved` and
which are still `draft` waiting on the user, and what is excluded from this cycle. Then run
the validator.

**Then the two closing blocks the preamble describes, and they go last:** what changed in
plain words, one line per file, and what to do next with what each option buys and costs. The
first row is normally handing a brief to a coding agent, and it is only a row for a `CHG` the
user has actually approved: a `draft` in that position is this skill authorizing its own work.
A candidate routed back into discovery belongs in the table too, and its cost is the honest
one — building on a premise that was just disproved is more expensive than the re-entry.
