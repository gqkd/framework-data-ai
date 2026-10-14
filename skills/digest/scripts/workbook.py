"""The workbook of the digest: five sheets, every derived cell a formula with its value beside it.

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
CL = "'Come leggerlo'!"
OL = "'Ore lavorate'!"
AT = "Attività!"
THEME_LABELS = ("Architettura", "Sviluppo", "Deploy")
SIZE_RANGE = {"S": (1, 2), "M": (3, 5), "L": (6, 12), "XL": (13, 40)}
PREFIX_LABEL = [("OD-", "Decisione da prendere"), ("DEC-", "Decisione presa"),
                ("CHG-", "Modifica al prodotto"), ("KI-", "Problema noto"),
                ("INC-", "Evoluzione futura"), ("EVR-", "Valutazione")]
MONTHS = ("Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto",
          "Settembre", "Ottobre", "Novembre", "Dicembre")
# The palette of the Gantt, that of the plan its readers agreed on: a bar per status, a lighter
# fill on the cell of the status, the rows of a phase and of an increment tinted, a diamond for
# a milestone, a red line on the date of reference.
BAR = {"fatta": "#BFBFBF", "bloccata": "#E06666", "rallentata": "#F4B183",
       "in corso": "#2E75B6", "da fare": "#9DC3E6"}
STATUS_FILL = {"bloccata": "#F8D7D7", "rallentata": "#FCE4D6", "in corso": "#DDEBF7"}
PHASE_ROW, PHASE_BAR = "#DCE4F0", "#8497B0"
INC_ROW, INC_BAR = "#EEF3F9", "#1F3A5F"
# A phase not broken down yet, lighter than one drawn on its items; a request to others.
OUTLINE_BAR, REQUEST_BAR = "#C9D3E3", "#B4A7D6"
RED = "#C00000"
MARK = {"agreed": RED, "expected": INC_BAR, "milestone": "#EB6834",
        "stage_milestone": "#EB6834"}


def number(x):
    """A Fraction as the number a cell stores: an int when it is one."""
    if isinstance(x, Fraction):
        return int(x) if x.denominator == 1 else float(x)
    return x


def col_name(c: int) -> str:
    """A column's letters, from its index counted from 0."""
    out = ""
    c += 1
    while c:
        c, rem = divmod(c - 1, 26)
        out = chr(65 + rem) + out
    return out


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


def middle(size: str) -> Fraction:
    """The hours the estimate counts for a size: the middle of its range."""
    lo, hi = SIZE_RANGE[size]
    return Fraction(lo + hi, 2)


def comma(x: Fraction) -> str:
    """A number as a cell's text says it, with a decimal comma: «1,5»."""
    return f"{float(x):g}".replace(".", ",")


def size_hours(rng: str) -> str:
    """The hours the estimate counts for the sizes of a range, each at its middle."""
    return "(" + "+".join(f'({rng}="{s}")*{float(middle(s)):g}' for s in SIZE_RANGE) + ")"


def kind_formula(cell: str) -> str:
    out = '""'
    for prefix, label in reversed(PREFIX_LABEL):
        out = f'IF(LEFT({cell},{len(prefix)})="{prefix}","{label}",{out})'
    return "=" + out


def kind_value(i: str) -> str:
    return next((label for prefix, label in PREFIX_LABEL if i.startswith(prefix)), "")


def estimate_formula(cell: str) -> str:
    out = '"da stimare"'
    for s in reversed(SIZE_RANGE):
        out = f'IF({cell}="{s}","{comma(middle(s))} ore",{out})'
    return "=" + out


def estimate_value(size: str | None) -> str:
    return f"{comma(middle(size))} ore" if size in SIZE_RANGE else "da stimare"


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
DATE = "dd/mm/yyyy"


def setup(ws, widths: dict, freeze: tuple | None, protect: bool = True):
    for col, w in widths.items():
        ws.set_column(f"{col}:{col}", w)
    if freeze:
        ws.freeze_panes(*freeze)
    ws.hide_gridlines(2)
    ws.set_landscape()
    ws.set_paper(9)
    ws.fit_to_pages(1, 0)
    ws.set_margins(left=0.75, right=0.75, top=1, bottom=1)
    if protect:
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
    week = [(w["item"], w["status"], False) for w in F["next_week"]]
    pos["week"] = table(r, "1. La prossima settimana", week)
    r = pos["week"][1] + 3

    todo = [(it, m.status[it.id], False) for it in m.todo]
    a, b = pos["todo"] = table(r, "2. Da fare nel perimetro del rilascio", todo)
    t = b + 1
    rng = f"{AT}$E${a}:$E${b}"
    count_cells(ws, S, t, a, b, bool(m.todo))
    ws.write_string(t - 1, 1, "Totale", S.total())
    for c in (2, 3, 4, 6, 7, 8):
        ws.write_blank(t - 1, c, None, S.total())
    ws.write_formula(t - 1, 5, f'=ROUND(SUMPRODUCT({size_hours(rng)}),1)&" ore"', S.total(),
                     F["est_total"])
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


def calendar(table: list) -> list:
    """The days of the table by month and by week: [(first day, [(first day, [index])])].

    A week that runs across two months is split, so that a month holds only its own days."""
    months: list = []
    for k, row in enumerate(table):
        d = row[0]
        if not months or (months[-1][0].year, months[-1][0].month) != (d.year, d.month):
            months.append((d, []))
        weeks = months[-1][1]
        if not weeks or table[weeks[-1][1][-1]][0].isocalendar()[:2] != d.isocalendar()[:2]:
            weeks.append((d, []))
        weeks[-1][1].append(k)
    return months


def hours_sheet(wb, S, m, F) -> None:
    ws = wb.add_worksheet("Ore lavorate")
    # The day by day folds in three levels, the month, the week and the day, and Excel opens
    # no group on a protected sheet: this sheet is not protected, as the Gantt with phases.
    setup(ws, {"A": 30, "B": 12, "D": 11, "E": 13, "F": 11, "I": 12, "J": 14, "L": 11, "M": 13,
               "N": 12}, (2, 0), protect=False)
    ws.outline_settings(True, False, True, False)
    ws.write_string(0, 0, "Ore lavorate", S.title())
    months = calendar(m.table)
    first = 30
    last = first + max(len(m.table) + sum(1 + len(w) for _, w in months), 1) - 1
    col = {c: f"{OL}${c}${first}:${c}${last}" for c in "BCDEFGHIJKLM"}

    ws.write_string(2, 0, "1. Ore per periodo", S.section())
    header(ws, S, 4, WINDOW_HEAD, 30)
    starts = [f"=WORKDAY({CL}$B$4,-{F['pace_days']})", f"={CL}$B$4-7", f"={CL}$B$4-30",
              f"={CL}$B$7"]
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
        ws.write_formula(r - 1, 1, f"=SUBTOTAL(9,{col[src]})", S.cell(num_format=HOURS),
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

    def total(r: int, text: str, n: int, rows: list, fill: str, level: int) -> None:
        """A month or a week: the SUBTOTAL of the n rows under it, which leaves out the
        totals among them, and no date, so that the sums by date above do not count it."""
        style = S.cell(bold=True, bg_color=fill)
        ws.write_string(r - 1, 0, text, style)
        ws.write_blank(r - 1, 1, None, style)
        cols = [sum((row[c] for row in rows), Fraction(0)) for c in range(1, 10)]
        values = ([sum(cols, Fraction(0))] + cols[:4] + [sum(cols[4:], Fraction(0))]
                  + cols[4:])
        for c, v in enumerate(values):
            x = col_name(2 + c)
            ws.write_formula(r - 1, 2 + c, f"=SUBTOTAL(9,{x}{r + 1}:{x}{r + n})",
                             S.cell(bold=True, bg_color=fill, num_format=HOURS), number(v))
        ws.set_row(r - 1, None, None, {"level": level, "collapsed": level == 1})

    r = first
    for d0, weeks in months:
        days = [m.table[k] for _, ks in weeks for k in ks]
        total(r, f"{MONTHS[d0.month - 1]} {d0.year}", len(days) + len(weeks), days, "#D9E1F2",
              0)
        r += 1
        for w0, ks in weeks:
            w1 = m.table[ks[-1]][0]
            total(r, f"settimana del {dm(w0)}" if w0 == w1 else
                  f"settimana dal {dm(w0)} al {dm(w1)}", len(ks), [m.table[k] for k in ks],
                  "#EEF3F9", 1)
            r += 1
            for k in ks:
                day_line(ws, S, r, m.table[k])
                ws.set_row(r - 1, None, None, {"level": 2, "hidden": True})
                r += 1
    ws.write_string(last, 0, "Mesi e settimane si aprono con il «+» a sinistra. I giorni in "
                             "rosso sono sabato e domenica.", S.note())


def day_line(ws, S, r: int, row: list) -> None:
    """One day of the table: its name, its date, its hours by column."""
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
        ("S", "da 1 a 2 ore."),
        ("M", "da 3 a 5 ore."),
        ("L", "da 6 a 12 ore."),
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
        ("Ore stimate", "Ogni voce ha la sua stima in ore, e la consegna prevista è una data "
                        "sola."),
        ("Voci in corso", "Una voce in corso è stimata per quello che le resta da fare. Le ore "
                          "già spese sono indicate a parte."),
        ("Stima di consegna", "Nel Riepilogo, al punto 1."),
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
    a, b = at["todo"]
    waits = m.waits
    w_first = 17
    w_last = w_first + max(len(waits), 1) - 1
    # Three rows and no more: what the delivery is, what it is expected to be, and the delay.
    # What the expectation depends on and where the time goes were taken out on the request of
    # the person who sends the file: the requests to others have a section of their own, and
    # the hours a sheet.
    rows = [
        ("Consegna concordata", f"={dmy_f(B6)}", F["B4"]),
        ("Consegna prevista oggi", f'=IF(ISNUMBER(I12),"il "&{dd("I12")},"non stimabile")',
         F["B5"]),
        ("Ritardo", '=IF(NOT(ISNUMBER(J12)),"non stimabile",IF(J12=0,"nessuno",'
                    'J12&IF(J12=1," giorno lavorativo"," giorni lavorativi")))', F["B6"]),
    ]
    for k, (label, formula, value) in enumerate(rows):
        r = 4 + k
        ws.write_string(r - 1, 0, label, lab)
        ws.merge_range(r - 1, 1, r - 1, 9, "", big)
        ws.write_formula(r - 1, 1, formula, big, value)
        ws.set_row(r - 1, 24)
    late = {"type": "formula", "format": wb.add_format({"bold": True, "font_color": "#C00000",
                                                        "bg_color": "#F8CBAD"})}
    ws.conditional_format("B6:J6", dict(late, criteria="=AND(ISNUMBER($J$12),$J$12>0)"))

    # The estimate of the delivery, in rows the reader does not see: the expected delivery and
    # the delay are formulas on them, and so are the Gantt's days.
    ws.write_string(9, 0, "Calcolo stima consegna", S.section())
    header(ws, S, 11, ("Caso", "Voci che mancano", "Ore stimate che mancano",
                       f"Ore lavorate al giorno (media ultimi {F['pace_days']} giorni)",
                       "meno ore fuori perimetro", "meno ore fuori dal prodotto",
                       "Ore al giorno per il rilascio", "Giorni lavorativi necessari",
                       "Consegna prevista", "Ritardo sulla consegna concordata"), 43.5)
    rng = f"{AT}$E${a}:$E${b}"
    pace_days = f"NETWORKDAYS({OL}$B$5,{OL}$C$5)"
    # One row, the estimate. Row 13 stays empty, so that every section below sits where the
    # reference workbook has it.
    case, r = F["case"], 12
    ws.write_string(r - 1, 0, "Stima", S.cell(bold=True))
    if m.todo:
        ws.write_formula(r - 1, 1, f"=COUNTA({AT}$A${a}:$A${b})", S.cell(num_format="0"),
                         case["B"])
    else:
        ws.write_number(r - 1, 1, 0, S.cell(num_format="0"))
    ws.write_formula(r - 1, 2, f"=SUMPRODUCT({size_hours(rng)})", S.cell(num_format=HOURS),
                     number(case["C"]))
    for c, (src, key) in enumerate((("D", "D"), ("H", "E"), ("I", "F"))):
        ws.write_formula(r - 1, 3 + c, f"=ROUND({OL}${src}$5/{pace_days},1)",
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
    ws.conditional_format("J12", dict(late, criteria="=AND(ISNUMBER(J12),J12>0)"))
    for hidden in range(9, 13):
        ws.set_row(hidden, None, None, {"hidden": True})

    # 2. Cosa serve da altri
    ws.write_string(14, 0, "2. Cosa serve da altri", S.section())
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

    # 3. Avanzamento per tema
    s4 = w_last + 2
    ws.write_string(s4 - 1, 0, "3. Avanzamento per tema", S.section())
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
        ws.write_formula(r - 1, 6, f'=ROUND(SUMPRODUCT({sel}*{size_hours(rng)}),1)&" ore"',
                         S.cell(), t["est"])
    r = h2 + 4
    first, last = h2 + 1, h2 + 3
    ws.write_string(r - 1, 0, "Totale", S.total())
    sums = [sum(F["themes"][t][k] for t in F["themes"])
            for k in ("done", "prev_closed", "this_closed", "todo", "delta")]
    for c, (letter, v) in enumerate(zip("BCDEF", sums)):
        ws.write_formula(r - 1, 1 + c, f"=SUM({letter}{first}:{letter}{last})",
                         S.total(num_format=SIGNED if letter == "F" else "0"), v)
    ws.write_formula(r - 1, 6, f'=ROUND(SUMPRODUCT({size_hours(rng)}),1)&" ore"', S.total(),
                     F["est_total"])

    # 4. Ripartizione delle ore di progetto, on a page of its own
    s5 = r + 2
    ws.set_h_pagebreaks([s5 - 1])
    ws.write_string(s5 - 1, 0, "4. Ripartizione delle ore di progetto", S.section())
    # How the hours are split today, and no more: the split «optimal» to deliver on the agreed
    # date, and its difference from today's, were taken out on the request of the person who
    # sends the file.
    header(ws, S, s5 + 1, ("Tipo di ore", "Oggi (media ultimi 7 giorni)"), 43.5)
    labels = (*THEME_LABELS, "Fuori perimetro", "Fuori dal prodotto")
    for k, label in enumerate(labels):
        r = s5 + 2 + k
        ws.write_string(r - 1, 0, label, S.cell(bold=True))
        ws.write_formula(r - 1, 1, f"={OL}${'EFGHI'[k]}$13", S.cell(num_format="0%"),
                         number(F["now_share"][k]))
    t = s5 + 7
    ws.write_string(t - 1, 0, "Totale", S.total())
    ws.write_formula(t - 1, 1, f"=SUM(B{s5 + 2}:B{s5 + 6})", S.total(num_format="0%"),
                     number(sum(F["now_share"], Fraction(0))))
    for rr in range(s5 + 2, s5 + 8):
        ws.set_row(rr - 1, 15.75)
    # No charts. The reference had two pies under this table, and has one since the split
    # «optimal» went; the person who sends the file asked for them to go: the table says the
    # same in five rows, and the Gantt is the one picture the readers asked for.


# ─────────────────────────────────────────────────────────────────────────────
# Gantt

def short_status(text: str) -> str:
    """The status of a row of «Da fare», in the one word the Gantt has room for."""
    for word in ("Bloccata", "Rallentata", "In corso"):
        if text.startswith(word):
            return word.lower()
    return "da fare"


def label(status: str) -> str:
    """A status as the Gantt prints it, in the words of the plan its readers agreed on."""
    for word, shown in (("da fare", "Da iniziare"), ("fatta", "Chiusa"), ("fatto", "Chiuso")):
        if status.startswith(word):
            return shown + status[len(word):]
    return status[:1].upper() + status[1:]


def last_working(d: date) -> date:
    """The day a milestone is marked on: itself, or the Friday before a Saturday or a Sunday."""
    return d - timedelta(days=max(0, d.weekday() - 4))


def gantt_sheet(wb, ws, S, m, F, at: dict) -> None:
    """The plan its readers agreed on: milestones on top, then the work, one row each.

    Six rows of heading: the title, the date of reference, the legend of the colours, then the
    month, the day and the date of each column of the calendar, which has one column per
    working day for the four weeks before the digest's and the four after, and one per week
    before and after them. Columns A to G say what a row is, who follows it, its status, its
    first and last day and its hours.

    The milestones of the release come first: the agreed delivery, the expected one, which is
    point 1 of the summary, then those the person declared and those of the phases, by date.
    Under them, when the person asked for them, the requests to others still open. Then the
    work. The items done sit on the days they were worked; the items to do follow one another
    in the order of «Da fare», each for the hours of its estimate, at the hours per day of the
    summary, so the last one ends on the expected delivery. Their first and last day are
    formulas on the sizes in Attività and on that pace; the bars are conditional formats on
    those two dates, so a recalculation moves them, and a column of a week holds a bar when the
    item touches that week.

    When the roadmap orders its increments in stages, which the sheet calls phases, the rows
    are grouped the same way: a row per phase, under it a row per increment, whose hours, first
    and last day are the sum, the earliest and the latest of what composes it, and under that
    its components. The status of the milestone of a phase is a formula on the rows of the
    phase. The groups fold, closed when the file opens: the phases in view, the increments one
    level down, their components two.
    """
    days: list = F["gantt_days"]                   # (date, one column for a whole week)
    staged = m.staging is not None
    folds = staged or any(g["level"] for g in F["gantt"])
    first = 7                                      # column H, the first of the calendar
    last = first + len(days) - 1
    # Excel does not open or close a group on a protected sheet, so a Gantt that folds is left
    # unprotected.
    setup(ws, {"A": 12 if staged else 10, "B": 44, "C": 16, "D": 22, "E": 10.5, "F": 10.5,
               "G": 6}, (6, 7), protect=not folds)
    if folds:
        ws.outline_settings(True, False, True, False)
    for k, (_, weekly) in enumerate(days):
        ws.set_column(first + k, first + k, 5.6 if weekly else 3.6)
    today = f"{CL}$B$4"
    grey = "#595959"
    requests = F["gantt_requests"]
    outlined = any(g.get("outline") for g in F["gantt"])

    # Title, date of reference, legend.
    ws.write_string(0, 0, "Gantt", S.title())
    ws.write_string(1, 0, "Data di riferimento", S(bold=True))
    ws.write_formula(1, 2, f"={today}", S(bold=True, num_format=DATE, align="left"),
                     serial(m.when))
    keys = [(BAR[state], "■", label(state))
            for state in ("da fare", "in corso", "rallentata", "bloccata", "fatta")]
    if staged:
        keys += [(PHASE_BAR, "■", "Fase"), (INC_BAR, "■", "Incremento")]
    if outlined:
        keys += [(OUTLINE_BAR, "■", "Fase da dettagliare")]
    if requests:
        keys += [(REQUEST_BAR, "■", "Richiesta ad altri")]
    keys += [(MARK["milestone"], "◆", "Pietra miliare"), (RED, "│", "Data di riferimento")]
    fragments = []
    for colour, sign, text in keys:
        fragments += [S(bold=True, font_color=colour), sign + " ",
                      S(font_color=grey), text + "    "]
    ws.write_rich_string(2, 0, *fragments)

    # Month, day and date of every column of the calendar.
    for r0 in (3, 4):
        for c in range(7):
            ws.write_blank(r0, c, None, S.cell(bg_color=NAVY))
    head = S.head(align="center", text_wrap=False)
    k = 0
    while k < len(days):
        j = k
        while j + 1 < len(days) and (days[j + 1][0].year, days[j + 1][0].month) == \
                (days[k][0].year, days[k][0].month):
            j += 1
        c6 = f"{col_name(first + k)}6"
        formula = (f"=CHOOSE(MONTH({c6})," + ",".join(f'"{x}"' for x in MONTHS)
                   + f')&" "&YEAR({c6})')
        if j > k:
            ws.merge_range(3, first + k, 3, first + j, "", head)
        d0 = days[k][0]
        ws.write_formula(3, first + k, formula, head, f"{MONTHS[d0.month - 1]} {d0.year}")
        k = j + 1
    for c, text in enumerate(("ID", "Attività", "Owner", "Stato", "Inizio", "Fine", "Ore")):
        ws.write_string(5, c, text, S.head())
    letter = S(align="center", font_size=8, font_color=grey)
    stamp = {"bold": True, "align": "center", "font_color": NAVY, "bg_color": INC_ROW,
             "border": 1, "border_color": GREY_BORDER}
    # The first day shown one by one: the Monday four weeks before the digest's, or the
    # Monday of the week the project started when that is later; with `from: week`, the
    # Monday of the digest's week.
    monday = f"{today}-WEEKDAY({today},3)"
    begin = f"{CL}$B$7"
    day_from = (f"={monday}" if F["gantt_from"] == "week" else
                f"=MAX({monday}-{7 * F['window_weeks']},{begin}-WEEKDAY({begin},3))")
    for k, (d, weekly) in enumerate(days):
        c = col_name(first + k)
        prev = f"{col_name(first + k - 1)}6"
        if k == 0 and weekly:                      # the week the project started
            formula = f"={begin}-WEEKDAY({begin},3)"
        elif weekly and days[k - 1][1]:
            formula = f"={prev}+7"
        elif weekly:                               # the first week after the days
            formula = f"={prev}-WEEKDAY({prev},3)+7"
        elif k == 0 or days[k - 1][1]:             # the first day
            formula = day_from
        else:
            formula = f"=WORKDAY({prev},1)"
        ws.write_formula(5, first + k, formula,
                         S(num_format="dd/mm" if weekly else "dd", **stamp), serial(d))
        if weekly:
            ws.write_string(4, first + k, "sett.", letter)
        else:
            ws.write_formula(4, first + k, f'=CHOOSE(WEEKDAY({c}6,2),"L","M","M","G","V","S",'
                                           f'"D")', letter, "LMMGVSD"[d.weekday()])
    ws.set_row(5, 21.75)
    ws.conditional_format(5, first, 5, last,
                          {"type": "formula", "criteria": f"={col_name(first)}$6={today}",
                           "format": wb.add_format({"bg_color": RED, "font_color": "#FFFFFF"})})

    grid = S(border=1, border_color="#E7E6E6")
    when = S.cell(num_format=DATE)
    hours_fmt = S.cell(num_format=HOURS)
    indent = {"indent": 1} if staged else {}
    a, _ = at["todo"]
    G = "Riepilogo!$G$12"
    cached = (lambda d: serial(d) if isinstance(d, date) else "non stimabile")
    milestone_rows: list[int] = []
    c0 = col_name(first)
    # The last day a column covers: itself, or the Sunday of its week.
    col_end = f'{c0}$6+IF({c0}$5="sett.",6,0)'

    def owner(r: int, who, **kw) -> None:
        if who:
            ws.write_string(r - 1, 2, str(who), S.cell(**kw))
        else:
            ws.write_blank(r - 1, 2, None, S.cell(**kw))

    def tint(r: int, colour: str | None) -> None:
        for c in range(first, last + 1):
            ws.write_blank(r - 1, c, None, S(bg_color=colour, border=1, border_color="#E7E6E6")
                           if colour else grid)

    def block_head(r: int, text: str) -> None:
        ws.write_string(r - 1, 0, text, S(bold=True, font_color=NAVY))

    def milestone(r: int, g: dict) -> None:
        """A row with a date and a diamond on it."""
        ws.write_string(r - 1, 0, "—", S.cell(align="center"))
        ws.write_string(r - 1, 1, g["name"], S.cell(bold=True))
        owner(r, g.get("owner"))
        d = g["date"]
        if g["kind"] == "agreed":
            ws.write_formula(r - 1, 4, f"={CL}$B$6", when, serial(d))
        elif g["kind"] == "expected":
            ws.write_formula(r - 1, 4, "=Riepilogo!$I$12", when, cached(d))
        else:
            ws.write_datetime(r - 1, 4, dt(d), when)
        ws.write_formula(r - 1, 5, f"=E{r}", when, cached(d))
        ws.write_blank(r - 1, 6, None, S.cell())
        mark = S(bold=True, align="center", border=1, border_color="#E7E6E6",
                 font_color=MARK[g["kind"]])
        for k, (day, weekly) in enumerate(days):
            c = col_name(first + k)
            if weekly:
                test = f"AND($E{r}>={c}$6,$E{r}<={c}$6+6)"
                on = isinstance(d, date) and day <= d <= day + timedelta(days=6)
            else:
                test = f"WORKDAY($E{r}+1,-1)={c}$6"
                on = isinstance(d, date) and last_working(d) == day
            ws.write_formula(r - 1, first + k, f'=IF(ISNUMBER($E{r}),IF({test},"◆",""),"")',
                             mark, "◆" if on else "")
        milestone_rows.append(r)

    # The milestones of the release, and those of the phases, by date.
    r = 7
    block_head(r, "PIETRE MILIARI")
    r += 1
    rows_first = r
    verdicts: list = []                            # (row on top, milestone of a phase)
    for g in F["gantt_top"]:
        milestone(r, g)
        if g["kind"] == "agreed":
            ws.write_string(r - 1, 3, g["status"], S.cell(bold=True))
        elif g["kind"] == "expected":
            ws.write_formula(r - 1, 3, '=IF(ISNUMBER(Riepilogo!$J$12),IF(Riepilogo!$J$12>0,'
                                       '"Ritardo "&Riepilogo!$J$12&" gg lav.","In tempo"),'
                                       '"Non stimabile")', S.cell(bold=True), g["status"])
        elif g["kind"] == "stage_milestone":
            verdicts.append((r, g))                # a formula on the rows of its phase, below
            ws.conditional_format(r - 1, first, r - 1, last,
                                  {"type": "formula", "criteria": f'=$D${r}="A rischio"',
                                   "format": wb.add_format({"font_color": RED})})
        else:
            ws.write_string(r - 1, 3, g["status"], S.cell())
        r += 1
    r += 1

    # The requests to others still open, of those the person named: a bar from the day of the
    # request to the day it is needed by, red after that day up to today.
    if requests:
        block_head(r, "COSA SERVE DA ALTRI")
        r += 1
        req_first = r
        for x in requests:
            w = x["wait"]
            ws.write_blank(r - 1, 0, None, S.cell())
            ws.write_string(r - 1, 1, str(w["what"]), S.cell())
            owner(r, w["owner"])
            ws.write_formula(r - 1, 3, f'=IF(F{r}<{today},"Scaduta da "&({today}-F{r})&'
                                       f'IF({today}-F{r}=1," giorno"," giorni"),IF(F{r}={today},'
                                       f'"Scade oggi","Entro "&(F{r}-{today})&'
                                       f'IF(F{r}-{today}=1," giorno"," giorni")))',
                             S.cell(bold=True), x["status"])
            ws.write_datetime(r - 1, 4, dt(x["asked"]), when)
            ws.write_datetime(r - 1, 5, dt(x["needed_by"]), when)
            ws.write_blank(r - 1, 6, None, S.cell())
            tint(r, None)
            r += 1
        rq = (req_first - 1, first, r - 2, last)
        rf = req_first
        for criteria, colour in (
                (f"AND($F{rf}<{today},{col_end}>$F{rf},{c0}$6<={today})", BAR["bloccata"]),
                (f"AND(ISNUMBER($E{rf}),{col_end}>=WORKDAY($E{rf}+1,-1),"
                 f"{c0}$6<=WORKDAY($F{rf}+1,-1))", REQUEST_BAR)):
            ws.conditional_format(*rq, {"type": "formula", "criteria": "=" + criteria,
                                        "format": wb.add_format({"bg_color": colour})})
        ws.conditional_format(req_first - 1, 3, r - 2, 3,
                              {"type": "formula", "criteria": f'=LEFT($D{rf},7)="Scaduta"',
                               "format": wb.add_format({"bold": True, "font_color": "#9C0006",
                                                        "bg_color": STATUS_FILL["bloccata"]})})
        ws.conditional_format(req_first - 1, 3, r - 2, 3,
                              {"type": "formula", "criteria": f'=$D{rf}="Scade oggi"',
                               "format": wb.add_format({"bg_color": STATUS_FILL["rallentata"]})})
        r += 1

    # The work.
    todo_k = 0
    unknown_start = False
    row_of: dict = {}                              # id of a row of F["gantt"] -> its row here

    def fold(r: int, level: int, children: bool) -> None:
        """The level of a row in the groups that fold."""
        if folds:
            ws.set_row(r - 1, None, None, {"level": level, "hidden": level > 0,
                                           "collapsed": children})

    phase_fill = S(bold=True, bg_color=PHASE_ROW, border=1, border_color=GREY_BORDER)
    inc_cell = {"bg_color": INC_ROW}
    for g in F["gantt"]:
        kind = g["kind"]
        row_of[id(g)] = r
        if kind in ("group", "stage"):
            ws.write_string(r - 1, 0, g["code"] if kind == "stage" else "", phase_fill)
            ws.write_string(r - 1, 1, g["name"], phase_fill)
            for c in range(2, 7):
                ws.write_blank(r - 1, c, None, phase_fill)
            if g.get("outline"):
                # Not broken down yet: the days the plan gives it, no hours, nothing under it.
                ws.write_string(r - 1, 3, label(g["status"]),
                                S(italic=True, bg_color=PHASE_ROW, border=1,
                                  border_color=GREY_BORDER))
                for c, d in ((4, g["start"]), (5, g["end"])):
                    ws.write_datetime(r - 1, c, dt(d),
                                      S(bold=True, bg_color=PHASE_ROW, border=1,
                                        border_color=GREY_BORDER, num_format=DATE))
            tint(r, PHASE_ROW)
            fold(r, 0, bool(g["members"]))
        elif kind == "inc":
            n = len(g["rows"])
            ws.write_string(r - 1, 0, g["id"], S.cell(bold=True, **inc_cell))
            ws.write_string(r - 1, 1, str(g["title"]), S.cell(bold=True, **inc_cell))
            owner(r, g.get("owner"), **inc_cell)
            ws.write_string(r - 1, 3, label(g["status"]), S.cell(italic=True, **inc_cell))
            fill_when = S.cell(num_format=DATE, **inc_cell)
            if n:
                span_e, span_f = f"E{r + 1}:E{r + n}", f"F{r + 1}:F{r + n}"
                ws.write_formula(r - 1, 4, f'=IF(COUNT({span_e})=0,"non stimabile",'
                                           f'MIN({span_e}))', fill_when, cached(g["start"]))
                ws.write_formula(r - 1, 5, f'=IF(COUNTIF({span_f},"non stimabile")>0,'
                                           f'"non stimabile",MAX({span_f}))',
                                 fill_when, cached(g["end"]))
                ws.write_formula(r - 1, 6, f"=SUM(G{r + 1}:G{r + n})",
                                 S.cell(num_format=HOURS, **inc_cell), number(g["hours"]))
            else:
                ws.write_blank(r - 1, 4, None, fill_when)
                ws.write_blank(r - 1, 5, None, fill_when)
                ws.write_number(r - 1, 6, 0, S.cell(num_format=HOURS, **inc_cell))
            tint(r, INC_ROW)
            fold(r, g["level"], n > 0)
        else:
            it = g["item"]
            ws.write_string(r - 1, 0, it.shown_id, S.cell(bold=True, **indent))
            ws.write_string(r - 1, 1, str(it.title or ""), S.cell(**indent))
            owner(r, g.get("owner"))
            if kind == "done":
                unknown_start |= it.first_day is None
                ws.write_string(r - 1, 3, label("fatta"), S.cell())
                ws.write_datetime(r - 1, 4, dt(g["start"]), when)
                ws.write_datetime(r - 1, 5, dt(g["end"]), when)
                ws.write_number(r - 1, 6, number(it.hours), hours_fmt)
            else:
                # The first day worked is in the status, «In corso dal 08/10», and not in the
                # bar, which is the item's place in the queue, as for every other item. A
                # blocked item says what it waits for and from whom.
                status = short_status(m.status[it.id])
                if status == "bloccata" and m.blockers.get(it.id):
                    status += f" da {m.blockers[it.id]}"
                    if g["since"]:
                        status += f", iniziata il {dm(g['since'])}"
                elif g["since"]:
                    status += f" dal {dm(g['since'])}"
                ws.write_string(r - 1, 3, label(status), S.cell())
                row = a + todo_k
                cum = ("0" if todo_k == 0 else
                       f"SUMPRODUCT({size_hours(f'{AT}$E${a}:$E${row - 1}')})")
                own = size_hours(f"{AT}$E${row}")
                ws.write_formula(r - 1, 4, f'=IF({G}<=0,"non stimabile",WORKDAY({today}-1,'
                                           f'ROUNDDOWN(ROUND({cum}/{G},9),0)+1))',
                                 when, cached(g["start"]))
                ws.write_formula(r - 1, 5, f'=IF({G}<=0,"non stimabile",WORKDAY({today}-1,'
                                           f'MAX(1,ROUNDUP(ROUND(({cum}+{own})/{G},9),0))))',
                                 when, cached(g["end"]))
                ws.write_formula(r - 1, 6, f"={own}", hours_fmt, number(it.estimate()))
                todo_k += 1
            tint(r, None)
            fold(r, g["level"], False)
        r += 1
    rows_last = r - 1

    # A phase or a group spans the rows it holds: its first and last day are those of an
    # increment, on every row under it, whose MIN and MAX change nothing. A phase's hours are
    # those of its increments; a group's, of the items it holds directly.
    total_fill = S(bold=True, bg_color=PHASE_ROW, border=1, border_color=GREY_BORDER,
                   num_format=HOURS)
    span_fill = S(bold=True, bg_color=PHASE_ROW, border=1, border_color=GREY_BORDER,
                  num_format=DATE)
    spans: dict = {}                               # id of a phase -> (first, last row under it)
    for g in F["gantt"]:
        if g["kind"] not in ("stage", "group") or g.get("outline") or not g["members"]:
            continue
        srow = row_of[id(g)]
        lo, hi = srow + 1, max(row_of[id(x)] for x in g["members"])
        spans[id(g)] = (lo, hi)
        if g["kind"] == "stage":
            incs = [row_of[id(x)] for x in g["incs"]]
            ws.write_formula(srow - 1, 6, "=" + ("+".join(f"G{x}" for x in incs) or "0"),
                             total_fill, number(sum((x["hours"] for x in g["incs"]),
                                                    Fraction(0))))
        else:
            ws.write_formula(srow - 1, 6, f"=SUM(G{lo}:G{hi})", total_fill,
                             number(sum((x["item"].hours if x["kind"] == "done"
                                         else x["item"].estimate() for x in g["items"]),
                                        Fraction(0))))
        if not g["items"]:
            continue
        span_e, span_f = f"E{lo}:E{hi}", f"F{lo}:F{hi}"
        ws.write_formula(srow - 1, 4, f'=IF(COUNT({span_e})=0,"non stimabile",MIN({span_e}))',
                         span_fill, cached(g["start"]))
        ws.write_formula(srow - 1, 5, f'=IF(COUNTIF({span_f},"non stimabile")>0,'
                                      f'"non stimabile",MAX({span_f}))',
                         span_fill, cached(g["end"]))

    # What the milestone of a phase says, on the rows of its phase.
    for sr, g in verdicts:
        lo, hi = spans.get(id(g["phase"]), (0, -1))
        e = g["end"]
        if lo <= hi:
            span_d, span_f = f"D{lo}:D{hi}", f"F{lo}:F{hi}"
            verdict = (f'=IF(COUNTIF({span_f},"non stimabile")>0,"Non stimabile",'
                       f'IF(OR(COUNTIF({span_d},"da scomporre*")>0,COUNT({span_f})=0),'
                       f'"Incompleta",IF(MAX({span_f})>E{sr},"A rischio","In tempo")))')
            ws.write_formula(sr - 1, 3, verdict, S.cell(bold=True), label(g["status"]))
        elif e and g["status"] in ("a rischio", "in tempo"):
            # Nothing of the phase is shown, because all of it is closed: its last day is a
            # fact, not a formula on rows that are not there.
            ws.write_formula(sr - 1, 3, f'=IF(DATE({e.year},{e.month},{e.day})>E{sr},'
                                        f'"A rischio","In tempo")',
                             S.cell(bold=True), label(g["status"]))
        else:
            ws.write_string(sr - 1, 3, label(g["status"]), S.cell(bold=True))

    if rows_last >= rows_first:
        span = (rows_first - 1, first, rows_last - 1, last)
        rf = rows_first
        # A column of a day holds a bar on that day, and one of a week when the item touches
        # it; an item that starts or ends on a Saturday or a Sunday, on the Friday before.
        inside = (f"ISNUMBER($E{rf}),{col_end}>=WORKDAY($E{rf}+1,-1),"
                  f"{c0}$6<=WORKDAY($F{rf}+1,-1)")

        # A status is matched by its start: an item already started says since when after it.
        def is_(state: str) -> str:
            return f'LEFT($D{rf},{len(state)})="{state}"'

        rules = [(f"=AND({is_(label(state))},{inside})", colour)
                 for state, colour in BAR.items()]
        if outlined:
            rules.append((f"=AND({is_(label('da dettagliare'))},{inside})", OUTLINE_BAR))
        if folds:
            # A phase or a group has no status of its own, an increment its own colour.
            rules[:0] = [(f'=AND($D{rf}="",{inside})', PHASE_BAR),
                         (f'=AND(LEFT($A{rf},4)="INC-",{inside})', INC_BAR)]
        for criteria, colour in rules:
            ws.conditional_format(*span, {"type": "formula", "criteria": criteria,
                                          "format": wb.add_format({"bg_color": colour})})
        # The date of reference, a red line down the calendar.
        ws.conditional_format(*span, {"type": "formula", "criteria": f"={c0}$6={today}",
                                      "format": wb.add_format({"left": 2, "left_color": RED})})
        for state, colour in STATUS_FILL.items():
            ws.conditional_format(rf - 1, 3, rows_last - 1, 3,
                                  {"type": "formula", "criteria": f"={is_(label(state))}",
                                   "format": wb.add_format({"bg_color": colour})})
        for mr in milestone_rows:
            ws.conditional_format(mr - 1, 3, mr - 1, 3,
                                  {"type": "formula",
                                   "criteria": f'=OR($D${mr}="A rischio",LEFT($D${mr},7)='
                                               f'"Ritardo")',
                                   "format": wb.add_format({"bold": True, "font_color": "#9C0006",
                                                            "bg_color": STATUS_FILL["bloccata"]})})
            ws.conditional_format(mr - 1, 3, mr - 1, 3,
                                  {"type": "formula", "criteria": f'=$D${mr}="In tempo"',
                                   "format": wb.add_format({"bold": True,
                                                            "font_color": "#1B7A50"})})

    shown = F["gantt_done"]
    weeks = ("una", "due", "tre", "quattro", "cinque", "sei")[F["window_weeks"] - 1]
    recent = next((g["name"] for g in F["gantt"] if g["kind"] == "group"
                   and g["name"].startswith("Chiuso dal")), None)
    notes = ["Barre: azzurro le voci da iniziare, blu quelle in corso, arancione chiaro le "
             "rallentate, rosso le bloccate, grigio le chiuse, nei giorni in cui ci si è "
             "lavorato. La linea rossa è la data di riferimento.",
             f"Le {weeks} settimane prima di questa e le {weeks} dopo hanno una colonna per "
             "giorno lavorativo; prima e dopo, una colonna per settimana "
             "(«sett.», col suo lunedì), che una barra occupa quando la voce tocca quella "
             "settimana. Una voce chiusa di sabato o di domenica sta sul venerdì prima.",
             "Le voci da fare sono in fila nell'ordine della tabella «Da fare» del foglio "
             "Attività, ognuna con le ore della sua stima, al ritmo del Riepilogo: l'ultima "
             "finisce il giorno della consegna prevista. Una voce già cominciata sta al suo "
             "posto nella fila come le altre, e il giorno in cui ci si è lavorato la prima "
             "volta è nel suo Stato, «In corso dal …». Una voce bloccata dice che cosa aspetta "
             "e da chi.",
             "Owner: chi segue la voce, come dichiarato; vuoto finché nessuno l'ha indicato.",
             "In testa le pietre miliari: ◆ rosso la consegna concordata, ◆ blu la consegna "
             "prevista, ◆ arancione le altre."]
    if shown is False:
        notes[0] = ("Le voci chiuse non sono mostrate. Barre: azzurro le voci da iniziare, blu "
                    "quelle in corso, arancione chiaro le rallentate, rosso le bloccate. La "
                    "linea rossa è la data di riferimento.")
    elif shown == "recent":
        notes[0] = ("Barre: azzurro le voci da iniziare, blu quelle in corso, arancione chiaro "
                    "le rallentate, rosso le bloccate. Delle voci chiuse si vedono solo quelle "
                    "chiuse dal primo giorno mostrato giorno per giorno, in grigio, nel gruppo "
                    f"«{recent or 'Chiuso dal …'}» che si apre con il «+» a sinistra. La linea "
                    "rossa è la data di riferimento.")
    if requests:
        notes.append("Sotto le pietre miliari, le richieste ad altri ancora aperte, con chi "
                     "deve rispondere nella colonna Owner: in viola dal giorno della richiesta "
                     "alla scadenza, in rosso i giorni dopo la scadenza, fino a oggi.")
    if staged:
        notes[2:2] = [
            "Le voci sono raggruppate per fase e per incremento, nell'ordine della roadmap. "
            "Un incremento non ha ore sue: vale la somma di ciò che lo compone, prima le "
            "decisioni e i problemi da risolvere, poi le modifiche. La sua barra, in blu "
            "scuro, va dalla prima all'ultima delle sue voci; quella di una fase o di un "
            "gruppo, più chiara, dalla prima all'ultima delle voci che contiene.",
            "Fasi e incrementi si aprono con il «+» a sinistra: all'apertura si vedono le "
            "pietre miliari" + (", le richieste ad altri" if requests else "")
            + " e le fasi.",
            "Un incremento «Da scomporre» non ha ancora niente sotto e non entra nella stima. "
            "La pietra miliare di una fase è «A rischio» quando l'ultima voce della fase "
            "finisce dopo la sua data, «Incompleta» quando la fase ha incrementi da "
            "scomporre."]
    if outlined:
        notes.append("Una fase «Da dettagliare» non è ancora scomposta in voci e non entra "
                     "nella stima: la sua barra, più chiara, va dal primo all'ultimo giorno "
                     "che le dà il piano.")
    if unknown_start:
        notes.append("Delle voci chiuse prima del dettaglio giorno per giorno si vede solo il "
                     "giorno di chiusura.")
    for k, text in enumerate(notes):
        ws.write_string(r + k, 0, text, S.note())


# ─────────────────────────────────────────────────────────────────────────────

def write(m, F, path, now: datetime) -> None:
    wb = xlsxwriter.Workbook(str(path), {"default_format_properties": {"font_name": "Arial",
                                                                      "font_size": 10}})
    wb.set_properties({"title": f"{m.name} · stato del rilascio al {m.when.strftime('%d/%m/%Y')}",
                       "created": now.replace(tzinfo=None)})
    S = Styles(wb)
    # The summary and the Gantt are the first two sheets, and their formulas name the others:
    # XlsxWriter writes the sheets in the order they are added, so those two are added first
    # and filled last.
    summary = wb.add_worksheet("Riepilogo")
    gantt = wb.add_worksheet("Gantt")
    at = activities(wb, S, m, F)
    hours_sheet(wb, S, m, F)
    shown = [w["item"].shown_id for w in F["next_week"]] + [it.shown_id for it in
                                                           m.todo + m.done + m.out]
    legend_sheet(wb, S, m, shown)
    summary_sheet(wb, summary, S, m, F, at)
    gantt_sheet(wb, gantt, S, m, F, at)
    wb.close()
