#!/usr/bin/env python3
"""Local documentary-memory CLI, usable directly from a complete framework checkout/export."""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
from pathlib import Path
import sys

FRAMEWORK = Path(__file__).resolve().parent
_name = "_framework_data_ai_" + hashlib.sha256(str(FRAMEWORK).encode()).hexdigest()[:16]
if _name not in sys.modules:
    _spec = importlib.util.spec_from_file_location(
        _name, FRAMEWORK / "src/framework_data_ai/__init__.py",
        submodule_search_locations=[str(FRAMEWORK / "src/framework_data_ai")])
    _module = importlib.util.module_from_spec(_spec)
    sys.modules[_name] = _module
    _spec.loader.exec_module(_module)
main = importlib.import_module(f"{_name}.memory.cli").main

if __name__ == "__main__":
    raise SystemExit(main())
