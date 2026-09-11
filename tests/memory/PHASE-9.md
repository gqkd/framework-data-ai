# Product Memory phase 9 — operational qualification evidence

Execution record, 2026-09-10/11, on `codex/product-memory-phase-0`, starting at `80d9969`.
**Implementation and evidence capture are delivered; operational qualification is not closed.**
The behavior review has an unsupported-claim finding, source-trace gaps and no independent
human signoff. No published release, adoption, push, merge or production execution is implied.

## Implemented

| File / surface | Change and benefit |
|---|---|
| `evals/behaviour/memory/qualify.py` | Explicit synthetic preparation/capture; read-only command sandbox with preflight; no hidden answer keys; exact-input replay into a new directory; complete process streams and timeouts; mutations fail closed; no automatic semantic grading |
| `evals/behaviour/memory/pilot.py` | Explicit private read-only documentary pilot using the actual adopted pin; optional static Python observations; no inferred mapping; per-file partial/unavailable coverage; output containment and source/Git-state checks |
| `memory/providers/enola.py` | Recognizes tightly bounded directory-level `symbol-rollup` dependencies produced by the pinned provider, instead of rejecting the entire observation |
| `memory/code_graph.py` | Retains provider-derived aggregates as raw evidence; never promotes them to direct code nodes/edges; unsupported evidence keeps coverage partial |
| `references/operational-memory.md` | Incidental claims need sources; absent formal models do not erase documented constraints; cost adjectives require evidence or explicit hypothesis; aggregate provenance clarified |
| Offline/provider tests | Capture/replay integrity, output containment, full streams/timeouts, disabled fsmonitor, aggregate parsing and no indirect-edge promotion; real-provider nested-package reproducer |
| Evaluation results | Fourteen unaltered answers, one separate targeted sample, trace hashes and explicit review findings; frozen cases/thresholds unchanged |
| Registry/plugin metadata | PATCH source version **3.8.1**; no mandatory field or migration introduced |

The OpenAI documentation skill was used to check the supported CLI execution and permission
options. No new skill, agent delegation, account reset, plugin installation, graph service,
embedding pipeline or model judge was added. Existing Enola lock, Python dependencies and
optional Cytoscape renderer are unchanged; no new license-bearing component is incorporated.

## Defect found by the real pilot

The pinned Enola 0.4.15 can emit package-to-package dependency aggregates with a directory
in `file`, `props.derived: symbol-rollup`, and no source position. The reader previously
allowed directory locators only for modules, so a valid aggregate rejected all observations
for two Python checkouts. A minimal **synthetic nested-package import** reproduced that
failure before the fix. No private implementation was copied into a fixture.

The reader now accepts only the recognized aggregate shape, positive non-boolean count,
directory containing a captured source and absence of source positions. Unknown directories,
forged positions, inconsistent hashes/census and malformed records remain rejected. The
projection excludes all provider-derived structural records from direct traversal. This
does not add transitive impact to the provider or silently convert aggregate evidence into
observed calls. Offline and real-binary regressions exercise both sides of the boundary.

## Synthetic model assessment

See the [full review and original answers](../../evals/behaviour/memory/results/2026-09-10/REVIEW.md).
Fourteen complete responses were obtained over the original run plus an exact-input replay;
one interrupted quota-limited attempt remains unavailable. A separate targeted sample is
retained, not substituted. No project/runtime mutation was observed in post-run inventories.

The implementing agent read all answers in full and compared them with the frozen rubric.
Mandatory conclusions are generally cautious and supported, but the cache answer makes
unsupported incidental claims; two other cases lack complete required source-output traces.
The extra cache sample does not demonstrate that its finding was resolved. **Not 14/14 pass.**
The CLI does not expose actual model/reasoning identity in these events. These are single
samples with precomputed context, not automatic skill-routing, reliability or comparative
improvement measurements. Human review and final-runtime qualification remain pending.

## Real pilot — reviewed anonymous aggregates only

No real documentary/code contents were sent to the model. The local process selected only
the configured `internal`/`public` documentary sources; confidential corpus/extracts were
outside that capture. This is not a comprehensive privacy audit. Raw context/graphs and
source identities remain in private temporary output, not in the framework distribution.

The final capture selected **99 documentary sources**, with **457 nodes / 544 relations**,
**59 issues / 74 gaps** and explicitly **partial** coverage. These are emitted diagnostics,
not 59 verified semantic defects. At a 100,000-character context budget:

| Anonymous scope | Required | Included | Deferred | Missing | Rule resolution |
|---|---:|---:|---:|---:|---|
| 1 | 258 | 19 | 234 | 5 | actual pinned commit, 3.6.3 |
| 2 | 148 | 19 | 127 | 2 | actual pinned commit, 3.6.3 |

Neither pack is complete. `reading_status: not-attested`, `understanding: not-evaluated`
and `authorization: not-verified` are preserved. Missing historical Alternatives sections
were inspected as headings, not filled in or retrofitted into immutable decisions.
Direct code observations were run separately, because no local document-to-code binding
was installed: **mapping not validated**, not a completed cross-repository impact analysis.

| Anonymous checkout | Tracked Python files | Provider records | Coverage |
|---|---:|---:|---|
| 1 | 44 | 688 | partial: 41 available, 3 partial Python; 76 other unsupported files |
| 2 | 0 | 0 | unavailable for this profile; 41 unsupported files |
| 3 | 10 | 60 | partial: 6 available, 4 partial Python; 16 other unsupported files |
| 4 | 0 | 0 | unavailable for this profile; 21 unsupported files |
| 5 | 0 | 0 | unavailable: 7 unsupported files, 4 unavailable submodule entries |

The two Python observations were rejected before the fix and return partial evidence after
it. Other languages, untracked/ignored files, submodules, running processes and customer
data are not observed by this profile. No code, project tests, hooks or database was executed.
Selected source hashes and Git state stayed unchanged **during each pilot capture**.

Earlier documentary captures counted 98 sources / 454 nodes / 540 relations; the private
documentation was independently changing between runs. These counts therefore do not
measure an effect of the provider fix. Existing dirty changes were preserved. The sole
intended documentary mutation outside the framework is a required parking-lot annotation
about a stale checkout instruction, separately validated under the product's adopted pin;
it is not adoption or remediation of product decisions.

## Verification and handoff

Before the committed-source gate: **12 qualification/pilot tests passed**, **35 adapter
tests passed**, and **10 real pinned-provider conformance tests passed**, including the
nested-package regression. Full framework/selfcheck evidence is recorded below after
running against the committed implementation. No expected finding or frozen threshold was
changed to pass a test. Browser behavior is unchanged from phase 8; no new browser session
or real-document viewer export is part of this phase.

The practical remaining work is independent review of the behavior findings, complete
source-output capture with identified model/final runtime, and a separately authorized
adoption/mapping exercise. The frozen metadata/architecture decisions are not reopened by
these limitations. A successful unit test or static observation is not production verification.

## First committed-source gate

On `99d13f5153d3313af35c5af00749eefaaaaa88db`, the full selfcheck found exactly one
problem: `.claude-plugin/marketplace.json` still declared 3.8.0 while the registry and
plugin manifest declared 3.8.1. The catalog is corrected to the registry's version; no
version-consistency check is bypassed. All **273 offline memory tests passed in 112.878 s**
within that run; the overall gate nevertheless failed. A separate pre-commit memory run
passed the same 273 tests in 105.028 s.

On the committed implementation, **10/10 real Enola conformance tests passed in 7.226 s**.
The unchanged viewer's **8 Node tests passed**; 30 artifact schemas / 4 catalogs, 23 memory
schemas, third-party inventory/constraints and whitespace checks passed. Provider lock,
Python dependencies, renderer and frozen cases/fixture generator/metadata overlay are
unchanged from `80d9969` (verified by Git diff). Local Python was CPython 3.14.4, not the
CI-configured 3.12; no claim is made of remote CI execution.

The sole private documentary annotation passed its adopted 3.6.3 validator before and
after editing: **0 errors, 7 warnings, all 7 already annotated, 0 unannotated**. The
annotation and partial-review timestamp were not committed with unrelated private work.
