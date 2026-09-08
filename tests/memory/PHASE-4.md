# Product Memory phase 4: operational engine, integration pending

Implementation record, 2026-09-08. Starts from phase-three commit `241850c` on
`codex/product-memory-phase-0`. **This is a partial phase, not a completed phase-four
handoff.** The engine and its gates are implemented; changes to common instructions,
templates and the seven skills were not applied.

Only the framework was changed. No product/client documents, historical artifacts,
production data, release version, remote configuration, hooks or provider installation
were changed. No remote push or product migration.

## Implemented

```text
adopted local framework version / pin ----> separate rule sources + hashes
                                              |
document snapshot + scoped graph ----------> context
                                              |
                               required sources independent of text budget
                               included / deferred / missing
                                              |
actual caller reading declarations --------> reading report
                               declared-read / outstanding, never understood

CHG + ICG + candidate subjects ------------> predicted impact
explicit before / after code bundles ------> structural differences
                                              |
                               bounded direct-edge traversal on both sides
                               component / repository / current-target-design
                                              |
                               differences to review + uncertainties
```

The context engine conservatively retains scoped documents, historical/superseded
decisions and shared declared consumers. It localizes Decision/Consequences/Review
condition and requires Alternatives on reconsideration. Required sources have hashes,
line ranges, reasons and graph paths when available; truncation cannot delete a reading
obligation. Classification-filtered sources remain unassessed and are not exported.

Framework rules come from the adopted local commit when pinned, not silently from the
runtime version. Missing pins/rules and version-only working-tree use are visible gaps.
The generator and adopted rules have separate identities. Code graphs are separate
explicit inputs; no provider, project test, clone or installation is invoked by context,
impact or readings.

Impact compares captured bytes and Git inventories, retains removals/overlapping roots
and traverses direct resolved dependencies with direction/edge provenance. Missing or
unselected repositories, unsupported bytes, unresolved edges and mapping/traversal gaps
cannot become no-impact conclusions. Categories remain attached to candidates. Repository
targets are projected through their declared roots before component comparison.

## Files

| File/group | Responsibility |
|---|---|
| `memory/context.py` | Conservative source assembly, mandate/ICG diagnostics, reading declarations |
| `memory/framework_sources.py` | Adopted version/pin resolution and instruction-byte guards |
| `memory/impact.py` | Predicted vs structural comparison, cycle-safe bounded traversal |
| `memory/operational_io.py` | Bounded strict JSON and bundle/report coherence checks |
| `memory/cli.py` | Read-only `context`, `impact`, `readings` commands |
| `memory/code_graph.py` | Add logical documentary repository to code receipt inputs |
| `schemas/memory-contracts.yaml` and five generated schemas | Context/impact/hypothesis/reading contracts |
| `tests/memory/test_operational.py` | 32 operational engine tests on disposable synthetic workspaces |
| `tests/memory/test_references.py` | Operational CLI from an independent Git export |
| `references/product-memory.md`, test README, this report | Usage, limits and partial-phase state |

Python modules above live under `src/framework_data_ai/`. No external library/source
was added: existing PyYAML/jsonschema and standard-library mechanics are reused. The
pinned optional code provider and its isolation profile remain the phase-three unit.

## Executed verification

Host: Linux/WSL, Python **3.14.4**. Results measured on this implementation:

| Gate | Result |
|---|---|
| `python3 -B tests/selfcheck.py` | Passed, including **156 offline memory tests** |
| `python3 -B tests/memory/enola_conformance.py --enola <already-present-pinned-binary>` | **9 passed**, isolated synthetic sources |
| `python3 -B schemas/generate_memory.py --check` | 12 schemas, 0 out of date |
| `python3 -B third_party/inventory.py --check` | Current; no added dependency |
| `git diff --check` | Passed |

The new tests exercise document-only operation, mandatory-source budgets, rejected
alternatives, historical decisions, missing/ambiguous sections, pin mismatch/no fallback,
concurrent rule changes, source filtering, qualified ICG joins, scoped inferences,
reading-claim tampering, bundle corruption, missing code, namespace mismatch, partial
repository selection, file removal, overlapping views, direct-call propagation, cyclic
truncation, CLI read-only behavior and portable outputs. An earlier fixture typo and the
missing unconditional hop-bound check were corrected before the passing run.

Frozen fixture meaning, acceptance criteria and comprehension questions were not weakened.
No model-based comprehension/skill evaluation was run. No native Windows code-provider
certification or actual Python 3.12 execution is claimed by a CI declaration.

## Limits and compatibility

- Reports are derived JSON on stdout, not new mandatory product artifacts or durable memory
  facts. Existing `query` semantics and product schemas remain unchanged.
- Required readings can be numerous: conservative retrieval is not semantic applicability
  analysis. Text budgets count delivered characters, not tokens or total JSON overhead.
- A caller-reported complete reading is not independently verified reading, comprehension,
  human `last_review`, task authorization or production evidence.
- CHG/ICG checks are bounded diagnostics. `authorization` stays `not-verified`; the
  trusted-base gate and command execution receipts still belong to phase five.
- Code bundle hashes establish internal coherence, not producer trust/current freshness.
  Source code is not bundled; code readings remain due. Unsupported worktree bytes may
  be unobserved even when Git inventory is unchanged.
- Impact after/context requires the current documentary snapshot. Earlier before snapshots
  must carry the same logical documentary namespace. Regenerate pre-phase-four code
  receipts lacking that input; the generator fingerprint already invalidates old snapshots.
- No inferred relation becomes a constraint, and no absent structural match establishes
  preservation, no consumers or no runtime/semantic consequences.
- No new dependency, graph database, embedding/model, semantic RAG, viewer or eighth skill.

## Pending approval and remaining phase-four work

The execution approval system rejected the proposed instruction patch, including after
the approved plan's exact phase-four scope was supplied as evidence. It requires explicit
user confirmation for the specific rule permitting ordinary technical steps inside an
already approved mandate without approval per edit/test.

The patch was **not applied**. In particular, `references/preamble.md`,
`references/routing-table.md`, `SKILLS.md`, the seven `skills/*/SKILL.md` files and
`templates/AGENTS.md`/`templates/IMP.md` remain unchanged. No workaround was used.
The previously noted disagreement about automatic `last_review` updates in some
instructions/templates is therefore also still pending.

After explicit confirmation:

1. Add the shared operational-memory reference and concise consumption points in the
   seven existing skills, preserving their routing and responsibilities.
2. Implement the approved distinction between analysis, proposal and bounded execution;
   preserve escalation for new scope/cascades, open choices, immutable-body edits and
   external permissions.
3. Align review-date instructions to the existing human-attestation rule and add the
   context/impact references to AGENTS/IMP templates without new mandatory fields.
4. Validate the changed skills, rerun all framework gates and review the instruction diff.
   Only then mark phase four complete and proceed to phase five.
