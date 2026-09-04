# Evals

`tests/selfcheck.py` checks that the framework is consistent with itself. It cannot check
the part that decides whether any of this is usable: whether the right skill answers when
somebody types a sentence, and whether it then does the right thing. That is what lives
here, and it needs a model to run, which is why it is not in CI.

## Triggering

`trigger/cases.yaml` holds 118 prompts, each labelled with the one skill that should
answer, or `none`.

**Six of them have never been run, and for four days none of them could be.** `business`
arrived in 2.8.11 with four cases of its own, one more for `audit` and one more negative,
and the first of those carried an unquoted `management:` inside its prompt -- so
`yaml.safe_load` at `run.py:177` raised on the file and the whole suite died before reaching
a model. Nothing caught it: no self-check parses this file and nothing here runs in CI. The
quoting is fixed; the six new cases are still unmeasured, and the table below is 112 rows of
a 118 row set.

Naming the expected skill rather than asking a yes/no per skill is the whole design. The
seven overlap, and a prompt going to the wrong sibling is worse than a prompt going nowhere:
the wrong skill will confidently do something. One run scores both questions, and the
confusion between siblings comes out as a matrix instead of as an impression.

Twenty-six cases expect `none`, and about a third of those are lexical traps rather than
unrelated work: *release the lock on the postgres table*, *prepare a release of our internal
python package to the private pypi*, *ingest these csvs into bigquery*, *validate this CSV
against DC-001*, *where do I start debugging this*. Each one carries a word one of the six
descriptions leans on, attached to something the framework has no claim over. Undertriggering
costs a user one repeated sentence. Overtriggering on these costs them a skill that starts
rewriting documentation when they asked about a database lock.

One skill at a time. The whole set in one go does not fit in a session, and each skill
needs a repository its work makes sense in, which is what `fixtures.yaml` maps.

```bash
python evals/trigger/run.py --skill resolve
python evals/trigger/run.py --skill none         # the 25 negatives, shared, run once
python evals/trigger/run.py --case "risolviamo*" --runs 5      # one case, harder
```

**Install the plugin first.** The numbers are worth nothing if the skills do not resolve
the way they will in front of a user:

```bash
ln -s $PWD ~/.claude/skills/framework-data-ai
claude plugin details framework-data-ai        # should list all seven
```

## Where it stands

**114 of 118, measured on 2026-08-27 against 3.0.0.** The first execution of this set, and
that is the exact word: `cases.yaml` had not loaded for four days -- an unquoted
`management:` in the `business` case, raising inside `yaml.safe_load` at `run.py:177` -- so
the six new cases had never been run at all, and the 118 compare with nothing. The eight rows
of 08-19 against 2.6.2 remain the last comparable number that exists, and they measured a
different, smaller set. Read this as a first number, not as an improvement over it.

| | | miss |
|---|---|---|
| `audit` | 15/15 | |
| `business` | 4/4 | never measured before this run |
| `cycle` | 13/14 | *go ahead and implement a redis cache*: work starting with no approved `CHG`, the indirect case the description claims and the hardest one |
| `release` | 15/16 | *abbiamo avuto un incidente stanotte, l'accuracy in produzione e' crollata*, which went nowhere |
| `requirement` | 18/20 | raising an `EVP` threshold; and adding to the parking lot of `OPEN.md` |
| `resolve` | 11/11 | |
| `start` | 12/12 | but see the paragraph below: one of these twelve does not reproduce |
| negatives | 26/26 | |

**AND THE FIXTURES IT WAS MEASURED IN HAVE SINCE MOVED, WHICH IS THE SECOND VARIABLE.** This
table is a measurement of 3.0.0 *on the fixtures as they stood on 08-27*, and that second half
is not decoration: `trigger/fixtures.yaml` maps every skill's prompts into one of the
repositories `make.py` builds, and its own note says why -- "a prompt only means what it means
somewhere it could be acted on", and the first full run scored `resolve` 5 of 11 in a repository
whose open register was empty, "which says the fixture was being measured and not the
description". On 08-31 the fixture migration for `REG016` removed the duplicated field labels
from the bodies of six of them, `audit/dirty-repo`, `requirement/seed`, `resolve/ordering-a`,
`release/F-clean-pass` and `cycle/fixture-base` -- which is `default`, where the 26 negatives
run -- among them.

The values those labels held are still in the maps, so the repositories carry the same facts and
a prompt has the same thing to act on. Whether that moves any routing is **unmeasured**, and
saying it does not would be the same unverified negative this file keeps having to correct. What
follows from it is narrow and firm: the 114 and any later number differ in two variables rather
than one, and a later number is not an improvement over this one. It is a different measurement.

**THE TOTAL CONTAINS ONE POINT THAT DOES NOT REPRODUCE, AND IT IS IN `start`.** *we just
closed the deal and I have the pitch deck, the offer PDF and the contract* passed in the row
above, measured 13:19 on 08-27, and then scored **0 of 5** at 18:16 the same day. Nothing in
this repository changed between those two timestamps -- not a description, not any file, which
was checked by comparing the two states rather than remembered -- and
`skills/start/SKILL.md` has not been touched since 08-18. So `start` is 12/12 in this table
and one twelfth of it is a coin nobody can call. The adjacent fact points the wrong way to be
an explanation: the run at 13:19 was the one right before the account ran out of quota, so it
is the *degraded* condition, and it is the one that passed.

**One of the four is not a description gap, and it must not be fixed.** *abbiamo avuto un
incidente stanotte, l'accuracy in produzione e' crollata a 0.62, dobbiamo tornare alla 1.6*
is labelled `expect: release`, on the stated reasoning that rollback is release's other half.
The skill says the opposite about itself, at `skills/release/SKILL.md:76`: "Rollback only
exists after a deployment, when regressions show up in production, and **that path re-enters
through `LOG` and change intake**" -- which is `requirement`, then `cycle`. `PROCESSES.md`
P-09 routes an incident the same way, through four skills, starting with the signal. So the
label contradicts the skill it measures, and widening `release`'s description until the case
passes would be adapting the instrument to the result. The case stays as written and the row
keeps its miss.

Its history is worth keeping for the same reason. On 08-19 this case fired `requirement` and
this file recorded it as "the only misroute in the set and an arguable label". It was not a
misroute: it was the right answer, scored as wrong by a label that was already contradicted by
the skill. What changed since is that it now fires nothing at all, which is a separate and
worse behaviour, and it is not what a corrected label would fix.

**Read the other three as descriptions, not as noise.** `--runs 5` on each of them came
back **0 of 5** every time: the redis cache of `cycle`, the overnight incident of `release`,
and both of `requirement`. That is the first thing this directory has ever run five times, and
it falsified the premise it was run under -- these were assumed to be flapping cases, and they
are stable misses. The one case that had genuinely flapped, the negative *spiegami cosa
contiene un CHG* which overtriggered `cycle` on 08-19, is now 5 of 5 correct.

The failure across the set is entirely undertriggering: four cases that fired nothing, and not
one misroute between siblings. Undertriggering costs a user a repeated sentence; the other
direction costs them a skill that starts rewriting documentation.

### 3.0.2, the whole set on one fixture state

**116 of 118, measured 2026-08-31 and 2026-09-01.** All eight rows, every one of them run
against the same version and the same built fixtures.

| | | miss |
|---|---|---|
| `audit` | 15/15 | |
| `business` | 4/4 | |
| `cycle` | 14/14 | |
| `release` | 15/16 | the overnight incident, and it stays -- the label contradicts the skill it measures, above |
| `requirement` | 20/20 | |
| `resolve` | 11/11 | |
| `start` | 12/12 | one of these does not reproduce; see 3.0.0 above |
| negatives | 25/26 | *scrivimi la funzione python che fa il match fra movimenti bancari e scritture contabili* started `cycle` |

**WHAT WAS VERIFIED BEFORE ADDING THESE UP, BECAUSE THE ROWS WERE NOT ALL MEASURED AT ONCE.**
Three rows landed at 14:34 on 08-31 and five at 19:12, and the fixture migration for `REG016`
rebuilt the repositories at 19:04:32 -- so the first three were re-run at 19:26 and the whole
table is on one fixture state. Across the two versions the rows span, 3.0.1 and 3.0.2, the
front matter of every skill is byte-identical -- the sha256 of the concatenated set
matches -- the only change under `.claude-plugin/` is the version string, and the CLI reports
the same always-on cost, ~2,271 tokens, on both. The other two changed files, `checks.yaml` and
`validate.py`, are read on invocation and never in session.

**IT DOES NOT COMPARE WITH THE 114, AND NOT BECAUSE OF THE VERSION.** Two variables moved
between them: the descriptions, in 3.0.1, and the fixtures, in the `REG016` migration. A number
that differs in two variables measures neither of them.

**THE FIX IN 3.0.1 WAS A TRADE, AND THE MEASUREMENT IS WHAT SAYS SO.** It cleared three
undertriggers and created one overtrigger, and the overtrigger is the expensive direction: an
undertrigger costs a user a repeated sentence, this costs them `cycle` starting on a request to
write a Python function. That attribution is narrow enough to make, which is why it is made
here rather than hedged: the negatives run in `default`, which is `cycle/fixture-base`, whose
generator has not changed since 08-27 at 11:15 -- nineteen minutes before the 114 was measured
on it. For that row the fixture is the same and the descriptions are the only thing that moved.

The widening that caught *go ahead and implement a redis cache in front of the scoring lookup,
ARC#current says atlas-web queries the warehouse* also catches *scrivimi la funzione python che
fa il match fra movimenti bancari e scritture contabili*. The first names the architecture and
the second names nothing the framework owns, and the description does not carry that boundary.
Whether it can is the open question the next version inherits.

### 3.0.1, the two rows that were touched

**34 of 34, over 170 runs, on 2026-08-31.** `requirement` 20/20 and `cycle` 14/14, each case
run five times, and **not one case was less than unanimous**. The three stable misses that
3.0.1 was written for went from 0 of 5 to 5 of 5:

| | 3.0.0 | 3.0.1 |
|---|---|---|
| *aggiorna l'EVP di atlas: alzare la soglia a 0.93* | 0/5 | 5/5 |
| *aggiungi al parcheggio di OPEN.md che potremmo vendere il forecast* | 0/5 | 5/5 |
| *go ahead and implement a redis cache in front of the scoring lookup* | 0/5 | 5/5 |

**This is not a set score and does not replace the 114.** Two rows out of eight were
re-measured, because two descriptions were edited and six were not. The 114 of 118 above is
the measurement of 3.0.0 and stays that; there is no whole-set number for 3.0.1.

**AND THE RISK THIS CHANGE INTRODUCES IS THE PART THAT IS NOT MEASURED.** Triggering is a
routing decision among seven descriptions, so widening two of them can pull cases *away* from
the other five and from `none` -- and overtriggering is the expensive direction: it costs a
user a skill that starts writing, where undertriggering costs them a repeated sentence. The
26 negatives and the five untouched skills were not re-run. Nothing here says they did not
move, only that nobody looked. That is the first thing to run before this number is quoted as
an improvement.

### The measurement before this one, kept

The whole trigger set, measured on **2026-08-19**. Six rows against **2.6.2** between 12:39
and 16:05, and `release` against **2.8.0** at 22:45, because the framework moved twice that
evening in work happening beside this. It scored **104 of 112**, against 105 measured on 08-10
across seven versions: `audit` gained one, `requirement` and `start` each lost one, and nothing
there separated that from the noise. Kept because a first number with nothing behind it is
worth less than a first number with a smaller, older set behind it.

Triggering depends on the `description:` fields and on nothing else, which is the rule that
made those rows comparable across 2.6.2 and 2.8.0 and makes them *not* comparable with the
table above: the set itself grew by six cases.

WHAT THE SET CANNOT TELL YOU YET, AND IT IS THE SAME THING EVERY TIME. One run per case is
the default, so a case that flips is a coin nobody has flipped twice. `resolve`'s eleventh
case has now been measured as passing (08-18) and as missing (08-19) with no change to any
description in between, which is not a regression and not an improvement -- it is the
measurement saying it is not precise enough to answer. `--runs 5` on the cases that move is
what settles it, and it has not been run.

The failure across the set is still undertriggering: one misroute between siblings, and one
overtrigger against 25 negatives that include lexical traps.

**`release` scored 10 of 16 in the same afternoon, and the six misses were the harness.**
Six of the most explicit prompts in the set -- *prepara la release 1.2.0*, *mi serve la
release note per REL-007* -- produced no assistant turn at all, and no assistant turn was
scored as `none`: the answer that means the description did not fire. Two of the six were
then run one at a time and both fired. The set was re-run whole and came back 15 of 16, with
the miss being the one it has always had.

That is the fifth number this directory has produced from a harness fault rather than from a
skill, and the fix is under the next heading with the other four. What separates this one:
the guard for it already existed and had a hole. It looked for the model saying it was out
of quota, which is a sentence that only exists when the run got far enough for a model to
say it. Both runners now refuse any case that produced no assistant turn, on the rule that
does not depend on a phrase -- a process that never answered did not choose.

**A run that never reached a model used to score as a run that fired nothing.** The first
`audit` re-run on 08-18 came back 0 of 15 because the account hit its session limit partway
through, which is the same shape as a description that stopped working entirely, and
nothing in the output distinguished them. That is the third wrong number this file has
carried for a harness reason, after the 120 second timeout and the six skills in one
fixture. `run.py` now marks those runs unusable and refuses to print a total while any case
is one.

Earlier numbers here are wrong and are kept because every one of them was wrong in the
flattering direction, which is the direction that gets believed:

**3 of 10 for `audit`.** That harness registered the descriptions as `.claude/commands/*.md`,
which is a different mechanism from an installed skill.

**51 of 112.** A 120 second timeout in `run.py`, where `subprocess.run` hands back an empty
stdout on expiry, so every slow case parsed as "no skill fired" rather than as "no answer".
`start` scored 0 of 12 in a run where it was firing correctly every time. The runner now
reads the stream and stops at the first skill, and the same case takes 5 seconds.

**83 of 112**, after that fix, is closer but still measures the wrong thing: it ran all six
in one repository, and that repository had an empty open register. `risolviamo gli open,
sono fermi da due mesi` had nothing to resolve there, and `resolve` scored 5 of 11. On a
register with nine live entries it scores 10 of 11 and fires in under seven seconds. The
model declining to start was mostly right, and the measurement called it a failure.

## The labels are a judgement

`expect` came from the earlier per-skill eval sets where they claimed a prompt, and was
assigned by hand for the 57 they did not, with the reason in `why` where the call is not
obvious. Read them before trusting a score. A few are genuinely arguable: writing a runbook
is real framework work that no skill claims, and *quali commitment abbiamo preso col
cliente* is a read rather than a write, which is why both are `none` today. If a label is
wrong the number is wrong, and that is a better failure than a number nobody can question.

## When `claude plugin eval` opens

`claude plugin eval` is the right tool and it is in early access: it reads
`evals/**/case.yaml`, resolves skills-dir plugins, and runs a no-plugin baseline arm on its
own, which is the comparison this runner does not do. `cases.yaml` keeps the labels in data
rather than in code so the move costs a reshape of one file and nothing else.

## Behaviour

Triggering is the cheap half. `behaviour/` asks whether the answer is right once the skill
fires, one skill at a time, against the repositories in `fixtures/`:

```bash
python evals/fixtures/make.py          # build the repositories first
python evals/behaviour/run.py release  # or audit, cycle, requirement, resolve, start
```

All six have a run. Every one of them found something, and in four cases the defect was in
this repository rather than in the skill: a gate rule that blocked on metrics the plan
declares non-blocking, a fixture claiming a coverage it did not have, a measurement that
could not reach the validator the skill is told to run first, and a truncated transcript
read as a result.

`audit` and `resolve` were re-run twice on **2026-08-18**: once against 1.1.0 and the
register split one per product, and again after 2.0.0 replaced `deadline` with `trigger`
and planted `REG009` in `audit/dirty-repo`. The other four are from the runs above. Every one of those runs found the defect in this repository rather than in the skill: the
warning count `audit/dirty-repo` produces, the list of views a clean repository is missing
which still named two of four, and then an expectation that asks a fixture never to be
written to while the skill it measures is told to transcribe values the repository already
holds. What each
run showed is written into the `because` of the case it belongs to, which is where it can
be read next to the expectation it bears on.

**Grading is by hand.** The runner prints what the skill said, what it wrote, and whether
the repository still validates, and a person decides. A keyword match on "go" and "block"
scores the laundering fixture correct for saying the word while missing that 0.812 under a
0.85 threshold is the entire point of it. At six cases per skill that is affordable; it is
the first thing that has to change if the set grows.

## What is not measured yet

**No baseline arm.** Nothing here answers "would plain Claude have done as well", which is
the question that decides whether the skills earn their token cost. `claude plugin eval`
runs that arm by itself and is in early access.

**Nothing runs in CI**, because all of it needs a model.

**Every input here was written by somebody who already understood the framework.** The
fixtures were built to be hard and several of them caught real defects, but they were built
by the same understanding that wrote the skills. A real project is the first input nobody
here shaped.
