# Development flessibile — esecuzione approvata del 14/09

Piano registrato prima delle nuove invocazioni. La [scheda di revisione](DEVELOPMENT-REVIEW.md)
e il [registro di preparazione](DEVELOPMENT-REVIEW-RESULTS.json) restano snapshot
della fase precedente, quando la conferma era pendente.

## Conferma e perimetro

L'utente ha risposto «si» alla domanda esplicita di confermare le sette rubriche
e il requisito aggiuntivo di R004 per avviare le quattordici prove.
Il criterio di R004 sulla condizione di riesame della condivisione resta quindi
invariato e obbligatorio nella rubrica originale. Non e' stato modificato l'oracle.

Attestazione separata: /tmp/framework-retrieval-development-human-review-20260914.json.
Registra solo R004, R007, R010, R013, R016, R019 e R022, sugli hash congelati.
Il booleano di indipendenza rappresenta la conferma dell'utente rispetto
all'autore del dataset; non attesta un audit d'identita' o come abbia letto
le fonti. La conferma non assegna voti alle future risposte, non copre holdout
e non autorizza scritture nei prodotti.

Preparazione precedente: /tmp/framework-retrieval-development-review-20260914-01.
Nuova esecuzione, directory assente prima dell'avvio:
 /tmp/framework-retrieval-development-flexible-20260914-01.

## Condizioni congelate del blocco

- A: 3.6.3, db75f310e2f42453cb0fe1b26573c3f6b5736790.
- B: 3.8.1, faaf42259c7b43dfecbd1c52df21b2c4788cfc50.
- Modello richiesto gpt-5.6-sol, reasoning high; nessuna sostituzione.
- CLI 0.150.1 ricontrollata prima del blocco; Python e runner esistenti.
- run_flexible.py, una ripetizione per domanda, quattordici prove seriali.
  Nessun nuovo adapter, provider o grafo precaricato; input e fonti invariati.
- Ordine dal calendario congelato: R016 B/A, R022 A/B, R007 A/B, R004 A/B,
  R019 B/A, R013 B/A, R010 A/B. Quattro A/B e tre B/A, non un bilanciamento perfetto.
- Copie e sessioni fresche per ogni prova. --no-timeout, nessun tetto token
  o monetario del runner; restano i limiti del fornitore e i timeout dei probe.
- Hash, attestazione e preflight verificati dal runner prima di ciascuna prova;
  stop al primo errore infrastrutturale o mutazione. Nessun retry automatico.
- Nessun acquisto, reset di quota, installazione, commit o push.

## Verifica precedente e interpretazione

Nella preparazione sono passati 65/65 test offline del retrieval in 10,769 s;
nessuno script e' stato cambiato dopo quel controllo. Il gate completo
dell'incremento reader aveva 338 test memory passati; non e' una nuova esecuzione
del gate in questo blocco.

E' un primo allargamento esplorativo a sette famiglie ulteriori del corpus
condiviso, non una dimostrazione statistica di risparmio. Non sostituisce
la campagna causale sui metodi di lettura. Non aggregare alla serie v1
o trattare R001 come replica contemporanea.

Per ciascuna coppia si conserva ogni tentativo e si riporta avanzamento,
consumo/durata, copertura nel log, anomalie e risposta. Output vuoti o frame
non verificabili non ricevono credito; lo stream non attesta il payload del
modello. La diagnostica delle letture viene emessa dopo la conclusione o lo
stop del blocco dal wrapper invariato. Durante l'esecuzione si osservano
soltanto tracce gia' scritte, senza guidare l'agente sotto test.

Qualita' della risposta, retrieval osservato e costo restano distinti.
Assenze, eventuali confronti Git e claim aggiuntivi richiedono revisione;
le risposte rimangono pending-independent-review. Nessuna soglia abbassata
o rubrica corretta in base ai risultati.

## Avanzamento iniziale

- Rubriche del nuovo blocco confermate: 7/7 (100%).
- Nuove catture completate: 0/14 (0%).
- Copertura precedente: 1/24 (4,2%); development 1/8 (12,5%).
- Obiettivo di copertura dopo il blocco: 8/24 (33,3%), development 8/8 (100%).
  Domanda con un solo braccio catturato va segnalata come coppia incompleta.

OpenAI Docs ha guidato la verifica dei permessi e dello stream CLI, non il
giudizio sulle risposte. [Fonte ufficiale](https://learn.chatgpt.com/docs/non-interactive-mode).
