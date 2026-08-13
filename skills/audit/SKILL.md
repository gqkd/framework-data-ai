---
name: audit
description: >
  Check a Data & AI framework repository against its own rules: run the validator,
  interpret what it found, and fix what is safe to fix. When asked whether the documents
  agree with each other, it goes a step further and reads both ends of the pairs that have
  to say the same thing, which no script can decide. Use when asked to audit, check or
  validate the documentation, when asked whether the docs are consistent, whether they
  contradict each other, or whether something is out of date, when the framework check is
  failing in CI, before merging a change to the artifacts, or when asked to regenerate
  `decisions/INDEX.md` or `TRACEABILITY.md`. Triggers on "è tutto a posto", "controlla i
  documenti", "i documenti sono coerenti", "controlla la coerenza", "verifica che i
  documenti non si contraddicano", "fai un audit della documentazione", "il check in CI è
  rosso", "check the docs", "are the docs consistent", "do these documents contradict each
  other", "audit the documentation", "the framework check is failing".
---

# audit

The validator is a script, and it runs the same way here and in CI: one implementation,
two entry points. What this skill adds is not more checking, it is the judgment about what
to do with the findings, and above all about what **not** to do with them.

That distinction is the whole point. Almost every finding has a cheap way to make it
disappear that leaves the repository worse than it was.

## Running it

```bash
python3 "${CLAUDE_PLUGIN_ROOT:?unset: point it at your framework-data-ai checkout}/skills/audit/scripts/validate.py" --root <project> --json
```

`python3`, not `python`: the script's shebang already says `python3`, and on most systems
`python` alone is not on PATH at all. `${CLAUDE_PLUGIN_ROOT}` is set for you when this runs
as an installed plugin and unset when you are working inside a checkout of the framework
itself, which is exactly where the skill gets tested. The `:?` is what makes that second
case say so. Without it the path collapses to `/skills/audit/scripts/validate.py` and the
shell reports `command not found`, which names neither of the two things that went wrong.

`--root` is the project being checked, not the framework. `--json` when you are going to
process the output, plain when a person is going to read it. Two more flags matter:

- `--emit-index` regenerates `decisions/INDEX.md`, `TRACEABILITY.md`, each
  `products/<p>/product.index.yaml`, and the `§5` region inside the root `OPEN.md`
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

One test, and it is the same one `references/routing-table.md` §5 applies everywhere else:

> **Apply it when the repository already contains the correct value. Propose it when
> supplying the value means knowing something the repository does not say.**

That is decidable by reading, which a list of examples is not. Three things pass it:

- **A missing `<!-- section: id -->` marker** when the section is plainly there under a
  heading and only the marker is absent.
- **A field contradicted by another field in the same front matter.**
  `artifact_type: architecture-doc` next to `schema: framework/architecture/v1` is a typo
  and the schema line says what it should have been. You are not choosing a value, you are
  copying one.
- **A `status` on an immutable that another document has already settled.** If a `DEC`
  declares `supersedes: DEC-001`, then `DEC-001` is superseded and saying so is
  transcription. `status` is the only field on an immutable this can ever apply to.

Everything else is proposed, and the boundary is worth being exact about because it is
where runs of this skill diverge. Excluding a dbt directory from `scan` is a real repair
and the framework says so, but nothing in the repository states that `models/` is not the
framework's: that fact lives in somebody's head, and a repair that needs a fact from
outside is a proposal however obvious it looks from inside. Same for `FM002` where the
front matter and the document disagree and neither is a copy of the other.

Propose a diff and wait for everything else. In particular:

- **`--emit-index`.** It looks like the safest thing here and it is the most destructive.
  It overwrites `decisions/INDEX.md` and `TRACEABILITY.md` wholesale, it does not merge,
  and it can only write what front matter can express. A project that added a column for
  why each decision still matters, or rows for where a source system enters the chain,
  loses exactly that. Run `--emit-index --check` first and show what would change. The
  validator now refuses to overwrite either file when it does not carry the
  `Generated by` line, so the accident is caught, but the refusal is a backstop and not a
  substitute for looking.

  The `§5` region of the root `OPEN.md` is the one exception and it is safe by
  construction: it rewrites only what sits between `<!-- generated: open-union -->` and
  `<!-- /generated -->`, the prose around it is untouched, and a register carrying no
  markers is not written to at all. Say so when you show the diff, because the file it
  edits is the one nobody expects a generator to open.

- **`FM001` on a file that is not an artifact at all**, a dbt model, a Helm values file, a
  `CONTRIBUTING.md`. This is a real repair and not a silencing: the validator was reading a
  file the framework has no claim over. It goes in `scan.skip_dirs` or `scan.skip_files` in
  the project's `framework.yaml`. Name the directory or the file, never a parent that also
  holds artefacts.
- **`FM002`** says the front matter contradicts the type. Two repairs exist and they are
  opposites: change the declaration, or change the document to match it. An `immutable`
  declared `living` might be a typo in the front matter, or it might be a document somebody
  has been editing in place for months. Find out which before touching it.
- **`FM004`**, a field still holding the template's placeholder. Almost always a scaffold
  that was never finished, and almost never something you can fill by reading: `owners`
  is the one field in the front matter that commits a person other than you, and the
  preamble is explicit that it is asked and never deduced — not from the git config, not
  from the last document that named somebody. `created` is a fact about when, and
  `derives_from: [PRB-NNN]` is either a document to write or a line to delete. Ask, or
  propose the deletion. Filling these from what is lying around is how the finding
  disappears and the fiction stays.
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

- **Fill in a field with a plausible value.** `verified_code`, `evp_hash`,
  `evp_version` are facts about the world: a commit that exists, a file that was hashed. If
  you cannot establish the real value, the finding stays open and you say so. An invented
  hash passes the validator and turns an evidence document into a decoration.
- **Lower a severity to clear a finding.** `framework.yaml` records a decision that a check
  does not apply to this project, which is a legitimate thing to conclude: `XP003: off` in
  a repository with one product is correct. Switching off a check that *does* apply, in
  order to go green, is not a configuration change, it is a deletion of the finding. If you
  are tempted, propose it out loud with the reason and let a person decide.
- **Widen `scan` to clear a finding.** It is lowering a severity, one level further out:
  the document stops being reported because it stopped being looked at, and unlike a
  severity there is no record in the report that anything was excluded. Adding `notebooks/`
  is configuration. Adding `products/` is the deletion of every finding inside it.
- **Add a section marker without the section.** `SEC001` on a `CHG` usually means the
  document is genuinely missing "what must NOT change", which is the most expensive gap in
  the framework: an agent optimises what it was asked for and breaks what nobody named. The
  repair is to write the section, and only a person knows what belongs in it.

## The second pass: do the documents still agree with each other

Everything above is the validator and what to do with what it says. The validator checks
that **the link exists**: that `derives_from` points at something, that the `DEC` is there,
that the section is there, that the `status` is in its enumeration. It cannot check that
**the two ends say the same thing**, and that is a different question with a different
failure: a `DEC` that decided Postgres and an `ARC#current` that still describes the queue
it replaced both validate, are both linked correctly, and contradict each other.

This pass is that question. **Run it when asked, not on every invocation.** It costs a read
of the artifact set, and a skill that costs more than it saves gets switched off, which is
the framework's own rule about itself. But when it has not run, **say so** — a clean
validator report read as "the documents agree" is exactly the silence this pass exists to
remove.

### Do not invent the checklist

The pairs are already written down: `references/routing-table.md §2` is the cascade, and
this pass is that table **read backwards**. Where the cascade says *if you write A you must
also update B*, this asks *does B still reflect A*. One source, not two, and the same reason
as everywhere else here: a second list drifts from the first and nobody notices.

Enumerate from what is generated, not from what you remember reading. `decisions/INDEX.md`
carries every `DEC` with its scope, status and products; `products/<p>/product.index.yaml`
carries that product's living artifacts and open entries. Run `--emit-index --check` first:
if the indices are stale, the enumeration you are about to build from them is stale too.

| These have to agree | The question |
|---|---|
| accepted `DEC scope: architecture` → `ARC#current` | does the architecture describe what the decision decided, and did `#target` move with it |
| accepted `DEC scope: product` → `PBR` | does the brief carry the capability, the scope or the outcome the decision changed |
| accepted `DEC scope: platform` → `PLATFORM.md`, and `products:` | does the substrate document reflect it, and does the decision list **every** product |
| `GLOSSARY` term that is also a field of a `DC` → that `DC` | the same definition on both sides, and did the contract's version bump |
| a `GLOSSARY` metric used by more than one product → each product | does each compute it with that formula. If they cannot, they are two metrics and need two names |
| `CMT` out of technical reach → `RSK#state` **and** `OPEN.md` | is the row there, and the entry |
| a numeric promise in `COMMITMENTS` → an `EVP` threshold | the two must not come apart: a promise with no threshold is unmeasured, a threshold with no promise is unowned |
| `ARC#delta` → `#current` and `#target` | is the delta still the difference between them. A stale delta is a silent lie |
| `WF#delta` → `#current` and `#target` | the same |
| a `PBR` capability that depends on another product → an internal `DC` | does the contact point have a contract |
| `OPEN.md` open entries → the accepted `DEC` set | is a question still listed as open that a decision already answers. `OD002` catches this only when the `DEC` names the entry in `derives_from`, which is the minority of the cases: the rest are here |
| each register → the product whose directory it sits in | is every entry actually about that product. `OD008` catches the ones that declare another product; the ones that declare nothing and are still misfiled are here, and they are the common shape — an entry written while working on one product and filed where the session happened to be |

### The three rules of this pass

**It proposes, it never applies.** A structural finding can sometimes be repaired by
transcription. A disagreement never can: both ends may be right, and which one holds is the
question. `ARC#current` may be stale, or the `DEC` may have been superseded by a
conversation nobody wrote down, and those want opposite repairs. Show both, with their
provenance, and ask — the same move `references/routing-table.md §4` prescribes for a
conflict found while writing.

**Say what agreed.** Every pair examined is reported, including the ones that were fine.
This pass exists because an absence of findings was indistinguishable from an absence of
looking, and reporting only the disagreements rebuilds that hole one level up.

**Say what you could not check.** A pair whose second end does not exist yet — a `CMT` with
no `EVP` to hold its threshold, a delta with no target — is not agreement, it is a pair you
could not read. Name it. A capability whose truth lives in the code and not in a document is
the same case: this pass reads documents, and where the answer is in a repository it says
which repository and stops.

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

And say whether the second pass ran. A clean validator means the structure holds: the links
resolve, the fields are legal, nothing is stale by date. It does not mean the documents agree
with each other, and handing back "nothing to report" without that sentence lets it be read
as though it did.

**Then the two closing blocks the preamble describes, and they go last:** what changed in
plain words, one line per file, and what to do next with what each option buys and costs. The
rows come from the findings you did not fix, one per finding worth acting on, with the cost of
leaving it standing stated rather than implied — and if the second pass has not run, that is a
row of its own.

## Turning a check on

The framework's rule is to add a check when the failure it prevents has already happened
once, and not before. When that happens, the change is one line in the project's
`framework.yaml`:

```yaml
checks:
  LC002: error
```

`skills/audit/checks.yaml` is the catalog: every check carries the failure it
prevents, which is what you read to decide. A check sitting at `off` there is one the
validator cannot run yet, and it carries `blocked_by` saying what has to exist first — so
read that before proposing to switch one on. None is `off` today.
