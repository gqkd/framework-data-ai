---
schema: framework/open-register/v1
artifact_type: open-register
lifecycle: living
status: active
products: [prodotto-a, prodotto-b, prodotto-c]
owners: [NOME]
created: AAAA-MM-GG
last_review: AAAA-MM-GG HH:MM
classification: internal
---

# Decisioni aperte e problemi noti — registro di prova

Questo file **non è un template**: `templates/README.md` spiega perché `OPEN.md` non ne
ha uno. È il dato di test con cui `tests/test_framework.py` costruisce il set del giorno
uno, e le sue voci sono scelte per esercitare i rami di `check_open_register`, non per
essere un punto di partenza per un progetto reale.

Prima della separazione fra framework e prodotti, la fixture leggeva l'`OPEN.md` vero del
progetto che stava nello stesso repository. L'esito del test che il README chiama «il test
che conta» cambiava quindi ogni volta che qualcuno modificava un registro di lavoro, in
silenzio e per ragioni scollegate dal framework.

---

# §1 · Decisioni aperte

## Costo di ritorno ALTO — decidere prima della prima riga di codice

### OD-001 · Voce senza default, a costo alto

Esercita `OD003`: costo alto e nessun default in uso insieme sulla stessa voce sono la
combinazione che il validatore segnala, perché va decisa anche con informazione
incompleta.

- **Domanda:** quale datastore per i dati condivisi fra i prodotti?
- **Costo di ritorno:** alto.
- **Default in uso:** nessuno.
- **Il problema che il default introduce:** senza default non sta succedendo niente, e
  ogni componente sceglierà per conto proprio al primo bisogno.
- **Scadenza:** prima della prima riga di codice che persiste qualcosa.

## Costo di ritorno MEDIO — decidere entro il primo mese

### OD-002 · Voce ordinaria, con un default dichiarato

Il caso normale: il validatore non deve segnalare niente. Serve a distinguere `OD003` da
un avviso che scatta su qualunque voce.

- **Domanda:** i tre prodotti condividono un unico modello di identità?
- **Costo di ritorno:** medio.
- **Default in uso:** identità separata per prodotto, cioè lo stato di fatto oggi.
- **Il problema che il default introduce:** un utente che usa due prodotti ha due
  account, e nessuno dei due sa dell'altro.
- **Scadenza:** al secondo prodotto che va in produzione.

---

# §2 · Problemi noti accettati

Nessuno in questo registro di prova.

---

# §3 · Parcheggio

Nessuno in questo registro di prova.

---

# §4 · Decisioni chiuse

Nessuna in questo registro di prova. Quando una voce di §1 viene decisa, esce da lì e
resta qui una riga sola con il rimando al `DEC` che l'ha chiusa.
