# Verifica locale del dataset sintetico e del runner

## 16/09: qualificazione preliminare del traversal

[Report G0](GRAPH-ABLATION-G0.md): 4/4 confronti completati (100%), zero nuovi
gruppi richiesti nei quattro casi con seed fissati. Non e' zero informazione
utile ne' una misura di comprensione. Gate complessivo non superato; nuove
catture con agente 0/8 (0%). Nessuna chiamata al modello.

15/15 nuovi test di test_graph_ablation_qualification.py e 100/100 regressioni
retrieval superati, rispettivamente in 0,006 s e 8,626 s. Due esecuzioni del
qualificatore ricostruiscono il dataset congelato, verificano gli inventari
e producono build identiche. Le uscite integrali restano nelle due directory
/tmp/framework-graph-ablation-g0-20260916-01 e -02; hash nel registro numerico.
La correzione sul LOG come provenienza, non corpo consegnato, e' nel piano.

## Consolidamento del 16/09: blocco development completato

Il [report aggiornato](DEVELOPMENT-CONTINUATION.md) e il relativo
[registro numerico](DEVELOPMENT-CONTINUATION-RESULTS.json) conservano quattro
batch: 19 tentativi, 16 risposte complete (14 accoppiate e due aggiuntive),
tre interruzioni per quota con usage sconosciuta. Sette nuove coppie complete;
con R001, development 8/8 e copertura della banca 8/24. Revisione indipendente
delle 16 risposte ancora 0/16; non e' un giudizio di efficacia.

Suite offline retrieval rieseguita dopo le catture: 100/100 in 9,017 secondi.
Nessuna mutazione nei 19 risultati; otto hash del runner ancora corrispondenti.
R019-A ha 5/6 gruppi verificati, tutte le altre 13 catture accoppiate sono complete.
R004 mostra una condizione richiesta ma non esplicitata in entrambe le risposte.
Una invocazione spontanea di context compare ora in R013-B del quarto batch:
output JSON catturato completo, ma troncamento dichiarato dall'agente; copertura
partial, zero percorsi esplorati e code not-requested. Non prova beneficio causale.

Il [piano di attribuzione](GRAPH-ATTRIBUTION-PLAN.md) registra sei sonde locali,
i limiti metodologici dei report storici e il confronto sullo stesso runtime
ancora da implementare. Nessuna nuova chiamata al modello per quel confronto.
Nessuna modifica a runtime, corpus, oracle o runner, installazione, commit o push.

## Registro storico

Registro cronologico: controlli iniziali del 2026-09-12 e incrementi del 13-14/09.
Le sezioni iniziali descrivono verifiche senza modello al momento della loro esecuzione.
Il pilota reale è in [PILOT-R001.md](PILOT-R001.md); le cinque coppie successive
sono in [REPETITIONS-R001.md](REPETITIONS-R001.md), con costi e limiti separati.

## Contenuto effettivamente generato

- 3 prodotti fittizi: due con codice, uno con solo design.
- 35 documenti del corpus comune, escluso framework.yaml.
- 3 repository Git sintetici senza remote; 7 file sotto code/, incluso il commento di review.
- 24 domande in 8 famiglie: 8 per sviluppo e 16 riservate alla valutazione.
- 144 esecuzioni A/B pianificate, tutte not-run.
- Soluzioni, rubriche e requisiti delle fonti separati dalle copie progetto/runtime.

Il manifest finale conta 42 file comuni e ne registra questo hash aggregato:
165e1f33d6c13b4fa889afd14816376bf478beda0224fbcda73d6447d8694292.
Le parti non deterministiche interne a Git non entrano in questo hash; gli identificativi
dei commit sintetici sono verificati separatamente.

## Prove eseguite

| Controllo | Esito |
|---|---|
| Suite mirata test_retrieval_dataset.py | 17 test passati; rieseguiti il 13/09 in 2.977 s |
| Gate completo tests/selfcheck.py | Passato il 12/09, inclusi 290 test offline in 140.101 s |
| Validazione con runtime 3.6.3 esportato | Zero errori; avvisi/informazioni confrontati con validation-expected.yaml |
| Validazione con runtime 3.8.1 esportato | Zero errori; avvisi/informazioni confrontati con validation-expected.yaml |
| Riproducibilita' in directory diverse | Stessi contenuti e commit del codice |
| Parita' A/B | Differisce solo framework.yaml nei progetti |
| Codice fittizio | Test di produttore/consumatore eseguiti; KeyError e ingresso indipendente verificati |
| Lettura delle regole dal runtime B esportato | Fonti disponibili; limite version-only esplicito, non unavailable |
| Modelli, produzione, migrazioni, installazioni | Non eseguiti |

Il 13/09 gli hash degli input del generatore sono stati confrontati con il manifest finale:
prepare.py, corpus.yaml, questions.yaml, oracle.yaml, PROTOCOL.md, validation-expected.yaml
e l'helper evals/fixtures/generators/memory.py erano tutti invariati. Anche HEAD del framework
era invariato. Dopo la ripresa sono stati aggiunti soltanto questo resoconto e il suo link.

I tempi riportati sono quelli di questi controlli locali, non stime di implementazione
o misure di miglioramento dell'agente. L'ambiente e' WSL/Linux, CPython 3.14.4 con le
dipendenze gia' vincolate del framework. Nessuna CI remota o matrice multipiattaforma
e' stata eseguita. I 17 test nuovi sono inclusi nei 290, non si sommano a quel totale.

L'avviso ID001 sui due contratti omonimi e' intenzionale. I segnali non classificati
restano visibili: la baseline segnala quello di alpha, il runtime attuale anche quello
di beta. Questo controllo meccanico non diventa un risultato di comprensione.

Durante il collaudo sono state corrette solo le nuove fixture e il preparatore:
riferimenti qualificati nei CHG, stato draft dell'architettura senza codice e forma del
registro rischi. Inoltre e' stato rimosso il pin Git irraggiungibile dalle configurazioni
dei progetti esportati. I commit reali dei runtime e gli hash restano nel manifest.
Nessuna regola, dipendenza o versione del runtime del framework e' stata modificata.

## Riproduzione e limiti

Usare i comandi del README con una directory di output nuova. Il preparatore non legge
repository di prodotti, non accetta un corpus reale, non fa fetch e non chiama modelli.
I commit da confrontare devono gia' esistere localmente:

- A: db75f310e2f42453cb0fe1b26573c3f6b5736790, 3.6.3.
- B: faaf42259c7b43dfecbd1c52df21b2c4788cfc50, 3.8.1.

La copia ispezionabile di questa esecuzione e' /tmp/framework-retrieval-v1-final-20260912.
E' temporanea, non l'unica copia del dataset: definizioni e generatore sono nel framework.

Alla consegna del dataset restavano necessari revisione indipendente e runner.
L'incremento del runner e' descritto sotto. La separazione in cartelle non protegge le
soluzioni da un agente con accesso all'intero disco. Nessun risultato di retrieval,
risparmio, efficacia multi-agente o affidabilita' su progetti reali e' dichiarato.

## Incremento del 13/09: runner A/B

Sono stati aggiunti run.py, read_source.py, metrics.py, RUNNER.md e
tests/memory/test_retrieval_runner.py. Il README collega la guida operativa.
Corpus, domande, oracle, preparatore, protocollo v1 e runtime non sono cambiati.
RUNNER.md e' l'estensione del protocollo; non si riscrive lo snapshot del dataset.

Prove eseguite senza LLM:

- 24 nuovi test automatici passati; ultima esecuzione mirata in 2.926 s.
- Gate completo tests/selfcheck.py passato anche dopo le ultime protezioni:
  314 test in 95.592 s, inclusi i 17 del dataset e i 24 del runner, non da sommare.
- Eventi CLI simulati: letture complete, pagine mancanti, output troncati,
  contenuto contraffatto, contatori assenti o incoerenti, timeout e scritture.
- Le simulazioni verificano il parser, non sono risposte del benchmark e non
  approvano l'oracle. Tutte le catture complete restano pending-review.
- Rigenerazione e confronto delle basi, prompt e oracle alterati respinti,
  copie fresche e calendario accoppiato; nessuna invocazione implicita.
- Test del rifiuto di una seconda esecuzione sulle stesse copie.

Preflight REALE, CLI 0.150.1, Linux/WSL, stessa Python 3.14.4 del dataset:

| Probe | Braccio A | Braccio B |
|---|---|---|
| Lettura fonti e runtime | Consentita | Consentita |
| Lettore paginato e dipendenze Python | Funzionanti | Funzionanti |
| Avvio CLI del runtime | Funzionante | Funzionante |
| Scrittura su fonti o runtime | Negata | Negata |
| Lettura canary del valutatore | Negata | Negata |
| Lettura della prova sorella | Negata | Negata |
| Rete dei comandi | Negata | Negata |
| Scrittura nello scratch dedicato | Consentita | Consentita |
| Alterazioni a fonti, Git o lettore dopo il probe | Nessuna | Nessuna |

La traccia finale del preflight e' in
/tmp/framework-retrieval-runner-verified-20260913, domanda development R001,
una coppia in ordine B/A. I due prompt hanno lo stesso hash.
run.json registra model_invocations_attempted: 0; results.json non conta il
preflight come consumo LLM sconosciuto. Le copie temporanee non sono versionate.

Questi controlli non attestano il prompt interno completo della CLI o il payload
effettivamente inviato al modello. Le fonti osservate nel log non provano
comprensione. Restano necessari revisione umana delle rubriche, scelta esplicita
di modello/reasoning, pilota su eventi reali e successiva valutazione delle risposte.
Non sono stati eseguiti migrazioni, installazioni, commit, push o chiamate LLM.

## Incremento successivo del 13/09: revisione per quesito

Il runner genera schede riservate al valutatore con domanda, rubriche originali,
intervalli richiesti e fonti integrali numerate. L'attestazione richiede ora
reviewed_questions e prepared_manifest_sha256 oltre all'hash dell'oracle.
Una revisione di R001 non copre altri quesiti o una preparazione diversa.
Gli input del valutatore vengono controllati prima di invocare la CLI.
Nessuna approvazione umana e' stata registrata dall'agente.

- Test mirati del runner: 27 passati in 3.890 s.
- Gate completo: 317 test passati in 101.255 s, inclusi i 27 del runner.
- Preflight reale ripetuto sulla coppia R001: entrambi i bracci passed,
  zero invocazioni del modello, nessuna alterazione delle fonti.
- Scheda e tracce: /tmp/framework-retrieval-pilot-review-20260913.

La scheda R001 e le due fonti STACK.md e DEC-002 sono state lette integralmente
per verificarne la coerenza: Python e' la scelta corrente; DEC-002 e' accepted e
supera DEC-001. Questa verifica e' dell'autore del benchmark, non indipendente.
Il giudizio sulle risposte e le misure comparative restano non eseguiti.
Il passo successivo richiede la conferma umana dei criteri di R001 e la scelta
esplicita di modello e ragionamento. La revisione non autorizza implementazioni
nei prodotti sintetici o reali e non modifica le soglie del benchmark.

## Ultimo incremento del 13/09: pilota reale R001

La conferma utente successiva alla scheda e' stata registrata solo per R001,
con interpretazione e limiti dichiarati. Modello richiesto gpt-5.6-sol, high,
ricavato dalla configurazione desktop esplicita e annunciato prima dell'avvio.
Non si deduce l'identita' effettiva del modello dal parametro richiesto.

Eseguite quattro invocazioni: due iniziali non valide per un flag del runner
che disabilitava il tool host, poi un solo retry della coppia B/A dopo il fix.
I dati originari non sono stati sovrascritti. Consumo complessivo 3.788.103 token,
inclusi 77.167 dei tentativi non validi. Dettagli, hash e percorsi delle evidenze
sono in [PILOT-R001.md](PILOT-R001.md).

- Entrambi i retry completano la cattura e coprono 2/2 gruppi di fonti richieste.
- Nessuna mutazione osservata; preflight corretto passato A/B.
- Le risposte restano pending-independent-review: niente punteggi automatici.
- 29 test del runner passati in 3.843 s; gate completo passato con 319 test
  in 121.652 s. Sono totali successivi, non da sommare ai precedenti.
- Tutti i sette input congelati del generatore sono invariati rispetto al manifest.
- Nessuna modifica al runtime, installazione, migrazione, commit o push.

Il candidato legge piu' istruzioni e usa piu' token su questa domanda.
Non e' dimostrato un miglioramento: una coppia non misura la suite, i grafi
non sono stati invocati, il costo della strumentazione va riesaminato.
Le altre 23 domande restano non eseguite. Nessun ulteriore retry o campagna avviato.

## Incremento del 14/09: cinque ripetizioni R001 senza tetto di durata

Autorizzazione utente: proseguire con i test e misurare il consumo senza imporre
limiti di token o tempo. run.py aggiunge --no-timeout e --pair-order AB/BA,
registrati nel manifest; il comportamento predefinito resta invariato.
Corpus, oracle, preparatore, prompt e commit dei runtime non sono cambiati.

- Prima delle chiamate: 31 test mirati passati in 5.124 s; gate completo passato
  con 321 test in 117.726 s. I 31 sono inclusi nei 321.
- Dopo le ultime chiamate: stessi 31 test passati in 6.991 s, senza LLM reale.
- Cinque coppie catturate, ordine B/A, A/B, B/A, A/B, B/A; nessun timeout del runner.
- Due stop per quota, seguiti da richieste esplicite di continuare. Piano e due
  riprese registrati separatamente; nessun retry automatico o reset acquistato/usato.
- Registro completo: 13 tentativi, 11 catture complete, 2 unavailable per quota.
  Dieci catture entrano nelle statistiche accoppiate; l'A della quarta coppia
  interrotta resta osservazione aggiuntiva, con consumo conservato.
- Consumo noto del blocco: 8.237.452 token, piu' due consumi sconosciuti.
  Totale storico con il pilota: 12.025.555 token noti, piu' gli stessi unknown.
- Copertura dei gruppi richiesti: 4/5 prove per ciascun braccio. In 3B e nel
  nuovo 4A manca nel log il testo di una pagina STACK, pur con exit 0.
- Dieci eventi reader senza testo nelle coppie selezionate, uno nell'A aggiuntivo.
  L'origine del vuoto non e' stata determinata; nessun credito retroattivo.
- Nessuna mutazione negli inventari delle tredici prove; nessuna riga JSON invalida.
- Hash dei cinque input del runner e del prompt identici nei sette batch.
- Somme e mediane estratte in PowerShell e ricontrollate in JavaScript.

Risposte lette integralmente dall'autore, non valutate indipendentemente:
stato pending-independent-review conservato. Risultati di tempo e token misti,
tre blocchi temporali, cache non controllata. Nessuna prova del vantaggio del
grafo, dello sviluppo o del lavoro multi-agente; nessuna invocazione memory.py
osservata nei comandi. Le altre 23 domande restano non eseguite.

Report e registro numerico riportano percorsi e SHA-256 delle evidenze locali
temporanee. I grezzi non sono stati pubblicati o archiviati nel repository.
Nessuna modifica al runtime, nuova dipendenza, migrazione, installazione, commit o push.

## Incremento successivo del 14/09: reader flessibile, esperimento separato

R001 eseguita su una coppia A/B con run_flexible.py, dopo preregistrazione.
Il reader consente file interi o intervalli scelti dall'agente. Non e' una
sessione IDE ordinaria: restano frame verificabili e i limiti del client.
Gli script v1 e gli input del corpus sono rimasti byte-identici.

- Nuovi test offline: 17 passati in 4,575 s.
- Gate completo passato; la sottosuite memory conta 338 test in 265,695 s,
  inclusi i 17 nuovi. Gli altri controlli del gate sono verdi.
- Preflight senza modello A/B passato; ripetuto prima di ogni chiamata reale.
- Nessun timeout del runner, retry, errore di quota o consumo sconosciuto
  nelle due nuove invocazioni. Modello richiesto gpt-5.6-sol/high, CLI 0.150.1.
- A: 192,359 s, 583.667 token, 13 letture, 13 output reader verificati.
- B: 249,301 s, 366.557 token, 21 letture, 18 output verificati e tre vuoti.
  Sette richieste usano intervalli espliciti; nessuna pagina e' imposta.
- Entrambe coprono 2/2 gruppi di fonti richieste. B cita anche un manifest
  il cui output reader e' vuoto: non si accredita quella lettura.
- Il frame di FRAMEWORK.md e' completo nel log B, mentre la risposta
  dichiara il tentativo integrale troncato. La causa non e' determinata:
  log del comando, payload del modello e comprensione restano distinti.
- Nessuna mutazione osservata, nessuna riga JSON invalida; otto hash del
  runner e sette input congelati ricontrollati. Nessuna invocazione memory.py.
- Diagnostica offline sulle undici catture v1 complete: undici output vuoti,
  in accordo con il ledger storico. Nessuna modifica o accredito retroattivo.
- Consumo del nuovo blocco: 950.224 token. Storico: 12.975.779 token noti,
  piu' due consumi sconosciuti, 19 tentativi totali; analisi dell'autore esclusa.
- Risposte lette integralmente dall'autore; revisione indipendente 0/2.
  Copertura ancora 1/24 (4,2%), development 1/8 (12,5%), nuove catture 2/2.

Report: [PILOT-R001-FLEXIBLE.md](PILOT-R001-FLEXIBLE.md).
Hash e metriche: [PILOT-R001-FLEXIBLE-RESULTS.json](PILOT-R001-FLEXIBLE-RESULTS.json).
Nessuna nuova dipendenza o modifica al runtime. Non e' dimostrato un risparmio
generale: la nuova coppia non si aggrega alla serie v1.

## Preparazione successiva del 14/09: sette domande development

Preparate R004, R007, R010, R013, R016, R019 e R022, una coppia ciascuna,
con il reader flessibile invariato. Zero chiamate al modello e zero preflight.
Le quattordici prove sono prepared-not-executed, non risultati.

- Sette schede con fonti integrali generate e lette per intero dall'autore.
- Sette input del generatore controllati invariati; attestazione ancora
  pending-independent-human-review, nessun nome/data di revisore compilato.
- R004: la rubrica richiede una condizione di riesame della condivisione,
  sostenuta dalla fonte ma piu' ampia della domanda sulla cache. Questione
  registrata prima di eseguire il caso, senza cambiare l'oracle congelato.
- R016: code/gamma-scheduler assente nelle due copie preparate, controllato
  in sola lettura. Non e' una misurazione del throughput o un test del modello.
- Suite offline retrieval: 65/65 passati in 10,769 s; nessuna invocazione reale.
- Copertura eseguita ancora 1/24 (4,2%), development 1/8 (12,5%).
  Schede controllate dall'autore 7/7; nuove rubriche confermate da un umano 0/7.

[Scheda unica](DEVELOPMENT-REVIEW.md) e
[registro della preparazione](DEVELOPMENT-REVIEW-RESULTS.json).
La revisione dell'autore non sostituisce la conferma umana dei criteri.
Nessuna modifica al runtime, dipendenza, installazione, commit o push.

## Incremento del 15/09: ripresa interrotta e diagnosi del meccanismo

La ripresa autorizzata del blocco development si e' fermata alla quinta invocazione
su dodici, su `R004-1-A`, dopo 3,341 s con exit 1: limite di utilizzo del fornitore,
usage assente. Non stimare zero. Nessun retry automatico, nessun reset riscattato.

- Quattro catture complete: R022 A/B e R007 A/B, tutte `pending-review`.
  Copertura dei gruppi richiesti 3/3 e 4/4, in entrambi i bracci.
- Sette prove mai avviate: R004-B, R019 B/A, R013 B/A, R010 A/B.
- Consumo noto del blocco: 2.866.861 token, piu' un consumo sconosciuto.
- Nessuna mutazione, nessuna riga JSON invalida, preflight passato prima di ogni prova.
- Registro numerico: [DEVELOPMENT-RUN-RESULTS.json](DEVELOPMENT-RUN-RESULTS.json),
  generato dalle evidenze temporanee, non trascritto a mano.

Successivamente, senza alcuna chiamata al modello, sono state valutate le
ventiquattro risposte gia' catturate ed e' stato verificato in modo deterministico
se la funzionalita' in esame sia mai stata esercitata. Esito in
[MECHANISM-DIAGNOSIS.md](MECHANISM-DIAGNOSIS.md):

- Zero invocazioni di `memory.py` in tutti i batch reali; 39 occorrenze della stringa,
  tutte testo letto dentro i documenti. Confermato dal contatore della serie v1.
- Il pacchetto di contesto e' identico byte per byte per due domande diverse e con
  selettore di nodo esplicito; 93% dei caratteri consegnati sono regole adottate,
  `required_sources` elenca l'intero corpus. Non restringe la lettura.
- `memory.py query` e' letterale: ogni termine italiano delle domande restituisce
  zero documenti, i corrispondenti inglesi ne restituiscono. Il grafo del codice
  resta `not-requested` senza snapshot esplicito.
- Valutazione dell'autore contro le rubriche congelate, non revisione indipendente:
  dieci coppie valutabili, nove pareggi, una differenza. Su R016 il braccio A asserisce
  «0 elementi/s» e viola il `must_not` della rubrica; B rifiuta esplicitamente quella
  formulazione. La regola violata e' pero' presente anche nel runtime di A, B non cita
  la sezione nuova, e su R022 la stessa differenza di precisione compare fra due
  sessioni dello stesso braccio A. Effetto non separato dalla varianza.
- Copertura delle fonti richieste: pareggio in tutte le coppie complete. Tempo: B piu'
  lento in tre coppie su quattro. Token totali dominati dalla cache non controllata.

Lo stato `pending-independent-review` resta invariato per tutte le risposte: questa
valutazione e' dell'agente che analizza e non sostituisce la conferma umana.
Nessun miglioramento e' dimostrato e nessun peggioramento e' osservato. Le otto prove
residue, nella configurazione attuale, non possono misurare la funzionalita' in esame.

Nessuna modifica a runtime, corpus, oracle, prompt, preparatore, runner o attestazioni.
Suite offline retrieval rieseguita: 65/65. Nessuna installazione, commit o push.

## Incremento successivo del 15/09: economia della lettura e potenza

Seconda analisi deterministica sulle stesse catture, senza chiamate al modello.
Misura il volume di testo effettivamente consegnato dal lettore strumentato, che non
risente della cache non controllata del fornitore. Esito in
[MECHANISM-DIAGNOSIS.md](MECHANISM-DIAGNOSIS.md), sezioni 8-11.

- Dall'84% al 97% dei caratteri letti in ogni prova e' documentazione del framework.
  Le fonti che contengono la risposta pesano fra 2.247 e 3.507 caratteri, cioe' fra
  l'1,5% e il 4,0% del totale letto. Vale per entrambi i bracci.
- Copertura delle fonti richieste: 100% in entrambi i bracci, in tutte le coppie
  complete. La baseline satura gia' la metrica; non resta margine osservabile.
- Sovraccarico di B sulle quattro coppie flessibili: +93.732 caratteri di framework,
  di cui 15.892 il nuovo references/operational-memory.md. Il resto e' rilettura:
  A legge FRAMEWORK.md una volta sola, 36.061 caratteri, in ogni prova; B arriva a
  77.090 e 66.034 caratteri, cioe' 2,02 e 1,73 volte il file.
- Ipotesi scartata: il lettore non impone tetti e i dieci output vuoti non dipendono
  dalla dimensione. Colpiscono AGENTS.md quanto FRAMEWORK.md, 4 in A e 6 in B.
- Serie v1, cinque coppie, stessa domanda e stesso lettore: la varianza interna a
  ciascun braccio e' di circa due volte (pagine 27-53 in A, token non in cache
  42.966-89.886 in A). Test dei segni esatto bilaterale: p = 1,00 su pagine, token e
  tempo; p = 0,38 sui comandi. Nessuna direzione.
- Potenza sui token non in cache: deviazione standard delle differenze accoppiate
  13.991 su media 62.419. Servono ~5 coppie per un effetto del 30%, ~10 per il 20%,
  ~40 per il 10%, ~158 per il 5%. Le otto prove residue sono quattro coppie.

Conseguenza: la campagna cosi' disegnata puo' rilevare soltanto effetti dell'ordine
del 30-50%. Nessun risparmio e nessun guadagno di retrieval e' dimostrato, e nessun
peggioramento e' dimostrato: i punti stimati vanno in entrambe le direzioni e sono
piu' piccoli del rumore. Il costo dominante e' la documentazione del framework letta
a ogni prova, non le fonti di progetto.

Nessuna modifica a runtime, corpus, oracle, prompt, preparatore, runner o attestazioni.
Suite offline retrieval rieseguita: 65/65. Nessuna installazione, commit o push.

## Incremento del 15/09: il grafo interrogato direttamente, e la condizione C

Le condizioni A e B misuravano se un agente scopre il motore. Non lo scopre mai.
Sono state quindi aggiunte due cose: una misura diretta del canale di retrieval del
motore, senza modello, e un terzo braccio che fornisce all'agente l'invocazione
documentata. Report in [GRAPH-RETRIEVAL.md](GRAPH-RETRIEVAL.md), numeri in
[GRAPH-RETRIEVAL-RESULTS.json](GRAPH-RETRIEVAL-RESULTS.json).

Misura diretta, zero chiamate al modello, ground truth i gruppi dell'oracle congelato.
Il grafo si costruisce: 48 nodi, 48 archi, 35 sorgenti, 17 gaps, 0 issues.

| Metodo | Gruppi su 75 | Recall | Costo consegnato |
|---|---:|---:|---:|
| query con il testo italiano della domanda | 0 | 0,0% | 0 |
| query con i termini inglesi corretti (tetto) | 36 | 48,0% | 4.331 medi |
| context pack documentato | 54 | 72,0% | 99.723 |
| agente che legge i file, osservato | — | 100% | 58.598-172.444 |

- M1 e' a zero perche' la ricerca e' lessicale e le domande sono in italiano su corpus
  inglese; literal e fts5 si comportano allo stesso modo.
- M2 e' al 100% sulle cinque domande a fonte singola e fra il 40% e il 50% su tutte le
  altre: il grafo regge dove non serve e cede dove servirebbe.
- M3 elenca l'intero corpus documentale e perde comunque 21 gruppi su 75. Sono tutti e
  ventuno percorsi sotto code/: il pacchetto non contiene codice.
- Il grafo del codice non e' attivabile: memory.py code esce 2 con 0 nodi, 0 archi,
  0 sorgenti, coverage unavailable; doctor riporta provider enola 0.4.15
  provider-not-configured e tre repository binding-unavailable. Installare il provider
  e' vietato sia da references/operational-memory.md sia dal prompt del benchmark.

Su questo corpus e con questa configurazione il grafo non migliora il retrieval:
recupera meno di quanto l'agente ottenga leggendo i file, e il canale mancante richiede
una condizione che il protocollo esclude. Il limite di questa misura e' esplicito: 35
documenti sono pochi, e su corpora dove leggere tutto non e' praticabile un recall del
72% potrebbe battere una lettura parziale.

Condizione C: [run_graph.py](run_graph.py) mantiene il braccio A invariato e aggiunge al
solo braccio candidato l'invocazione testuale di references/operational-memory.md.
Modo instrumented-source-retrieval-graph-v3, prompt per braccio registrati negli hash.
Preflight reale passato su entrambi i bracci di R022, zero invocazioni del modello,
nessuna mutazione. Il preflight richiede --codex assoluto e --sandbox-helper sul binario
vendorizzato: senza quest'ultimo bwrap non risolve l'eseguibile.

Nuovi test offline: 17 passati, inclusi il divieto per il braccio A di ricevere
l'istruzione e la coerenza interna del report. Suite retrieval completa: 82/82.
Nessuna modifica a runtime, corpus, oracle, prompt esistenti, preparatore o attestazioni.
Nessuna installazione, commit o push.

## Incremento del 15/09: quattro prove reali con Opus

La CLI Claude annidata non si autentica in questo ambiente (loggedIn: false, authMethod:
none), quindi run_claude.py resta preparato e non eseguito. Le quattro prove sono state
eseguite come subagenti in-process su Opus: contesto fresco, copia isolata per prova,
fonti e runtime resi non scrivibili a livello di filesystem. Report in
[OPUS-ARENA.md](OPUS-ARENA.md), numeri in [OPUS-ARENA-RESULTS.json](OPUS-ARENA-RESULTS.json).

Isolamento piu' debole delle catture codex e dichiarato tale: non e' stato possibile
imporre un confine sul filesystem ne' verificare tutte le chiamate ai tool. Verifica
disponibile: ogni fonte citata nelle quattro risposte compare nel log del lettore
strumentato. Non aggregare con la serie codex.

- Copertura delle fonti richieste: 3/3 in tutte e quattro le prove, entrambi i bracci.
- Zero invocazioni di memory.py. R022-1-B ha letto FRAMEWORK.md 612-680, cioe' la §12
  sulla memoria operativa, e dichiara di non aver eseguito alcuno script del framework.
- Volume di lettura confermato: R022 24.543 (A) e 42.530 (B); R016 12.571 e 12.248.
  Differenza fra bracci +17.987 su R022 e -323 su R016: il candidato costa di piu' o
  quanto la baseline, mai meno. Stessa direzione della serie codex.
- Opus legge 4,6-4,7 volte meno di GPT per la stessa copertura. La differenza sta nel
  framework, non nelle fonti: su R016 GPT legge FRAMEWORK.md intero (36.061 caratteri)
  in ogni prova, Opus legge le righe 195-235 (2.526). Quota framework dall'89% al 20%.
- Tutte e quattro le prove superano la rubrica, incluso il braccio baseline su R016.
  Nella serie codex quel braccio falliva, concludendo «0 elementi/s». Era l'unica
  differenza di qualita' trovata fra le due versioni in dieci coppie: con Opus sparisce
  da entrambi i lati, quindi era una debolezza del modello e non un merito della 3.8.1.

Cautela di misura registrata: i caratteri sono quelli emessi dal lettore; una lettura
integrale puo' essere troncata dalla pipeline dell'agente prima del modello. E' successo
in due prove, dichiarate dagli agenti; quelle letture sono contate a parte.

Valutazione delle risposte fatta dall'autore, non indipendente: pending-independent-review
resta su tutte. Due domande, una ripetizione: non separano l'effetto dalla varianza.
Nessuna modifica a runtime, corpus, oracle, prompt, preparatore o attestazioni.
Suite retrieval: 100/100. Nessuna installazione, commit o push.
