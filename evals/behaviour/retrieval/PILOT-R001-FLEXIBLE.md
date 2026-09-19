# R001 — pilota separato con letture flessibili

2026-09-14. **Due catture completate, nessun miglioramento generale dimostrato.**
Il nuovo reader funziona senza pagine imposte; persistono anomalie del log che
impediscono di equiparare il testo catturato a quello visto dal modello.

Piano scritto prima delle chiamate: [preregistrazione](PILOT-R001-FLEXIBLE-PLAN.md).
Metodo: [lettore flessibile v2](FLEXIBLE-READER.md).
Dati, percorsi e SHA-256: [registro numerico](PILOT-R001-FLEXIBLE-RESULTS.json).
Le [cinque coppie v1](REPETITIONS-R001.md) restano una serie separata.

## Avanzamento: non confondere ripetizioni, copertura e qualita'

| Oggetto | Completati / totale | Percentuale |
|---|---:|---:|
| Nuove catture del pilota | 2/2 | 100% |
| Nuovi test offline del metodo | 17/17 | 100% |
| Test della suite memory nel gate completo | 338/338 | 100% |
| Preflight senza modello A/B | 2/2 | 100% |
| Domande uniche raggiunte nell'intera campagna | 1/24 | 4,2% |
| Domande development raggiunte | 1/8 | 12,5% |
| Revisione indipendente delle nuove risposte | 0/2 | 0% |

I 17 nuovi test sono inclusi nei 338, non si sommano. Le due invocazioni
ripetono R001 e non aumentano la copertura. Le altre 23 domande non sono state
eseguite. Nessun punteggio semantico e' stato assegnato automaticamente.

## Condizioni

- A: framework 3.6.3, commit db75f310e2f42453cb0fe1b26573c3f6b5736790.
- B: framework 3.8.1, commit faaf42259c7b43dfecbd1c52df21b2c4788cfc50.
- Ordine A/B, una sessione fresca per braccio, modello richiesto gpt-5.6-sol,
  reasoning high, CLI 0.150.1, Python 3.14.4. Identita' effettiva del modello
  non attestata dall'etichetta richiesta.
- Stesso corpus sintetico congelato, stessa domanda e stessa rubrica R001.
  Nessun prodotto reale migrato, nessun corpus cliente nel benchmark.
- Reader strumentato con file intero per default o --start/--end scelti
  dall'agente. Nessuna pagina imposta di 40 righe/4000 byte. Resta la soglia
  di sicurezza preesistente di 2 MB per file, non un budget del modello.
- --no-timeout: nessun tetto token, monetario o di durata del runner.
  Nessun retry completo, acquisto, reset di quota, installazione o provider.
- Nessun grafo precaricato, mapping aggiuntivo o modifica al runtime.

La preparazione e' in /tmp/framework-retrieval-v1-final-20260912.
Il preflight separato e' in /tmp/framework-retrieval-r001-flexible-preflight-20260914.
Le prove sono in /tmp/framework-retrieval-r001-flexible-20260914-01.

## Risultati osservati

| Misura | A: precedente | B: nuova |
|---|---:|---:|
| Durata processo, secondi | 192,359 | 249,301 |
| Token input | 578.581 | 359.507 |
| Di cui input in cache | 476.032 | 276.736 |
| Input non in cache | 102.549 | 82.771 |
| Token output | 5.086 | 7.050 |
| Di cui reasoning | 1.997 | 3.780 |
| Totale input + output | 583.667 | 366.557 |
| Comandi reader | 13 | 21 |
| Richieste di file intero | 13 | 14 |
| Richieste con intervalli espliciti | 0 | 7 |
| Output reader con frame verificato | 13/13 | 18/21 |
| Output reader vuoti, exit 0 | 0 | 3 |
| Gruppi di fonti richieste coperti nel log | 2/2 | 2/2 |
| Tutti i comandi completati, anche falliti | 20 | 26 |
| Comandi memory.py osservati | 0 | 0 |

In questa singola coppia B usa **217.110 token in meno (-37,2%)** ma impiega
**56,942 secondi in piu' (+29,6%)**. Non e' una stima del risparmio del framework:
una sola domanda, ordine fisso, cache non controllata, percorsi di ricerca diversi
e visibilita' degli output incompleta. Il risultato non e' aggregato alle mediane v1.

I token sono il consumo cumulativo del turno riportato dalla CLI, non la
dimensione del corpus. Cache e reasoning sono sottoinsiemi, non addendi ulteriori.
Non sono euro, ne' consumo della sola lettura. Le durate misurano il processo
della prova, non includono preparazione, preflight o analisi di questo agente.

Consumo noto di questo blocco: **950.224 token**, nessun tentativo a consumo
sconosciuto, 441,660 secondi di processo complessivi. Storico con i blocchi v1:
**12.975.779 token noti piu' due consumi sconosciuti**, su 19 tentativi.
Il costo dell'agente che prepara e analizza il benchmark non e' incluso.
Somme estratte in PowerShell e ricontrollate in JavaScript.

## Cosa dicono le risposte, e cosa non attestano

Entrambe le risposte sono state lette integralmente dall'autore del benchmark:
indicano Python, citano la decisione accepted che sostituisce quella precedente
e distinguono l'owner del documento dal decisore non esplicitamente registrato.
STACK.md e DEC-002 sono stati riletti integralmente per controllare queste
affermazioni; preamble e template DEC sono stati controllati nei passaggi
owners/approvers. Questo e' un controllo dell'autore, **non revisione indipendente**.

Entrambe le catture contengono STACK.md completo e le sezioni richieste di
DEC-002: Decision, Consequences e Review condition. Cio' attesta gli output,
non la comprensione. In B e' osservata anche la lettura del piccolo file Python;
non e' un test del grafo del codice. Non si osservano invocazioni memory.py
nei comandi di nessun braccio.

Il giudizio ufficiale resta pending-independent-review. Non si premiano a
posteriori letture extra e non si trasformano le citazioni in un voto.

## Il risultato piu' utile: tre livelli di evidenza distinti

1. **Fonte su disco**: il documento e il suo hash.
2. **Testo nello stream CLI**: frame completo, intervallo e hash verificabili.
3. **Testo visibile al modello e comprensione**: non attestati dal livello 2.

In B, item_9 contiene un frame verificato di FRAMEWORK.md, righe 1-680.
La risposta finale dichiara invece che la lettura integrale era troncata e
rivendica soltanto intervalli selezionati. E' una discrepanza osservata:
non prova quale livello del client abbia tagliato qualcosa, ne' esclude
un errore dell'agente nel descrivere la propria lettura. Non si deduce la causa.

I tre output vuoti di B sono:

| Evento | Comando di lettura | Altra evidenza osservata |
|---|---|---|
| item_7 | product.yaml, intero file | Nessun frame del manifest accreditato; citato comunque in risposta |
| item_29 | SKILLS.md, righe 1-32 | Frame del file intero gia' catturato in item_10 |
| item_30 | FRAMEWORK.md, righe 250-263 | Frame del file intero gia' catturato in item_9 |

Non sono tre documenti necessariamente mai consegnati al modello. Non sono
nemmeno tre troncamenti dimostrati: il campo aggregated_output e' vuoto.
Il manifest e' corto e gli altri due comandi chiedono intervalli brevi:
non basta la lunghezza dei file a spiegare tutte queste omissioni.

Nessun frame troncato/non verificabile viene rilevato dalla diagnostica in
queste due catture. Questo **non contraddice** il troncamento dichiarato da B:
la diagnostica esamina lo stream, non il payload interno del modello.
Il testo di product.yaml dichiarato come letto non riceve credito retroattivo.

A sceglie solo file interi; B sceglie anche sette intervalli, compresi riesami
di un file gia' presente nel log. La frammentazione quindi puo' esistere senza
paginazione imposta. Non tutte le letture aggiuntive sono spreco e non tutte
le riletture sono recuperi riusciti: occorrono fonte, intervallo e motivo.
Nemmeno meno comandi implica automaticamente meno token o meno tempo.

## Qualificazione tecnica e privacy

- Nuovi 17 test offline passati in 4,575 s; verificano file interi, intervalli,
  input invalidi, symlink/confini, frame, diagnostica, hash, isolamento da v1
  e percorso simulato di esecuzione.
- Gli stessi 17 test sono passati anche dopo il pilota, in 3,203 s,
  senza nuove chiamate al modello.
- Gate tests/selfcheck.py passato; la sottosuite memory riporta 338 test
  in 265,695 s, oltre agli altri controlli di coerenza del gate.
- Preflight reale senza modello passato A/B. Ripetuto dal runner prima di
  ciascuna prova reale: fonti/runtime leggibili ma non scrivibili, scratch
  scrivibile, rete dei comandi e letture di evaluator/prova sorella negate.
- Diagnostica applicata in sola lettura alle undici catture complete delle
  ripetizioni v1: coincide con gli undici output vuoti gia' registrati.
  Nessuna causa nuova dedotta e nessun risultato storico riscritto.
- Otto input del runner invariati rispetto al nuovo manifest; cinque input
  v1 invariati rispetto al ledger storico; sette input del generatore
  invariati rispetto al manifest congelato. Nessuna mutazione nelle due prove.
- Nessuna riga JSON invalida o errore infrastrutturale. rg non e' disponibile
  nel sandbox: entrambi tentano il comando, poi usano find/grep.
  Quel costo resta contabilizzato; non e' stato installato nulla.
- Nessuna nuova dipendenza. Inferenza remota tramite CLI autenticata:
  esecuzione locale dei tool non significa modello offline. Solo dati
  sintetici nelle prove; nessun commit, push o pubblicazione delle tracce.

OpenAI Docs ha guidato la verifica del formato degli eventi; le anomalie qui
descritte sono osservazioni locali, non garanzie della documentazione.
[Riferimento ufficiale](https://learn.chatgpt.com/docs/non-interactive-mode).

## Decisione sul seguito

Il reader flessibile e' qualificato tecnicamente come condizione distinta,
**non come strumento che attesta il contenuto visto dal modello**.
Non promuovere il -37,2% a beneficio del prodotto e non ripetere R001
indefinitamente cercando una coppia favorevole.

La campagna di confronto dei metodi di lettura, prevista dalla preregistrazione,
resta separata e non e' stata avviata: richiede repliche controbilanciate e
metriche esplicite per output, copertura e qualita'. Prima di altre chiamate
costose, usare le anomalie conservate per qualificare il contratto del client
e sottoporre le risposte a revisione indipendente.

Per aumentare davvero la copertura servono poi le altre sette domande
development, previa revisione delle loro rubriche; R001 e' l'unica confermata.
Le sedici evaluation restano riservate, non usate per tarare il metodo.
Ancora non misurati: vantaggio causale dei grafi, impatto delle modifiche sul
codice, indici obsoleti, task di sviluppo e collaborazione tra contributori.

Gli SHA-256 del registro identificano le evidenze locali temporanee; non ne
garantiscono la conservazione. I grezzi in /tmp non sono archiviati nel repository.
