#!/usr/bin/env python3
"""Build every fixture the evals run against, into `build/`.

    python evals/fixtures/make.py            all of them
    python evals/fixtures/make.py release    one

WHY GENERATORS AND NOT THE FIXTURES THEMSELVES. Three times in the work that produced
these, a fixture was edited by hand and the change was gone at the next run of whatever
built it, because most of them start with `shutil.rmtree`. What is under `generators/` is
the source; `build/` is its output and is not tracked.

The release fixtures are the reason this cannot be a directory of files. Each one is a real
git repository with three commits, and `D-tampered-plan` turns on that history: the frozen
evaluation plan is recoverable only through `git show <frozen_at>:products/atlas/EVP.md`,
which is what the gate is supposed to do when the hash does not match. Committing a git
repository inside a git repository does not store the history, it stores a gitlink, and the
one thing that fixture exists to test would be the thing that did not survive.

What is under `static/` has no generator and never had one: two open registers and a
project with a corpus and no framework in it. Those are copied.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"

# Each generator takes a destination and writes one or more fixtures under it. `release`
# writes six and takes its own root, so it is called differently; the map records that
# rather than pretending they are uniform.
GENERATED = {
    "audit": ("audit.py", "audit"),
    "cycle": ("cycle.py", "cycle/fixture-base"),
    "requirement": ("requirement.py", "requirement/seed"),
    "release": ("release.py", None),          # writes its own tree, six of them
    "platform": ("platform.py", "platform"),
    "review": ("review.py", "review/gap"),
    "coherence": ("coherence.py", "coherence/contradiction"),
}
STATIC = {
    "resolve/ordering-a": "ordering-a",
    "resolve/coldstart": "coldstart",
    "start/corpus-project": "corpus-project",
}


def run(script: Path, *args: str) -> None:
    r = subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"{script.name} failed:\n{r.stdout}\n{r.stderr}")


def main() -> int:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    BUILD.mkdir(parents=True, exist_ok=True)

    for name, (script, dest) in GENERATED.items():
        if only and only != name:
            continue
        target = BUILD / (dest or name)
        shutil.rmtree(target, ignore_errors=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        run(HERE / "generators" / script, str(target))
        print(f"  {name:12} -> {target.relative_to(HERE)}")

    for dest, src in STATIC.items():
        if only and not dest.startswith(only):
            continue
        target = BUILD / dest
        shutil.rmtree(target, ignore_errors=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(HERE / "static" / src, target)
        print(f"  {dest:24} copied")

    # `ordering-b` is `ordering-a` with the entries permuted inside their sections, and it
    # is derived rather than stored so the two cannot drift apart. They were byte identical
    # once, which made the stability test unable to fail.
    if not only or only == "resolve":
        run(HERE / "generators" / "resolve_shuffle.py", str(BUILD / "resolve"))
        print("  resolve/ordering-b       derived from ordering-a")
    return 0


if __name__ == "__main__":
    sys.exit(main())
