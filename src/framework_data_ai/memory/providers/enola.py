"""Strict, independently written Enola adapter. No Cognee runtime or copied reader code.

The supported unit is the pinned binary PLUS this Python syntax/coverage guard, not
unmodified Enola: the release silently recovers malformed Python (PHASE-3.md).
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sys
import tempfile

from ...workspace import MemoryInputError
from ..code_sources import safe_path
from ..models import FRAMEWORK, canonical, digest
from .base import Capabilities, Observation
from .process import bounded_run

LOCK = FRAMEWORK / "providers.lock.json"
KINDS = {"module", "symbol", "route", "storage", "dependency", "service", "intent",
         "extraction", "association", "test_ref", "file_ref", "lint"}
RELATIONS = {"declares", "imports", "calls", "implements", "depends_on", "instantiates",
             "injects", "has_method", "handled_by", "implemented_by", "names"}
CONFIG = b"""repo: /work/repository
extractors: [python]
explainers: []
renderers: []
providers: []
ignore: [.enola/**]
test_globs: []
incremental: false
history:
  enabled: false
output:
  dir: .enola
"""


def strict_json(data: bytes):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    def constant(_):
        raise ValueError("non-finite JSON number")
    return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)


def fact_id(fact):
    return hashlib.sha256("\0".join(fact.get(k, "") for k in ("repo", "kind", "name", "file"))
                          .encode()).hexdigest()[:32]


def read_output(output: Path, files: dict[str, bytes], lock: dict) -> dict:
    """Receipt is mandatory. Never skip a corrupt record or invent a nominal target ID."""
    def read(name):
        path = output / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 20_000_000:
            raise ValueError("missing or oversized provider artifact")
        return path.read_bytes()
    receipt = strict_json(read("receipt.json"))
    if (type(receipt.get("format_version")) is not int or receipt["format_version"] != lock["format_version"]
            or receipt.get("enola_version") != lock["version"]
            or receipt.get("extractor_version") != lock["extractor_version"]
            or receipt.get("extractors") != ["python"] or receipt.get("explainers") not in (None, [])):
        raise ValueError("unknown provider format, version or extraction profile")
    if receipt.get("providers"):
        raise ValueError("external provider execution is not part of the profile")
    raw, insight_bytes = read("facts.jsonl"), read("insights.json")
    hashes = receipt.get("output_hashes", {})
    for name, data in (("facts.jsonl", raw), ("insights.json", insight_bytes)):
        if hashes.get(name) != "sha256:" + digest(data):
            raise ValueError("provider artifact integrity failed")
    snapshot_id = "sha256:" + digest(raw + lock["version"].encode() + receipt["config_hash"].encode())
    if receipt.get("snapshot_id") != snapshot_id:
        raise ValueError("provider snapshot identity failed")
    lines = raw.splitlines()
    if len(lines) > 100000 or any(not line.strip() for line in lines):
        raise ValueError("invalid provider record stream")
    records = [strict_json(line) for line in lines]
    insights = strict_json(insight_bytes)
    if (type(receipt.get("fact_count")) is not int or receipt["fact_count"] != len(records)
            or type(receipt.get("insight_count")) is not int or not isinstance(insights, list)
            or receipt["insight_count"] != len(insights) or insights):
        raise ValueError("provider counts or disabled-insight profile disagree")
    quality = receipt.get("quality", {})
    for key in ("files_seen", "files_parsed", "files_skipped", "dirs_skipped", "parse_errors", "heuristic_insights"):
        if type(quality.get(key)) is not int or quality[key] < 0:
            raise ValueError("missing provider quality counters")
    if quality["files_seen"] != len(files) or quality["files_parsed"] > len(files):
        raise ValueError("provider file inventory disagrees with captured input")
    census = quality.get("census", {})
    for key in ("files_walked", "parsed", "excluded_by_ignore", "excluded_by_kind", "skipped_with_cause"):
        if type(census.get(key)) is not int or census[key] < 0:
            raise ValueError("missing or invalid provider census")
    if (census["files_walked"] != sum(census[k] for k in ("parsed", "excluded_by_ignore", "excluded_by_kind", "skipped_with_cause"))
            or census["parsed"] != quality["files_parsed"] or quality["heuristic_insights"] != len(insights)):
        raise ValueError("provider census counters disagree")
    for record in records:
        if not isinstance(record, dict) or record.get("kind") not in KINDS or record.get("repo") != "repository":
            raise ValueError("invalid provider fact or repository label")
        for key in ("name", "file"):
            if not isinstance(record.get(key, ""), str) or "\0" in record.get(key, ""):
                raise ValueError("invalid fact identity field")
        if not record.get("name") or record.get("id") != fact_id(record):
            raise ValueError("provider fact identity mismatch")
        path = record.get("file", "")
        if path and path != ".":
            safe_path(path)
        # Enola emits package-coupling rollups with a directory locator. They are
        # retained receipt evidence, NOT direct imports or invented file locations.
        props = record.get("props", {})
        rollup = (record["kind"] == "dependency" and isinstance(props, dict)
                  and props.get("derived") == "symbol-rollup"
                  and props.get("coupling_kind") == "symbol-rollup"
                  and type(props.get("symbol_edges")) is int and props["symbol_edges"] > 0)
        directory = path == "." or any(p.startswith(path + "/") for p in files)
        directory_rollup = rollup and directory and not any(
            key in record for key in ("line", "end_line", "column", "end_column"))
        if record["kind"] != "module" and path and path not in files and not directory_rollup:
            raise ValueError("provider source lies outside the captured input")
        if record["kind"] == "module" and path != "." and not any(p.startswith(path + "/") for p in files):
            raise ValueError("provider module lies outside the captured input")
        for key in ("line", "end_line", "column", "end_column"):
            if key in record and (type(record[key]) is not int or record[key] < 1):
                raise ValueError("invalid provider source position")
        if "line" in record and (path not in files or record.get("end_line", record["line"]) < record["line"]
                                   or record.get("end_line", record["line"]) > max(1, len(files[path].splitlines()))):
            raise ValueError("provider source range is outside captured bytes")
        if not isinstance(record.get("props", {}), dict) or not isinstance(record.get("relations", []), list):
            raise ValueError("invalid fact properties or relations")
        for relation in record.get("relations", []):
            if (not isinstance(relation, dict) or relation.get("kind") not in RELATIONS
                    or not isinstance(relation.get("target"), str) or not relation["target"]
                    or ("target_id" in relation and not re.fullmatch(r"[0-9a-f]{32}", relation["target_id"]))):
                raise ValueError("invalid provider direct relation")
    # Volatile receipt fields are neither copied nor used as canonical identity.
    evidence = {key: receipt[key] for key in ("snapshot_id", "format_version", "enola_version", "extractor_version",
                 "config_hash", "ignore_glob_hash", "output_hashes", "fact_count", "insight_count", "quality")}
    return dict(records=records, insights=insights, evidence=evidence)


class EnolaProvider:
    def __init__(self, binary: Path | None = None):
        self.lock = strict_json(LOCK.read_bytes())["enola"]
        self.binary = binary
        self.capabilities = Capabilities("enola", self.lock["version"], ("python",),
                                        ("declares", "imports", "calls", "implements", "instantiates", "names"),
                                        self.lock["profile"])

    def status(self):
        result = dict(status="unavailable", provider="enola", version=self.lock["version"],
                      profile=self.lock["profile"], runtime=f"cpython-{platform.python_version()}",
                      configuration_hash=digest(CONFIG), lock_hash=digest(LOCK.read_bytes()))
        key = platform.system() + "-" + platform.machine()
        if key not in self.lock["platforms"] or sys.version_info < (3, 12):
            return dict(result, reason="unsupported-host")
        if not shutil.which("bwrap") or not shutil.which("prlimit"):
            return dict(result, reason="isolation-unavailable")
        if self.binary is None or not self.binary.is_file() or self.binary.is_symlink():
            return dict(result, reason="provider-not-configured")
        if self.binary.stat().st_size > 100_000_000:
            return dict(result, reason="binary-integrity-failed")
        if digest(self.binary.read_bytes()) != self.lock["platforms"][key]["binary_sha256"]:
            return dict(result, reason="binary-integrity-failed")
        return dict(result, status="available", binary_hash=self.lock["platforms"][key]["binary_sha256"])

    def extract(self, files):
        state = self.status()
        if state["status"] != "available":
            return Observation("unavailable", problems=[dict(code=state["reason"])], evidence=state)
        valid, coverage, problems = {}, [], []
        for path, data in sorted(files.items()):
            safe_path(path)
            if not path.endswith(".py"):
                coverage.append(dict(path=path, status="unsupported", reason="python-profile-only"))
                continue
            try:
                ast.parse(data, filename=path, feature_version=(3, 12))
            except (SyntaxError, ValueError, UnicodeError, RecursionError):
                coverage.append(dict(path=path, status="unavailable", reason="python-syntax-guard"))
                problems.append(dict(code="parse-error", path=path, detector="cpython-ast-3.12-grammar"))
                continue
            valid[path] = data
        if not valid:
            return Observation("unavailable", coverage=coverage, problems=problems or [dict(code="no-supported-source")],
                               evidence=state)
        try:
            with tempfile.TemporaryDirectory(prefix="framework-enola-") as directory:
                stage = Path(directory)
                repo, output = stage / "repository", stage / "output"
                repo.mkdir()
                output.mkdir()
                (repo / ".enola").mkdir()
                for path, data in valid.items():
                    target = repo / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                (stage / "config.yaml").write_bytes(CONFIG)
                # Execute the checked COPY, closing the replacement window on the caller's binary.
                executable = stage / "enola"
                executable.write_bytes(self.binary.read_bytes())
                if digest(executable.read_bytes()) != state["binary_hash"]:
                    raise MemoryInputError("provider binary changed before isolation")
                executable.chmod(0o500)
                args = [shutil.which("prlimit"), "--fsize=25000000", "--cpu=45", "--nofile=256", "--",
                        shutil.which("bwrap"), "--unshare-all", "--die-with-parent", "--new-session",
                        "--ro-bind", "/usr", "/usr", "--ro-bind", "/lib", "/lib", "--ro-bind", "/lib64", "/lib64",
                        "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--tmpfs", "/home",
                        "--dir", "/home/observer", "--dir", "/work", "--ro-bind", str(repo), "/work/repository",
                        "--bind", str(output), "/work/repository/.enola", "--ro-bind", str(stage / "config.yaml"),
                        "/work/config.yaml", "--ro-bind", str(executable), "/enola", "--clearenv",
                        "--setenv", "HOME", "/home/observer", "--setenv", "PATH", "/usr/bin",
                        "--setenv", "ENOLA_NO_UPDATE_CHECK", "1", "--setenv", "ENOLA_NO_PROMPTS", "1",
                        "--setenv", "GOMAXPROCS", "2", "--setenv", "GOMEMLIMIT", "512MiB",
                        "--chdir", "/work", "/enola", "--generate", "/work/config.yaml"]
                result, _ = bounded_run(args, env={"PATH": "/usr/bin:/bin"})
                if result:
                    raise MemoryInputError("provider execution or isolation failed")
                parsed = read_output(output, valid, self.lock)
        except (MemoryInputError, OSError, ValueError, TypeError, KeyError, RecursionError):
            return Observation("unavailable", coverage=coverage, problems=problems + [dict(code="provider-output-rejected")],
                               evidence=state)
        represented = {r.get("file") for r in parsed["records"] if r.get("kind") != "module"}
        for path in valid:
            # A syntactically valid empty file can have no facts. Do not call that full structural coverage.
            coverage.append(dict(path=path, status="available" if path in represented else "partial",
                                 reason="provider-facts" if path in represented else "no-file-facts"))
        quality = parsed["evidence"]["quality"]
        if quality["parse_errors"]:
            problems.append(dict(code="provider-parse-errors", count=quality["parse_errors"]))
        if quality["files_skipped"] or quality["census"]["skipped_with_cause"]:
            problems.append(dict(code="provider-skipped-sources"))
        status = "partial" if problems or any(c["status"] != "available" for c in coverage) else "available"
        return Observation(status, parsed["records"], parsed["insights"], sorted(coverage, key=lambda c: c["path"]),
                           problems, dict(state, receipt=parsed["evidence"]))
