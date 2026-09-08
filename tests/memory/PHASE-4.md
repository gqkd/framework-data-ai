# Product Memory phase 4: operational context and seven-skill integration

Implementation record, 2026-09-08–09. Starts from phase-three commit `241850c` on
`codex/product-memory-phase-0`. The engine checkpoint is `36f8240`; this follow-up
integrates it into common instructions, templates and the seven existing skills.
The specific bounded-execution rule was applied only after explicit user approval.

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

## Seven-skill integration

The shared procedure lives in `references/operational-memory.md`. Following the
`skill-creator` guidance, the seven entry points retain their responsibilities and link
to that procedure instead of acquiring seven copies or an eighth skill:

| Skill | Consumption point |
|---|---|
| `start` | Existing-product assessment and ingestion proposal after the control plane exists; document-only fallback |
| `requirement` | Conflict checks against existing constraints, historical decisions and consumers |
| `resolve` | Evidence and complete alternatives when reconsidering a choice |
| `cycle` | Candidate classification, approved-CHG brief, explicit before/after impact and outstanding prerequisites |
| `audit` | Requested semantic/impact review; heading triage is not complete decision reading |
| `release` | Source discovery without replacing frozen evaluation, repository checks or deployment authority |
| `business` | Cross-document assessment without promoting hypotheses to commitments |

Preamble, routing, SKILLS, README and AGENTS/IMP templates distinguish analysis, proposal
and implementation. Ordinary technical edits/tests inside a scope already approved by
the project's process no longer require per-step approval. New documentary
classifications/cascades, new decisions, scope expansion, immutable-body edits, required
open choices and external permissions retain their escalation rules.

Human `last_review` remains a proposal, not an automatic reading-report/scaffolding
update. The previous conflicting summaries in SKILLS/start/AGENTS were aligned to the
existing common rule. Reports link sources instead of copying authoritative facts, and
IMP gains optional report/snapshot references, not new mandatory metadata.

Every selected skill and the shared guide remain required readings even with zero text
budget. Changed adopted guide bytes invalidate the context identity independently of
the product snapshot. If adopted rules reference a missing guide, its absence becomes
an explicit gap. Historical pins that do not reference it do not acquire today's guide.

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
| `tests/memory/test_operational.py` | 35 operational/integration tests on disposable synthetic workspaces |
| `tests/memory/test_references.py` | Operational CLI from an independent Git export |
| `references/operational-memory.md` | Shared procedure, required reading, evidence and execution boundaries |
| `references/preamble.md`, `references/routing-table.md`, `SKILLS.md` | Analysis/proposal/bounded implementation and human-attestation alignment |
| Seven `skills/*/SKILL.md` | Concise context consumption at existing decision points |
| `templates/AGENTS.md`, `templates/IMP.md` | Execution-scope guidance and optional context/impact references |
| `tests/selfcheck.py` | Include the shipped operational CLI in the existing skill-flag reference check |
| `README.md`, `references/product-memory.md`, test README, this report | Usage, limits, generated catalog synchronization and phase handoff |

Python modules above live under `src/framework_data_ai/`. No external library/source
was added: existing PyYAML/jsonschema and standard-library mechanics are reused. The
pinned optional code provider and its isolation profile remain the phase-three unit.

## Executed verification

Host: Linux/WSL, Python **3.14.4**. Results measured on this implementation:

| Gate | Result |
|---|---|
| `python3 -u -B tests/selfcheck.py` | Passed, including **159 offline memory tests**, after generated README synchronization |
| `python3 -B -m unittest discover -s tests/memory -p test_operational.py -v` | **35 passed** |
| `skill-creator/scripts/quick_validate.py`, each skill directory | **7 passed** |
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

During integration, skill validation found two pre-existing descriptions above 1,024
characters. The audit/requirement descriptions were shortened while preserving their
scope. The first full run then passed all 159 offline tests but failed the generated
README cost-region check; the existing schema/catalog generator regenerated that region.
No acceptance criterion, warning/error severity or gate was weakened.

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

## Handoff and subsequent work

The prior partial report and rejected instruction attempt are preserved in `36f8240`.
The user then explicitly approved the bounded-execution change; this follow-up applies
it, without bypassing the earlier refusal or extending it into new scope.

This phase supplies a usable editor-independent engine and seven-skill consumption
procedure; the final framework gate passed. Phase-four implementation is complete.
It is not a release, a migrated product installation, a measured comprehension
result or certification of the external-contributor path.

Phase five remains separate: trusted documentary base, independent mandate/PR authority,
relevant multi-repository evidence and secure contribution checks. Phase six owns the
release-set/deployment distinction and closure of implemented versus verified. Existing
release/PR behavior is not silently advertised as enforcing those future gates.
