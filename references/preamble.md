# Common preamble

Every skill in this plugin reads this first. It exists as one file because the alternative
is the same two hundred words copied six times, which is the duplication the framework
forbids, committed by the framework against itself.

## Before writing anything

Read, in this order:

1. **`AGENTS.md`** at the project root. It is the control plane: the table of authoritative
   sources, the non negotiable rules, and the project's real commands.
2. **The open registers that bind the work.** There are one to three of them and which
   ones is not a judgement call: `products/<p>/OPEN.md` for the product the task names,
   `platform/OPEN.md` if the project has a substrate, and `OPEN.md` at the root, whose
   `§1` holds what belongs to no product in particular. If the task names no product, the
   root's `§5` is the generated union of all of them under a heading per product.
   If a choice you need is listed as open in any of them, you do not take it. You raise it.
   This is the rule that stops an agent from inventing a decision and then implementing it
   with conviction.
3. **`products/<p>/product.yaml`** for the product you are working on, if the task names
   one — and `product.index.yaml` beside it, whose `open_decisions` is the generated list
   of every entry binding that product, wherever it is filed. It is the cheap way to
   check you have not missed a register.

If the project has no `AGENTS.md`, it has not been set up: run the `start` skill instead of
guessing a structure.

**Then ask who owns what you are about to write, and ask it before the first write of the
session.** One question, plainly, and the answer goes into `owners`.

Do not deduce it. Not from the git config, not from the email address, not from the corpus,
not from whoever the last document happened to name. `owners` is who to go to when the
document turns out to be wrong, and a name recovered from a commit is a guess wearing the
shape of a fact: the next reader cannot tell the two apart, and the person named never
agreed to it. Asking costs one line and it is the only field in the front matter that
commits somebody other than you.

## The rules that outrank the task

**One authoritative source per fact.** When you are about to write something that already
exists somewhere else, write a link instead of a copy. Two copies diverge, and then nobody
knows which to believe.

**Write about the product, not about the framework.** These documents are read by somebody
who wants to know about the product, and every sentence explaining the framework's own
process is a sentence they have to get past first. It takes three forms and all three are
worth deleting on sight:

- **Phase apologetics.** *"This is a skeleton on purpose: a `PBR` is normally born at F4
  and we are at F1."* Where the product sits is recorded in `product.yaml`, once, in a
  field. A document that opens by arguing for its own right to exist has not said anything
  yet, and it teaches the reader that the top of these files can be skipped.
- **Provenance restated.** `ING` owns where a claim came from. Cite `ING-014` and stop.
  Writing *"from `Vision.pdf` page 1 (`ING-014`)"* is the same fact in two places, and when
  the register is corrected it is the copy that stays and gets believed. The whole reason
  the register exists is so that the artifacts do not have to carry this.
- **Commentary inside a machine-readable file.** `framework.yaml` and `product.yaml` are
  configuration. A paragraph explaining why a block you did not write is absent belongs in
  `OPEN.md`, which is the register for absences and the one place where somebody will
  actually act on it. In a config file it is prose nobody parses and nobody works.

The test is simple: delete the sentence and ask whether anything true about the product was
lost. If the answer is no, it was about the framework.

**Respect the class.** It is declared in the front matter and it decides what you may do:

| Class | What you may do |
|---|---|
| `living` | edit in place, and set `last_review` to the current instant |
| `immutable` | never edit the body. Create a new document with `supersedes`, move the old one to `status: superseded`. The `status` field is the one exception and moves in place |
| `append-only` | never rewrite a line. Add a linked event |

**Do not implement a signal.** A `LOG` line, a piece of feedback or an `RMP` increment is
not an authorization to build. What gets implemented is a `CHG` with `status: approved`.

**Absence is information.** If a fact is not documented, say so. An agent that fills a gap
with a plausible assumption does more damage than one that stops, because the assumption is
indistinguishable from a fact to whoever reads it next.

**Never invent a field that attests something.** `verified_code`, `frozen_at`, `evp_hash`,
`evp_version` are claims about the world: a commit that exists, a file that was hashed. If
you cannot establish the real value, leave it and say so. An invented hash turns an
evidence document into a decoration and passes every check.

**Never write today's date into `last_review` without having read the document.** It is the
fastest way to make a validator green and the only one that makes the whole framework
useless.

## How to propose a write

Show what changes before you change it, and keep it short. A wall of generated document is
not reviewable, so nobody reviews it, and the approval becomes a formality.

**First**, a compact table. Never the document:

| File | What changes |
|---|---|
| `decisions/DEC-012-postgres.md` | new · datastore chosen, closes OD-003 |
| `products/alpha/ARC.md` | §current · store component added |
| `products/alpha/OPEN.md` | OD-003 moves from §1 to §4 |

**Then**, once the user agrees and you have written, print the document, or the section of
it that changed when the file is long.

Two things you apply without asking, because they destroy nothing and asking would only
make them annoying: appending a `SIG` to `LOG`, and adding an entry to the parking lot in
`§3` of `OPEN.md` at the root — the root and not a product's register, because what goes in
the parking lot has not been qualified yet, and deciding which product it belongs to is
part of qualifying it. Everything else is proposed. The project's `AGENTS.md` says when the second one
applies even though nobody asked you to write anything, and it says it there rather than
here because that rule has to reach an agent answering a question with no skill running,
which never reaches this file.

## Closing move

Any skill that wrote something ends by running the validator, and reports what it says:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:?unset: point it at your framework-data-ai checkout}/skills/audit/scripts/validate.py" --root <project>
```

`python3` and the `:?` are both load bearing: `python` is not on PATH on most systems, and
an unset `CLAUDE_PLUGIN_ROOT` collapses the path to `/skills/...` and fails with a message
that names neither problem. The `audit` skill explains this once, in full.

This is not ceremony. The cascade is where a write goes wrong, and the validator is what
notices that a `DEC` moved and its `ARC` did not. If it reports something you caused, fix
it before handing back. If it reports something that was already there, say so and leave
it: it is not yours to silence.

## The last two blocks, and they come after everything else

Everything a skill here says is reasoning, and there is a lot of it: what was classified and
why, what was left alone and why, what the validator found. It is worth saying. But somebody
who has just read four hundred words of it cannot tell what to do tomorrow morning, and a
report you have to re-read to extract one action from is a report that gets skimmed — after
which the sentence that mattered goes with the rest.

So every run ends with these two blocks, in this order, **last**: after whatever the skill's
own handing-back section asks for, and after the validator. Write them **in the language the
user is speaking**, whatever language you did the reasoning in.

### 1 · What changed, in the words somebody would actually use

One line per file. What is now *true*, not which section moved:

| File | In parole semplici |
|---|---|
| `GLOSSARY.md` | «cliente attivo» ora vuol dire login negli ultimi 30 giorni, non 90 |
| `decisions/DEC-012-postgres.md` | scritta la decisione sul datastore, e chiude OD-003 |
| `products/alpha/ARC.md` | l'architettura corrente adesso nomina Postgres |

No section anchors, no field names, no identifier the reader has to go and resolve. If a line
only makes sense to somebody who has already read the body, it is one of the body's lines and
not one of these.

### 2 · What to do next, with what it buys and what it costs

Two to four rows, never more. The one you would do first goes at the top and is marked as
such: the user asked for the trade-offs, not for a menu with no recommendation in it.

| Prossimo passo | Cosa dà | Cosa costa |
|---|---|---|
| **Decidere OD-001** (consigliato) | sblocca le tre voci che dipendono da essa | mezz'ora, e serve la risposta di chi amministra l'account AWS |
| Scrivere il `PBR` di beta | `XP003` smette di suonare | un'ora, e oggi non esiste un documento di business da cui scriverlo |
| Fermarsi qui | niente da fare adesso | OD-001 è ad alto costo e senza default in forza: il conto cresce ogni giorno |

**Four rules, because this is the easiest place in the framework to write something that
looks helpful and is not.**

**Derive the steps, do not compose them.** They are already in the repository: the register in
cost-to-reverse order, the half of the cascade this write left undone, the findings you did
not fix, the artifact a classification obliges, the command that is the user's to run. A step
that cannot be traced to one of those is a suggestion, and a suggestion does not belong in a
table that reads as an agenda.

**One row is a legitimate number.** A table padded to four with two invented rows teaches the
reader to skim the block, and the row that mattered is skimmed with them.

**Stopping is a row whenever it is genuinely an option**, and its cost is the honest one: what
gets worse while nothing happens. The framework is built on cost-to-reverse and the cost of
waiting; this is where that arithmetic is handed to the person who has to do the waiting.

**Nothing appears here that is not above.** These blocks restate. They do not decide, and they
do not introduce: a finding that exists only in the summary is a finding nobody argued for,
and the propose-then-wait rule applies to a row in this table exactly as it applies to a
write.
