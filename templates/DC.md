---
schema: framework/data-contract/v1
artifact_type: data-contract
lifecycle: living
status: active
id: DC-NNN
version: 1.0.0
products: [prodotto-a]
consumers: [prodotto-b]
owners: [NOME]
created: AAAA-MM-GG
last_review: AAAA-MM-GG HH:MM
classification: internal
---

# DC-NNN · Data contract — Nome del dataset o interfaccia

**Domanda:** cosa può aspettarsi chi consuma questi dati, e chi risponde se si rompe?

**Priorità.** I contratti *fra i tre prodotti* vengono prima di quelli verso l'esterno.
Sono contratti con te stesso a sei mesi di distanza, e sono quelli che romperai in
silenzio.

## Schema

| Campo | Tipo | Nullable | Chiave | PII | Semantica |
|---|---|---|---|---|---|
| | | | PK/FK | sì/no | link a `GLOSSARY` |

## Garanzie

| Garanzia | Valore | Come si verifica |
|---|---|---|
| Freschezza | max N minuti/ore dall'evento | |
| Completezza | ≥ N% righe attese | |
| Unicità | chiave unica al 100% | |
| Valori ammessi | enum per campo | |

**È la sezione per cui il documento esiste.** Lo schema lo deduci dal database in trenta
secondi; le garanzie no, sono l'unica informazione non ricavabile da nessun'altra parte.

## Frequenza di aggiornamento

## Consumatori noti

Chi legge questo dato. Se un prodotto compare qui, deve comparire anche nella sezione
complementarità del suo `PBR`.

## Politica di breaking change

- Cosa consideriamo breaking: rimozione di campo, cambio di tipo, cambio di semantica a
  schema invariato (il più insidioso, perché non lo rileva nessun controllo automatico)
- Preavviso dovuto ai consumatori
- Durata del periodo di doppia scrittura
- Come si versiona

## Storico versioni

| Versione | Data | Cambiamento | Breaking | `DEC` |
|---|---|---|---|---|

---

## Anti-pattern

- **Schema senza garanzie.** Il documento perde la sua unica ragione di esistere.
- **Semantica non collegata al `GLOSSARY`.** Nasce così la stessa metrica calcolata in due
  modi in due prodotti.
- **Cambiare la semantica lasciando lo schema.** È il breaking change che nessun controllo
  automatico rileva e che rompe i consumatori in silenzio.
- **Consumatori non elencati.** Non saprai chi avvisare, quindi non avviserai nessuno.
- **Nessun `DC` fra i tuoi prodotti** perché "è tutto mio". È esattamente il caso in cui
  serve di più.
