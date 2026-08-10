# Documentation framework for Data & AI projects

It defines **which documents exist in a Data/AI project, who creates them, when, and which
question each one answers**. It has two audiences: a new person who has to understand the
system well enough to change it without breaking decisions taken for good reasons, and an
AI agent that has to answer questions without inventing the missing parts.

This repository holds **the definition only**. The artifacts of a real project, its
decisions, products, initiatives and corpus, live in that project's repository, not here.

| File | What it is |
|---|---|
| **`FRAMEWORK.md`** | The reference document. Start here |
| `framework-flow.mermaid` | The lifecycle with its gates. Importable into draw.io: *Arrange → Insert → Advanced → Mermaid* |
| `Framework.drawio` | An older drawing of the same lifecycle, kept for editing in draw.io |
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

Six skills operate the framework from inside Claude Code. `SKILLS.md` is the reference for
what each one does and where their boundaries fall; this is the on-ramp.

### Install it

From a checkout, one line, and nothing is copied:

```bash
ln -s $PWD ~/.claude/skills/framework-data-ai
claude plugin details framework-data-ai        # should list all six
```

A symlink rather than an install, deliberately: the checkout stays the single source, so a
change to a skill is live in the next session with nothing to reinstall. The six cost about
1,500 tokens in every session just by being available, and two to three thousand more each
time one fires. That is the price of having them, and it is worth knowing before you decide
it is worth paying.

### Where to enter

You do not pick a skill, you say what happened. One of them answers.

| What is true right now | What to say | What answers |
|---|---|---|
| No documentation, or a pile of documents from the client | *"partiamo, ecco i deck"* · *"where do I start"* | `start` |
| Somebody said something worth recording | *"abbiamo deciso"* · *"the customer wants"* | `requirement` |
| Work is blocked on a choice nobody has made | *"risolviamo gli open"* · *"what do I need to decide"* | `resolve` |
| Deciding what to build next | *"cosa facciamo in questo ciclo"* | `cycle` |
| A release candidate exists | *"possiamo rilasciare?"* | `release` |
| Before merging, or CI is failing | *"fammi un check"* | `audit` |

### A first session

On a project with business documents and no framework in it:

```
you   partiamo con questo progetto, i documenti del cliente sono in corpus/
      → start reads the corpus, scaffolds AGENTS.md, OPEN.md, GLOSSARY.md and the
        product folder, writes ING.md with a provenance line per claim, and tells you
        which documents gave it nothing and what each of those needs. It writes no
        decisions: at ingestion nothing has been decided.

you   risolviamo gli open, da quale partiamo?
      → resolve orders OPEN.md by what it costs to reverse, and works one at a time.
        Expect it to hand back a question, not a decision.

you   cosa costruiamo adesso?
      → cycle classifies each candidate through the ICG gate and writes the
        classification down. Expect `proposed`, not `accepted`.

you   possiamo rilasciare?
      → release checks the report against the frozen evaluation plan and says go or
        rework. Expect it to refuse to deploy: preparing the evidence is its job, the
        command is yours.
```

### What to expect them not to do

This is the part worth reading before the first session, because a skill that surprises you
once gets switched off.

**They propose and wait.** Two writes happen without asking, because they destroy nothing:
appending a signal to `LOG`, and adding a line to the parking lot of `OPEN.md`. Everything
else arrives as a diff and a question.

**Told to overwrite, they will not.** Asked to "align the documentation" with a new
definition of a term the glossary already defines differently, the run left the glossary
alone, showed both definitions with where each came from, and asked which one holds. That
is the designed behaviour and not caution: the most recent sentence in a project is usually
the least reliable one.

**They will not settle an architectural question on one sentence.** Told a queue was moving
to another database, contradicting an accepted decision, the run recorded the signal and
proposed the rest, including moving the old decision to `superseded`, which is the only
field an immutable allows.

**They report what they did not do.** A finding left standing on purpose, with the reason,
is a good outcome. A report that says everything is green after ten minutes usually means
something was silenced.

**They cannot check the world.** `verified_against` names a commit and `evp_hash` names a
file; a skill can tell you it could not establish either, and that is the honest answer. It
will not fill them in with something plausible.

## The gate

```bash
pip install -r requirements.txt
python3 skills/audit/scripts/validate.py --root ../my-project
python3 skills/audit/scripts/validate.py --root ../my-project --emit-index
```

Twenty six checks, catalogued in `skills/audit/checks.yaml`, each with the
failure it prevents written next to it. Two block on day one and they are the two
`SKILLS.md §9` names: front matter that parses, and front matter that means something.
Everything else warns. Two are `off`, because they would need input that does not exist
yet, and the catalog says which and why.

A project raises or lowers any of them in its own `framework.yaml`:

```yaml
checks:
  LC002: error      # a decision was taken on a document nobody had reread
  XP003: off        # we only have one product
```

That one line is the whole mechanism behind the rule this framework gives itself: **turn a
check on when the failure it prevents has already happened once, and not before.** If
turning one on costs a commit of code, it does not happen, and twelve checks switched on in
advance get switched off together the first time they are in the way.

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

`--emit-index` regenerates `decisions/INDEX.md` and `TRACEABILITY.md` from the front
matter, and `--emit-index --check` exits non-zero when what is on disk has drifted, which
is what keeps a generated file from quietly becoming a hand written one.

It only touches a file that says `Generated by` in its header. Without that line the file
is left alone and named in the report, because the two directions are not symmetric: a
generated file that drifted costs a regeneration, and a hand written file that got
regenerated costs whatever it held that front matter cannot express. Projects do keep these
by hand, for a column on why a decision still matters or a row for where a source system
enters the chain, and the generator can only ever write back the part it can derive.

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

- **`--emit-manifest`.** The `GENERATED` sections of `product.yaml` are still written by
  hand, and the template says so at the bottom, where somebody will read it.
- **Distribution.** A project refers to the framework by path. There is no packaging, no
  release to install, and no migration note when a rename lands. With one project this is
  invisible. With the second it is the first thing that breaks.

  Half of it does exist now: a project writes `framework_version` in its own
  `framework.yaml` and the validator says so when the two disagree. That does not pin
  anything, and it is not meant to. It answers the question that comes first, which is
  whether a finding is the rules having moved or the documents being wrong, because those
  need opposite responses and a team that guesses wrong at it twice stops reading the
  validator. `version:` in `schemas/artifact-types.yaml` says what a bump means, and it is
  deliberately not the plugin's version: a release that rewords a skill changes nothing
  about whether a document still validates.
- **Two checks that need structured input.** `CHG001` and `CHG002` want the `ICG` routing
  as a field on the `CHG` front matter rather than as prose in its body. The recovered
  versions matched prose, and matching prose is the fragility the section markers exist to
  remove. They stay `off` until the field exists.

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

Seven living documents that have to be true, about twenty that are written once and never
touched again, and one file, `OPEN.md`, that says what has not been decided yet, because
that is the information no other document holds and the one an agent will otherwise invent.
