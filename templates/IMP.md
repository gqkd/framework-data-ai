---
schema: framework/cycle-plan/v1
artifact_type: cycle-plan
lifecycle: living
status: active
version: 12
products: [product-a]
owners: [NAME]
created: YYYY-MM-DD HH:MM
last_review: YYYY-MM-DD HH:MM
classification: internal
---

# Cycle implementation plan: cycle N

**Question:** how do we execute the change contracts approved in this cycle?

**Living, replaced every cycle: the latest one always holds.** It is an **output** of
reshaping, not an input. Writing the plan before you know whether product or architecture
have to change means rewriting it the moment reshaping changes the scope. `version` is the
cycle number.

## Selected changes

| `CHG` | Why now | Depends on | Status |
|---|---|---|---|

## §Excluded in this cycle

The changes assessed and not selected, with the reason.

This is the section that saves you from re-explaining the same choice every week, and that
tells an agent the difference between "it was not done" and "it was decided not to do it".

## Sequence and dependencies

Order of execution. What blocks what.

## Integration and rollout strategy

How the changes land together. If they are released separately, in what order and with what
intermediate compatibility.

## Impact on artifacts

| Artifact | Update required |
|---|---|
| `ARC` | |
| `DC` | |
| `EVP` | if the thresholds change you need a `DEC` |
| `RSK` | |

## Cycle outcome

*Filled in at closing.* What landed, what slipped, what was abandoned.

---

## Anti-patterns

- **Writing it before reshaping.** A structural error: the plan is obsolete the moment
  reshaping changes the scope.
- **No "excluded" section.**
- **Containing `RMP` increments instead of `CHG`.** A roadmap increment is not authorized:
  first it becomes a `CHG`.
- **Piling up the plans of past cycles.** It is living and replaced: the history lives in
  the `CHG` and the `REL`. If you keep twelve plans, you have twelve that look current.
