---
schema: framework/agents-control-plane/v1
artifact_type: agents-control-plane
lifecycle: living
status: active
owners: [NAME]
created: YYYY-MM-DD
last_review: YYYY-MM-DD HH:MM
classification: internal
---

# Instructions for agents

Read this file first. Then `OPEN.md`. Then the `product.yaml` of the product you are
working on.

## Authoritative sources

Each kind of question has exactly one source. Do not infer from elsewhere what is written
here.

| Question | Source |
|---|---|
| How the system is built | `products/<p>/ARC.md#current`, plus `PLATFORM.md` if there is one |
| What shape it is going to have | `products/<p>/ARC.md#target` |
| What is missing to get there | `products/<p>/ARC.md#delta`, ordered by `RMP.md` |
| Why it is built that way | `decisions/DEC-NNN.md` |
| What the product does and for whom | `products/<p>/PBR.md` |
| What a term or a metric means | `GLOSSARY.md` |
| What a piece of data guarantees | `products/<p>/contracts/DC-NNN.md` |
| How to operate it in production | `products/<p>/RB.md` |
| What was promised to a customer | `COMMITMENTS.md` |
| **What is NOT decided** | `OPEN.md` |
| What you are authorized to build right now | `products/<p>/changes/CHG-NNN.md` |

## Non negotiable rules

1. **Do not take decisions listed in `OPEN.md`.** If you need a choice that is listed
   there as open, stop and ask. Do not fill the gap with a plausible assumption: that is
   the main way an agent causes damage that is hard to trace back.
2. **Do not implement a signal.** A line in `LOG`, a piece of feedback or an increment in
   `RMP` does not authorize you to build. What you implement is a `CHG` with
   `status: approved`.
3. **Respect the artifact class.**
   - `immutable` → do not modify it; create a new one with `supersedes`
   - `append-only` → do not rewrite lines; add a linked event
   - `living` → modify it and update `last_review`
4. **If a fact is not documented, say so.** Absence is information. Prefer "it is not
   documented where this data lives" to an invented answer.

## Mandatory updates

After changing the code, update:

| What you touched | What to update |
|---|---|
| Architecture or dependencies | `ARC.md` **and** a new `DEC` |
| The schema or the meaning of a piece of data | the relevant `DC`, with a version bump |
| An AI component (model, prompt, retrieval) | a new `EVR` |
| A domain term or a metric | `GLOSSARY.md` |
| Anything you release | `REL` **and** `RLM` |
| A risk, or you introduced one | `RSK.md §state` |

## Definition of Done

Work is finished when: the `CHG` is `verified` · the artifacts in the table above are
updated · the project's validator passes with no errors.

## Commands

```bash
# TODO: fill in with the project's real commands
make dev
make test
```

> If this project has no validator yet, say so here rather than leaving the line out. An
> agent that finds no gate assumes there is nothing to pass, and an agent that finds a
> command that does not exist stops and asks. The second failure is the cheap one.

## Sensitive data

- Do not put real customer data in document examples or in committed evaluation datasets.
- PII fields are marked in the `DC` with `pii: true`. Do not copy them into logs, examples
  or fixtures.
- If a task requires access to production data, stop and ask.

## Escalation, stop and ask

The decision is listed in `OPEN.md` · no approved `CHG` covers the requested work · the
work would require modifying an `immutable` · an `EVP` threshold would have to be lowered
to clear the gate · a `DC` would be broken without warning its consumers.

---

## Anti-patterns

- **Filling the authoritative sources table with the same file twice.** Two rows pointing
  at the same document means the split is wrong, and an agent will read whichever it finds
  first.
- **Leaving the Commands section with the placeholders in it.** An agent runs what is
  written here. `make dev` on a project that has no Makefile teaches it that this file is
  decorative, and from then on it stops reading it.
- **Writing rules with no consequence attached.** "Respect the artifact class" alone is
  ignorable. What makes the rule hold is the sentence that says what breaks: an agent that
  reads a historical document as current truth takes wrong decisions with total confidence.
- **Adding rules until nobody reads them.** This file competes for attention with the task
  the agent was given. Four rules that are followed beat twelve that are skimmed.
