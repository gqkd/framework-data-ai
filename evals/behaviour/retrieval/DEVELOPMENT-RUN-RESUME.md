# Ripresa development — 15/09, prima delle nuove chiamate

L'utente ha chiesto «continua» dopo lo stop del 14/09. Questa e' una ripresa
esplicita, non un retry automatico. Resta il [piano iniziale](DEVELOPMENT-RUN-PLAN.md)
e resta valida la conferma umana delle sette rubriche, incluso il criterio R004.

## Stato recuperato, senza sovrascritture

Batch originario: /tmp/framework-retrieval-development-flexible-20260914-01.
Si e' fermato alla quarta invocazione per quota durante R022-B.

| Prova | Stato | Secondi | Token noti |
|---|---|---:|---:|
| R016-B | cattura completa, revisione pendente | 142,629 | 429.971 |
| R016-A | cattura completa, revisione pendente | 96,566 | 208.470 |
| R022-A | cattura completa, resta aggiuntiva non accoppiata | 215,000 | 885.945 |
| R022-B | unavailable, errore esplicito di quota | 49,249 | sconosciuti |

Totale originario: 1.524.386 token noti piu' un consumo sconosciuto.
Nessuna mutazione nelle quattro prove. R016 copre 3/3 gruppi in entrambi
i bracci, R022-A 3/3. Diagnostica: un output reader vuoto in R016-A,
uno in R022-A e uno nel R022-B interrotto; nessuno in R016-B.
L'errore e' terminale e manca la usage: non stimare zero o ricostruire
un consumo dal testo disponibile.

R016 resta la prima coppia selezionata; non viene ripetuta. La coppia R022
viene rieseguita interamente su copie nuove per confrontare due sessioni
dello stesso blocco di ripresa. Il vecchio A e il B fallito restano nel
conteggio di tutti i tentativi, mai cancellati o sostituiti.

## Ripresa autorizzata

Nuova directory, assente prima dell'avvio:
 /tmp/framework-retrieval-development-flexible-20260915-01.

Dodici invocazioni: R022 A/B, R007 A/B, R004 A/B, R019 B/A, R013 B/A, R010 A/B.
Cinque coppie sono prime esecuzioni, R022 e' l'unica coppia ripetuta.
Il calendario congelato determina l'ordine, non la qualita' o il costo osservati.
Gli orari dividono la campagna in almeno due blocchi temporali: non ignorarlo
nei confronti, e non presentare una media globale come effetto causale.

Tutto il resto invariato: corpus, oracle, commit A/B, run_flexible.py,
gpt-5.6-sol/high, CLI 0.150.1 ricontrollata, --no-timeout, nessun tetto
token artificiale, nessun provider/installazione/modifica al runtime.
Controllo hash e test offline prima delle chiamate; preflight prima di ogni
prova, stop al primo errore, nessun ulteriore retry automatico.

Lettura delle quote il 15/09: nessun blocco dichiarato al momento del
controllo; non garantisce che le dodici prove possano finire. Nessun reset
riscattato, acquisto o cambio di account da parte dell'agente.
OpenAI Docs consultata per eventi/usage: non modifica l'interpretazione
dei risultati o le rubriche.

## Conteggi espliciti

Prima della ripresa: tre catture complete totali su quattro tentativi.
Per il confronto accoppiato sono utilizzabili due catture su quattordici
previste, una coppia su sette (14,3%); R022-A e' un'osservazione aggiuntiva.
Copertura A/B complessiva inclusa R001: 2/24 (8,3%), development 2/8 (25%).
R022 e' stata raggiunta in un solo braccio, non conta ancora come coppia.

Nuova ripresa inizialmente 0/12. Se termina, saranno quattordici catture
accoppiate, piu' un A aggiuntivo completo e un B fallito: sedici tentativi
complessivi del blocco development. Qualita' indipendente sempre pendente.
