# Product Memory qualification

This is an optional evaluation tool, not an eighth skill, runtime dependency or automatic
release gate. `cases.yaml` is frozen; do not edit desired answers to fit a run. Source
hashes and exact required/forbidden claims matter more than a convincing verdict.

## Prepare and capture

Run from a complete framework checkout, using its constrained Python dependencies:

```bash
python3 -B evals/behaviour/memory/qualify.py --output /tmp/memory-qualification-run
```

Preparation builds only synthetic inputs, applies the existing additive phase-2 overlay,
and delivers a precomputed documentary context plus optional separate code observation.
`--enola /path/to/pinned/enola` explicitly enables the already installed provider; absence
does not become fake code evidence. No provider, model CLI, database or plugin is installed.

Add `--execute` to invoke the existing authenticated Codex CLI, sequentially. `--case NAME`
selects exact cases; `--timeout` bounds each process group. `--sandbox-helper` names the
exact native Codex executable when it lives outside the minimal runtime paths. Nothing
falls back to an unsandboxed run. The installed adapter was exercised with Codex CLI 0.150.1.

The adapter uses ephemeral sessions, ignored user configuration, no model override, no
web search, hooks, plugins, apps, browser/computer use, global memory or subagents. It
preserves saved authentication, not personal model/config customizations. The CLI version
is recorded; this JSON event protocol does **not** report actual model/reasoning identity.
That is a reproducibility limitation, not permission to invent a model identifier. Capture
that identity independently before treating these samples as a versioned model qualification.

Sandbox preflight proves project reads work and checks denied writes, an existing external
canary and command networking. Only synthetic project/runtime inputs and the exact sandbox
helper are readable to commands. Evaluator, answer keys and sibling runs are not exposed.
The CLI itself still needs account/service access: this is not a sandbox around its trusted
authentication implementation. Tool-output delivery and claimed reading are not proof of
understanding. This evaluates **precomputed-memory-assisted comprehension**, not automatic
skill routing, autonomous context selection or a controlled improvement over another arm.

These options follow the official [non-interactive execution documentation](https://learn.chatgpt.com/docs/non-interactive-mode)
and [permission-profile documentation](https://learn.chatgpt.com/docs/permissions).

## Review, do not auto-score

The result directory keeps the prepared sources, their before-inventory, prompt, input and
runtime fingerprints, CLI version, command, preflight evidence, full event stream, stderr,
final answer and result status. A successful complete turn is `pending-review`, never `pass`.
The complete CLI event stream does **not** guarantee complete command output: the observed
CLI sometimes retained only a trailing portion of a multi-command response, without an
explicit truncation marker. Missing source content is a review-evidence gap, even with
exit code zero and a plausible answer. A requested `cat`/`sed` is not a reading receipt.
An outage stops the batch; remaining names stay explicitly not run. Any detected project
or copied-runtime mutation is a critical failure. Inputs must remain unchanged.

Review each case against the original rubric:

1. Every `must_include`: identify the answer passage and its actual source evidence.
2. Every `must_not`: inspect the complete answer and actions, not just the closing verdict.
3. Every required file/section/absence: inspect tool events for successful complete delivery,
   additional reads after truncation and the scope of the negative assertion.
4. Record critical failures separately; no aggregate score can override them. Report extra
   unsupported assertions even when the narrow mandatory checklist is satisfied.
5. Identify who assessed it. Agent-assisted assessment is not independent human signoff.

No built-in model judge, keyword pass check or automatic approval is provided. Keep full
answers for review; a short report must not substitute for them. One sample per case cannot
establish reliability, token savings or a causal advantage over the previous framework.

An interrupted trial is retained. To retry without silently changing the input:

```bash
python3 -B evals/behaviour/memory/qualify.py --output /tmp/memory-qualification-retry \
  --from-prepared /tmp/memory-qualification-run --case NAME --execute
```

Replay verifies input/runtime inventories and the unchanged case/prompt contract, creates
a new result directory and does not regenerate graphs or invoke a provider. Supply the same
required sandbox-helper option. Retrying a completed but poor answer must be recorded as
another sample, never as replacement evidence.

## Private pilot

`pilot.py --root /path/to/docs --product PRODUCT --output /private/absent-directory` runs
capture/graph/context with the actual adopted pin and reports filtered/partial evidence.
Optional repeated `--code-root /path/to/checkout --enola /path/to/pinned/enola` observes only
tracked Python statically. No checkout, product code, tests, hooks, database, deployment or
LLM is executed. Other languages, ignored/untracked sources and submodules remain explicit
limitations. This direct observer pilot does **not** verify document-to-code mapping.

Outputs are private, not anonymized. Only explicitly reviewed aggregate counts belong in
the public framework. It checks selected input hashes and Git status before/after without
requiring a clean worktree. A dirty checkout is not permission to revert someone else's work.
No migration, adoption, mutation of immutable documents, push, tag or publication is implied.

## Recorded assessment

The [2026-09-10 review](results/2026-09-10/REVIEW.md) retains fourteen original answers,
one separate targeted sample and capture hashes. It is explicitly **not** a fourteen-case
pass: unsupported claims and incomplete source-output evidence remain visible.
