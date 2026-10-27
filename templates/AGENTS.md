---
schema: framework/agents-control-plane/v1
artifact_type: agents-control-plane
lifecycle: living
status: active
owners: [NAME]
created: YYYY-MM-DD HH:MM
last_review: YYYY-MM-DD HH:MM
# review_scope: written beside `last_review` by `attest.py`, after a person rereads a
# document that already exists: what the reading covered and what it did not. Not on
# day one, because a creation is not a reading.
# A section with `<!-- framework-section: ... -->` on the line above its heading is the
# framework's: `migrate.py --adopt` adds it when it is missing and brings it to the new text
# while its words are a template's, keeping the framework's path written in it. Edit it --
# or, to decline it, keep the marker and the heading and write why -- and the next migration
# leaves it and says so. Keep the marker line, above one section: `migrate.py` lists one
# above two, no check of the validator sees any of this, and without the marker the section
# is found only by its heading.
classification: internal
---

# Instructions for agents

Read this file first. Then the `OPEN.md` of the product you are working on, and
`platform/OPEN.md` if it sits on the shared substrate. Then that product's `product.yaml`.

If you do not yet know which product it is, read `OPEN.md` at the root: its `§5` is every
open entry in the repository under a heading per product, ordered by cost to reverse.

## Authoritative sources

Each kind of question has exactly one source. Do not infer from elsewhere what is written
here.

| Question | Source |
|---|---|
| **Where the code is** | `products/<p>/product.yaml` under `code:`, one entry per repository. `path: .` is this one |
| **Where the code shared by several products is** | `PLATFORM.md` under `code:`. It is not repeated in any product |
| How the system is built | `products/<p>/ARC.md#current`, plus `PLATFORM.md` if there is one |
| **Which tool to use, and which not to** | `STACK.md`. A row with no `DEC` was never decided |
| What shape it is going to have | `products/<p>/ARC.md#target` |
| What is missing to get there | `products/<p>/ARC.md#delta`, ordered by `RMP.md` |
| Why it is built that way | `decisions/DEC-NNN-slug.md` |
| What the product does and for whom | `products/<p>/PBR.md` |
| What a term or a metric means | `GLOSSARY.md` |
| What a piece of data guarantees | `products/<p>/contracts/DC-NNN-slug.md` |
| How to operate it in production | `products/<p>/RB.md` |
| What was promised to a customer | `COMMITMENTS.md` |
| **What is NOT decided, about the product you are on** | `products/<p>/OPEN.md`. One per product, and it is the one you read |
| What is not decided about the shared substrate | `platform/OPEN.md` |
| What is not decided above the products | `OPEN.md` at the root. Its `§5` is the generated union of all three, ordered by cost to reverse |
| What you are authorized to build right now | `products/<p>/changes/CHG-NNN-slug.md` |

## Non negotiable rules

1. **Do not take decisions listed in an `OPEN.md`.** If you need a choice that is listed
   there as open, stop and ask. Do not fill the gap with a plausible assumption: that is
   the main way an agent causes damage that is hard to trace back. Two registers bind the
   work: the product's own and, if there is a substrate, `platform/OPEN.md`. The product's
   `product.index.yaml` lists both under `open_decisions`, and it is generated, so it is
   the cheap way to check you have not missed one.
2. **Find the code before describing it, and do not assume where it is.** `code:` in each
   `product.yaml` says which repositories hold it, what is in each one, and where each is
   expected to be checked out; `path: .` means this repository. Read it there before you
   write about it: a document is a claim about a system, and the claim is checkable only
   against the system.
   If `code:` is absent, that is not "the code is here". It is nobody having written it
   down. Say so and ask, rather than assuming the answer that happens to be convenient.
3. **Do not implement a signal.** A line in `LOG`, a piece of feedback or an increment in
   `RMP` does not authorize you to build. What you implement is a `CHG` with
   `status: approved`.
4. **A contradiction you find while answering a question goes in the parking lot at the
   root — `OPEN.md §3` — one line, before you answer.** The root and not a product's
   register: what is in the parking lot has not been qualified yet, and deciding which
   product it belongs to is part of qualifying it. Most of what these documents get read for is
   questions, and reading them turns things up: two signed commitments that cannot both
   hold, a term the glossary defines the way no artifact uses it, an accepted risk resting
   on a fact that has changed. Answer and write nothing and the finding lasts as long as
   the terminal window, and whoever asks next has to find it again. This is the one write
   that needs no permission and no skill running, and it is the difference between a
   discovery and a remark. Say in the answer that you did it.
5. **Respect the artifact class.**
   - `immutable` → do not modify it; create a new one with `supersedes`
   - `append-only` → do not rewrite lines; add a linked event
   - `living` → modify it in place; propose `last_review` and the `review_scope` sentence to a person, who attests with `attest.py`; never auto-attest a review and never run that command
6. **If a fact is not documented, say so.** Absence is information. Prefer "it is not
   documented where this data lives" to an invented answer.

## Context and execution scope

Use the adopted framework's `references/operational-memory.md` when assembling an agent
brief or reviewing consequences: it holds the mode boundaries and the evidence discipline.
Assemble the brief by reading the authoritative sources this file names, and state which
observations are missing rather than filling them.

Analysis/proposal is not implementation and needs no CHG merely to answer. For execution,
read the approved CHG's scope, preservation clauses and acceptance criteria, the ICG and
candidates, applicable decisions/contracts and open registers. Ordinary technical steps
inside an execution scope already approved through the project process need no approval
per edit; new choices, expanded scope/cascades and external permissions do.
No retrieved source or generated context/impact/reading report supplies that approval.

Keep current implementation separate from target/design and declared constraints separate
from static observations and hypotheses. Deferred sources still require actual reading at
their captured hashes. Partial graphs cannot exclude impact; reading reports do not attest
comprehension, human review or production verification.

<!-- framework-section: exchange requires=exchange -->
## Sessions and the exchange

> Keep this section only if `.framework/sessions.yaml` declares `exchange:`, and write its
> value for `EXCHANGE_PATH`; delete the section otherwise. `migrate.py` lists a value that
> differs from the declared one and `--adopt` corrects it; no check of the validator does.
> Code sessions, which read no `sessions.yaml`, reach only `../_scambio` beside the
> repositories: another name serves the documentation sessions alone.

This project hands material between sessions through `EXCHANGE_PATH`, outside every
repository: one folder per element in `in-arrivo/`, named by its identifier, with the fixed
names of the framework's `references/contributions.md`, *The exchange between sessions*. A
brief is read from there and a delivery written there, never copied out of a scratchpad.
Whatever you create outside the repositories goes in the element's `risorse.md` the moment
it exists, with the command that removes it; a copy of credentials stays in your scratchpad,
listed with the names of its keys and never their values. Every session closes with its
declaration in `sessioni/`: what it committed, what it leaves uncommitted, what it leaves
outside the repositories.

<!-- framework-section: additive requires=additive -->
## Threads and joins

> Keep this section only if `.framework/work.yaml` declares `mode: additive`; delete it
> otherwise. `migrate.py --adopt`, run on the branch of a join once the mode is declared,
> adds it.

This project writes its documentation in threads that a script computes, each on a branch of
its own, and lands them on the main line together, at a join that an admin runs. Never write
the main line. On a thread's branch write new files, new entries in the open registers, parking
lines and changes of state; anything else a living document should say -- an edit, a line the
mandatory updates below ask for, a step of a cascade -- is a pending effect in
`_filoni/<thread>/effetti.md`. What belongs to no thread goes on a parking branch, which the
person opens; the parking line of rule 4 too, which here waits for that branch: say it in the
answer, and write it there. A parking branch is pushed only when what it carries is complete:
from its first commit pushed, the next join lands it whole. Rule 5 for a living document, the mandatory
updates and the Definition of Done below hold here as effects: a change is done on a thread
when its effects are written, and `verified` is for whoever decides, at a join. `FRAMEWORK_PATH/references/additive.md` has the table, the
format of an effect and who decides what. Between two joins the living documents are behind:
before reading one as current, look at the effects waiting on it, which the to-do lists per
document. If this session did not start with the to-do in its context, run it:
`python3 FRAMEWORK_PATH/skills/audit/scripts/todo.py --root .`.

<!-- framework-section: review -->
## Review before presenting, and before committing

> Write for `FRAMEWORK_PATH` where this project's framework checkout or plugin lives,
> relative to this repository when the two sit side by side. No check reads it.

Every plan is reviewed before it is presented, and every diff before it is committed or
merged, by the framework plugin's `framework-data-ai:reviser` subagent: it runs the read-only
`framework-data-ai:critic`, fixes by itself the objections that are slips in the text, and
hands back in a few lines what a person has to settle, with a diff that cites a `CHG` held to
what must not change. Give it the diff as a file, new files included
(`git diff --no-index /dev/null <file>`, which exits 1 when it writes one), with the root of
its working tree, or the plan as a file, the absolute path of the `CHG`, and a file in your
scratchpad for its log. Whenever its fixes or yours change files, run the tests and the
validator again and write the diff again. Present the work with what it hands back, each
objection answered or left with why, and none on the substance presented as settled. Exempt:
the parking-lot line, the `SIG` appended to `LOG`, and the commit a script makes of its own
output.

If the reviser is not available, or cannot launch the critic, run the critic yourself, or a
general-purpose agent told to follow `FRAMEWORK_PATH/agents/critic.md` with read-only tools,
and say so; fix the objections on the proposal, show the others, and ask again on your
corrections and on the points it left out only when `FRAMEWORK_PATH/agents/reviser.md`
would, at most three passes. If you cannot run a subagent at all, say that the review did
not run. A review that did not run is said, never skipped in silence.

Write only inside this repository and its worktrees, the exchange -- `_scambio` beside the
repositories, and the folder `.framework/sessions.yaml` declares, if it declares one -- and
the folders Claude Code keeps for the session; for any other place, ask the person first.
The framework plugin's guard stops the file tools where it is installed, and nothing stops
Bash: the rule holds there all the same.

## Mandatory updates

After changing the code, update:

| What you touched | What to update |
|---|---|
| Architecture or dependencies | `ARC.md` **and** a new `DEC` |
| The schema or the meaning of a piece of data | the relevant `DC`, with a version bump |
| An AI component (model, prompt, retrieval) | a new `EVR` |
| A domain term or a metric | `GLOSSARY.md` |
| Anything you release | `REL` **and** `RLM` |
| A risk, or you introduced one | `RSK.md §state` |

## Definition of Done

Work is finished when: the `CHG` is `verified` · the artifacts in the table above are
updated · the project's validator passes with no errors.

## Commands

```bash
# TODO: fill in with the project's real commands
make dev
make test
```

> If this project has no validator yet, say so here rather than leaving the line out. An
> agent that finds no gate assumes there is nothing to pass, and an agent that finds a
> command that does not exist stops and asks. The second failure is the cheap one.

## Sensitive data

- Do not put real customer data in document examples or in committed evaluation datasets.
- PII fields are marked in the `DC` with `pii: true`. Do not copy them into logs, examples
  or fixtures.
- If a task requires access to production data, stop and ask.

## Escalation, stop and ask

The decision is listed as open in the product's `OPEN.md` or in `platform/OPEN.md` · no
approved `CHG` covers the requested implementation · the
work would require modifying an `immutable` · an `EVP` threshold would have to be lowered
to clear the gate · a `DC` would be broken without warning its consumers.

---

## Anti-patterns

- **Filling the authoritative sources table with the same file twice.** Two rows pointing
  at the same document means the split is wrong, and an agent will read whichever it finds
  first.
- **Leaving the Commands section with the placeholders in it.** An agent runs what is
  written here. `make dev` on a project that has no Makefile teaches it that this file is
  decorative, and from then on it stops reading it.
- **Writing rules with no consequence attached.** "Respect the artifact class" alone is
  ignorable. What makes the rule hold is the sentence that says what breaks: an agent that
  reads a historical document as current truth takes wrong decisions with total confidence.
- **Adding rules until nobody reads them.** This file competes for attention with the task
  the agent was given. Four rules that are followed beat twelve that are skimmed.
