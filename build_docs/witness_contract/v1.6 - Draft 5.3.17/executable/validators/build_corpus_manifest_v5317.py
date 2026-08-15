#!/usr/bin/env python3
"""Deterministically rebuild the path-bound 5.3.17 whole-corpus manifest."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "validation"))

from identity import canonical_bytes, corpus_file_id, duoid  # noqa: E402

MANIFEST_NAME = "MANIFEST_v1_6_draft_5_3_17.json"
EXCLUDED_NAMES = {MANIFEST_NAME, "VALIDATION_REPORT.json"}


def corpus_files(root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file()
            and path.name not in EXCLUDED_NAMES
            and "__pycache__" not in path.parts
        ),
        key=lambda path: path.relative_to(root).as_posix(),
    )


def build_manifest(root: Path) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    for path in corpus_files(root):
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        entries.append(
            {
                "file_id": corpus_file_id(relative, data),
                "path": relative,
                "size_bytes": len(data),
            }
        )
    return {
        "contract_version": "v1.6-draft-5.3.17",
        "corpus_root_id": duoid(
            "DUOTRONIC/CORPUS-ROOT/v1",
            canonical_bytes(entries),
        ),
        "file_count": len(entries),
        "files": entries,
        "manifest_version": "corpus_manifest/v10",
        "path_binding": True,
    }


def write_atomic(path: Path, value: dict[str, object]) -> None:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        indent=2,
    ) + "\n"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = build_manifest(root)
    path = root / MANIFEST_NAME
    if args.check:
        current = json.loads(path.read_text(encoding="utf-8"))
        if current != manifest:
            print("manifest is stale", file=sys.stderr)
            return 1
    else:
        write_atomic(path, manifest)
    print(
        json.dumps(
            {
                "corpus_root_id": manifest["corpus_root_id"],
                "file_count": manifest["file_count"],
                "manifest": str(path),
                "status": "current" if args.check else "rebuilt",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
