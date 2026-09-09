# Product memory — documents, separate code graph and operational reports

This is an opt-in development aid, not an authorization, autonomous agent, semantic RAG
service or second source of truth. Markdown/YAML remain authoritative. The CLI projects
declared relationships and provides source-backed text queries. It does not change a
product's documents, approve a CHG, execute project code, install hooks or contact a database.

```text
project Markdown/YAML --> shared parser/resolver --> documentary graph
                               |                         |
                     content-hashed snapshot       query + source bodies

explicit code bindings --> captured Git/worktree bytes --> isolated optional provider
                                                             |
declared code roots ------[current/target/design bridge]--> separate code graph
```

## Commands and scope

Run these from any directory, using a complete framework checkout or Git export:

```bash
python3 /path/to/framework/memory.py doctor --root /path/to/documents
python3 /path/to/framework/memory.py build --root /path/to/documents
python3 /path/to/framework/memory.py build --root /path/to/documents --dry-run --export
python3 /path/to/framework/memory.py query --root /path/to/documents --product product-a
python3 /path/to/framework/memory.py query --root /path/to/documents --text 'tenant state'
python3 /path/to/framework/memory.py query --root /path/to/documents --node DEC-001 --hops 2
```

All outputs are JSON (`--json` is accepted explicitly too). Exit codes: **0** usable
documentary result, **1** partial result (inspect issues/truncation), **2** unavailable or
invalid request. Code inspection is `not_requested` in documentary commands. An available
documentary graph does **not** mean complete product knowledge or zero code impact.

`doctor`, `query` and `build --dry-run` are read-only. `build` only publishes under
`_meta/memory/snapshots/<content-id>/`, with `graph.json` and its hashed `manifest.json`.
An existing snapshot is checked for equality and never overwritten. A lock prevents two
publishers from competing; an abandoned `.build.lock` requires operator inspection, not
automatic lock theft. The directory rename is atomic on the same filesystem; network
filesystem guarantees and crash durability of directory entries depend on the host.

Queries currently rebuild an in-memory projection of the **current** selected sources;
they do not trust an old on-disk snapshot or cache. Full source bodies (without front
matter) accompany selected documents, with content revisions and exact line offsets.
This is a documentary pack, not an operational context pack. The separate `context`
command below supplies required readings, budget accounting and adopted-rule composition;
neither command establishes contribution authority.
YAML manifests have no body; their normalized inventory is in the graph.

## Configuration and private bindings

No configuration is required to try the read-only commands. For shared use, give the
documentation repository a stable logical ID, not its absolute checkout path:

```yaml
# .framework-memory/config.yaml — versioned, no product/component inventory
document_repository: platform-docs
classifications: [public, internal]
include_unclassified: true
exclude: []                         # root-relative path prefixes, not glob patterns
max_file_bytes: 2000000
max_total_bytes: 20000000
max_files: 5000
query_limit: 100
max_hops: 3
```

`local` is the single-document-repository default, not a federation ID. Current commands
accept one documentation root containing multiple products; federation of separate
documentation repositories is not implemented. Repository paths must never be identities.

Optional private bindings have this shape. `doctor` validates/counts them without opening
the repositories. Only the explicit `code` command observes code; paths never become
canonical identities or appear in exported configuration:

```yaml
# .framework-memory/local.yaml — NOT versioned
checkouts:
  repository:product:product-a:backend: /local/checkout
  repository:platform:access: /local/shared-checkout
```

Suggested additions to the **using project's** `.gitignore`, reviewed and applied by its
maintainer (the CLI does not edit it):

```gitignore
/.framework-memory/local.yaml
/_meta/memory/
```

Do not put this configuration in `.framework/`, which already has another job. Both
`.framework-memory` and `_meta/memory` are explicit scan exclusions even with
`skip_hidden: false`. Project exclusions extend the framework floor. Symbolic source
links are not followed, and symbolic output/configuration ancestors are rejected.

## Optional metadata: forward only

The artifact registry names optional properties; their nested types come from
`schemas/memory-contracts.yaml`. Generated artifact schemas remain self-contained. Existing
artifacts need no new fields, and immutable documents must not be retroactively enriched.

| Artifact | Optional metadata | Meaning |
|---|---|---|
| DEC | `applies_to: [component:platform:identity]` | Locate a constraint's subjects |
| ICG | `subjects: {SIG-001: [component:product:product-a:api]}` | Keep candidate → components; categories remain in routing/impacts |
| CHG | `targets`, `preserves` | References to affected objects and preserved constraints, not approval |
| ARC | `components` with `current` / `target` | Product component identity and locations |
| PLATFORM | `components` with `current` / `target` / `design` | Shared component identity, no phantom product |
| New SD | `components` with `design` only | Documentary memory before code/ARC exists |
| Manifest / PLATFORM `code` row | `zones: [{path: tests, kind: test}]` | Classification, not exclusion or observed coverage |

```yaml
components:
  component:product:product-a:api:
    current:
      section: current
      code_roots:
        - {repository: product.backend, path: src}
        - {repository: platform.access, path: adapters}
    target:
      section: target
```

`section` resolves a unique explicit marker or ATX heading title. Setext headings are not
supported. Repository aliases resolve in the declaring artifact's owning scope; a design
file outside a product directory uses full `repository:product:<product>:<key>` IDs. Paths
are relative to the repository root; `..`, absolute paths and backslashes are rejected.
Overlapping roots are retained, including across components; no single-owner shortcut.
Views remain separate. Responsibilities, alternatives and rationale stay in the prose.

Absent means unknown. An allowed empty list means declared empty for that field only.
Legacy DEC without `applies_to` remain searchable. A `supersedes` edge never removes the
older document or decides whether all its constraints expired. Read the relevant sections.
Unresolved metadata produces a partial graph with source-localized issues, not a guessed
target. `subjects` validates candidate declaration, scoped routing join, logical duplicates
and component resolution; it never fabricates component-level impact categories.

## Provenance and reproducibility

`memory-contracts.yaml` is the single relation vocabulary. Declared: `applies_to`,
`supersedes`, `derives_from`, `targets`, `preserves`. Derived only: `constrained_by`,
`affected_by`, `belongs_to`, `documents`, `realized_in`. Inverses retain their origin edge,
source ranges and versioned derivation rule. `affected_by` is navigation, not observed
damage; `realized_in` is a declared root mapping, not proof of implementation.

Source kind (`document`/`code`/`check`) and assertion method
(`declared`/`derived`/`inferred`) are independent. Confidence is valid only for inferred
claims; inferred claims are rejected from this documentary projection. Nodes and edges
carry source IDs, exact content hashes and inclusive line ranges. Metadata edges locate
the complete front-matter block, not a guessed field line. The snapshot records the
documentation commit when available, actual included bytes, effective selection policy,
framework version and generator source hashes. A hash is a revision, not a signature or
evidence of approval.

Canonical JSON is UTF-8, sorted keys, compact separators and a final LF. No wall clock,
machine checkout path, local binding or repository URL is inserted. File mtimes are not
identities. Input inventory/content/configuration are reread before a coherent result and
again before publication; concurrent changes fail explicitly. No dirty boolean substitutes
for bytes. Code/index/staged-state observations use a separate receipt described below.

All root-code nodes in the **documentary graph** retain `path_status: unresolved`,
`observation_status: not_requested`, `freshness: unknown`: local existence has not been
checked by the documentary builder. Observed states live in the code graph's bridge,
not in rewritten documentary declarations. A document's `current` freshness means these source bytes are the selected
snapshot, not that its claims about the product are up to date. `verified_code` remains
an attestation in the source, not a new observation by this CLI.

## Search, privacy and limits

Literal search is always available and uses the standard library. `--search-engine fts5`
opts into an ephemeral SQLite FTS5 index; `doctor` checks support. Its absence falls back
to literal search and is reported. FTS tokens are quoted, results are ranked and tied by
path, and the query does not accept SQL/FTS operators. Neither engine needs models or a
graph database. No external source code or dependency was incorporated in phase 2.

Classification and explicit exclusions are applied **before** indexing and export;
excluded bodies and names do not enter results. Defaults allow public/internal and
unclassified sources; use `include_unclassified: false` for a restrictive run. Parsing
classification requires reading selected candidate files locally. These filters are not
an ACL or a secret scanner: approved source bodies can themselves contain confidential
text or malicious instructions. Retrieved text remains evidence, not executable authority;
review classification before sharing a pack. The tool does not execute that text.

Product filtering narrows navigation within the already authorized source set. It is not
a security boundary: use configuration exclusions/classifications for that. Unqualified
legacy bindings are included conservatively. Scope-filtered queries can omit consumers
outside the selected product; they do not prove there are none. `belongs_to` traversal is
excluded by default to avoid expanding a local question into every document in a scope;
request a relation explicitly to include it. Limits/truncation are visible, and missing
matches mean only no match in selected documentation, never no consequences.

Operational context/impact CLI reports are described below. The seven existing skills
consume them through [operational-memory.md](operational-memory.md), the shared reading
and execution-scope reference. The separate opt-in PR authority/receipt gate is documented
in [contributions.md](contributions.md); exact release-set assessment is in
[release-evidence.md](release-evidence.md). Semantic retrieval and the optional viewer
remain outside this increment. No new skill,
release version, migration or provider installation is implied by enabling this CLI.

## Operational CLI — phase 4 engine

The engine is implemented independently of the editor. Common preamble, routing, the seven
skills and AGENTS/IMP templates now distinguish analysis, proposal and implementation
within an already approved mandate. Ordinary technical steps within that scope do not
require per-edit approval; new decisions, wider scope/cascades, immutable-body edits and
external permissions still require escalation. Reports themselves confer no authority.

```bash
python3 /path/to/framework/memory.py context --root /path/to/documents \
  --goal "Assess consequences for the selected product" --product product-a --skill cycle
python3 /path/to/framework/memory.py context --root /path/to/documents \
  --goal "Reconsider the rejected alternative" --reconsider --text-budget 60000
python3 /path/to/framework/memory.py context --root /path/to/documents \
  --goal "Inspect the selected mandate" --change CHG-001 --mode implement \
  --code-snapshot /path/to/documents/_meta/memory/code-snapshots/AFTER_ID
python3 /path/to/framework/memory.py impact --root /path/to/documents \
  --before /path/to/documents/_meta/memory/code-snapshots/BEFORE_ID \
  --after /path/to/documents/_meta/memory/code-snapshots/AFTER_ID \
  --change CHG-001 --direction dependents --hops 3 --limit 100
python3 /path/to/framework/memory.py readings \
  --pack /path/to/context.json --claims /path/to/reading-claims.json
```

All three commands emit JSON to stdout only; they do not publish reports, mutate product
documents, install/execute a provider or run project tests. If saving output, choose an
authorized non-source location such as the reserved runtime directory. Exit 1 means a
partial context/impact or incomplete reading report; exit 2 means unavailable/invalid
input. Impact without two explicit snapshots is unavailable, not an empty success.

### Context inputs and completeness

`--mode` records analysis/proposal/implement intent; it does not grant permission.
`--change` selects a unique CHG ID or exact source path. The engine joins its qualified
candidates with the ICG, reports missing mandatory mandate sections and an architecture
classification lacking a cited accepted DEC. This is a bounded prerequisite diagnostic,
not exhaustive authorization or cascade validation. `mandate.authorization` is always
`not-verified`: an approved status in a branch is not trusted-base evidence.

Repeated `--product` scopes primary evidence; omission includes all selected products.
Shared declared consumers can widen the evidence set without altering the selected mandate.
Scope selection is not an ACL: classification/configuration exclusions still run first.
The current policy conservatively includes scoped documents rather than guessing semantic
relevance. This prioritizes constraints over compactness and can leave many readings due.

`required_sources` preserves exact source IDs/hashes/ranges, reasons and optional graph
paths even at `--text-budget 0`. The budget counts delivered text characters, not tokens
or total JSON size. `--node` adds bounded documentary exploration, never ranks mandatory
sources out. Empty graph paths have a conservative scope-inclusion reason; they are not
invented relationships. `--hops` cannot exceed the configured bound.

Applicable candidates include historical/superseded DECs with no `applies_to`.
Decision/Consequences and any Review condition are delivered as full localized sections;
`--reconsider` also requires Alternatives. Missing/ambiguous sections stay explicit,
without a historical backfill. The parser recognizes template headings, explicit matching
markers and the documented Italian aliases in `context.py`; other headings require manual
localization. Status and source section inventory remain visible. The agent still decides
actual applicability after reading; the engine does not prove semantic understanding.

Unlike `query`, `context` can include entire selected documentary files, including their
front matter. Treat a pack as sensitive as those source files; local configuration is
excluded, but secrets mistakenly placed in allowed source content are not redacted by a
secret scanner. Do not share packs across different access scopes.

### Adopted rules and source identity

`framework_sources.py` reads the project's `framework_version`/`framework_commit`.
A full pin resolves source blobs in the supplied local framework checkout, without fetching,
checking out or executing historical code. `--framework-root` explicitly chooses that
local source repository. A pin/version mismatch never falls back to today's rules.
A version without a commit is `version-only-unverified`; working-tree instruction hashes
remain explicit. Missing adoption information or rule files keeps the pack incomplete.

The framework's FRAMEWORK/preamble/routing table and optionally the selected skill are
separate sources from product documents. Adopted version/commit and actual source hashes
identify these rules; `runtime` separately identifies the generator. Re-reading guards
against concurrent changes. Deterministic report IDs contain no clock or checkout path.

`--code-snapshot` requires a published manifest/graph bundle, validates its hashes and
requires the same documentary snapshot. It never claims live freshness: outer status is
`not-rechecked`, while observation fields describe the captured snapshot. Unsupported,
partial, missing and unselected repositories remain gaps. The graph does not contain code
bodies, so code reading requirements remain deferred at their repository/path/hash.

### Reading declarations and hypotheses

A claims file has this shape, using values from the actual pack after source reading:

```json
{
  "context": "CONTEXT_ID",
  "readings": [
    {
      "requirement": "reading:REQUIREMENT_ID",
      "revision": "sha256:SOURCE_HASH",
      "start_line": 10,
      "end_line": 28
    }
  ]
}
```

IDs/hashes above are placeholders. The reader checks the context identity, full requested
range, revision, unknown/duplicate claims and missing sections. It can accept a caller's
declaration of an externally read deferred source; it cannot independently verify that
reading. Reports say `declared-complete` or `incomplete`, never understood/verified.
Neither delivery nor claims modify `last_review` or replace a person's attestation.

`--hypotheses` accepts the generated `hypotheses.v1.json` format: a claim with inferred
provenance, rationale and in-scope source ranges. Optional confidence is valid only on
inferred assertions. These remain separate hypotheses, never authoritative graph edges.

### Structural comparison

`impact` compares captured byte hashes and Git inventories on both sides, and traverses
resolved direct provider edges at file granularity. Default direction is reverse/dependents;
dependencies/both are explicit alternatives. Cycles are visited once; node/hop limits
are reported. Cross-repository nominal names never acquire invented bindings.

The after bundle must match current documentation. A baseline may use earlier documentation
only in the same logical document repository. Phase-four code receipts add that namespace
to their input identity; regenerate earlier receipts that lack it. Generator/source changes
already require regenerated snapshots. No adoption, historical artifact or release version
is changed automatically.

Predicted candidates/categories/subjects and targets/preserves remain separate from observed
file/root/dependency matches. Repository targets map through declared roots. Categories stay
candidate-level, not automatically component-level. Overlapping roots and current/target/design
remain distinct. Comparison reports unexpected components and missing matches for review,
not functional regressions or successful preservation. Unsupported bytes, unavailable
repositories, unresolved edges and incomplete mappings remain uncertainties.
Consequently structural impact reports are partial even for a usable comparison: no
runtime/semantic completeness, test success, current deployment or absence-of-impact claim.

## Optional code observer — phase 3

`code` is an explicit, separate operation. It does not turn on when running `query` or
`build`. It requires private `local.yaml` bindings to repositories already declared in
the selected documentation. A manifest's path hint is not automatically opened, a
checkout basename is not an identity, and a binding cannot create an undeclared repository.

```bash
# Read-only preflight: checks the operator-supplied binary hash, not a full sandbox run.
python3 /path/to/framework/memory.py doctor --root /path/to/documents --enola /path/to/enola

# Observe selected worktree bytes in temporary isolation, without publishing a snapshot.
python3 /path/to/framework/memory.py code --root /path/to/documents \
  --repository repository:product:product-a:backend --enola /path/to/enola --dry-run

# Publish observations for all declared repositories with explicit local bindings.
python3 /path/to/framework/memory.py code --root /path/to/documents --enola /path/to/enola

# Observe exactly the full commit object ID explicitly chosen by the operator.
python3 /path/to/framework/memory.py code --root /path/to/documents \
  --repository repository:product:product-a:backend --source git \
  --revision "$CHOSEN_COMMIT_ID" --enola /path/to/enola
```

The last command needs a full 40- or 64-hex commit object ID, not `HEAD`, a tag or a
branch. It supports a bare repository or a checkout with missing files without checking
anything out. Worktree observation never silently switches to Git objects. Repeated
`--repository` selects multiple repositories; omission selects all declared repositories.
A commit selection is limited to one repository so the same hash is not blindly applied
to different histories.

By default, the worktree selection covers tracked files and records nonignored untracked
paths as excluded. `--include-untracked` explicitly includes untracked Python source.
Git-ignored untracked files are not inventoried. All tracked inventory entries are recorded,
but only `.py` bytes go to this provider profile: other languages and JSON Schema are
`unsupported`, not irrelevant and not evidence of no impact. JSON Schema remains a
documented contract input, not an invented code/lineage extractor.

Captured byte hashes, selected commit, staged index entries, inventory and untracked
policy identify the observation. Staged and unstaged changes are distinct; observing a
commit is not observing the current working tree. File symlinks, submodules, missing files,
merge conflicts and bounded-read failures are not silently traversed or repaired.
The limits are 5,000 inventory entries, 2 MB per Python source and 20 MB of Python bytes.
Narrow the repository selection or review a limits change; the tool never truncates a
successful code snapshot. Code roots map components, not the privacy boundary of a scan:
the selected repository's supported source is inspected, including code outside a root.

### Supported provider unit and isolation

`providers.lock.json` is authoritative for release, commit, format/extractor version,
platform and archive/executable checksums. Obtain the locked release separately, verify
the archive checksum, retain its notices, then supply the extracted executable via
`--enola`. No command downloads, installs, upgrades or searches PATH for Enola. An absent,
changed or unrecognized executable returns `unavailable`. Dependencies are optional:
the documentary core remains usable without Enola, bubblewrap or prlimit.

The initial supported unit is **the pinned Linux x86_64 executable plus this adapter's
Python 3.12 grammar guard**, on Linux/WSL with CPython >=3.12. Other platforms/languages
are not certified by this phase. The CPython runtime version is an input because parser
behavior can differ between versions. The real conformance run recorded in `PHASE-3.md`
used the stated host runtime; CI configuration alone is not a recorded Python 3.12 run.

This qualification matters: the unmodified candidate recovered an invalid Python file
and claimed `parse_errors: 0`. The adapter uses `ast.parse`, without imports or execution,
to reject malformed/unsupported Python syntax before extraction. Invalid files remain in
coverage with `python-syntax-guard`; their symbols are not projected. If valid files remain,
the result is partial. If none remain, it is unavailable. This is a syntax diagnostic,
not another extractor or a claim to validate runtime semantics.

Only captured Python files are copied into a disposable repository. Repository-local
provider configuration, agent rules, Git hooks, Git metadata and credentials are not
copied. A trusted configuration disables additional providers, explainers, renderers,
incremental caches, update checks and prompts. Bubblewrap uses new namespaces including
network isolation, an empty private HOME, read-only sources and a separate writable output
mount. Only the verified binary copy is executed. There are process/output bounds and
prlimit file-size/CPU/file-descriptor limits; no unsafe nonisolated fallback. This is a
local isolation boundary, not a claim of protection against every kernel/parser exploit.

### Separate graph, explicit evidence

`code` emits the complete JSON graph; default publication is exclusively under
`_meta/memory/code-snapshots/<id>/`, containing `code-graph.json` and `manifest.json`.
`--dry-run` still runs temporary isolation but does not publish. Same-filesystem atomic
publication, conflict handling and immutable existing-output checks match documentary
snapshots. The output does not bundle code bodies or private bindings, but names, literal
annotations and source paths can still be sensitive: do not treat it as anonymized.

The schema is generated from `memory-contracts.yaml`. It keeps:

- Qualified repository identities, captured file revisions and measured source ranges.
- Nodes for files, modules, definitions, dependencies and reference records.
- Direct `calls`, `imports`, `declares`, `implements`, `instantiates`, `names` edges, plus
  rule-derived file `contains` edges. No transitive impact edges or `impact()` provider API.
- `target_id` resolution only; a missing ID remains unresolved even if one nominal match
  exists. A missing target ID in the selected fact set remains visible. Cross-repository
  symbol linking is not implemented; a declared repository/root mapping is not a symbol binding.
- Original provider records, including duplicates carrying distinct positions/properties.
  Exact duplicate records retain occurrence counters; node identities merge only the same
  repository/provider/kind/name/file. Each edge points back to its own record evidence.
- Structural facts separated from raw provider annotations and disabled-explainer insights.
  Nonstructural records/relations remain evidence and are reported as not projected.
- A bridge to documentary root/component IDs, retaining overlapping roots and separate
  `current`/`target`/`design`. A path match is never proof that target architecture exists.
- Explicit `path_status`, `observation_status`, `freshness`, per-file coverage and problems.
  Zone classifications can overlap and never cause automatic exclusion.

Receipt format, writer/extractor versions, record IDs, snapshot identity, artifact hashes,
record counts, census consistency and source boundaries are validated before graph creation.
Missing/corrupt receipt, unsupported format or inconsistent outputs are rejected as
`unavailable`, not downgraded to a convincing empty graph. Wall clock, duration and private
receipt paths are excluded from canonical output. Hashes attest byte identity, not truth.

### Verification and dependency changes

```bash
python3 -B -m unittest discover -s tests/memory -v
python3 -B tests/memory/enola_conformance.py --enola /path/to/enola
python3 schemas/generate_memory.py --check
python3 third_party/inventory.py --check
python3 tests/selfcheck.py
```

The offline suite requires no provider installation or network. Real conformance is an
explicit additional gate, not an implicit CI download and not a skipped test presented
as passed. It uses only synthetic inputs. Updating the lock requires repeating both suites,
reviewing the output-contract/profile delta and regenerating the integration inventory.
`third_party/manifest.yaml` records reviewed sources and license scope. No source or binary
was copied from Cognee/Enola into this framework. Its generated inventory is not a complete
transitive dependency/license SBOM. No additional graph database, model or framework
runtime dependency was introduced.
