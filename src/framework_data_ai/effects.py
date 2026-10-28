"""What a thread says a living document should say, waiting for the join that rewrites it.

In the additive mode no session rewrites a living document while a thread is open: it writes
new files, new entries, parking lines and states, and for everything else a pending effect in
`_filoni/<slug>/effetti.md` on the thread's branch. The join reads the effects and rewrites the
documents; the to-do lists them per document, so that whoever reads a living document between
two joins sees what is waiting on it. Both read this format, so it is fixed:

    ## products/beta/ARC.md#current
    - Da: DEC-110, CHG-031
    - Diventa vero: il catalogo si legge dal servizio X, non più dal file Y.
    - Perché: DEC-110 §2; atlas-svc@abc1234 src/catalog/

One heading per target: the path of the document from the root of the documentation, and
after `#` the anchor -- the key of an entry in a register that is a map, or the id of a
`<!-- section: ... -->` marker that labels a heading -- or no anchor, where the effect is on the
whole document.
Three lines under it, each once: where it comes from, what becomes true, and why. A line
indented under one of them continues it. The labels are Italian, as the fixed names of the
exchange are.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

THREADS = "_filoni"
EFFECTS = "effetti.md"
REVIEW = "revisione.md"
DELIVERIES = "consegne"

LABELS = {"Da": "sources", "Diventa vero": "becomes", "Perché": "why"}
HEADING = re.compile(r"^##\s+(?P<target>\S.*?)\s*$")
FIELD = re.compile(r"^-\s+(?P<label>[^:]+):\s*(?P<value>.*)$")

# The registers that are maps, and the maps whose keys an effect can be anchored to. The other
# maps of a front matter -- `code` of a platform or a product, `verified_code` of an
# architecture -- name things that are not written one per effect.
ANCHOR_MAPS = {"open-register": ("entries",), "commitments": ("commitments",),
               "glossary": ("terms",), "risk-register": ("risks",),
               "operational-stack": ("stack",), "roadmap": ("increments", "delivery_stages")}


@dataclass
class Effect:
    path: str
    anchor: str | None
    line: int
    sources: list[str] = field(default_factory=list)
    becomes: str = ""
    why: str = ""

    @property
    def target(self) -> str:
        return f"{self.path}#{self.anchor}" if self.anchor else self.path


def read(text: str) -> tuple[list[Effect], list[tuple[int, str]]]:
    """The effects in the text, and what in it cannot be read, by line."""
    effects: list[Effect] = []
    problems: list[tuple[int, str]] = []
    seen: set[str] = set()
    last: str | None = None
    for n, line in enumerate(text.splitlines(), 1):
        heading = HEADING.match(line)
        if heading:
            # The path has no spaces; the anchor may, as a term of a glossary does.
            path, _, anchor = heading.group("target").partition("#")
            if not path.strip() or re.search(r"\s", path.strip()):
                problems.append((n, f"`{line.strip()}` names no document: `## <path>#<anchor>`."))
                effects.append(Effect("", None, n))
            else:
                effects.append(Effect(path.strip().strip("/"), anchor.strip() or None, n))
            seen, last = set(), None
            continue
        if not line.strip() or (line.startswith("# ") and not effects):
            continue                       # blank, or the title of the file
        if not effects:
            problems.append((n, "a line before the first effect: the file is a title and "
                                "effects, each under `## <path>#<anchor>`."))
            continue
        current = effects[-1]
        name = current.target or f"the heading at line {current.line}"
        fld = FIELD.match(line)
        if fld:
            label = fld.group("label").strip()
            if label not in LABELS:
                problems.append((n, f"`{label}` is not one of the three lines of an effect: "
                                    f"{', '.join(LABELS)}."))
                last = None
                continue
            if label in seen:
                problems.append((n, f"`{label}` twice under {name}."))
            seen.add(label)
            last = LABELS[label]
            value = fld.group("value").strip()
            if last == "sources":
                current.sources = [s.strip() for s in re.split(r"[,;]", value) if s.strip()]
            else:
                setattr(current, last, value)
        elif line.startswith((" ", "\t")) and last and last != "sources":
            setattr(current, last, f"{getattr(current, last)} {line.strip()}".strip())
        else:
            problems.append((n, f"under {name}, a line that is none of the three: "
                                "`- Da:`, `- Diventa vero:`, `- Perché:`."))
    for e in effects:
        missing = [label for label, attr in LABELS.items() if not getattr(e, attr)]
        if missing and e.path:
            problems.append((e.line, f"{e.target} has no {', '.join(f'`{m}`' for m in missing)}."))
    return [e for e in effects if e.path], problems
