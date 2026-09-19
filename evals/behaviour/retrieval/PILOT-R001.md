# Pilota R001 — recupero delle fonti e costo del percorso

Data: 2026-09-13. Una domanda development, una ripetizione per braccio.
Esito: entrambe le catture utilizzabili coprono le fonti richieste. In questa
coppia il runtime attuale consuma più token e impiega più tempo. Nessun
miglioramento generale, punteggio di comprensione o risparmio è dimostrato.
Le risposte restano pending-independent-review.

## Prova eseguita

Domanda: «Con quale linguaggio dobbiamo scrivere un nuovo servizio di alpha,
e chi ha deciso?». Alpha e tutti i documenti sono sintetici.

| Parametro | Valore |
|---|---|
| A, precedente | 3.6.3, db75f310e2f42453cb0fe1b26573c3f6b5736790 |
| B, attuale | 3.8.1, faaf42259c7b43dfecbd1c52df21b2c4788cfc50 |
| Modello richiesto / reasoning | gpt-5.6-sol / high, identici per i due bracci |
| Provenienza della scelta | Valori espliciti della configurazione desktop, annunciati prima dell'avvio |
| Identità effettiva del modello | Non attestata dallo stream, non dedotta dal parametro richiesto |
| Client / ambiente | Codex CLI 0.150.1; Linux/WSL; CPython 3.14.4 e dipendenze esistenti |
| Ordine | B poi A, dal calendario congelato; nessun parallelismo |
| Contenuti | Fonti identiche salvo framework.yaml; nessun indice o context pack precaricato |
| Limite | 600 secondi per prova; nessun tetto token o monetario applicato |
| Rubrica | Solo R001: «continua» interpretato come conferma dopo la richiesta esplicita e dichiarato prima dell'esecuzione |

L'attestazione locale registra questa interpretazione e specifica che la lettura
umana non è osservabile indipendentemente. Non approva gli altri 23 quesiti e
non costituisce revisione delle risposte generate.

## Risultati della coppia dopo la correzione del runner

Fonte dei numeri: result.json e usage terminale di ciascun braccio, ispezionati
per intero nei campi riportati; comandi e pagine aggregati dalle rispettive tracce.

| Misura | A precedente | B attuale |
|---|---:|---:|
| Gruppi di fonti richieste coperti | 2/2 | 2/2 |
| Pagine strumentate osservate | 36 | 67 |
| Di cui documenti del framework | 26 | 56 |
| Pagine prima della prima lettura di STACK.md | 22 | 51 |
| File distinti nelle pagine | 14 | 18 |
| Comandi terminati, inclusi quelli falliti | 40 | 73 |
| Tempo del processo, secondi | 211,217 | 365,427 |
| Input token cumulativi | 975.907 | 2.715.228 |
| Di cui input in cache | 903.552 | 2.625.792 |
| Input non in cache, per differenza | 72.355 | 89.436 |
| Output token cumulativi | 7.163 | 12.638 |
| Di cui reasoning | 2.283 | 4.228 |
| Totale input + output | 983.070 | 2.727.866 |
| Mutazioni a fonti, runtime, Git o lettore | 0 | 0 |
| Frame non verificabili | 0 | 0 |
| Errori del tool host nel retry | 0 | 0 |

Le fonti richieste sono STACK.md integralmente e le sezioni Decision,
Consequences e Review condition di DEC-002. Entrambi hanno consegnato nel log
anche il record DEC-002 integrale e la decisione precedente DEC-001.
La verifica confronta testo, hash e righe: non accredita la sola citazione finale.

Ho letto integralmente le due risposte e le fonti sintetiche STACK.md, DEC-002,
DEC-001 e AGENTS.md. Osservazione dell'autore del benchmark, non voto indipendente:

- entrambe rispondono Python e indicano DEC-002 accepted come autorità;
- entrambe distinguono la vecchia decisione JavaScript, superseded;
- entrambe distinguono owner del documento e approvatore: non inventano il
  nome di chi ha deliberato quando il record non lo identifica;
- entrambe dichiarano di non aver eseguito test del prodotto.

Restano da valutare indipendentemente correttezza complessiva, affermazioni
aggiuntive, conformità alle istruzioni e appropriatezza delle letture.
Un 2/2 di copertura su R001 non significa 100% di retrieval sulla suite.

## Che cosa spiega il costo, e che cosa non sappiamo

Il conteggio è cumulativo sulle chiamate interne del turno. Non rappresenta
milioni di token unici del corpus né la dimensione di un singolo contesto.
La cache è già compresa nell'input, il reasoning nell'output: non si sommano
di nuovo. Non è una misura monetaria né una fattura.

La traccia mostra che entrambi leggono tutto FRAMEWORK.md in 17 pagine.
B legge inoltre SKILLS.md integralmente, la skill audit, il preambolo e la
memoria operativa; A legge solo la prima pagina di SKILLS.md e nessun SKILL.md.
B impiega 46 pagine del framework prima di STACK.md, A 18.
Il file sintetico AGENTS.md richiede FRAMEWORK.md e le istruzioni pertinenti:
questo bootstrap è parte del test, non una proprietà inevitabile di ogni uso.

È plausibile che istruzioni più estese, selezione delle skill e lettore da
40 righe/4000 byte amplifichino il costo; la traccia sostiene l'ipotesi, non
separa causalmente i tre effetti. Non possiamo attribuire token esatti ai singoli
documenti dalla sola usage aggregata. Il diverso rispetto delle istruzioni va
considerato nella revisione: meno letture non equivale automaticamente a meglio.

Entrambi tentano rg, assente nell'ambiente WSL, e recuperano con find; non è
un guasto del retrieval. Non sono osservate invocazioni del grafo documentale
o di context pack. Nessun provider del grafo del codice è installato.
Questa domanda prova la navigazione verso una decisione, non il vantaggio
del grafo, l'analisi di impatto, la capacità di sviluppo o il lavoro multi-agente.

Una sola coppia, un solo modello richiesto e cache non azzerata non consentono
conclusioni statistiche. Sessioni e worktree freschi non garantiscono cache
del fornitore fredda. Non si ricava una percentuale di risparmio generalizzabile.

## Tentativi iniziali non validi, conservati

Prima del retry il runner disabilitava code_mode_host. Nella CLI provata questo
rendeva inutilizzabili gli strumenti, pur passando il probe del sandbox.
Entrambi i modelli hanno risposto senza poter leggere fonti. Sono prove
non valide per valutare il framework, non errori di retrieval del framework.

| Tentativo iniziale | Input | Cache, inclusa nell'input | Output | Totale |
|---|---:|---:|---:|---:|
| A | 37.430 | 18.048 | 1.081 | 38.511 |
| B | 37.537 | 18.048 | 1.119 | 38.656 |

I vecchi result.json riportano pending-review perché il parser non guardava
quel diagnostico stderr. Non sono stati riscritti: la correzione interpretativa
è registrata qui. Il runner attuale classifica quel caso unavailable e conserva
il consumo. Il retry è stato annunciato ed eseguito una sola volta per braccio,
in directory nuova e con identico fix per A e B.

Totale delle quattro invocazioni: **3.788.103 token**.
Di questi, 77.167 appartengono ai tentativi non validi e 3.710.936 alla coppia
con strumenti funzionanti. Nessun tentativo scompare dal totale.
Il dato non include il lavoro dell'agente che costruisce questo benchmark.

## Correzioni applicate e verifiche

- run.py: feature degli strumenti abilitate esplicitamente e controllo delle
  feature prima del sandbox probe, con gli stessi override della prova reale.
- metrics.py: errore del tool host distinto da risposta catturata; consumi
  mantenuti; una frase nella risposta non vale come diagnostico del client.
- test_retrieval_runner.py: due regressioni nuove; 29 test mirati passati
  in 3,843 secondi.
- tests/selfcheck.py: gate completo passato, inclusi 319 test in 121,652 secondi.
  I 29 sono inclusi nei 319, non si aggiungono.
- Preflight corretto A/B passato; nel retry entrambi gli stderr sono vuoti,
  gli eventi risultano validi e gli inventari non rilevano mutazioni.
- Hash di corpus, domande, oracle, protocollo v1, preparatore e generatore
  condiviso ricontrollati: invariati.

La skill OpenAI Docs ha guidato la verifica delle opzioni CLI nella documentazione
ufficiale; il guasto specifico è stato invece osservato sul client locale.
Non sono cambiate regole, skill o dipendenze del runtime del framework.
Nessun commit, push, installazione o migrazione è stato eseguito.

## Privacy ed evidenze

Sono state usate l'autenticazione esistente e l'inferenza remota del client:
prompt e contenuti sintetici selezionati raggiungono il fornitore. Il test non è
offline. I comandi del modello non hanno accesso alla rete, ai prodotti reali,
al valutatore o al braccio fratello, secondo i probe eseguiti. Non sono stati
letti dati di clienti o credenziali per costruire il dataset.
Non è attestato il payload interno completo del client o il contenuto rimasto
nel contesto dopo eventuali trasformazioni. Nessuna nuova dipendenza introdotta.

Evidenze locali temporanee, non pubblicate né automaticamente versionate:

- Preparazione: /tmp/framework-retrieval-v1-final-20260912.
- Attestazione R001: /tmp/framework-retrieval-r001-human-review-20260913.json.
- Tentativi non validi: /tmp/framework-retrieval-r001-pilot-20260913.
- Preflight corretto: /tmp/framework-retrieval-r001-fixed-preflight-20260913.
- Coppia utilizzabile: /tmp/framework-retrieval-r001-pilot-retry1-20260913.
  Ogni trials/R001-1-A o trials/R001-1-B contiene answer.md, result.json,
  events.stdout, events.stderr, prompt.txt e inventari.

| Evidenza del retry | SHA-256 |
|---|---|
| Prompt, identico A/B | ec0bcc36bfaca08d110a6a83b82b6196b7497355a6f4160d2867e3ba907c4257 |
| A result.json | 13e9e1beb219bb571f763704621beb427028fdca676451970368ed23f85b9e3e |
| B result.json | 45fe9bdfaa60d2a670cafa27d5542ac686a7f2c588ebf35da7e73170276233ce |
| A answer.md | c5e0e4d834f56af4911a81e35b8c5569c5f22db42757f57deae7e262d0a8a426 |
| B answer.md | 57de74e91d27f7097c6fa16d4f81a58dd196d2b1977db8c56d2b9d7069411910 |
| A events.stdout | 3ca01e73fc0be342c30bff25012ec6712b965f47ba8aa46781648f04d0e5daf2 |
| B events.stdout | cf262b2aa7669f667c3a7fd333e08967e4ec515da118d691f022c2b3824fa2a8 |

## Prossimo passo proposto, non eseguito

Prima di ampliare la campagna: revisionare le risposte R001 e decidere un limite
di consumo esplicito per le prove successive. Il timeout non basta.
Poi qualificare separatamente un adapter v2 con letture meno frammentate, senza
modificare la domanda per suggerire le fonti e senza saltare vincoli pertinenti.
Mantenere v1 come misura originale e applicare v2 a entrambi i bracci.

Le altre domande development serviranno a verificare casi in cui le relazioni
contano: decisioni superate, impatto fra componenti, assenza di codice e vincoli
di autorizzazione. I quesiti evaluation restano non eseguiti e non usati per
correggere il runner. Nessuna campagna ulteriore è stata avviata.
