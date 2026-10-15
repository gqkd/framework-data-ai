#!/usr/bin/env python3
"""Adopting a new version of the framework, as a difference rather than as an announcement.

`FW001` tells a repository that the rules moved. It does not tell it *which of the findings
in front of it moved with them*, and that is the whole question: one of them is a migration
and the other is a repair, they want opposite responses, and guessing wrong at it a few
times is how a validator stops being read.

So this runs both validators on the same project -- the one from the version the project
declares, and the one from the version it is moving to -- and splits the findings three
ways:

    already there      reported by both. Documents to repair. Not migration work.
    new                reported only by the new validator. This is the migration.
    gone               reported only by the old one. Cleared by the move.
    accepted           reported now, and annotated in the project with why it stays and
                       what removes it. Examined, so not outstanding, so not a reason to
                       refuse `--adopt`.

The old validator is not kept anywhere: it is reconstructed from this repository's git
history, at the commit where `schemas/artifact-types.yaml` last declared the version the
project pinned. That is why no tag is needed and why nothing has to have been released:
the history is the archive.

The migration notes are not restated here either. They live beside the number they explain,
in the registry, and this reads them out of it -- so there is one copy, and it is the one
whoever bumps the version has to write.
"""

import argparse
from contextlib import contextmanager
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Needs pyyaml:  pip install pyyaml")

FRAMEWORK = Path(__file__).resolve().parents[3]
REGISTRY_REL = "schemas/artifact-types.yaml"
VALIDATE_REL = "skills/audit/scripts/validate.py"

# The findings `--adopt` clears by writing a number, rather than by anybody editing a
# document. They are not migration work and are not repairs: they are the migration itself,
# stated as a finding.
#
# `FW003` was missing, and its absence deadlocked exactly the projects that took this
# framework most seriously. A project that pins gets `FW003` the moment the framework moves;
# `FW003` landed in NEW; `--adopt` refuses while NEW is non-empty; and the only thing that
# clears `FW003` is `--adopt` writing the pin. So pinning made adopting impossible, and the
# way out was to delete the pin -- the field's own purpose, undone by the tool that exists to
# move it.
ADOPT_CLEARS = ("FW001", "FW002", "FW003")

# `AN003` names the finding it is about in square brackets at the head of its message.
ANNOTATION_SUBJECT = re.compile(r"^\[([A-Z]{2,3}\d{3})\]")


def adopt_clears(finding: dict) -> bool:
    """True when `--adopt` removes this finding by writing the number, not by an edit.

    Kept out of the loop that uses it so a test can state the rule directly: the defect
    it encodes survived because nothing could name it. See the comment in the loop.
    """
    if finding.get("code") in ADOPT_CLEARS:
        return True
    about = ANNOTATION_SUBJECT.match(finding.get("message") or "")
    return (finding.get("code") == "AN003"
            and about is not None and about.group(1) in ADOPT_CLEARS)

SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
VERSION_LINE = re.compile(r"^version:\s*['\"]?(\d[\d.]*)", re.M)
# `# 2.0.0 -> 2.1.0.` and the one that opens the history, `# 1 -> 1.1.0.`
NOTE_OPENS = re.compile(r"^#\s*(\d[\d.]*)\s*->\s*(\d+\.\d+\.\d+)\.")


def semver(v):
    m = SEMVER.match(str(v).strip())
    return tuple(int(g) for g in m.groups()) if m else None


def git(args, cwd, **kw):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, **kw)


def declared_version(root: Path):
    """What the project says it was written against, where it says it, and why not.

    The third return value is what this used to lack. A `framework.yaml` that does not parse
    came back out of here as a `yaml` traceback -- the tool died on the one file it exists to
    read, having said nothing about the project -- and a file with no `framework_version` in
    it came back indistinguishable from a file that is not valid YAML at all. They are
    different repairs.
    """
    cfg = root / "framework.yaml"
    if not cfg.exists():
        return None, cfg, None
    try:
        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        first = str(e).strip().splitlines()[0]
        return None, cfg, (f"{cfg} does not parse as YAML: {first}. Nothing can be read out "
                           "of it, including which version this repository was written "
                           "against, and the validator will stop on the same line.")
    if not isinstance(data, dict):
        return None, cfg, f"{cfg}: the top level has to be a mapping."
    return data.get("framework_version"), cfg, None


COMMIT = re.compile(r"^[0-9a-fA-F]{7,40}$")


def say_if_the_checkout_moved(root: Path, framework: Path) -> None:
    """The same line `validate.py` prints, for the same reason, in the other entry point.

    Written here rather than imported, and the duplication is the established shape of this
    file: `semver` and `VERSION_LINE` are here twice already, because this tool has to run
    against two validators and must not depend on either of them. Importing the current one
    to say a sentence about git would be a dependency bought for a message.

    Stderr, before anything is read. See `validate.py` for why the ordering is the point:
    the fault this reports is the one that stops the report carrying it from being produced.
    """
    try:
        cfg = yaml.safe_load((root / "framework.yaml").read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return                       # `declared_version` reports an unreadable config
    pinned = cfg.get("framework_commit") if isinstance(cfg, dict) else None
    if not isinstance(pinned, str) or not COMMIT.match(pinned.strip()):
        return
    pinned = pinned.strip()
    head = git(["rev-parse", "HEAD"], framework)
    shallow = git(["rev-parse", "--is-shallow-repository"], framework)
    if head.returncode != 0 or shallow.stdout.strip() == "true":
        return
    at = head.stdout.strip()
    if at.lower().startswith(pinned.lower()):
        return
    print(f"framework-data-ai: this checkout is at {at[:12]}, and "
          f"{root / 'framework.yaml'} pins {pinned[:12]}. What follows was not produced by "
          "the rules this project declares.", file=sys.stderr)


def registry_version(text: str):
    m = VERSION_LINE.search(text)
    return m.group(1) if m else None


def migration_notes(text: str) -> list[tuple[str, str, str]]:
    """Every `X -> Y` note in the registry, as (from, to, prose).

    They are comments, which is the right place for them -- beside the number they explain,
    in the file that defines it -- and the cost is that they have to be read out rather than
    parsed. A note runs from its opening line until the comment block ends or the next note
    opens.
    """
    notes, cur = [], None
    for line in text.splitlines():
        m = NOTE_OPENS.match(line)
        if m:
            if cur:
                notes.append(cur)
            cur = [m.group(1), m.group(2), line.lstrip("# ").rstrip()]
            continue
        if cur is None:
            continue
        if line.startswith("#"):
            cur[2] += "\n" + line.lstrip("#").strip()
        else:
            notes.append(cur)
            cur = None
    if cur:
        notes.append(cur)
    return [tuple(n) for n in notes]


def commit_declaring(version: str, framework: Path):
    """The newest framework commit whose registry declared `version`.

    Newest and not oldest: a version is current from the commit that introduced it until
    the one that replaced it, and the validator a project has been running all along is the
    last one that shipped under that number, not the first.
    """
    # Asked before the log, because git's own answer to "not a repository" is
    # `Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set)`, which
    # names neither the directory nor what is wrong with it. A framework unpacked from an
    # archive rather than cloned is a real way to arrive here, and the whole comparison
    # rests on the history being present.
    if git(["rev-parse", "--git-dir"], framework).returncode != 0:
        return None, (f"{framework} is not a git checkout, so the validator of {version} "
                      "cannot be reconstructed: this tool reads it out of the framework's "
                      "own history. Point --framework at a clone. The migration notes above "
                      "are still the ones for this move.")

    log = git(["log", "--follow", "--format=%H", "--", REGISTRY_REL], framework)
    if log.returncode != 0:
        tail = log.stderr.strip().splitlines()
        return None, f"git could not read the history of {REGISTRY_REL}: " + (
            tail[-1] if tail else "no reason given")
    for sha in log.stdout.split():
        show = git(["show", f"{sha}:{REGISTRY_REL}"], framework)
        if show.returncode == 0 and registry_version(show.stdout) == version:
            return sha, None
    return None, (f"no commit of {REGISTRY_REL} ever declared {version!r}. Either the "
                  "project pins a version this checkout does not contain, or its history "
                  "is shallow: `git fetch --unshallow` and try again")


def export(sha: str, framework: Path, into: Path) -> Path:
    """That commit's whole tree, so the old validator finds its own schemas and catalog."""
    archive = into / "old.tar"
    with archive.open("wb") as fh:
        r = subprocess.run(["git", "archive", sha], cwd=framework, stdout=fh,
                           stderr=subprocess.PIPE, text=False)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode(errors="replace").strip())
    tree = into / "old"
    tree.mkdir()
    with tarfile.open(archive) as tar:
        # `filter="data"` is the default from 3.14 and a DeprecationWarning before it. Named
        # rather than left implicit so this prints nothing on 3.12, which is what CI runs:
        # a migration tool whose first output is a warning about itself gets distrusted
        # before it has said anything.
        tar.extractall(tree, filter="data")
    archive.unlink()
    return tree


def key(f: dict, seen: Counter) -> tuple:
    """What identifies one finding across two versions of the validator.

    (code, path) and not the message: a reworded message is a PATCH by this framework's own
    definition, and a diff that treated it as a new finding would report the whole
    repository as migration work the first time somebody fixed a sentence.

    The ordinal is what stops that from swallowing the interesting case. A check can report
    the same code on the same file many times -- one per entry of a register, one per
    unresolved citation -- and keyed on the pair alone, three findings and five findings are
    the same key: a version that made a check twice as noisy on a file it already reported
    would come out of this tool as "nothing new". Counting them keeps the two extra ones
    visible without making the diff sensitive to wording.
    """
    k = (f["code"], f["path"])
    seen[k] += 1
    return (*k, seen[k])


def findings(validator: Path, root: Path) -> dict:
    """One validator's report on the project, keyed by `key`."""
    r = subprocess.run([sys.executable, "-I", "-B", str(validator), "--root", str(root), "--json"],
                       capture_output=True, text=True)
    if r.returncode not in (0, 1) or not r.stdout.strip():
        tail = (r.stderr or r.stdout).strip().splitlines()
        raise RuntimeError(tail[-1] if tail else "no output")
    out = json.loads(r.stdout)
    seen: Counter = Counter()
    return {key(f, seen): f for f in out["findings"]}


@contextmanager
def previous_framework(args, declared, root, framework):
    """Own complete tree in its own process; never import the new core into the old one.

    A package path is explicitly operator-trusted executable tooling, not project input.
    A package's version is checked, but is not proof that its bytes came from a Git pin.
    """
    if args.from_framework:
        tree = args.from_framework.resolve()
        for relative in (REGISTRY_REL, VALIDATE_REL, "skills/audit/checks.yaml"):
            if not (tree / relative).is_file():
                raise RuntimeError(f"previous framework lacks {relative}; supply a complete export")
        if registry_version((tree / REGISTRY_REL).read_text(encoding="utf-8")) != declared:
            raise RuntimeError("previous framework export does not declare the requested version")
        yield tree, {"kind": "explicit-export", "version": declared,
                     "commit_verified": False}
        return
    config = yaml.safe_load((root / "framework.yaml").read_text(encoding="utf-8")) if (root / "framework.yaml").exists() else {}
    pin = args.from_commit or (config.get("framework_commit") if isinstance(config, dict)
                              and not args.from_version else None)
    if pin is not None:
        if not isinstance(pin, str) or not COMMIT.fullmatch(pin):
            raise RuntimeError("previous framework commit is not a valid Git commit ID")
        resolved = git(["rev-parse", "--verify", f"{pin}^{{commit}}"], framework)
        if resolved.returncode:
            raise RuntimeError("previous framework commit unavailable; supply its trusted complete export with --from-framework")
        sha = resolved.stdout.strip()
        old_registry = git(["show", f"{sha}:{REGISTRY_REL}"], framework)
        if old_registry.returncode or registry_version(old_registry.stdout) != declared:
            raise RuntimeError("previous framework commit and declared version disagree")
        origin = "explicit-commit" if args.from_commit else "project-pin"
    else:
        sha, why = commit_declaring(declared, framework)
        if sha is None:
            raise RuntimeError(why)
        origin = "version-history"
    with tempfile.TemporaryDirectory(prefix="framework-migrate-") as tmp:
        yield export(sha, framework, Path(tmp)), {"kind": origin, "version": declared,
                                                "commit": sha, "commit_verified": True}


def catalog(tree: Path) -> dict | None:
    """The `checks:` of a framework tree, or None where it cannot be read: then nothing is
    listed, because every check would read as new."""
    try:
        data = yaml.safe_load((tree / "skills/audit/checks.yaml").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError):
        return None
    checks = data.get("checks") if isinstance(data, dict) else None
    return checks if isinstance(checks, dict) else None


def new_checks(old_catalog: dict, new_catalog: dict) -> list[dict]:
    """The checks the new catalog runs and the old one did not have, with level and title.

    READ OUT OF THE TWO CATALOGS, NOT OUT OF THE NOTE. The note says why a check arrived, and
    is written by hand; this says which ones did, and cannot forget one. A finding of a new
    check lands under NEW like any other, and only where the project gives it something to
    read: this is the list of what may, so that a NEW section with nothing from a check is
    read as the check having looked, rather than as the check not existing.
    """
    old = set(old_catalog or {})
    return [{"code": code, "level": str((spec or {}).get("level", "warn")),
             "title": str((spec or {}).get("title", ""))}
            for code, spec in sorted((new_catalog or {}).items())
            if code not in old and (spec or {}).get("level") != "retired"]


AGENTS_REL = "AGENTS.md"
TEMPLATE_REL = "templates/AGENTS.md"
SESSIONS_REL = ".framework/sessions.yaml"
SESSIONS_KEYS = {"exchange"}
# The line directly above a heading of `templates/AGENTS.md` that makes the section the
# framework's: above, as `<!-- section: ... -->` marks a mandatory section of a document, and
# a different word, because it means something else. It travels into the project with the
# section, so that the next migration finds the section under a heading somebody renamed.
SECTION_MARK = re.compile(r"^<!--\s*framework-section:\s*([a-z][a-z0-9-]*)"
                          r"((?:\s+requires=[a-z-]+)*)\s*-->\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
# What the template leaves to whoever fills it, and what this tool writes in. The exchange is
# declared in `.framework/sessions.yaml`, so that is where its value always comes from: a
# copy that says another place is out of date, not the project's choice. The framework's
# path is the project's to write, and a value it wrote is kept.
PLACEHOLDERS = ("FRAMEWORK_PATH", "EXCHANGE_PATH")
DECLARED = {"EXCHANGE_PATH"}


def sections(text: str) -> list[dict]:
    """The `## ` sections of a Markdown file: heading, marker, and the lines they span.

    A section starts at its marker when the line above its heading is one. The front matter
    and fenced code are not read for headings: `## ` is a YAML comment in the first, and
    anything at all in the second.
    """
    lines = text.split("\n")
    i = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                i = j + 1
                break
    out, fence = [], None
    for n in range(i, len(lines)):
        line = lines[n]
        f = FENCE.match(line)
        if f and (fence is None or f.group(1) == fence):
            fence = None if fence else f.group(1)
            continue
        if fence or not line.startswith("## "):
            continue
        mark = SECTION_MARK.match(lines[n - 1].strip()) if n > i else None
        begin = n - 1 if mark else n
        if out:
            out[-1]["end"] = begin
        out.append({"heading": line[3:].strip(), "start": begin, "end": len(lines),
                    "id": mark.group(1) if mark else None,
                    "requires": re.findall(r"requires=([a-z-]+)", mark.group(2)) if mark else []})
    for s in out:
        body = lines[s["start"]:s["end"]]
        while body and not body[-1].strip():
            body.pop()
        s["text"] = "\n".join(body)
    return out


def _normal(text: str) -> str:
    """Trailing spaces and runs of blank lines do not make two copies of a section differ."""
    return re.sub(r"\n{3,}", "\n\n",
                  "\n".join(line.rstrip() for line in text.strip().split("\n")))


def _flat(text: str) -> str:
    """The words of a section, for comparing two copies: the marker line, which a copy made by
    hand does not have, and where the lines break, which an editor changes, do not count."""
    kept = [line for line in text.split("\n") if not SECTION_MARK.match(line.strip())]
    return " ".join(" ".join(kept).split())


def render(text: str, fill: dict | None, quotes: bool = False) -> str:
    """A template section as it goes into a project: what the template says to whoever fills
    it -- its blockquotes, the only thing a marked section may put in one -- dropped, and the
    placeholders written in. `fill=None` leaves them; `quotes=True` keeps the blockquotes, for
    recognising a copy that `start` made by copying the body as it was."""
    kept = [line for line in text.split("\n") if quotes or not line.lstrip().startswith(">")]
    out = _normal("\n".join(kept))
    for name, value in (fill or {}).items():
        out = out.replace(name, value)
    return out


def written_values(template_section: str, project_section: str,
                   quotes_too: bool = True) -> dict | None:
    """What the project wrote for each placeholder, when its copy is this template's section
    and nothing else, however its lines break; None when somebody changed a word. A
    placeholder still written as itself comes back as itself: the copy was never filled.
    `quotes_too` also recognises a copy that kept the template's blockquotes, which is a copy
    still to clean, never one already in its final form."""
    flat = _flat(project_section)
    for quotes in ((False, True) if quotes_too else (False,)):
        pattern, seen = [], set()
        for piece in re.split(f"({'|'.join(PLACEHOLDERS)})",
                              _flat(render(template_section, None, quotes))):
            if piece in PLACEHOLDERS:
                pattern.append(f"(?P={piece})" if piece in seen else f"(?P<{piece}>[^`]+?)")
                seen.add(piece)
            else:
                pattern.append(re.escape(piece))
        m = re.fullmatch("".join(pattern), flat)
        if m:
            return m.groupdict()
    return None


def loose_values(template_section: str, project_section: str) -> dict:
    """The placeholders a copy somebody edited still lets be read, by the code span around
    each: `FRAMEWORK_PATH/agents/critic.md` finds the path in any wording. A span that is the
    placeholder alone would match any code span, so it is not read."""
    flat, found = _flat(project_section), {}
    for span in re.findall(r"`[^`]*`", _flat(render(template_section, None))):
        for name in PLACEHOLDERS:
            if name in span and span != f"`{name}`" and name not in found:
                rx = re.escape(span).replace(re.escape(name), "([^`]+?)", 1)
                m = re.search(rx, flat)
                if m:
                    found[name] = m.group(1)
    return found


def template_history(framework: Path, limit: int = 80) -> list[str]:
    """Every text `templates/AGENTS.md` has had, newest first, out of the framework's history.

    A copy is unedited when it is the template's text of some version, not only of the one the
    project declares: the same number has shipped two templates, a run that repeats on the
    same version has no previous tree, and a project may have copied an older one. An export
    with no history gives nothing, and only the previous tree, when there is one, is known.
    """
    key = str(framework)
    if key in _HISTORY:
        return _HISTORY[key]
    shas = git(["log", "--format=%H", f"-n{limit}", "--", TEMPLATE_REL], framework)
    out = []
    if shas.returncode == 0 and shas.stdout.split():
        batch = subprocess.run(
            ["git", "cat-file", "--batch"], cwd=framework, capture_output=True,
            input="".join(f"{sha}:{TEMPLATE_REL}\n" for sha in shas.stdout.split()).encode())
        data, at = batch.stdout, 0
        while batch.returncode == 0 and at < len(data):
            eol = data.index(b"\n", at)
            head = data[at:eol].split()
            at = eol + 1
            if len(head) == 3 and head[1] == b"blob":
                size = int(head[2])
                out.append(data[at:at + size].decode("utf-8", "replace"))
                at += size + 1
    _HISTORY[key] = list(dict.fromkeys(out))
    return _HISTORY[key]


_HISTORY: dict[str, list[str]] = {}


def framework_path(root: Path, framework: Path) -> tuple[str, bool]:
    """The framework's path as `AGENTS.md` will say it, and whether it holds on this machine
    only. Relative when the two checkouts sit side by side, so that the line holds on every
    machine that keeps them that way; absolute otherwise, because `../../..` towards a plugin
    cache is a path nobody can read or check. Written where the project has none: a value it
    wrote is kept, and the report says when it leads to no framework on this machine."""
    try:
        rel = Path(os.path.relpath(framework, root)).as_posix()
    except ValueError:                  # two drives on Windows: there is no relative path
        return framework.as_posix(), True
    if rel.startswith("../") and ".." not in rel[3:]:
        return rel, False
    return framework.as_posix(), True


def exchange_declared(root: Path, framework: Path) -> tuple[str | None, str | None]:
    """The `exchange:` value, or why there is none that can be written into `AGENTS.md`.

    The validator's reading, with its words: it stops on a file that is not a mapping or
    carries a key it does not know, and refuses a value that is a place on one machine or
    inside the documentation (`exchange.declared`, read from the framework's package rather
    than restated). What the validator stops on is not a place to write down.
    """
    path = root / SESSIONS_REL
    if not path.exists():
        return None, None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeError, yaml.YAMLError) as e:
        return None, f"{SESSIONS_REL} does not parse: {str(e).strip().splitlines()[0]}"
    if not isinstance(data, dict):
        return None, f"{SESSIONS_REL}: the top level has to be a mapping"
    unknown = sorted(set(data) - SESSIONS_KEYS)
    if unknown:
        return None, f"{SESSIONS_REL}: unknown key(s) {', '.join(map(repr, unknown))}"
    if data.get("exchange") is None:      # absent, or `exchange:` with nothing after it
        return None, None
    _, problem = _exchange_rule(framework).declared(data["exchange"], root)
    return (None, f"{SESSIONS_REL}: {problem}") if problem else (str(data["exchange"]).strip(), None)


def _exchange_rule(framework: Path):
    """`exchange.py` of the framework being adopted, in a namespace of its own, the way
    `validate.py` loads its package: two checkouts in one process never share modules."""
    import hashlib
    import importlib
    import importlib.util
    name = "_framework_data_ai_" + hashlib.sha256(str(framework).encode()).hexdigest()[:16]
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            name, framework / "src/framework_data_ai/__init__.py",
            submodule_search_locations=[str(framework / "src/framework_data_ai")])
        core = importlib.util.module_from_spec(spec)
        sys.modules[name] = core
        spec.loader.exec_module(core)
    return importlib.import_module(f"{name}.exchange")


def _find(have: list[dict], sid: str | None, heading: str) -> dict | None:
    """By the marker, else by the heading: a copy made by hand has no marker."""
    return (next((p for p in have if sid and p["id"] == sid), None)
            or next((p for p in have if p["heading"].lower() == heading.lower()), None))


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z]{4,}", _flat(text).lower()))


def _resembles(template_section: str, have: list[dict]) -> dict | None:
    """An unmarked section of the project that reads like a copy of this one under another
    heading: most of the template's words are in it. Adding beside it would put the rule in
    the file twice. A rule elsewhere that only names the critic shares a handful of words,
    and is not mistaken for it; a copy translated whole shares almost none, and is not found.
    """
    words = _words(render(template_section, None)) - set(map(str.lower, PLACEHOLDERS))
    if not words:
        return None
    return next((p for p in have if not p["id"]
                 and len(words & _words(p["text"])) >= 0.6 * len(words)), None)


def _leads_to_framework(root: Path, value: str) -> bool:
    """Whether a path written in `AGENTS.md` reaches a framework on this machine: the one
    thing about it anything can check. Said in the report, never acted on: the value is
    committed for every machine, and one where it does not hold -- a CI runner, a colleague
    with the plugin elsewhere -- is not the one to rewrite it for the others."""
    where = Path(value).expanduser()
    where = where if where.is_absolute() else root / where
    return (where / "agents" / "critic.md").is_file()


def marked_ids(framework: Path) -> set[str]:
    return {s["id"] for s in sections((framework / TEMPLATE_REL).read_text(encoding="utf-8"))
            if s["id"]}


def section_plan(root: Path, framework: Path, old_template: str | None,
                 replace=()) -> dict:
    """What `--adopt` will do to the framework's sections of the project's `AGENTS.md`.

    THE FRAMEWORK'S SECTIONS ARRIVE WITH THE VERSION, NOT BY HAND. A rule the framework
    added to `templates/AGENTS.md` reached a project only if somebody copied it, with its
    path filled in, into the one file a session without a skill reads -- so it reached the
    projects whose people read the release notes. The sections marked in the template are the
    framework's: one missing from the project is added; one that is the template's text, of
    this version or any earlier one, with only the placeholders filled, is brought to the new
    text keeping the path the project wrote and taking the exchange from where it is declared;
    one somebody edited is left and named, because the edit is the project's -- which is also
    how a project declines one: keep the marker and the heading, and write why -- unless
    `replace` names it. Unmarked sections -- the commands, the table of sources -- are the
    project's, and are read only to place a section.
    """
    plan = {"path": AGENTS_REL, "exists": (root / AGENTS_REL).is_file(), "sections": []}
    if not plan["exists"]:
        return plan
    template = (framework / TEMPLATE_REL).read_text(encoding="utf-8")
    have = sections((root / AGENTS_REL).read_text(encoding="utf-8"))
    known = [sections(t) for t in dict.fromkeys(
        [*([old_template] if old_template else []), *template_history(framework)])]
    exchange, unusable = exchange_declared(root, framework)
    path, local = framework_path(root, framework)
    fill = {"FRAMEWORK_PATH": path}
    if exchange:
        fill["EXCHANGE_PATH"] = exchange
    tpl = sections(template)
    for n, s in enumerate(tpl):
        if not s["id"]:
            continue
        entry = {"id": s["id"], "heading": s["heading"]}
        unmet = [r for r in s["requires"] if r != "exchange" or not exchange]
        doubled = [p for p in have if p["id"] == s["id"]]
        mine = _find(have, s["id"], s["heading"])
        if unmet:
            entry.update(action="skipped", at=(
                (unusable or "no exchange declared in " + SESSIONS_REL)
                if unmet == ["exchange"] else f"needs {', '.join(unmet)}, which this tool does "
                                              "not know"))
            if mine:
                entry["at"] += ("; the copy in AGENTS.md is left as it is" + (
                    ", and the template says to delete it where no exchange is declared"
                    if unmet == ["exchange"] and not unusable else ""))
            plan["sections"].append(entry)
            continue
        if len(doubled) > 1:
            entry.update(action="left", at=(
                f"the marker is above {len(doubled)} sections: "
                f"{', '.join(repr(p['heading']) for p in doubled)}. Keep it above one"))
            plan["sections"].append(entry)
            continue
        if mine is None:
            alike = _resembles(s["text"], have)
            if alike and s["id"] in replace:
                kept = {k: v for k, v in loose_values(s["text"], alike["text"]).items()
                        if k not in DECLARED}
                entry.update(action="update", text=render(s["text"], {**fill, **kept}),
                             at=(f"replaces \"{alike['heading']}\", which read like a copy "
                                 "of it, as --replace-section asks: its own words are lost"),
                             anchor=alike["heading"], marker=None, where="replace",
                             forced=True)
                plan["sections"].append(entry)
                continue
            if alike:
                entry.update(action="left", at=(
                    f"\"{alike['heading']}\" reads like a copy of it under another heading, "
                    "so it is not added beside it. If it is this rule: `--adopt "
                    f"--replace-section {s['id']}` puts the template's text in its place, or "
                    f"`<!-- framework-section: {s['id']} -->` on the line above that heading "
                    "keeps its words as the project's edit"))
                plan["sections"].append(entry)
                continue
            after = next((p for t in tpl[n + 1:] if (p := _find(have, t["id"], t["heading"]))),
                         None)
            before = next((p for t in reversed(tpl[:n])
                           if (p := _find(have, t["id"], t["heading"]))), None)
            entry.update(action="add", text=render(s["text"], fill),
                         at=(f"before \"{after['heading']}\"" if after
                             else f"after \"{before['heading']}\"" if before else "at the end"),
                         anchor=(after or before or {}).get("heading"),
                         where="before" if after else "after" if before else "end")
            if local and "FRAMEWORK_PATH" in s["text"]:
                entry["at"] += f"; the framework's path is {path}, true on this machine only"
            plan["sections"].append(entry)
            continue

        def holds(values: dict) -> dict:
            """The values a new text keeps: what the project wrote in them."""
            return {k: v for k, v in values.items() if v != k and k not in DECLARED}

        def say_where(values: dict) -> None:
            given = values.get("FRAMEWORK_PATH")
            if given and given != "FRAMEWORK_PATH" and not _leads_to_framework(root, given):
                plan.setdefault("notes", []).append(
                    f"the framework's path in the section {s['heading']!r}, {given}, leads to "
                    "no framework on this machine. It is kept: it may hold where it was "
                    "written. If it holds nowhere, correct it by hand.")

        values = written_values(s["text"], mine["text"], quotes_too=False)
        if values is not None and mine["id"] and all(v != k for k, v in values.items()) and all(
                values[k] == fill.get(k) for k in values if k in DECLARED):
            say_where(values)
            continue                    # this version's text, with the project's values
        if values is None:
            for candidate in [s, *(_find(old, s["id"], s["heading"]) for old in known)]:
                values = (written_values(candidate["text"], mine["text"])
                          if candidate else None)
                if values is not None:
                    break
        forced = values is None and s["id"] in replace
        if forced:
            values = loose_values(s["text"], mine["text"])
        if values is None:
            entry.update(action="left", at=(
                f"\"{mine['heading']}\" is edited in the project: left as it is. "
                f"`--adopt --replace-section {s['id']}` puts the template's text in its place"))
            plan["sections"].append(entry)
            continue
        kept = holds(values)
        entry.update(action="update", text=render(s["text"], {**fill, **kept}),
                     at=(f"replaces \"{mine['heading']}\""
                         + (", an edited copy, as --replace-section asks: its own words are "
                            "lost" if forced else "")),
                     anchor=mine["heading"], marker=mine["id"], where="replace", forced=forced)
        say_where(values)
        if local and "FRAMEWORK_PATH" in s["text"] and "FRAMEWORK_PATH" not in kept:
            entry["at"] += f"; {path} holds on this machine only"
        plan["sections"].append(entry)
    return plan


def agents_dirty(root: Path) -> str | None:
    """Why `AGENTS.md` cannot be written now, or None. Several sessions share one working
    tree: a line this tool writes beside one somebody has not committed is a line nobody can
    tell apart from theirs. Staged and untracked count; a project outside git has no commit
    to protect, and is written."""
    r = git(["status", "--porcelain", "--", AGENTS_REL], root)
    if r.returncode == 0 and r.stdout.strip():
        return (f"not adopted, and nothing written: {AGENTS_REL} has changes that are not "
                "committed. Commit them, or set them aside, and adopt again: what `--adopt` "
                "writes there has to be a change of its own, for a person to reread and attest.")
    return None


def apply_sections(text: str, plan: dict) -> tuple[str, list[str]]:
    """The plan applied to the text of `AGENTS.md`, one section at a time, rereading between
    them; and the headings written. Nothing is written to disk here, so that the number and
    the sections go in together or not at all. The front matter is not touched: `last_review`
    is a person's."""
    done = []
    for entry in plan["sections"]:
        if entry["action"] not in ("add", "update"):
            continue
        lines = text.split("\n")
        have = sections(text)
        block = entry["text"].split("\n")
        at = _find(have, entry.get("marker") or (entry["id"] if entry["where"] == "replace"
                                                 else None), entry.get("anchor") or "")
        if entry["where"] == "replace":
            lines[at["start"]:at["start"] + at["text"].count("\n") + 1] = block
        elif entry["where"] == "before":
            lines[at["start"]:at["start"]] = block + [""]
        elif entry["where"] == "after":
            stop = at["start"] + at["text"].count("\n") + 1
            lines[stop:stop] = ["", *block]
        else:
            while lines and not lines[-1].strip():
                lines.pop()
            lines += ["", *block, ""]
        text = "\n".join(lines)
        done.append(entry["heading"])
    return text, done


def retired_pins(root: Path, framework: Path) -> list[dict]:
    """The `checks:` lines of the project that pin a code the new catalog has retired.

    A RETIRED CODE IS THE ONE THING A PIN CANNOT SURVIVE, and the project that pinned it is
    the project that took the check most seriously. The new validator ignores the line while
    the project still declares the older version and stops on it once the project declares
    the new one -- so a project that adopted by writing the number would be stopped before
    seeing any migration. This tool's job is to say what changes, not to refuse: the pin is
    filed under GONE, because the move is what makes it meaningless, and `--adopt` removes
    the line with the number so that nothing is left for the validator to stop on.
    """
    cfg = root / "framework.yaml"
    if not cfg.exists():
        return []
    try:
        settings = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    pins = settings.get("checks") if isinstance(settings, dict) else None
    if not isinstance(pins, dict):
        return []
    catalog = yaml.safe_load((framework / "skills/audit/checks.yaml")
                             .read_text(encoding="utf-8")).get("checks") or {}
    out = []
    for code, override in pins.items():
        spec = catalog.get(code) or {}
        if spec.get("level") != "retired":
            continue
        level = override.get("level") if isinstance(override, dict) else override
        out.append({"code": code, "path": "framework.yaml", "level": "retired",
                    "message": (f"pinned at {level!r} in framework.yaml, and retired in "
                                f"{spec.get('retired_in', 'this version')}: the line switches "
                                "nothing on, and the validator of the new version stops on it "
                                "once the project declares that version. `--adopt` removes "
                                "the line with the number.")})
    return out


PIN_LINE = re.compile(r"^([ \t]+)([A-Z]{2,3}\d{3})\s*:")


def without_pins(text: str, codes) -> str:
    """`framework.yaml` without the `checks:` lines pinning `codes`, comments and all else kept.

    Line based, like `adopt`, for the reason given there. The long form -- a key with a
    nested `level:` under it -- goes with its nested lines, or the file would be left with an
    indented orphan that no longer parses.
    """
    codes = set(codes)
    lines = text.split("\n")
    kept: list[str] = []
    i = 0
    while i < len(lines):
        m = PIN_LINE.match(lines[i])
        if m and m.group(2) in codes:
            indent = len(m.group(1))
            # The nested lines of the long form, with the blank and comment lines among them,
            # up to the last line that is deeper than the key: a comment sitting between the
            # key and its `level:` goes with the key, a comment before the next key stays.
            end = i + 1
            j = i + 1
            while j < len(lines):
                stripped = lines[j].strip()
                deeper = len(lines[j]) - len(lines[j].lstrip()) > indent
                if stripped and not stripped.startswith("#") and not deeper:
                    break
                if stripped and not stripped.startswith("#") and deeper:
                    end = j + 1
                j += 1
            i = end
            continue
        kept.append(lines[i])
        i += 1
    return "\n".join(kept)


def adoption_problem(root, framework, current):
    """Never write a Git pin for a dirty/different tree or preserve a stale package pin."""
    cfg = yaml.safe_load((root / "framework.yaml").read_text(encoding="utf-8")) if (root / "framework.yaml").exists() else {}
    top = git(["rev-parse", "--show-toplevel"], framework)
    if top.returncode or Path(top.stdout.strip()).resolve() != framework:
        if isinstance(cfg, dict) and "framework_commit" in cfg:
            return "pinned adoption requires a clean target Git checkout; an export cannot update framework_commit"
        return None
    state = git(["status", "--porcelain", "--untracked-files=all"], framework)
    registry = git(["show", f"HEAD:{REGISTRY_REL}"], framework)
    if state.returncode or state.stdout.strip() or registry.returncode or registry_version(registry.stdout) != current:
        return "adoption requires a clean committed target framework, not uncommitted implementation bytes"
    return None


def adopt(cfg: Path, version: str, commit: str | None, drop=()) -> str | None:
    """Write the new number, the pinned commit beside it when there is one, and no retired pin.

    Returns the reason nothing was written, or None when it was. The one reason is a retired
    pin the line based edit could not remove -- flow style, `checks: {LC005: warn}` -- because
    writing the number and leaving the pin would stop the validator of the version just
    adopted, which is the failure the removal exists to prevent.

    Both or neither, and that is the point of doing it here. A project that pins moves two
    facts at once; a migration that moved one of them would leave the pin naming the version
    it just stopped running, which `FW003` then reports for the rest of the week. The pin is
    only rewritten when the file already carries one: adding it to a project that never asked
    for it would be this tool taking a decision that costs a deliberate bump per fix.

    A rewrite through yaml.safe_dump would drop every comment in a project's own
    configuration, including the ones explaining why a check is switched off -- which is
    the reasoning this framework asks people to write down.
    """
    # Quoted, always. A bare `2.7` is a decimal to YAML and a bare `3` a whole number,
    # and `FW001` reports both as unusable -- which would be this tool writing the
    # finding it exists to clear.
    declared = f'framework_version: "{version}"'
    if not cfg.exists():
        cfg.write_text(declared + "\n", encoding="utf-8")
        return None
    text = cfg.read_text(encoding="utf-8")
    line = re.compile(r"^framework_version:.*$", re.M)
    text = (line.sub(declared, text, count=1) if line.search(text)
            else declared + "\n" + text)
    pin = re.compile(r"^framework_commit:.*$", re.M)
    if commit and pin.search(text):
        text = pin.sub(f'framework_commit: "{commit}"', text, count=1)
    # A `checks:` line on a code this version retired: filed under GONE by the comparison,
    # removed here with the number, or the validator of the version just adopted stops on it.
    if drop:
        text = without_pins(text, drop)
        try:
            left = (yaml.safe_load(text) or {}).get("checks") or {}
        except yaml.YAMLError:
            left = {}
        still = sorted(c for c in drop if isinstance(left, dict) and c in left)
        if still:
            return (f"not adopted: framework.yaml pins {', '.join(still)} in a form this tool "
                    "does not edit -- flow style, or a shape the line based removal does not "
                    "recognise. Remove the line by hand, then adopt: written with the pin in "
                    "place, the number would stop the validator it declares.")
    cfg.write_text(text, encoding="utf-8")
    return None


def verdict(report: dict) -> int:
    """0 when there is nothing left to do, 1 when there is.

    An adopted migration is nothing left to do even though it reported findings a moment
    ago: they were the reason to run it.
    """
    if report["problems"]:
        return 1
    if report.get("adopted"):
        return 0
    if any(e["action"] in ("add", "update")
           for e in (report.get("agents") or {}).get("sections", [])):
        return 1
    if report["up_to_date"]:
        return 0
    return 1 if report["new"] or report["version_line"] or report["problems"] else 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Compare a project against two versions of the framework")
    ap.add_argument("--root", default=".", type=Path, help="the project, not the framework")
    ap.add_argument("--framework", default=FRAMEWORK, type=Path,
                    help="the framework checkout to migrate towards")
    ap.add_argument("--from", dest="from_version",
                    help="override the version in the project's framework.yaml")
    previous = ap.add_mutually_exclusive_group()
    previous.add_argument("--from-framework", type=Path,
                          help="trusted complete previous export/checkout; version checked, commit provenance not authenticated")
    previous.add_argument("--from-commit", help="exact previous framework Git commit; overrides the project pin")
    ap.add_argument("--adopt", action="store_true",
                    help="write the new framework_version into the project, and the "
                         "framework's sections of its AGENTS.md")
    ap.add_argument("--replace-section", action="append", default=[], metavar="ID",
                    help="with --adopt: put the template's text in place of a section of "
                         "AGENTS.md the report lists as left (edited, or copied by hand)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root, framework = args.root.resolve(), args.framework.resolve()
    # Both are checked before anything is read, and they are checked apart: pointed at a
    # project that is not there, this reported "declares no framework_version" about a
    # `framework.yaml` inside a directory that does not exist, which sends somebody to write
    # a line into a file they cannot open.
    if not root.is_dir():
        sys.exit(f"{root}: no such directory. `--root` is the project being migrated.")
    if not (framework / REGISTRY_REL).exists():
        sys.exit(f"{framework}: no {REGISTRY_REL} here, so this is not a checkout of the "
                 "framework. `--framework` is the definition, `--root` is the project.")
    say_if_the_checkout_moved(root, framework)

    registry = (framework / REGISTRY_REL).read_text(encoding="utf-8")
    current = registry_version(registry)
    declared, cfg, unreadable = declared_version(root)
    declared = args.from_version or declared
    compare_explicitly = bool(args.from_framework or args.from_commit)
    if not unreadable and not args.from_version and cfg.exists():
        settings = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        pin = settings.get("framework_commit") if isinstance(settings, dict) else None
        if pin is not None:
            head = git(["rev-parse", "HEAD"], framework)
            compare_explicitly |= (not isinstance(pin, str) or not COMMIT.fullmatch(pin)
                                   or head.returncode != 0 or not head.stdout.strip().lower().startswith(pin.lower()))

    report = {"project": str(root), "declared": declared, "current": current,
              "up_to_date": False, "notes": [], "already_there": [], "new": [], "gone": [],
              "version_line": [], "accepted": [], "problems": [], "new_checks": []}
    old_template = None

    if unreadable and not args.from_version:
        report["problems"].append(unreadable)
    elif declared is None:
        report["problems"].append(
            f"{cfg} declares no `framework_version`, so there is no version to migrate "
            "from. That is `FW002`, and the repair is to write the number the project has "
            "actually been validating against -- not today's, unless it really is.")
    elif semver(declared) is None:
        report["problems"].append(
            f"the project declares {declared!r}, which is not three numbers separated by "
            "dots. `2` and `1.1` are a whole number and a decimal to YAML, and neither "
            "compares with a version. Quote it, or complete it.")
    elif semver(declared) == semver(current) and not compare_explicitly:
        # Not a problem, and the distinction is the exit code. A repository already on the
        # current version is the state every repository is supposed to end up in, and a tool
        # that returns 1 for it cannot be put in a pipeline: the run that says "nothing to
        # do" and the run that says "the history is shallow and I could not compare" would
        # be indistinguishable to whoever wired it up. A section of `AGENTS.md` still to
        # write is something to do, and `verdict` says so: still not a failure to compare.
        report["up_to_date"] = True
    elif semver(declared) > semver(current):
        report["problems"].append(
            f"the project declares {declared} and this checkout is {current}: it is ahead "
            "of the framework it is being pointed at, which usually means `--framework` "
            "points at a stale checkout.")

    if declared and semver(declared) and (semver(declared) < (semver(current) or (0, 0, 0))
            or (semver(declared) == semver(current) and compare_explicitly)):
        lo, hi = semver(declared), semver(current)
        for frm, to, prose in migration_notes(registry):
            if semver(to) and lo < semver(to) <= hi:
                report["notes"].append({"from": frm, "to": to, "note": prose})

        try:
            with previous_framework(args, declared, root, framework) as (old_tree, origin):
                report["previous_source"] = origin
                before, now = (catalog(t) for t in (old_tree, framework))
                if before is not None and now is not None:
                    report["new_checks"] = new_checks(before, now)
                if (old_tree / TEMPLATE_REL).is_file():
                    old_template = (old_tree / TEMPLATE_REL).read_text(encoding="utf-8")
                old = findings(old_tree / VALIDATE_REL, root)
                new = findings(framework / VALIDATE_REL, root)
                if origin.get("commit"):
                    report["commit"] = origin["commit"][:12]
                # The pins on codes the move retires. Not a finding of either validator: the
                # old one applied the line, the new one ignores it and says so on stderr. It
                # is filed here, under GONE, because that is what the move does to it.
                report["gone"].extend(retired_pins(root, framework))
                for k in sorted(set(old) | set(new)):
                    f = new.get(k) or old[k]
                    # `FW001` and `FW002` are about the number this tool exists to move.
                    # They are new by construction on every migration, and what clears
                    # them is `--adopt` rather than an edit to any document -- so filing
                    # them under "this is the migration work" told the reader to go and
                    # fix something, while `--adopt` was ignoring them. One of the two
                    # was lying, and it was the report.
                    # A FINDING THE PROJECT HAS EXAMINED AND LEFT STANDING IS NOT
                    # MIGRATION WORK, AND FILING IT AS SUCH IS WHAT DEADLOCKED THIS
                    # TOOL. `--adopt` refuses while NEW is non-empty, which is right:
                    # the number it writes is the claim that the migration is done. But
                    # what landed under NEW was every finding the new validator reports
                    # and the old one did not, including the ones that are defects of
                    # the validator itself -- and no amount of work on the documents
                    # removes those. A project that had finished the migration and
                    # written down why two findings stay could not say so, because
                    # there was nowhere for that to be written and nothing here to read
                    # it. There is now, and the guard keeps its meaning: it blocks on
                    # work outstanding, and an examined finding is not outstanding.
                    # AND THE SAME DEADLOCK RETURNS ONE LEVEL UP, THROUGH THE
                    # ANNOTATION. A repository that asks for `require_all` gets an
                    # `AN003` for every unannotated warning -- including the `FW001` and
                    # `FW003` that exist only because this migration has not happened
                    # yet. That `AN003` is not in `ADOPT_CLEARS`, so it landed under NEW
                    # and refused the adoption that would have removed the finding it
                    # was reporting about. The only ways out were to annotate a finding
                    # that is about to vanish -- which the next run reports as `AN001`,
                    # obsolete -- or to stop asking for all annotations. Both punish the
                    # project for taking the framework seriously, which is the sentence
                    # written above about the pin, word for word. An annotation finding
                    # whose subject `--adopt` clears is cleared by `--adopt` too.
                    where = ("version_line" if adopt_clears(f)
                             else "accepted" if k in new and new[k].get("accepted")
                             else "already_there" if k in old and k in new
                             else "new" if k in new else "gone")
                    entry = {"code": f["code"], "path": f["path"], "level": f["level"],
                             "message": f["message"]}
                    if where == "accepted":
                        entry["accepted"] = new[k]["accepted"]
                    report[where].append(entry)
        except (RuntimeError, OSError, ValueError, KeyError, yaml.YAMLError) as e:
            report["problems"].append(f"could not compare the {declared} and {current} validators: {e}")

    # Read whether or not the version moved: a project that declares an exchange after
    # adopting is owed the section as much as one that crosses the version adding it.
    if not report["problems"]:
        try:
            unknown = sorted(set(args.replace_section) - marked_ids(framework))
            if unknown:
                report["problems"].append(
                    f"--replace-section {', '.join(unknown)}: not a section the template "
                    f"marks as the framework's ({', '.join(sorted(marked_ids(framework)))})")
            report["agents"] = section_plan(root, framework, old_template,
                                            replace=set(args.replace_section))
        except (OSError, UnicodeError, ImportError, AttributeError) as e:
            report["problems"].append(f"could not read {AGENTS_REL}, its template or the "
                                      f"framework's reading of the exchange: {e}")
    pending = [e for e in (report.get("agents") or {}).get("sections", [])
               if e["action"] in ("add", "update")]

    if args.adopt:
        if not report["problems"] and pending:
            problem = agents_dirty(root)
            if problem:
                report["problems"].append(problem)
        if not report["problems"]:
            problem = adoption_problem(root, framework, current)
            if problem:
                report["problems"].append(problem)
        if report["new"]:
            report["problems"].append(
                "not adopted. `--adopt` writes the new number, which is the claim that the "
                "migration is done; do it after the findings under NEW are gone. A finding "
                "that is not going to go -- a defect of the validator, a state the project "
                "has examined and decided to keep -- belongs in "
                "`.framework/expected-findings.yaml` with the reason and the event that "
                "clears it, and it stops counting as outstanding. That file is the honest "
                "path through this guard, and it exists so that writing the number by hand "
                "is not.")
        elif report["problems"]:
            if not any(p.startswith("not adopted") for p in report["problems"]):
                report["problems"].append("not adopted, and nothing written, for the reason "
                                          "above.")
        else:
            head = git(["rev-parse", "HEAD"], framework)
            top = git(["rev-parse", "--show-toplevel"], framework)
            commit = (head.stdout.strip() if head.returncode == 0 and top.returncode == 0
                      and Path(top.stdout.strip()).resolve() == framework else None)
            # Both or neither. The sections are prepared before the number is written and
            # written only once it is; if they cannot be, the number goes back to what it was.
            original = (root / AGENTS_REL).read_bytes().decode("utf-8") if pending else ""
            agents_text, written = (apply_sections(original.replace("\r\n", "\n"),
                                                   report["agents"])
                                    if pending else (None, []))
            if written and "\r\n" in original:   # the file's line endings stay the file's
                agents_text = agents_text.replace("\n", "\r\n")
            before = cfg.read_bytes() if cfg.exists() else None
            problem = adopt(cfg, current, commit,
                            drop=[p["code"] for p in retired_pins(root, framework)])
            if problem:
                report["problems"].append(problem)
            elif written:
                staged = root / (AGENTS_REL + ".migrate")
                try:
                    # Written beside and moved over: an interruption leaves the old file.
                    staged.write_bytes(agents_text.encode("utf-8"))
                    os.replace(staged, root / AGENTS_REL)
                    report["adopted"] = current
                    report["agents_written"] = written
                except OSError as e:
                    staged.unlink(missing_ok=True)
                    if before is None:
                        cfg.unlink(missing_ok=True)
                    else:
                        cfg.write_bytes(before)
                    report["problems"].append(
                        f"not adopted, and nothing written: {AGENTS_REL} could not be written "
                        f"({e}), so {cfg.name} was put back as it was.")
            else:
                report["adopted"] = current

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return verdict(report)

    print(f"Project:   {root}")
    print(f"Declared:  {declared}")
    print(f"Framework: {current}" + (f"  (old validator from {report['commit']})"
                                     if report.get("commit") else ""))
    if report["up_to_date"]:
        print(f"\nAlready on {current}: nothing to migrate"
              + (f", and {len(pending)} of the framework's sections of {AGENTS_REL} to write, "
                 "below: `--adopt`." if pending and not report.get("adopted") else "."))
    for p in report["problems"]:
        print(f"\n! {p}")
    if report["notes"]:
        print("\n-- WHAT MOVED " + "-" * 40)
        for n in report["notes"]:
            print(f"\n{n['note']}")
    if report["new_checks"]:
        print(f"\n-- CHECKS NEW SINCE {declared} ({len(report['new_checks'])}) " + "-" * 20)
        print("   in the catalog now and not in the declared version's; their findings, if "
              "any, are under NEW")
        for c in report["new_checks"]:
            print(f"   {c['code']}  {c['level']:<6} {c['title']}")
    for key, label, why in (
            ("new", "NEW: reported only by the new validator",
             "this is the migration work"),
            ("version_line", "THE VERSION LINE ITSELF",
             "not a document to repair: `--adopt` writes it, once NEW is empty"),
            ("already_there", "ALREADY THERE: reported by both",
             "documents to repair, unrelated to the version"),
            ("accepted", "EXAMINED AND LEFT STANDING",
             "annotated in the project, with why and what clears each one: `--adopt` does "
             "not block on these"),
            ("gone", "GONE: reported only by the old one",
             "cleared by the move, nothing to do")):
        group = report[key]
        if not group:
            continue
        print(f"\n-- {label} ({len(group)}) " + "-" * 20)
        print(f"   {why}")
        for f in group:
            print(f"   [{f['code']}] {f['path']}\n       {f['message'].splitlines()[0]}")
            if f.get("accepted"):
                print(f"       why it stays: {f['accepted']['reason']}")
                print(f"       cleared by:   {f['accepted']['clears_when']}")
    agents = report.get("agents")
    if agents and agents["sections"]:
        print(f"\n-- THE FRAMEWORK'S SECTIONS OF {AGENTS_REL} ({len(agents['sections'])}) "
              + "-" * 20)
        print("   `--adopt` writes ADD and UPDATE with the number; LEFT and SKIPPED are not "
              "written")
        for e in agents["sections"]:
            print(f"   {e['action'].upper():<8}{e['heading']}\n       {e.get('at') or e.get('why')}")
            if e.get("text") and not report.get("agents_written"):
                for line in e["text"].split("\n"):
                    print(f"       | {line}".rstrip())
    for note in (agents or {}).get("notes", []):
        print(f"\n{AGENTS_REL}: {note}")
    if agents and not agents["exists"]:
        print(f"\n{AGENTS_REL}: not in the project, so no section of it is written. `start` "
              "creates it from the template.")
    if report.get("adopted"):
        print(f"\nAdopted: {cfg} now declares {report['adopted']}")
    if report.get("agents_written"):
        print(f"\n{AGENTS_REL}: written {', '.join(repr(h) for h in report['agents_written'])}. "
              "It is a living document. Commit it with framework.yaml, as the adoption; then a "
              "person rereads it and attests with `skills/audit/scripts/attest.py --root "
              f"<project> {AGENTS_REL} --scope \"...\"`, and the attestation is committed on "
              "its own. Until then the validator reports the change: `LC006` once it is "
              "committed, `PR005` on a pull request.")
    print()
    return verdict(report)


if __name__ == "__main__":
    sys.exit(main())
