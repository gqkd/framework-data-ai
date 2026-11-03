#!/usr/bin/env python3
"""The SessionStart hook: in a project of the framework, the plugin's version against the latest
release and the version the project pins; in one in the additive mode, also the to-do in a few
lines.

A plugin's hooks run in every session of everyone who has the plugin enabled, so this one first
looks, with the standard library alone, above the folder the session started in, for a
`framework.yaml` with a `framework_version:` line or for `.framework/work.yaml`, and leaves at once,
saying nothing, where there is neither: a missing dependency of the scripts must not print a line
in every session of every project, nor a `framework.yaml` of another tool bring the plugin's
versions, and a question about them, into a project that is not the framework's.

The three versions. The plugin's is its `plugin.json`. The latest release is the highest
`v<x>.<y>.<z>` tag where the plugin comes from, read with `git ls-remote --tags` at most once a
day -- the day it was tried and the last answer kept in `CLAUDE_PLUGIN_DATA`, and nothing read
where there is no such folder -- with a short time limit, no terminal, and git's and ssh's prompts
turned off; a credential helper that is another system's program, as Git Credential Manager from
Windows under WSL, does not see those variables and may still open a window for a private source.
When it cannot be read it says so and uses the last answer kept. The mode and the pin
are read as the to-do reads them: the main line's `.framework/work.yaml` and, in the mode, its
`framework.yaml` -- `origin/main`, or `main` where there is none --; the checkout's where the main
line does not read, and the checkout's pin outside the mode. A plugin older than the latest
release, or than the pin -- said more strongly, since there the problems are certain --, is said
first, with the commands of the way it was installed: from a marketplace added by URL, copied into
the cache; from a local folder that is a git checkout, read in place, and from one that is not, as
from a URL; for one session with `--plugin-dir`, no commands. The person is asked to accept it
when the session starts -- `source` `startup`, none that reads, or any value but the four that
follow --: on a resumption, a `/clear`, a compaction or a fork the versions are put back in the
context without asking. Where Claude Code says nobody is there to answer -- as under `claude -p`
--, nobody is asked: the agent says it at the top of its final answer.

Where the mode is declared and the pin is the version that brought it or later, or none, it runs
`todo.py --summary` and prints what it says; where that fails it prints one line saying so, and
where to look, and where the versions cannot be compared it says so in one line and goes on to the
to-do. Whatever it prints Claude Code puts in the session's context. It never stops a session: it
always exits 0. Its time limits -- the release, the main line, the to-do -- add up to less than
the 120 seconds `hooks.json` gives it.
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

PLUGIN = "framework-data-ai"
MODE = re.compile(r"^mode:[ \t]*['\"]?additive['\"]?[ \t]*(?:#.*)?$", re.M)
PIN = re.compile(r"^framework_version:[ \t]*['\"]?(\d+)\.(\d+)\.(\d+)", re.M)
# What makes a `framework.yaml` the framework's: the line `start` always writes, whatever its value.
MARK = re.compile(r"^framework_version:", re.M)
RELEASE = re.compile(r"\trefs/tags/v(\d+)\.(\d+)\.(\d+)(?:\^\{\})?$", re.M)
# The first version that knows the mode: a project pinned below it is not in it, whatever its
# `work.yaml` says, and a plugin updated before the adoption must not speak for it.
SINCE = (4, 9, 0)
MAIN_LINE = ("origin/main", "main")   # as `todo.py` reads it, by its defaults
AGAIN = ("resume", "clear", "compact", "fork")
# Set by Claude Code to `0` in a session nobody attends, as under `claude -p` (seen with 2.1.317;
# its documentation does not name it). Missing, or with another value, the session counts as
# attended and the person is asked: a change of name brings the question back, not silence.
ALONE = ("CLAUDE_CODE_SESSION_ATTENDED", "0")
RELEASE_SECONDS = 8
MAIN_SECONDS = 5                      # the main line's two files, together
TODO_SECONDS = 90
KEPT = "latest-release.json"          # in CLAUDE_PLUGIN_DATA
# The prompts turned off: git's terminal and askpass, ssh's askpass, Git Credential Manager's
# window where it reads these variables. With no terminal either (`start_new_session`), ssh cannot
# ask for a passphrase or a host key, and fails instead.
QUIET = {"GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "", "SSH_ASKPASS": "",
         "SSH_ASKPASS_REQUIRE": "never", "GCM_INTERACTIVE": "never"}


def documentation(start: Path) -> Path | None:
    """The folder with a `framework.yaml` that has a `framework_version:` line, or with
    `.framework/work.yaml`, up to the top of the repository that holds `start`."""
    for folder in (start, *start.parents):
        if (folder / ".framework" / "work.yaml").is_file() \
                or MARK.search(read(folder / "framework.yaml")):
            return folder
        if (folder / ".git").exists():
            return None
    return None


def read(path: Path) -> str:
    """The file's text, a byte order mark dropped -- an editor may save one, and YAML ignores
    it --; `""` where it does not read."""
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return ""


def version(text: str) -> tuple[int, ...] | None:
    m = PIN.search(text)
    return tuple(map(int, m.groups())) if m else None


def shown(v: tuple[int, ...] | None) -> str:
    return ".".join(map(str, v)) if v else "?"


def main_line(root: Path) -> tuple[str, str, str] | None:
    """The main line, and its `.framework/work.yaml` and `framework.yaml` beside `root`, each `""`
    where it holds no such file; None where there is no main line here, or it does not read in
    time."""
    until = time.monotonic() + MAIN_SECONDS

    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                              stdin=subprocess.DEVNULL,
                              timeout=max(0.1, until - time.monotonic()))
    try:
        base = next((b for b in MAIN_LINE
                     if git("rev-parse", "--verify", "-q", f"{b}^{{commit}}").returncode == 0),
                    None)
        if base is None:
            return None
        work, pinned = (git("show", f"{base}:./{f}") for f in (".framework/work.yaml",
                                                                 "framework.yaml"))
    except (OSError, UnicodeError, subprocess.SubprocessError):
        return None
    return (base, work.stdout.lstrip(chr(0xFEFF)) if work.returncode == 0 else "",
            pinned.stdout.lstrip(chr(0xFEFF)) if pinned.returncode == 0 else "")


def project(root: Path) -> tuple[bool, tuple[int, ...] | None, str]:
    """Whether the project is in the additive mode, the version it pins, and where that was
    read: as the to-do reads them."""
    line = main_line(root)
    if line is not None and MODE.search(line[1]):
        return True, version(line[2]), f"on {line[0]}"
    mode = line is None and bool(MODE.search(read(root / ".framework" / "work.yaml")))
    return mode, version(read(root / "framework.yaml")), "in this checkout"


def plugins_root() -> Path:
    """Where Claude Code keeps its records of plugins and marketplaces."""
    if os.environ.get("CLAUDE_CODE_PLUGIN_CACHE_DIR"):
        return Path(os.environ["CLAUDE_CODE_PLUGIN_CACHE_DIR"])
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "plugins"


def installed(here: Path) -> tuple[str, str, dict]:
    """How this copy was loaded -- `inline`, `folder`, `remote` or `unknown` --, the name of its
    marketplace, and the marketplace's record. Not by the kind of source the record writes
    alone: by where this copy sits against it. Read in place, it is `folder` when its folder is
    the top of a git checkout, and `remote` otherwise."""
    data = os.environ.get("CLAUDE_PLUGIN_DATA") or ""
    if data and Path(data).name.endswith("-inline"):
        return "inline", "", {}
    try:
        known = json.loads((plugins_root() / "known_marketplaces.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        known = {}
    for name, record in (known.items() if isinstance(known, dict) else ()):
        if not isinstance(record, dict) or not isinstance(record.get("installLocation"), str):
            continue
        try:
            place = Path(record["installLocation"]).expanduser().resolve()
            if place.is_file():
                place = place.parent
            if (place == here or place in here.parents) and not (
                    plugins_root().resolve() in place.parents):
                return ("folder" if (here / ".git").exists() else "remote"), name, record
            if (plugins_root() / "cache" / name).resolve() in here.parents:
                return "remote", name, record
        except (OSError, RuntimeError):
            continue
    return "unknown", "", {}


def quiet(call: list[str]) -> str:
    """What `call` writes, run with no terminal and the prompts of `QUIET` turned off, its whole
    process group stopped at the time limit; `""` where it fails."""
    with subprocess.Popen(call, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, text=True, start_new_session=True,
                          env={**os.environ, **QUIET}) as p:
        try:
            out, _ = p.communicate(timeout=RELEASE_SECONDS)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except (OSError, AttributeError):
                p.kill()
            return ""
    return out if p.returncode == 0 else ""


def latest_release(kind: str, record: dict, here: Path) -> tuple[tuple[int, ...] | None, str]:
    """The highest release where the plugin comes from, and what to add about it: nothing when
    read today, the day of the last answer when it could not be read today. Read at most once a
    day, failed or not, and not at all where there is no data folder to keep that day in."""
    source = record.get("source") if isinstance(record.get("source"), dict) else {}
    if kind == "folder" or (kind == "inline" and (here / ".git").exists()):
        # The checkout the plugin's own files are the top of, read on its remote: its tags move
        # only after a pull.
        call, key = ["git", "-C", str(here), "ls-remote", "--tags"], str(here)
    elif kind == "remote" and source.get("source") == "github" and source.get("repo"):
        url = f"https://github.com/{source['repo']}.git"
        call, key = ["git", "ls-remote", "--tags", url], url
    # Not tried: how `known_marketplaces.json` writes a git URL the documentation does not say,
    # and a record of another shape reads as "does not say".
    elif kind == "remote" and source.get("source") == "git" and source.get("url"):
        call, key = ["git", "ls-remote", "--tags", str(source["url"])], str(source["url"])
    else:
        return None, "where the plugin comes from does not say"
    data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if not data:
        return None, "no data folder to keep it in, so it is not read"
    kept_at = Path(data) / KEPT
    try:
        kept = json.loads(kept_at.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        kept = {}
    if not isinstance(kept, dict) or kept.get("source") != key:
        kept = {}
    today = date.today().isoformat()
    if today not in (kept.get("checked"), kept.get("tried")):
        try:
            found = sorted({tuple(map(int, m)) for m in RELEASE.findall(quiet(call))})
        except (OSError, UnicodeError, subprocess.SubprocessError):
            found = []
        kept = {**kept, "source": key, "tried": today}
        if found:
            kept.update(checked=today, latest=shown(found[-1]))
        try:
            kept_at.parent.mkdir(parents=True, exist_ok=True)
            kept_at.write_text(json.dumps(kept) + "\n", encoding="utf-8")
        except OSError:
            pass
    latest = (version("framework_version: " + kept["latest"])
              if isinstance(kept.get("latest"), str) else None)
    if latest and kept.get("checked") == today:
        return latest, ""
    if latest:
        return latest, f"as read on {kept.get('checked', '?')}: it could not be read today"
    return None, "it could not be read today"


def update_road(kind: str, market: str, here: Path) -> str:
    if kind == "remote":
        return (f"To update, the person runs `claude plugin marketplace update {market}`, then "
                f"`claude plugin update {PLUGIN}@{market}`, then starts a new session or runs "
                "`/reload-plugins`.")
    if kind == "folder":
        return (f"It is read in place from {here}: to update, the person runs "
                f"`git -C {here} pull`, then starts a new session or runs `/reload-plugins`; "
                "no reinstalling.")
    if kind == "inline":
        return ("It was loaded for this session alone, with `--plugin-dir`: no update command "
                "touches it, and the folder it was loaded from is the one the person brings "
                "forward.")
    return ("How it was installed could not be read. From a marketplace added by URL, the person "
            f"runs `claude plugin marketplace update {PLUGIN}`, then `claude plugin update "
            f"{PLUGIN}@{PLUGIN}`; from a marketplace added from a local folder, `git pull` in "
            "that folder; then a new session or `/reload-plugins`.")


def versions(here: Path, pin: tuple[int, ...] | None, where: str, how: str) -> list[str]:
    """The lines on the three versions; `how` is `ask` at the start of an attended session,
    `again` when it did not just start, `alone` when nobody attends it."""
    try:
        meta = json.loads((here / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        mine = version("framework_version: " + str(meta.get("version", "")))
    except (OSError, UnicodeError, ValueError, AttributeError):
        mine = None
    kind, market, record = installed(here)
    latest, note = latest_release(kind, record, here)
    release = (shown(latest) + (f" ({note})" if note else "")) if latest else f"unknown ({note})"
    out = [f"{PLUGIN}: this plugin is {shown(mine)}; the latest release is {release}; the "
           f"project pins {shown(pin) if pin else 'no version that reads'} {where}."]
    behind_pin = bool(mine and pin and mine < pin)
    behind = bool(mine and latest and mine < latest)
    if not (behind_pin or behind):
        return out
    if behind_pin:
        out.append(f"This plugin is older than the version the project pins: its skills, its "
                   f"validator and its scripts do not know what came up to {shown(pin)}, so "
                   "problems here are certain, not possible.")
    else:
        out.append("This plugin is older than the latest release: an older version can give "
                   "problems a newer one has fixed.")
    out.append({"ask": "Before anything else, tell the person so and ask them to accept going on "
                       "with it as it is, or to update first; the answer is recorded nowhere, it "
                       "is a fact of their machine.",
                "again": "This session did not just start -- it was resumed, cleared, compacted "
                         "or forked --: do not ask the person to accept it.",
                "alone": "Nobody attends this session -- Claude Code says so, as under `claude "
                         "-p` --, so nobody can answer: do not ask; say it, with the three "
                         "versions, at the top of your final answer."}[how])
    out.append(update_road(kind, market, here))
    return out


def reason(lines: list[str], code: int) -> str:
    """The line that names what is missing -- the validator's own `Needs <module>`, or
    Python's -- where there is one; the last one otherwise; the exit code when nothing was said."""
    named = next((l for l in lines if l.startswith("Needs ") or "No module named" in l), None)
    return named or (lines[-1] if lines else f"exit {code}, with no message")


def main() -> int:
    try:
        raw = sys.stdin.read()
        try:
            given = json.loads(raw) if raw.strip() else {}
            source = given.get("source") if isinstance(given, dict) else None
        except ValueError:
            source = None
        start = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()
        root = documentation(start)
        if root is None:
            return 0
        mode, pin, where = project(root)
        here = Path(__file__).resolve().parents[1]
    except Exception:
        return 0
    # The versions apart: whatever fails in them leaves the to-do to be said.
    try:
        how = ("alone" if os.environ.get(ALONE[0]) == ALONE[1] else
               "again" if source in AGAIN else "ask")
        print("\n".join(versions(here, pin, where, how)))
    except Exception as e:
        print(f"{PLUGIN}: the plugin's version could not be compared here: "
              f"{type(e).__name__}: {e}"[:300])
    if not mode or (pin is not None and pin < SINCE):
        return 0
    todo = here / "skills" / "audit" / "scripts" / "todo.py"
    try:
        r = subprocess.run([sys.executable, str(todo), "--root", str(root), "--summary"],
                           capture_output=True, text=True, timeout=TODO_SECONDS)
        out = r.stdout.strip() if r.returncode == 0 else ""
        why = ([reason((r.stderr or r.stdout).strip().splitlines(), r.returncode)]
               if r.returncode else [])
    except subprocess.TimeoutExpired:
        out, why = "", [f"it took more than {TODO_SECONDS} seconds"]
    except (OSError, subprocess.SubprocessError) as e:
        out, why = "", [f"{type(e).__name__}: {e}"]
    if out:
        print(out)
    elif why:
        print(f"The to-do of the additive mode could not be computed here: {why[0][:200]} "
              "(`references/workstation.md` says what the framework's scripts need).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
