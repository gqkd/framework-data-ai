#!/usr/bin/env python3
"""Prepare and measure an explicitly authored graph calibration, without LLMs.

This is a controlled seed-to-neighbour probe, not a blind routing evaluation or
an isolated agent runner. Original retrieval fixtures and runtime are untouched.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
DEFINITIONS = HERE / "calibration"
CANDIDATE = "faaf42259c7b43dfecbd1c52df21b2c4788cfc50"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dataset = load_module("calibration_dataset", HERE / "prepare.py")
g0 = load_module("calibration_g0", HERE / "qualify_graph_ablation.py")


def definitions():
    corpus, cases, oracle = (dataset.read_yaml(DEFINITIONS / name) for name in
                             ("corpus.yaml", "cases.yaml", "oracle.yaml"))
    if {d["dataset_id"] for d in (corpus, cases, oracle)} != {"graph-calibration-v1"}:
        raise ValueError("Dataset identity mismatch")
    paths = [item["path"] for item in corpus["documents"]]
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate document path")
    for path in paths:
        dataset.relative_path(path)
    ids = [case["id"] for case in cases["cases"]]
    if len(set(ids)) != 4 or len(ids) != 4 or set(ids) != set(oracle["cases"]):
        raise ValueError("Expected four distinct calibration cases")
    policy = cases["policy"]
    if (policy["control_hops"], policy["graph_hops"], policy["limit"], policy["relations"]) != (
            0, 2, 20, "runtime default"):
        raise ValueError("Changed traversal policy")
    for case in cases["cases"]:
        expected = oracle["cases"][case["id"]]
        for path in [case["seed"], *case["expected_additional_paths"],
                     *case["expected_unreached_required_paths"], *expected["required_paths"]]:
            if path not in paths:
                raise ValueError("Unknown calibration source")
        if case["seed"] not in case["question"] or case["seed"] not in expected["required_paths"]:
            raise ValueError("Start source must be explicit in question and rubric")
        if not expected["must_include"] or not expected["must_not"]:
            raise ValueError("Incomplete author rubric")
    if oracle["review_status"] != "author-draft-pending-independent-review":
        raise ValueError("Do not manufacture independent approval in fixture definitions")
    return corpus, cases, oracle


def build_project(project, corpus, version):
    helper = dataset.load_generator()
    docs = helper.Documents(project)
    docs.base(tuple(corpus["products"]))
    for item in corpus["documents"]:
        docs.artifact(item["path"], item["kind"], item["body"],
                      lifecycle=item.get("lifecycle", "immutable"),
                      status=item.get("status", "accepted"), **item.get("fields", {}))
    helper.write(project, "framework.yaml", "framework_version: " + version +
                 "\nscan:\n  skip_dirs: [code]\n")


def query_args(project, case, hops, policy):
    # No expected paths, rubric statements or oracle are used in the request.
    return ["query", "--root", str(project), "--node", case["seed"],
            "--hops", str(hops), "--limit", str(policy["limit"])]


def navigation_packet(result, condition):
    if condition not in {"S", "G"}:
        raise ValueError("Unknown condition")
    paths = g0.selected_document_paths(result)
    if any(node["kind"] != "document" for node in result["nodes"]):
        raise ValueError("This calibration expects document-only navigation")
    nodes = {node["id"]: node["data"]["path"] for node in result["nodes"]}
    packet = {
        "schema": "framework/graph-calibration-navigation/v1",
        "purpose": "Navigation only; read the original sources before answering.",
        "coverage": result["coverage"], "mapping_complete": result["mapping_complete"],
        "truncated": result["truncated"], "snapshot": result["snapshot"],
        "documents": sorted(paths), "edges": [], "paths": [],
        "limitations": ["Not authorization, implementation evidence or exhaustive impact",
                        "A missing edge is not absence of a constraint",
                        "Document bodies and metadata remain available in the identical source corpus"],
    }
    if condition == "G":
        source_paths = {source["id"]: source["path"] for source in result["sources"]}
        for edge in result["edges"]:
            proof = edge["provenance"]
            packet["edges"].append({
                "id": edge["id"], "relation": edge["relation"],
                "source": nodes[edge["source"]], "target": nodes[edge["target"]],
                "assertion_method": proof["assertion_method"],
                "sources": [dict(path=source_paths[loc["source"]],
                                 start_line=loc["start_line"], end_line=loc["end_line"])
                            for loc in proof["sources"]],
                **({"rule": proof["rule"]} if "rule" in proof else {}),
            })
        packet["paths"] = [dict(document=nodes[path["node"]], steps=path["steps"])
                           for path in result["paths"]]
    # Never export bodies, oracle labels, expected effects, or evaluative hints.
    return packet


def assess(case, oracle_case, results):
    found = {arm: g0.selected_document_paths(result) for arm, result in results.items()}
    required = set(oracle_case["required_paths"])
    expected_added = set(case["expected_additional_paths"])
    expected_missing = set(case["expected_unreached_required_paths"])
    checks = {
        "control_is_exact_seed": found["S"] == {case["seed"]},
        "additional_paths_match": found["G"] - found["S"] == expected_added,
        "missing_required_match": required - found["G"] == expected_missing,
        "seed_preserved": found["S"] <= found["G"],
        "not_truncated": not any(result["truncated"] for result in results.values()),
        "same_snapshot": results["S"]["snapshot"] == results["G"]["snapshot"],
        "no_extra_discovery": found["G"] <= required,
    }
    return {"question": case["id"], "checks": checks, "passed": all(checks.values()),
            "required_paths": sorted(required),
            "coverage": {arm: {"found_required": len(paths & required), "of": len(required),
                                "documents": sorted(paths)}
                         for arm, paths in found.items()},
            "additional_required": sorted((found["G"] - found["S"]) & required),
            "missing_required": sorted(required - found["G"])}


def prepare_and_measure(output):
    g0.absent_output(output, DEFINITIONS)
    corpus, cases, oracle = definitions()
    version = dataset.framework_info(CANDIDATE)
    output.mkdir(parents=True)
    evaluator = output / "evaluator"
    evaluator.mkdir()
    source_files = [DEFINITIONS / name for name in ("corpus.yaml", "cases.yaml", "oracle.yaml")]
    source_files += [Path(__file__), HERE / "prepare.py", HERE / "qualify_graph_ablation.py",
                     dataset.ROOT / "evals/fixtures/generators/memory.py"]
    inputs = {path.relative_to(dataset.ROOT).as_posix(): dataset.digest(path.read_bytes())
              for path in source_files}
    # Persist expected effects and input identities before invoking the engine.
    dataset.save(evaluator / "declared-before-measurement.json", {
        "dataset_id": corpus["dataset_id"], "candidate": version, "inputs": inputs,
        "cases": cases, "oracle": oracle, "model_invocations": 0,
        "status": "author-expectations-not-independent-review"})
    for name in ("corpus.yaml", "cases.yaml", "oracle.yaml"):
        shutil.copyfile(DEFINITIONS / name, evaluator / name)
    build_project(output / "arms/S/project", corpus, version["version"])
    dataset.export_runtime(CANDIDATE, output / "arms/S/framework")
    (output / "arms/G").mkdir(parents=True)
    for area in ("project", "framework"):
        shutil.copytree(output / "arms/S" / area, output / "arms/G" / area)
    before = {arm: {area: dataset.inventory(output / "arms" / arm / area)
                    for area in ("project", "framework")} for arm in ("S", "G")}
    if before["S"] != before["G"]:
        raise ValueError("Arm source/runtime parity failed")
    dataset.save(evaluator / "before.json", before)
    receipts = []
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1",
               GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null", GIT_OPTIONAL_LOCKS="0")

    def execute(label, arm, entry, args, *, engine=True):
        project = output / "arms" / arm / "project"
        runtime = output / "arms" / arm / "framework"
        command = [sys.executable, "-B", str(runtime / entry), *args]
        done = subprocess.run(command, cwd=project, env=env, capture_output=True)
        (evaluator / (label + ".stdout.json")).write_bytes(done.stdout)
        (evaluator / (label + ".stderr.txt")).write_bytes(done.stderr)
        receipts.append({"label": label, "command": command, "exit_code": done.returncode,
                         "stdout_sha256": dataset.digest(done.stdout),
                         "stderr_sha256": dataset.digest(done.stderr)})
        if engine:
            return g0.decode_result(done.returncode, done.stdout), done.stdout
        if done.returncode:
            raise ValueError(f"Validator did not pass: see {label}.stdout.json")
        return json.loads(done.stdout), done.stdout

    graphs = {}
    for arm in ("S", "G"):
        project = output / "arms" / arm / "project"
        execute("validate-" + arm, arm, "skills/audit/scripts/validate.py",
                ["--root", str(project), "--json"], engine=False)
        graphs[arm] = execute("build-" + arm, arm, "memory.py",
                              ["build", "--root", str(project), "--dry-run", "--export"])
    if graphs["S"][1] != graphs["G"][1]:
        raise ValueError("Graph bytes differ between identical arms")
    graph = graphs["S"][0]
    if graph["issues"]:
        raise ValueError("Unexpected graph issue; inspect export before proceeding")
    responses = {}
    for case in cases["cases"]:
        responses[case["id"]] = {}
        for arm, hops in (("S", cases["policy"]["control_hops"]), ("G", cases["policy"]["graph_hops"])):
            project = output / "arms" / arm / "project"
            result, _ = execute(case["id"] + "-" + arm, arm, "memory.py",
                                query_args(project, case, hops, cases["policy"]))
            if result["snapshot"] != graph["snapshot"]:
                raise ValueError("Query/build snapshot mismatch")
            responses[case["id"]][arm] = result
            dataset.save(output / "arms" / arm / "navigation" / (case["id"] + ".json"),
                         navigation_packet(result, arm))
    # Assertions are evaluator-only; neither request builder nor packet sees oracle.
    rows = [assess(case, oracle["cases"][case["id"]], responses[case["id"]])
            for case in cases["cases"]]
    after = {arm: {area: dataset.inventory(output / "arms" / arm / area)
                   for area in ("project", "framework")} for arm in ("S", "G")}
    if before != after:
        raise ValueError("Input mutation during measurement")
    for path, original_hash in inputs.items():
        if dataset.digest((dataset.ROOT / path).read_bytes()) != original_hash:
            raise ValueError("Author inputs changed during measurement")
    # Review material is intentionally outside both arms.
    for case in cases["cases"]:
        rubric = oracle["cases"][case["id"]]
        chunks = ["# " + case["id"], case["question"],
                  "AUTHOR DRAFT — independent approval is not recorded.",
                  json.dumps(rubric, ensure_ascii=False, indent=2)]
        for path in rubric["required_paths"]:
            chunks += ["## " + path, (output / "arms/S/project" / path).read_text(encoding="utf-8")]
        review = evaluator / "review" / (case["id"] + ".md")
        review.parent.mkdir(exist_ok=True)
        review.write_text("\n\n".join(chunks) + "\n", encoding="utf-8")
    report = {
        "schema": "framework/graph-calibration-result/v1", "dataset_id": corpus["dataset_id"],
        "candidate": version, "inputs": inputs, "source_runtime_parity": True,
        "unchanged_inputs": True, "graph_bytes_identical": True, "model_invocations": 0,
        "case_count": len(rows), "mechanical_checks_passed": sum(row["passed"] for row in rows),
        "mechanical_calibration_passed": all(row["passed"] for row in rows),
        "cases_with_additional_required": sum(bool(row["additional_required"]) for row in rows),
        "graph": {"snapshot": graph["snapshot"], "nodes": len(graph["nodes"]),
                  "edges": len(graph["edges"]), "gaps": graph["gaps"]},
        "source_inventory_sha256": dataset.digest(dataset.canonical(before["S"]["project"])),
        "runtime_inventory_sha256": dataset.digest(dataset.canonical(before["S"]["framework"])),
        "questions": rows, "receipts": receipts,
        "independent_rubric_approval": False, "agent_isolation_qualified": False,
        "agent_dispatch_allowed": False,
        "limitations": [
            "Authored calibration demonstrates traversability, not agent effectiveness or generalization",
            "Seed paths explicitly supplied; no measurement of spontaneous initial-source routing",
            "All source front matter and manual links remain available in both arms",
            "S packets omit graph edges but readable runtime could reconstruct them; sandbox still required",
            "No code graph, agent answers, token savings or wall-time gains measured",
            "Original legacy G0 result is unchanged and must not be pooled with this calibration"],
    }
    dataset.save(evaluator / "result.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = prepare_and_measure(args.output)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Calibration failed; no model invoked: {error}\n")
    print(json.dumps({key: result[key] for key in (
        "dataset_id", "case_count", "mechanical_checks_passed",
        "cases_with_additional_required", "model_invocations", "agent_dispatch_allowed")}, indent=2))
    return 0 if result["mechanical_calibration_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
