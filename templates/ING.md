---
schema: framework/ingestion-register/v1
artifact_type: ingestion-register
lifecycle: append-only
status: active
products: [prodotto-a, prodotto-b, prodotto-c]
owners: [NOME]
created: AAAA-MM-GG
classification: confidential
---

# Registro di ingestione del corpus business

**Domanda:** cosa affermano i documenti prodotti dal business, dove è scritto esattamente, e
cosa ne abbiamo fatto?

**Perché non si scrive diretto negli artefatti definitivi.** Tre ragioni concrete:

- **Provenienza.** Qui resta il rimando a documento e slide. Nell'artefatto definitivo quella
  traccia si perde, e ne avrai bisogno ogni volta che un'affermazione va verificata.
- **Coda di revisione.** Duecento slide producono più affermazioni di quante se ne valutino in
  una sessione. Questo registro è lo stato del lavoro e ti permette di interromperti.
- **Rifiuto tracciato.** Puoi respingere un'affermazione conservando il fatto che il business
  l'ha detta — esattamente ciò che serve quando fra otto mesi qualcuno chiede perché quella
  funzionalità non c'è.

**Append-only:** le righe non si modificano. Cambia solo la colonna `Esito`, e se cambia una
valutazione si aggiunge una riga nuova che rimanda alla precedente.

## §affermazioni

| ID | Documento | Posizione | Verbatim | Tipo | Destinazione | Esito |
|---|---|---|---|---|---|---|
| ING-001 | offerta-cliente.pptx | slide 1 | "Un'unica esperienza per i tre moduli" | vincolo travestito da claim | `OPEN.md` OD-003 | instradato |
| ING-002 | offerta-cliente.pptx | slide 2 | "Riduzione del 30% del tempo di riconciliazione" | obiettivo numerico | `CMT-004` + soglia `EVP` | instradato |
| ING-003 | offerta-cliente.pptx | slide 2 | "Cliente attivo: chi ha operato negli ultimi 30 giorni" | definizione | `GLOSSARY` | instradato |

`Tipo`: usa la tassonomia di `routing-table.md §1`.

`Esito`: `da valutare` · `instradato` · `respinto` · `rinviato` · `contraddizione`

Per `respinto` la ragione è obbligatoria: è l'informazione per cui il registro esiste.

## §contraddizioni

La parte di maggior valore del registro. Ogni voce porta **entrambe** le provenienze.

| ID | Affermazione A | Fonte A | Affermazione B | Fonte B | Natura | Dove è finita |
|---|---|---|---|---|---|---|
| ING-C01 | "Dati in tempo reale" | offerta-cliente.pptx slide 2 | "Aggiornamento ogni ora, batch notturno esistente" | analisi-requisiti.docx §Vincoli | promessa temporale incompatibile | `OPEN.md` OD-011 |

**Se le due versioni sono state dette a due clienti diversi**, non è una decisione tecnica: è
un impegno da rinegoziare, va in `COMMITMENTS §Fuori portata` e va segnalato subito. Due
clienti a cui è stato promesso il contrario è un problema che si risolve solo parlandone.

## §da guardare

Slide e pagine segnalate da `extract.py` come povere di testo, cioè probabilmente grafiche.

| Documento | Pagine | Guardato | Cosa conteneva |
|---|---|---|---|
| offerta-cliente.pptx | 3 | sì | diagramma a tre box: implica tenancy condivisa → OD-003 |

Su un deck commerciale il vincolo architetturale è spesso disegnato, non scritto. La colonna
`Guardato` esiste perché la tentazione di saltare questo passaggio è forte.

## §bilancio

Compilato alla fine di ogni lotto di ingestione.

- Documenti processati:
- Affermazioni classificate:
- Instradate / respinte / rinviate:
- **Contraddizioni trovate:**
- **Impegni risultati fuori portata:**

---

## Anti-pattern

- **Estrarre tutto per completezza.** Un deck di quaranta slide contiene forse quindici
  affermazioni con conseguenze. Il resto è narrazione commerciale, e includerla rende
  irreperibile ciò che conta.
- **Verbatim parafrasato.** La colonna si chiama verbatim per un motivo: l'ambiguità
  dell'originale è precisamente l'informazione che serve per negoziare.
- **Nessuna riga in `§contraddizioni`.** Con tre o più documenti scritti da persone diverse
  non significa che non ci siano: significa che non li hai confrontati.
- **Trattare il corpus come una specifica.** È la registrazione di ciò che è stato promesso.
  Destinazione principale `COMMITMENTS`, non un documento di prodotto.
- **Saltare `§da guardare`.** È dove stanno i vincoli architetturali che nessuno ha scritto.
