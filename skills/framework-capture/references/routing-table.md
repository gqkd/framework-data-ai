# Tabella di instradamento

Riferimento condiviso dalle due modalità di `framework-capture`. Risponde a una sola
domanda: **data un'affermazione, dove va scritta e cosa cambia con lei?**

È l'unica fonte di questa logica. Non duplicarla nelle istruzioni di altre skill: se
divergesse, il corpus e le note conversazionali finirebbero in posti diversi.

---

## 1 · Classificazione

Il tipo di enunciato non si deduce dall'argomento ma dalla **forza epistemica**: la stessa
frase può essere una promessa, una convinzione o un'osservazione, e le tre cose vanno in
posti diversi. «Il sistema processa 10M di righe al giorno» può significare *lo abbiamo
promesso*, *crediamo che servirà*, oppure *l'abbiamo misurato*. Se non è distinguibile dal
contesto, **chiedi**: è la domanda che paga di più in tutta la skill.

| Tipo | Riconoscibile da | Destinazione autorevole | Classe |
|---|---|---|---|
| **Impegno** | presente in un documento mostrato a un cliente; «abbiamo promesso», «da contratto» | `COMMITMENTS.md` → `CMT-NNN` | vivente |
| **Decisione presa** | «abbiamo deciso», «usiamo X», «andiamo con» | nuovo `DEC-NNN` | immutabile |
| **Definizione** | «un X è», «si calcola come», «per Y intendiamo» | `GLOSSARY.md` | vivente |
| **Osservazione sul presente** | «oggi funziona così», «il dato arriva ogni ora» | `WF.md §corrente` | vivente |
| **Evidenza raccolta** | «ho intervistato», «ho interrogato la tabella» | `EVD-NNN` o `DFB-NNN` | immutabile |
| **Problema del cliente** | «il problema è che», «perdono tempo a» | `PRB-NNN` | immutabile |
| **Ipotesi** | «se facessimo X allora Y» | `HYP-NNN` | immutabile |
| **Richiesta o feedback** | «il cliente vuole», «hanno chiesto» | `LOG.md` → `SIG-NNN` type `feedback`/`request` | append-only |
| **Incidente o anomalia** | «è andato giù», «i numeri sono strani» | `LOG.md` → `SIG-NNN` type `incident`/`drift` | append-only |
| **Vincolo** | «non possiamo», «la normativa richiede», «deve stare in UE» | `RSK.md §stato` + `PBR.md` vincoli | vivente |
| **Rischio** | «c'è il rischio che», «se succedesse» | `RSK.md §stato` | vivente |
| **Obiettivo numerico** | «riduzione del 30%», «entro 2 secondi» | `EVP.md` soglia **e** `COMMITMENTS` se promesso | vivente |
| **Capability promessa** | «il sistema farà», «include il modulo» | `PBR.md` capability con `stato: shaped` | vivente |
| **Correzione di un fatto scritto** | «in realtà no», «è cambiato» | dipende dal documento che lo contiene → §3 | — |
| **Ragionamento non concluso** | «forse», «sto pensando», «potremmo valutare» | `OPEN.md §3 parcheggio`, o niente | vivente |

**Il caso che si sbaglia più spesso.** Una richiesta non è un mandato. «Il cliente vuole
l'export in Excel» va in `LOG` come `SIG`, e al massimo genera un incremento `conditional`
in `RMP`. **Non** diventa un `CHG` e non si implementa: quello richiede di passare da
intake, triage e `ICG`. Saltare questo passaggio è il modo in cui una suite di prodotti
diventa la somma delle ultime cose chieste.

**Il caso più insidioso.** Una frase di marketing è spesso una decisione architetturale.
«Un'unica esperienza per i tre moduli» non è un claim: è una decisione di tenancy e
identità, cioè `OD-003` di `OPEN.md`. Quando classifichi un impegno, chiediti sempre
**quale vincolo tecnico ne deriva**, e scrivilo nella riga corrispondente di
`COMMITMENTS`. Se quella colonna è vuota per tutte le righe, la classificazione non è
finita.

---

## 2 · Cascata

Scrivere in un posto solo non basta: la coerenza sta nelle scritture collegate. Queste sono
obbligatorie, e il validatore verifica alcune di esse.

| Se scrivi | Devi anche |
|---|---|
| `DEC` con `scope: architecture` | aggiornare `ARC.md` nello stesso passaggio — altrimenti `validate.py` segnala `CHG002` |
| `DEC` con `scope: product` | aggiornare `PBR.md` se cambia capability, scope o outcome |
| `DEC` con `scope: platform` | elencare **tutti** i prodotti in `products`, e aggiornare `PLATFORM.md` |
| un `DEC` che chiude una voce di `OPEN.md` | spostare la voce in `OPEN.md §4` con il rimando, e rigenerare `product.yaml` |
| una voce `GLOSSARY` per un termine che è anche un campo di un `DC` | aggiornare la semantica del `DC` e bumpare la versione |
| una metrica in `GLOSSARY` usata da più prodotti | verificare che tutti la calcolino con quella formula. Se non possono, sono due metriche: servono due nomi |
| un `CMT` con `Fattibilità: fuori portata` | aprire una riga in `RSK §stato` **e** una voce in `OPEN.md`, e segnalarlo all'utente come la cosa più urgente del progetto |
| un vincolo su un dato (freschezza, volume, residenza) | aggiornare le **garanzie** del `DC` relativo, non solo lo schema |
| una soglia in `EVP` | se abbassa una soglia esistente, serve un `DEC` con il motivo. Mai in silenzio |
| un `SIG` che materializza un rischio noto | aggiungere una riga in `RSK §eventi` |
| `WF §corrente` | verificare se il `§delta` resta vero. Un delta stantio è una bugia silenziosa |
| una capability in `PBR` che dipende da un altro prodotto | verificare che esista un `DC` interno per quel punto di contatto |

---

## 3 · Correzioni, e la regola della classe

Una correzione è l'operazione più delicata, perché la classe del documento decide **cosa
sei autorizzato a fare**.

| Classe del documento da correggere | Operazione ammessa |
|---|---|
| **vivente** | modifica in luogo, aggiorna `last_review` all'istante corrente (`AAAA-MM-GG HH:MM`, non alla sola data: nella stessa giornata può succedere più volte) |
| **immutabile** | **mai modificare.** Crea un documento nuovo con `supersedes`, e porta il vecchio a `status: superseded` |
| **append-only** | **mai riscrivere una riga.** Aggiungi un evento collegato (`ANA-NNN` su `SIG-NNN`) |

Sull'immutabile la tentazione è forte e va nominata: se un `PRB` risulta sbagliato, la
correzione non è modificarlo. Quel documento registra cosa credevamo allora, e cancellarlo
distrugge l'unica informazione che rende ricostruibile perché una decisione sembrava
sensata. Scrivi un `PRB` nuovo.

---

## 4 · Conflitti

Prima di scrivere, verifica se l'affermazione contraddice qualcosa già presente. **Un
conflitto rilevato è il risultato più utile della skill** e non si risolve
automaticamente: si porta all'utente.

Cerca conflitti in questi punti, che sono quelli dove si annidano:

1. **Garanzie sui dati** — la nuova affermazione contraddice la freschezza o la
   completezza dichiarata in un `DC`?
2. **Definizioni** — il termine è già in `GLOSSARY` con un'altra definizione, o con un
   `Non include` che l'affermazione viola?
3. **Impegni** — contraddice un `CMT`? È il conflitto più costoso, perché qualcuno lo ha
   detto a un cliente.
4. **Decisioni** — esiste un `DEC` `accepted` che dice il contrario? Allora questa non è
   un'informazione nuova: è un cambio di decisione, e richiede un `DEC` che supersede.
5. **Fuori scope** — l'affermazione riguarda qualcosa che `PBR §Fuori scope` o `RMP §Non in
   roadmap` escludono esplicitamente? Non è una dimenticanza: è stato deciso.
6. **Decisioni aperte** — la scelta necessaria è in `OPEN.md`? Allora non scriverla come
   fatto: è ancora aperta, e questa è forse l'informazione che la chiude — ma la chiude
   l'utente, non tu.

Quando trovi un conflitto: **fermati, mostra le due versioni con la loro provenienza,
chiedi quale vale.** Non scegliere la più recente per default: nel corpus business il
documento più recente è spesso il deck commerciale, cioè il meno affidabile sui fatti.

---

## 5 · Quanto automatizzare

**L'automaticità è inversamente proporzionale all'ampiezza della cascata.**

**Applica direttamente**, senza chiedere: una destinazione sola, classe append-only,
nessuna interpretazione, nessun conflitto. In pratica: registrare un `SIG` in `LOG`, o una
voce nel parcheggio di `OPEN.md`. Sono operazioni che non distruggono niente e che
chiedere renderebbe solo fastidiose.

**Proponi un diff e attendi conferma** in tutti gli altri casi, e in particolare: quando la
cascata tocca più di un file · quando è coinvolto un immutabile · quando hai rilevato un
conflitto · quando la classificazione era ambigua · quando la scrittura chiuderebbe una
voce di `OPEN.md`.

La ragione è precisa: la cascata è il punto in cui la fiducia di un agente supera la sua
accuratezza. Una classificazione sbagliata scrive un fatto plausibile nel posto autorevole,
e da lì in avanti tutti — persone e agenti — lo leggono come vero. Chiedere costa dieci
secondi; questo errore costa una decisione.

---

## 6 · Raccolta a fine sessione

In modalità conversazionale, **non registrare frase per frase.** Una conversazione è fatta
in gran parte di ragionamento ad alta voce, e trattare ogni affermazione come un fatto da
archiviare produce un registro di rumore in cui i fatti veri diventano irreperibili.

Il modello corretto è la raccolta a fine sessione: tieni traccia mentalmente delle
affermazioni registrabili, e quando la conversazione arriva a un punto di riposo — o quando
l'utente lo chiede — presenta l'elenco:

> Da questa conversazione mi sembrano registrabili quattro cose:
> 1. *decisione* — Postgres come datastore primario → `DEC` nuovo + `ARC` + chiude `OD-005`
> 2. *definizione* — «cliente attivo» = login negli ultimi 30 giorni → `GLOSSARY`, **in
>    conflitto** con la formula già presente per prodotto-b
> 3. *richiesta* — export Excel chiesto dal cliente → `SIG` in `LOG`
> 4. *ragionamento* — valutare se separare il modulo di reporting → parcheggio
>
> Quali registro?

Le eccezioni, da scrivere subito senza aspettare: un **incidente** (`SIG` type `incident`,
perché il valore dipende dall'ora esatta) e un impegno **fuori portata** appena emerso.
