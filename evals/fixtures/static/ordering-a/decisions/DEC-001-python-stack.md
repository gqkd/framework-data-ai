---
schema: framework/decision-record/v1
artifact_type: decision-record
leaves_open: []
lifecycle: immutable
status: accepted
id: DEC-001
scope: architecture
products: [retail-forecast]
owners: [g.quaglia]
approvers: [g.quaglia]
created: 2026-03-10
classification: internal
---

# DEC-001 · We build the forecasting stack in Python

## Context

The two people who will maintain this for the next year write Python and nothing else.

## Decision

We use Python 3.12 for every component of the forecasting pipeline.

## Alternatives considered

| Alternative | Why discarded |
|---|---|
| Scala on Spark | Nobody on the team maintains it after the consultant leaves |

## Consequences

Easier: hiring, and reusing the client's existing notebooks. Harder: anything that needs
JVM-only connectors. Impossible: reusing the group's existing Scala ingestion jobs.
