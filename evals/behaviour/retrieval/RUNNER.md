# Runner A/B — protocollo strumentato v1

Stato: implementato, collaudato offline e sottoposto al pilota reale R001.
Esiti e limiti della qualificazione sono nel [resoconto del pilota](PILOT-R001.md).
Estende il [protocollo del dataset](PROTOCOL.md) senza cambiare corpus, domande,
oracle, commit dei runtime o soglie proposte. Non è un rilascio del runtime.

## Cosa misura e cosa no

| Livello | Evidenza | Risultato |
|---|---|---|
| Integrità | Rigenerazione sintetica, confronto dei file non-Git con la preparazione | Input riproducibili, non semplice fiducia nel manifest |
| Isolamento | Probe con il sandbox Linux/WSL della CLI | Letture consentite, scritture alle fonti e accessi esterni negati |
| Retrieval osservato | Pagine nei risultati dei comandi, confrontate con le fonti | Copertura delle righe/sezioni attese, non giudizio semantico |
| Qualità | Risposta, rubriche e traccia per revisore indipendente | Sempre pending-review, mai successo assegnato dal runner |
| Consumo | Usage terminale dello stream CLI | Input + output; cache e reasoning separati, non sommati due volte |

Lo stream CLI non è una cattura attestata del payload inviato al modello.
Le pagine piccole e i delimitatori permettono di verificare il contenuto presente
nei risultati dei comandi; non provano che ogni byte sia rimasto nel contesto
del modello dopo trasformazioni o compattazioni. Il report espone questo limite
come model_delivery_attestation: unavailable.
complete_delivery significa **copertura completa osservata nel log**, non
comprensione provata o consegna al modello attestata.

Le [ripetizioni R001 del 14/09](REPETITIONS-R001.md) hanno osservato comandi
reader conclusi con exit 0 e aggregated_output vuoto. Non ricevono credito,
ma non incrementano unverified_frames: non esiste un frame da verificare.
Quel contatore a zero non attesta quindi che ogni lettura abbia testo nel log.
Le durate e la usage terminale restano osservabili, mentre la copertura può
risultare incompleta. L'origine del vuoto e l'effettiva consegna al modello
non sono determinate. Il runner non è stato cambiato durante queste prove.

Le letture normali, le ricerche e i context pack restano disponibili.
Solo le pagine strumentate ricevono credito meccanico come fonti originali.
È un confronto fra **workflow strumentati**, non fra sessioni IDE inalterate.
L'overhead del lettore è incluso nei token di entrambi i bracci.
Il pilota R001 controlla forma e troncamento degli eventi reali di quella coppia;
non qualifica altri client, strumenti o forme di evento. Una diversa forma degli
strumenti richiede un adapter esplicito.

## Componenti

~~~text
prepare.py → basi A/B + evaluator riservato
                       │
run.py ── verifica tramite rigenerazione e oggetti Git locali
       ├─ domanda, ripetizione, A → progetto/runtime freschi → CLI isolata
       └─ domanda, ripetizione, B → progetto/runtime freschi → CLI isolata
                                      │
                 read_source.py ── fonti scelte dall'agente
                                      │
                        eventi + risposta + inventari
                                      ↓
                       metrics.py → copertura + token
                                      ↓
                            revisione indipendente
~~~

- run.py riusa inventari, cattura dei processi e timeout di ../memory/qualify.py;
  non ne riusa context pack, fixture o rubriche.
- read_source.py è l'unico file del valutatore esposto all'agente. Non conosce
  oracle, domande successive o fonti obbligatorie. Legge project o framework,
  senza link, .git o percorsi esterni; massimo 40 righe/4000 byte per pagina,
  2 MB per file. Una riga troppo lunga produce un errore, non una falsa lettura completa.
- metrics.py verifica testo, hash, scope e intervalli; ricompone pagine e sezioni;
  applica i gruppi AND-di-OR dell'oracle. Non accredita un hash senza testo, una
  citazione auto-dichiarata, un comando riuscito o un frame incompleto.
- Il parser tratta item.completed / command_execution riusciti. Eventi intermedi
  e duplicati non raddoppiano letture o conteggi. Altri strumenti restano nel log
  senza diventare ricevute di lettura.

Gli interni Git delle prove sono rigenerati dalla narrativa controllata, non
copiati dalle basi dell'operatore. SHA e contenuto rimangono quelli del dataset.
L'inventario prima/dopo comprende anche interni Git, permessi e lettore.

## Uso sicuro

Usare Linux/WSL e l'ambiente Python vincolato del framework. Servono gli stessi
oggetti Git locali del preparatore; niente fetch. Ogni destinazione deve essere
nuova, assoluta e separata da repository e basi. Nessun esperimento viene sovrascritto.

### 1. Preparazione senza modello e senza CLI

~~~bash
python -B evals/behaviour/retrieval/run.py \
  --from-prepared /tmp/retrieval-synthetic-v1 \
  --output /tmp/retrieval-plan-01 \
  --question R001
~~~

Produce una coppia A/B. --question è ripetibile; --repetitions accetta 1–3.
L'ordine viene dal calendario congelato, incluse le coppie randomizzate.
Il limite predefinito è sei prove: non si lanciano accidentalmente le 144 previste.
Per superarlo serve --max-trials esplicito; una coppia non viene tagliata.
--pair-order AB oppure BA permette un controbilanciamento esplicito: cambia
solo l'ordine entro ogni coppia, conserva l'ordine fra coppie e non riscrive il
calendario congelato. run.json registra l'override. Il default scheduled resta invariato.

### 2. Preflight senza modello

~~~bash
python -B evals/behaviour/retrieval/run.py \
  --from-prepared /tmp/retrieval-synthetic-v1 \
  --output /tmp/retrieval-preflight-01 \
  --question R001 --preflight-only \
  --codex /percorso/assoluto/codex \
  --sandbox-helper /percorso/assoluto/del/binario/nativo/codex
~~~

--sandbox-helper serve se il binario nativo è fuori dai percorsi già leggibili.
Si autorizza quel file, non la home o l'intera installazione.
Il probe verifica lettore, dipendenze Python e avvio della CLI dei due runtime.
Prima del probe, un controllo delle feature richiede code_mode_host, shell_tool
e unified_exec attivi e le integrazioni escluse disattivate. Preflight e chiamata
al modello usano gli stessi override espliciti. Il comando features list non
offre --ignore-user-config: il controllo attesta solo le feature nominate e
sovrascritte, non l'assenza di ogni configurazione personale.
code_mode_host è necessario agli strumenti nella CLI 0.150.1: disabilitarlo
rompe le letture anche quando il sandbox del sistema operativo funziona.
Rete dei comandi negata, fonti/runtime non scrivibili, canary del valutatore e
AGENTS dell'altra prova non leggibili. Solo scratch è scrivibile.
Un controllo inconcludente ferma tutto, senza fallback a permessi più deboli.

### 3. Revisione prima delle chiamate

oracle-review.template.json è intenzionalmente non approvato. Un revisore umano
diverso dall'autore del dataset verifica le rubriche dei quesiti selezionati.
La preparazione genera evaluator/review/README.md e una scheda per quesito, con
domanda, criteri originali, gruppi di fonti, righe obbligatorie e fonti integrali
numerate. Queste schede restano fuori dai percorsi leggibili dall'agente.

Compilare una copia del template: status: independently-reviewed, reviewer,
reviewed_on (data ISO), independent_of_dataset_author: true,
reviewed_questions con i soli ID effettivamente verificati, oracle_sha256 e
prepared_manifest_sha256 invariati. Il secondo hash vincola anche domande,
corpus e versioni della preparazione: una rubrica non viene riutilizzata su input
diversi solo perché il file oracle è rimasto uguale.

Il runner richiede copertura di tutti i quesiti selezionati. Una revisione di
R001 abilita solo quel quesito, su entrambi i bracci e per le ripetizioni richieste;
non approva gli altri 23. Non occorre revisionare tutta la campagna per un pilota
di una coppia. Per la campagna completa vanno revisionati tutti i quesiti eseguiti.
I vecchi template privi di scope/hash della preparazione devono essere rigenerati.

Non modificare le schede snapshot o gli altri input sotto evaluator; annotare
l'esito nella copia separata dell'attestazione. Il runner controlla anche gli hash
degli input del valutatore prima di chiamare la CLI.
Il runner controlla byte e dichiarazione; non può attestare identità o indipendenza
della persona. Le revisioni simulate nei test NON approvano l'oracle reale.

### 4. Esecuzione esplicita, dopo la revisione

~~~bash
python -B evals/behaviour/retrieval/run.py \
  --from-prepared /tmp/retrieval-synthetic-v1 \
  --output /tmp/retrieval-pilot-01 \
  --question R001 --execute \
  --model MODELLO_SCELTO --reasoning low \
  --oracle-review /percorso/revisione-umana.json \
  --codex /percorso/assoluto/codex \
  --sandbox-helper /percorso/assoluto/del/binario/nativo/codex
~~~

Il modello non viene scelto automaticamente o ereditato da questa conversazione.
Il reasoning deve essere supportato dal modello scelto; nessun fallback.
La CLI attesa è 0.150.1. Cambiarla richiede riqualificazione e --expected-cli:
il solo override del numero non dimostra compatibilità.

Il timeout predefinito è 600 secondi per prova, modificabile con --timeout.
--no-timeout, incompatibile con --timeout, osserva la durata fino alla conclusione
senza una scadenza del runner per la prova LLM; run.json registra null.
I probe tecnici mantengono scadenze proprie e non sono misure del tempo dell'agente.
Restano possibili errori o interruzioni del client/fornitore; non diventano risposte valide.
**Non è un tetto token o monetario**: consumo e quote del fornitore non sono
controllati dal timeout. Nessun pagamento, reset quote o installazione automatica.
Si parte da una coppia development; i quesiti evaluation non vanno usati per tarare il runner.

## Configurazione e privacy

Sessione effimera nuova per prova, niente resume o parallelismo.
Configurazione utente e regole execpolicy ignorate, approvazioni negate.
Plugin, app, web, memorie, subagenti e integrazioni estranee sono disabilitati
con opzioni registrate.

Il caricamento automatico degli AGENTS è disattivato in entrambi i bracci.
Il prompt richiede di leggere quello sintetico con il lettore: l'ingresso rimane
AGENTS.md, ma la lettura è osservabile e non incorpora istruzioni personali.
Le directory delle skill globali/sistema vengono enumerate per disabilitarle,
senza leggerne i contenuti. I sette SKILL del framework rimangono leggibili nel
runtime assegnato, non come plugin installato.
Il pilota deve comunque controllare istruzioni predefinite/gestite della CLI:
il preflight attesta i confini dei comandi, non l'intero prompt interno del client.

I comandi ricevono un piccolo ambiente esplicito, senza credenziali, configurazione
Git personale o user-site Python. Il client usa l'autenticazione già disponibile:
non si copiano, stampano o modificano credenziali.
L'inferenza remota, se avviata, trasmette al fornitore prompt e contenuti sintetici
selezionati: **locale non significa inferenza offline**.
I log rimangono locali e non sono pubblicati o versionati automaticamente.

Nessuna nuova dipendenza Python, graph DB, embeddings, telemetria o valutatore LLM.
Si usano libreria standard e PyYAML già presenti, Git e CLI installata.
Il candidato usa le proprie dipendenze del framework. Non viene installato un
provider di code graph: la prova primaria non misura il guadagno di quel provider
o di un mapping aggiunto apposta.

## Report e interpretazione

Ogni prova conserva prompt, comando/configurazione, stdout JSONL e stderr,
risposta, preflight, inventari e result.json. run.json conserva hash, selezione,
modello richiesto, reasoning, CLI e invocazioni tentate.
L'identità effettiva del modello resta null: il parametro -m non la attesta.
pending-review significa solamente cattura completata.

Una usage terminale valida fornisce input_tokens e output_tokens.
cached_input_tokens è un sottoinsieme dell'input, reasoning_output_tokens dell'output.
Sottocontatori assenti restano null. Contatori negativi, non interi, incoerenti
o usage multiple diventano unknown. Una cattura parziale conserva consumi
osservati, ma entire_turn_capture resta false.
I subtotali includono tentativi falliti; consumi mancanti non diventano zero.
Niente percentuali di risparmio o costo per risposta corretta prima della revisione.
I token sono cumulativi sulle chiamate del turno, non token unici del corpus
o dimensione di un singolo contesto. Non sono una fattura: la cache è distinta
e non viene applicato alcun prezzo non verificato.

Il diagnostico stderr del router "code-mode host is disabled" rende la prova
unavailable anche se il modello conclude il turno. La usage rimane conservata:
una cattura completa non implica strumenti disponibili. Il controllo riconosce
questo errore osservato, non pretende di classificare ogni errore futuro.
La stessa frase citata nella risposta non basta a invalidare una prova.
Un retry deve usare una destinazione nuova; i tentativi precedenti e i loro
consumi non si cancellano né si sostituiscono nel resoconto.

Ancora da fare: revisione indipendente delle risposte; giudizio sulle osservazioni
Git, assenze e affermazioni extra;
aggregazione per quesito/famiglia, confronto a qualità controllata e campagna completa.
Il runner non implementa un giudice automatico a parole chiave.
Il 14/09 l'utente ha richiesto prove senza un tetto di consumo o durata:
nessun budget token viene introdotto. Prima di attribuire l'overhead al framework
va riesaminato l'effetto delle letture strumentate:
40 righe per chiamata e bootstrap completo possono dominare un quesito semplice.
Un eventuale adapter v2 deve essere distinto, applicato a entrambi i bracci e
riqualificato; non si cambiano prompt o limiti durante una coppia.

Riferimenti ufficiali consultati per le opzioni, non dipendenze aggiunte:
[esecuzione non interattiva](https://learn.chatgpt.com/docs/non-interactive-mode),
[permessi](https://learn.chatgpt.com/docs/permissions),
[configurazione](https://learn.chatgpt.com/docs/config-file/config-reference) e
[caricamento AGENTS](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
