---
name: digest
description: >
  Prepare the daily digest of one product: what closed since the last digest and in how many
  hours, what is left in the perimeter of the current release as a range of hours, when it
  can be delivered at the recent pace and at a normal day's, what that waits on from others,
  and what is planned today and on the next working day. Computed from the registers and
  from a state file the person fills through this skill; plain text the person sends, never
  the skill. Triggers on "prepara il digest", "digest giornaliero", "digest di oggi", "fammi
  il digest di atlas", "consuntivo di ieri", "daily digest", "prepare today's digest", "the
  daily digest for the product". Do not use for the weekly SAL for management, which is
  `business`; for deciding what to build in a cycle, which is `cycle`; for a presentation to
  a customer, which is `presentation`; or for a digest of pull requests, commits or a
  container image.
---

# digest

Read `references/preamble.md`, which sits at `${CLAUDE_PLUGIN_ROOT}`, first.

The digest is where the work on one product stands today, written for the person doing it
and for whoever they send it to. It is not an artifact and has no owner, like the SAL of
`business` and the deck of `presentation`: do not ask who is responsible for it, and do not
put an owner, an approver or a "prepared by" on it. It is never a source either. A fact that
appears in it first goes back to the register that owns it, through `requirement` or
`resolve`, and comes back into the next digest from there.

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

Hours, sizes, themes, the perimeter of a release, what was asked of whom and the plan for
tomorrow have no source among the artifacts and must not acquire one there. The person
declares them, through this skill, in `_meta/digest/state-<product>.yaml`. The script
computes everything else; this skill asks, proposes and writes the state file.

`_meta/digest/` is a clone of a **private** repository, separate from the documentation and
from the framework, and the documentation repository ignores it: the hours somebody works are
not documentation, and the series must not be lost with one laptop. Every digest is committed
and pushed there by the script, which refuses to push to a GitHub remote that does not report
itself private.

```
_meta/digest/
  state-<product>.yaml                       what the person declared
  DIG-NNN-<product>-YYYY-MM-DD/
    DIG-NNN-<product>-YYYY-MM-DD.txt         the digest, as it is sent
    frozen.yaml                              what it was computed from
```

One sequence of numbers across the products. A snapshot is never edited: the next one checks
its hash. A second digest on the same day takes a new number and replaces the first.

The state file, with one item of each shape:

```yaml
product: atlas
standard_hours: 8                  # a normal working day
release:
  name: "1.0"                      # the current release: the perimeter is measured against it
  delivery: 2026-10-13             # the agreed delivery date
  commitment: null                 # the CMT, when the date was promised to a customer
items:
  OD-114:
    title: come il sistema capisce quale indicatore gli viene chiesto
    what: >-
      la regola con cui una domanda in linguaggio naturale viene ricondotta a un indicatore
      definito, da cui dipende che il numero in risposta sia quello giusto.
    theme: architettura            # architettura | sviluppo | infrastruttura
    scope: "1.0"                   # the release name, or out
    size: S                        # S 1-2 h, M 3-5, L 6-12, XL 13-40
    seen: Which rule maps a question to a defined metric   # the register's title, confirmed
  DEC-019:
    title: un archivio dati per cliente
    what: >-
      ogni cliente ha un archivio fisicamente separato, invece di un archivio unico filtrato
      per cliente.
    theme: architettura
    scope: "1.0"
    hours_before: 14               # closed before the first digest: the real hours it took
  CHG-003: {scope: out}            # closed long ago, outside the perimeter: nothing else
  OD-098: {split_into: [OD-120, OD-121]}   # beside its other fields, once it is split
  KI-022: {excluded: "a security issue, kept out of anything sent"}
waits:
  - what: Ambiente preprod
    owner: team infrastruttura
    asked: 2026-09-25
    needed_by: 2026-10-09
    without: le modifiche non si possono verificare né chiudere.
    missing: manca preprod         # printed beside each item it blocks
    blocks: [CHG-024]              # cannot proceed without it
    slows: []                      # can proceed on a hypothesis
    note: null                     # when it blocks no item: what it blocks instead
    resolved: null                 # the date it arrived
requests:                          # decisions asked of somebody: open OD entries only
  OD-116: {to: responsabile di progetto, by: 2026-10-09, fallback: lo tolgo dal perimetro.}
plan:
  2026-10-07: [CHG-018, CHG-022]
  2026-10-08: [CHG-018, CHG-021]
periods:                           # keyed by the first day: from one digest to the day before the next
  2026-10-06:
    hours: {OD-114: 5, CHG-017: 3, CHG-019: 1.5}
    outside: {Riunioni di stato: 1, Formazione di un junior: 0.5}
```

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
   write it on one yes. Every item closed inside the release needs its hours, as
   `hours_before`; ask for them, all in one line.
4. **The rest of the state:** the release and its agreed delivery date, the hours of a
   normal day, and the waits already open, as in §4.
5. **The baseline:** `--baseline`. It freezes the state and prints a summary that is not
   sent. The first digest is the next working day's.

## 2 · Every run

1. **The validator**, as in `references/preamble.md`. An error in a file the digest reads (a
   register, a `DEC`, a `CHG`, the `RMP`, a release of the product) stops the run: the
   digest would repeat it. Report any other error and go on.
2. **The inventory.** `--inventory` prints what the skill needs and nothing it should guess:
   the period, the items new, changed, closed or vanished since the last digest, the
   `DEC` that are another name for an entry they decided, the items the commits of the period
   cite with the commits beside them, the repositories it could not read, the open waits with
   their days, and whether the store is set up.
3. **Propose, then write.** One compact table: each new or changed item with the theme, scope,
   size, title and description proposed, and every other change to the state file. Write
   nothing before the person agrees or corrects.
4. **Ask** the questions of §4, all of them in one message.
5. **Write the state file**, then `--check`. Fix what it reports in the state file, never by
   loosening a sentence to get past it.
6. **Render**: the same command with no mode. Show the digest as it is in the `.txt`, then
   everything the script printed after it.

## 3 · Classifying an item

Proposed from the register, confirmed or corrected by the person, written to the state file
and reused unchanged until the person changes it.

- **Theme**: `architettura` for what decides how the system is built, `sviluppo` for what
  builds it, `infrastruttura` for what runs and releases it.
- **Scope**: the current release or `out`. Start from the changes the `IMP` selects for the
  cycle and the perimeter `DEC`, and say where the state file and the `IMP` disagree. Never
  propose an `INC` that the `RMP` marks `conditional`: a conditional increment inside a
  dated estimate is the plan with dates the roadmap template forbids. An open `KI` in the
  perimeter means its fix is in this release, which the framework would write as a `CHG`;
  say so when proposing it.
- **Size**, for an open item in the perimeter. An `XL` is counted with its whole range and
  flagged to be split; when it is split, `split_into` names the items that replace it.
- **Title**: the item in a few plain words, lowercase.
- **What it is** (`what`), the line "Cos'è" wherever the item appears:
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
  digest is sent to, a security issue for one. It is neither printed nor counted.
- **`gone`**, with the reason, for an item that left the registers without being closed, an
  increment moved out of the roadmap for one. Without it the script refuses.

A `DEC` that decides an open entry is the same item as the entry: classify the entry, and its
hours count once.

## 4 · What to ask, and only this

What the commits and the registers say is never asked. Ask, in one message:

1. **Activities outside the register** in the period, with hours: meetings, training, managing
   repositories, anything else.
2. **Real hours on the items the inventory found worked on.** Show the list and let the person
   answer with the numbers alone, in one line; they may add an item the list missed.
3. **Waits on other people**, new or resolved. For a new one: what is needed, from whom, when
   it was asked, by when it is needed, what cannot be done without it, and which items it
   blocks or only slows.
4. **The plan** for the digest's day and the next working day, proposed from what is in
   progress, what was planned and not done, and the order of the `IMP`.
5. **Decisions asked of others**, new or arrived: an open `OD` of the register, with whom it was
   asked of, by when, and what happens if it does not arrive. A choice that is in no register
   is not asked about here: it goes to the register first.

The agreed delivery date is asked at the first run and when the release changes. If it was
promised to a customer, it is a commitment: name the `CMT` in `release.commitment` and say
whether the register's wording carries the same date.

Never ask which items were worked on, closed or opened.

## 5 · The format

Fixed. Sections, order, titles and labels are those of the canonical example the script is
tested against, `tests/fixtures/digest/DIG-002-atlas-2026-10-07.txt` in the framework's
repository. Plain text, no tables, dates in titles and never "ieri", "oggi" or "domani", no
long dashes, every item in the annexes and nothing cut short.

What the canonical example has no line for stays out of the digest: an item worked on and not
closed, hours on items outside the perimeter, an item re-estimated or split, an item that
entered the perimeter or reopened. The script lists them after the digest, as lines ready to
paste, together with every value it printed in a form the example does not show. Show both
lists to the person. They are proposals for the format, not part of it; the person decides
whether to paste them.

Every number is the script's: the reconciliation, the pace, the delivery dates, the days of
waiting. Do not compute one in the conversation and do not round one by hand. If a number is
wrong, a declaration in the state file is, and that is what gets corrected.

## What not to do

- Do not edit an artifact, the parking lot included.
- Do not edit a snapshot, or the hours of a period that was already printed.
- Do not send, upload or publish the digest. Pushing the store is the script's, to a private
  repository.
- Do not write a decision asked of somebody that is not an open `OD` in a register.
- Do not put a date, an estimate or an hour into an artifact.

## Handing back

The path of the snapshot and whether the store was pushed; the lines the format has no room
for and the provisional forms the script printed; the items the inventory named and the person
said were not worked on; any disagreement between sources the script reported, and any
contradiction found, each as the line ready for the parking lot; the result of the validator.

Then add the two closing blocks required by the preamble.
