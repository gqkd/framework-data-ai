# Product Memory phase 3: isolated provider and separate code graph

Implementation record, 2026-09-08. Builds on phase-two commit `d47ea03` on
`codex/product-memory-phase-0`. Only the framework changes: no product/client documents,
historical immutable artifacts, product migration, external hook/configuration, release
version or remote push. The user's instruction authorizes this framework phase, not a
product implementation or a new product decision.

## Delivered unit

```text
authoritative documents --> documentary snapshot / graph (unchanged authority)
                                      |
                           component -> declared root
                                      |
private binding -> explicit Git/worktree capture -> Python syntax guard
                                      |                    |
                              captured revisions      invalid = gap
                                      |
                       isolated pinned Enola on a copy
                                      |
                        strict receipt + fact reader
                                      |
                            SEPARATE code graph
                                      |
               root bridge / direct edges / evidence / coverage
```

The new `memory.py code` command observes explicitly bound, declared repositories and
produces `code-graph.json` plus a content-addressed manifest. Files, definitions, direct
imports/calls and source locations are available without installing a memory server,
graph database, embedding model or MCP platform integration. `build` and `query` remain
documentary-only; a design-only workspace does not require invented code.

An agent can inspect *which captured source* supports a direct relationship and *which
component/root declaration* connects it to the documents. It cannot infer complete runtime
behavior, claim zero impact from missing edges, approve a CHG or declare a target implemented.
Operational context packs, traversal/impact policy and skill integration remain phase 4.

## Files and responsibilities

| Files | Change |
|---|---|
| `memory/providers/base.py` | Replaceable capability/status/extract boundary and controllable fake; no `impact()` |
| `memory/providers/enola.py` | Independent strict reader, pinned binary checks, Python syntax guard, isolated execution; no Cognee dependency |
| `memory/providers/process.py` | Bounded subprocess stdout/stderr, timeout and process-group cleanup |
| `memory/code_sources.py` | Explicit worktree/commit capture, actual hashes, staged index, untracked policy, missing/unsupported coverage and coherent rereads |
| `memory/code_graph.py` | Qualified identities, retained evidence, direct edges, unresolved targets, overlapping root bridges and separate publication |
| `memory/cli.py` | Optional `code` command and non-executing provider preflight in `doctor` |
| `snapshots.py` | Reused atomic publication primitive; lock becomes a generator input; documentary API preserved |
| `schemas/memory-contracts.yaml`, `schemas/memory/code-graph.v1.json` | One new generated output schema; no new artifact or required product field |
| `providers.lock.json` | Official release/commit, extractor/format/profile and archive/executable checksums |
| `third_party/manifest.yaml`, `inventory.py`, `inventory.json` | Reviewed-source provenance and generated direct-integration inventory; no copied code or bundled binary |
| `tests/memory/test_code_provider.py` | Offline provider, reader, capture, identity, provenance and publication gates |
| `tests/memory/enola_conformance.py` | Explicit real-binary suite using only synthetic inputs; no downloader/installer |
| `tests/memory/test_references.py`, `tests/selfcheck.py` | Export fixture carries the lock; normal framework gate includes the offline provider suite |
| `references/product-memory.md`, README files, this report | Commands, profile limitations, dependency maintenance and handoff |

Source module paths in the table are relative to `src/framework_data_ai/`. Generated
artifact schemas and catalog tables retain their phase-two meaning. No existing skill,
dependency requirement, PR policy or acceptance question was silently rewritten.

## Conformance finding and narrow adapter correction

The candidate is identified by the lock, not by a moving `latest` tag. The official
[release](https://github.com/enola-labs/enola/releases/tag/v0.4.15) and its archive checksum
were checked against the downloaded artifact. Source review used the pinned commit's
[fact contract](https://github.com/enola-labs/enola/blob/d8864dfb238718eded7635912bc4a4fd3ef9959f/docs/schema/facts.md),
[receipt contract](https://github.com/enola-labs/enola/blob/d8864dfb238718eded7635912bc4a4fd3ef9959f/docs/schema/receipt.md),
configuration, Python extractor and receipt writer.

The **unmodified provider failed a required gate**. Given `def broken(:` followed by an
unfinished call, it exited successfully, emitted `broken.broken` and reported three parsed
files with zero parse errors. This was observed in a network-isolated real-binary run,
not inferred from a README. Its Python AST walker accepts Tree-sitter recovery without
surfacing root syntax errors; a receipt's existence is therefore not sufficient evidence.

The planned fallback was then inspected at its pinned source revision (see the third-party
manifest). `code-review-graph`'s Python parse path likewise walks the recovered tree without
a root `has_error` gate. This is a source-level finding, **not** a completed runtime
certification of the fallback. It was not installed, and its `install` command was not run.

The supported unit is consequently **Enola plus the adapter's independent CPython syntax
guard**. `ast.parse(..., feature_version=(3, 12))` validates only syntax, never imports or
executes project code. Bad files are retained in source coverage but excluded from provider
input and structural facts. Mixed input becomes partial; all invalid/unsupported input is
unavailable. The provider receipt describes the valid subset, while the framework receipt
describes the complete selected inventory and every gap. No upstream fork or second code
extractor was necessary. This is an explicit adapter correction, not certification of
unmodified Enola and not a weakened acceptance criterion.

## Integrity and authority boundaries

- Actual bytes, commit/index/inventory, profile, runtime and generator identify results.
  Wall clock, mtimes, private paths, checkout basename and provider duration do not.
- Unknown versions/formats, missing receipt, corrupt JSON, duplicate JSON keys, count/hash
  mismatches, invalid IDs and out-of-input source ranges are rejected.
- Duplicate records retain occurrence IDs and source evidence. Entity aggregation uses
  repository/provider/kind/name/file; different positions/properties remain inspectable.
- Only a provided, verified `target_id` resolves an edge. Name-only matches and cross-repo
  symbols remain unresolved. A repository/root binding is not a symbol-level binding.
- Structural facts and provider annotations/heuristics are separate. Nonprojected evidence
  is retained and reported, not silently presented as complete structural coverage.
- Current/target/design root bridges preserve overlaps and source declarations. Zones
  classify test/vendor/generated/normal code; they do not exclude or prove irrelevance.
- There is no write to observed checkouts. Only captured Python files enter the isolated
  copy; local config, agent instructions, Git metadata and hooks do not. Isolation failure
  is unavailable, never permission to run unsandboxed. No network/download during observation.
- Explicit Git commit mode supports missing worktrees and bare repositories. It never
  silently substitutes HEAD, performs a checkout, runs filters or repairs source state.
- Concurrent changes block coherent publication. Existing snapshots are compared and
  never overwritten; publication uses the same atomic-directory primitive as phase 2.

## Verification and limitations

The deterministic offline suite and full framework selfcheck passed before committing.
The separate real-binary conformance suite has **nine executable cases**: basic Python
facts/locations, mixed parser failure, all invalid/unsupported, repeated-byte determinism,
frozen multi-repository fixture, test/generated/vendor coverage, nonexecution of local
config/hooks/source side effects, CLI/documentary fallback and explicit-commit observation.
Final measured results on the phase-three tree:

| Gate | Observed result |
|---|---|
| Full `tests/selfcheck.py` | Passed: framework consistent with itself |
| Offline memory suite included in selfcheck | **123 passed**, including **33** new phase-three tests; no skips/expected failures |
| Explicit `enola_conformance.py --enola <pinned executable>` | **9 passed** on the real binary |
| Artifact schema/catalog generation check | **30 schemas and 4 tables** current |
| Memory schema generation check | **7 schemas** current |
| Direct integration inventory `--check` | Current |
| `git diff --check` | No whitespace errors |

The offline tests additionally cover missing-repository appearance, source/index mutations,
changed bindings/provider, tampered but schema-valid graph output, provider-record retention,
unresolved targets, missing receipts, census inconsistency, output locks and symlink refusal.
The real suite was rerun after the final source changes. Results refer to executed local
commands, not to an unrun remote CI or a claim of product comprehension.

Real conformance was run on Linux x86_64 through WSL, CPython 3.14.4, with the pinned
release and extractor. The grammar guard targets Python 3.12 syntax; support for native
Windows/macOS, other languages, newer Python grammar, complete dynamic dispatch and
cross-repository symbol resolution is **not** claimed. Configured CI Python 3.12 is not
evidence that the real-provider suite has run there. No model comprehension evaluation was
run; the fourteen existing questions remain unchanged.

The binary is operator supplied, not installed or distributed by this commit. Bubblewrap
and prlimit are required host tools only for code observation. Its integration inventory
is not a full transitive SBOM or legal clearance: root license, upstream NOTICE, declared
vendored grammar licenses and Go dependency declarations were inspected; every transitive
license was not audited. No source was copied from Enola, Cognee or the fallback.

Remaining limits include bounded repository size, unsupported non-Python source,
Git-ignored untracked files outside the inventory, static-analysis incompleteness, source
annotations potentially containing sensitive information, host-dependent filesystem
atomicity and a syntax guard that is not a typechecker or runtime validation. An unavailable
or partial code graph does not make the documentary graph unavailable.

## Handoff

The next phase consumes these observations to compose operational context/impact reports
and extend the seven existing skills. It must retain mandatory documentary reading,
source provenance, declared-vs-observed distinctions and existing authorization policy.
It must not promote raw provider annotations into product constraints or infer impact
absence from an unresolved edge or unavailable repository.
