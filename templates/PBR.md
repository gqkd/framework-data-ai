---
schema: framework/product-brief/v1
artifact_type: product-brief
lifecycle: living
status: active
version: 1.0.0
products: [prodotto-a]
owners: [NOME]
created: AAAA-MM-GG
last_review: AAAA-MM-GG HH:MM
derives_from: [PRB-NNN, HYP-NNN, CMT-NNN]
classification: internal
---

# Product brief — Nome prodotto

**Domanda:** qual è il prodotto corrente, per chi, quale outcome produce, quali
comportamenti supporta?

**Perché esiste.** È la controparte prodotto di `ARC`: quel documento dice com'è fatto il
sistema, questo dice cosa è il prodotto. Senza, il reshaping produce solo artefatti
architetturali e le decisioni di prodotto restano orali. Se il prodotto è già stato
venduto, questa definizione oggi esiste solo dentro dei pitch: scriverla è il primo atto.

## Una riga

Cosa fa, per chi, con quale effetto.

## Attori

| Ruolo | Cosa ottiene | Come lo misuriamo |
|---|---|---|
| | | |

Distingui **utente** (usa) da **buyer** (paga) da **owner del processo** (subisce il
cambiamento). Spesso sono tre persone diverse con interessi divergenti.

## Outcome

Cosa cambia nel mondo se il prodotto funziona. Non funzionalità: effetti.
Ogni outcome ha una metrica dal `GLOSSARY`, con valore attuale e target.

## Capability attuali

Cosa il prodotto fa **oggi**, non cosa farà. Ogni capability con `stato: live |
in-build | shaped | pitched`.

`pitched` è il caso da nominare per primo: **promessa in un documento commerciale, senza
nessun design dietro.** È lo stato più pericoloso che una capability possa avere, perché a
chi legge un pitch è indistinguibile da `live`, e senza una parola per dirlo finisce
silenziosamente fra le altre tre. Se una riga è `pitched`, il `PBR` deve dire *in quale
documento* è stata promessa.

## §Fuori scope

Cosa il prodotto **non** fa, deliberatamente, con la ragione. Sezione obbligatoria.

È la sezione più letta dagli agenti: impedisce di implementare con entusiasmo qualcosa che
avevi valutato e scartato. Ogni voce con un rimando al `DEC` che l'ha esclusa, dove esiste.

## Complementarità con gli altri prodotti

Cosa questo prodotto assume che facciano gli altri due, e cosa offre loro. I punti di
contatto qui elencati devono corrispondere a un `DC` interno: se non c'è, è un'integrazione
implicita, cioè un debito.

## Metriche di prodotto

Nome, definizione in `GLOSSARY`, valore attuale, target, chi lo guarda.

## Vincoli

Commerciali (da `COMMITMENTS`), normativi, tecnici, di costo.

## Release corrente

Riferimento a `REL` e `RLM`. Campo generato.

---

## Anti-pattern

- **Elencare funzionalità invece di outcome.** Un elenco di feature non permette a nessuno
  di decidere cosa tagliare quando serve tagliare.
- **Confondere utente e buyer.** Nei prodotti B2B chi usa e chi paga vogliono cose
  diverse; un brief che li fonde produce un prodotto che non soddisfa né l'uno né l'altro.
- **Descrivere il prodotto immaginato.** Questo documento è vivente: descrive oggi. Il
  futuro sta in `RMP`.
- **Fuori scope vuoto.** Significa che non hai ancora deciso niente, oppure che le
  decisioni sono orali.
- **Complementarità dichiarata a parole senza un `DC`.** È il modo in cui tre prodotti
  diventano uno inseparabile senza che nessuno l'abbia deciso.
