---
schema: framework/decision-record/v1
artifact_type: decision-record
lifecycle: immutable
status: proposed
id: DEC-NNN
scope: architecture
products: [prodotto-a, prodotto-b]
owners: [NOME]
approvers: [NOME]
created: AAAA-MM-GG
derives_from: [HYP-NNN, EVD-NNN, SIG-NNN]
supersedes: null
classification: internal
---

# DEC-NNN · Titolo della decisione, all'attivo

**Domanda:** quale decisione è stata presa, perché, in quel momento, e quali alternative
sono state scartate?

`status`: `proposed | accepted | superseded`

## Perché un solo tipo di documento per prodotto e architettura

Storicamente l'ADR registra decisioni architetturali. Ma rinunciare a un prodotto,
scegliere un segmento, accettare un rischio commerciale o fissare una priorità sono
decisioni tanto da registrare quanto la scelta di un database — e sono spesso più costose.

Un registro separato per le decisioni di prodotto significa che quelle **cross-prodotto**,
cioè le più care, non hanno casa e finiscono nel registro del prodotto su cui stavi
lavorando quel giorno.

Quindi: **un tipo di documento, una numerazione, una cartella.** Il campo `scope`
determina la natura della decisione:

| `scope` | Cosa registra | Esempi |
|---|---|---|
| `product` | Decisioni su cosa costruiamo, per chi, con quale priorità | esito di un gate · pivot · stop · scelta di segmento · scope dell'MVP · accettazione di un rischio commerciale |
| `architecture` | Decisioni su come è fatto il sistema | scelta di un datastore · stile di integrazione · confine fra componenti · modello di deploy |
| `platform` | Decisioni che vincolano tutti e tre i prodotti | tenancy · identità · substrato condiviso · convenzioni |

`scope: architecture` è l'ADR classico: una specializzazione, non un documento diverso.
Un `DEC` con `scope: platform` deve elencare tutti i prodotti in `products`.

## Contesto

Il **vincolo** che rendeva necessaria una decisione. Non la cronistoria di come ci siamo
arrivati: la forza che non lasciava scelta se non scegliere.

## Decisione

All'attivo, al presente. *"Usiamo X per Y."*

## Alternative considerate

| Alternativa | Perché scartata |
|---|---|

Se le alternative sembrano ovviamente peggiori, non le hai considerate: le hai costruite
per far vincere la scelta già fatta. È l'anti-pattern più comune e più riconoscibile.

## Conseguenze

Cosa diventa più facile. Cosa diventa più difficile. **Cosa diventa impossibile.**
Includi le conseguenze scomode: sono quelle per cui il documento verrà riletto.

## Condizione di riesame

*Opzionale ma molto utile.* Se la decisione è deliberatamente provvisoria, la condizione
osservabile che la rimette in discussione. Una decisione provvisoria con condizione di
riesame è una decisione; senza condizione è un rinvio mascherato, e va in `OPEN.md`.

---

## Anti-pattern

- **Scritto a posteriori per giustificare.** Si riconosce sempre: le alternative sono
  uomini di paglia.
- **Modificarlo.** È immutabile. Se la decisione cambia, ne scrivi uno nuovo con
  `supersedes` e porti il vecchio a `status: superseded`.
- **Contesto che racconta la storia invece del vincolo.** Chi legge fra un anno vuole
  sapere cosa ti costringeva, non chi era in riunione.
- **Nessuna conseguenza negativa.** Ogni decisione ne ha. Ometterle rende il documento
  inutile proprio nel momento in cui serve, cioè quando qualcuno ne subisce una.
- **Un `DEC` per ogni scelta minuta.** Registra ciò che sarebbe costoso riscoprire.
  Se la scelta si inverte in un pomeriggio, non serve un `DEC`.
