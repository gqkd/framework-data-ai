---
schema: framework/workflow/v1
artifact_type: workflow
lifecycle: living
status: active
version: 1.0.0
products: [prodotto-a]
owners: [NOME]
created: AAAA-MM-GG
last_review: AAAA-MM-GG HH:MM
derives_from: [PRB-NNN]
classification: internal
---

# Workflow — Nome del processo

**Domanda:** come funziona il processo oggi, come funzionerà, e cosa cambia esattamente?

**Un solo file, tre sezioni.** Il target ha senso solo in contrapposizione al corrente e
il valore sta nel delta: file separati produrrebbero due diagrammi che divergono. Per
riferimenti puntuali usa gli anchor: `WF.md#target`.

---

# §corrente

Come funziona **davvero** oggi, incluse le scorciatoie.

## Passi

| # | Chi | Cosa fa | Sistemi e file toccati | Dove nasce il dato |
|---|---|---|---|---|
| 1 | | | nomi reali: quale tabella, quale Excel, quale cartella | creato / copiato |

La colonna dei sistemi vuole i **nomi reali**. È la mappa dato → sistema, e per un agente
è l'unica fonte da cui sapere dove risiede un'informazione.

## Punti di dolore

Numerati, ciascuno con rimando all'evidenza in `EVD` che lo documenta.

## Workaround esistenti

Gli Excel ombra, i copia-incolla, i messaggi su chat. Sono la parte più informativa del
documento, non l'imbarazzo da omettere: un workaround è un requisito che qualcuno ha già
implementato a mano.

---

# §target

## Passi

Stessa tabella del corrente, in versione target.

## Cosa resta manuale, e perché

Sezione obbligatoria. Scelta deliberata, non omissione. Nei sistemi AI *dove sta l'umano*
è una delle decisioni più costose da cambiare dopo: rimanda al `DEC` che la fissa.

## Impatto sui ruoli

Chi, da domani, fa una cosa diversa. Chi perde un pezzo di lavoro. Chi ne guadagna uno.

## Requisiti che ne derivano

---

# §delta

Passo per passo: cosa scompare, cosa nasce, cosa cambia solo di attore. Generabile, ma
tenerlo esplicito è utile perché è ciò che si legge in una revisione.

---

## Anti-pattern

- **Descrivere il processo ufficiale invece di quello reale.** Se il §corrente sembra
  ordinato, non l'hai osservato: l'hai chiesto a chi lo ha progettato.
- **Sistemi generici.** "Il CRM" non serve a nessuno. Serve quale tabella.
- **Nessuna riga in "cosa resta manuale".** Significa che stai promettendo automazione
  totale, e non è vero.
- **Aggiornare il §target senza aggiornare il §delta.** Il delta diventa una bugia
  silenziosa, che è peggio di un delta assente.
