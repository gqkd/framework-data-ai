---
schema: framework/change-contract/v1
artifact_type: change-contract
lifecycle: immutable
status: draft
id: CHG-NNN
products: [product-a]
owners: [NAME]
approvers: [NAME]
created: YYYY-MM-DD HH:MM
icg: ICG-NNN
derives_from: [SIG-NNN, INC-NNN, DEC-NNN]
verified_by: null               # the EVR, once there is one. Empty until `status: verified`
classification: internal
---

# CHG-NNN · Change title

**Question:** which change is authorized, within which boundaries, and how will we know it
worked?

`status`: `draft | approved | implemented | verified | rolled-back`

**Why it exists.** An agent must not implement a `LOG` line, a piece of feedback, a request
or an `RMP` increment: those are signals, not authorizations. It must implement a `CHG` with
`status: approved`. This document is what turns a signal into a mandate with boundaries.

---

## The three mandatory fields

Everything else is optional. These three are not: they are the document.

<!-- section: what-changes -->
### 1 · What changes

The observable behavior after the change. Not the files to modify: the effect.

<!-- section: what-must-not-change -->
### 2 · What must NOT change

The boundaries. Existing behaviors that must stay identical, components not to be touched,
contracts not to be broken.

This is the field that makes the document useful to an agent: without it, an agent will
optimize point 1 at the expense of things nobody told it to preserve.

<!-- section: how-we-know-it-worked -->
### 3 · How we know it worked

Verifiable acceptance criteria. A test, a metric with a threshold, an `EVR` that passes. If
it is not verifiable, it is not a criterion: it is a hope.

---

## Optional fields: fill in only the relevant ones

| Field | When it is needed |
|---|---|
| **Trigger** | always useful: which `SIG` or `INC` originates it |
| **Artifacts to update** | explicit list, checked by the validator |
| **Rollout** | if it is not an ordinary release |
| **Rollback** | if the standard rollback is not enough |

**The routing and the impacts are not fields here.** They live in the `ICG` named by the
`icg` field above, keyed by the candidate this change derives from, because that is where
they were decided and a fact belongs to one document. Restating them here is how the two
come to disagree, and the one that would be believed is this one, which is the copy. To
read them: `icg` → `routing[candidate]` and `icg` → `impacts[candidate]`.

What each impact obliges you to do is unchanged: `architecture` wants an updated `ARC` and
a `DEC`, `data` a `DC` version bump and notice to its consumers, `ai` a new `EVR`, and
`risk-compliance` a line in `RSK §state`.

## Verification

*Filled in at closure.* Outcome of the point 3 criteria, the `EVR` of reference, the `RLM`
of the release that contains it.

---

## Anti-patterns

- **A `CHG` without field 2.** It is the most expensive defect: an agent optimizes what you
  ask for and breaks what you did not name.
- **Acceptance criteria that cannot be verified.** "It works better" is not a criterion.
- **Turning it into an eighteen-section form.** With a single approver who is also the
  requester, an elaborate approval process is theater. Three fields filled in well are worth
  more than eighteen filled in out of duty.
- **Implementing while in `status: draft`.** If this happens systematically, the `status`
  field is doing nothing and you may as well delete it. But then you lose the boundary
  between idea and mandate.
- **One `CHG` per commit.** Record units of change with an outcome, not activity.
