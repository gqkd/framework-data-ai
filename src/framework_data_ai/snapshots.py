"""Content-addressed documentary snapshots and atomic publication.

No wall clock, checkout path or private local binding enters a canonical output.
Source revisions hash the actual bytes, not Git's dirty boolean or a timestamp.
"""
from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile

from .artifacts import Artifact, jsonify, parse_front_matter
from .memory.models import CONTRACT_PATH, FRAMEWORK, canonical, contract, digest, validate, validate_graph
from .workspace import MemoryInputError, Workspace, no_symlink_ancestors


class ConcurrentChange(MemoryInputError):
    pass


def bounded_metadata(value):
    """Bound alias expansion/cycles before JSON conversion; reuse the shared leaf conversion."""
    limits = contract()["metadata_limits"]
    visited = 0

    def convert(item, depth=0):
        nonlocal visited
        visited += 1
        if visited > limits["items"] or depth > limits["depth"]:
            raise ValueError("metadata expansion limit exceeded")
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise ValueError("metadata keys must be strings")
            return {key: convert(child, depth + 1) for key, child in item.items()}
        if isinstance(item, list):
            return [convert(child, depth + 1) for child in item]
        return jsonify(item)

    return convert(value)


def git_head(root: Path) -> str | None:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_OPTIONAL_LOCKS="0")
    try:
        def run(*args):
            return subprocess.run(["git", "-C", str(root), *args], env=env, check=True,
                                  capture_output=True, text=True, timeout=10).stdout.strip()
        if Path(run("rev-parse", "--show-toplevel")).resolve() != root:
            return None  # A parent repository is not the declared documentation checkout.
        return run("rev-parse", "--verify", "HEAD")
    except (OSError, subprocess.SubprocessError):
        return None


def optional_dependency_version(name: str) -> str:
    # Older supported referencing releases need no typing-extensions on Python 3.12.
    # Absence is still part of identity, not an invented mandatory runtime dependency.
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not-installed"


def generator_inputs() -> dict:
    paths = [FRAMEWORK / "memory.py", FRAMEWORK / "schemas/artifact-types.yaml", CONTRACT_PATH,
             FRAMEWORK / "providers.lock.json"]
    paths += sorted((FRAMEWORK / "src/framework_data_ai").rglob("*.py"))
    if (FRAMEWORK / "constraints.txt").is_file():
        paths.append(FRAMEWORK / "constraints.txt")
    inputs = {path.relative_to(FRAMEWORK).as_posix(): digest(path.read_bytes())
              for path in sorted(paths)}
    inputs["runtime:python"] = digest(canonical([sys.implementation.name, *sys.version_info[:3]]))
    for name in ("PyYAML", "jsonschema", "attrs", "jsonschema-specifications", "referencing", "rpds-py"):
        inputs["runtime:" + name] = digest(metadata.version(name).encode("utf-8"))
    if sys.version_info < (3, 13):
        inputs["runtime:typing-extensions"] = digest(optional_dependency_version("typing-extensions").encode("utf-8"))
    return inputs


def read_inputs(workspace: Workspace) -> tuple[dict[str, bytes], dict]:
    files = {}
    total = 0
    try:
        for path in workspace.paths():
            descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
            with os.fdopen(descriptor, "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise MemoryInputError("a selected source is not a regular file")
                data = stream.read(workspace.config["max_file_bytes"] + 1)
            if len(data) > workspace.config["max_file_bytes"]:
                raise MemoryInputError("a source exceeds max_file_bytes; no snapshot published")
            total += len(data)
            if total > workspace.config["max_total_bytes"]:
                raise MemoryInputError("sources exceed max_total_bytes; no snapshot published")
            files[path.relative_to(workspace.root).as_posix()] = data
        controls = {}
        for name in ("framework.yaml", ".framework-memory/config.yaml"):
            path = workspace.root / name
            controls[name] = digest(path.read_bytes()) if path.exists() else None
    except (OSError, RuntimeError) as error:
        raise ConcurrentChange("selected inputs became unreadable; retry the build") from error
    return files, {"controls": controls, "commit": git_head(workspace.root),
                   "effective_config": workspace.config,
                   "effective_scan": {k: sorted(v) if isinstance(v, set) else v
                                      for k, v in workspace.scan.items()}}


@dataclass
class Snapshot:
    workspace: Workspace
    artifacts: list[Artifact]
    texts: dict[str, str]
    sources: dict[str, dict]
    issues: list[dict]
    inputs: dict
    id: str
    _read_fingerprint: str

    def assert_unchanged(self) -> None:
        current = Workspace.open(self.workspace.root)
        files, guard = read_inputs(current)
        fingerprint = digest(canonical({"files": {p: digest(b) for p, b in files.items()},
                                        "guard": guard, "generator": generator_inputs()}))
        if fingerprint != self._read_fingerprint:
            raise ConcurrentChange("sources, configuration or generator changed; snapshot not published")


def capture(root: Path) -> Snapshot:
    workspace = Workspace.open(root)
    files, guard = read_inputs(workspace)
    generator = generator_inputs()
    fingerprint = digest(canonical({"files": {p: digest(b) for p, b in files.items()},
                                    "guard": guard, "generator": generator}))
    artifacts, texts, sources, issues, selected = [], {}, {}, [], {}
    filtered = 0
    id_re = re.compile(r"\b((?:%s)-\d{3,})\b" % "|".join(workspace.registry["id_prefixes"]))
    for relative, data in sorted(files.items()):
        try:
            text = data.decode("utf-8").replace("\r\n", "\n")
            meta, body, error = parse_front_matter(text)
        except (UnicodeError, ValueError, RecursionError):
            meta, body, error = None, "", "unreadable encoding or metadata"
        classification = meta.get("classification") if meta else None
        if ((classification is None and not workspace.config["include_unclassified"]) or
                (classification is not None and classification not in workspace.config["classifications"])):
            filtered += 1
            continue
        selected[relative] = digest(data)
        if error:
            issues.append(dict(code="parse-failed", path=relative,
                               detail="source could not be parsed; it is not represented"))
            continue
        source = dict(id="source:" + digest(canonical([workspace.config["document_repository"],
                                                       relative, digest(data)])), path=relative,
                      revision="sha256:" + digest(data), lines=max(1, len(text.splitlines())))
        sources[relative] = source
        texts[relative] = text
        try:
            converted = bounded_metadata(meta)
        except (ValueError, RecursionError):
            issues.append(dict(code="metadata-limit", path=relative,
                               detail="metadata cannot be safely expanded; source not projected"))
            continue
        artifact = Artifact(workspace.root / relative, relative, converted, body)
        artifact.ids = set(id_re.findall(body))
        artifacts.append(artifact)
    inputs = dict(document_repository=workspace.config["document_repository"],
                  document_commit=guard["commit"], contents=selected,
                  framework_version=workspace.registry["version"],
                  generator_version=contract()["generator_version"], generator=generator,
                  config=workspace.config,
                  scan={k: sorted(v) if isinstance(v, set) else v for k, v in workspace.scan.items()},
                  filtered_sources=filtered, code_observation="not_requested")
    snapshot = Snapshot(workspace, artifacts, texts, sources, issues, inputs,
                        digest(canonical(inputs)), fingerprint)
    snapshot.assert_unchanged()
    return snapshot


def publish(snapshot: Snapshot, graph: dict) -> dict:
    """Publish an immutable directory by rename. An existing result is verified, never overwritten."""
    validate_graph(graph)
    if graph["snapshot"] != snapshot.id or snapshot.id != digest(canonical(snapshot.inputs)):
        raise MemoryInputError("graph and snapshot identities disagree")
    graph_bytes = canonical(graph)
    manifest = dict(schema="framework-memory/manifest/v1", id=snapshot.id, inputs=snapshot.inputs,
                    files={"graph.json": digest(graph_bytes)})
    validate("manifest", manifest)
    publish_payload(snapshot.workspace.root, "snapshots", snapshot.id,
                    {"graph.json": graph_bytes, "manifest.json": canonical(manifest)}, snapshot.assert_unchanged)
    return manifest


def publish_payload(root: Path, namespace: str, identifier: str, payload: dict, assert_unchanged) -> None:
    """Shared atomic writer; namespace and flat filenames cannot escape the runtime directory."""
    filenames_valid = (set(payload) == {"index.html", "manifest.json"} if namespace == "views"
                       else all(re.fullmatch(r"[a-z-]+\.json", name) for name in payload))
    if (namespace not in ("snapshots", "code-snapshots", "views")
            or not re.fullmatch(r"[0-9a-f]{64}", identifier) or not filenames_valid):
        raise MemoryInputError("unsafe snapshot identity or filename")
    assert_unchanged()
    base_rel = Path("_meta/memory") / namespace
    no_symlink_ancestors(root, base_rel)
    base = root / base_rel
    base.mkdir(parents=True, exist_ok=True)
    lock = base / ".build.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise MemoryInputError("another build holds the snapshot lock; no output overwritten") from error
    os.close(descriptor)
    staging = None
    try:
        target = base / identifier
        if target.is_symlink():
            raise MemoryInputError("snapshot destination is a symbolic link")
        if target.exists():
            if (set(p.name for p in target.iterdir()) != set(payload) or
                    any((target / name).is_symlink() or (target / name).read_bytes() != data
                        for name, data in payload.items())):
                raise MemoryInputError("existing snapshot differs; refusing to overwrite it")
            assert_unchanged()
            return
        staging = Path(tempfile.mkdtemp(prefix=".pending-", dir=base))
        for name, data in payload.items():
            with (staging / name).open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        assert_unchanged()
        staging.rename(target)
        staging = None
    finally:
        if staging is not None:
            shutil.rmtree(staging)  # Only this invocation's newly created, unpublished directory.
        lock.unlink()
