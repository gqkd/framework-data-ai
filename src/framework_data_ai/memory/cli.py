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
    for name in ("doctor", "build", "query"):
        command = commands.add_parser(name)
        command.add_argument("--root", type=Path, required=True)
        command.add_argument("--json", action="store_true", help="JSON is also the default output")
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
        if args.command == "doctor":
            workspace = Workspace.open(args.root)
            local = workspace.local_bindings()
            result = dict(command="doctor", status="available", document_repository=workspace.config["document_repository"],
                          selected_paths=len(workspace.paths()), local_binding_count=len(local),
                          code_provider="not_requested; integration belongs to phase 3",
                          search=dict(literal=True, sqlite_fts5=fts5_available()),
                          ignored_paths=[".framework-memory/local.yaml", "_meta/memory/"],
                          limitations=["doctor does not validate artifacts or observe code",
                                       "local repository bindings are counted, not opened or exported"])
        else:
            snapshot = capture(args.root)
            graph = build(snapshot)
            if args.command == "build":
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
        return 1 if result.get("coverage") == "partial" else 0
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
