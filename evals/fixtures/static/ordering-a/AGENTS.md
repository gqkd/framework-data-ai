---
schema: framework/agents-control-plane/v1
artifact_type: agents-control-plane
lifecycle: living
status: active
products: [retail-forecast, store-ops]
owners: [g.quaglia]
created: 2026-03-02
last_review: 2026-07-30 09:45
classification: internal
---

# Instructions for agents

Read this file first. Then `OPEN.md`. Then the `product.yaml` of the product you are
working on.

## Authoritative sources

| Question | Source |
|---|---|
| How the system is built | `products/<p>/ARC.md#current` |
| What shape it is going to have | `products/<p>/ARC.md#target` |
| Why it is built that way | `decisions/DEC-NNN.md` |
| What the product does and for whom | `products/<p>/PBR.md` |
| **What is NOT decided** | `OPEN.md` |

## Non negotiable rules

1. **Do not take decisions listed in `OPEN.md`.** If you need a choice that is listed
   there as open, stop and ask.
2. One authoritative source per fact. Link, do not copy.
3. Respect the lifecycle class declared in the front matter.

## Commands

```bash
python3 -m venv .venv && . .venv/bin/activate
pytest -q
```
