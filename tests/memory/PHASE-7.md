# Product Memory phase 7 — adoption and complete source distribution

Execution record for 2026-09-09. Scope: framework only, on the existing
`codex/product-memory-phase-0` branch, starting from `6e1ae81`. The public pre-increment
baseline remains `db75f310e2f42453cb0fe1b26573c3f6b5736790` (registry 3.6.3).
No product/client source or database was accessed for this phase.

## Implemented

| Surface | Result |
|---|---|
| `migrate.py` | Complete previous export or exact Git commit; project pin preferred; separate isolated validator processes; explicit baseline provenance |
| Adoption safety | Read-only by default; approved adoption writes version/existing pin only; dirty target or Gitless pinned adoption refused; failure remains nonzero even on the same version |
| `memory.py gaps` | Deterministic, source-filtered adoption-report; optional mapping questions with source revision and lifecycle-aware handling; no inferred values or repairs |
| Snapshot identity | Generator inputs also hash constraints and actual interpreter/dependency versions, without host paths or run timestamps |
| Dependencies | Generated constraints and integration inventory from one manifest; existing Enola lock unchanged; no new runtime dependency or vendored code |
| Source packaging | Tests compare actual full previous and proposed Git archives from an unrelated working directory; package includes schemas, guides, skills, templates and runtime |
| Documentation | Shared adoption guide; audit skill routes to it and adopted context retains it; README/FRAMEWORK/PROCESSES/SKILLS and migration diagrams aligned |
| Version | 3.7.0 synchronized in registry and plugin metadata; check-naming migration note; generated catalogs/schemas |
| CI | Read-only framework workflow, pinned action revisions, Python 3.12/3.14 matrix, constrained dependency installation and pip check; consumer examples use the same constraints |

No eighth skill. The skill-creator guidance kept the audit change narrow and placed the
procedure in a single reference. Read-only memory, mapping enrichment, provider use and
trusted CI adoption are independent of the framework upgrade.

## Verification record

The first 13 new adoption tests passed against complete source exports. After adding
project-pin, same-version failure and runtime-provenance cases, all 16 passed in 11.199 s
in an isolated CPython 3.14.4 environment. An additional test covers all eight original
scenarios against both validators, with no new fields and no source writes.

Dependencies installed into `/tmp/framework-phase7-validation-20260909`, not a product
environment. The OS lacks ensurepip/python3-venv; the existing pip successfully populated
the isolated interpreter via `--python`. `pip check`: no broken requirements. No OS
package was installed. Publisher release metadata and installed requirement declarations
were inspected for the versions recorded in `third_party/manifest.yaml`.

The post-version 17-test compatibility run passed in 13.846 s. The full offline memory
suite then passed all 240 tests in 125.987 s in the isolated environment. A subsequent
narrow guard/test preserves support for older referencing versions that do not install
the optional typing-extensions package; its absence is represented, not made mandatory.
All 9 real pinned Enola conformance tests passed in 6.363 s. Audit skill quick validation,
30 artifact schemas/4 catalogs, 21 memory schemas, inventory/constraints and git diff
whitespace checks passed. No frozen fixture expectation or severity was relaxed.

Final post-commit selfcheck results will be recorded after the committed version can be
exercised by the migration check. It requires committed target bytes and is not bypassed
for a working-tree version bump; its adoption fixture now uses a clean temporary clone
outside the synthetic project, never the dirty development tree.

## What this does not claim

- Compatibility is exercised on the complete 3.6.3 baseline and synthetic scenario set,
  not every historical framework or customized consumer. Earlier MAJOR migrations remain
  separate; no historical DEC/ICG/EVR was enriched.
- A package version does not authenticate archive origin. `--from-framework` executes
  operator-trusted tooling; it is not a safe way to run an untrusted PR's validator.
- Dependency constraints fix versions, not wheel hashes or OS packages. Publisher license
  metadata and reviewed provider sources are not a transitive binary SBOM, legal opinion
  or vulnerability audit. No Python/provider binaries are redistributed.
- CPython 3.12 is configured in CI; the local runtime is 3.14.4. A remote CI run is not
  claimed. Strict contribution/release witnesses still require project integration.
- Offline tests prove mechanics, not that an agent understood the sources, nor real
  product tests, builds, thresholds, default-branch delivery or production deployment.
- Multi-document-repository federation, semantic/hybrid retrieval, graph database,
  co-change mining and interactive viewer remain outside this increment. The code graph
  remains separate and optional; missing code observations are not empty impact.

## Adoption handoff

Use `references/adoption.md`: compare trusted complete sources first; approve only the
actual version/pin change; try documentary memory; review gaps in the authoritative living
sources or future successor artifacts. Source history need not be rolled back to stop using
the tool. A tool rollback does not undo a product deployment or retain the newer strict gates.

This phase does not run `--adopt` on an actual project, install/reinstall a plugin, create
a release tag, push/publish, alter remote protection or deploy anything. The version in
source is prepared for the separate reviewed release/adoption workflow.
