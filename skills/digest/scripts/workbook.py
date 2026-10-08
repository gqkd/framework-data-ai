"""The workbook of the digest: four sheets, every derived cell a formula with its value beside it.

Loaded by `digest.py` by path, never run on its own. It receives what `digest.py` computed, the
model of the day and its figures, and lays them out: where a cell follows from other cells it
writes the formula and the value the script computed for it, so the file reads the same in a
preview that does not recalculate and in a spreadsheet that does. The layout, the styles and the
formulas are those of the reference workbook in `tests/fixtures/digest/`, and `tests/selfcheck.py`
compares the two cell by cell; the differences it allows are listed there, each with its reason.

Row numbers here are those a reader sees, from 1; XlsxWriter counts from 0, hence the `- 1` at
every call.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from fractions import Fraction

import xlsxwriter

NAVY, GREY_BORDER = "#1F3864", "#BFBFBF"
PIE = ["#2A78D6", "#1BAF7A", "#EDA100", "#4A3AA7", "#EB6834"]
CL = "'Come leggerlo'!"
OL = "'Ore lavorate'!"
AT = "Attività!"
THEME_LABELS = ("Architettura", "Sviluppo", "Deploy")
SIZE_RANGE = {"S": (1, 2), "M": (3, 5), "L": (6, 12), "XL": (13, 40)}
PREFIX_LABEL = [("OD-", "Decisione da prendere"), ("DEC-", "Decisione presa"),
                ("CHG-", "Modifica al prodotto"), ("KI-", "Problema noto"),
                ("INC-", "Evoluzione futura"), ("EVR-", "Valutazione")]
MONTHS = ("gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic")
# The bars of the calendar are characters of a fixed-width font, so that a day is as wide in
# every row and in the header above them. Courier New is on every Windows machine, and
# LibreOffice draws it with Liberation Mono, which has the same widths.
MONO = "Courier New"
GANTT_CHARS = 105          # what fits in columns B to J at 10 points
GANTT_COLOURS = {"done": "#7F7F7F", "best": "#2A78D6", "worst": "#9DC3E6",
                 "milestone": "#EB6834", "delivery": "#C00000", "today": "#EDA100"}


def number(x):
    """A Fraction as the number a cell stores: an int when it is one."""
    if isinstance(x, Fraction):
        return int(x) if x.denominator == 1 else float(x)
    return x


def dt(d: date) -> datetime:
    return datetime(d.year, d.month, d.day)


def serial(d: date) -> int:
    return (d - date(1899, 12, 30)).days


def dm(d: date) -> str:
    return d.strftime("%d/%m")


def dd(ref: str) -> str:
    """The formula of «dd/mm» for a date cell, without a format that depends on the language."""
    return f'TEXT(DAY({ref}),"00")&"/"&TEXT(MONTH({ref}),"00")'


def dmy_f(ref: str) -> str:
    return f'{dd(ref)}&"/"&YEAR({ref})'


def size_sum(rng: str, which: int) -> str:
    """The minimum (0) or maximum (1) of the sizes in a range of the Taglia column."""
    return "(" + "+".join(f'({rng}="{s}")*{r[which]}' for s, r in SIZE_RANGE.items()) + ")"


def kind_formula(cell: str) -> str:
    out = '""'
    for prefix, label in reversed(PREFIX_LABEL):
        out = f'IF(LEFT({cell},{len(prefix)})="{prefix}","{label}",{out})'
    return "=" + out


def kind_value(i: str) -> str:
    return next((label for prefix, label in PREFIX_LABEL if i.startswith(prefix)), "")


def estimate_formula(cell: str) -> str:
    out = '"da stimare"'
    for s, (lo, hi) in reversed(SIZE_RANGE.items()):
        out = f'IF({cell}="{s}","tra {lo} e {hi} ore",{out})'
    return "=" + out


def estimate_value(size: str | None) -> str:
    if size in SIZE_RANGE:
        lo, hi = SIZE_RANGE[size]
        return f"tra {lo} e {hi} ore"
    return "da stimare"


class Styles:
    def __init__(self, wb):
        self.wb = wb
        self.cache = {}

    def __call__(self, **props):
        key = tuple(sorted(props.items()))
        if key not in self.cache:
            p = {"font_name": "Arial", "font_size": 10}
            p.update(props)
            self.cache[key] = self.wb.add_format(p)
        return self.cache[key]

    # The few styles the sheets share, by what they are for.
    def title(self):
        return self(bold=True, font_size=16, font_color=NAVY)

    def section(self):
        return self(bold=True, font_size=12, font_color=NAVY)

    def head(self, **kw):
        base = {"bold": True, "font_color": "#FFFFFF", "bg_color": NAVY, "text_wrap": True,
                "valign": "vcenter", "border": 1, "border_color": GREY_BORDER}
        base.update(kw)
        return self(**base)

    def cell(self, **kw):
        base = {"text_wrap": True, "valign": "top", "border": 1, "border_color": GREY_BORDER}
        base.update(kw)
        return self(**base)

    def total(self, **kw):
        base = {"bold": True, "bg_color": "#D9E1F2"}
        base.update(kw)
        return self.cell(**base)

    def note(self):
        return self(italic=True, font_size=9, font_color="#555555")


HOURS = "0.0;\\-0.0;0"
SIGNED = "\\+0;\\-0;0"
SIGNED_PCT = "\\+0%;\\-0%;0%"
DATE = "dd/mm/yyyy"


def setup(ws, widths: dict, freeze: tuple | None):
    for col, w in widths.items():
        ws.set_column(f"{col}:{col}", w)
    if freeze:
        ws.freeze_panes(*freeze)
    ws.hide_gridlines(2)
    ws.set_landscape()
    ws.set_paper(9)
    ws.fit_to_pages(1, 0)
    ws.set_margins(left=0.75, right=0.75, top=1, bottom=1)
    ws.protect()


# ─────────────────────────────────────────────────────────────────────────────
# Attività

ITEM_HEAD = ("Voce", "Titolo", "Tema", "Tipo", "Taglia", "Ore stimate", "Ore effettive", "Stato",
             "Che cos'è")


def item_row(ws, S, r: int, it, status: str, effective: bool):
    rid = it.shown_id
    ws.write_string(r - 1, 0, rid, S.cell(bold=True))
    ws.write_string(r - 1, 1, str(it.title or ""), S.cell())
    ws.write_string(r - 1, 2, THEME_LABELS[("architettura", "sviluppo", "deploy").index(it.theme)]
                    if it.theme in ("architettura", "sviluppo", "deploy") else "", S.cell())
    ws.write_formula(r - 1, 3, kind_formula(f"A{r}"), S.cell(), kind_value(rid))
    if it.size:
        ws.write_string(r - 1, 4, it.size, S.cell())
    else:
        ws.write_blank(r - 1, 4, None, S.cell())
    ws.write_formula(r - 1, 5, estimate_formula(f"E{r}"), S.cell(), estimate_value(it.size))
    if effective:
        ws.write_number(r - 1, 6, number(it.hours), S.cell(num_format=HOURS))
    else:
        ws.write_blank(r - 1, 6, None, S.cell())
    ws.write_string(r - 1, 7, status, S.cell())
    ws.write_string(r - 1, 8, str(it.what or ""), S.cell())


def none_row(ws, S, r: int, columns: int, col: int = 1):
    for c in range(columns):
        if c == col:
            ws.write_string(r - 1, c, "Nessuna.", S.cell())
        else:
            ws.write_blank(r - 1, c, None, S.cell())


def header(ws, S, r: int, labels, height=None):
    for c, label in enumerate(labels):
        ws.write_string(r - 1, c, label, S.head())
    if height:
        ws.set_row(r - 1, height)


def activities(wb, S, m, F) -> dict:
    """The sheet of the four lists; returns the rows of each, for the formulas of the others."""
    ws = wb.add_worksheet("Attività")
    setup(ws, {"A": 10, "B": 36, "C": 13, "D": 22, "E": 8, "F": 15, "G": 11, "H": 42, "I": 62},
          (2, 1))
    ws.write_string(0, 0, "Attività", S.title())
    pos = {}

    def table(r: int, title: str, rows: list) -> tuple[int, int]:
        ws.write_string(r - 1, 0, title, S.section())
        header(ws, S, r + 1, ITEM_HEAD, 21.75)
        first = r + 2
        if not rows:
            none_row(ws, S, first, 9)
            return first, first
        for k, (it, status, eff) in enumerate(rows):
            item_row(ws, S, first + k, it, status, eff)
        return first, first + len(rows) - 1

    r = 3
    plan = [(p["item"], p["status"], False) for p in m.plan_rows]
    pos["plan"] = table(r, "1. Prossimi giorni", plan)
    r = pos["plan"][1] + 3

    todo = [(it, m.status[it.id], False) for it in m.todo]
    a, b = pos["todo"] = table(r, "2. Da fare nel perimetro del rilascio", todo)
    t = b + 1
    rng = f"{AT}$E${a}:$E${b}"
    count_cells(ws, S, t, a, b, bool(m.todo))
    ws.write_string(t - 1, 1, "Totale", S.total())
    for c in (2, 3, 4, 6, 7, 8):
        ws.write_blank(t - 1, c, None, S.total())
    ws.write_formula(t - 1, 5, f'="tra "&ROUND(SUMPRODUCT({size_sum(rng, 0)}),1)&" e "&'
                               f'ROUND(SUMPRODUCT({size_sum(rng, 1)}),1)&" ore"',
                     S.total(), F["est_total"])
    r = t + 3

    done = [(it, m.status[it.shown_id], True) for it in m.done]
    a, b = pos["done"] = table(r, "3. Fatto nel perimetro del rilascio", done)
    t = b + 1
    count_cells(ws, S, t, a, b, bool(m.done))
    ws.write_string(t - 1, 1, "Totale", S.total())
    for c in (2, 3, 4, 5, 7, 8):
        ws.write_blank(t - 1, c, None, S.total())
    ws.write_formula(t - 1, 6, f"=SUM(G{a}:G{b})", S.total(num_format=HOURS),
                     number(sum((it.hours for it in m.done), Fraction(0))))
    r = t + 3

    out = [(it, m.status[it.id], False) for it in m.out]
    a, b = pos["out"] = table(r, "4. Fuori perimetro", out)
    t = b + 1
    count_cells(ws, S, t, a, b, bool(m.out))
    ws.write_string(t - 1, 1, "Non entrano nella stima", S.total())
    for c in range(2, 9):
        ws.write_blank(t - 1, c, None, S.total())
    ws.write_string(t + 1, 0, "Ore effettive: solo per le voci chiuse. Le ore lavorate sulle voci "
                              "aperte sono nella colonna Stato.", S.note())

    a, b = pos["todo"]
    ws.conditional_format(f"H{a}:H{b}",
                          {"type": "formula", "criteria": f'=LEFT($H{a},8)="Bloccata"',
                           "format": wb.add_format({"bold": True, "font_color": "#9C0006",
                                                    "bg_color": "#F8CBAD"})})
    ws.conditional_format(f"H{a}:H{b}",
                          {"type": "formula", "criteria": f'=LEFT($H{a},10)="Rallentata"',
                           "format": wb.add_format({"bg_color": "#FCE4D6"})})
    return pos


def count_cells(ws, S, t: int, a: int, b: int, any_rows: bool):
    if any_rows:
        ws.write_formula(t - 1, 0, f'=COUNTA(A{a}:A{b})&" voci"', S.total(), f"{b - a + 1} voci")
    else:
        ws.write_string(t - 1, 0, "0 voci", S.total())


# ─────────────────────────────────────────────────────────────────────────────
# Ore lavorate

WINDOW_HEAD = ("Periodo", "Dal", "Al", "Ore totali", "Architettura", "Sviluppo", "Deploy",
               "Fuori perimetro", "Fuori dal prodotto", "Media al giorno sul rilascio")
CATEGORY_LABELS = ("Supporto alla demo e alla produzione", "Reportistica e presentazioni di stato",
                   "Riunioni", "Solleciti e accessi infrastruttura", "Formazione del junior")
CATEGORY_SHORT = ("Supporto", "Reportistica", "Riunioni", "Solleciti", "Formazione")
WEEKDAYS = ("lun", "mar", "mer", "gio", "ven", "sab", "dom")


def hours_sheet(wb, S, m, F) -> None:
    ws = wb.add_worksheet("Ore lavorate")
    setup(ws, {"A": 30, "B": 12, "D": 11, "E": 13, "F": 11, "I": 12, "J": 14, "L": 11, "M": 13,
               "N": 12}, (2, 0))
    ws.write_string(0, 0, "Ore lavorate", S.title())
    first = 30
    last = first + max(len(m.table), 1) - 1
    col = {c: f"{OL}${c}${first}:${c}${last}" for c in "BCDEFGHIJKLM"}

    ws.write_string(2, 0, "1. Ore per periodo", S.section())
    header(ws, S, 4, WINDOW_HEAD, 30)
    starts = [f"=WORKDAY({CL}$B$4,-3)", f"={CL}$B$4-7", f"={CL}$B$4-30", f"={CL}$B$7"]
    for k, w in enumerate(F["windows"]):
        r = 5 + k
        ws.write_string(r - 1, 0, w["label"], S.cell(bold=True))
        ws.write_formula(r - 1, 1, starts[k], S.cell(num_format=DATE), serial(w["from"]))
        ws.write_formula(r - 1, 2, f"={CL}$B$4-1", S.cell(num_format=DATE), serial(w["to"]))
        values = [w["tot"], w["arch"], w["svil"], w["dep"], w["out"], w["outside"]]
        for c, (src, v) in enumerate(zip("CDEFGH", values)):
            ws.write_formula(r - 1, 3 + c,
                             f'=SUMIFS({col[src]},{col["B"]},">="&$B{r},{col["B"]},"<="&$C{r})',
                             S.cell(num_format=HOURS, bold=(c == 0)), number(v))
        nd = f"NETWORKDAYS(MAX(B{r},{CL}$B$7),C{r})"
        ws.write_formula(r - 1, 9, f"=IF({nd}<=0,0,(E{r}+F{r}+G{r})/{nd})",
                         S.cell(num_format="0.0"), number(w["avg"]))

    ws.write_string(9, 0, "2. Come si dividono le ore, in percentuale", S.section())
    header(ws, S, 11, WINDOW_HEAD[:9])
    for k, w in enumerate(F["windows"]):
        r, src = 12 + k, 5 + k
        ws.write_formula(r - 1, 0, f"=A{src}", S.cell(bold=True), w["label"])
        ws.write_formula(r - 1, 1, f"=B{src}", S.cell(num_format=DATE), serial(w["from"]))
        ws.write_formula(r - 1, 2, f"=C{src}", S.cell(num_format=DATE), serial(w["to"]))
        ws.write_formula(r - 1, 3, f"=D{src}", S.cell(num_format=HOURS, bold=True),
                         number(w["tot"]))
        for c, (letter, v) in enumerate(zip("EFGHI", w["pct"])):
            last_col = c == 4
            ws.write_formula(r - 1, 4 + c, f"=IF($D{src}=0,0,{letter}{src}/$D{src})",
                             S.cell(num_format="0%", bold=last_col,
                                    **({"bg_color": "#FFF2CC"} if last_col else {})),
                             number(v))

    ws.write_string(17, 0, "3. Dove vanno le ore fuori dal prodotto", S.section())
    header(ws, S, 19, ("Categoria", "Ore dall'inizio", "Ultimi 7 giorni"))
    w0, w7 = F["windows"][3], F["windows"][1]
    for k, label in enumerate(CATEGORY_LABELS):
        r, src = 20 + k, "IJKLM"[k]
        ws.write_string(r - 1, 0, label, S.cell(bold=True))
        ws.write_formula(r - 1, 1, f"=SUM({col[src]})", S.cell(num_format=HOURS),
                         number(w0["cats"][k]))
        ws.write_formula(r - 1, 2,
                         f'=SUMIFS({col[src]},{col["B"]},">="&$B$6,{col["B"]},"<="&$C$6)',
                         S.cell(num_format=HOURS), number(w7["cats"][k]))
    ws.write_string(24, 0, "Totale", S.total())
    ws.write_formula(24, 1, "=SUM(B20:B24)", S.total(num_format=HOURS),
                     number(sum(w0["cats"], Fraction(0))))
    ws.write_formula(24, 2, "=SUM(C20:C24)", S.total(num_format=HOURS),
                     number(sum(w7["cats"], Fraction(0))))

    ws.write_string(26, 0, "4. Giorno per giorno, dall'inizio del progetto", S.section())
    for c in range(3):
        ws.write_blank(27, c, None, S.cell(bg_color=NAVY))
    ws.merge_range(27, 3, 27, 5, "Sul rilascio", S.head(align="center", text_wrap=False))
    for c in (6, 7):
        ws.write_blank(27, c, None, S.head(align="center", text_wrap=False))
    ws.merge_range(27, 8, 27, 12, "di cui fuori dal prodotto",
                   S.head(align="center", text_wrap=False))
    header(ws, S, 29, ("Giorno", "Data", "Ore totali", *THEME_LABELS, "Fuori perimetro",
                       "Fuori dal prodotto", *CATEGORY_SHORT), 27.75)
    for k, row in enumerate(m.table):
        r = first + k
        d = row[0]
        weekend = d.weekday() >= 5
        ws.write_formula(r - 1, 0,
                         f'=CHOOSE(WEEKDAY(B{r},2),"lun","mar","mer","gio","ven","sab","dom")'
                         f'&" "&{dd(f"B{r}")}',
                         S.cell(bold=True, **({"font_color": "#C00000"} if weekend else {})),
                         f"{WEEKDAYS[d.weekday()]} {dm(d)}")
        ws.write_datetime(r - 1, 1, dt(d), S.cell(num_format=DATE))
        product = sum(row[1:5], Fraction(0))
        outside = sum(row[5:10], Fraction(0))
        ws.write_formula(r - 1, 2, f"=SUM(D{r}:H{r})", S.cell(num_format=HOURS, bold=True),
                         number(product + outside))
        for c in range(4):
            ws.write_number(r - 1, 3 + c, number(row[1 + c]), S.cell(num_format=HOURS))
        ws.write_formula(r - 1, 7, f"=SUM(I{r}:M{r})", S.cell(num_format=HOURS),
                         number(outside))
        for c in range(5):
            ws.write_number(r - 1, 8 + c, number(row[5 + c]),
                            S.cell(num_format=HOURS, font_color="#7F7F7F"))
    ws.write_string(last, 0, "I giorni in rosso sono sabato e domenica.", S.note())


# ─────────────────────────────────────────────────────────────────────────────
# Come leggerlo

LEGEND = [
    ("Tipi di voce", [
        ("Decisione da prendere (OD)", "Una scelta tecnica ancora aperta. Finché non è presa, il "
                                       "lavoro che dipende da lei non può partire."),
        ("Decisione presa (DEC)", "Una scelta tecnica chiusa e messa per iscritto."),
        ("Modifica al prodotto (CHG)", "Un intervento autorizzato sul codice o sugli ambienti."),
        ("Problema noto (KI)", "Un difetto conosciuto, da correggere."),
        ("Evoluzione futura (INC)", "Una capacità prevista per dopo questo rilascio."),
    ]),
    ("Taglie (stima delle ore per una voce)", [
        ("S", "da 1 a 2 ore"),
        ("M", "da 3 a 5 ore"),
        ("L", "da 6 a 12 ore"),
        ("XL", "da 13 a 40 ore. Troppo grande per essere stimata bene: va spezzata in voci più "
               "piccole."),
    ]),
    ("Stati di una voce da fare", [
        ("Da iniziare", "Pronta, aspetta il suo turno."),
        ("In corso", "Ci sto lavorando."),
        ("Rallentata", "Si può fare, ma senza qualcosa che deve arrivare da altri il risultato "
                       "andrà rivisto."),
        ("Bloccata", "Non si può fare finché non arriva qualcosa da altri. Il motivo è sempre "
                     "scritto accanto."),
    ]),
    ("Tipi di ore", [
        ("Architettura", "Decidere come è fatto il sistema: scelte tecniche, disegno, prove per "
                         "decidere."),
        ("Sviluppo", "Scrivere e correggere il codice del prodotto."),
        ("Deploy", "Portare il prodotto negli ambienti: costruzione delle versioni, rilascio, "
                   "configurazione."),
        ("Fuori perimetro", "Lavoro sul prodotto, ma su voci previste per dopo questo rilascio."),
        ("Fuori dal prodotto", "Riunioni, reportistica, supporto alla demo e alla produzione, "
                               "formazione, solleciti."),
    ]),
    ("Regole dei numeri", [
        ("Perimetro", "Ciò che deve esserci nel rilascio concordato. Le voci fuori perimetro sono "
                      "elencate ma non entrano nella stima."),
        ("Ore stimate", "Sono sempre un intervallo, dalla somma delle taglie più piccole a quella "
                        "delle più grandi."),
        ("Voci in corso", "Una voce resta stimata per intero finché non si chiude. Le ore già "
                          "spese sono indicate a parte."),
        ("Stima di consegna", "Spiegata nel Riepilogo, al punto 2."),
    ]),
    ("Domande e chiarimenti", [
        ("Come chiedere", "Per un dubbio su una riga, un commento sulla cella o una mail: rispondo "
                          "per iscritto entro il giorno lavorativo successivo."),
    ]),
]
EVR_LEGEND = ("Valutazione (EVR)", "Una prova fatta per decidere, con il suo esito messo per "
                                   "iscritto.")


def legend_sheet(wb, S, m, shown_ids: list[str]):
    ws = wb.add_worksheet("Come leggerlo")
    setup(ws, {"A": 34, "B": 100}, None)
    ws.write_string(0, 0, "Come leggere questo file", S.title())
    ws.write_string(2, 0, "Date di riferimento", S.section())
    dates = [("Data di questo aggiornamento", m.when), ("Aggiornamento precedente", m.prev_date),
             ("Consegna concordata", m.delivery), ("Inizio del progetto", m.start),
             ("Prossimo aggiornamento", m.next_update)]
    for k, (label, d) in enumerate(dates):
        ws.write_string(3 + k, 0, label, S.cell(bold=True))
        ws.write_datetime(3 + k, 1, dt(d), S(bold=True, bg_color="#FFF2CC", num_format=DATE,
                                             align="left", border=1, border_color=GREY_BORDER))
    r = 10
    for title, rows in LEGEND:
        ws.write_string(r - 1, 0, title, S.section())
        r += 1
        if title == "Tipi di voce" and any(i.startswith("EVR-") for i in shown_ids):
            rows = rows + [EVR_LEGEND]
        for a, b in rows:
            ws.write_string(r - 1, 0, a, S.cell(bold=True))
            ws.write_string(r - 1, 1, b, S.cell())
            r += 1
        r += 1


# ─────────────────────────────────────────────────────────────────────────────
# Riepilogo

def summary_sheet(wb, ws, S, m, F, at: dict):
    setup(ws, {"A": 36, "B": 13, "C": 17, "E": 14, "F": 16, "H": 15, "J": 18}, (2, 0))
    ws.activate()
    B4, B5, B6 = f"{CL}$B$4", f"{CL}$B$5", f"{CL}$B$6"
    ws.write_formula(0, 0, f'="{m.name.upper()} · stato del rilascio al "&{dmy_f(B4)}',
                     S.title(), f"{m.name.upper()} · stato del rilascio al "
                                f"{m.when.strftime('%d/%m/%Y')}")

    # 1. A che punto siamo
    ws.write_string(2, 0, "1. A che punto siamo", S.section())
    lab = S(bold=True, bg_color="#F2F2F2", text_wrap=True, valign="vcenter", border=1,
            border_color=GREY_BORDER)
    big = S(bold=True, font_size=14, text_wrap=True, align="left", valign="vcenter", border=1,
            border_color=GREY_BORDER)
    small = S(bold=True, text_wrap=True, align="left", valign="vcenter", border=1,
              border_color=GREY_BORDER)
    a, b = at["todo"]
    waits = m.waits
    w_first = 17
    w_last = w_first + max(len(waits), 1) - 1
    stat = f"$F${w_first}:$F${w_last}"
    rows = [
        ("Consegna concordata", f"={dmy_f(B6)}", F["B4"], big, 24),
        ("Consegna prevista oggi",
         f'=IF(AND(ISNUMBER(I12),ISNUMBER(I13)),"tra il "&{dd("I12")}&" e il "&{dd("I13")},'
         f'"non stimabile")', F["B5"], big, 24),
        ("Ritardo", '=IF(NOT(ISNUMBER(J13)),"non stimabile",IF(J13=0,"nessuno",'
                    '"da "&J12&" a "&J13&" giorni lavorativi"))', F["B6"], big, 24),
        ("La previsione vale solo se",
         (f'="arrivano in tempo le "&ROWS({stat})&" cose richieste ad altri (punto 3). Oggi "&'
          f'(COUNTIF({stat},"SCADUTA*")+COUNTIF({stat},"Scade oggi"))&'
          f'" sono scadute o scadono oggi."') if waits else None, F["B7"], small, 30),
        ("Dove va il tempo", None, F["B8"], small, 30),
    ]
    r8 = (f'="Dall\'inizio del progetto "&(ROUND({OL}E8,0)+ROUND({OL}F8,0)+ROUND({OL}G8,0)+'
          f'ROUND({OL}H8,0)+ROUND({OL}I8,0))&" ore lavorate: "&ROUND({OL}E8,0)&" architettura, "&'
          f'ROUND({OL}F8,0)&" sviluppo, "&ROUND({OL}G8,0)&" deploy, "&ROUND({OL}H8,0)&'
          f'" fuori perimetro, "&ROUND({OL}I8,0)&" fuori dal prodotto ("&'
          f'ROUND({OL}I15*100,0)&"%: riunioni, reportistica, supporto, formazione)."')
    for k, (label, formula, value, fmt, height) in enumerate(rows):
        r = 4 + k
        if label == "Dove va il tempo":
            formula = r8
        ws.write_string(r - 1, 0, label, lab)
        ws.merge_range(r - 1, 1, r - 1, 9, "", fmt)
        if formula:
            ws.write_formula(r - 1, 1, formula, fmt, value)
        else:
            ws.write_string(r - 1, 1, value, fmt)
        ws.set_row(r - 1, height)
    late = {"type": "formula", "format": wb.add_format({"bold": True, "font_color": "#C00000",
                                                        "bg_color": "#F8CBAD"})}
    ws.conditional_format("B6:J6", dict(late, criteria="=AND(ISNUMBER($J$13),$J$13>0)"))

    # 2. Calcolo stima consegna
    ws.write_string(9, 0, "2. Calcolo stima consegna", S.section())
    header(ws, S, 11, ("Caso", "Voci che mancano", "Ore stimate che mancano",
                       "Ore lavorate al giorno (media ultimi 3 giorni)", "meno ore fuori perimetro",
                       "meno ore fuori dal prodotto", "Ore al giorno per il rilascio",
                       "Giorni lavorativi necessari", "Consegna prevista",
                       "Ritardo sulla consegna concordata"), 43.5)
    rng = f"{AT}$E${a}:$E${b}"
    nd3 = f"NETWORKDAYS({OL}$B$5,{OL}$C$5)"
    for k, (label, case) in enumerate(zip(("Caso migliore", "Caso peggiore"), F["cases"])):
        r = 12 + k
        ws.write_string(r - 1, 0, label, S.cell(bold=True))
        if m.todo:
            ws.write_formula(r - 1, 1, f"=COUNTA({AT}$A${a}:$A${b})", S.cell(num_format="0"),
                             case["B"])
        else:
            ws.write_number(r - 1, 1, 0, S.cell(num_format="0"))
        ws.write_formula(r - 1, 2, f"=SUMPRODUCT({size_sum(rng, k)})", S.cell(num_format=HOURS),
                         number(case["C"]))
        for c, (src, key) in enumerate((("D", "D"), ("H", "E"), ("I", "F"))):
            ws.write_formula(r - 1, 3 + c, f"=ROUND({OL}${src}$5/{nd3},1)",
                             S.cell(num_format="0.0"), number(case[key]))
        ws.write_formula(r - 1, 6, f"=D{r}-E{r}-F{r}", S.cell(num_format="0.0", bold=True),
                         number(case["G"]))
        ws.write_formula(r - 1, 7, f'=IF(G{r}<=0,"non stimabile",ROUNDUP(ROUND(C{r}/G{r},9),0))',
                         S.cell(num_format="0", bold=True), case["H"])
        ws.write_formula(r - 1, 8, f'=IF(ISNUMBER(H{r}),WORKDAY({B4}-1,MAX(1,H{r})),'
                                   f'"non stimabile")',
                         S.cell(num_format=DATE, bold=True, bg_color="#FFF2CC"),
                         serial(case["I"]) if isinstance(case["I"], date) else case["I"])
        ws.write_formula(r - 1, 9, f'=IF(ISNUMBER(I{r}),IF(I{r}>{B6},NETWORKDAYS({B6}+1,I{r}),0),'
                                   f'"non stimabile")',
                         S.cell(num_format='0" giorni lavorativi"', bold=True), case["J"])
    ws.conditional_format("J12:J13", dict(late, criteria="=AND(ISNUMBER(J12),J12>0)"))

    # 3. Cosa serve da altri
    ws.write_string(14, 0, "3. Cosa serve da altri", S.section())
    header(ws, S, 16, ("Cosa serve", "Da chi", "Richiesto il", "Giorni di attesa", "Serve entro",
                       "Stato", "Voci bloccate"), 15)
    ws.merge_range(15, 7, 15, 9, "Cosa succede se manca", S.head())
    if not waits:
        none_row(ws, S, w_first, 7, col=0)
        ws.merge_range(w_first - 1, 7, w_first - 1, 9, "", S.cell())
    for k, w in enumerate(waits):
        r = w_first + k
        ws.write_string(r - 1, 0, str(w["what"]), S.cell(bold=True))
        ws.write_string(r - 1, 1, str(w["owner"]), S.cell())
        asked, needed = w["asked"], w["needed_by"]
        asked = asked if isinstance(asked, date) else date.fromisoformat(str(asked))
        needed = needed if isinstance(needed, date) else date.fromisoformat(str(needed))
        ws.write_datetime(r - 1, 2, dt(asked), S.cell(num_format=DATE))
        ws.write_formula(r - 1, 3, f"={B4}-C{r}", S.cell(num_format="0"), (m.when - asked).days)
        ws.write_datetime(r - 1, 4, dt(needed), S.cell(num_format=DATE))
        ws.write_formula(r - 1, 5,
                         f'=IF(E{r}<{B4},"SCADUTA da "&({B4}-E{r})&IF({B4}-E{r}=1," giorno",'
                         f'" giorni"),IF(E{r}={B4},"Scade oggi","Entro "&(E{r}-{B4})&'
                         f'IF(E{r}-{B4}=1," giorno"," giorni")))',
                         S.cell(bold=True), F["wait_status"][k])
        blocks = [str(x) for x in w.get("blocks") or []]
        slows = [str(x) for x in w.get("slows") or []]
        text = ", ".join(blocks) if blocks else "nessuna"
        if slows:
            text += f" (rallenta {', '.join(slows)})"
        ws.write_string(r - 1, 6, text, S.cell())
        ws.merge_range(r - 1, 7, r - 1, 9, str(w["without"]), S.cell(font_color="#C00000"))
        ws.set_row(r - 1, 27.75)
    ws.conditional_format(f"F{w_first}:F{w_last}",
                          {"type": "formula", "criteria": f'=LEFT($F{w_first},7)="SCADUTA"',
                           "format": wb.add_format({"bold": True, "font_color": "#9C0006",
                                                    "bg_color": "#F8CBAD"})})
    ws.conditional_format(f"F{w_first}:F{w_last}",
                          {"type": "formula", "criteria": f'=$F{w_first}="Scade oggi"',
                           "format": wb.add_format({"bg_color": "#FCE4D6"})})

    # 4. Avanzamento per tema
    s4 = w_last + 2
    ws.write_string(s4 - 1, 0, "4. Avanzamento per tema", S.section())
    ws.write_blank(s4, 0, None, S.cell(bg_color=NAVY))
    ws.merge_range(s4, 1, s4, 3, "Voci fatte", S.head(align="center", text_wrap=False))
    ws.merge_range(s4, 4, s4, 6, "Voci da fare", S.head(align="center", text_wrap=False))
    h2 = s4 + 2
    this_period = (f'="In questo aggiornamento ("&IF({B4}-1={B5},{dd(B5)},IF({B4}-1-{B5}=1,'
                   f'{dd(B5)}&" e "&{dd(f"{B4}-1")},"dal "&{dd(B5)}&" al "&{dd(f"{B4}-1")}))&")"')
    for c, label in enumerate(("Tema", "Finora", f"Nell'aggiornamento precedente ({m.prev_label})",
                               None, "Da fare oggi", "Variazione dall'aggiornamento precedente",
                               "Ore stimate da fare")):
        if label is None:
            ws.write_formula(h2 - 1, c, this_period, S.head(),
                             f"In questo aggiornamento ({m.this_label})")
        else:
            ws.write_string(h2 - 1, c, label, S.head())
    ws.set_row(h2 - 1, 45.75)
    da, db = at["done"]
    yellow = {"bg_color": "#FFF2CC", "bold": True}
    for k, (key, label) in enumerate(zip(("architettura", "sviluppo", "deploy"), THEME_LABELS)):
        r = h2 + 1 + k
        t = F["themes"][key]
        ws.write_string(r - 1, 0, label, S.cell(bold=True))
        ws.write_formula(r - 1, 1, f"=COUNTIF({AT}$C${da}:$C${db},A{r})", S.cell(num_format="0"),
                         t["done"])
        ws.write_number(r - 1, 2, t["prev_closed"], S.cell(num_format="0"))
        ws.write_number(r - 1, 3, t["this_closed"], S.cell(num_format="0", **yellow))
        ws.write_formula(r - 1, 4, f"=COUNTIF({AT}$C${a}:$C${b},A{r})", S.cell(num_format="0"),
                         t["todo"])
        ws.write_formula(r - 1, 5, f"=E{r}-{t['todo'] - t['delta']}",
                         S.cell(num_format=SIGNED, **yellow), t["delta"])
        sel = f"({AT}$C${a}:$C${b}=A{r})"
        ws.write_formula(r - 1, 6, f'="tra "&ROUND(SUMPRODUCT({sel}*{size_sum(rng, 0)}),1)&" e "&'
                                   f'ROUND(SUMPRODUCT({sel}*{size_sum(rng, 1)}),1)&" ore"',
                         S.cell(), t["est"])
    r = h2 + 4
    first, last = h2 + 1, h2 + 3
    ws.write_string(r - 1, 0, "Totale", S.total())
    sums = [sum(F["themes"][t][k] for t in F["themes"])
            for k in ("done", "prev_closed", "this_closed", "todo", "delta")]
    for c, (letter, v) in enumerate(zip("BCDEF", sums)):
        ws.write_formula(r - 1, 1 + c, f"=SUM({letter}{first}:{letter}{last})",
                         S.total(num_format=SIGNED if letter == "F" else "0"), v)
    ws.write_formula(r - 1, 6, f'="tra "&ROUND(SUMPRODUCT({size_sum(rng, 0)}),1)&" e "&'
                               f'ROUND(SUMPRODUCT({size_sum(rng, 1)}),1)&" ore"',
                     S.total(), F["est_total"])

    # 5. Ripartizione delle ore di progetto, on a page of its own
    s5 = r + 2
    ws.set_h_pagebreaks([s5 - 1])
    ws.write_string(s5 - 1, 0, "5. Ripartizione delle ore di progetto", S.section())
    header(ws, S, s5 + 1, ("Tipo di ore", "Oggi (media ultimi 7 giorni)",
                           f"Ottimale per consegnare il {dm(m.delivery)}", "Differenza"), 43.5)
    ws.write_formula(s5, 2, f'="Ottimale per consegnare il "&{dd(B6)}', S.head(),
                     f"Ottimale per consegnare il {dm(m.delivery)}")
    smin = f"SUMPRODUCT({size_sum(rng, 0)})"
    rate7 = f"({OL}$D$6/NETWORKDAYS({OL}$B$6,{OL}$C$6))"
    share = f"MIN(1,({smin}/MAX(1,NETWORKDAYS({B4},{B6})))/{rate7})"
    labels = (*THEME_LABELS, "Fuori perimetro", "Fuori dal prodotto")
    for k, label in enumerate(labels):
        r = s5 + 2 + k
        ws.write_string(r - 1, 0, label, S.cell(bold=True))
        ws.write_formula(r - 1, 1, f"={OL}${'EFGHI'[k]}$13", S.cell(num_format="0%"),
                         number(F["now_share"][k]))
        if k < 3:
            f = (f'=IF(OR({smin}=0,{OL}$D$6=0),0,{share}*SUMPRODUCT(({AT}$C${a}:$C${b}='
                 f'"{label}")*{size_sum(rng, 0)})/{smin})')
        else:
            mine = f"{OL}${'HI'[k - 3]}$13"
            both = f"({OL}$H$13+{OL}$I$13)"
            f = f"=IF({both}=0,0,(1-{share})*{mine}/{both})"
        ws.write_formula(r - 1, 2, f, S.cell(num_format="0%"), number(F["optimal"][k]))
        ws.write_formula(r - 1, 3, f"=C{r}-B{r}", S.cell(num_format=SIGNED_PCT, bold=True),
                         number(F["optimal"][k] - F["now_share"][k]))
    t = s5 + 7
    ws.write_string(t - 1, 0, "Totale", S.total())
    ws.write_formula(t - 1, 1, f"=SUM(B{s5 + 2}:B{s5 + 6})", S.total(num_format="0%"),
                     number(sum(F["now_share"], Fraction(0))))
    ws.write_formula(t - 1, 2, f"=SUM(C{s5 + 2}:C{s5 + 6})", S.total(num_format="0%"),
                     number(sum(F["optimal"], Fraction(0))))
    ws.write_blank(t - 1, 3, None, S.cell(bg_color="#D9E1F2"))
    for rr in range(s5 + 2, s5 + 10):
        ws.set_row(rr - 1, 15.75)
    ws.conditional_format(f"D{s5 + 2}:D{s5 + 6}",
                          {"type": "formula", "criteria": f"=$D{s5 + 2}<-0.05",
                           "format": wb.add_format({"bold": True, "font_color": "#C00000"})})
    for k, (col, title) in enumerate((("B", "Oggi (media ultimi 7 giorni)"),
                                      ("C", f"Ottimale per consegnare il {dm(m.delivery)}"))):
        ch = wb.add_chart({"type": "pie"})
        ch.add_series({
            "name": f"=Riepilogo!${col}${s5 + 1}",
            "categories": f"=Riepilogo!$A${s5 + 2}:$A${s5 + 6}",
            "values": f"=Riepilogo!${col}${s5 + 2}:${col}${s5 + 6}",
            "points": [{"fill": {"color": c}, "border": {"color": "#FFFFFF"}} for c in PIE],
            "data_labels": {"percentage": True, "position": "best_fit", "separator": "\n",
                            "font": {"name": "Arial", "size": 10}},
        })
        ch.set_title({"name": title, "name_font": {"name": "Arial", "size": 18, "bold": True}})
        ch.set_legend({"position": "right", "font": {"name": "Arial", "size": 10}})
        ch.set_chartarea({"fill": {"color": "#FFFFFF"},
                          "border": {"color": "#D9D9D9", "width": 0.75}})
        ch.set_plotarea({"fill": {"none": True}, "border": {"none": True}})
        ch.set_size({"width": 472, "height": 283})
        ws.insert_chart(f"{'AE'[k]}{s5 + 12}", ch)

    # 6. Calendario: on a page of its own, after the pies
    s6 = s5 + 28
    ws.set_h_pagebreaks([s5 - 1, s6 - 1])
    gantt(wb, ws, S, m, F, s6)


def gantt(wb, ws, S, m, F, s6: int):
    """The calendar, in columns B to J: one row per item and per milestone, one slot per day.

    Columns of a spreadsheet cannot be days here, because sections 1 to 5 fix their widths; the
    days are slots of characters in a fixed-width font, so every day has the same width.
    """
    days: list[date] = F["gantt_days"]
    cpd = 3 if len(days) * 3 <= GANTT_CHARS else 2 if len(days) * 2 <= GANTT_CHARS else 1
    if len(days) > GANTT_CHARS:
        days = days[-GANTT_CHARS:]
    index = {d: k for k, d in enumerate(days)}

    def slot(d: date | None) -> int | None:
        if d is None:
            return None
        while d not in index and d >= days[0]:
            d -= timedelta(days=1)          # a weekend counts on the Friday before it
        return index.get(d, 0 if d < days[0] else None)

    mono = {k: wb.add_format({"font_name": MONO, "font_size": 10, "font_color": c})
            for k, c in GANTT_COLOURS.items()}
    mono["plain"] = wb.add_format({"font_name": MONO, "font_size": 10})
    head_mono = wb.add_format({"font_name": MONO, "font_size": 10, "font_color": "#FFFFFF"})
    head_today = wb.add_format({"font_name": MONO, "font_size": 10, "bold": True,
                                "font_color": "#FFC000"})
    bar_cell = S(font_name=MONO, valign="vcenter", border=1, border_color=GREY_BORDER)
    head_cell = S(font_name=MONO, bg_color=NAVY, font_color="#FFFFFF", valign="vcenter",
                  border=1, border_color=GREY_BORDER)
    today = slot(m.when)

    def runs(chars: list[tuple[str, str]]) -> list:
        """Adjacent characters of one colour joined, as XlsxWriter's rich string wants them."""
        out: list = []
        for fmt, ch in chars:
            if out and out[-2] is fmt:
                out[-1] += ch
            else:
                out += [fmt, ch]
        return out

    def write_runs(r: int, parts: list, cell_fmt):
        ws.merge_range(r - 1, 1, r - 1, 9, "", cell_fmt)
        while len(parts) > 2 and parts[-1].strip() == "":
            parts = parts[:-2]
        if len(parts) <= 2:
            ws.write_string(r - 1, 1, parts[1] if parts else "", cell_fmt)
        else:
            ws.write_rich_string(r - 1, 1, *parts, cell_fmt)

    def bar_row(r: int, label: str, segments: list[tuple[int, int, str]], marks=()):
        line = [(mono["plain"], " ") for _ in range(len(days) * cpd)]
        if today is not None:
            mid = today * cpd + (cpd - 1) // 2
            line[mid] = (mono["today"], "│")
        for a, b, colour in segments:
            for k in range(a * cpd, (b + 1) * cpd):
                line[k] = (mono[colour], "█")
        for k, colour in marks:
            line[k * cpd + (cpd - 1) // 2] = (mono[colour], "♦")
        ws.write_string(r - 1, 0, label, S(text_wrap=False, shrink=True, valign="vcenter",
                                           border=1, border_color=GREY_BORDER))
        write_runs(r, runs(line), bar_cell)

    ws.write_string(s6 - 1, 0, "6. Calendario delle attività", S.section())
    months = [" "] * (len(days) * cpd)
    numbers: list[tuple] = [(head_mono, " ")] * (len(days) * cpd)
    previous = None
    for k, d in enumerate(days):
        if d.month != previous:
            for j, ch in enumerate(MONTHS[d.month - 1]):
                if k * cpd + j < len(months):
                    months[k * cpd + j] = ch
            previous = d.month
        if cpd == 3 or d.weekday() == 0 or k == today:
            fmt = head_today if k == today else head_mono
            for j, ch in enumerate(f"{d.day:02d}"):
                if k * cpd + j < len(numbers) and (cpd == 3 or numbers[k * cpd + j][1] == " "):
                    numbers[k * cpd + j] = (fmt, ch)
    ws.write_blank(s6, 0, None, S.head())
    ws.merge_range(s6, 1, s6, 9, "".join(months).rstrip(), head_cell)
    ws.write_string(s6 + 1, 0, "Attività", S.head())
    write_runs(s6 + 2, runs(numbers), head_cell)

    r = s6 + 3
    unknown_start = False
    for g in F["gantt"]:
        if g["kind"] == "done":
            it = g["item"]
            unknown_start |= it.first_day is None
            bar_row(r, f"{it.shown_id} {it.title}",
                    [(slot(g["start"]), slot(g["end"]), "done")])
        elif g["kind"] == "todo":
            it = g["item"]
            if g["end"] is None:
                ws.write_string(r - 1, 0, f"{it.id} {it.title}", S(text_wrap=False, shrink=True,
                                                                    border=1,
                                                                    border_color=GREY_BORDER))
                ws.merge_range(r - 1, 1, r - 1, 9, "non stimabile", S.cell(italic=True))
            else:
                segs = [(slot(g["start"]), slot(g["end"]), "best")]
                if g["worst"] and g["worst"] > g["end"]:
                    segs.append((slot(g["end"]) + 1, slot(g["worst"]), "worst"))
                bar_row(r, f"{it.id} {it.title}", segs)
        else:
            colour = "delivery" if g["kind"] == "delivery" else "milestone"
            bar_row(r, f"{g['name']} ({dm(g['date'])})", [], [(slot(g["date"]), colour)])
        r += 1
    note = wb.add_format({"font_name": "Arial", "font_size": 9, "italic": True,
                          "font_color": "#555555"})
    parts = [note, "Legenda: ", mono["done"], "█", note, " fatta, ", mono["best"], "█", note,
             " da fare nel caso migliore, ", mono["worst"], "█", note,
             " in più nel caso peggiore, ", mono["today"], "│", note, " oggi, ", mono["milestone"],
             "♦", note, " milestone, ", mono["delivery"], "♦", note, " consegna concordata."]
    ws.write_rich_string(r, 0, *parts, note)
    text = ("Le voci da fare sono in fila nell'ordine della tabella «Da fare», al ritmo della "
            "stima del punto 2.")
    if unknown_start:
        text += " Delle voci chiuse prima del dettaglio giorno per giorno si vede solo il giorno " \
                "di chiusura."
    ws.write_string(r + 1, 0, text, S.note())


# ─────────────────────────────────────────────────────────────────────────────

def write(m, F, path, now: datetime) -> None:
    wb = xlsxwriter.Workbook(str(path), {"default_format_properties": {"font_name": "Arial",
                                                                      "font_size": 10}})
    wb.set_properties({"title": f"{m.name} · stato del rilascio al {m.when.strftime('%d/%m/%Y')}",
                       "created": now.replace(tzinfo=None)})
    S = Styles(wb)
    # The summary is the first sheet, and its formulas name the others: XlsxWriter writes the
    # sheets in the order they are added, so the summary is added first and filled last.
    summary = wb.add_worksheet("Riepilogo")
    at = activities(wb, S, m, F)
    hours_sheet(wb, S, m, F)
    shown = [p["item"].shown_id for p in m.plan_rows] + [it.shown_id for it in
                                                         m.todo + m.done + m.out]
    legend_sheet(wb, S, m, shown)
    summary_sheet(wb, summary, S, m, F, at)
    wb.close()
