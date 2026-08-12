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
| `framework-flow.mermaid` | The lifecycle with its gates. Importable into draw.io: *Arrange → Insert → Advanced → Mermaid* |
| `Framework.drawio` | The same lifecycle in draw.io's own format. Its layout is the one the mermaid file follows; its content is one revision behind |
| `SKILLS.md` | The six skills that operate the framework, and where their boundaries fall |
| `templates/` | One template per artifact, each with its anti-patterns at the bottom |
| `schemas/` | The artifact catalog and what each type is allowed to be. `artifact-types.yaml` is the source; `generate.py` projects it into the JSON Schemas, into `FRAMEWORK.md §7` and into `templates/README.md` |
| `skills/` | The six skills. `audit/` also carries the gate: `scripts/validate.py` and `checks.yaml` |
| `references/` | Shared by the skills: the common preamble and the routing table |
| `tests/selfcheck.py` | The framework checked against itself. Runs in CI |

## Reading order

**To understand the framework:** `FRAMEWORK.md` → `framework-flow.mermaid` →
`templates/README.md`

**To start using it by hand:** `FRAMEWORK.md §10`, the entry assessment and the day one set

**To start using it with the skills:** *Using it with the skills*, below, then `SKILLS.md`
for what each one does and where their boundaries fall

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

**2. Install it as a plugin.** Also local. A marketplace can be a directory on your own
disk, so this publishes nothing either:

```bash
claude plugin marketplace add $PWD --scope local
claude plugin install framework-data-ai@framework-data-ai --scope local
```

This copies the repository into `~/.claude/plugins/cache/`. The copy is taken at install
time, so an edit to a skill does not reach it until you reinstall. That is the only reason
to prefer the symlink while you are still changing things.

Having both is safe: installing the plugin disables the symlink automatically, and
uninstalling re-enables it. `claude plugin details framework-data-ai` shows which one is
live under `Source:`.

To undo it:

```bash
claude plugin uninstall framework-data-ai@framework-data-ai --scope local
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
`AGENTS.md`, `OPEN.md`, `GLOSSARY.md` and a folder for the product, and moves the corpus
under `_meta/`, which is where everything that is about the framework rather than about the
product lives. It writes `ING.md`, which records where each claim came from. It tells you
which documents it could not read and what each one needs. It writes no decisions, because
at this point nothing has been decided.

**You:** *"let's work through the open decisions, which one first?"*

`resolve` sorts `OPEN.md` by how expensive each choice is to undo, and takes one at a time.
Expect a question back, not a decision.

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
anything: adding a signal to `LOG`, and adding a line to the parking lot in `OPEN.md`.
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

Thirty four checks, catalogued in `skills/audit/checks.yaml`, each with the failure it
prevents written next to it.

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


- **Distribution.** A project refers to the framework by path. There is no packaging, no
  release to install, and no migration note when a rename lands. With one project this is
  invisible. With the second it is the first thing that breaks.

  Half of it exists. A project writes `framework_version` in its own `framework.yaml`, and
  the validator tells you when that number and the framework's disagree.

  This pins nothing, and is not meant to. It answers the question that comes first: is this
  finding here because the rules moved, or because the document is wrong? Those need
  opposite responses. Guess wrong twice and people stop reading the validator.

  `version:` in `schemas/artifact-types.yaml` explains when the number goes up. It is not
  the plugin's version, on purpose: a release that rewords a skill cannot break a
  document.
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

Seven living documents that have to stay true. About twenty written once and never touched
again. And `OPEN.md`, which says what has not been decided yet.

That last one is the point. No other document holds it, and it is what an agent invents when
nobody wrote it down.
