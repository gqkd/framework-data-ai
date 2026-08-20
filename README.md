# Documentation framework for Data & AI projects

It defines **which documents exist in a Data/AI project, who writes them, when, and what
question each one answers**.

Two kinds of reader need it. A new person, who has to understand the system before changing
it, so they do not undo a decision somebody made for a good reason. And an AI agent, which
has to answer questions without filling the gaps with something plausible.

This repository holds **the definition only**. The artifacts of a real project, its
decisions, products, initiatives and corpus, live in that project's repository, not here.

| File | What it is |
|---|---|
| **`FRAMEWORK.md`** | The reference document. Start here |
| `framework-flow.mermaid.md` | The lifecycle with its gates, drawn. It renders where you are reading it; the fence is what makes that happen, and the diagram inside it is importable into draw.io: *Arrange → Insert → Advanced → Mermaid* |
| `Framework.drawio` | Where the layout came from, and not a second copy of the truth. The mermaid file is the one kept current; this one has not been redrawn since 2026-08-06 and is not maintained. Import the mermaid if you want a draw.io view of today |
| `SKILLS.md` | The six skills that operate the framework, and where their boundaries fall |
| `PROCESSES.md` | The twelve operating processes: who does what, what each one leaves written, and which of them the tooling actually carries today. Diagrammed, one per process |
| `templates/` | One template per artifact, each with its anti-patterns at the bottom |
| `schemas/` | The artifact catalog and what each type is allowed to be. `artifact-types.yaml` is the source; `generate.py` projects it into the JSON Schemas, into `FRAMEWORK.md §7` and into `templates/README.md` |
| `skills/` | The six skills. `audit/` also carries the gate: `scripts/validate.py`, `scripts/migrate.py` and `checks.yaml` |
| `ci/` | Two files a project copies into `.github/`: the pull request template and the workflow that checks a change set against the `CHG` authorizing it |
| `references/` | Shared by the skills: the common preamble and the routing table |
| `tests/selfcheck.py` | The framework checked against itself. Runs in CI |

## Reading order

**To understand the framework:** `FRAMEWORK.md` → `framework-flow.mermaid.md` →
`templates/README.md`

**To start using it by hand:** `FRAMEWORK.md §10`, the entry assessment and the day one set

**To start using it with the skills:** *Using it with the skills*, below, then `SKILLS.md`
for what each one does and where their boundaries fall

**To run it with other people:** `PROCESSES.md`, which is the same lifecycle told by who
does the work rather than by which document comes out. It is also the honest inventory: each
process says whether the tooling carries it, carries part of it, or leaves it to a person

## Applying it to a project

The framework is not copied into the project. Keep it cloned next to it and refer to it by
path:

```
~/projects/framework-data-ai      the definition
~/projects/my-project             the artifacts
```

## Using it with the skills

Six skills run the framework from inside Claude Code. This section is how to start.
`SKILLS.md` says what each one does in detail.

### Turning it on

There are three separate things here, and only the last one is public.

**1. A symlink.** Nothing is copied and nothing is published:

```bash
ln -s $PWD ~/.claude/skills/framework-data-ai
claude plugin details framework-data-ai        # should list all six
```

Use this while you are still changing the skills. Edit a skill and the change is live in
the next session. Remove it with `rm ~/.claude/skills/framework-data-ai`.

**There is no copy, and that cuts both ways.** A skill reads these files as they are on
disk, so a run started while somebody is halfway through a change to the framework sees
half of it. That has happened: a registry that had begun to want lists, templates that had
not caught up yet, and eighteen findings in a real project from a shape written in a file
that was correct ten minutes later. Before a run that matters, ask the framework whether it
currently agrees with itself:

```bash
python3 tests/selfcheck.py      # green means the tree is consistent right now
```

Installing it as a plugin, below, takes a copy at install time and has the opposite
problem: your edits do not reach it until you reinstall. Neither is wrong; know which one
you are running.

**2. Install it as a plugin.** Also local. A marketplace can be a directory on your own
disk, so this publishes nothing either:

```bash
claude plugin marketplace add $PWD
claude plugin install framework-data-ai@framework-data-ai
```

**No `--scope`, and this used to say `--scope local` in all three commands.** Two different
senses of the word had been collapsed: *local* as in "this publishes nothing", which is
what the paragraph above means and stays true, and `--scope local`, which is the flag that
installs for one project directory instead of for you. A framework you use across every
project wants the default, `user`. The cost of the confusion is not an error message: the
flag installs a *second* copy at a different scope beside the one that was already running,
and then `claude plugin details` has two answers.

This copies the repository into `~/.claude/plugins/cache/`. The copy is taken at install
time, so an edit to a skill does not reach it until you reinstall. That is the only reason
to prefer the symlink while you are still changing things.

Having both is safe: installing the plugin disables the symlink automatically, and
uninstalling re-enables it. `claude plugin details framework-data-ai` shows which one is
live under `Source:`.

**To pick up a change, reinstall rather than update.** `claude plugin update` exists and is
shorter, but the install path is keyed on the `version` in `plugin.json`, which does not
move when a skill is edited — so it can find nothing to do and say so cheerfully:

```bash
claude plugin uninstall framework-data-ai@framework-data-ai
claude plugin install framework-data-ai@framework-data-ai
```

Then restart the session; the copy is read at start-up. The marketplace does not need
re-adding: its source is this directory, so it is read from disk every time. To check the
copy actually moved, look for something you know is new in
`~/.claude/plugins/cache/framework-data-ai/framework-data-ai/<version>/`, rather than
trusting the command's own report.

To undo it:

```bash
claude plugin uninstall framework-data-ai@framework-data-ai
claude plugin marketplace remove framework-data-ai
```

**3. Publish it.** Push the repository somewhere others can reach, and they add it as a
marketplace by URL. Nothing above requires this.

**What it costs.** The six skills add about 1,500 tokens to every session, just by being
available. Each one costs another two to three thousand when it runs.

### If you have client documents to read

`start` reads decks, PDFs, Word files and spreadsheets. The converter is not bundled:

```bash
npm install -g @firecrawl/anydoc     # or: pip install firecrawl-anydoc
sudo apt install poppler-utils       # PDFs only, and not optional there
```

Without the first, every office file comes back empty. The extractor says so at the top of
its own report, so you find out before you classify anything rather than after.

`poppler-utils` is what gives a PDF page a number and what tells a scanned PDF from a
readable one. `anydoc` reads PDFs too and is the fallback, but it has no page in it: the
text arrives and the page number does not, and a claim you cannot point back at a page is
a claim you cannot check.

### Where to enter

You do not choose a skill. You say what happened, and one of them answers. The skills
understand Italian and English equally.

| What is true right now | What you say | What answers |
|---|---|---|
| No documentation yet, or a folder of client documents | *"let's start, the client documents are in that folder"* | `start` |
| Somebody said something worth writing down | *"we decided to use Airflow"* | `requirement` |
| Work is stuck on a choice nobody made | *"let's work through the open decisions"* | `resolve` |
| Choosing what to build next | *"what do we build this cycle?"* | `cycle` |
| A release candidate is ready | *"can we ship 1.7?"* | `release` |
| Before you merge, or CI is failing | *"check the docs"* | `audit` |

### A first session

A folder of client documents and no framework in it:

**You:** *"let's start with this project, the client documents are in docs-in/"*

`start` asks who owns what it is about to write, then reads the documents. It creates
`AGENTS.md`, `GLOSSARY.md`, an `OPEN.md` for the product and one at the root, and moves the corpus
under `_meta/`, which is where everything that is about the framework rather than about the
product lives. It writes `ING.md`, which records where each claim came from. It tells you
which documents it could not read and what each one needs. It writes no decisions, because
at this point nothing has been decided.

**You:** *"let's work through the open decisions, which one first?"*

`resolve` sorts the open register of the product you name by how expensive each choice is to
undo, and takes one at a time. Expect a question back, not a decision. There is one register
per product, plus one for the substrate and one at the root for what belongs to no product:
name none and it reads the union the root keeps generated, across all of them.

**You:** *"what do we build now?"*

`cycle` sorts the candidates into kinds of change and writes that down. Expect it marked
`proposed`, not `accepted`.

**You:** *"can we ship?"*

`release` compares the test results against the plan that was frozen before the tests ran,
and says ship or rework. It will not deploy. Preparing the evidence is its job; running the
command is yours.

### What they will not do

Read this before the first session. A tool that surprises you once gets switched off.

**They propose, then wait.** Two things happen without asking, because neither can destroy
anything: adding a signal to `LOG`, and adding a line to the parking lot in the `OPEN.md` at
the root.
Everything else comes back as a diff and a question.

**They will not overwrite a definition.** In a test, the glossary said a customer is active
after a login in the last 90 days. Told "make it 30 days, align the documentation", the
skill left the glossary alone. It showed both versions, said where each came from, and asked
which one holds. The newest sentence in a project is usually the least reliable one.

**They will not decide architecture from one sentence.** Told a queue was moving to MongoDB,
which contradicted a decision already on record, the skill wrote down the request and
proposed the rest. It did not write the new decision itself.

**They tell you what they did not do.** A problem left open on purpose, with the reason, is
a good result. A report that says everything is fine after ten minutes usually means
something got hidden.

**They cannot check the world.** Some fields name a commit or a file hash. If a skill cannot
confirm one, it says so. It will not fill in something plausible.

## The gate

```bash
pip install -r requirements.txt
python3 skills/audit/scripts/validate.py --root ../my-project
python3 skills/audit/scripts/validate.py --root ../my-project --emit-index
```

<!-- generated: counts -->
*Generated from `schemas/artifact-types.yaml` and `skills/audit/checks.yaml`. Edit those, not this line.*

**30 artifact types. 56 checks** (5 error, 49 warn, 2 info), each catalogued with the failure it prevents written next to it.
<!-- /generated -->

The count above is generated, and it is generated because the one that used to be here was
wrong by fifteen: true when it was typed, regenerated by nothing, in the repository whose own
rule is that a number nobody measures is a number waiting to be false.

Only two block on day one: `FM001`, front matter that parses, and `FM002`, front matter
that means something. Everything else warns, and two report at `info`, for a state every
repository starts in.

A project raises or lowers any of them in its own `framework.yaml`:

```yaml
checks:
  LC002: error      # a decision was taken on a document nobody had reread
  XP003: off        # we only have one product
```

That one line is why the framework can follow its own rule: **turn a check on once the
thing it prevents has actually happened, and not before.**

If turning a check on costs a commit of code, nobody does it. And twelve checks turned on
in advance all get turned off together, the first time they get in the way.

The same file says which files are artifacts in the first place. The validator reads every
`.md` and `.yaml` under the root, and a project that also holds code holds a great deal of
neither:

```yaml
scan:
  skip_dirs: [dbt, infra, notebooks]
  skip_files: [CONTRIBUTING.md, environment.yml]
```

Those **extend** the framework's own exclusions, they do not replace them: `corpus/` is
source material the framework defines as not-an-artifact, and `schemas/` and `skills/` are
the framework itself. A key `framework.yaml` does not recognise stops the validator instead
of being dropped, because a `scan:` block that reads as applied and is not leaves you with a
validator you believe you configured.

`--emit-index` regenerates `decisions/INDEX.md`, `TRACEABILITY.md` and one
`products/<p>/product.index.yaml` per product from the front matter, and
`--emit-index --check` exits non-zero when what is on disk has drifted, which is what keeps
a generated file from quietly becoming a hand written one.

It also fills `§5` of the root `OPEN.md`, and that one is a region rather than a file:
everything between `<!-- generated: open-union -->` and `<!-- /generated -->` is rewritten
and everything around it is left alone. The open register is one per product now, so the
ordering by cost to reverse that `§1` is built on only ever holds inside one of them; `§5`
is where the three become one ordered list, under a heading per product. A register that
does not carry the markers is not written to at all — they are the boundary and they are
also the permission.

The product index is the derived half of `product.yaml`: which decisions are open for that
product, which changes are active, which of its documents are living and when each was last
reviewed. `product.yaml` beside it stays authoritative and hand written. They are two files
rather than sections rewritten inside one because `product.yaml` carries the reasoning
behind each of its fields in comments, and rewriting parts of a YAML file while preserving
those is a swamp — and because the sections that were marked `GENERATED` and kept by hand
had already started to disagree with the register.

It only touches a file whose header says `Generated by`. Any other file is left alone and
named in the report instead.

The two mistakes are not the same size. Regenerating a file that had drifted costs one
command. Regenerating a file somebody maintained by hand loses whatever they put in it that
front matter cannot hold: a column on why a decision still matters, a row for where a source
system enters the chain. The generator can only write back what it can derive.

In a project's CI, one line:

```yaml
- run: python3 ../framework-data-ai/skills/audit/scripts/validate.py --root .
```

On a pull request it takes two more arguments — what the change set says it is doing and
which files it touches — and checks it against the `CHG` that authorizes it. `ci/` holds the
template and the workflow; `PR001` to `PR004` are the checks.

How the project gets hold of the framework in CI is the part that is not solved. See below.

### Where the rules live, and why none of them are in the validator

| File | Holds |
|---|---|
| `schemas/artifact-types.yaml` | the catalog: what each type is, may be, must carry, and where it goes |
| `schemas/framework/<type>/v1.json` | the front matter check itself, generated from the above |
| `skills/audit/checks.yaml` | which checks run, at what severity, and what each prevents |

The catalog tables in `FRAMEWORK.md §7` and in `templates/README.md` are generated from the
registry too. They used to be written by hand in both places and had already drifted: `DC`
was `living, versioned` in one and `living` in the other, and so were `EVP` and `IMP`. The
framework broke its own single rule inside its own reference document, within five commits
of that rule being written.

The front matter check *is* the published schema, rather than a Python reimplementation of
it. One enforcement path and not two: a schema an editor reads and a schema CI enforces
cannot disagree when they are the same file.

`tests/selfcheck.py` closes the last hole. The validator skips `templates/` and `schemas/`
for reasons written down in the registry, and the cost is that nothing was checking the
definition everything else is checked against: that is how `templates/RLM.yaml` went
without `status` and `owners` for as long as it did. The self check runs in CI here.

## What still does not exist


- **Distribution.** A project refers to the framework by path. There is no packaging and no
  release to install. With one project this is invisible. With the second it is the first
  thing that breaks.

  Pinning is no longer part of that gap. A project can write `framework_commit` beside its
  `framework_version`, and `FW003` compares it with the commit doing the checking; versions
  are tagged from `v2.8.0` on. What is still missing is the install: the framework arrives by
  being cloned next to the project, and a pin tells you which commit that clone has to be at
  rather than fetching it for you.

  What exists is the part underneath it. A project writes `framework_version` in its own
  `framework.yaml`, and the validator tells you when that number and the framework's
  disagree — which answers the question that comes first: is this finding here because the
  rules moved, or because the document is wrong? Those need opposite responses, and guessing
  wrong twice is how people stop reading the validator.

  `skills/audit/scripts/migrate.py` answers it finding by finding. It rebuilds the validator
  the project pinned out of this repository's git history, runs it and the current one over
  the same project, and reports what is new, what was already there and what is gone. No tag
  and no release are needed for that: the history is the archive. The note explaining each
  version sits beside the number in `schemas/artifact-types.yaml`, and the tool reads it out
  rather than keeping a second copy.

  `version:` in that file explains when the number goes up. It is the plugin's version too —
  one artifact, one number — which is a reversal of what stood here, and `tests/selfcheck.py`
  keeps the three files that state it from disagreeing.
- **A reference implementation.** Nothing here has been used on a real project for a full
  cycle. Every fixture in `evals/` was written by somebody who already understood the
  framework, which is the one limit more fixtures cannot fix.


## One product or several

Both work. With one product, skip `FRAMEWORK.md §9` and do not create `PLATFORM.md`.

With several, read it: the section turns on one distinction that gets collapsed constantly,
between having more than one product, which is a fact about the folder structure, and those
products sharing a substrate, which is a decision. It is not repeated here.

## License

[Apache License 2.0](LICENSE). Permissive: you can use it, change it and redistribute it,
including commercially. The clause that matters for a documentation framework is §4.b. If
you redistribute a modified version you must state that you changed it, because anyone
reading a set of rules needs to know whether they are reading these or a variant.

## In one line

A set of living documents that have to stay true, a larger set written once and superseded
rather than edited, two that only ever grow. And `OPEN.md`, which says what has not been
decided yet.

The counts are in the catalog in `FRAMEWORK.md §7`, which is generated from the registry.
They used to be here, as "seven" and "about twenty", and they were wrong: sixteen and
twelve. A number in prose is the thing this framework exists to stop, and the README had
been carrying two of them.

That last one is the point. No other document holds it, and it is what an agent invents when
nobody wrote it down.
