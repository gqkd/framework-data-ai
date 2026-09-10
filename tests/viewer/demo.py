#!/usr/bin/env python3
"""Generate ONLY synthetic viewer QA exports. Refuses to reuse an existing destination."""
import argparse
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "memory"))
import test_code_provider as cp
import test_documentary as doc
from test_viewer import viewer
import yaml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--enola", type=Path, required=True, help="already installed pinned provider")
    args = parser.parse_args()
    destination = args.destination.absolute()
    if destination.exists():
        raise ValueError("synthetic viewer destination already exists")
    cp.fixture.build(destination / "fixtures")
    root = destination / "fixtures/multi-repo"
    overlays = yaml.safe_load((cp.ROOT / "tests/fixtures/memory/phase2-metadata.yaml").read_text())
    for path, fields in overlays["multi-repo"].items():
        doc.amend(root / path, **fields)
    cp.CodeMemory.bind(None, root, {cp.API:"code/alpha-api",cp.WORKER:"code/beta-worker",cp.RULES:"code/shared-rules"})
    snapshot = cp.snapshots.capture(root)
    graph = cp.graphs.build(snapshot)
    built = cp.code.build_code(snapshot, graph, cp.enola.EnolaProvider(args.enola))
    built.publish()
    code = dict(graph=built.graph,inputs=built.inputs)
    source = graph["sources"][0]
    hypotheses = [dict(claim='Synthetic hypothesis </script><script>globalThis.pwned=true</script>',
                       provenance=dict(source_kind="document",assertion_method="inferred",confidence=0.4,
                                       rationale="Synthetic injection fixture; never a constraint",
                                       sources=[dict(source=source["id"],start_line=1,end_line=1)]))]
    cases = [("documents", root, viewer.export(snapshot,graph)),
             ("mapping", root, viewer.export(snapshot,graph,code=code,hypotheses=hypotheses))]
    changed = root / "products/alpha/PBR.md"
    changed.write_text(changed.read_text() + "\nSynthetic revision for the mismatch case.\n")
    snapshot = cp.snapshots.capture(root)
    cases.append(("mismatch",root,viewer.export(snapshot,cp.graphs.build(snapshot),code=code)))
    for name, project, report in cases:
        target = destination / "preview" / name
        target.mkdir(parents=True)
        source = project / report["output"]
        shutil.copy2(source,target/"index.html")
        shutil.copy2(source.with_name("manifest.json"),target/"manifest.json")
        print(name, target/"index.html", "code:", report["code_coverage"])
    print("Serve only",destination/"preview")


if __name__ == "__main__":
    main()
