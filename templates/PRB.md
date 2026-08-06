---
schema: framework/problem-statement/v1
artifact_type: problem-statement
lifecycle: immutable
status: active
id: PRB-NNN
products: [product-a]
owners: [NAME]
created: YYYY-MM-DD
classification: internal
---

# PRB-NNN · Problem title

**Question:** which problem, whose, and what does it cost not to solve it?

**Note on the class:** immutable. The value of this document lies precisely in not being
updated: six months from now you will want to know what you believed at the start. If the
understanding changes, write a new `PRB` that supersedes this one.

## Who lives it

A concrete role, not "the users". How many people, in what context, how often.

## What they do today and what it costs them

The current behavior and its cost: time, errors, money, lost opportunities. With numbers if
there are any, with the explicit statement "not quantified" if there are none.

## How we measure it today

The existing metric, or the explicit sentence **"today we do not measure it"**, which is
information, not a gap in the document.

## What happens if we do nothing

The baseline scenario. If the answer is "nothing serious", the problem probably does not
deserve a project.

## §Boundaries

What this problem is **not**. Neighboring problems that someone will confuse with this one.

## Reverse discovery

*Fill this in only if the solution has already been promised commercially.* Which solution
was sold, and which problem we are trying after the fact to make it match. State it openly:
the honest documentation of a reverse discovery is worth more than a simulated forward
discovery. Cross-reference to `COMMITMENTS`.

---

## Anti-patterns

- **Already containing the solution.** If the title names a technology ("we need a
  dashboard", "we need a predictive model") it is not the statement of a problem but a
  solution in disguise, and from that moment on the whole discovery will work to confirm
  it.
- **"The users" as the subject.** If you cannot name a role, you have not yet understood
  who has the problem.
- **Zero quantification and zero admission of having none.** One of the two has to be
  there.
- **Updating it.** It is immutable. Updating it erases the traceability of how the
  understanding changed.
