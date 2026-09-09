# Product Memory phase 5: trusted contributions and exact execution evidence

Implementation record, 2026-09-09. Starts from `5031cb2` (completed phase four) on
`codex/product-memory-phase-0`. Only the framework and synthetic test histories are in
scope. No product/client files, historical decisions, real corpus, production data,
remote protections, provider installation, release version or project migration changed.

## What this phase adds

```text
trusted CI controller
  approved documentary tip + selected ancestor + clean framework pin
       |
       +--> approved CHG / accepted ICG / cited DEC / operational policy
       |      immutable meaning + specific artifact / path / repository obligations
       |
       +--> exact proposed documentary + code Git objects
       |      recomputed paths; required consumers included even when unchanged
       |
       +--> authenticated producer / run / artifact digest witnesses
              receipts: exact code set + mandate base + policy + command + result
                             |
                   strict-contribution JSON gate
                   findings + limitations + review still required
```

The phase-four context/impact reports still do not authorize implementation. The new
explicit profile checks independently supplied authority anchors instead of trusting an
approval introduced by the contribution itself. It cannot infer hosting identity or an
authenticated test execution from JSON or a local Git path; those are controller duties.

## Contracts and behavior

- A full documentary mandate commit must be available and ancestral to the controller's
  approved tip. There is no latest-main fallback. A changed documentary proposal must
  include that approved tip; revoked mandates cannot be revived with an older approval.
- Runtime source bytes, adopted pin/version and rule snapshots are checked independently
  of the proposed checkout. Proposed policy or severity changes do not authorize themselves.
- CHG and ICG come from the approved base; candidate identities use the existing scoped
  resolver. Architecture needs a cited accepted DEC. Whole normative bodies/metadata are
  protected, including prose outside the three mandatory CHG sections. Existing closure
  metadata may progress without rewriting the mandate; immutable history stays protected.
- A reviewed policy binds mandate paths to allowed path prefixes, specifically affected
  ARC/DC/RSK documents, required repository sets and mandatory tests. It does not copy the
  meaning of a CHG. An unrelated DC or a touched DC without a version increase cannot pass.
- Repositories and changed paths are read from immutable Git objects without checkout,
  source execution, graph generation or network access. Links/submodules, inaccessible
  inputs, incomplete bindings and unobserved co-located non-document files block.
- Receipts bind the exact code set (including required unchanged consumers), documentary
  mandate, canonical policy hash, command, producer, run and result. Integrity is checked
  against an independently authenticated CI witness. Optional fast-cycle selection cannot
  remove a mandatory test; missing, stale, duplicate, failed and unauthenticated evidence
  fail the gate.
- `no-chg` needs an independently authenticated reviewer from the approved policy, other
  than the contribution author, for the exact reason/base/head/code-set digest. Mandatory
  exception tests remain required. PR text is data and never shell-interpolated.
- Strict mode is an explicit opt-in. Legacy behavior and severity remain unchanged and
  visibly unauthenticated. No new field is required of existing project artifacts.

## Files and responsibilities

| File/group | Change |
|---|---|
| `src/framework_data_ai/git_snapshot.py` | Bounded immutable Git inventory, ancestry, paths and blob reads |
| `src/framework_data_ai/authority.py` | Trusted-base mandate/scope/obligation checks and JSON gate |
| `src/framework_data_ai/evidence.py` | Authenticated receipt consistency and mandatory-test union |
| `src/framework_data_ai/contribution_ci.py` | Optional GitHub documentary controller, independent of the offline core |
| `skills/audit/scripts/validate.py` | Explicit strict CLI dispatch before worktree loading; visible legacy status |
| `skills/audit/checks.yaml` | Nine additive strict-only AUT/EVI errors; no legacy downgrade |
| `schemas/memory-contracts.yaml`, four generated JSON schemas | Trusted input, approved policy, execution receipt and report contracts |
| `ci/contribution.yml`, `ci/inspect_document_pr.py` | Manual default-branch controller example, pinned actions, no PR checkout/execution |
| `ci/contribution-policy.example.json`, `ci/CODEOWNERS.example` | Synthetic, explicitly reviewed adoption assets with placeholders |
| `ci/pull-request.yml`, `ci/PULL_REQUEST_TEMPLATE.md` | Legacy boundary labeling, least-privilege settings and literal metadata handling |
| `references/contributions.md` | Single procedure for trusted inputs, obligations, receipts, exceptions and CI adoption |
| `skills/audit/SKILL.md`, two memory guides, `README.md`, `PROCESSES.md` | Connect the existing audit skill/PR process and distinguish operational context from authorization |
| `tests/memory/test_authority.py`, test README, this report | Synthetic positive/adversarial coverage and phase handoff |

The audit entry point links the shared contribution guide instead of duplicating it,
following `skill-creator`. There is no eighth skill. Python standard-library mechanics,
existing PyYAML/jsonschema and existing scoped resolvers are reused. No new dependency,
graph database, embedding service, external source copy, model or viewer was added.

## Verification

Measured on Linux/WSL, Python **3.14.4**:

| Gate | Result |
|---|---|
| `python3 -u -B tests/selfcheck.py` | Passed, including **194 offline memory tests** |
| `python3 -B -m unittest discover -s tests/memory -p test_authority.py -v` | **35 passed**, included in the full-suite total |
| `tests/memory/enola_conformance.py` with the already-present pinned executable | **9 passed**, isolated synthetic code |
| `skill-creator/scripts/quick_validate.py skills/audit` | Passed; no other skill changed |
| `python3 -B schemas/generate_memory.py --check` | **16 schemas**, 0 out of date |
| `python3 -B third_party/inventory.py --check` | Current; no dependency added |
| `git diff --check` | Passed |

The GitHub tests use synthetic API documents, mocked fetch transport and actual disposable
Git objects. Receipt test successes are synthetic fixtures, not claims that those product
commands executed. The full selfcheck also confirms catalog/template/entry-point coherence
and unchanged legacy fixture outcomes. Catalog counts were regenerated from the source.
Frozen acceptance criteria and comprehension questions were not weakened or rewritten.
No actual Python 3.12, native Windows, remote GitHub execution or model-based comprehension
evaluation is claimed.

## Limits, adoption and next phase

The GitHub asset is deliberately a **manual documentary-PR inspector**, not an automatic
required multi-repository PR check. It verifies protected/default-branch identity through
the API, fetches only the base repository's pull ref without checkout, and strips the
hosting token before invoking the verifier. It invents neither code observations nor
receipts: a mandate needing them stays blocked.

Multi-repository code CI needs a project-specific authenticated collector around the
published input/receipt contract. Test code runs separately, unprivileged, against the
exact captured set. Configure branch protections, latest-push/code-owner review and the
trusted workflow/pin when adopting; no remote was configured in this phase. A clean
local Git history is not evidence of hosted approval. Required checks must bind the
actual head/merge candidate and be rerun when it changes.

The strict profile is a bounded structural/evidence gate, not a complete documentary
audit or proof of semantic preservation, scope completeness, agent understanding or
production delivery. Classification filters are not an ACL. File-extension screening
does not understand executable YAML/embedded code. The ordinary audit and human semantic
review remain necessary; strict success always retains `review_required: true` and
`deployment: not-assessed`.

Policy mapping curation and authenticated receipt production are real adoption costs.
Dependencies still follow the framework's existing requirements ranges: deployments
needing fully reproducible verifier environments must additionally lock that environment.

Next is phase six: release sets, release/evaluation evidence and the distinction between
implemented code and verified running versions. Packaging and migration remain phase
seven. This phase does not release the increment, merge it, push it or migrate a project.
