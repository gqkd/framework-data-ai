---
schema: framework/agents-control-plane/v1
artifact_type: agents-control-plane
lifecycle: living
status: active
products: [ricambi-ai]
owners: [l.bianchi]
created: 2026-07-28
last_review: 2026-07-28 16:40
classification: internal
---

# Instructions for agents

Read this file first. Then `OPEN.md`.

The repository was set up last week and holds almost nothing yet: a brief the client sent
us in `corpus/`, and the open register. There is no architecture document and no decision
record, because nothing has been decided.

## Authoritative sources

| Question | Source |
|---|---|
| What the product does and for whom | `products/ricambi-ai/PBR.md` (does not exist yet) |
| How the system is built | `products/ricambi-ai/ARC.md` (does not exist yet) |
| Why it is built that way | `decisions/DEC-NNN.md` (none yet) |
| **What is NOT decided** | `OPEN.md` |

## Non negotiable rules

1. **Do not take decisions listed in `OPEN.md`.** Stop and ask.
2. Absence is information. If a fact is not documented, say so rather than assuming it.
3. The framework templates live at `${CLAUDE_PLUGIN_ROOT}/templates/` and the validator at
   `${CLAUDE_PLUGIN_ROOT}/skills/audit/scripts/validate.py`.
