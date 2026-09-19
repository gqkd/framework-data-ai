# Isolare il beneficio del grafo — piano e verifica del 15/09

Stato: diagnosi locale verificata; esperimento causale ancora da eseguire.
Aggiornamento 16/09: [qualificazione G0](GRAPH-ABLATION-G0.md) eseguita su 4/4
casi, senza nuovi gruppi richiesti con i seed fissati. Gate complessivo non
superato; G1 resta 0/8. Serve rivedere il disegno prima delle chiamate al modello.
Non e' un giudizio indipendente delle risposte e non modifica rubriche o runtime.
I report MECHANISM-DIAGNOSIS.md, GRAPH-RETRIEVAL.md e OPUS-ARENA.md
sono stati trovati gia' presenti: restano intatti, con le cautele sotto.

## Risposta breve

Non occorre completare tutte le 24 domande per ottenere un primo segnale.
Occorre cambiare il confronto: **stesso runtime candidato, con e senza
navigazione del grafo**, non vecchio runtime contro nuovo runtime.
Le catture A/B finora osservate non dimostrano un beneficio del grafo.
L'assenza di uso spontaneo e' un risultato operativo importante, ma non misura
cosa succederebbe se il grafo fosse usato.

## Verifiche locali, senza modello

Letti integralmente: references/operational-memory.md e i moduli
src/framework_data_ai/memory/context.py, query.py, search.py;
graph_retrieval_bench.py e run_graph.py; i tre report citati sopra.

1. context.compose valida goal e lo registra nel report, ma non lo usa
   per cercare o classificare le fonti. Seleziona tutti gli artefatti nell'ambito
   conservativo; il selettore aggiunge percorsi, non restringe quella selezione.
   I repository condivisi possono allargare l'ambito delle evidenze.
   Questo e' coerente con il contratto prudenziale, ma non e' un retrieval
   mirato alla domanda. Il limite e' confermato dal codice, non solo da due output.

2. La ricerca literal confronta l'intera stringa come sottostringa.
   Una domanda completa puo' fallire anche se scritta nella lingua del corpus.
   FTS5 usa invece token in OR. Il risultato zero delle domande italiane
   non isola quindi il solo effetto della lingua.

3. graph_retrieval_bench.py non passa --hops: query usa hops=0.
   Il 48% riportato per i termini inglesi e' una condizione lessicale
   con termini e limite fissati, non il tetto del grafo. Non prova
   che attraversare relazioni non possa recuperare altro.
   Il campo question_sensitive=False e' assegnato nel codice dello script,
   non calcolato confrontando i pacchetti in quella esecuzione.

4. M3 conta percorsi in required_sources, inclusi quelli deferred.
   Non misura lettura completa delle sezioni. Confrontarlo con i gruppi
   verificati dal lettore dell'agente richiede metriche omogenee.
   Anche i denominatori differiscono: tutte le 24 domande per il motore,
   solo le domande gia' eseguite per gli agenti.
   Caratteri emessi non sono token del modello ne' costo monetario.

5. run_graph.py confronta ancora runtime A con runtime B piu' un'istruzione
   di uso. Puo' misurare quel pacchetto di cambiamenti, ma non isolare gli
   archi o il solo motore. Non va rinominato retroattivamente come ablation.

6. Nessuna invocazione osservata significa mancata adozione in quelle prove,
   non irraggiungibilita' tecnica. Una prova con altro modello non stabilisce
   da sola che la differenza precedente sia causata dal modello.
   Gli output vuoti non sono prova di un guasto casuale: la causa resta ignota.

7. Il minimo calcolato con le sole fonti oracle conosce gia' la risposta ed
   esclude le regole necessarie per operare in sicurezza. E' un riferimento
   descrittivo, non un costo operativo raggiungibile dimostrato. Il rapporto
   con quel minimo non prova da solo che il resto della lettura sia inutile.

### Due sonde riproducibili sul runtime B congelato

Python gia' disponibile: /tmp/framework-phase7-validation-20260909/bin/python.
Runtime e corpus: /tmp/framework-retrieval-v1-final-20260912/arms/B.
Nessuna installazione, rete, scrittura al corpus o invocazione LLM.

Comando: memory.py query --root <project> --limit 20, con:

| Selezione | hops | Nodi | Archi | Nodi raggiunti attraversando archi | Troncato |
|---|---:|---:|---:|---:|---|
| --text spreadsheet | 0 | 3 | 0 | 0 | no |
| --text spreadsheet | 2 | 3 | 0 | 0 | no |
| --node products/alpha/changes/CHG-001-boundary.md | 0 | 1 | 0 | 0 | no |
| stesso nodo | 2 | 3 | 2 | 2 | no |

Correzione del 16/09: la seconda sonda aggiunge un nodo entry SIG-001 e
il documento decisions/DEC-005-boundary.md al mandato iniziale. Il percorso
products/alpha/LOG.md compare come provenienza dell'entry, non come documento
selezionato con corpo esportato. La versione precedente di questo paragrafo
confondeva questi due fatti. E' navigazione possibile, non ancora un
miglioramento dimostrato nella risposta.
La prima non migliora: i tre documenti trovati lessicalmente non
aggiungono vicini con le relazioni selezionate. Entrambi gli esiti contano.

Sonda lessicale aggiuntiva, completata dopo la ripresa utente: con hops=0
e engine literal, «Which language should we use for alpha services?»
restituisce zero documenti, mentre «language» ne restituisce due.
Entrambe le stringhe sono inglesi. Conferma il limite della ricerca per
frase intera senza attribuire tutto alla differenza di lingua. Il primo
tentativo di questa sonda era stato negato per quota del servizio di
approvazione e non aveva eseguito il comando.

I tre moduli letti e operational-memory.md sono stati confrontati per hash
con il runtime B congelato: tutti e quattro corrispondono. HEAD del checkout
al controllo: faaf42259c7b43dfecbd1c52df21b2c4788cfc50.

## Piano minimo per una risposta utile

### Aggiornamento: uso spontaneo osservato nella terza ripresa

R013-B del batch 20260915-03 ha invocato spontaneamente context, senza
istruzione aggiuntiva nel prompt. Il conteggio zero delle serie precedenti
non va piu' usato come descrizione di tutta la campagna aggiornata.

Il comando --product alpha produce coverage=partial, exit 1 (esito previsto
dalla CLI per copertura parziale), 52 requirements, 28 blocchi consegnati,
99.723 caratteri di contenuto, zero percorsi/archi esplorati e codice
not-requested. L'ambito conservativo comprende tutti e tre i prodotti;
17 mapping gaps e un gap sul pin version-only restano visibili.

Il log contiene JSON valido di 161.138 caratteri; la risposta dichiara
troncamento e non usa contenuto non recuperato. Non e' prova di consegna
integrale al modello. La prima invocazione osservata del contesto non e'
ancora una prova di attraversamento utile degli archi o di miglioramento.
Questa osservazione aggiorna la diagnosi, non cambia il protocollo sotto.

La causa dell'espansione e' verificata con build --dry-run --export:
il nodo repository:platform:rules ha used_by=[]. PLATFORM.md, letto per
intero, dichiara alpha/beta nel proprio ambito e nel corpo, ma non ha
used_by nella voce code.rules. compose tratta l'assenza strutturata come
insieme dei consumatori sconosciuto e include tutti i prodotti. Non e'
una prova che gamma consumi la libreria. Un eventuale test con mapping
arricchito deve darlo a entrambi i bracci in una nuova fixture dichiarata,
senza alterare il corpus legacy congelato per far riuscire il grafo.

### G0 — Qualificare il confronto, senza nuove chiamate LLM

- Stesso commit candidato faaf42259c7b43dfecbd1c52df21b2c4788cfc50,
  stessi documenti, istruzioni, metadati, lettore e query iniziali nei due bracci.
- Braccio S: medesima ricerca lessicale e accesso diretto ai file, hops=0.
- Braccio G: medesima ricerca, con navigazione delle relazioni abilitata.
- Se un seed e' scelto dall'agente, registrarlo prima della biforcazione
  e usarlo in entrambi i bracci; mai derivarlo dalla soluzione oracle.
- Non dare al solo G un indice curato o informazioni nuove. Se occorre
  arricchire il mapping, farlo identicamente nei due bracci e dichiarare
  la nuova versione del corpus. Non toccare il corpus congelato.
- Per isolare davvero la disponibilita', il wrapper di test deve impedire
  il traversal nel braccio S. Una sola istruzione «non usare il grafo»
  permette un confronto di workflow, non garantisce l'isolamento tecnico.
- Verificare almeno un caso con archi utili e un caso senza archi utili;
  sorgenti identiche, provenienza corretta, percorsi differiti distinguibili.
- Verificare il wrapper con test offline e controllo anti-contaminazione.
  Non cambiare il runtime del framework per migliorare il risultato del test.

Uscita: protocollo congelato, preparazione riproducibile e manifest comparabile.

### G1 — Primo segnale end-to-end, su casi gia' development

Proposta: R007, R013, R019, R022; due bracci per domanda.
Una prima coppia per ciascun caso = **8 catture**, non una prova statistica
definitiva. Se G0 mostra assenza di archi pertinenti per un caso, segnalarlo
prima delle chiamate: misura un limite del mapping, non un fallimento del LLM.
Le fonti di codice restano leggibili direttamente in entrambi i bracci.

Indicatori principali, applicando le rubriche gia' confermate:

- vincoli e condizioni di riesame corretti e completi;
- conseguenze per altri componenti/prodotti e test da coinvolgere;
- errori di ambito o di autorita', conseguenze inventate, falsi «nessun impatto»;
- lettura verificata delle sezioni richieste, non sola presenza del percorso.

Per ogni conseguenza aggiuntiva: fonte, percorso del grafo usato, correttezza
verificabile. Separare scoperta spontanea dall'uso guidato: questo e' uso guidato.

Indicatori secondari: elapsed wall time, input, cached input, output,
ragionamento se disponibile, comandi, testo emesso e riletture. Non confondere
cache con risparmio monetario o caratteri con token. Nessun tetto artificiale
di tempo o token; limite delle invocazioni e' il campione, non il budget
per risposta. Stop su errore/quota, tentativi falliti conservati senza retry.

Valutazione delle risposte cieca rispetto al braccio, con revisione indipendente.
L'analisi dell'autore resta separata. Il primo segnale puo' essere:
beneficio osservato, nessuna differenza, regressione oppure inconcludente.

### G2 — Verificare che il segnale si ripeta

Solo dopo G1: altre due ripetizioni per caso, totale **24 catture / 12 coppie**.
Ordine controbilanciato e bloccato per domanda e sessione; conservare tutte
le repliche. Queste quantita' sono un disegno esplorativo, non una garanzia
di potenza statistica. Non riciclare le stime di varianza di R001 come
garanzia per qualita' o per domande diverse.

Se la baseline satura tutte le rubriche, introdurre un nuovo corpus sintetico
con distrattori, relazioni multi-hop e mapping incompleto, con verita' attesa
validata prima dell'uso. Non modificare retroattivamente le domande per
far vincere il grafo. I 16 holdout originari gia' ispezionati da analisi
successive non sono piu' una verifica cieca per decisioni prese dopo
quelle analisi: la provenienza dell'esposizione va registrata.

### G3 — Grafo del codice, esperimento distinto

Non giudicato dall'assenza del provider. Prima di testarlo: binding dei
checkout sintetici, provider fissato, disponibilita', snapshot e copertura
verificati. Entrambi i bracci ricevono le stesse versioni del codice.
Confrontare poi documenti+lettura del codice contro gli stessi piu' grafo
del codice; non mescolare con G1. Installazioni nuove richiedono un passaggio
esplicito, nessuna viene eseguita da questo piano.

## Come decidere

Il grafo merita integrazione operativa se aggiunge conseguenze/vincoli corretti
o preserva la qualita' riducendo in modo ripetibile lavoro e durata, senza
aumentare errori di ambito, autorita' e false rassicurazioni.
Se cambia solo la visualizzazione o aumenta testo senza beneficio, limitarlo
alla navigazione/diagnosi e migliorare il routing; non imporne l'uso universale.

La priorita' verificata e' distinguere **contesto di sicurezza** da
**evidenze pertinenti alla domanda**. Non eliminare vincoli obbligatori per
ottenere meno token. Il motore attuale puo' mantenere il primo ruolo anche
se il secondo richiede miglioramenti.

Non e' stata avviata alcuna chiamata G1/G2/G3 con questo documento.
