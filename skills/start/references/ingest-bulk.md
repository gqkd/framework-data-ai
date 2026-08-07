# Ingesting the business corpus

The procedure for the first load: sales decks, PDFs, requirements analyses, documents the
business produced before the technical project existed.

## What these documents really are

They are not a specification. They are **the record of what was promised**, produced by
people whose job was to sell. Mistaking them for requirements is how a product gets built
from a slide.

That decides the main destination: most of the content goes to `COMMITMENTS.md`, not to a
product document. But the corpus also holds five things of different value, and they have
to be separated because they end up in five places.

| What | Where it goes | Why it is worth having |
|---|---|---|
| **Domain vocabulary** | `GLOSSARY.md` | These are the words the customer will use. If your system calls them something else, every conversation carries a translation cost |
| **Numeric promises** | `COMMITMENTS` **and** a threshold in `EVP` | "A 30% reduction" is at once a commitment and an acceptance criterion. The two must not come apart |
| **Constraints disguised as claims** | `OPEN.md` or a `DEC` | "One single experience", "real time", "integrated with" are architectural decisions already taken by somebody who did not know they were taking one |
| **Descriptions of the current process** | `WF#current`, marked unverified | The business describes the customer's process second hand. Useful as a starting point, never as a fact |
| **Competitors mentioned** | `CMP` | Whoever got named in a sale is who the customer has in mind |

## Procedure

### 1 · Extract

Files live in `products/<p>/corpus/` when they concern one product, and in `corpus/` at the
root when they concern more than one. **You run the extraction**, one folder at a time. The
user does not run commands.

```bash
python -c "import markitdown, docx; print('ok')"   # first: without these the output is empty
python ${CLAUDE_PLUGIN_ROOT}/skills/start/scripts/extract.py \
    products/<p>/corpus -o ingest-out/<p> --jsonl
```

It produces `extract.md` with one block per slide, page or section, each labelled with its
provenance. You need that: you will go back to the original slide every time a claim has to
be checked, and without the number you will not find it again.

One output per product, not one for everything. When two products promise the same thing
differently, knowing which corpus each version came from is half the reconciliation work.

### 2 · Look at the flagged pages

The script lists the slides and pages with little text and, when it can, rasterises them
into `ingest-out/<p>/render/`. **Open those with the file reading tool: they are images, and
reading them is part of the extraction.** On a sales deck the architectural promise is
usually drawn. Three boxes with arrows and the words "one single platform" produce no
extractable text and are a tenancy constraint.

When it cannot rasterise (pptx and docx with no LibreOffice installed) the script names the
file and the pages. Ask the user to open them and describe them. Classifying that document
while skipping this step means ingesting everything except the part that constrains you.

If the script reports that a PDF is an exported presentation, treat the whole document as
visual: the extracted text has lost the layout, and in a deck the layout carries meaning.

### 3 · Classify into `ING.md`

One row in the ingestion register per relevant claim, using the routing table for the kind
and the destination.

**Do not write straight into the final artifacts.** The `ING` register exists for three
concrete reasons:

- **Provenance.** The row keeps the pointer to document and slide. In the final artifact
  that trail would be lost, and you will need it.
- **A review queue.** Two hundred slides produce more claims than anyone can judge in one
  session. The register is the state of the work, and it lets you stop halfway.
- **Traceable rejection.** You can reject a claim while keeping the fact that the business
  made it. That is exactly what you need when somebody asks eight months later why that
  feature is not there.

Be selective. A forty slide deck holds maybe fifteen claims with consequences. The rest is
sales narrative: do not extract it for completeness.

### 4 · Find the contradictions

**This is the highest value output of the whole operation**, and the one thing nobody would
do by hand across two hundred slides.

Three documents written by different people over eight months contradict each other, and
nobody knows because nobody has read them all in one go. Compare systematically:

- **Different numbers for the same metric** across two documents
- **Incompatible timing promises** — "real time" in a deck, "hourly refresh" in the
  requirements analysis
- **Different perimeters** — a module present in one offer and absent from another
- **Diverging definitions** of the same domain term
- **Assumptions about data** that a `DFB` will later disprove

Each contradiction produces:

- a row in `ING.md#contradictions` with **both** provenances
- an entry in `OPEN.md` §1 if it needs a decision, or a row in `COMMITMENTS` as a promise to
  renegotiate if the two versions went to two different customers

In the second case say so explicitly to the user. Two customers promised opposite things is
a problem that only gets solved by talking about it, and sooner is cheaper.

### 5 · Route, with confirmation

Work **by destination, not by source document**: fill `GLOSSARY` in one pass across the
whole corpus, then `COMMITMENTS`, then the rest. That produces entries consistent with each
other and surfaces divergences while you are writing them rather than afterwards.

The order that follows the real dependency:

1. `GLOSSARY` — everything else will use its terms
2. `COMMITMENTS`, including what is out of technical reach
3. `OPEN.md` — constraints disguised as claims, and contradictions you cannot resolve
4. `PBR` per product
5. `WF#current`, marked unverified
6. `CMP` if the corpus holds enough. Often it does not, and leaving it empty is correct

Ask for confirmation **by destination, not by row**: "the whole corpus produces these twelve
glossary entries, shall I write them?" is a question somebody can answer. Twelve separate
questions is not.

### 6 · Close with the tally

Five lines: how many claims classified, how many routed, how many rejected, **how many
contradictions**, and which commitments turn out to be beyond technical reach.

Then run the validator.

## What not to do

**Do not generate `PRB`, `HYP`, `EVD` or `DFB` from the corpus.** The material contains no
evidence: it contains sales claims. You may record a *stated* problem as a `PRB`, with its
provenance and its reverse-discovery section filled in. You may not produce an evidence
brief, because nobody observed anything.

An evidence brief built from a pitch deck passes any validator, looks true, and is exactly
the failure the framework exists to prevent.

**Do not summarise the corpus.** Nobody will read the summary. The value is in the claims,
extracted, classified, and tied back to their slide.
