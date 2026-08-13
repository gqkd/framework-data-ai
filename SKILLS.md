# The skills that operate the framework

Six skills, distributed as a Claude Code plugin. The plugin is named `framework-data-ai`
and supplies the namespace, so the skills carry short names: `/framework-data-ai:start`,
`:requirement`, `:resolve`, `:cycle`, `:release`, `:audit`.

The example phrasings are in both languages because the skills are: each description carries
its trigger phrases in Italian and in English, and the measurement in `evals/trigger/`
covers both. They are examples of what somebody types, not a syntax.

| Skill | What you actually say | What it does |
|---|---|---|
| **`start`** | *"partiamo, ecco i documenti"* · *"where do I start"* | entry assessment, scaffolding, corpus ingestion, seeds `OPEN.md` |
| **`requirement`** | *"abbiamo deciso"*, *"il cliente vuole"* · *"the customer wants"*, *"add that"* | classifies, routes to the one authoritative source, propagates, flags contradictions |
| **`resolve`** | *"risolviamo gli open"* · *"what do I need to decide"* | works `OPEN.md` in cost-to-reverse order, produces `DEC` and the cascade |
| **`cycle`** | *"cosa facciamo in questo ciclo"* · *"what do we build next"* | intake, `ICG`, reshaping, `CHG`, `IMP`, and the brief per change |
| **`release`** | *"possiamo rilasciare?"* · *"are we ready to ship"* | the `RG` gate, `RLM`, `REL` |
| **`audit`** | *"è tutto a posto?"* · *"check the docs are consistent"* | runs the validator, judges what to do with each finding, and on request reads both ends of the pairs that have to agree |

---

## 1 · A necessary clarification about automation

**A skill is not a daemon.** It runs when Claude runs: it does not fire on a push, it checks
nothing overnight, it has no state between one invocation and the next. If the checks lived
only in the skills they would run when somebody remembers to ask, which is to say rarely and
not at the moments that count.

| Nature of the task | Tool | When it runs |
|---|---|---|
| Deterministic: schema, ids, references, staleness, indices | **Python script** | in CI on every push, and by hand when needed |
| Extraction from formats: pptx, pdf, docx with provenance | **Python script** | when you ingest |
| Requires judgment: classifying a claim, propagating a cascade, writing a `CHG` | **Skill** | when you invoke it |
| Requires your knowledge: what was observed, what was promised | **You** | |

**The skills carry the scripts.** `audit` contains `validate.py`: the skill runs it
interactively and interprets the results, CI runs the same file and blocks the merge. One
implementation, two entry points. If the logic were duplicated in the skill's instructions
it would diverge from the version that runs in CI, which is the one that counts.

---

## 2 · Why these six, and where the boundaries fall

A skill is selected on its description, and a vague description triggers unreliably: it
fires when it is not needed and stays quiet when it would help. So each of the six has to
own a sentence you would actually say, and no two may compete for the same one.

**Information in, versus authorization out.** `requirement` brings information in and files
it. `cycle` sends authorization out. The boundary is the one rule of the framework an agent
breaks most easily: *a request is not a mandate*. "The customer wants Excel export" is a
`SIG` in `LOG`. It becomes buildable only after intake, triage and the `ICG`.

**Deciding, versus recording a decision.** `resolve` closes an entry in `OPEN.md` and takes
the decision with the user. `requirement` records a decision already taken. If `requirement`
finds it would close an open entry, it says so and stops: closing it is `resolve`'s job,
because closing an open decision is itself a decision.

**Why `start` holds the corpus ingestion.** Scaffolding without ingestion gives you empty
templates; ingestion without scaffolding has nowhere to write. They are one moment, the
beginning, and splitting them would mean a skill that always calls the other.

**Why the conversational recording is not in there with it.** It was, in an earlier design,
on the argument that the classification logic would otherwise be duplicated. That argument
no longer holds: `references/routing-table.md` is one file at the plugin root and both read
it, so nothing is duplicated. What is gained is triggering: "ingest these decks" and "we
decided on Postgres" are different sentences at different times, and one skill answering to
both answers to neither reliably.

**Why `cycle` and `release` are two.** Between opening a cycle and shipping there are days
of building. A single invocation cannot span them. They are two moments where you sit down.

**Why checking that the documents agree is not a seventh skill.** It is the most requested
one that does not exist, and the reason it does not is the rule above. *"I documenti sono
coerenti?"* is already `audit`'s sentence — it is in its description in those words — so a
skill built to answer it would compete for exactly the phrase §2 forbids two skills to share,
and the cost is not one skill misfiring but both. It is also not a separate moment: you sit
down to check the documents once, and whether the answer is structural or semantic is a
property of the finding, not of the occasion.

What it needed was a second pass inside `audit`, not a second door, and the split between
script and judgment holds unchanged: `validate.py` checks that the link exists, and the skill
reads what is written at both ends of it. A `DEC` that decided Postgres and an `ARC#current`
still describing what it replaced validate cleanly and contradict each other, and no schema
will ever say so. The pairs are not a new checklist either: they are
`references/routing-table.md §2` read backwards, because a cascade that says *write A, then
update B* is already the list of what has to agree.

**Why cross-product work is not a seventh skill.** It is not a separate moment, it is a
constraint running through the others: in the cascade of `requirement` (a glossary metric
used by two products), in the checks of `audit` (single glossary, `DC` consumers), in the
classification of `cycle` (a `DEC` with `scope: platform`). A dedicated skill would
duplicate all of it.

---

## 3 · What every skill shares

Four things live once, at the plugin root, because six copies of them would be the framework
breaking its own single rule against itself.

**`references/preamble.md`** — read `AGENTS.md`, `OPEN.md` and the `product.yaml` first; the
class rules; never invent a field that attests something; never write `last_review` without
having read the document.

**`references/routing-table.md`** — the classification, the cascade and the conflict rules.
Read by `start`, `requirement` and `resolve`. It is the single source of that logic: if
copies diverged, the corpus and the conversational notes would end up in different places.

**Propose, then write.** Every skill that writes shows a compact table first, never the
document:

| File | What changes |
|---|---|
| `decisions/DEC-012-postgres.md` | new · datastore chosen, closes OD-003 |
| `products/alpha/ARC.md` | §current · store component added |
| `OPEN.md` | OD-003 moves from §1 to §4 |

Then, after the user agrees and the write has happened, it prints the document. A wall of
generated document is not reviewable, so nobody reviews it and the approval becomes a
formality. Two things are applied without asking, because they destroy nothing: appending a
`SIG` to `LOG`, and adding to the parking lot of `OPEN.md`.

**Close with the validator.** Not only `audit`. The cascade is where a write goes wrong, and
the validator is what notices that a `DEC` moved and its `ARC` did not.

---

## 4 · The two levels of evaluation

Merging these is the most expensive mistake available in this design, so they are named
separately everywhere.

| | Question | Artifacts | When |
|---|---|---|---|
| **Task acceptance** | did this change get done correctly? | `CHG#how-we-know-it-worked`, the validator, the project's tests | at the end of each change |
| **Product evaluation** | is the product good enough to ship? | `EVR` against the frozen `EVP` | at the release gate |

Collapse them and you get either an agent that believes the task is done because the model
eval passed, or a release gate firing on every micro-task. They meet at exactly one point,
already written in `AGENTS.md`: touching an AI component requires a new `EVR`.

---

## 5 · From documents to agents

This is what the framework is for, beyond documenting: `cycle` ends by producing a brief per
approved `CHG` that a coding agent can execute without inventing anything. Everything in the
brief already exists in the repository. The brief assembles, it does not compose.

```
Mandate       CHG-NNN §what-changes
Guardrails    CHG-NNN §what-must-not-change · OPEN.md, what it may not decide
Context       AGENTS.md authoritative sources · ARC#current · the relevant DC · GLOSSARY
Done when     CHG-NNN §how-we-know-it-worked · mandatory updates · validator clean
              a new EVR, if an AI component was touched
```

The chain that produces the work is the architecture itself:

```
ARC#delta   what is structurally missing
   ↓
RMP         in what order, and on what evidence
   ↓
CHG         what is authorized          ← the agent's task
   ↓
EVR/EVP     whether it can ship
```

---

## 6 · What not to automate

**Do not let a skill generate the content of `PRB`, `HYP`, `EVD`, `DFB`.**

An agent produces a plausible problem statement, a well formed hypothesis and a tidy
evidence brief without having talked to anyone and without having queried a single row. The
result passes any validator and contains no information. It is exactly the failure the
framework exists to prevent, documentation that *looks* true, and it has an unpleasant
property: it is indistinguishable from the good version under a quick reading, so nobody
notices until a decision taken on it turns out to be wrong.

The risk is highest in ingestion, where the temptation is strongest: the business corpus is
full of claims shaped like requirements, and turning one into an `EVD` takes a step that
looks small.

**The rule:** a skill may structure, classify, link, propagate and generate from existing
sources. **It may not produce evidence.** If a document answers "what did we observe", you
write it.

This is also why `resolve` is an interview and not a generator. Asking is the safe form of
filling a document: the skill elicits what you know instead of inventing what it does not.

---

## 7 · What is still missing

- **`--emit-manifest`.** The `GENERATED` sections of `product.yaml` are still written by
  hand, and the template says so at the bottom where somebody will read it. Build it at the
  first `CHG`, not before: with a handful of artifacts the manifest updates in thirty
  seconds and a generator would be a factory built before the product.
- **Distribution, not versioning.** A project can now say which framework it was written
  against, and `FW001`/`FW002` tell "the rules moved" from "we did this wrong". What is
  still missing is everything that would make the declaration binding: no tag, no
  installable release, no pinned commit, no migration note. A repository can declare
  version 1 and run version 2, get a warning, and still be checked by the rules of 2.
- **A baseline for the behaviour evals.** They show what a skill did; they do not show what
  would have happened without it. The comparison worth running is not one turn against one
  turn — the claim these skills make is that tomorrow's session does not start over, and a
  single exchange cannot see that. It needs two: one that writes the documents, one that
  begins cold and answers a question whose answer lives only in them, with the repository
  and without. Expensive, and worth designing after a real project has supplied both the
  documents and the questions.

The rule that protects the framework applies to the skills too: **every skill must save more
time than it costs to maintain, this week.** A skill is code, and like all code it ages and
has to be kept aligned with a framework that changes underneath it.
