# Routing table

Shared by `start`, `requirement` and `resolve`, and by `cycle` for §4. It answers one
question: **given a statement, where does it get written and what changes with it?**

This is the only source of that logic. Do not restate it inside a skill: if the copies
diverged, the corpus and the conversational notes would end up in different places, and
nobody would notice until an agent found two conflicting answers.

---

## 1 · Classification

The kind of a statement does not follow from its subject but from its **epistemic
strength**. The same sentence can be a promise, a belief or an observation, and the three
go to different places. "The system processes 10M rows a day" can mean *we promised it*,
*we believe it will be needed*, or *we measured it*. When the context does not tell them
apart, **ask**: it is the question that pays best in the whole skill.

| Kind | Recognisable by | Authoritative destination | Class |
|---|---|---|---|
| **Commitment** | it appears in a document shown to a customer; "we promised", "it is in the contract" | `COMMITMENTS.md` → `CMT-NNN` | living |
| **Decision taken** | "we decided", "we are using X", "we are going with" | new `DEC-NNN` | immutable |
| **Definition** | "an X is", "it is computed as", "by Y we mean" | `GLOSSARY.md` | living |
| **Observation about the present** | "today it works like this", "the data arrives hourly" | `WF.md#current` | living |
| **Evidence gathered** | "I interviewed", "I queried the table" | `EVD-NNN` or `DFB-NNN` | immutable |
| **Customer problem** | "the problem is that", "they waste time on" | `PRB-NNN` | immutable |
| **Hypothesis** | "if we did X then Y" | `HYP-NNN` | immutable |
| **Request or feedback** | "the customer wants", "they asked for" | `LOG.md` → `SIG-NNN`, type `feedback` / `request` | append-only |
| **Incident or anomaly** | "it went down", "the numbers look wrong" | `LOG.md` → `SIG-NNN`, type `incident` / `drift` | append-only |
| **Constraint** | "we cannot", "the regulation requires", "it has to stay in the EU" | `RSK.md#state` + `PBR.md` constraints | living |
| **Risk** | "there is a risk that", "if it happened" | `RSK.md#state` | living |
| **Numeric target** | "a 30% reduction", "under 2 seconds" | `EVP.md` threshold, **and** `COMMITMENTS` if it was promised | living |
| **Promised capability** | "the system will do", "it includes the module" | `PBR.md` capability | living |
| **Correction of something written** | "actually no", "that changed" | depends on the document holding it → §3 | — |
| **Unfinished reasoning** | "maybe", "I am thinking", "we could look at" | `OPEN.md` §3 parking lot **at the root**, or nothing | living |

**Which open register.** `OPEN.md` is the one destination in this table that is not a single
file: one per product, one for the substrate, one at the root. The entry goes in the
register of the thing it is about — `products/<p>/OPEN.md` when it concerns one product,
`platform/OPEN.md` when it concerns the substrate, the root when it concerns no single one.
The parking lot is the exception and it is always at the root: what sits there has not been
qualified yet, and deciding whose it is is part of qualifying it. Numbering continues across
all of them, never restarts.

**The one most often got wrong.** A request is not a mandate. "The customer wants Excel
export" goes into `LOG` as a `SIG`, and at most produces a conditional increment in `RMP`.
It does **not** become a `CHG` and does not get implemented: that requires intake, triage
and the `ICG`. Skipping that step is how a product becomes the sum of the last things
anyone asked for.

**The most treacherous one.** A marketing sentence is often an architectural decision. "One
single experience across the three modules" is not a claim, it is a decision about tenancy
and identity, which means it belongs in `OPEN.md` as an `OD`. Whenever you classify a
commitment, ask **which technical constraint follows from it** and write that down next to
it. If that column is empty for every row, the classification is not finished.

---

## 2 · Cascade

Writing in one place is not enough: consistency lives in the linked writes. These are
mandatory, and the validator verifies some of them.

| If you write | You must also |
|---|---|
| `DEC` with `scope: architecture` | update `ARC.md#current` in the same pass, and `#target` if the destination moved |
| `DEC` with `scope: product` | update `PBR.md` if capability, scope or outcome change |
| `DEC` with `scope: platform` | list **every** product in `products`, and update `PLATFORM.md` |
| a `DEC` that closes an `OPEN.md` entry | move the entry to §4 **of the register it is already in**, with the cross reference, and carry `derives_from: [OD-NNN]` on the `DEC` |
| a `GLOSSARY` entry for a term that is also a field of a `DC` | update the semantics of that `DC` and bump its version |
| a `GLOSSARY` metric used by more than one product | check every product computes it with that formula. If they cannot, they are two metrics and need two names |
| a `CMT` that is out of technical reach | open a row in `RSK#state` **and** an entry in `OPEN.md`, and tell the user it is the most urgent thing in the project |
| a constraint on data (freshness, volume, residency) | update the **guarantees** of the relevant `DC`, not only its schema |
| a threshold in `EVP` | if it lowers an existing threshold, it needs a `DEC` with the reason. Never silently |
| a `SIG` that materialises a known risk | add a row to `RSK#events` |
| `WF#current` | check whether `#delta` is still true. A stale delta is a silent lie |
| `ARC#target` | check whether `ARC#delta` is still true, for the same reason |
| a `PBR` capability that depends on another product | check an internal `DC` exists for that contact point |

---

## 3 · Corrections, and the class rule

A correction is the most delicate operation, because the class of the document decides
**what you are allowed to do**.

| Class of the document | Allowed operation |
|---|---|
| **living** | edit in place. `last_review` is proposed and not written: it attests a reading, and the instant goes in the proposal (`YYYY-MM-DD HH:MM`, not the date alone: it can happen more than once in a day) |
| **immutable** | **never edit.** Create a new document with `supersedes`, and move the old one to `status: superseded` |
| **append-only** | **never rewrite a line.** Add a linked event (`ANA-NNN` on `SIG-NNN`) |

On immutables the temptation is strong and worth naming: if a `PRB` turns out to be wrong,
the repair is not to edit it. That document records what we believed then, and erasing it
destroys the only thing that makes it reconstructible why a decision looked sensible.
Write a new `PRB`.

---

## 4 · Conflicts

Before writing, check whether the statement contradicts something already there. **A
detected conflict is the most useful output of the skill** and it is not resolved
automatically: it goes to the user.

Look in these six places, which is where conflicts hide:

1. **Data guarantees** — does it contradict the freshness or completeness declared in a `DC`?
2. **Definitions** — is the term already in `GLOSSARY` with a different definition, or with
   a "does not include" the statement violates?
3. **Commitments** — does it contradict a `CMT`? This is the most expensive one, because
   somebody said it to a customer.
4. **Decisions** — is there an `accepted` `DEC` saying the opposite? Then this is not new
   information, it is a change of decision, and it needs a `DEC` that supersedes.
5. **Out of scope** — does it concern something `PBR` or `RMP` explicitly exclude? That is
   not an oversight, it was decided.
6. **Open decisions** — is the necessary choice listed in `OPEN.md`? Then do not write it as
   a fact: it is still open, and this may be the information that closes it, but the user
   closes it, not you.

When you find one: **stop, show both versions with their provenance, ask which one holds.**
Do not default to the more recent. In a business corpus the most recent document is often
the sales deck, which is the least reliable one about facts.

---

## 5 · How much to apply without asking

**Autonomy is inversely proportional to the breadth of the cascade.**

**Apply directly**, without asking: one destination, append-only class, no interpretation,
no conflict. In practice that is recording a `SIG` in `LOG`, or an entry in the parking lot
in `§3` of the root `OPEN.md`. These destroy nothing, and asking would only make them
annoying.

**Propose and wait** in every other case, and in particular: the cascade touches more than
one file · an immutable is involved · you detected a conflict · the classification was
ambiguous · the write would close an `OPEN.md` entry.

The reason is precise: the cascade is the point where an agent's confidence exceeds its
accuracy. A wrong classification writes a plausible fact into the authoritative place, and
from then on everyone, people and agents, reads it as true. Asking costs ten seconds. This
mistake costs a decision.

---

## 6 · The end-of-session sweep

In conversational mode, **do not record sentence by sentence.** A conversation is largely
reasoning out loud, and filing every claim produces a log of noise in which the real facts
become impossible to find. Since that log is what an agent will work from, the damage
propagates.

Keep track of what looks recordable, and when the conversation reaches a resting point, or
when the user asks, present the list:

> From this conversation four things look recordable:
> 1. *decision* — Postgres as the primary datastore → new `DEC` + `ARC` + closes `OD-005`
> 2. *definition* — "active customer" = login in the last 30 days → `GLOSSARY`, **in
>    conflict** with the formula already there for product-b
> 3. *request* — Excel export asked for by the customer → `SIG` in `LOG`
> 4. *reasoning* — consider splitting the reporting module → parking lot
>
> Which ones do I record?

Two exceptions get written immediately, without waiting: an **incident** (the value depends
on the exact time) and a commitment that has just turned out to be **out of reach**.
