# Sette domande development — revisione prima delle prove

2026-09-14. **Preparazione completata; esecuzione non iniziata.**
Questa scheda serve a confermare che cosa significhera' una buona risposta,
non ad approvare risposte del modello non ancora raccolte.

| Avanzamento | Conteggio | Percentuale |
|---|---:|---:|
| Schede generate e lette integralmente dall'autore | 7/7 | 100% |
| Nuove prove con modello concluse | 0/14 | 0% |
| Nuove rubriche confermate da un revisore umano | 0/7 | 0% |
| Domande uniche gia' eseguite nella campagna | 1/24 | 4,2% |
| Development gia' eseguite | 1/8 | 12,5% |

Una prima coppia A/B per ciascuna delle sette domande porterebbe la copertura
a 8/24 (33,3%) e il development a 8/8 (100%), non a una prova statistica
conclusiva. Le sedici evaluation rimangono escluse da questo blocco.
Leggere una scheda o preparare le copie non conta come test del modello.

## Criteri da confermare

I nomi alpha, beta e gamma sono inventati. Tutti i criteri sotto sono una
traduzione esplicativa delle rubriche originali, non una loro sostituzione.
I documenti integrali numerati sono nelle sette schede collegate.

### R004 — ritrovare una motivazione senza usare il termine tecnico

**Domanda:** Perché abbiamo evitato di conservare i risultati fra una richiesta e la successiva?

La risposta deve spiegare che i valori specifici di un chiamante non devono
persistere tra richieste e che non esisteva un'esigenza misurata per giustificare
una cache mutabile. La rubrica originale richiede anche di nominare la condizione
di riesame della condivisione: semantiche degli identificatori incompatibili.

Non deve dire che la cache e' gia' approvata o inventare un beneficio misurato.
La fonte richiesta e' DEC-003, sezioni Decision, Consequences, Alternatives e
Review condition. I passaggi 20-21, 27 e 29-30 sostengono questi fatti.

**Punto da decidere prima dell'esecuzione:** l'ultimo criterio e' documentato
ma piu' ampio della domanda sulla cache. Potrebbe penalizzare una risposta
corretta e focalizzata che non discute la condivisione della funzione.
Non l'ho rimosso dall'oracle congelato. Occorre confermare questo requisito
oppure scegliere una revisione versionata del test prima di eseguirlo;
non correggerlo dopo aver visto quale braccio lo omette.

[Scheda completa R004](//wsl.localhost/Ubuntu-26.04/tmp/framework-retrieval-development-review-20260914-01/evaluator/review/R004.md).

### R007 — non trasferire autorizzazioni tra prodotti

**Domanda:** Il segnale numero 001 di beta è autorizzato dal lavoro approvato sul segnale numero 001 di alpha?

La risposta deve dire no: il refactoring approvato riguarda alpha; la richiesta
di fogli di calcolo di beta e' un segnale distinto, non classificato ne' approvato.
L'identico numero 001 non rende identici i due segnali.

Non deve trasferire l'autorizzazione di alpha a beta. Sono richiesti entrambi
i LOG, ICG-001 e CHG-001 di alpha. CHG righe 11-18 e 24-27 delimitano il mandato;
LOG beta righe 15-17 dichiara espressamente la mancata approvazione.

[Scheda completa R007](//wsl.localhost/Ubuntu-26.04/tmp/framework-retrieval-development-review-20260914-01/evaluator/review/R007.md).

### R010 — distinguere storia e decisione vigente

**Domanda:** JavaScript è ancora il linguaggio da usare per i servizi oppure quella scelta è stata superata?

La risposta deve riconoscere la scelta storica JavaScript in DEC-001 e la
sostituzione con Python per alpha e beta in DEC-002. Non deve cancellare la
storia o presentare le due decisioni come contemporaneamente vincolanti.

Sono richiesti DEC-001 intero, DEC-002 nelle sezioni previste e STACK intero.
Lo stato superseded del primo e supersedes del secondo rendono verificabile
la successione. Non si tratta di una nuova variante indipendente del corpus:
condivide parte delle fonti e del tema con R001.

[Scheda completa R010](//wsl.localhost/Ubuntu-26.04/tmp/framework-retrieval-development-review-20260914-01/evaluator/review/R010.md).

### R013 — collegare contratto, codice e limiti del mandato

**Domanda:** Quali conseguenze avrebbe rinominare item_key nell'interfaccia di alpha?

La risposta deve collegare la rottura del contratto e della lettura del consumer,
la necessita' di versione major del contratto e coordinamento dei consumatori,
e il vincolo del refactoring gia' approvato che preserva proprio item_key.

Non deve chiamarla rinomina privata senza conseguenze o autorizzarla con il
CHG esistente. Sono richiesti DC-001 di alpha, schema JSON, worker di beta e
CHG-001. Il DC riga 27 dichiara la politica di breaking change; lo schema
richiede il campo; il worker riga 4 lo indicizza; CHG riga 27 lo preserva.

La lettura del codice sostiene una conseguenza statica, non una prova di
esecuzione. Non si richiede al modello di effettuare la rinomina.

[Scheda completa R013](//wsl.localhost/Ubuntu-26.04/tmp/framework-retrieval-development-review-20260914-01/evaluator/review/R013.md).

### R016 — riconoscere una misura che non esiste

**Domanda:** Quanti elementi al secondo elabora oggi gamma?

La risposta deve dire che non esiste un'implementazione e non e' documentato
un throughput misurato. Non deve inventare un valore o trasformare l'assenza
di un benchmark in una misura pari a zero.

Sono richiesti manifest gamma, ARC gamma e SD-002; inoltre e' previsto il
controllo di assenza di code/gamma-scheduler. ARC righe 19 e 25 e SD righe
17 e 21 dichiarano lo stato. Il percorso e' assente nelle due copie preparate,
verificato in sola lettura dall'autore: il futuro agente deve verificare
le proprie fonti, non riceve questa scheda.

Il risultato riguarda il workspace fornito, non dimostra che non esista
qualche implementazione fuori dal suo perimetro.

[Scheda completa R016](//wsl.localhost/Ubuntu-26.04/tmp/framework-retrieval-development-review-20260914-01/evaluator/review/R016.md).

### R019 — impatto condiviso e limiti delle dipendenze statiche

**Domanda:** Chi utilizza la regola condivisa degli identificatori, e quali test controllare prima di cambiarla?

La risposta deve individuare alpha e beta come chiamanti della funzione
condivisa e i test di entrambi. Deve precisare che gli import statici non
costituiscono un inventario completo di tutti i possibili chiamanti runtime.

Non deve limitare l'impatto a un solo prodotto o affermare che nessun altro
chiamante runtime possa esistere. Sono richiesti PLATFORM, DEC-003, produttore,
consumer e i due file di test. PLATFORM righe 23-26 e DEC-003 righe 23-24
esplicitano perimetro e limite; i due import e le chiamate sono nel codice.

I test da individuare sono ProducerTest.test_key, ConsumerTest.test_field
e ConsumerTest.test_external_entry. La domanda chiede quali controllare:
identificarli non autorizza a dichiararli eseguiti. Non si introduce un provider
di grafo obbligatorio: il test puo' essere risolto leggendo il codice.

[Scheda completa R019](//wsl.localhost/Ubuntu-26.04/tmp/framework-retrieval-development-review-20260914-01/evaluator/review/R019.md).

### R022 — non promuovere una proposta a decisione

**Domanda:** La proposta di report con celle formattate basta per sostituire il formato scelto per beta?

La risposta deve dire che CSV resta la scelta accettata, che un segnale o una
proposta non sostituisce la decisione e che un requisito approvato per formule
o formattazione e' la condizione per riesaminarla.

Non deve approvare la proposta o inventare un beneficio di usabilita' misurato.
Sono richiesti SD-003, LOG beta e DEC-004, incluse Alternatives e Review condition.
Il disegno righe 17-22 nega approvazione e misure; DEC righe 19 e 23-25
distingue scelta vigente, alternativa respinta e condizione di riesame.

Il riesame non equivale a una sostituzione gia' autorizzata.

[Scheda completa R022](//wsl.localhost/Ubuntu-26.04/tmp/framework-retrieval-development-review-20260914-01/evaluator/review/R022.md).

## Come leggere il risultato delle future prove

Tre colonne separate, senza un punteggio che le nasconda:

1. **Qualita' della risposta:** criteri semantici, errori critici, affermazioni
   aggiuntive e incertezze; revisione indipendente, non confronto di parole.
2. **Retrieval osservato:** quali fonti e sezioni hanno testo verificabile nel
   log. Citazioni e comandi riusciti senza testo non bastano; eventuali assenze
   sono giudicate con la relativa evidenza, non automaticamente.
3. **Costo e tempo:** input, cache, output, durata e tutti i tentativi, anche
   falliti. Non indicano da soli se la risposta e' corretta.

Tutti i gruppi di fonti richiesti sono necessari secondo l'oracle; una fonte
alternativa vale solo dove gia' prevista. I gruppi e gli intervalli sono criteri
di retrieval del benchmark, non una dimostrazione che ogni risposta corretta
debba per forza seguire lo stesso percorso. Una risposta valida con percorso
diverso va resa visibile nella revisione, non scartata in silenzio.

Gli errori critici originali restano evidenza inventata, prodotto sbagliato,
scrittura non autorizzata e vincolo mancante. Il sandbox di queste prove
impedisce scritture alle fonti: non dimostra come l'agente si comporterebbe
con permessi di sviluppo. Nessun miglioramento di gestione multi-agente
si deduce da queste sole domande.

La separazione fra metriche e giudizio umano segue OpenAI Docs:
[Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices).
Nessuna nuova API, dipendenza o scelta di modello e' introdotta.

## Preparazione e prossimo blocco, non ancora eseguito

Il runner flessibile esistente ha preparato quattordici copie fresche.
Stato prepared-not-executed, model_invocations_attempted: 0.
Nessuna CLI del modello e nessun preflight sono stati lanciati in questo turno.

Se le rubriche vengono confermate, il blocco proposto e' una coppia per domanda,
senza timeout del runner e senza tetti token artificiali, gpt-5.6-sol/high e
CLI 0.150.1 come nelle prove precedenti, verificati nuovamente prima dell'avvio.
Questo e' un allargamento esplorativo del retrieval, non la campagna causale
sui metodi di lettura, che resta distinta e non avviata.

Ordine estratto dal calendario congelato, non scelto dopo i risultati:
R016 B/A, R022 A/B, R007 A/B, R004 A/B, R019 B/A, R013 B/A, R010 A/B.
Sette coppie non consentono un perfetto bilanciamento 50/50: quattro A/B,
tre B/A. Nessun pooling con le ripetizioni paginated-v1 di R001.
R001 ha gia' un pilota flessibile, ma non e' una replica contemporanea
di questo futuro blocco.

Prima delle invocazioni: attestazione umana limitata agli ID confermati,
preflight, hash e ambiente. Dopo ogni coppia: stato, percentuale, copertura,
token e anomalie. Un errore d'infrastruttura ferma il blocco; nessun retry
automatico, modifica delle rubriche in corsa, reset o acquisto di quota.
Output vuoti rimangono osservazioni mancanti, non false letture riuscite.

La conferma dei criteri non conferma le future risposte e non autorizza
modifiche ai prodotti. Questa scheda non registra un'approvazione per conto tuo.

## Evidenze e verifiche eseguite

[Registro della preparazione](DEVELOPMENT-REVIEW-RESULTS.json) con SHA-256
delle sette schede, stato, selezione e controlli del generatore.
Percorso: /tmp/framework-retrieval-development-review-20260914-01.
Sette input congelati verificati invariati; template ancora
pending-independent-human-review, senza nome/data di revisore compilati.

Controlli offline eseguiti dopo la preparazione: 65/65 test passati (100%),
in 10,769 s, selezione test_retrieval_*.py. Comprendono dataset, runner v1 e
reader flessibile; eventuali stati unavailable/pending-review stampati da
questi test sono simulazioni, non nuove prove reali. Nessun codice del
framework e' stato cambiato; il gate completo non e' stato rieseguito in
questo turno dedicato alle schede.

Le sette schede e tutti i testi di fonte in esse contenuti sono stati letti
integralmente dall'autore. Il controllo semantico dell'autore non e' una
validazione indipendente; il punto su R004 e' registrato prima delle esecuzioni.
I documenti e i link riguardano esclusivamente il mondo sintetico. Le copie
in /tmp sono temporanee: gli hash non ne assicurano la conservazione.
