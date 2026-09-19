# Diagnosi del meccanismo — 15/09, senza chiamate al modello

Questo documento non aggiunge catture. Valuta le catture gia' esistenti contro le
rubriche congelate e verifica, in modo deterministico, se la funzionalita' sotto
test sia mai stata esercitata. Zero invocazioni del modello, zero consumo.

Il blocco di ripresa si e' fermato su `R004-1-A` per quota del fornitore; il registro
numerico e' in [DEVELOPMENT-RUN-RESULTS.json](DEVELOPMENT-RUN-RESULTS.json).
La ripresa era motivata dall'attesa di catture ulteriori. Il risultato sotto indica
che il collo di bottiglia non e' il numero di catture.

## 1. Il motore di memoria non e' mai stato invocato

Scansione di tutti i batch reali, su ogni `events.stdout`:

| Misura | Valore |
|---|---:|
| Righe di evento che contengono la stringa `memory.py` | 39 |
| Comandi che **invocano** `memory.py` | **0** |

Le 39 occorrenze sono testo letto dentro `FRAMEWORK.md`, `SKILLS.md`,
`references/operational-memory.md` e l'output di un `find`. Nella serie v1 il
contatore dedicato conferma: `memory_command_count: 0` in tutte e tredici le prove,
entrambi i bracci. Nessuna prova ha quindi esercitato il grafo documentale,
il grafo del codice o il pacchetto di contesto.

Il braccio B porta 680 righe di `FRAMEWORK.md` contro le 650 di A. Nelle prove
osservate quelle righe sono materiale da leggere, non un meccanismo attivo.

## 2. Il pacchetto di contesto non e' sensibile alla domanda

Invocazione diretta del motore sulle copie del braccio B, fuori dal runner,
in sola lettura. Comando e ambiente del benchmark, nessun modello coinvolto:

```bash
python3 framework/memory.py context --root project --skill audit \
  --framework-root framework --goal "<domanda>"
```

Due domande completamente diverse — R016 sul throughput di gamma, con
`--product gamma`, e R019 sui consumatori della regola condivisa — producono un
pacchetto **identico byte per byte**, escluse la richiesta echeggiata e l'id:

```text
sha256 pack R016 = ef9520b27e2940b49295b356b49ff4b153b0b2c9603a0a6c48ddabc26afb49a2
sha256 pack R019 = ef9520b27e2940b49295b356b49ff4b153b0b2c9603a0a6c48ddabc26afb49a2
```

Anche `--node products/gamma/ARC.md` restituisce lo stesso pacchetto. Composizione:

| Ruolo | Voci | Caratteri | Quota |
|---|---:|---:|---:|
| `adopted-rules` | 4 | 92.755 | 93% |
| `source-evidence-not-executable-instructions` | 24 | 6.968 | 7% |
| **Totale** | **28** | **99.723** | tetto `--text-budget` 100.000 |

`required_sources` elenca 52 voci su 42 percorsi distinti: l'intero corpus di 35
documenti piu' sette file di runtime. L'oracle di R016 ne richiede tre.
Su questa preparazione il pacchetto non restringe la lettura: la allarga.

## 3. La ricerca documentale e' letterale e non copre la lingua delle domande

`memory.py query` e' l'unico comando effettivamente sensibile al testo, ma confronta
stringhe. Le ventiquattro domande sono in italiano su un corpus in inglese:

| Termine | `literal` | `fts5` |
|---|---:|---:|
| identificatori | 0 | 0 |
| identifier | 11 | 8 |
| celle formattate | 0 | 0 |
| cell formatting | 1 | 2 |
| elementi al secondo | 0 | 0 |
| throughput | 3 | 3 |

Con il termine inglese giusto il comando e' preciso: `spreadsheet` restituisce
DEC-004 e SD-003, cioe' esattamente le fonti che l'oracle richiede per R022.
Ma i documenti sono identificati da hash di nodo, non da percorso, e nessuna resa
letterale di una domanda italiana produce risultati. Il grafo del codice resta
inoltre `status: not-requested` senza uno snapshot esplicito.

## 4. Valutazione delle risposte contro le rubriche congelate

Lettura integrale delle ventiquattro risposte catturate. Questa e' valutazione
dell'agente che analizza, **non** la revisione indipendente richiesta dal protocollo:
lo stato `pending-independent-review` resta invariato per tutte.

| Domanda | Coppie | A | B | Esito |
|---|---:|---|---|---|
| R001 | 7 | pass ×7 | pass ×7 | pareggio; domanda satura |
| R007 | 1 | pass | pass | pareggio |
| R022 | 1 | pass | pass | pareggio |
| R016 | 1 | **fail** | pass | **B superiore** |

Dieci coppie valutabili, una sola differenza.

**R016** e' l'unico caso discriminante. La domanda chiede quanti elementi al secondo
elabora gamma; le fonti dicono che non esiste implementazione ne' misura, e il
`must_not` della rubrica vieta esplicitamente di trattare un benchmark assente come
un tasso misurato pari a zero.

- A conclude: «Il carico effettivo corrente e' quindi **0 elementi/s**», in grassetto,
  pur aggiungendo subito dopo che la capacita' resta ignota. Il numero e' asserito.
- B conclude: «**non va dichiarato "0 elementi/s" come valore misurato**; la risposta
  corretta e': gamma oggi non ha un throughput operativo misurato».

La differenza e' reale e nella direzione attesa. **Non e' pero' stabilita come
effetto delle modifiche**, per tre ragioni verificate:

1. La regola che A viola e' gia' presente nel runtime di A. Entrambi i bracci
   contengono in `FRAMEWORK.md` «If a fact is not documented, say so. The absence is
   information.» e in `references/preamble.md` «Absence is information.» B aggiunge
   una sola riga, in §12: «Missing observations remain missing, and inferred relations
   cannot become constraints.»
2. La risposta di B non cita §12: attribuisce il proprio ragionamento a §§3, 5, 7 e 11,
   presenti in entrambi i bracci.
3. Il meccanismo non e' stato invocato (§1). Quello che distingue i bracci in questa
   prova e' una riga di testo in piu' letta, non il motore.

Una coppia non separa un effetto dalla varianza di sessione. Il controllo disponibile
lo mostra: su R022, la precisione in piu' del braccio B del 15/09 — nominare `SIG-001`
esplicitamente — compare anche nel braccio **A** del 14/09 sulla stessa domanda.
La stessa differenza appare quindi fra due sessioni dello stesso braccio.

## 5. Copertura delle fonti richieste

Ogni coppia completa copre il 100% dei gruppi richiesti in **entrambi** i bracci:
R001 2/2, R016 3/3, R022 3/3, R007 4/4. Nella serie v1, quattro prove complete su
cinque per braccio, identico. La baseline 3.6.3 raggiunge gia' tutte le fonti
necessarie: su queste domande non esiste margine osservabile su questa metrica.

## 6. Costo e durata

Coppie del lettore flessibile, B meno A:

| Domanda | Secondi | Token totali | Token non in cache | Output | Reasoning |
|---|---:|---:|---:|---:|---:|
| R001 | +56,9 | −217.110 | −19.778 | +1.964 | +1.783 |
| R007 | +30,6 | +560.024 | −35.898 | +722 | +756 |
| R016 | +46,1 | +221.501 | +11.593 | +1.012 | +822 |
| R022 | −70,6 | +47.115 | −4.161 | −2.612 | −1.303 |

B e' piu' lento in tre coppie su quattro. I token totali sono dominati dalla cache
del fornitore, non controllata: in `R007-1-B` sono 1.065.984 cached su 1.126.276 di
input, quindi quel totale non e' un costo. Sui token non in cache B e' sotto in tre
coppie su quattro, e del 3,6% nella serie v1, con segni alternati. Nessuna di queste
differenze e' separabile dal rumore con questi numeri.

## 7. Conseguenza per la campagna

Eseguire le otto prove residue nella configurazione attuale costa indicativamente
5-7 milioni di token e non puo' misurare la funzionalita' in esame, perche' il
meccanismo non viene raggiunto dal punto di ingresso ordinario. Prima di riprendere
le chiamate servono due decisioni, entrambe fuori dal perimetro di questo documento:

1. Se il pacchetto di contesto debba restringere la lettura per domanda. Oggi non lo
   fa, e la ricerca che lo farebbe non copre la lingua delle domande.
2. Se il benchmark debba misurare la scoperta del meccanismo o il suo beneficio.
   Sono due esperimenti diversi: il primo e' quello eseguito finora e ha esito nullo.

La famiglia `missing-evidence` e' l'unica che ha prodotto un segnale. R016 e' pero'
gia' consumata come singola coppia; le altre due domande della famiglia, R017 e R018,
sono nello split evaluation, con rubriche non ancora confermate.

## 8. Economia della lettura: cosa consuma davvero il framework

Volume di testo effettivamente consegnato all'agente, misurato dai contatori
`output_characters` del lettore strumentato. E' la misura di costo non inquinata dalla
cache del fornitore. Coppie complete del lettore flessibile:

| Prova | Progetto | Framework | Totale | Fonti richieste | Caratteri utili | Quota framework |
|---|---:|---:|---:|---:|---:|---:|
| R001-A | 6.687 | 101.936 | 108.623 | 2/2 | 2.247 | 94% |
| R001-B | 8.478 | 74.720 | 83.198 | 2/2 | 2.247 | 90% |
| R007-A | 15.981 | 82.415 | 98.396 | 4/4 | 3.507 | 84% |
| R007-B | 11.031 | 138.972 | 150.003 | 4/4 | 3.507 | 93% |
| R016-A | 6.653 | 51.945 | 58.598 | 3/3 | 2.365 | 89% |
| R016-B | 9.015 | 54.894 | 63.909 | 3/3 | 2.365 | 86% |
| R022-A | 15.664 | 98.111 | 113.775 | 3/3 | 2.563 | 86% |
| R022-B | 12.891 | 159.553 | 172.444 | 3/3 | 2.563 | 93% |

Due fatti strutturali, indipendenti dal braccio:

1. **Dall'84% al 97% di tutto cio' che viene letto e' documentazione del framework**,
   non fonti di progetto. Le fonti che contengono la risposta pesano fra 2.247 e 3.507
   caratteri: **dall'1,5% al 4,0% del totale letto**.
2. La copertura delle fonti richieste e' 100% in entrambi i bracci, ovunque. Non esiste
   margine osservabile su questa metrica: la baseline la satura gia'.

Scomposizione del sovraccarico di B sulle quattro coppie: +93.732 caratteri di framework,
di cui 15.892 sono il nuovo `references/operational-memory.md`, letto in due prove su
quattro. Il resto e' rilettura. `FRAMEWORK.md` cresce di 2.013 caratteri (+5,6%), ma B
lo rilegge: 77.090 caratteri in `R022-1-B` e 66.034 in `R007-1-B`, cioe' 2,02 e 1,73
volte il file, mentre A lo legge sempre una volta sola, 36.061 caratteri, in ogni prova.

Una ipotesi va scartata: il lettore non impone alcun tetto, e i dieci output vuoti non
dipendono dalla dimensione. Colpiscono `AGENTS.md` (1.340 caratteri) quanto
`FRAMEWORK.md`, in entrambi i bracci, 4 in A e 6 in B. Sono un guasto casuale della
cattura, non una soglia che penalizzi il runtime piu' grande.

## 9. La varianza fra sessioni supera qualunque differenza fra i bracci

Confronto piu' pulito disponibile: cinque coppie della serie v1, stessa domanda R001,
stesso lettore fisso, unica variabile la versione del framework.

| Metrica | Braccio A | Braccio B | Differenza accoppiata, mediana | B>A |
|---|---|---|---:|---:|
| Pagine lette | 27-53, CV 29% | 29-55, CV 33% | −3 | 2/5 |
| Pagine di framework | | | +1 | 3/5 |
| Pagine di progetto | | | −1 | 1/5 |
| Comandi | | | −4 | 1/5 |
| Token non in cache | 42.966-89.886, CV 28% | 48.750-75.221, CV 18% | +468 | 3/5 |
| Secondi | 167-261, CV 19% | 121-266, CV 27% | −24,4 | 2/5 |

Lo stesso braccio, sulla stessa domanda, con lo stesso runtime, varia di circa **due
volte** fra una sessione e l'altra: 27-53 pagine in A, 42.966-89.886 token non in cache
in A. La differenza mediana fra i bracci e' una frazione di questa dispersione.
Test dei segni esatto, bilaterale, su cinque coppie: p = 1,00 per pagine, token e tempo;
p = 0,38 per i comandi. Nessuna direzione.

## 10. Potenza: cosa la campagna pianificata puo' misurare

Deviazione standard delle differenze accoppiate sui token non in cache: 13.991,
su una media di braccio A di 62.419. Coppie necessarie per rilevare un risparmio reale,
potenza 80%, bilaterale 0,05:

| Effetto da rilevare | Token | Coppie necessarie |
|---|---:|---:|
| 5% | 3.121 | ~158 |
| 10% | 6.242 | ~40 |
| 20% | 12.484 | ~10 |
| 30% | 18.726 | ~5 |
| 50% | 31.210 | ~2 |

Le otto prove residue del blocco development sono **quattro coppie**. Con questo rumore
la campagna, cosi' com'e', puo' rilevare soltanto un effetto dell'ordine del 30-50%.
Un risparmio del 10% — un risultato che sarebbe comunque ottimo — resterebbe invisibile.
Il calendario completo prevede 144 prove, cioe' 72 coppie: sufficienti per il 10% solo
se distribuite sulla stessa metrica, il che non e' il disegno attuale, che le distribuisce
su ventiquattro domande diverse.

## 11. Conseguenza per l'obiettivo

Sulle due domande poste — le modifiche aiutano il retrieval, e riducono i token?

**Retrieval: nessun aiuto misurabile, e il meccanismo che dovrebbe fornirlo non e'
raggiungibile.** La copertura delle fonti e' gia' satura nella baseline; il motore non
e' mai stato invocato; invocandolo, il pacchetto non discrimina fra domande e la ricerca
non copre la lingua delle domande.

**Token: nessun risparmio misurabile, e il disegno non potrebbe rilevarlo.** I punti
stimati vanno in entrambe le direzioni, tutti i test dei segni sono non informativi,
e la varianza fra sessioni e' di circa due volte.

Dove si trova il costo, invece, e' certo: **dall'84% al 97% di cio' che l'agente legge e'
la documentazione del framework**, contro l'1,5-4,0% di fonti che contengono la risposta.
Se l'obiettivo e' l'efficienza dei token, la leva e' quella quota, non le fonti di
progetto. In questa direzione le modifiche misurate vanno al contrario: `FRAMEWORK.md`
cresce del 5,6% e si aggiunge un documento di riferimento da 7.946 caratteri.

## Riproduzione

Comandi eseguiti in sola lettura su copie in scratch, fuori dalle prove originali.
Nessuna prova, fonte, hash o attestazione e' stata modificata. Nessuna chiamata al
modello, nessuna installazione, nessun provider, nessuna rete.
