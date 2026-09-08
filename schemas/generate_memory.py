#!/usr/bin/env python3
"""Project memory-contracts.yaml to JSON Schema; no product artifact types added."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "_memory_schema_models", HERE.parent / "src/framework_data_ai/memory/models.py")
_models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_models)
artifact_field = _models.artifact_field


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rules = _models.contract()
    wanted = {HERE / "memory" / f"{name}.v1.json":
              json.dumps(_models.schema(name, rules), ensure_ascii=False, indent=2) + "\n"
              for name in rules["outputs"]}
    extra = set((HERE / "memory").glob("*.json")) - set(wanted)
    if extra:
        print("Unexpected generated memory schemas: " + ", ".join(p.name for p in sorted(extra)))
        return 1
    changed = [p for p, data in wanted.items()
               if not p.exists() or p.read_text(encoding="utf-8") != data]
    if args.check:
        for path in changed:
            print(f"out of date: {path.relative_to(HERE)}")
    else:
        for path, data in wanted.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data, encoding="utf-8", newline="\n")
    print(f"{len(wanted)} memory schemas; {len(changed)} " +
          ("out of date" if args.check else "regenerated changes"))
    return int(args.check and bool(changed))


if __name__ == "__main__":
    raise SystemExit(main())
