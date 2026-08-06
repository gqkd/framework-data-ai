# Framework di documentazione — Progetti Data & AI

Definisce **quali documenti esistono in un progetto Data/AI, chi li crea, quando, e a quale
domanda risponde ciascuno**. Ha due destinatari: una persona nuova che deve capire il sistema
senza rompere decisioni prese per buoni motivi, e un agente AI che deve rispondere senza
inventare le parti mancanti.

Questo repository contiene **solo la definizione e gli strumenti**. Gli artefatti di un
progetto reale — decisioni, prodotti, iniziative, corpus — vivono nel repository di quel
progetto, non qui.

| File | Cosa è |
|---|---|
| **`FRAMEWORK.md`** | Il documento di riferimento. Comincia da qui |
| `framework-flow.mermaid` | Il ciclo di vita completo con i gate. Importabile in draw.io: *Arrange → Insert → Advanced → Mermaid* |
| `Framework.drawio` | Lo stesso diagramma, già in formato draw.io |
| `SKILLS.md` | Le cinque skill che gestiscono il framework: due costruite, tre specificate |
| `templates/` | Un template per artefatto, con gli anti-pattern in fondo a ciascuno |
| `skills/framework-capture/` | **Costruita:** ingesta il corpus business (pptx/pdf/docx) e registra informazioni conversazionali, propagando la cascata sugli altri file |
| `skills/framework-audit/` | **Costruita:** valida un progetto e rigenera i suoi indici |
| `tests/` | Il framework verificato su se stesso |

## Ordine di lettura

**Per capire il framework:** `FRAMEWORK.md` → `framework-flow.mermaid` → `templates/README.md`

**Per cominciare a usarlo:** `FRAMEWORK.md §10` — l'entry assessment e il set del giorno uno

**Per automatizzarlo:** `SKILLS.md` → `skills/framework-capture/references/routing-table.md`
(è il nucleo: dove va ogni informazione e cosa cambia con lei) → `skills/framework-audit/SKILL.md`

## Applicarlo a un progetto

Il framework non si copia dentro il progetto: si tiene clonato accanto e si invoca per
percorso. Gli script non fanno nessuna assunzione su dove si trovano — `--root` dice su
quale progetto stanno lavorando.

```bash
pip install -r requirements.txt

# Il gate: 0 errori è la condizione di merge del progetto
python skills/framework-audit/scripts/validate.py --root ../mio-progetto --emit-index

# Estrazione del corpus business (la esegue la skill framework-capture, non l'utente)
python skills/framework-capture/scripts/extract.py ../mio-progetto/products/<p>/corpus \
    -o ../mio-progetto/ingest-out/<p> --jsonl
```

Errori bloccano, avvisi no. `--emit-index` rigenera `decisions/INDEX.md` e `TRACEABILITY.md`
**dentro il progetto**, non qui.

Senza `markitdown` i `.pptx` producono zero blocchi, senza `python-docx` i `.docx`: in
entrambi i casi l'estrazione **riesce** e non contiene niente, che è il modo più silenzioso
di perdere un corpus. I `.pdf` richiedono [poppler](https://poppler.freedesktop.org/) sul
`PATH`. La skill controlla le dipendenze prima di estrarre e si ferma se ne manca una.

## Verifica

```bash
pip install -r requirements.txt
pytest tests/
```

`tests/` verifica il framework su se stesso. Il test che conta è
`test_day_one_set_has_no_blocking_errors`: costruisce il set del giorno uno di
`FRAMEWORK.md §10` a partire dai template e controlla che passi il proprio validatore. Un
framework il cui stato iniziale non supera il proprio gate insegna, al primo commit, che il
gate si ignora.

## Provenienza

Estratto il 2026-08-06 da un repository in cui era mescolato con la sua prima istanza. La
storia è rimasta con quell'istanza, dove sta quasi tutto il suo contenuto; qui si riparte
da uno snapshot.

**Una cosa da sapere:** diversi documenti rimandano a voci `OD-NNN` — `OD-002` in
`FRAMEWORK.md §9` e `SKILLS.md §7`, `OD-005` in `SKILLS.md §2` e in `framework-capture` —
che vivono nel registro delle decisioni aperte di quel progetto e qui non sono
risolvibili. Vanno letti come «una decisione ancora aperta di quel tipo», non come rimandi
a un file di questo repository.

Per il resto il testo è neutro: nomi di prodotto e slug di decisione negli esempi sono
segnaposto. Un secondo progetto può adottarlo così com'è.

## In una riga

Sette documenti viventi che devono essere veri, una ventina che si scrivono una volta e non
si toccano più, e un file — `OPEN.md` — che dice cosa non è ancora deciso, perché è
l'informazione che nessun altro documento contiene e che un agente altrimenti inventa.
