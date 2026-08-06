---
name: framework-audit
description: Valida e mantiene il framework di documentazione Data & AI di un repository. Usa questa skill ogni volta che l'utente chiede di controllare, validare, verificare o mettere in ordine la documentazione del progetto; prima di un commit, di una release o di chiudere un ciclo; quando chiede se i documenti sono aggiornati o coerenti, se ci sono documenti obsoleti, se la tracciabilità è intatta, o se i tre prodotti sono ancora allineati; quando chiede di rigenerare gli indici delle decisioni o di tracciabilità; e quando chiede di impostare i controlli automatici in CI. Attivala anche se l'utente non nomina il framework ma parla di "controllare i documenti", "vedere se manca qualcosa", "fare pulizia nella documentazione" o "sistemare gli ADR".
---

# Framework audit

Valida il framework descritto in `FRAMEWORK.md` e rigenera ciò che va generato invece che
scritto a mano.

## Principio di funzionamento

I controlli deterministici stanno in `scripts/validate.py`, non in queste istruzioni. Una
sola implementazione, due punti di ingresso: questa skill lo esegue in interattivo e
interpreta i risultati; la CI lo esegue su ogni push e blocca il merge sugli errori.
Duplicare la logica qui la farebbe divergere dalla versione che gira in CI, che è la
versione che conta.

Il tuo lavoro non è controllare: è **interpretare e correggere**. Il controllo lo fa lo
script.

## Procedura

1. Esegui il validatore dalla radice del repository:

   ```bash
   python <skill>/scripts/validate.py --root . --emit-index
   ```

   Usa `--json` se devi elaborare i risultati programmaticamente, `--stale-days N` se il
   progetto ha una cadenza di revisione diversa dai 90 giorni di default.

2. Leggi i risultati e raggruppali per **causa**, non per file. Venti errori `FM002` su
   venti file sono un problema (un template compilato male), non venti.

3. Correggi gli **errori**. Sono violazioni meccaniche dello schema e si sistemano senza
   giudizio: campi mancanti, `lifecycle` sbagliato per il tipo, `status` fuori
   enumerazione, riferimenti pendenti, sezioni obbligatorie assenti.

4. Sugli **avvisi** applica giudizio e riporta all'utente. Non correggerli d'ufficio:
   quasi tutti richiedono di sapere qualcosa che non è nel repository.

5. Rileggi gli indici rigenerati (`decisions/INDEX.md`, `TRACEABILITY.md`) e verifica che
   il grafo abbia senso. Un `CHG` che non deriva da niente e un `EVR` che non è citato da
   nessuna release sono buchi di tracciabilità che lo script non può classificare come
   errori, ma che tu puoi notare.

6. Chiudi con un riassunto in tre righe: cosa hai corretto, cosa richiede una decisione
   dell'utente, cosa hai lasciato consapevolmente.

## Come interpretare i codici

| Codice | Significato | Come si corregge |
|---|---|---|
| `FM001` `FM002` | Front-matter assente, non valido o incompleto | Aggiungi i campi dal template corrispondente in `templates/` |
| `FM005` | `lifecycle` incoerente col tipo di artefatto | Non cambiare il tipo per far passare il controllo: la classe è una proprietà dell'artefatto, non un'etichetta |
| `FM007` | `scope` non valido su un `DEC-ADR` | `product`, `architecture` o `platform`. Se non sai quale, chiedi: la distinzione cambia chi deve approvare |
| `SEC001` | Sezione obbligatoria assente | Sono le sezioni che rendono utile il documento: `Cosa NON deve cambiare` di un `CHG`, `§delta` di un `WF`. Aggiungi la sezione **e il contenuto**, non solo il titolo |
| `REF001` `REF002` | Riferimento pendente | O l'artefatto citato non è mai stato scritto, o l'ID è sbagliato. Verifica quale prima di intervenire |
| `REF003` | Un artefatto è stato superato ma non marcato | Porta il vecchio a `status: superseded` |
| `LC002` | Documento vivente obsoleto | **Leggi il documento e verifica che corrisponda alla realtà, poi aggiorna `last_review`.** Vedi sotto |
| `LC004` | `last_review` presente ma non è un istante | Placeholder mai compilato, o data compilata e ora ancora `HH:MM`. Il formato è `AAAA-MM-GG` oppure `AAAA-MM-GG HH:MM`. Non è un errore bloccante perché il documento potrebbe essere appena nato, ma finché resta così non risulta mai rivisto |
| `CHG001` `CHG002` | Change che dichiara un impatto senza l'artefatto che ne deriva | Manca un `EVR` o un `DEC`. Non è formalità: è la traccia che spiega perché il sistema è cambiato |
| `RLM001` `RLM002` | Rollback non definito o non testato | Se non è testato dillo all'utente: è la differenza fra un piano e un'intenzione |
| `XP001` `XP003` | Incoerenza fra i prodotti | Glossario duplicato o prodotto senza `PBR`: sono i due modi in cui una suite complementare si sfalda |
| `OD002` | Decisione ancora aperta ma già chiusa da un `DEC` | Sposta la voce in `OPEN.md §4` con un rimando |

## L'unica correzione che non devi mai fare

**Non aggiornare `last_review` senza avere letto il documento.** È l'azione più veloce per
far tornare verde il validatore e l'unica che rende inutile l'intero framework: un
documento vivente con una data recente e un contenuto vecchio è peggio di un documento
assente, perché chi legge — persona o agente — lo tratta come vero.

Se non sei in grado di verificare che il documento corrisponda alla realtà, lascia
l'avviso e dillo all'utente. Un avviso onesto vale più di un verde falso.

Vale un principio analogo per `EVP`: se un `RG` non passa, non abbassare le soglie.
Cambiare una soglia è una decisione di prodotto e richiede un `DEC` con il motivo.

## Impostare la CI

Quando l'utente lo chiede, genera il workflow. Gli errori bloccano, gli avvisi no:

```yaml
name: framework
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install pyyaml
      - run: python skills/framework-audit/scripts/validate.py --root . --emit-index
      - name: Indici non aggiornati
        run: git diff --exit-code decisions/INDEX.md TRACEABILITY.md
```

**Aggiungi i controlli uno per volta, quando il fallimento che prevengono è già accaduto
una volta.** Dodici controlli attivati prima che esista il codice sono una fabbrica
costruita prima del prodotto: rallentano senza aver ancora prevenuto niente, e la reazione
prevedibile è disattivarli tutti.

## Aggiungere un nuovo controllo

Modifica `scripts/validate.py`, non queste istruzioni. Un controllo nuovo ha bisogno di:
un codice (`AREA###`), un livello (`ERROR` solo se è meccanicamente verificabile e sempre
sbagliato), e un messaggio che spieghi **perché** importa. Un messaggio che dice solo cosa
è sbagliato viene aggirato; uno che spiega la conseguenza viene corretto.

Aggiungi il tipo nuovo al dizionario `SCHEMAS` se stai introducendo un artefatto: è
l'unico punto da toccare.
