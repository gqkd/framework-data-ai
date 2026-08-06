---
schema: framework/commitments/v1
artifact_type: commitments
lifecycle: living
status: active
products: [prodotto-a, prodotto-b, prodotto-c]
owners: [NOME]
created: AAAA-MM-GG
last_review: AAAA-MM-GG HH:MM
classification: confidential
---

# Impegni commerciali presi

**A cosa serve.** In un'azienda che ha venduto l'idea prima di costruirla, questi non
sono requisiti da raccogliere: sono vincoli già in essere. Sono anche requisiti
architetturali travestiti — "un'unica esperienza fra i tre prodotti" è una decisione di
tenancy, non una frase di marketing.

**Perché è il primo documento da scrivere.** Questi vincoli li scoprirai comunque. La
scelta è se scoprirli adesso o nel momento peggiore, cioè quando saranno costosi da
soddisfare.

## Registro

Una voce per impegno. `CMT-NNN`.

### CMT-001 · Titolo dell'impegno

| Campo | Contenuto |
|---|---|
| **Cosa è stato promesso** | Le parole usate, il più fedelmente possibile |
| **A chi** | Cliente, prospect, investitore, partner |
| **Da chi e quando** | Chi l'ha detto e in quale contesto |
| **Prodotti coinvolti** | |
| **Scadenza implicita o esplicita** | Anche "entro l'anno" è una scadenza |
| **Margine di interpretazione** | Quanto è vincolante la formulazione letterale |
| **Traduzione tecnica** | Cosa comporta realmente costruire |
| **Fattibilità** | fattibile · fattibile con riserva · **fuori portata** |
| **Vincolo architetturale che ne deriva** | link a `DEC` o voce di `OPEN.md` |
| **Stato** | **non uscito** · aperto · soddisfatto · rinegoziato · non soddisfacibile |

`non uscito` è la promessa che esiste in un documento e che nessuno ha ancora ricevuto. Va
per prima perché è **il solo stato in cui il rimedio costa un pomeriggio invece della
credibilità**: correggere un deck interno è gratis, rinegoziare con un cliente no. Se una
riga passa da `non uscito` ad `aperto` senza che la fattibilità sia stata verificata, quella
è la transizione che questo documento esiste per intercettare.

## §Fuori portata

Sezione separata e obbligatoria. Gli impegni con `Fattibilità: fuori portata` vanno qui,
in evidenza, con la data in cui è stato comunicato a chi ha promesso — o la data in cui
va comunicato.

Un impegno impossibile che nessuno ha ancora rinegoziato è il rischio più grande del
progetto e non appartiene a nessun altro documento.

---

## Anti-pattern

- **Riformulare la promessa in linguaggio da requisito.** Perdi l'ambiguità originale, che
  è precisamente l'informazione che ti serve per negoziare. Conserva le parole dette.
- **Omettere gli impegni imbarazzanti.** Sono quelli per cui il documento esiste.
- **Trattarlo come documento commerciale.** Ogni voce genera un vincolo tecnico: se la
  colonna "vincolo architetturale" è vuota per tutte le righe, non hai finito di leggerlo.
- **Non datarlo.** Un impegno preso otto mesi fa a un prospect che non ha comprato non
  vincola come uno preso a un cliente pagante la settimana scorsa.
