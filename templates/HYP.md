---
schema: framework/hypothesis/v1
artifact_type: hypothesis
lifecycle: immutable
status: open
id: HYP-NNN
products: [prodotto-a]
owners: [NOME]
created: AAAA-MM-GG
derives_from: [PRB-NNN]
classification: internal
---

# HYP-NNN · Titolo dell'ipotesi

**Domanda:** cosa crediamo sia vero, e come faremo a scoprire di aver sbagliato?

`status`: `open | confirmed | refuted | partially-confirmed`

## L'ipotesi

> Crediamo che **[intervento]** per **[chi]** produca **[effetto misurabile]**.

Una frase. Se non ci sta in una frase, sono più ipotesi e vanno separate.

## Assunzioni, ordinate per rischio

| # | Assunzione | Rischio se falsa | Come si testa | Costo del test |
|---|---|---|---|---|
| 1 | | | | |

**L'ordine è la parte che conta.** La prima assunzione della lista è ciò che vai a
testare per primo: questa tabella pilota l'intera fase 2, più di qualsiasi altro
documento.

## Cosa ci farebbe abbandonare l'ipotesi

Condizione osservabile. Se non riesci a scriverla, non hai un'ipotesi.

## Confidenza iniziale

`alta | media | bassa`, con una riga di motivo.

## Esito

*Compilato al gate.* Confermata, smentita, parzialmente. Rimando a `EVD` e al `DEC` del
gate.

---

## Anti-pattern

- **Ipotesi non falsificabile.** "Migliorare l'esperienza utente" non è un'ipotesi: è un
  desiderio. Il test è se riesci a scrivere cosa la smentirebbe.
- **Assunzioni non ordinate.** Un elenco piatto non ti dice da dove cominciare, e
  comincerai da quella più facile invece che da quella più rischiosa.
- **Effetto non misurabile.** Se l'effetto non ha una metrica in `GLOSSARY`, aggiungila
  prima di procedere.
- **Una sola ipotesi per un problema complesso.** Se ne hai una sola, probabilmente hai
  già deciso e stai documentando a posteriori.
