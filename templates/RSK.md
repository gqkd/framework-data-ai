---
schema: framework/risk-register/v1
artifact_type: risk-register
lifecycle: living
status: active
version: 1.0.0
products: [prodotto-a]
owners: [NOME]
created: AAAA-MM-GG
last_review: AAAA-MM-GG HH:MM
classification: confidential
---

# Registro rischi e compliance — Nome prodotto

**Domanda:** quali rischi conosciamo, in quale stato sono, e cosa abbiamo deciso su
ciascuno?

**Un solo file, tre sezioni.** Un registro rischi non può essere immutabile — deve mostrare
lo stato corrente — ma le accettazioni di rischio sì, e la sequenza degli eventi anche. Tre
regimi in un file, a paragrafi, perché file separati divergerebbero.

---

# §stato

Vivente. La verità corrente. Una riga per rischio.

| ID | Rischio | Categoria | Probabilità | Impatto | Stato | Mitigazione | Owner | Rivisto |
|---|---|---|---|---|---|---|---|---|
| RSK-001 | | tecnico · dati · AI · compliance · commerciale · fornitore | B/M/A | B/M/A | | | | AAAA-MM-GG |

`stato`: `open` · `mitigated` · `accepted` · `transferred` · `closed` · `expired`

`expired` merita attenzione: è un rischio la cui mitigazione era legata a una condizione
che non vale più. Sono i più pericolosi, perché sembrano gestiti.

## Compliance

| Trattamento | Base giuridica | Retention | Extra-UE | Decisione automatizzata | `DC` |
|---|---|---|---|---|---|

Per i sistemi AI, aggiungi: bias noti e come sono stati misurati · human oversight, dove sta
e cosa può ribaltare · spiegabilità disponibile all'utente finale.

---

# §accettazioni

Immutabile. Una voce per rischio accettato: non si modifica, si supersede.

### RSK-NNN accettato il AAAA-MM-GG

Chi ha accettato · perché · esposizione stimata · condizioni sotto cui l'accettazione
decade · `DEC` di riferimento.

Un rischio accettato senza condizione di decadenza è un rischio dimenticato con più
passaggi burocratici.

---

# §eventi

Append-only. Cosa è effettivamente successo, per verificare a posteriori se le stime erano
sensate.

| Data | `RSK` | Evento | `SIG` | Conseguenza |
|---|---|---|---|---|

Questa sezione è l'unico modo per scoprire che valutavi sistematicamente male una categoria
di rischio.

---

## Anti-pattern

- **Registro scritto una volta e mai rivisto.** Un rischio senza `Rivisto` recente non è
  gestito: è archiviato.
- **Tutti i rischi `open`.** Significa che non decidi: valuti.
- **Accettazione senza condizione di decadenza.**
- **Omettere i rischi commerciali** perché "non sono tecnici". Un impegno fuori portata in
  `COMMITMENTS` è il rischio più grande del progetto e appartiene anche qui.
- **Nessuna riga in `§eventi`.** Se non registri gli incidenti anche qui, non saprai mai se
  le tue stime di probabilità valevano qualcosa.
