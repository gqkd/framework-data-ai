# Framework di documentazione — Progetti Data & AI

**Versione 1.0** · Documento di riferimento. Se stai entrando adesso nel progetto, leggi
questo file per intero prima di aprire qualsiasi altro documento.

---

## 1. A cosa serve

Questo framework definisce **quali documenti esistono, chi li crea, quando, e quale
domanda risponde ciascuno**. Ha due destinatari con esigenze diverse:

- **una persona nuova**, che deve capire il sistema abbastanza per modificarlo senza
  rompere decisioni prese per buoni motivi;
- **un agente AI**, che deve poter rispondere a domande sul progetto senza inventare le
  parti mancanti.

Il secondo destinatario condiziona la forma dei documenti più del primo. Un agente non
naviga un diagramma e non ricorda la riunione: legge file, segue link e — questo è il
punto — **riempie i vuoti con ipotesi plausibili**. Per questo il framework insiste su
tre cose che a un lettore umano sembrerebbero pedanteria: dichiarare cosa è fuori scope,
dichiarare cosa non è stato deciso, e non lasciare che lo stesso fatto sia autorevole in
due posti.

### Cosa questo framework non contiene

Elenco deliberato, da usare come difesa quando qualcuno proporrà di aggiungere un
documento: **PRD**, **project plan**, **test plan separato**, **data dictionary
autonomo**, **specifica dei requisiti**. Ogni proposta di nuovo artefatto deve superare
una sola domanda:

> A quale domanda risponde, che nessun documento esistente risponde già?

Se non c'è risposta, la risposta è no.

---

## 2. Il principio unico

> **Ogni fatto ha una sola fonte autorevole.**

È più importante di "un documento, una domanda". Un documento può rispondere a più
domande vicine (il Runbook contiene comandi, SLO e monitoring: va bene, sono la stessa
attività). Ciò che non può accadere è che *dove risiede il dato X* sia scritto in due
documenti diversi, perché prima o poi divergeranno e nessuno saprà quale credere.

Quando ti accorgi di stare scrivendo un fatto già presente altrove: mettici un link, non
una copia.

---

## 3. Le tre classi di artefatto

Il regime di manutenzione è la proprietà più importante di un documento, più del suo
contenuto. Ogni artefatto appartiene a una sola classe, dichiarata nel front-matter.

| Classe | Regola | Risponde a |
|---|---|---|
| **Vivente** (`living`) | Un solo file, sempre attuale, campo `last_review` | com'è **adesso** |
| **Immutabile** (`immutable`) | Nuovo file ogni volta, mai riscritto, si *supersede* | **perché** si è deciso così |
| **Append-only** (`append-only`) | Si aggiungono righe, non si modificano le esistenti | cosa è **successo** |

**Perché conta:** un agente che legge un documento storico come verità corrente prende
decisioni sbagliate con totale sicurezza. La classe è ciò che glielo impedisce.

**Corpo e stato non sono la stessa cosa.** «Mai riscritto» vale per la prosa e la decisione:
quelle non cambiano mai, e se cambiano è un nuovo file che supersede. Il campo `status` è
un'eccezione dichiarata: `CHG`, `HYP` e `DEC-ADR` lo fanno avanzare nello stesso file secondo
le transizioni enumerate nel loro schema (`draft → approved → implemented → verified →
rolled-back`, per un `CHG`) perché registra cosa è successo alla decisione, non cosa dice.
Non è una riscrittura — è l'unico campo per cui il framework permette di toccare un
immutabile sul posto.

**Regola per gli append-only:** al momento dell'osservazione non conosci ancora causa e
rimedio. Non aggiornare la riga: aggiungi un evento collegato.

```
SIG-014   segnale osservato
ANA-014   analisi di SIG-014
DEC-031   decisione presa su ANA-014
CHG-052   cambiamento generato da DEC-031
```

---

## 4. I due assi: iniziativa e prodotto

È la distinzione strutturale che regge il framework alla seconda iniziativa sullo stesso
sistema. Senza di essa la seconda iniziativa produce un documento di architettura
concorrente, e da lì non si torna indietro.

**Artefatti di iniziativa** — nascono e muoiono con l'iniziativa, non si mantengono:
`PRB` `HYP` `EVD` `CMP` `DFB` `SD`

**Artefatti di prodotto** — vivono quanto il sistema e accumulano contributi da
iniziative diverse:
`PBR` `WF` `ARC` `EVP` `DC` `RB` `RMP` `RSK` `LOG`

**Artefatti di piattaforma** — condivisi fra i tre prodotti:
`PLATFORM.md` `GLOSSARY.md` `DEC-ADR` (registro unico) `OPEN.md`

Ne segue la struttura delle cartelle:

```
repo/
├── AGENTS.md                    control plane per gli agenti
├── OPEN.md                      decisioni aperte e problemi noti
├── COMMITMENTS.md               cosa è stato promesso commercialmente
├── GLOSSARY.md                  unico, condiviso dai tre prodotti
├── PLATFORM.md                  architettura del substrato condiviso
├── corpus/                      documenti del business che parlano di più prodotti
├── decisions/                   registro unico DEC-NNN (prodotto + architettura)
│   ├── DEC-001-slug-della-decisione.md
│   ├── DEC-002-slug-della-decisione.md
│   └── DEC-003-slug-della-decisione.md
├── initiatives/
│   └── 2026-07-churn-scoring/
│       ├── PRB-001.md  HYP-001.md  EVD-001.md
│       └── CMP-001.md  DFB-001.md  SD-001.md
└── products/
    ├── prodotto-a/
    │   ├── corpus/              documenti del business su questo prodotto
    │   ├── product.yaml         manifest machine-readable
    │   ├── PBR.md               product brief (vivente)
    │   ├── ARC.md               delta rispetto a PLATFORM.md
    │   ├── WF.md                workflow: §corrente §target §delta
    │   ├── RMP.md               roadmap progressiva
    │   ├── IMP.md               piano del ciclo corrente
    │   ├── RSK.md               rischi: §stato §accettazioni §eventi
    │   ├── RB.md                runbook + SLO
    │   ├── LOG.md               registro segnali append-only
    │   ├── contracts/           DC-NNN per dataset o interfaccia
    │   ├── changes/             CHG-NNN
    │   └── releases/            REL-NNN.md + RLM-NNN.yaml + EVR-NNN.md
    ├── prodotto-b/
    └── prodotto-c/
```

---

## 5. Il ciclo di vita

Tre blocchi. Il primo è lineare e si percorre una volta per iniziativa. Il secondo
costruisce. Il terzo è continuo e non finisce mai.

### Blocco A — Discovery *(per iniziativa)*

| Fase | Produce |
|---|---|
| **F1 · Segnale e framing** | `PRB` formulazione problema · `HYP` ipotesi |
| **F2 · Problem discovery** | `WF §corrente` · `EVD` evidence brief |
| **F3 · Solution discovery** | `WF §target` · `CMP` competitor · `DFB` data feasibility |

### Blocco B — Costruzione *(per prodotto)*

| Fase | Produce |
|---|---|
| **F4 · Shaping MVP e MVA** | `PBR` product brief · `SD` solution design + MVA · `EVP` evaluation plan · `DC` data contract · `DEC` |
| **F5 · Build e release candidate** | `ARC` architettura — **vive da qui, non dal go-live** · codice |
| **F6 · Go-live controllato** | `RB` runbook + SLO · `EVR` eval report · `REL` release note · `RLM` release manifest |

> **Correzione rispetto alla versione precedente:** prima il gate sulle soglie di
> evaluation stava fra F4 e il go-live, ma F4 produce solo documenti di progetto — non
> c'era niente da valutare. La build viene prima della valutazione. Sempre.

### Blocco C — Esercizio ed evoluzione *(loop continuo, per prodotto)*

```
Run & Observe  →  Change intake  →  Triage e impact assessment  →  [ICG]
      ↑                                                             ↓
   Deploy  ←  [RG]  ←  Build  ←  IMP  ←  CHG  ←  Reshaping ────────┘
```

L'ordine conta, ed era sbagliato nella versione precedente: **il piano si scrive dopo il
reshaping**, non prima. Se scrivi il piano e poi il reshaping cambia lo scope, il piano
è già obsoleto.

| Passo | Produce |
|---|---|
| **Run & Observe** | `LOG` registro segnali (append-only) |
| **Change intake** | selezione dai segnali e dagli incrementi di `RMP` |
| **Triage e impact assessment** | classificazione → **ICG** |
| **Reshaping** prodotto e/o architettura | `PBR` `WF` `ARC` `EVP` `DC` `RSK` `DEC` `RMP` |
| **Change contract** | `CHG` — cosa è autorizzato |
| **Cycle implementation plan** | `IMP` — come lo eseguiamo in questo ciclo |
| **Build** | `ARC` aggiornata |
| **Release gate** | `EVR` |
| **Deploy** | `REL` `RLM` |

---

## 6. I gate

Due tipi, e confonderli è un errore comune. I **gate di ciclo di vita** si attraversano
una volta. I **controlli ricorrenti** scattano a ogni giro e non fanno avanzare il
progetto: lo trattengono.

| ID | Tipo | Domanda | Output | Se scade |
|---|---|---|---|---|
| **G1** | lifecycle | Il segnale merita tempo di indagine? | `DEC` | no-go |
| **G2** | lifecycle | Il problema è reale, ricorrente e costoso? | `DEC` | no-go |
| **G3** | lifecycle | La soluzione è desiderabile, sostenibile, fattibile e responsabile? | `DEC` | no-go |
| **G4** | lifecycle | Prodotto, architettura e piano sono definiti abbastanza per **iniziare la build**? | `DEC` | blocca |
| **RG** | ricorrente | Le soglie dell'`EVP` **congelato** sono superate? | `EVR` | no-go → **rework** |
| **MOR** | lifecycle | Quali ipotesi ha confermato o smentito l'uso reale? | `DEC` | — |
| **ICG** | ricorrente | Il cambiamento modifica prodotto, architettura, dati, evaluation o profilo di rischio? | routing nel `CHG` | — |

**Ogni gate produce un `DEC`.** Un gate che non lascia traccia scritta non è un gate, è
una riunione. Ogni gate ha un decisore (un ruolo) e un tempo massimo: oltre la scadenza
il default è no-go, perché un gate senza scadenza produce progetti in coma che nessuno
chiude — chiuderli richiederebbe una decisione.

### RG — Release Gate

Non è un gate di ciclo di vita: è un controllo della pipeline, ripetuto a ogni release
candidate, compresa la prima. Verifica l'`EVR` contro le soglie dell'`EVP` **nella
versione congelata al momento della RC**. Il congelamento è ciò che impedisce di
ritoccare le soglie dopo aver visto i risultati.

Se l'esito è negativo **prima del deployment**, si fa **rework**, non rollback. Il
rollback esiste solo dopo un deployment, quando emergono regressioni o incidenti in
produzione: quel percorso rientra da `LOG` → change intake.

### ICG — Impact Classification Gate

La domanda "impatta l'architettura?" è troppo stretta: un cambiamento può non toccare
l'architettura e invalidare l'outcome, il pricing, un data contract o il profilo di
rischio. Instradamento:

| Esito | Percorso |
|---|---|
| Nessun impatto strutturale | `CHG` tecnico, direttamente a `IMP` |
| Impatto prodotto | Product reshaping → `PBR` `WF` |
| Impatto architettura | Architecture reshaping → `ARC` `DEC` |
| Impatto entrambi | Joint reshaping |
| Ipotesi di soluzione invalidata | rientro in **F3** |
| Problema o segmento invalidato | rientro in **F2** |

---

## 7. Il catalogo degli artefatti

Un template per ciascuno in `templates/`. Ogni template contiene gli anti-pattern.

| ID | Nome | Classe | Asse | Nasce in |
|---|---|---|---|---|
| `AGENTS` | Control plane per agenti | vivente | piattaforma | giorno uno |
| `OPEN` | Decisioni aperte e problemi noti | vivente | piattaforma | giorno uno |
| `COMMITMENTS` | Impegni commerciali presi | vivente | piattaforma | giorno uno |
| `GLOSSARY` | Glossario e dizionario metriche | vivente | piattaforma | giorno uno |
| `PLATFORM` | Architettura del substrato condiviso | vivente | piattaforma | giorno uno |
| `product.yaml` | Manifest del prodotto | vivente, in parte generato | prodotto | giorno uno |
| `PBR` | Product brief | vivente | prodotto | F4 |
| `PRB` | Formulazione problema | immutabile | iniziativa | F1 |
| `HYP` | Ipotesi soluzione | immutabile | iniziativa | F1 |
| `WF` | Workflow corrente / target / delta | vivente | prodotto | F2 |
| `EVD` | Problem evidence brief | immutabile | iniziativa | F2 |
| `CMP` | Comparativa competitor | immutabile | iniziativa | F3 |
| `DFB` | Data feasibility brief | immutabile | iniziativa | F3 |
| `SD` | Solution design + MVA | immutabile | iniziativa | F4 |
| `EVP` | Evaluation plan | vivente, congelato per RC | prodotto | F4 |
| `DC` | Data contract | vivente, versionato | prodotto | F4 |
| `DEC-ADR` | Decision record — prodotto **o** architettura | immutabile | piattaforma | ovunque |
| `ARC` | Architettura corrente | vivente | prodotto | **F5** |
| `RB` | Runbook + SLO + monitoring | vivente | prodotto | F6 |
| `EVR` | Evaluation report | immutabile | prodotto | RG |
| `REL` | Release note (per umani) | immutabile | prodotto | F6 |
| `RLM` | Release manifest (per macchine) | immutabile | prodotto | F6 |
| `LOG` | Registro segnali | append-only | prodotto | F5 |
| `ING` | Registro di ingestione del corpus business | append-only | piattaforma | giorno uno |
| `RMP` | Progressive implementation roadmap | vivente | prodotto | F4 |
| `CHG` | Change contract | immutabile | prodotto | loop |
| `IMP` | Cycle implementation plan | vivente, sostituito | prodotto | loop |
| `RSK` | Rischi: stato / accettazioni / eventi | vivente | prodotto | F3 |

### Le distinzioni che si confondono più spesso

**`DEC-ADR` è un solo tipo di documento per decisioni di prodotto e di architettura.**
Il nome tiene insieme le due tradizioni: l'ADR classico è il caso `scope: architecture`.
Un solo registro, una sola numerazione (`DEC-NNN`), una sola cartella; il campo `scope`
determina la natura della decisione:

| `scope` | Registra | Esempi |
|---|---|---|
| `product` | cosa costruiamo, per chi, con quale priorità | esito di un gate · pivot · stop · scope dell'MVP · accettazione di un rischio commerciale |
| `architecture` | com'è fatto il sistema — l'ADR classico | datastore · stile di integrazione · confini fra componenti |
| `platform` | ciò che vincola tutti e tre i prodotti | tenancy · identità · substrato condiviso |

Rinunciare a un prodotto o accettare un rischio commerciale sono decisioni tanto da
registrare quanto la scelta di un database, e spesso più costose. Registri separati
significherebbero che le decisioni cross-prodotto — le più care — non hanno casa e
finiscono in quello del prodotto su cui stavi lavorando quel giorno.

**`RMP` ≠ `IMP`.** `RMP` risponde a *quali incrementi futuri ipotizziamo e da quali
evidenze dipendono*: è vivente, guarda avanti, ed è un **input** al change intake.
`IMP` risponde a *come eseguiamo i change contract approvati in questo ciclo*: è
sostituito ogni ciclo, ed è un **output** del reshaping.

**`SD` → `ARC`.** `SD` è lo snapshot immutabile del progetto al gate G4. `ARC` è la
verità corrente e comincia a vivere in **F5**, con la prima riga di codice: design e
implementazione divergono molto prima del go-live.

**`REL` + `RLM`.** La release note di dieci righe serve a una persona; non basta a un
agente né a un rollback. Il manifest è la stessa release in forma machine-readable, con
commit, digest, versioni di modello, prompt e dataset, `EVR` e `CHG` inclusi, target di
rollback.

**`LOG` assorbe il feedback.** Non esiste un documento "feedback" separato: tutto entra
in `LOG` con `type: incident | drift | feedback | request | metric | compliance`. Il
testo originale di un feedback si conserva verbatim in un campo, perché è l'unica cosa
che permette di ri-interpretarlo fra sei mesi.

**`WF` e `RSK` sono file unici a paragrafi.** `WF` ha `§corrente`, `§target`, `§delta`;
`RSK` ha `§stato`, `§accettazioni`, `§eventi`. File separati garantirebbero la
divergenza, che è il fallimento peggiore. I titoli markdown sono già indirizzabili da un
agente: usa link con anchor (`WF.md#target`).

---

## 8. Front-matter e identificatori

Ogni artefatto markdown comincia con questo blocco. È ciò che rende la cartella un grafo
interrogabile invece di un mucchio di file.

```yaml
---
schema: framework/decision-record/v1
id: DEC-014
artifact_type: decision-record
lifecycle: immutable            # living | immutable | append-only
status: accepted                # valori definiti dallo schema dell'artefatto
version: 1.0.0
products: [prodotto-a, prodotto-b]
scope: architecture             # solo per DEC
owners: [nome.cognome]
approvers: [nome.cognome]
created: 2026-07-27
last_review: 2026-07-29 18:40   # obbligatorio solo per lifecycle: living
derives_from: [HYP-001, EVD-003]
supersedes: DEC-009
verified_against: a1b2c3d       # commit o tag, dove applicabile
classification: internal
---
```

`status` e `artifact_type` sono definiti dallo **schema specifico** dell'artefatto, non
da un'enumerazione comune: un `DEC` è `proposed | accepted | superseded`, un `CHG` è
`draft | approved | implemented | verified | rolled-back`. L'enumerazione unica sarebbe
troppo generica per essere utile.

**`created` è un giorno, `last_review` è un istante.** Un documento nasce una volta sola,
ma si rivede anche tre volte nello stesso pomeriggio, e senza l'ora la terza revisione è
indistinguibile dalla prima: si perde l'unica cosa che il campo serve a stabilire, cioè se
la revisione è venuta prima o dopo il cambiamento che avrebbe dovuto recepire. Il formato è
`AAAA-MM-GG HH:MM`; la sola data resta accettata e vale mezzanotte. Un valore compilato a
metà — `2026-07-29 HH:MM` — **non** vale mezzanotte: è `LC004`, perché farlo passare
significherebbe presentare un documento mai rivisto come rivisto oggi.

### Catena di tracciabilità

```
PRB → HYP → EVD → DEC(gate) → SD → DEC/ADR → CHG → EVR → RLM → SIG → DEC → CHG
```

Non si mantiene a mano: si genera dal front-matter. Vedi `SKILLS.md`.

---

## 9. La gestione dei tre prodotti

I tre prodotti sono complementari e vengono costruiti da una sola persona. Questo cambia
il calcolo rispetto a tre team indipendenti: il vincolo stringente non è la qualità
dell'astrazione, è la **superficie di manutenzione**. Tre codebase divergenti sono un
costo permanente.

Quattro regole:

1. **Un solo `GLOSSARY.md`.** È il file dove la complementarità dei tre prodotti si
   definisce o si perde. Se lo stesso concetto ha due nomi in due prodotti, la
   complementarità è già rotta e nessuno se ne è accorto.
2. **Un solo registro `decisions/`**, con campo `products`. Le decisioni cross-prodotto
   sono le più costose e in registri separati finirebbero in quello del prodotto su cui
   stavi lavorando quel giorno.
3. **`PLATFORM.md` + un `ARC` breve per prodotto.** Non tre architetture: un substrato
   condiviso (identità, accesso ai dati, deploy, osservabilità, convenzioni) più il
   delta di dominio di ciascun prodotto.
4. **I data contract *fra* i tuoi tre prodotti vengono prima di quelli verso
   l'esterno.** Sono contratti con te stesso a sei mesi di distanza, e sono quelli che
   romperai in silenzio.

Il perimetro esatto del substrato condiviso è una decisione aperta: `OPEN.md`, voce
`OD-002`.

---

## 10. Da dove si comincia

### Entry assessment

Il framework ha più di un ingresso. Scegli la riga che descrive la tua situazione.

| Situazione | Ingresso |
|---|---|
| Idea, niente promesso a nessuno | F1, percorso completo |
| **Idea già venduta o promessa** | F1 con `COMMITMENTS.md` come vincolo, e **discovery inversa** |
| Codice esistente senza documentazione | F5 in reverse: `ARC` ricostruita dal codice, `PBR`, e un `DEC` per ogni decisione già implicita nel codice |
| Prodotto in produzione | Run & Observe + baseline (`ARC` `RB` `DC` `RSK`), poi discovery inversa |

**Sulla discovery inversa.** Quando la soluzione è già stata venduta, la discovery non
va da problema → ipotesi → soluzione, ma al contrario: *soluzione promessa → quale
problema risolve davvero → cosa succede se non lo risolve*. Chiamala per nome nei
documenti. Simulare una discovery in avanti quando la risposta è già stata promessa
produce documentazione finta, ed è il modo più rapido per perdere fiducia nell'intero
impianto.

### Il set del giorno uno

Prima di scrivere una riga di codice, in quest'ordine:

1. `ING.md` + `COMMITMENTS.md` — ingesta il corpus prodotto dal business (presentazioni,
   PDF, analisi dei requisiti) e da lì ricava cosa è stato promesso, a chi, entro quando,
   con quale margine di interpretazione, e cosa è fuori portata tecnica. Sono requisiti che
   scoprirai comunque: la scelta è se scoprirli ora o nel momento peggiore. La skill
   `framework-capture` fa l'estrazione e la classificazione.
2. `OPEN.md` — le decisioni che devi prendere prima di poter scrivere codice, con il
   costo di tornare indietro su ciascuna.
3. `GLOSSARY.md` — anche solo dieci voci. Le prime sono le entità condivise fra i tre
   prodotti.
4. `decisions/` — vuota, con la numerazione avviata.
5. `AGENTS.md` — regole operative per gli agenti.
6. `product.yaml` × 3 — manifest minimo per prodotto.
7. `PBR.md` × 3 — la definizione dei tre prodotti oggi esiste solo dentro dei pitch
   commerciali. Scriverla è il primo atto, non un artefatto di manutenzione.
8. `PLATFORM.md` — anche solo con le sezioni vuote e le decisioni rinviate a `OPEN.md`.

Poi, **quando esiste la cosa da documentare** e non prima:

| Quando | Aggiungi |
|---|---|
| Prima riga di codice | `ARC.md` per prodotto |
| Primo dataset condiviso | `DC` |
| Primo componente con qualità da misurare | `EVP` |
| Inizio della build | `LOG.md` |
| Primo rilascio | `RB` `EVR` `REL` `RLM` |
| Primo errore che un controllo avrebbe intercettato | quel controllo in CI |

### La regola che protegge il framework

> Ogni artefatto deve superare una domanda sola: **mi fa risparmiare più tempo di quanto
> costa mantenerlo, questa settimana?**

Se la risposta è "quando l'azienda crescerà", non è ora. Un framework al 60% che usi
batte uno al 95% che abbandoni fra due mesi.

---

## 11. Regole per gli agenti

Queste stanno anche in `AGENTS.md`, che è il file che un agente legge per primo. Qui per
completezza del quadro.

1. **`OPEN.md` prima di decidere qualsiasi cosa.** Se una scelta necessaria è elencata
   là come aperta, l'agente non la prende: la solleva. È la regola che impedisce a un
   agente di inventare una decisione e implementarla con convinzione.
2. **Non implementare un segnale.** Una riga di `LOG`, un feedback o un incremento di
   `RMP` non sono autorizzazioni a costruire. Si implementa un `CHG` approvato.
3. **Fonte autorevole per tipo di domanda:** com'è fatto → `ARC` · perché → `decisions/`
   · cosa significa un termine → `GLOSSARY` · cosa garantisce un dato → `DC` · cosa è
   stato promesso → `COMMITMENTS` · cosa non è deciso → `OPEN`.
4. **Rispettare la classe.** Non modificare il corpo di un `immutable`: crearne uno nuovo
   che supersede. Il campo `status` fa eccezione — segue le transizioni dichiarate nello
   schema del tipo e si aggiorna sul posto. Non riscrivere una riga di `append-only`:
   aggiungere un evento collegato.
5. **Aggiornamenti obbligatori dopo una modifica:** tocchi l'architettura → `ARC` **e**
   un `DEC` · tocchi dati o schema → il `DC` relativo · tocchi un componente AI → un
   nuovo `EVR` · rilasci → `REL` **e** `RLM`.
6. **Se un fatto non è documentato, dirlo.** L'assenza è un'informazione. Un agente che
   completa un vuoto con un'ipotesi plausibile fa più danni di uno che si ferma.
