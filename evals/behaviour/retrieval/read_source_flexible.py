#!/usr/bin/env python3
"""Flexible-sized, still instrumented reads; no forced 40-line pages."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
# In a trial this file is read_source.py, beside the unchanged v1 helper.
HELPER = HERE / ("read_source_v1.py" if Path(__file__).name == "read_source.py"
                 else "read_source.py")
spec = importlib.util.spec_from_file_location("flexible_reader_v1_helper", HELPER)
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)


def page(roots, scope, relative, start=1, end=None):
    if scope not in ("project", "framework") or type(start) is not int or start < 1:
        raise ValueError("invalid scope or starting line")
    if end is not None and (type(end) is not int or end < start):
        raise ValueError("invalid ending line")
    content = legacy.source_path(roots[scope], relative).read_bytes()
    lines = content.decode("utf-8").splitlines(keepends=True)
    if not lines or start > len(lines):
        raise ValueError("no source lines at this offset")
    last = len(lines) if end is None else min(end, len(lines))
    return {"schema": "retrieval/source-delivery/v1", "scope": scope, "path": relative,
            "file_sha256": hashlib.sha256(content).hexdigest(),
            "start_line": start, "end_line": last, "total_lines": len(lines),
            "next_line": last + 1 if last < len(lines) else None,
            "text": "".join(lines[start - 1:last])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scope", choices=("project", "framework"))
    parser.add_argument("path")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int)
    args = parser.parse_args()
    trial = Path(__file__).resolve().parent.parent
    try:
        value = page({name: trial / name for name in ("project", "framework")},
                     args.scope, args.path, args.start, args.end)
    except (ValueError, OSError) as error:
        parser.exit(2, f"Source unavailable: {error}\n")
    sys.stdout.write(legacy.frame(value))


if __name__ == "__main__":
    main()
