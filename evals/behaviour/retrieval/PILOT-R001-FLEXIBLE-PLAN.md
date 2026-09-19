# Pilota R001 con letture flessibili — preregistrazione

2026-09-14. Richiesta utente: «ok va avanti con i test», dopo la spiegazione
delle verifiche mancanti. Ogni aggiornamento riporta percentuale e denominatore.

## Perimetro prima delle chiamate

Una coppia A/B, ordine A poi B, per qualificare il metodo di lettura flessibile.
Non e' una nuova domanda: copertura del dataset ancora 1/24 (4,2%), gruppo
development 1/8 (12,5%). Avanzamento delle nuove invocazioni inizialmente 0/2.

- A: 3.6.3, db75f310e2f42453cb0fe1b26573c3f6b5736790.
- B: 3.8.1, faaf42259c7b43dfecbd1c52df21b2c4788cfc50.
- Modello richiesto gpt-5.6-sol, reasoning high; CLI 0.150.1 invariata.
- Stesso corpus e stessa rubrica R001 confermata; preparazione
  /tmp/framework-retrieval-v1-final-20260912.
- Revisione: /tmp/framework-retrieval-r001-human-review-20260913.json.
- Preflight senza modello in /tmp/framework-retrieval-r001-flexible-preflight-20260914.
- Coppia reale in /tmp/framework-retrieval-r001-flexible-20260914-01.
- Sessioni e copie fresche, nessun grafo precaricato o arricchimento di mapping.
- --no-timeout: nessun tetto token, monetario o di durata del runner per le prove.
  I probe tecnici hanno scadenze proprie. Restano i limiti del fornitore.
- Nessun acquisto o reset di quota da parte dell'agente. Nessun retry automatico
  della prova: errore d'infrastruttura o mutazione ferma il blocco. Le normali
  riletture dentro la prova restano una scelta dell'agente e vengono contabilizzate.

La sola condizione nuova e' descritta in FLEXIBLE-READER.md: letture strumentate
integrali o per intervalli, con istruzione esplicita di recuperare output mancanti.
Non la chiameremo una sessione IDE ordinaria, ne' una modifica del framework.

## Gate e osservazioni

Prima del modello: nuovi test offline, gate completo del framework, hash v1
invariati, diagnosi delle catture storiche e preflight A/B con gli stessi confini.
I 17 nuovi test mirati sono passati prima di questa preregistrazione; il gate
completo e il preflight devono ancora terminare o essere eseguiti.

Per ciascun braccio: risposta integrale, gruppi di fonti osservati, output
vuoti/troncati/verificati, numero e intervalli delle letture, token input/cache/
output/reasoning, durata del processo, inventari e hash. Non assegnare successo
semantico dalla copertura: la revisione indipendente delle risposte resta pendente.

## Interpretazione preregistrata

Questo e' un pilota di qualificazione, non una prova causale del risparmio.
Le serie v1 precedenti sono storiche: cache, finestre temporali e percorsi non
sono controllati. Anche il prompt del lettore cambia nelle istruzioni dichiarate.
La granularita' effettiva puo' ancora dipendere dai limiti di output della CLI.

Un output vuoto o troncato non si accredita e non dimostra da solo che il modello
non abbia ricevuto il testo. Non si eliminano prove in funzione del costo o della
qualita', non si cambiano le rubriche e non si sommano queste due chiamate alle
cinque coppie v1 per calcolare una mediana favorevole.

Se il pilota e' utilizzabile, il passo seguente e' una campagna distinta e
controbilanciata dei metodi di lettura, poi le altre domande development dopo
revisione delle loro rubriche. Le sedici evaluation restano riservate.
