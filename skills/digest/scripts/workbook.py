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

from datetime import date, datetime
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
MONTHS = ("gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto",
          "settembre", "ottobre", "novembre", "dicembre")
# The bars of the Gantt, by the status of the row; a milestone is a diamond in its day.
BAR = {"fatta": "#BFBFBF", "da fare": "#2A78D6", "bloccata": "#F4B183"}
TODO_STATES = ("da fare", "in corso", "rallentata")


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


def size_top(rng: str) -> str:
    """The hours the estimate counts for the sizes of a range: the top of each one."""
    return "(" + "+".join(f'({rng}="{s}")*{hi}' for s, (_, hi) in SIZE_RANGE.items()) + ")"


def kind_formula(cell: str) -> str:
    out = '""'
    for prefix, label in reversed(PREFIX_LABEL):
        out = f'IF(LEFT({cell},{len(prefix)})="{prefix}","{label}",{out})'
    return "=" + out


def kind_value(i: str) -> str:
    return next((label for prefix, label in PREFIX_LABEL if i.startswith(prefix)), "")


def estimate_formula(cell: str) -> str:
    out = '"da stimare"'
    for s, (_, hi) in reversed(SIZE_RANGE.items()):
        out = f'IF({cell}="{s}","{hi} ore",{out})'
    return "=" + out


def estimate_value(size: str | None) -> str:
    return f"{SIZE_RANGE[size][1]} ore" if size in SIZE_RANGE else "da stimare"


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
    ws.write_formula(t - 1, 5, f'=ROUND(SUMPRODUCT({size_top(rng)}),1)&" ore"', S.total(),
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
        ("S", "da 1 a 2 ore; nella stima conta 2 ore."),
        ("M", "da 3 a 5 ore; nella stima conta 5 ore."),
        ("L", "da 6 a 12 ore; nella stima conta 12 ore."),
        ("XL", "da 13 a 40 ore; nella stima conta 40 ore. Troppo grande per essere stimata bene: "
               "va spezzata in voci più piccole."),
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
        ("Ore stimate", "Ogni voce conta per il massimo della sua taglia: la stima è prudente, e "
                        "la consegna prevista è una data sola."),
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
    late_n = f'(COUNTIF({stat},"SCADUTA*")+COUNTIF({stat},"Scade oggi"))'
    rows = [
        ("Consegna concordata", f"={dmy_f(B6)}", F["B4"], big, 24),
        ("Consegna prevista oggi",
         f'=IF(ISNUMBER(I12),"il "&{dd("I12")},"non stimabile")', F["B5"], big, 24),
        ("Ritardo", '=IF(NOT(ISNUMBER(J12)),"non stimabile",IF(J12=0,"nessuno",'
                    'J12&IF(J12=1," giorno lavorativo"," giorni lavorativi")))', F["B6"], big, 24),
        ("La previsione vale solo se",
         (f'="arriva"&IF(ROWS({stat})=1," in tempo l\'unica cosa richiesta","no in tempo le "&'
          f'ROWS({stat})&" cose richieste")&" ad altri (punto 3). Oggi "&IF({late_n}=0,'
          f'"nessuna è scaduta.",IF({late_n}=1,"1 è scaduta o scade oggi.",'
          f'{late_n}&" sono scadute o scadono oggi."))') if waits else None, F["B7"], small,
         30),
        ("Dove va il tempo", None, F["B8"], small, 30),
    ]
    r8 = (f'="Dall\'inizio del progetto "&(ROUND({OL}E8,0)+ROUND({OL}F8,0)+ROUND({OL}G8,0)+'
          f'ROUND({OL}H8,0)+ROUND({OL}I8,0))&" ore lavorate: "&ROUND({OL}E8,0)&" architettura, "&'
          f'ROUND({OL}F8,0)&" sviluppo, "&ROUND({OL}G8,0)&" deploy, "&ROUND({OL}H8,0)&'
          f'" fuori perimetro, "&ROUND({OL}I8,0)&" fuori dal prodotto ("&'
          f'ROUND({OL}I15*100,0)&"%: riunioni, reportistica, supporto, formazione)."')
    if m.staging is not None:
        # What the expected delivery does not count, where the readers stop: an increment
        # with nothing under it is worth zero hours until somebody breaks it down.
        n = 'COUNTIF(Gantt!$C$5:$C$1000,"da scomporre*")'
        tail = (f'&IF({n}=0,"",IF({n}=1," Non conta 1 incremento ancora da scomporre (vedi '
                f'Gantt).", " Non conta "&{n}&" incrementi ancora da scomporre (vedi '
                f'Gantt)."))')
        label, formula, value, fmt, height = rows[3]
        rows[3] = (label, (formula or '="non dipende da richieste ad altri."') + tail, value,
                   fmt, height)
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
    ws.conditional_format("B6:J6", dict(late, criteria="=AND(ISNUMBER($J$12),$J$12>0)"))

    # 2. Calcolo stima consegna
    ws.write_string(9, 0, "2. Calcolo stima consegna", S.section())
    header(ws, S, 11, ("Caso", "Voci che mancano", "Ore stimate che mancano",
                       "Ore lavorate al giorno (media ultimi 3 giorni)", "meno ore fuori perimetro",
                       "meno ore fuori dal prodotto", "Ore al giorno per il rilascio",
                       "Giorni lavorativi necessari", "Consegna prevista",
                       "Ritardo sulla consegna concordata"), 43.5)
    rng = f"{AT}$E${a}:$E${b}"
    nd3 = f"NETWORKDAYS({OL}$B$5,{OL}$C$5)"
    # One row: every item at the top of its size. Row 13 stays empty, so that every section
    # below sits where the reference workbook has it.
    case, r = F["case"], 12
    ws.write_string(r - 1, 0, "Ogni voce al massimo della sua taglia", S.cell(bold=True))
    if m.todo:
        ws.write_formula(r - 1, 1, f"=COUNTA({AT}$A${a}:$A${b})", S.cell(num_format="0"),
                         case["B"])
    else:
        ws.write_number(r - 1, 1, 0, S.cell(num_format="0"))
    ws.write_formula(r - 1, 2, f"=SUMPRODUCT({size_top(rng)})", S.cell(num_format=HOURS),
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
    ws.conditional_format("J12", dict(late, criteria="=AND(ISNUMBER(J12),J12>0)"))

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
        ws.write_formula(r - 1, 6, f'=ROUND(SUMPRODUCT({sel}*{size_top(rng)}),1)&" ore"',
                         S.cell(), t["est"])
    r = h2 + 4
    first, last = h2 + 1, h2 + 3
    ws.write_string(r - 1, 0, "Totale", S.total())
    sums = [sum(F["themes"][t][k] for t in F["themes"])
            for k in ("done", "prev_closed", "this_closed", "todo", "delta")]
    for c, (letter, v) in enumerate(zip("BCDEF", sums)):
        ws.write_formula(r - 1, 1 + c, f"=SUM({letter}{first}:{letter}{last})",
                         S.total(num_format=SIGNED if letter == "F" else "0"), v)
    ws.write_formula(r - 1, 6, f'=ROUND(SUMPRODUCT({size_top(rng)}),1)&" ore"', S.total(),
                     F["est_total"])

    # 5. Ripartizione delle ore di progetto, on a page of its own
    s5 = r + 2
    ws.set_h_pagebreaks([s5 - 1])
    ws.write_string(s5 - 1, 0, "5. Ripartizione delle ore di progetto", S.section())
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


def gantt_sheet(wb, ws, S, m, F, at: dict) -> None:
    """One row per item and per milestone, one column per working day.

    The items done sit on the days they were worked; the items to do follow one another in the
    order of «Da fare», each for the top of its size, at the hours per day of the estimate, so
    the last one ends on the date of point 2 of the summary. Their first and last day are
    formulas on the sizes in Attività and on that pace; the bars are conditional formats on
    those two dates, so a recalculation moves them.

    When the roadmap orders its increments in stages, the rows are grouped the same way: a
    row per stage, under it a row per increment, whose hours, first and last day are the sum,
    the earliest and the latest of what composes it, and under that its components. A stage
    that names a milestone ends with it, and the status of the milestone is a formula on the
    rows of the stage. The groups fold, closed when the file opens: the stages and the
    milestones in view, the increments one level down, their components two.
    """
    days: list[date] = F["gantt_days"]
    staged = m.staging is not None
    first = 6                                      # column G, the first day
    last = first + len(days) - 1
    # Excel does not open or close a group on a protected sheet, so a Gantt that folds is the
    # one sheet left unprotected.
    setup(ws, {"A": 12 if staged else 10, "B": 36, "C": 18, "D": 11,
               "E": 11, "F": 7}, (4, 6), protect=not staged)
    if staged:
        ws.outline_settings(True, False, True, False)
    ws.set_column(first, last, 3.6)
    ws.write_string(0, 0, "Gantt", S.title())

    head = S.head(align="center", text_wrap=False)
    for c in range(6):
        ws.write_blank(2, c, None, S.cell(bg_color=NAVY))
    k = 0
    while k < len(days):
        j = k
        while j + 1 < len(days) and days[j + 1].month == days[k].month:
            j += 1
        formula = (f"=CHOOSE(MONTH({col_name(first + k)}4),"
                   + ",".join(f'"{x}"' for x in MONTHS) + ")")
        if j > k:
            ws.merge_range(2, first + k, 2, first + j, "", head)
        ws.write_formula(2, first + k, formula, head, MONTHS[days[k].month - 1])
        k = j + 1
    for c, label in enumerate(("Voce", "Titolo", "Stato", "Inizio", "Fine", "Ore")):
        ws.write_string(3, c, label, S.head())
    day_head = S.head(align="center", text_wrap=False, num_format="dd")
    today = f"{CL}$B$4"
    # The first day of the project, or the Monday of the digest's week.
    first_day = (f"=WORKDAY({today}-WEEKDAY({today},3)-1,1)" if F.get("gantt_from_week")
                 else f"=WORKDAY({CL}$B$7-1,1)")
    for k, d in enumerate(days):
        formula = first_day if k == 0 else f"=WORKDAY({col_name(first + k - 1)}4,1)"
        ws.write_formula(3, first + k, formula, day_head, serial(d))
    ws.set_row(3, 21.75)
    ws.conditional_format(3, first, 3, last,
                          {"type": "formula", "criteria": f"={col_name(first)}$4={today}",
                           "format": wb.add_format({"bg_color": "#FFC000",
                                                    "font_color": NAVY})})

    grid = S(border=1, border_color="#E7E6E6")
    when = S.cell(num_format=DATE)
    hours_fmt = S.cell(num_format=HOURS)
    indent = {"indent": 1} if staged else {}
    a, _ = at["todo"]
    G = "Riepilogo!$G$12"
    cached = (lambda d: serial(d) if isinstance(d, date) else "non stimabile")
    stage_fill = S(bold=True, bg_color="#D9E1F2", border=1, border_color=GREY_BORDER)
    r = 5
    todo_k = 0
    rows_first = r
    unknown_start = False
    stage_rows: dict = {}                          # row of a stage -> (stage, its increments)
    spans: dict = {}                               # row of a stage or a group -> [lo, hi, it]
    current_stage = None
    current_span = None
    in_inc = False
    milestone_rows: list[int] = []

    def fold(r: int, level: int, children: bool) -> None:
        """The level of a row in the groups that fold, which exist only with stages."""
        if staged:
            ws.set_row(r - 1, None, None, {"level": level, "hidden": level > 0,
                                           "collapsed": children})

    for g in F["gantt"]:
        kind = g["kind"]
        if kind in ("inc", "todo", "done") and current_span:
            spans[current_span][1] = r
        if kind in ("group", "stage"):
            label = g["name"] if kind == "group" else f"Tappa {g['id']}"
            ws.write_string(r - 1, 0, label, stage_fill)
            ws.write_string(r - 1, 1, g["name"] if kind == "stage" else "", stage_fill)
            for c in range(2, 6):
                ws.write_blank(r - 1, c, None, stage_fill)
            for c in range(first, last + 1):
                ws.write_blank(r - 1, c, None, S(bg_color="#D9E1F2", border=1,
                                                 border_color="#E7E6E6"))
            if kind == "stage":
                current_stage = r
                stage_rows[r] = (g, [])
            else:
                current_stage = None
            current_span = r
            spans[r] = [r + 1, r, g]
            in_inc = False
            fold(r, 0, bool(g["incs"]) if kind == "stage" else True)
        elif kind == "inc":
            n = len(g["rows"])
            ws.write_string(r - 1, 0, g["id"], S.cell(bold=True))
            ws.write_string(r - 1, 1, str(g["title"]), S.cell(bold=True))
            ws.write_string(r - 1, 2, g["status"], S.cell(italic=True))
            if n:
                span_d, span_e = f"D{r + 1}:D{r + n}", f"E{r + 1}:E{r + n}"
                ws.write_formula(r - 1, 3, f'=IF(COUNT({span_d})=0,"non stimabile",'
                                           f'MIN({span_d}))', when, cached(g["start"]))
                ws.write_formula(r - 1, 4, f'=IF(COUNTIF({span_e},"non stimabile")>0,'
                                           f'"non stimabile",MAX({span_e}))',
                                 when, cached(g["end"]))
                ws.write_formula(r - 1, 5, f"=SUM(F{r + 1}:F{r + n})", hours_fmt,
                                 number(g["hours"]))
            else:
                ws.write_blank(r - 1, 3, None, when)
                ws.write_blank(r - 1, 4, None, when)
                ws.write_number(r - 1, 5, 0, hours_fmt)
            for c in range(first, last + 1):
                ws.write_blank(r - 1, c, None, grid)
            if current_stage:
                stage_rows[current_stage][1].append(r)
            in_inc = True
            fold(r, 1, n > 0)
        elif kind in ("done", "todo"):
            it = g["item"]
            ws.write_string(r - 1, 0, it.shown_id, S.cell(bold=True, **indent))
            ws.write_string(r - 1, 1, str(it.title or ""), S.cell(**indent))
            if kind == "done":
                unknown_start |= it.first_day is None
                ws.write_string(r - 1, 2, "fatta", S.cell())
                ws.write_datetime(r - 1, 3, dt(g["start"]), when)
                ws.write_datetime(r - 1, 4, dt(g["end"]), when)
                ws.write_number(r - 1, 5, number(it.hours), hours_fmt)
            else:
                # The first day worked is in the status, «in corso dal 08/10», and not in the
                # bar, which is the item's place in the queue, as for every other item.
                status = short_status(m.status[it.id])
                if g["since"]:
                    status += f" dal {dm(g['since'])}"
                ws.write_string(r - 1, 2, status, S.cell())
                row = a + todo_k
                cum = ("0" if todo_k == 0 else
                       f"SUMPRODUCT({size_top(f'{AT}$E${a}:$E${row - 1}')})")
                own = size_top(f"{AT}$E${row}")
                ws.write_formula(r - 1, 3, f'=IF({G}<=0,"non stimabile",WORKDAY({today}-1,'
                                           f'ROUNDDOWN(ROUND({cum}/{G},9),0)+1))',
                                 when, cached(g["start"]))
                ws.write_formula(r - 1, 4, f'=IF({G}<=0,"non stimabile",WORKDAY({today}-1,'
                                           f'MAX(1,ROUNDUP(ROUND(({cum}+{own})/{G},9),0))))',
                                 when, cached(g["end"]))
                ws.write_formula(r - 1, 5, f"={own}", hours_fmt, number(it.top()))
                todo_k += 1
            for c in range(first, last + 1):
                ws.write_blank(r - 1, c, None, grid)
            fold(r, 2 if in_inc else 1, False)
        else:
            delivery = kind == "delivery"
            ws.write_string(r - 1, 0, "", S.cell())
            ws.write_string(r - 1, 1, g["name"], S.cell(bold=True))
            if kind == "stage_milestone":
                lo, hi = current_stage + 1, r - 1
                span_c, span_e = f"C{lo}:C{hi}", f"E{lo}:E{hi}"
                verdict = (f'=IF(COUNTIF({span_e},"non stimabile")>0,"non stimabile",'
                           f'IF(OR(COUNTIF({span_c},"da scomporre*")>0,COUNT({span_e})=0),'
                           f'"incompleta",IF(MAX({span_e})>D{r},"a rischio","in tempo")))')
                if lo > hi and g["end"]:
                    # Nothing of the stage is shown, because all of it is closed: its last day
                    # is a fact, not a formula on rows that are not there.
                    e = g["end"]
                    verdict = (f'=IF(DATE({e.year},{e.month},{e.day})>D{r},"a rischio",'
                               f'"in tempo")')
                if lo > hi and not g["end"]:
                    # Nothing under the stage at all: incomplete, whatever the date says.
                    ws.write_string(r - 1, 2, g["status"], S.cell(bold=True))
                else:
                    ws.write_formula(r - 1, 2, verdict, S.cell(bold=True), g["status"])
                milestone_rows.append(r)
            else:
                ws.write_string(r - 1, 2, "consegna" if delivery else "milestone", S.cell())
            if delivery:
                ws.write_formula(r - 1, 3, f"={CL}$B$6", when, serial(g["date"]))
            else:
                ws.write_datetime(r - 1, 3, dt(g["date"]), when)
            ws.write_formula(r - 1, 4, f"=D{r}", when, serial(g["date"]))
            ws.write_blank(r - 1, 5, None, S.cell())
            mark = S(bold=True, align="center", border=1, border_color="#E7E6E6",
                     font_color="#C00000" if delivery else "#EB6834")
            # A milestone on a Saturday or a Sunday is marked on the Friday before it.
            shown = max((d for d in days if d <= g["date"]), default=None)
            for k, d in enumerate(days):
                c = col_name(first + k)
                ws.write_formula(r - 1, first + k, f'=IF(WORKDAY($D{r}+1,-1)={c}$4,"◆","")',
                                 mark, "◆" if d == shown else "")
            if kind == "stage_milestone":
                ws.conditional_format(r - 1, first, r - 1, last,
                                      {"type": "formula", "criteria": f'=$C${r}="a rischio"',
                                       "format": wb.add_format({"font_color": "#C00000"})})
            current_stage = None if kind == "stage_milestone" else current_stage
            current_span = None
            in_inc = False
        r += 1
    rows_last = r - 1
    for srow, (stage, incs) in stage_rows.items():
        total = "+".join(f"F{x}" for x in incs) or "0"
        ws.write_formula(srow - 1, 5, f"={total}",
                         S(bold=True, bg_color="#D9E1F2", border=1, border_color=GREY_BORDER,
                           num_format=HOURS),
                         number(sum((h["hours"] for h in stage["incs"]), Fraction(0))))
    # The first and last day of a stage or a group, as those of an increment, on every row it
    # holds: its increments are the MIN and the MAX of their own rows, so they change nothing.
    span_fill = S(bold=True, bg_color="#D9E1F2", border=1, border_color=GREY_BORDER,
                  num_format=DATE)
    for srow, (lo, hi, g) in spans.items():
        if not g["items"]:
            continue
        if g["kind"] == "group":
            # A group holds its items directly: its hours are theirs, as a stage's are those of
            # its increments.
            ws.write_formula(srow - 1, 5, f"=SUM(F{lo}:F{hi})",
                             S(bold=True, bg_color="#D9E1F2", border=1, border_color=GREY_BORDER,
                               num_format=HOURS),
                             number(sum((r["item"].hours if r["kind"] == "done"
                                         else r["item"].top() for r in g["items"]),
                                        Fraction(0))))
        span_d, span_e = f"D{lo}:D{hi}", f"E{lo}:E{hi}"
        ws.write_formula(srow - 1, 3, f'=IF(COUNT({span_d})=0,"non stimabile",MIN({span_d}))',
                         span_fill, cached(g["start"]))
        ws.write_formula(srow - 1, 4, f'=IF(COUNTIF({span_e},"non stimabile")>0,'
                                      f'"non stimabile",MAX({span_e}))',
                         span_fill, cached(g["end"]))

    if rows_last >= rows_first:
        span = (rows_first - 1, first, rows_last - 1, last)
        f0 = f"{col_name(first)}$4"
        inside = f"ISNUMBER($D{rows_first}),{f0}>=$D{rows_first},{f0}<=$E{rows_first}"
        # A status is matched by its start: an item already started says since when after it.
        def is_(state: str) -> str:
            return f'LEFT($C{rows_first},{len(state)})="{state}"'

        rules = [(f"=AND({is_(state)},{inside})", colour)
                 for state, colour in (("fatta", BAR["fatta"]), ("bloccata", BAR["bloccata"]))]
        todo = ",".join(is_(x) for x in TODO_STATES)
        rules.append((f"=AND(OR({todo}),{inside})", BAR["da fare"]))
        rules.append((f"={f0}={today}", "#FFF2CC"))
        if staged:
            # The bar of a stage or a group, darker than that of an increment, under it.
            groups = sorted({g["name"] for g in F["gantt"] if g["kind"] == "group"})
            heads = ",".join([f'LEFT($A{rows_first},6)="Tappa "']
                             + [f'$A{rows_first}="{x}"' for x in groups])
            rules[:0] = [(f"=AND(OR({heads}),{inside})", NAVY),
                         (f'=AND(LEFT($A{rows_first},4)="INC-",{inside})', "#44546A")]
        for criteria, colour in rules:
            ws.conditional_format(*span, {"type": "formula", "criteria": criteria,
                                          "format": wb.add_format({"bg_color": colour})})
        ws.conditional_format(rows_first - 1, 2, rows_last - 1, 2,
                              {"type": "formula", "criteria": f"={is_('bloccata')}",
                               "format": wb.add_format({"bold": True, "font_color": "#9C0006",
                                                        "bg_color": "#F8CBAD"})})
        ws.conditional_format(rows_first - 1, 2, rows_last - 1, 2,
                              {"type": "formula", "criteria": f"={is_('rallentata')}",
                               "format": wb.add_format({"bg_color": "#FCE4D6"})})
        for mr in milestone_rows:
            ws.conditional_format(mr - 1, 2, mr - 1, 2,
                                  {"type": "formula", "criteria": f'=$C${mr}="a rischio"',
                                   "format": wb.add_format({"bold": True,
                                                            "font_color": "#9C0006",
                                                            "bg_color": "#F8CBAD"})})
            ws.conditional_format(mr - 1, 2, mr - 1, 2,
                                  {"type": "formula", "criteria": f'=$C${mr}="in tempo"',
                                   "format": wb.add_format({"bold": True,
                                                            "font_color": "#1B7A50"})})

    notes = ["In grigio le voci fatte, nei giorni in cui ci si è lavorato. In blu le voci da "
             "fare, in arancione chiaro quelle bloccate. In giallo la colonna di oggi.",
             "Le voci da fare sono in fila nell'ordine della tabella «Da fare» del foglio "
             "Attività, ognuna con le ore massime della sua taglia, al ritmo della stima del "
             "Riepilogo (punto 2): l'ultima finisce il giorno della consegna prevista. Una "
             "voce già cominciata sta al suo posto nella fila come le altre, e il giorno in cui "
             "ci si è lavorato la prima volta è nel suo Stato, «in corso dal …».",
             "◆ arancione: milestone. ◆ rosso: consegna concordata."]
    if not F.get("gantt_done", True):
        notes[0] = ("Le voci chiuse non sono mostrate. In blu le voci da fare, in arancione "
                    "chiaro quelle bloccate. In giallo la colonna di oggi.")
    if staged:
        notes[1:1] = [
            "Le voci sono raggruppate per tappa e per incremento, nell'ordine della roadmap. "
            "Un incremento non ha ore sue: vale la somma di ciò che lo compone, prima le "
            "decisioni e i problemi da risolvere, poi le modifiche. La sua barra, in grigio "
            "scuro, va dalla prima all'ultima delle sue voci.",
            "Tappe e incrementi si aprono con il «+» a sinistra: all'apertura si vedono solo "
            "le tappe e le milestone. La barra di una tappa o di un gruppo, in blu scuro, va "
            "dalla prima all'ultima delle sue voci.",
            "Un incremento «da scomporre» non ha ancora niente sotto e non entra nella stima. "
            "La milestone di una tappa è «a rischio» quando l'ultima voce della tappa finisce "
            "dopo la sua data, «incompleta» quando la tappa ha incrementi da scomporre."]
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
