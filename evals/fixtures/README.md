# Fixtures

Repositories to run the evals against. `python evals/fixtures/make.py` builds them into
`build/`, which is not tracked.

## Why generators and not the fixtures themselves

Three times in the work that produced these, a fixture was edited by hand and the edit was
gone at the next run of whatever built it, because most of them start with `shutil.rmtree`.
`generators/` is the source and `build/` is its output.

The release fixtures are the reason this cannot simply be a directory of files. Each is a
real git repository with three commits, and `D-tampered-plan` turns on that history: the
frozen evaluation plan is only recoverable through
`git show <frozen_at>:products/atlas/EVP.md`, which is exactly what the gate is
supposed to do when the hash it was handed does not match the plan in front of it.
Committing a git repository inside a git repository stores a gitlink, not the history, so
the one thing that fixture exists to test would be the thing that did not survive being
checked in.

`static/` holds the three with no generator and no history: two open registers and a
project with a corpus and no framework in it.

## What each one is for

| | |
|---|---|
| `audit/dirty-repo` | Real defects: front matter that does not parse, a `derives_from` pointing at a decision nobody wrote, a decision superseded by one that never moved it to `superseded`, a product with no open register of its own, an open entry carrying a date where its trigger belongs, one at the root that does not say which products it binds, a decision that does not say what it leaves open, a data contract citing a glossary term nobody defined, and a commitment recorded as delivered on a product with no risk register. Four errors and nineteen warnings, by construction. |
| `audit/clean-repo` | Nothing wrong with it. A checker that reports something here is inventing. It is also the smallest correct example of the register layout: the entries in `products/atlas/OPEN.md`, and a root register holding the parking lot and the union region. |
| `cycle/fixture-base` | Ten signals, a roadmap, and the previous cycle's `ICG`. Two of its routings are traps: one `not-classifiable` that must come back, one `not-a-candidate` that must not be re-triaged. Six signals are in no `ICG` at all. |
| `release/A` … `F` | Six release candidates differing only in the evidence they carry. Four block, each for its own reason; `A` ships with a non-blocking metric over its ceiling, and `F` ships with three rows exactly on their threshold. |
| `requirement/seed` | A documented product, so a statement has somewhere to be filed and something to contradict. |
| `resolve/ordering-a` | Nine open decisions. Two are filed under a heading that contradicts the cost they declare, one depends on an entry that exists nowhere, one is missing `Default in force` entirely. Two of its planted defects went unreported by anything until `REG005` existed: the entry with no `Default in force` at all, and the one depending on an entry nowhere in the register. Both are described in this row and neither was ever a finding. |
| `resolve/ordering-b` | The same register, entries permuted inside their sections, derived rather than stored so the two cannot drift. The order produced must match `ordering-a`, and when it does not, the ranking is coming from the sequence of the file. |
| `resolve/coldstart` | Almost nothing written, because almost everything is blocked on a decision nobody took. |
| `platform` | Three products on one substrate and a change that reaches all of them: a signed commitment promising an identifier to customers, another promising to pseudonymise it, three architectures joining on it, and a risk accepted on the grounds that it stays what it is. Eleven documents, three owners. The only fixture here where "propose a diff and wait" produces something too long to read. It is also the only one carrying the full register layout: `platform/OPEN.md` for the two substrate decisions, one register per product for what is only theirs, and a root holding the parking lot and the generated union. |
| `start/corpus-project` | Business documents and no framework, the only state `start` is written for. Three of the seven give nothing back: an empty scanned PDF, a `.docx` that is not a zip archive, and a file of whitespace. They need three different things done about them, so a run that reports a count has not helped. |

## A fixture that cannot fail is not a fixture

Two of these were built wrong and the runs found it, which is worth recording because both
were wrong in the direction that scores well.

`ordering-a` and `ordering-b` were byte identical. The stability question they exist to ask
could not have failed however the skill behaved.

Every release fixture blocked, including the one named `clean-pass-boundary`, so a gate that
refused everything scored six out of six. `F` was built for that, and then `A` turned out to
be a pass too, on a reading of the plan the rule had not accounted for.
