---
schema: framework/runbook/v1
artifact_type: runbook
lifecycle: living
status: active
version: 1.0.0
products: [product-a]
owners: [NAME]
created: YYYY-MM-DD HH:MM
last_review: YYYY-MM-DD HH:MM
classification: internal
---

# Runbook, SLO and monitoring: Product name

**Question:** how do we keep it alive, and how do we know it is going badly before someone
tells us?

**Acid test:** a new person can re-run a failed pipeline reading only this document, at
three in the morning, without asking anyone anything.

## Operations

**Real, copy-pasteable** commands, not descriptions.

```bash
# start
# stop
# re-run of a failed job
# rollback to the last good release (see RLM for the target)
```

## Dependencies

| Dependency | What happens if it goes down | Acceptable degradation |
|---|---|---|

## SLO

| SLO | Target | Window | Error budget |
|---|---|---|---|
| Data freshness | | | |
| Availability | | | |
| Data quality | | | |
| Accuracy in production | | | |

## Monitoring

| What we monitor | Alert threshold | Where | Who receives it |
|---|---|---|---|
| Output: quality metrics | | | |
| **Input: quality and volume of incoming data** | | | |
| Distribution drift | | | |
| Cost per unit | | | |

**In data and AI systems monitoring the output is not enough: the input has to be
monitored.** Most silent failures come in through the data, not the code, and they raise no
exception at all.

## Known failure modes

| Observable symptom | Likely cause | Action |
|---|---|---|

## Escalation

Who gets woken up, in what order, within what time.

---

## Anti-patterns

- **Describing the architecture instead of the commands.** The architecture belongs in
  `ARC`. What is needed here is what to type.
- **Untested commands.** A command in the runbook that does not work is worse than no
  command: it burns the minutes you should be spending thinking.
- **Monitoring only the output.** See above.
- **No cost per unit in the monitoring.** In AI systems cost is the most common way a
  working system becomes unsustainable.
- **SLO with no error budget.** A target that cannot be breached is not an objective, it is
  a wish, and it will be ignored at the first incident.
