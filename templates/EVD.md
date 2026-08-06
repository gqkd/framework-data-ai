---
schema: framework/evidence-brief/v1
artifact_type: evidence-brief
lifecycle: immutable
status: active
id: EVD-NNN
products: [prodotto-a]
owners: [NOME]
created: AAAA-MM-GG
derives_from: [PRB-NNN, HYP-NNN]
classification: internal
---

# EVD-NNN · Problem evidence brief

**Domanda:** che prove abbiamo che il problema esiste, e quanto è grande?

**Nota sulla classe:** immutabile e datato. Il valore delle evidenze è probatorio, non
descrittivo: non si aggiornano, si datano. Un brief ritoccato in silenzio ti fa perdere la
capacità di capire perché una decisione sembrava sensata allora.

## Metodo

Con chi abbiamo parlato o quali dati abbiamo interrogato, quando, quanti, come sono stati
selezionati. Se il campione è distorto, dirlo qui.

## Evidenze

| # | Evidenza | Fonte | Forza |
|---|---|---|---|
| 1 | | intervista / query / documento | debole · media · forte |

## Quantificazione

Frequenza, volume, costo. Se non quantificabile, dirlo e spiegare perché.

## §Evidenze contrarie

**Sezione obbligatoria.** Cosa abbiamo trovato che va nella direzione opposta, cosa non
torna, chi ha detto che il problema non esiste.

È il singolo campo che alza di più l'affidabilità del documento. Un brief che ammette cosa
non torna viene creduto; uno che va tutto nella stessa direzione viene giustamente
scontato da qualsiasi lettore esperto — e da un buon agente.

## Assunzioni di `HYP`

| Assunzione | Esito | Evidenza |
|---|---|---|
| HYP-NNN #1 | confermata / smentita / non testata | #3, #7 |

---

## Anti-pattern

- **Solo citazioni qualitative senza volumi.** "Tutti si lamentano" non è un'evidenza.
- **Sezione contraria vuota.** Non significa che non ci siano evidenze contrarie:
  significa che non le hai cercate.
- **Confondere forza e quantità.** Dieci interviste allo stesso team sono un'evidenza,
  non dieci.
- **Non collegare le evidenze alle assunzioni.** Senza quella tabella hai raccolto
  materiale, non testato un'ipotesi.
