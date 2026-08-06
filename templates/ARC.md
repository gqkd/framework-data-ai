---
schema: framework/architecture/v1
artifact_type: architecture
lifecycle: living
status: active
version: 1.0.0
products: [prodotto-a]
owners: [NOME]
created: AAAA-MM-GG
last_review: AAAA-MM-GG HH:MM
verified_against: COMMIT_HASH
classification: internal
---

# Architettura — Nome prodotto

**Domanda:** com'è fatto il sistema adesso?

**Comincia a vivere in F5**, con la prima riga di codice — non dal go-live: design e
implementazione divergono molto prima. Il campo `verified_against` registra il commit su
cui questo documento è stato verificato l'ultima volta.

**Struttura per tre prodotti:** questo file contiene il **delta** rispetto a
`PLATFORM.md`. Ciò che è condiviso si documenta una volta sola, là.

## Componenti

| Componente | Responsabilità (una riga) | Condiviso o specifico | `DEC` |
|---|---|---|---|

## Flusso del dato end-to-end

Diagramma. È la parte che manca più spesso e quella che serve più di tutte: se una persona
nuova non riesce a disegnare il sistema alla lavagna dopo aver letto questo documento, di
solito manca il flusso del dato.

## Stati del dato

Dove risiede e in che forma: raw, curated, serving. Con rimando ai `DC`.

## Confini

Cosa è nostro, cosa è di terzi, cosa è degli altri due prodotti. Ogni confine verso un
altro prodotto deve corrispondere a un `DC`.

## Ambienti

| Ambiente | Scopo | Differenze rilevanti dal produttivo |
|---|---|---|

Le differenze sono la parte utile: è dove nascono i bug che non si riproducono.

## Decisioni che spiegano questa architettura

Elenco dei `DEC` rilevanti. Solo link: qui **com'è**, nei `DEC` **perché**.

---

## Anti-pattern

- **Diventare la somma di tutti i `DEC`.** Se `ARC` inizia a spiegare le motivazioni, sta
  duplicando, e presto divergerà dai `DEC`.
- **Descrivere il sistema progettato invece di quello costruito.** Questo è vivente:
  se non corrisponde al codice, è dannoso, non incompleto.
- **Nessun flusso del dato.** Vedi sopra.
- **Duplicare `PLATFORM.md`.** Se una sezione è identica in tutti e tre gli `ARC`, non
  appartiene agli `ARC`.
- **`verified_against` mai aggiornato.** È il solo modo per sapere quanto ti puoi fidare.
