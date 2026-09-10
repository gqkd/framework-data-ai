# Adopting Product Memory without migrating product history

Use this guide when evaluating or adopting the increment. These are three independent
operations; installing/upgrading the framework does not grant permission for the other two.

```text
trusted previous framework + proposed framework
                    | compare validators, same project, read-only
                    v
              migration report -- approved adoption --> framework.yaml pin/version

explicit memory command --> selected sources --> regenerated documentary/code projections
explicit enrichment review --> gaps + source reading --> future metadata in its owning artifact
```

## 1. Compare, then adopt only with approval

Keep the previous trusted checkout/export until the comparison has been reviewed. Run from
any directory with Python dependencies installed from the proposed complete framework:

```bash
python3 /path/to/new-framework/skills/audit/scripts/migrate.py --root /path/to/documents --json
```

When the project's `framework_commit` is available in the framework clone, it is the
baseline. Otherwise, an unpinned version resolves via the registry's Git history; that is
not proof of the exact rules previously executed. `--from-commit` selects an explicit
commit, which must declare the requested version; an unavailable pin does not silently
fall back to another commit. `--from` overrides the starting version (and therefore stops
using the project's old pin). The report identifies `previous_source`.

For packages extracted from Git archives, with no Git history:

```bash
python3 /path/to/new-package/skills/audit/scripts/migrate.py \
  --root /path/to/documents --from-framework /path/to/old-package --json
```

Supply **complete, operator-trusted framework trees**, not just the old validator file and
never a framework supplied by an untrusted product PR. The tool executes both validators
in separate Python processes with their own schemas/packages. Export version matching is
checked; its origin is **not authenticated** (`commit_verified: false`). Independently
verify the archive source/digest before executing it. Neither a passing comparison nor a
same-version no-op establishes independent contribution authority.

Review new findings and historical repairs separately; preserve annotations only while
their findings still exist (`AN001`). `FW001`/`FW002`/`FW003` identify version/pin work.
With explicit approval, add `--adopt`: it only changes `framework.yaml`, never memory
configuration or optional product metadata. A pinned project needs a clean committed
target Git checkout; a Gitless export cannot move its pin. Strict profiles also require
the actual approved Git objects; a package alone cannot authenticate them.

`test_adoption.py` checks real complete baseline/new archives, foreign import isolation,
wrong/missing sources, dirty and Gitless pinned adoption, and the isolated approved write.
The normal migration/selfcheck gates still apply. No automated check can approve a new
architectural choice or declare that a human reviewed an annotation.

## 2. Use memory explicitly, without a provider or semantic search

```bash
python3 /path/to/framework/memory.py doctor --root /path/to/documents
python3 /path/to/framework/memory.py query --root /path/to/documents --text 'access boundary' --search-engine literal
python3 /path/to/framework/memory.py context --root /path/to/documents --goal 'Explain the planned change' --skill cycle
python3 /path/to/framework/memory.py gaps --root /path/to/documents
```

These commands do not persist memory or run a code provider. No configuration, graph DB,
embedding service, MCP server or model key is required. Literal search is the default;
SQLite FTS5 is an explicit optional local text-search mode, not semantic retrieval.
Unobserved/unavailable code is not zero impact. Required readings and their missing/deferred
status remain visible; delivering a context pack does not prove understanding.

`build` explicitly publishes derived snapshots; `build --dry-run --export` only reports.
Use [product-memory.md](product-memory.md) for source filters, stable scope IDs, private
bindings, output exclusions and the separately isolated `code` command. Strict contribution
and release profiles need independently trusted CI inputs and are separate opt-ins; copying
a workflow or enabling memory does not activate repository protection.

## 3. Enrich only where the sources support it

`gaps` is a deterministic **adoption-report**, not an artifact or completeness score. It
reports missing optional fields, missing `code_roots` on accepted component views, source
revisions, lifecycle-aware handling and graph issues. It respects source exclusions and
classification filters. It never invents `applies_to`, `subjects`, components or paths.
An absent code root on a design can be correct; an explicitly empty field is not reported
as an absent one. No graph inference authorizes a historical rewrite.

Keep repository ownership in `product.yaml` or the shared platform manifest; components
and their current/target/design roots in the owning architecture/design. No second product
inventory belongs in memory configuration. `FM002` checks optional field shape through
the artifact schema; graph issues such as `root-unresolved` and `component-owner-mismatch`
report structural mapping problems. No check decides whether a mapping is true.
`test_adoption.py` checks deterministic/filter-respecting gaps and lifecycle handling.

For living documents propose reviewed metadata edits; for immutable documents use a new
successor when justified, and for append-only sources a linked new event. Do not create a
successor just to eliminate an optional gap. No required field is added to old projects.

## Distribution, dependencies and rollback

The distribution is the complete repository or a complete Git archive, also usable through
the existing plugin mechanism. Do not distribute `src/` or one script alone: schemas,
references, templates, skill bodies and provider lock are runtime inputs. There is no new
PyPI package, autonomous installer, binary bundling or background service.

```bash
python3 -m pip install -r /path/to/framework/requirements.txt -c /path/to/framework/constraints.txt
python3 /path/to/framework/third_party/inventory.py --check
python3 /path/to/framework/schemas/generate.py --check
python3 /path/to/framework/schemas/generate_memory.py --check
```

Use an isolated environment. `requirements.txt` retains supported ranges for embedders;
`constraints.txt` fixes the exercised direct/transitive baseline for CPython 3.12/3.14.
It is generated from `third_party/manifest.yaml`, not maintained in two places. Review
versions there, regenerate inventory/constraints, and rerun the full suite after updates.
Version constraints do not pin wheel hashes or OS packages and are not a vulnerability
audit. CI declares both Python versions; execution evidence is in the phase report.

Enola remains operator-supplied at `providers.lock.json`'s exact platform digest. The only
redistributed third-party code is the optional MIT browser renderer described in
`references/memory-viewer.md`. Publisher license metadata and
reviewed-but-not-copied repository commits live in the manifest/inventory; preserve their
own notices if distribution later includes binaries. The viewer is an opt-in local export,
not a runtime dependency or product release gate. Hybrid/semantic retrieval remains deferred.

Rollback the **tool** by selecting the preserved previous checkout and its environment;
the migration command intentionally refuses to disguise a downgrade as a forward adoption.
A maintainer may restore the matching earlier project pin/configuration with explicit
approval. Do not delete/rewrite historical artifacts. Derived snapshots can remain ignored;
the old validator ignores generated memory under the normal scan defaults, tested by
`test_tool_rollback_preserves_historical_documents_and_ignores_generated_memory`.
Rebuilding with new rule bytes, constraints or interpreter/dependency versions produces
a new identity. Arbitrarily old versions, custom
scan overrides and project-promoted warnings require their own comparison. Tool rollback
does not undo a product deployment or preserve gates that the older tool did not implement.
