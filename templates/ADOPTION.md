---
schema: framework/adoption-log/v1
artifact_type: adoption-log
lifecycle: append-only
status: active
owners: [NAME]
created: YYYY-MM-DD HH:MM
classification: internal
---

# Adoption log

**Question:** is this framework paying for itself, and which parts of it are not?

`status`: `active | abandoned`

**Why it exists.** Every check, template and rule in this framework was written against a
failure somebody imagined. This is the only file that records which of them met a failure
that actually happened. Without it the framework can only grow: nobody ever has grounds to
delete anything, and a structure that only accumulates is one people eventually route
around instead of arguing with.

It is also the only artifact here that is about the framework rather than about the
product. It does not describe what you are building. It describes what documenting it
cost.

**Three fields per cycle.** Not seven. A log that takes an afternoon does not get a second
entry, and a single entry is worth nothing — the value is entirely in comparing the third
cycle with the first. Add a fourth field when you have wanted it twice.

**Write it at the end of the cycle, not from memory a month later.** The number that
matters most is the one hardest to reconstruct: the minutes. Nobody remembers whether the
release gate took twenty minutes or ninety, and that difference is the whole question.

---

<!-- section: cycles -->
## 1 · One entry per cycle

Append. Never edit a past entry: this file is the record of what you believed at the time,
and a corrected number tells you nothing about whether the framework is improving.

### YYYY-MM · what the cycle was about

- **Minutes on the framework:** time spent writing and updating documents, not time spent
  building. Count the interviews. **Label where the number came from** — `measured`,
  `estimated`, or `not measured` — and never leave that off. An agent has no reliable clock
  across a session and a person does not remember, so an unlabelled number is a guess that
  will be compared against a real one later.
- **What it caught:** findings that changed what somebody did. A contradiction between two
  documents, a decision nobody had taken, an assumption an agent was about to make. Name
  them; a count is not evidence.
- **What was noise:** findings that were correct and did not matter, questions asked twice,
  documents nobody opened, fields filled in out of duty. **This is the user's answer, not
  the agent's**, and if nobody has answered it the value is `not assessed`. Never `none`: an
  invented zero in the one field that exists to retire parts of this framework will look
  like an improvement next cycle.

### 2026-MM · example, delete it

- **Minutes on the framework:** 85. Most of it the triage, which needed three passes
  because the roadmap and the signal log disagreed about what was already committed.
- **What it caught:** two commitments to different customers that cannot both hold
  (`CMT-004` / `CMT-011`), found while answering an unrelated question. One decision that
  had been taken in a meeting and existed nowhere.
- **What was noise:** `OD003` fired on four entries whose cost to reverse was mislabelled
  rather than undecided. The `WF§target` section was written and never read by anybody.

<!-- section: verdict -->
## 2 · What this changes, once there is enough to compare

Do not fill this in during the first cycle. It needs at least three.

**The survival test, applied to one artifact or one check at a time:**

> It has to have prevented an error that happened, carried a decision somebody actually
> took, or saved time in the following cycle.

Something that has done none of the three in three cycles is not neutral. It costs
attention every time somebody reads these instructions, and it teaches that parts of this
structure are ceremony — which is what makes the next rule get skipped too.

**What a project can decide by itself, and what it can only propose.** Not everything here
is local, and this file is evidence rather than a second registry: a section that a type
must carry is defined centrally, and deleting it produces `SEC001` rather than a leaner
repository. Three verdicts, and they are not interchangeable:

| Verdict | What it means | Where it takes effect |
|---|---|---|
| **turned off** | a check that has cost more attention than it has caught | `checks:` in this project's `framework.yaml`. Yours to decide |
| **stopped writing** | an artifact this project never needed. Nothing forces one to exist before the thing it documents | here, and nowhere else. Nothing breaks: an absent artifact is not a finding |
| **proposed** | a required section or field that has earned nothing in three cycles | an issue on the framework, quoting the rows below. Not something this repository can change |

| What | Cycles observed | Verdict, and the evidence |
|---|---|---|
| `OD003` | 3 | kept: found two undecided high-cost entries in cycle 2 |
| `CMP` | 3 | stopped writing: no competitor was ever named in a decision |
| `WF §target` | 3 | proposed: written every cycle, opened by nobody. Cannot be removed here |

---

## Anti-patterns

- **Counting instead of naming.** "Four findings" says nothing. Which four, and what
  changed because of them. A count can only go up, so it always reads as success.
- **Answering `What was noise` on the user's behalf.** The agent is the last one who can
  see it: what it produced looks necessary from where it is standing. Ask, and write `not
  assessed` if no answer comes. `none` is the one value that must never be written here,
  because next cycle it will be read as a baseline that got worse.
- **Editing a past entry.** This file is append-only for the same reason `LOG` is: the
  point is the trend, and a trend made of numbers you have gone back and improved is not
  one.
- **Recording minutes you did not measure.** An estimate labelled as an estimate is useful.
  An invented number that reads as measured is worse than no entry, because it will be
  compared against a real one later. `not measured` is a legitimate value and the only
  honest one when nobody looked at a clock.
- **Writing a verdict this repository cannot carry out.** "Removed `WF §target`" reads as
  done and produces `SEC001` on the next run, and then the finding gets explained away
  rather than acted on. A section the framework requires can only be `proposed` from here.
- **Keeping the log after the project stopped keeping the framework.** Set
  `status: abandoned` and write the last entry saying what happened. Two cycles of silence
  is a result — it is the strongest one this file can record — and a file that just trails
  off leaves the next reader thinking the project is still going.
