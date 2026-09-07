# Product Memory phase 0: implementation report

Recorded on 2026-09-07. This is a historical execution record, not the current framework
version authority and not a model-evaluation result.

## Starting point

| Item | Observed value |
|---|---|
| Base commit | `db75f310e2f42453cb0fe1b26573c3f6b5736790` |
| Registry version at baseline | `3.6.3` |
| Initial WSL Git state | Clean `main`, tracking `origin/main` |
| Implementation branch | `codex/product-memory-phase-0` |
| Local runtime | WSL Ubuntu 26.04, Python 3.14.4 |
| Direct dependencies observed | PyYAML 6.0.3; jsonschema 4.19.2 |
| Existing CI runtime | Python 3.12; not executed locally in this phase |

Sources: WSL Git status and rev-parse, Python version, pip package metadata, the registry,
and `.github/workflows/framework.yml`, inspected directly during this implementation.
No fetch, provider installation, dependency update, commit, push or product migration was
performed to obtain the baseline. The base revision matches the approved implementation
plan, so there was no intervening framework delta to re-plan.

## What changed

```text
Existing authoritative framework                 unchanged
  validator / schemas / seven skills / dependencies
                     |
       existing selfcheck and CI
                     |
          tests/memory/test_phase0.py
             /                   \
    synthetic workspaces      versioned acceptance contract
      docs + Git code         questions + sources + outcomes
             |                   |
    actual validator CLI     future memory/provider work
```

| File | Purpose |
|---|---|
| `evals/fixtures/generators/memory.py` | Eight deterministic synthetic workspaces, including real local code repositories |
| `evals/fixtures/make.py` | Registers the generator in the existing fixture builder |
| `tests/memory/test_phase0.py` | Nineteen offline tests; real validator CLI, controls and three explicit expected failures |
| `tests/selfcheck.py` | Runs the new suite from the existing CI entry point and prints expected failures |
| `tests/fixtures/memory/acceptance.yaml` | Coverage contract, bounded Python provider requirements, defect inventory and twenty-four deferred obligations |
| `tests/fixtures/memory/baseline-findings.yaml` | Observed check/path/severity baseline, including informational findings |
| `evals/behaviour/memory/cases.yaml` | Fourteen comprehension questions, required reading, expected answers and forbidden conclusions |
| `tests/memory/README.md` | Execution, ownership, freeze policy and limitations |
| `evals/README.md`, `evals/fixtures/README.md` | Discovery links without changing historical eval scores |
| This file | Starting state, scope, measured results and handoff |

The generated workspaces live under the existing ignored `evals/fixtures/build/memory/`
when built manually. The test suite uses disposable temporary directories. No synthetic
product artifact is inserted into the framework's own documentation or any real product.
Fixture names are invented; no client corpus was used.

## Measured checks

Commands run from the framework checkout:

```bash
python3 -B tests/selfcheck.py
python3 -B schemas/generate.py --check
python3 -B -m unittest discover -s tests/memory -v
git diff --check
```

- Before editing: full selfcheck passed; 30 schemas and 4 catalog tables were current.
- New standalone suite: 19 tests, 16 ordinary passes and 3 expected failures. No unexpected
  failures or skips. The synthetic producer and consumer each also run a passing unit test.
- Full selfcheck passed both at first integration and on the final rerun after acceptance
  coverage completion; the final run includes all 19 phase-zero tests and prints the
  3 expected failures explicitly.
- Generated schema check still passes. Schema generator, registry and generated files are
  unchanged. The patch adds no production runtime dependencies or version bump.

The suite invokes the actual validator with `--json --stale-days 36500` on every scenario;
the fixed age window keeps the synthetic review dates from introducing current-day noise.
PR cases also pass `--pr-text-file` and `--changed-files`. Inputs are rehashed afterwards
to detect unexpected writes.

The migrator is exercised as `migrate.py --root <temporary-document-only-fixture>
--framework <this-checkout> --json`, without `--adopt`. It returns `up_to_date: true` and
leaves sources unchanged. This proves only the current-version no-op; it does **not** prove
future migration compatibility. Existing selfcheck migration/export tests also pass.

## What the existing validator misses

| Reproducer | Current observation | Required after phase 1 |
|---|---|---|
| Qualified signal in CHG, local key in ICG | No `CHG002` despite the missing architecture decision | Report the missing DEC |
| Same shape through PR check | No `PR004` despite no ARC in the supplied change set | Report the missing ARC update |
| Identically numbered signals in two products, only one classified | No `ICG001` for the other product | Report only the untriaged product's signal |

For the first row, phase 1 must report the missing DEC. For the second it must report the
missing ARC update. For the third it must report the untriaged signal only in its owning
product. The two join assertions form one defect family, not two independent discoveries.

Controls show the gates are active: a global roadmap candidate with architecture impact
produces `CHG002` and `PR004`; no triage produces two `ICG001` findings; separate triage for
both products produces none. Other fixtures have no warnings or errors; the document-only
fixture has its expected informational untriaged-signal finding.

`expectedFailure` is used only on the desired-result assertions, not on fixture setup.
Unrelated finding drift, malformed sources or execution failures fail normally. If a
resolver fix makes an assertion succeed, unexpected success fails the suite until its
marker is deliberately removed. No validator check or severity has been changed.

## What is not claimed

- No agent comprehension runs, model scores or token savings were measured. The cases are
  frozen specifications, and source-existence checks do not prove an agent read those sources.
- No parser/resolver refactor, memory CLI, documentary graph, code graph, context pack,
  external provider, retrieval engine, viewer, release workflow or new skill is implemented.
- The twenty-four future deterministic obligations are assigned to phases 1-7, not marked
  as successful tests of nonexistent components.
- The Python code fixture bounds the first provider test surface. No SQL lineage, runtime
  call graph, universal language support or customer-data access is claimed.
- CI's Python 3.12 environment and remote CI were not run; the measured local runtime is
  Python 3.14.4. The existing CI workflow will run the same selfcheck on a later push/PR.
- The existing behaviour runner permits edits in a disposable copy and does not grade the
  semantic criteria automatically. A future evaluation must inspect both response and diff.

## Handoff to phase 1

Keep this change set separate from the fixes. Implement the shared identity/resolution
path in the validator's three affected checks, preserving the current CLI and historical
export behavior. Remove each expected-failure marker with its fix, review the baseline
finding delta and keep both positive and negative controls. Do not broaden phase 1 into a
graph/provider implementation or migrate any real product implicitly.
