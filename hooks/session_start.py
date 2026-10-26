#!/usr/bin/env python3
"""The SessionStart hook: in a project in the additive mode, the to-do in a few lines.

A plugin's hooks run in every session of everyone who has the plugin enabled, so this one first
looks, with the standard library alone, for `.framework/work.yaml` with `mode: additive` above
the folder the session started in, and leaves at once, saying nothing, where there is none: a
missing dependency of the scripts must not print a line in every session of every project.
Where the mode is declared it runs `todo.py --summary` and prints what it says, which Claude Code
puts in the session's context; where that fails it prints one line saying so, and where to look.
It never stops a session: it always exits 0.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

MODE = re.compile(r"^mode:[ \t]*['\"]?additive['\"]?[ \t]*(?:#.*)?$", re.M)
PIN = re.compile(r"^framework_version:[ \t]*['\"]?(\d+)\.(\d+)\.(\d+)", re.M)
# The first version that knows the mode: a project pinned below it is not in it, whatever its
# `work.yaml` says, and a plugin updated before the adoption must not speak for it.
SINCE = (4, 9, 0)


def documentation(start: Path) -> Path | None:
    """The folder with `.framework/work.yaml` declaring the additive mode, up to the top of
    the repository that holds `start`."""
    for folder in (start, *start.parents):
        work = folder / ".framework" / "work.yaml"
        try:
            if work.is_file() and MODE.search(work.read_text(encoding="utf-8")):
                pinned = folder / "framework.yaml"
                pin = PIN.search(pinned.read_text(encoding="utf-8")) if pinned.is_file() else None
                if pin and tuple(map(int, pin.groups())) < SINCE:
                    return None
                return folder
        except (OSError, UnicodeError):
            return None
        if (folder / ".git").exists():
            return None
    return None


def reason(lines: list[str], code: int) -> str:
    """The line that names what is missing -- the validator's own `Needs <module>`, or
    Python's -- where there is one; the last one otherwise; the exit code when nothing was said."""
    named = next((l for l in lines if l.startswith("Needs ") or "No module named" in l), None)
    return named or (lines[-1] if lines else f"exit {code}, with no message")


def main() -> int:
    try:
        sys.stdin.read()
        start = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()
        root = documentation(start)
    except Exception:
        return 0
    if root is None:
        return 0
    todo = Path(__file__).resolve().parents[1] / "skills" / "audit" / "scripts" / "todo.py"
    try:
        r = subprocess.run([sys.executable, str(todo), "--root", str(root), "--summary"],
                           capture_output=True, text=True, timeout=90)
        said = r.stdout.strip() if r.returncode == 0 else ""
        why = ([reason((r.stderr or r.stdout).strip().splitlines(), r.returncode)]
               if r.returncode else [])
    except subprocess.TimeoutExpired:
        said, why = "", ["it took more than 90 seconds"]
    except (OSError, subprocess.SubprocessError) as e:
        said, why = "", [f"{type(e).__name__}: {e}"]
    if said:
        print(said)
    elif why:
        print(f"The to-do of the additive mode could not be computed here: {why[0][:200]} "
              "(`references/workstation.md` says what the framework's scripts need).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
