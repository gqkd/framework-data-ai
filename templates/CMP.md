---
schema: framework/competitor-comparison/v1
artifact_type: competitor-comparison
lifecycle: immutable
status: active
id: CMP-NNN
products: [prodotto-a]
owners: [NOME]
created: AAAA-MM-GG
derives_from: [HYP-NNN]
classification: internal
---

# CMP-NNN · Comparativa · build, buy o adatta

**Domanda:** costruiamo, compriamo o adattiamo?

**Nota sulla classe:** immutabile e datato. Il mercato cambia: una comparativa di due anni
fa si rifà, non si ritocca.

## Criteri, definiti prima di guardare le opzioni

| # | Criterio | Peso | Soglia minima accettabile |
|---|---|---|---|
| 1 | | | |

**Definirli prima è l'intero valore del documento.** Criteri scelti dopo aver visto le
opzioni sono razionalizzazione, e si riconoscono perché combaciano sospettosamente con i
punti di forza del vincitore.

## Opzioni

| Opzione | Copertura | Costo ingresso | Costo a regime | Lock-in | Dove stanno i dati | Effort integrazione | Maturità |
|---|---|---|---|---|---|---|---|
| Non fare nulla | | | | | | | |
| Build interno | | | | | | | |
| Fornitore A | | | | | | | |

Le righe **"non fare nulla"** e **"build interno"** sono obbligatorie: sono ciò che
trasforma la tabella da lista della spesa in decisione.

## Verdetto

Una riga, con il criterio che ha deciso. Rimando al `DEC`.

---

## Anti-pattern

- **Criteri definiti dopo le opzioni.** Vedi sopra.
- **Assenza della riga "build".** Senza, non hai confrontato: hai scelto un fornitore.
- **Assenza della riga "non fare nulla".** È l'opzione con cui competi davvero.
- **Copertura funzionale come unico criterio.** Il costo a regime e il lock-in decidono
  più spesso, e più tardi.
- **Non datarlo.** Una comparativa senza data verrà riusata quando non vale più.
