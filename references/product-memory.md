# Documentary memory — phase 2

This is an opt-in development aid, not an authorization, autonomous agent, semantic RAG
service or second source of truth. Markdown/YAML remain authoritative. The CLI projects
declared relationships and provides source-backed text queries. It does not change a
product's documents, approve a CHG, run code, install hooks or contact a database.

```text
project Markdown/YAML --> shared parser/resolver --> documentary graph
                               |                         |
                     content-hashed snapshot       query + source bodies

declared code roots --[not observed in phase 2]--> future separate code graph
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
invalid request. Code inspection is always `not_requested` in this phase. An available
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
This is a documentary pack, **not** phase 4's operational context pack: mandatory reading,
budget accounting, framework-rule composition and contribution authority are not claimed.
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

Optional private bindings have this shape. Phase 2 validates/counts them in `doctor` but
does not open them or include them in snapshots, queries or search:

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
for bytes. Detailed code/index/staged-state receipts belong to phase 3.

All root-code nodes currently have `path_status: unresolved`,
`observation_status: not_requested`, `freshness: unknown`: local existence has not been
checked. A document's `current` freshness means these source bytes are the selected
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

Code providers, operational context/impact reports, stricter PR authority, release
evidence, semantic retrieval and the optional viewer remain later phases. No new skill,
release version, migration or provider installation is implied by enabling this CLI.
