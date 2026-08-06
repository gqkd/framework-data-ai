---
schema: framework/roadmap/v1
artifact_type: roadmap
lifecycle: living
status: active
version: 1.0.0
products: [prodotto-a]
owners: [NOME]
created: AAAA-MM-GG
last_review: AAAA-MM-GG HH:MM
classification: internal
---

# Progressive implementation roadmap — Nome prodotto

**Domanda:** quali incrementi futuri ipotizziamo, e da quali evidenze dipendono?

**Non confondere con `IMP`.** Questo documento guarda avanti, è vivente e i suoi incrementi
sono un **input** al change intake. `IMP` guarda il ciclo corrente, viene sostituito ogni
ciclo, ed è un **output** del reshaping. Tenerli separati è ciò che evita di riscrivere il
piano ogni volta che il reshaping cambia lo scope.

## Incrementi

Ogni incremento ha uno **stato di maturità**, che è la parte utile del documento:

| Stato | Significato |
|---|---|
| `committed` | Deciso, con `DEC`. Entrerà in un `CHG`. |
| `shaped` | Definito abbastanza per essere stimato, non ancora deciso |
| `conditional` | Dipende da un'evidenza che non abbiamo ancora |

### INC-NNN · Titolo

| Campo | Contenuto |
|---|---|
| Stato | committed · shaped · conditional |
| Outcome atteso | quale outcome del `PBR` muove |
| Dipende da | evidenze, altri incrementi, `OD` di `OPEN.md` |
| Architecture enabler | cosa deve esistere prima, con rimando a `DEC` |
| Entry criteria | quando può iniziare |
| Exit criteria | quando è finito |
| Prodotti coinvolti | se tocca più di uno, richiede un `DEC` con `scope: platform` |

## §Non in roadmap

Cosa abbiamo deciso di non fare, con la ragione. Evita di rispiegare la stessa scelta ogni
mese e dice a un agente che l'assenza è deliberata.

---

## Anti-pattern

- **Trattarla come un piano con date.** Un incremento `conditional` con una data è una
  bugia: la data implica una certezza che lo stato nega.
- **Tutti gli incrementi `committed`.** Significa che non stai distinguendo, e la roadmap
  torna a essere una lista dei desideri ordinata.
- **Nessuna dipendenza da evidenze.** Se nessun incremento dipende da qualcosa che devi
  ancora scoprire, non stai facendo un progetto data: stai eseguendo un ordine.
- **Confonderla con `IMP`.** Il sintomo: la roadmap contiene assegnazioni e sequenze di
  lavoro.
