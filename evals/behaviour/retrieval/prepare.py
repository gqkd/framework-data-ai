#!/usr/bin/env python3
"""Offline synthetic A/B preparation. No model, clone, migration, or graph generation."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import random
import re
import shutil
import subprocess
import sys
import tarfile

import yaml

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASELINE = "db75f310e2f42453cb0fe1b26573c3f6b5736790"
CANDIDATE = "faaf42259c7b43dfecbd1c52df21b2c4788cfc50"
RUNTIME_PATHS = {
    "FRAMEWORK.md", "SKILLS.md", "PROCESSES.md", "memory.py", "src", "schemas",
    "references", "skills", "templates", "assets", "providers.lock.json",
    "constraints.txt", "requirements.txt",
}
PROMPT = """Analizza in sola lettura il progetto sintetico, partendo da AGENTS.md.
Il runtime del framework associato si trova in ../framework.
Non modificare le fonti, approvare cambiamenti, installare strumenti, accedere alla rete
o delegare lavoro. Non leggere evaluator, altri esperimenti o file fuori dal progetto
e dal runtime assegnati. Eventuali indici derivati devono restare nello spazio temporaneo
esplicitamente autorizzato dal runner, mai nelle fonti.
Rispondi in italiano con conclusione, fonti effettivamente lette (percorso e sezioni),
incertezze e prove mancanti. Non dichiarare letture, esecuzioni o misure non effettuate.

Domanda:
"""


class UniqueLoader(yaml.SafeLoader):
    """A duplicate answer/source key must not silently replace an earlier one."""


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"Duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def read_yaml(path):
    return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueLoader)


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def relative_path(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError(f"Unsafe relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in ("..", ".git", "evaluator") for p in path.parts):
        raise ValueError(f"Unsafe relative path: {value!r}")
    if str(path) != value or value == ".":
        raise ValueError(f"Non-canonical relative path: {value!r}")
    return path


def load_generator():
    path = ROOT / "evals/fixtures/generators/memory.py"
    spec = importlib.util.spec_from_file_location("retrieval_synthetic_helpers", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def definitions():
    corpus, questions, oracle = (read_yaml(HERE / name) for name in
                                 ("corpus.yaml", "questions.yaml", "oracle.yaml"))
    if len({d["dataset_id"] for d in (corpus, questions, oracle)}) != 1:
        raise ValueError("Dataset identities differ")
    rows = questions["questions"]
    ids = [q["id"] for q in rows]
    if len(ids) != len(set(ids)) or set(ids) != set(oracle["cases"]):
        raise ValueError("Question/oracle IDs differ or repeat")
    if len(rows) != 24 or sorted(Counter(q["family"] for q in rows).values()) != [3] * 8:
        raise ValueError("Expected 24 questions in eight balanced families")
    for family in {q["family"] for q in rows}:
        if Counter(q["split"] for q in rows if q["family"] == family) != {
                "development": 1, "evaluation": 2}:
            raise ValueError("Each family needs one development and two evaluation questions")
    for case in oracle["cases"].values():
        if not case.get("must_include") or not case.get("must_not") or not case.get("sources"):
            raise ValueError("Incomplete review rubric")
        for group in case["sources"]:
            if not isinstance(group, list) or not group or any(
                    source not in oracle["sources"] for source in group):
                raise ValueError("Unknown or empty source alternative group")
        for absence in case.get("absences", []):
            relative_path(absence)
    paths = [d["path"] for d in corpus["documents"]]
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate document path")
    for path in paths:
        relative_path(path)
    for source in oracle["sources"].values():
        relative_path(source["path"])
    for name, repo in corpus["repositories"].items():
        if not re.fullmatch(r"[a-z][a-z0-9-]*", name):
            raise ValueError("Unsafe repository name")
        for field in ("files", "later_files"):
            for path in repo.get(field, {}):
                relative_path(path)
    for path in corpus.get("extra_files", {}):
        relative_path(path)
        if path in paths or not path.startswith("code/"):
            raise ValueError("Extra files must be distinct synthetic code inputs")
    return corpus, questions, oracle


def git_bytes(*args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    return subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", str(ROOT), *args],
                          env=env, check=True, capture_output=True, timeout=60).stdout


def framework_info(commit):
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("Framework snapshots require full lowercase commit IDs")
    resolved = git_bytes("rev-parse", "--verify", commit + "^{commit}").decode().strip()
    registry = yaml.safe_load(git_bytes("show", f"{resolved}:schemas/artifact-types.yaml"))
    return {"commit": resolved, "version": registry["version"]}


def export_runtime(commit, destination):
    top = set(git_bytes("ls-tree", "--name-only", commit).decode().splitlines())
    archive = git_bytes("archive", "--format=tar", commit, *sorted(top & RUNTIME_PATHS))
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as stream:
        for member in stream:
            name = member.name.rstrip("/")
            rel = relative_path(name)
            if rel.parts[0] not in RUNTIME_PATHS:
                raise ValueError(f"Unexpected runtime member: {name}")
            target = destination / name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(stream.extractfile(member).read())
                target.chmod(0o755 if member.mode & 0o111 else 0o644)
            else:
                raise ValueError(f"Runtime contains a link or special file: {name}")


def build_project(destination, corpus):
    """Render fiction; no oracle, model answer or product repository is an input."""
    if destination.exists() or destination.is_symlink():
        raise ValueError("Synthetic project destination must be absent")
    helper = load_generator()
    docs = helper.Documents(destination)
    docs.base(tuple(corpus["products"]))
    commits = {}
    for name, repository in corpus["repositories"].items():
        first, _ = helper.code_repository(destination, "code/" + name, repository["files"])
        repo = destination / "code" / name
        if repository.get("later_files"):
            for path, content in repository["later_files"].items():
                helper.write(repo, path, content)
            helper.git(repo, "add", "--all")
            helper.git(repo, "commit", "-m", "Add synthetic health observation")
        commits[name] = {"attested": first, "head": helper.git(repo, "rev-parse", "HEAD")}
    docs.manifest("alpha", {"api": helper.repository_entry("alpha-api", "Producer and tests")})
    docs.manifest("beta", {"worker": helper.repository_entry("beta-worker", "Consumer and tests")})
    for artifact in corpus["documents"]:
        fields = dict(artifact.get("fields", {}))
        if "attest" in artifact:
            fields["verified_code"] = {key: commits[name]["attested"]
                                       for key, name in artifact["attest"].items()}
        docs.artifact(artifact["path"], artifact["kind"], artifact["body"],
                      lifecycle=artifact.get("lifecycle", "living"),
                      status=artifact.get("status", "active"), **fields)
    for path, content in corpus.get("extra_files", {}).items():
        helper.write(destination, path, content)
    return commits


def inventory(root, *, omit_config=False):
    """Content/mode identity, excluding nondeterministic Git internals, never following links."""
    result = {}
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in [*dirs, *files]:
            if (Path(parent) / name).is_symlink():
                raise ValueError("Symlinks are not permitted in prepared inputs")
        dirs[:] = sorted(name for name in dirs if name != ".git")
        for name in sorted(files):
            path = Path(parent) / name
            rel = path.relative_to(root).as_posix()
            if omit_config and rel == "framework.yaml":
                continue
            result[rel] = {"sha256": digest(path.read_bytes()), "bytes": path.stat().st_size,
                           "executable": bool(path.stat().st_mode & 0o111)}
    return result


def source_receipts(project, oracle):
    """Resolve authored source requirements, not inferred answers, to exact byte/line spans."""
    receipts = {}
    for identifier, source in oracle["sources"].items():
        path = project / str(relative_path(source["path"]))
        content = path.read_bytes()
        lines = content.decode("utf-8").splitlines(keepends=True)
        spans = []
        if source.get("sections"):
            for heading in source["sections"]:
                starts = [n for n, line in enumerate(lines) if line.strip() == "## " + heading]
                if len(starts) != 1:
                    raise ValueError(f"Missing/ambiguous section {heading} in {source['path']}")
                start = starts[0]
                end = next((n for n in range(start + 1, len(lines))
                            if re.match(r"^#{1,2} ", lines[n])), len(lines))
                spans.append({"section": heading, "start_line": start + 1, "end_line": end,
                              "sha256": digest("".join(lines[start:end]).encode("utf-8"))})
        else:
            spans.append({"start_line": 1, "end_line": len(lines), "sha256": digest(content)})
        receipts[identifier] = {"path": source["path"], "file_sha256": digest(content),
                                "required_spans": spans}
    for case in oracle["cases"].values():
        for relative in case.get("absences", []):
            if (project / relative).exists():
                raise ValueError(f"Required absence is present: {relative}")
    return receipts


def schedule(questions, repetitions=3, seed=1729):
    rng = random.Random(seed)
    result = []
    for split in ("development", "evaluation"):
        for repetition in range(1, repetitions + 1):
            rows = [q for q in questions["questions"] if q["split"] == split]
            rng.shuffle(rows)
            for row in rows:
                arms = ["A", "B"]
                rng.shuffle(arms)
                result.extend({"question": row["id"], "split": split, "arm": arm,
                               "repetition": repetition, "status": "not-run"} for arm in arms)
    return result


def prepare(output, baseline=BASELINE, candidate=CANDIDATE):
    output = Path(output)
    if not output.is_absolute() or output.exists() or output.is_symlink():
        raise ValueError("Output must be an absent absolute directory")
    if any(parent.is_symlink() for parent in output.parents):
        raise ValueError("Output cannot use symlink parents")
    if output.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("Output must be outside the framework checkout")
    corpus, questions, oracle = definitions()
    versions = {"A": framework_info(baseline), "B": framework_info(candidate)}
    if baseline == candidate:
        raise ValueError("A/B requires two distinct framework snapshots")
    output.mkdir(parents=True, exist_ok=False)
    evaluator = output / "evaluator"
    evaluator.mkdir()
    project_a = output / "arms/A/project"
    commits = build_project(project_a, corpus)
    project_b = output / "arms/B/project"
    project_b.parent.mkdir(parents=True)
    shutil.copytree(project_a, project_b)
    projects = {"A": project_a, "B": project_b}
    for arm, project in projects.items():
        # Git-less exports cannot resolve a project Git pin. Exact runtime commits
        # and inventories are attested independently by the trusted evaluator.
        config = {"framework_version": versions[arm]["version"], "scan": {"skip_dirs": ["code"]}}
        (project / "framework.yaml").write_text(
            yaml.safe_dump(config, sort_keys=False), encoding="utf-8", newline="\n")
        export_runtime(versions[arm]["commit"], project.parent / "framework")
    common = inventory(project_a, omit_config=True)
    if common != inventory(project_b, omit_config=True):
        raise ValueError("Source parity failed")
    receipts = source_receipts(project_a, oracle)
    if receipts != source_receipts(project_b, oracle):
        raise ValueError("Reference source receipts differ between arms")
    save(evaluator / "questions.json", questions)
    save(evaluator / "oracle.json", oracle)
    save(evaluator / "source-requirements.json", receipts)
    save(evaluator / "schedule.json", schedule(questions))
    for question in questions["questions"]:
        path = evaluator / "prompts" / (question["id"] + ".txt")
        path.parent.mkdir(exist_ok=True)
        path.write_text(PROMPT + question["prompt"] + "\n", encoding="utf-8", newline="\n")
    source_paths = [HERE / name for name in
                    ("prepare.py", "corpus.yaml", "questions.yaml", "oracle.yaml",
                     "PROTOCOL.md", "validation-expected.yaml")]
    source_paths.append(ROOT / "evals/fixtures/generators/memory.py")
    manifest = {
        "schema": "framework/synthetic-retrieval-preparation/v1",
        "dataset_id": corpus["dataset_id"], "synthetic_only": True,
        "status": "prepared-not-evaluated", "oracle_review": oracle["review_status"],
        "versions": versions, "code_commits": commits,
        "project_adoption": "version-only; exact runtime commits and bytes attested by evaluator",
        "generator_inputs": {p.relative_to(ROOT).as_posix(): digest(p.read_bytes())
                             for p in source_paths},
        "source_content_sha256": digest(canonical(common)),
        "source_files": common, "allowed_arm_differences": ["framework.yaml"],
        "arms": {arm: {"project_files": inventory(project),
                       "runtime_files": inventory(project.parent / "framework")}
                 for arm, project in projects.items()},
        "question_count": len(questions["questions"]), "planned_trials": len(schedule(questions)),
        "model_runs": 0, "precomputed_context": False, "metadata_enrichment": False,
        "source_boundary": "Only bundled fictional definitions and local framework Git objects",
        "limitations": [
            "Directory separation is not sandbox enforcement",
            "Git-less runtime uses version-only adoption; rule-byte identity is evaluator-side",
            "Same-world evaluation questions are not independent unseen corpora",
            "Human oracle review and instrumented runner are still required",
            "No claim of retrieval improvement, token savings, or real-project generalization",
        ],
    }
    save(evaluator / "manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--baseline", default=BASELINE, help="Full locally available commit ID")
    parser.add_argument("--candidate", default=CANDIDATE, help="Full locally available commit ID")
    args = parser.parse_args()
    try:
        result = prepare(args.output, args.baseline, args.candidate)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"Preparation failed (no model run): {exc}\n")
    print(json.dumps({key: result[key] for key in
                      ("dataset_id", "status", "versions", "question_count", "model_runs")},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
