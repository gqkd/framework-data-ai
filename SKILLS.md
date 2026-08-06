# Skills for managing the framework

Five skills. Two are to be rebuilt (`framework-capture`, `framework-audit`), three are
specified well enough to be implemented when they are needed.

---

## 1 · A necessary clarification about automation

The goal, "not updating everything by hand" and replacing the "automated checks to add to
CI", is reachable, but not all of it with the same tool.

**A skill is not a daemon.** It runs when Claude runs: it does not fire on a push, it
checks nothing overnight, it has no state between one invocation and the next. If the
checks lived only in the skills, they would run when you remember to ask, which is to say
rarely and not at the moments that count.

| Nature of the task | Tool | When it runs |
|---|---|---|
| Deterministic: schema, IDs, references, staleness, indexes | **Python script** | in CI on every push, and by hand when needed |
| Extraction from formats: pptx, pdf, docx with provenance | **Python script** | when you ingest |
| Requires judgment: classifying a claim, propagating a cascade, writing a `CHG` | **Skill** | when you invoke it |
| Requires your knowledge: what was observed, what was promised | **You** | |

**The skills carry the scripts.** `framework-audit` contains `validate.py`: the skill runs
it interactively and interprets the results, CI runs the same file and blocks the merge.
One implementation, two entry points. If the logic were duplicated in the skill's
instructions it would diverge from the version that runs in CI, that is, from the one that
counts.

**The skills live in the repository**, under `skills/`, versioned with the code. They are
the same for the three products: `product.yaml` says which one they are being applied to.
It is the concrete mechanism for managing the three projects together. You do not need one
skill per product.

---

## 2 · Why five

A skill is selected on the basis of its description, and a vague description triggers
unreliably: it fires when it is not needed and does not fire when it would be. Five
boundaries correspond to the five moments where you genuinely change working mode:

**set up** · **record** · **change** · **release** · **verify**

### Why corpus and conversation are a single skill

They look like two different things: loading two hundred slides, and saying "we decided on
Postgres". But the underlying operation is identical, *external information → classified →
routed → propagated*, and the logic that governs it (taxonomy, cascade, conflict handling)
is the same.

If they sat in two skills that logic would be duplicated, and it would diverge: after three
months the corpus and the conversational notes would end up in different places, and you
would not notice until an agent found two conflicting answers. It is the same reason
`validate.py` is a single file.

So: **one skill, two input modes, one shared reference.**

```
framework-capture/
├── SKILL.md                    mode selection + conversational procedure
├── references/
│   ├── routing-table.md        ⟵ the core: taxonomy, cascade, conflicts
│   └── ingest-bulk.md          procedure for the business corpus
└── scripts/
    └── extract.py              pptx · pdf · docx → blocks with provenance
```

### Why not a sixth skill for the three products

Cross-product management is not a separate moment of work: it is a constraint that runs
through the other five. It lives inside each of them: in the cascade of `capture` (a
glossary metric used by two products), in the checks of `audit` (single glossary, consumers
of the `DC`), in the classification of `change` (a `DEC` with `scope: platform`). A
dedicated skill would duplicate all of this.

---

## 3 · `framework-capture`: recording *(to be rebuilt)*

The skill you will use most of all. It is the answer to "I want to add information
conversationally and I want the files to be changed consistently".

### Mode A: business corpus

Presentations, PDFs, requirements analyses produced by the business before the technical
project existed.

The starting point that changes everything: **these documents are not a specification.**
They are the record of what was promised, produced by the people whose job was to sell. The
main destination is `COMMITMENTS.md`, not a product document. But they also contain five
things of different value (domain vocabulary, numeric promises, constraints disguised as
claims, descriptions of the current process, competitors mentioned) and they have to be
separated because they end up in five places.

`extract.py` normalizes pptx, pdf, docx and text into blocks labeled with document and
position (slide N, page N). Two behaviors that are worth more than the rest:

- **It flags and rasterizes text-poor pages.** On a sales deck the architectural promise is
  often *drawn*: three boxes with arrows and the words "single platform" produce no
  extractable text and are a tenancy constraint.
- **It recognizes decks exported to PDF** and warns that the extracted text has lost the
  layout, because in a deck the layout carries meaning.

Then classification goes through **`ING.md`**, not straight into the artifacts: it preserves
provenance, it acts as an interruptible review queue, and it lets you reject a claim while
keeping the fact that the business made it. That is exactly what you need when, eight months
later, someone asks why that feature is not there.

**The highest-value output is the contradictions.** Three documents written by different
people over eight months contradict each other, and nobody knows because nobody has read
them all in one go. On the trial corpus one surfaces immediately: the deck promises
"real-time data", the requirements analysis says "hourly refresh, existing nightly batch".
If the two versions were told to two different customers this is not a technical problem but
a commitment to renegotiate, and sooner is better.

### Mode B: conversational

**It does not record sentence by sentence.** A conversation is largely reasoning out loud,
and filing every claim produces a log of noise in which the real facts become impossible to
find. And since that log is the source an agent will work from, the damage propagates.

The model is the **end-of-session sweep**:

> From this conversation four things look recordable to me:
> 1. *decision*: Postgres as the datastore → new `DEC` + `ARC` + closes `OD-005`
> 2. *definition*: "active customer" = login in the last 30 days → `GLOSSARY`, **in
>    conflict** with the formula already present for product-b
> 3. *request*: Excel export asked for by the customer → `SIG` in `LOG`
> 4. *reasoning*: consider separating reporting → parking lot
>
> Which ones do I record?

Exceptions written immediately: an **incident** (the value depends on the exact time) and an
**out-of-reach commitment** that has just surfaced.

### The three ideas that make consistency work

**Classification goes on epistemic strength, not on the topic.** "The system processes 10M
rows a day" can mean *we promised it*, *we believe it will be needed* or *we measured it*:
three things with the same textual shape that go to three different places. If the context
does not tell them apart, the skill asks. It is the question that pays best.

**The cascade is mandatory and tabulated.** A `DEC` with `scope: architecture` forces you to
update `ARC` in the same pass; a glossary entry for a term that is also a field of a `DC`
forces you to bump that contract; an out-of-reach commitment opens a row in `RSK` and one in
`OPEN`. Writing to a single file is easy: writing to the right four is why the skill exists.

**Automaticity is inversely proportional to the breadth of the cascade.** A single
destination, append-only, no ambiguity, no conflict → apply directly. Cascade over several
files, an immutable involved, a conflict detected, ambiguous classification → propose the
diff and wait. The cascade is the point where an agent's confidence exceeds its accuracy:
asking costs ten seconds, this mistake costs a decision.

---

## 4 · `framework-init`: setting up

**Triggers on:** "set up the framework", "new product", "I have code with no
documentation", "where do I start".

1. **Entry assessment.** Idea · idea already sold · code without documentation · product in
   production. It is not a formality: the entry point determines which documents make sense
   and which would be fiction.
2. **Scaffolding.** Folder tree, relevant templates with the front matter filled in. Not the
   body.
3. **Delegates to `framework-capture`** the ingestion of the business corpus, when the entry
   point is "already sold". It does not reimplement extraction: it calls it.
4. **Reconstruction from code**, when the entry point is "existing code": it proposes a
   starting `ARC` and, the useful part, lists the **decisions already implicit in the code**
   that have no `DEC`. A datastore chosen, a tenancy model: these are decisions taken, just
   not recorded.
5. **Seeds `OPEN.md`** with the decisions still to take, each with its cost to reverse.

**Frequency:** three times in total. And that is right: a skill used three times that gets
you started with the correct structure is worth more than ten runs of something marginal.

---

## 5 · `framework-change`: changing

**Triggers on:** "I need to add", "what do I do in this cycle", "open a change".

It implements the stretch of the cycle that was in the wrong order: intake → triage → `ICG`
→ reshaping → `CHG` → `IMP`.

1. **Triage and impact assessment.** It reads `PBR`, `ARC`, the `DC`, `EVP`, `RSK` and
   **proposes** the `ICG` classification. An `ICG` decided automatically is a gate that does
   not exist.
2. **Routes.** If reshaping is needed, it lists which artifacts to update **before** writing
   the plan. If the routing is "hypothesis invalidated" it stops: the re-entry is in F3 or
   F2, not in a `CHG`.
3. **Writes the `CHG`** with the three mandatory fields. The added value is **What must NOT
   change**: the skill fills it in better than you do, because it can read `ARC` and the `DC`
   and find the contracts the change risks breaking without anyone having noticed.
4. **Updates `IMP`** and the `§excluded` section.
5. **Verifies** with `validate.py` before taking the `CHG` to `verified`.

**Boundary with `capture`:** `capture` records the signal in `LOG`; `change` turns it into a
mandate. A recorded signal is not authorized to be implemented. That is the separation that
stops a product from becoming the sum of the last things anyone asked for.

---

## 6 · `framework-release`: releasing

**Triggers on:** "release", "prepare the release", "can I release?".

1. **Checks the `RG` gate:** an `EVR` exists for the candidate, it cites the `EVP` in its
   frozen version, all metrics and slices are above threshold. If not: **rework**, and it
   says so with that word, because this is not a rollback. It is not in production yet.
2. **Generates `RLM.yaml`** from git, the build and the configuration: commit, digest, model
   and prompt versions, dataset, `DC` touched, `CHG` included, rollback target. Filling it
   in by hand means getting it wrong.
3. **Generates `REL.md`** from the `CHG`, translated into effects. Ten lines.
4. **Updates** `product.yaml` and opens a `SIG` of type `metric` for the first 48 hours.
5. **It does not run the deploy.** It prepares the evidence; you give the command.

It is the skill with the lowest share of judgment, and therefore the one that saves the most
time at equal risk.

---

## 7 · `framework-audit`: verifying *(to be rebuilt)*

`skills/framework-audit/` with `scripts/validate.py`, to be verified on a trial repository.

It checks: front matter and schema by type · consistency between `lifecycle` and type ·
`status` within the type's enumeration · uniqueness of IDs · dangling references · cycles in
the supersedence chain · mandatory sections (`What must NOT change` of a `CHG`, `§delta` of a
`WF`, the three of `RSK`, the three of `ING`) · staleness of the living artifacts · `CHG`
that declare an impact without the artifact that derives from it · rollback undefined or
untested · closed decisions still listed as open.

**Cross-product:** single glossary · consumers of the `DC` that match existing products ·
products without a `PBR`.

**Generates:** `decisions/INDEX.md` and `TRACEABILITY.md`.

A hygiene rule worth repeating: **do not update `last_review` without having read the
document.** It is the fastest action for turning the validator green again and the only one
that makes the entire framework useless.

### To be built: `--emit-manifest`, for the `GENERATED` sections of `product.yaml`

Today those sections are marked "generated" and a person writes them. A section that
declares itself generated and is not, is **worse than one written by hand**: nobody rereads
it, because everyone assumes something keeps it true.

Before writing the generator, split the manifest fields into two groups. The dividing line
is: *does filling it in require judgment?*

| Derivable, the script does it | From what |
|---|---|
| `artifacts.living[].last_review`, `.stale` | the same scan the validator already does |
| `artifacts.immutable_count`, `.append_only` | same |
| `open_decisions` | the `### OD-NNN` headings of `OPEN.md §1` |
| `open_risks` | `RSK.md §state` |
| `active_changes` | the `CHG` with `status: approved` |
| `release.*` | the last `REL`/`RLM`, and `rollback_target` from the one before it |

| Not derivable, stays conversational | Why |
|---|---|
| `stage.block`, `.phase`, `.next_gate`, `.mor_completed` | a gate is cleared by a person; no file records it before the `DEC` |
| `one_liner`, `name` | it is a positioning decision |
| `platform.shares` | it is `OD-002`, that is, an open decision |
| `entry_points`, `roles` | conventions, not observable facts |

Then: **the first group is generated by `validate.py --emit-manifest`**, alongside
`--emit-index`, because it derives from the same scan and is the same kind of object, an
index. The second group is maintained by `framework-capture` in conversational mode: "we
cleared G3" is a claim with a destination, and `routing-table.md` is already the place where
you decide which one.

You do not need a new skill for this, and the reason is the same as in
[§2 · Why not a sixth skill for the three products](#why-not-a-sixth-skill-for-the-three-products):
a skill that "manages the manifest" would duplicate the scan of `audit` and the taxonomy of
`capture` in order to hold together a file that is only the projection of both.

Three constraints on the generator, which are the reason it has to be written and not
improvised:

1. **Regenerating must not be able to erase the second group.** It rewrites the fields it
   owns, it leaves the others intact. A generator that rewrites the whole file loses `stage`
   on the first run, and nobody notices until it matters.
2. **It must be idempotent and checkable in CI.** `--emit-manifest --check` exits non-zero if
   the file on disk diverges from what would be generated: it is the only way to notice that
   someone has hand-written into a generated field.
3. **Until it exists, the fields stay marked for what they are.** The comment at the bottom
   of `templates/product.yaml` says that today you fill them in yourself. That comment
   disappears together with the problem, not before.

**When to build it:** when there are enough artifacts that rereading them by hand costs more
than writing the script. Realistically at the first `CHG`, not before. With three `PBR` and
zero `CHG` the manifest updates in thirty seconds and the generator is the factory built
before the product.

---

## 8 · What not to automate

**Do not let a skill generate the content of `PRB`, `HYP`, `EVD`, `DFB`.**

An agent produces a plausible problem statement, a well-formed hypothesis and a tidy evidence
brief without having talked to anyone and without having queried a single piece of data. The
result passes any validator and contains no information. It is exactly the failure the
framework exists to prevent, documentation that *looks* true, and it has an unpleasant
property: it is indistinguishable from the good version under a quick inspection, so you do
not notice until a decision taken on that basis turns out to be wrong.

The risk is highest precisely in ingestion, where the temptation is strong: the business
corpus contains claims shaped like requirements, and turning them into an `EVD` takes a step
that looks small. It is not: nobody observed anything.

**The rule:** a skill can structure, classify, link, propagate and generate from existing
sources. **It cannot produce evidence.** If a document answers "what did we observe", you
write it.

---

## 9 · Build order

| When | What | Why now |
|---|---|---|
| Now | `framework-capture` | You have the business corpus to ingest and you have nothing yet. It is the first real job |
| Now | `framework-audit` | Turn it on in CI with **one** check only: valid front matter. The rest later |
| Before the first commit | `framework-init` | You use it three times and it saves you three divergent structures |
| At the first real change cycle | `framework-change` | Before that you do not have enough signals for it to be needed |
| At the first `CHG` | `validate.py --emit-manifest` | Before that the manifest updates by hand in thirty seconds. See §7 |
| At the first release | `framework-release` | Before that there is nothing to release |

On CI checks: **add them one at a time, when the failure they prevent has already happened
once.** Twelve checks turned on before the code exists are a factory built before the
product: they slow you down without having prevented anything yet, and the predictable
reaction is to turn them all off.

The rule that protects the framework applies to the skills too: **every skill must save more
time than it costs to maintain, this week.** A skill is code, and like all code it ages and
has to be kept aligned with a framework that changes in the meantime.
