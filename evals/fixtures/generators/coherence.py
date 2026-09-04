#!/usr/bin/env python3
"""A repository where one document cites a decision and contradicts it, and another does not.

WHAT IT MEASURES, WHICH NO CHECK CAN. The validator verifies that a link exists: that
`derives_from` points at something, that the `DEC` is there, that the status is in its
enumeration. It cannot verify that the two ends say the same thing, and the second pass of
`audit` is that question. That pass was run with two filters, and a document that names a
decision and contradicts it passes both: the citation resolves, so "does B name A" is
satisfied, and if the contradiction is older than the window, recency never looks.

So this fixture plants exactly that shape, and its opposite beside it:

    decisions/DEC-001-warehouse.md   accepted, scope architecture, and its first section
                                     heading is a one-line statement of what it decided.
    products/atlas/ARC.md            cites DEC-001 by name, in the section the decision
                                     governs, and describes the arrangement the decision
                                     replaced. Both filters pass. Nothing reports it.
    decisions/DEC-002-retention.md   accepted, scope product.
    products/atlas/PBR.md            cites DEC-002 and says what it decided. The negative
                                     case, and it is here because a pass that reports every
                                     pair it looks at has not read anything.

The dates are the other half of the plant: `DEC-001` is accepted six weeks before the
architecture was last reviewed, so a pass comparing against the decisions accepted since the
document last moved does not reach it. A fixture where the contradiction is recent would
measure the easy filter.

The validator reports nothing here. That is deliberate and it is the point: a run that ends
with "no findings" and stops has not done the second pass, and this is the repository where
the difference between the two is visible.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml

VERSION = yaml.safe_load(
    (Path(__file__).resolve().parents[3] / "schemas" / "artifact-types.yaml").read_text()
)["version"]

DAY = "2026-05-04 09:00"

# Distinct instants, and not one batch stamp: `LC005` reports three living documents sharing a
# minute, correctly, and a fixture whose subject is a reading has no business carrying the
# shape of a reading that did not happen.
LATER = "2026-06-15 10:00"
REVIEWED = {"agents": "2026-06-15 10:00", "open": "2026-06-15 11:20",
            "product_open": "2026-06-15 14:05", "manifest": "2026-06-16 09:40",
            "arc": "2026-06-16 11:15", "pbr": "2026-06-17 15:30"}


def fm(**kw) -> str:
    return "---\n" + "\n".join(f"{k}: {v}" for k, v in kw.items()) + "\n---\n\n"


def write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def build(root: Path) -> None:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)

    write(root, "framework.yaml", f"framework_version: {VERSION}\n")
    write(root, "AGENTS.md", fm(
        schema="framework/agents-control-plane/v1", artifact_type="agents-control-plane",
        lifecycle="living", status="active", owners="[g.quaglia]", created=DAY,
        last_review=REVIEWED["agents"]) + "# Control plane\n\nRead `products/atlas/OPEN.md` first.\n")
    write(root, "OPEN.md", fm(
        schema="framework/open-register/v1", artifact_type="open-register",
        lifecycle="living", status="active", owners="[g.quaglia]", created=DAY,
        last_review=REVIEWED["open"],
        entries="\n  OD-001:\n    status: open\n    cost_to_reverse: low\n"
                "    products: [all]\n    default_in_force: one warehouse for everything\n")
        + "# Open\n\n## Cost to reverse LOW\n\n### OD-001 - whether a second warehouse is worth it\n")
    write(root, "products/atlas/OPEN.md", fm(
        schema="framework/open-register/v1", artifact_type="open-register",
        lifecycle="living", status="active", owners="[g.quaglia]", created=DAY,
        last_review=REVIEWED["product_open"],
        entries="\n  OD-002:\n    status: open\n    cost_to_reverse: low\n"
                "    default_in_force: the nightly load, unchanged\n")
        + "# Open\n\n## Cost to reverse LOW\n\n### OD-002 - how often the load runs\n")
    write(root, "products/atlas/product.yaml", fm(
        schema="framework/product-manifest/v1", artifact_type="product-manifest",
        lifecycle="living", status="active", products="[atlas]", owners="[g.quaglia]",
        created=DAY, last_review=REVIEWED["manifest"],
        stage="\n  phase: F4\n  since: 2026-05-04",
        code="\n  backend:\n    url: git@example.invalid:org/atlas-backend.git\n"
             "    contains: the loader and the models\n"))

    # THE DECISION, AND ITS FIRST SECTION HEADING IS A ONE-LINE STATEMENT OF WHAT IT DECIDED.
    # That is what makes the contradiction findable by a reading: the issue that produced this
    # fixture observed that a decision's `§` headings are short, and that a contradiction of
    # this kind is visible from the heading alone.
    write(root, "decisions/DEC-001-warehouse.md", fm(
        schema="framework/decision-record/v1", artifact_type="decision-record",
        id="DEC-001", lifecycle="immutable", status="accepted", scope="architecture",
        products="[atlas]", owners="[g.quaglia]", created="2026-05-04",
        supersedes="null", leaves_open="[]") + (
        "# DEC-001 - Orders reach the warehouse by nightly batch\n\n"
        "## 1 - The queue is removed and the batch is the only path\n\n"
        "The order service wrote to a message queue and the warehouse consumed it. That is\n"
        "gone: the loader reads the source tables once a night and nothing streams.\n\n"
        "## 2 - Why\n\n"
        "One path is one thing to operate, and the queue served a latency nobody asked for.\n"))

    write(root, "decisions/DEC-002-retention.md", fm(
        schema="framework/decision-record/v1", artifact_type="decision-record",
        id="DEC-002", lifecycle="immutable", status="accepted", scope="product",
        products="[atlas]", owners="[g.quaglia]", created="2026-05-06",
        supersedes="null", leaves_open="[]") + (
        "# DEC-002 - Orders are kept for twenty-four months\n\n"
        "## 1 - Twenty-four months, and then they go\n\n"
        "Anything older is aggregated and the rows are dropped.\n"))

    # THE CONTRADICTION. It cites `DEC-001` by name, in the section that decision governs, and
    # describes the arrangement `DEC-001 §1` removed. The citation resolves, so the filter
    # that asks whether the document names the decision is satisfied by the very sentence that
    # contradicts it.
    write(root, "products/atlas/ARC.md", fm(
        schema="framework/architecture/v1", artifact_type="architecture",
        lifecycle="living", status="active", products="[atlas]", owners="[g.quaglia]",
        created=DAY, last_review=REVIEWED["arc"], derives_from="[DEC-001]",
        verified_code="\n  product.backend: 4c1f9ae") + (
        "# Architecture\n\n"
        "<!-- section: current -->\n## Current\n\n"
        "The order service publishes to the message queue, and the warehouse loader consumes\n"
        "it continuously. This follows `DEC-001`, which settled how orders reach the\n"
        "warehouse.\n\n"
        "<!-- section: target -->\n## Target\n\n"
        "The same, with the queue partitioned by region.\n\n"
        "<!-- section: delta -->\n## Delta\n\n"
        "Partitioning is not done.\n"))

    # THE NEGATIVE CASE. A pass that reports every pair it looks at has read nothing, so the
    # fixture has to contain a pair that agrees and is cited the same way.
    write(root, "products/atlas/PBR.md", fm(
        schema="framework/product-brief/v1", artifact_type="product-brief",
        lifecycle="living", status="active", products="[atlas]", owners="[g.quaglia]",
        created=DAY, last_review=REVIEWED["pbr"], derives_from="[DEC-002]") + (
        "# Product brief\n\n"
        "<!-- section: what -->\n## What it does\n\n"
        "It reconciles orders against the warehouse. Orders are kept for twenty-four months\n"
        "and then aggregated, which is `DEC-002`.\n"))


if __name__ == "__main__":
    build(Path(sys.argv[1]).resolve())
