#!/usr/bin/env python3
"""The pictures in the README, drawn by code so that they can be drawn again.

    python3 docs/readme/build.py                  write the PNGs beside this file
    python3 docs/readme/build.py --keep-html DIR  also keep the page each PNG is taken from
    python3 docs/readme/build.py --only skills    draw one picture, both themes

WHY A SCRIPT AND NOT A DRAWING. `Framework.drawio` was the drawing, and it has not been
redrawn since 2026-08-06: a picture nobody can regenerate is a copy of the truth with a date
on it. These are three SVGs written by the functions below, each in a light and a dark variant
from the same coordinates, so the two cannot disagree, and a change is an edit here and one
command. All three are drawn by hand from what `FRAMEWORK.md`, `framework-flow.mermaid.md`,
`SKILLS.md` and the skills, `validate.py` and `ci/`, `references/additive.md`, `work.py` and
`todo.py` say, and none carries a count: a number in a picture goes stale the way a number in
prose does.

WHAT IT NEEDS, AND WHAT IT DOES NOT CHECK. `pip install playwright` and `playwright install
chromium`, which the framework itself does not need and `requirements.txt` does not carry, and
the network for the fonts (Geist, Geist Mono, Instrument Serif). The script refuses to write a
picture in which a text overflows the box or the label it was placed in, the defect a person
reviewing a PNG misses; it does not see two elements that overlap, and nothing in CI renders
the pictures, because a PNG is not byte-stable across browser versions.

NOTHING CHECKS THAT THE PICTURES ARE CURRENT, AND THAT IS A CHOICE. A check that needs no
render was possible -- a stamp of what was drawn, recomputed by the self check from the
sources -- and the owner chose to declare the gap instead. So any of these leaves a picture
wrong with every check green, until whoever made the change runs this script in the same
commit:

- `FRAMEWORK.md` §4, the folder tree, whose root files and folders the first picture lists
  inside the repository;
- `FRAMEWORK.md` §5-6 and `framework-flow.mermaid.md`: a phase, a gate or an exit that moves;
- the skills, `SKILLS.md` and each `SKILL.md`: one added or renamed, or what one does, what it
  produces, where it keeps it and the sentence it answers to; and `validate.py` with the
  workflows in `ci/`, for what checks the repository and where;
- `references/additive.md`, `work.py` and `todo.py`: where a thread, a parking branch or the
  effects are written, the commands that open them, how the threads are computed, who runs
  the join and what it does.

This list is the one place the rule is written; the README points here.

THE LOOK is that of an explainer rather than of a specification: a colour per stage, cards,
numbered steps and icons, a title inside the picture. The connectors keep the rules of the
diagram-design skill -- orthogonal, rounded corners, a label never on its own line.
"""
from __future__ import annotations

import argparse
import math
import pathlib
import sys
import tempfile
import textwrap
from xml.sax.saxutils import escape

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent

FONTS = ("https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1"
         "&family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap")
SANS, MONO, SERIF = "'Geist', sans-serif", "'Geist Mono', monospace", "'Instrument Serif', serif"
W = 960

# A hue is (fill, stroke, text): the tint a card is washed with, the colour of its edge and
# icon, and the colour a word takes on that tint.
LIGHT = dict(
    name="light", bg="#f7f8fa", dot="rgba(31,36,48,0.07)", card="#ffffff", ink="#1f2430",
    muted="#5b6475", soft="#8a93a3", line="#9aa3b2", shadow="rgba(31,36,48,0.10)",
    blue=("#eaf1ff", "#3d6fe0", "#2457c5"), violet=("#f1ebff", "#7b52e0", "#5e37c2"),
    green=("#e7f7ef", "#1f9e68", "#137a4f"), amber=("#fff3e2", "#e08a24", "#a85d08"),
    coral=("#fff0e9", "#eb6c36", "#c4501f"), slate=("#eef1f5", "#8a93a3", "#4a5262"))
DARK = dict(
    name="dark", bg="#0f1520", dot="rgba(238,241,246,0.06)", card="#171e2b", ink="#eef1f6",
    muted="#a7b0c0", soft="#7d8798", line="#5d6879", shadow="rgba(0,0,0,0.45)",
    blue=("rgba(96,140,255,0.14)", "#6f9bff", "#a3bfff"),
    violet=("rgba(160,125,255,0.15)", "#a98bff", "#cbb8ff"),
    green=("rgba(60,200,130,0.13)", "#4fd18f", "#8fe6ba"),
    amber=("rgba(245,165,74,0.14)", "#f5a54a", "#f8c78c"),
    coral=("rgba(240,138,89,0.16)", "#f08a59", "#f7b493"),
    slate=("rgba(140,150,170,0.14)", "#7d8798", "#c2c9d6"))

ICONS = {  # 24x24, stroked
    "file": '<path d="M14 3v4a1 1 0 0 0 1 1h4"/><path d="M17 21h-10a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2h7l5 5v11a2 2 0 0 1 -2 2"/>',
    "log": '<path d="M14 3v4a1 1 0 0 0 1 1h4"/><path d="M17 21h-10a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2h7l5 5v11a2 2 0 0 1 -2 2"/><path d="M9 9l1 0"/><path d="M9 13l6 0"/><path d="M9 17l6 0"/>',
    "branch": '<path d="M5 18a2 2 0 1 0 4 0a2 2 0 1 0 -4 0"/><path d="M5 6a2 2 0 1 0 4 0a2 2 0 1 0 -4 0"/><path d="M15 6a2 2 0 1 0 4 0a2 2 0 1 0 -4 0"/><path d="M7 8l0 8"/><path d="M9 18h6a2 2 0 0 0 2 -2v-5"/><path d="M14 14l3 -3l3 3"/>',
    "robot": '<path d="M6 6a2 2 0 0 1 2 -2h8a2 2 0 0 1 2 2v4a2 2 0 0 1 -2 2h-8a2 2 0 0 1 -2 -2l0 -4"/><path d="M12 2v2"/><path d="M9 12v9"/><path d="M15 12v9"/><path d="M5 16l4 -2"/><path d="M15 14l4 2"/><path d="M9 18h6"/><path d="M10 8v.01"/><path d="M14 8v.01"/>',
    "users": '<path d="M5 7a4 4 0 1 0 8 0a4 4 0 1 0 -8 0"/><path d="M3 21v-2a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v2"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/><path d="M21 21v-2a4 4 0 0 0 -3 -3.85"/>',
    "test": '<path d="M20 8.04l-12.122 12.124a2.857 2.857 0 1 1 -4.041 -4.04l12.122 -12.124"/><path d="M7 13h8"/><path d="M19 15l1.5 1.6a2 2 0 1 1 -3 0l1.5 -1.6"/><path d="M15 3l6 6"/>',
    "pipeline": '<path d="M5 18a2 2 0 1 0 4 0a2 2 0 1 0 -4 0"/><path d="M5 6a2 2 0 1 0 4 0a2 2 0 1 0 -4 0"/><path d="M15 12a2 2 0 1 0 4 0a2 2 0 1 0 -4 0"/><path d="M7 8l0 8"/><path d="M7 8a4 4 0 0 0 4 4h4"/>',
}


def rounded(points: list[tuple[int, int]], r: int = 10) -> str:
    """An orthogonal polyline through `points`, each interior corner a quarter turn of `r`."""
    d = [f"M {points[0][0]},{points[0][1]}"]
    for i in range(1, len(points) - 1):
        (x0, y0), (x1, y1), (x2, y2) = points[i - 1], points[i], points[i + 1]
        if (x0 != x1 and y0 != y1) or (x1 != x2 and y1 != y2):
            sys.exit(f"diagonal segment through {points[i]}: connectors are orthogonal")
        ix, iy = (x1 > x0) - (x1 < x0), (y1 > y0) - (y1 < y0)
        ox, oy = (x2 > x1) - (x2 < x1), (y2 > y1) - (y2 < y1)
        d.append(f"L {x1 - ix * r},{y1 - iy * r} Q {x1},{y1} {x1 + ox * r},{y1 + oy * r}")
    d.append(f"L {points[-1][0]},{points[-1][1]}")
    return " ".join(d)


def width(s: str, size: float, family: str = SANS, weight: int = 400) -> float:
    """What a line is expected to take: exact for the monospace, a safe guess for Geist."""
    if family == MONO:
        return len(s) * size * 0.6
    return len(s) * size * (0.58 if weight >= 600 else 0.53)


class Svg:
    """One picture in one theme: a header that stays put, and a body below it."""

    def __init__(self, slug: str, height: int, t: dict, title: str, desc: str, top: int = 0):
        self.slug, self.h, self.t, self.top = f"{slug}-{t['name']}", height, t, top
        self.title, self.desc = title, desc
        self.layers: dict[str, list[str]] = {k: [] for k in
                                              ("head", "zones", "arrows", "labels", "nodes")}

    # -- text ------------------------------------------------------------------------------

    def text(self, x, y, s, *, size=12, fill=None, family=SANS, weight=400, anchor="start",
             spacing=None, italic=False, box=None, layer="nodes"):
        attrs = [f'x="{x}"', f'y="{y}"', f'fill="{fill or self.t["ink"]}"',
                 f'font-size="{size}"', f'font-family="{family}"']
        if weight != 400:
            attrs.append(f'font-weight="{weight}"')
        if anchor != "start":
            attrs.append(f'text-anchor="{anchor}"')
        if spacing:
            attrs.append(f'letter-spacing="{spacing}"')
        if italic:
            attrs.append('font-style="italic"')
        if box:
            attrs.append('data-box="{} {} {} {}"'.format(*box))
        self.layers[layer].append(f"<text {' '.join(attrs)}>{escape(s)}</text>")

    def header(self, kicker, title, sub):
        """A kicker in a pill, the title, and one line under it: what the picture is about."""
        t = self.t
        kw = width(kicker, 11, MONO) + 11 * 0.12 * len(kicker) + 24
        self.layers["head"].append(
            f'<rect x="40" y="28" width="{kw:.0f}" height="24" rx="12" fill="{t["coral"][0]}" '
            f'stroke="{t["coral"][1]}" stroke-width="1"/>')
        self.text(52, 44, kicker, size=11, weight=600, family=MONO, fill=t["coral"][2],
                  spacing="0.12em", layer="head", box=(40, 28, kw, 24))
        self.text(40, 90, title, size=28, weight=700, layer="head", box=(36, 60, 888, 40))
        self.text(40, 116, sub, size=14, fill=t["muted"], layer="head", box=(36, 96, 888, 30))

    def callout(self, x, y, s, *, size=17):
        self.text(x, y, s, size=size, fill=self.t["muted"], family=SERIF, italic=True,
                  layer="nodes", box=(x - 4, y - 20, W - 2 * (x - 4), 28))

    # -- shapes ----------------------------------------------------------------------------

    def card(self, x, y, w, h, hue=None, *, rx=12, dashed=False, tint=False, shadow=True,
             stroke_w=1.4):
        t = self.t
        stroke = t[hue][1] if hue else t["line"]
        dash = ' stroke-dasharray="5,4"' if dashed else ""
        flt = f' filter="url(#{self.slug}-shadow)"' if shadow else ""
        out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{t["card"]}"{flt}/>']
        if tint and hue:
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
                       f'fill="{t[hue][0]}"/>')
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="none" '
                   f'stroke="{stroke}" stroke-width="{stroke_w}"{dash}/>')
        self.layers["nodes"].append("".join(out))

    def zone(self, x, y, w, h, hue, label, note="", note_end=None):
        t = self.t
        fill, stroke, ink = t[hue]
        self.layers["zones"].append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{fill}" '
            f'fill-opacity="0.75" stroke="{stroke}" stroke-opacity="0.35" stroke-width="1"/>')
        lw = width(label, 10, MONO) + 10 * 0.14 * len(label) + 20
        self.layers["zones"].append(
            f'<rect x="{x + 16}" y="{y + 12}" width="{lw:.0f}" height="20" rx="10" '
            f'fill="{stroke}"/>')
        self.text(x + 26, y + 26, label, size=10, weight=600, family=MONO, fill=t["card"],
                  spacing="0.14em", layer="zones", box=(x + 16, y + 12, lw, 20))
        if note:
            self.text(note_end or x + w - 16, y + 26, note, size=12, fill=ink, anchor="end",
                      layer="zones", box=(x, y, w, 40))

    def pill(self, x, y, s, hue, *, size=11, solid=False, dashed=False, layer="nodes"):
        """A chip that sizes itself to its text; returns its width."""
        t = self.t
        fill, stroke, ink = t[hue]
        w = width(s, size, MONO) + 18
        h = size + 11
        dash = ' stroke-dasharray="3,2"' if dashed else ""
        self.layers[layer].append(
            f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" '
            f'fill="{stroke if solid else fill}" stroke="{stroke}" stroke-width="1"{dash}/>')
        self.text(x + 9, y + h / 2 + size * 0.36, s, size=size, weight=500, family=MONO,
                  fill=t["card"] if solid else ink, layer=layer, box=(x, y, w, h))
        return w

    def icon(self, name, x, y, size, color, stroke=1.7):
        s = size / 24
        self.layers["nodes"].append(
            f'<g transform="translate({x},{y}) scale({s:.3f})" fill="none" stroke="{color}" '
            f'stroke-width="{stroke / s:.2f}" stroke-linecap="round" stroke-linejoin="round">'
            f'{ICONS[name]}</g>')

    def icon_tile(self, name, x, y, hue, size=44):
        t = self.t
        self.layers["nodes"].append(
            f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="12" fill="{t[hue][0]}" '
            f'stroke="{t[hue][1]}" stroke-opacity="0.5" stroke-width="1"/>')
        self.icon(name, x + (size - 26) / 2, y + (size - 26) / 2, 26, t[hue][1])

    def badge(self, cx, cy, n, hue, r=13):
        t = self.t
        self.layers["nodes"].append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{t[hue][1]}"/>')
        self.text(cx, cy + 5, str(n), size=14, weight=700, anchor="middle", fill=t["card"])

    def diamond(self, cx, cy, kind, hue=None, r=10):
        t = self.t
        fill, stroke = {"gate": (t["card"], t["ink"]), "control": (t["ink"], t["ink"]),
                        "focal": (t["coral"][1], t["coral"][1])}[kind]
        pts = f"{cx},{cy - r} {cx + r},{cy} {cx},{cy + r} {cx - r},{cy}"
        self.layers["nodes"].append(
            f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="1.6" '
            f'stroke-linejoin="round"/>')

    def dot(self, cx, cy, fill, r=5):
        self.layers["nodes"].append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{self.t["card"]}" '
            f'stroke-width="2.5"/>')

    # -- connectors ------------------------------------------------------------------------

    def wire(self, points, *, color=None, dashed=False, head=True, w=1.8, marker="line"):
        t = self.t
        c = color or t["line"]
        dash = ' stroke-dasharray="6,5"' if dashed else ""
        mk = f' marker-end="url(#{self.slug}-{marker})"' if head else ""
        self.layers["arrows"].append(
            f'<path d="{rounded(points)}" fill="none" stroke="{c}" stroke-width="{w}" '
            f'stroke-linecap="round"{dash}{mk}/>')

    def label(self, x, y, s, *, color=None, anchor="middle", size=10):
        """A connector's label in a small pill; `y` is the baseline, the pill ends at y+4."""
        t = self.t
        w = width(s, size, MONO) + size * 0.08 * len(s) + 14
        x0 = {"middle": x - w / 2, "start": x - 7, "end": x - w + 7}[anchor]
        self.layers["labels"].append(
            f'<rect x="{x0:.1f}" y="{y - size - 2}" width="{w:.1f}" height="{size + 6}" '
            f'rx="{(size + 6) / 2}" fill="{t["card"]}" stroke="{t["line"]}" stroke-opacity="0.6" '
            f'stroke-width="1"/>')
        self.text(x, y, s, size=size, weight=600, family=MONO, fill=color or t["muted"],
                  anchor=anchor, spacing="0.08em", layer="labels",
                  box=(x0, y - 40, w, 80))

    def legend(self, y, items):
        """A row of small samples, each with its words, starting at x=40."""
        t, x = self.t, 40
        for kind, hue, words in items:
            if kind == "card":
                self.layers["nodes"].append(
                    f'<rect x="{x}" y="{y - 11}" width="22" height="14" rx="4" fill="{t["card"]}" '
                    f'stroke="{t[hue][1] if hue else t["line"]}" stroke-width="1.4"/>')
                x += 30
            elif kind == "tint":
                self.layers["nodes"].append(
                    f'<rect x="{x}" y="{y - 11}" width="22" height="14" rx="4" fill="{t[hue][0]}" '
                    f'stroke="{t[hue][1]}" stroke-width="1.4"/>')
                x += 30
            elif kind == "dashed":
                self.layers["nodes"].append(
                    f'<rect x="{x}" y="{y - 11}" width="22" height="14" rx="4" fill="{t[hue][0]}" '
                    f'stroke="{t[hue][1]}" stroke-width="1.4" stroke-dasharray="3,2"/>')
                x += 30
            else:
                self.diamond(x + 9, y - 4, kind, r=8)
                x += 26
            self.text(x, y, words, size=12, fill=t["muted"], box=(40, y - 16, W - 80, 24))
            x += width(words, 12) + 28

    # -- output ----------------------------------------------------------------------------

    def render(self) -> str:
        t = self.t
        markers = "".join(
            f'<marker id="{self.slug}-{k}" markerWidth="10" markerHeight="10" refX="8" refY="5" '
            f'orient="auto" markerUnits="userSpaceOnUse"><path d="M1,1 L9,5 L1,9 Z" '
            f'fill="{c}"/></marker>'
            for k, c in (("line", t["line"]), ("ink", t["ink"]), ("coral", t["coral"][1]),
                         ("blue", t["blue"][1]), ("violet", t["violet"][1]),
                         ("green", t["green"][1]), ("amber", t["amber"][1]),
                         ("slate", t["slate"][1])))
        defs = (f'<pattern id="{self.slug}-dots" width="20" height="20" '
                f'patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1.1" '
                f'fill="{t["dot"]}"/></pattern>'
                f'<filter id="{self.slug}-shadow" x="-10%" y="-10%" width="120%" height="140%">'
                f'<feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="{t["shadow"]}"/>'
                f'</filter>{markers}')
        body = "".join("".join(self.layers[k]) for k in ("zones", "arrows", "labels", "nodes"))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {self.h}" '
                f'role="img" aria-labelledby="{self.slug}-title {self.slug}-desc">'
                f'<title id="{self.slug}-title">{escape(self.title)}</title>'
                f'<desc id="{self.slug}-desc">{escape(self.desc)}</desc>'
                f'<defs>{defs}</defs>'
                f'<rect width="{W}" height="{self.h}" rx="18" fill="{t["bg"]}"/>'
                f'<rect width="{W}" height="{self.h}" rx="18" fill="url(#{self.slug}-dots)"/>'
                f'{"".join(self.layers["head"])}'
                f'<g transform="translate(0,{self.top})">{body}</g></svg>')


# ── 1 · how it works: four steps on one repository ───────────────────────────────────────

STEPS = (
    ("blue", "file", "Bring it in", "Decks, PDFs, meetings: each fact goes to its one place.",
     "we decided on Airflow", ("start", "requirement"), "WRITES"),
    ("violet", "branch", "Decide", "Open choices settled; a request becomes a mandate.",
     "what do we build next?", ("resolve", "cycle"), "WRITES"),
    ("green", "robot", "Build and ship", "Built from a brief, shipped through a gate.",
     "can we ship 1.7?", ("release",), "WRITES"),
    ("amber", "users", "Tell", "SAL and slides kept in _meta/, a daily workbook.",
     "let’s do the weekly SAL", ("business", "presentation", "digest"), "READS ARTIFACTS"),
)


def skills(t: dict) -> Svg:
    s = Svg("skills", 628, t, "How the framework works",
            "Four steps, each carried by its skills, on one documentation repository: bring "
            "facts in, decide, build and ship, and tell the people outside; audit and the "
            "validator in CI check the repository, and in the additive mode contribute lets "
            "many people write it on threads.")
    s.header("HOW IT WORKS", "One repository, and the skills that keep it true",
             "You say what happened. A skill puts each fact in its one place, and people and "
             "agents work from there.")

    cw, ch, gap, y = 196, 248, 32, 144
    xs = [40 + i * (cw + gap) for i in range(4)]
    # Flow between the steps, then each step down to the repository or up from it.
    for x in xs[:-1]:
        s.wire([(x + cw + 4, y + 36), (x + cw + gap - 4, y + 36)], w=2)
    py = y + ch + 56
    for (hue, *_, verb), x in zip(STEPS, xs):
        cx = x + cw // 2
        if verb.startswith("WRITES"):
            s.wire([(cx, y + ch + 4), (cx, py - 4)], color=t[hue][1], marker=hue, w=2)
            s.label(cx + 14, y + ch + 32, verb, color=t[hue][2], anchor="start")
        else:
            # The last step is the rightmost: its label goes on the inner side of its arrow.
            s.wire([(cx, py + 4), (cx, y + ch - 4 + 8)], color=t[hue][1], marker=hue, w=2)
            s.label(cx - 14, y + ch + 32, verb, color=t[hue][2], anchor="end")

    for n, ((hue, icon, title, body, quote, chips, _), x) in enumerate(zip(STEPS, xs), 1):
        b = (x, y, cw, ch)
        s.card(x, y, cw, ch, hue)
        s.icon_tile(icon, x + 16, y + 16, hue)
        s.badge(x + cw - 28, y + 30, n, hue)
        s.text(x + 16, y + 88, title, size=18, weight=700, box=b)
        lines = textwrap.wrap(body, 27)
        if len(lines) > 2:
            sys.exit(f"{title}: {body!r} needs {len(lines)} lines in a card that has two")
        for i, line in enumerate(lines):
            s.text(x + 16, y + 110 + 17 * i, line, size=12.5, fill=t["muted"], box=b)
        # The sentence somebody says, in a bubble with a tail.
        by = y + 146
        s.layers["nodes"].append(
            f'<path d="M {x + 16},{by + 6} a 6,6 0 0 1 6,-6 h {cw - 44} a 6,6 0 0 1 6,6 v 16 '
            f'a 6,6 0 0 1 -6,6 h -{cw - 64} l -8,7 l 0,-7 h -12 a 6,6 0 0 1 -6,-6 Z" '
            f'fill="{t[hue][0]}" stroke="{t[hue][1]}" stroke-opacity="0.45" stroke-width="1"/>')
        s.text(x + 26, by + 18, f"“{quote}”", size=12, fill=t[hue][2], italic=True,
               box=(x + 16, by, cw - 32, 28))
        cx, cy = x + 16, y + 192
        for c in chips:
            w = width(c, 11, MONO) + 18
            if cx + w > x + cw - 16:
                cx, cy = x + 16, cy + 28
            cx += s.pill(cx, cy, c, hue) + 6

    # The repository the four stand on.
    px, pw, ph = 40, 880, 112
    s.card(px, py, pw, ph, "coral", tint=True, rx=16, stroke_w=1.6)
    s.icon_tile("log", px + 20, py + 18, "coral", size=48)
    s.text(px + 84, py + 38, "Your documentation repository", size=18, weight=700,
           box=(px, py, pw, ph))
    s.text(px + 84, py + 58, "one authoritative source for every fact, beside your code",
           size=12.5, fill=t["muted"], box=(px, py, 520, ph))
    cx = px + 84
    for c in ("AGENTS.md", "OPEN.md", "GLOSSARY.md", "decisions/", "products/<p>/"):
        cx += s.pill(cx, py + 72, c, "slate") + 6
    s.layers["nodes"].append(
        f'<line x1="{px + 568}" y1="{py + 20}" x2="{px + 568}" y2="{py + ph - 20}" '
        f'stroke="{t["coral"][1]}" stroke-opacity="0.35" stroke-width="1"/>')
    for i, (icon, chip, words) in enumerate((("test", "audit", "checks it; validate.py in CI"),
                                              ("pipeline", "contribute",
                                               "threads, in additive mode"))):
        gy = py + 26 + 36 * i
        s.icon(icon, px + 588, gy, 20, t["coral"][1])
        w = s.pill(px + 616, gy - 1, chip, "coral")
        s.text(px + 624 + w, gy + 15, words, size=12.5, fill=t["muted"],
               box=(px + 600, py, pw - 600, ph))

    s.callout(40, py + ph + 40, "A request is not a mandate: only an approved change goes out "
                                "to be built.")
    return s


# ── 2 · the lifecycle and its gates ──────────────────────────────────────────────────────

def lifecycle(t: dict) -> Svg:
    top = 140
    s = Svg("lifecycle", 608 + top, t, "The lifecycle and its gates",
            "Discovery per initiative from F1 to F3, construction per product from F4 to F6, "
            "and the loop of operation and evolution that returns to the build, with the "
            "gates crossed once and the controls repeated on every lap.", top=top)
    s.header("THE LIFECYCLE", "From a signal to a product that keeps changing",
             "Discovery once per initiative, construction per product, then a loop that never "
             "ends. Every gate leaves something written.")
    c = (40, 276, 512, 748)
    nw, nh = 172, 76
    A, B, C = 40, 200, 352
    cyA, cyB, cyC = A + 38, B + 38, C + 38

    s.zone(24, 0, 912, 136, "blue", "A · DISCOVERY", "per initiative, elastic", 920)
    s.zone(24, 160, 676, 136, "violet", "B · CONSTRUCTION", "per product · F5 and F6 every lap",
           684)
    s.zone(24, 312, 912, 176, "green", "C · THE LOOP", "operation and evolution, per product",
           780)

    s.wire([(c[0] + nw, cyA), (c[1] - 2, cyA)])
    s.wire([(c[1] + nw, cyA), (c[2] - 2, cyA)])
    s.wire([(c[2] + 86, A + nh), (c[2] + 86, 148), (196, 148), (196, B - 2)])
    s.wire([(c[0] + nw, cyB), (c[1] - 2, cyB)], color=t["coral"][1], marker="coral", w=2.2)
    s.wire([(c[1] + nw, cyB), (c[2] - 2, cyB)])
    s.wire([(480, cyB - 10), (480, 182), (412, 182), (412, B - 2)], dashed=True)
    s.label(446, 172, "REWORK")
    s.wire([(c[2] + nw, cyB), (794, cyB), (794, C - 2)])
    s.wire([(874, C), (874, A + nh + 2)], color=t["blue"][1], marker="blue", dashed=True)
    s.label(860, 156, "RE-ENTRY", color=t["blue"][2], anchor="end")
    s.wire([(c[3], cyC), (c[2] + nw + 2, cyC)])
    s.wire([(c[2], cyC), (c[1] + nw + 2, cyC)])
    s.wire([(480, cyC + 10), (480, 472), (88, 472), (88, C + nh + 2)])
    s.label(300, 462, "NOT STRUCTURAL")
    s.wire([(800, C + nh), (800, 456), (640, 456), (640, C + nh + 2)], dashed=True)
    s.wire([(c[1], cyC), (c[0] + nw + 2, cyC)])
    s.wire([(196, C), (196, 304), (318, 304), (318, B + nh + 2)])
    s.label(244, 294, "NEXT LAP")

    for x, y, kind, name, where in ((244, cyA, "gate", "G1", "above"),
                                    (480, cyA, "gate", "G2", "above"),
                                    (520, 148, "gate", "G3", "above"),
                                    (244, cyB, "focal", "G4", "above"),
                                    (480, cyB, "control", "RG", "below"),
                                    (720, 456, "gate", "MOR · ONCE", "below"),
                                    (480, cyC, "control", "ICG", "above")):
        s.diamond(x, y, kind)
        col = t["coral"][2] if kind == "focal" else t["ink"]
        if where == "above":
            s.label(x, y - 16, name, color=col)
        else:
            s.label(x, y + 26, name, color=col)

    def node(x, y, title, subs, hue, tag=None, kind=None, sub_size=10.5):
        """A phase or a step: its name, the phase number in its colour before it, the
        artifacts under it. The names are the ones FRAMEWORK.md §5 gives the phases."""
        focal, dashed = kind == "focal", kind == "reentry"
        s.card(x, y, nw, nh, "coral" if focal else hue, tint=focal or dashed, dashed=dashed,
               shadow=not dashed)
        b = (x, y, nw, nh)
        ty = y + (nh - 16 - 15 * len(subs)) / 2 + 12
        lead = (f'<tspan font-family="{MONO}" fill="{t[hue][1]}">{tag}</tspan> '
                if tag else "")
        s.layers["nodes"].append(
            f'<text x="{x + nw // 2}" y="{ty}" fill="{t["ink"]}" font-size="13" '
            f'font-family="{SANS}" font-weight="700" text-anchor="middle" '
            f'data-box="{x} {y} {nw} {nh}">{lead}{escape(title)}</text>')
        for i, sub in enumerate(subs):
            s.text(x + nw // 2, ty + 17 + 15 * i, sub, size=sub_size, fill=t["muted"],
                   family=MONO, anchor="middle", box=b)

    node(c[0], A, "Signal and framing", ["PRB · HYP"], "blue", "F1")
    node(c[1], A, "Problem discovery", ["WF §current · EVD"], "blue", "F2")
    node(c[2], A, "Solution discovery", ["WF §target · CMP", "DFB · RSK"], "blue", "F3")
    node(c[3], A, "Back into discovery", ["invalidated at MOR or ICG →",
                                          "F2 problem, F3 solution;",
                                          "a new initiative → F1"],
         "blue", kind="reentry", sub_size=10)
    node(c[0], B, "Shaping MVP and MVA", ["PBR · SD · EVP · DC", "RMP · DEC"], "violet", "F4")
    node(c[1], B, "Build", ["release candidate", "ARC from here · LOG · code"], "violet", "F5")
    node(c[2], B, "Controlled go-live", ["EVR · REL · RLM", "RB, the first time"], "violet",
         "F6")
    node(c[3], C, "Run and observe", ["LOG: incident, drift,", "feedback"], "green")
    node(c[2], C, "Intake and triage", ["signals from LOG", "increments from RMP"], "green")
    node(c[1], C, "Reshaping", ["PBR · WF · ARC · EVP", "DC · RSK · RMP · DEC"], "green")
    node(c[0], C, "Change contract", ["CHG: what is authorized", "then IMP: this cycle"],
         "green", kind="focal")

    s.callout(40, 532, "Elastic before G4, strict after it: an evaluation plan written after "
                       "the results is not one.")
    s.legend(572, [("gate", None, "gate, crossed once"), ("control", None, "control, every lap"),
                   ("focal", None, "where it tightens"),
                   ("tint", "coral", "what an agent builds"),
                   ("dashed", "blue", "out of the loop")])
    return s


# ── 3 · the additive mode: threads and a join ────────────────────────────────────────────

def threads(t: dict) -> Svg:
    top = 140
    s = Svg("threads", 476 + top, t, "Threads and a join in the additive mode",
            "The main line moves only at a join: threads computed by the to-do and a parking "
            "branch write new files directly and everything a living document should say as "
            "a pending effect, and an admin's join applies the effects and lands it all.",
            top=top)
    s.header("THE ADDITIVE MODE", "Many people, one documentation",
             "On a thread nothing rewrites a living document: what it should say waits, as an "
             "effect, for the join.")
    MAIN, JOIN, TA, TB, PK = 36, 116, 196, 276, 356
    lanes = ((MAIN, "slate", "MAIN LINE", "main", "moves only at a join"),
             (JOIN, "coral", "JOIN", "work.py join", "admin, deputy or delegate"),
             (TA, "blue", "THREAD", "open --thread <t>", "computed by the to-do"),
             (TB, "violet", "THREAD", "open --thread <t>", "taken whole, by one person"),
             (PK, "slate", "PARKING", "open --branch <slug>", "what belongs to no thread"))
    for y, hue, name, cmd, note in lanes:
        fill, stroke, ink = t[hue]
        s.layers["zones"].append(
            f'<rect x="24" y="{y - 36}" width="912" height="72" rx="14" fill="{fill}" '
            f'fill-opacity="0.7" stroke="{stroke}" stroke-opacity="0.25" stroke-width="1"/>')
        b = (36, y - 36, 168, 72)
        s.pill(40, y - 27, name, hue, size=10, solid=True, layer="zones")
        s.text(40, y + 9, cmd, size=10.5, fill=ink, family=MONO, layer="zones", box=b)
        s.text(40, y + 25, note, size=11.5, fill=t["muted"], layer="zones", box=b)

    s.wire([(212, MAIN), (W - 40, MAIN)], color=t["ink"], head=False, w=3)
    for x, lane, end, hue in ((248, PK, 728, "slate"), (272, TB, 704, "violet"),
                              (296, TA, 680, "blue")):
        s.wire([(x, MAIN + 15), (x, lane), (end, lane), (end, JOIN + 6)], color=t[hue][1],
               marker=hue, w=2.4)
    s.wire([(632, MAIN), (632, JOIN), (914, JOIN), (914, MAIN + 7)], color=t["coral"][1],
           marker="coral", w=3)
    s.label(900, 80, "JOIN --MERGE", color=t["coral"][2], anchor="end")
    s.label(618, 80, "WORK.PY JOIN", color=t["coral"][2], anchor="end")

    w = width("todo.py · the threads", 11, MONO) + 18
    s.card(216, MAIN - 15, w + 8, 30, None, rx=15)
    s.text(228, MAIN + 4, "todo.py · the threads", size=11, weight=600, family=MONO,
           box=(216, MAIN - 15, w + 8, 30))
    s.text(W - 40, MAIN - 14, "living documents current again", size=12, fill=t["muted"],
           anchor="end", box=(600, MAIN - 34, 320, 28))
    for x in (680, 704, 728):
        s.dot(x, JOIN, t["coral"][1], r=4)
    s.dot(914, MAIN, t["ink"], r=6)

    def commit(x, lane, hue, ident, note, effect=False, w=136):
        s.card(x, lane - 21, w, 42, hue, rx=10, tint=effect, dashed=effect, shadow=not effect)
        b = (x, lane - 21, w, 42)
        s.text(x + w // 2, lane - 3, ident, size=11, weight=600, family=MONO, anchor="middle",
               box=b, fill=t[hue][2] if effect else t["ink"])
        s.text(x + w // 2, lane + 13, note, size=11, fill=t["muted"], anchor="middle", box=b)

    commit(320, TA, "blue", "DEC-110", "a new decision")
    commit(472, TA, "blue", "ARC.md#current", "a pending effect", effect=True, w=160)
    commit(320, TB, "violet", "CHG-031", "a new change, draft")
    commit(472, TB, "violet", "WF.md#target", "a pending effect", effect=True, w=160)
    commit(320, PK, "slate", "SIG-014 · OD-051", "a LOG line, an OPEN entry", w=176)
    s.card(740, JOIN - 22, 160, 44, "coral", rx=10, tint=True, stroke_w=1.6)
    b = (740, JOIN - 22, 160, 44)
    s.text(820, JOIN - 4, "effects → living docs", size=11, weight=600, family=MONO,
           anchor="middle", fill=t["coral"][2], box=b)
    s.text(820, JOIN + 13, "changes approved, checked", size=11, fill=t["muted"],
           anchor="middle", box=b)

    s.legend(436, [("card", "blue", "written directly on the branch"),
                   ("dashed", "blue", "a pending effect, in _filoni/<slug>/effetti.md"),
                   ("tint", "coral", "the join rewrites the living documents")])
    return s


DIAGRAMS = {"skills": skills, "lifecycle": lifecycle, "threads": threads}

PRELOAD = ('<div aria-hidden="true" style="position:absolute;opacity:0">'
           f'<span style="font:700 12px {SANS}">a</span><span style="font:600 12px {SANS}">a</span>'
           f'<span style="font:12px {SANS}">a</span><span style="font:italic 12px {SANS}">a</span>'
           f'<span style="font:500 9px {MONO}">a</span><span style="font:600 9px {MONO}">a</span>'
           f'<span style="font:9px {MONO}">a</span>'
           f'<span style="font:italic 14px {SERIF}">a</span></div>')

CHECK = """() => {
  const bad = [];
  for (const el of document.querySelectorAll('text[data-box]')) {
    const [x, y, w, h] = el.dataset.box.split(' ').map(Number);
    const b = el.getBBox();
    if (b.x < x - 0.5 || b.y < y - 0.5 || b.x + b.width > x + w + 0.5 || b.y + b.height > y + h + 0.5)
      bad.push(`${el.textContent} overflows its box by ` +
               Math.max(x - b.x, y - b.y, b.x + b.width - x - w, b.y + b.height - y - h).toFixed(1));
  }
  return bad;
}"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--keep-html", type=pathlib.Path, help="keep the pages the PNGs come from")
    ap.add_argument("--only", choices=sorted(DIAGRAMS), action="append")
    args = ap.parse_args()
    from playwright.sync_api import sync_playwright

    work = args.keep_html or pathlib.Path(tempfile.mkdtemp())
    work.mkdir(parents=True, exist_ok=True)
    failures = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=2, viewport={"width": W, "height": 900})
        for name in args.only or DIAGRAMS:
            for theme in (LIGHT, DARK):
                svg = DIAGRAMS[name](theme).render()
                html = work / f"{name}-{theme['name']}.html"
                html.write_text(
                    f'<!DOCTYPE html><html><head><meta charset="utf-8">'
                    f'<link href="{escape(FONTS)}" rel="stylesheet"><style>html,body{{margin:0;'
                    f'background:transparent}}svg{{display:block;width:{W}px;height:auto}}'
                    f'</style></head><body>{PRELOAD}{svg}</body></html>', encoding="utf-8")
                page.goto(html.as_uri())
                page.wait_for_load_state("networkidle")
                fonts = page.evaluate(
                    "document.fonts.ready.then(() => ['700 12px Geist', '9px \"Geist Mono\"', "
                    "'italic 14px \"Instrument Serif\"'].filter(f => !document.fonts.check(f)))")
                if fonts:
                    failures.append(f"{name} ({theme['name']}): fonts did not load: {fonts}. "
                                    "The network is needed for them.")
                    continue
                bad = page.evaluate(CHECK)
                if bad:
                    failures += [f"{name} ({theme['name']}): {b}" for b in bad]
                    continue
                suffix = "" if theme is LIGHT else "-dark"
                out = HERE / f"{name}{suffix}.png"
                page.locator("svg").first.screenshot(path=str(out), omit_background=True)
                print(f"wrote {out.relative_to(ROOT)}")
        browser.close()
    for f in failures:
        print(f"x {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
