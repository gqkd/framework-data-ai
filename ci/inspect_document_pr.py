#!/usr/bin/env python3
"""Run the explicit documentary-PR controller from this pinned framework checkout."""
import hashlib
import importlib
import importlib.util
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
name = "_framework_data_ai_" + hashlib.sha256(str(root).encode()).hexdigest()[:16]
if name not in sys.modules:
    spec = importlib.util.spec_from_file_location(name, root / "src/framework_data_ai/__init__.py",
             submodule_search_locations=[str(root / "src/framework_data_ai")])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
main = importlib.import_module(name + ".contribution_ci").main

if __name__ == "__main__":
    raise SystemExit(main())
