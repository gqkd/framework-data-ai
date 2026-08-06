---
schema: framework/problem-statement/v1
artifact_type: problem-statement
lifecycle: immutable
status: active
id: PRB-NNN
products: [prodotto-a]
owners: [NOME]
created: AAAA-MM-GG
classification: internal
---

# PRB-NNN · Titolo del problema

**Domanda:** quale problema, di chi, e quanto costa non risolverlo?

**Nota sulla classe:** immutabile. Il valore di questo documento è proprio non essere
aggiornato: fra sei mesi vorrai sapere cosa credevi all'inizio. Se la comprensione cambia,
scrivi un nuovo `PRB` che supersede questo.

## Chi lo vive

Ruolo concreto, non "gli utenti". Quante persone, in quale contesto, con quale frequenza.

## Cosa fa oggi e cosa gli costa

Il comportamento attuale e il suo costo: tempo, errori, denaro, occasioni perse. Con
numeri se ci sono, con la dichiarazione "non quantificato" se non ci sono.

## Come lo misuriamo oggi

La metrica esistente, oppure la frase esplicita **"oggi non lo misuriamo"** — che è
un'informazione, non una lacuna del documento.

## Cosa succede se non facciamo nulla

Lo scenario base. Se la risposta è "niente di grave", il problema probabilmente non
merita un progetto.

## §Confini

Cosa **non** è questo problema. Problemi vicini che qualcuno confonderà con questo.

## Discovery inversa

*Compila solo se la soluzione è già stata promessa commercialmente.* Quale soluzione è
stata venduta, e quale problema stiamo cercando a posteriori di far corrispondere.
Dichiararlo apertamente: la documentazione onesta di una discovery inversa vale più di una
discovery in avanti simulata. Rimando a `COMMITMENTS`.

---

## Anti-pattern

- **Contenere già la soluzione.** Se il titolo nomina una tecnologia — "serve una
  dashboard", "serve un modello predittivo" — non è la formulazione di un problema ma una
  soluzione travestita, e da quel momento tutta la discovery lavorerà per confermarla.
- **"Gli utenti" come soggetto.** Se non riesci a nominare un ruolo, non hai ancora capito
  chi ha il problema.
- **Zero quantificazione e zero ammissione di non averla.** Una delle due deve esserci.
- **Aggiornarlo.** È immutabile. Aggiornarlo cancella la tracciabilità di come è
  cambiata la comprensione.
