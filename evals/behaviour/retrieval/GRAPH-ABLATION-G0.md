# Qualificazione G0 del grafo — 16 settembre 2026

## Esito

**Misura preliminare completata: 4/4 casi (100%). Gate G0 complessivo non superato.
Nuove prove con agente: 0/8 (0%). Controlli offline: 115/115 superati (100%).**

Con i quattro seed dichiarati prima della misura, attraversare il grafo non aggiunge
alcun gruppo di fonti richiesto dalle rubriche. Non avvio le otto chiamate G1:
manca il caso positivo di scoperta richiesto dal piano, oltre alla qualificazione
dell'isolamento del runner. Non e' una bocciatura generale del grafo e non e' un
test di comprensione del modello. E' un limite misurato di questa configurazione
di retrieval sul corpus legacy sintetico.

## Confronto effettivamente eseguito

- Runtime unico: 3.8.1, commit faaf42259c7b43dfecbd1c52df21b2c4788cfc50.
- Stesso corpus, nessun arricchimento di metadati, nessuna modifica al framework.
- Seed manuali in GRAPH-ABLATION-SEEDS.json, salvati prima della prima misura.
  Sono normalizzazioni di casi development gia' esplorati, non query scelte da
  un modello cieco. La scelta spreadsheet aveva gia' avuto una sonda: e' dichiarato.
- Ricerca literal, limite 20, relazioni predefinite, zero salti contro due salti.
  Questi sono limiti del retrieval esplicitamente fissati, non limiti di durata
  o token per risposte LLM. Non sono state eseguite risposte LLM.
- Tutte le query e i loro output sono registrati prima del caricamento delle
  rubriche per lo scoring. La ricostruzione del dataset include anche l'oracle:
  esso non viene passato alla costruzione dei seed o ai comandi del motore.
- Vengono contati solo nodi documento selezionati con corpo esportato.
  Le fonti di provenienza di un nodo/arco non valgono come documenti trovati.
  Anche i corpi esportati non provano lettura o comprensione da parte di un LLM.

| Caso | Seed | Gruppi richiesti, senza traversal | Con traversal | Documenti aggiunti |
|---|---|---:|---:|---|
| R007: autorizzazione del segnale | SIG-001 | 2/4 | 2/4 | Nessuno |
| R013: rinomina dell'interfaccia | item_key | 2/4 | 2/4 | DEC-005, non richiesto dalla rubrica minima |
| R019: regola condivisa e test | identifier | 2/6 | 2/6 | Nessuno |
| R022: proposta contro decisione | spreadsheet | 3/3 | 3/3 | Nessuno |

Totale descrittivo: 9/17 gruppi in entrambi i bracci (52,9%).
**Zero nuovi gruppi richiesti non significa zero informazione utile:** in R013
la decisione aggiunta puo' aiutare a motivare il vincolo. Non e' lecito
classificarla come rumore soltanto perche' non appartiene alla rubrica minima.
Il suo effetto sulla risposta non e' stato misurato.

## Perche' il confronto e' poco informativo

1. **Documento trovato e voce collegata non coincidono.** Per R007 la ricerca
   testuale seleziona i due LOG. Il collegamento derives_from del CHG punta
   invece al nodo entry di SIG-001. Nel grafo esportato il dato entry.document
   identifica il LOG, ma non c'e' un arco percorribile fra questi due nodi.
   Le relazioni predefinite escludono belongs_to; includerla collegherebbe
   indiscriminatamente documenti attraverso l'ambito del prodotto, non soltanto
   attraverso una dipendenza pertinente. Non l'ho abilitata per far crescere il punteggio.

2. **Il workflow non e' proiettato integralmente.** Il CHG sintetico contiene
   icg: ICG-001 e l'ICG contiene routing: SIG-001. Nell'export, l'ICG ha solo
   belongs_to: quei campi non producono qui una catena navigabile
   segnale → classificazione → mandato. Questo dato e' verificato nell'export,
   non dedotto dall'assenza di risultati della query.

3. **Gran parte delle fonti mancanti e' codice.** Due gruppi in R013 e quattro
   in R019 sono schema, implementazioni o test. Il provider del grafo del
   codice non e' configurato in questa prova; quei file sono comunque leggibili
   direttamente da un agente. Non attribuire al modello questo limite del canale
   documentale, ne' trattare un codice non osservato come impatto nullo.

4. **Per R022 la ricerca lessicale basta gia'.** Trova tutti e tre i documenti
   richiesti. E' un buon controllo senza vantaggio di scoperta, non un caso
   da eliminare per favorire il grafo.

Il grafo contiene 48 nodi e 48 archi, ma 43 archi sono belongs_to;
restano tre derives_from, un supersedes e la relativa inversa affected_by.
I 17 mapping gap restano visibili. Tutte le otto query riportano available
e truncated=false: available non certifica completezza del mapping.

### Correzione di una sonda precedente

Il piano del 15/09 descriveva la query dal CHG come aggiunta del LOG e di DEC-005.
Il LOG compariva fra le fonti di provenienza del nodo SIG, non come documento
selezionato con corpo esportato. La distinzione non era stata mantenuta nel testo.
La correzione e' registrata anche nel piano: quella sonda prova un collegamento
al segnale e alla decisione, non la consegna del corpo del LOG.

### Zero salti non significa assenza del grafo

R019-S restituisce un arco fra nodi gia' selezionati anche con hops=0.
Per le metriche di scoperta qui usate non altera l'esito. Per un esperimento
con agente, invece, il JSON grezzo di S renderebbe disponibili relazioni:
serve un adattatore che separi davvero le due condizioni e un preflight che
ne verifichi l'isolamento. Un divieto scritto nel prompt non basta.

## Verifiche e prove conservate

Implementazione: qualify_graph_ablation.py; test:
tests/memory/test_graph_ablation_qualification.py.

- 15/15 nuovi unit test superati in 0,006 s.
- 100/100 test retrieval preesistenti superati in 8,626 s; i messaggi di
  trial in quella suite vengono dai mock, non da nuove chiamate a un modello.
- Due esecuzioni complete del qualificatore in directory diverse:
  /tmp/framework-graph-ablation-g0-20260916-01 e
  /tmp/framework-graph-ablation-g0-20260916-02.
- Ogni esecuzione ricostruisce gli input dagli oggetti Git locali e dalle
  definizioni sintetiche, verifica l'inventario congelato ed esegue solo
  il runtime ricostruito, non un checkout fornito senza verifica.
- Due build e otto query per esecuzione; build identiche byte per byte;
  inventari invariati prima/dopo. Gli output completi e stderr sono conservati.
- Il registro GRAPH-ABLATION-G0-RESULTS.json riproduce il primo report, con
  hash di manifest, oracle, seed, generatori, inventario runtime e output.
- Codice di errore, JSON invalido e copertura unavailable falliscono il
  qualificatore: non vengono trasformati in risultati vuoti.
- Nessuna installazione, migrazione, rete richiesta dal qualificatore,
  chiamata LLM, modifica ai runtime storici, commit o push.

Lettura per la diagnosi: report e liste dei nodi/archi dell'export;
ICG-001 e CHG-001 sintetici per intero; query.py per intero;
graph.py limitatamente a register_documents, relations e subjects.
Il giudizio e' dell'autore del test, non una revisione indipendente.

## Prossimo passo, senza riscrivere il risultato negativo

Prima di G1 occorre una revisione esplicita del disegno, non altre otto chiamate
identiche e non una nuova ricerca di seed presentata come preregistrata.

1. Conservare questo corpus legacy e le quattro misure come controllo.
2. Preparare una fixture di calibrazione distinta con relazioni realmente
   attraversabili: fonti di partenza esplicite, vincoli collegati con lessico
   diverso, documenti non pertinenti e almeno un caso senza beneficio atteso.
   Stessi contenuti e metadati in entrambi i bracci. Questo misura il potenziale
   del traversal, non il guadagno medio sui progetti esistenti.
3. Congelare nuova verita' attesa e provenienza della revisione prima delle
   risposte. Non spacciare la selezione dell'autore per revisione indipendente.
4. Separare due domande: sa scegliere il nodo iniziale? Una volta scelto,
   il traversal gli fa recuperare vincoli utili? Il primo problema richiede
   valutare il routing; il secondo un confronto a seed identico.
5. Qualificare il runner sullo stesso runtime, impedendo l'accesso involontario
   al grafo nel controllo, poi avviare il blocco G1 aggiornato senza tetti
   artificiali per risposta e senza retry automatici dopo errori o quota.

Eventuali miglioramenti al motore (ponte documento/entry, navigazione del workflow,
indicizzazione dei riferimenti strutturati) sono candidati emersi dai test:
non sono stati implementati ne' introdotti surrettiziamente nel benchmark.
Il grafo del codice resta un esperimento distinto.
