No. Within the available evidence, asynchronous transport is neither implemented nor accepted as a design decision.

- Architecture — current: `products/alpha/ARC.md`, **Current**, and `products/beta/ARC.md`, **Current**, describe only the shared normalization rule and the DC-001 producer/consumer boundary.
- Architecture — target: both ARC files, **Target**, explicitly say: “An asynchronous transport is a possibility, not an accepted design or implemented service.” This is a possible future shape, not current architecture.
- Architecture — delta: both ARC files, **Delta**, state that no performance evidence or decision authorizes adding the transport.
- Decisions: `decisions/DEC-001-shared-rule.md`, **Decision**, accepts only reuse of a pure normalization function. It says nothing about asynchronous transport. `OPEN.md`, `products/alpha/OPEN.md`, and `products/beta/OPEN.md` declare no open decisions.
- Available code:
  - `code/alpha-api/service.py` synchronously calls `normalize()` and returns a dictionary.
  - `code/beta-worker/worker.py` synchronously reads the payload and calls `normalize()`.
  - `code/shared-rules/shared_rules.py` is a pure synchronous function.
  - Their tests exercise those direct calls. A scoped text search found no async, queue, broker, publish/subscribe, message, or event implementation in the available source.
- Snapshot distinction: Alpha’s `ARC.md` verifies baseline commit `08bb1e25…`; the available Alpha checkout is later commit `6a1c6ef…`. I inspected the intervening diff: it only adds `health()`, not asynchronous transport. Beta and shared-rules checkouts match their architecture-pinned commits.
- Contract: `products/alpha/contracts/DC-001-response.md`, **Schema**, **Guarantees**, and **Consumers**, defines the normalized response field and Beta consumption, but does not specify a transport or attest deployment.

Uncertainties and limits: I inspected the local authoritative documents, manifests, available code, tests, contract, commit history, context pack, and documentary graph. I did not execute tests or measure runtime behavior. No deployment configuration or live-service evidence is provided, and `products/beta/PBR.md` explicitly says no deployment is attested. The graph is partial static evidence, so its missing transport edges alone would not prove absence; the conclusion rests primarily on the explicit architecture language and the available source code.