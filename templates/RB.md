---
schema: framework/runbook/v1
artifact_type: runbook
lifecycle: living
status: active
version: 1.0.0
products: [prodotto-a]
owners: [NOME]
created: AAAA-MM-GG
last_review: AAAA-MM-GG HH:MM
classification: internal
---

# Runbook, SLO e monitoring — Nome prodotto

**Domanda:** come si tiene in vita, e come sappiamo che sta andando male prima che ce lo
dicano?

**Prova del nove:** una persona nuova riesce a ri-eseguire una pipeline fallita leggendo
solo questo documento, alle tre di notte, senza chiedere niente a nessuno.

## Operazioni

Comandi **reali e copiabili**, non descrizioni.

```bash
# avvio
# arresto
# ri-esecuzione di un job fallito
# rollback all'ultima release buona (vedi RLM per il target)
```

## Dipendenze

| Dipendenza | Cosa succede se cade | Degradazione accettabile |
|---|---|---|

## SLO

| SLO | Target | Finestra | Error budget |
|---|---|---|---|
| Freschezza del dato | | | |
| Disponibilità | | | |
| Qualità del dato | | | |
| Accuratezza in produzione | | | |

## Monitoring

| Cosa monitoriamo | Soglia di allerta | Dove | Chi riceve |
|---|---|---|---|
| Output: metriche di qualità | | | |
| **Input: qualità e volume dei dati in ingresso** | | | |
| Drift della distribuzione | | | |
| Costo per unità | | | |

**Nei sistemi data e AI monitorare l'output non basta: va monitorato l'input.** La maggior
parte dei fallimenti silenziosi entra dai dati, non dal codice, e non solleva nessuna
eccezione.

## Failure mode noti

| Sintomo osservabile | Causa probabile | Azione |
|---|---|---|

## Escalation

Chi si sveglia, in che ordine, entro quanto.

---

## Anti-pattern

- **Descrivere l'architettura invece dei comandi.** L'architettura sta in `ARC`. Qui serve
  cosa digitare.
- **Comandi non testati.** Un comando nel runbook che non funziona è peggio di nessun
  comando: consuma i minuti in cui servirebbe pensare.
- **Monitorare solo l'output.** Vedi sopra.
- **Nessun costo per unità nel monitoring.** Nei sistemi AI il costo è il modo più comune
  in cui un sistema funzionante diventa insostenibile.
- **SLO senza error budget.** Un target che non si può sforare non è un obiettivo, è un
  desiderio, e verrà ignorato al primo incidente.
