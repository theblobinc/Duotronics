#!/usr/bin/env python3
"""Regenerate the Draft 5.3.1 inventory, checksums, and human manifest."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = "PACKAGE_INVENTORY_v1_6_draft_5_3_1.json"
CHECKSUMS = "refs/manifest/CHECKSUMS_v1_6_draft_5_3_1.sha256"
MANIFEST = "refs/manifest/MANIFEST_v1_6_draft_5_3_1_complete.md"
REPORT = "DRAFT5_3_1_VALIDATION_REPORT.json"
EXCLUDED = {INVENTORY, CHECKSUMS, MANIFEST, REPORT}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files() -> list[Path]:
    return sorted(
        (path for path in ROOT.rglob("*") if path.is_file() and "node_modules" not in path.relative_to(ROOT).parts),
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )


def main() -> int:
    paths = files()
    records = []
    checksum_lines = ["# SHA-256 closure for Duotronic Witness Contract v1.6 Draft 5.3.1", "# Generated artifacts named in the inventory are intentionally excluded from recursive closure."]
    extensions = Counter()
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        excluded = relative in EXCLUDED
        file_hash = None if excluded else digest(path)
        records.append({
            "path": relative,
            "size_bytes": path.stat().st_size,
            "sha256": file_hash,
            "excluded_from_hash_closure": excluded,
            "exclusion_reason": "self_referential_generated_artifact" if excluded else None,
        })
        extensions[path.suffix.lower() or "[no extension]"] += 1
        if not excluded:
            checksum_lines.append(f"{file_hash}  {relative}")

    inventory = {
        "schema_version": "package_inventory/v2",
        "package": "duotronic-witness-contract-v1.6-draft-5.3.1",
        "status": "complete_corrective_draft_not_frozen",
        "base_package": "v1.6 - Draft 5.2.2.zip",
        "base_package_sha256": "437395d28c452f0a20937eaf562020afae2214edf01a8df2fe6dadd062201c22",
        "file_count": len(records),
        "hash_covered_file_count": len(records) - len(EXCLUDED),
        "hash_excluded_file_count": len(EXCLUDED),
        "hash_exclusion_rule": sorted(EXCLUDED),
        "checksum_file": CHECKSUMS,
        "canonical_descriptor": "CANONICAL_CORPUS_v1_6_draft_5_3_1.json",
        "files": records,
    }
    (ROOT / INVENTORY).write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / CHECKSUMS).write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    manifest_lines = [
        "# Complete Manifest — Duotronic Witness Contract v1.6 Draft 5.3.1",
        "",
        "**Status:** complete corrective development corpus; not frozen.",
        "",
        f"- Total regular files: {len(records)}",
        f"- Hash-covered files: {len(records) - len(EXCLUDED)}",
        f"- Self-referential generated exclusions: {len(EXCLUDED)}",
        "- Historical Draft 5.2.2 source files: 492, plus the exact retained source ZIP",
        "- External release signature: absent by design; freeze prohibited",
        "",
        "## Files by extension",
        "",
    ]
    manifest_lines.extend(f"- `{ext}`: {count}" for ext, count in sorted(extensions.items()))
    manifest_lines.extend(["", "## Hash exclusion", "", "The inventory, checksum file, this human manifest, and the validator report are generated artifacts excluded from their own recursive hash closure. Every other file is SHA-256 covered.", ""])
    (ROOT / MANIFEST).write_text("\n".join(manifest_lines), encoding="utf-8")
    print(json.dumps({"file_count": len(records), "covered": len(records)-len(EXCLUDED), "excluded": sorted(EXCLUDED)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
