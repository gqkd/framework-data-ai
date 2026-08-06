#!/usr/bin/env python3
"""
Validatore del framework di documentazione Data & AI.

Una sola implementazione, due punti di ingresso:
  · la skill framework-audit lo esegue in interattivo e interpreta i risultati
  · la CI lo esegue su ogni push e blocca il merge sugli ERROR

Uso:
  python validate.py                      valida il repository corrente
  python validate.py --root path/         valida un altro percorso
  python validate.py --json               output machine-readable
  python validate.py --emit-index         rigenera decisions/INDEX.md e TRACEABILITY.md
  python validate.py --stale-days 90      soglia di obsolescenza per i documenti viventi

Exit code: 0 se nessun ERROR, 1 altrimenti. I WARN non bloccano.

Nessuna dipendenza oltre a pyyaml.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Serve pyyaml:  pip install pyyaml")


# ─────────────────────────────────────────────────────────────────────────────
# Schema degli artefatti
#
# status e artifact_type sono definiti per tipo, non da un'enumerazione comune:
# un'enumerazione unica sarebbe troppo generica per intercettare qualcosa.
# ─────────────────────────────────────────────────────────────────────────────

LIFECYCLES = {"living", "immutable", "append-only"}

SCHEMAS: dict[str, dict] = {
    "problem-statement":   {"lifecycle": "immutable",   "status": ["active", "superseded"]},
    "hypothesis":          {"lifecycle": "immutable",   "status": ["open", "confirmed", "refuted", "partially-confirmed"]},
    "evidence-brief":      {"lifecycle": "immutable",   "status": ["active", "superseded"]},
    "competitor-comparison": {"lifecycle": "immutable", "status": ["active", "superseded"]},
    "data-feasibility":    {"lifecycle": "immutable",   "status": ["active", "superseded"]},
    "solution-design":     {"lifecycle": "immutable",   "status": ["active", "superseded"]},
    "decision-record":     {"lifecycle": "immutable",   "status": ["proposed", "accepted", "superseded"],
                            "scope": ["product", "architecture", "platform"]},
    "change-contract":     {"lifecycle": "immutable",   "status": ["draft", "approved", "implemented", "verified", "rolled-back"],
                            "sections": ["Cosa cambia", "Cosa NON deve cambiare", "Come sappiamo che ha funzionato"]},
    "evaluation-report":   {"lifecycle": "immutable",   "status": ["active"],
                            "required": ["evp_version", "evp_hash", "verified_against"]},
    "release-note":        {"lifecycle": "immutable",   "status": ["active"]},
    "release-manifest":    {"lifecycle": "immutable",   "status": ["active"]},
    "product-brief":       {"lifecycle": "living",      "status": ["active", "draft"]},
    "workflow":            {"lifecycle": "living",      "status": ["active", "draft"],
                            "sections": ["corrente", "target", "delta"]},
    # `verified_against` è un commit, e in fase di progetto non c'è nessun commit
    # contro cui verificare: pretenderlo da `draft` vieterebbe di progettare prima di
    # implementare, che è l'ordine che il framework prescrive. Da `active` torna
    # obbligatorio, perché un'architettura dichiarata corrente e non verificata
    # descrive ciò che si spera sia stato costruito — e a colpo d'occhio è
    # indistinguibile da una che descrive il sistema reale.
    "architecture":        {"lifecycle": "living",      "status": ["active", "draft"],
                            "required_if_active": ["verified_against"]},
    # Il substrato condiviso dai tre prodotti. A differenza di ARC nasce al giorno
    # uno, prima del codice: non può richiedere verified_against.
    "platform-architecture": {"lifecycle": "living",    "status": ["active", "draft"]},
    "product-manifest":    {"lifecycle": "living",      "status": ["active", "draft"]},
    "evaluation-plan":     {"lifecycle": "living",      "status": ["active", "draft"]},
    # `draft` è l'interfaccia progettata e non ancora concordata. Serve perché un `DC` si
    # scrive *prima* di essere firmato — è il documento in cui si raccolgono le decisioni
    # che bloccano la firma — e le due alternative sono entrambe peggiori: dichiararlo
    # `active`, cioè dire ai consumatori che possono farci affidamento, oppure non
    # scriverlo finché non è chiuso, cioè non avere dove scrivere cosa lo blocca.
    "data-contract":       {"lifecycle": "living",      "status": ["draft", "active", "deprecated"]},
    "runbook":             {"lifecycle": "living",      "status": ["active", "draft"]},
    "roadmap":             {"lifecycle": "living",      "status": ["active"]},
    "cycle-plan":          {"lifecycle": "living",      "status": ["active"]},
    "risk-register":       {"lifecycle": "living",      "status": ["active"],
                            "sections": ["stato", "accettazioni", "eventi"]},
    "glossary":            {"lifecycle": "living",      "status": ["active"]},
    "commitments":         {"lifecycle": "living",      "status": ["active"]},
    "open-register":       {"lifecycle": "living",      "status": ["active"]},
    "agents-control-plane": {"lifecycle": "living",     "status": ["active"]},
    "signal-log":          {"lifecycle": "append-only", "status": ["active"]},
    "ingestion-register":  {"lifecycle": "append-only", "status": ["active"],
                            "sections": ["affermazioni", "contraddizioni", "da guardare"]},
}

BASE_REQUIRED = ["schema", "artifact_type", "lifecycle", "status", "owners", "created"]

# `corpus` è materiale di origine, non artefatto: sono i documenti che il business ci
# ha consegnato, e non possiamo correggerne il front-matter perché non li abbiamo
# scritti noi. `ingest-out` è il prodotto intermedio dell'estrazione, rigenerabile.
SKIP_DIRS = {"templates", "skills", "corpus", "ingest-out",
             ".git", "node_modules", ".venv", "__pycache__"}

ID_RE = re.compile(r"\b((?:PRB|HYP|EVD|CMP|DFB|SD|DEC|CHG|EVR|REL|RLM|DC|SIG|ANA|INC|OD|KI|RSK|CMT|ING)-\d{3,})\b")


# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Finding:
    level: str      # ERROR | WARN | INFO
    code: str
    path: str
    message: str

    def line(self) -> str:
        icon = {"ERROR": "x", "WARN": "!", "INFO": "-"}[self.level]
        return f"{icon} [{self.code}] {self.path}\n    {self.message}"


@dataclass
class Artifact:
    path: Path
    rel: str
    meta: dict
    body: str
    ids: set[str] = field(default_factory=set)

    @property
    def id(self) -> str | None:
        return self.meta.get("id")

    @property
    def type(self) -> str | None:
        return self.meta.get("artifact_type")


def is_bare_yaml(text: str) -> bool:
    """Un file .yaml del framework: tutto il file è metadata.

    Le righe di commento e le righe vuote iniziali non contano. Un manifest che
    si apre spiegando cosa è resta un manifest, e senza questo verrebbe
    segnalato come privo di front-matter.
    """
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        return line.startswith("schema:")
    return False


def parse_front_matter(text: str) -> tuple[dict | None, str, str | None]:
    """Ritorna (meta, body, errore)."""
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end == -1:
            return None, text, "front-matter aperto ma non chiuso"
        raw, body = text[4:end], text[end + 4:]
    elif is_bare_yaml(text):
        raw, body = text, ""
    else:
        return None, text, "front-matter assente"
    try:
        meta = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        return None, body, f"YAML non valido: {str(e).splitlines()[0]}"
    if not isinstance(meta, dict):
        return None, body, "front-matter non è una mappa"
    return meta, body, None


def discover(root: Path) -> tuple[list[Artifact], list[Finding]]:
    artifacts, findings = [], []
    for p in sorted(root.rglob("*")):
        if p.is_dir() or p.suffix not in {".md", ".yaml", ".yml"}:
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts[:-1]):
            continue
        # Documenti che parlano *del* framework, non artefatti prodotti *dal* framework.
        if p.name in {"README.md", "FRAMEWORK.md", "SKILLS.md", "INDEX.md",
                      "TRACEABILITY.md"}:
            continue
        rel = str(p.relative_to(root))
        meta, body, err = parse_front_matter(p.read_text(encoding="utf-8", errors="replace"))
        if err:
            findings.append(Finding("ERROR", "FM001", rel, err))
            continue
        art = Artifact(p, rel, meta, body)
        art.ids = set(ID_RE.findall(body))
        artifacts.append(art)
    return artifacts, findings


# L'ora è facoltativa nella scrittura ma non nella lettura: un documento si può
# rivedere due volte in una giornata, e senza l'ora la seconda revisione non è
# distinguibile dalla prima.
MOMENT_FORMATS = ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M",
                  "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                  "%Y-%m-%d")


def parse_moment(v) -> datetime | None:
    """Un istante, o None se non lo è.

    YAML restituisce tre tipi diversi per lo stesso campo: `2026-07-29` è un
    date, `2026-07-29 14:30:00` è un datetime, `2026-07-29 14:30` resta una
    stringa perché senza i secondi non è un timestamp YAML valido. Sono tutte
    e tre scritture legittime.

    Niente troncamento: `2026-07-29 HH:MM` è un campo mezzo compilato, e farlo
    passare per mezzanotte lo trasformerebbe in un documento appena rivisto.
    """
    if isinstance(v, datetime):        # prima di date: ne è una sottoclasse
        return v
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day)
    if isinstance(v, str):
        for fmt in MOMENT_FORMATS:
            try:
                return datetime.strptime(v.strip(), fmt)
            except ValueError:
                continue
    return None


def as_list(v) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


# ─────────────────────────────────────────────────────────────────────────────
# Controlli
# ─────────────────────────────────────────────────────────────────────────────

def check_schema(a: Artifact) -> list[Finding]:
    out = []
    for f in BASE_REQUIRED:
        if a.meta.get(f) in (None, "", []):
            out.append(Finding("ERROR", "FM002", a.rel, f"campo obbligatorio mancante: {f}"))

    t = a.type
    if t is None:
        return out
    spec = SCHEMAS.get(t)
    if spec is None:
        out.append(Finding("WARN", "FM003", a.rel,
                           f"artifact_type '{t}' non è nello schema: template nuovo o errore di battitura?"))
        return out

    lc = a.meta.get("lifecycle")
    if lc not in LIFECYCLES:
        out.append(Finding("ERROR", "FM004", a.rel, f"lifecycle '{lc}' non valido"))
    elif lc != spec["lifecycle"]:
        out.append(Finding("ERROR", "FM005", a.rel,
                           f"lifecycle '{lc}' non ammesso per {t}: deve essere '{spec['lifecycle']}'"))

    st = a.meta.get("status")
    if st is not None and st not in spec["status"]:
        out.append(Finding("ERROR", "FM006", a.rel,
                           f"status '{st}' non valido per {t}. Ammessi: {', '.join(spec['status'])}"))

    if "scope" in spec:
        sc = a.meta.get("scope")
        if sc not in spec["scope"]:
            out.append(Finding("ERROR", "FM007", a.rel,
                               f"scope '{sc}' non valido. Ammessi: {', '.join(spec['scope'])}. "
                               "Lo scope determina se è una decisione di prodotto, di architettura o di piattaforma."))

    # Alcuni campi sono obbligatori solo da `active`: sono quelli che attestano un
    # fatto sul mondo (un commit verificato) e che in bozza non esistono ancora.
    obbligatori = list(spec.get("required", []))
    if st == "active":
        obbligatori += spec.get("required_if_active", [])

    for f in obbligatori:
        if a.meta.get(f) in (None, "", [], "COMMIT_HASH", "SHA_DEL_FILE_EVP"):
            out.append(Finding("ERROR", "FM008", a.rel, f"{t} richiede il campo '{f}' compilato"))

    for s in spec.get("sections", []):
        if not re.search(rf"^#{{1,3}} .*{re.escape(s)}", a.body, re.M | re.I):
            out.append(Finding("ERROR", "SEC001", a.rel,
                               f"sezione obbligatoria assente: '{s}'"))
    return out


def check_lifecycle_rules(a: Artifact, stale_days: int, now: datetime) -> list[Finding]:
    out = []
    lc = a.meta.get("lifecycle")

    if lc == "living":
        raw = a.meta.get("last_review")
        lr = parse_moment(raw)
        if lr is None and raw not in (None, "", []):
            # Il campo c'è ma non è un istante: placeholder del template, o
            # compilato a metà. Dirgli che manca manderebbe a cercare la cosa
            # sbagliata, quindi la segnalazione nomina il formato atteso.
            out.append(Finding("WARN", "LC004", a.rel,
                               f"last_review vale '{raw}', che non è un istante: atteso "
                               "'AAAA-MM-GG' oppure 'AAAA-MM-GG HH:MM'. Finché resta così "
                               "il documento non risulta mai rivisto."))
        elif lr is None:
            out.append(Finding("ERROR", "LC001", a.rel,
                               "un documento vivente richiede last_review: senza, non c'è modo di "
                               "accorgersi che è diventato obsoleto"))
        else:
            age = (now - lr).days
            if age > stale_days:
                out.append(Finding("WARN", "LC002", a.rel,
                                   f"vivente non rivisto da {age} giorni (soglia {stale_days}). "
                                   "Un documento vivente obsoleto è peggio di uno assente: viene letto come vero."))
    elif lc == "immutable":
        if a.meta.get("last_review") is not None:
            out.append(Finding("WARN", "LC003", a.rel,
                               "un immutabile non ha last_review: non va rivisto, va superseduto"))
    return out


def check_references(arts: list[Artifact]) -> list[Finding]:
    out = []
    by_id: dict[str, Artifact] = {}
    for a in arts:
        if not a.id:
            continue
        if a.id in by_id:
            out.append(Finding("ERROR", "ID001", a.rel,
                               f"id '{a.id}' duplicato, già usato in {by_id[a.id].rel}"))
        else:
            by_id[a.id] = a

    # Gli ID citati nei registri append-only o nei documenti a paragrafi non sono
    # file autonomi: raccogliamo anche quelli come esistenti.
    inline_ids: set[str] = set()
    for a in arts:
        if a.meta.get("lifecycle") == "append-only" or a.type in {"open-register", "risk-register", "commitments", "roadmap", "ingestion-register"}:
            inline_ids |= a.ids

    known = set(by_id) | inline_ids

    for a in arts:
        for ref in as_list(a.meta.get("derives_from")):
            if isinstance(ref, str) and ID_RE.fullmatch(ref) and ref not in known:
                out.append(Finding("ERROR", "REF001", a.rel,
                                   f"derives_from punta a '{ref}' che non esiste"))
        sup = a.meta.get("supersedes")
        if sup and isinstance(sup, str) and ID_RE.fullmatch(sup):
            if sup not in known:
                out.append(Finding("ERROR", "REF002", a.rel, f"supersedes punta a '{sup}' che non esiste"))
            else:
                target = by_id.get(sup)
                if target is not None and target.meta.get("status") != "superseded":
                    out.append(Finding("ERROR", "REF003", target.rel,
                                       f"superseduto da {a.id} ma status è '{target.meta.get('status')}': "
                                       "va portato a 'superseded'"))

    # cicli nella catena supersedes
    for start in by_id:
        seen, cur = set(), start
        while cur:
            if cur in seen:
                out.append(Finding("ERROR", "REF004", by_id[start].rel,
                                   f"catena supersedes ciclica a partire da {start}"))
                break
            seen.add(cur)
            nxt = by_id.get(cur)
            cur = nxt.meta.get("supersedes") if nxt else None
    return out


def check_change_discipline(arts: list[Artifact]) -> list[Finding]:
    """Gli aggiornamenti obbligatori dichiarati in AGENTS.md, verificati sui CHG chiusi."""
    out = []
    by_id = {a.id: a for a in arts if a.id}
    for a in arts:
        if a.type != "change-contract":
            continue
        if a.meta.get("status") not in {"implemented", "verified"}:
            continue
        body = a.body.lower()
        if "impatto ai" in body and "sì" in body:
            if not any(r.startswith("EVR-") for r in a.ids):
                out.append(Finding("WARN", "CHG001", a.rel,
                                   "dichiara impatto AI ma non cita nessun EVR: una modifica a un "
                                   "componente AI richiede un nuovo evaluation report"))
        if "impatto architettura" in body and "sì" in body:
            if not any(r.startswith("DEC-") for r in a.ids):
                out.append(Finding("WARN", "CHG002", a.rel,
                                   "dichiara impatto architettura ma non cita nessun DEC: "
                                   "una modifica architetturale richiede una decisione registrata"))
    for a in arts:
        if a.type == "release-manifest":
            rb = (a.meta.get("rollback") or {})
            if isinstance(rb, dict):
                if not rb.get("target"):
                    out.append(Finding("ERROR", "RLM001", a.rel,
                                       "rollback.target vuoto: il manifest è inutile nel solo momento in cui serve"))
                if rb.get("tested") is False:
                    out.append(Finding("WARN", "RLM002", a.rel,
                                       "rollback.tested è false: una procedura di rollback non testata "
                                       "non è una procedura, è un'intenzione"))
    return out


# Una voce di OPEN.md §1: dal titolo fino al titolo successivo.
OD_BLOCK_RE = re.compile(r"^###\s+(OD-\d{3,})(.*?)(?=^#{1,3}\s|\Z)", re.M | re.S)


def check_open_register(root: Path, arts: list[Artifact]) -> list[Finding]:
    """Le decisioni aperte non devono avere un DEC che le ha già chiuse."""
    out = []
    opens = [a for a in arts if a.type == "open-register"]
    if not opens:
        out.append(Finding("WARN", "OD001", "OPEN.md",
                           "nessun registro delle decisioni aperte: un agente non ha modo di sapere "
                           "cosa non è stato deciso e riempirà i vuoti da sé"))
        return out

    # Chiude una voce solo il DEC che ne *deriva*. Un DEC nomina le voci aperte per
    # tre motivi diversi — ne chiude una, ne dipende, o ne apre una più stretta — e
    # dedurlo dal fatto che la citi segnalerebbe i tre casi allo stesso modo. Un
    # avviso che si presenta quasi sempre a sproposito insegna a chiuderli tutti.
    closed_by: dict[str, str] = {}
    for d in arts:
        if d.type != "decision-record" or d.meta.get("status") != "accepted":
            continue
        for ref in as_list(d.meta.get("derives_from")):
            if isinstance(ref, str) and ref.startswith("OD-"):
                closed_by[ref] = d.id or d.rel

    for a in opens:
        senza_default = []
        for m in OD_BLOCK_RE.finditer(a.body):
            od, block = m.group(1), m.group(2)
            if od in closed_by:
                out.append(Finding("WARN", "OD002", a.rel,
                                   f"{od} è ancora fra le decisioni aperte ma {closed_by[od]} "
                                   "vi deriva da: sposta la voce in §4 con un rimando"))
            # Costo e default vanno letti sulla stessa voce: un default mancante su
            # una decisione a costo medio si può rinviare, su una a costo alto no.
            if "Costo di ritorno:** alto" in block and "Default in uso:** nessuno" in block:
                senza_default.append(od)
        if senza_default:
            out.append(Finding("INFO", "OD003", a.rel,
                               f"{', '.join(senza_default)}: costo di ritorno alto e nessun default "
                               "in uso. Vanno prese anche con informazione incompleta, perché il "
                               "costo di aspettare supera quello di sbagliare"))
    return out


def check_cross_product(arts: list[Artifact]) -> list[Finding]:
    """Coerenza fra i tre prodotti: contratti interni e glossario unico."""
    out = []
    products = {p for a in arts for p in as_list(a.meta.get("products"))}
    glossaries = [a for a in arts if a.type == "glossary"]
    if len(glossaries) > 1:
        out.append(Finding("ERROR", "XP001", ", ".join(g.rel for g in glossaries),
                           "più di un glossario: è il file dove la complementarità dei prodotti si "
                           "definisce o si perde, e deve essere unico"))
    for a in arts:
        if a.type != "data-contract":
            continue
        for c in as_list(a.meta.get("consumers")):
            if products and c not in products:
                out.append(Finding("WARN", "XP002", a.rel,
                                   f"consumer '{c}' non corrisponde a nessun prodotto noto"))
    # prodotti senza PBR
    with_pbr = {p for a in arts if a.type == "product-brief" for p in as_list(a.meta.get("products"))}
    for p in sorted(products - with_pbr):
        out.append(Finding("WARN", "XP003", f"products/{p}/",
                           f"il prodotto '{p}' non ha un PBR: la sua definizione esiste solo altrove"))
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Generazione indici
# ─────────────────────────────────────────────────────────────────────────────

def emit_index(root: Path, arts: list[Artifact]) -> list[str]:
    written = []
    decs = sorted((a for a in arts if a.type == "decision-record"), key=lambda a: a.id or "")
    if decs:
        rows = ["# Indice delle decisioni", "",
                "Generato da `validate.py --emit-index`. Non modificare a mano.", "",
                "| ID | Scope | Status | Prodotti | Titolo | Supersedes |",
                "|---|---|---|---|---|---|"]
        p = root / "decisions" / "INDEX.md"
        for d in decs:
            title = next((l.lstrip("# ").strip() for l in d.body.splitlines() if l.startswith("# ")), "")
            try:                       # link relativo alla posizione dell'indice
                href = str(d.path.relative_to(p.parent))
            except ValueError:
                href = "../" + d.rel
            rows.append(f"| [{d.id}]({href}) | {d.meta.get('scope','')} | {d.meta.get('status','')} "
                        f"| {', '.join(as_list(d.meta.get('products')))} | {title} | {d.meta.get('supersedes') or ''} |")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(rows) + "\n", encoding="utf-8")
        written.append(str(p.relative_to(root)))

    edges = []
    for a in arts:
        for ref in as_list(a.meta.get("derives_from")):
            if isinstance(ref, str):
                edges.append((ref, a.id or a.rel))
    if edges:
        rows = ["# Indice di tracciabilità", "",
                "Generato da `validate.py --emit-index`. Catena: PRB → HYP → EVD → DEC → SD → "
                "CHG → EVR → RLM → SIG → DEC.", "",
                "| Da | A |", "|---|---|"]
        rows += [f"| {s} | {t} |" for s, t in sorted(set(edges))]
        p = root / "TRACEABILITY.md"
        p.write_text("\n".join(rows) + "\n", encoding="utf-8")
        written.append(str(p.relative_to(root)))
    return written


# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    # La console di Windows non è UTF-8: senza questo, un carattere fuori dalla
    # codepage fa terminare il validatore con UnicodeEncodeError invece che con
    # il suo esito. Uno strumento che va in crash quando ha qualcosa da dire è
    # peggio di uno assente.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")

    ap = argparse.ArgumentParser(description="Valida il framework di documentazione Data & AI")
    ap.add_argument("--root", default=".", type=Path)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--emit-index", action="store_true")
    ap.add_argument("--stale-days", type=int, default=90)
    ap.add_argument("--warn-as-error", action="store_true")
    args = ap.parse_args()

    root = args.root.resolve()
    now = datetime.now()

    arts, findings = discover(root)
    for a in arts:
        findings += check_schema(a)
        findings += check_lifecycle_rules(a, args.stale_days, now)
    findings += check_references(arts)
    findings += check_change_discipline(arts)
    findings += check_open_register(root, arts)
    findings += check_cross_product(arts)

    written = emit_index(root, arts) if args.emit_index else []

    errors = [f for f in findings if f.level == "ERROR"]
    warns = [f for f in findings if f.level == "WARN"]
    infos = [f for f in findings if f.level == "INFO"]

    if args.json:
        print(json.dumps({
            "artifacts": len(arts),
            "errors": len(errors), "warnings": len(warns), "info": len(infos),
            "generated": written,
            "findings": [f.__dict__ for f in findings],
        }, indent=2, ensure_ascii=False))
    else:
        print(f"Artefatti analizzati: {len(arts)}")
        if written:
            print(f"Indici rigenerati: {', '.join(written)}")
        for group, label in ((errors, "ERRORI"), (warns, "AVVISI"), (infos, "NOTE")):
            if group:
                print(f"\n-- {label} ({len(group)}) " + "-" * 40)
                for f in group:
                    print(f.line())
        if not findings:
            print("\nNessun problema rilevato.")
        else:
            print(f"\nTotale: {len(errors)} errori | {len(warns)} avvisi | {len(infos)} note")

    return 1 if errors or (args.warn_as_error and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
