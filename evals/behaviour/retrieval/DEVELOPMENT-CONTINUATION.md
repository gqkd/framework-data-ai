# Development: catture completate e cosa manca per giudicare il grafo

Data del riepilogo: 16/09/2026; batch identificati dalle date 14-15/09. Corpus soltanto sintetico.
Questo report aggiorna gli stati storici senza riscriverli. Il
[registro numerico](DEVELOPMENT-CONTINUATION-RESULTS.json) conserva tutti i
tentativi dei quattro batch, hash delle evidenze e separazione delle repliche.

## Avanzamento

- Nuove coppie: **7/7 (100%)**, quattordici catture accoppiate.
- Development, inclusa R001 gia' eseguita: **8/8 domande (100%)**.
- Copertura di domande uniche dell'intera banca: **8/24 (33,3%)**.
- Revisione indipendente delle risposte di questo blocco: **0/16 (0%)**.
- Gruppi di fonti interamente verificati in **13/14 catture accoppiate**;
  l'eccezione e' R019-A, 5/6. Non e' un punteggio semantico.

Questi sono conteggi di esecuzione e copertura del campione, non percentuali
di efficacia. La conferma delle rubriche non equivale a un voto sulle risposte.

## Esito utile oggi

Il confronto tra versioni non dimostra ancora che il grafo migliori il lavoro.
Le domande nuove mostrano che anche la baseline collega documenti, codice,
consumatori e mandato. La lettura delle fonti non garantisce pero' che tutti
i criteri entrino nella risposta.

Nella terza ripresa si osserva per la prima volta nel campione development
un'invocazione spontanea del contesto: il precedente conteggio zero resta
valido per i suoi batch, non per tutta la campagna aggiornata. Il contesto
non esplora percorsi del grafo in quella prova. Non attribuire al grafo
differenze di token o tempo del confronto tra versioni.

## Coppie selezionate, non mescolate con le catture aggiuntive

A = 3.6.3, commit db75f310e2f42453cb0fe1b26573c3f6b5736790.
B = 3.8.1, commit faaf42259c7b43dfecbd1c52df21b2c4788cfc50.
Stesso corpus, lettore flessibile v2, gpt-5.6-sol/high richiesto,
CLI 0.150.1. L'identita' effettiva del modello non e' attestata dal parametro.
Nessun limite artificiale di token o durata per risposta.
Le inferenze usano il servizio autenticato, non un modello locale; la rete dei
comandi e' disabilitata e le sole fonti fornite sono sintetiche.

| Domanda | Gruppi A / B | Token A | Token B | Delta token B | Secondi A / B |
|---|---|---:|---:|---:|---|
| R004 | 1/1 / 1/1 | 733.234 | 1.042.637 | +42,2% | 224,190 / 206,392 |
| R007 | 4/4 / 4/4 | 575.093 | 1.135.117 | +97,4% | 183,576 / 214,163 |
| R010 | 3/3 / 3/3 | 1.172.215 | 836.106 | -28,7% | 341,118 / 262,263 |
| R013 | 4/4 / 4/4 | 825.143 | 1.661.972 | +101,4% | 379,908 / 322,500 |
| R016 | 3/3 / 3/3 | 208.470 | 429.971 | +106,3% | 96,566 / 142,629 |
| R019 | 5/6 / 6/6 | 929.352 | 768.650 | -17,3% | 318,564 / 302,113 |
| R022 | 3/3 / 3/3 | 554.768 | 601.883 | +8,5% | 245,741 / 175,185 |

Delta = (B/A - 1), solo descrittivo. Token totali = input + output:
la cache e' un sottoinsieme dell'input, il ragionamento un sottoinsieme
dell'output. Il ledger conserva anche input non in cache. I totali non
sono una fattura, ne' caratteri letti; non si sommano nuovamente cache e
ragionamento. Non calcolare un risparmio generale da una coppia per famiglia
e da blocchi separati da quote e orari differenti.

Totale dei quattro batch development: **19 tentativi**, **16 risposte complete**
(14 accoppiate + R022-A originaria e R013-B del batch 02 aggiuntive),
**3 errori di quota**. Consumo noto: **13.265.692 token**, piu' tre consumi
sconosciuti, mai trattati come zero. Una sola invocazione effettiva di memory.py
nei comandi catturati di questi quattro batch, in R013-B del batch 03.

R001 e le sue ripetizioni restano nei report precedenti: non sono nuovi
quesiti e non entrano nel totale di questo blocco. Le prove con altri
modelli e protocolli non sono aggregate.

## Osservazioni qualitative dell'autore

Le risposte sono state lette integralmente. Non e' revisione indipendente,
nessun pass/fail ufficiale e nessuna soglia cambiata dopo l'esecuzione.

| Caso | Osservazione |
|---|---|
| R004 — ragione della scelta | Entrambi spiegano isolamento e assenza di necessita' misurata della cache. Entrambi omettono la condizione esplicita di riesame della condivisione per semantiche incompatibili, richiesta dalla rubrica confermata. Lettura 1/1 non equivale a risposta completa. |
| R007 — ambito del mandato | Entrambi distinguono i segnali dei due prodotti e rifiutano il trasferimento dell'approvazione. |
| R010 — decisione superata | Entrambi distinguono JavaScript storico da Python vigente, decisione superseded da accepted e ambito dei due prodotti dalla scelta ancora aperta del terzo. |
| R013 — contratto e codice | Entrambi ricostruiscono breaking change, major version, coordinamento e clausola di preservazione. Distinguono il campo d'ingresso dal campo del report e non cambiano automaticamente la funzione condivisa. B aggiunge il rifiuto del commento non autoritativo; A esegue anche la prova del payload rinominato. |
| R016 — dato assente | B evita una portata misurata inventata. A scrive zero come carico operativo e lo distingue da capacita' non misurata: formulazione da giudicare contro la rubrica, non da trasformare senza cautela in una misura dichiarata. |
| R019 — dipendenze e test | Entrambi trovano i due consumatori, i tre test e il limite degli import statici. A esegue i tre test; B li legge senza eseguirli. A ha 5/6 gruppi verificati per un output reader vuoto, B 6/6. |

R004 e' stato confrontato con la scheda originale integrale: il requisito
sulle semantiche incompatibili era esplicitamente confermato prima delle
prove. Non viene aggiunto adesso per penalizzare una risposta.

### Test realmente eseguiti dentro le prove

- R019-A: output verificati, un test del produttore e due del consumatore
  superati. La lettura del file dei test del consumatore ha tuttavia output
  vuoto nella cattura; la risposta afferma di averlo letto integralmente.
  Eseguire un test non attesta averne letto il corpo.
- R013-B aggiuntiva del batch 02: tre test verdi e prova rinomina -> KeyError
  verificati negli eventi.
- R013-B selezionata del batch 03: due primi comandi di test falliscono per
  import rules non risolto; dopo PYTHONPATH locale, uno e due test passano.
  La risposta riporta il problema e distingue la rottura dedotta da una
  variante non eseguita. I tentativi falliti non sono cancellati.
- R013-A selezionata: verificati uno + due test verdi e KeyError sulla chiave rinominata.

Questi sono test di comportamento del codice fittizio, non test del
miglioramento del framework. Nessuna implementazione richiesta o applicata.

## L'invocazione spontanea di memoria

R013-B, batch 03, invoca memory.py context con product alpha, modalita'
analysis e la domanda come goal. Il comando emette un JSON valido di
161.138 caratteri nel log. La risposta dichiara output troncato e prosegue
sulle fonti dirette: il log completo non attesta il payload visto dal modello.

Il pacchetto dichiara:

- coverage partial, exit 1 previsto dalla CLI per tale copertura;
- 52 requirements, 28 blocchi inclusi, 99.723 caratteri di contenuto;
- nessun percorso/ arco esplorato, codice not-requested;
- 17 mapping gaps e pin del framework version-only non attestato;
- evidenze allargate ai tre prodotti: la voce strutturata used_by del
  repository condiviso e' vuota, quindi il fallback e' conservativo.

Non si tratta di crash o autorizzazione, e non prova comprensione. Il
candidato costa piu' token della baseline su questa coppia, ma differiscono
anche letture, verifiche e sessioni: il costo aggiuntivo non e' attribuito
causalmente a quella sola invocazione.

## Quanto manca per capire se il grafo aiuta?

Il passo utile non e' completare alla cieca le altre sedici domande dello
stesso A/B. E' il [confronto isolato sul grafo](GRAPH-ATTRIBUTION-PLAN.md):

1. Qualificare senza modello stesso runtime, stessi input/semi di ricerca e
   mapping in entrambi i bracci, con attraversamento degli archi abilitato
   oppure escluso. Le sonde locali sono fatte; il runner isolato no.
2. Prima lettura del segnale: quattro casi development, una coppia ciascuno,
   **otto catture**, poi valutazione cieca/indipendente delle risposte.
3. Se emerge un segnale, altre due ripetizioni: **24 catture totali**.
   Campione esplorativo, non garanzia di significativita' statistica.
4. Grafo del codice separato, soltanto con provider/binding qualificati.
   L'assenza del provider non e' un risultato negativo del grafo del codice.

Priorita': conseguenze e vincoli corretti, errori di ambito/autorita',
false rassicurazioni e letture verificate. Token e tempo vengono dopo.
Nessuna delle chiamate di questo blocco esegue quel nuovo confronto.

## Verifiche e provenienza

- **100/100 test offline retrieval passati**, 9,017 secondi; eseguiti dopo
  la fine delle catture temporizzate. Gli eventi simulati dei test non sono
  nuove chiamate al modello o risposte della campagna.
- Gli otto file del runner coincidono ancora con gli hash qualificati.
- Controllo finale del registro: 111 hash delle evidenze corrispondenti,
  19/19 preflight passed, 50 link relativi risolti e sette file senza
  errori di whitespace; somma dei token ricalcolata dai 19 record.
- Nessuna mutazione e nessuna infrastruttura invalida registrata nei 19
  risultati; gli errori di quota rimangono unavailable.
- Sei sonde locali senza modello documentate nel piano di attribuzione:
  due confronti hops=0/2 e una domanda inglese intera contro parola chiave.
- I tre moduli context/query/search e la guida operational-memory letti
  corrispondono per hash al runtime B congelato.
- I report di altre analisi gia' presenti sono preservati e non aggregati.

Preparazione congelata: manifest SHA-256
2c52d59b39b5267b8ec2c2b1a14d8e9e4b2b1dac8cf96318f0e18cabaeb403cc.
Rubriche: oracle SHA-256
717c5ff6ac3480316d0b9f181eb96c3ee4223fed1968d9e85f8f515635a9d758.
Il registro numerico punta alle directory temporanee delle prove e conserva
gli hash; la persistenza di quelle directory non e' garantita indefinitamente.

Piani: [iniziale](DEVELOPMENT-RUN-PLAN.md),
[prima ripresa](DEVELOPMENT-RUN-RESUME.md),
[seconda](DEVELOPMENT-RUN-RESUME-2.md),
[terza](DEVELOPMENT-RUN-RESUME-3.md).
La seconda dichiara esplicitamente il fallimento del salvataggio iniziale
prima del dispatch; non viene presentata come preregistrazione persistita.
La terza e' stata salvata e gli hash verificati prima delle nuove chiamate.

Nessuna modifica a runtime, corpus, oracle o runner qualificati.
Nessuna migrazione reale, installazione, riscatto reset, acquisto, commit o push.
