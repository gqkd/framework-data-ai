# Documentation framework for Data & AI projects

It defines **which documents exist in a Data/AI project, who creates them, when, and which
question each one answers**. It has two audiences: a new person who has to understand the
system well enough to change it without breaking decisions taken for good reasons, and an
AI agent that has to answer questions without inventing the missing parts.

This repository holds **the definition only**. The artifacts of a real project, its
decisions, products, initiatives and corpus, live in that project's repository, not here.

| File | What it is |
|---|---|
| **`FRAMEWORK.md`** | The reference document. Start here |
| `framework-flow.mermaid` | The lifecycle with its gates. Importable into draw.io: *Arrange → Insert → Advanced → Mermaid* |
| `Framework.drawio` | An older drawing of the same lifecycle, kept for editing in draw.io |
| `SKILLS.md` | The five skills that operate the framework. None is built yet |
| `templates/` | One template per artifact, each with its anti-patterns at the bottom |

## Reading order

**To understand the framework:** `FRAMEWORK.md` → `framework-flow.mermaid` →
`templates/README.md`

**To start using it:** `FRAMEWORK.md §10`, the entry assessment and the day one set

**To automate it:** `SKILLS.md`

## Applying it to a project

The framework is not copied into the project. Keep it cloned next to it and refer to it by
path:

```
~/projects/framework-data-ai      the definition
~/projects/my-project             the artifacts
```

Nothing here needs installing today, because there is nothing here to run. See the next
section for why.

## There is no tooling yet

Two skills used to live here, `framework-capture` and `framework-audit`, the second of
which carried the validator that acted as the merge gate. Both have been removed, together
with their scripts and the test suite, because they are being rebuilt from scratch.

What this costs, stated plainly rather than discovered later:

- **No gate.** Nothing checks front matter, artifact ids, dangling references, staleness of
  living documents, or the discipline rules. Every one of those is currently enforced by
  attention alone.
- **No generated indices.** `decisions/INDEX.md` and `TRACEABILITY.md` were generated from
  front matter. Until the validator exists again they are written by hand, which means they
  will be wrong, which is worse than absent because a generated file is one nobody rereads.
- **No corpus extraction.** Turning presentations and PDFs into sourced claims is manual.

`SKILLS.md` describes what the five skills should do and in which order to build them. It
is the starting point for the rebuild, and every design detail in it survived the deletion
on purpose.

## Provenance

Extracted on 2026-08-06 from a repository where it was mixed with its first instance. The
history stayed with that instance, which holds nearly all of its content; here it starts
from a snapshot.

**One thing to know:** several documents refer to `OD-NNN` entries, `OD-002` in
`FRAMEWORK.md §9` and `SKILLS.md §7`, `OD-005` in `SKILLS.md §2`. Those live in that
project's open register and cannot be resolved here. Read them as "an open
decision of that kind", not as links to a file in this repository.

Otherwise the text is neutral: product names and decision slugs in the examples are
placeholders. A second project can adopt it as it stands.

## License

[Apache License 2.0](LICENSE). Permissive: you can use it, change it and redistribute it,
including commercially. The clause that matters for a documentation framework is §4.b. If
you redistribute a modified version you must state that you changed it, because anyone
reading a set of rules needs to know whether they are reading these or a variant.

## In one line

Seven living documents that have to be true, about twenty that are written once and never
touched again, and one file, `OPEN.md`, that says what has not been decided yet, because
that is the information no other document holds and the one an agent will otherwise invent.
