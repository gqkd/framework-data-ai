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

```bash
python evals/trigger/run.py --runs 3 --fixture <a framework repository>
python evals/trigger/run.py --case "risolviamo*" --runs 5      # one case, harder
```

**Install the plugin first.** The numbers are worth nothing if the skills do not resolve
the way they will in front of a user:

```bash
ln -s $PWD ~/.claude/skills/framework-data-ai
claude plugin details framework-data-ai        # should list all six
```

This is not a formality. An earlier version of this measurement registered the six
descriptions as `.claude/commands/*.md` and reported that `audit` fired on 3 of 10 prompts
it should have answered. Re-run against the installed plugin, the first seven cases tried
all scored, including both of the lexical traps above. The old number was measuring the
harness.

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
