# The additive mode

A project is in the additive mode when `.framework/work.yaml` on its main line declares
`mode: additive`. Every skill, and every session working on the documentation, reads this file
before writing in such a project: it prevails over the class table of the preamble and over the
cascade of `routing-table.md`, which say to edit a living document in place and to carry a write
into the documents it obliges in the same pass. Here those become pending effects.

Why the mode exists: several people work on the documentation at once, each on a thread the
to-do computes, and a living document rewritten on two branches is a conflict that only a person
can settle. So during a thread nobody rewrites a living document: what it should say waits, as
an effect, for the one moment shared documents change -- the join, which an admin runs.

## Where you write

Never on the main line: it moves only at a join. On the branch of a thread, opened with
`work.py open --thread`; or, for what belongs to no thread -- new information, a new open
decision or issue, a line in `LOG`, a parking line --, on a parking branch, opened with
`work.py open --branch <slug>` and no element, and checked as a thread's is. Opening a branch
takes the person's name: a session with nothing open asks them first, and the `contribute`
skill does the rest. A parking branch is one short piece of work: `open` pushes it empty, and
from its first commit pushed it is ready and the next join lands it whole -- but, where the
project pins 4.13.0 or later, or no version that reads, a hotfix's, named `hotfix-...`, ready
with the line of its merge request and landed once its code is merged (*What a code session
delivers*) --, so its commits are pushed -- and the main line brought in with `sync --no-push` --
only when it is complete. Given up, it is deleted on the remote and where it was opened, by
whoever opened it or by an admin. It claims nothing and forecasts nothing, so at the join every
effect it wrote is shown as outside the forecast. On a thread's branch goes what belongs to that
thread's work; what does not, a parking line found on the way included, goes on a parking branch.
The branch of a join is where living documents are rewritten, and where what only those who
decide write goes: a release, a change `verified`, the freeze of the evaluation plan, an
approval, a mandate withdrawn, the forecast of an approved one, and from 4.11.0 a mandate no
thread held written `implemented` once its code is merged; from 4.12.0, a hotfix, in a lightning
join (`contribute`, *The hotfix*), and written `implemented` at the first join after its code is
merged, since no thread takes it; and, where the project pins 4.13.0 or later, or no version that
reads, the mandate of each thread the join brings in with its code, written `implemented` with
the `KI` it repairs closed, since the join merges that code -- the thread writes the line of its
merge request instead (*What a code session delivers*). An admin opens one with
`work.py join --no-threads` when no thread is ready.

| Written directly on the thread's branch | Written as a pending effect |
|---|---|
| new files: a `DEC`, `CHG`, `ICG`, `EVR`, `REL`, `RLM`, and any other new artifact -- a `PRB`, `HYP`, `EVD`, `CMP`, `DFB`, `SD`, a new `DC` | every other change to a living document: `ARC`, `PBR`, `WF`, `GLOSSARY`, `DC`, `RSK`, `RMP`, `EVP`, `RB`, `IMP`, `COMMITMENTS`, `STACK`, `PLATFORM`, `AGENTS.md`, `product.yaml`, and the **body** of an `OPEN` register: an entry moved from §1 to §4, an entry rewritten |
| new entries in the open registers -- in `entries:` and their section --, lines in `LOG` and `ING`, which are append-only, lines in the parking lot | a new key in another register that is a map: `commitments`, `risks`, `terms` of `GLOSSARY`, `stack`, `increments` and, below 4.12.0 pinned, `delivery_stages` of `RMP` -- from 4.12.0 pinned, or no version that reads, a thread or a parking line does not touch the `delivery_stages`: the join asks whoever decides |
| changes of state: `status` and `closed_by` of an entry, `status` of an immutable -- but a `CHG` withdrawn is a join's, below, and from 4.11.0 so is a mandate no thread holds written `implemented`, above, and from 4.13.0 the thread's own mandate written `implemented` and a `KI` it repairs closed, but for a change with no code to merge --, the verification section of a `CHG`, from 4.13.0 with the line of its merge request | |
| `last_review` and `review_scope`, when a person attests a reading with `attest.py` | |

`BR005` reports, on the branch of a thread or of parking, a living document changed in a way
that is not additive. Never on those branches, and only on the branch of a join, with no thread
if need be: `.framework/work.yaml`, the adoption of a framework version -- `migrate.py --adopt`
run in the join's worktree --, `.framework/contribution-policy.json`, the annotations in
`.framework/expected-findings.yaml`, a `CHG` moving to `approved`, a `CHG` moving to
`withdrawn` or a new `withdrawn_by` on one, and the `affects` of an approved `CHG`. The one exception is the
commit that first writes `mode: additive`, which lands as any commit did before the mode; the
section of `AGENTS.md` on threads and joins arrives with the next `--adopt`, on a join's branch.

A new entry, and a new `CHG` in its front matter, carries `affects`: the documents, or the
sections, it is expected to touch -- `products/<p>/ARC.md#current`, `products/<p>/OPEN.md#OD-042`,
or a path alone for a whole document. It is the one input of the threads a person writes -- but
for an approved `CHG` from 4.11.0, below --, and a forecast: the to-do puts in one thread the
entries that forecast one anchor, or two anchors of one document one of which is inside the
other by name, `AFF001` reports an anchor that does not exist, and the join shows an effect
written outside what its thread forecast. A section is an anchor on any living document when its
marker, `<!-- section: <id> -->`, is above its heading, with only blank lines between; a section
inside another is named after it, `<id>-<rest>` -- `delta-inc-17` inside `delta` --, and the two
meet, by name. `AFF001`, and `EFF001` for an effect, hold the name to the headings both ways: a
marked section inside another by its heading and not named after it is not an anchor, nor one
named after another and not inside it -- `scope-out` beside `scope` is renamed where it is in
use. So an anchor as wide as a section meets everything under it: anchor
at the finest section the work touches. The keys of a map -- an increment, a tool of `STACK`,
a term -- meet only themselves, not the section that shows them. A marker is an edit of a living
document like any other: on a thread an effect, which the join writes -- `BR005` reads only that
lines were added, and does not see one written directly --; and an `affects` names it once a
join has brought it to the main line, or `AFF001` reports it there. An entry with more anchors
than `thresholds.od_affects` is worth proposing to split, and `requirement`, `resolve` and
`cycle` propose it. From 4.12.0 pinned, or no version that reads, the skill that writes an entry
or a `CHG` writes its `affects` always, from the text, at the finest section, and never leaves it
empty, and on a thread notes it in `scelte.md` (below).
The `affects` of a `CHG` in draft is anybody's to write; that of an approved
one is written or corrected by who decides, at a join, and is fixed once it is past `approved`
-- `BR006` says it moving anywhere else.

**A mandate is a thread by itself**, where the main line pins 4.11.0 or later, or no version that
reads. A `CHG` approved never shares a thread with a decision or an entry, nor with another
`CHG`: what two mandates change at the same time is code, so the to-do reads the code prefixes
of their blocks in the contribution policy, and not their `affects` or the `documents` of the
block. Two whose prefixes meet are two threads, and whoever opens one makes the other wait until
the join lands it -- the narrower the code prefixes of a block, the fewer wait; from 4.12.0 an
approved hotfix, which no thread takes, makes those whose prefixes meet its own wait the same
way, until a join writes it `implemented`, or withdraws it where its code will not reach
production (`contribute`, *The hotfix*); the field is whoever decides', and a thread or a parking
line that writes it or takes it off is a `BR006`. Two people
opening two such mandates in the same minute both pass that check, on two claims: the `open` whose
push lands second says it, unless its fetch or its computing of the to-do after the push fails;
the one that landed first may be told by nothing; who goes first is theirs to agree. A `KI` an
approved `CHG` derives from is not waited for -- the change is what repairs it --, unless an
increment of the change requires it, one it carries or one that lists it in `changes`: then it
is a wait, the order a roadmap wants. An open one not waited for is what the change repairs; a
parked one nothing requires is neither waited for nor listed. While an approved change repairs
a `KI` and is to do, the issue is no node of its own, even where another change waits for it,
and the to-do lists it with every mandate to do that repairs it; while every change that
repairs it waits, the issue is a node, which anybody may take, so that nothing a change waits
for can wait on it in turn. Below 4.13.0 pinned the thread of the change closes it on its
branch -- `status: decided`, `closed_by` the change --, and where the project pins 4.13.0 or
later, or no version that reads, the join that brings the change's code in and writes it
`implemented` -- but for a change written `implemented` on its thread's branch, one with no
code to merge among them, whose thread closes it as before --; either one when the to-do lists
that mandate alone for it -- a hotfix's, whoever decides at the join that writes the hotfix
`implemented` --, so that of several listed together none closes it while another is still
listed; one its mandates land without closing is a node again. A mandate's thread does not claim it,
nor has it in its forecast at the join, and its own
`depends_on` and `decide_with` are not followed while it is in their hands. One a thread claimed
before -- while its change waited, before the change was approved, or before the adoption -- is
named with that thread, which releases its claim (`work.py release <KI> --who "<name>"`): the
mandate's thread closes it, once the code is merged -- from 4.13.0 the join that brings that
code in, but for a change written `implemented` on its thread's branch, as above; a hotfix's,
whoever decides, as above --, and two branches never write its row. These closings, and a
mandate written `implemented`, rest on who writes them, on whatever branch: no check reads them
-- but, from 4.13.0, `join --finish` and `--merge` refuse while a change the join brings in with its
code is not `implemented` on the join's branch, and `join` asks whoever
decides about one written `implemented` on a thread's branch with no line of its merge request.
The change still waits for the decisions and the changes it derives from, and for what its
increments require. So a mandate whose code is merged, and whose closing is pushed on its
branch, is ready -- from 4.13.0, one whose verification carries the line of its merge request,
pushed, its code merged by the join --, and the next join that lands the ready threads lands
it; one whose code was merged while no thread held it -- it waited for another on the same
code, or nobody opened it -- is written `implemented` by who decides, at the first join after
the merge. The other nodes meet only nodes of their kind -- decisions with decisions, the rest
with the rest --, and an entry with no `affects` is out of the threads, listed to be anchored: an
exception the next join clears, by writing its anchor, and that a skill writing an entry does not
leave behind. Below 4.11.0 the threads are computed as they were: a node with no `affects`
touches its whole product, and a mandate meets entries and other mandates by its `affects` and
its whole block.

## The effects

One file per thread, `_filoni/<slug>/effetti.md` on its branch, where `<slug>` is the branch's
name after the prefix. One heading per target, and three lines under it, each once:

```markdown
## products/beta/ARC.md#current
- Da: DEC-110, CHG-031
- Diventa vero: il catalogo si legge dal servizio X, non più dal file Y.
- Perché: DEC-110 §2; atlas-svc@abc1234 src/catalog/
```

The target is the document's path from the root of the documentation and, after `#`, the anchor:
the key of an entry in a register that is a map (`entries` of an `OPEN`, `commitments`, `terms`
of `GLOSSARY`, `risks`, `stack`, `increments` and `delivery_stages` of `RMP`), or the id of a
`<!-- section: ... -->` marker that labels a heading; no anchor where the effect is on the whole
document. An effect stands within its thread's forecast when its anchor is forecast or is inside
one forecast by name; one on a section is within a forecast on its whole document, and not the
reverse. The join names the other threads whose forecast meets it, either way; from 4.12.0
`work.py meetings` writes, outside the repository, one card for each place two threads meet,
within their forecasts or not, for whoever runs the join to put two texts that differ to
whoever decides, and for its review (`contribute`, the join). `Da` names
the identifiers it comes from, `Diventa vero` what the document should say, `Perché` where that
is written. The labels are Italian, as the fixed names of the exchange are, and `EFF001` reports
a file that does not read. The file is edited freely while the thread is open; `_filoni/` is not
scanned as documentation, and `join --finish` removes it, leaving it in the history.

Between two joins the living documents are behind. Before reading one as current, look at the
effects waiting on it: the to-do lists them per document (`skills/audit/scripts/todo.py`).

## The choices of form

Where the project pins 4.12.0 or later, or no version that reads, a session on the branch of a
thread or of a parking line does not ask what is placement, form or the classification of an
`ICG`: it takes the default, writes it, and notes it in `_filoni/<slug>/scelte.md`, one row of
one table per choice:

| Scelta | Preso | Alternative | Perché |
|---|---|---|---|
| l'incremento di CHG-031 | INC-004 | INC-005; nessuno | le decisioni da cui deriva vengono da INC-004 |

The defaults: the destination the routing table gives; the anchor of what the session creates,
from its text, never empty; the classification of an `ICG` that the rules of `routing` give; the
increment of a `CHG`, the one its decisions or issues derive from, none where there is not one
only. The stages of the roadmap are not touched on these branches: `delivery_stages` is
living, and the join asks whoever decides, when a thread or a parking branch brings a new
increment or an effect on the roadmap -- the stages read back in the compact view of `cycle`,
and written on the join's branch (`contribute`, the join); a roadmap without them is asked
whether to set them up, as `cycle` does the first time --; a join that leaves the roadmaps as
they were asks nothing. What is substance stays a question, on the thread as before: a
contradiction with what is written, what must not change, the strength of a piece of
information, a real decision, a content of the product no source gives. `join` shows the
choices of each thread beside its effects, with what it brought with no anchor and the to-do's
whole list to anchor; whoever decides confirms or changes them on the join's branch, where the
whole review reads them. The labels are Italian, as those of the effects; every cell is written,
`nessuna` in `Alternative` where there is none; a `|` inside a cell is written `\|`. `EFF002`
reports a file that does not read, and `join --finish` removes it with `_filoni/`, leaving it
in the history.

## What a code session delivers

A code session works in another repository and writes nothing in this one. In the additive mode
the brief asks it for `documentazione.md` in the element's folder of the exchange, beside
`verifica.md`: what the documentation should say after the change, in its own words. The
documentation session of the thread copies it to `_filoni/<slug>/consegne/<CHG>/documentazione.md`,
commits it, and draws the effects from it with the rules of the `requirement` skill -- proposed
line by line, confirmed once; from 4.12.0 pinned, or no version that reads, written without
asking and said in the session's last answer, target by target, after the push, for whoever
followed the code to correct by a commit on the branch, pushed with the checks and the review
of any push (`contribute`), before the join, a row of substance still a question --, touching
no living document. The check that holds is the join's, whose review
reads them beside the delivery. A `contribution-policy.json`
delivered goes to the same folder, not into `.framework/`: an admin carries it there at a join.
The delivery is copied and not moved, so the folder goes to `integrati/`: once the copy is
committed, and a `verifica.md` delivered written into the change's §Verification, which the
thread writes, `exchange.py --root <thread worktree> integrate <CHG>` moves it and writes its
`INTEGRATO`, which names `documentazione.md: _filoni/<slug>/consegne/<CHG>/` in `parts`. Where
the project pins 4.13.0 or later, or no version that reads, the verification carries the line
of the code's merge request, `Merge request: <link> @ <commit>` -- the link of `mr-link.txt`
and the commit of the code's branch the delivery was verified at, forty characters, the last
such line counting where there are several --, written once the merge request is open and
before `integrate`, which closes the launch; a change asked for after is a new launch, whose
delivery `integrate` joins to the first, one block more in `INTEGRATO`.

The exchange is one machine's, and the thread's branch is what carries the delivery to the
others: it reaches the join committed on the branch. Below 4.13.0 pinned, the usual way is that
whoever takes a thread with a change runs its code session too, on the same machine -- a
recommendation, not a role, and whoever writes only code does not enter `people` for it. When
somebody else writes the code, the brief is carried to that person's machine, with the absolute
paths of this one; the delivery is carried back by hand to the thread's machine, and its
`risorse.md`, which describes the machine it came from, goes as `references/contributions.md`
says (*What a mandate creates outside the repositories*): as it came, from 4.12.0 pinned, or no
version that reads; its rows in a note above the table, below.

Where the project pins 4.13.0 or later, or no version that reads, nothing is carried by hand,
neither the brief nor the delivery: every code session starts from a documentation session,
and whoever holds the thread of a change launches it from the thread's worktree, on the
thread's machine (`exchange.py code`, `contribute`). Everything goes through the threads, the
documentation the code changes included: the code session proposes it in `documentazione.md`
and never writes it. The code's branch has the thread's name; the documentation session pushes
it and opens its merge request on the person's yes, and the line in the verification makes the
thread ready without waiting for the merge: the join merges the code on the forge before the
documentation lands -- on a forge `join` does not call, whoever decides merges it there, having
read it, when `join` asks at its step 1, so there the code lands before the join's review --, and
writes the change `implemented` (*Who decides what*).

A hotfix has no thread: from 4.13.0 pinned, or no version that reads, its parking branch is its
claim and carries its delivery. The name is fixed, so that two people compute it alike:
`work.py open --branch hotfix-<home>-<change>` for an approved one, the name the to-do gives
beside it, and `hotfix-<reference>`, the reference in lower case and dashes, for one launched
with `no-chg`, whose number is reserved from that branch; opened, it is `parcheggio-hotfix-...`,
and whoever launches the hotfix's code -- anybody, for an approved one -- opens it first, where
a second `open` of the same name is refused. The delivery goes in `_filoni/<slug>/consegne/<CHG>/`
on that branch: `documentazione.md`, from which the effects are drawn as on a thread,
`verifica.md`, `mr-link.txt`, whose last line is `Merge request: <link> @ <commit>`, and
`evidenze/`, which enters the history of the documentation: its text files are read for values
of credentials before it is committed, a file that carries one is deleted or cleaned by the
person in the exchange first -- `evidenze/` with it where it is left empty, which git would not
keep --, and an image is not read; `integrate` on the branch closes the launch. The branch is
ready with that line, and a join brings it in only once its code is merged -- by the project's
own way to production, never by a join --: there whoever decides carries the verification and
the link into the change's §Verification, with the texts of the join, which its review reads --
for a `no-chg`, after writing the change, with the number reserved -- and writes it
`implemented` with the acts of decision. A parking branch named `hotfix-...` is read as a
hotfix's, so no other work goes on one named so. Outside the additive mode there is no branch:
a hotfix's delivery is integrated as always, and one with `no-chg` waits for its change first.

**The way the code is merged.** `merge_method` in `.framework/work.yaml` -- `merge`, `squash`
or `rebase`, optional, read only in the additive mode -- says how a join merges, from 4.13.0,
the merge requests of the threads it brings in. An admin writes it, as every line of that
file, on a join's branch: it enters with the join that brings the project to 4.13.0, as the
`exchange:` line does, its value the admin's. Where it is missing, or the repository of a merge
request does not admit it, the join takes the one way that repository admits, or asks whoever
decides once, `join --merge-method <way>`. A value it does not know is `WK001`, and the key
outside the mode `WK002`. Where it says `rebase`, a code branch behind its base is brought up
to date by re-applying its commits on the base, its push forced with lease on the person's yes,
not by joining the base into it (`contribute`, *The code behind its base*).

The reviewer's log of a thread is `_filoni/<slug>/revisione.md` on its branch, appended to and
never rewritten, and that of a join `_filoni/ricongiungimento-<n>/revisione.md`: both stay in the
history when `--finish` removes the folder. Where the project pins 4.12.0 or later, or no
version that reads, the review on a thread or on a parking line is one pass -- the slips fixed,
the substance left to the contributor or to the join --, and the join's is whole, up to three
passes, before anybody decides: on everything the threads and parking branches bring and on the
substance their logs left open, with the outcome of the join's rehearsal -- the acts of decision
applied without a commit and checked -- and the corrections of whoever decides read again, an
element still found wanting left in draft or proposed for a later join; a brief keeps up to
three passes wherever it is written (`references/preamble.md`, the review) -- but a hotfix's,
from 4.12.0 pinned, which has one, written in its lightning join, and from 4.13.0 pinned, or no
version that reads, one too where it is rewritten in the exchange of another machine that
launches the hotfix, and for the brief of a hotfix with `no-chg`, whose change is written later
(`contribute`, *The hotfix*); and, from 4.13.0, every brief one pass more on the *Commands* the
person changed at the launch proposed, on them alone (`cycle`, Step 6).

## The rereading

With `rereading: required` a join's text owes a reading as any other text does; below 4.12.0
pinned it is the default. With `rereading: optional` -- from 4.12.0 pinned, or no version that
reads, the default, which `required` written overrides -- it does not: `LC006` and `PR005` are
quiet about what a join brought, `LC001` about a document a join brought into being and whose
last change came from a join, and all three on a thread's or a parking branch about everything,
since what is written there reaches the main line through a join. On the branch of a join, from
4.12.0 pinned, or no version that reads, and read with `--base` -- as `join --finish` and
`join --merge` read it --, the documents are read one by one as on the main line after the
merge: what the join brings is a join's, and the rest speaks, so an annotation finds its
finding before the merge and not after.

The warnings of a thread's or a parking branch are the join's to count, from 4.12.0 pinned, or
no version that reads: there `require_all` makes no `AN003`, since a contributor cannot
annotate, but on `EXC005` and `EXC006`, which can say an exposure on the contributor's machine
that the join, run on another one, never sees, and whose way out is the repair; and an
annotation on what `rereading: optional` silences on that branch is not looked for -- nor on
the branch of a join read without `--base`, silenced there as on a thread. With
`rereading: required` `LC006` still speaks on a thread, as a warning, and `sync` draws from it
the readings a merge makes due. `LC009` reminds of a join's text nobody has read once it has waited
longer than `thresholds.unread_days`, and the to-do lists it. Text that reached the main line
outside a join -- a direct commit, a join signed by somebody who does not decide, one landed by a
fast-forward -- is read as before.

## Who decides what

`admins` in `.framework/work.yaml` are the admins; `deputies` and whoever holds a delegation
(`work.py delegate`) stand in for them; the other `people` are contributors. These are
permissions in the documentation repository, not the responsibilities of `PROCESSES.md`. Nothing
blocks. Most rows are seen one way or another: a command refuses (a thread with a decision, a
delegation, the join), a check reports (`BR004`, on who approved; `BR006`, on a mandate
withdrawn or a forecast moved), or the join shows the change
to the admin before merging. Some are a convention nobody checks: releasing somebody else's
claim, deleting an abandoned thread's branch, `.framework/work.yaml`, an adoption or an
annotation written on a thread's or a parking branch instead of a join's, and, from 4.11.0, a
mandate written `implemented` or a `KI` it repairs closed, on whatever branch -- from 4.13.0 but
a mandate written `implemented` with no line of its merge request on the branch of the thread
that claims it, which `join` names and asks whoever decides about; one written so on a parking
branch, or at a join for a mandate no thread held, and a `KI` closed, still rest on who writes
them.

| What | Admin | Deputy or delegate | Contributor |
|---|---|---|---|
| Decide an open decision (a `DEC` accepted, the entry closed), supersede a `DEC`, accept a risk | yes | yes | prepares it as a `DEC` in `proposed`, its measures and alternatives in the body, on a parking branch, deriving from the entry: `join` shows it, and the admin accepts it on the join's branch with its cascade, the entry moved and the documents it obliges -- from 4.12.0 pinned, or no version that reads, the cascade written with the texts, before the review, and the acceptance after it -- or leaves it proposed, where the to-do lists it until a later join accepts it or another decision supersedes it |
| Split an open decision, change its question, dependencies or `affects`; the order and stages of `RMP` | applies the effect at the join; from 4.12.0 pinned, or no version that reads, the `delivery_stages` are no effect: written at the join, on the answer to its question | the same | proposes it as an effect; from 4.12.0 pinned, or no version that reads, not the `delivery_stages`, which the join asks whoever decides about |
| Open a new `OD` or `KI`, parking lines, new information | yes | yes | yes: they become true at the join |
| Classify an impact (`ICG`) | confirms | confirms | writes the draft |
| Write a `CHG` in draft; write the brief of an approved one and implement it | yes | yes | yes |
| Approve a `CHG`, at a join, in bulk if need be | yes | yes | no |
| Withdraw an approved `CHG` that will never be carried out (`withdrawn`, naming in `withdrawn_by` the accepted `DEC` or the `CHG` that replaces or absorbs it), or change its `withdrawn_by`; write or correct the `affects` of an approved `CHG`; at a join. One a thread holds is withdrawn once the thread is released or joined, and one the thread carried out lands `implemented`, to be `rolled-back` if its work must go | yes | yes | proposes a withdrawal as a `DEC` `proposed` deriving from the `CHG`, on a parking branch -- accepted, it is the `withdrawn_by` --, and a forecast on a parking line |
| Mark a `CHG` implemented, close a `KI` fixed by a change or a commit | whoever holds the thread -- from 4.13.0 pinned, or no version that reads, not for a mandate with code to merge: whoever runs the join that brings its code in, on every forge, closing the `KI` it repairs --; at a join, one no thread holds whose code is merged | the same | the same -- from 4.13.0 a mandate's thread writes the line of its merge request instead --; at a join, no |
| Close a `KI` without fixing it | yes | yes | no: it is a decision |
| Freeze the `EVP`, say yes or no to a release, `REL` and `RLM`, `verified` | yes | yes | prepares the evidence |
| Take a thread of work only -- a mandate's thread, `mandate:` in the to-do from 4.11.0, is one --; take a thread with a decision | yes; yes | yes; yes | yes; no |
| Leave one's own thread (`work.py release`); release somebody else's claim (`release --theirs`); delete an abandoned thread's branch | yes; yes; yes | the same | yes; no; no |
| Delete a parking branch given up | yes | yes | one's own |
| A substantive objection of the reviewer | on a decision: decides | the same | on one's own effect: fixes it, or brings it to the join |
| Run a join, choose its threads, settle effects that contradict each other, sort the parking lot, land it on the main line | yes | yes | no |
| Reread and attest | yes | yes | yes |
| Mandates and code paths in the contribution policy | yes | yes | no |
| `.framework/work.yaml`, delegations, adopting a framework version, annotating an expected finding | yes | no; a delegate may give up the delegation | no |
