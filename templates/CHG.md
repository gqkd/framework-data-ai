---
schema: framework/change-contract/v1
artifact_type: change-contract
lifecycle: immutable
status: draft
id: CHG-NNN
products: [prodotto-a]
owners: [NOME]
approvers: [NOME]
created: AAAA-MM-GG
derives_from: [SIG-NNN, INC-NNN, DEC-NNN]
classification: internal
---

# CHG-NNN · Titolo del cambiamento

**Domanda:** quale cambiamento è autorizzato, entro quali confini, e come sapremo che ha
funzionato?

`status`: `draft | approved | implemented | verified | rolled-back`

**Perché esiste.** Un agente non deve implementare una riga di `LOG`, un feedback, una
richiesta o un incremento di `RMP`: sono segnali, non autorizzazioni. Deve implementare un
`CHG` con `status: approved`. Questo documento è ciò che trasforma un segnale in un mandato
con confini.

---

## I tre campi obbligatori

Tutto il resto è opzionale. Questi tre no: sono il documento.

### 1 · Cosa cambia

Il comportamento osservabile dopo il cambiamento. Non i file da modificare: l'effetto.

### 2 · Cosa NON deve cambiare

I confini. Comportamenti esistenti che devono restare identici, componenti da non toccare,
contratti da non rompere.

È il campo che rende utile il documento a un agente: senza, un agente ottimizzerà il punto
1 a spese di cose che nessuno gli aveva detto di preservare.

### 3 · Come sappiamo che ha funzionato

Criteri di accettazione verificabili. Un test, una metrica con soglia, un `EVR` che passa.
Se non è verificabile, non è un criterio: è una speranza.

---

## Campi opzionali — compila solo quelli rilevanti

| Campo | Quando serve |
|---|---|
| **Trigger** | sempre utile: quale `SIG` o `INC` lo origina |
| **Routing `ICG`** | esito della classificazione d'impatto: nessuno / prodotto / architettura / entrambi |
| **Impatto architettura** | se sì → richiede `ARC` aggiornata **e** un `DEC` |
| **Impatto dati** | se sì → richiede bump del `DC` e avviso ai consumatori |
| **Impatto AI** | se sì → richiede un nuovo `EVR` |
| **Impatto rischio o compliance** | se sì → riga in `RSK §stato` |
| **Artefatti da aggiornare** | elenco esplicito, verificato dal validatore |
| **Rollout** | se non è un rilascio ordinario |
| **Rollback** | se il rollback standard non basta |

## Verifica

*Compilato alla chiusura.* Esito dei criteri del punto 3, `EVR` di riferimento, `RLM` della
release che lo contiene.

---

## Anti-pattern

- **Un `CHG` senza il campo 2.** È il difetto più costoso: un agente ottimizza ciò che gli
  chiedi e rompe ciò che non hai nominato.
- **Criteri di accettazione non verificabili.** "Funziona meglio" non è un criterio.
- **Trasformarlo in un modulo da diciotto sezioni.** Con un solo approvatore che è anche il
  richiedente, un processo di approvazione elaborato è teatro. Tre campi compilati bene
  valgono più di diciotto compilati per dovere.
- **Implementare in `status: draft`.** Se accade sistematicamente, il campo `status` non
  serve a niente e tanto vale eliminarlo — ma allora perdi il confine fra idea e mandato.
- **Un `CHG` per ogni commit.** Registra unità di cambiamento con un outcome, non attività.
