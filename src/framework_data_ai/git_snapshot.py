"""Read immutable Git objects, not worktrees, archives, filters or proposed executables."""
from dataclasses import dataclass
from pathlib import Path
import re

from .memory.code_sources import git, safe_path, MAX_FILE, MAX_TOTAL, MAX_FILES
from .workspace import MemoryInputError


def commit(root, value):
    if not isinstance(value, str) or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value):
        raise MemoryInputError("a full immutable commit ID is required")
    if git(root, "rev-parse", "--verify", value + "^{commit}").decode().strip() != value:
        raise MemoryInputError("revision is not an available commit")
    return value


def ancestor(root, earlier, later):
    commit(root, earlier)
    commit(root, later)
    # merge-base returns an immutable ID; unlike --is-ancestor, absence is not confused
    # with a subprocess/access error. Shallow or unrelated history fails closed.
    if git(root, "merge-base", earlier, later).decode().strip() != earlier:
        raise MemoryInputError("the selected mandate commit is outside the approved history")


def relative(value):
    safe_path(value)
    if any(ord(c) < 32 for c in value) or any(p.casefold() == ".git" for p in value.split("/")):
        raise MemoryInputError("unsafe Git source path")
    return value


@dataclass
class GitSnapshot:
    root: Path
    revision: str
    entries: dict

    @classmethod
    def open(cls, root, revision):
        root = Path(root).resolve()
        commit(root, revision)
        entries = {}
        for row in git(root, "ls-tree", "-r", "-z", revision).split(b"\0"):
            if not row:
                continue
            header, raw = row.split(b"\t", 1)
            mode, kind, oid = header.decode("ascii").split()
            path = relative(raw.decode("utf-8"))
            if path in entries:
                raise MemoryInputError("duplicate Git path")
            entries[path] = (mode, kind, oid)
        if len(entries) > MAX_FILES:
            raise MemoryInputError("Git source inventory exceeds the bound")
        return cls(root, revision, entries)

    def read(self, path):
        entry = self.entries.get(relative(path))
        if not entry or entry[0] not in ("100644", "100755") or entry[1] != "blob":
            raise MemoryInputError("required Git source is missing, a link or a submodule")
        return git(self.root, "cat-file", "blob", entry[2], limit=MAX_FILE)

    def changed(self, after):
        return sorted(p for p in self.entries.keys() | after.entries.keys()
                      if self.entries.get(p) != after.entries.get(p))
