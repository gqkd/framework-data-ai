# Le stesse domande con Opus: il modello conta piu' della versione del framework

Quattro prove reali, 15/09, con Opus al posto di gpt-5.6-sol. Stesse domande, stesso
corpus congelato, stessi due runtime, stesso lettore strumentato, stesso prompt.
Numeri in [OPUS-ARENA-RESULTS.json](OPUS-ARENA-RESULTS.json).

## Come e' stato eseguito, e cosa questo indebolisce

La CLI Claude annidata non si autentica in questo ambiente (`loggedIn: false`), quindi
[run_claude.py](run_claude.py) non e' stato eseguito. Le prove girano invece come
subagenti in-process: contesto fresco, nessuna eredita' di conversazione, fonti e runtime
resi non scrivibili a livello di filesystem, una copia isolata per prova.

**Isolamento piu' debole delle catture codex**, e va dichiarato: non e' stato possibile
imporre un confine sul filesystem ne' verificare tutte le chiamate ai tool. La verifica
disponibile e' che **ogni fonte citata nelle quattro risposte compare nel log del lettore
strumentato**, riga per riga. E' evidenza, non prova. Questi risultati non si aggregano
con la serie codex.

**Cautela di misura**: i caratteri sono quelli che il lettore ha *emesso*. Una lettura
integrale puo' essere troncata dalla pipeline di output dell'agente prima che il modello
la veda — e' successo in due prove, dichiarate dagli agenti stessi. Quelle letture sono
contate a parte e non entrano nel totale confermato.

## Volume di lettura

| Prova | Progetto | Framework | Emessi | Non confermati | **Confermati** | Gruppi |
|---|---:|---:|---:|---:|---:|---:|
| R022-A | 16.926 | 43.678 | 60.604 | 36.061 | **24.543** | 3/3 |
| R022-B | 15.586 | 65.018 | 80.604 | 38.074 | **42.530** | 3/3 |
| R016-A | 10.045 | 2.526 | 12.571 | 0 | **12.571** | 3/3 |
| R016-B | 10.045 | 2.203 | 12.248 | 0 | **12.248** | 3/3 |

## Il grafo migliora il retrieval? No, nemmeno con Opus

**Copertura 3/3 in tutte e quattro le prove, entrambi i bracci.** Come con GPT, la
baseline satura gia' la metrica e non resta margine osservabile.

**Zero invocazioni del motore**, terza famiglia di modelli con lo stesso esito. Il caso
piu' netto e' R022-B: ha letto `FRAMEWORK.md` righe 612-680, cioe' proprio la §12
«Optional operational memory», e nella sua stessa risposta dichiara «Non ho eseguito il
validator, `memory.py` ne' alcuno script del framework». Ha letto la documentazione del
meccanismo e ha scelto di non usarlo. La non-scoperta non dipende dal modello.

## Il grafo migliora il consumo di token? No

Differenza fra bracci, caratteri confermati:

| Domanda | B − A | di cui framework |
|---|---:|---:|
| R022 | **+17.987** | +19.327 |
| R016 | −323 | −323 |

Il runtime candidato costa di piu' o quanto la baseline, mai meno. Stessa direzione
osservata con GPT, dove R022 dava +61.442 caratteri di framework.

Sui token dichiarati dal runtime — 56.762 e 66.472 su R022, 50.718 e 48.868 su R016 — la
differenza fra bracci e' +17% su R022 e −3,6% su R016: segni opposti, come nella serie
codex. Il confronto diretto con i token di codex non e' pulito, perche' quei totali sono
dominati da input in cache; il volume di lettura resta la metrica comparabile.

## Il risultato che cambia una conclusione precedente

Opus legge **4,6-4,7 volte meno** di GPT per la stessa copertura: 24.543 contro 113.775
caratteri su R022-A, 12.571 contro 58.598 su R016-A. I due rapporti coincidono su
domande diverse.

La differenza non e' nelle fonti di progetto, che sono simili, ma nel framework. Su R016
GPT legge `FRAMEWORK.md` per intero — 36.061 caratteri, in ogni prova — mentre Opus legge
`--start 195 --end 235`, cioe' 2.526 caratteri: la sola tabella delle fasi. La quota
framework passa dall'89% al 20%.

E soprattutto: **tutte e quattro le prove Opus superano la rubrica**, incluso il braccio
baseline su R016. Nella serie codex il braccio A falliva quel caso, concludendo
«0 elementi/s» in grassetto e violando il `must_not` sull'assenza trattata come misura.

Quella era l'**unica** differenza di qualita' trovata fra le due versioni del framework in
dieci coppie. Con Opus sparisce da entrambi i lati. Non era un merito della versione
3.8.1: era una debolezza del modello, e va tolta dal conto dei benefici delle modifiche.

## Cosa resta non misurato

La qualita' delle risposte e' valutata dall'autore, non da revisione indipendente: lo
stato `pending-independent-review` resta su tutte. Due domande su ventiquattro, una
ripetizione ciascuna, non separano un effetto dalla varianza di sessione — che nella
serie codex e' circa il doppio. La condizione C, in cui il motore viene esplicitamente
indicato all'agente, non e' stata eseguita con Opus.
