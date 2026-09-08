"""Replaceable observation boundary: entities and direct edges, never impact policy."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class Capabilities:
    name: str
    version: str
    languages: tuple[str, ...]
    direct_edges: tuple[str, ...]
    profile: str


@dataclass
class Observation:
    status: str  # available / partial / unavailable; never an assertion of no impact
    records: list[dict] = field(default_factory=list)
    insights: list[dict] = field(default_factory=list)
    coverage: list[dict] = field(default_factory=list)
    problems: list[dict] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)


class CodeProvider(Protocol):
    capabilities: Capabilities

    def status(self) -> dict: ...

    def extract(self, files: dict[str, bytes]) -> Observation:
        """Observe captured bytes, not a mutable checkout; return direct facts with locations."""
        ...


class FakeProvider:
    """Controllable conformance double; not a parser and never exposed as a CLI provider."""
    capabilities = Capabilities("fake", "1", ("python",), ("calls", "imports", "declares"), "test-only")

    def __init__(self, observe=None, *, available=True):
        self.observe, self.available, self.calls = observe, available, 0

    def status(self):
        return {"status": "available" if self.available else "unavailable", "provider": "fake"}

    def extract(self, files):
        self.calls += 1
        if not self.available:
            return Observation("unavailable", problems=[{"code": "provider-unavailable"}])
        if self.observe:
            return self.observe(files)
        return Observation("available", coverage=[{"path": path, "status": "available"}
                                                   for path in sorted(files)])
