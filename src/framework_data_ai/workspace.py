"""Read-only workspace selection. Local checkout bindings are never canonical input.

This phase does not visit code repositories. A declared path is not an observation.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import stat

import yaml

from .artifacts import document_selected, load_scan, skipped_dir
from .memory.models import FRAMEWORK, contract, validate


class MemoryInputError(ValueError):
    """A bounded, user-facing failure, without personal paths or source contents."""


def read_mapping(path: Path, label: str) -> dict:
    if path.is_symlink():
        raise MemoryInputError(f"{label}: symbolic links are not followed")
    if not path.exists():
        return {}
    try:
        info = path.stat()
        if not stat.S_ISREG(info.st_mode):
            raise MemoryInputError(f"{label}: expected a regular file")
        if info.st_size > 1000000:
            raise MemoryInputError(f"{label}: configuration exceeds 1 MB")
        result = yaml.safe_load(path.read_text(encoding="utf-8"))
        if result is None:
            return {}
        if not isinstance(result, dict):
            raise MemoryInputError(f"{label}: expected a mapping")
        return result
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise MemoryInputError(f"{label}: configuration could not be read") from error


def no_symlink_ancestors(root: Path, relative: Path) -> None:
    current = root
    for part in relative.parts:
        if part in ("", ".", ".."):
            raise MemoryInputError("unsafe output/configuration path")
        current = current / part
        if current.is_symlink():
            raise MemoryInputError("symbolic links are not followed in output/configuration paths")


@dataclass
class Workspace:
    root: Path
    registry: dict
    config: dict
    scan: dict

    @classmethod
    def open(cls, root: Path) -> Workspace:
        root = root.resolve()
        if not root.is_dir():
            raise MemoryInputError("documentation root is not a directory")
        no_symlink_ancestors(root, Path(".framework-memory/config.yaml"))
        registry = yaml.safe_load((FRAMEWORK / "schemas/artifact-types.yaml").read_text(encoding="utf-8"))
        config = {**contract()["defaults"],
                  **read_mapping(root / ".framework-memory/config.yaml", "memory config")}
        try:
            validate("config", config)
            project = read_mapping(root / "framework.yaml", "framework config")
            scan = load_scan(registry, project)
        except (ValueError, TypeError, AttributeError) as error:
            raise MemoryInputError("invalid memory or scan configuration") from error
        # The reserved runtime locations remain excluded even with skip_hidden: false.
        scan["skip_dirs"] |= {".git", ".framework-memory", "_meta/memory"}
        config["classifications"] = sorted(config["classifications"])
        config["exclude"] = sorted(config["exclude"])
        return cls(root, registry, config, scan)

    def local_bindings(self) -> dict:
        no_symlink_ancestors(self.root, Path(".framework-memory/local.yaml"))
        value = read_mapping(self.root / ".framework-memory/local.yaml", "local bindings")
        validate("local", value)
        return value.get("checkouts", {})

    def paths(self) -> list[Path]:
        """Prune excluded trees before visiting them. Never follow links into code/data."""
        result = []
        excluded = set(self.config["exclude"])

        def denied(relative):
            return any(relative.as_posix() == item or relative.as_posix().startswith(item + "/")
                       for item in excluded)

        def walk_error(_):
            raise MemoryInputError("a selected directory cannot be read")

        for directory, dirs, files in os.walk(self.root, followlinks=False, onerror=walk_error):
            parent = Path(directory)
            selected_dirs = []
            for name in sorted(dirs):
                path = parent / name
                relative = path.relative_to(self.root)
                if (denied(relative) or skipped_dir(relative.parts, self.scan["skip_dirs"])
                        or (self.scan["skip_hidden"] and name.startswith("."))):
                    continue
                if path.is_symlink():
                    raise MemoryInputError("a selected directory is a symbolic link; exclude it explicitly")
                selected_dirs.append(name)
            dirs[:] = selected_dirs
            for name in sorted(files):
                path = parent / name
                relative = path.relative_to(self.root)
                if document_selected(relative, self.scan) and not denied(relative):
                    if path.is_symlink():
                        raise MemoryInputError("a selected source is a symbolic link; exclude it explicitly")
                    if not stat.S_ISREG(path.stat().st_mode):
                        raise MemoryInputError("a selected source is not a regular file")
                    result.append(path)
                    if len(result) > self.config["max_files"]:
                        raise MemoryInputError("selected sources exceed max_files; narrow the scan")
        return sorted(result)
