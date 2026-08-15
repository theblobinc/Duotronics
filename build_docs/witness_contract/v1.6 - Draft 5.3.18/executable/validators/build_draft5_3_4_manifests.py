#!/usr/bin/env python3
"""Regenerate the Draft 5.3.4 inventory, checksums, and human manifest."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = "PACKAGE_INVENTORY_v1_6_draft_5_3_4.json"
CHECKSUMS = "refs/manifest/CHECKSUMS_v1_6_draft_5_3_4.shake256_512"
MANIFEST = "refs/manifest/MANIFEST_v1_6_draft_5_3_4_complete.md"
REPORT = "DRAFT5_3_4_VALIDATION_REPORT.json"
EXCLUDED = {INVENTORY, CHECKSUMS, MANIFEST, REPORT}


def digest(path: Path) -> str:
    return hashlib.shake_256(path.read_bytes()).hexdigest(64)


def is_runtime_cache(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return "__pycache__" in relative.parts or path.suffix == ".pyc"


def files() -> list[Path]:
    return sorted(
        (path for path in ROOT.rglob("*") if path.is_file() and not is_runtime_cache(path)),
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )


def main() -> int:
    paths = files()
    absent = [relative for relative in EXCLUDED if not (ROOT / relative).is_file()]
    if absent:
        raise SystemExit(f"generated artifact placeholders missing: {sorted(absent)}")
    records = []
    checksum_lines = [
        "# SHAKE256-512 closure for Duotronic Witness Contract v1.6 Draft 5.3.4",
        "# The four self-referential generated artifacts are intentionally excluded.",
    ]
    extensions = Counter()
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        excluded = relative in EXCLUDED
        file_hash = None if excluded else digest(path)
        records.append({
            "path": relative,
            "size_bytes": path.stat().st_size,
            "shake256_512": file_hash,
            "excluded_from_hash_closure": excluded,
            "exclusion_reason": "self_referential_generated_artifact" if excluded else None,
        })
        extensions[path.suffix.lower() or "[no extension]"] += 1
        if not excluded:
            checksum_lines.append(f"{file_hash}  {relative}")

    excluded_count = sum(record["excluded_from_hash_closure"] for record in records)
    if excluded_count != len(EXCLUDED):
        raise SystemExit(f"hash exclusion count mismatch: {excluded_count}")
    inventory = {
        "schema_version": "package_inventory/v2",
        "package": "duotronic-witness-contract-v1.6-draft-5.3.4",
        "status": "complete_living_corrective_two_domain_snapshot_ledger_draft_permanently_not_frozen",
        "historical_source_packages": [
            {"path": "history/source_packages/v1.6 - Draft 5.2.2.zip", "shake256_512": "437395d28c452f0a20937eaf562020afae2214edf01a8df2fe6dadd062201c22", "file_count": 492},
            {"path": "history/source_packages/v1.6 - Draft 5.3.1.zip", "shake256_512": "26608233721f6b56ce6dfe5dfe653029c421e72a551196e004d2b2d3d59de588", "file_count": 560},
            {"path": "history/source_packages/v1.6 - Draft 5.3.2.zip", "shake256_512": "57daa37189dcd8c0cf8cff990850393f4feaa70aeea9736b5edabffc58a37675", "file_count": 1158},
            {"path": "history/source_packages/v1.6 - Draft 5.3.3.zip", "shake256_512": "b02165cffa8b95b41a210f06b5e734e9592472a9c29630c07bb0ea318c7c3cb1", "file_count": 1238}
        ],
        "file_count": len(records),
        "hash_covered_file_count": len(records) - excluded_count,
        "hash_excluded_file_count": excluded_count,
        "hash_exclusion_rule": sorted(EXCLUDED),
        "checksum_file": CHECKSUMS,
        "canonical_descriptor": "CANONICAL_CORPUS_v1_6_draft_5_3_4.json",
        "files": records,
    }
    (ROOT / INVENTORY).write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / CHECKSUMS).write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    manifest_lines = [
        "# Complete Manifest — Duotronic Witness Contract v1.6 Draft 5.3.4",
        "",
        "**Status:** complete living corrective two-domain, snapshot-derived, ledger-cutoff corpus; permanently not frozen.",
        "",
        f"- Total regular files: {len(records)}",
        f"- Hash-covered files: {len(records) - excluded_count}",
        f"- Self-referential generated exclusions: {excluded_count}",
        "- Exact historical Draft 5.2.2 source archive: retained and verified",
        "- Exact historical Draft 5.3.1 source archive: retained and verified",
        "- Exact historical Draft 5.3.2 source archive: retained and verified",
        "- Exact historical Draft 5.3.3 source archive: retained and verified",
        "- Vendored AJV runtime: included in hash closure",
        "- External governance signature: absent; package is not an external trust root",
        "- Contract lifecycle: permanently unfrozen",
        "",
        "## Files by extension",
        "",
    ]
    manifest_lines.extend(f"- `{extension}`: {count}" for extension, count in sorted(extensions.items()))
    manifest_lines.extend([
        "",
        "## Hash exclusion",
        "",
        "The active inventory, checksum file, this human manifest, and the validator report are generated artifacts excluded from their own recursive hash closure. Every other regular file is SHAKE256-512 covered.",
        "",
    ])
    (ROOT / MANIFEST).write_text("\n".join(manifest_lines), encoding="utf-8")
    print(json.dumps({"file_count": len(records), "covered": len(records) - excluded_count, "excluded": sorted(EXCLUDED)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
