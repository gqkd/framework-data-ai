---
schema: framework/signal-log/v1
artifact_type: signal-log
lifecycle: append-only
status: active
products: [prodotto-a]
owners: [NOME]
created: AAAA-MM-GG
classification: internal
---

# Registro segnali — Nome prodotto

**Domanda:** cosa è stato osservato, quando?

**Un solo registro per tutti i segnali.** Non esiste un documento "feedback" separato: il
`type` distingue. Il motivo non è risparmiare un file, è che il change intake abbia **una
sola fonte** invece di due che si contendono la priorità.

**Append-only, e questo ha una conseguenza importante.** Al momento dell'osservazione non
conosci causa, rimedio né change generata: non si aggiorna la riga, si aggiungono eventi
collegati.

```
SIG-014   segnale osservato
ANA-014   analisi di SIG-014
DEC-031   decisione presa su ANA-014
CHG-052   change generata da DEC-031
```

## Segnali

| ID | Data | Type | Osservato | Impatto | Chi/Dove | Collegati |
|---|---|---|---|---|---|---|
| SIG-001 | AAAA-MM-GG | incident | | | | ANA-001, CHG-004 |

`type`: `incident` · `drift` · `feedback` · `request` · `metric` · `compliance`

## Analisi

Solo per i segnali che ne richiedono una. Post-mortem completo solo per gli eventi
significativi.

### ANA-NNN · su SIG-NNN

Causa · come l'abbiamo capito · cosa avrebbe permesso di accorgersene prima · rimando al
`DEC` se ne è nata una decisione.

## Feedback verbatim

Per i segnali `type: feedback`, il testo originale **con le parole di chi l'ha detto**.

Il valore sta nel non tradurlo subito in requisito: le parole originali sono l'unica cosa
che consente di ri-interpretare un segnale fra sei mesi, quando avrai capito meglio il
dominio. Un requisito già tradotto ha perso informazione in modo irreversibile.

### SIG-NNN

> testo originale

---

## Anti-pattern

- **Tenerlo solo per gli incidenti gravi.** Il drift lento non è un incidente e non lo
  noterai mai senza registro.
- **Registro vuoto.** Il change intake si nutrirà solo di richieste esplicite, cioè della
  voce di chi parla più forte, non di ciò che il sistema sta segnalando.
- **Aggiornare una riga con la causa scoperta dopo.** Rompe la classe append-only e
  cancella la sequenza temporale, che è l'unica cosa che questo documento sa fare.
- **Tradurre il feedback in requisito al momento della raccolta.**
