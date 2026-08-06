---
schema: framework/glossary/v1
artifact_type: glossary
lifecycle: living
status: active
products: [prodotto-a, prodotto-b, prodotto-c]
owners: [NOME]
created: AAAA-MM-GG
last_review: AAAA-MM-GG HH:MM
classification: internal
---

# Glossario e dizionario metriche

**Unico per tutti i prodotti.** È il file dove la complementarità dei tre prodotti si
definisce o si perde: se lo stesso concetto ha due nomi in due prodotti, o lo stesso nome
significa due cose, la complementarità è già rotta e nessuno se ne è accorto.

**È normativo, non descrittivo.** Non registra come i termini vengono usati: stabilisce
come vanno usati. Modificarne una voce richiede un `DEC`.

## §Termini di dominio

### Nome del termine

- **Definizione:** una frase, senza usare il termine stesso.
- **Non include:** i casi che qualcuno assumerebbe inclusi e non lo sono. Campo
  obbligatorio: è dove sta il valore.
- **Sinonimi vietati:** altri modi in cui viene chiamato e che non vanno usati.
- **Usato in:** prodotti e artefatti.
- **Owner della definizione:** chi decide se cambia.

## §Metriche

### Nome della metrica

- **Definizione in parole:** cosa misura e perché a qualcuno importa.
- **Formula:** esplicita, con numeratore e denominatore.
- **Fonte:** tabella o `DC` di riferimento.
- **Finestra temporale:** giorni, mese di calendario, rolling.
- **Esclusioni:** account di test, resi, cancellazioni, utenti interni.
- **Non confondere con:** la metrica simile da cui va distinta.
- **Owner della definizione:**
- **Prodotti che la calcolano:** se più di uno, **devono usare questa formula**. Se non
  possono, sono due metriche diverse e servono due voci con due nomi diversi.

---

## Anti-pattern

- **Definire un termine usando il termine.** "Cliente attivo: un cliente che è attivo."
  Succede più spesso di quanto sembri.
- **Omettere `Non include`.** È il campo che risolve le discussioni; senza, il glossario
  è decorativo.
- **Formule diverse per la stessa metrica in prodotti diversi.** È il fallimento tipico di
  una suite complementare, e il più imbarazzante da spiegare a un cliente che confronta
  due dashboard.
- **Aggiungere una voce senza owner.** Una definizione che nessuno possiede si degrada
  alla prima discussione.
- **Trattarlo come descrittivo.** Se registri gli usi invece di stabilirli, hai scritto un
  dizionario dei disaccordi.
