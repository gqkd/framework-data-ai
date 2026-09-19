# Seconda ripresa esplicita del blocco R001

2026-09-14, dopo la nuova richiesta utente «continua» e il controllo delle
quote delle 11:20 UTC. Integra il piano e la prima ripresa, senza riscriverli.

## Stato osservato prima delle nuove invocazioni

- Coppie 1 e 2, e coppia 3 in 03-retry1: sei catture pending-review.
- Coppia 4 originaria, A: pending-review, 178.889 s, 471845 token, 2/2 fonti.
- Coppia 4 originaria, B: unavailable dopo 80.578 s. Lo stream contiene error
  e turn.failed per limite d'uso; manca la usage terminale, consumo unknown.
- Coppia 5: non preparata. Nessun processo del benchmark osservato attivo.
- Il blocco si e' fermato al fallimento, senza retry automatico.
- Le quote risultano nuovamente disponibili. Nessun credito acquistato o reset consumato.

## Ripresa preregistrata

Il runner congelato seleziona coppie complete, rifiuta il resume e richiede copie
nuove. Non viene modificato per selezionare il solo B. Si eseguono quattro chiamate:

| Coppia globale | Ordine | Directory sotto /tmp/ |
|---|---|---|
| 4, nuovo tentativo | A, B | framework-retrieval-r001-repeat-20260914-04-retry1 |
| 5 | B, A | framework-retrieval-r001-repeat-20260914-05 |

La nuova coppia 4 costituisce l'osservazione accoppiata; il precedente A completo
resta un'osservazione aggiuntiva separata, con risposta e consumo nel registro.
La separazione dipende dall'interruzione del B, non dal costo o dalla risposta di A.
Le coppie 1-3 non vengono ripetute. Le directory originarie restano intatte.

Se tutte le chiamate terminano, il registro conterra' 13 tentativi:
10 catture delle cinque coppie, 1 A completo della coppia interrotta,
2 fallimenti per quota con consumo sconosciuto. Il subtotale gia' osservato
prima di questa ripresa e' 6214898 token; non comprende il pilota precedente
o il consumo dell'agente valutatore, ne' sostituisce con zero i due unknown.

Modello richiesto gpt-5.6-sol/high, CLI 0.150.1, no-timeout e ogni altro
parametro restano quelli del piano. I cinque hash degli input del runner
sono stati confrontati con run.json della coppia 4: identici.
Un nuovo fallimento interrompe il blocco, senza retry automatici.

I risultati accoppiati saranno distinti in tre blocchi temporali:
coppie 1-2 prima della prima pausa, coppia 3 fra le pause, coppie 4-5 dopo
la seconda pausa. L'A aggiuntivo appartiene al blocco intermedio.
La cache del fornitore resta non controllata. Le pause non sono tempo di
risposta della prova, ma impediscono di presentare la campagna come continua.
