# Product Memory phase 8 — optional offline graph viewer

Execution record for 2026-09-09/10. Framework-only work on
`codex/product-memory-phase-0`, starting from phase 7 commit
`a33883998508a9850e4200e8887eaa24f2384cf9`. No actual product/client sources,
code repositories or databases were accessed. Browser/provider inputs were synthetic.

## Implemented

| Surface | Result |
|---|---|
| `memory.py view` | Explicit local export; optional captured code/hypotheses; read-only dry-run; no observer invocation |
| `memory/viewer.py` | Validated source/provenance projection, exact revision checks for mapping, dependency checksums, escaped JSON, CSP script hashes |
| `snapshots.py` | Atomic content-addressed `views/<id>/index.html` plus manifest; existing snapshot namespaces keep JSON-only filenames |
| `assets/memory-viewer/` | Native controls, distinct document/code/hypothesis views, checked presentation mapping, filters, source inspector, bounded directional connection trace |
| Source navigation | Embedded selected documentary text with line numbers/hash; code locations/provider records without code bodies or live file opening |
| Rendering | At most 250 nodes/1,500 relations, explicit limits/absence warnings, selectable lists for keyboard access, responsive canvas |
| Contract | Two generated schemas from `memory-contracts.yaml`; no new product artifacts or mandatory product metadata |
| Dependency | Unmodified Cytoscape.js 3.34.3 minified renderer + MIT LICENSE only; exact source commit, npm integrity and file hashes in inventory |
| Notices | MIT license plus framework Apache license and NOTICE embedded in each HTML |
| Documentation/version | `references/memory-viewer.md` owns usage/tradeoffs; README, framework/adoption/runtime references aligned; 3.8.0 source version, not a published release |
| Tests/CI | Python contract/regression tests; separate pinned Node model/renderer job; explicit synthetic browser runner/generator; no browser/npm install in core CI |

The Sites capability guidance kept the implementation in the existing repository, as a
local working surface with native controls and a small JavaScript model. No frontend
framework, Sites registration/hosting, eighth skill or background service was introduced.

## Verification before the final committed-source gate

- Sixteen new viewer Python tests passed, including deterministic immutable output,
  source filtering, provenance bounds, forged/mismatching code bridges, XSS terminators,
  CSP hashes, asset tampering, symlink/size rejection and no product writes.
- Eight Node tests passed, including actual pinned Cytoscape headless use, namespace
  separation, declared-edge endpoints, traversal direction and bounded display.
- Twenty adoption tests passed in 12.359 s. New cases compare a complete phase-7
  3.7.0 export with proposed 3.8.0 and prove that documentary commands still work when
  browser assets are omitted; `view` then fails closed. The existing complete 3.6.3
  baseline/eight-scenario comparisons remain intact.
- Nine real pinned Enola conformance tests passed in 7.765 s, synthetic inputs only.
  The adapter and provider lock were not changed.
- The first full offline suite ran 257 tests in 107.334 s and found one obsolete assertion:
  the phase-3 inventory test expected no copied source of any kind. It now asserts that
  **only the optional Cytoscape renderer** is incorporated, while preserving exact
  Enola-lock equality. No frozen acceptance finding, severity or provider rule was relaxed.
- Artifact generator, 23 memory schemas, inventory/constraints and whitespace checks
  passed. Runtime is isolated CPython 3.14.4; Node 22.22.1. Python 3.12 is configured
  in CI, not locally exercised here.

## Browser evidence

Final UI exercised on installed Edge 152.0.4191.62 through existing Playwright,
using `tests/viewer/demo.py` and `tests/viewer/browser.cjs`. The app browser control
helper could not initialize, so no claim is made that its interactive automation worked.
The user approved browser testing; the alternative used isolated headless browser contexts.

Three synthetic cases passed: documentary-only; real-provider code snapshot with compatible
mapping and an explicitly inferred annotation; changed documentary revision with the old
code snapshot and mapping disabled. Code coverage in the latter two is correctly **partial**,
not promoted to complete. Checks covered real controls, filters, keyboard source selection,
connection trace, source inspection, disabled options, 320px layout, 200% text enlargement,
and interactions after going offline. No page errors or external requests were observed.

Desktop, mapping and mobile screenshots were visually inspected. That inspection exposed
overlapping long labels and canvas overflow after resize; compact canvas labels/force layout,
container clipping and resize fitting corrected them. Full identifiers remain in the list
and inspector; dense overviews still need zoom or narrower filters. This is not a formal
accessibility audit or a large-graph performance benchmark.

A separate `file://` test started with network offline, rendered the self-contained HTML,
selected the hypothesis containing a synthetic closing-script injection, and confirmed it
remained text with no execution or page errors. No actual confidential document was exported.

Temporary evidence: `/tmp/framework-viewer-phase8-release/preview/` contains the three
HTML/manifest pairs; Windows temporary `framework-viewer-phase8-release/` contains screenshots
and the offline-file check copy. They are not part of the public framework distribution.

## Boundaries and handoff

The optional renderer is removable independently of retrieval/impact/contribution/release
semantics. The HTML contains all selected documentary text, not just visible nodes:
local does not mean anonymized. Do not publish real exports without scope/privacy review.
Code snapshots are internally coherent, not producer-authenticated or live re-observed.
Mismatched snapshots can only be viewed separately. Mapping and graph paths are navigation,
not proof of implementation, causality, understanding, approval or absence of impact.

Cytoscape acquisition verified npm SHA-512 and copied only the two inventoried files,
without install scripts/hooks. This is not signature verification, a complete SBOM,
vulnerability audit or legal clearance. No graph database, embeddings, federation,
semantic RAG, automatic inferred links or customer-data lineage was added.

No product adoption, plugin reinstall, tag, push/publish, remote-protection change,
remote CI execution or deployment was performed. Final selfcheck must run on the committed
implementation because the framework's version-migration check requires committed bytes;
its measured outcome will be recorded below after execution.
