---
name: start
description: >
  Set up the Data & AI documentation framework in a project and ingest the business corpus
  that already exists. Use at the very beginning of a project, and whenever the user has
  business documents to bring in: decks, pitch decks, PDFs, requirements analyses,
  spreadsheets, offers, contracts, transcripts. Triggers on "partiamo", "iniziamo il progetto", "ingesta questi
  documenti", "ho questi PowerPoint del commerciale", "parti da questi PDF", "estrai i
  requisiti da qui", "imposta il framework", "nuovo prodotto", "ho del codice senza
  documentazione", "da dove comincio", "set up the framework", "new product", "ingest these
  documents", "I have code with no documentation", "where do I start". Use it even when the
  user only drops files in a folder and says "guarda qui": a pile of business documents at
  the start of a project is always this skill.
---

# start

Read `references/preamble.md`, which sits at `${CLAUDE_PLUGIN_ROOT}`, before anything
else, and
`references/routing-table.md` before classifying anything. The routing table is the single
source of the classification and cascade logic. Read it, do not summarise it from memory:
it is the file that keeps this skill and `requirement` writing to the same places.

This skill does two things that are one moment: it creates the structure, and it fills what
the business already wrote. Scaffolding without ingestion gives you empty templates.
Ingestion without scaffolding has nowhere to write.

## Step 1 · Entry assessment

Not a formality. The entrance decides which documents make sense and which would be
fiction. Ask, and do not guess:

| Situation | Entrance |
|---|---|
| An idea, nothing promised to anyone | F1, the full path |
| **An idea already sold or promised** | F1 with `COMMITMENTS.md` as a constraint, and **reverse discovery** |
| Existing code with no documentation | F5 in reverse: `ARC#current` reconstructed from the code, `PBR`, and a `DEC` for every decision already implicit in the code |
| A product already in production | baseline first (`ARC` `RB` `DC` `RSK`), then reverse discovery |

**On reverse discovery.** When the solution has already been sold, discovery does not run
problem → hypothesis → solution but the other way round: *promised solution → which problem
it actually solves → what happens if it does not*. Call it by that name in the documents.
Faking a forward discovery when the answer was already promised produces documentation that
looks true, and it is the fastest way to lose trust in the whole structure.

## Step 2 · Find the corpus before you build anything around it

The user drops the client's documents somewhere in the project and says to start. Where is
not knowable in advance: `corpus`, `docs`, `documenti`, a folder named after the customer,
or loose at the root. **Do not guess and do not glob.** Ask the extractor:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:?unset: point it at your framework-data-ai checkout}/skills/start/scripts/extract.py" \
    --find <project> --json
```

It counts documents rather than matching folder names, and it does not count the ones this
framework wrote: front matter is what separates a client's `.md` from an artifact, and a
corpus dropped at the root beside `AGENTS.md` is exactly the case that breaks a rule based
on location. `.` in the output means the files are loose at the project root. Sibling
folders of one corpus are gathered, so `docs/contracts`, `docs/decks` and
`docs/spreadsheets` come back as `docs`.

| `verdict` | What you do |
|---|---|
| `one` | say which folder, in one line, and go on. Name its subdirectories if it has more than one |
| `several` | **ask.** Do not take the largest |
| `none` | **ask.** Do not scaffold |

On `several`: the second folder is very often an older version of the same deck, and which
one is current is not something a file count can answer. Getting it wrong here does not
produce an error, it produces a repository built on a superseded offer, and nothing
downstream will contradict it.

When the answer carries `notes_only`, there is no deck, no PDF and no spreadsheet anywhere:
what was handed over is plain text and markdown. That happens — an analysis exported from a
wiki, a transcript, pasted notes — and it looks exactly like a folder of somebody's own
working notes. Say which you think it is in the one line where you name the folder, and let
the user correct you before you ingest it.

On `none`: an empty ingestion and a corpus you failed to find leave the same repository
behind. Scaffolding first and asking later means the answer arrives after the structure has
been justified by the absence.

### Then propose the move. Do not perform it.

`_meta/corpus/<product>/` is where the corpus belongs, and moving it is still a write like
any other: **show it and wait.** The preamble applies here more than anywhere, because this
is the one thing in the repository that cannot be regenerated, and a folder that has been
moved out from under a link somebody sent the customer, a script, or Git LFS is not a
problem you find out about today.

Offer both, and take the second answer without arguing:

- **Import it.** `git mv` where the repository is under git, plain `mv` otherwise. Then
  check that nothing was lost, before you touch anything else:

  ```bash
  before=$(find <source> -type f -exec sha256sum {} + | awk '{print $1}' | sort | sha256sum)
  # ... move ...
  after=$(find _meta/corpus/<p> -type f -exec sha256sum {} + | awk '{print $1}' | sort | sha256sum)
  [ "$before" = "$after" ] && echo "same files" || echo "STOP: the corpus changed"
  ```

  Count and content, not count alone. If they differ, stop and say so: a corpus short of
  two files reads exactly like a corpus that never had them.

- **Leave it where it is.** Then add its folder to `scan.skip_dirs` in `framework.yaml` and
  say you did. Without that line every `.md` in it comes back as `FM001`, which is a first
  impression the tool does not recover from. `scan` already exists for precisely this: no
  new field is needed, and the corpus keeps working where the client's links point.

## Step 3 · Scaffolding

Create the day one set, and nothing else. The framework's own rule is that an artifact
appears when the thing it documents exists, not before.

```
AGENTS.md  OPEN.md  COMMITMENTS.md  GLOSSARY.md  ING.md  framework.yaml
decisions/            empty, numbering started
products/<p>/         product.yaml, PBR.md
_meta/                README.md, corpus/<p>/, extract/
```

**`_meta/` holds what is about the framework rather than about the product**, and the root
holds documents only. Where the corpus ended up is whatever step 2 settled: under
`_meta/corpus/<product>/` if it was imported, or where it was with its folder named in
`scan.skip_dirs`. Say which, in the handover. `_meta/extract/` is where the extractor
writes, and it can be deleted and rebuilt at any time.

Write `_meta/README.md`, three lines, saying exactly that:

```markdown
# Not documentation

This directory is about the framework, not about the product. Nothing here answers a
question about what we are building.

- `corpus/` is what the business gave us. **Irreplaceable: never delete it.**
- `extract/` is what `extract.py` produced from it. Delete it and rerun; nothing is lost.
```

Copy from `templates/` at the plugin root, fill the **front matter** and leave the body to
the interview and the corpus. `created` and `last_review` take the real instant, to the
minute. `owners` takes **the answer to the question the preamble told you to ask** and
nothing else: this is the first skill to run in a repository, so it is the one that sets
the name every later document copies, and a name inferred here propagates silently. A
placeholder that survives into a real repository reads as a real value to anything that
does not know the template.

**Create `STACK.md` if the corpus named a single tool, and it almost certainly did.** Every
tool on an architecture slide goes into **§unratified**, never into §chosen: it was chosen by
whoever drew the slide, and a `DEC` for it does not exist. On the corpus this framework was
first used against, one slide named eleven — React, FastAPI, Apache NiFi, Iceberg, S3,
LangGraph, Azure OpenAI, Kubernetes, an OIDC provider — and before this file there was
nowhere to record that they were decisions nobody had taken. They would have gone into
`ARC#current` looking chosen, or nowhere at all.

Give each row where it came from, as an `ING`, and what it would cost to change. That second
column is the agenda: the expensive ones are the decisions to take first, and a project
about to work on its architecture is looking for exactly that list.

**Do not create `PLATFORM.md`.** It is born with the decision to share a technical
substrate, and that decision does not have to be taken now. Until it is, the question lives
in `OPEN.md` as an entry with its cost to reverse. An empty `PLATFORM.md` waiting to be
filled collects whatever has not found a home yet, and the substrate ends up defined by
what accumulated in it rather than by a choice.

**Always write a `framework.yaml`**, even when there is nothing to configure, because one
line in it is not configuration:

```yaml
framework_version: 1          # from `version:` in the framework's artifact-types.yaml

scan:                         # only if the project holds code as well as documents
  skip_dirs: [dbt, infra, notebooks]
```

`framework_version` records which framework this repository was written against. The day
the framework changes, findings appear in a repository nobody touched, and without that
line there is nothing to tell "the rules moved" from "we did this wrong". Those want
opposite responses, one is a migration and one is a repair, and a team that guesses wrong
at it twice stops reading the validator. Copy the number from `version:` at the top of the
framework's `schemas/artifact-types.yaml`; do not invent one.

`scan` is the other half, and only when the project holds code. Without it the first run
reports every dbt model and every Kubernetes manifest as a document with no front matter,
which is a first impression a tool does not recover from.

**Two keys and no prose.** This file is configuration. Do not write a paragraph explaining
why there is no `scan:` block, or why some other key is absent: an absence worth acting on
is an `OPEN.md` entry, where somebody works it, and a comment in a YAML file is neither
parsed nor worked. The same goes for `product.yaml`. Leaving `framework_version: 1` alone
on a line is the correct output of this step.

## Step 4 · Ingest the corpus

Only if there is one. See `references/ingest-bulk.md` for the procedure and
`scripts/extract.py` for the extractor.

The starting point that changes everything: **these documents are not a specification.**
They are the record of what was promised, produced by people whose job was to sell. The
main destination is `COMMITMENTS.md`, not a product document.

Everything goes through **`ING.md` first**, never straight into the artifacts. That
preserves provenance, gives you an interruptible review queue, and lets you reject a claim
while keeping the fact that the business made it, which is exactly what you need when
somebody asks eight months later why that feature is not there.

**The highest value output is the contradictions.** Three documents written by different
people over eight months contradict each other and nobody knows, because nobody has read
them all in one go. They go in `ING.md#contradictions`. If two versions of the same promise
went to two different customers, that is not a technical problem, it is a commitment to
renegotiate, and sooner is cheaper.

## Step 5 · Seed `OPEN.md`

This is the step that makes the rest of the project possible, and the one most likely to be
skipped because it feels like admitting ignorance.

Every choice you could not make from the corpus becomes an entry, ordered by **cost to
reverse**, which is what `OPEN.md` §1 is already structured around. For each: what is
already happening today in the absence of a decision (`Default in force`), and what it
would cost to change your mind later.

`Default in force` is mandatory. A decision not taken does not mean nothing is happening:
something is happening by default, and naming it is what turns a vague worry into a
decidable question.

Seed it with the questions the framework knows you will face:

- What is in the MVP, and what is explicitly out
- Which datastore, which integration style
- Whether the products share a technical substrate, if there is more than one
- Every commitment that looked out of technical reach during ingestion

The `resolve` skill works this register afterwards. A thin `OPEN.md` does not mean few open
questions, it means they are still in somebody's head.

## What you must not do

**Do not write `PRB`, `HYP`, `EVD` or `DFB` from the corpus.** A deck contains claims shaped
like requirements, and turning one into an evidence brief takes a step that looks small. It
is not: nobody observed anything. The result passes every validator and contains no
information, and it is indistinguishable from the real thing under a quick reading, so the
damage surfaces only when a decision taken on it turns out to be wrong. You may structure,
classify, link and propagate. You may not produce evidence.

**Do not fill `GLOSSARY.md` with everything the corpus mentions.** Ten entries that are
argued over beat sixty copied out. Start with the terms that appear with two meanings, and
with the entities more than one product shares: that is where a glossary earns its keep.

## Handing back

Report in this order: the structure created, what the corpus produced (commitments,
glossary candidates, and above all contradictions), the `OPEN.md` entries seeded with the
high cost ones first, and what you deliberately did not write and why.

Then run the validator and say what it found. At this point `OD003` firing on a high cost
entry with no default in force is the correct outcome, not a failure: it is the register
telling you which decision cannot wait.
