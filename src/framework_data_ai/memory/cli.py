"""CLI implementations. stdout is JSON; errors are bounded and never echo private config."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import jsonschema

from ..snapshots import capture, publish
from ..workspace import MemoryInputError, Workspace
from .graph import build
from .models import canonical
from .query import query
from .search import fts5_available


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    readings = commands.add_parser("readings", help="validate caller-reported readings; never attest understanding")
    readings.add_argument("--pack", type=Path, required=True)
    readings.add_argument("--claims", type=Path, required=True)
    for name in ("doctor", "gaps", "build", "query", "code", "context", "impact", "view"):
        command = commands.add_parser(name)
        command.add_argument("--root", type=Path, required=True)
        command.add_argument("--json", action="store_true", help="JSON is also the default output")
        if name == "view":
            command.add_argument("--code-snapshot", type=Path, help="explicit captured bundle; never execute a provider")
            command.add_argument("--hypotheses", type=Path, help="explicit inferred annotations, never constraints")
            command.add_argument("--dry-run", action="store_true", help="validate and render without publishing")
        if name in ("context", "impact"):
            command.add_argument("--change", help="one CHG ID or source path; not an approval")
            command.add_argument("--hops", type=int, default=2)
        if name == "context":
            command.add_argument("--goal", required=True)
            command.add_argument("--mode", choices=("analysis", "proposal", "implement"), default="analysis")
            command.add_argument("--product", action="append")
            command.add_argument("--node")
            command.add_argument("--reconsider", action="store_true", help="require full Alternatives sections")
            command.add_argument("--text-budget", type=int, default=100000, help="characters delivered; required_sources never ranked out")
            command.add_argument("--skill", choices=("start", "requirement", "resolve", "cycle", "audit", "release", "business"))
            command.add_argument("--framework-root", type=Path, help="explicit local source of adopted rule bytes; never fetched")
            command.add_argument("--code-snapshot", type=Path, help="published code snapshot directory; no provider execution")
            command.add_argument("--hypotheses", type=Path, help="explicit inferred assertions, never constraints")
        if name == "impact":
            command.add_argument("--before", type=Path, help="published baseline code snapshot directory")
            command.add_argument("--after", type=Path, help="published proposed code snapshot directory")
            command.add_argument("--limit", type=int, default=100)
            command.add_argument("--direction", choices=("dependents", "dependencies", "both"), default="dependents")
        if name in ("doctor", "code"):
            command.add_argument("--enola", type=Path, help="explicit already-installed pinned executable; never downloaded")
        if name == "code":
            command.add_argument("--repository", action="append", help="qualified declared repository ID; default: all")
            command.add_argument("--source", choices=("worktree", "git"), default="worktree")
            command.add_argument("--revision", help="full commit ID; required for --source git and exactly one repository")
            command.add_argument("--include-untracked", action="store_true", help="explicitly include nonignored untracked Python")
            command.add_argument("--dry-run", action="store_true", help="do not publish; isolated temporary execution still occurs")
        if name == "build":
            command.add_argument("--dry-run", action="store_true", help="validate/export without writing")
            command.add_argument("--export", action="store_true", help="emit the complete canonical graph")
        if name == "query":
            search = command.add_mutually_exclusive_group()
            search.add_argument("--text")
            search.add_argument("--node")
            command.add_argument("--product")
            command.add_argument("--limit", type=int)
            command.add_argument("--hops", type=int, default=0)
            command.add_argument("--relation", action="append")
            command.add_argument("--search-engine", choices=("literal", "fts5"), default="literal")
    args = parser.parse_args(argv)
    try:
        if args.command == "readings":
            from .context import reading_report
            from .operational_io import read_json
            result = reading_report(read_json(args.pack), read_json(args.claims))
        elif args.command == "doctor":
            workspace = Workspace.open(args.root)
            local = workspace.local_bindings()
            from .providers.enola import EnolaProvider
            result = dict(command="doctor", status="available", document_repository=workspace.config["document_repository"],
                          selected_paths=len(workspace.paths()), local_binding_count=len(local),
                          code_provider=EnolaProvider(args.enola).status(),
                          search=dict(literal=True, sqlite_fts5=fts5_available()),
                          ignored_paths=[".framework-memory/local.yaml", "_meta/memory/"],
                          limitations=["doctor does not validate artifacts or observe code",
                                       "local repository bindings are counted, not opened or exported"])
        else:
            snapshot = capture(args.root)
            graph = build(snapshot)
            if args.command == "view":
                from .viewer import export
                from .operational_io import load_code, read_json
                result = export(snapshot, graph, code=load_code(args.code_snapshot) if args.code_snapshot else None,
                                hypotheses=read_json(args.hypotheses) if args.hypotheses else None,
                                dry_run=args.dry_run)
            elif args.command == "gaps":
                from .adoption import assess
                result = assess(snapshot, graph)
            elif args.command == "context":
                from .context import compose
                from .models import FRAMEWORK
                from .operational_io import load_code, read_json
                result = compose(snapshot, graph, goal=args.goal, mode=args.mode, products=args.product,
                                 change=args.change, selector=args.node, reconsider=args.reconsider,
                                 budget=args.text_budget, hops=args.hops, skill=args.skill,
                                 framework_root=args.framework_root or FRAMEWORK,
                                 code=load_code(args.code_snapshot) if args.code_snapshot else None,
                                 hypotheses=read_json(args.hypotheses) if args.hypotheses else None)
            elif args.command == "impact":
                from .impact import compare
                from .operational_io import load_code
                result = compare(snapshot, graph, change=args.change, hops=args.hops, limit=args.limit,
                                 direction=args.direction,
                                 before=load_code(args.before) if args.before else None,
                                 after=load_code(args.after) if args.after else None)
            elif args.command == "code":
                from .code_graph import build_code
                from .providers.enola import EnolaProvider
                code = build_code(snapshot, graph, EnolaProvider(args.enola), repositories=args.repository,
                                  mode=args.source, revision=args.revision, include_untracked=args.include_untracked)
                if not args.dry_run:
                    code.publish()
                result = code.graph
            elif args.command == "build":
                if not args.dry_run:
                    publish(snapshot, graph)
                result = graph if args.export else dict(
                    command="build", snapshot=snapshot.id, coverage=graph["coverage"],
                    written=not args.dry_run,
                    output=f"_meta/memory/snapshots/{snapshot.id}/" if not args.dry_run else None,
                    nodes=len(graph["nodes"]), edges=len(graph["edges"]),
                    issues=graph["issues"], gaps=graph["gaps"], code_observation="not_requested")
            else:
                result = query(snapshot, graph, text=args.text, selector=args.node, product=args.product,
                               limit=args.limit, hops=args.hops, relations=args.relation,
                               engine=args.search_engine)
                snapshot.assert_unchanged()
        sys.stdout.write(canonical(result).decode("utf-8"))
        if result.get("status") == "incomplete":
            return 1
        return {"partial": 1, "unavailable": 2}.get(result.get("coverage"), 0)
    except MemoryInputError as error:
        sys.stdout.write(canonical(dict(status="unavailable", error=str(error))).decode("utf-8"))
        return 2
    except (jsonschema.ValidationError, jsonschema.SchemaError, OSError, ValueError, TypeError,
            KeyError, AttributeError, RecursionError):
        # Don't print jsonschema's exception: it includes the rejected instance, possibly
        # local paths/credentials. Detailed source problems belong in sanitized graph issues.
        sys.stdout.write(canonical(dict(status="unavailable", error="input or output contract failed; no result claimed")).decode("utf-8"))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
