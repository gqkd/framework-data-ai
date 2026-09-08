# Product Memory phase 2: optional contracts and documentary memory

Implementation record, 2026-09-08. Builds on phase-one commit `ad515a9` on
`codex/product-memory-phase-0`. This phase changes the framework only. No product
migration, immutable historical edit, remote push or framework release is part of it.

## Delivered result

An agent or maintainer can now query documentary sources without installing a code
provider, embedding model, service or graph database. Results include source revisions,
graph paths, complete selected document bodies and explicit gaps. A design-only product
works without an ARC or invented code. This is a **documentary pack**, not the operational
context pack, impact assessment or approval-policy enforcement planned for later phases.

```text
Authoritative Markdown/YAML
          |
  shared parser + scoped resolver
          |
  capture actual source bytes ------- immutable content manifest
          |
  document / entry / scope / component / repository / root nodes
          |
  declared edges + rule-backed derived edges
          |
  literal search / optional SQLite FTS5 / bounded explanatory traversal
          |
  JSON documentary pack + source references + gaps

Code roots: declared locations only. Code graph: phase 3, separate.
```

Compared with phase 1, agents no longer need to reconstruct every explicit relationship
from repeated file searches. They can retrieve a decision and its predecessors, navigate
component declarations and inspect the sources of each edge. The improvement is
traceability and visible uncertainty, **not** a claim that an agent now knows every
consequence or has passed the comprehension evaluation.

## Files and responsibilities

| Files | Implemented change |
|---|---|
| `schemas/memory-contracts.yaml` | Single contract for relation methods/inverses, identity shapes, views/root pairs, optional metadata, configuration, provenance and derived outputs |
| `schemas/generate_memory.py`, `schemas/memory/*.json` | Six self-contained generated output/configuration schemas; `--check` gate |
| `schemas/artifact-types.yaml` | Optional field references for DEC/ICG/CHG/ARC/SD/PLATFORM; repository zones; explicit runtime-directory exclusions |
| `schemas/generate.py`, seven affected `schemas/framework/*/v1.json` | Narrow nested-field support from the memory contract, duplicate-definition guards and regenerated artifact schemas |
| `src/framework_data_ai/artifacts.py`, `skills/audit/scripts/validate.py` | Shared scan selection/defaults; validator keeps its public `load_scan` alias and previous gate behavior |
| `src/framework_data_ai/workspace.py` | Validated shared config, private bindings, source selection, path and resource boundaries |
| `src/framework_data_ai/snapshots.py` | Actual-byte revisions, logical workspace identity, documentation commit when available, coherent-read checks and atomic publication |
| `src/framework_data_ai/memory/models.py` | Contract-driven schemas/runtime validation, canonical JSON, endpoint/provenance/inverse integrity |
| `src/framework_data_ai/memory/graph.py` | Documentary nodes/edges, component views, root mappings and scoped subjects joins |
| `src/framework_data_ai/memory/search.py`, `query.py` | Literal and optional FTS5 retrieval, bounded traversal and explanatory documentary packs |
| `memory.py`, `src/framework_data_ai/memory/cli.py` | Local-checkout/export-safe `doctor`, `build`, `query`; structured JSON and explicit exit states |
| `templates/DEC-ADR.md`, `ICG.md`, `CHG.md`, `ARC.md`, `SD.md`, `PLATFORM.md`, `product.yaml` | Commented optional examples and guidance; no new required field or retroactive enrichment |
| `references/product-memory.md`, root `README.md` | Operational commands, suggested ignore rules, contract semantics and boundaries |
| `tests/fixtures/memory/phase2-metadata.yaml`, `tests/memory/test_documentary.py` | Additive synthetic overlays and executable phase-two gates |
| `tests/memory/test_references.py`, `README.md`, this report; `tests/selfcheck.py` | Memory CLI Git-export test, current handoff and whole-suite integration |

No new artifact type or skill was added. `checks.yaml`, existing skill instructions,
provider configuration, dependency declarations and release metadata are unchanged.
The generator continues to maintain the existing catalog regions; no catalog is edited
by hand. Cross-document memory diagnostics are produced by `memory.py`, not new implicit
PR gates. The regular validator checks the new optional **shapes** through its schemas.

## Contract decisions made concrete

- All ten relation methods come from the contract. `constrained_by` and `affected_by`
  require a versioned rule and origin edge; inverse endpoints and source ranges are
  verified. An inverse cannot be declared by the author of an artifact.
- Node/source identity includes the logical documentation repository and owning scope.
  Homonymous local signals stay distinct. Ambiguous selectors and joins never choose a
  first match. Body-ID declaration semantics remain the known legacy policy from phase 1.
- `subjects` remains candidate → components, with one scoped routing join. Missing
  components remain named and partial. Impact categories are not spread over components.
- Component views keep `current`, `target`, `design` separate. Multiple repositories and
  overlapping roots are retained. The platform is not registered as a product.
- `realized_in` means a declared location. All code/root observations are `not_requested`
  with unresolved paths and unknown freshness in this phase, even if a checkout happens
  to exist. No file-level code claims are emitted.
- Source kind and assertion method are independent; confidence is accepted only for
  inferred claims. Inferences are rejected from this authoritative documentary projection.
- Legacy decisions without `applies_to` remain retrievable. Supersession never removes
  older text or automatically retires all its constraints.
- Canonical UTF-8 JSON uses sorted keys, stable ordering and a final LF. Actual source
  bytes and effective policy identify a snapshot; wall clock, mtimes, checkout paths,
  local bindings and repository URLs are not inserted into outputs.
- Publication verifies the graph/snapshot association and source consistency, writes a
  private staging directory and renames it atomically. Existing differing snapshots and
  competing writers are rejected. No authoritative source is overwritten.

## Technology choices and trade-offs

The core uses Python plus the existing PyYAML and jsonschema dependencies. JSON files are
the portable projection; there is no graph database. Plain-text retrieval is always
available. SQLite from the standard library offers an **optional in-memory FTS5** index;
capability is checked and fallback is reported. SQLite connections are explicitly closed.

No GitHub source code was copied or forked for this phase, and no new third-party module,
license/NOTICE obligation, hook or service was introduced. Code parsing is deliberately
not rebuilt here: the substitutable provider and its license/conformance review belong
to phase 3. The optional viewer and hybrid retrieval remain outside this phase.

Trade-offs accepted now:

- Queries rebuild from selected current sources; an old cache cannot silently answer as
  current. This is simpler to trust, but not an incremental indexing implementation.
- Optional mapping preserves adoption and history, but mapping precision is uneven.
  Missing metadata is a visible gap, not a generated guess.
- Literal/FTS search finds words, not equivalent meanings. Retrieval matches never create
  declared edges; body-only consumer references remain text, not invented graph semantics.
- The graph stores references to source revisions, not a permanent archive of all source
  bodies. Historical source recovery still depends on the source repository/backups.
- JSON schemas validate structure; understanding the meaning of a decision still requires
  reading its source. The model-based comprehension evaluation remains outstanding.

## Measured verification

Local environment: WSL Ubuntu 26.04, Python **3.14.4**, PyYAML **6.0.3**, jsonschema
**4.19.2**, SQLite **3.46.1**. CI's configured Python 3.12 and remote CI have not been run
in this local phase. No model CLI, provider or network service was used for these tests.

```bash
python3 -B -m unittest discover -s tests/memory -v
python3 -B -u tests/selfcheck.py
python3 -B schemas/generate.py --check
python3 -B schemas/generate_memory.py --check
git diff --check
```

- Final full selfcheck passed, including **90 memory tests**, zero expected failures.
- Existing artifact generation: **30 schemas and four catalog tables** current.
- Memory generation: **six schemas** current, separate from product artifact types.
- All seven edited templates still validate against their own artifact schemas.
- Frozen phase-zero fixtures and desired answers remain unchanged. Their phase-one
  findings baseline/delta checks still pass. New mapping tests operate on disposable
  synthetic copies, not real products or accepted historical artifacts.
- A real Git export starts the memory CLI from an unrelated directory with an incompatible
  package on PYTHONPATH, and produces a read-only documentary pack using its own source.

All seven phase-two obligations from the frozen acceptance contract now have executable
tests: canonical order, portable facts, document-only memory, inverse provenance,
confidence provenance, legacy-decision retrieval and partial supersession. Their tests
exercise generated documents and actual runtime outputs, not merely the specification.

Additional documentary safeguards are tested: scoped graph identities/subjects, malformed
metadata, confidentiality filtering, exact search-source lines, FTS fallback, traversal
limits, dirty content/deletion, concurrent source/configuration changes, differing existing
snapshots, source/output links, special files, YAML alias cycles and resource limits.
These do **not** satisfy the corresponding code-provider/evidence obligations of later
phases; no code snapshot or model-comprehension success is inferred from them.

## Adoption and explicit limits

Read-only commands work without new configuration. Shared usage should declare a stable
documentation repository ID in `.framework-memory/config.yaml`. Private bindings belong
in `.framework-memory/local.yaml`; generated output belongs under `_meta/memory/`. The
using project's maintainer reviews the suggested gitignore changes. This phase does not
edit those locations in any real project or run the migrator with `--adopt`.

Compatibility means the tested legacy fixtures remain valid without adding metadata,
not a universal downgrade guarantee. In particular, old closed repository-row schemas
do not know `zones`; enabling that field must be considered in phase 7's downgrade tests.
Registry/plugin versions remain unchanged until the increment is packaged and reviewed.

Source classification is an explicit local selection policy, not an ACL or DLP system.
Defaults permit public/internal and unclassified artifacts; selected bodies may still
contain secrets or hostile instructions. Excluded bodies/names are not indexed/exported,
but reading candidate metadata locally is necessary to classify it. Product navigation
filters are not security boundaries. No retrieved text is executed by this tool.

There is one documentation root per invocation. Multiple products/repositories inside
it are supported; federation of documentation checkouts is not implemented. Structural
localization supports ATX headings/markers, not a full CommonMark AST. File-system
double reads detect observed mutations, not every possible adversarial ABA race; atomic
rename/crash durability also depends on the filesystem. A stale build lock is not stolen.

The ordinary validator still supplies lifecycle, placement and workflow checks. Memory
build is not a replacement for that gate. There is no `context`/`impact` command, provider
capability contract implementation, task mandate check, deployment proof or agent skill
integration yet. Those are explicitly later units of the approved plan.

## Handoff to phase 3

Add the independent code-provider contract, pinned adapter and code snapshot/conformance
tests. Reuse the documentary identities, mappings, canonical serialization and visible
failure states. Observe code roots only through declared bindings; never translate an
unavailable repository/provider into zero impact. Keep direct code edges separate and
leave cross-repository traversal/impact policy in the framework query layer. Do not
install upstream hooks or overwrite agent instructions as a side effect.
