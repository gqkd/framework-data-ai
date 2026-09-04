#!/usr/bin/env python3
"""A repository whose history says which documents were reread and which were only edited.

WHY THIS EXISTS RATHER THAN BORROWING THE RELEASE FIXTURES. They are git repositories with
dated commits, so they looked like a bench for `LC006` and they are not. Measured before this
file was written: thirty living documents across the six of them carried a gap between the
instant they attest and the commit that last touched them, and twenty-nine of the thirty were
the first commit importing everything after those instants. No story, no edit, nobody's
mistake. Reading that number as a measurement would have been the generator measuring itself,
and a check validated against it would have been validated against its own worst failure mode.

So the story is planted, and each commit can be said in one sentence:

    day 1   the first documented set of a product.
    day 12  the contract gains a column; the architecture and the brief follow it.
            None of the three is reread.
    day 20  the architecture is reread and stamped. The other two are not.

What that produces, and the three properties are the reason for the three commits:

    products/atlas/contracts/DC-001-orders.md   changed and never reread -> 11 days
    products/atlas/PBR.md                       changed and never reread -> 11 days
    products/atlas/ARC.md                       changed, then reread     -> nothing
    everything else                             only the import          -> nothing

The third is the negative case and it is the one that costs the check its floor: rereading a
document means editing it to write the date, so without an exclusion every honest review leaves
a gap of the minutes between the stamp and the commit. `ARC.md` is reread by a commit that
changes nothing but its `last_review` line, which is the shape that exclusion recognises, and
it has a real change before it so the comparison has somewhere to step back to.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

# The version is read and not written, for the reason `tests/selfcheck.py` asserts across the
# whole repository: a literal here is a line that goes wrong silently the day the framework
# moves, in a fixture whose subject is documents going out of date.
VERSION = yaml.safe_load(
    (Path(__file__).resolve().parents[3] / "schemas" / "artifact-types.yaml").read_text()
)["version"]

DAY1 = "2026-06-01 09:00"
DAY12 = "2026-06-12 11:30"
DAY20 = "2026-06-20 16:00"


def fm(**kw) -> str:
    return "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"


def write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def build(root: Path) -> None:
    if root.exists():
        import shutil
        shutil.rmtree(root)
    root.mkdir(parents=True)

    import os
    env = dict(os.environ, GIT_AUTHOR_NAME="g.quaglia", GIT_AUTHOR_EMAIL="g@example.com",
               GIT_COMMITTER_NAME="g.quaglia", GIT_COMMITTER_EMAIL="g@example.com")

    def git(*a, when=None):
        e = dict(env)
        if when:
            e["GIT_AUTHOR_DATE"] = e["GIT_COMMITTER_DATE"] = when
        r = subprocess.run(("git",) + a, cwd=root, capture_output=True, text=True, env=e)
        if r.returncode != 0:
            raise SystemExit(f"git {a} failed:\n{r.stderr}")
        return r.stdout.strip()

    def arc(reviewed: str, delta: str) -> str:
        return fm(schema="framework/architecture/v1", artifact_type="architecture",
                  lifecycle="living", status="active", products="[atlas]",
                  owners="[g.quaglia]", created=DAY1, last_review=reviewed,
                  verified_code="\n  product.backend: 4c1f9ae") + (
            "# Architecture\n\n"
            "<!-- section: current -->\n## Current\n\n"
            "The order service writes to the warehouse once a night.\n\n"
            "<!-- section: target -->\n## Target\n\n"
            "The same, with the order channel carried through.\n\n"
            "<!-- section: delta -->\n## Delta\n\n" + delta + "\n")

    def contract(columns: str) -> str:
        return fm(schema="framework/data-contract/v1", artifact_type="data-contract",
                  id="DC-001", lifecycle="living", status="active", version="1.0.0",
                  products="[atlas]", owners="[g.quaglia]", created=DAY1,
                  last_review=DAY1, consumers="[atlas]") + (
            "# DC-001 - Data contract: orders\n\n"
            "<!-- section: schema -->\n## Schema\n\n" + columns + "\n")

    def brief(capabilities: str) -> str:
        return fm(schema="framework/product-brief/v1", artifact_type="product-brief",
                  lifecycle="living", status="active", products="[atlas]",
                  owners="[g.quaglia]", created=DAY1, last_review=DAY1) + (
            "# Product brief\n\n"
            "<!-- section: what -->\n## What it does\n\n" + capabilities + "\n")

    # --- day 1: the first documented set --------------------------------------
    write(root, "framework.yaml", f"framework_version: {VERSION}\n")
    write(root, "AGENTS.md", fm(
        schema="framework/agents-control-plane/v1", artifact_type="agents-control-plane",
        lifecycle="living", status="active", owners="[g.quaglia]", created=DAY1,
        last_review=DAY1) + "# Control plane\n\nRead `products/atlas/OPEN.md` first.\n")
    write(root, "OPEN.md", fm(
        schema="framework/open-register/v1", artifact_type="open-register",
        lifecycle="living", status="active", owners="[g.quaglia]", created=DAY1,
        last_review=DAY1,
        entries="\n  OD-001:\n    status: open\n    cost_to_reverse: low\n"
                "    products: [all]\n    default_in_force: the nightly load, unchanged\n")
        + "# Open\n\n## Cost to reverse LOW\n\n### OD-001 - whether the channel is a column\n")
    write(root, "products/atlas/OPEN.md", fm(
        schema="framework/open-register/v1", artifact_type="open-register",
        lifecycle="living", status="active", owners="[g.quaglia]", created=DAY1,
        last_review=DAY1,
        entries="\n  OD-002:\n    status: open\n    cost_to_reverse: low\n"
                "    default_in_force: the channel is carried and not read\n")
        + "# Open\n\n## Cost to reverse LOW\n\n### OD-002 - who consumes the channel\n")
    write(root, "products/atlas/product.yaml", fm(
        schema="framework/product-manifest/v1", artifact_type="product-manifest",
        lifecycle="living", status="active", products="[atlas]", owners="[g.quaglia]",
        created=DAY1, last_review=DAY1,
        stage="\n  phase: F4\n  since: 2026-06-01",
        # `VER001` asks that a repository attested in an `ARC` be one the manifest records.
        # The bench has to be clean in every direction but the one it is planted in, or the
        # finding it exists to produce arrives inside a list of unrelated ones.
        code="\n  backend:\n    url: git@example.invalid:org/atlas-backend.git\n"
             "    contains: the order service and the nightly load\n"))
    write(root, "products/atlas/PBR.md", brief(
        "It reconciles orders against the warehouse once a night."))
    write(root, "products/atlas/ARC.md", arc(DAY1, "Nothing outstanding."))
    write(root, "products/atlas/contracts/DC-001-orders.md", contract(
        "| Column | Type | Meaning |\n|---|---|---|\n"
        "| order_id | integer | the order, as the source system numbers it |\n"
        "| placed_at | timestamp | when the order was accepted |"))
    git("init", "-q", "-b", "main")
    git("add", "-A")
    git("commit", "-q", "-m", "atlas: the first documented set", when=DAY1)

    # --- day 12: the contract gains a column, and two documents follow it ------
    # None of the three carries a new `last_review`, which is the whole planted defect: the
    # documents were changed, and what they now say has not been read by anybody.
    write(root, "products/atlas/contracts/DC-001-orders.md", contract(
        "| Column | Type | Meaning |\n|---|---|---|\n"
        "| order_id | integer | the order, as the source system numbers it |\n"
        "| placed_at | timestamp | when the order was accepted |\n"
        "| channel | string | where the order came from: web, phone, partner |"))
    write(root, "products/atlas/ARC.md", arc(
        DAY1, "The channel is carried but nothing reads it downstream yet."))
    write(root, "products/atlas/PBR.md", brief(
        "It reconciles orders against the warehouse once a night, and tells them apart by "
        "the channel they arrived through."))
    git("add", "-A")
    git("commit", "-q", "-m", "orders: carry the channel through", when=DAY12)

    # --- day 20: the architecture is reread, and only that ---------------------
    # The commit changes one line in one file and that line is the stamp. It is the shape a
    # reading takes, and the check has to see it as a reading rather than as a change, or
    # every honest review reports a gap of the minutes it took to commit.
    write(root, "products/atlas/ARC.md", arc(
        DAY20, "The channel is carried but nothing reads it downstream yet."))
    git("add", "-A")
    git("commit", "-q", "-m", "ARC: reread after the channel change", when=DAY20)


if __name__ == "__main__":
    build(Path(sys.argv[1]).resolve())
