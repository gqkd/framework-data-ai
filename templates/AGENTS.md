---
schema: framework/agents-control-plane/v1
artifact_type: agents-control-plane
lifecycle: living
status: active
owners: [NOME]
created: AAAA-MM-GG
last_review: AAAA-MM-GG HH:MM
classification: internal
---

# Istruzioni per agenti

Leggi questo file per primo. Poi `OPEN.md`. Poi il `product.yaml` del prodotto su cui
stai lavorando.

## Fonti autorevoli

Ogni tipo di domanda ha una sola fonte. Non dedurre da altre parti ciò che è scritto qui.

| Domanda | Fonte |
|---|---|
| Com'è fatto il sistema | `products/<p>/ARC.md` e `PLATFORM.md` |
| Perché è fatto così | `decisions/DEC-NNN.md` |
| Cosa fa il prodotto e per chi | `products/<p>/PBR.md` |
| Cosa significa un termine o una metrica | `GLOSSARY.md` |
| Cosa garantisce un dato | `products/<p>/contracts/DC-NNN.md` |
| Come si opera in produzione | `products/<p>/RB.md` |
| Cosa è stato promesso a un cliente | `COMMITMENTS.md` |
| **Cosa NON è deciso** | `OPEN.md` |
| Cosa è autorizzato costruire adesso | `products/<p>/changes/CHG-NNN.md` |

## Regole non negoziabili

1. **Non prendere decisioni elencate in `OPEN.md`.** Se ti serve una scelta che è
   elencata là come aperta, fermati e chiedi. Non completare il vuoto con un'ipotesi
   plausibile: è il modo principale in cui un agente causa danni difficili da rintracciare.
2. **Non implementare un segnale.** Una riga di `LOG`, un feedback o un incremento di
   `RMP` non autorizzano a costruire. Si implementa un `CHG` con `status: approved`.
3. **Rispetta la classe dell'artefatto.**
   - `immutable` → non modificare; creane uno nuovo con `supersedes`
   - `append-only` → non riscrivere righe; aggiungi un evento collegato
   - `living` → modifica e aggiorna `last_review`
4. **Se un fatto non è documentato, dichiaralo.** L'assenza è informazione. Preferisci
   "non è documentato dove risiede questo dato" a una risposta inventata.

## Aggiornamenti obbligatori

Dopo aver modificato il codice, aggiorna:

| Hai toccato | Aggiorna |
|---|---|
| Architettura o dipendenze | `ARC.md` **e** un nuovo `DEC` |
| Schema o semantica di un dato | il `DC` relativo, con bump di versione |
| Un componente AI (modello, prompt, retrieval) | nuovo `EVR` |
| Un termine di dominio o una metrica | `GLOSSARY.md` |
| Qualcosa che rilasci | `REL` **e** `RLM` |
| Un rischio, o ne hai introdotto uno | `RSK.md §stato` |

## Definition of Done

Un lavoro è finito quando: il `CHG` è `verified` · gli artefatti della tabella sopra sono
aggiornati · `python skills/framework-audit/scripts/validate.py` passa senza errori.

## Comandi

```bash
# TODO: compila con i comandi reali del progetto
make dev
make test
python skills/framework-audit/scripts/validate.py
```

## Dati sensibili

- Non inserire dati reali di clienti negli esempi dei documenti né nei dataset di
  valutazione committati.
- I campi PII sono marcati nei `DC` con `pii: true`. Non replicarli in log, esempi o
  fixture.
- Se un task richiede accesso a dati produttivi, fermati e chiedi.

## Escalation — fermati e chiedi

Decisione presente in `OPEN.md` · nessun `CHG` approvato copre il lavoro richiesto ·
il lavoro richiederebbe di modificare un `immutable` · le soglie di un `EVP` andrebbero
abbassate per passare il gate · un `DC` andrebbe rotto senza preavviso ai consumatori.
