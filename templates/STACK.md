---
schema: framework/operational-stack/v1
artifact_type: operational-stack
lifecycle: living
status: active
owners: [NAME]
created: YYYY-MM-DD HH:MM
last_review: YYYY-MM-DD HH:MM
classification: internal
stack:
  query-engine:
    tool: DuckDB
    status: chosen
    decided_in: DEC-004
    used_by: [product-a]
  table-format:
    tool: Apache Iceberg
    status: unratified                # so it must NOT name a decided_in: nobody decided
    note: named on the architecture slide of the sales deck. Nobody decided it
  orchestration:
    tool: Airflow
    status: ruled-out
    decided_in: DEC-007
---

# Operational stack

**Question:** what do we reach for, who decided it, and what must not be introduced?

**Why it exists.** `ARC#current` describes the system that exists. A `DEC` records one
decision and the reasoning behind it. Neither answers the question somebody asks before
writing a line of code — *which tool do we use here, and which one is off the table* — and
answering it today means reading every decision in the register and hoping none was missed.

The section that earns this document its place is **§unratified**, and it is not the
embarrassing one. On a real project the architecture slide of a sales deck named eleven
tools. Every one of them was a decision, taken by whoever drew the slide, and none had a
`DEC` behind it. Before this file existed there was nowhere to write that down: the tools
were either absent from the documentation or described in `ARC#current` as though somebody
had chosen them.

It is `OPEN.md`'s **`Default in force`** applied to tooling. A tool in use is not a neutral
fact waiting for a decision — it is a decision already taken, by default, and naming it is
what turns it into one somebody can take on purpose.

**The front matter is the checkable half.** The body is where the reason goes, which is the
same split the `ICG` uses. A row names the `DEC` that chose it; it never restates the
argument, because when a decision is revisited the copy is what survives and gets believed.

---

<!-- section: chosen -->
## 1 · Chosen

One row per capability, not per tool: the capability is what the next person is looking for,
and two tools under one capability is either a mistake or a migration and both need saying.

| Capability | Tool | Version constraint | Decided in | Used by |
|---|---|---|---|---|
| Query engine | DuckDB | ≥ 1.0 | `DEC-004` | `product-a` |

**A row with no `decided_in` does not belong in this section.** That is what §unratified is
for, and moving a row up from there is exactly the act of taking the decision: write the
`DEC`, then move it. Filling this table with tools nobody chose produces a document that
looks like a set of decisions and is a list of accidents.

<!-- section: unratified -->
## 2 · In use, never decided

The honest section, and usually the longest one at the start. A tool that arrived in a
sales deck, in a proof of concept, or because somebody tried it on a Friday.

| Capability | Tool | Where it came from | What it would cost to change |
|---|---|---|---|
| Table format | Apache Iceberg | architecture slide, `ING-032` | high: the data lake is written in it |

**Where it came from** is a pointer, usually an `ING`, and never a retelling of the source.
**What it would cost to change** is why this section is ordered the way it is: the expensive
ones are the ones to ratify or replace first, and the cheap ones can stay unratified for a
long time without hurting anybody.

Each row is a candidate for `OPEN.md`. Not all of them: a formatter nobody will ever argue
about does not need a decision. The ones that constrain something else do, and those are the
ones with a high cost to change.

<!-- section: ruled-out -->
## 3 · Ruled out

What must not be introduced, and why not. This section is read by agents more often than
either of the others, because it is the only one that answers a question with "no".

| Tool | Ruled out in | Instead of it |
|---|---|---|
| Airflow | `DEC-007` | the orchestration lives in the integration layer |

Without this an agent proposing a second orchestrator is doing something reasonable: nothing
told it there had been an argument. A rejected option that leaves no trace gets re-proposed
every few months, and each time the reasoning has to be reconstructed by whoever remembers.

---

## Anti-patterns

- **A row in §chosen with no `DEC`.** It reads as decided and it is not, and the difference
  matters the moment somebody wants to change it: a decision can be revisited, an accident
  has to be reconstructed first.
- **Restating why, here.** The reason lives in the `DEC` this row names. Two copies of an
  argument diverge, and this one — shorter, in a table, easier to read — is the one that
  gets believed.
- **Listing libraries.** This is not a dependency file. A row belongs here when choosing
  differently would have changed the architecture, not when it saved somebody an afternoon.
  `requirements.txt` already exists and is generated.
- **An empty §unratified on a project older than a week.** Every project runs on tools
  nobody voted on. An empty section means they have not been looked for.
- **Leaving §ruled-out empty because nothing was rejected.** Something was: every chosen
  tool beat an alternative, and the alternative is what an agent will suggest.
