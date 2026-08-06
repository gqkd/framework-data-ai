---
schema: framework/evaluation-plan/v1
artifact_type: evaluation-plan
lifecycle: living
status: active
version: 1.0.0
products: [prodotto-a]
owners: [NOME]
created: AAAA-MM-GG
last_review: AAAA-MM-GG HH:MM
derives_from: [HYP-NNN, PBR]
classification: internal
---

# Evaluation plan — Nome del componente

**Domanda:** come sapremo se funziona, prima di metterlo in produzione?

**Vivente ma congelato per ogni release candidate.** A ogni RC si registra la versione
(`version` + hash del file) e l'`EVR` cita quella. Il congelamento è ciò che impedisce di
ritoccare le soglie dopo aver visto i risultati — che è il modo in cui un piano di
valutazione diventa un rituale.

## Dataset di valutazione

- Come è costruito, con quale criterio di selezione
- Dimensione
- Chi ha etichettato, e con quale livello di accordo se più di uno
- Dove è versionato
- Come si aggiorna, e con quale cautela: allargare il dataset cambia i numeri storici

## Baseline

Contro cosa confrontiamo: una regola banale, il processo attuale, un operatore umano.
**Campo obbligatorio.** Senza baseline non stai valutando, stai descrivendo: "85% di
accuratezza" non significa nulla finché non sai che la regola banale fa 83%.

## Metriche e soglie

| Metrica | Definizione | Baseline | Soglia minima | Target | Blocca il rilascio? |
|---|---|---|---|---|---|
| | link a `GLOSSARY` | | numero | numero | sì/no |

Soglie numeriche. "Buono" non è una soglia.

## Slice

Sottoinsiemi misurati separatamente, per non nascondere fallimenti dentro una media.
Per ciascuno la soglia può differire, e va dichiarata.

| Slice | Perché conta | Soglia |
|---|---|---|

## Casi limite

Comportamenti attesi in condizioni fuori distribuzione: input vuoto, lingua inattesa,
volume anomalo, dato mancante.

## Definizione di fallimento

Sotto quali condizioni **non si rilascia**, anche se la media è sopra soglia.

## Metrica di business

A quale outcome del `PBR` puntano le metriche tecniche, e con quale legame ipotizzato.
Se il legame non è dimostrato, dirlo: è un'ipotesi, e appartiene a `HYP`.

---

## Anti-pattern

- **Definire le soglie dopo aver visto i risultati.** Scriverle prima è l'intero valore del
  documento; tutto il resto è contabilità.
- **Nessuna baseline.** Il campo più omesso e il più decisivo.
- **Solo metriche aggregate.** Le medie nascondono esattamente i fallimenti che
  importano.
- **Abbassare una soglia per far passare un `RG`.** Se serve, è una decisione di prodotto
  e richiede un `DEC` con il motivo, non una modifica silenziosa.
- **Dataset di valutazione che cresce senza registrare la versione.** Rende i confronti
  storici privi di significato.
