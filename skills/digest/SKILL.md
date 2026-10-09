---
name: digest
description: >
  Prepare the daily status workbook of one product, an Excel file for people who will not
  open the registers: when the release can be delivered against the agreed date and why,
  what waits on other people, progress by theme, where the hours go, every item to do, done
  and out of the perimeter, the hours day by day, and a Gantt with the milestones.
  Computed from the registers and from a state file the person fills through this skill;
  the person sends it, never the skill. Triggers on "prepara il digest", "digest
  giornaliero", "digest di oggi", "fammi il digest di atlas", "consuntivo di ieri", "daily
  digest", "prepare today's digest", "the daily digest for the product". Do not use for the
  weekly SAL for management, which is `business`; for deciding what to build in a cycle,
  which is `cycle`; for a presentation to a customer, which is `presentation`; or for a
  digest of pull requests, commits or a container image.
---

# digest

Read `references/preamble.md`, which sits at `${CLAUDE_PLUGIN_ROOT}`, first.

The digest is where the work on one product stands today, written for the person doing it
and for whoever they send it to: a functional team and a direction that read the first sheet
and little else. It is not an artifact and has no owner, like the SAL of `business` and the
deck of `presentation`: do not ask who is responsible for it, and do not put an owner, an
approver or a "prepared by" on it. It is never a source either. A fact that appears in it
first goes back to the register that owns it, through `requirement` or `resolve`, and comes
back into the next digest from there.

**This skill writes no artifact.** The register is read, never edited: not a status, not a
title, not the parking lot. That is a deliberate exception to rule 4 of the project's
`AGENTS.md` and to the preamble's license to append to the parking lot without asking. A
contradiction found while preparing the digest goes into the hand-back, as the line ready to
paste; "aggiungi al parcheggio" takes it to `requirement`.

## Where it stops and `business` begins

`business` is the weekly SAL for the people who steer: movement, needs and decisions,
retold from the artifacts, with no hours and no estimates. This skill is the daily account of
the work itself: hours, sizes, a delivery date and what it waits on. They do not share a
sentence and they do not share a reader; neither one feeds the other.

## What the person declares, and where it lives

Hours, sizes, themes, the perimeter of a release, closing dates, what was asked of whom, the
plan of the next days and the milestones have no source among the artifacts and must not
acquire one there. The person declares them, through this skill, in
`_meta/digest/state-<product>.yaml`. The script computes everything else; this skill asks,
proposes and writes the state file.

`_meta/digest/` is a clone of a **private** repository, separate from the documentation and
from the framework, and the documentation repository ignores it: the hours somebody works are
not documentation, and the series must not be lost with one laptop. Every workbook is
committed and pushed there by the script, which refuses to push to a GitHub remote that does
not report itself private.

```
_meta/digest/
  state-<product>.yaml                       what the person declared
  DIG-NNN-<product>-YYYY-MM-DD/
    DIG-NNN-<product>-YYYY-MM-DD.xlsx        the workbook, as it is sent
    frozen.yaml                              what it was computed from
```

One sequence of numbers across the products. A snapshot is never edited: the next one checks
its hash, and it freezes every day up to the day before its date, so a classification
changed today never moves the hours of a day already sent. A second workbook on the same day
takes a new number and replaces the first.

The state file, format 2, with one item of each shape:

```yaml
format: 2
product: atlas
release:
  name: "1.0"                      # the current release: the perimeter is measured against it
  delivery: 2026-10-13             # the agreed delivery date
  start: 2026-09-22                # the first day of the project
  commitment: null                 # the CMT, when the date was promised to a customer
items:
  OD-120:
    title: formati dei dati in ingresso
    what: >-
      quali formati di file lo strumento di caricamento deve saper leggere.
    theme: architettura            # architettura | sviluppo | deploy
    scope: "1.0"                   # the release name, or out
    size: L                        # S 1-2 h, M 3-5, L 6-12, XL 13-40: counted at the top
    seen: Which file formats the loader reads   # the register's title, confirmed
  KI-013:
    title: tempo massimo superato sulle domande lunghe
    what: >-
      le domande che richiedono molti passaggi di calcolo superavano il tempo massimo e
      l'utente non riceveva risposta.
    theme: sviluppo
    scope: "1.0"
    size: M
    closed_on: 2026-10-07          # every item closed in the perimeter has one
  DEC-019:
    title: un archivio dati per cliente
    what: >-
      ogni cliente ha un archivio fisicamente separato, invece di un archivio unico filtrato
      per cliente.
    theme: architettura
    scope: "1.0"
    size: XL
    closed_on: 2026-09-29
    hours_before: 14               # worked on days rebuilt in bulk, before the first digest
  INC-041:
    title: rilevamento delle anomalie
    what: segnalazione automatica dei valori che si discostano dall'andamento atteso.
    theme: sviluppo
    scope: out
    out_reason: previsto nell'architettura futura   # the workbook prints it as the why
    seen: Anomaly detection on customer metrics
  CHG-003: {scope: out}            # closed long ago, outside the perimeter: nothing else
  OD-098: {split_into: [OD-120, OD-121]}   # beside its other fields, once it is split
  KI-022: {excluded: "a security issue, kept out of anything sent"}
order:                             # the rows of the two lists, in the order shown
  todo: [CHG-018, OD-120, OD-121, OD-109, OD-115, CHG-022, CHG-024]   # with stages: only the
  out: [CHG-021, OD-076, INC-040, INC-041]                            # items in none of them
  first: []                        # items put before everything, urgent or already started
days:
  2026-09-25:                      # before the first digest: rebuilt in bulk, by column
    themes: {architettura: 3}
    outside: {supporto: 4, riunioni: 2}
  2026-10-08:                      # after it: by item
    hours: {CHG-018: 4, OD-076: 1}
    outside: {riunioni: 1, solleciti: 1}
waits:
  - what: Ambiente preprod
    owner: team infrastruttura
    asked: 2026-09-25
    needed_by: 2026-10-09
    without: le modifiche non si possono verificare né chiudere.
    missing: manca l'ambiente preprod   # printed as the status of each item it blocks
    blocks: [CHG-024]              # cannot proceed without it
    slows: []                      # can proceed on a hypothesis
    resolved: null                 # true, or the date, once it arrived
plan:                              # today and the next working day
  2026-10-09: [{item: CHG-018, hours: 5}]
  2026-10-12: [{item: CHG-018, hours: 2, closes: true}, {item: OD-120, hours: 3}]
milestones:
  - {name: Demo al team funzionale, date: 2026-10-15}
  - {stage: t1, date: 2026-10-14}  # the milestone a stage of the roadmap names: the date only
gantt:                             # optional; without it, the Gantt of 4.3.0
  done: false                      # default true; false leaves out the items closed, and the
                                   # increments and stages left with nothing to do
  from: week                       # default start; week starts the days on this week's Monday
```

**When the roadmap orders its increments in stages** (`delivery_stages` in `RMP.md`, kept by
`cycle`), the digest takes the order from there and not from `order.todo`. The stages in their
sequence; in each one the increments, those that others depend on first; in each increment
the decisions and issues it requires, then its changes, and the items blocked by a wait at
the end of their increment. Pinned items come before everything, and items in no stage after
everything, in `order.todo`, which then holds only those. An increment is not a piece of work
here: it has a title in the state file and no theme, scope or size, because it is worth the
sum of what composes it. One with nothing under it is «da scomporre», worth zero hours, and
both the summary and the conversation say that the expected delivery leaves it out. A
conditional increment is counted like the others, and labelled.

The hours outside the product go in five categories and no others: `supporto` (support to the
demo and to production), `reportistica` (reports and status presentations), `riunioni`,
`solleciti` (chasing other people and access to the infrastructure), `formazione` (training a
junior). The hours of an excluded item count as out of the perimeter, without its name.

## 1 · The first run on a project

1. **The store.** Propose the private repository, named after the documentation repository
   with `-digest` at the end, and the account it goes under. On the person's yes, and only
   then, create it with `gh repo create <owner>/<name> --private`, and run:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT:?unset: point it at your framework-data-ai checkout}/skills/digest/scripts/digest.py" --root <project> --init-store <url>
   ```

   It clones the repository into `_meta/digest/` and adds that path to the project's
   `.gitignore`. Say that it did. Add one line to `_meta/README.md`, if the project has one:
   `digest/` holds what the person declared for the digest, kept in its own private
   repository.
2. **The inventory.** Run the script with `--inventory`. With no state file every item of
   the product is unclassified.
3. **The classification**, as in §3. Items closed outside the release, which is most of the
   history, need `scope: out` and nothing else: propose that for all of them in one line and
   write it on one yes. Every item closed inside the release needs its size, its closing date
   and its hours, as `hours_before`; ask for them, all in one table.
4. **The release**: its name, the agreed delivery date and the first day of the project.
5. **The days before the baseline**, from the first day of the project: each one rebuilt in
   bulk, the hours on the product by theme and out of the perimeter, the hours outside it by
   category. A working day nobody worked is declared empty; a Saturday or a Sunday only when
   somebody worked. Theme by theme, these days add up to the `hours_before` of the items, and
   the script refuses until they do.
6. **The waits** already open, as in §4, and the order of the two lists: the items to do in
   the perimeter, then the items outside it. Propose an order: what is in progress first,
   then what unblocks the most. With stages in the roadmap, only the items in no stage are
   ordered here.
7. **The baseline:** `--baseline`. It freezes the state and prints a summary that is not
   sent. The first workbook is the next working day's.

## 2 · Every run

1. **The validator**, as in `references/preamble.md`. An error in a file the digest reads (a
   register, a `DEC`, a `CHG`, the `RMP`, a release of the product) stops the run: the
   workbook would repeat it. Report any other error and go on.
2. **The inventory.** `--inventory` prints what the skill needs and nothing it should guess:
   the period and its working days still without hours, the items new, changed, closed or
   vanished since the last digest with the closing day its commit proposes, the `DEC` that are
   another name for an entry they decided, the items the commits cite day by day with the
   commits beside them, the repositories it could not read, the open waits with their status,
   whether the milestones were ever declared, and whether the store is set up.
3. **Propose, then write.** One compact table: each new or changed item with the theme, scope,
   size, title and description proposed, each item closed with its proposed closing date,
   where each new item goes in its list (at the end, unless the person says otherwise; with
   stages, only for an item in none of them), and every other change to the state file. A
   change in no increment of a roadmap in stages is worth naming: its increment is assigned
   through `cycle`, since this skill writes no artifact. Write nothing before the person agrees or corrects.
4. **Ask** the questions of §4, all of them in one message.
5. **Write the state file**, then `--check`. Fix what it reports in the state file, never by
   loosening a sentence to get past it.
6. **Render**: the same command with no mode, and `--copy-to` the folder the person opens
   files from, so the snapshot stays the original and the copy is the one to send:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/digest/scripts/digest.py" --root <project> --product <p> --copy-to <folder>
   ```

   Show what the script printed: the lines of "A che punto siamo", what changed since the
   last workbook (items closed, new, split, re-estimated, out of or into the perimeter), and
   the path of the copy as a link the person can open.

## 3 · Classifying an item

Proposed from the register, confirmed or corrected by the person, written to the state file
and reused unchanged until the person changes it.

- **Theme**: `architettura` for what decides how the system is built, `sviluppo` for what
  builds it, `deploy` for what takes it into an environment and runs it there.
- **Scope**: the current release or `out`. Start from the changes the `IMP` selects for the
  cycle and the perimeter `DEC`, and say where the state file and the `IMP` disagree. A
  conditional increment is counted like any other, by the person's choice: the roadmap has
  no date for it, and the date the digest computes says it is conditional. An open `KI` in the
  perimeter means its fix is in this release, which the framework would write as a `CHG`;
  say so when proposing it. An item outside the perimeter needs `out_reason`, the why the
  workbook prints.
- **Size**, for every item in the perimeter, open or closed. The estimate counts every item
  at the top of its size, S 2 hours, M 5, L 12, XL 40: one number, on the side of caution,
  and one delivery date. An `XL` is flagged to be split; when it is split, `split_into` names
  the items that replace it.
- **Closing date** (`closed_on`), for every item closed in the perimeter: proposed from the
  commit that closed it in the register, confirmed by the person. A commit that came late
  gives a late date, which is why it is confirmed.
- **Title**: the item in a few plain words, lowercase.
- **What it is** (`what`), the column "Che cos'è" wherever the item appears:
  1. one sentence, two at most;
  2. plain words without trivialising: the technical concept stays, explained in the same
     sentence;
  3. none of the register's jargon, no field name, no section anchor, no identifier;
  4. written for somebody who will never open the register.

  Good: *la regola con cui una domanda in linguaggio naturale viene ricondotta a un indicatore
  definito, da cui dipende che il numero in risposta sia quello giusto.* Jargon: *mappa
  deterministica applicata dopo il pianificatore.* Trivial: *una miglioria alle risposte.*
- **`seen`**: the register's title of the item at the time of confirming. When the register's
  title changes, the script stops until the classification is confirmed again.
- **Exclusion**: `excluded` with the reason, for an item that must not reach whoever the
  workbook is sent to, a security issue for one. It is neither printed nor counted by name.
- **`gone`**, with the reason, for an item that left the registers without being closed, an
  increment moved out of the roadmap for one. Without it the script refuses.

A `DEC` that decides an open entry is the same item as the entry: classify the entry, and its
hours count once, on the entry's identifier.

## 4 · What to ask, and only this

What the commits and the registers say is never asked. Ask, in one message:

1. **Real hours, day by day, on the items the inventory found worked on.** Show the list by
   day and let the person answer with the numbers alone; they may add an item the list
   missed. Every working day of the period is declared, an empty one included.
2. **Hours outside the product**, day by day, in the five categories.
3. **Waits on other people**, new or resolved. For a new one: what is needed, from whom, when
   it was asked, by when it is needed, what cannot be done without it, and which items it
   blocks or only slows, with what the item lacks in a few words. A decision asked of
   somebody is a wait like any other.
4. **The plan** for the digest's day and the next working day: which items, how many hours
   each, and whether that day closes it. Proposed from what is in progress, what was planned
   and not done, and the order of the list.
5. **The milestones**, name and date: at the first workbook, which is the first Gantt, and
   afterwards only when the person says they want to change them. Never every day. A
   milestone a stage of the roadmap names needs only its date, asked the first time the stage
   appears; until then the script refuses, and says which.

The agreed delivery date is asked at the first run and when the release changes. If it was
promised to a customer, it is a commitment: name the `CMT` in `release.commitment` and say
whether the register's wording carries the same date.

Never ask which items were worked on, closed or opened.

## 5 · The workbook

Fixed. Sheets, sections, positions, formulas, colours and fonts are those of the reference
workbook the script is tested against, `tests/fixtures/digest/DIG-003-atlas-2026-10-09.xlsx`
in the framework's repository; `tests/selfcheck.py` lists the few cells allowed to differ and
why: every item counts for the top of its size, so where the reference prints a range the
workbook prints its top, and the estimate is one row instead of a best and a worst case.

1. **Riepilogo**, the sheet most readers stop at: where the release stands (agreed delivery,
   delivery expected today, delay, what the forecast depends on, where the time goes), how the
   estimate is computed, what is needed from others, progress by theme, how the hours of the
   project are split today and how they should be to deliver on the agreed date. No charts:
   the reference had two pies there, taken out on the person's request.
2. **Gantt**: one row per item and per milestone, one column per working day, and the hours
   of each row. Every item done on the days it was worked; every item to do in the order of
   «Da fare», for the top of its size, at the pace of the estimate, so the last one ends on
   the expected delivery; the milestones and the agreed delivery as diamonds; today's column
   in yellow. The first and last day of an item to do are formulas, and the bars conditional
   formats on them. With stages, the rows are grouped by stage and by increment: the row of
   an increment is the sum, the earliest start and the latest end of what composes it, and
   the milestone that closes a stage says by formula whether it is «in tempo», «a rischio» or
   «incompleta». With stages the rows also fold, closed when the file opens: the stages and
   the milestones in view, a stage's increments under its «+», an increment's components
   under its own, and the row of a stage spans its items with a bar of its own. Two
   preferences under `gantt` in the state make it lighter: `done: false` leaves out what is
   closed, and the increments and stages with nothing left to do, but never an increment
   still to break down or a stage that names a milestone; `from: week` starts the days on the
   Monday of the digest's week instead of the first day of the project.
3. **Attività**: the next days, what is left in the perimeter, what was done in it since the
   start, what is outside it. Every item, nothing cut short.
4. **Ore lavorate**: the hours by period, as shares, outside the product by category, and day
   by day from the start. Every other number follows from the last table.
5. **Come leggerlo**: the dates every formula starts from, in yellow, and the legend.

Every derived cell is a formula, written with the value the script computed for it, so the
file reads the same in a preview and in a spreadsheet. The sheets are protected without a
password, except a Gantt that folds: Excel opens no group on a protected sheet. Where a
number cannot be computed, the cell says «non stimabile»; an empty list has one row,
«Nessuna.», which no count includes.

Every number is the script's: the hours left, the pace, the delivery dates, the days of
waiting, the shares. Do not compute one in the conversation and do not round one by hand. If
a number is wrong, a declaration in the state file is, and that is what gets corrected.

## From the digest of 4.1.0

The state file of 4.1.0 is refused, with the command that converts it:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/digest/scripts/digest.py" --root <project> --product <p> --migrate
```

It converts what is mechanical (the theme `infrastruttura` becomes `deploy`, a period of one
day becomes that day, the activities outside the register take the category their name
suggests) and lists the rest, which this skill then asks: the first day of the project, the
days before the first digest rebuilt in bulk, a period of several days split by day, the
closing dates and sizes of the items done, the reasons of the items outside the perimeter,
the order of the lists, the plan with its hours, the milestones, and the decisions asked of
others that are still pending, as waits. The snapshots of 4.1.0 stay as they are and still
anchor the chain of hashes.

## What not to do

- Do not edit an artifact, the parking lot included.
- Do not edit a snapshot, or the hours of a day already sent.
- Do not send, upload or publish the workbook. Pushing the store is the script's, to a
  private repository; the copy is for the person.
- Do not put a date, an estimate or an hour into an artifact.

## Handing back

The path of the snapshot and of the copy, and whether the store was pushed; what changed
since the last workbook; the items the inventory named and the person said were not worked
on; any disagreement between sources the script reported, and any contradiction found, each
as the line ready for the parking lot; the result of the validator.

Then add the two closing blocks required by the preamble.
