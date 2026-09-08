# Product Memory: acceptance tests and scoped core

This directory preserves the phase-zero baseline and tests the scoped core and phase-two
documentary memory. Historical reports are in `BASELINE.md` and `PHASE-1.md`; the current
handoff is `PHASE-2.md`. A code provider and operational context/impact packs remain later
phases. The phase-two query output is a documentary pack, not a task authorization.

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
  contract and the two known defect families. No provider is installed or tested yet.
- `tests/fixtures/memory/baseline-findings.yaml` records the frozen phase-zero output by
  check, path and severity, including informational findings. Empty output is not proof
  that the reasoning task is satisfied.
- `tests/fixtures/memory/phase1-findings.yaml` records the additive finding delta after
  fixing the resolver. The historical baseline and desired answers are not rewritten.
- `tests/fixtures/memory/phase2-metadata.yaml` enriches only disposable fixture copies;
  the original generator and comprehension questions are unchanged.
- `evals/behaviour/memory/cases.yaml` owns the fourteen comprehension questions, their
  required sources, expected answers and forbidden conclusions. `memory` names an eval
  scenario group, not an eighth skill. Model evaluation has **not** been run.

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

The case file is compatible with the existing `evals/behaviour/run.py` scenario loader.
That runner requires a separately available model CLI and currently permits edits in its
disposable copy: read-only is an acceptance criterion, **not** an enforced sandbox mode.
For any later run, inspect both the answer and the file diff; any unauthorized write is a
critical failure even if the answer sounds correct. The runner does not automatically
grade `must_include`, `must_not` or source-reading depth. No model run or score is claimed
by the deterministic tests, which only validate the inputs and their references.

Provider conformance is deliberately deferred. Python imports, definitions, calls and
source locations are the first required coverage. JSON Schema is a contract input, not a
claim of SQL lineage or customer-data analysis. A future provider must expose unresolved,
unsupported and unavailable evidence explicitly. No graph or retrieval output is faked
into a successful baseline.

The full increment's twenty-four deterministic obligations were frozen under
`deferred_checks` in the acceptance contract with their implementation phases. Their
inputs and required outcomes were specifications, not successful engine tests. Executable
coverage is added with each phase; see `PHASE-2.md` for what is covered now. The migration
smoke checks only an already-current fixture
and no writes; export tests cover the entry points, not every future migration.

See `BASELINE.md` for the measured checkout, environment and phase-zero results.
