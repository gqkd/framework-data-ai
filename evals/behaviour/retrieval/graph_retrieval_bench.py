#!/usr/bin/env python3
"""Deterministic retrieval benchmark of the optional memory engine. No model is called.

Scores the engine's own retrieval against the frozen oracle: for each question, can the
documentary graph deliver the required source groups, and at what delivered-character
cost? Three methods, none of which reads the oracle's answers:

  M1  query with the question text exactly as asked
  M2  query with correct English terms  -> the engine's ceiling, not agent behaviour
  M3  context pack, the invocation documented in references/operational-memory.md

Delivery is not comprehension and a retrieved path is not a correct answer. This measures
the retrieval channel only; answer quality stays with independent human review.
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
import subprocess
import sys

import yaml

HERE = Path(__file__).resolve().parent
# Derived from each question's own wording, never from oracle must_include phrases.
TERMS = {
    "R001": ["language", "service", "alpha"], "R002": ["format", "report", "beta"],
    "R003": ["Redis", "gamma", "approved"], "R004": ["results", "request", "between"],
    "R005": ["accepted", "batch", "complete"], "R006": ["whitespace", "identifier", "alpha"],
    "R007": ["signal", "beta", "alpha", "approved"], "R008": ["queued", "report", "published"],
    "R009": ["language", "gamma", "service"], "R010": ["JavaScript", "language", "service"],
    "R011": ["queue", "alpha", "deliver"], "R012": ["architecture", "alpha", "health"],
    "R013": ["item_key", "interface", "alpha"], "R014": ["refactor", "alpha", "tests"],
    "R015": ["normalization", "worker", "beta"], "R016": ["throughput", "gamma"],
    "R017": ["latency", "interface", "alpha"], "R018": ["revision", "production", "alpha"],
    "R019": ["shared", "identifier", "rule", "tests"], "R020": ["transformation", "alpha", "beta"],
    "R021": ["item_key", "producer", "worker"], "R022": ["spreadsheet", "report", "beta"],
    "R023": ["shared", "rule", "two", "implementations"], "R024": ["comment", "contributor", "rename"],
}


def engine(python, memory, *args):
    done = subprocess.run([python, str(memory), *args], capture_output=True, text=True, timeout=600)
    try:
        return json.loads(done.stdout)
    except json.JSONDecodeError:
        return None


def index(graph):
    nodes = {n["id"]: n["data"]["path"] for n in graph["nodes"] if n.get("data", {}).get("path")}
    nodes.update({s["id"]: s["path"] for s in graph["sources"]})
    return nodes


def delivered(documents, paths):
    found = collections.Counter()
    for document in documents:
        path = paths.get(document.get("node")) or paths.get(document.get("source"))
        if path:
            found[path] += len(document.get("body") or "")
    return found


def covered(case, sources, found):
    groups = case["sources"]
    return sum(1 for group in groups if any(sources[n] in found for n in group)), len(groups)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True, help="prepared arm B project copy")
    parser.add_argument("--framework", type=Path, required=True, help="its candidate runtime copy")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--skill", default="audit")
    args = parser.parse_args(argv)

    memory = args.framework / "memory.py"
    if not memory.is_file():
        parser.exit(2, "this runtime has no optional memory engine; nothing to benchmark\n")
    oracle = yaml.safe_load((HERE / "oracle.yaml").read_text(encoding="utf-8"))
    questions = yaml.safe_load((HERE / "questions.yaml").read_text(encoding="utf-8"))["questions"]
    sources = {k: v["path"] for k, v in oracle["sources"].items()}

    graph = engine(args.python, memory, "build", "--root", str(args.project), "--dry-run", "--export")
    if graph is None:
        parser.exit(2, "the engine did not export a graph on this project\n")
    paths = index(graph)

    def query(terms):
        found = collections.Counter()
        for term in terms:
            got = engine(args.python, memory, "query", "--root", str(args.project),
                         "--text", term, "--limit", str(args.limit))
            if got:
                found.update(delivered(got.get("documents", []), paths))
        return found

    pack = engine(args.python, memory, "context", "--root", str(args.project),
                  "--goal", "benchmark probe", "--skill", args.skill,
                  "--framework-root", str(args.framework)) or {}
    pack_paths = {s.get("path") for s in pack.get("required_sources", []) if isinstance(s, dict)}
    pack_chars = sum(len(c.get("text", "")) for c in pack.get("content", []))

    rows = []
    for question in questions:
        qid = question["id"]
        case = oracle["cases"][qid]
        m1 = query([question["prompt"]])
        m2 = query(TERMS[qid])
        required = {sources[n] for group in case["sources"] for n in group}
        hit1, groups = covered(case, sources, m1)
        hit2, _ = covered(case, sources, m2)
        hit3 = sum(1 for group in case["sources"] if any(sources[n] in pack_paths for n in group))
        rows.append({"id": qid, "split": question["split"], "groups": groups,
                     "m1_groups": hit1, "m1_chars": sum(m1.values()),
                     "m2_groups": hit2, "m2_chars": sum(m2.values()), "m2_documents": len(m2),
                     "m2_precision": round(100 * len(set(m2) & required) / len(m2), 1) if m2 else 0.0,
                     "m3_groups": hit3, "m3_chars": pack_chars})

    total = sum(r["groups"] for r in rows)
    report = {
        "schema": "framework/graph-retrieval-benchmark/v1",
        "scope": "retrieval channel only; delivery is not comprehension and never an answer score",
        "model_invocations": 0,
        "graph": {"nodes": len(graph["nodes"]), "edges": len(graph["edges"]),
                  "sources": len(graph["sources"]), "gaps": len(graph["gaps"]),
                  "snapshot": graph["snapshot"]},
        "context_pack": {"required_source_paths": len(pack_paths), "delivered_characters": pack_chars,
                         "question_sensitive": False},
        "questions": rows,
        "recall": {m: {"groups": sum(r[f"{m}_groups"] for r in rows), "of": total,
                       "percent": round(100 * sum(r[f"{m}_groups"] for r in rows) / total, 1)}
                   for m in ("m1", "m2", "m3")},
    }
    print(json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
