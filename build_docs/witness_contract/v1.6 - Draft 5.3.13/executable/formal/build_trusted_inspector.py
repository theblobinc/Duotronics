#!/usr/bin/env python3
"""Reproducibly build and compare the dedicated trusted-inspector target."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executable/runtime"))
from proof_authority import canonical_bytes, run_bounded_process, sha256_file  # noqa: E402

TARGET = "witnessAuthorityInspector"
OUTPUT = Path(".lake/build/bin") / TARGET
SOURCE_ROOT = Path("formal/draft5_3_6/lean")


def tree_hash(root: Path) -> str:
    records = []
    for path in sorted(root.rglob("*.lean")):
        records.append([path.relative_to(root).as_posix(), sha256_file(path)])
    return hashlib.sha256(canonical_bytes(records)).hexdigest()


def build_once(lake: str) -> tuple[str | None, dict]:
    with tempfile.TemporaryDirectory(prefix="wc-inspector-build-") as temporary:
        copy = Path(temporary) / "source"
        copy.mkdir()
        shutil.copy2(ROOT / "lakefile.lean", copy / "lakefile.lean")
        shutil.copy2(ROOT / "lean-toolchain", copy / "lean-toolchain")
        selected_source = copy / SOURCE_ROOT
        selected_source.parent.mkdir(parents=True)
        shutil.copytree(ROOT / SOURCE_ROOT, selected_source)
        result = run_bounded_process(
            (lake, "build", TARGET), cwd=copy,
            env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC", "SOURCE_DATE_EPOCH": "0"},
            timeout_seconds=600,
        )
        output = copy / OUTPUT
        return (sha256_file(output) if result.returncode == 0 and output.is_file() else None), {
            "returncode": result.returncode, "timed_out": result.timed_out,
            "output_limit_exceeded": result.output_limit_exceeded,
            "stdout_sha256": result.stdout_sha256, "stderr_sha256": result.stderr_sha256,
        }


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--json", action="store_true")
    args = parser.parse_args(); lake = shutil.which("lake")
    result = {
        "schema_version": "trusted_inspector_reproducible_build/v1", "target": TARGET,
        "toolchain": (ROOT / "lean-toolchain").read_text(encoding="utf-8").strip(),
        "source_root": SOURCE_ROOT.as_posix(),
        "source_tree_sha256": tree_hash(ROOT / SOURCE_ROOT),
        "build_command": ["lake", "build", TARGET], "lake_available": bool(lake),
        "builds": [], "output_binary_sha256": None, "status": "not_run",
    }
    code = 2
    if lake:
        first_hash, first = build_once(lake); second_hash, second = build_once(lake)
        result["builds"] = [first, second]
        if first_hash and first_hash == second_hash:
            result["output_binary_sha256"] = first_hash; result["status"] = "passed"; code = 0
        else:
            result["status"] = "failed"; code = 1
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else result["status"])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
