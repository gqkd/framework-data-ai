---
schema: framework/solution-design/v1
artifact_type: solution-design
lifecycle: immutable
status: active
id: SD-NNN
products: [prodotto-a]
owners: [NOME]
created: AAAA-MM-GG
derives_from: [HYP-NNN, DFB-NNN, PBR]
classification: internal
---

# SD-NNN · Solution design e MVA

**Domanda:** cosa costruiamo, con quali componenti, e cosa abbiamo deliberatamente
rinviato?

**Nota sulla classe:** immutabile. È lo snapshot del progetto al gate G4. Da F5 in poi la
verità corrente sta in `ARC`, che comincia a vivere con la prima riga di codice: design e
implementazione divergono molto prima del go-live.

## Scope dell'MVP

Una frase.

## §Fuori scope

Esplicito, con la ragione e il rimando al `DEC` dove esiste. Sezione obbligatoria e la più
letta dagli agenti.

## Componenti e flusso del dato

Diagramma end-to-end. Per ogni componente: responsabilità in una riga.

## Scelte tecnologiche

| Scelta | `DEC` | Nell'MVA? |
|---|---|---|
| | DEC-NNN | sì/no |

Qui **cosa**, nei `DEC` **perché**. Se questa tabella spiega le motivazioni, sta
duplicando.

## MVA — Minimum Viable Architecture

Le decisioni architetturali **irreversibili o costose da invertire** che vanno prese
adesso. Non l'architettura ideale: il sottoinsieme minimo.

| Decisione | Perché ora | Costo di inversione | `DEC` |
|---|---|---|---|

Test: se una decisione si può cambiare in una settimana, non appartiene all'MVA.

## Debito accettato

| Debito | Perché lo accettiamo | Trigger di rientro |
|---|---|---|

Il trigger è obbligatorio: senza, non è debito accettato ma debito dimenticato. Se il
debito attraversa più artefatti, la sua casa è `OPEN.md §2`.

## Modello di costo

Costo per unità (query, inferenza, token, GB) e costo a regime stimato. Nei sistemi AI il
costo è un requisito non funzionale, non una voce di budget.

---

## Anti-pattern

- **MVA che include tutto "per sicurezza".** Se l'MVA coincide con l'architettura ideale,
  non hai fatto la selezione che è l'unico scopo del concetto.
- **Fuori scope vuoto.** Un agente leggerà l'assenza come dimenticanza e implementerà.
- **Debito senza trigger.**
- **Nessun modello di costo.** Nei progetti AI il costo unitario scoperto in produzione è
  la causa più comune di riprogettazione forzata.
- **Aggiornarlo dopo G4.** È immutabile: da lì in poi si aggiorna `ARC`.
