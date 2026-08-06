# Skill per la gestione del framework

Cinque skill. Due sono costruite e funzionanti (`framework-capture`, `framework-audit`), tre
sono specificate abbastanza per essere implementate quando servono.

---

## 1 · Una precisazione necessaria sull'automazione

L'obiettivo — «non aggiornare a mano tutto», e sostituire i «controlli automatici da
aggiungere alla CI» — si raggiunge, ma non tutto con lo stesso strumento.

**Una skill non è un demone.** Gira quando gira Claude: non si attiva su un push, non
controlla niente di notte, non ha stato fra un'invocazione e l'altra. Se i controlli
vivessero solo nelle skill, verrebbero eseguiti quando ti ricordi di chiederlo, cioè
raramente e non nei momenti che contano.

| Natura del compito | Strumento | Quando gira |
|---|---|---|
| Deterministico: schema, ID, riferimenti, obsolescenza, indici | **Script Python** | in CI su ogni push, e a mano quando serve |
| Estrazione da formati: pptx, pdf, docx con provenienza | **Script Python** | quando ingesti |
| Richiede giudizio: classificare un'affermazione, propagare una cascata, scrivere un `CHG` | **Skill** | quando la invochi |
| Richiede la tua conoscenza: cosa è stato osservato, cosa è stato promesso | **Tu** | — |

**Le skill portano gli script.** `framework-audit` contiene `validate.py`: la skill lo esegue
in interattivo e interpreta i risultati, la CI esegue lo stesso file e blocca il merge. Una
sola implementazione, due punti di ingresso. Se la logica fosse duplicata nelle istruzioni
della skill divergerebbe dalla versione che gira in CI, cioè da quella che conta.

**Le skill stanno nel repository**, in `skills/`, versionate col codice. Sono le stesse per i
tre prodotti: `product.yaml` dice a quale si stanno applicando. È il meccanismo concreto della
gestione condivisa dei tre progetti — non serve una skill per prodotto.

---

## 2 · Perché cinque

Una skill viene selezionata in base alla sua descrizione, e una descrizione vaga si attiva in
modo inaffidabile: scatta quando non serve e non scatta quando servirebbe. Cinque confini
corrispondono ai cinque momenti in cui cambi davvero modalità di lavoro:

**imposto** · **registro** · **cambio** · **rilascio** · **verifico**

### Perché corpus e conversazione sono una skill sola

Sembrano due cose diverse: caricare duecento slide, e dire «abbiamo deciso Postgres». Ma
l'operazione sottostante è identica — *informazione esterna → classificata → instradata →
propagata* — e la logica che la governa (tassonomia, cascata, gestione dei conflitti) è la
stessa.

Se stessero in due skill quella logica sarebbe duplicata, e divergerebbe: dopo tre mesi il
corpus e le note conversazionali finirebbero in posti diversi, e non te ne accorgeresti finché
un agente non trova due risposte in conflitto. È la stessa ragione per cui `validate.py` è un
file unico.

Quindi: **una skill, due modalità di ingresso, un riferimento condiviso.**

```
framework-capture/
├── SKILL.md                    selezione della modalità + procedura conversazionale
├── references/
│   ├── routing-table.md        ⟵ il nucleo: tassonomia, cascata, conflitti
│   └── ingest-bulk.md          procedura per il corpus business
└── scripts/
    └── extract.py              pptx · pdf · docx → blocchi con provenienza
```

### Perché non una sesta skill per i tre prodotti

La gestione cross-prodotto non è un momento di lavoro separato: è un vincolo che attraversa
gli altri cinque. Vive dentro ciascuno — nella cascata di `capture` (una metrica di glossario
usata da due prodotti), nei controlli di `audit` (glossario unico, consumatori dei `DC`), nella
classificazione di `change` (un `DEC` con `scope: platform`). Una skill dedicata duplicherebbe
tutto questo.

---

## 3 · `framework-capture` — registrare *(costruita)*

La skill che userai più di tutte. È la risposta a «voglio aggiungere informazioni in modo
conversazionale e voglio che i file vengano cambiati coerentemente».

### Modalità A — corpus business

Presentazioni, PDF, analisi dei requisiti prodotti dal business prima che esistesse il
progetto tecnico.

Il punto di partenza che cambia tutto: **questi documenti non sono una specifica.** Sono la
registrazione di ciò che è stato promesso, prodotta da chi doveva vendere. La destinazione
principale è `COMMITMENTS.md`, non un documento di prodotto. Ma contengono anche cinque cose
di valore diverso — vocabolario di dominio, promesse numeriche, vincoli travestiti da claim,
descrizioni del processo attuale, concorrenti citati — e vanno separate perché finiscono in
cinque posti.

`extract.py` normalizza pptx, pdf, docx e testo in blocchi etichettati con documento e
posizione (slide N, pagina N). Due comportamenti che valgono più del resto:

- **Segnala e rasterizza le pagine povere di testo.** Su un deck commerciale la promessa
  architetturale è spesso *disegnata*: tre box con delle frecce e la scritta «piattaforma
  unica» non producono nessun testo estraibile e sono un vincolo di tenancy.
- **Riconosce i deck esportati in PDF** e avvisa che il testo estratto ha perso il layout,
  perché in un deck il layout porta significato.

Poi la classificazione passa per **`ING.md`**, non diretto negli artefatti: conserva la
provenienza, fa da coda di revisione interrompibile, e permette di respingere un'affermazione
conservando il fatto che il business l'ha detta — che è esattamente ciò che serve quando fra
otto mesi qualcuno chiede perché quella funzionalità non c'è.

**L'output di maggior valore sono le contraddizioni.** Tre documenti scritti da persone
diverse in otto mesi si contraddicono, e nessuno lo sa perché nessuno li ha letti tutti di
fila. Sul corpus di prova usato per testare l'estrattore è emersa immediatamente: il deck
promette «dati in tempo reale», l'analisi dei requisiti dice «aggiornamento ogni ora, batch
notturno esistente». Se le due versioni sono state dette a due clienti diversi non è un
problema tecnico ma un impegno da rinegoziare, e prima è meglio.

### Modalità B — conversazionale

**Non registra frase per frase.** Una conversazione è in gran parte ragionamento ad alta voce,
e archiviare ogni affermazione produce un registro di rumore in cui i fatti veri diventano
irreperibili — e siccome quel registro è la fonte da cui lavorerà un agente, il danno si
propaga.

Il modello è la **raccolta a fine sessione**:

> Da questa conversazione mi sembrano registrabili quattro cose:
> 1. *decisione* — Postgres come datastore → `DEC` nuovo + `ARC` + chiude `OD-005`
> 2. *definizione* — «cliente attivo» = login negli ultimi 30 giorni → `GLOSSARY`, **in
>    conflitto** con la formula già presente per prodotto-b
> 3. *richiesta* — export Excel chiesto dal cliente → `SIG` in `LOG`
> 4. *ragionamento* — valutare se separare il reporting → parcheggio
>
> Quali registro?

Eccezioni scritte subito: un **incidente** (il valore dipende dall'ora esatta) e un **impegno
fuori portata** appena emerso.

### Le tre idee che fanno funzionare la coerenza

**La classificazione va sulla forza epistemica, non sull'argomento.** «Il sistema processa 10M
di righe al giorno» può significare *lo abbiamo promesso*, *crediamo che servirà* o *l'abbiamo
misurato*: tre cose con la stessa forma testuale che vanno in tre posti diversi. Se non è
distinguibile dal contesto la skill chiede — è la domanda che paga di più.

**La cascata è obbligatoria e tabellata.** Un `DEC` con `scope: architecture` obbliga ad
aggiornare `ARC` nello stesso passaggio; una voce di glossario per un termine che è anche un
campo di un `DC` obbliga a bumpare quel contratto; un impegno fuori portata apre una riga in
`RSK` e una in `OPEN`. Scrivere in un file solo è facile: scrivere nei quattro giusti è il
motivo per cui la skill esiste.

**L'automaticità è inversamente proporzionale all'ampiezza della cascata.** Una destinazione
sola, append-only, nessuna ambiguità, nessun conflitto → applica direttamente. Cascata su più
file, immutabile coinvolto, conflitto rilevato, classificazione ambigua → proponi il diff e
attendi. La cascata è il punto in cui la fiducia di un agente supera la sua accuratezza:
chiedere costa dieci secondi, questo errore costa una decisione.

---

## 4 · `framework-init` — impostare

**Si attiva:** «imposta il framework», «nuovo prodotto», «ho del codice senza documentazione»,
«da dove comincio».

1. **Entry assessment.** Idea · idea già venduta · codice senza documentazione · prodotto in
   produzione. Non è una formalità: l'ingresso determina quali documenti hanno senso e quali
   sarebbero finzione.
2. **Scaffolding.** Albero delle cartelle, template pertinenti con il front-matter compilato.
   Non il corpo.
3. **Delega a `framework-capture`** l'ingestione del corpus business, quando l'ingresso è «già
   venduto». Non riimplementa l'estrazione: la richiama.
4. **Ricostruzione da codice**, quando l'ingresso è «codice esistente»: propone un `ARC` di
   partenza e — la parte utile — elenca le **decisioni già implicite nel codice** che non hanno
   un `DEC`. Un datastore scelto, un modello di tenancy: sono decisioni prese, solo non
   registrate.
5. **Semina `OPEN.md`** con le decisioni da prendere, ciascuna con il costo di ritorno.

**Frequenza:** tre volte in tutto. Ed è giusto così: una skill usata tre volte che ti fa
partire con la struttura corretta vale più di dieci esecuzioni di qualcosa di marginale.

---

## 5 · `framework-change` — cambiare

**Si attiva:** «devo aggiungere», «cosa faccio in questo ciclo», «apri una change».

Implementa il tratto del ciclo che era nell'ordine sbagliato: intake → triage → `ICG` →
reshaping → `CHG` → `IMP`.

1. **Triage e impact assessment.** Legge `PBR`, `ARC`, i `DC`, `EVP`, `RSK` e **propone** la
   classificazione `ICG`. Un `ICG` deciso automaticamente è un gate che non esiste.
2. **Instrada.** Se serve reshaping, elenca quali artefatti aggiornare **prima** di scrivere il
   piano. Se il routing è «ipotesi invalidata» si ferma: il rientro è in F3 o F2, non in un
   `CHG`.
3. **Scrive il `CHG`** con i tre campi obbligatori. Il valore aggiunto è **Cosa NON deve
   cambiare**: la skill lo compila meglio di te, perché può leggere `ARC` e i `DC` e trovare i
   contratti che il cambiamento rischia di rompere senza che nessuno l'abbia notato.
4. **Aggiorna `IMP`** e la sezione `§escluse`.
5. **Verifica** con `validate.py` prima di portare il `CHG` a `verified`.

**Confine con `capture`:** `capture` registra il segnale in `LOG`; `change` lo trasforma in
mandato. Un segnale registrato non è autorizzato a essere implementato — è la separazione che
impedisce a un prodotto di diventare la somma delle ultime cose chieste.

---

## 6 · `framework-release` — rilasciare

**Si attiva:** «rilascio», «prepara la release», «posso rilasciare?».

1. **Verifica il gate `RG`:** esiste un `EVR` per il candidato, cita l'`EVP` nella versione
   congelata, tutte le metriche e le slice sono sopra soglia. Se no: **rework**, e lo dice con
   questa parola, perché non è un rollback — non è ancora in produzione.
2. **Genera `RLM.yaml`** da git, build e configurazione: commit, digest, versioni di modello e
   prompt, dataset, `DC` toccati, `CHG` inclusi, target di rollback. Compilarlo a mano
   significa sbagliarlo.
3. **Genera `REL.md`** dai `CHG`, tradotti in effetti. Dieci righe.
4. **Aggiorna** `product.yaml` e apre un `SIG` type `metric` per le prime 48 ore.
5. **Non esegue il deploy.** Prepara l'evidenza; il comando lo dai tu.

È la skill con la quota di giudizio più bassa, quindi quella che risparmia più tempo a parità
di rischio.

---

## 7 · `framework-audit` — verificare *(costruita)*

`skills/framework-audit/` con `scripts/validate.py`, verificato su un repository di prova.

Controlla: front-matter e schema per tipo · coerenza fra `lifecycle` e tipo · `status`
nell'enumerazione del tipo · unicità degli ID · riferimenti pendenti · cicli nella catena di
supersedenza · sezioni obbligatorie (`Cosa NON deve cambiare` di un `CHG`, `§delta` di un `WF`,
le tre di `RSK`, le tre di `ING`) · obsolescenza dei viventi · `CHG` che dichiarano un impatto
senza l'artefatto che ne deriva · rollback non definito o non testato · decisioni chiuse ancora
elencate come aperte.

**Cross-prodotto:** glossario unico · consumatori dei `DC` che corrispondono a prodotti
esistenti · prodotti senza `PBR`.

**Genera:** `decisions/INDEX.md` e `TRACEABILITY.md`.

Una regola di igiene che vale la pena ripetere: **non aggiornare `last_review` senza aver letto
il documento.** È l'azione più veloce per far tornare verde il validatore e l'unica che rende
inutile l'intero framework.

### Da costruire: `--emit-manifest`, per le sezioni `GENERATO` di `product.yaml`

Oggi quelle sezioni sono marcate «generato» e le scrive una persona. Una sezione che si
dichiara generata e non lo è, è **peggio di una scritta a mano**: nessuno la rilegge, perché
tutti presumono che qualcosa la tenga vera.

Prima di scrivere il generatore, separa i campi del manifest in due gruppi. La riga di
confine è: *serve giudizio per compilarlo?*

| Derivabile — lo fa lo script | Da cosa |
|---|---|
| `artifacts.living[].last_review`, `.stale` | la stessa scansione che fa già il validatore |
| `artifacts.immutable_count`, `.append_only` | idem |
| `open_decisions` | i titoli `### OD-NNN` di `OPEN.md §1` |
| `open_risks` | `RSK.md §stato` |
| `active_changes` | i `CHG` con `status: approved` |
| `release.*` | l'ultimo `REL`/`RLM`, e `rollback_target` dal penultimo |

| Non derivabile — resta conversazionale | Perché |
|---|---|
| `stage.block`, `.phase`, `.next_gate`, `.mor_completed` | un gate lo passa una persona; nessun file lo registra prima del `DEC` |
| `one_liner`, `name` | è una decisione di posizionamento |
| `platform.shares` | è `OD-002`, cioè una decisione aperta |
| `entry_points`, `roles` | convenzioni, non fatti osservabili |

Poi: **il primo gruppo lo genera `validate.py --emit-manifest`**, accanto a `--emit-index`,
perché deriva dalla stessa scansione ed è lo stesso tipo di oggetto — un indice. Il secondo
gruppo lo mantiene `framework-capture` in modalità conversazionale: «abbiamo passato G3» è
un'affermazione con una destinazione, e `routing-table.md` è già il posto dove si decide
quale.

Non serve una skill nuova per questo, e la ragione è la stessa di
[§2 · Perché non una sesta skill per i tre prodotti](#perché-non-una-sesta-skill-per-i-tre-prodotti):
una skill che «gestisce il manifest» duplicherebbe la scansione di `audit` e la tassonomia di
`capture` per tenere insieme un file che è solo la proiezione di entrambe.

Tre vincoli sul generatore, che sono il motivo per cui va scritto e non improvvisato:

1. **Rigenerare non deve poter cancellare il secondo gruppo.** Riscrive i campi che possiede,
   lascia intatti gli altri. Un generatore che riscrive il file intero perde `stage` alla
   prima esecuzione, e nessuno se ne accorge finché non serve.
2. **Deve essere idempotente e verificabile in CI.** `--emit-manifest --check` esce diverso da
   zero se il file su disco diverge da ciò che verrebbe generato: è l'unico modo per accorgersi
   che qualcuno ha scritto a mano in un campo generato.
3. **Finché non esiste, i campi restano marcati per quello che sono.** Il commento in fondo a
   `templates/product.yaml` dice che oggi li compili tu. Quel commento sparisce insieme al
   problema, non prima.

**Quando costruirlo:** quando esistono abbastanza artefatti perché rileggerli a mano costi più
di scrivere lo script — realisticamente al primo `CHG`, non prima. Con tre `PBR` e zero `CHG`
il manifest si aggiorna in trenta secondi e il generatore è la fabbrica costruita prima del
prodotto.

---

## 8 · Cosa non automatizzare

**Non far generare a una skill il contenuto di `PRB`, `HYP`, `EVD`, `DFB`.**

Un agente produce un problem statement plausibile, un'ipotesi ben formulata e un evidence
brief ordinato senza aver parlato con nessuno e senza aver interrogato un dato. Il risultato
passa qualsiasi validatore e non contiene informazione. È esattamente il fallimento che il
framework esiste per prevenire — documentazione che *sembra* vera — e ha una proprietà
sgradevole: è indistinguibile dalla versione buona a un'ispezione rapida, quindi non te ne
accorgi finché una decisione presa su quella base non si rivela sbagliata.

Il rischio è più alto proprio nell'ingestione, dove la tentazione è forte: il corpus business
contiene affermazioni con la forma di requisiti, e trasformarle in un `EVD` richiede un
passaggio che sembra piccolo. Non lo è: nessuno ha osservato niente.

**La regola:** una skill può strutturare, classificare, collegare, propagare e generare da
fonti esistenti. **Non può produrre evidenza.** Se un documento risponde a «cosa abbiamo
osservato», lo scrivi tu.

---

## 9 · Ordine di costruzione

| Quando | Cosa | Perché ora |
|---|---|---|
| Adesso | `framework-capture` | Hai il corpus business da ingestare e non hai ancora niente. È il primo lavoro reale |
| Adesso | `framework-audit` | Attivala in CI con **un solo** controllo: front-matter valido. Il resto dopo |
| Prima del primo commit | `framework-init` | La usi tre volte e ti evita tre strutture divergenti |
| Al primo ciclo di change reale | `framework-change` | Prima non hai abbastanza segnali perché serva |
| Al primo `CHG` | `validate.py --emit-manifest` | Prima il manifest si aggiorna a mano in trenta secondi. Vedi §7 |
| Al primo rilascio | `framework-release` | Prima non c'è niente da rilasciare |

Sui controlli in CI: **aggiungili uno per volta, quando il fallimento che prevengono è già
accaduto una volta.** Dodici controlli attivati prima che esista il codice sono una fabbrica
costruita prima del prodotto: rallentano senza aver ancora prevenuto niente, e la reazione
prevedibile è disattivarli tutti.

Vale anche per le skill la regola che protegge il framework: **ogni skill deve risparmiare più
tempo di quanto costa mantenerla, questa settimana.** Una skill è codice, e come tutto il
codice invecchia e va tenuta allineata a un framework che nel frattempo cambia.
