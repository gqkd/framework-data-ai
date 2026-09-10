# Product Memory: acceptance tests and scoped core

This directory preserves the phase-zero baseline and tests the scoped core, documentary
memory, the separate code observer, operational engine, contribution and release gates.
Historical reports are in `BASELINE.md` and `PHASE-1.md` through `PHASE-8.md`.
The current phase handoff is `PHASE-9.md`: operational qualification and observed defects.
No query or context pack is a task authorization.

Run the deterministic suite from the framework checkout:

```bash
python3 -B -m unittest discover -s tests/memory -v
```

`tests/selfcheck.py` runs the same suite. Behavioural questions live in
`evals/behaviour/memory/cases.yaml`; these are specifications, not recorded model results.
All products, repositories, documents and code in these fixtures are synthetic.

## Inputs and their ownership

- `evals/fixtures/generators/memory.py` owns the eight scenario workspaces. The standard
  builder exposes them with `python evals/fixtures/make.py memory`; the tests generate
  isolated temporary copies instead. Never hand-edit `evals/fixtures/build/`.
- `tests/fixtures/memory/acceptance.yaml` freezes coverage, the bounded provider-language
  contract and the two known defect families. Its original criteria remain unchanged.
- `tests/fixtures/memory/baseline-findings.yaml` records the frozen phase-zero output by
  check, path and severity, including informational findings. Empty output is not proof
  that the reasoning task is satisfied.
- `tests/fixtures/memory/phase1-findings.yaml` records the additive finding delta after
  fixing the resolver. The historical baseline and desired answers are not rewritten.
- `tests/fixtures/memory/phase2-metadata.yaml` enriches only disposable fixture copies;
  the original generator and comprehension questions are unchanged.
- `evals/behaviour/memory/cases.yaml` owns the fourteen comprehension questions, their
  required sources, expected answers and forbidden conclusions. `memory` names an eval
  scenario group, not an eighth skill. See `PHASE-9.md` for actual captures and review
  limitations; the original `results: not-run` is the frozen baseline, not a live ledger.

The generated files use the registry's current version and fixed synthetic review times.
All other fixture meaning and acceptance criteria are versioned with this baseline;
change them only with a contract-version bump and an explicit rationale. The code Git
histories have fixed authors, timestamps and contents. Tests compare files and commit IDs,
not `.git` internals, whose locks, reflogs and index timestamps are not portable outputs.

## The historical failures are now ordinary regression tests

| Defect family | Result restored by phase 1 | Positive controls |
|---|---|---|
| Qualified candidate join | `CHG002` and `PR004` for `alpha:SIG-001` classified under the local `SIG-001` key | A global `INC-001` with the same architecture impact triggers both checks |
| Product scope in triage | `ICG001` for beta when only alpha's homonymous signal was classified | No classifications reports both logs; separate classifications report neither |

Phase zero carried three `unittest.expectedFailure` markers. The fixes first produced
three unexpected successes; phase one removed the markers without weakening the expected
answers. Fixture prerequisites, full CLI execution, schema validity and unrelated findings
are still independently checked. No check is disabled or downgraded.

`test_references.py` adds scope and ambiguity controls, exact section-location checks,
compatibility aliases, and a real Git-export fixture. An exported validator must load its
own package from an unrelated working directory, even beside an incompatible package on
PYTHONPATH. Live and exported validators can coexist in one Python process.

`test_documentary.py` executes the graph, schema, CLI, search and snapshot gates. It
checks provenance, inverse methods, legacy decision retrieval, source filters, portable
canonical bytes, partial results, source mutation, atomic publication and safe fallback.
The export fixture also starts the memory CLI without relying on the live checkout.

## Behavioural evaluation and safety

Use the dedicated opt-in `evals/behaviour/memory/qualify.py`; its README owns the protocol.
It preflights a Linux/WSL read-only, restricted-read, command-network-denied sandbox,
captures full answers/events and detects additions, deletions, links and mode changes.
No model executes in the deterministic suite or CI. Capture success is **pending review**,
not comprehension success. Missing quota, interrupted turns and unproven isolation remain
unavailable. Every mandatory/forbidden criterion and source-reading obligation needs review.
The old generic `evals/behaviour/run.py` still permits edits for other artifact-producing
skill evals; it is not the qualification runner. Its behaviour has not been changed.

`test_code_provider.py` runs the offline phase-three gates with a controllable fake and
strict synthetic receipt tests. Python imports, definitions, calls and source locations
are the first required coverage. JSON Schema is a contract input, not SQL lineage or
customer-data analysis. Unresolved, unsupported and unavailable remain distinct evidence.
No graph or retrieval output is faked into a successful baseline.

Real provider conformance is a separate explicit command, not an automatic download or a
skipped test counted as passed:

```bash
python3 -B tests/memory/enola_conformance.py --enola /path/to/pinned/enola
```

It uses only synthetic input, Linux/WSL isolation and the executable hash in
`providers.lock.json`. See `PHASE-3.md` for the upstream parser failure and the mandatory
adapter syntax guard. No source from the actual products is tested or modified.

The full increment's twenty-four deterministic obligations were frozen under
`deferred_checks` in the acceptance contract with their implementation phases. Their
inputs and required outcomes were specifications, not successful engine tests. Executable
coverage is added with each phase; see `PHASE-4.md` for the operational engine and
`PHASE-5.md` for contribution checks, `PHASE-6.md` for release evidence and `PHASE-7.md`
for migration/distribution. `test_adoption.py` compares complete baseline and new Git
exports without history or foreign imports, tests isolated approved adoption, optional
forward-only gaps, documentary operation and rollback without changing historical sources.
This is not a claim that every historical version or consumer customization is compatible.

See `BASELINE.md` for the measured checkout, environment and phase-zero results.

`test_operational.py` exercises required source budgets, historical/reconsidered decisions,
adopted rule pins, caller-reported readings, scoped hypotheses, integrity-checked code
bundles, before/after comparison, overlapping mappings and bounded cyclic traversal.
Each of the seven skills retains the shared adopted rules under a zero delivery budget;
changed rule bytes invalidate context identity, and a referenced missing guide stays a gap.
The Git export fixture also exercises `context` from an unrelated working directory.
These tests prove deterministic mechanics, not an agent's comprehension or source-reading
honesty. No skill-forward model evaluation is claimed.

`test_authority.py` creates committed synthetic framework/document/code histories and
independently witnessed synthetic receipts. It exercises PR-only approval, normative
tampering, current revocation, affected-contract binding, exact multi-repository sets,
stale/failed/forged execution evidence, independent no-chg review, source filters and a
portable strict CLI. The optional GitHub controller is checked with synthetic API inputs,
mocked fetch transport and pinned/manual workflow configuration; no remote CI is claimed.

`test_release.py` adds synthetic multi-repository candidates, legacy single-repository
normalization, frozen-plan and exact-build/configuration checks, separate stage receipts,
actual default-branch ancestry (including a branch named master), shared releases and
compatibility sources, cyclic/missing dependencies, premature CHG closure, private inputs
and an exported read-only CLI. The receipt successes simulate trusted-controller evidence;
they do not claim that real product builds, model evaluations or deployments executed.
