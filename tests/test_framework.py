"""
Test del framework su se stesso.

Il test che conta è `test_day_one_set_has_no_blocking_errors`: costruisce il set
del giorno uno esattamente come lo prescrive FRAMEWORK.md §10 e verifica che
passi il gate della CI. Un framework il cui stato iniziale non supera il proprio
validatore insegna, al primo commit, che il validatore si ignora.

  pytest tests/ -v
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
VALIDATE = ROOT / "skills" / "framework-audit" / "scripts" / "validate.py"
TEMPLATES = ROOT / "templates"


def _load_validate():
    spec = importlib.util.spec_from_file_location("validate_mod", VALIDATE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["validate_mod"] = mod          # serve ai @dataclass del modulo
    spec.loader.exec_module(mod)
    return mod


v = _load_validate()


# ─────────────────────────────────────────────────────────────────────────────
# Fixture: il set del giorno uno
# ─────────────────────────────────────────────────────────────────────────────

PRODUCTS = ["prodotto-a", "prodotto-b", "prodotto-c"]

NOW = datetime.now()


def _fill(text: str, product: str) -> str:
    """Compila i placeholder come farebbe una persona al giorno uno.

    L'istante prima della data: `AAAA-MM-GG HH:MM` contiene `AAAA-MM-GG`, e
    invertendo l'ordine resterebbe un `HH:MM` orfano.
    """
    return (text
            .replace("AAAA-MM-GG HH:MM", NOW.strftime("%Y-%m-%d %H:%M"))
            .replace("AAAA-MM-GG", NOW.date().isoformat())
            .replace("NOME", "nome.cognome")
            .replace("prodotto-a", product))


@pytest.fixture
def day_one(tmp_path: Path) -> Path:
    """Il set del giorno uno di FRAMEWORK.md §10, compilato."""
    (tmp_path / "decisions").mkdir()

    for name in ["ING.md", "COMMITMENTS.md", "GLOSSARY.md", "AGENTS.md", "PLATFORM.md",
                 "OPEN.md"]:
        src = TEMPLATES / name
        if not src.exists():
            pytest.fail(f"manca templates/{name}: è prescritto dal set del giorno uno")
        (tmp_path / name).write_text(_fill(src.read_text(encoding="utf-8"), "prodotto-a"),
                                     encoding="utf-8")

    for p in PRODUCTS:
        d = tmp_path / "products" / p
        d.mkdir(parents=True)
        for name in ["product.yaml", "PBR.md"]:
            (d / name).write_text(_fill((TEMPLATES / name).read_text(encoding="utf-8"), p),
                                  encoding="utf-8")
    return tmp_path


def _findings(root: Path, level: str) -> list:
    arts, findings = v.discover(root)
    for a in arts:
        findings += v.check_schema(a)
        findings += v.check_lifecycle_rules(a, 90, NOW)
    findings += v.check_references(arts)
    findings += v.check_change_discipline(arts)
    findings += v.check_open_register(root, arts)
    findings += v.check_cross_product(arts)
    return [f for f in findings if f.level == level]


# ─────────────────────────────────────────────────────────────────────────────
# Il test che conta
# ─────────────────────────────────────────────────────────────────────────────

def test_day_one_set_has_no_blocking_errors(day_one: Path):
    errors = _findings(day_one, "ERROR")
    assert errors == [], "il set del giorno uno non passa il proprio validatore:\n" + \
        "\n".join(f"  [{f.code}] {f.path}: {f.message}" for f in errors)


# ─────────────────────────────────────────────────────────────────────────────
# I difetti singoli
# ─────────────────────────────────────────────────────────────────────────────

def test_product_yaml_template_is_parsed():
    """Il manifest si apre con due righe di commento: sono YAML valido."""
    text = (TEMPLATES / "product.yaml").read_text(encoding="utf-8")
    meta, _, err = v.parse_front_matter(text)
    assert err is None, f"templates/product.yaml non viene riconosciuto: {err}"
    assert meta["schema"] == "framework/product-manifest/v1"


def test_platform_is_a_known_artifact_type():
    """PLATFORM.md è prescritto al giorno uno e citato da AGENTS.md come fonte."""
    assert "platform-architecture" in v.SCHEMAS


def test_unfilled_placeholder_date_is_not_reported_as_missing():
    """Un placeholder non compilato è un avviso, non un campo mancante."""
    art = v.Artifact(path=Path("PBR.md"), rel="PBR.md", body="",
                     meta={"artifact_type": "product-brief", "lifecycle": "living",
                           "last_review": "AAAA-MM-GG HH:MM"})
    codes = {f.code for f in v.check_lifecycle_rules(art, 90, NOW)}
    assert "LC001" not in codes, "un placeholder presente viene segnalato come assente"
    assert "LC004" in codes, "un placeholder non compilato deve essere segnalato"


def test_missing_last_review_is_still_an_error():
    """Il caso vero — campo assente — resta bloccante."""
    art = v.Artifact(path=Path("PBR.md"), rel="PBR.md", body="",
                     meta={"artifact_type": "product-brief", "lifecycle": "living"})
    findings = v.check_lifecycle_rules(art, 90, NOW)
    assert any(f.code == "LC001" and f.level == "ERROR" for f in findings)


# ─────────────────────────────────────────────────────────────────────────────
# Un'architettura esiste prima del codice che descrive
# ─────────────────────────────────────────────────────────────────────────────


def _arc(**meta) -> "v.Artifact":
    base = {"schema": "framework/architecture/v1", "artifact_type": "architecture",
            "lifecycle": "living", "owners": ["nome.cognome"], "created": "2026-07-30"}
    return v.Artifact(path=Path("ARC.md"), rel="products/prodotto-a/ARC.md", body="",
                      meta={**base, **meta})


def test_an_architecture_can_be_drafted_before_the_code_exists():
    """`verified_against` è un commit, e in fase di progetto non c'è nessun commit
    contro cui verificare.

    Pretenderlo da `draft` vieta di progettare prima di implementare — che è
    esattamente l'ordine che il framework prescrive. Il documento di design
    di un componente può nascere mesi prima di qualunque riga di codice: se il
    validatore lo rifiuta, la conclusione che si tira è che il validatore si ignora."""
    codes = {f.code for f in v.check_schema(_arc(status="draft"))}
    assert "FM008" not in codes, (
        "un'architettura in bozza non può richiedere un commit che non esiste")


def test_an_active_architecture_still_needs_a_verified_commit():
    """Il caso che la regola protegge davvero. Un'architettura dichiarata corrente e
    non verificata contro nessun commit descrive ciò che si spera sia stato
    costruito — ed è indistinguibile, a colpo d'occhio, da una che descrive il
    sistema reale."""
    findings = v.check_schema(_arc(status="active"))
    assert any(f.code == "FM008" and f.level == "ERROR" for f in findings), \
        "da active il commit di verifica torna obbligatorio"


def test_a_data_contract_can_exist_before_it_is_signed():
    """Un `DC` descrive un'interfaccia, e un'interfaccia si progetta prima di essere
    concordata: capita che un'`ARC` dichiari un'interfaccia «firmabile» solo dopo la
    chiusura di un pacchetto di decisioni ancora aperte.

    Senza uno stato intermedio le uscite sono due, entrambe sbagliate: dichiararlo
    `active` — cioè dire ai consumatori che possono farci affidamento — oppure non
    scriverlo, e allora il documento che deve *raccogliere* le quattro decisioni che
    lo bloccano non esiste finché non sono chiuse."""
    art = v.Artifact(path=Path("DC-001.md"), rel="products/prodotto-a/contracts/DC-001.md",
                     body="", meta={"schema": "framework/data-contract/v1",
                                    "artifact_type": "data-contract",
                                    "lifecycle": "living", "status": "draft",
                                    "owners": ["nome.cognome"], "created": "2026-07-31"})
    codes = {f.code for f in v.check_schema(art)}
    assert "FM006" not in codes, "un contratto dati in bozza non è uno status non valido"


# ─────────────────────────────────────────────────────────────────────────────
# last_review è un istante, non un giorno
# ─────────────────────────────────────────────────────────────────────────────

def test_two_reviews_in_the_same_day_are_distinguishable():
    """Il motivo per cui l'ora serve: si può rivedere un documento due volte
    in una giornata, e la seconda deve poter vincere sulla prima."""
    mattina = v.parse_moment("2026-07-29 09:15")
    sera = v.parse_moment("2026-07-29 18:40")
    assert mattina is not None and sera is not None
    assert mattina < sera, "due revisioni dello stesso giorno collassano sullo stesso istante"
    assert (sera.hour, sera.minute) == (18, 40)


def test_accepts_every_form_yaml_produces_for_the_same_field():
    """Tre scritture legittime, tre tipi Python diversi in uscita da YAML:
    `2026-07-29` è un date, `... 14:30:00` è un datetime, `... 14:30` resta
    una stringa perché senza secondi non è un timestamp YAML valido."""
    for raw in ["2026-07-29 14:30", "2026-07-29T14:30", "2026-07-29 14:30:00",
                datetime(2026, 7, 29, 14, 30), date(2026, 7, 29)]:
        got = v.parse_moment(raw)
        assert got is not None, f"{raw!r} non viene riconosciuto"
        assert got.date() == date(2026, 7, 29), f"{raw!r} finisce nel giorno sbagliato"


def test_half_filled_time_placeholder_is_not_taken_for_midnight():
    """Il caso che il troncamento a dieci caratteri lasciava passare: data
    compilata, ora ancora placeholder. Passava come mezzanotte del giorno
    giusto, cioè come documento appena rivisto."""
    art = v.Artifact(path=Path("PBR.md"), rel="PBR.md", body="",
                     meta={"artifact_type": "product-brief", "lifecycle": "living",
                           "last_review": "2026-07-29 HH:MM"})
    codes = {f.code for f in v.check_lifecycle_rules(art, 90, NOW)}
    assert "LC004" in codes, "un last_review mezzo compilato viene accettato come valido"


def test_stale_threshold_still_counts_in_days():
    """L'ora serve a ordinare, non a cambiare la soglia di obsolescenza."""
    art = v.Artifact(path=Path("PBR.md"), rel="PBR.md", body="",
                     meta={"artifact_type": "product-brief", "lifecycle": "living",
                           "last_review": (NOW - timedelta(days=120)).strftime("%Y-%m-%d %H:%M")})
    findings = v.check_lifecycle_rules(art, 90, NOW)
    assert any(f.code == "LC002" for f in findings)
    assert "120 giorni" in next(f.message for f in findings if f.code == "LC002")


def test_the_corpus_is_not_validated_as_framework_artifacts(day_one: Path):
    """`products/<p>/corpus/` contiene i documenti forniti dal business. Un `.md`
    fra quelli non è un artefatto del framework, e bocciarlo per front-matter
    assente riempirebbe il gate di errori su file che non possiamo correggere."""
    corpus = day_one / "products" / "prodotto-a" / "corpus"
    corpus.mkdir(parents=True, exist_ok=True)
    (corpus / "analisi-requisiti.md").write_text(
        "# Analisi requisiti\n\nIl cliente chiede l'export in Excel.\n", encoding="utf-8")

    errors = _findings(day_one, "ERROR")
    assert errors == [], "il corpus del business viene validato come se fossimo noi ad averlo scritto:\n" + \
        "\n".join(f"  [{f.code}] {f.path}: {f.message}" for f in errors)


# ─────────────────────────────────────────────────────────────────────────────
# Il registro delle decisioni aperte
# ─────────────────────────────────────────────────────────────────────────────

def _open_register(body: str) -> "v.Artifact":
    return v.Artifact(path=Path("OPEN.md"), rel="OPEN.md", body=body,
                      meta={"artifact_type": "open-register", "lifecycle": "living",
                            "status": "active"})


def _dec(id_: str, body: str = "", **meta) -> "v.Artifact":
    a = v.Artifact(path=Path(f"{id_}.md"), rel=f"decisions/{id_}.md", body=body,
                   meta={"artifact_type": "decision-record", "lifecycle": "immutable",
                         "status": "accepted", "id": id_, **meta})
    a.ids = set(v.ID_RE.findall(body))
    return a


def test_a_dec_that_only_mentions_an_open_decision_has_not_closed_it():
    """Un `DEC` cita le voci aperte per tre motivi diversi: ne chiude una, ne
    dipende, o ne apre una più stretta. Solo il primo caso va segnalato, e
    l'unico segnale affidabile è `derives_from`."""
    opens = _open_register("### OD-002 · Perimetro del substrato\n\n- **Default in uso:** niente.\n")
    dec = _dec("DEC-001", "Il repository del substrato nasce quando OD-002 ne definirà "
                          "il perimetro, non prima.", derives_from=["OD-001"])

    codes = {f.code for f in v.check_open_register(Path("."), [opens, dec])}
    assert "OD002" not in codes, \
        "una voce citata come dipendenza viene segnalata come già chiusa"


def test_a_dec_that_derives_from_an_open_decision_has_closed_it():
    """Il caso vero resta segnalato: se il DEC deriva dalla voce, la voce va in §4."""
    opens = _open_register("### OD-001 · Monorepo o tre repository\n\n- **Default in uso:** nessuno.\n")
    dec = _dec("DEC-001", "Tre repository separati.", derives_from=["OD-001"])

    findings = v.check_open_register(Path("."), [opens, dec])
    assert any(f.code == "OD002" and "OD-001" in f.message for f in findings)


def test_a_high_cost_decision_without_a_default_is_named():
    """La nota va letta per agire, quindi deve dire *quale* voce. E deve
    correlare costo e default sulla stessa voce: un default mancante su una
    decisione a costo medio non è la stessa cosa."""
    opens = _open_register(
        "### OD-005 · Piattaforma dati\n\n"
        "- **Costo di ritorno:** alto.\n- **Default in uso:** nessuno.\n\n"
        "### OD-010 · Target di deploy\n\n"
        "- **Costo di ritorno:** medio.\n- **Default in uso:** nessuno.\n")

    infos = [f for f in v.check_open_register(Path("."), [opens]) if f.code == "OD003"]
    assert len(infos) == 1, f"attesa una sola nota, ottenute {len(infos)}"
    assert "OD-005" in infos[0].message
    assert "OD-010" not in infos[0].message, "una voce a costo medio non va in questa nota"


def test_output_survives_a_legacy_windows_console():
    """La CI e il terminale di Windows non usano la stessa codepage."""
    proc = subprocess.run(
        [sys.executable, str(VALIDATE), "--root", str(ROOT)],
        capture_output=True, text=True, encoding="cp1252", errors="replace",
        env={**__import__("os").environ, "PYTHONIOENCODING": "cp1252"},
    )
    assert "UnicodeEncodeError" not in proc.stderr, \
        f"il validatore va in crash su una console non-UTF8:\n{proc.stderr[-600:]}"
