# Optional offline graph viewer

The viewer is a navigation aid, not retrieval, a graph database, an approval gate, or a
second source of truth. It helps inspect relationships and their evidence across the
products selected by one documentary workspace. It does not federate independent
documentary repositories or observe customer databases.

## Export and open

From a complete framework checkout/export and the same Python environment used for memory:

```bash
python3 /path/to/framework/memory.py view --root /path/to/documents --dry-run
python3 /path/to/framework/memory.py view --root /path/to/documents
# Optional: explicitly supply an already captured code bundle; no provider is started.
python3 /path/to/framework/memory.py view --root /path/to/documents \
  --code-snapshot /path/to/documents/_meta/memory/code-snapshots/<id>
```

The JSON response names `_meta/memory/views/<id>/index.html`. Open that file in a
JavaScript-enabled browser; no server, Node runtime, installation, CDN, account or network
is required. `--hypotheses FILE` accepts the existing source-backed inferred contract.
A missing optional input is not silently discovered. `--dry-run` performs rendering and
validation but creates no output. Partial documentary coverage retains the normal exit 1;
invalid input/export returns 2. Code availability is reported separately and never becomes
a claim of no impact.

## What the interface means

| Surface | Meaning / boundary |
|---|---|
| Documents | Canonical documentary nodes and relations, with their original provenance |
| Code | Separate captured structural graph, including unresolved edges in the accessible relation list; no nominal target guessing |
| Mapping | Dashed **presentation-only** component-to-observed-file links, checked against documentary root declarations; not proof of implementation |
| Hypotheses | Separate, explicitly supplied inferred annotations and source citations; never constraints or generated canonical edges |
| Inspector | Independent source kind/assertion method, rule and evidence, observation state, exact record and source locations |
| Source buttons | Full captured documentary text, with line numbers and content hash; code bodies are not included and no live file is opened |
| Connection trace | Deterministic bounded traversal of displayed edges, forward/reverse marked; not causality, risk assessment or impact analysis |

Scope/repository, node kind, assertion, current/target/design, relation and text filters
compose. A declared-edge filter retains its endpoints even when the nodes themselves are
derived. Current/target/design on code files describes a **matching declared root**, not
a code lifecycle state; other code entities are not assigned a view by inference.
The selectable node/relation lists provide a keyboard alternative to the canvas.

At most 250 nodes and 1,500 relations among displayed nodes are rendered. Filtering is
applied before the node cap. Counts and truncation are explicit; an empty view or missing
path only describes that filtered/bounded view. Hypotheses are inspected independently;
they are not automatically attached to a component on semantic similarity.

## Revision and privacy boundaries

- Code inputs must be coherent published bundles in the same documentary namespace.
  Their checksums establish internal integrity, not producer authenticity.
- Exact documentary snapshot equality is required for mapping. If the snapshots differ,
  code remains independently inspectable with a prominent warning and no presentation
  bridges. This does **not** loosen the context command's stricter revision matching.
- A compatible bridge must also match the actual component, root, repository, path,
  view and declaration provenance. Self-consistent but forged declarations are rejected.
- Live code freshness is always **unknown / not rechecked** in this viewer. Captured
  observation states remain visible as historical evidence.
- Documentary scan/classification exclusions apply before export. All selected documents'
  text is embedded, not just the currently visible nodes. Code names, paths, annotations
  and evidence can be sensitive too. **An offline file is not an anonymized or safe-to-publish
  file.** Review its scope before copying/sharing it.
- No customer-data ingestion, arbitrary path opening, clickable untrusted URLs, remote
  resources, telemetry, browser storage, provider execution or Markdown HTML interpretation.
  Source content is rendered as text. Embedded JSON escapes HTML terminators; executable
  scripts are CSP hash-allowlisted and network connections are disabled.
- Export is capped at 25 MB, otherwise it fails rather than silently omitting sources.
  Narrow selected input or review the limit deliberately.
- The content-addressed HTML plus manifest is atomically published only under the ignored
  memory directory. Existing mismatching output is never overwritten. The identity covers
  the selected graphs, hypotheses, source text, framework UI assets, licenses and dependency
  inventory. No wall clock, absolute local bindings or display coordinates are canonical.

## Technology and maintenance

Use the unmodified **Cytoscape.js 3.34.3** browser renderer (MIT), fixed to its source
commit and npm tarball integrity in `third_party/manifest.yaml`. The copied files are only
the minified renderer and LICENSE, with SHA-256 checks. The HTML carries its MIT license,
the framework license and notice. `third_party/inventory.py --check` checks vendored bytes;
the export checks again before publication.

Primary upstream: [repository](https://github.com/cytoscape/cytoscape.js/tree/v3.34.3),
[API documentation](https://js.cytoscape.org/),
[pinned license](https://github.com/cytoscape/cytoscape.js/blob/v3.34.3/LICENSE).
The acquisition used `npm pack cytoscape@3.34.3 --ignore-scripts`; no hooks or application
integration were installed. npm tarball integrity was checked, not its provenance signature.
No transitive binary SBOM, vulnerability audit or legal clearance is claimed.

Native HTML/CSS and a small pure JavaScript presentation model avoid a frontend framework
or runtime graph service. Reusing an unmodified renderer keeps upstream upgrades separable
from the framework's authority/provenance logic. The tradeoffs are a larger self-contained
HTML, maintenance of the asset pin/CSP tests, canvas accessibility requiring an alternate
list, and bounded views rather than a whole-platform live dashboard.

The feature is **optional and removable from a release** without changing context, impact,
contribution or release semantics. To omit it, omit the CLI branch/viewer module/assets and
its manifest entry, docs, generated schemas and viewer-only tests; regenerate the inventory.
Simply deleting its assets makes `view` fail closed, while the existing Python core keeps
working. No product document migration, new mandatory metadata or eighth skill is required.

## Verification

```bash
python3 -B -m unittest discover -s tests/memory -p test_viewer.py -v
node --test tests/viewer/model.test.cjs
python3 schemas/generate_memory.py --check
python3 third_party/inventory.py --check
python3 tests/selfcheck.py
```

Node is a **development/CI test** requirement only, not an export/runtime requirement.
The separately pinned CI job runs model and actual renderer headless tests without npm
installation. Browser QA is explicit, not an automatic browser download: with already
installed Playwright and Edge, run `tests/viewer/browser.cjs` against a localhost server
serving **only synthetic exports**, supplying a screenshot output directory. Select the
installed package with `PLAYWRIGHT_MODULE` and optionally browser channel with
`VIEWER_BROWSER`. The script exercises real controls, offline interactions, keyboard
selection, source inspection, 320px layout and 200% text enlargement. Execution evidence
belongs in `tests/memory/PHASE-8.md`, not in a claim that an agent understood the code.
