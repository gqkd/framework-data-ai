---
schema: framework/release-note/v1
artifact_type: release-note
lifecycle: immutable
status: active
id: REL-NNN
products: [prodotto-a]
owners: [NOME]
created: AAAA-MM-GG
derives_from: [CHG-NNN, EVR-NNN]
classification: internal
---

# REL-NNN · Release note

**Domanda:** cosa è cambiato, per chi, e come si torna indietro?

**Per una persona. Dieci righe.** La versione machine-readable è `RLM-NNN.yaml`: sono due
documenti perché hanno due lettori, non per ridondanza.

## Cosa cambia

Dal punto di vista di chi usa il sistema. Non i commit: gli effetti.

## Change incluse

`CHG-NNN` · `DEC-NNN`

## Rischi e rollback

Cosa potrebbe andare storto e come si torna indietro. Il target di rollback esatto è in
`RLM`.

## Cosa monitorare nelle prime 48 ore

Metriche specifiche di questa release, non quelle di routine.

---

## Anti-pattern

- **Elencare i commit.** Chi legge non sa cosa sia un commit e non gli serve.
- **Ometterla perché "è un cambiamento piccolo".** È il collante fra gli ID e la realtà:
  il punto in cui una decisione tracciata diventa qualcosa che gira in produzione a una
  data precisa.
- **Duplicare `RLM`.** Se questa nota contiene hash, non è per umani.
