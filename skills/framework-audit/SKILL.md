---
name: framework-audit
description: >
  Check a Data & AI framework repository against its own rules: run the validator,
  interpret what it found, and fix what is safe to fix. Use when asked to audit, check or
  validate the documentation, when asked whether the docs are consistent or whether
  something is out of date, when the framework check is failing in CI, before merging a
  change to the artifacts, or when asked to regenerate `decisions/INDEX.md` or
  `TRACEABILITY.md`.
---

# framework-audit

The validator is a script, and it runs the same way here and in CI: one implementation,
two entry points. What this skill adds is not more checking, it is the judgment about what
to do with the findings, and above all about what **not** to do with them.

That distinction is the whole point. Almost every finding has a cheap way to make it
disappear that leaves the repository worse than it was.

## Running it

```bash
python <framework>/skills/framework-audit/scripts/validate.py --root <project> --json
```

`--root` is the project being checked, not the framework. `--json` when you are going to
process the output, plain when a person is going to read it. Two more flags matter:

- `--emit-index` regenerates `decisions/INDEX.md` and `TRACEABILITY.md`
- `--list-checks` prints the catalog with the severity in force

If `--root` is not obvious, ask. Running it against the wrong directory produces a clean
report, and a clean report on the wrong repository is worse than an error.

## The rule that outranks everything else here

> **Never update `last_review` without having read the document.**

It is the fastest way to turn the validator green and the only one that makes the whole
framework useless. `last_review` is not a field about the file, it is a claim that a person
looked at the document and found it still true. Writing today's date into it without that
having happened converts every downstream reader, human and agent, into someone acting on a
document nobody has checked, while the staleness warning that would have told them is gone.

If `LC002` fires, the work is to read the document. If you are not going to read it, leave
the warning standing: it is doing its job.

## Fix directly, or propose

Apply without asking only what is mechanical and cannot be wrong:

- **`--emit-index` output.** Generated files, regenerate them.
- **A missing `<!-- section: id -->` marker** when the section itself is plainly there
  under a heading and only the marker is absent.

Propose a diff and wait for everything else. In particular:

- **`FM002`** says the front matter contradicts the type. Two repairs exist and they are
  opposites: change the declaration, or change the document to match it. An `immutable`
  declared `living` might be a typo in the front matter, or it might be a document somebody
  has been editing in place for months. Find out which before touching it.
- **`REF001` / `REF002`**, a reference to something that does not exist. Deleting the
  reference silences the check and destroys the only surviving trace that the thing was
  supposed to exist. Look for what it pointed at, including in git history. If it never
  existed, say so in prose in the document rather than removing the line.
- **`OD002`**, an entry decided but still listed as open. The repair is a move, not a
  delete: the entry leaves `§1` and leaves a cross reference line in `§4` of `OPEN.md`. An
  entry deleted outright takes with it the fact that the question was ever asked.
- **Anything at all on an `immutable`.** The class means what it says. If the content is
  wrong, the repair is a new document with `supersedes`, and the old one moves to
  `status: superseded`. The `status` field is the only one you may touch in place.

## What you must never do

- **Fill in a field with a plausible value.** `verified_against`, `evp_hash`,
  `evp_version` are facts about the world: a commit that exists, a file that was hashed. If
  you cannot establish the real value, the finding stays open and you say so. An invented
  hash passes the validator and turns an evidence document into a decoration.
- **Lower a severity to clear a finding.** `framework.yaml` records a decision that a check
  does not apply to this project, which is a legitimate thing to conclude: `XP003: off` in
  a repository with one product is correct. Switching off a check that *does* apply, in
  order to go green, is not a configuration change, it is a deletion of the finding. If you
  are tempted, propose it out loud with the reason and let a person decide.
- **Add a section marker without the section.** `SEC001` on a `CHG` usually means the
  document is genuinely missing "what must NOT change", which is the most expensive gap in
  the framework: an agent optimises what it was asked for and breaks what nobody named. The
  repair is to write the section, and only a person knows what belongs in it.

## Reading the report

Order the findings by what they cost, not by the order they were printed. A useful
sequence:

1. `error` level: they block the merge.
2. Anything on a **living** document, because it is being read as current truth right now.
3. Anything that breaks a **chain**: `REF*`, `ID001`. A traceability graph with holes reads
   as an absent one.
4. The rest.

When you report back, say which findings you fixed, which you are proposing, and which you
are deliberately leaving. **A finding left standing on purpose, with the reason, is a good
outcome.** A report that says everything is green after ten minutes of work usually means
something was silenced.

## Turning a check on

The framework's rule is to add a check when the failure it prevents has already happened
once, and not before. When that happens, the change is one line in the project's
`framework.yaml`:

```yaml
checks:
  LC002: error
```

`skills/framework-audit/checks.yaml` is the catalog: every check carries the failure it
prevents, which is what you read to decide. Two checks are `off` and cannot simply be
switched on, and the catalog says why in `blocked_by`.
