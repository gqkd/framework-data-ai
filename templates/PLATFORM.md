---
schema: framework/platform-architecture/v1
artifact_type: platform-architecture
lifecycle: living
status: draft
version: 0.1.0
products: [prodotto-a, prodotto-b, prodotto-c]
owners: [NOME]
created: AAAA-MM-GG
last_review: AAAA-MM-GG HH:MM
classification: internal
---

# Architettura del substrato condiviso

**Domanda:** cosa è comune ai tre prodotti, e con quali garanzie ciascuno può contarci?

**Perché esiste.** Tre prodotti costruiti da una persona sola non hanno il problema di
tre team: hanno il problema della superficie di manutenzione. Questo documento è la
risposta — un substrato descritto una volta, più un `ARC` breve per prodotto che ne
dichiara solo il **delta**. Senza, ogni `ARC` ridescrive identità, deploy e osservabilità,
le tre descrizioni divergono, e la divergenza si scopre al primo refactor.

**Nasce al giorno uno**, anche solo con le sezioni vuote e le decisioni rinviate a
`OPEN.md`. È diverso da `ARC`, che nasce in F5 con la prima riga di codice: qui le sezioni
vuote sono informazione, perché dicono cosa non è ancora deciso.

> Il perimetro esatto è la decisione aperta `OD-002`. Finché è aperta, questo documento
> elenca i candidati e non li dà per assegnati.

## Perimetro

Cosa è piattaforma e cosa non lo è. La riga di confine è una sola:

> Se cambia perché cambia il business di **un** prodotto, non è piattaforma.

| Componente | Piattaforma | Ragione | `DEC` |
|---|---|---|---|
| Identità e autorizzazione | sì / no / da decidere | | |
| Accesso ai dati e migrazioni | | | |
| Deploy e infrastruttura | | | |
| Osservabilità e logging | | | |
| Convenzioni di API e di errore | | | |
| Layer di valutazione AI | | | |
| Logica di dominio | **no** | cambia con il business di un prodotto | |

## Componenti

Uno per riga: cosa fa, cosa garantisce a chi lo usa, dove sta il codice.

| Componente | Garanzia offerta | Percorso | Stato |
|---|---|---|---|
| | | | live · in-build · shaped |

## Contratti verso i prodotti

Cosa un prodotto può assumere. **Ogni riga è un impegno**: romperla rompe tre prodotti
insieme, ed è la ragione per cui i data contract interni vengono prima di quelli esterni.

| Contratto | Consumatori | `DC` | Come si rompe |
|---|---|---|---|
| | | | |

## Modello di tenancy e identità

La decisione più costosa da invertire dell'intero progetto: tocca schema,
autorizzazione, fatturazione e migrazione dati. Se è ancora aperta, scrivi qui il rimando
a `OD-003` e **il default in uso**, non una descrizione di come potrebbe essere.

## Vincoli che la piattaforma impone

Cosa un prodotto **non** può fare per il fatto di starci sopra. Un vincolo non scritto
viene scoperto violandolo.

## Separabilità

I tre prodotti sono vendibili singolarmente. Per ciascuno: cosa serve per farlo girare da
solo, e cosa oggi glielo impedisce.

| Prodotto | Gira da solo | Cosa lo lega agli altri |
|---|---|---|
| | sì / no | |

Questa sezione è il presidio contro `OD-004`: in assenza di decisione il default di fatto
diventa il database condiviso, che rende i prodotti inseparabili senza che nessuno
l'abbia deciso.

## Decisioni che vincolano tutti e tre

Solo rimandi ai `DEC` con `scope: platform`. Generato da `validate.py --emit-index`.

---

## Anti-pattern

- **Descrivere la piattaforma che vorresti.** Questo documento è vivente: descrive cosa
  esiste oggi. Il substrato immaginato appartiene a `RMP` o a una voce di `OPEN.md`.
- **Perimetro vuoto ma componenti pieni.** Significa che stai accumulando codice condiviso
  senza aver deciso cosa merita di esserlo: è così che la logica di dominio finisce nella
  piattaforma e i prodotti diventano inseparabili.
- **Ripetere qui il contenuto di un `ARC`.** La piattaforma dice cosa è comune; il delta di
  dominio sta nell'`ARC` del prodotto. Ripeterlo garantisce due versioni divergenti.
- **Sezione separabilità compilata a memoria.** «Sì, gira da solo» va verificato provando a
  farlo partire, non ragionandoci. Finché non l'hai provato il valore è "non verificato".
- **Contratti verso i prodotti senza la colonna "come si rompe".** Un contratto di cui non
  sai come si rompe non è un contratto, è una speranza.
