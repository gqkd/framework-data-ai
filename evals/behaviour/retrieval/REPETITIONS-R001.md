# Ripetizioni R001 — risultati e limiti del confronto

2026-09-14. Cinque coppie nuove, distinte dal pilota del 13/09.
**Non emerge un vantaggio stabile di costo o durata, né è provato un miglioramento
della comprensione.** Entrambi i runtime arrivano alla scelta Python e alla decisione
corrente nelle risposte lette; la qualità complessiva resta da revisionare indipendentemente.

Il [registro numerico](REPETITIONS-R001-RESULTS.json) conserva tutte le tredici
invocazioni, comprese le due interrotte e l'A completo della coppia interrotta.
Le statistiche accoppiate usano dieci catture, non undici.
Nessun risultato è stato selezionato in base alla risposta o al consumo.

## Avanzamento, con denominatori distinti

Su richiesta dell'utente, ogni aggiornamento deve indicare quale insieme misura:

| Insieme | Completato | Avanzamento |
|---|---:|---:|
| Esecuzioni accoppiate di questo blocco | 10/10 | 100% |
| Domande development distinte provate | 1/8 | 12,5% |
| Domande distinte dell'intero dataset provate | 1/24 | 4,2% |
| Test automatici mirati del runner, ultima esecuzione | 31/31 passati | 100% |
| Risposte complete di questo blocco revisionate indipendentemente | 0/11 | 0% |

Le percentuali delle domande misurano copertura, non superamento o comprensione.
Ripetere R001 non aumenta quel contatore. Non si sommano le ripetizioni extra
alle 144 prove del calendario originale per costruire una percentuale artificiale.
Le sedici domande evaluation restano riservate, non una coda avviata automaticamente.

## Che cosa è stato provato

Domanda sintetica R001: «Con quale linguaggio dobbiamo scrivere un nuovo servizio
di alpha, e chi ha deciso?». Una domanda development ripetuta, non cinque domande
diverse. Nessun prodotto reale è stato migrato o utilizzato come corpus.

| Parametro | Valore |
|---|---|
| A, precedente | 3.6.3 — db75f310e2f42453cb0fe1b26573c3f6b5736790 |
| B, candidato | 3.8.1 — faaf42259c7b43dfecbd1c52df21b2c4788cfc50 |
| Modello richiesto / reasoning | gpt-5.6-sol / high, identici |
| Identità effettiva | Non attestata; actual_model_identity resta null |
| Ambiente | CLI 0.150.1; CPython 3.14.4; Linux/WSL |
| Ingresso | Sessione nuova, AGENTS sintetico e runtime assegnato |
| Strumento di lettura | Identico: massimo 40 righe/4000 byte per pagina |
| Durata e consumo | --no-timeout; nessun tetto token o monetario del runner |
| Cache del fornitore | Non azzerata né controllata; sessione nuova non significa cache fredda |
| Grafi/provider | Nessun grafo precaricato, provider aggiunto o installazione |
| Rubrica | Conferma umana limitata a R001 e agli hash della preparazione; non approva le risposte |

Piano, [prima ripresa](REPETITIONS-R001-RESUME.md) e
[seconda ripresa](REPETITIONS-R001-RESUME-2.md) sono rimasti separati e invariati:
[preregistrazione](REPETITIONS-R001-PLAN.md). Le riprese seguono nuove richieste
utente dopo gli stop per quota; non sono retry automatici.

I runtime sono due commit esatti, non una coppia modificata per isolare ogni
singola funzionalità della memoria. Il confronto attribuirebbe differenze al
pacchetto complessivo solo dopo aver controllato gli altri fattori, non a un modulo specifico.

## Risultati accoppiati

Origine: campi di result.json, usage terminale e comandi/pagine dei rispettivi
events.stdout, aggregati in sola lettura. Somme e mediane ricontrollate con una
seconda implementazione aritmetica JavaScript. Le undici risposte complete sono
state lette integralmente dall'autore del benchmark; non è una revisione indipendente.

Tempo = durata del processo CLI, inclusi i suoi strumenti, dall'avvio alla
terminazione. Non include preparazione, preflight, analisi del valutatore o pause
fra le finestre di quota. Non è la sola latenza del modello.

| Coppia / blocco temporale | Ordine | A, secondi | B, secondi | A, token | B, token | Token B − A | Fonti A · B |
|---|---|---:|---:|---:|---:|---:|---|
| 1 / 1 | B/A | 261,397 | 211,736 | 1.890.366 | 625.259 | -1.265.107 | 2/2 · 2/2 |
| 2 / 1 | A/B | 198,579 | 174,144 | 880.351 | 906.886 | 26.535 | 2/2 · 2/2 |
| 3 / 2 | B/A | 244,225 | 266,102 | 572.001 | 868.190 | 296.189 | 2/2 · 1/2 |
| 4 / 3 | A/B | 179,364 | 121,298 | 593.394 | 332.709 | -260.685 | 1/2 · 2/2 |
| 5 / 3 | B/A | 167,355 | 223,527 | 408.791 | 687.660 | 278.869 | 2/2 · 2/2 |

Le righe 3 e 4 sono le coppie complete nelle directory retry1; i tentativi
originari non spariscono dal registro. La differenza B − A negativa indica
meno token per B, non risparmio a qualità equivalente già dimostrato.

| Misura: mediana (min–max), cinque prove per braccio | A | B |
|---|---:|---:|
| Tempo processo, secondi | 198,579 (167,355–261,397) | 211,736 (121,298–266,102) |
| Token totali cumulativi | 593.394 (408.791–1.890.366) | 687.660 (332.709–906.886) |
| Input non in cache | 61.778 (42.966–89.886) | 62.246 (48.750–75.221) |
| Input in cache | 525.568 (339.456–1.826.816) | 605.696 (265.728–851.200) |
| Output token | 7305 (5556–9864) | 6936 (4735–7746) |
| Reasoning, già nell'output | 2427 (1476–3953) | 2389 (2117–3166) |
| Pagine osservate | 37 (27–53) | 31 (29–55) |
| Comandi terminati, inclusi falliti | 44 (35–62) | 36 (32–62) |

B usa meno token in 2/5 coppie e più token in 3/5. È più veloce in 3/5.
La mediana delle differenze entro coppia è +26.535 token e −24,435 secondi.
È diversa dalla differenza fra le mediane dei due bracci: descrivono statistiche diverse.

Il totale accoppiato è 4.344.903 token per A e 3.420.704 per B.
Il totale favorisce B, mentre la mediana dei token favorisce A: il primo A
da 1.890.366 token pesa molto sulla somma. Non scegliamo la statistica più
favorevole e non trasformiamo nessuna di queste differenze in una percentuale
di risparmio del framework.

### Input, cache e output

| Prova | Input | Di cui cache | Input meno cache | Output | Di cui reasoning |
|---|---:|---:|---:|---:|---:|
| 1A | 1.880.502 | 1.826.816 | 53.686 | 9864 | 2971 |
| 1B | 617.513 | 567.680 | 49.833 | 7746 | 3166 |
| 2A | 873.046 | 830.080 | 42.966 | 7305 | 2427 |
| 2B | 899.950 | 851.200 | 48.750 | 6936 | 2389 |
| 3A | 563.870 | 473.984 | 89.886 | 8131 | 3953 |
| 3B | 860.715 | 795.904 | 64.811 | 7475 | 2922 |
| 4A | 587.346 | 525.568 | 61.778 | 6048 | 1476 |
| 4B | 327.974 | 265.728 | 62.246 | 4735 | 2117 |
| 5A | 403.235 | 339.456 | 63.779 | 5556 | 1850 |
| 5B | 680.917 | 605.696 | 75.221 | 6743 | 2314 |

Il totale è input + output. Cache e reasoning sono sottoinsiemi, non addendi
aggiuntivi. I token sono cumulativi sulle chiamate interne del turno: non sono
testo unico del corpus, dimensione di un contesto singolo o fattura monetaria.
Non abbiamo la suddivisione attestata del costo per documento o per singola lettura.
La CLI documenta eventi JSONL e usage terminale, non una ricevuta attestata del
payload di ogni documento rimasto nel contesto.
[Riferimento ufficiale](https://learn.chatgpt.com/docs/non-interactive-mode).

### Le pause sono un fattore del test

| Blocco | Coppie accoppiate | Mediana token A | Mediana token B | Mediana secondi A | Mediana secondi B |
|---|---|---:|---:|---:|---:|
| 1 | 1–2 | 1.385.358,5 | 766.072,5 | 229,988 | 192,940 |
| 2 | 3 | 572.001,0 | 868.190,0 | 244,225 | 266,102 |
| 3 | 4–5 | 501.092,5 | 510.184,5 | 173,360 | 172,413 |

Blocco 1 prima della prima pausa; blocco 2 tra le pause; blocco 3 dopo la
seconda pausa. L'A originario della coppia 4 appartiene al blocco 2 ed è
separato dalle statistiche accoppiate. Gli ordini sono tre B/A e due A/B,
non perfettamente bilanciati. Con questi numeri non si separano effetto
della versione, variabilità del percorso, cache e condizioni temporali.

## Retrieval: cosa è verificato

Richieste: STACK.md integrale (44 righe) e le sezioni Decision, Consequences
e Review condition di DEC-002. Le sezioni richieste di DEC-002 sono osservate
in 10/10 catture accoppiate. La copertura completa dei due gruppi è 4/5 per
ciascun braccio, ma non è una percentuale generale di successo del retrieval.

| Prova | Lettura con output assente nella traccia | Conseguenza |
|---|---|---|
| 3B | STACK.md, righe 1–40; item_50 | STACK non interamente verificabile; DEC-002 verificata |
| 4A nuova | STACK.md, righe 41–44; item_32 | Stessa distinzione; il front matter di STACK è invece osservato |

In entrambi i casi il comando termina con exit 0 e aggregated_output vuoto.
Non è stato osservato un frame da rifiutare: non è lecito assegnare credito
dal solo comando, dalla citazione o dalla risposta plausibile.
Questo **non dimostra che il modello non abbia ricevuto il testo**: lo stream
CLI non attesta l'input effettivo del modello. L'origine del vuoto non è determinata.

I vuoti non riguardano solo STACK: dieci eventi reader senza testo nelle
coppie selezionate, più uno nell'A aggiuntivo. Tra le fonti del framework
coinvolte ci sono FRAMEWORK.md e il template DEC. Zero unverified_frames
non implica zero letture prive di output: il contatore riguarda i frame presenti.

Una ripetizione diagnostica locale, senza LLM, dello stesso reader sulla
pagina STACK 1–40 di 3B ha restituito il frame atteso, exit 0, 742 caratteri di
testo e hash invariato. Non accredita retroattivamente la prova e non identifica
quale passaggio del client abbia perso o omesso l'output.

Le risposte a volte dichiarano letture integrali che la traccia non consente
di verificare integralmente. Sono affermazioni non attestabili dal log, non
prove sufficienti per accusare il modello di aver mentito.

## Qualità delle risposte: osservazioni, non voto

Nelle undici risposte complete lette integralmente:

- la risposta centrale è Python con DEC-002 accepted; nessuna ripropone
  JavaScript come scelta corrente;
- viene segnalata la mancanza di un approvatore esplicito;
- la precisione nel distinguere owner del documento e decisore non è uniforme:
  alcune formulazioni della coppia 4 attribuiscono inizialmente la decisione
  all'owner e poi qualificano l'affermazione. Anche B5 va rivisto su questo punto.
  Non basta cercare la parola Python per assegnare correttezza complessiva.

A1 aggiunge un disallineamento tra HEAD del codice sintetico e verified_code
in ARC. Sono stati verificati il file ARC, il codice e gli output Git:
l'osservazione è supportata, ma non riceve un bonus definito dopo il test.
A3 esegue il validatore: l'output osservato conferma 0 errori, 23 warning e
1 info; LC002 su STACK segnala 103 giorni senza review. È un'osservazione
ulteriore, non una nuova soglia o una prova di maggiore comprensione.

Restano pending-independent-review correttezza complessiva, attribuzioni,
citazioni, affermazioni extra, conformità alle istruzioni e utilità della risposta.
Non sono stati riscritti result.json, rubriche o soglie per assegnare voti.

## Frammentazione e percorsi

| Prova | Pagine framework | Pagine progetto/codice | Comandi | SKILL.md osservate | Reader con output vuoto |
|---|---:|---:|---:|---|---:|
| 1A | 41 | 12 | 62 | audit (12 pagine) | 0 |
| 1B | 20 | 11 | 36 | nessuna SKILL.md | 1 |
| 2A | 25 | 8 | 37 | nessuna SKILL.md | 1 |
| 2B | 48 | 7 | 62 | audit (13 pagine) | 1 |
| 3A | 41 | 12 | 60 | audit (12 pagine) | 0 |
| 3B | 42 | 8 | 56 | audit (13 pagine) | 1 |
| 4A | 18 | 9 | 35 | nessuna SKILL.md | 4 |
| 4B | 20 | 9 | 32 | nessuna SKILL.md | 0 |
| 5A | 28 | 9 | 44 | nessuna SKILL.md | 2 |
| 5B | 18 | 11 | 32 | nessuna SKILL.md | 0 |

Sono pagine osservate, comprese eventuali riletture, non documenti distinti.
Per esempio 4B legge FRAMEWORK in 17 pagine e poi rilegge due pagine:
19 eventi, 680 righe uniche e 80 righe ripetute.

Occorre separare tre cose:

1. **Frammentazione del progetto:** una risposta può richiedere stack,
   decisione corrente, precedente decisione, architettura e codice.
   È una proprietà legittima del corpus; non è stata ridotta per far vincere B.
2. **Paginazione dello strumento:** il reader v1 impone 40 righe/4000 byte.
   Lo stesso FRAMEWORK di 650 righe in A e 680 in B richiede almeno 17 pagine.
   Questo vincolo è del banco di prova, non del formato documentale.
3. **Percorso scelto dall'agente:** leggere audit, schemi, template o codice
   aggiunge passaggi diversi. Audit è osservata in due prove A e due prove B;
   l'A aggiuntivo legge resolve. È lettura di istruzioni, non misura del
   triggering di un plugin installato.

Il primo pilota aveva audit solo in B; nella prima nuova coppia avviene il
contrario. Anche con la stessa versione cambiano percorso e consumo.
Le letture in più sono una possibile componente del costo, non una
spiegazione causale completa: ad esempio A1 e A3 hanno entrambe 53 pagine
osservate ma consumi molto diversi.

Nei comandi delle tredici tracce non sono osservate invocazioni di memory.py.
Nessun provider code graph è stato aggiunto. **Questa domanda non misura il
vantaggio del grafo, dell'analisi di impatto, della memoria fra sessioni,
dello sviluppo o della collaborazione fra agenti.**

## Registro dei costi, senza tentativi nascosti

| Insieme | Invocazioni | Token noti |
|---|---:|---:|
| Cinque coppie complete selezionate | 10 | 7.765.607 |
| A completo della coppia 4 interrotta | 1 | 471.845 |
| B interrotti per quota, coppie originarie 3 e 4 | 2 | Sconosciuti |
| Questo blocco | 13 | **8.237.452 + due consumi sconosciuti** |
| Pilota precedente, incluse due prove infrastrutturali non valide | 4 | 3.788.103 |
| Totale storico: pilota + ripetizioni | 17 | **12.025.555 + due consumi sconosciuti** |

Le undici catture complete sono pending-review; le due interrotte sono
unavailable, non errori di comprensione. L'A originario della coppia 3 non
è mai stato invocato e non è un quattordicesimo tentativo.

I processi delle dieci prove accoppiate sommano 2.047,727 secondi, circa
34 minuti. Tutti i tredici tentativi sommano 2.322,971 secondi, circa
38 minuti e 43 secondi. Preparazione, preflight, valutatore e attese delle
quote sono esclusi: la campagna non è stata continua.

Non sono compresi i token di questa conversazione di costruzione e analisi.
Nessun acquisto, reset di quota o retry automatico; nessun costo mancante
convertito in zero.

## Modifiche e verifica tecnica

Le sole estensioni implementative di questo blocco, prima delle invocazioni:

- run.py: --no-timeout e --pair-order AB/BA esplicito e registrato;
- test_retrieval_runner.py: verifica degli override, default preservati e
  passaggio di timeout None alla cattura;
- RUNNER.md e documenti di preregistrazione/risultato aggiornati.

Corpus, oracle, preparatore, prompt, reader, parser e commit dei runtime
sono rimasti congelati. I cinque hash degli input del runner e il prompt
coincidono in tutti i sette batch, comprese le riprese.

| Controllo | Esito |
|---|---|
| Test mirati prima del blocco | 31 passati, 5,124 s |
| Gate completo prima del blocco | 321 test passati, 117,726 s; gate superato |
| Test mirati dopo le ultime invocazioni | 31 passati, 6,991 s |
| Contabilità del riepilogo | Somme/mediane PowerShell ricontrollate in JavaScript |
| Inventari delle tredici prove | Nessuna mutazione osservata a fonti, runtime, Git o reader |
| Stream | Nessuna riga JSON invalida; i vuoti descritti sopra restano un limite |
| Richieste al modello nei test unitari | Simulate; non ulteriori invocazioni del benchmark |

I 31 test sono inclusi nei 321, non si sommano. I test automatici dimostrano
proprietà del runner, non il miglioramento del modello. OpenAI Docs ha guidato
il controllo delle opzioni CLI e della forma degli eventi; la disponibilità
locale, gli stop per quota e i vuoti sono stati verificati sulle tracce reali.

Nessuna modifica a regole, skill, dipendenze o versione del runtime;
nessuna migrazione, installazione, commit o push.

## Privacy e conservazione

Inferenza remota tramite l'autenticazione CLI esistente: al fornitore arrivano
prompt e contenuti sintetici selezionati. Non è un test offline.
I probe del runner verificano i confini dei comandi: rete negata, fonti non
scrivibili, valutatore e prove sorelle non leggibili. Nessun corpus reale
o dato di cliente è stato usato; nessuna credenziale copiata o pubblicata.

Nessuna nuova dipendenza: libreria standard, dipendenze esistenti del framework,
Git e CLI già installata. Le evidenze grezze restano locali, non pubblicate.
Le directory sono temporanee: il JSON qui accanto conserva numeri e hash,
**non sostituisce un archivio delle tracce e delle risposte**.

Sotto /tmp/framework-retrieval-r001-repeat-20260914-:
01, 02, 03, 03-retry1, 04, 04-retry1, 05.
In ogni batch: run.json; in trials/R001-1-A e trials/R001-1-B:
result.json, answer.md se prodotta, events.stdout, events.stderr, prompt,
preflight e inventari. Percorsi esatti e SHA-256 sono nel registro JSON.

## Cosa fare dopo, non ancora eseguito

1. Revisionare le risposte R001 indipendentemente, incluse attribuzioni e
   letture dichiarate ma non verificabili.
2. Qualificare separatamente la raccolta con letture ordinarie: stesso corpus,
   nessun accorpamento dei documenti, fonti scelte dall'agente, nessun tetto di
   durata o token. Distinguere output vuoto, troncato e verificato; non assumere
   che allargare le pagine risolva da solo i vuoti della CLI.
3. Dopo la qualificazione, confrontare A/B con quel metodo in una campagna
   distinta da v1. Non togliere gli obblighi di lettura per migliorare un numero.
4. Revisionare e provare gli altri quesiti development: impatti fra componenti,
   decisioni superate, codice assente, autorizzazioni e relazioni documentali.
5. Misurare separatamente domande successive nella stessa sessione e, poi,
   modifiche al codice e contributi concorrenti. Non mischiarle al bootstrap
   di una sessione nuova.

Le altre 23 domande non sono state eseguite. Le sedici evaluation restano
riservate e non sono state usate per adattare il comportamento del runner.
