# Protocollo del benchmark sintetico — v1

## Stato e obiettivo

Il dataset è scritto e verificabile offline. Non è una misura del comportamento
dell'agente e non dimostra risparmio di token. Le rubriche richiedono ancora una revisione
umana indipendente. Non è necessario migrare o leggere alcun repository reale.

Domanda sperimentale: a parità di agente e fatti disponibili, il framework attuale aiuta
a recuperare le fonti necessarie e rispondere correttamente, con quale consumo?
La costruzione di grafi corretti e la capacità dell'agente di cercare sono prove diverse.

## Origine dei documenti

corpus.yaml è narrativa inventata e codice scritto per questo esperimento, non un'importazione
o un'anonimizzazione di documenti esistenti. Il preparatore non accetta una directory di
documenti reali. Riusa solo gli helper di rendering/Git del generatore sintetico precedente.
Nessun modello genera il dataset durante la preparazione.

Tre prodotti: alpha produce identificatori, beta li consuma e ha un ingresso indipendente,
gamma ha solo un design. Tre repository Git locali contengono produttore, consumatore e
libreria. Un secondo commit del produttore aggiunge health; l'ARC attesta il commit precedente.
Non esiste un database, un servizio distribuito o una misura di performance.

Il corpus comprende decisioni accettate e superate, proposte, segnali con identificatori
uguali in prodotti diversi, contratti, un mandato approvato e uno draft, rischi e codice.
Le assenze sono intenzionali. Non si aggiungono documenti solo per rendere vera una risposta.

oracle.yaml è la specifica di revisione scritta separatamente: non viene estratta dal grafo,
dal context pack o dalle risposte dell'agente. Autore di corpus e oracle coincide:
la separazione dei file non è una revisione indipendente. Servono controllo umano delle
fonti e conferma delle rubriche prima di usare i punteggi per una decisione.

## Configurazioni

| Braccio | Runtime | Documenti |
|---|---|---|
| A | Commit pre-memory 3.6.3 | Corpus sintetico comune |
| B | Commit 3.8.1 | Stesso corpus; nessun arricchimento manuale |

I commit completi sono parametri del preparatore e registrati nel manifest. Provengono
da oggetti Git già locali: nessun fetch, checkout, cambio branch o installazione.
Le copie runtime escludono test, valutatori, risposte, report e storia Git.
framework.yaml è l'unica differenza consentita fra le due copie dei documenti.
Il contenuto degli altri file e le revisioni del codice sono uguali.

Le copie dei progetti dichiarano solo framework_version: i runtime esportati non hanno
.git, quindi dichiarare framework_commit nel progetto creerebbe un pin irraggiungibile.
I commit esatti e gli hash di ogni file runtime sono nel manifest del valutatore, che il
runner deve verificare prima e dopo ogni prova. La memoria usa la modalità supportata
version-only-unverified e ne dichiara il limite: l'identità delle regole è controllata dal
valutatore, non attestata dal progetto. Questo esperimento non qualifica l'adozione via Git.

Il confronto A/B misura l'incremento complessivo del framework, istruzioni comprese:
non attribuisce causalmente ogni differenza al solo grafo. Un'ablazione del grafo e un
braccio C con metadati opzionali richiedono esperimenti successivi.

## Domande e separazione

24 domande italiane, otto famiglie con tre domande ciascuna. Una per famiglia è destinata
allo sviluppo del benchmark, due alla valutazione riservata. Il manifest conserva gli hash.
Le domande riservate non vanno usate per regolare prompt o retrieval e poi riportate come
una verifica nuova. Se ciò accade, si annota e si costruisce un nuovo set.

Le domande condividono lo stesso piccolo mondo: non sono 24 repository indipendenti.
Il corpus è intenzionalmente compatto, non una prova di scala o di generalizzazione.
In seguito servono varianti più grandi e strutturalmente diverse, non soli duplicati.
Le 14 domande precedenti restano regressioni separate e non vengono riscritte.

Ogni esecuzione riceve una sola domanda, istruzioni neutrali e il normale ingresso AGENTS.md.
Niente percorso della risposta suggerito dal runner; niente context pack precalcolato.
I riferimenti presenti nella domanda quando necessari a esprimerne l'oggetto non sono
aggiunti dal valutatore. Il modello deve scegliere gli strumenti e le fonti.

## Isolamento e runtime: prerequisiti prima delle esecuzioni

Il preparatore NON è un runner e NON costituisce un sandbox. Non lanciarvi un agente
con accesso all'intera directory di output. Il runner deve:

1. Montare una sola copia progetto/runtime per esecuzione, senza evaluator, oracle,
   sorgenti del generatore, altri bracci, altre domande o risultati precedenti.
2. Usare sessioni nuove, senza memorie globali, plugin personali, web o subagenti.
3. Consentire lettura delle fonti e scrittura soltanto dei derivati in uno spazio dedicato,
   con lo stesso permesso nei due bracci. Mai rendere scrivibile tutto il progetto per
   permettere la costruzione di un indice. Registrare ogni tentativo di scrittura.
4. Provare prima letture consentite, scritture negate e impossibilità di leggere
   un canary esterno sintetico. Nessuna credenziale o corpus privato come canary.
5. Registrare modello richiesto e identità effettivamente attestabile, ragionamento,
   versione CLI, tool disponibili, budget, ambiente e hash degli input.
   Un'identità non verificabile resta un limite, non si inventa dal modello della chat.
6. Registrare i contenuti realmente consegnati dagli strumenti, distinguendo letture
   complete e troncate. Un comando richiesto o un exit code zero non prova una lettura.
7. Verificare che fonti e runtime siano invariati; conservare separatamente i derivati.

La rete dei comandi resta disabilitata; l'eventuale CLI autenticata deve comunque
contattare il fornitore del modello. Dataset locale non significa inferenza locale.
Nessun modello, account o consumo viene attivato da prepare.py.

## Esecuzione proposta

Tre ripetizioni per domanda e braccio: 144 esecuzioni pianificate, tutte inizialmente
not-run. schedule.json fissa l'ordine riproducibile, con coppie A/B randomizzate e
separazione sviluppo/valutazione. Ogni esecuzione richiede una copia fresca: il preparatore
fornisce due basi, non 144 sandbox già pronte.

Le ripetizioni non sono nuovi quesiti indipendenti. Eventuali intervalli d'incertezza
devono raggruppare per domanda e dichiarare la dipendenza dal corpus comune.
Account non disponibile, timeout e catture incomplete non diventano risposte sbagliate
o successi: sono stati distinti. Conservare i tentativi e i consumi osservabili.

## Rubriche e misure

In oracle.yaml, sources è una congiunzione di gruppi: basta una fonte valida per ciascun
gruppo di alternative. source-requirements.json risolve le fonti in hash e intervalli
di righe. Questi sono requisiti attesi, NON ricevute di lettura dell'agente.
Le sezioni Decision, Consequences e Review condition si leggono integralmente dove
richieste; Alternatives si aggiunge quando si ripropone una soluzione scartata.

Per ogni risposta si registrano separatamente:

- gruppi di fonti obbligatorie effettivamente recuperati e retrieval completo;
- correttezza di ciascun fatto richiesto, citazioni e affermazioni aggiuntive;
- rispetto delle assenze, dei confini di prodotto, del mandato e dell'incertezza;
- errori critici, che nessuna media può compensare;
- token, durata, numero di strumenti e fonti lette.

must_include e must_not sono criteri semantici, non stringhe da cercare nella risposta.
Una risposta può contenere tutte le parole attese ed essere falsa. Valutazione delle
risposte alla cieca rispetto al braccio, con revisione umana dei casi critici.
Una fonte ulteriore valida può essere ammessa dopo revisione, in entrambi i bracci,
documentando la modifica alla rubrica e ricalcolando entrambi: mai per favorire un braccio.

Obiettivo proposto, ancora da ratificare: almeno 95% di retrieval completo e zero
errori critici osservati. Una piccola prova senza errori non certifica rischio nullo.
Le medie non sostituiscono i risultati per famiglia e i peggiori casi.

## Token e interpretazione

Usare contatori effettivi dell'intera esecuzione, comprese istruzioni e passaggi intermedi.
Registrare input, output e cache separatamente. I token cached e reasoning possono essere
sottoinsiemi di contatori già inclusi: verificarne la semantica, senza doppio conteggio.
Se il contatore non è disponibile, il consumo è unknown, non zero né caratteri/4.
Non sommare nuovamente il testo dei tool già contabilizzato nell'input del modello.

Riportare consumo totale e token per risposta riuscita, includendo i tentativi falliti.
L'eventuale valutatore LLM è un costo separato. Riportare distribuzione della cache:
randomizzare l'ordine non garantisce la stessa cache del fornitore.
Separare costruzione iniziale degli indici e riuso. Il protocollo primario usa copie
senza indici precalcolati. Un esperimento warm va dichiarato separatamente.

Risparmio percentuale = 100 * (1 - token_nuovo / token_precedente), quando comparabile
e con denominatore positivo. Non dichiarare efficienza se la qualità è peggiorata;
se il nuovo framework risponde meglio consumando di più, riportare quel compromesso.
I token non sono automaticamente euro, quote dell'abbonamento o tempo risparmiato.

## Evoluzione e criteri di consegna

Questa consegna: corpus, domande, oracle, preparatore A/B, manifest, piano e test offline.
Non include runner strumentato, revisione indipendente, esecuzioni LLM, braccio C, prove
multi-agente, test di scala o misurazioni comparative. Non cambia regole o schemi del runtime.

Pratiche di riferimento: [OpenAI, Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices).
La documentazione ha orientato la separazione fra prove meccaniche e giudizio umano;
non introduce una dipendenza dall'Evals API o da servizi esterni.
