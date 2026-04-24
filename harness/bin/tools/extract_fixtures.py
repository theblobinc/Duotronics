"""Generate JSON twins of every YAML fixture pack and trace, for drift checks.

Usage:
  python tools/extract_fixtures.py            # rewrite JSON twins
  python tools/extract_fixtures.py --check    # exit 1 if drift detected
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml


ROOT = Path(__file__).resolve().parent.parent
TARGETS = (
    ROOT / "fixtures",
    ROOT / "golden_traces",
    ROOT / "meta_fixtures",
    ROOT / "meta_golden_traces",
)


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(yaml_path: Path) -> Path:
    data = _load_yaml(yaml_path)
    json_path = yaml_path.with_suffix(".json")
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return json_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    drift: list[str] = []
    rewritten = 0
    for directory in TARGETS:
        if not directory.exists():
            continue
        for yaml_path in sorted(directory.glob("*.yaml")):
            json_path = yaml_path.with_suffix(".json")
            yaml_data = _load_yaml(yaml_path)
            if args.check:
                if not json_path.exists():
                    drift.append(f"missing JSON twin: {json_path.relative_to(ROOT)}")
                    continue
                if _load_json(json_path) != yaml_data:
                    drift.append(f"drift: {yaml_path.relative_to(ROOT)} ↔ {json_path.relative_to(ROOT)}")
            else:
                _write_json(yaml_path)
                rewritten += 1

    if args.check:
        if drift:
            for line in drift:
                print(line, file=sys.stderr)
            return 1
        print("fixtures: no drift")
        return 0
    print(f"rewrote {rewritten} JSON twin(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
