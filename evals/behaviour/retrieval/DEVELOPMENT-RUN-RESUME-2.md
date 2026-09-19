# Seconda ripresa development — 15/09

## Provenienza della registrazione

L'utente ha chiesto: «vai avanti, quanto manca per capire se il grafo migliora o no
l'attuale framework?». Le quattro coppie residue sono state annunciate prima
dell'avvio. Il primo tentativo di salvare questo piano con apply_patch e' fallito
per un errore di sintassi PowerShell; il comando successivo ha comunque avviato
il runner. Questo file viene pertanto salvato **dopo l'avvio**, non e' una
preregistrazione persistita prima delle chiamate. Il piano e gli argomenti
erano presenti nell'invocazione precedente al lancio. Nessuna selezione e'
stata modificata sulla base delle risposte.

## Stato precedente e selezione

Il primo batch ha completato R016-B/A e un R022-A aggiuntivo, poi e' fallito
su R022-B per quota. La prima ripresa ha completato R022-A/B e R007-A/B,
poi e' fallita su R004-A per quota (3,341 secondi, usage sconosciuta).
R004-B e le tre coppie successive non sono state invocate in quella ripresa.

Restano selezionate le coppie R016 del primo batch, R022 e R007 della prima
ripresa. Nessuna viene ripetuta. Il vecchio R022-A resta un'osservazione
aggiuntiva; i due errori di quota restano tentativi con consumo sconosciuto.

Nuovo output: /tmp/framework-retrieval-development-flexible-20260915-02.
Otto invocazioni, calendario congelato: R004 A/B, R019 B/A, R013 B/A, R010 A/B.
Non e' una ripresa automatica e non sovrascrive i batch precedenti.

## Condizioni

Stesso corpus preparato in /tmp/framework-retrieval-v1-final-20260912,
stessi commit A/B, oracle e conferma umana delle sette rubriche.
gpt-5.6-sol/high richiesto, CLI 0.150.1, lettore flessibile v2,
--no-timeout, nessun tetto artificiale di token, stop al primo errore.
Nessun provider, reset, acquisto, modifica ai runtime o retry automatico.
Gli otto script del runner sono stati confrontati con gli hash qualificati
prima dell'avvio; tutti corrispondono. La directory nuova era assente.

Prima del batch: 3/7 coppie nuove complete (42,9%), copertura complessiva
4/24 domande (16,7%), development 4/8 (50%). Se tutte le otto chiamate
terminano: 7/7 nuove coppie, 8/24 domande, 8/8 development. Revisione
indipendente delle risposte ancora da fare, non inclusa nella percentuale.

## Il test del grafo e' separato

Queste otto prove completano il confronto tra versioni; non introducono
un invito all'uso del motore, mapping aggiuntivi o un provider.
L'assenza di invocazioni del motore nelle prove precedenti impedisce di
attribuire al grafo differenze di qualita', token o tempo.
Il confronto isolato sullo stesso runtime va progettato separatamente.
