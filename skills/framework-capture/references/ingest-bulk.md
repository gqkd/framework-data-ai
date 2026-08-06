# Modalità A — Ingestione del corpus business

Procedura per il primo caricamento: presentazioni commerciali, PDF, analisi dei requisiti,
documenti prodotti dal business prima che esistesse il progetto tecnico.

## Cosa sono davvero questi documenti

Non sono una specifica. Sono **la registrazione di ciò che è stato promesso**, prodotta da
chi doveva vendere. Confonderli con requisiti è il modo in cui si costruisce un prodotto a
partire da una slide.

Questo determina la destinazione principale: la maggior parte del contenuto va in
`COMMITMENTS.md`, non in un documento di prodotto. Ma il corpus contiene anche cinque cose
di valore diverso, e vanno separate:

| Cosa | Dove va | Perché è preziosa |
|---|---|---|
| **Vocabolario di dominio** | `GLOSSARY.md` | Sono le parole che il cliente userà. Se il tuo sistema le chiama diversamente, ogni conversazione avrà un costo di traduzione |
| **Promesse numeriche** | `COMMITMENTS` **e** soglia in `EVP` | «Riduzione del 30%» è insieme un impegno e un criterio di accettazione. Le due cose non si scollegano |
| **Vincoli travestiti da claim** | `OPEN.md` o `DEC` | «Unica esperienza», «tempo reale», «integrato con» sono decisioni architetturali già prese da chi non sapeva di prenderle |
| **Descrizioni del processo attuale** | `WF §corrente`, marcate come non verificate | Il business descrive il processo del cliente per sentito dire. Utile come punto di partenza, mai come fatto |
| **Concorrenti citati** | `CMP` | Chi è stato nominato in una vendita è chi il cliente ha in mente |

## Procedura

### 1 · Estrai

I file stanno in `products/<prodotto>/corpus/` se parlano di un prodotto solo, in `corpus/`
alla radice se parlano di più prodotti o della suite. **L'estrazione la esegui tu**, una
cartella per volta — l'utente non lancia comandi:

```bash
python -c "import markitdown, docx; print('ok')"      # prima: senza, l'estrazione è vuota
python skills/framework-capture/scripts/extract.py products/<prodotto>/corpus \
    -o ingest-out/<prodotto> --jsonl
```

Produce `extract.md` con un blocco per slide, pagina o sezione, ciascuno etichettato con la
provenienza. Ti serve: dovrai tornare alla slide originale ogni volta che un'affermazione va
verificata, e senza il numero non la ritrovi.

Un output per prodotto, non uno solo per tutto. Quando due prodotti promettono la stessa
cosa in modo diverso, sapere da quale corpus viene ciascuna versione è metà del lavoro di
riconciliazione.

### 2 · Guarda le pagine segnalate

Lo script elenca le slide e pagine con poco testo e, quando può, ne rasterizza le immagini
in `ingest-out/<prodotto>/render/`. **Aprile con lo strumento di lettura file: sono
immagini, e leggerle è parte dell'estrazione.** Su un deck commerciale la promessa
architetturale è spesso disegnata — tre box con delle frecce e la scritta «piattaforma
unica» non producono nessun testo estraibile e sono un vincolo di tenancy.

Quando non può rasterizzare — pptx e docx senza LibreOffice installato — lo script nomina
il file e le pagine. Chiedi all'utente di aprirle e descriverle. Classificare quel documento
saltando questo passaggio significa ingestare tutto tranne la parte che vincola.

Se lo script segnala che un PDF è una presentazione esportata, tratta l'intero documento
come visivo: il testo estratto ha perso il layout, e in un deck il layout porta significato.

### 3 · Classifica in `ING.md`

Per ogni affermazione rilevante, una riga nel registro di ingestione, usando
`references/routing-table.md` per il tipo e la destinazione.

**Non scrivere direttamente negli artefatti definitivi.** Il registro `ING` esiste per tre
ragioni concrete:

- **Provenienza.** La riga conserva il rimando a documento e slide. Nell'artefatto
  definitivo quella traccia si perderebbe, e ne avrai bisogno.
- **Coda di revisione.** Duecento slide producono più affermazioni di quante tu possa
  valutare in una sessione. Il registro è lo stato del lavoro, e ti permette di
  interromperti.
- **Rifiuto tracciato.** Puoi respingere un'affermazione conservando il fatto che il
  business l'ha detta. È esattamente ciò che serve quando fra otto mesi qualcuno chiede
  perché quella funzionalità non c'è.

Sii selettivo. Un deck di quaranta slide contiene forse quindici affermazioni con
conseguenze. Il resto è narrazione commerciale: non estrarla per completezza.

### 4 · Trova le contraddizioni

**È l'output di maggior valore di tutta l'operazione**, e la sola cosa che nessuno farebbe a
mano su duecento slide.

Tre documenti scritti da persone diverse in otto mesi si contraddicono, e nessuno lo sa
perché nessuno li ha mai letti tutti di fila. Confronta sistematicamente:

- **Numeri diversi per la stessa metrica** fra due documenti
- **Promesse temporali incompatibili** — «tempo reale» in un deck, «aggiornamento ogni ora»
  nell'analisi dei requisiti
- **Perimetri diversi** — un modulo presente in un'offerta e assente in un'altra
- **Definizioni divergenti** dello stesso termine di dominio
- **Assunzioni sui dati** che il `DFB` smentirà

Ogni contraddizione produce:

- una riga in `ING` con `type: contradiction` e **entrambe** le provenienze
- una voce in `OPEN.md §1` se richiede una decisione, oppure in `COMMITMENTS` come impegno
  da rinegoziare se le due versioni sono state dette a due clienti diversi

Nel secondo caso, dillo all'utente esplicitamente: due clienti a cui è stato promesso il
contrario è un problema che si risolve solo parlandone, e prima è meglio.

### 5 · Instrada, con conferma

Lavora **per destinazione, non per documento sorgente**: compila `GLOSSARY` in un passaggio
attraversando tutto il corpus, poi `COMMITMENTS`, poi il resto. Produce voci coerenti fra
loro e ti fa notare le divergenze mentre le scrivi, invece che dopo.

Ordine consigliato, che segue la dipendenza reale:

1. `GLOSSARY` — tutto il resto ne userà i termini
2. `COMMITMENTS` — inclusa la sezione `§Fuori portata`
3. `OPEN.md` — vincoli travestiti da claim, e contraddizioni non risolvibili da te
4. `PBR` per prodotto — capability con `stato: shaped`
5. `WF §corrente` — marcato come non verificato
6. `CMP`, `PRB`, `HYP` se il corpus contiene abbastanza materiale. Spesso non è così, ed è
   corretto lasciarli vuoti

Chiedi conferma per destinazione, non per riga: «da tutto il corpus escono queste dodici
voci di glossario, le scrivo?» è una domanda a cui si può rispondere. Dodici domande
separate no.

### 6 · Chiudi con il bilancio

Un riassunto di cinque righe: quante affermazioni classificate, quante instradate, quante
respinte, **quante contraddizioni** e quali impegni risultano fuori portata.

Poi esegui `framework-audit` per verificare che le scritture siano coerenti.

## Cosa non fare

**Non generare `PRB`, `HYP`, `EVD` o `DFB` dal corpus.** Il materiale non contiene evidenza:
contiene affermazioni commerciali. Puoi estrarre un problema *dichiarato* come `PRB` con la
provenienza e la sezione di discovery inversa compilata; non puoi produrre un evidence brief,
perché nessuno ha osservato niente.

Un evidence brief costruito da un pitch deck passa qualsiasi validatore, sembra vero, ed è
esattamente il fallimento che il framework esiste per prevenire.

**Non riassumere il corpus.** Nessuno leggerà il riassunto. Il valore sta nelle affermazioni
estratte, classificate e collegate alla loro slide.
