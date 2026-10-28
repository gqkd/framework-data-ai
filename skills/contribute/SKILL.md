---
name: contribute
description: >
  Work on the documentation of a project in the additive mode, the one whose
  `.framework/work.yaml` declares `mode: additive`: say what there is to do, take a thread the
  to-do computes, write on its branch what may be written there and the rest as pending effects,
  bring in what a code session delivered, have it reviewed and pushed, and leave it ready; and, for
  an admin, a deputy or a delegate, run the join that lands the ready threads on the main line.
  Triggers on "quali filoni ci sono", "cosa c'è da fare nei filoni", "prendo un filone", "apro
  il filone", "chiudo il filone", "lascio il filone", "facciamo il ricongiungimento", "porta i
  filoni su main", "which threads can I take", "take a thread", "close my thread", "run the
  join". Not for what a cycle builds, which is `cycle` ("cosa facciamo in questo ciclo"), nor for
  which decision to take, which is `resolve` ("cosa devo decidere").
---

# contribute

Read `references/preamble.md`, which sits at `${CLAUDE_PLUGIN_ROOT}`, first, then
`references/additive.md`: what is written where during a thread, the format of the effects, and
who decides what. This skill is the procedure around them, and restates neither.

```bash
F="${CLAUDE_PLUGIN_ROOT:?unset: point it at your framework-data-ai checkout}/skills/audit/scripts"
```

## Only in the additive mode

The mode is the main line's: `python3 "$F/todo.py" --root <documentation>` says so in its first
line when `.framework/work.yaml` there does not declare it. Outside the mode there are no threads
and no joins: say which skill the request belongs to and stop. `--who` is always the person's
name as they give it, one of `people` in `.framework/work.yaml`, never read from `git config`.

## The first time on a machine

Run `python3 "$F/work.py" --root <documentation> doctor --who "<name>"` and show what it says.
A `todo` line is something the framework needs and the person installs or fixes; a `note` is a
recommendation. It reads files, not the session: say so when it reports a plugin or a setting the
person believes is otherwise.

## What there is to do

```bash
python3 "$F/work.py" --root <documentation> list      # fetches: the to-do reads what the clone has
python3 "$F/todo.py" --root <documentation>
```

Show, in this order: the threads to take, those with a decision marked as such; the threads open,
in whose hands and whether ready; what waits after a thread or after the join; the changes to
approve at a join; the entries for every product with no anchors, out of the threads until
somebody anchors them; the effects waiting, per document; what a join brought and nobody has
read; the branches without claims, abandoned.
Recommend one thread, and say why: the oldest decision first when the person decides, otherwise
the thread whose work unblocks the most. A thread with a decision is for an admin, a deputy or a
delegate; a contributor takes threads of work only, and prepares a decision without taking it:
a `DEC` in `proposed`, with the measures and the alternatives in its body, on a parking branch.
At the join the admin accepts it, and the entry closes, or leaves it proposed.

The threads are computed, never drawn: do not propose to move an element from one thread to
another, or to take part of one. What holds a thread together is the anchors its elements forecast
in `affects`; if that is wrong, the repair is the anchor -- on an entry written as an effect, on
an approved `CHG` by who decides at a join, proposed on a parking line.

## Taking a thread

```bash
python3 "$F/work.py" --root <documentation> open --thread <thread> --who "<name>"
```

It claims every element of the thread, creates its branch and a worktree beside the repository,
and pushes both: the work happens in that worktree, and the rest of this skill runs there. A
thread abandoned -- its branch there, its claims gone -- is taken again on its branch, with the
work half done that `open` lists. For what belongs to no thread -- new information, a new
entry, a line in `LOG`, parking lines -- `open --who "<name>" --branch <slug>` with no element
opens a parking branch, written and checked as a thread is. It is one short piece of work:
`open` pushes it empty, and from its first commit pushed it is ready and the next join lands it
whole. So commit, and bring the main line in with `sync --no-push`, until it is complete, and
push then. Given up, delete it on the remote (`git push origin --delete <branch>`) and here. It forecasts
nothing, so the join shows every effect it wrote as outside the forecast.

## Working on the thread

Write by `references/additive.md`: new files, new entries, parking lines and changes of state on
the branch -- not a `CHG` withdrawn or the forecast of an approved one, which are a join's --, and everything else a living document should say as an effect in
`_filoni/<slug>/effetti.md`. The skills that write -- `requirement`, `resolve`, `cycle`, `release`
-- run on the branch as usual and say their own exceptions; this skill does not repeat them. Reserve
every new identifier before writing it, from this branch: `work.py --root <thread worktree>
reserve`, as `audit` describes. From here on `<thread worktree>` is the root: run on the main
checkout, the checks below compare the main line with itself and find nothing.

**What a code session delivered.** When `in-arrivo/<CHG>/documentazione.md` is in the declared
exchange, copy it to `_filoni/<slug>/consegne/<CHG>/documentazione.md` and commit it, then draw the
effects from it with the rules of `requirement`: each line proposed with its target, confirmed once
by the person. A `contribution-policy.json` delivered goes to the same folder. Then the delivery
moves to `integrati/` as `references/contributions.md` describes, with `documentazione.md` named in
`parts` at its place on the branch.

## Before each push

```bash
python3 "$F/work.py" --root <thread worktree> list
python3 "$F/validate.py" --root <thread worktree> --base origin/main
```

On a thread nothing else runs the checks of the branches: there is no pull request. `BR005` is a
living document changed in a way that is not additive -- move the change into an effect --;
`BR001` and `BR003` are numbers, and `BR002` a decision on an entry the main line has closed,
as `audit` says; `BR006` a mandate withdrawn or its forecast moved off a join -- take it out
and propose it, a withdrawal as a `DEC` `proposed`, a forecast on a parking line --; `EFF001` is an effects file that does not read,
`AFF001` an anchor that does not exist. Then the review the preamble asks for, on the diff of the
branch against `origin/main`, effects included, with `_filoni/<slug>/revisione.md` as its log.
Then the push, and `work.py --root <thread worktree> sync` whenever the main line has moved --
on a parking branch not yet complete, `sync --no-push`:
never `git merge` and never a rebase, which `audit` explains.

## When the thread is done

A thread is ready when every element it claimed is done on its branch -- an entry closed, a
change `implemented`, an increment broken down -- and the branch carries a pushed commit of its
own past the main line; in a thread with a decision and a change, when its entries are closed,
and the change goes back to the main line for the next round. The to-do then lists it as ready.
That is the end of a contributor's part: the join lands it, and nobody merges a thread by hand.
To give a thread up before then, `work.py release <IDs> --who "<name>"`: its branch stays, and
whoever takes it again finds the work done so far.

## The join

For an admin, a deputy or a delegate; `join` refuses anybody else. One join at a time, on a
branch of its own, by these steps:

1. `python3 "$F/work.py" --root <documentation> join --who "<name>"`, with the names of the
   threads to land, or none for all those ready. It shows, thread by thread, what the roles keep
   to those who decide -- a classification accepted, the evaluation plan frozen, a change
   `verified`, a known issue closed without a change, the contribution policy -- the effects
   written outside the forecast, and what the checks of the branches find on each, then merges
   the threads one by one, in the same run. Read what it showed to the person before anything
   else: it is to be judged, not filtered. A thread that should not land is dropped by `join
   --abandon` and a new `join` naming the threads to keep. A conflict it leaves is two texts of which one holds: show both, and ask
   whoever decides that matter. `--no-threads` opens a join with no thread, for what is written
   only on a join's branch: `.framework/work.yaml`, an adoption, the contribution policy,
   annotations, and what only those who decide write -- a release, a change `verified`, the
   freeze of the evaluation plan, an approval.
2. In the join's worktree, rewrite the living documents from the effects of the threads merged,
   each target once, and nothing an effect does not say but the cascade of a decision accepted
   here. Two effects on one target from two
   threads that contradict each other are put to the person, with both. On the same branch, the
   person approves the changes in draft they choose -- those of the threads and those the to-do
   lists to approve -- with their name in `approvers`, accepts or leaves the decisions a
   contributor proposed, which `join` showed and the to-do lists -- accepting one, the person
   writes here its cascade: the entry moved, the documents it obliges --, carries a delivered contribution policy into `.framework/`, sorts the
   parking lot, writes the anchors of the entries that have none, and writes what only those who
   decide write: a release, a change `verified`, the freeze of the evaluation plan.
3. `python3 "$F/validate.py" --root <join worktree> --emit-index`, then the validator again.
4. The review the preamble asks for, on the diff of the living documents; its log goes to
   `_filoni/ricongiungimento-<n>/revisione.md`, committed before the next step.
5. `join --finish --who "<name>"` removes `_filoni/` and signs the branch; `join --merge --who
   "<name>"` lands it on the main line, by a merge of its own, and releases what it landed. A
   commit after the signature -- a `sync` because the main line moved, a correction -- is signed
   again by `--finish`, and `--merge` refuses a branch whose last commit is unsigned. When the
   push of the main line did not go, `--merge` says so: once the person has pushed it, `join
   --close` releases what the join landed. `join --abandon` drops a join that did not land.

`--merge` is the one time anything writes the main line, and it is the person's gesture, with
their name. A join takes longer the more threads it lands: for each it reads the branch and runs
the validator. Changing `.framework/work.yaml`, giving or taking back a delegation, adopting a
framework version and annotating an expected finding are for an admin alone.

**Delegation.** An admin who will be away gives a delegation:
`work.py delegate --to "<name>" --who "<admin>"`, taken back with `work.py revoke --to "<name>"
--who "<admin, or the delegate>"`.

## With the sandbox

`references/workstation.md` gives the recommended configuration of the Bash sandbox and says which
commands of this skill do not succeed under it. Those stay the person's to run: say the command,
and do not retry it outside the sandbox.

## What you must not do

**Do not write the main line**, nor merge a thread or a join into it by hand: a join landed by a
fast-forward, or by a merge whose message does not name its branch, is read as text that came
outside a join, and one with commits after its signature has those read the same way. **Do not rewrite a living
document on a thread**: write the effect. **Do not take a decision as a contributor**, nor approve a
change on a thread's branch. **Never force a push**, and never delete a claim or a reservation by
hand. **Do not run `attest.py`**, as the preamble says, even where the rereading is optional.

## Handing back

Say which thread, which branch and worktree, what was written on it and what as effects, what the
checks of the branch said, and what the review left standing. For a join: the threads landed and
kept, the effects applied, what the person decided at the join, and what the main line holds now.
Then the two closing blocks the preamble describes, last. The next steps are derived: the to-do's
threads to take, the thread that waits for this one, the join when the to-do suggests one.
