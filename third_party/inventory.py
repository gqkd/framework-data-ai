#!/usr/bin/env python3
"""Generate the small integration inventory from the lock/manifest; not a binary SBOM."""
import argparse
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def render():
    lock = json.loads((ROOT / "providers.lock.json").read_text(encoding="utf-8"))
    manifest = yaml.safe_load((ROOT / "third_party/manifest.yaml").read_text(encoding="utf-8"))
    result = dict(schema="framework-memory/integration-inventory/v1", scope="direct-integration-not-transitive-SBOM",
                  providers={k: v for k, v in lock.items() if k != "schema"},
                  incorporated_code=manifest["incorporated_code"], host_requirements=manifest["host_requirements"])
    return json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = ROOT / "third_party/inventory.json"
    content = render()
    changed = not target.exists() or target.read_text(encoding="utf-8") != content
    if args.check:
        print("integration inventory " + ("out of date" if changed else "current"))
    else:
        target.write_text(content, encoding="utf-8", newline="\n")
        print("integration inventory generated")
    return int(args.check and changed)


if __name__ == "__main__":
    raise SystemExit(main())
