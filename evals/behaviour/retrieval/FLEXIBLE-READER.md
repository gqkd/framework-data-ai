# Esperimento di lettura flessibile — v2

Condizione separata dal runner v1, che resta byte-identico. Il corpus e le
rubriche non cambiano. Non e' un rilascio del runtime del framework.

## Cosa cambia

Il reader restituisce per default il file intero. L'agente puo' scegliere
--start N --end M, con estremi inclusivi; omettere --end legge fino alla fine.
Un end oltre EOF viene limitato all'ultima riga disponibile. Non esistono
pagine forzate di 40 righe/4000 byte. Restano i confini di percorso e il limite
di sicurezza di 2 MB per file del reader v1: non sono un budget token del modello.

Il testo e' ancora dentro frame verificabili: **non sono letture IDE ordinarie
inalterate**. Questa condizione isola meglio la granularita' del reader, ma il
formato dei frame, il bootstrap e i limiti di output del client restano fattori.
Non si accorpano documenti o saltano obblighi di lettura per migliorare un numero.

Il prompt differisce solo nel paragrafo sulle letture: file intero/intervalli
e gestione esplicita di output vuoti o troncati. Non suggerisce fonti o risposte.
Quest'ultima istruzione e' anch'essa una differenza dichiarata: il confronto non
isola causalmente il solo numero massimo di righe.

## Componenti e confini

- run_flexible.py riusa la preparazione riproducibile e l'esecuzione isolata di
  run.py. Sulle copie nuove modifica soltanto tools e prompt, prima dei probe,
  e registra modalita', policy, hash e inventari aggiornati. Controlla che
  progetto e runtime non siano cambiati durante la costruzione.
- read_source_flexible.py viene esposto come tools/read_source.py; riusa il
  reader originale come tools/read_source_v1.py per percorsi sicuri e frame.
- metrics.py resta invariato: accredita solo frame completi con testo, hash
  e intervalli corrispondenti alle fonti. Un output troncato non diventa credito.
- diagnose_reads.py aggiunge reading-diagnostics.json fuori dalle fonti.
  Distingue output vuoto, assente, fallito, non riconosciuto, non verificabile
  o troncato, parzialmente verificato e verificato. Non riscrive result.json
  e non assegna voti o credito retroattivo.

La diagnostica copre solo comandi riconosciuti del reader. Non prova che ogni
lettura possibile sia osservata o che il testo sia stato consegnato al modello.
source_output_status riguarda gli output dei comandi, non la comprensione,
la copertura di tutte le fonti necessarie o il rispetto integrale delle istruzioni.

Gli hash degli otto script coinvolti entrano nel manifest del nuovo run.
Le copie esistenti e i report v1 restano intatti. Nessun monkey patch delle
funzioni del runner, nessun bypass di revisione, inventario o preflight.

## Uso

Da Linux/WSL, con l'ambiente Python esistente:

~~~bash
python -B evals/behaviour/retrieval/run_flexible.py \
  --from-prepared /tmp/framework-retrieval-v1-final-20260912 \
  --output /tmp/retrieval-flexible-preflight-NEW \
  --question R001 --pair-order AB --preflight-only \
  --codex /percorso/codex --sandbox-helper /percorso/binario-nativo/codex
~~~

Per eseguire, usare un'altra directory nuova, --execute al posto di
--preflight-only, modello/reasoning espliciti, --oracle-review e --no-timeout.
La rubrica deve coprire le domande scelte e la preparazione esatta. Il default
senza questi flag prepara soltanto: non chiama modelli. Nessun resume.

Per ispezionare una traccia senza modificarla:

~~~bash
python -B evals/behaviour/retrieval/diagnose_reads.py --trial /tmp/.../trials/R001-1-A
~~~

Restano le medesime restrizioni: fonti/runtime non scrivibili, scratch dedicato,
rete dei comandi negata, niente evaluator o altre prove, niente plugin personali,
memorie globali, subagenti, provider o installazioni. Il client usa inferenza
remota con autenticazione esistente: locale non significa offline.

Nessuna nuova dipendenza. OpenAI Docs ha guidato la verifica dello stream CLI;
le anomalie specifiche sono evidenze locali, non garanzie dedotte dalla documentazione.
[Riferimento ufficiale](https://learn.chatgpt.com/docs/non-interactive-mode).
