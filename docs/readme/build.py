#!/usr/bin/env python3
"""The pictures in the README, drawn by code so that they can be drawn again.

    python3 docs/readme/build.py                  write the PNGs beside this file
    python3 docs/readme/build.py --keep-html DIR  also keep the page each PNG is taken from

WHY A SCRIPT AND NOT A DRAWING. `Framework.drawio` was the drawing, and it has not been
redrawn since 2026-08-06: a picture nobody can regenerate is a copy of the truth with a date
on it. These are four SVGs written by the functions below, each in a light and a dark variant
from the same coordinates, so the two cannot disagree, and a change is an edit here and one
command.

WHY THE CHIPS OF THE MAP ARE READ FROM THE REGISTRY. The map places every artifact type by its
`axis` and its `lifecycle` as `schemas/artifact-types.yaml` declares them, so a type added
there is a chip here at the next run, and a type whose class changes moves column. Its column
and band headers, the text of an empty cell and its callout are written here by hand, from
`FRAMEWORK.md` §3-4, and so are the other three pictures, from what `FRAMEWORK.md` §5-6 and
`framework-flow.mermaid.md`, `SKILLS.md` and the skills, `references/additive.md` and
`work.py` say. None carries a count: a number in a picture goes stale the way a number in
prose does.

WHAT IT NEEDS, AND WHAT IT DOES NOT CHECK. `pip install playwright` and `playwright install
chromium`, which the framework itself does not need and `requirements.txt` does not carry, and
the network for the fonts (Geist, Geist Mono, Instrument Serif). The script refuses to write a
picture in which a text overflows the box or the label mask it was placed in, the defect a
person reviewing a PNG misses; it does not see two elements that overlap, and nothing in CI
renders the pictures, because a PNG is not byte-stable across browser versions.

NOTHING CHECKS THAT THE PICTURES ARE CURRENT, AND THAT IS A CHOICE. A check that needs no
render was possible -- a stamp of what was drawn, recomputed by the self check from the
registry and `skills/` -- and the owner chose to declare the gap instead. So any of these
leaves a picture wrong with every check green, until whoever made the change runs this script
in the same commit:

- the registry: a type added, removed or renamed, its `axis`, `lifecycle`, `class_note` or
  `born_in`;
- `FRAMEWORK.md` §3-4: what a class or an axis is said to be, and the folder tree, whose root
  files and folders the skills picture lists inside the repository;
- `FRAMEWORK.md` §5-6 and `framework-flow.mermaid.md`: a phase, a gate or an exit that moves;
- the skills, `SKILLS.md` and each `SKILL.md`: one added or renamed, or what one does, what it
  produces and the sentence it answers to;
- `references/additive.md`, `work.py` and `todo.py`: where a thread, a parking branch or the
  effects are written, the commands that open them, how the threads are computed, who runs
  the join and what it does.

This list is the one place the rule is written; the README points here.

The visual grammar is that of the diagram-design skill: a 4px grid, orthogonal connectors
with rounded corners, labels on a mask with a gap above their line, one or two accents.
"""
from __future__ import annotations

import argparse
import math
import pathlib
import sys
import tempfile
import textwrap
from xml.sax.saxutils import escape

import yaml

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
REGISTRY = ROOT / "schemas" / "artifact-types.yaml"

FONTS = ("https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1"
         "&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap")
SANS, MONO, SERIF = "'Geist', sans-serif", "'Geist Mono', monospace", "'Instrument Serif', serif"
W = 960

LIGHT = dict(name="light", paper="#f5f5f5", node="#ffffff", ink="#2d3142", muted="#4f5d75",
             soft="#7a8399", accent="#eb6c36", link="#2e5aa8",
             ink_rgb="45,49,66", accent_rgb="235,108,54", muted_rgb="79,93,117")
DARK = dict(name="dark", paper="#2d3142", node="#393e53", ink="#f5f5f5", muted="#bfc0c0",
            soft="#8e98ac", accent="#f08a59", link="#6a95d8",
            ink_rgb="245,245,245", accent_rgb="240,138,89", muted_rgb="191,192,192")


def rgba(rgb: str, a: float) -> str:
    return f"rgba({rgb},{a})"


def rounded(points: list[tuple[int, int]], r: int = 8) -> str:
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


class Svg:
    """One diagram in one theme: primitives that know the tokens, in paint order."""

    def __init__(self, slug: str, height: int, t: dict, title: str, desc: str):
        self.slug, self.h, self.t = f"{slug}-{t['name']}", height, t
        self.title, self.desc = title, desc
        self.layers: dict[str, list[str]] = {k: [] for k in
                                              ("zones", "arrows", "labels", "nodes", "top")}

    # -- text ------------------------------------------------------------------------------

    def text(self, x, y, s, *, size=9, fill=None, family=SANS, weight=400, anchor="start",
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

    def eyebrow(self, x, y, s, *, fill=None, anchor="start", box=None, layer="nodes"):
        self.text(x, y, s, size=8, fill=fill or self.t["muted"], family=MONO, weight=500,
                  anchor=anchor, spacing="0.16em", box=box, layer=layer)

    def callout(self, x, y, s, *, anchor="start", box=None):
        # An italic capital leans past its origin by a pixel or so: the box allows for it.
        if box:
            box = (box[0] - 4, box[1], box[2] + 8, box[3])
        self.text(x, y, s, size=14, fill=self.t["muted"], family=SERIF, italic=True,
                  anchor=anchor, box=box, layer="top")

    # -- shapes ----------------------------------------------------------------------------

    def zone(self, x, y, w, h, label, note="", note_end=None):
        """A region with its name at the top left; the note follows it, or ends at `note_end`
        when a connector has to come down through the space after the name."""
        t = self.t
        self.layers["zones"].append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" '
            f'fill="{rgba(t["ink_rgb"], 0.025)}" stroke="{rgba(t["ink_rgb"], 0.12)}" '
            f'stroke-width="0.8"/>')
        self.eyebrow(x + 16, y + 18, label, fill=rgba(t["ink_rgb"], 0.55), layer="zones",
                     box=(x, y, w, 28))
        if note and note_end:
            self.text(note_end, y + 18, note, fill=t["soft"], anchor="end", layer="zones",
                      box=(x, y, w, 28))
        elif note:
            self.text(x + 16 + 7 * len(label) + 12, y + 18, note, fill=t["soft"],
                      layer="zones", box=(x, y, w, 28))

    def box(self, x, y, w, h, kind="step", dashed=False):
        t = self.t
        fill, stroke = {
            "step": (t["node"], t["ink"]),
            "focal": (rgba(t["accent_rgb"], 0.10), t["accent"]),
            "input": (rgba(t["muted_rgb"], 0.10), t["soft"]),
            "external": (rgba(t["ink_rgb"], 0.04), rgba(t["ink_rgb"], 0.35)),
            "chip": (t["node"], rgba(t["ink_rgb"], 0.30)),
            "reentry": (rgba(t["ink_rgb"], 0.02), t["link"]),
        }[kind]
        dash = ' stroke-dasharray="4,3"' if dashed else ""
        self.layers["nodes"].append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{t["paper"]}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="1"{dash}/>')

    def node(self, x, y, w, h, name, subs=(), *, kind="step", dashed=False, tag=None,
             sub_family=MONO, name_y=None, quote=None):
        """A box, its name, up to three lines under it and an optional quoted sentence."""
        t = self.t
        self.box(x, y, w, h, kind, dashed)
        b = (x, y, w, h)
        cx = x + w // 2
        if tag:
            tw = 8 + 6 * len(tag)
            tc = t["accent"] if kind == "focal" else t["muted"]
            self.layers["nodes"].append(
                f'<rect x="{x + 8}" y="{y + 8}" width="{tw}" height="12" rx="2" fill="none" '
                f'stroke="{tc}" stroke-opacity="0.5" stroke-width="0.8"/>')
            self.text(x + 8 + tw / 2, y + 17, tag, size=7, fill=tc, family=MONO,
                      anchor="middle", spacing="0.08em", box=b)
        lines = 1 + len(subs) + (1 if quote else 0)
        ny = name_y if name_y is not None else y + h // 2 - (lines - 1) * 7 + 4
        if tag and name_y is None:
            ny += 6          # below the tag, which a long name would otherwise touch
        names = name if isinstance(name, (list, tuple)) else [name]
        for i, n in enumerate(names):
            self.text(cx, ny + 16 * i, n, size=12, weight=600, anchor="middle", box=b)
        sy = ny + 16 * (len(names) - 1) + 17
        for s in subs:
            self.text(cx, sy, s, size=9, fill=t["muted"], family=sub_family, anchor="middle",
                      box=b)
            sy += 13
        if quote:
            self.text(cx, sy + 1, f"“{quote}”", size=9, fill=t["soft"],
                      anchor="middle", box=b)

    def chip(self, x, y, w, h, s, *, kind="chip", dashed=False, size=9):
        self.box(x, y, w, h, kind, dashed)
        self.text(x + w // 2, y + h // 2 + 3, s, size=size, family=MONO, anchor="middle",
                  box=(x, y, w, h))

    def diamond(self, cx, cy, kind="gate"):
        t = self.t
        fill, stroke = {"gate": (t["paper"], t["ink"]),
                        "control": (t["muted"], t["muted"]),
                        "focal": (t["paper"], t["accent"])}[kind]
        pts = f"{cx},{cy - 8} {cx + 8},{cy} {cx},{cy + 8} {cx - 8},{cy}"
        self.layers["nodes"].append(
            f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>')
        if kind == "focal":
            self.layers["nodes"].append(
                f'<polygon points="{cx},{cy - 4} {cx + 4},{cy} {cx},{cy + 4} {cx - 4},{cy}" '
                f'fill="{t["accent"]}"/>')

    def dot(self, cx, cy, fill=None, r=4):
        self.layers["nodes"].append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill or self.t["ink"]}" '
            f'stroke="{self.t["paper"]}" stroke-width="2"/>')

    # -- connectors ------------------------------------------------------------------------

    def wire(self, points, *, kind="default", dashed=False, head=True, width=1.2):
        t = self.t
        color = {"default": t["muted"], "accent": t["accent"], "link": t["link"],
                 "ink": t["ink"], "soft": t["soft"]}[kind]
        dash = ' stroke-dasharray="4,3"' if dashed else ""
        marker = f' marker-end="url(#{self.slug}-{kind})"' if head else ""
        self.layers["arrows"].append(
            f'<path d="{rounded(points)}" fill="none" stroke="{color}" '
            f'stroke-width="{width}"{dash}{marker}/>')

    def label(self, x, y, s, *, kind="default", anchor="middle"):
        """An arrow label whose baseline is `y`: the mask spans y-9 to y+3."""
        t = self.t
        color = {"default": t["muted"], "accent": t["accent"], "ink": t["ink"],
                 "link": t["link"]}[kind]
        w = math.ceil(len(s) * 5.4) + 8
        x0 = {"middle": x - w / 2, "start": x - 4, "end": x - w + 4}[anchor]
        self.layers["labels"].append(
            f'<rect x="{x0}" y="{y - 9}" width="{w}" height="12" rx="2" fill="{t["paper"]}"/>')
        # Measured against its mask only horizontally: a glyph box is taller than the 12px
        # the mask covers, and the letters themselves are not.
        self.text(x, y, s, size=8, fill=color, family=MONO, anchor=anchor, spacing="0.06em",
                  layer="labels", box=(x0, y - 40, w, 80))

    # -- legend ----------------------------------------------------------------------------

    def legend(self, items):
        t, y = self.t, self.h - 52
        self.layers["top"].append(
            f'<line x1="40" y1="{y}" x2="{W - 40}" y2="{y}" '
            f'stroke="{rgba(t["ink_rgb"], 0.12)}" stroke-width="0.8"/>')
        self.eyebrow(40, y + 18, "LEGEND", layer="top")
        x, iy = 40, y + 36
        for kind, text in items:
            if kind in ("line", "accent-line", "dashed-line"):
                c = t["accent"] if kind == "accent-line" else t["muted"]
                dash = ' stroke-dasharray="4,3"' if kind == "dashed-line" else ""
                head = "accent" if kind == "accent-line" else "default"
                self.layers["top"].append(
                    f'<line x1="{x}" y1="{iy - 3}" x2="{x + 24}" y2="{iy - 3}" stroke="{c}" '
                    f'stroke-width="1.2"{dash} marker-end="url(#{self.slug}-{head})"/>')
                x += 32
            elif kind in ("gate", "control", "focal-gate"):
                save = self.layers["nodes"]
                self.layers["nodes"] = self.layers["top"]
                self.diamond(x + 8, iy - 3, {"gate": "gate", "control": "control",
                                             "focal-gate": "focal"}[kind])
                self.layers["nodes"] = save
                x += 24
            else:
                fill, stroke, dash = {
                    "step": (t["node"], t["ink"], False),
                    "focal": (rgba(t["accent_rgb"], 0.10), t["accent"], False),
                    "input": (rgba(t["muted_rgb"], 0.10), t["soft"], False),
                    "external": (rgba(t["ink_rgb"], 0.04), rgba(t["ink_rgb"], 0.35), False),
                    "chip": (t["node"], rgba(t["ink_rgb"], 0.30), False),
                    "dashed": (t["node"], rgba(t["ink_rgb"], 0.45), True),
                    "reentry": (rgba(t["ink_rgb"], 0.02), t["link"], True),
                }[kind]
                d = ' stroke-dasharray="3,2"' if dash else ""
                self.layers["top"].append(
                    f'<rect x="{x}" y="{iy - 9}" width="16" height="12" rx="2" fill="{fill}" '
                    f'stroke="{stroke}" stroke-width="1"{d}/>')
                x += 24
            self.text(x, iy, text, size=9, fill=t["muted"], layer="top",
                      box=(40, y, W - 80, 52))
            x += math.ceil(len(text) * 4.9) + 24

    # -- output ----------------------------------------------------------------------------

    def render(self) -> str:
        t = self.t
        markers = "".join(
            f'<marker id="{self.slug}-{k}" markerWidth="8" markerHeight="6" refX="7" refY="3" '
            f'orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{c}"/></marker>'
            for k, c in (("default", t["muted"]), ("accent", t["accent"]),
                         ("link", t["link"]), ("ink", t["ink"]), ("soft", t["soft"])))
        body = "".join("".join(self.layers[k]) for k in self.layers)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {self.h}" '
                f'role="img" aria-labelledby="{self.slug}-title {self.slug}-desc">'
                f'<title id="{self.slug}-title">{escape(self.title)}</title>'
                f'<desc id="{self.slug}-desc">{escape(self.desc)}</desc>'
                f'<defs>{markers}</defs>'
                f'<rect width="{W}" height="{self.h}" rx="12" fill="{t["paper"]}"/>'
                f'{body}</svg>')


# ── 1 · the skills around the repository ─────────────────────────────────────────────────

def skills(t: dict) -> Svg:
    s = Svg("skills", 600, t, "The skills around one documentation repository",
            "What comes into the documentation repository through which skill, what goes "
            "out of it through which, and the two that check it and write it in parallel.")
    s.eyebrow(40, 32, "THE SKILLS · AROUND ONE REPOSITORY")

    cap_l, sk_l, repo, sk_r, cap_r = (40, 120), (184, 176), (384, 176), (584, 184), (792, 128)
    tops = (136, 232, 328)
    ins = [("Client documents", ["decks · PDFs", "sheets · offers"]),
           ("Something said", ["in a meeting,", "a call, a chat"]),
           ("You, deciding", ["one question", "at a time"])]
    left = [("Start the project", "start", "the documents are in docs-in/"),
            ("Record what was said", "requirement", "we decided to use Airflow"),
            ("Settle what is open", "resolve", "what do I need to decide?")]
    right = [("Authorize a change", "cycle", "what do we build next?"),
             ("Gate the release", "release", "can we ship 1.7?"),
             ("Tell the people outside", "business, presentation, digest",
              "let’s do the weekly SAL")]
    outs = [("A coding agent", ["a brief for each", "approved CHG"]),
            ("The release", ["ship or rework,", "REL and RLM"]),
            ("The business", ["the SAL, the slides,", "a daily workbook"])]

    for i, top in enumerate(tops):
        cy = top + 36
        s.node(cap_l[0], top + 8, cap_l[1], 56, ins[i][0], ins[i][1], kind="input",
               sub_family=SANS)
        s.node(sk_l[0], top, sk_l[1], 72, left[i][0], [left[i][1]], quote=left[i][2])
        s.node(sk_r[0], top, sk_r[1], 72, right[i][0], [right[i][1]], quote=right[i][2])
        s.node(cap_r[0], top + 8, cap_r[1], 56, outs[i][0], outs[i][1], kind="external",
               sub_family=SANS)
        s.wire([(cap_l[0] + cap_l[1], cy), (sk_l[0], cy)])
        s.wire([(sk_l[0] + sk_l[1], cy), (repo[0], cy)])
        s.wire([(repo[0] + repo[1], cy), (sk_r[0], cy)])
        s.wire([(sk_r[0] + sk_r[1], cy), (cap_r[0], cy)], kind="accent" if i == 0 else "default")

    # The repository, focal: what it holds, by its top level.
    rx, rw, ry, rh = repo[0], repo[1], 136, 264
    s.box(rx, ry, rw, rh, "focal")
    s.text(rx + rw // 2, ry + 26, "Your documentation", size=12, weight=600, anchor="middle",
           box=(rx, ry, rw, rh))
    s.text(rx + rw // 2, ry + 40, "one repository, beside the code", size=9,
           fill=t["muted"], anchor="middle", box=(rx, ry, rw, rh))
    for j, c in enumerate(("AGENTS.md", "OPEN.md", "GLOSSARY.md", "COMMITMENTS.md",
                           "decisions/", "products/<p>/", "initiatives/<i>/")):
        s.chip(rx + 16, ry + 56 + 28 * j, rw - 32, 20, c)

    # Above: writing it in parallel. Below: checking it.
    cx = rx + rw // 2
    s.node(rx, 40, rw, 64, "Work in parallel", ["contribute"], kind="step", dashed=True,
           quote="take a thread")
    s.wire([(cx, 104), (cx, ry)], dashed=True)
    s.label(cx + 10, 124, "AT A JOIN", anchor="start")
    s.node(rx, 440, rw, 72, "Check they agree", ["audit · validate.py in CI"],
           quote="check the docs")
    s.wire([(cx, 440), (cx, ry + rh)])
    s.label(cx + 10, 424, "CHECKS", anchor="start")

    s.callout(40, 468, "You do not choose a skill.", box=(40, 440, 320, 72))
    s.callout(40, 488, "You say what happened, and one answers.", box=(40, 440, 320, 72))
    s.callout(W - 40, 468, "Only an approved CHG goes out to be built:", anchor="end",
              box=(584, 440, 336, 72))
    s.callout(W - 40, 488, "a request is not a mandate.", anchor="end",
              box=(584, 440, 336, 72))

    s.legend([("focal", "the repository"), ("step", "a skill"), ("input", "what comes in"),
              ("external", "what goes out"), ("dashed", "additive mode only"),
              ("accent-line", "the one authorization out")])
    return s


# ── 2 · the lifecycle and its gates ──────────────────────────────────────────────────────

def lifecycle(t: dict) -> Svg:
    s = Svg("lifecycle", 636, t, "The lifecycle and its gates",
            "Discovery per initiative from F1 to F3, construction per product from F4 to F6, "
            "and the loop of operation and evolution that returns to the build, with the "
            "gates crossed once and the controls repeated on every lap.")
    s.eyebrow(40, 28, "THE LIFECYCLE · AND ITS GATES")
    c = (40, 276, 512, 748)
    nw, nh = 172, 72
    A, B, C = 80, 240, 392
    cyA, cyB, cyC = A + 36, B + 36, C + 36

    # The notes of B and C end where no connector comes down through the header.
    s.zone(24, 40, 912, 128, "DISCOVERY", "per initiative, elastic", note_end=920)
    s.zone(24, 200, 676, 128, "CONSTRUCTION", "per product · F5 and F6 on every lap",
           note_end=684)
    s.zone(24, 352, 912, 160, "OPERATION AND EVOLUTION", "per product, a loop", note_end=780)

    # Connectors first.
    s.wire([(c[0] + nw, cyA), (c[1], cyA)])
    s.wire([(c[1] + nw, cyA), (c[2], cyA)])
    s.wire([(c[2] + 86, A + nh), (c[2] + 86, 188), (180, 188), (180, B)])
    s.wire([(c[0] + nw, cyB), (c[1], cyB)], kind="accent")
    s.wire([(c[1] + nw, cyB), (c[2], cyB)])
    s.wire([(480, cyB - 8), (480, 224), (412, 224), (412, B)], dashed=True)
    s.label(446, 214, "REWORK")
    s.wire([(c[2] + nw, cyB), (794, cyB), (794, C)])
    s.wire([(874, C), (874, A + nh)], kind="link", dashed=True)
    s.label(864, 196, "RE-ENTRY", kind="link", anchor="end")
    s.wire([(c[3], cyC), (c[2] + nw, cyC)])
    s.wire([(c[2], cyC), (c[1] + nw, cyC)])
    s.wire([(480, cyC + 8), (480, 500), (88, 500), (88, C + nh)])
    s.label(300, 488, "NOT STRUCTURAL")
    # MOR is a side path walked once, after the first period of real use, as the mermaid
    # draws it: every other lap goes from run straight to intake.
    s.wire([(800, C + nh), (800, 488), (640, 488), (640, C + nh)], dashed=True)
    s.wire([(c[1], cyC), (c[0] + nw, cyC)])
    s.wire([(196, C), (196, 344), (318, 344), (318, B + nh)])
    s.label(244, 332, "NEXT LAP")

    # Gates: outlined once, filled on every lap, the accent where the framework tightens.
    for x, y, kind, name, where in ((244, cyA, "gate", "G1", "above"),
                                    (480, cyA, "gate", "G2", "above"),
                                    (520, 188, "gate", "G3", "above"),
                                    (244, cyB, "focal", "G4", "above"),
                                    (480, cyB, "control", "RG", "below"),
                                    (720, 488, "gate", "MOR · ONCE", "below"),
                                    (480, cyC, "control", "ICG", "above")):
        s.diamond(x, y, kind)
        k = "accent" if kind == "focal" else "ink"
        if where == "above":
            s.label(x, y - 14, name, kind=k)
        elif where == "below":
            s.label(x, y + 22, name, kind=k)
        else:
            s.label(x - 14, y + 3, name, kind=k, anchor="end")

    s.node(c[0], A, nw, nh, "Signal and framing", ["PRB · HYP"], tag="F1")
    s.node(c[1], A, nw, nh, "Problem discovery", ["WF §current · EVD"], tag="F2")
    s.node(c[2], A, nw, nh, "Solution discovery", ["WF §target · CMP · DFB · RSK"],
           tag="F3")
    s.node(c[3], A, nw, nh, "Back into discovery",
           ["invalidated by MOR or ICG", "problem → F2 · solution → F3",
            "a new initiative → F1"],
           kind="reentry", dashed=True)
    s.node(c[0], B, nw, nh, "Shaping MVP and MVA", ["PBR · SD · EVP · DC",
                                                     "RMP · DEC"], tag="F4")
    s.node(c[1], B, nw, nh, "Build a candidate", ["ARC lives from here", "LOG · code"],
           tag="F5")
    s.node(c[2], B, nw, nh, "Controlled go-live", ["EVR · REL · RLM",
                                                    "RB, the first time"], tag="F6")
    s.node(c[3], C, nw, nh, "Run and observe", ["LOG", "incident · drift · feedback"])
    s.node(c[2], C, nw, nh, "Intake and triage", ["signals from LOG",
                                                   "increments from RMP"])
    s.node(c[1], C, nw, nh, "Reshaping", ["PBR · WF · ARC · EVP",
                                           "DC · RSK · RMP · DEC"])
    s.node(c[0], C, nw, nh, "Change contract", ["CHG · what is authorized",
                                                 "then IMP · this cycle"], kind="focal")

    s.callout(40, 540, "Every gate leaves something written: one with no written trace is a meeting.",
              box=(40, 520, 880, 32))
    s.callout(40, 562, "Elastic before G4, strict after it.", box=(40, 542, 880, 32))
    s.legend([("step", "a phase or a step"), ("gate", "gate, crossed once"),
              ("control", "control, every lap"), ("focal-gate", "where it tightens"),
              ("focal", "what an agent builds"), ("reentry", "out of the loop")])
    return s


# ── 3 · the documents, read from the registry ────────────────────────────────────────────

AXES = (("platform", "PLATFORM", "at the root, shared by every product"),
        ("product", "PRODUCT", "in products/<p>/, for as long as the system lives"),
        ("initiative", "INITIATIVE", "in initiatives/<i>/, born and closed with it"))
CLASSES = (("living", "LIVING", "How it is now",
            "one file, always current; in the additive mode, as of the last join", 3),
           ("immutable", "IMMUTABLE", "Why it was decided",
            "a new file each time, superseded, never rewritten", 2),
           ("append-only", "APPEND-ONLY", "What happened", "lines added, never edited", 1))
# What an empty cell means, where the framework says it. Any other empty cell is a dash.
EMPTY = {("initiative", "living"): "none: an initiative’s documents are not maintained"}


def documents(t: dict) -> Svg:
    types = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))["types"]
    known_axes, known_classes = {a for a, *_ in AXES}, {c for c, *_ in CLASSES}
    cells: dict[tuple[str, str], list[dict]] = {}
    for spec in types.values():
        if spec["axis"] not in known_axes or spec["lifecycle"] not in known_classes:
            sys.exit(f"{spec['id']}: axis {spec['axis']!r} or lifecycle {spec['lifecycle']!r} "
                     "has no place in the map; give it one in docs/readme/build.py")
        cells.setdefault((spec["axis"], spec["lifecycle"]), []).append(spec)
    if not any(spec["id"] == "OPEN" for spec in types.values()):
        sys.exit("the map's focal chip is OPEN, and the registry no longer has it")

    cw, ch, gap, pad = 132, 48, 8, 8
    widths = [n * cw + (n - 1) * gap + 2 * pad for *_, n in CLASSES]
    xs = [40]
    for w in widths[:-1]:
        xs.append(xs[-1] + w + gap)
    bands = []
    for axis, *_ in AXES:
        rows = max(math.ceil(len(cells.get((axis, c), [])) / n) or 1 for c, *_, n in CLASSES)
        bands.append(32 + rows * (ch + gap) + 4)
    top = 120
    height = top + sum(bands) + 12 * len(bands) + 32 + 64

    s = Svg("documents", height, t, "Where each document lives, and how each is kept",
            "The artifact types of the framework placed by the axis they belong to, platform, "
            "product or initiative, and by their class, living, immutable or append-only, "
            "as the registry declares them.")
    s.eyebrow(40, 32, "THE DOCUMENTS · WHERE EACH LIVES, HOW EACH IS KEPT")
    s.text(W - 40, 32, "drawn from schemas/artifact-types.yaml", size=8, fill=t["soft"],
           family=MONO, anchor="end", box=(480, 16, 440, 24))

    for (lc, label, question, rule, _), x, w in zip(CLASSES, xs, widths):
        s.eyebrow(x + pad, 60, label, fill=t["ink"], box=(x, 44, w, 64))
        s.text(x + pad, 80, question, size=12, weight=600, box=(x, 44, w, 64))
        s.text(x + pad, 96, rule, size=9, fill=t["muted"], box=(x, 44, w, 64))

    y = top
    for (axis, label, where), bh in zip(AXES, bands):
        s.zone(24, y, W - 48, bh, label, where)
        for (lc, *_, n), x, w in zip(CLASSES, xs, widths):
            specs = cells.get((axis, lc), [])
            if not specs:
                why = EMPTY.get((axis, lc))
                s.text(x + w // 2, y + 32 + ch // 2 + 4, why or "—", size=9 if why else 12,
                       fill=t["soft"], anchor="middle", box=(x, y, w, bh))
            if x > 40:
                s.layers["zones"].append(
                    f'<line x1="{x - gap // 2}" y1="{y + 32}" x2="{x - gap // 2}" '
                    f'y2="{y + bh - 8}" stroke="{rgba(t["ink_rgb"], 0.14)}" '
                    f'stroke-width="0.8" stroke-dasharray="2,3"/>')
            for k, spec in enumerate(specs):
                cx = x + pad + (k % n) * (cw + gap)
                cy = y + 32 + (k // n) * (ch + gap)
                focal = spec["id"] == "OPEN"
                optional = str(spec.get("born_in", "")).startswith("only if")
                s.box(cx, cy, cw, ch, "focal" if focal else "chip", dashed=optional)
                b = (cx, cy, cw, ch)
                s.text(cx + 8, cy + 16, spec["id"], size=9, weight=600, family=MONO,
                       fill=t["accent"] if focal else t["ink"], box=b)
                name = spec["name"].replace("**", "")
                lines = textwrap.wrap(name, 25)
                note = spec.get("class_note")
                if len(lines) + bool(note) > 2:
                    sys.exit(f"{spec['id']}: {name!r} and its note need more than two lines")
                for i, line in enumerate(lines):
                    s.text(cx + 8, cy + 30 + 11 * i, line, size=9, fill=t["muted"], box=b)
                if note:
                    s.text(cx + 8, cy + 41, note, size=8, fill=t["soft"], family=MONO, box=b)
        y += bh + 12

    s.callout(40, y + 18, "OPEN is the one that is not single: one per product, one for a shared "
                          "substrate, one at the root.", box=(40, y, 880, 32))
    s.legend([("chip", "an artifact type"), ("focal", "read before deciding anything"),
              ("dashed", "born only with the decision to share a substrate")])
    return s


# ── 4 · the additive mode: threads and a join ────────────────────────────────────────────

def threads(t: dict) -> Svg:
    s = Svg("threads", 588, t, "Threads and a join in the additive mode",
            "The main line moves only at a join: threads computed by the to-do and a parking "
            "branch write new files directly and everything a living document should say as "
            "a pending effect, and an admin's join applies the effects and lands it all.")
    s.eyebrow(40, 32, "THE ADDITIVE MODE · THREADS AND A JOIN")
    MAIN, JOIN, TA, TB, PK = 96, 176, 256, 336, 416
    lanes = ((MAIN, "MAIN LINE", "main", "moves only at a join"),
             (JOIN, "JOIN", "work.py join", "admin, deputy or delegate"),
             (TA, "THREAD", "open --thread <t>", "computed by the to-do"),
             (TB, "THREAD", "open --thread <t>", "taken whole, by one person"),
             (PK, "PARKING", "open --branch <slug>", "what belongs to no thread"))
    for i, (y, name, cmd, note) in enumerate(lanes):
        b = (40, y - 40, 152, 80)
        s.eyebrow(40, y - 8, name, fill=t["ink"], box=b)
        s.text(40, y + 6, cmd, size=9, fill=t["muted"], family=MONO, box=b)
        s.text(40, y + 19, note, size=9, fill=t["soft"], box=b)
        if i:
            s.layers["zones"].append(
                f'<line x1="40" y1="{y - 40}" x2="{W - 40}" y2="{y - 40}" '
                f'stroke="{rgba(t["ink_rgb"], 0.10)}" stroke-width="0.8"/>')

    # The main line, and the to-do the threads come out of.
    s.wire([(200, MAIN), (W - 40, MAIN)], kind="ink", head=False, width=1.6)
    # Threads, deepest first so no branch crosses another.
    for x, lane, end in ((240, PK, 728), (264, TB, 704), (288, TA, 680)):
        s.wire([(x, MAIN + 14), (x, lane), (end, lane), (end, JOIN + 4)], width=1.4)
    s.wire([(632, MAIN), (632, JOIN), (904, JOIN), (904, MAIN + 4)], kind="accent",
           width=1.6)
    s.label(892, 140, "JOIN --MERGE", kind="accent", anchor="end")
    s.label(620, 140, "WORK.PY JOIN", kind="accent", anchor="end")

    s.chip(208, MAIN - 14, 136, 28, "todo.py · the threads")
    s.text(W - 40, MAIN - 16, "living documents current again", size=9, fill=t["muted"],
           anchor="end", box=(600, MAIN - 40, 320, 32))
    for x in (680, 704, 728):
        s.dot(x, JOIN, fill=t["accent"], r=3)
    s.dot(904, MAIN, r=4)

    def commit(x, lane, ident, note, dashed=False, w=128):
        s.box(x, lane - 18, w, 36, "chip", dashed=dashed)
        b = (x, lane - 18, w, 36)
        s.text(x + w // 2, lane - 3, ident, size=9, weight=600, family=MONO, anchor="middle",
               box=b)
        s.text(x + w // 2, lane + 10, note, size=9, fill=t["muted"], anchor="middle", box=b)

    commit(320, TA, "DEC-110", "a new decision")
    commit(464, TA, "ARC.md#current", "a pending effect", dashed=True, w=152)
    commit(320, TB, "CHG-031", "a new change, in draft")
    commit(464, TB, "WF.md#target", "a pending effect", dashed=True, w=152)
    commit(320, PK, "SIG-014 · OD-051", "a LOG line, an OPEN entry", w=136)
    s.box(736, JOIN - 18, 144, 36, "focal")
    b = (736, JOIN - 18, 144, 36)
    s.text(808, JOIN - 3, "effects → living docs", size=9, weight=600, family=MONO,
           anchor="middle", fill=t["accent"], box=b)
    s.text(808, JOIN + 10, "changes approved, validated", size=9, fill=t["muted"],
           anchor="middle", box=b)

    s.callout(40, 484, "During a thread nobody rewrites a living document:",
              box=(40, 464, 880, 32))
    s.callout(40, 506, "what it should say waits, as an effect, for the join.",
              box=(40, 486, 880, 32))
    s.legend([("chip", "written directly on the branch"),
              ("dashed", "a pending effect, in _filoni/<slug>/effetti.md"),
              ("focal", "the join rewrites the living documents")])
    return s


DIAGRAMS = {"skills": skills, "lifecycle": lifecycle, "documents": documents,
            "threads": threads}

PRELOAD = ('<div aria-hidden="true" style="position:absolute;opacity:0">'
           f'<span style="font:600 12px {SANS}">a</span><span style="font:9px {MONO}">a</span>'
           f'<span style="font:600 9px {MONO}">a</span>'
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
                    "document.fonts.ready.then(() => ['600 12px Geist', '9px \"Geist Mono\"', "
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
