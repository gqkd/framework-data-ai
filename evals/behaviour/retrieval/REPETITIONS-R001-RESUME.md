# Ripresa esplicita del blocco R001

2026-09-14, dopo la nuova richiesta utente «continua».
Questo documento integra il piano originario senza riscriverlo.
SHA-256 del piano originario:
66967db136a2c648bbc2b3cb93300453103f92048a6493b38511a4a07a51f760.

## Stato osservato prima della ripresa

- Coppie 1 e 2: quattro catture concluse, pending-review, 2/2 fonti richieste
  in ciascuna; nessuna mutazione osservata.
- Coppia 3, B: unavailable dopo 15.777 secondi. Lo stream termina con
  error e turn.failed per limite d'uso dell'account. Una pagina di AGENTS
  è osservata, ma manca la usage terminale: consumo unknown, non zero.
- Coppia 3, A: non invocata. Coppie 4 e 5: non preparate.
- Il blocco si è fermato automaticamente, senza retry. Nessun processo delle
  prove risultava attivo alla verifica successiva.

Il 14/09 alle 07:49 UTC il controllo account non indicava un limite raggiunto.
Non è stato consumato un credito di reset né acquistato credito.
La nuova richiesta dell'utente autorizza la ripresa; non si attribuisce questa
nuova invocazione a un retry automatico del piano iniziale.

## Ripresa registrata prima delle nuove chiamate

| Coppia globale | Ordine | Directory sotto /tmp/ |
|---|---|---|
| 3, nuovo tentativo | B, A | framework-retrieval-r001-repeat-20260914-03-retry1 |
| 4 | A, B | framework-retrieval-r001-repeat-20260914-04 |
| 5 | B, A | framework-retrieval-r001-repeat-20260914-05 |

Le prime due coppie non vengono rieseguite. Il tentativo non valido resta nella
directory originaria 03, incluso lo stato not-run del suo A.
Per arrivare a cinque coppie concluse sono previste ora sei nuove invocazioni,
undici tentativi complessivi se terminano tutte, di cui uno con consumo sconosciuto.
Un nuovo errore d'infrastruttura ferma nuovamente il blocco, senza retry automatici.

Modello richiesto gpt-5.6-sol/high, CLI 0.150.1, durata libera e parametri
del piano invariati. Tutti i cinque hash degli input del runner sono stati
confrontati con run.json del tentativo interrotto: identici.
Le destinazioni nuove sono state verificate assenti.

La pausa e il cambio di finestra di quota sono condizioni registrate, non
eliminate dai risultati. La cache del fornitore non è stata controllata:
le coppie 1–2 e 3–5 vanno anche mostrate come due blocchi temporali distinti.
Non si dichiara che il reset della finestra lasci invariata la cache.
