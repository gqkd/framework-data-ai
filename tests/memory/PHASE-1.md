# Product Memory phase 1: shared parser and scoped resolver

Implementation record, 2026-09-07 to 2026-09-08. Phase zero was saved separately in local commit
`82ab68f` before changing production code. The working branch remains
`codex/product-memory-phase-0`; no push or product migration is part of this phase.

## Delivered boundary

```text
validate.py (same CLI and import surface)
       |
       +-- artifacts.py: parsing, discovery, source sections
       |
       +-- references.py: identities, declarations, scoped joins
                    |
           CHG checks / PR checks / triage
```

| File | Change |
|---|---|
| `src/framework_data_ai/artifacts.py` | Extracts the existing Artifact, parsing helpers and discovery; adds exact section spans and source-line offsets |
| `src/framework_data_ai/references.py` | Shared declaration index, scoped candidate identities, explicit resolution outcomes, repository aliases and impact joins |
| `src/framework_data_ai/__init__.py` | Importable local package; no installation metadata or dependencies added |
| `skills/audit/scripts/validate.py` | Local bootstrap, compatibility aliases, shared reference inventory and the three repaired check paths |
| `tests/memory/test_references.py` | Scope, ambiguity, parsing, gate and Git-export tests |
| `tests/memory/test_phase0.py` | Removes three expected-failure markers; asserts the repaired outcomes and exact baseline delta |
| `tests/fixtures/memory/phase1-findings.yaml` | Expected additive differences, without changing historical observations |
| `tests/selfcheck.py` | Includes extracted modules when checking emitted diagnostics; runs the whole memory suite |
| `tests/memory/README.md`, this report | Current usage, limits, measured results and handoff |
| `README.md` | Adds the shared core and acceptance suite to the repository map |

No schemas, templates, product documents, accepted decisions, model prompts or provider
installations were changed. No framework release is declared: the combined increment's
versioning and distribution remain a later phase, not an implicit adoption of this branch.

## Identity and ambiguity

An internal identity contains the logical documentation-repository ID, owning scope and
local artifact ID/path. Physical checkout paths are not identities. The legacy CLI uses
the local single-repository default; a caller composing repositories must supply distinct
logical `document_repository` IDs.

Ownership comes from the containing product manifest/directory, not from a document's
`products:` binding. A shared root decision can bind two products without becoming owned
by either. The substrate has `platform` scope, not a fictitious platform product.

Local ICG rows and qualified CHG references normalize to the same candidate only in the
same scope. Roadmap candidates also retain their owning scope despite not requiring a
written qualifier. Unknown products, missing declarations, wrong types, invalid references,
out-of-scope references and ambiguous declarations have explicit outcomes. An ambiguous
lookup never exposes a single target. Historical aliases are not inferred from numbers.

`normalize_candidate` normalizes a row/reference; it is **not** evidence that a declaration
exists. `resolve` checks declarations; `artifact` resolves standalone artifact IDs;
`repository` resolves existing `product.*`/`platform.*` aliases without opening code.
Syntax and local-prefix rules are read from the current artifact registry.

The repository-alias API is implemented and tested, but the existing `VER*` checks have
not been rewritten to use it. This phase does not claim that every validator check has
been migrated to the new resolution API.

## Restored behavior

| Case | Result now |
|---|---|
| Qualified candidate with architecture impact, no DEC | `CHG002` is emitted |
| Same candidate in a PR with no ARC update | `PR004` is emitted |
| Qualified AI impact marked verified without EVR | `CHG001` is emitted |
| Only one product's homonymous signal is triaged | `ICG001` remains for the other product |
| Candidate matches only a different scope | `CHG003` reports the unresolvable join; no impact is borrowed |
| Duplicate ICG ID | The join is ambiguous and cannot silently choose a classification |
| Duplicate CHG ID cited by a PR | `PR002` reports ambiguity instead of choosing an authorization |

Diagnostic severities and gate status policies are unchanged. In particular, triage still
counts the statuses it counted before; this is not the future strict approval profile.
The new resolver does not approve classifications, modify immutable decisions or implement
signals. An incomplete join is reported even when another known obligation can be checked.

## Compatibility and deliberately retained limits

- Existing CLI options and exit-code semantics remain. Moved functions/classes remain
  available as aliases when importing `validate.py` directly.
- Each validator bootstraps the core from its own framework root under an isolated module
  namespace. A prior import or an editable install cannot silently supply another checkout's
  implementation. The package also supports normal direct imports from `src/`.
- Parsing and discovery retain their old scan exclusions and body-ID declaration policy.
  A register's cited IDs of its own declared prefix are still the bounded legacy ambiguity;
  this phase does not reinterpret prose as a stricter declaration format.
- `locate_sections` handles ATX headings, explicit markers and fenced code blocks. It
  returns all occurrences, including duplicates, with inclusive one-based source lines.
  Setext headings and a full CommonMark AST are not supported. The existing marker-presence
  validator check has not changed. A later context builder must not pretend these spans
  provide complete structural understanding of arbitrary Markdown.
- No graph/output schema, canonical snapshot serialization, context-budget policy, search
  engine, model evaluation or code provider exists as a result of this phase.

## Verification record

Local runtime: WSL Ubuntu 26.04, Python 3.14.4, PyYAML 6.0.3 and jsonschema 4.19.2, unchanged
from phase zero. CI's configured Python 3.12 and remote CI have not been run locally.

```bash
python3 -B -m unittest discover -s tests/memory -v
python3 -B tests/selfcheck.py
python3 -B schemas/generate.py --check
git diff --check
```

- Memory suite: 49 tests pass, zero expected failures, skips or unexpected failures.
- Full selfcheck passed at first integration and on the final rerun, which executed all
  49 memory tests with no expected failures.
- Schema generation check: 30 schemas and 4 catalog tables remain current; no schema delta.
- Compatibility tests create a temporary Git repository from the new source, commit and
  export it, then run the exported validator and migrator from outside that tree. They
  also import the live and exported validators together and verify each class's origin.
- The migrator no-op remains read-only. Its no-op result is not evidence of compatibility
  with a future schema migration. Existing migration/history checks remain in selfcheck.
- A direct comparison against the phase-zero commit covered 23 generated/static fixture
  roots using `--json --stale-days 36500`. Only two audit reports changed: the qualified
  candidate gained `CHG002`, and the product-collision fixture gained `ICG001`. No finding
  was removed and no unrelated check changed. PR context is tested separately by the suite.
- The shipped PR workflow was inspected: it checks out the whole framework repository,
  so it also brings `src/`. No workflow edit or dependency installation is needed here.

The phase-zero sources, comprehension questions and expected answers remain unchanged.
The finding delta is recorded separately. No behavioural runs with a model are claimed.

## Handoff

Phase 2 can reuse these APIs to define optional metadata and the documentary graph. It
must still supply logical repository IDs, preserve source provenance, distinguish missing
evidence from a negative result, and validate its own output contract. It must not add an
independent parser or normalize candidates by stripping their product qualifier.

Do not silently broaden this phase into approval policy, code-provider integration or
product migration. Those remain separate reviewable units of the implementation plan.
