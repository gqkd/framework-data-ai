---
schema: framework/release-note/v1
artifact_type: release-note
lifecycle: immutable
status: active
id: REL-NNN
products: [product-a]
owners: [NAME]
created: YYYY-MM-DD
derives_from: [CHG-NNN, EVR-NNN]
classification: internal
---

# REL-NNN · Release note

**Question:** what changed, for whom, and how do you go back?

**For a person. Ten lines.** The machine-readable version is `RLM-NNN.yaml`: they are two
documents because they have two readers, not out of redundancy.

## What changes

From the point of view of whoever uses the system. Not the commits: the effects.

## Changes included

`CHG-NNN` · `DEC-NNN`

## Risks and rollback

What could go wrong and how you go back. The exact rollback target is in `RLM`.

## What to monitor in the first 48 hours

Metrics specific to this release, not the routine ones.

---

## Anti-patterns

- **Listing the commits.** The reader does not know what a commit is and has no use for
  one.
- **Leaving it out because "it's a small change".** It is the glue between the IDs and
  reality: the point where a traced decision becomes something running in production on a
  precise date.
- **Duplicating `RLM`.** If this note contains hashes, it is not for humans.
