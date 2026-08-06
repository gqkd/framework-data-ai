---
schema: framework/cycle-plan/v1
artifact_type: cycle-plan
lifecycle: living
status: active
version: 12
products: [prodotto-a]
owners: [NOME]
created: AAAA-MM-GG
last_review: AAAA-MM-GG HH:MM
classification: internal
---

# Cycle implementation plan — ciclo N

**Domanda:** come eseguiamo i change contract approvati in questo ciclo?

**Vivente, sostituito ogni ciclo: vale sempre l'ultimo.** È un **output** del reshaping,
non un input: scrivere il piano prima di sapere se prodotto o architettura devono cambiare
significa riscriverlo appena il reshaping cambia lo scope. `version` è il numero del ciclo.

## Change selezionate

| `CHG` | Perché ora | Dipende da | Stato |
|---|---|---|---|

## §Escluse in questo ciclo

Le change valutate e non selezionate, con la ragione.

È la sezione che ti evita di rispiegare la stessa scelta ogni settimana, e che dice a un
agente la differenza fra "non è stato fatto" e "è stato deciso di non farlo".

## Sequenza e dipendenze

Ordine di esecuzione. Cosa blocca cosa.

## Strategia di integrazione e rollout

Come le change entrano insieme. Se rilasciate separatamente, in quale ordine e con quale
compatibilità intermedia.

## Impatto sugli artefatti

| Artefatto | Aggiornamento richiesto |
|---|---|
| `ARC` | |
| `DC` | |
| `EVP` | se le soglie cambiano serve un `DEC` |
| `RSK` | |

## Esito del ciclo

*Compilato alla chiusura.* Cosa è entrato, cosa è slittato, cosa è stato abbandonato.

---

## Anti-pattern

- **Scriverlo prima del reshaping.** Errore strutturale: il piano diventa obsoleto appena
  il reshaping cambia lo scope.
- **Nessuna sezione "escluse".**
- **Contenere incrementi di `RMP` invece di `CHG`.** Un incremento di roadmap non è
  autorizzato: prima diventa un `CHG`.
- **Accumulare i piani dei cicli passati.** È vivente e sostituito: la storia sta nei `CHG`
  e nelle `REL`. Se conservi dodici piani, ne hai dodici che sembrano attuali.
