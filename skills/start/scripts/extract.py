#!/usr/bin/env python3
"""
Provenance-preserving extractor for a business document corpus.

It does not summarise and does not interpret: it normalises. It produces text
blocks, each labelled with its document and position (slide N, page N, section),
because without exact provenance the extraction is unusable: you have to go back
to the original slide every time a claim needs checking.

It also flags the pages that need visual inspection. On a sales deck this is
the part that matters most: the architectural promise is usually not written,
it is drawn. Three boxes with arrows saying "one single platform" produce no
extractable text at all and are a tenancy constraint.

Usage:
  python3 extract.py --doctor                       what is installed
  python3 extract.py --find .                       where is the corpus
  python3 extract.py <file-or-folder> [...] -o out/
  python3 extract.py _meta/corpus/<p> -o _meta/extract/<p> --jsonl
  python3 extract.py corpus/ -o out/ --min-chars 40 threshold for "text-poor page"

Output in out/:
  extract.md      blocks with a provenance heading, readable
  extract.jsonl   one JSON line per block (with --jsonl)
  inventory.json  inventory of documents and pages needing visual inspection
  render/         images of the flagged pages, ready to look at

Dependencies. Check them before ingesting: with one missing, the formats that
needed it produce zero blocks, and a corpus quietly short of a third of itself
still reads as complete.

  anydoc         every office format, and the only converter here.
                 `npm install -g @firecrawl/anydoc` gives a command;
                 `pip install firecrawl-anydoc` gives an importable module.
                 Same engine either way, and this script takes whichever it
                 finds. Set ANYDOC_BIN to point at a specific binary.
  poppler-utils  PDF, and not optional there. It is what gives a page a number,
                 what tells a scanned PDF from a readable one, and what
                 rasterises the pages somebody has to look at. anydoc converts
                 PDFs too, and is the fallback, but its model has no page in it.
  LibreOffice    optional, and only for a legacy binary .ppt. anydoc reads that
                 format, but there is no package to split, so the slide numbers
                 are lost unless soffice converts it to .pptx first.
"""

from __future__ import annotations

import argparse
import io
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass, asdict, field
from pathlib import Path

# Extension to the format name anydoc knows. This doubles as the list of what the
# extractor handles, and the format is passed explicitly rather than left to content
# detection: the extension is what routed the file to its handler in the first place, so
# using it here too means a file whose name lies fails loudly instead of being parsed as
# whatever it happens to look like inside.
ANYDOC_FORMAT = {
    ".pptx": "pptx", ".pptm": "pptx", ".ppsx": "pptx", ".ppsm": "pptx",
    ".potx": "pptx", ".potm": "pptx",
    ".ppt": "ppt", ".pps": "ppt", ".pot": "ppt",
    ".docx": "docx", ".docm": "docx", ".doc": "doc",
    ".odt": "odt", ".rtf": "rtf", ".epub": "epub",
    ".xlsx": "xlsx", ".xlsm": "xlsx", ".xlsb": "xlsx", ".xls": "xlsx",
    ".ods": "ods", ".csv": "csv",
    ".odp": "odp",
    ".pdf": "pdf",
}
SUPPORTED = set(ANYDOC_FORMAT) | {".md", ".txt"}
LEGACY_PPT = {".ppt", ".pps", ".pot"}

ANYDOC_INSTALL = ("needs anydoc: `npm install -g @firecrawl/anydoc` "
                  "or `pip install firecrawl-anydoc`")

# Levels 1 and 2 only. A deeper heading is a place inside a section, not another place in
# the document, and splitting there gives one block per paragraph.
HEADING = re.compile(r"^(#{1,2})\s+(.+?)\s*$", re.M)

# Namespace-agnostic: the prefix is `p:` in every deck anyone has produced, and assuming
# it is the kind of thing that holds until the one deck that matters is written by a
# generator nobody has heard of.
SLD_LST = re.compile(r"<(?:\w+:)?sldIdLst\b[^>]*>(.*?)</(?:\w+:)?sldIdLst>", re.S)
SLD_ONE = re.compile(r"<(?:\w+:)?sldId\b[^>]*?(?:/>|>.*?</(?:\w+:)?sldId>)", re.S)


@dataclass
class Block:
    source: str          # file name
    locator: str         # "slide 4", "page 12", "§ Pricing", "document"
    text: str
    kind: str = "text"   # text | notes | table


@dataclass
class DocInfo:
    source: str
    kind: str
    units: int = 0                 # slides, pages or sections
    chars: int = 0
    has_text_layer: bool = True
    visual_review: list[int] = field(default_factory=list)
    rendered: int = 0              # how many flagged pages were rasterised
    note: str = ""


def run(cmd: list[str]) -> tuple[int, str]:
    # Explicit `encoding`, not the locale's: poppler emits UTF-8, and on Windows the
    # locale is cp1252. With the implicit codec a page containing a curly quote raises
    # UnicodeDecodeError inside subprocess's reader thread, where the exception does not
    # propagate: the page comes back empty and gets flagged as "text-poor", which is to
    # say as graphical content. The tool then sends you to look at an image that does not
    # exist instead of telling you it could not read.
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                           encoding="utf-8", errors="replace")
        return p.returncode, p.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return 1, f"{e}"


# ── anydoc ──────────────────────────────────────────────────────────────────

_MODULE: object | bool | None = None      # None: not looked yet. False: not installed.
_READY: str | None = None


def anydoc_ready() -> str:
    """Empty when anydoc can be reached, otherwise the line that says how to install it.

    Asked once, before any document is opened, so that a missing converter is reported as
    one fact about the run rather than as the same sentence repeated under every file. The
    two installation routes give different things — the pip package installs a module and
    no command, the npm package a command and no module — and either is enough.
    """
    global _MODULE, _READY
    if _READY is not None:
        return _READY
    try:
        import anydoc                                     # type: ignore
        _MODULE, _READY = anydoc, ""
    except ImportError:
        _MODULE = False
        _READY = "" if (os.environ.get("ANYDOC_BIN") or shutil.which("anydoc")) \
                 else ANYDOC_INSTALL
    return _READY


def toolchain() -> dict:
    """What is installed, at which version, and what is lost without each.

    Recorded as well as printed. Two machines with different poppler versions produce
    different text from one PDF, and without a stamp in the inventory a corpus extracted
    last month cannot be compared with the same corpus extracted today: the difference reads
    as the documents having changed.
    """
    def version(cmd: list[str], pattern: str = r"(\d+[\d.]+)") -> str | None:
        if not shutil.which(cmd[0]):
            return None
        # Both streams. Poppler prints its version to stderr, which is why the first
        # version of this reported every one of its four tools as "present, version
        # unknown" -- a diagnostic that says nothing is worse than no diagnostic, because
        # it looks like it looked.
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                               encoding="utf-8", errors="replace")
        except (subprocess.TimeoutExpired, OSError):
            return "present, would not answer"
        m = re.search(pattern, (r.stdout or "") + (r.stderr or ""))
        return m.group(1) if m else "present, version unknown"

    mod = None
    try:
        import anydoc                                          # type: ignore
        mod = getattr(anydoc, "__version__", "present, version unknown")
    except ImportError:
        pass
    exe = os.environ.get("ANYDOC_BIN") or shutil.which("anydoc")

    return {
        "anydoc": {"module": mod, "command": version([exe, "-V"]) if exe else None,
                   "needed_for": "every office format. Without it they produce no blocks"},
        "poppler": {k: version([k, "-v"] if k != "pdftotext" else ["pdftotext", "-v"])
                    for k in ("pdfinfo", "pdftotext", "pdffonts", "pdftoppm")},
        "libreoffice": {"soffice": version(["soffice", "--version"]),
                        "needed_for": "rasterising a deck, and slide numbers in a legacy .ppt"},
    }


def report_doctor(as_json: bool) -> int:
    """`--doctor`: say what is installed and what each absence costs."""
    t = toolchain()
    anydoc_ok = bool(t["anydoc"]["module"] or t["anydoc"]["command"])
    poppler_ok = all(t["poppler"].values())
    if as_json:
        print(json.dumps(t, indent=2, ensure_ascii=False))
        return 0 if anydoc_ok and poppler_ok else 1

    rows = [("anydoc (module)", t["anydoc"]["module"]),
            ("anydoc (command)", t["anydoc"]["command"])]
    rows += [(k, v) for k, v in t["poppler"].items()]
    rows += [("soffice", t["libreoffice"]["soffice"])]
    for name, v in rows:
        print(f"  {name:<20} {v or 'ABSENT'}")
    print()
    if not anydoc_ok:
        print(f"! {ANYDOC_INSTALL}")
        print("  Without it every office document produces zero blocks.")
    if not poppler_ok:
        print("! poppler is incomplete: `apt install poppler-utils`.")
        print("  Without it a PDF has no page numbers, a scanned PDF cannot be told from an "
              "unreadable one, and no page is rasterised.")
    if not t["libreoffice"]["soffice"]:
        print("- LibreOffice absent, which is allowed: a deck's flagged slides are not "
              "rasterised and a legacy .ppt loses its slide numbers. Everything else works.")
    if anydoc_ok and poppler_ok:
        print("Nothing degraded.")
    return 0 if anydoc_ok and poppler_ok else 1


def wrote_by_framework(path: Path) -> bool:
    """A Markdown file this framework produced, rather than one the business handed over.

    Both are `.md` and both sit in the project. The front matter is what separates them, and
    it has to be read rather than guessed from the location: a corpus dropped at the root
    next to `AGENTS.md` is exactly the case this is for.
    """
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:400]
    except OSError:
        return False
    return head.startswith("---") and "schema: framework/" in head


def find_corpus(root: Path) -> list[tuple[str, int, int]]:
    """Directories holding documents somebody handed over, most likely first.

    The skill has to know where the corpus is before it can move it, and the answer is not
    knowable from here: people drop client files in `corpus`, in `docs`, in `documenti`, in
    a folder named after the customer, or loose at the project root. Guessing by name would
    work for the first three and fail silently on the others, so this counts documents
    instead: a directory holding files in a business format, none of which this framework
    wrote.

    Returns (relative directory, business documents, plain notes). Ranked by the first
    count, because a folder of PDFs and decks is a corpus and a folder of `.md` files might
    be anything.
    """
    found: dict[str, list[int]] = {}
    for p in sorted(root.rglob("*")):
        suffix = p.suffix.lower()
        if p.is_dir() or suffix not in SUPPORTED:
            continue
        parts = p.relative_to(root).parts
        if any(x.startswith(".") for x in parts):
            continue
        if any(x in {"node_modules", "__pycache__", "build", "render", "_conv"}
               for x in parts[:-1]):
            continue
        rel_dir = "/".join(parts[:-1])
        # This framework's own output, not somebody's documents. Named as a path so a
        # project keeping an ETL step in `extract/` is not quietly skipped over.
        if rel_dir == "_meta/extract" or rel_dir.startswith("_meta/extract/"):
            continue
        if suffix in {".md", ".txt"} and wrote_by_framework(p):
            continue
        counts = found.setdefault(rel_dir or ".", [0, 0])
        counts[0 if suffix in ANYDOC_FORMAT else 1] += 1
    return sorted(((d, b, n) for d, (b, n) in found.items()),
                  key=lambda r: (-r[1], -r[2], r[0]))


def group_corpus(rows: list[tuple[str, int, int]]) -> list[dict]:
    """Sibling directories of one corpus, gathered under the folder that holds them.

    `docs/contracts`, `docs/decks` and `docs/spreadsheets` are one corpus filed by kind, and
    reported as three candidates they force a question with no right answer. Grouped by the
    first path component they are one, and the extractor reads a directory recursively so
    the group is directly usable as the corpus root.

    Grouping is by first component and nothing cleverer, because the alternatives are worse.
    Names cannot be trusted -- that is what `--find` exists to avoid -- and file dates say
    when a file was copied, not which version is current. `corpus/` beside `vecchi-deck/`
    stays two groups, which is the case that has to be asked about.

    The children are kept and printed. When a group has more than one, the skill says so:
    `client-files/2025` and `client-files/2026` group correctly and are still worth a
    sentence, and no rule here can tell which year is the offer that was signed.
    """
    groups: dict[str, dict] = {}
    for d, business, notes in rows:
        head = d.split("/", 1)[0]
        g = groups.setdefault(head, {"path": head, "documents": 0, "notes": 0,
                                     "children": []})
        g["documents"] += business
        g["notes"] += notes
        if d != head:
            g["children"].append({"path": d, "documents": business, "notes": notes})
    for g in groups.values():
        g["children"].sort(key=lambda c: (-c["documents"], c["path"]))
    return sorted(groups.values(), key=lambda g: (-g["documents"], -g["notes"], g["path"]))


def report_corpus(root: Path, as_json: bool = False) -> int:
    """`--find`: say where the corpus is, or say that somebody has to be asked."""
    groups = group_corpus(find_corpus(root))
    strong = [g for g in groups if g["documents"]]
    verdict = "one" if len(strong) == 1 else ("none" if not strong else "several")

    if as_json:
        print(json.dumps({"root": str(root), "verdict": verdict,
                          "corpus": strong[0]["path"] if verdict == "one" else None,
                          "candidates": groups}, indent=2, ensure_ascii=False))
        return 0 if verdict == "one" else 1

    if not groups:
        print(f"No business documents under {root}.")
        print("Ask where they are. Do not scaffold a repository around a corpus you have "
              "not found: an empty ingestion looks the same as a corpus with nothing in it.")
        return 1

    print(f"{_n(len(groups), 'candidate', 'candidates')} under {root}:\n")
    for g in groups:
        detail = _n(g["documents"], "business document", "business documents")
        if g["notes"]:
            detail += f", {_n(g['notes'], 'plain note', 'plain notes')}"
        if g["children"]:
            detail += f", across {_n(len(g['children']), 'directory', 'directories')}"
        print(f"  {g['path']:<40} {detail}")
        for c in g["children"]:
            print(f"    {c['path']:<38} {c['documents']}")
    print()

    if verdict == "none":
        print("Nothing here looks like a business document. Ask where they are.")
        return 1
    if verdict == "one":
        print(f"One candidate: {strong[0]['path']}")
        if len(strong[0]["children"]) > 1:
            print("It holds several subdirectories. Name them when you report which folder "
                  "you are using: one of them being an older version of another is not "
                  "something this can see.")
        return 0
    print("More than one candidate. Ask which of these holds the documents the business "
          "handed over, and do not pick the largest: the other one is often an earlier "
          "version of the same deck, and which is current is not something a file count "
          "can tell you.")
    return 1


def is_deck(pdfinfo_meta: str) -> bool:
    """Whether a PDF is a presentation, from the page geometry `pdfinfo` already reports.

    A4 portrait is 595 x 842 and a 16:9 slide is 960 x 540. Wide landscape means slides,
    and that changes what a thin page means: on a report two hundred characters is a short
    page, on a slide it is a title over a diagram.

    The line sits at 1.25, which is below 4:3, and that is a deliberate inclusion rather
    than a loose bound. 4:3 is 1.33 and landscape A4 is 1.41, so a ratio cannot separate an
    old deck from a wide report — only 16:9 at 1.78 sits clearly above both. Given that,
    the question is which mistake to make, and the two are not the same size: a deck read
    as a report loses whatever was drawn on it, while a report read as a deck costs almost
    nothing, because the rule the flag feeds is measured against the document's own pages
    and a text-dense report has no page thin against its own median.
    """
    m = re.search(r"^Page size:\s+([\d.]+) x ([\d.]+)", pdfinfo_meta, re.M)
    if not m:
        return False
    w, h = float(m.group(1)), float(m.group(2))
    return h > 0 and w / h >= 1.25


def thin_against_median(sizes: dict[int, int]) -> list[int]:
    """Pages carrying less than half the text of the typical page beside them.

    Measured against the document's own pages and not against a constant, which is what
    makes it need no calibrating: a uniformly dense deck flags nothing, and that is the
    right answer for one. A fixed threshold cannot do this. On the deck that prompted it,
    forty characters caught one page of nine while three more were mostly picture — among
    them the one naming the source systems and promising real time, all of it inside
    screenshots and none of it in the extracted text.
    """
    if not sizes:
        return []
    ordered = sorted(sizes.values())
    median = ordered[len(ordered) // 2]
    return sorted(n for n, c in sizes.items() if c < median / 2)


def on_slide_chars(md: str) -> int:
    """How much text is on the slide, which is not how much text the slide produced.

    anydoc renders the speaker notes as a blockquote after the slide's own content, and
    they do not count: the question the threshold answers is whether the slide is a picture,
    and a picture with a talkative presenter is still a picture. Counting them is how a
    diagram carrying the whole architectural promise stays unflagged because somebody wrote
    two sentences of patter under it — which is precisely the slide this is looking for.

    A real quotation in the slide body is counted out too. That costs a glance at a slide
    that turns out to be fine, against missing the one that is not.
    """
    return sum(len(ln) for ln in md.split("\n") if not ln.lstrip().startswith(">"))


def _n(count: int, one: str, many: str) -> str:
    return f"{count} {one}" if count == 1 else f"{count} {many}"


def _labelled(msg: str) -> str:
    # The command already prefixes its own name and the module's exceptions do not. Adding
    # one unconditionally produced `anydoc: anydoc: malformed document`, which reads like
    # two layers failing rather than one thing saying its name.
    msg = str(msg).strip()
    return msg if msg.lower().startswith("anydoc") else f"anydoc: {msg}"


def anydoc_markdown(data: bytes, fmt: str) -> tuple[str, str]:
    """Convert bytes to Markdown. Returns (markdown, error); one of the two is empty.

    The module is preferred over the command because a forty slide deck is forty
    conversions, and in process they cost nothing. When only the command is installed the
    document goes in on stdin, which keeps the sliced decks below out of temporary files.
    """
    if (miss := anydoc_ready()):
        return "", miss
    if _MODULE:
        try:
            return _MODULE.to_markdown_bytes(data, fmt) or "", ""   # type: ignore[attr-defined]
        except Exception as e:                            # anydoc raises a family of these
            return "", _labelled(e)
    exe = os.environ.get("ANYDOC_BIN") or shutil.which("anydoc")
    try:
        p = subprocess.run([exe, "-", "--format", fmt], input=data,
                           capture_output=True, timeout=300)
    except (subprocess.TimeoutExpired, OSError) as e:
        return "", _labelled(e)
    if p.returncode != 0:
        err = p.stderr.decode("utf-8", "replace").strip()
        return "", _labelled(err.splitlines()[-1] if err else f"exit {p.returncode}")
    return p.stdout.decode("utf-8", "replace"), ""


def split_on_headings(src: str, md: str) -> list[Block]:
    """Sections as blocks, each located by its heading.

    anydoc returns one Markdown stream per document and its model has no sections in it,
    so the only structure left that corresponds to a place a reader can find again is the
    heading: a Word outline level, a worksheet name, an EPUB chapter. `§ Pricing` sends
    somebody to a point in the file; `document` sends them to the file.

    The heading line stays inside its own block. Dropping it would lose the one document
    whose entire content is headings, and keeping it costs a repeated line.
    """
    md = md.strip()
    if not md:
        return []
    hits = list(HEADING.finditer(md))
    if not hits:
        return [Block(src, "document", md)]

    out = []
    if (pre := md[:hits[0].start()].strip()):
        out.append(Block(src, "preamble", pre))
    for i, h in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(md)
        out.append(Block(src, f"§ {h.group(2)}", md[h.start():end].strip()))
    return out


# ── PPTX ────────────────────────────────────────────────────────────────────

def slice_pptx(data: bytes) -> "Iterator[bytes]":
    """One single-slide package per slide, in presentation order. Yields nothing if it cannot.

    anydoc has no slide in its document model: a whole deck converts to one flat stream
    with nothing marking where slide 3 ended, and the slide number is the entire point of
    the extraction. So the boundary comes from the package instead. Rewriting `sldIdLst`
    to hold one entry and converting that is exact rather than approximate: layout and
    master inheritance, tables and speaker notes all resolve the way they do in the full
    deck, because it *is* the full deck with the running order shortened to one.

    Each slice is a copy of the package, stored rather than deflated so the images are not
    recompressed once per slide.

    A generator, and that is the whole reason this is not a list. Every slice holds the
    entire package, media and all, so returning them together costs deck size times slide
    count: a forty slide deck of thirty megabytes wanted more than a gigabyte, on a machine
    with fifteen. Yielded one at a time, the caller converts a slice and drops it, and the
    peak is one copy. This docstring used to claim that property while the code built the
    whole list, which is worse than the bug: the next reader believes it.
    """
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        names = z.namelist()
        if "ppt/presentation.xml" not in names:
            return
        xml = z.read("ppt/presentation.xml").decode("utf-8", "replace")
    except (zipfile.BadZipFile, OSError, KeyError):
        return                           # legacy binary .ppt, or a package we cannot read

    m = SLD_LST.search(xml)
    if not m:
        return
    ids = SLD_ONE.findall(m.group(1))
    if len(ids) < 2:
        return                           # nothing to split: one slide, or a list we misread

    head, tail = xml[:m.start(1)], xml[m.end(1):]
    for one in ids:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as w:
            for n in names:
                # By name, never by the ZipInfo read out of `z`: writestr stamps the offset
                # of the copy onto the object it is given, and the source archive is then
                # unreadable from the second slide on.
                w.writestr(n, (head + one + tail).encode("utf-8")
                           if n == "ppt/presentation.xml" else z.read(n))
        yield buf.getvalue()


def extract_pptx(path: Path, out: Path, min_chars: int) -> tuple[list[Block], DocInfo]:
    src = path.name
    info = DocInfo(src, "pptx")
    if (miss := anydoc_ready()):
        return [], DocInfo(src, "pptx", note=miss)

    data = path.read_bytes()
    # Pulled one at a time out of a generator, so the peak is one copy of the package and
    # not one per slide. The first is drawn early only to answer "can this be split at all",
    # which decides between the two branches below, and is put back with `chain`.
    slices = slice_pptx(data)
    first = next(slices, None)

    if first is None and path.suffix.lower() in LEGACY_PPT and shutil.which("soffice"):
        # anydoc reads a legacy .ppt, but the binary format carries no package to split, so
        # the whole deck would arrive as one block and every claim in it would lose its
        # slide number. Where LibreOffice happens to be installed, converting first buys
        # the numbers back. It is an improvement and not a requirement: without it the deck
        # is still ingested, and the note below says what it cost.
        rc, _ = run(["soffice", "--headless", "--convert-to", "pptx",
                     "--outdir", str(out / "_conv"), str(path)])
        cand = out / "_conv" / (path.stem + ".pptx")
        if rc == 0 and cand.exists():
            data = cand.read_bytes()
            slices = slice_pptx(data)
            first = next(slices, None)

    if first is None:
        md, err = anydoc_markdown(data, ANYDOC_FORMAT[path.suffix.lower()])
        if not (body := md.strip()):
            info.note = err or "anydoc produced no output"
            return [], info
        info.note = ("converted whole: no slide list to split on, so every claim from this "
                     "deck is located to the file and not to a slide. Checking one means "
                     "reading the deck.")
        if path.suffix.lower() in LEGACY_PPT and not shutil.which("soffice"):
            info.note += " LibreOffice would convert it to .pptx first and restore them."
        blocks = split_on_headings(src, body)
        info.units, info.chars = len(blocks), len(body)
        return blocks, info

    blocks = []
    for n, chunk in enumerate(itertools.chain([first], slices), 1):
        md, err = anydoc_markdown(chunk, "pptx")
        del chunk                    # the copy of the package goes now, not at the next loop
        body = md.strip()
        if err and not info.note:
            info.note = err
        info.chars += len(body)
        info.units = n
        if body:
            blocks.append(Block(src, f"slide {n}", body))
        if on_slide_chars(body) < min_chars:
            info.visual_review.append(n)         # text-poor slide: it is a picture

    if info.visual_review and not info.note:
        info.note = (f"{_n(len(info.visual_review), 'slide', 'slides')} under {min_chars} "
                     "characters: likely graphical content. Worth looking at.")
    return blocks, info


# ── PDF ─────────────────────────────────────────────────────────────────────

def extract_pdf(path: Path, out: Path, min_chars: int) -> tuple[list[Block], DocInfo]:
    src = path.name
    info = DocInfo(src, "pdf")

    if not shutil.which("pdftotext"):
        # Poppler is what gives a PDF page a number, and anydoc's model has no page in it.
        # Falling through keeps the text, and the note has to carry what was lost, because
        # the blocks come out looking like any other. It also has to say that the scanned
        # check did not run: without poppler this script cannot tell a scanned PDF from an
        # unreadable one, and those want opposite responses.
        md, err = anydoc_markdown(path.read_bytes(), "pdf")
        if not (body := md.strip()):
            info.note = (f"{err or 'no text'} - and with poppler missing there is no second "
                         "reader, and no way to tell a scanned PDF from an unreadable one. "
                         "Those want opposite responses. `apt install poppler-utils`.")
            return [], info
        blocks = split_on_headings(src, body)
        info.units, info.chars = len(blocks), len(body)
        info.note = ("poppler is not installed, so this was converted with anydoc, which has "
                     "no page numbers: claims from it are located to the file. It also means "
                     "the scanned check did not run. `apt install poppler-utils`.")
        return blocks, info

    _, meta = run(["pdfinfo", str(path)])
    m = re.search(r"^Pages:\s+(\d+)", meta, re.M)
    info.units = int(m.group(1)) if m else 0

    # `pdfinfo` has been reporting the page geometry all along and nothing was listening.
    # The old signal was "more than 40% of the pages came back thin", which on a wordy deck
    # never fires: the one that prompted this had one page of nine under the threshold and
    # three more that were mostly picture.
    deck = is_deck(meta)

    _, fonts = run(["pdffonts", str(path)])
    info.has_text_layer = len(fonts.strip().splitlines()) > 2
    if not info.has_text_layer:
        info.note = "no text layer: scanned PDF. Look at it page by page, or run OCR."
        info.visual_review = list(range(1, min(info.units, 40) + 1))
        return [], info

    blocks = []
    sizes: dict[int, int] = {}
    for n in range(1, info.units + 1):
        rc, txt = run(["pdftotext", "-layout", "-f", str(n), "-l", str(n), str(path), "-"])
        body = (txt or "").strip()
        info.chars += len(body)
        sizes[n] = len(body)
        if body:
            blocks.append(Block(src, f"page {n}", body))
        if len(body) < min_chars:
            info.visual_review.append(n)

    if deck:
        # Every page, and no threshold. Counting characters cannot find a diagram, because a
        # diagram's labels are text: on a real deck this flagged the title slide, the thanks
        # slide and the contacts page, and missed the one page carrying the entire target
        # architecture -- which had more extracted text than most, being fifteen boxes with
        # names in them. There is no character count that separates fifteen labels from a
        # paragraph, and the vector drawing they sit on leaves no trace `pdfimages` can see.
        #
        # `ingest-bulk.md` has said for months that an exported presentation should be
        # treated as visual throughout. The code was doing something cleverer and worse.
        info.visual_review = list(range(1, min(info.units, 40) + 1))
        info.note = ("a presentation exported to PDF, by page geometry. Every page is listed "
                     "for review, deliberately and not by a threshold: the extracted text "
                     "has lost the layout, and in a deck the layout carries the claim. A "
                     "diagram's labels are text, so no character count can find one -- the "
                     "page holding the architecture reads as one of the wordiest.")
        if info.units > 40:
            info.note += (f" Capped at 40 of {info.units} pages: read the rest by hand, "
                          "starting where the architecture is.")
    elif info.units and len(info.visual_review) > info.units * 0.4:
        info.note = ("many text-poor pages: likely a presentation exported to PDF. The "
                     "extracted text loses the layout, and on a sales deck the layout is "
                     "where the promise lives.")
    elif info.visual_review:
        info.note = f"{_n(len(info.visual_review), 'text-poor page', 'text-poor pages')}."
    return blocks, info


# ── everything else anydoc reads ────────────────────────────────────────────

def extract_flat(path: Path, out: Path, min_chars: int) -> tuple[list[Block], DocInfo]:
    """Word, OpenDocument, RTF, EPUB, the spreadsheets and CSV.

    None of these has a page: a .docx has pages only once something decides where to break
    them, and a worksheet has none at all. The heading is the locator, which is why the
    spreadsheets belong here rather than in a shape of their own — anydoc writes one
    heading per sheet, so `§ Pricing 2026` is the sheet, and a requirements matrix keeps
    saying which tab it came from.

    `min_chars` is deliberately unused. It marks a page or slide as text-poor, meaning the
    content is probably in a diagram somebody has to open. A section has no page to open.
    """
    fmt = ANYDOC_FORMAT[path.suffix.lower()]
    info = DocInfo(path.name, fmt)
    if (miss := anydoc_ready()):
        info.note = miss
        return [], info

    md, err = anydoc_markdown(path.read_bytes(), fmt)
    blocks = split_on_headings(path.name, md)
    if not blocks:
        info.note = err or "no text extracted: empty document, or entirely images"
        return [], info
    info.units = len(blocks)
    info.chars = sum(len(b.text) for b in blocks)
    return blocks, info


def extract_plain(path: Path, out: Path, min_chars: int) -> tuple[list[Block], DocInfo]:
    # `min_chars` is unused here too, and the signature keeps it only so every handler is
    # called the same way. A plain file has no pages and nothing to look at: a two line
    # note is a short claim, not a suspect one, and dropping it would lose the claim while
    # the inventory reported the document as read.
    txt = path.read_text(encoding="utf-8", errors="replace")
    return ([Block(path.name, "document", txt.strip())] if txt.strip() else [],
            DocInfo(path.name, path.suffix.lstrip("."), units=1, chars=len(txt)))


def handler_for(suffix: str):
    if suffix in {".md", ".txt"}:
        return extract_plain
    if suffix == ".pdf":
        return extract_pdf
    # `.odp` is a presentation and gets no slice: OpenDocument keeps every slide in one
    # content.xml, so there is no running order to shorten. It converts whole, and the
    # heading split is what is left. Exporting it to .pptx is what buys the numbers back.
    if ANYDOC_FORMAT.get(suffix) in {"pptx", "ppt"}:
        return extract_pptx
    return extract_flat


FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
ATX = re.compile(r"^(#{1,6})(\s)")


def demote(text: str) -> str:
    """Push a block's own headings below the provenance heading that introduces it.

    Every converted document now arrives with headings in it, and in a report where the
    provenance line is itself `## deck.pptx — slide 4` they compete: a `# Offerta` inside a
    block outranks the line saying which file it came from, and the reader — usually an
    agent deciding where a claim belongs — loses the boundary between one document and the
    next. Demoting makes the nesting say what is true: this heading is inside that block.

    Fences are tracked because `# comment` in the first column of a shell snippet is not a
    heading, and promoting it to one changes what the snippet says.
    """
    out: list[str] = []
    fence = ""
    for line in text.split("\n"):
        if (m := FENCE.match(line)):
            if fence and line.strip().startswith(fence):
                fence = ""
            elif not fence:
                fence = m.group(1)
        elif not fence and (h := ATX.match(line)):
            line = "#" * min(6, len(h.group(1)) + 2) + line[len(h.group(1)):]
        out.append(line)
    return "\n".join(out)


def build_extract_md(n_files: int, blocks: list[Block], silent: list[DocInfo],
                     infos: list[DocInfo], notes: list[str] = ()) -> str:
    """The report an agent reads. A pure function so it can be checked without poppler.

    Everything the extractor could not get is stated here, above everything it did get.
    `inventory.json` has always carried the same accounting, but nothing tells you to open
    it, and a gap you have to know to go looking for reads as completeness: a scanned PDF
    waiting for OCR and a file the filesystem refused both leave a corpus that looks whole.
    """
    md = ["# Business corpus extraction", "",
          "Generated by `extract.py`. This is not a framework artifact: it is raw material "
          "waiting to be classified. Where each claim belongs is decided with the routing "
          "table.", ""]

    # A missing converter is one fact about the run, not one fact per document. Left to the
    # table below it becomes forty rows saying the same sentence, which reads as forty
    # damaged documents rather than as one thing to install.
    for n in notes:
        md += [f"> {n}", ""]

    if silent:
        md += [f"## {len(silent)} of {n_files} documents produced no text", "",
               "Nothing below came from these. Each one is a claim you do not have yet, "
               "not a claim that does not exist. Settle them before treating the "
               "extraction as the corpus.", "",
               "| Document | Why |", "|---|---|"]
        md += [f"| {i.source} | {i.note.replace('|', '/') or 'no text content'} |"
               for i in silent]
        md += [""]

    # One step further in: these produced text, so they are not silent, but the part that
    # matters is drawn rather than written. On a sales deck the architectural constraint is
    # almost always a diagram. This warning used to go to stdout and nowhere else, so it
    # survived exactly as long as the terminal did.
    need = [i for i in infos if i.visual_review]
    if need:
        md += [f"## {_n(len(need), 'document has', 'documents have')} pages you have to look at", "",
               "These gave text, and the text is not the whole claim: a page this thin "
               "usually carries a diagram. Read the pages listed before classifying "
               "anything that came from these documents.", "",
               "| Document | Pages or slides |", "|---|---|"]
        md += [f"| {i.source} | {', '.join(str(p) for p in i.visual_review[:12])}"
               f"{' ...' if len(i.visual_review) > 12 else ''} |" for i in need]
        md += [""]

    # A document converted whole when it should have been split still gives text, so it
    # appears nowhere above. What it lost is the locator, and that only surfaces months
    # later when a claim has to be checked and there is no slide number to go back to.
    flat = [i for i in infos if i.note and "located to the file" in i.note]
    if flat:
        md += [f"## {_n(len(flat), 'document has', 'documents have')} no internal provenance", "",
               "These converted, but not in pieces: their blocks point at the file and not "
               "at a slide or a page. Checking a claim from one of them means reading the "
               "whole document.", "",
               "| Document | Why |", "|---|---|"]
        md += [f"| {i.source} | {i.note.replace('|', '/')} |" for i in flat]
        md += [""]

    for b in blocks:
        md += [f"## {b.source} — {b.locator}", "", demote(b.text), ""]
    return "\n".join(md)


def render_pages(path: Path, pages: list[int], out: Path) -> list[str]:
    """Rasterise the flagged pages, so the agent can actually look at them.

    A deck goes through PDF first. This is the case the whole visual review exists for --
    on a sales deck the architectural constraint is drawn and not written -- and until now
    it was the one case that was not served: only PDFs were rasterised, so for a `.pptx` the
    tool named the slides and asked somebody to open them by hand. LibreOffice exports the
    deck once and slide N lands on page N, which is what makes the numbers already collected
    from the package usable against the export.

    Without LibreOffice this returns nothing and the caller says so. That is a real gap and
    not a silent one: the pages stay listed, and reading them stays somebody's job.
    """
    if not pages:
        return []
    if path.suffix.lower() != ".pdf":
        if not shutil.which("soffice"):
            return []
        conv = out / "_conv"
        rc, _ = run(["soffice", "--headless", "--convert-to", "pdf",
                     "--outdir", str(conv), str(path)])
        cand = conv / (path.stem + ".pdf")
        if rc != 0 or not cand.exists():
            return []
        path = cand
    d = out / "render"
    d.mkdir(parents=True, exist_ok=True)
    made = []
    for n in pages[:40]:                       # a cap: looking at 200 pages is not a plan
        prefix = d / f"{path.stem}-p{n:03d}"
        rc, _ = run(["pdftoppm", "-jpeg", "-r", "150", "-f", str(n), "-l", str(n),
                     str(path), str(prefix)])
        if rc == 0:
            made += [str(p) for p in sorted(d.glob(f"{path.stem}-p{n:03d}*.jpg"))]
    return made


def main() -> int:
    # Same trap as the validator: the Windows console is not UTF-8, and a character
    # outside the codepage ends the extraction with a traceback after the files have
    # already been written. The result exists but you never get to read it.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")

    ap = argparse.ArgumentParser(description="Extract a business corpus, preserving provenance")
    ap.add_argument("inputs", nargs="*", type=Path)
    ap.add_argument("--doctor", action="store_true",
                    help="do not extract: say which converters are installed, at which "
                         "version, and what each absence costs")
    ap.add_argument("--find", action="store_true",
                    help="do not extract: say which directory under the given path holds "
                         "the documents the business handed over, or say that somebody has "
                         "to be asked")
    ap.add_argument("-o", "--out", type=Path, default=Path("_meta/extract"),
                    help="output DIRECTORY, created if absent")
    ap.add_argument("--jsonl", action="store_true")
    ap.add_argument("--json", action="store_true",
                    help="with --find: machine-readable, so the skill reads a verdict "
                         "instead of parsing a sentence written for a person")
    ap.add_argument("--min-chars", type=int, default=40,
                    help="a page or slide under this many characters is text-poor and gets "
                         "flagged for you to look at. Pages and slides only: a short .md or "
                         ".txt is a short claim, not a suspect one, and is kept whole")
    ap.add_argument("--no-render", action="store_true")
    args = ap.parse_args()

    if args.doctor:
        return report_doctor(args.json)
    if not args.inputs:
        print("Nothing to extract. Pass a file or a folder, or --doctor, or --find <project>.",
              file=sys.stderr)
        return 2
    if args.find:
        return report_corpus(args.inputs[0], args.json)

    files: list[Path] = []
    for i in args.inputs:
        if i.is_dir():
            # The README of a corpus/ folder explains what to put in it: the framework
            # wrote it, not the business. Ingesting it would put our own instructions
            # into ING.md wearing the shape of a customer claim.
            files += [p for p in sorted(i.rglob("*"))
                      if p.suffix.lower() in SUPPORTED and p.name.lower() != "readme.md"]
        elif i.suffix.lower() in SUPPORTED:
            files.append(i)
        else:
            print(f"! skipped (unhandled format): {i}", file=sys.stderr)
    if not files:
        print("No handleable document found.", file=sys.stderr)
        return 1

    # `-o` names a directory. Pointed at a file it used to end in a FileExistsError
    # traceback, which reads as a crash in the extractor rather than as a typo in the
    # command, and the difference matters when an agent has to decide whether to retry.
    if args.out.exists() and not args.out.is_dir():
        print(f"-o wants a directory and {args.out} is a file.", file=sys.stderr)
        return 1
    args.out.mkdir(parents=True, exist_ok=True)

    # Said once, before anything is read. A converter that is not installed is not a
    # property of any one document, and finding out forty rows into a table is finding out
    # too late to have saved the run.
    notes: list[str] = []
    if (miss := anydoc_ready()):
        # A PDF only reaches anydoc when poppler is absent, so it counts as blocked only
        # then. Counting it always would overstate the damage, and not counting it when
        # poppler is missing too would understate it, which is the worse of the two.
        pdf_needs_it = shutil.which("pdftotext") is None
        blocked = [f for f in files if f.suffix.lower() in ANYDOC_FORMAT
                   and (f.suffix.lower() != ".pdf" or pdf_needs_it)]
        if blocked:
            line = (f"**{len(blocked)} of {len(files)} documents were not converted: "
                    f"{miss}.** They are listed below as though they were empty. They are "
                    "not: nothing read them. Install it and run this again before "
                    "classifying anything.")
            notes.append(line)
            print(f"\n! {line}\n", file=sys.stderr)

    all_blocks: list[Block] = []
    infos: list[DocInfo] = []
    silent: list[DocInfo] = []

    for f in files:
        h = handler_for(f.suffix.lower())
        try:
            blocks, info = h(f, args.out, args.min_chars)
        except Exception as e:                        # one broken document must not stop the batch
            blocks, info = [], DocInfo(f.name, f.suffix.lstrip("."), note=f"error: {e}")
        if not args.no_render and info.visual_review:
            rendered = render_pages(f, info.visual_review, args.out)
            info.rendered = len(rendered)
            if rendered:
                info.note += f" Images in {args.out / 'render'}/ ({len(rendered)})."
        all_blocks += blocks
        infos.append(info)
        if not blocks:
            silent.append(info)
        print(f"- {f.name}: {len(blocks)} blocks, {info.units} units"
              + (f" - {info.note}" if info.note else ""))

    (args.out / "extract.md").write_text(
        build_extract_md(len(files), all_blocks, silent, infos, notes), encoding="utf-8")

    if args.jsonl:
        with (args.out / "extract.jsonl").open("w", encoding="utf-8") as fh:
            for b in all_blocks:
                fh.write(json.dumps(asdict(b), ensure_ascii=False) + "\n")

    # The toolchain is stamped into the inventory. The same corpus read on a machine with a
    # different poppler produces different text, and without this the difference reads as the
    # documents having changed rather than the reader.
    (args.out / "inventory.json").write_text(
        json.dumps({"toolchain": toolchain(),
                    "documents": [asdict(i) for i in infos],
                    "blocks": len(all_blocks)}, indent=2, ensure_ascii=False),
        encoding="utf-8")

    print(f"\n{len(all_blocks)} blocks from {len(files)} documents -> {args.out}/extract.md")
    if silent:
        print(f"{len(silent)} of them gave no text, listed at the top of extract.md")
    need = [i for i in infos if i.visual_review]
    if need:
        print(f"\n{_n(len(need), 'document needs', 'documents need')} visual inspection:")
        for i in need:
            print(f"  - {i.source}: pages/slides {i.visual_review[:12]}"
                  f"{' ...' if len(i.visual_review) > 12 else ''}")
        print("\nOn a sales deck the architectural constraint is usually drawn rather "
              "than written: look at these pages before classifying anything.")

        # Pointing at a folder that was never produced teaches people to ignore the
        # warning, and this is the one part of the extraction you cannot delegate.
        if any(i.rendered for i in need):
            print(f"  Images ready in {args.out / 'render'}/")
        manual = [i for i in need if not i.rendered]
        if manual:
            print("  Not rasterised here. Open these yourself, at the pages listed:")
            for i in manual:
                print(f"    - {i.source}")
            # Named only when it would actually change the outcome. This line used to be
            # printed unconditionally and pointed at an install that did nothing, which is
            # worse than no advice: the next warning from the same tool gets skipped too.
            if not shutil.which("soffice") and any(i.kind != "pdf" for i in manual):
                print("  (a deck is rasterised through LibreOffice, which is not installed: "
                      "https://www.libreoffice.org/download)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
