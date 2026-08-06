---
schema: framework/data-feasibility/v1
artifact_type: data-feasibility
lifecycle: immutable
status: active
id: DFB-NNN
products: [prodotto-a]
owners: [NOME]
created: AAAA-MM-GG
derives_from: [HYP-NNN]
classification: internal
---

# DFB-NNN · Data feasibility brief

**Domanda:** i dati che servono esistono, sono accessibili, e sono abbastanza buoni?

**Perché è il gate più economico del framework.** Due giorni qui risparmiano mesi. È il
documento che la maggior parte dei progetti data salta, ed è il motivo per cui la maggior
parte dei progetti data slitta.

**Nota sulla classe:** immutabile nel verdetto. L'inventario delle fonti *gradua* nei `DC`
della fase F4, quindi questo documento non resta da mantenere.

## Fonti

| Fonte | Sistema | Owner | Accesso | Freschezza | Volume | Storico | PII |
|---|---|---|---|---|---|---|---|
| | | | come si ottiene | latenza reale | righe/GB | da quando | sì/no |

## Qualità osservata

**Osservata, non dichiarata.** Numeri ottenuti interrogando i dati, con la query o lo
script allegato.

| Fonte | Completezza | Duplicati | Chiavi nulle | Anomalie | Campione |
|---|---|---|---|---|---|
| | % | % | % | | n righe, periodo |

## Gap

Cosa non c'è, cosa costerebbe averlo, e chi dovrebbe produrlo.

## Compliance

Base giuridica del trattamento · retention · trasferimenti extra-UE · decisioni
automatizzate. Ogni voce genera una riga in `RSK §stato`.

## Verdetto

`fattibile` · `fattibile con riserva` · `non fattibile ora`

Con la riserva o il blocco espressi come condizione osservabile. Rimando al `DEC` del gate
G3.

---

## Anti-pattern

- **Compilarlo leggendo la documentazione dello schema.** L'intero valore sta nell'aver
  guardato i dati. Se non hai eseguito una query, non hai scritto un `DFB`.
- **Qualità "buona".** Serve una percentuale, non un aggettivo.
- **Freschezza dichiarata dal fornitore del dato.** Misurala.
- **Verdetto "fattibile" con gap non quantificati.** Un gap senza costo stimato è un
  verdetto rinviato, non un verdetto.
- **Omettere la compliance perché "sono dati interni".** I dati interni contengono dati
  personali di dipendenti e clienti.
