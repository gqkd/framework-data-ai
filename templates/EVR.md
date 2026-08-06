---
schema: framework/evaluation-report/v1
artifact_type: evaluation-report
lifecycle: immutable
status: active
id: EVR-NNN
products: [prodotto-a]
owners: [NOME]
created: AAAA-MM-GG
derives_from: [EVP]
evp_version: 1.2.0
evp_hash: SHA_DEL_FILE_EVP
verified_against: COMMIT_HASH
classification: internal
---

# EVR-NNN · Evaluation report

**Domanda:** cosa ha prodotto la valutazione, confrontata con le soglie **dichiarate
prima**?

**Serve al gate `RG`.** Uno per release candidate, compresa la prima. Immutabile: mai
riscritto.

## Versione valutata

| Elemento | Versione o hash |
|---|---|
| Codice | commit |
| Modello | nome e versione |
| Prompt | hash o tag |
| Configurazione | |
| Dataset di valutazione | versione |
| **`EVP` di riferimento** | versione + hash |

**Senza questi campi il report non è un eval, è un numero.** Il riferimento all'`EVP`
congelato è ciò che rende verificabile che le soglie non siano state ritoccate dopo.

## Risultati

| Metrica | Soglia `EVP` | Baseline | Risultato | Esito |
|---|---|---|---|---|
| | | | | pass / fail |

## Risultati per slice

| Slice | Soglia | Risultato | Esito |
|---|---|---|---|

## Fallimenti osservati

Non solo quanti: **di che natura**. Un errore sistematico su una categoria è un problema
diverso da un rumore distribuito, anche a parità di metrica.

## Confronto con l'`EVR` precedente

| Metrica | Precedente | Attuale | Δ |
|---|---|---|---|

La serie storica di questi report è la memoria della qualità del sistema, ed è l'unico
strumento che permette di accorgersi di un peggioramento lento — il modo in cui i sistemi
AI si degradano nella pratica.

## Verdetto

`go` · `no-go` → **rework**, non rollback: non è ancora in produzione.

Rimando ai `CHG` valutati.

---

## Anti-pattern

- **Nessun riferimento alla versione esatta.** Il difetto più grave: rende il report
  inutilizzabile per qualsiasi confronto.
- **Nessun riferimento all'`EVP` congelato.** Non si può verificare che le soglie fossero
  quelle di prima.
- **Solo metriche aggregate.** Le slice sono la parte che scopre i problemi.
- **Verdetto `go` con una slice sotto soglia, senza un `DEC` che lo motivi.** È il modo in
  cui un gate diventa un rituale.
