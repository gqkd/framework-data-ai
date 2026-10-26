#!/usr/bin/env python3
"""The write guard: a `PreToolUse` hook on Write, Edit and NotebookEdit that stops an agent
writing outside the place it works in.

THE RULE. An agent writes in the repository its session started in and in that repository's
worktrees, in the exchange between sessions, in what Claude Code itself has a session keep --
its scratchpad, the project's memory, the plans -- and in the folders the person lists in the
plugin's `allowed_dirs` option. For anything else it asks the person. Permission rules cannot
say this: an exception to a rule on what lies outside the project holds only against rules
relative to the current folder.

WHERE IT HOLDS. In the working folder only: a repository with `.framework/`, and the
repositories beside it in the same parent folder -- the code repositories, the worktrees
`work.py open` creates there. Anywhere else it lets every write through and says nothing: a
plugin's hooks run in every session of everyone who has the plugin enabled, and a session
that has nothing to do with the framework is not the framework's to fence. Inside, it holds
for every project, whatever version it pins and whatever its mode: it follows the plugin.

HOW IT ANSWERS. Exit 0 lets the call through; exit 2 stops it, and what it writes on stderr
is what the agent reads. Any other exit lets the call through as well, which is why the
guard uses the standard library alone, and why, once it knows it is in the working folder,
an error of its own stops the call instead of letting it pass. It does not see the shell:
`references/workstation.md` says what limits Bash.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

EXCHANGE = "_scambio"       # beside the repositories, the name references/workstation.md fixes
SESSIONS = Path(".framework") / "sessions.yaml"


def real(path: Path | str) -> Path:
    """The path with every link resolved, so that a link inside the repository pointing
    outside is outside. A file not written yet resolves through the folders that exist."""
    return Path(os.path.realpath(os.path.expanduser(str(path))))


def repository(start: Path) -> Path | None:
    """The working tree that holds `start`: the nearest folder with a `.git`, file or folder."""
    for folder in (start, *start.parents):
        if (folder / ".git").exists():
            return folder
    return None


def in_working_folder(repo: Path) -> bool:
    """A repository with `.framework/`, or one beside such a repository. A folder beside it
    this user cannot look into is not one, rather than an error that would turn the guard off
    for every repository there; a parent folder nobody may list says nothing either way, and
    is taken as not a working folder."""
    def framework(folder: Path) -> bool:
        try:
            return (folder / ".framework").is_dir()
        except OSError:
            return False
    if framework(repo):
        return True
    try:
        siblings = sorted(repo.parent.iterdir())
    except OSError:
        return False
    return any(framework(s) for s in siblings)


def worktrees(repo: Path) -> list[Path]:
    """The repository's working trees, the main checkout among them, as git lists them; the
    repository alone when git cannot say."""
    try:
        r = subprocess.run(["git", "-C", str(repo), "worktree", "list", "--porcelain"],
                           capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return [repo]
    found = [Path(line[len("worktree "):]) for line in r.stdout.splitlines()
             if line.startswith("worktree ")] if r.returncode == 0 else []
    return found or [repo]


def exchanges(repo: Path) -> list[Path]:
    """`_scambio` beside the repository, and the place `.framework/sessions.yaml` declares, if
    another, each only as a folder beside the repository that is not a repository itself, once
    links are followed: `..`, a path further out, a repository beside, or a link to any of
    them would open what the guard closes. The declaration is read from the last commit of the
    session's branch, not from the file on disk, which the session may write with these very
    tools; a commit, which the shell makes, can still move it, as far as a folder beside: the
    shell is outside the guard anyway. Read with a pattern rather than a YAML parser, which
    the standard library does not have."""
    names = [EXCHANGE]
    try:
        r = subprocess.run(["git", "-C", str(repo), "show", f"HEAD:{SESSIONS.as_posix()}"],
                           capture_output=True, text=True, timeout=5)
        m = re.search(r"^exchange:[ \t]*(['\"]?)([^'\"#\n]+?)\1[ \t]*(?:#.*)?$", r.stdout, re.M)
        value = m.group(2).strip().rstrip("/") if r.returncode == 0 and m else ""
        if value.startswith("../") and re.fullmatch(r"[^/\\]+", value[3:]) \
                and value[3:] not in (".", ".."):
            names.append(value[3:])
    except (OSError, subprocess.SubprocessError):
        pass
    def repository_or_closed(place: Path) -> bool:
        try:
            return (place / ".git").exists()
        except OSError:     # one this user cannot look into is not taken for the exchange
            return True
    places = [real(repo.parent / name) for name in dict.fromkeys(names)]
    return [p for p in places if p.parent == real(repo.parent) and not repository_or_closed(p)]


def personal(raw: str | None, base: Path) -> list[Path]:
    """The folders of the plugin's `allowed_dirs` option, relative ones against the folder that
    holds the repositories. How Claude Code puts a list into one variable is not documented: a
    JSON list is read as one, anything else as one path per line, comma or path separator."""
    if not raw or not raw.strip():
        return []
    try:
        value = json.loads(raw)
    except ValueError:
        value = None
    items = value if isinstance(value, list) else re.split(f"[\n,{re.escape(os.pathsep)}]", raw)
    paths = [Path(os.path.expanduser(str(i).strip())) for i in items if str(i).strip()]
    return [p if p.is_absolute() else base / p for p in paths]


def slug(folder: str | Path) -> str:
    """How Claude Code names a project's folders: every character not a letter or a digit
    becomes `-`."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(folder))


def claude_writes(path: Path, data: dict, start: str, main: Path) -> bool:
    """What Claude Code itself has a session write with these tools: its scratchpad, the memory
    of its project and the plans. The scratchpad is the one the hook is given; when it is not
    given -- the session of the one live test, started with `-p`, was not given one -- it is
    where Claude Code's documentation says it goes on Linux and macOS, `claude-<uid>/<folder
    of the session>/<session>/scratchpad` in the temporary folder, and where
    `CLAUDE_CODE_TMPDIR` moves it, with or without `claude-<uid>`, which the documentation
    does not say. Windows has no uid: there only the scratchpad given counts. The memory is
    the project's, named after the main checkout, which the worktrees share, or after the
    folder the session started in: not the memory other projects load when they start."""
    scratch = [data.get("scratchpad_dir")]
    uid = getattr(os, "getuid", None)
    if data.get("session_id") and uid:
        tail = Path(slug(start), str(data["session_id"]), "scratchpad")
        moved = os.environ.get("CLAUDE_CODE_TMPDIR")
        scratch += ([Path(moved, f"claude-{uid()}", tail), Path(moved, tail)] if moved
                    else [Path(tempfile.gettempdir(), f"claude-{uid()}", tail)])
    if any(s and inside(path, real(s)) for s in scratch):
        return True
    config = real(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    if inside(path, config / "plans"):
        return True
    return any(inside(path, config / "projects" / slug(p) / "memory") for p in {main, start})


def inside(path: Path, folder: Path) -> bool:
    return path == folder or folder in path.parents


def decide(data: dict, start: str, repo: Path) -> int:
    given = data.get("tool_input") or {}
    target = given.get("file_path") or given.get("notebook_path")
    if not target:
        print("The framework's write guard found no path in this call, and stops it: ask the "
              "person.", file=sys.stderr)
        return 2
    path = real(Path(start, os.path.expanduser(str(target))))
    trees, exchange = worktrees(repo), exchanges(repo)
    places = [*trees, *exchange,
              *personal(os.environ.get("CLAUDE_PLUGIN_OPTION_ALLOWED_DIRS"), repo.parent)]
    if claude_writes(path, data, start, trees[0]) or any(inside(path, real(p)) for p in places):
        return 0
    print(f"The framework's write guard stops this write: {path} is outside what this session "
          f"may write. It may write in {repo} and its worktrees, in the exchange "
          f"({', '.join(map(str, exchange)) or 'none here'}), in what Claude Code keeps for the "
          "session and in the folders of the plugin option `allowed_dirs`. Do not write it "
          f"another way -- through the shell, a copy, or a change to `{SESSIONS.as_posix()}` "
          "-- ask the person, who can open a session in that folder or add it to "
          "`allowed_dirs`.",
          file=sys.stderr)
    return 2


def main() -> int:
    try:
        data = json.load(sys.stdin)
        start = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
        repo = repository(real(start))
        if repo is None or not in_working_folder(repo):
            return 0
    except Exception:       # not knowing where it is, it is not the guard's place to stop
        return 0
    try:
        return decide(data, start, repo)
    except Exception as e:  # inside the working folder, a write nobody judged is not let through
        print(f"The framework's write guard could not judge this write "
              f"({type(e).__name__}: {e}), and stops it: ask the person.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
