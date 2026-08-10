# Common preamble

Every skill in this plugin reads this first. It exists as one file because the alternative
is the same two hundred words copied six times, which is the duplication the framework
forbids, committed by the framework against itself.

## Before writing anything

Read, in this order:

1. **`AGENTS.md`** at the project root. It is the control plane: the table of authoritative
   sources, the non negotiable rules, and the project's real commands.
2. **`OPEN.md`**. If a choice you need is listed there as open, you do not take it. You
   raise it. This is the rule that stops an agent from inventing a decision and then
   implementing it with conviction.
3. **`products/<p>/product.yaml`** for the product you are working on, if the task names one.

If the project has no `AGENTS.md`, it has not been set up: run the `start` skill instead of
guessing a structure.

## The rules that outrank the task

**One authoritative source per fact.** When you are about to write something that already
exists somewhere else, write a link instead of a copy. Two copies diverge, and then nobody
knows which to believe.

**Respect the class.** It is declared in the front matter and it decides what you may do:

| Class | What you may do |
|---|---|
| `living` | edit in place, and set `last_review` to the current instant |
| `immutable` | never edit the body. Create a new document with `supersedes`, move the old one to `status: superseded`. The `status` field is the one exception and moves in place |
| `append-only` | never rewrite a line. Add a linked event |

**Do not implement a signal.** A `LOG` line, a piece of feedback or an `RMP` increment is
not an authorization to build. What gets implemented is a `CHG` with `status: approved`.

**Absence is information.** If a fact is not documented, say so. An agent that fills a gap
with a plausible assumption does more damage than one that stops, because the assumption is
indistinguishable from a fact to whoever reads it next.

**Never invent a field that attests something.** `verified_against`, `evp_hash`,
`evp_version` are claims about the world: a commit that exists, a file that was hashed. If
you cannot establish the real value, leave it and say so. An invented hash turns an
evidence document into a decoration and passes every check.

**Never write today's date into `last_review` without having read the document.** It is the
fastest way to make a validator green and the only one that makes the whole framework
useless.

## How to propose a write

Show what changes before you change it, and keep it short. A wall of generated document is
not reviewable, so nobody reviews it, and the approval becomes a formality.

**First**, a compact table. Never the document:

| File | What changes |
|---|---|
| `decisions/DEC-012-postgres.md` | new · datastore chosen, closes OD-003 |
| `products/alpha/ARC.md` | §current · store component added |
| `OPEN.md` | OD-003 moves from §1 to §4 |

**Then**, once the user agrees and you have written, print the document, or the section of
it that changed when the file is long.

Two things you apply without asking, because they destroy nothing and asking would only
make them annoying: appending a `SIG` to `LOG`, and adding an entry to the parking lot of
`OPEN.md`. Everything else is proposed. The project's `AGENTS.md` says when the second one
applies even though nobody asked you to write anything, and it says it there rather than
here because that rule has to reach an agent answering a question with no skill running,
which never reaches this file.

## Closing move

Any skill that wrote something ends by running the validator, and reports what it says:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:?unset: point it at your framework-data-ai checkout}/skills/audit/scripts/validate.py" --root <project>
```

`python3` and the `:?` are both load bearing: `python` is not on PATH on most systems, and
an unset `CLAUDE_PLUGIN_ROOT` collapses the path to `/skills/...` and fails with a message
that names neither problem. The `audit` skill explains this once, in full.

This is not ceremony. The cascade is where a write goes wrong, and the validator is what
notices that a `DEC` moved and its `ARC` did not. If it reports something you caused, fix
it before handing back. If it reports something that was already there, say so and leave
it: it is not yours to silence.
