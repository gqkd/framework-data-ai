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
A `todo` line is something the framework needs and the person installs or fixes -- the one on an
exchange not declared is the project's, fixed at a join, and only whoever decides gets it --; a
`note` is a recommendation. It reads files, not the session: say so when it reports a plugin or a
setting the person believes is otherwise.

## What there is to do

```bash
python3 "$F/work.py" --root <documentation> list      # fetches: the to-do reads what the clone has
python3 "$F/todo.py" --root <documentation>
```

Show, in this order: the threads to take, those with a decision marked as such, each with its
notes -- a mandate that shares a code prefix with another, so that opening one makes the other
wait, or one with no code prefixes -- and the known issues a mandate repairs; the threads open,
in whose hands and whether ready -- from 4.13.0 pinned, or no version that reads, a hotfix's
parking branch ready is not landed by that: a join brings it in only once its code is merged,
which the to-do does not ask the forge, so a join it suggests for that branch alone may bring
nothing in --; what waits after a thread or after the join; the changes to
approve at a join; the entries with no anchors, out of the threads until somebody anchors them
at a join -- from 4.11.0 pinned every entry with no `affects`, an exception the join clears --;
the effects waiting, per document; what a join brought and nobody has read; the branches
without claims, abandoned; from 4.12.0 the hotfixes approved, which are no thread to take --
from 4.13.0 each with the name of its parking branch and whether it is open: whoever launches
its code opens it, and it is the claim (*The hotfix*).
Recommend one thread, and say why: the oldest decision first when the person decides, otherwise
the thread whose work unblocks the most. A thread with a decision is for an admin, a deputy or a
delegate; a contributor takes threads of work only -- from 4.11.0 pinned a mandate's, `mandate:`
in the to-do, is one --, and prepares a decision without taking it:
a `DEC` in `proposed`, with the measures and the alternatives in its body, on a parking branch.
At the join the admin accepts it, and the entry closes, or leaves it proposed.

The threads are computed, never drawn: do not propose to move an element from one thread to
another, or to take part of one. What holds a thread together is the anchors its elements forecast
in `affects`; if that is wrong, the repair is the anchor -- the finest section the work touches,
a section inside another named `<id>-<rest>` (`references/additive.md`) --, on an entry written
as an effect, on an approved `CHG` by who decides at a join, proposed on a parking line. From
4.11.0 pinned an approved `CHG` is a thread alone, and what makes it wait for another is the
code prefixes of its block in the contribution policy, which who decides narrows, at a join.

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
whole -- but, from 4.13.0, a hotfix's, `hotfix-...`, which is ready with the line of its merge
request and lands once its code is merged (*The hotfix*). So commit, and bring the main line in
with `sync --no-push`, until it is complete, and push then. Given up, delete it on the remote
(`git push origin --delete <branch>`) and here. It forecasts nothing, so the join shows every
effect it wrote as outside the forecast.

**A thread with a change, and its code.** Below 4.13.0 pinned, the usual way is that whoever
takes a thread with a `CHG` also runs its code session, on the same machine: the exchange is
that machine's, so the delivery reaches the thread without being carried by hand. It is a
recommendation, not a role: when somebody else writes the code -- a person who writes only
code, the second developer of a thread with two changes --, the brief is carried to that
person's machine, with the absolute paths of this one, which whoever carries it says; the
delivery is carried back to the thread's machine, and its resources go as
`references/contributions.md` says in *A delivery from another machine*. Whoever writes only
code does not enter `people` for it.

From 4.13.0 pinned, or no version that reads, every code session starts from a documentation
session, and nobody opens Claude in the code repository: whoever holds the thread launches it
from the thread's worktree and answers it there, so nothing is carried by hand, neither the
brief out nor the delivery back. So whoever writes the code holds the thread -- `code` refuses a
`--root` whose thread does not hold the change --, and is among `people`, a contributor at
least, a person who writes only code included. The launch wants the declared exchange and the
`claude` CLI on
the `PATH`: without the CLI -- the desktop app or an extension alone -- say that the launch
wants it and how to install it, as `doctor` says, and never propose opening the session by
hand; without an exchange, say that the launch wants one, and that its `exchange:` line is
brought to a join. Once the brief is written on the thread and reviewed (`cycle`, Step 6),
propose the launch: the code repository, among the folders beside the documentation that are
git repositories -- asked at the first launch of each `CHG`, read back from the launch file
after --; the worktree the code session works in, `<repository>-<chg>` beside it, on a branch
with the thread's name, and the branch it starts from, the remote's default or one the person
names (`--base`); the commands the brief grants, shown and not changed -- to change one is to
change the brief, with its review. Then ask "lancio?": the yes of whoever holds the thread is
the gesture, and each step after it is a command of yours, in view, `code` run as
`python3 <F>/exchange.py --root <thread worktree> code <CHG> ...`, with `<F>` the absolute path
`$F` holds written out and the call alone, as the sandbox's settings let it out:

1. `open` pushed the thread's branch in the documentation (*Taking a thread*), and nobody else
   touches it.
2. The first call, `code <CHG> --repo <code repository>`, with `--base <branch>` where the
   person named one, creates the worktree and the same branch in the code repository, links the
   files the brief names and writes the launch file, then stops: push the branch as it prints,
   and run the preparation the brief names. What it says of the branch against its remote goes
   to the person -- commits that are not the code session's, which the launch tells it; two
   sides diverged, with the two commands, join them or keep the remote, of which you run the one
   the person chooses (`references/contributions.md`) --, and so does how far it is behind its
   base, which `--join-base` joins on a yes (*The code behind its base*, below).
3. The launch, `code <CHG> --launch`, run in the background: the code session works on that
   branch, on the person's subscription alone, and comes back at each stop, below, until its
   delivery.
4. On the person's yes -- the code session neither pushes nor opens it --, push its commits,
   showing first what the push carries, and open the merge request of the code with the text
   of `mr.md`, on GitHub with `gh pr create` -- on another forge, which nothing here calls, the
   person opens it with that text and gives you its link --; its link goes in `mr-link.txt`, in
   the delivery folder. A push refused because the remote moved while the code session worked does
   not close
   the launch: say so, and the delivery is made again by a new launch -- the first call again,
   which asks whether to join the two or keep the remote --, whose code session verifies again.
5. The delivery brought in as *What a code session delivered* says, its verification written
   into the change's `## Verification` with the line `Merge request: <link> @ <commit>`: the
   link of `mr-link.txt`, and the commit at the head of the code's branch then, forty
   characters.
6. `integrate`, which closes the launch: after the merge request and its line, never before,
   since a link written after would be a second delivery.
7. The thread is ready once that line is on its branch, pushed (*When the thread is done*): it
   does not wait for the merge, which the join makes (*The join*, steps 1 and 6).

Each stop is said to the person in plain words, and no approval is ever yours:
- `negata`: "the code session asks to run `<command>`, because <the reason it wrote>:
  approve?". On the yes, `code <CHG> --resume --allow <file>`, the rule written whole, for that
  run alone, several together where the person approves them together; for a commit, show
  first what would enter, `git -C <worktree> status --short` and `git -C <worktree> diff
  --cached --stat`. A step of a rebase, and the commit that concludes a merge of the base, you
  run on the yes, as the stop prints them, and the resume then carries no rule. A push or a
  merge request is never the code session's and is no question; a block of the framework's
  guard, or of a hook of the person's, has no rule that grants it.
- `domanda`: where the documentation has the answer, give it, with the file and the section it
  comes from, and tell the person what was asked and what you answered; where it is not
  written, or is a decision, the question is the person's, and a new decision goes its way in
  the documentation. The answer goes with `--resume --reply <file>`.
- `account`: a limit of the subscription, or a credential, which the stop names: say it, and
  stop. It is the one limit on what the code session spends.
- `fine`: what it answered. A step that wanted the network and that the code session's sandbox
  stopped is a command failed: give the person the command, and do not retry it outside the
  sandbox.
- `consegna`: steps 4 to 6.

`code <CHG> --status` says whether it runs and where it stopped. A change asked for after the
launch closed is a new launch on the same branch: the brief back in `in-arrivo/<CHG>/`, with
what to change at its end, and its delivery `integrate` joins to the first.

**The code behind its base.** When the join says a merge request waits behind its base, which
wants it up to date, or in conflict with it (*The join*, step 1), whoever holds the thread
brings it up to date, on the person's yes. The brief goes back in `in-arrivo/<CHG>/`, and the
first call with `--join-base` joins the base into the code's branch by a merge: a conflict goes
to the code session first, the commit that concludes the merge is yours, and its push is made
at once -- refused, the remote is kept and the base joined again. Where the code is merged by a
rebase, `merge_method: rebase` or `--join-base rebase`, the branch's commits are re-applied on
the base instead, step by step as in a rebase, and its push is forced with lease, on the
person's yes. Then a new launch verifies it again, and its delivery is integrated, its line
naming the new commit.

## Working on the thread

Write by `references/additive.md`: new files, new entries, parking lines and changes of state on
the branch -- not a `CHG` withdrawn or the forecast of an approved one, nor, from 4.11.0, a
mandate no thread holds written `implemented`, which is a join's, nor, from 4.13.0 pinned, or no
version that reads, the thread's own mandate written `implemented` or a `KI` it repairs closed,
which the join writes once it merges the code, but for a change with no code to merge, written
`implemented` on the branch as before (*When the thread is done*) --, and everything else a living
document should
say as an effect in `_filoni/<slug>/effetti.md`. Where the project pins 4.12.0 or later, or no
version that reads, what is placement, form or the classification of an `ICG` takes its default,
noted in `_filoni/<slug>/scelte.md` (`references/additive.md`, *The choices of form*), and only
substance is asked. The skills that
write -- `requirement`, `resolve`, `cycle`, `release` -- run on the branch as usual and say their
own exceptions; this skill does not repeat them. Each new identifier is reserved by the skill
that writes it, before writing it, from this branch -- `work.py --root <thread worktree> reserve`,
as the preamble says: not a step anybody has to remember. From here on `<thread worktree>` is
the root: run on the main checkout, the checks below compare the main line with itself and find
nothing.

**What a code session delivered.** When `in-arrivo/<CHG>/documentazione.md` is in the declared
exchange, copy it to `_filoni/<slug>/consegne/<CHG>/documentazione.md` and commit it, then draw the
effects from it with the rules of `requirement`: each line proposed with its target, confirmed once
by the person -- where the project pins 4.12.0 or later, or no version that reads, written
without asking, and said in your last answer, target by target, after the push: whoever followed
the code corrects one by a commit on the branch, pushed by the steps of *Before each push*,
before the join, whose review reads the effects beside the delivery in any case; a line of
substance stays a question.
A `contribution-policy.json` delivered goes to the same folder. A `verifica.md` delivered is
written into the change's §Verification, with what it cites in `evidenze/` and the link of
`mr-link.txt`: the thread writes it, and `integrate` refuses while that section is empty. Once
what the delivery brought is committed, close it with
`python3 "$F/exchange.py" --root <thread worktree> integrate <CHG>`: it moves the folder to
`integrati/` and writes its `INTEGRATO`, with `documentazione.md` at its place on the branch;
an `mr.md` is placed by hand, as `references/contributions.md` describes. From 4.13.0 pinned,
or no version that reads, the delivery comes from the launch (*A thread with a change, and its
code*), in a fixed order: the merge request first, opened by you on the person's yes, its link
in `mr-link.txt`; then the verification, with the line `Merge request: <link> @ <commit>` in the
change's §Verification -- the last such line counts, where there are several --; then
`integrate`, which closes the launch, and the push.

## Before each push

```bash
python3 "$F/work.py" --root <thread worktree> list     # fetches; `sync --no-push` if main moved
python3 "$F/work.py" --root <thread worktree> check    # offline: the views, the validator
```

The fetch first -- `list`, or `sync --no-push` when the main line has moved, since `sync`
without it publishes the branch --: a main line seen hours ago lets through what the real one
would not. Then `check`, which fetches nothing: it regenerates the views, runs the validator
with `--base` on the branch, details only what the main line does not have -- but for a copy of
credentials beside the repositories, an `EXC005` it details each time, since it reads the main
line from a temporary folder --, says when the last fetch was, and gives the branch's row of
`list` as the remote had it at the last fetch or push. Its exit 1 is an error of the validator,
or a view it did not write, having no generator's line: that one a person maintains, and is
put to them, as `audit` says of `--emit-index`. Commit the views it regenerated with the work
before the review and the push: `sync`
refuses a tree with changes. `check` alone, which runs under the sandbox too, is for the round
repeated between two pushes. On a thread nothing else runs the checks of the branches: there is
no pull request. `BR005` is a
living document changed in a way that is not additive -- move the change into an effect --;
`BR001` and `BR003` are numbers -- renumbered by you, without asking, since a number is form:
`python3 <F>/work.py --root <thread worktree> renumber <ID> --who "<name>"`, with `<F>` the
absolute path `$F` holds written out and the call alone, as the sandbox's settings let it out
(`references/workstation.md`), said in your last answer; `sync` refusing a number both sides
created is the same --, and `BR002` a decision on
an entry the main line has closed, as `audit` says; `BR006` a mandate withdrawn or its forecast
moved off a join -- take it out and propose it, a withdrawal as a `DEC` `proposed`, a forecast
on a parking line --, or, from 4.12.0 pinned, one brought back out of `withdrawn`, which stays
withdrawn: a new `CHG` carries what it would have done, or `hotfix: true` written or taken off,
put back as the main line has it -- a hotfix is whoever decides' (*The hotfix*) --; `EFF001` is
an effects file that does not read, `EFF002` a choices file, `AFF001` an anchor that does not
exist. Where the project asks
for `require_all`, from 4.12.0 pinned, or no version that reads, the only `AN003` on a thread is on
`EXC005` or `EXC006`, which can say an exposure on this machine the join never sees: the annotation
is the join's to write, so the way out is the repair of what each finding names, on this machine --
a copy of credentials deleted on the yes of the person whose machine it is, as `audit` says, a
value out of the list, the exchange moved out of a git repository with its folders. The `exchange:`
line of `.framework/sessions.yaml` is every machine's: a change to it is brought to the join, not
made on the thread.
Then the review the preamble asks for, on the diff of the
branch against `origin/main`, effects included, with `_filoni/<slug>/revisione.md` as its log:
one pass, where the project pins 4.12.0 or later, or no version that reads, and the substance it
leaves is the contributor's to fix or to bring to the join.
Then the push, and `work.py --root <thread worktree> sync` whenever the main line has moved --
on a parking branch not yet complete, `sync --no-push`:
never `git merge` and never a rebase, which `audit` explains.

## When the thread is done

A thread is ready when every element it claimed is done on its branch -- an entry closed, a
change `implemented` or, from 4.13.0 pinned, or no version that reads, with the line of its
merge request in its §Verification, an increment broken down -- and the branch carries a pushed
commit of its own past the main line; in a thread with a decision and a change, which the to-do
computes only below 4.11.0, when its entries are closed, and the change goes back to the main
line for the next round. The to-do then lists it as ready. A mandate's thread is the mandate
alone, from 4.11.0 pinned, and once it is ready and pushed the next join opened on the threads
ready lands it, whatever else is open; one already open, or one that names its threads without
it, does not. Below 4.13.0 pinned it is ready once its code is merged: write it `implemented`
on the branch, close each `KI` the to-do says it repairs -- `status: decided`, `closed_by` the
change --, and push, at once. Those `KI` are not claimed, so `list` says your branch changes
them without a claim. Close one only when the to-do lists your mandate alone
for it -- of several listed together, none closes it while another is still listed -- and not
one it says a thread still claims: that thread releases it first. From 4.13.0 pinned, or no
version that reads, the thread writes neither, but for a change with no code to merge (below):
it is ready once its verification carries the
line, pushed at once, without waiting for the merge, wherever the code's forge is -- the join
merges the code, or, on a forge it does not call, whoever decides merges it there when the join
asks, at its step 1 --, and the join writes the change `implemented` with the `KI` it repairs
closed. A change written `implemented`
on the branch -- a thread taken before the adoption, a change with no code to merge, or a habit
-- makes the thread ready as before, with each `KI` it repairs closed on the branch as above,
since the join closes only those of a change it brings in with the line, and the join asks
whoever decides whether its code is merged before letting it in. A thread of yours that claims
a `KI` the to-do lists as repaired by a mandate releases it, `work.py release <KI> --who
"<name>"`: the mandate closes it -- from 4.13.0, the join that brings its code in, or the
thread of a change written `implemented` on its branch. One left
open when its mandates land is a node of the to-do
again. When two threads holding mandates on the same code are opened in
the same minute, the `open` whose push landed second says so, unless its fetch or its
computing of the to-do after the push fails, and the other may be told by nothing: agree with
that person who goes first, and `release` if it is not you. That is the end of a
contributor's part: the join lands it, and nobody merges a thread by hand -- nor, from 4.13.0,
its code: the join merges its merge request, or, on a forge `join` does not call, whoever
decides does, at the join's step 1.
To give a thread up before then, `work.py release <IDs> --who "<name>"`: its branch stays, and
whoever takes it again finds the work done so far.

## The join

For an admin, a deputy or a delegate; `join` refuses anybody else. One join at a time, on a
branch of its own. You run it, commands included: the person says "let's run the join" and
answers only what is theirs -- the approvals, a conflict, the choices of form, the list to
anchor, which mandates no thread holds have their code merged, the stages of a roadmap, and
from 4.13.0 whether code on a forge `join` does not call is merged and how to merge where the
project does not say -- and gives the yes that lands it. Without the sandbox you run every
command below, `--merge` only after that yes. With it, the commands that reach the remote or
write beside the repository -- `join` and its `--finish`, `--merge`, `--close` and
`--abandon`, `sync` -- are the person's: give each as a line ready to paste and wait for them
to say it ran
(`references/workstation.md`); `reserve` and `renumber` stay yours, each run alone with the
absolute path, where the settings let them out of the sandbox, and a line to paste where it
stops one anyway; once the join is open, have the work go on in a session started
in its worktree, as for a thread, since the views and an adoption are written there. Where the
project pins a version before 4.12.0, the acts of step 5 are written at step 2 with the texts,
step 3 is skipped, and the review reads them committed.

1. **The threads landed.** `python3 "$F/work.py" --root <documentation> join --who "<name>"`,
   with the names of the threads to land, or none for all those ready. It shows, thread by
   thread, what the roles keep to those who decide -- a classification accepted, the evaluation
   plan frozen, a change `verified`, a known issue closed without a change, the contribution
   policy -- the effects written outside the forecast, what it brought with no anchor, the
   choices of form it took by default, from its `scelte.md`, and what the checks of the
   branches find on each, with the to-do's whole list to anchor first and the hotfixes the whole
   review reads outside the diff -- approved by a join with one pass since the last one signed
   `Revisione: completa` --, then merges the threads one by one, in the same run. Where the main
   line pins 4.13.0 or later, or no version that reads, before it merges it asks the forge, with
   `gh` on GitHub, about the code of each thread with a change and of each hotfix's parking
   branch: a merge request of the branch with the thread's name, at the delivery's commit, that
   the forge lets merge now, and the way to merge it -- `merge_method` in `.framework/work.yaml`
   where its repository admits it, else the one way it admits, else the one whoever decides says
   once, `--merge-method <way>` --; and it says what `--merge` will merge. One merged at that
   commit already counts as merged; one merged at another head comes in, with the commits after
   the delivery said and their diff written in `--out`, a folder in your scratchpad, for the
   review (step 4); a hotfix's comes in only once merged, by the project's own way to
   production, on every forge. On a forge `join` does not call, whoever decides merges a
   thread's code there, having read it -- nobody else merges it --, and says whether a thread's
   or a hotfix's code is merged, and at the delivery's commit; there a thread's code lands
   before the review of step 4, where on GitHub it lands after: `--merged <thread>` at that
   commit, `--merged-elsewhere <thread>` at another head -- whose commits nobody read,
   which whoever decides looks at on the forge, correcting on the join's branch what the
   documentation does not cover --, and with no answer it waits. `--merged` answers too for a
   change written `implemented` on its thread's branch with no line, which `join` names. On
   GitHub a join merges one merge request per code repository, and the second waits for the next
   join; one the forge holds merged already takes no turn, nor does an answer of whoever decides
   on a forge `join` does not call. What
   waits -- no `gh`, or no access, which it says with the remedy; a head moved; a draft, a
   conflict, checks or approvals the forge wants; closed; behind its base; a hotfix's not merged;
   the second of a repository -- is said with its way out, and nothing is opened or merged: run
   `join` again with the line it prints, which names the threads without what waits and repeats
   the answers. Closed without a merge, a thread waits for a new delivery, or whoever holds it
   releases it and its mandate is withdrawn at a join; a hotfix whose code will not reach
   production, whoever decides withdraws at a join, and its parking branch is deleted; nothing is
   released or deleted by itself. Behind its base, or in conflict with it, whoever holds the
   thread brings the code up to date (*The code behind its base*, above): tell that person. Read
   what it showed to the person before anything else: it is to be judged, not filtered. A thread
   that should not land is dropped by `join --abandon` and a new `join` naming the threads to
   keep. A thread that creates a number the join already created, or one with no reservation of
   its own -- written with none, or reserved for another branch --, stops `join` before it is
   merged: run `join` again, naming the threads still to merge without it, and say that it waits
   for a later join. The skill of whoever holds it renumbers it at their next session, where
   `BR003` shows it once the reservations are fetched -- reserved for another branch, or for none
   --; nobody else writes on that branch. If the thread holds the reservation instead, the copy to
   renumber is the one the join wrote itself, which `--finish` shows as `BR003`. A number a merged
   thread created is never renumbered at the join: one found wrong after the merge -- `BR001` or
   `BR003` at `--finish`, `sync` refusing it -- is for whoever decides, who abandons the join
   (`join --abandon`) and opens it again without that thread. A conflict it leaves is two texts of
   which one holds: show both, and ask whoever decides that matter. `--no-threads` opens a join
   with no thread, for what is written only on a join's branch: `.framework/work.yaml`, an
   adoption, the contribution policy, annotations, and what only those who decide write -- a
   release, a change `verified`, the freeze of the evaluation plan, an approval, a mandate
   withdrawn or the forecast of an approved one, and from 4.11.0 a mandate no thread held written
   `implemented` once its code is merged (step 5); from 4.12.0 a hotfix (*The hotfix*, below); and
   from 4.13.0, on a join with threads, the mandate of each thread it brings in with its code,
   written `implemented` at step 5.
2. **The texts**, in the join's worktree, and no act of decision. Anchor every entry the to-do
   lists with no anchors -- its `affects`, the finest section it touches: from 4.11.0 pinned
   that list is an exception, long the first time, short after: what a join anchors leaves it,
   and what reaches the main line with no `affects`, or stops waiting, enters it for the next
   --, and every change a thread brought with no `affects`, which `join` showed. Put back as the
   main line has it a `hotfix: true` a thread wrote or took off, which `join` showed as a
   `BR006`: a thread's change is a draft a join approves as a mandate, and a hotfix is whoever
   decides' to call (*The hotfix*). Rewrite the
   living documents from the effects of the threads merged, each target once, and nothing an
   effect does not say but the cascade of a decision whoever decides means to accept -- the
   entry moved, the documents it obliges --; those a thread drew from a delivery without
   asking, from 4.12.0 pinned, or no version that reads, are read beside its
   `_filoni/<slug>/consegne/<CHG>/documentazione.md`. Where two threads meet, the cards say it:
   `python3 "$F/work.py" --root <join worktree> meetings --out <your scratchpad>/incontri`, once
   the threads are merged and again once the cascades are committed, writes one for each place
   two threads, or a thread and a cascade, meet -- one target, or one section inside another;
   an entry whose state two threads changed; two elements two threads created from the same
   one --, each text with its thread, who holds it, the commit, the day, `Da:` and `Perché:`.
   Two texts that say the same become one, and you say so; two that differ are put to the
   person, each with where it comes from, asking which holds; the cards go to the review
   (step 4). Confirm or change, with
   the person, the choices of form the threads took by default, which `join` showed -- a change
   is written here, as an edit of what the thread wrote --; carry a delivered contribution
   policy into `.framework/`; sort the parking lot; write the text of a release, and the `EVR`
   the freeze of the evaluation plan writes. Ask the person
   which approved mandates no thread holds have their code merged -- one that waited for
   another on the same code, one nobody opened --: the delivery of each is a text, written
   here -- `documentazione.md`, and a `contribution-policy.json` delivered, carried to
   `_filoni/ricongiungimento-<n>/consegne/<CHG>/`, what it says written in the living
   documents, a `verifica.md` written into the change's §Verification, the policy carried
   into `.framework/` as above; its folder in the exchange is closed once the join has landed
   (step 6) --; below 4.13.0 pinned, a delivery that is on the machine of whoever wrote the code
   comes as `references/contributions.md` says (*A delivery from another machine*), and one that
   has not arrived holds nothing back: the mandate lands, and its delivery comes at a later join.
   From 4.13.0 pinned, or no version that reads, nothing is carried by hand: a delivery is carried
   here only from this machine's exchange, and one that is not there holds nothing back, the
   mandate landing without it. Where the project pins 4.12.0 or later, or no version that reads,
   and a thread or a parking branch brings a new increment or an effect on an `RMP.md` -- the
   targets of its `effetti.md` say it --, read back to the person the stages of that roadmap in
   the compact view of `cycle` (Step 5b) -- the stages in their sequence, the increments of each,
   the new ones with no stage -- ask whether the sequence still holds and where each new increment
   goes, and write the `delivery_stages` here. A roadmap with no `delivery_stages` yet has nothing
   to read back: ask whether to set its stages up; on a yes, do it here as `cycle` says for the
   first time (Step 5b) -- proposed from its body, the lines quoted, what the digest will show the
   day after, written on the person's confirmation --; on a no, ask again only when a later join
   brings another change to that roadmap. A join whose threads and parking branches leave the
   roadmaps as they were asks nothing. The cascade of each act of step 5 that obliges texts -- a
   decision to accept, a mandate whose delivery is carried -- is committed on its own, before the
   rest, its title `join: the cascade of <ID>`, so that leaving that act is the revert of that
   commit, which gives back the text the review read (step 4). Then
   `python3 "$F/work.py" --root <join worktree> check`, which regenerates the views -- its exit
   1 read as in *Before each push* --, and commit the rest with them: the rehearsal starts from
   tracked files with no change, and the reading of what a join brought counts only what lies
   between the merge base and HEAD.
3. **The rehearsal.** Note the untracked files the worktree already has (`git status
   --porcelain --untracked-files=all`). Apply, without committing them, the acts of decision the
   person said they mean to take (step 5); run `check`, and keep what it says in a file in your
   scratchpad, outside the worktree. Then take away the acts and what `check` wrote, the files
   `git status` shows now and did not before: those tracked or in the index with `git restore
   --source=HEAD --staged --worktree -- <files>`, which takes away a file HEAD does not have
   too, the untracked ones deleted. What speaks only from a state -- `CHG002` and `CHG003`,
   from `approved` up -- speaks before the review.
4. **The review** the preamble asks for, before anybody decides -- from 4.12.0 pinned, or no
   version that reads, whole, on the diff of the join's branch against `origin/main`:
   everything the threads bring and what the join writes, the living documents rewritten
   included, and a join that brings only states reviewed too --, with the outcome of the
   rehearsal, the folder of the meeting cards, the hotfixes `join` listed to review in full,
   which are not in the diff -- the path of each `CHG`, read whole --, the log of each thread and
   parking branch merged, `_filoni/<slug>/revisione.md` in the join's worktree, whose substance
   left open is reviewed again against that diff, and
   each delivery a thread drew effects from without asking,
   `_filoni/<slug>/consegne/<CHG>/documentazione.md`, beside which those effects and what the
   join rewrote from them are read; and, from 4.13.0 pinned, or no version that reads, each
   diff `join` wrote in `--out` at step 1, the commits a merge request brought after its
   delivery, read with the documentation of its thread or parking branch: where that does not
   cover them, the objection is of substance -- on an approved hotfix, whose change is not
   corrected, what its code does beyond it is a new `CHG` deriving from it. A merge request
   merged at another head on a forge `join` does not call has no diff: whoever decides has
   looked at its commits there, at step 1. A substance objection is settled by whoever decides: the
   text corrected, or the act it concerns left for a later join -- the element in draft or
   proposed, or, for an act of step 5 on an element past them, as it stands --, with what step 2
   wrote for it taken back: `git revert --no-edit` of its cascade's commit, which gives back
   text the review has read and is not reviewed again -- write in the log the commit it
   reverted. A revert that conflicts is resolved, and the lines it resolves are a correction;
   with no pass left it is not resolved but dropped, `git revert --abort`: the act is taken as
   the review read it, or, where the review holds an objection on it, the join is abandoned
   (`join --abandon`) and opened again. The corrections go to the reviser again, relaunched
   with them, as `agents/reviser.md` says. The reviser's log goes to
   `_filoni/ricongiungimento-<n>/revisione.md`; commit the corrections, the reviser's and those
   of whoever decides, with the log, since the reviser runs no git -- in a join with no thread
   the log is all `_filoni/` holds, and `--finish` removes only what is tracked.
5. **The acts of decision**, committed with the views `check` regenerates: the changes in draft
   the person chooses approved, with their name in `approvers` -- those of the threads and those
   the to-do lists to approve --; the decisions a contributor proposed accepted, which `join`
   showed and the to-do lists, or left; a classification accepted; a change `verified`, or
   withdrawn, naming in `withdrawn_by` the accepted `DEC` or the `CHG` that replaces or absorbs
   it; the freeze of the evaluation plan; and from 4.11.0
   the mandates no thread held, whose code is merged, written `implemented`, with each `KI` the
   to-do lists that mandate alone for closed; from 4.12.0 a hotfix whose code is merged written
   `implemented` the same way, with the known issues it repairs; and from 4.13.0 pinned, or no
   version that reads, the change of each thread and of each hotfix's parking branch brought in
   with its code -- a `merge-request:` line in its merge, which `join` showed -- written
   `implemented`, with each `KI` the to-do lists it alone for closed: `--finish` and `--merge`
   refuse while one is not, and to leave its thread out is `join --abandon` and a join without
   it. States and names only: the
   texts they oblige were written at step 2 and the review read them, so this commit is not
   reviewed again. An act the
   person no longer takes here has its cascade taken back as at step 4, by the revert of its
   commit, before this one.
6. **The check, and the landing.** `check` once more; then `join --finish --who "<name>"
   --review full`, which removes `_filoni/`, signs the branch and writes beside the signature
   `Revisione: completa` -- the review it had, which tells the next join which hotfixes are still
   to read whole; `--review one-pass` in a lightning join, and with no `--review` the mark of the
   last signature -- one pass where the join approved a hotfix after it --, or one pass where
   there is none. Read the `BR` findings it prints back to the
   person, in plain words, and ask "procedo?". The person's yes in the chat is the gesture that
   lands the join, with their name, and you never give it in their place: then `join --merge
   --who "<name>"` merges it into the main line, by a merge of its own, and releases what it
   landed. From 4.13.0 pinned, or no version that reads, `--merge`, after its own refusals,
   first merges on the forge the code of each thread step 1 let in -- `gh pr merge` at the
   delivery's commit, `--match-head-commit`, the way step 1 found; one merged there at that
   commit already is not merged again --, then lands the documentation: one yes for both, so
   that no `implemented` reaches the main line before its code. Read back, with the `BR`
   findings, what it will merge. A commit after the signature -- a `sync` because the main line
   moved, a correction -- is signed again by `--finish`, and `--merge` refuses a branch whose
   last commit is unsigned -- and, from 4.13.0, one signed by a plugin older than 4.13.0, whose
   signature lacks the lines its merges carry: `--finish` again.
   Once it has landed, close the delivery of each mandate carried at step 2 and written
   `implemented` at step 5: `python3 "$F/exchange.py" --root <main checkout> integrate <CHG>
   --commit <the commit of its cascade at step 2>`, which the main line now holds and which
   still holds the
   `_filoni/` that `--finish` removed. One whose act was not taken keeps its folder in
   `in-arrivo/`. A join abandoned has moved nothing out of `in-arrivo/`.

When it goes wrong:
- **the main line moved before `--merge`**, which refuses: `sync` in the join's worktree, `check`,
  `--finish` again with the same `--review`, the `BR` read back and "procedo?", and after the yes
  `--merge` again;
- **the main line moved while `--merge` pushed**: first `git -C <main checkout> reset --keep
  HEAD~1`, as `--merge` says -- with the sandbox it writes outside the session's worktree, and is
  the person's --, then as above;
- **the remote refused the push** -- a hook, a protection rule --: the person looks, then
  `--merge` again, which pushes the same merge and releases;
- **the push of the main line did not go**, and the person pushed it: `join --close` releases
  what the join landed;
- **the forge refused a merge request at `--merge`**, from 4.13.0, or left it for later -- a
  merge queue --: the documentation did not land, and what was merged stays merged, which
  `--merge` says. Once the forge allows it, or says it merged at the delivery's commit, `--merge`
  again, which counts it merged; or `join --abandon`, and at the next join what was merged
  counts as merged, and one left behind its base, or in conflict with it, waits there for its
  code brought up to date (*The code behind its base*). One merged on the forge at another head
  since step 1, or closed: `join --abandon`, and the next join reads its commits, or the thread
  waits for its new delivery;
- **a join that will not land**: `join --abandon` drops it.

`--merge` is the one time anything writes the main line -- and, from 4.13.0, merges the code of
the threads on the forge --, and the person's yes is its gesture. A
join takes longer the more threads it lands: for each it reads the branch and runs the
validator. Changing `.framework/work.yaml`, giving or taking back a delegation, adopting a
framework version and annotating an expected finding are for an admin alone.

**Delegation.** An admin who will be away gives a delegation:
`work.py delegate --to "<name>" --who "<admin>"`, taken back with `work.py revoke --to "<name>"
--who "<admin, or the delegate>"`.

## The hotfix

From 4.12.0 pinned, or no version that reads, for an admin, a deputy or a delegate: whoever decides
says "facciamo una hotfix", and you carry the lightning join, with the commands as for any join
(`cycle`, *A hotfix*, says what a hotfix is and what its code goes through):

1. `join --who "<name>" --no-threads`; the hotfixes it lists to review in full are not this
   join's, whose one pass reads the hotfix alone: they wait for the next join with the whole
   review;
2. in its worktree, the `SIG` in the `LOG` where the signal is not there yet, the `ICG` with its
   true classification and a short `CHG` deriving from the signal, with its three
   sections, `hotfix: true` and its `affects`, each number reserved as you reserve any; where the
   project has a contribution policy, the change's block with its code prefixes, the anchors on
   which the to-do makes other mandates wait; routed `architecture` or `both`, a minimal `DEC` in
   its `derives_from` (`CHG005`);
3. the review, one pass, before anybody decides; then the approval, asked and written with the
   views `check` regenerates; then the brief, in the same join, with the rules of `cycle` (Step 6)
   and one pass of review too -- the one exception to the brief of the round after, since a hotfix
   has no thread and cannot wait for one; from 4.13.0 a hotfix's brief rewritten on another
   machine that launches it has one pass as well (below);
4. `check`, `join --finish --who "<name>" --review one-pass`, the `BR` read back and "procedo?",
   and after the yes `join --merge`;
5. from 4.13.0 pinned, or no version that reads, the launch on the hotfix's brief, proposed as
   for a thread (*A thread with a change, and its code*), to whoever decides, who carried the
   join -- not the only way: an approved hotfix anybody may launch, below. First its parking
   branch, from the main line `--merge` has just moved: `work.py --root <documentation> open
   --who "<name>" --branch hotfix-<home>-<change>`, with the name the to-do gives beside the
   hotfix, which opens `parcheggio-hotfix-...` and is the claim; where it is there already,
   somebody else took the hotfix, `open` refuses, and you do not launch, and say so. Under the
   sandbox the session of the lightning join writes in the join's worktree and not in the
   branch's: from `open` on, everything goes on in a session started in the branch's worktree,
   as for a thread, and say so; without it the same session may go on. The launch has `--root`
   on that worktree, and its stops, resumes and delivery go as for a thread, the merge request
   citing the `CHG`. The join's worktree, which `--merge` says to remove, is removed once the
   session started in it is closed, since the guard reads its folder from there.

The next join with the whole review reads its `CHG` again, and its delivery when it comes; the
brief keeps its one pass. `join` lists the `CHG`, from the `Revisione:` line `--finish` writes,
until a join signed `Revisione: completa` lands. After the lightning join a
hotfix is no thread to take: the to-do lists it apart, `open` refuses it -- from 4.13.0 naming
its parking branch, the claim of whoever launches its code --, a mandate on the same
code prefixes waits for it, and whoever decides writes it `implemented` at the first join after its
code is merged, at step 5, with the known issues it repairs; the to-do says the days since each
was approved. An objection on a hotfix already in production is a new `CHG` deriving from it, never
a withdrawal; one whose code will not reach production whoever decides withdraws at a join,
`withdrawn_by` the `DEC` that says so, and the mandates it held stop waiting, the known issues it
repairs threads to take again. `hotfix: true` is whoever decides', written on a join's branch,
here or at the first join after an emergency merge: written or taken off on a thread or a parking
line it is a `BR006`, and a contributor's change stays a draft a join approves as a mandate.

From 4.13.0 pinned, or no version that reads, the delivery of a hotfix goes on its parking
branch, whoever launched it, in `_filoni/<slug>/consegne/<CHG>/`: `documentazione.md`, the
effects drawn from it as on a thread, `verifica.md`, `mr-link.txt` with the line
`Merge request: <link> @ <commit>`, the merge request opened before on the person's yes, and
`evidenze/`. Before bringing it onto the branch, read the text files `evidenze/` holds -- logs
and outputs enter the history of the documentation, which `--finish` does not take away --: a
file that carries the value of a credential is said to the person, who deletes it or cleans it
in the exchange -- `evidenze/` with it, where it is left empty: git keeps no empty folder,
and `integrate` would find it delivered and not on the branch --, and only then is the delivery
brought onto the branch. An image is not read:
what a screenshot shows enters as it is. Then commit, close the launch with `integrate <CHG>` on
the branch, and push. The branch lands at the first join after its code
is merged, whoever runs it -- merged at another head, its commits read as a thread's --, and until
then it waits; there whoever decides carries the verification and the link from the delivery
folder into the change's §Verification at step 2, a text the review reads, and writes the change
`implemented` at step 5, with the known issues it repairs. A parking branch named `hotfix-...` is
read as a hotfix's, landing only
with that line: open no other one so, and work on one opened so before the adoption goes on a
parking branch named otherwise.

An approved hotfix, from 4.13.0 pinned, or no version that reads, anybody may launch, a
contributor too: `open --thread` refuses it and names its parking branch, which you open as
above, the claim, launching from its worktree. Where this machine's exchange has no brief for
it, write it there, with the rules of `cycle` (Step 6) and one pass of review, as in the
lightning join, naming the `CHG` in that worktree. Launched so on another machine, the brief the
lightning join wrote stays in the exchange of whoever decides with nothing delivered, which
`EXC002` reports once the hotfix is `implemented`. Whoever decides closes it with `exchange.py
--root <main checkout> integrate <CHG>`, a folder with nothing delivered moving with
`parts: {}`: when `EXC002` reports it so, or before, while the hotfix is `approved`, once the
to-do shows its parking branch taken and this machine has no worktree of that branch beside the
documentation -- somebody else opened it, elsewhere.

With a join already open: where its whole review is done -- step 4, the corrections read again
included --, the hotfix is written on it, reviewed in one pass on the hotfix alone, and the join
closed at once, `--review one-pass`. Where it is not, the hotfix goes the way of the next
paragraph; where that way is closed -- a contribution policy for the code with no
`exception_reviewers`, where `no-chg` never passes (`AUT006`) --, say how far the review is, and
whoever decides chooses: finish it, where it is near the end, and the hotfix enters there; or
`join --abandon` and the lightning join, the threads staying ready for the join after, what was
rewritten written again.

When nobody who decides can be reached, or the join open is not reviewed whole, the code goes with
`no-chg: hotfix <reference>` in its merge request; below 4.13.0 pinned, at the first join whoever
decides writes, at step 2, the `SIG`, the `ICG` and a `CHG` with `hotfix: true` that says it was
authorized after, approved and written `implemented` at step 5. From 4.13.0 pinned, or no version
that reads, it is launched too, by whoever implements it, from the documentation: first its
parking branch, `open --who "<name>" --branch hotfix-<reference>`, the reference in lower case
and dashes, pushed empty, its claim; from that branch the number of its `CHG` reserved, as any
number is, which its brief -- one with no `CHG`: the reference, what breaks, the guardrails, the
delivery (`cycle`, *A hotfix*), reviewed in one pass -- names, and its folder in the exchange
carries; then the first
call from that worktree, `code <CHG> --repo <code repository> --no-chg "hotfix <reference>"`,
and the rest as above, the merge request saying `no-chg: hotfix <reference>`. The delivery goes
on that branch as above, and the `CHG` is written by the join that brings the branch in, once its
code is merged -- not the first join after the merge: a branch late, the `CHG` waits for it --:
at step 2 the `SIG`, the `ICG` and the `CHG` with the number reserved, `hotfix: true` and that it
was authorized after, before the effects the branch brings, approved and written `implemented`
at step 5. Until then `EXC001` says the folder of a `CHG` the documentation does not declare yet,
a warning.

## With the sandbox

`references/workstation.md` gives the recommended configuration of the Bash sandbox and says which
commands of this skill do not succeed under it. Those stay the person's to run: say the command,
and do not retry it outside the sandbox. From 4.13.0 pinned, or no version that reads, a third
entry of `excludedCommands`, `python3 *exchange.py* code *`, lets every call of `code` out -- the
first, which creates the worktree beside the code repository, `--join-base` with it, `--launch`,
`--resume` and `--status` --, each run alone with the absolute path written out, as `reserve`
and `renumber` are; where it is missing, give the line to paste. The commands around it stay
the documentation session's, in view, and under the sandbox the person's, given as lines to
paste, since they write in the code's worktree or reach the network: the push of the branch and
of the code session's commits, the merge request, the preparation of the worktree, the join of
the two sides of a branch and each `git rebase --continue`, its abort, the regeneration of the
files the brief says are generated, the return to the remote, the commit that concludes a merge
of the base and its push.

## What you must not do

**Do not write the main line**, nor merge a thread or a join into it by hand: a join landed by a
fast-forward, or by a merge whose message does not name its branch, is read as text that came
outside a join, and one with commits after its signature has those read the same way. **Do not rewrite a living
document on a thread**: write the effect. **Do not take a decision as a contributor**, nor approve a
change on a thread's branch. **Never force a push** -- the one exception, from 4.13.0, is the
push with lease of a code branch re-applied on its base, which `code --join-base` prints and the
person approves (*The code behind its base*) --, and never delete a claim or a reservation by
hand: no hook stops either, and the project's `ci/refs.yml`, copied from 4.12.0, opens an issue
for a reservation deleted or moved, a delegation moved and a work branch pushed with force.
**Do not run `attest.py` to attest**, as the preamble says, even where the rereading is
optional: `--commit` alone, which writes no stamp, you run once the person has attested.

## Handing back

Say which thread, which branch and worktree, what was written on it and what as effects -- those
drawn from a delivery without asking, from 4.12.0 pinned, or no version that reads, target by
target, for whoever followed the code to correct by a commit on the branch, pushed, before the
join --, what the checks of the branch
said, and what the review left standing. From 4.13.0 pinned, or no version that reads, for a
change also its code: the code's worktree and branch, where its launch stands -- running,
stopped on what, delivered, closed --, the merge request with its link and the line written in
the verification, what waits for the person -- a stop to answer, a command to paste -- and
whether the thread is ready; for a hotfix, its parking branch and whether its code is merged.
For a join: the threads landed and kept, the effects
applied, what the person decided at the join, and what the main line holds now -- from 4.13.0
also the merge requests merged on the forge, and those that wait, each with its way out.
Then the two closing blocks the preamble describes, last. The next steps are derived: the to-do's
threads to take, the thread that waits for this one, the join when the to-do suggests one.
