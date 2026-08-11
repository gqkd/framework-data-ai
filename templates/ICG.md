---
schema: framework/impact-classification/v1
artifact_type: impact-classification
lifecycle: immutable
status: proposed
id: ICG-NNN
products: [product-a]
owners: [NAME]
created: YYYY-MM-DD HH:MM
routing:
  SIG-NNN: architecture
  INC-NNN: none
impacts:
  SIG-NNN: [data]
classification: internal
---

# ICG-NNN · Triage of cycle N

**Question:** of everything that could be built now, what kind of change is each candidate,
and what does that make it cost?

`status`: `proposed | accepted | superseded`

**Why it exists.** The impact classification is a gate, and a gate that leaves no written
trace is not a gate, it is a meeting. Until this document existed the classification lived
as a line inside a `CHG`, which meant it only survived for candidates that became changes:
the ones routed back into discovery, and every triage a user stopped after reading, left
nothing behind at all. It also means the routing is a field rather than prose, which is what
a check can read.

One of these per cycle, not one per candidate. A triage is a comparison: the reason a
candidate is not being opened is usually another candidate.

---

## The front matter carries the verdict

`routing` is where each candidate goes and there is exactly one answer per candidate.
`impacts` is what it touches on the way, and a candidate can touch several, so it is a
separate field and not a longer list of routings. Both are keyed by the candidate's own
identifier, so a `CHG` written later can be traced back to the row that authorized it.

| `routing` | What follows |
|---|---|
| `none` | no structural impact: a technical `CHG`, straight to `IMP` |
| `product` | product reshaping → `PBR`, `WF` |
| `architecture` | architecture reshaping → `ARC`, `DEC` |
| `both` | joint reshaping |
| `hypothesis-invalidated` | re-entry into F3. **Not** a `CHG` |
| `problem-invalidated` | re-entry into F2. **Not** a `CHG` |
| `not-classifiable` | the evidence to classify it does not exist yet. Say what would settle it |
| `not-a-candidate` | looked at, and it is not a change proposal at all. Say why in §3 |

| `impacts` | What it requires |
|---|---|
| `architecture` | an updated `ARC` **and** a `DEC` |
| `data` | a `DC` version bump and notice to its consumers |
| `ai` | a new `EVR` |
| `risk-compliance` | a line in `RSK §state` |

`not-classifiable` is not an escape hatch, it is the honest answer to the most common case
at triage. Three people saying a number feels wrong is not an invalidated hypothesis and it
is not a bug either, and forcing it into either is how a real signal gets closed or a
working product gets torn up. Name the measurement that would decide it.

---

<!-- section: intake -->
## 1 · What was considered

Where the candidates came from and, more importantly, where they stopped.

**Every signal you read goes in `routing`, including the ones that go nowhere.** `LOG` is
append-only, so a row can never be marked handled and triage state cannot live there. It
lives here instead, which means the difference between a signal nobody has read and one
somebody read and set aside exists only if you record the second. `ICG001` reports the
first, and it can only tell them apart because `not-a-candidate` is written down. A signal
left out of `routing` because it was obviously nothing will be re-read every cycle from now
until somebody routes it.

- **From `LOG.md`:** which signals, and from which point onwards.
- **From `RMP.md`:** which increments were live candidates this cycle.
- **From `ARC#delta`:** which structural gaps. A delta row with no `RMP` entry is worth
  naming: something structural is missing from the plan.
- **From the conversation:** candidates the user raised that were in no document. Write
  them into `LOG` or `RMP` first, then classify them. A candidate that exists only in a chat
  window cannot be audited later.

<!-- section: classification -->
## 2 · Each candidate, and why

One row per candidate in `routing`, in the order that makes the cycle legible rather than by
identifier. Give the reason against a document, not against an impression: the classification
is only reviewable if the reader can check what it was based on.

| Candidate | Routing | Impacts | Why, and against which document |
|---|---|---|---|
| `SIG-NNN` | `architecture` | `data` | contradicts `DEC-NNN`, which states … |

**Propose, do not decide.** A classification applied automatically is a gate that does not
exist. This document is written `proposed` and becomes `accepted` when the user says so.

<!-- section: open-questions -->
## 3 · What is unresolved, and what it blocks

Everything that has to come back to a person before the cycle can proceed. A triage that
ends with nothing here has usually stopped looking.

- **Conflicts.** A candidate that contradicts a `CMT`, a `DEC`, a `DC` guarantee or an
  explicit `PBR` exclusion is not a change to classify. `references/routing-table.md` §4
  says what to do: show both versions with their provenance and ask which one holds. Do not
  resolve it here.
- **Missing evidence.** Each `not-classifiable` candidate, with the measurement that would
  settle it.
- **Precedence.** When one candidate's routing changes what another is worth, say so. An
  increment built on a hypothesis this triage just invalidated is not worth opening, and
  that judgement belongs in front of the user rather than inside your ordering.
- **Decisions nobody has taken.** These hand off to `resolve`. Do not take them here to keep
  the cycle moving.
