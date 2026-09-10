Yes. There is a potentially redundant normalization relationship across the Alpha producer–Beta consumer boundary that merits investigation, but the available evidence does not authorize changing or recording it as a decision.

Conclusions:

- Alpha normalizes the value before producing `normalized`: [service.py](/tmp/framework-memory-phase9-replay-20260910/trials/discover-an-unrecorded-relationship/project/code/alpha-api/service.py:3).
- Beta normalizes that already-normalized field again: [worker.py](/tmp/framework-memory-phase9-replay-20260910/trials/discover-an-unrecorded-relationship/project/code/beta-worker/worker.py:3).
- Both calls use the same pure implementation, `value.strip().casefold()`: [shared_rules.py](/tmp/framework-memory-phase9-replay-20260910/trials/discover-an-unrecorded-relationship/project/code/shared-rules/shared_rules.py:2).
- DC-001, §“Guarantees,” explicitly guarantees that the producer’s value “is stripped and case-folded.” For payloads conforming to that guarantee, the consumer’s second normalization appears redundant.
- DEC-001, §“Decision,” establishes reuse of one pure normalization function and prohibits tenant-state caching. It does not explicitly state that both sides must apply the function to the same value or that consumer-side re-normalization is required. Thus, the shared-library decision does not resolve this apparent redundancy.

Why this only merits investigation:

- Beta’s test exercises only an already normalized value (`"demo"`); it does not demonstrate whether re-normalization is intentional or needed: [test_worker.py](/tmp/framework-memory-phase9-replay-20260910/trials/discover-an-unrecorded-relationship/project/code/beta-worker/tests/test_worker.py:4).
- Alpha’s test confirms producer normalization: [test_service.py](/tmp/framework-memory-phase9-replay-20260910/trials/discover-an-unrecorded-relationship/project/code/alpha-api/tests/test_service.py:4).
- The JSON Schema requires only a string; it cannot establish that the string was semantically normalized: [response.schema.json](/tmp/framework-memory-phase9-replay-20260910/trials/discover-an-unrecorded-relationship/project/code/alpha-api/contracts/response.schema.json:1).
- No available source says whether Beta also accepts payloads from non-Alpha or untrusted/legacy producers, or whether the second call is intended as defensive canonicalization.
- No integration, deployment, runtime, performance, or failure evidence was available or measured. I did not execute tests.

Sources actually read include `AGENTS.md`; the root, platform, Alpha, and Beta `OPEN.md` registers; both `product.yaml` manifests; `PLATFORM.md`; both products’ `PBR.md` and `ARC.md`; DC-001; DEC-001; the schema; producer, consumer, shared-rule code and tests; and the context/document graph as navigation and provenance aids. The registers contain no declared open decision or known issue covering this relationship. Graph absence therefore does not settle its impact.

Accordingly: investigate whether Beta’s second call is intentional defense-in-depth or unnecessary duplicate processing, but do not infer approval to remove it or create a new decision.