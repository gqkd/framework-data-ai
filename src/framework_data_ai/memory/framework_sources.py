"""Read adopted rules, never execute them or substitute the runtime for a missing pin."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import stat

import yaml

from ..snapshots import ConcurrentChange
from ..workspace import MemoryInputError, no_symlink_ancestors, read_mapping
from .code_sources import git
from .models import FRAMEWORK, canonical, digest

SKILLS = ("start", "requirement", "resolve", "cycle", "audit", "release", "business")
BASE = ("FRAMEWORK.md", "references/preamble.md", "references/routing-table.md")
MAX_BYTES = 2_000_000


def local_bytes(root, relative):
    no_symlink_ancestors(root, Path(relative))
    path = root / relative
    if not stat.S_ISREG(path.stat().st_mode):
        raise MemoryInputError("framework source is not a regular file")
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise MemoryInputError("framework source exceeds the read bound")
    return data


@dataclass
class FrameworkSources:
    root: Path
    project: Path
    skill: str | None
    result: dict

    def assert_unchanged(self):
        if capture_framework(self.project, root=self.root, skill=self.skill).result != self.result:
            raise ConcurrentChange("adopted framework sources changed during context assembly")


def capture_framework(project, *, root=FRAMEWORK, skill=None):
    root, project = Path(root).resolve(), Path(project).resolve()
    if skill is not None and skill not in SKILLS:
        raise MemoryInputError("unknown framework skill")
    no_symlink_ancestors(project, Path("framework.yaml"))
    config = read_mapping(project / "framework.yaml", "framework adoption")
    version, commit = config.get("framework_version"), config.get("framework_commit")
    result = dict(version=version if isinstance(version, str) else None,
                  commit=commit if isinstance(commit, str) else None,
                  resolution="unavailable", sources=[], gaps=[])
    paths = [*BASE, *([f"skills/{skill}/SKILL.md"] if skill else [])]

    def read(relative):
        if commit:
            entry = git(root, "ls-tree", commit, "--", relative).decode("utf-8").strip()
            if not entry.startswith("100644 blob ") and not entry.startswith("100755 blob "):
                raise MemoryInputError("adopted framework source is absent or not a regular Git blob")
            return git(root, "show", f"{commit}:{relative}", limit=MAX_BYTES)
        return local_bytes(root, relative)

    try:
        if not isinstance(version, str) or not version:
            raise MemoryInputError("framework version is not declared")
        if commit is not None:
            if not isinstance(commit, str) or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", commit):
                raise MemoryInputError("framework pin must be a full commit ID")
            if git(root, "rev-parse", "--verify", f"{commit}^{{commit}}").decode().strip() != commit:
                raise MemoryInputError("framework pin is not a commit")
        registry = yaml.safe_load(read("schemas/artifact-types.yaml"))
        if not isinstance(registry, dict) or registry.get("version") != version:
            raise MemoryInputError("available framework rules do not match the adopted version")
        result["resolution"] = "pinned-commit" if commit else "version-only-unverified"
        # New operational guidance is optional for historical versions; never import it
        # from today's runtime into a pinned old rule set.
        try:
            optional = read("references/operational-memory.md")
        except (OSError, MemoryInputError):
            optional = None
        for relative in [*paths, *(["references/operational-memory.md"] if optional is not None else [])]:
            try:
                data = optional if relative == "references/operational-memory.md" else read(relative)
                text = data.decode("utf-8").replace("\r\n", "\n")
                revision = "sha256:" + digest(data)
                result["sources"].append(dict(id="framework-source:" + digest(canonical([relative, revision, commit])),
                                              path=relative, revision=revision, lines=max(1, len(text.splitlines())),
                                              text=text, role="adopted-framework-rules-not-authority-verification"))
            except (OSError, UnicodeError, MemoryInputError):
                result["gaps"].append(dict(path=relative, reason="adopted-source-unavailable"))
        if optional is None and any("references/operational-memory.md" in source["text"]
                                    for source in result["sources"]):
            result["gaps"].append(dict(path="references/operational-memory.md",
                                       reason="referenced-adopted-source-unavailable"))
        if not commit:
            result["gaps"].append(dict(path="framework.yaml", reason="version-only-does-not-pin-rule-bytes"))
    except (OSError, UnicodeError, yaml.YAMLError, MemoryInputError):
        result["gaps"].append(dict(path="framework.yaml", reason="adopted-rules-unavailable-or-pin-mismatch"))
    return FrameworkSources(root, project, skill, result)
