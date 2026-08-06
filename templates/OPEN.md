---
schema: framework/open-register/v1
artifact_type: open-register
lifecycle: living
status: active
products: [prodotto-a, prodotto-b, prodotto-c]
owners: [NOME]
created: AAAA-MM-GG
last_review: AAAA-MM-GG HH:MM
classification: internal
---

# Decisioni aperte e problemi noti

**A cosa serve.** Contiene tutto ciò che è ancora indeciso o consapevolmente rotto. È
l'informazione che nessun altro documento del framework contiene: `decisions/` registra
ciò che è stato *deciso*, `ARC` com'è fatto il sistema, `RSK` cosa può andare storto. Solo
questo file dice **cosa non è ancora stato scelto** — e senza, un agente riempie il vuoto
con un'ipotesi plausibile e la implementa con convinzione.

**È l'unico documento del framework che si accorcia.** Quando una decisione viene presa,
la voce esce da `§1` e diventa un `DEC-NNN`, lasciando una riga di rimando in `§4`. Se il
file non si accorcia mai, stai accumulando invece di decidere.

**Uno per repository, alla radice.** Se un prodotto ha bisogno di un proprio registro
tecnico — perché ne aveva già uno prima di adottare il framework, o perché le sue voci
sono troppe e troppo specifiche — può stare in `products/<p>/OPEN.md`, ma allora `AGENTS.md`
deve dire esplicitamente quale dei due risponde a quale domanda. Due registri senza quella
riga sono due registri che divergono.

## Come si usa

1. **Un agente legge questo file prima di prendere qualunque decisione strutturale.** Se
   la scelta necessaria è elencata qui come aperta, non la prende: la solleva.
2. **Il campo `Default in uso` è obbligatorio.** Una decisione non presa non significa
   assenza di comportamento: qualcosa sta già succedendo, fosse anche «niente». Scrivere
   cosa è la differenza fra un rinvio consapevole e un buco.
3. **Il costo di ritorno determina l'urgenza, non l'importanza.** Le voci a costo alto
   vanno decise anche con informazione incompleta, perché il costo di aspettare supera
   quello di sbagliare. Quelle a costo basso si rinviano quanto si vuole.
4. **Quando decidi:** scrivi il `DEC`, sostituisci la voce con una riga di rimando in `§4`,
   elimina il resto.

---

# §1 · Decisioni aperte

Raggruppate per costo di ritorno, non per argomento: è il costo che dice quali guardare
per prime.

## Costo di ritorno ALTO — decidere prima della prima riga di codice

### OD-001 · Titolo della decisione, in forma di scelta

- **Domanda:** la scelta effettiva, formulata come domanda con almeno due risposte.
- **Costo di ritorno:** alto.
- **Default in uso:** cosa sta già succedendo, oggi, in assenza di decisione. Se davvero
  non sta succedendo niente, scrivi `nessuno` — ma è la combinazione più cara che esista
  insieme a un costo alto, e il validatore te la segnala.
- **Il problema che il default introduce:** perché lasciarla aperta costa qualcosa.
- **Dipende da:** altre voci `OD-NNN` che vanno decise prima, se ce ne sono.
- **Orientamento:** la direzione verso cui propendiamo, e perché. Facoltativo, e non è
  una decisione: serve a non ricominciare il ragionamento da zero fra due settimane.
- **Scadenza:** una data, o un evento osservabile.

## Costo di ritorno MEDIO — decidere entro il primo mese

### OD-002 · Titolo

- **Domanda:**
- **Costo di ritorno:** medio.
- **Default in uso:**
- **Il problema che il default introduce:**
- **Scadenza:**

## Costo di ritorno BASSO — si rinviano quanto si vuole

### OD-003 · Titolo

- **Domanda:**
- **Costo di ritorno:** basso.
- **Default in uso:**
- **Trigger:** la condizione che la rende urgente. Su una voce a costo basso il trigger
  sostituisce la scadenza: non c'è una data entro cui deciderla, c'è un evento dopo il
  quale non si può più rinviare.

---

# §2 · Problemi noti accettati

Problemi reali che abbiamo scelto di non risolvere ora. **Ogni voce ha un trigger che la
riapre:** senza trigger non è un problema accettato, è un problema dimenticato.

### KI-001 · Titolo

- Cosa è rotto o mancante, in una riga.
- Perché lo accettiamo ora.
- Chi o cosa ne subisce l'effetto.
- **Trigger di riapertura:** la condizione osservabile che rende necessario risolverlo.
- **Riferimento:** `CHG` / `DEC` / `SIG` collegato.

---

# §3 · Parcheggio

Idee e domande emerse e non ancora qualificate. Non sono decisioni aperte: sono cose da
guardare. Una riga ciascuna, senza formato. Se una resta qui per tre mesi senza che nessuno
la tocchi, cancellala — il parcheggio che non si svuota è un secondo backlog che nessuno
legge.

---

# §4 · Decisioni chiuse

Una riga per voce chiusa, con la data e il `DEC` che l'ha chiusa. Non ricopiare il
contenuto: sta nel `DEC`.

- **AAAA-MM-GG · OD-NNN** → [`DEC-NNN`](decisions/DEC-NNN-slug.md) · una riga su cosa si è
  deciso. Se la decisione ha chiuso la voce solo in parte, dillo qui e apri la parte
  residua come nuova voce in `§1`, con il numero nuovo.

---

## Anti-pattern

- **Omettere `Default in uso`.** È l'errore che rende inutile l'intero file. «Non deciso»
  suona come «non sta succedendo niente», e invece qualcosa sta già succedendo: di solito
  la scelta implicita di chi ha scritto il primo pezzo di codice.
- **Usare il costo di ritorno per dire quanto la decisione è importante.** Sono cose
  diverse. Una scelta poco importante ma costosa da ribaltare va decisa prima di una
  importante e reversibile.
- **Lasciare la voce in `§1` dopo aver scritto il `DEC`.** Il registro dice allora che è
  aperta una cosa che è chiusa, e un agente si fermerà a chiedere il permesso per una
  decisione già presa. Il validatore lo intercetta, ma solo se il `DEC` la dichiara in
  `derives_from`.
- **Mettere in `derives_from` di un `DEC` un `OD-NNN` che quel `DEC` non chiude.** Un `DEC`
  nomina una voce aperta per tre motivi diversi — la chiude, ne dipende, o ne apre una più
  stretta — e `derives_from` significa il primo. Per gli altri due, il rimando va in prosa.
- **Registrare qui i rischi.** Un rischio è qualcosa che può andare storto e sta in `RSK`;
  una decisione aperta è qualcosa che va scelto. Se la voce non ha almeno due risposte
  possibili, non appartiene a questo file.
- **Farlo crescere.** Un registro che si allunga a ogni sessione e non si accorcia mai non
  è un registro di decisioni: è la prova che non se ne sta prendendo nessuna.
