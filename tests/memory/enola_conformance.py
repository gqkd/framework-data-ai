"""Explicit real-binary conformance. Never downloads or installs; not the offline suite."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from test_code_provider import (CodeMemory, API, WORKER, RULES, ROOT, fixture, enola,
                                models, graphs, code, sources)


class EnolaConformance(unittest.TestCase):
    setUpClass = classmethod(CodeMemory.setUpClass.__func__)
    project = CodeMemory.project
    bind = CodeMemory.bind
    build = CodeMemory.build

    def setUp(self):
        CodeMemory.setUp(self)
        self.provider = enola.EnolaProvider(self.binary)
        self.assertEqual(self.provider.status()["status"], "available", self.provider.status())

    def test_definitions_imports_calls_and_source_locations(self):
        result = self.provider.extract({
            "app.py": b"from helper import normalize\n\ndef response(value):\n    return normalize(value)\n",
            "helper.py": b"def normalize(value):\n    return value.strip()\n"})
        self.assertNotEqual(result.status, "unavailable", result.problems)
        symbols = {r["name"]: r for r in result.records if r["kind"] == "symbol"}
        self.assertEqual(symbols["app.response"]["line"], 3)
        self.assertTrue(any(r["kind"] == "dependency" and any(e["kind"] == "imports" for e in r.get("relations", []))
                            for r in result.records))
        calls = [r for r in symbols["app.response"]["relations"] if r["kind"] == "calls"]
        self.assertTrue(any(r.get("target_id") == symbols["helper.normalize"]["id"] for r in calls))

    def test_parse_failure_is_visible_and_invalid_symbols_are_not_projected(self):
        result = self.provider.extract({"ok.py": b"def ok(): return 1\n", "broken.py": b"def broken(:\n return missing(\n"})
        self.assertEqual(result.status, "partial")
        self.assertTrue(any(p["code"] == "parse-error" for p in result.problems))
        self.assertFalse(any(r.get("file") == "broken.py" for r in result.records))
        self.assertEqual(result.evidence["receipt"]["quality"]["files_seen"], 1)

    def test_all_invalid_and_unsupported_is_unavailable(self):
        result = self.provider.extract({"broken.py": b"def :", "types.ts": b"export const a=1;"})
        self.assertEqual(result.status, "unavailable")
        self.assertEqual({c["status"] for c in result.coverage}, {"unsupported", "unavailable"})

    def test_same_bytes_twice_ignore_wallclock_and_random_staging_paths(self):
        files = {"app.py": b"def run(value): return external(value)\n"}
        first = self.provider.extract(files)
        second = self.provider.extract(files)
        self.assertNotEqual(first.status, "unavailable", first.problems)
        self.assertEqual(models.canonical(vars(first)), models.canonical(vars(second)))

    def test_frozen_multirepository_fixture_retains_external_unknowns(self):
        root = self.project()
        result = self.build(root, self.provider)
        graph = result.graph
        self.assertEqual(len(graph["repositories"]), 3)
        self.assertTrue(graph["records"])
        self.assertTrue(any(e["resolution"] == "unresolved" for e in graph["edges"]))
        for edge in graph["edges"]:
            if edge["target"]:
                nodes = {n["id"]: n for n in graph["nodes"]}
                self.assertEqual(nodes[edge["source"]]["repository"], nodes[edge["target"]]["repository"])
        self.assertTrue(any(c["status"] == "unsupported" for r in graph["repositories"] for c in r["coverage"]))
        result.publish()

    def test_tests_generated_and_vendor_are_not_implicitly_excluded(self):
        files = {"tests/test_app.py": b"def test_app(): assert True\n", "vendor/util.py": b"def util(): return 1\n",
                 "generated/schema.py": b"# Code generated automatically. Do not edit.\ndef schema(): return 1\n"}
        result = self.provider.extract(files)
        self.assertNotEqual(result.status, "unavailable", result.problems)
        self.assertEqual({c["path"] for c in result.coverage}, set(files))
        self.assertTrue(all(c["status"] == "available" for c in result.coverage), result.coverage)

    def test_repository_config_hooks_and_source_side_effects_are_not_executed(self):
        root = self.project()
        repo = root / "code/alpha-api"
        sentinel = self.case / "DO-NOT-CREATE"
        (repo / "mcp-arch.yaml").write_text("providers:\n - name: unsafe\n   command: [touch, " + str(sentinel) + "]\n")
        (repo / "enola-intent.yaml").write_text("intentionally not an accepted configuration")
        hook = repo / ".git/hooks/pre-commit"
        hook.parent.mkdir(exist_ok=True)
        hook.write_text("#!/bin/sh\ntouch " + str(sentinel) + "\n")
        hook.chmod(0o700)
        (repo / "service.py").write_text("from pathlib import Path\nPath(" + repr(str(sentinel)) + ").touch()\ndef response(): return 1\n")
        before = {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
        commands = []
        original = enola.bounded_run
        def inspect(argv, **kwargs):
            commands.append(argv)
            return original(argv, **kwargs)
        with patch.object(enola, "bounded_run", inspect):
            result = self.build(root, self.provider, repositories=[API])
        self.assertTrue(result.graph["records"])
        self.assertFalse(sentinel.exists())
        after = {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertTrue(commands)
        self.assertTrue(all("--unshare-all" in argv and "--clearenv" in argv and "--generate" in argv for argv in commands))
        self.assertFalse((repo / ".enola").exists())

    def test_cli_code_is_json_and_preserves_documentary_commands(self):
        root = self.project()
        for command, extra in (("code", ["--dry-run", "--repository", API, "--enola", str(self.binary)]),
                               ("code", ["--dry-run", "--repository", API]), ("query", ["--product", "alpha"])):
            run = subprocess.run([sys.executable, "-B", str(ROOT / "memory.py"), command, "--root", str(root), *extra],
                                 capture_output=True, text=True, timeout=60)
            self.assertFalse(run.stderr)
            result = json.loads(run.stdout)
            if command == "query":
                self.assertEqual(run.returncode, 0)
                self.assertEqual(result["code_observation"], "not_requested")
            elif "--enola" not in extra:
                self.assertEqual(run.returncode, 2)
                self.assertEqual(result["coverage"], "unavailable")
            else:
                self.assertIn(run.returncode, (0, 1), result)
                self.assertTrue(result["nodes"])
        self.assertFalse((root / "_meta/memory").exists())

    def test_missing_worktree_can_be_observed_at_explicit_commit(self):
        root = self.project()
        repo = root / "code/alpha-api"
        commit = fixture.git(repo, "rev-parse", "HEAD").strip()
        (repo / "service.py").unlink()
        result = self.build(root, self.provider, repositories=[API], mode="git", revision=commit)
        self.assertTrue(any(n.get("file") == "service.py" and n["kind"] == "symbol" for n in result.graph["nodes"]))
        self.assertEqual(result.inputs["repositories"][API]["commit"], commit)
        self.assertFalse((repo / "service.py").exists())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enola", type=Path, required=True)
    args = parser.parse_args()
    EnolaConformance.binary = args.enola.resolve()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EnolaConformance)
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
