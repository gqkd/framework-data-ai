"""Shared artifact reading; no policy decisions or graph construction.

The legacy validator re-exports this API. Discovery intentionally preserves the old
body-ID declaration semantics and scan exclusions; changing those is a separate policy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
import re
from typing import Protocol

import yaml

SECTION_MARK = re.compile(r"<!--\s*section:\s*([a-z0-9-]+)\s*-->")


class FindingSink(Protocol):
    def add(self, code: str, path: str, message: str) -> None: ...


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
        """The declared `artifact_type`, or None when it is not a plain name.

        Normalised here rather than at each use. `artifact_type: [a, b]` is one stray
        bracket away in a hand written front matter, and almost every use of it downstream
        is a dict or set lookup, which raises on an unhashable value: the validator died on
        the malformed document instead of reporting it, and said nothing about the two
        hundred it had not reached yet. The raw value stays in `meta` for whoever has to
        print it back.
        """
        t = self.meta.get("artifact_type")
        return t if isinstance(t, str) else None



def as_map(v) -> dict:
    """A front matter map, or an empty one when what is there is not a map.

    `terms: [Freshness, Tenant]` is one bracket away from `terms:` with two rows under it,
    and it killed the validator: `.items()` on a list raises, the process died on the
    malformed document, and nothing was said about the two hundred artifacts it had not
    reached. The schema already reports the shape -- that is what `FM002` is -- so the job
    here is only to let the run finish and report it.

    `entries:` has been guarded since the same thing happened to it. Three maps added in one
    week were not, because each was written by copying the line above it, which is how a
    lesson stays learned in one place.
    """
    return v if isinstance(v, dict) else {}


def as_list(v) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def jsonify(o):
    """YAML gives back date and datetime objects; JSON Schema validates JSON.

    Without this every artifact fails on `created`, which is a correct field, and the
    validator spends its credibility on its own bug.
    """
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    if isinstance(o, dict):
        return {k: jsonify(v) for k, v in o.items()}
    if isinstance(o, list):
        return [jsonify(v) for v in o]
    return o


def is_bare_yaml(text: str) -> bool:
    """A `.yaml` artifact: the whole file is metadata.

    Leading comments and blank lines do not count. A manifest that opens by explaining
    what it is stays a manifest, and without this it would be reported as having no front
    matter at all.
    """
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        return line.startswith("schema:")
    return False


def parse_front_matter(text: str) -> tuple[dict | None, str, str | None]:
    """Returns (meta, body, error)."""
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end == -1:
            return None, text, "front matter opened and never closed"
        raw, body = text[4:end], text[end + 4:]
    elif is_bare_yaml(text):
        raw, body = text, ""
    else:
        return None, text, "no front matter"
    try:
        meta = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        return None, body, f"invalid YAML: {str(e).splitlines()[0]}"
    if not isinstance(meta, dict):
        return None, body, "front matter is not a mapping"
    return meta, body, None



def skipped_dir(parts: tuple[str, ...], skip_dirs: set[str]) -> bool:
    """Whether a document sitting in these directories is excluded from the scan.

    An entry with no slash matches a directory of that name at any depth, which is what
    `corpus` and `node_modules` want: they mean the same thing wherever they turn up.

    An entry with a slash is a path from the root, and exists because a bare name is
    sometimes too blunt to be safe. `_meta/extract` is the extractor's output and holds no
    source document; `extract` on its own would silently exclude the extraction step of
    every ETL project that keeps one in a directory of that name. The registry already
    states the principle it took a mistake to learn -- an exclusion that protects the
    framework's convenience is paid for by everyone using it -- and until now it could only
    be honoured by choosing awkward names.
    """
    if any(part in skip_dirs for part in parts):
        return True
    rel = "/".join(parts)
    return any("/" in s and (rel == s or rel.startswith(s + "/")) for s in skip_dirs)


def load_scan(registry: dict, project: dict) -> dict:
    """Framework exclusions are a floor: project configuration can only extend them."""
    base = registry["scan"]
    scan = project.get("scan") or {}
    return {
        "skip_hidden": bool(scan.get("skip_hidden", base.get("skip_hidden"))),
        "skip_dirs": set(base["skip_dirs"]) | set(as_list(scan.get("skip_dirs"))),
        "skip_files": set(base["skip_files"]) | set(as_list(scan.get("skip_files"))),
    }


def document_selected(relative: Path, scan: dict) -> bool:
    parts = relative.parts
    return (relative.suffix in {".md", ".yaml", ".yml"}
            and not (scan["skip_hidden"] and any(p.startswith(".") for p in parts))
            and not skipped_dir(parts[:-1], scan["skip_dirs"])
            and relative.name not in scan["skip_files"])


def discover(root: Path, scan: dict, registry: dict, report: FindingSink) -> list[Artifact]:
    id_re = re.compile(r"\b((?:%s)-\d{3,})\b" % "|".join(registry["id_prefixes"]))

    artifacts = []
    for p in sorted(root.rglob("*")):
        if p.is_dir() or not document_selected(p.relative_to(root), scan):
            continue
        rel = str(p.relative_to(root))
        meta, body, err = parse_front_matter(
            p.read_text(encoding="utf-8", errors="replace"))
        if err:
            report.add("FM001", rel, err)
            continue
        art = Artifact(p, rel, meta, body)
        # Every identifier in the body, not only the ones in a declaring position. That is
        # looser than it looks like it should be, and the looseness is deliberate.
        #
        # A register does distinguish declaring an entry from citing one, but it does so in
        # prose, not in layout. `OPEN.md §4` closes an entry with
        # `- **2026-05-12 · OD-000** -> DEC-001`, and states a dependency with
        # `- **Depends on:** OD-011.` Both are list items carrying an identifier after some
        # text, and the only thing separating them is that one prefix is a date and the
        # other is a field label. Keying a check on that is a heuristic that will misfire,
        # and a check that misfires on correct documents gets switched off within a week,
        # which costs more than the hole it closed.
        #
        # The hole is therefore known and bounded: inside a register, an identifier of a
        # prefix that register declares is treated as existing even when it is only being
        # cited. `inline_id_declarations` keeps that from spreading to every other prefix,
        # which is where it did real damage. Closing the rest wants the registers to mark
        # their entries, not the validator to guess at them.
        art.ids = set(id_re.findall(body))
        artifacts.append(art)
    return artifacts



@dataclass(frozen=True)
class SectionSpan:
    """One ATX heading, with inclusive one-based source lines (including its marker)."""
    title: str
    level: int
    marker: str | None
    start_line: int
    heading_line: int
    end_line: int


def locate_sections(body: str, *, first_line: int = 1) -> tuple[SectionSpan, ...]:
    """Locate sections without paraphrasing them or conflating repeated headings.

    Input is the parsed body, not front matter. Nested headings remain inside their
    parent span. Fenced examples are not headings. Markers label the next heading
    only when separated by whitespace. Setext headings are not supported in this API;
    this does not change the validator's existing marker-presence check.
    """
    if first_line < 1:
        raise ValueError("first_line must be one-based")
    lines = body.splitlines()
    headings = []
    fence = None
    pending = None
    for offset, line in enumerate(lines):
        number = first_line + offset
        if fence:
            if re.fullmatch(r" {0,3}" + re.escape(fence[0]) +
                            "{" + str(fence[1]) + r",}\s*", line):
                fence = None
            continue
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if opening and not (opening[1][0] == "`" and "`" in opening[2]):
            fence = (opening[1][0], len(opening[1]))
            pending = None
            continue
        marker = SECTION_MARK.fullmatch(line.strip())
        if marker:
            pending = (marker[1], number)
            continue
        heading = re.match(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?)|[ \t]*)$", line)
        if heading:
            title = re.sub(r"[ \t]+#+[ \t]*$", "", heading[2] or "").strip()
            headings.append((title, len(heading[1]), pending[0] if pending else None,
                             pending[1] if pending else number, number))
            pending = None
        elif line.strip():
            pending = None
    result = []
    last = first_line + len(lines) - 1
    for index, (title, level, marker, start, heading) in enumerate(headings):
        end = next((other[3] - 1 for other in headings[index + 1:] if other[1] <= level), last)
        result.append(SectionSpan(title, level, marker, start, heading, end))
    return tuple(result)


def body_first_line(text: str, body: str) -> int:
    """Source offset of the exact body returned by parse_front_matter."""
    if not text.endswith(body):
        raise ValueError("body is not the parsed suffix of this source")
    return text[:len(text) - len(body)].count("\n") + 1
