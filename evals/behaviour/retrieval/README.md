# Synthetic retrieval benchmark

## Latest: G1 executed with live agents, 19/09

The [G1 report](G1-GRAPH-ABLATION.md) and [results](G1-GRAPH-ABLATION-RESULTS.json) record
the first end-to-end graph ablation with real model calls: one candidate runtime, arm S
reading documents directly and arm G required to use the engine first. Eight trials, four
complete pairs, no failures. The graph arm costs 17.1% more tokens and adds nothing --
0/4 pairs saved tokens, 0/4 recovered an additional required source group, 0/4 changed the
answer; 17/17 groups in both arms and no critical failures. Four live engine invocations
produced zero documents once, an argument error once and redundant confirmation twice.
Grading is author-side; independent review remains pending. The result agrees with the
model-free G0 qualification below rather than overturning it.

## Earlier: graph qualification, 16/09

The [G0 report](GRAPH-ABLATION-G0.md) and [results](GRAPH-ABLATION-G0-RESULTS.json)
record 4/4 source-discovery comparisons, no model calls: the frozen seeds yield
no additional required source groups with traversal. One extra decision is not
in the minimum rubric; this does not make it useless. G0 is not qualified for
agent dispatch, and the proposed eight agent trials remain 0/8. The report
explains document/entry routing, code-source limits, and the need for real
control-arm isolation. The old LOG provenance/delivery claim is corrected in
the attribution plan. Fifteen new offline tests and all 100 existing retrieval
tests pass. No source corpus, oracle or runtime changes were made.

## Current continuation and graph attribution

The [completed development block](DEVELOPMENT-CONTINUATION.md), consolidated
on 16/09, records seven new pairs and 8/24 unique questions including R001.
Its [ledger](DEVELOPMENT-CONTINUATION-RESULTS.json) retains 19 attempts,
16 complete answers and three quota failures with unknown usage. Independent
answer review is still pending. One spontaneous context invocation is now
observed; the earlier zero-invocation counts describe their own batches only.

The [15/09 graph-attribution audit and plan](GRAPH-ATTRIBUTION-PLAN.md) qualifies
the conclusions of the reports below: the direct benchmark uses zero-hop lexical
queries, context requirement paths are not verified reading, and neither A/B nor
the existing guided arm isolates graph traversal on the same runtime. Two local
probes confirm that traversal can add sources in one case and none in another.
This is not yet evidence of better answers. Existing reports are retained as
historical author analyses, not independent or causal verdicts.

The [second development resumption record](DEVELOPMENT-RUN-RESUME-2.md)
records the user-authorized remaining four pairs, including the failed initial
attempt to persist the record before dispatch. The earlier status paragraphs
below describe their original snapshots; they are not live counters.

## Earlier snapshots

Status: the R001 pilot, five paired v1 repetitions and a separate flexible-reader
A/B pilot are captured. Answers remain pending independent review, with no
general improvement claim. Unique-question coverage is still 1/24 (4.2%).
The [flexible-reader report](PILOT-R001-FLEXIBLE.md) and its
[numeric ledger](PILOT-R001-FLEXIBLE-RESULTS.json) document the new condition:
agent-selected ranges, persistent empty outputs, and a discrepancy between
captured full text and the model's report of truncation. See its
[preregistration](PILOT-R001-FLEXIBLE-PLAN.md) and [reader guide](FLEXIBLE-READER.md).
Do not pool the two reading methods.

The [repetition report](REPETITIONS-R001.md) and [numeric ledger](REPETITIONS-R001-RESULTS.json)
record mixed cost/time results, missing-output observations, quota interruptions
and every attempted run. The [pilot report](PILOT-R001.md) remains separate.
See the [preregistered plan](REPETITIONS-R001-PLAN.md),
[first resumption](REPETITIONS-R001-RESUME.md) and
[second resumption](REPETITIONS-R001-RESUME-2.md) for the selection history.

The [runner guide](RUNNER.md) documents preparation, sandbox-only checks, explicit
execution, review requirements and the limits of source-delivery observation.
Preparation also creates evaluator-only review packets for the selected questions.
A human review covers only its explicit question IDs and exact prepared inputs.

The [local verification record](VERIFICATION.md) lists the delivered corpus and executed checks.

The [Opus arena](OPUS-ARENA.md) and its [numeric report](OPUS-ARENA-RESULTS.json) repeat
two questions with a second model family. Both arms reach 3/3 required groups, the engine
is still never invoked — one trial read the Product Memory section and declined to run it —
and the candidate arm reads more, never less. Opus reads 4.6-4.7x less than the codex arm
for identical coverage, and passes the R016 rubric that the codex baseline failed, so the
single quality difference previously seen between framework versions was a model weakness.
Isolation there is weaker than the codex sandbox; the two series are not pooled.

The [graph retrieval benchmark](GRAPH-RETRIEVAL.md) and its
[numeric report](GRAPH-RETRIEVAL-RESULTS.json) measure the engine's own retrieval channel
against the frozen oracle, with no model: 0% recall for the question as asked, 48% with
correct English terms, 72% for the documented context pack, against 100% observed for
agents reading files. All 21 missed groups are code paths; the code graph is unavailable
because its provider is not configured and the protocol forbids installing one.
[run_graph.py](run_graph.py) adds arm C, which supplies that documented invocation to the
candidate arm only.

The [mechanism diagnosis](MECHANISM-DIAGNOSIS.md) and the
[resume ledger](DEVELOPMENT-RUN-RESULTS.json) record the interrupted 15/09 block and a
model-free finding: `memory.py` was never invoked in any real trial, the context pack is
byte-identical across different questions, and the documentary query is literal, so no
Italian question term matches the English corpus. Author-side rubric grading of the
captured answers shows nine ties and one difference, not separated from session variance.
No improvement is demonstrated and no regression is observed.

Only invented products, documents and executable Python. No real project migration.
See [PROTOCOL.md](PROTOCOL.md) for the Italian experiment description, and
[questions.yaml](questions.yaml) for the questions. [oracle.yaml](oracle.yaml) is
evaluator-only reference material. Only R001 has a recorded human rubric
confirmation; the other questions remain pending independent review.

The [seven-question development review](DEVELOPMENT-REVIEW.md) now collects
the next rubric confirmation in one place, with full source packets and
[preparation evidence](DEVELOPMENT-REVIEW-RESULTS.json). Fourteen trial copies
are prepared, not executed. R004 has an explicitly recorded rubric-scope
question; no frozen input or human attestation was changed.

## Prepare, without a model

From the framework checkout, with its existing constrained Python environment and Git:

```bash
python3 -B evals/behaviour/retrieval/prepare.py --output /tmp/retrieval-synthetic-v1
python3 -B -m unittest discover -s tests/memory -p test_retrieval_dataset.py -v
```

The destination must be an absent absolute directory outside the framework checkout.
Both framework commits must already exist locally; nothing is fetched or installed.
Defaults are the pre-memory 3.6.3 and committed 3.8.1 snapshots. Override them only
with full commit IDs using --baseline and --candidate; the manifest records both.
Projects use version-only adoption because their runtimes have no Git history. Exact
runtime commits and file hashes are evaluator-side attestations, not project Git pins.

## Generated layout

```text
arms/A/project/       synthetic source documents and local code repositories
arms/A/framework/     previous runtime, without evals/tests/history
arms/B/project/       identical source content except framework.yaml
arms/B/framework/     current runtime, without evals/tests/history
evaluator/            questions, reference answers, requirements, schedule, manifest
```

Directory layout is NOT a security boundary. The separate runner enforces filesystem
isolation: one project's sources and its runtime only; no sibling, generator, evaluator,
oracle, user corpus or framework Git history. This preparer never invokes a model.
There are two reusable bases, not 144 already isolated trial workspaces.

No graph or context pack is precomputed. Trials must start with one question and the
ordinary project entry point. Optional metadata arm C is deferred, not included in B.

The executable checks prove consistency, reproducibility, source parity and fixture
behaviour. They do not prove agent comprehension or token savings. Source requirements
are expected reading spans, not actual agent reading receipts. The runner captures
instrumented source outputs. R001 has exercised that interface with a real model;
independent answer review and broader qualification remain separate work.
No Evals API or new dependency is introduced.

Historical compatibility uses the two exact local Git objects. In shallow checkouts where
they are unavailable, that integration test reports a skip and does not fetch history;
the core fixture tests still run. Neither a skip nor a schema pass is an agent-quality score.
