"""Print the active harness spec target and schema selection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness_lib.schema_versions import resolve_schema_snapshot, spec_target_for


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema-version", default=None)
    parser.add_argument("--target-schema-version", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    selected = args.schema_version
    target = args.target_schema_version or selected
    snapshot = resolve_schema_snapshot(selected)
    spec_target = spec_target_for(selected)
    payload = {
        "spec_target": spec_target,
        "selection": {
            "schema_version": selected,
            "target_schema_version": target,
        },
        "snapshot": snapshot,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print("spec target:")
    for key, value in spec_target.items():
        print(f"  {key}: {value}")
    print("schema selection:")
    print(f"  source: {selected}")
    print(f"  target: {target}")
    print("registry snapshot:")
    for key, value in snapshot.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())