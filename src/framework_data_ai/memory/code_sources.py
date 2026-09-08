"""Bounded, explicit Git/worktree capture. Never execute code, filters, hooks or checkout."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath
import re
import stat

from ..snapshots import ConcurrentChange
from ..workspace import MemoryInputError
from .models import digest

MAX_FILE = 2_000_000
MAX_TOTAL = 20_000_000
MAX_FILES = 5000


def safe_path(value: str) -> str:
    if (not isinstance(value, str) or not value or "\\" in value or ":" in value
            or "\0" in value or value.startswith("/") or "//" in value
            or any(part in ("", ".", "..") for part in value.split("/"))):
        raise MemoryInputError("code path is not a safe repository-relative path")
    return value


def git(root: Path, *args, limit=MAX_TOTAL) -> bytes:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_OPTIONAL_LOCKS="0",
               GIT_TERMINAL_PROMPT="0", GIT_NO_REPLACE_OBJECTS="1")
    # Stream into bounded memory; neither commands nor stderr can inject local paths into output.
    from .providers.process import bounded_run
    result, output = bounded_run(["git", "--no-pager", "-c", "core.fsmonitor=false", "-C", str(root), *args],
                                 env=env, timeout=15, limit=limit)
    if result:
        raise MemoryInputError("code Git source is unavailable or the selected revision is invalid")
    return output


def file_bytes(root: Path, relative: str) -> bytes:
    parts = PurePosixPath(safe_path(relative)).parts
    # Resolve each directory through a held descriptor: a concurrent directory replacement
    # cannot redirect the file read through a symlink after a separate preflight check.
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    except OSError as error:
        if isinstance(error, FileNotFoundError):
            raise
        raise MemoryInputError("code source links and non-directory ancestors are not followed") from error
    finally:
        os.close(directory)
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise MemoryInputError("code source is not a regular file")
        data = stream.read(MAX_FILE + 1)
    if len(data) > MAX_FILE:
        raise MemoryInputError("code source exceeds the per-file byte limit")
    return data


@dataclass
class CodeCapture:
    root: Path
    mode: str
    revision: str | None
    include_untracked: bool
    files: dict[str, bytes]
    coverage: list[dict]
    inputs: dict

    def assert_unchanged(self):
        try:
            current = capture_code(self.root, mode=self.mode, revision=self.revision,
                                   include_untracked=self.include_untracked)
            if current.inputs == self.inputs:
                return
        except (MemoryInputError, OSError):
            pass
        raise ConcurrentChange("code sources or index changed; code snapshot not published")


def capture_code(root: Path, *, mode="worktree", revision=None, include_untracked=False) -> CodeCapture:
    if mode not in ("worktree", "git") or (mode == "git") != (revision is not None):
        raise MemoryInputError("Git observation requires an explicit revision; no HEAD fallback")
    # Pin a commit object, not a moving ref or an option parsed by Git.
    if revision is not None and not re.fullmatch(r"[0-9a-f]{40}(?:[0-9a-f]{24})?", revision):
        raise MemoryInputError("Git revision must be a full commit object ID")
    if include_untracked and mode == "git":
        raise MemoryInputError("untracked files do not belong to a Git revision")
    absolute = Path(os.path.abspath(root))
    if any(p.is_symlink() for p in (absolute, *absolute.parents)):
        raise MemoryInputError("code checkout bindings must not traverse symbolic links")
    root = absolute
    if not root.is_dir():
        raise MemoryInputError("bound code repository is missing")
    entries, files, coverage = {}, {}, []
    if mode == "git":
        commit = git(root, "rev-parse", "--verify", revision + "^{commit}").decode().strip()
        listing = git(root, "ls-tree", "-r", "-z", commit)
        for item in listing.split(b"\0"):
            if item:
                header, path = item.split(b"\t", 1)
                permissions, kind, oid = header.decode().split()
                entries[safe_path(path.decode())] = (permissions, oid)
        index_hash = None
    else:
        top = Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve()
        if top != root:
            raise MemoryInputError("binding is not the root of the declared Git checkout")
        commit = git(root, "rev-parse", "--verify", "HEAD").decode().strip()
        index = git(root, "ls-files", "--stage", "-z")
        index_hash = digest(index)
        for item in index.split(b"\0"):
            if item:
                header, path = item.split(b"\t", 1)
                permissions, oid, stage = header.decode().split()
                if stage != "0":
                    raise MemoryInputError("code index has unresolved merge stages")
                entries[safe_path(path.decode())] = (permissions, oid)
        untracked = git(root, "ls-files", "--others", "--exclude-standard", "-z")
        for item in untracked.split(b"\0"):
            if item:
                path = safe_path(item.decode())
                if include_untracked:
                    entries[path] = ("100644", None)
                else:
                    coverage.append(dict(path=path, status="excluded", reason="untracked-not-selected"))
    if len(entries) + len(coverage) > MAX_FILES:
        raise MemoryInputError("code inventory exceeds the file limit")
    total = 0
    for path, (permissions, oid) in sorted(entries.items()):
        if permissions not in ("100644", "100755"):
            coverage.append(dict(path=path, status="unavailable", reason="symlink-or-submodule"))
            continue
        if mode == "worktree":
            candidate = root / path
            if any(p.is_symlink() for p in (candidate, *candidate.parents)):
                raise MemoryInputError("code source links are not followed")
            if not candidate.exists():
                coverage.append(dict(path=path, status="unavailable", reason="worktree-file-missing"))
                continue
        if not path.endswith(".py"):
            coverage.append(dict(path=path, status="unsupported", reason="python-profile-only"))
            continue
        try:
            data = (git(root, "cat-file", "blob", oid, limit=MAX_FILE) if mode == "git"
                    else file_bytes(root, path))
        except FileNotFoundError:
            coverage.append(dict(path=path, status="unavailable", reason="worktree-file-missing"))
            continue
        total += len(data)
        if total > MAX_TOTAL:
            raise MemoryInputError("code capture exceeds the total byte limit")
        files[path] = data
    coverage.sort(key=lambda item: item["path"])
    inputs = dict(mode=mode, commit=commit, index_hash=index_hash, include_untracked=include_untracked,
                  inventory={p: list(v) for p, v in sorted(entries.items())}, coverage=coverage,
                  contents={p: digest(b) for p, b in sorted(files.items())})
    return CodeCapture(root, mode, revision, include_untracked, files, coverage, inputs)
