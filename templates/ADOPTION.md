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
  building. Count the interviews. If you cannot separate the two, say so and estimate.
- **What it caught:** findings that changed what somebody did. A contradiction between two
  documents, a decision nobody had taken, an assumption an agent was about to make. Name
  them; a count is not evidence.
- **What was noise:** findings that were correct and did not matter, questions asked twice,
  documents nobody opened, fields filled in out of duty. This is the field people skip, and
  it is the one that makes the log worth keeping.

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
structure are ceremony — which is what makes the next rule get skipped too. Turn it off in
`framework.yaml`, or delete the section, and record here which and why.

| What | Cycles observed | Kept, or removed and why |
|---|---|---|
| `OD003` | 3 | kept: found two undecided high-cost entries in cycle 2 |
| `WF §target` | 3 | removed: written every cycle, opened by nobody |

---

## Anti-patterns

- **Counting instead of naming.** "Four findings" says nothing. Which four, and what
  changed because of them. A count can only go up, so it always reads as success.
- **Leaving `What was noise` empty.** It is never empty. An empty one means the entry was
  written to look good, and then the log has become another thing to maintain rather than
  the instrument that decides what to stop maintaining.
- **Editing a past entry.** This file is append-only for the same reason `LOG` is: the
  point is the trend, and a trend made of numbers you have gone back and improved is not
  one.
- **Recording minutes you did not measure.** An estimate labelled as an estimate is useful.
  An invented number that reads as measured is worse than no entry, because it will be
  compared against a real one later.
- **Keeping the log after the project stopped keeping the framework.** Set
  `status: abandoned` and write the last entry saying what happened. Two cycles of silence
  is a result — it is the strongest one this file can record — and a file that just trails
  off leaves the next reader thinking the project is still going.
