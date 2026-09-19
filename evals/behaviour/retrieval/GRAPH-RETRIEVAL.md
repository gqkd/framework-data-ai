# Il grafo migliora il retrieval? Misura diretta, senza modello

Le condizioni A e B misuravano se un agente *scopre* il motore di memoria. Non lo ha mai
fatto: zero invocazioni in diciannove prove reali. Questo documento misura una cosa
diversa e piu' utile: **il motore, interrogato direttamente, trova le fonti che servono?**

Nessuna chiamata al modello. Ground truth: i gruppi di fonti dell'oracle congelato, che
sono un AND di gruppi, ciascuno un OR di alternative. Riproducibile con
[graph_retrieval_bench.py](graph_retrieval_bench.py); numeri in
[GRAPH-RETRIEVAL-RESULTS.json](GRAPH-RETRIEVAL-RESULTS.json).

La consegna di un percorso non e' comprensione e non e' una risposta corretta. Qui si
misura soltanto il canale di retrieval.

## Il grafo che viene costruito

`memory.py build` sul progetto sintetico produce 48 nodi, 48 archi, 35 sorgenti,
17 gaps, 0 issues. Il grafo esiste e si costruisce senza errori.

## Tre metodi, 24 domande, 75 gruppi richiesti

| Metodo | Gruppi trovati | Recall | Costo medio consegnato | Precisione |
|---|---:|---:|---:|---:|
| M1 — `query` con il testo della domanda | 0/75 | **0,0%** | 0 caratteri | — |
| M2 — `query` con i termini inglesi giusti | 36/75 | **48,0%** | 4.331 caratteri | 17,8% |
| M3 — `context` pack documentato | 54/75 | **72,0%** | 99.723 caratteri | 7,6% |
| Agente che legge i file, osservato | — | **100%** | 58.598-172.444 | — |

I termini di M2 derivano dal testo di ciascuna domanda, mai dalle risposte dell'oracle,
e sono elencati nello script. M2 e' un **tetto superiore**: presuppone che l'agente
indovini il termine inglese corretto. Non e' comportamento osservato.

## Perche' M1 e' a zero

`memory.py query` confronta stringhe. Le ventiquattro domande sono in italiano, il corpus
e' in inglese. Nessuna resa letterale di una domanda produce un documento:

| Termine | `literal` | `fts5` |
|---|---:|---:|
| identificatori | 0 | 0 |
| identifier | 11 | 8 |
| celle formattate | 0 | 0 |
| cell formatting | 1 | 2 |
| elementi al secondo | 0 | 0 |
| throughput | 3 | 3 |

Entrambi i motori si comportano allo stesso modo. Non e' un difetto del motore di ricerca:
e' che la ricerca e' lessicale e il benchmark interroga in un'altra lingua.

## Perche' M2 si ferma a meta'

Il recall di M2 crolla con il numero di gruppi richiesti:

| Gruppi richiesti | Domande | Recall |
|---:|---:|---:|
| 1 | 5 | **100,0%** |
| 2 | 3 | 50,0% |
| 3 | 7 | 47,6% |
| 4 | 4 | 43,8% |
| 5 | 3 | 40,0% |
| 6 | 2 | 41,7% |

Il grafo regge perfettamente sulle domande a fonte singola — dove un grafo non serve — e
scende sotto la meta' su tutte le altre. Le domande a fonte multipla sono esattamente
quelle per cui un grafo dovrebbe esistere.

## Perche' M3 non arriva a 100 nonostante consegni tutto

Il context pack elenca 42 percorsi, cioe' l'intero corpus documentale, e consegna 99.723
caratteri. Perde comunque **21 gruppi su 75**, e sono tutti la stessa cosa:

| Gruppi persi | Percorso |
|---:|---|
| 6 | `code/alpha-api/service.py` |
| 5 | `code/beta-worker/worker.py` |
| 3 | `code/beta-worker/tests/test_worker.py` |
| 2 | `code/shared-rules/rules.py` |
| 2 | `code/alpha-api/contracts/item.schema.json` |
| 2 | `code/alpha-api/tests/test_service.py` |
| 1 | `code/review-comment.txt` |

**Il pacchetto non contiene codice.** Ogni domanda che richiede di leggere codice perde
quei gruppi: R019 2/6, R020 1/4, R021 1/3, R013 2/4, R015 3/6, R014 3/5, R006 3/5.

## Il grafo del codice non e' attivabile qui

`memory.py code --root project --source worktree` esce con codice 2 e restituisce
0 nodi, 0 archi, 0 sorgenti, 0 bridges, `coverage: unavailable`. Le tre repository
dichiarate riportano `binding-unavailable` e `path_status: unresolved`. La causa e'
esplicita in `doctor`:

```json
{"provider":"enola","version":"0.4.15","status":"unavailable","reason":"provider-not-configured"}
```

Il provider esterno non e' configurato, e sia `references/operational-memory.md`
(«Do not install a provider») sia il prompt del benchmark («Non installare provider»)
vietano di installarlo. La meta' codice della funzionalita' **non e' esercitabile** in
questo ambiente: non e' un risultato negativo del grafo, e' una condizione mancante.

## Il grafo migliora il consumo di token?

Costo per arrivare alla copertura completa dei gruppi richiesti, misurato sulle dimensioni
reali dei file, un rappresentante per gruppo:

| Percorso | Caratteri, mediana | Rapporto sul minimo |
|---|---:|---:|
| Minimo teorico: leggere solo le fonti richieste | **1.528** | 1,0x |
| Via grafo: context pack + i file di codice che il pack non contiene | **99.723** | **65,3x** |
| Agenti che leggono i file, osservato nelle prove | **103.510** | 67,8x |

Il percorso via grafo costa **99.723 caratteri contro i 103.510 osservati: il 3,7% in meno**,
cioe' praticamente la stessa cosa. Il motivo e' strutturale, non contingente: il pacchetto
e' un blocco fisso che consegna l'intero corpus documentale fino al tetto di `--text-budget`,
quindi legge tutto esattamente come fa l'agente, solo preconfezionato.

Entrambi i percorsi stanno a circa **66 volte** il minimo teorico. Il margine di
efficienza esiste ed e' enorme, ma nessuno dei due lo tocca: il minimo per rispondere a
una di queste domande sta fra 555 e 3.021 caratteri.

Il caso peggiore e' istruttivo: su R005, R008 e R017 — una sola fonte richiesta, fra 555
e 654 caratteri — il pacchetto ne consegna comunque 99.723, cioe' da 152 a 180 volte il
necessario. Piu' la domanda e' semplice, peggiore e' il rapporto.

## Il pacchetto sotto pressione di budget

`required_sources` resta 52 a ogni valore di `--text-budget`: la promessa del contratto
(«required_sources never ranked out») regge. La ripartizione del testo consegnato, pero',
va nella direzione opposta a quella utile:

| `--text-budget` | Regole adottate | Evidenza di progetto | Quota evidenza |
|---:|---:|---:|---:|
| 200.000 | 119.095 | 18.065 | 13,2% |
| 100.000 | 92.755 | 6.968 | 7,0% |
| 50.000 | 49.126 | **870** | 1,7% |
| 20.000 | 19.559 | **422** | 2,1% |
| 10.000 | 7.496 | 2.484 | 24,9% |
| 5.000 | 0 | 4.946 | 100% |

Stringere il budget non compra fonti piu' pertinenti: ne compra **meno**. A 50.000
caratteri il pacchetto consegna 870 caratteri di evidenza — meno di un documento — e ne
spende 49.126 in regole. Solo sotto i 5.000, quando le regole non entrano affatto,
l'evidenza resta sola.

## Cosa succede quando il corpus cresce

E' la domanda che decide se il grafo serva su un progetto reale: con 35 documenti leggere
tutto e' praticabile, e un recall del 72% non e' interessante. Corpora sintetici piu'
grandi, ottenuti replicando i sottoalberi di prodotto, stessa domanda, stesso
`--product gamma`:

| Documenti | `required_sources` | Evidenza consegnata | Precisione (3 fonti utili) |
|---:|---:|---:|---:|
| 35 | 52 | 6.968 | 5,8% |
| 98 | 115 | 6.968 | 2,6% |
| 224 | 241 | 6.968 | **1,2%** |

`required_sources` **cresce linearmente con il corpus**: il rapporto resta circa 1,08
volte il numero di documenti a ogni scala. Il pacchetto non classifica e non restringe,
**enumera**. L'evidenza consegnata resta invece fissa a 6.968 caratteri, perche' e' il
residuo del budget dopo le regole: a 224 documenti significa **29 caratteri per ciascuna
delle 241 fonti che ti dice di leggere**.

Questo chiude la riserva lasciata aperta sopra. Su un corpus piu' grande il pacchetto non
diventa un recuperatore al 72%: diventa l'istruzione di leggere l'intero repository, con
precisione che scende come 1/N. Il caso in cui un grafo servirebbe di piu' e' quello in
cui questo pacchetto serve di meno.

## Conclusione sul retrieval

Con il grafo documentale interrogato direttamente, il tetto raggiungibile e' **72%** dei
gruppi richiesti, e solo pagando 99.723 caratteri consegnati. Con la ricerca, il tetto
realistico e' **48%**, e con la domanda posta come l'utente la pone e' **0%**.

Gli agenti che leggono i file direttamente raggiungono **100%** in ogni prova completata.

Su questo corpus e con questa configurazione, il grafo **non migliora il retrieval**:
recupera meno di quanto l'agente gia' ottiene, e il canale che mancherebbe — il codice —
richiede un provider che il protocollo vieta di installare.

## Cosa non e' misurato qui

La qualita' delle risposte, che resta di revisione umana indipendente. Il beneficio del
grafo su corpora molto piu' grandi di 35 documenti, dove leggere tutto non e' praticabile
e un recall del 72% potrebbe battere una lettura parziale. La condizione in cui il
provider di codice e' configurato. E il comportamento di un agente a cui il motore venga
esplicitamente indicato: quella e' la condizione C, eseguita separatamente con
[run_graph.py](run_graph.py).
