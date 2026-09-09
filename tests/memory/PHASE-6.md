# Product Memory phase 6: exact release sets and witnessed delivery

Implementation record, 2026-09-09. Starts from phase-five commit `b44dbbd` on
`codex/product-memory-phase-0`. Scope: framework only, with disposable synthetic Git
histories. No product/client artifact, historical immutable, production instance, provider
installation, remote protection, release version, project migration or remote push changed.

## Implemented

```text
approved documentary snapshot + clean adopted framework runtime
       |
       +--> RLM release_set + existing config/infrastructure/AI/data
       |      repositories/commits/build digests + shared release/condition references
       |                         |
       |                canonical candidate identity
       |                         |
       +--> EVR verified_code + release_set_hash + exact frozen EVP bytes/version
       +--> REL / included CHG / current approval / exact dependency identities
       |
independently authenticated receipts
       +--> pre-release: build provenance + frozen threshold evaluation
       +--> integration: tested whole set + dependency compatibility
       +--> deployment: observed whole set + environment + timestamp + smoke result
       |
default-branch histories of ALL included repositories (not an assumed main)
       |
strict-release: prepared / implemented / verified evidence eligibility
               no lifecycle write, no manifest rewrite, no merge or deployment
```

The RLM identity binds builds and operational inputs, not only commits. A changed prompt,
configuration, dataset, infrastructure target or shared release invalidates reuse of the
old EVR identity and execution receipts. Declared repository aliases are resolved through
the existing scoped index; a required consumer cannot disappear from the set. Shared
releases are traversed with cycle/depth/count bounds and conflicting repository versions
are rejected. Compatibility sources are byte-pinned and require an existing section marker;
their meaning remains an integration/review obligation, not a parser's decision.

RLM.release_set and EVR.release_set_hash are optional additive fields. A historical scalar
RLM is normalized only when exactly one eligible repository identifies it; one commit is
never copied across a distributed set. Normalization is a detached read view, not a rewrite.
Historical EVRs without exact-set evidence do not become strict passes retroactively.

The new `strict-release` validator profile consumes CI-authenticated inputs and emits a
read-only JSON report. It verifies adopted rule/runtime bytes, approved documentary history,
current source/mandate consistency, candidate/EVR/REL linkage, frozen plan, repository
identity/default-branch ancestry and independently witnessed receipts. Missing access,
filtered sources, stale/failed/forged receipts and an observation of staging instead of
the manifest's production target remain failures. A request for prepared cannot hide an
already verified CHG: current closure claims raise the required evidence level.

RLS001/RLS002 are additive documentary warnings only for RLMs opting into the new metadata.
RLS003–RLS007 are strict-profile errors. The strict gate cannot be weakened by project
severity overrides. Legacy schemas and fixture outcomes remain compatible.

The release skill previously instructed closing CHGs immediately after preparing RLM/REL.
That path is now split into proposed integration and observed-delivery transitions. The
skill keeps the frozen metric/slice rules, human approval boundary and deploy prohibition.
Following skill-creator, detailed mechanics live in one shared reference; the entry point
links it without creating another skill. Operational context retains the selected audit or
release guide only when the adopted skill references it, including gaps for missing guides;
historical pins do not silently acquire current instructions.

## Files

| File/group | Responsibility |
|---|---|
| `src/framework_data_ai/release_sets.py` | Detached legacy normalization, scoped code/build set, canonical candidate identity and EVR coherence |
| `src/framework_data_ai/release_evidence.py` | Strict read-only history, frozen-plan, dependency, receipt and lifecycle-eligibility assessment |
| `src/framework_data_ai/authority.py` | Shared clean-runtime check; explicit generated-source inclusion for the release reader only |
| `src/framework_data_ai/memory/framework_sources.py` | Keep the selected skill's adopted contribution/release guide in required source delivery |
| `schemas/artifact-types.yaml` and two generated artifact schemas | Optional RLM.release_set / EVR.release_set_hash |
| `schemas/memory-contracts.yaml` and four generated schemas | Versioned release set, trusted input, staged receipt, release report |
| `skills/audit/scripts/validate.py`, `skills/audit/checks.yaml` | Strict-release dispatch and seven catalogued checks |
| `skills/release/SKILL.md`, `references/release-evidence.md` | Existing release skill, shared evidence protocol, no automatic closure/deploy |
| `templates/RLM.yaml`, `templates/EVR.md`, `templates/REL.md`, `templates/CHG.md` | Forward-only guidance on exact set and preparation/integration/delivery distinction |
| `FRAMEWORK.md`, `PROCESSES.md`, `README.md`, `references/product-memory.md` | Public entry points and affected release-flow diagrams aligned |
| `tests/memory/test_release.py`, test README, this report | Synthetic acceptance and phase handoff |

No new external library, copied repository module, database, model, embedding service,
viewer or signing/deployment service was added. Existing standard library, PyYAML,
jsonschema, Git snapshots, scoped resolver and canonical serialization are reused.

## Verification

Measured on Linux/WSL, Python **3.14.4**:

| Gate | Result |
|---|---|
| `python3 -u -B tests/selfcheck.py` on stable source files | Passed, including **223 offline memory tests** in 116.368 seconds |
| Phase-six release cases included in that total | **29 passed**; the earlier targeted run passed 28 before the source-delivery case was added |
| Real-provider conformance with the already-present pinned Enola executable | **9 passed**, isolated synthetic code |
| `skill-creator/scripts/quick_validate.py skills/release` | Passed |
| `python3 -B schemas/generate.py --check` | 30 artifact schemas and 4 catalog tables current |
| `python3 -B schemas/generate_memory.py --check` | 20 schemas, 0 out of date |
| `python3 -B third_party/inventory.py --check` | Current; no added dependency |
| `git diff --check` | Passed |

An earlier full run found one concurrent-generator-change error while final edits were
in progress. The guard correctly refused that snapshot. The stable rerun above passed;
no gate, frozen fixture meaning or acceptance criterion was relaxed. All previous
contribution, context, documentary and provider regression cases remain included.

## Boundaries and adoption

- Trusted-controller inputs are an API, not self-authenticating JSON. Hosting identities,
  approved tips and receipt producer/run/stage/artifact identity must be authenticated by
  the project's integration, not copied from the contribution or from a claimed verdict.
- Pre-release receipts must establish build-to-code provenance and the actual metric/slice
  gate; arbitrary prose tables are not numerically graded by this structural verifier.
  Integration receipts cover the full transitive set and referenced compatibility conditions.
- A deployment witness must capture the actual whole set and smoke result in the intended
  environment. It must not copy expected values out of RLM or select an old green run while
  ignoring a newer failed/rolled-back observation. Evidence is as-of, not monitoring.
- Supported state is evidence eligibility, not the project's complete Definition of Done or
  new authorization. Ordinary documentary audit, semantic review and project-specific
  closure/production requirements still apply; no artifact status changes automatically.
- The framework supplies no deployer, atomic multi-repository transaction, hosting collector
  or cross-documentary-repository dependency fetcher. Missing dependency access blocks.
- No live build/deploy, remote GitHub run, native Windows certification, Python 3.12 execution
  or model-understanding result is claimed. Tests use Linux/WSL and synthetic receipts.

Next is phase seven: full historical/new export migration checks, packaging/constraints,
adoption documentation and final public-diagram alignment, then the compatible MINOR bump.
No version bump, release tag, plugin reinstall or project adoption belongs to this phase.
