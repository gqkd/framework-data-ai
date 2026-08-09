# Evals

`tests/selfcheck.py` checks that the framework is consistent with itself. It cannot check
the part that decides whether any of this is usable: whether the right skill answers when
somebody types a sentence, and whether it then does the right thing. That is what lives
here, and it needs a model to run, which is why it is not in CI.

## Triggering

`trigger/cases.yaml` holds 112 prompts, each labelled with the one skill that should
answer, or `none`.

Naming the expected skill rather than asking a yes/no per skill is the whole design. The
six overlap, and a prompt going to the wrong sibling is worse than a prompt going nowhere:
the wrong skill will confidently do something. One run scores both questions, and the
confusion between siblings comes out as a matrix instead of as an impression.

Twenty-five cases expect `none`, and about a third of those are lexical traps rather than
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
claude plugin details framework-data-ai        # should list all six
```

## Where it stands

| | | miss |
|---|---|---|
| `audit` | 14/15 | a prompt naming a path the fixture does not have |
| `cycle` | 12/13 | *go ahead and implement a redis cache*: work starting with no approved `CHG`, the indirect case the description claims and the hardest one |
| `release` | 15/16 | a production incident went to `requirement`, the only misroute in the set and an arguable label |
| `requirement` | 18/20 | raising an `EVP` threshold; adding to the parking lot of `OPEN.md` |
| `resolve` | 10/11 | closing an `OD` with a decision already taken, which is arguably `requirement` |
| `start` | 12/12 | |
| negatives | 24/25 | *spiegami cosa contiene un CHG*, an explanation, started `cycle` |

**105 of 112.** The failure is undertriggering: one misroute between siblings in the whole
set, and one overtrigger, against 25 negatives that include lexical traps.

Two earlier numbers are wrong and are recorded here because both were wrong in the
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

## What is not measured yet

Triggering is the cheap half. Whether a skill does the right thing once it fires is the
expensive half, and it needs a fixture repository per scenario. Those fixtures exist, built
during the evaluation that produced this directory, and they are not in this repository:
the impact classification and release gate ones in particular encode scenarios worth
keeping. Bringing them in is the next thing.
