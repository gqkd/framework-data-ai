# Ripetizioni R001 — piano registrato prima dell'esecuzione

Data: 2026-09-14. Autorizzazione utente: «ok vai avanti con i test», dopo
la richiesta esplicita di misurare durata e consumo senza imporre un limite.

## Perimetro di questo blocco

Cinque nuove coppie R001, una sola domanda development, dieci invocazioni
sequenziali. Il pilota del 13/09 resta separato: non è una delle cinque coppie.
Non si selezionano o eliminano esecuzioni in funzione della risposta o del costo.
Nessun retry automatico: un problema d'infrastruttura ferma il blocco e lascia
le prove residue non eseguite, con consumi osservati o esplicitamente sconosciuti.

| Coppia | Ordine | Directory sotto /tmp/ |
|---|---|---|
| 1 | B, A | framework-retrieval-r001-repeat-20260914-01 |
| 2 | A, B | framework-retrieval-r001-repeat-20260914-02 |
| 3 | B, A | framework-retrieval-r001-repeat-20260914-03 |
| 4 | A, B | framework-retrieval-r001-repeat-20260914-04 |
| 5 | B, A | framework-retrieval-r001-repeat-20260914-05 |

Il calendario originale assegna B/A a tutte le ripetizioni di R001.
L'override qui sopra è esplicito e registrato, non attribuito al calendario.
Con cinque coppie l'ordine non è perfettamente bilanciato: tre B/A, due A/B.
Ogni directory è un batch distinto con repetition: 1 interna al batch;
la coppia globale è identificata da questa tabella, non da quel numero isolato.

## Parametri fissi

- A: framework 3.6.3, db75f310e2f42453cb0fe1b26573c3f6b5736790.
- B: framework 3.8.1, faaf42259c7b43dfecbd1c52df21b2c4788cfc50.
- Modello richiesto gpt-5.6-sol, reasoning high; CLI 0.150.1.
- Preparazione originale: /tmp/framework-retrieval-v1-final-20260912.
- Attestazione della rubrica R001: /tmp/framework-retrieval-r001-human-review-20260913.json.
- Prompt, reader da 40 righe/4000 byte, corpus, oracle e requisiti invariati.
- Sessione e worktree freschi; cache del fornitore non azzerata né presunta fredda.
- Nessun tetto token, monetario o timeout della prova; --no-timeout.
- Stesso sandbox, rete dei comandi negata, sole fonti sintetiche e runtime.
- Nessun context pack precaricato, provider aggiunto o installazione.
- La rubrica confermata non costituisce valutazione delle risposte.

Le sole estensioni del runner sono durata libera e override d'ordine,
con test automatici prima del blocco. I loro hash entrano in ogni run.json.

## Cosa osservare e riportare

Per ogni esecuzione: esito della cattura, gruppi di fonti coperti, tempo,
input non in cache/in cache, output e reasoning, pagine framework/progetto,
comandi e letture delle skill. Usare mediana e intervallo min–max per braccio
e differenze entro coppia. Non chiamare successo semantico il solo retrieval.

Leggere le risposte per una prima analisi dichiarata dell'autore; la revisione
indipendente resta necessaria. Non alterare i risultati del runner per dare un voto.
Conteggiare anche tentativi falliti; separare il consumo di questo blocco
da quello storico e dal lavoro dell'agente valutatore.

## Passi distinti successivi

Il confronto con letture ordinarie è un esperimento diverso, ancora da
qualificare. Non si cambiano strumenti a metà di questo blocco.
Le altre domande development richiedono revisione delle proprie rubriche:
la conferma R001 non le approva. Le sedici evaluation restano riservate.
Le sessioni con domande successive, dopo la lettura iniziale delle istruzioni,
costituiscono un'ulteriore condizione, non sono mischiate alle sessioni nuove.
