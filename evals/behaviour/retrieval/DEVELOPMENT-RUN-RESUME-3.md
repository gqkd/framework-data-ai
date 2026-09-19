# Terza ripresa development — 15/09

Registrata prima delle nuove chiamate, dopo il nuovo «continua» dell'utente.
Restano valide le sette rubriche confermate e le condizioni del piano iniziale.
Non e' un retry automatico: la precedente esecuzione si era fermata per quota.

## Esito della seconda ripresa

/tmp/framework-retrieval-development-flexible-20260915-02:
R004 A/B e R019 B/A complete; R013-B completa aggiuntiva; R013-A interrotta
per quota dopo 22,496 secondi, usage sconosciuta; R010 A/B mai invocate.
Nessuna mutazione. Cinque catture complete su sei tentativi.
R019-A ha 5/6 gruppi: l'output reader di consumer-tests e' vuoto,
nonostante la risposta nomini i test e li esegua con successo.
Il candidato ha 6/6. Non convertire questa differenza in un effetto del grafo.

Le coppie selezionate finora sono R016 (primo batch), R022 e R007
(prima ripresa), R004 e R019 (seconda ripresa): cinque su sette.
R022-A originaria e R013-B della seconda ripresa restano aggiuntive.
Tre errori di quota rimangono nel conteggio, con consumo sconosciuto.

## Nuovo batch

Output assente da verificare prima dell'avvio:
/tmp/framework-retrieval-development-flexible-20260915-03.

Quattro chiamate, calendario congelato: R013 B/A, R010 A/B.
R013 viene ripetuta come coppia su copie nuove nello stesso blocco temporale;
il precedente B non viene scartato. R010 e' la prima esecuzione.

Stesso corpus e runtime A/B, stessi runner qualificati da ricontrollare,
gpt-5.6-sol/high richiesto, CLI 0.150.1, --no-timeout, nessun tetto token,
nessun provider/installazione/reset/acquisto, nessuna modifica al framework.
Preflight per prova, stop al primo errore, nessun ulteriore retry automatico.
La lettura delle quote non dichiara blocchi; non garantisce la fine del batch.

## Denominatori

Prima: 5/7 coppie nuove (71,4%), copertura A/B 6/24 (25%),
development 6/8 (75%). Nuovo batch 0/4.
Se completo: 7/7 nuove coppie, copertura 8/24 (33,3%), development 8/8.
Quattro batch development: 19 tentativi, 16 risposte complete, di cui
14 accoppiate e 2 aggiuntive; 3 errori con consumo sconosciuto.
La revisione indipendente delle risposte resta pendente.

Il confronto isolato del grafo e' un esperimento diverso, descritto in
GRAPH-ATTRIBUTION-PLAN.md; queste quattro chiamate non lo eseguono.
