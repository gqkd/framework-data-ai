#!/usr/bin/env python3
"""G0 source-discovery qualification, without models or semantic answer grading.

Execute identical literal seeds against one reconstructed candidate runtime with
hops=0/2. Query results are persisted before consulting oracle source groups.
This is NOT the isolated agent ablation: hops=0 can still export seed-to-seed edges.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
MANIFEST = "2c52d59b39b5267b8ec2c2b1a14d8e9e4b2b1dac8cf96318f0e18cabaeb403cc"
ORACLE = "717c5ff6ac3480316d0b9f181eb96c3ee4223fed1968d9e85f8f515635a9d758"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")


def dataset_module():
    spec = importlib.util.spec_from_file_location("graph_g0_dataset", HERE / "prepare.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_seeds(seeds):
    if (seeds.get("schema") != "framework/graph-ablation-seeds/v1"
            or seeds.get("engine") != "literal"
            or seeds.get("control_hops") != 0 or seeds.get("graph_hops") != 2
            or seeds.get("limit") != 20 or seeds.get("relations") != "runtime default"
            or set(seeds.get("questions", {})) != {"R007", "R013", "R019", "R022"}):
        raise ValueError("Unexpected preregistered retrieval policy")
    for item in seeds["questions"].values():
        if not item.get("terms") or any(not isinstance(t, str) or not t.strip()
                                        for t in item["terms"]):
            raise ValueError("Every seed must be nonempty text")


def request_args(project, term, hops, seeds):
    # Deliberately receives no oracle/case/source requirements.
    return ["query", "--root", str(project), "--text", term, "--search-engine", seeds["engine"],
            "--limit", str(seeds["limit"]), "--hops", str(hops)]


def decode_result(returncode, stdout):
    if returncode not in (0, 1):
        raise ValueError(f"Engine unavailable or failed: exit={returncode}")
    value = json.loads(stdout)
    if not isinstance(value, dict) or value.get("coverage") not in ("available", "partial"):
        raise ValueError("Engine did not report usable coverage")
    if (returncode == 1) != (value["coverage"] == "partial"):
        raise ValueError("Exit status/coverage mismatch")
    return value


def selected_document_paths(result):
    # Provenance sources are NOT discovered documents. Count selected document
    # nodes only and verify that they also have exported document bodies.
    nodes = {n["id"]: n["data"]["path"] for n in result["nodes"]
             if n["kind"] == "document"}
    body_nodes = {d["node"] for d in result["documents"]}
    if set(nodes) != body_nodes:
        raise ValueError("Selected documents and exported body identities differ")
    return set(nodes.values())


def source_group_score(case, sources, found):
    groups = [{sources[key]["path"] for key in group} for group in case["sources"]]
    covered = [i for i, paths in enumerate(groups) if found & paths]
    return {"covered_groups": covered, "total_groups": len(groups),
            "missing_groups": [sorted(paths) for i, paths in enumerate(groups) if i not in covered],
            "non_required_documents": sorted(found - set().union(*groups))}


def summarize(result):
    return {"snapshot": result["snapshot"], "coverage": result["coverage"],
            "truncated": result["truncated"], "selection_status": result["selection_status"],
            "documents": sorted(selected_document_paths(result)),
            "nodes": len(result["nodes"]), "edges": len(result["edges"]),
            "traversed_nodes": sum(bool(p["steps"]) for p in result["paths"]),
            "body_characters_exported": sum(len(d["body"]) for d in result["documents"]),
            "gaps": len(result["gaps"])}


def absent_output(output, source):
    if (not output.is_absolute() or output.exists() or output.is_symlink()
            or any(p.is_symlink() for p in output.parents)
            or output.resolve().is_relative_to(source.resolve())
            or output.resolve().is_relative_to(HERE.parents[2].resolve())):
        raise ValueError("Output must be absent, outside input/framework, without symlink parents")


def qualify(source, output, seeds_path):
    absent_output(output, source)
    seeds_bytes = seeds_path.read_bytes()
    seeds = json.loads(seeds_bytes)
    validate_seeds(seeds)
    manifest_bytes = (source / "evaluator/manifest.json").read_bytes()
    if sha(manifest_bytes) != MANIFEST:
        raise ValueError("Unrecognized frozen manifest")
    manifest = json.loads(manifest_bytes)
    dataset = dataset_module()
    original_inventory = dataset.inventory(source)
    output.mkdir(parents=True)
    save(output / "seeds.json", seeds)
    observations = {}
    receipts = []
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1",
               GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null", GIT_OPTIONAL_LOCKS="0")
    with tempfile.TemporaryDirectory(prefix="graph-ablation-g0-") as temporary:
        regenerated = Path(temporary) / "prepared"
        dataset.prepare(regenerated, manifest["versions"]["A"]["commit"],
                        manifest["versions"]["B"]["commit"])
        if original_inventory != dataset.inventory(regenerated):
            raise ValueError("Frozen input differs from reconstructed authored fixture")
        # Only execute the regenerated runtime, never a caller-supplied checkout.
        project = regenerated / "arms/B/project"
        runtime = regenerated / "arms/B/framework"
        initial = dataset.inventory(regenerated)

        def execute(label, args):
            command = [sys.executable, "-B", str(runtime / "memory.py"), *args]
            proc = subprocess.run(command, cwd=project, env=env, capture_output=True)
            (output / f"{label}.stdout.json").write_bytes(proc.stdout)
            (output / f"{label}.stderr.txt").write_bytes(proc.stderr)
            value = decode_result(proc.returncode, proc.stdout)
            receipts.append({"label": label, "command": command, "exit_code": proc.returncode,
                             "stdout_sha256": sha(proc.stdout), "stderr_sha256": sha(proc.stderr)})
            return value, proc.stdout

        graph1, bytes1 = execute("build-1", ["build", "--root", str(project), "--dry-run", "--export"])
        graph2, bytes2 = execute("build-2", ["build", "--root", str(project), "--dry-run", "--export"])
        if bytes1 != bytes2:
            raise ValueError("Graph exports are not byte-identical")
        for qid, item in seeds["questions"].items():
            observations[qid] = {}
            for condition, hops in (("S", seeds["control_hops"]), ("G", seeds["graph_hops"])):
                observations[qid][condition] = []
                for index, term in enumerate(item["terms"]):
                    result, _ = execute(f"{qid}-{condition}-{index}", request_args(project, term, hops, seeds))
                    if result["snapshot"] != graph1["snapshot"]:
                        raise ValueError("Query/build snapshot mismatch")
                    observations[qid][condition].append(summarize(result))
        if initial != dataset.inventory(regenerated) or original_inventory != dataset.inventory(source):
            raise ValueError("Input mutated during qualification")

    # The oracle never participates in seed construction or engine invocations.
    oracle_bytes = (source / "evaluator/oracle.json").read_bytes()
    if sha(oracle_bytes) != ORACLE:
        raise ValueError("Oracle hash changed")
    oracle = json.loads(oracle_bytes)
    rows = []
    for qid, conditions in observations.items():
        selected = {arm: set().union(*(set(r["documents"]) for r in results))
                    for arm, results in conditions.items()}
        scores = {arm: source_group_score(oracle["cases"][qid], oracle["sources"], paths)
                  for arm, paths in selected.items()}
        if not selected["S"] <= selected["G"]:
            raise ValueError("Graph lost seed documents")
        new_groups = sorted(set(scores["G"]["covered_groups"]) - set(scores["S"]["covered_groups"]))
        rows.append({"question": qid, "observations": conditions, "scores": scores,
                     "additional_documents": sorted(selected["G"] - selected["S"]),
                     "additional_required_groups": new_groups,
                     "useful_source_discovery_delta": bool(new_groups)})
    useful = sum(row["useful_source_discovery_delta"] for row in rows)
    report = {"schema": "framework/graph-ablation-qualification/v1", "model_invocations": 0,
              "scope": "Source discovery only, not comprehension, quality or agent isolation",
              "manifest_sha256": MANIFEST, "oracle_sha256": ORACLE,
              "seeds_sha256": sha(seeds_bytes), "candidate": manifest["versions"]["B"],
              "generator_sha256": sha(Path(__file__).read_bytes()),
              "dataset_generator_sha256": sha((HERE / "prepare.py").read_bytes()),
              "runtime_inventory_sha256": sha(dataset.canonical(manifest["arms"]["B"]["runtime_files"])),
              "byte_identical_builds": True, "inputs_unchanged": True,
              "graph": {"snapshot": graph1["snapshot"], "nodes": len(graph1["nodes"]),
                        "edges": len(graph1["edges"]), "gaps": len(graph1["gaps"])},
              "cases_with_additional_required_groups": useful, "cases": len(rows),
              "has_useful_and_no_useful_cases": 0 < useful < len(rows),
              "agent_ablation_ready": False,
              "remaining_gates": ["Technically isolate provided graph navigation; zero hops still exports edges",
                                  "Prepare paired same-runtime trials and qualify their sandbox",
                                  "Persist intervention protocol and grading provenance before model dispatch"],
              "limitations": ["Manually normalized development seeds; not fresh blind retrieval",
                              "A missing source group is not proof that the answer is impossible",
                              "Documentary graph only; code files remain available through direct reading",
                              "Exported document paths/bodies do not prove model receipt, reading or understanding",
                              "Truncation and mapping gaps limit interpretation, not silently counted as complete"],
              "questions": rows, "receipts": receipts}
    save(output / "qualification.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seeds", type=Path, default=HERE / "GRAPH-ABLATION-SEEDS.json")
    args = parser.parse_args()
    try:
        result = qualify(args.prepared_root, args.output, args.seeds)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Qualification failed; no model invoked: {error}\n")
    print(json.dumps({key: result[key] for key in ("model_invocations", "byte_identical_builds",
          "inputs_unchanged", "cases_with_additional_required_groups", "cases", "agent_ablation_ready")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
