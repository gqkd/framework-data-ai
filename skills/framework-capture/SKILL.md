---
name: framework-capture
description: Porta informazione dentro il framework di documentazione Data & AI, scrivendola nel documento autorevole e aggiornando in modo coerente tutti i file collegati. Usa questa skill in due situazioni. Primo, quando l'utente ha documenti di business da ingestare — presentazioni, pitch deck, PDF, analisi dei requisiti, offerte, contratti — e dice cose come "ingesta questi documenti", "ho questi PowerPoint del commerciale", "parti da questi PDF", "estrai i requisiti da qui". Secondo, e più spesso, quando l'utente comunica conversazionalmente un'informazione da registrare: una decisione presa, un impegno preso verso un cliente, una definizione di un termine o di una metrica, un vincolo, un rischio, una richiesta di un cliente, un incidente, o una correzione di qualcosa già scritto — anche senza nominare nessun file. Frasi come "abbiamo deciso di usare X", "il cliente vuole Y", "in realtà il dato arriva ogni ora", "aggiungi che", "registra che", "un cliente attivo è chi", "non possiamo far uscire i dati dall'UE" devono attivare questa skill. Attivala anche quando l'utente chiede di aggiornare la documentazione dopo una conversazione, o di sistemare i file perché qualcosa è cambiato.
---

# Framework capture

Un'informazione entra nel framework in un solo modo: **classificata, scritta nella sua unica
fonte autorevole, e propagata ai file che devono cambiare con lei.** Questa skill fa quello.

Leggi `FRAMEWORK.md` del repository prima di scrivere qualsiasi cosa: definisce le classi di
artefatto e la regola della fonte unica, che sono i due vincoli che governano ogni scrittura.

## Le due modalità

| Modalità | Quando | Riferimento da leggere |
|---|---|---|
| **A · Corpus** | L'utente ha documenti da ingestare (pptx, pdf, docx, analisi requisiti) | `references/ingest-bulk.md` |
| **B · Conversazionale** | L'utente comunica un'informazione parlando | questo file, §Modalità B |

Entrambe usano **`references/routing-table.md`**, che è l'unica fonte della logica di
classificazione, della cascata e della gestione dei conflitti. Leggila sempre: non tenerla a
memoria e non riassumerla, perché è il file che tiene allineate le due modalità.

---

## Modalità B — Conversazionale

### Non registrare frase per frase

Una conversazione è in gran parte ragionamento ad alta voce. Trattare ogni affermazione come
un fatto da archiviare produce un registro di rumore in cui i fatti veri diventano
irreperibili — e siccome il registro è la fonte da cui lavorerà un agente, il danno si
propaga.

Il modello è la **raccolta a fine sessione**: tieni traccia delle affermazioni registrabili e
presentale insieme quando la conversazione arriva a un punto di riposo, o quando l'utente lo
chiede. Vedi `routing-table.md §6` per la forma dell'elenco.

Due eccezioni da scrivere subito: un **incidente** (il valore dipende dall'ora esatta) e un
**impegno fuori portata** appena emerso (è il rischio più grande del progetto).

### Procedura per ogni affermazione

1. **Classifica** con `routing-table.md §1`. La distinzione che conta non è l'argomento ma la
   forza epistemica: la stessa frase può essere una promessa, una convinzione o
   un'osservazione, e le tre vanno in posti diversi. Se non è distinguibile dal contesto,
   **chiedi** — è la domanda che paga di più.

2. **Verifica i conflitti** con `routing-table.md §4` prima di scrivere. Un conflitto
   rilevato è il risultato più utile della skill. Non risolverlo scegliendo il più recente:
   mostra le due versioni con la loro provenienza e chiedi.

3. **Rispetta la classe** dell'artefatto di destinazione. Vivente si modifica, immutabile si
   supersede, append-only si estende. Su un immutabile la tentazione di correggere in luogo è
   forte e va rifiutata: quel documento registra cosa si credeva allora.

4. **Propaga la cascata** con `routing-table.md §2`. È la parte che rende "coerente" il
   cambiamento e la ragione per cui questa skill esiste: scrivere in un file solo è facile,
   scrivere nei quattro giusti no.

5. **Decidi se applicare o proporre** con `routing-table.md §5`. In breve: una destinazione
   sola, append-only, nessuna ambiguità, nessun conflitto → applica. Tutto il resto →
   proponi il diff e attendi.

6. **Verifica** con `validate.py` della skill `framework-audit`. Non ricontrollare a mano
   quello che uno script controlla meglio.

### Esempio

Utente: «alla fine andiamo con Postgres, e comunque il cliente attivo per noi è chi ha fatto
login negli ultimi 30 giorni»

Due affermazioni di tipo diverso, con cascate diverse:

**Decisione** → `DEC-NNN` nuovo, `scope: architecture`. Cascata: `ARC.md` aggiornata nello
stesso passaggio, `OD-005` di `OPEN.md` spostata in §4 con il rimando, `product.yaml`
rigenerato. Quattro file, un immutabile coinvolto → **proponi il diff.**

**Definizione** → `GLOSSARY.md`. Prima però controlla: il termine c'è già? Un `DC` ha un
campo con quella semantica? Un altro prodotto calcola la stessa metrica con un'altra formula?
Se sì → conflitto, ti fermi e lo mostri. Se no → cascata su `DC` se il termine è un campo.

Nota cosa **non** fai: non aggiungi la definizione in `PBR`, non la ripeti nel `DC`. Vive in
un posto solo e altrove si linka. È la regola della fonte unica, ed è ciò che impedisce alle
due copie di divergere.

---

## Modalità A — Corpus business

Leggi `references/ingest-bulk.md` per la procedura completa. Le tre cose da sapere prima:

**Questi documenti non sono una specifica.** Sono la registrazione di ciò che è stato
promesso, prodotta da chi doveva vendere. La destinazione principale è `COMMITMENTS.md`, non
un documento di prodotto. Trattarli come requisiti è il modo in cui si costruisce un prodotto
a partire da una slide.

**Passa per `ING.md`, non scrivere diretto negli artefatti.** Il registro di ingestione
conserva la provenienza (documento + slide), fa da coda di revisione interrompibile, e
permette di respingere un'affermazione conservando il fatto che il business l'ha detta.

**L'output di maggior valore sono le contraddizioni.** Tre documenti scritti da persone
diverse in otto mesi si contraddicono, e nessuno lo sa perché nessuno li ha letti tutti di
fila. Confrontarli sistematicamente è la sola cosa che nessuno farebbe a mano.

### L'estrazione la esegui tu

L'utente mette i file in una cartella e te lo dice. Non chiedergli di lanciare comandi:
il senso della skill è che non debba.

Le cartelle sono fisse:

| Il documento parla di… | Cartella |
|---|---|
| Un prodotto solo | `products/<prodotto>/corpus/` |
| Più prodotti, o della suite | `corpus/` alla radice |

**1 · Verifica le dipendenze prima di estrarre.**

```bash
python -c "import markitdown, docx; print('ok')"
```

Se fallisce, **fermati e dillo**. Senza `markitdown` un `.pptx` produce zero blocchi *e
nessun errore*: l'estrazione riesce e non contiene niente, e un corpus non letto è
indistinguibile da un corpus vuoto. L'installazione è `pip install -r requirements.txt`.
Per i `.pdf` serve anche `poppler` sul `PATH`.

**2 · Estrai, una cartella per volta**, saltando quelle che contengono solo il `README.md`:

```bash
python skills/framework-capture/scripts/extract.py products/<prodotto>/corpus \
    -o ingest-out/<prodotto> --jsonl
```

L'output è rigenerabile e non versionato. Tienilo separato per prodotto: serve a sapere da
quale corpus viene un'affermazione quando due prodotti promettono la stessa cosa in modo
diverso, che è la contraddizione più cara da scoprire tardi.

**3 · Guarda le pagine che lo script segnala.** Sono quelle con poco testo, cioè quelle in
cui la promessa architetturale è *disegnata*: tre box con delle frecce e la scritta
«piattaforma unica» non producono nessun testo estraibile e sono un vincolo di tenancy.

Se le ha rasterizzate in `ingest-out/<prodotto>/render/`, **aprile con lo strumento di
lettura file**: sono immagini, leggerle è parte dell'estrazione e non un supplemento
facoltativo. Se non ha potuto rasterizzarle — succede con pptx e docx senza LibreOffice —
lo script nomina il file e le pagine: chiedi all'utente di aprirle e di descriverti cosa
c'è, invece di classificare quel documento senza averle viste.

---

## Il limite da non superare

Questa skill può **strutturare, classificare, collegare, propagare e generare da fonti
esistenti**. Non può **produrre evidenza**.

Non generare il contenuto di `EVD`, `DFB`, o di un `PRB` che affermi fatti non dichiarati da
nessuno. Un evidence brief costruito da un pitch deck passa qualsiasi validatore, sembra
vero, e non contiene informazione — ed è indistinguibile dalla versione buona a un'ispezione
rapida, quindi non lo scopri finché una decisione presa su quella base non si rivela
sbagliata.

Se un documento risponde a «cosa abbiamo osservato», lo scrive l'utente. Tu puoi predisporre
la struttura e dire cosa manca.
