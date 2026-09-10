#!/usr/bin/env python3
"""Explicit local documentary pilot. Raw output is PRIVATE; no model or product writes.

This exercises the existing capture/graph/context code on an explicitly selected
documentation root, with its actual adopted rule pin. It neither fills mappings nor
substitutes runtime rules for missing adopted rules. Code observation requires
explicit checkout roots and an already installed pinned provider. Python is read,
never executed. With no local document bindings, this does not attest a mapping.
"""
from __future__ import annotations

import argparse
from collections import Counter
import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def git_state(root):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    result = subprocess.run(["git", "--no-pager", "-c", "core.fsmonitor=false", "-C", str(root),
                             "status", "--porcelain=v1", "--untracked-files=all"],
                            env=env, check=True, capture_output=True, text=True, timeout=30)
    return result.stdout


def private_output(output, roots):
    # Resolve existing parent symlinks before checking containment, including an
    # absent final directory. A lexical outside path is not an outside destination.
    resolved = output.resolve()
    if not output.is_absolute() or output.exists() or output.is_symlink() or any(
            resolved.is_relative_to(base.resolve()) for base in roots):
        raise ValueError("output must be an absent absolute private directory outside input/framework repositories")
    return resolved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="absent PRIVATE directory outside both repos")
    parser.add_argument("--product", action="append", required=True)
    parser.add_argument("--code-root", type=Path, action="append", default=[])
    parser.add_argument("--enola", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.code_root and args.enola is None:
        parser.error("code observation needs an explicit already installed pinned provider")
    try:
        output = private_output(args.output, (root, ROOT, *args.code_root))
    except ValueError as error:
        parser.error(str(error))
    # Directory mode is a useful local precaution, not encryption or permission audit.
    output.mkdir(parents=True, mode=0o700)
    spec = importlib.util.spec_from_file_location("pilot_runtime", ROOT / "memory.py")
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
    snapshots = importlib.import_module(runtime._name + ".snapshots")
    graphs = importlib.import_module(runtime._name + ".memory.graph")
    context = importlib.import_module(runtime._name + ".memory.context")
    before = git_state(root)
    snapshot = snapshots.capture(root)
    graph = graphs.build(snapshot)
    save(output / "documents.json", graph)
    save(output / "inputs.json", snapshot.inputs)
    products = []
    for number, product in enumerate(args.product, 1):
        pack = context.compose(snapshot, graph, products=[product], mode="analysis",
                               goal="Read-only readiness and consequences assessment; no implementation",
                               skill="audit", reconsider=True, budget=100000, framework_root=ROOT)
        save(output / f"context-{number}.json", pack)
        products.append({"alias": f"scope-{number}", "required_sources": len(pack["required_sources"]),
                         "delivery_complete": pack["delivery_complete"],
                         "required_delivery": dict(Counter(r["delivery"] for r in pack["required_sources"])),
                         "framework_resolution": pack["framework"]["resolution"],
                         "adopted_version": pack["framework"]["version"],
                         "reading_status": pack["reading_status"], "understanding": pack["understanding"],
                         "authorization": pack["mandate"]["authorization"],
                         "code_status": pack["code"]["status"]})
    snapshot.assert_unchanged()
    after = git_state(root)
    if before != after:
        raise RuntimeError("Git state changed during pilot; no clean observation claim")
    save(output / "git-state.json", {"before": before, "after": after})
    observations = []
    for number, code_root in enumerate(args.code_root, 1):
        sources = importlib.import_module(runtime._name + ".memory.code_sources")
        enola = importlib.import_module(runtime._name + ".memory.providers.enola")
        provider = enola.EnolaProvider(args.enola)
        code_before = git_state(code_root)
        captured = sources.capture_code(code_root)
        observed = provider.extract(captured.files)
        captured.assert_unchanged()
        accounted = {r["path"] for r in observed.coverage}
        coverage = [*captured.coverage, *observed.coverage,
                    *[dict(path=p, status="unavailable", reason="provider-coverage-missing")
                      for p in sorted(set(captured.files) - accounted)]]
        if code_before != git_state(code_root):
            raise RuntimeError("Code Git state changed during observation")
        save(output / f"code-inputs-{number}.json", captured.inputs)
        save(output / f"code-observation-{number}.json", {
            "provider": provider.status(), "status": observed.status, "records": observed.records,
            "coverage": coverage, "problems": observed.problems})
        observations.append({"alias": f"checkout-{number}", "tracked_python_files": len(captured.files),
                             "provider_status": observed.status, "records": len(observed.records),
                             "coverage": dict(Counter(r["status"] for r in coverage)),
                             "overall_coverage": "unavailable" if observed.status == "unavailable" else
                                 "partial" if observed.status != "available" or any(r["status"] != "available" for r in coverage)
                                 else "available",
                             "sources_unchanged": True, "git_state_unchanged": True,
                             "document_mapping": "not-validated"})
    snapshot.assert_unchanged()
    if before != git_state(root):
        raise RuntimeError("Documentation Git state changed during code observation")
    summary = {"schema": "framework/memory-pilot/v1", "sources_unchanged": True,
               "git_state_unchanged": True, "document_coverage": graph["coverage"],
               "selected_sources": len(graph["sources"]), "nodes": len(graph["nodes"]),
               "relations": len(graph["edges"]), "issues": len(graph["issues"]),
               "gaps": len(graph["gaps"]), "scopes": products,
               "code_observations": observations,
               "classifications": snapshot.workspace.config["classifications"],
               "limitations": ["Not semantic validation of real documents", "No code/document mapping inferred",
                               "Code provider supports Python only; other files are not proven irrelevant",
                               "Existing working changes preserved; not a clean-tree assertion",
                               "Raw outputs may contain sensitive contents; do not publish"]}
    save(output / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
