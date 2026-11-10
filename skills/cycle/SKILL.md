---
name: cycle
description: >
  Open a development cycle: take the candidate signals and roadmap increments, classify their
  impact at the ICG gate, reshape product and architecture where it says to, write the change
  contracts that authorize the work, plan the cycle, and brief each change for a code session it
  launches. Use to decide what to build next, to authorize work and, in a
  documentation session, to implement an approved CHG. Triggers on "cosa facciamo in questo
  ciclo", "cosa costruiamo adesso", "apriamo un ciclo", "prossimo sprint", "devo aggiungere",
  "apriamo un change", "pianifica il ciclo", "dammi i task per gli agenti", "vai pure e
  implementa", "implementa il CHG-021", "voglio implementare il CHG", "procedi con", "what do we
  build next", "open a change", "plan this cycle", "give me the agent tasks", "go ahead and
  implement", "go ahead and build". Use it whenever work is about to start on something not yet
  an approved CHG, including an instruction to go ahead and build a named thing, which leaves
  the authorization step out.
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
| `risk-compliance` | a risk: the entry in `risks:`, and its line in `RSK §state` |

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
and becomes `accepted` when the user says so -- in the additive mode, when an admin, a deputy or
a delegate says so: a contributor's stays proposed, and the join shows one accepted on a thread.
On a thread, where the project pins 4.12.0 or later, or no version that reads, the classification
the rules above give is written without asking and noted in `_filoni/<slug>/scelte.md`; an
ambiguity that only a decision settles stays a question. A gate crossed automatically is a gate that
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
approved one authorizes anything. In the additive mode a change stays in draft on the thread:
an admin, a deputy or a delegate approves it at a join (`references/additive.md`), and its brief
comes in the round after -- a hotfix's excepted, below. It carries `affects` in its front
matter, the documents it is expected to touch -- at the finest section, as
`references/additive.md` says, and from 4.12.0 pinned, or
no version that reads, written always and never left empty --, which the join reads as its
forecast;
from 4.11.0 pinned the change is a thread by itself, and the code prefixes of its
block in the contribution policy say which other mandates wait for it; below 4.11.0 its
`affects` and its whole block put it in a thread. One that touches much is worth proposing to
split.

**A hotfix.** From 4.12.0 pinned, or no version that reads, a fix that cannot wait is a cycle of
its own, which shortens the papers and not the environments: its code follows the project's road to
production, pre-production included, and the processes of that road are the project's, written by
its documentation session -- an emergency protocol among them --, never this framework's. Its `ICG`
gives the true classification; its `CHG` is short, the three sections, `hotfix: true` and its
`affects`. Routed `none` or `product`, it goes as below; routed `architecture` or `both`, it wants
a minimal `DEC` in its `derives_from`, written with it -- in the additive mode in the same join
--, and `CHG005` says one missing. In
the additive mode whoever decides says "facciamo una hotfix" and `contribute` carries the lightning
join (*The hotfix*): a join with no thread, the `SIG` where it is not there yet, the `ICG` and the
`CHG` deriving from the signal, the change's block with its
code prefixes in the contribution policy where the project has one, one pass of review before the
approval, and the brief written right after it in the same join, with the rules of Step 6 and one
pass too -- the exception to the round after, since a hotfix cannot wait a round and has no thread
--; the next join with the whole review reads the `CHG` again, and its delivery when it comes,
and the brief keeps its one pass, its work done once the code is written and its rules the
`CHG`'s -- but for the one more on its *Commands*, where the person changes them at the launch
proposed (Step 6, *The commands*). Outside the mode it is approved as any
change, and its brief written at once. `hotfix: true` is written by whoever decides -- in the
additive mode on a join's branch, written or taken off on a thread or a parking line being a
`BR006` --. An objection
on a hotfix already in production, `approved` or `implemented`, is settled by a new `CHG` that
derives from it, never by a withdrawal, which would say it is never to be carried out;
`rolled-back` only where its code is taken out. One whose code will not reach production is
withdrawn, at a join in the additive mode, `withdrawn_by` the `DEC` that says so. When
nobody who decides can be reached, the code goes with `no-chg: hotfix <reference>` in its merge
request, and afterwards -- in the additive mode, below 4.13.0 pinned at the first join; from
4.13.0 pinned, or no version that reads, at the one that brings in its parking branch, not the
first after the merge where the branch is late (below) -- whoever decides writes the `SIG`, the
`ICG` and a `CHG` with `hotfix: true` that says it was authorized after.

**A hotfix's code session**, from 4.13.0 pinned, or no version that reads, is launched as any
(Step 6, *The launch*), and nothing of it is carried by hand. In the additive mode a hotfix has
no thread, and its launch starts from its parking branch, opened first, from the main line, by
the session that launches it: `open --branch hotfix-<home>-<change>` for an approved one, the
name the to-do prints beside it, and `hotfix-` with the reference as a slug for one with
`no-chg`. It becomes `parcheggio-hotfix-...`, pushed empty, and is the hotfix's claim: a second
`open` of that name is refused, and then somebody else has the hotfix -- launch nothing, and say
so. The code's branch takes its name, and `code` runs with `--root` on its worktree. The hotfix
of a lightning join is launched there once `join --merge` has landed it (`contribute`, *The
hotfix*); an approved hotfix anybody can launch the same way, and on a machine whose exchange
does not hold its brief, the brief is written again in that exchange, naming the `CHG` in that
worktree, by Step 6 and with one pass of review, as the lightning join's. When the code session
delivers, open its merge request on the person's yes, as for any launch, and bring the whole
delivery onto the branch, in `_filoni/<slug>/consegne/<CHG>/`: `documentazione.md`, from which
you write the effects, `verifica.md`, `evidenze/` -- which enters the history of the
documentation with it: read its text files first, and a file that carries the value of a
credential is said to the person, who deletes or cleans it in the exchange before it comes onto
the branch, deleting `evidenze/` too where it is left empty, which git would not keep and
`integrate` would find missing; an image is not read -- and
`mr-link.txt`, with the line `Merge request: <link> @ <commit>`, the commit the head of the
code's branch is at then. Commit, close the launch with `integrate` on the branch, and push; a
change asked after, on the merge request, is a new launch on the same branch (Step 6, *The
launch*), whose delivery comes onto it the same way. The branch lands at the first join after
its code is merged, by the project's own way to production, never by a join, whoever runs it
-- `join` asks the forge, on GitHub, or, on a forge it does not call, whoever decides, and a
branch whose code is not merged waits --, where whoever decides
brings the verification and the link from that folder into the change's §Verification, with
the texts of the join, which its review reads, and does the checks. Outside the additive mode
there are no branches: an approved hotfix's delivery is integrated as any change's, and one
with `no-chg` once its change is written.

With `no-chg`, at the same versions, the documentation session writes a brief with no change:
its *Mandate* the reference and what breaks, its *Guardrails* all but the change's line, its
*Done when* what breaks no longer breaking and, for the review of the code's diff, no `CHG` to
give, there being none; *Commands*, *Context* and the *Delivery* as in any brief. Its own review
is a hotfix's brief's, one pass, with no `CHG` given either: the change is written later, and
read whole then. `code` launches it with
`--no-chg "hotfix <reference>"` in place of the approved change, and the merge request you open
says `no-chg: hotfix <reference>`. The number of its change is reserved when the brief is written,
before the launch: the brief names it, its folder in the exchange carries it, and the change
written later takes it. In the additive mode it is reserved from the parking branch, by
`work.py reserve`, which refuses outside a work branch, and at the join that brings that branch
in, once its code is merged -- not the first join after the merge, where the branch is late: the
change waits for it --, whoever decides writes the `SIG`, the `ICG` and the change with that
number -- `BR003` takes a number reserved for a branch the join merges --, before the effects
the branch brings, and approves it and writes it `implemented` at step 5. Outside the mode it is
the first number free when the brief is written: two elements can take the same one, and the
validator sees the duplicate as it sees any.

**When it reaches `implemented`** -- which it does when the work is merged, without waiting for any
cleaning --, and the project declares an exchange, its resources belong to whoever created them:
where the project pins 4.12.0 or later, or no version that reads, do not read its `risorse.md`,
propose nothing and ask nothing. Below, read it and propose removing what is still there, one row at
a time with the command the row gives, asking whether the row is this machine's; run a command only
on the person's approval, and delete the row when you have; a row of a delivery carried by hand from
another machine goes to the note above the table, with its command for whoever is on that machine,
and is not run here (`references/contributions.md`, *What a mandate creates outside the
repositories*). Then, below 4.13.0 pinned, once the delivery is integrated -- `verifica.md`
written into the change's §Verification, which `integrate` refuses to call placed while that
section is empty -- and committed, move the folder from `in-arrivo/` to `integrati/` with its
`INTEGRATO`: `exchange.py --root <documentation> integrate <CHG>` does both. From 4.13.0 pinned,
or no version that reads, that is done when the delivery comes -- before the merge, but for a
`no-chg` outside the additive mode, whose delivery waits for its change (*A hotfix*) --, and is
what closes the launch (Step 6, *The launch*): nothing in the exchange waits for `implemented`,
and a change asked after is a new launch, whose delivery `integrate` joins to the folder in
`integrati/`. `exchange.py` lists what is left;
`EXC002`, and `EXC004` where it reports, are what the validator says when it is left undone,
warnings that `require_all` does not turn into errors.

**The increment it realises.** When the roadmap declares `increments:`, ask which increment
the change belongs to, proposing the one whose decisions or issues it derives from, and
write it in the change's own `derives_from` beside the rest: a `CHG` cannot be edited after
approval, so this is the one moment its place in the plan can be written where it belongs.
A change that belongs to no increment is legal, and the digest places it after every stage;
say so when the person chooses it. On a thread, where the project pins 4.12.0 or later, or no
version that reads, do not ask: write the increment its decisions or issues derive from -- none
where there is not one only -- and note it in `_filoni/<slug>/scelte.md`, which the join shows
to whoever decides.

## Step 5 · The cycle plan

`IMP` says how the approved contracts get executed this cycle. It is living and replaced
each cycle, and it is an output of the reshaping, never an input. Include what is
**excluded** this cycle: a plan that lists only what is in is one somebody will read as
open-ended. In the additive mode `IMP` is a living document like the others: the new plan is a
pending effect, and reaches the main line at the next join.

## Step 5b · The stages of the roadmap

This skill keeps the order of delivery in `RMP.md`: the `delivery_stages` and the
`increments` of its front matter, which the daily digest draws its Gantt from. The template
says what each field means; what follows is when to touch them.

- **At the opening of every cycle**, read them back to the person in one compact view:
  the stages in their sequence, the increments of each with their state, and under each
  increment what composes it, open and closed. Ask whether the sequence still holds. An
  increment with nothing under it is worth zero hours in the digest's estimate: name the
  ones in the stages that come next, and propose breaking them down, into the `OD` and `KI`
  they require and into `CHG` in draft.
- **When a change of the cycle is written**, it names its increment itself (Step 4). Only a
  change written before the roadmap had `increments:` goes in that increment's `changes`.
- **When every component of an increment is closed**, propose `state: delivered`. `RMP004`
  reports an increment marked delivered with work still open.
- **The first time**, on a roadmap that has no `delivery_stages` yet:
  1. If its body already orders the increments, in a table of phases or in prose, propose
     the two maps from it, and quote the lines each stage and each dependency comes from.
     Ids of stages are short lowercase slugs: a phase called «0b» becomes `t0b`.
  2. List the existing changes, decisions and issues that no increment can be read from,
     in one table, with the increment you propose for each and an empty cell where you
     cannot tell. The person fills the table; do not infer what the documents do not say.
  3. Say what the digest will show the day after: increments that were estimated with a
     size of their own become the sum of what composes them, so one with nothing under it
     leaves the estimate, and the expected delivery moves earlier with no work done.
  4. Write the maps on the person's confirmation, and run the validator: `RMP001`-`RMP005`
     report what does not agree.

  In the additive mode, where the project pins 4.12.0 or later, or no version that reads, a
  thread writes no stage, so the first time is a join's: it asks whoever decides whether to
  set them up, when a thread or a parking branch brings a change to a roadmap without them,
  and follows these four steps on its branch (`contribute`, the join).

Every change to `RMP.md` is a change to a living document: the person rereads it and
attests it, as for any other (`LC006`). That is the reason to touch the stages at the pace
of the cycles, and not every day. In the additive mode it is a pending effect, and the stages
change at a join; where the project pins 4.12.0 or later, or no version that reads, a thread
or a parking line does not touch the `delivery_stages`, nor asks whether their sequence still
holds: the join asks whoever decides, when a branch it lands brings a new increment or an
effect on that roadmap, and one that leaves the roadmaps as they were asks nothing
(`contribute`, the join). The rest of this step -- the increments, their breaking down, `state:
delivered` -- stays on the branch: what it changes in `RMP.md` as pending effects, the entries
and the changes it creates written on the branch.

## Step 6 · The agent brief

For each approved `CHG`, produce the brief that lets a coding agent execute it without
inventing anything. Everything in it already exists: the brief assembles, it does not
compose.

```
Mandate            CHG-NNN §what-changes
Guardrails         CHG-NNN §what-must-not-change
                   products/<p>/OPEN.md and platform/OPEN.md, the decisions it may not take
                   a copy of credentials only in your scratchpad, never under the folder of
                   the repositories, named by its path and its keys, never their values,
                   deleted when you close unless your person asks to keep it, and your
                   final answer says which: deleted, or kept, where, with the command
                   that removes it
                   an action denied to you: stop, and write why you need it
                   the push and the merge request are not yours: the session that
                   launched you does them
                   a question for your person: ask it, and write it also in domande.md
                   in the Delivery folder, one entry per question with its day; then stop
                   the linked files, such as .env, are read and never written
Commands           test: `<command>`
                   prepare: `<command>`
                   generated: `<file>`, by `<command>`
                   link: `<file>`
Context            AGENTS.md authoritative sources, resolved for this product
                   ARC#current, the relevant DC, GLOSSARY
Done when          CHG-NNN §how-we-know-it-worked
                   the artifacts in AGENTS.md "mandatory updates" are proposed in
                   documentazione.md (Delivery), not written
                   the validator passes with no errors
                   a new EVR, if an AI component was touched
                   the diff, new files included (git diff --no-index /dev/null <file>,
                   which exits 1 when it writes one), reviewed before it is committed by
                   framework-data-ai:reviser, which runs framework-data-ai:critic, given
                   <absolute path of CHG-NNN>, the absolute path of <framework>, where
                   the critic reads the rules the work invokes, and a file in the
                   session's scratchpad for its log; where the reviser cannot run, by
                   the critic alone, or by a general agent following
                   <framework>/agents/critic.md read only, its
                   objections on the proposal fixed and asked again as
                   <framework>/agents/reviser.md says; if files changed after the review,
                   the checks above run again; what it hands back, each objection
                   answered or left with why, in the verification handed back
                   (verifica.md, with an exchange)
```

**The commands.** *Commands* names what the launch of the code session runs or grants, one item
per line, each command or file between backticks: `test:` a test the code session may run
without asking; `prepare:` what its worktree needs before the tests run -- installing the
dependencies, a build --, which the documentation session runs, in view, before the launch;
`generated:` a file the preparation writes, such as the lockfile, `by` the command that
regenerates it: the code session never writes it, and the documentation session regenerates it
at a step of a rebase, or a merge of the base, that has it in conflict; `link:` a file git
ignores that the tests read, such as `.env`, linked from the main checkout of the code
repository and never copied. Propose them from `CHG §how-we-know-it-worked` and the
instructions of the code repository; the brief's review reads them, and the person confirms
them after it, shown with the launch proposed: changing one is changing the brief, reviewed
again -- the reviser relaunched with what the brief's review was given, its log file included,
and each line changed, as it was and as it is, with its line -- in one pass on the commands
changed and what they grant alone, whatever passes the brief had, a hotfix's included. That pass
fixes nothing and hands back what it finds: show the commands again before "lancio?", and a
second change has a pass of its own. The launch grants the tests the brief names, as written:
show them, do not change them, and change one only by changing the brief, with that pass. After
the launch a command changed is a new launch's: `--resume` holds the brief to its *Commands* as
they were at `--launch`, all four kinds, by a print the launch file keeps, and refuses a brief
whose *Commands* changed since, a `prepare:`, `generated:` or `link:` line as a `test:` one,
which the code session, writing in the delivery folder, could otherwise change for itself. No
copy of the brief as launched is kept: the way out of that refusal is a new launch, the first
call again, its brief reviewed whole. The lines a stop prints for you to run -- `generated:` at
a step in conflict, `prepare:` -- are read from the brief as it is: show each before it runs,
and run it only on the person's yes.

**Where the brief goes.** When `.framework/sessions.yaml` declares `exchange:`, write the
brief to `<exchange>/in-arrivo/CHG-NNN/brief.md`, creating the folder, and tell the person
its absolute path: the code session reads it from there, and delivers into the same folder,
so the brief and the verification of one mandate end up side by side. A brief left in this
conversation, or in a session's scratchpad, is one somebody copies by hand. Where the project
pins 4.13.0 or later, or no version that reads, nothing is carried by hand: once the brief of an
approved change is written and reviewed, propose its launch (*The launch*, below), on the machine
where the code is written, whose documentation session gives the code session its answers and
receives its questions, its actions denied and its delivery until it closes; whoever writes the
code on another machine says "implementa il CHG-021" to the documentation session there. A
brief written in this exchange for a change then launched from another machine stays here with
nothing delivered, which `EXC002` reports once the change is `implemented`: close it with
`exchange.py --root <documentation> integrate <CHG>`, a folder with nothing delivered moving
with `parts: {}` (`references/contributions.md`, *From in-arrivo to integrati*), as `contribute`
says of a hotfix's (*The hotfix*). The exchange declared is then a requirement for implementing,
with the `claude` CLI: without the key,
say that the launch wants it and how it is declared (`references/contributions.md`, *The
place*) -- in the additive mode the `exchange:` line comes with the join that brings the project
to 4.13.0; outside it, propose it, and write it on the person's yes. Below 4.13.0 pinned, when
the code is written on another machine, the brief is carried there, with the absolute paths of
this one, and the delivery is carried back into this folder (`references/contributions.md`, *A
delivery from another machine*); without the key, hand it over as before. With it, the brief
carries one more block, written with the absolute path of the folder, because the code session
works in another directory -- from 4.13.0 pinned, or no version that reads, its own worktree of
the code repository --:

```
Delivery           <absolute path>/in-arrivo/CHG-NNN/, under the fixed names: verifica.md,
                   mr.md -- the text of the merge request, which the session that launched
                   you opens and whose link it writes in mr-link.txt --, evidenze/,
                   contribution-policy.json
                   documentazione.md: what the documentation should say after this change,
                   which the thread, or the parking branch of a hotfix, turns into effects,
                   or, outside the additive mode, the session that launched you writes into
                   the documents
                   risorse.md: one row per resource, the moment it exists -- type, path or
                   name, the command that removes it, a copy of credentials with the names
                   of its keys; you delete that copy when you close, removing the rest is
                   for your person, when they want, and your final answer says what is
                   left, with those commands
                   sessioni/<date>-<session>.md when you close with something uncommitted,
                   or a review that was due and did not run: committed, not committed,
                   outside the repositories; none when everything is committed and every
                   review that was due ran
```

`references/contributions.md`, *The exchange between sessions*, is where each of those is
described, and the place to read before writing the block for the first time. Where the project
pins a version below 4.12.0, the brief is as it was in three places: no line on copies of
credentials among the guardrails; `risorse.md` ends at "the command that removes it; a copy of
credentials only in your scratchpad, with the names of its keys and never their values", with
nothing on who removes the resources, which the documentation session proposes (Step 4); and
the declaration is written at every close, "sessioni/<date>-<session>.md when you close:
committed, not committed, outside the repositories". Where it pins a version below 4.13.0, the
brief is as it was in four more: none of the last four items of the guardrails, from "an action
denied to you" to "the linked files"; no *Commands*;
the mandatory updates of *Done when* "are updated -- in the additive mode proposed in
documentazione.md (Delivery), not written"; and the *Delivery* names "verifica.md, mr.md,
mr-link.txt, evidenze/, contribution-policy.json", with "documentazione.md, in the additive mode:
what the documentation should say after this change, which the thread turns into effects".

Write `<framework>` and the path of the `CHG` as absolute paths when you produce the brief:
the code session works from another repository -- and, below 4.13.0 pinned, may not have the
plugin enabled; from 4.13.0, or no version that reads, the launch gives it the plugin `code` runs
from, with its guard (`--plugin-dir`). The path of the `CHG` is where the code session reads it
approved, and where it stays for the whole work: the documentation's checkout outside the
additive mode; the thread's worktree on a thread; for the hotfix of a lightning join, the main
checkout of the machine of that join, where `join --merge` brings it -- the brief is written in
the join, before the hotfix's parking branch exists, and `code` runs with `--root` on that
branch's worktree, opened after `--merge` from the main line, where the change is the same; its
one pass of review runs before `--merge`, so tell the reviser that this path holds the approved
change only once the join has landed, and is not a reference to correct --;
for a hotfix whose brief is written outside the lightning join, the worktree of its parking
branch, since on another machine only `--merge` moves the main checkout, and the change there may
be missing or older.

**The launch**, where the project pins 4.13.0 or later, or no version that reads. Every code
session starts from a documentation session, which launches it, answers what is its to answer
and never approves by itself: nobody opens Claude in the code repository. Once the brief of an
approved change is written and reviewed, propose the launch, on the machine where the code is
written: the code repository, proposed among the folders beside the documentation that are git
repositories and asked at the first launch of each change -- later calls read it from the launch
file --; the code session's worktree, `<repository>-<id>` beside it, on its branch -- the
thread's in the additive mode, the hotfix's parking branch, `<id>` outside the mode --, from the
remote's default branch, or another start the person names, such as a hotfix's production branch,
the project's process (`--base`); and the brief's *Commands* -- the tests the launch grants, the
preparation, the files generated and those linked --, for the person to confirm, as *The commands*
says. Then ask "lancio?": the person's yes is the gesture. `references/contributions.md`,
*The exchange between sessions*, says the rest; in short, with
`F="${CLAUDE_PLUGIN_ROOT:?}/skills/audit/scripts"` and `--root` on the documentation's checkout,
or, in the additive mode, the worktree of the thread or of the hotfix's parking branch:

1. `python3 "$F/exchange.py" --root <documentation> code <CHG> --repo <code repository>`
   creates the worktree, its branch and the linked files, and stops. It says how the branch
   stands against its remote -- brought forward where the remote is ahead, or diverged, with
   both sides and the two commands, join them by a rebase or keep the remote, for the person to
   choose -- and how far it is behind its base, which `--join-base` joins on the person's yes.
2. Run, in view, the commands its last lines list -- the push of the branch, the preparation
   the brief names --, each on the yes where it says so. A preparation that fails is said, and
   stops the launch, unless a rebase or a merge of the base is in progress.
3. `code <CHG> --launch`, in the background. The code session runs on the person's subscription
   only: a setting of Claude Code's that gives it a key or another provider is refused, with its
   file and line, and one its first event shows stops it on `account`.
4. Each run ends on a stop, said in a few lines, which you tell in plain words. `negata`: "the
   code session asks to run `<command>`, because <its why>: approve?" -- for a commit, with
   `git -C <worktree> status --short` and `git -C <worktree> diff --cached --stat` beside --;
   on the yes, each rule the stop proposes that the person approves, whole, in a file of your
   scratchpad, `--resume --allow <file>`, for that run only. A `git rebase --continue`, or the
   commit that concludes a merge of the base and its push, at once, is yours to run on the yes,
   in view, as the stop says, and then `--resume` with nothing; a push or a merge request is
   never the code session's, and no question; a block of the framework's guard is approved by
   no rule.
   `account`: a limit or a credential of the account, said; resume when it allows. `domanda`:
   where the documentation has the answer, give it yourself, with the file and the section it
   comes from, and tell the person what was asked and what you answered; where it is not
   written, or is a decision, ask the person, and a new decision goes its way in the
   documentation (`requirement`, `resolve`); the answer in a file, `--resume --reply <file>`.
   `fine`: the code session's answer, said; a step of network its sandbox stopped is a command
   you give the person. `--status` says whether it runs and where it stopped, from any
   documentation session of the machine.
5. `consegna`, the delivery: push the code session's commits and open the merge request with
   the text of `mr.md`, on the person's yes -- `gh pr create` on GitHub; on another forge, which
   nothing here calls, the person opens it with that text and gives you its link --, and write
   the link in `mr-link.txt`. A push refused because the remote moved does not close the
   launch: say it, open nothing and bring nothing in; a new launch makes the delivery again,
   verified on the branch brought up to date. Then bring the delivery in: on a thread as
   `contribute` says (*What a code session delivered*), on a hotfix's parking branch as *A
   hotfix* says; outside the additive mode, what `documentazione.md` proposes written into the
   documents by the rules of `requirement`, and `verifica.md` into the change's §Verification,
   with the line `Merge request: <link> @ <commit>`, the link of `mr-link.txt` and the commit
   the head of the code's branch is at then. Commit, and `integrate <CHG>`, which closes the
   launch. A change asked after -- what the review of the merge request asks, say -- is a new
   launch on the same branch: the brief back in `in-arrivo/<CHG>/`, with what to change and why
   at its end, which the review reads.

With the sandbox, every call of `code` leaves it where the settings let it out, by the third
entry of `sandbox.excludedCommands`, `python3 *exchange.py* code *` (`references/workstation.md`):
run each alone, with the absolute path `$F` holds written out, and nothing around it. The push,
the preparation, the rebase and each step of it stay inside, and where the sandbox stops one,
give the person the command and do not retry it outside. Below 4.13.0 pinned nothing
is launched: the brief goes as before, and the person opens the code session. From 4.13.0, where
it does not launch, say why, and do not propose opening it by hand: without `claude` on the
`PATH` -- the desktop app or the extension alone --, the launch wants the CLI, and
`work.py doctor` says what this machine has and how to add it; without an exchange declared, as
above; a code repository outside the folder that holds the documentation and the exchange, where
the guard would not hold the code session; Windows outside WSL, which `code` refuses.

**"Implementa il CHG-021"** -- "voglio implementare il CHG", "vai pure e implementa" -- in a
documentation session, at any version: a change not `approved` goes through its approval first
(Step 4); an approved one goes to its launch -- below 4.13.0 pinned, to its brief, as before, for
the person to hand over; one with no code to change has no code session, and on a thread is
written `implemented` there as before (`contribute`, *When the thread is done*). With its brief in
`in-arrivo/<CHG>/`, propose the launch on it;
without, write it by this step, with its review, then propose the launch. In a session that is
not a documentation one -- the code session itself, which loads this plugin, or one opened in
the code repository -- launch nothing and write no brief: the code session is already there,
and `code` wants `--root` on the documentation. In the additive mode the thread comes first:
whoever implements a change holds its thread, and this skill does not open it -- `contribute`
does (*Taking a thread*), where nobody holds it. Where the person holds it, start from its
worktree. The brief is written there, with the path of the `CHG` there and its review, and the
launch leaves from that worktree, `--root` on it. Where `open --thread` refuses -- a mandate
that waits, a thread in somebody else's hands --, launch nothing, and say why. An approved
hotfix has no thread: anybody launches it from its parking branch (*A hotfix*, Step 4).

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
first row is normally handing a brief to a coding agent -- from 4.13.0 pinned, or no version
that reads, launching its code session --, and it is only a row for a `CHG` the user has
actually approved: a `draft` in that position is this skill authorizing its own work.
A candidate routed back into discovery belongs in the table too, and its cost is the honest
one — building on a premise that was just disproved is more expensive than the re-entry.
