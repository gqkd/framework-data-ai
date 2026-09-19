#!/usr/bin/env python3
"""Small, identical source-delivery adapter for both synthetic benchmark arms."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys

BEGIN = "<<<retrieval-source-v1>>>"
END = "<<<end-retrieval-source-v1>>>"
MAX_FILE_BYTES = 2_000_000
MAX_PAGE_BYTES = 4000
MAX_LINES = 40


def source_path(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise ValueError("invalid relative source path")
    path = PurePosixPath(relative)
    if path.is_absolute() or str(path) != relative or relative == "." or any(
            part in ("..", ".git", "evaluator") for part in path.parts):
        raise ValueError("invalid relative source path")
    target = root / relative
    if root.is_symlink() or any(p.is_symlink() for p in [target, *target.parents]):
        raise ValueError("source links are not supported")
    if not target.resolve().is_relative_to(root.resolve()) or not target.is_file():
        raise ValueError("source is not a regular file inside the assigned root")
    if target.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("source exceeds reader size limit")
    return target


def page(roots, scope, relative, start=1):
    if scope not in ("project", "framework") or type(start) is not int or start < 1:
        raise ValueError("invalid scope or starting line")
    content = source_path(roots[scope], relative).read_bytes()
    lines = content.decode("utf-8").splitlines(keepends=True)
    if not lines or start > len(lines):
        raise ValueError("no source lines at this offset")
    selected, size = [], 0
    for line in lines[start - 1:start - 1 + MAX_LINES]:
        length = len(line.encode("utf-8"))
        if size + length > MAX_PAGE_BYTES:
            break
        selected.append(line)
        size += length
    if not selected:
        raise ValueError("single source line exceeds page limit; no reading claimed")
    end = start + len(selected) - 1
    return {"schema": "retrieval/source-delivery/v1", "scope": scope, "path": relative,
            "file_sha256": hashlib.sha256(content).hexdigest(),
            "start_line": start, "end_line": end, "total_lines": len(lines),
            "next_line": end + 1 if end < len(lines) else None, "text": "".join(selected)}


def frame(value):
    return BEGIN + "\n" + json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n" + END + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scope", choices=("project", "framework"))
    parser.add_argument("path")
    parser.add_argument("--start", type=int, default=1)
    args = parser.parse_args()
    # This standalone file is copied to TRIAL/tools; no configurable outside root.
    trial = Path(__file__).resolve().parent.parent
    try:
        result = page({name: trial / name for name in ("project", "framework")},
                      args.scope, args.path, args.start)
    except (ValueError, OSError) as error:
        parser.exit(2, f"Source unavailable: {error}\n")
    sys.stdout.write(frame(result))


if __name__ == "__main__":
    main()
