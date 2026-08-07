---
name: start
description: >
  Set up the Data & AI documentation framework in a project and ingest the business corpus
  that already exists. Use at the very beginning of a project, and whenever the user has
  business documents to bring in: decks, pitch decks, PDFs, requirements analyses, offers,
  contracts, transcripts. Triggers on "partiamo", "iniziamo il progetto", "ingesta questi
  documenti", "ho questi PowerPoint del commerciale", "parti da questi PDF", "estrai i
  requisiti da qui", "imposta il framework", "nuovo prodotto", "ho del codice senza
  documentazione", "da dove comincio", "set up the framework", "new product", "ingest these
  documents", "I have code with no documentation", "where do I start". Use it even when the
  user only drops files in a folder and says "guarda qui": a pile of business documents at
  the start of a project is always this skill.
---

# start

Read `references/preamble.md` at the plugin root before anything else, and
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

## Step 2 · Scaffolding

Create the day one set, and nothing else. The framework's own rule is that an artifact
appears when the thing it documents exists, not before.

```
AGENTS.md  OPEN.md  COMMITMENTS.md  GLOSSARY.md  ING.md
decisions/            empty, numbering started
products/<p>/         product.yaml, PBR.md
```

Copy from `templates/` at the plugin root, fill the **front matter** and leave the body to
the interview and the corpus. Fill `owners`, `created` and `last_review` with real values:
a placeholder that survives into a real repository reads as a real value to anything that
does not know the template.

**Do not create `PLATFORM.md`.** It is born with the decision to share a technical
substrate, and that decision does not have to be taken now. Until it is, the question lives
in `OPEN.md` as an entry with its cost to reverse. An empty `PLATFORM.md` waiting to be
filled collects whatever has not found a home yet, and the substrate ends up defined by
what accumulated in it rather than by a choice.

If the project holds code as well as documents, write a `framework.yaml` with the
directories the validator should not read. Otherwise the first run reports every dbt model
and every Kubernetes manifest as a document with no front matter, which is a first
impression a tool does not recover from.

```yaml
scan:
  skip_dirs: [dbt, infra, notebooks]
```

## Step 3 · Ingest the corpus

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

## Step 4 · Seed `OPEN.md`

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
