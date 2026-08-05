#!/usr/bin/env python3
"""Build final-byte provenance, inventory, checksum, and manifest for Draft 5.3.16."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = "PACKAGE_INVENTORY_v1_6_draft_5_3_16.json"
CHECKSUMS = "refs/manifest/CHECKSUMS_v1_6_draft_5_3_16.sha256"
MANIFEST = "refs/manifest/MANIFEST_v1_6_draft_5_3_16_complete.md"
REPORT = "DRAFT5_3_16_VALIDATION_REPORT.json"
PROVENANCE = "PACKAGE_PROVENANCE_v1_6_draft_5_3_16.json"
REVIEW = "refs/review/v1.6_draft_5.3.16_update_checklist.md"
RECURSIVE_EXCLUDED = {INVENTORY, CHECKSUMS, MANIFEST, REPORT}
SOURCE_DIGEST_EXCLUDED = RECURSIVE_EXCLUDED | {PROVENANCE}
def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def is_runtime_cache(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return "__pycache__" in relative.parts or path.suffix == ".pyc"


def files() -> list[Path]:
    return sorted(
        (path for path in ROOT.rglob("*") if path.is_file() and not is_runtime_cache(path)),
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )


def tree_digest(paths: list[Path], excluded: set[str]) -> str:
    value = hashlib.sha256()
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        if relative in excluded:
            continue
        encoded = relative.encode("utf-8")
        value.update(len(encoded).to_bytes(8, "big"))
        value.update(encoded)
        value.update(bytes.fromhex(digest(path)))
        value.update(path.stat().st_size.to_bytes(8, "big"))
    return value.hexdigest()


def write_provenance() -> None:
    current = files()
    generator = Path(__file__).relative_to(ROOT).as_posix()
    record = {
        "schema_version": "package_provenance/v1",
        "package_version": "v1.6-draft-5.3.16",
        "provenance_status": "unpublished_workspace",
        "source_repository": "https://github.com/TBI-Contracting/duotronic-witness-contract",
        "source_ref": None,
        "source_commit_sha": None,
        "source_subtree_path": ".",
        "source_subtree_sha256": tree_digest(current, SOURCE_DIGEST_EXCLUDED),
        "source_digest_exclusions": sorted(SOURCE_DIGEST_EXCLUDED),
        "generator_name": generator,
        "generator_version": "draft5_3_16_manifest_builder/v1",
        "generator_sha256": digest(ROOT / generator),
        "source_generation": "v1.6-draft-5.3.15",
        "base_revision": "v1.6-draft-5.3.15",
        "transformation_change_set": REVIEW,
        "transformation_change_set_sha256": digest(ROOT / REVIEW),
        "workspace_status": "unpublished_workspace",
        "workspace_clean": False,
        "reproducibility_class": "portable_corpus_rebuildable_from_supplied_files_but_not_committed_source_activation_ready",
        "activation_effect": "committed_source_provenance_gate_incomplete",
    }
    (ROOT / PROVENANCE).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    write_provenance()
    paths = files()
    absent = [relative for relative in RECURSIVE_EXCLUDED if not (ROOT / relative).is_file()]
    if absent:
        raise SystemExit(f"generated artifact placeholders missing: {sorted(absent)}")
    records: list[dict] = []
    checksums = [
        "# SHA-256 closure for Duotronic Witness Contract v1.6 Draft 5.3.16",
        "# Four recursive generated artifacts have explicit null hash/size fields in the inventory.",
    ]
    extensions = Counter()
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        excluded = relative in RECURSIVE_EXCLUDED
        file_hash = None if excluded else digest(path)
        records.append({
            "path": relative,
            "size_bytes": None if excluded else path.stat().st_size,
            "sha256": file_hash,
            "excluded_from_hash_closure": excluded,
            "excluded_fields": ["sha256", "size_bytes"] if excluded else [],
            "exclusion_reason": "recursive_generated_artifact_describes_package_closure" if excluded else None,
        })
        extensions[path.suffix.lower() or "[no extension]"] += 1
        if not excluded:
            checksums.append(f"{file_hash}  {relative}")
    excluded_count = sum(record["excluded_from_hash_closure"] for record in records)
    if excluded_count != 4:
        raise SystemExit(f"hash exclusion count mismatch: {excluded_count}")
    inventory = {
        "schema_version": "package_inventory/v3",
        "package_version": "v1.6-draft-5.3.16",
        "package": "duotronic-witness-contract-v1.6-draft-5.3.16",
        "status": "completed_corrective_development_draft_permanently_not_frozen",
        "historical_source_packages": [],
        "source_package_policy": "changes_merged_no_embedded_source_packages",
        "lineage_record": "history/SOURCE_PACKAGE_LINEAGE_v1_6_draft_5_3_16.json",
        "file_count": len(records),
        "hash_covered_file_count": len(records) - excluded_count,
        "hash_excluded_file_count": excluded_count,
        "hash_exclusion_rule": sorted(RECURSIVE_EXCLUDED),
        "excluded_field_policy": "recursive entries set sha256 and size_bytes to null and declare excluded_fields plus reason",
        "checksum_file": CHECKSUMS,
        "canonical_descriptor": "CANONICAL_CORPUS_v1_6_draft_5_3_16.json",
        "package_provenance": PROVENANCE,
        "files": records,
    }
    (ROOT / INVENTORY).write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / CHECKSUMS).write_text("\n".join(checksums) + "\n", encoding="utf-8")
    lines = [
        "# Complete Manifest — Duotronic Witness Contract v1.6 Draft 5.3.16",
        "",
        "**Status:** completed standalone corrective development corpus; permanently not frozen.",
        "",
        f"- Total regular files: {len(records)}",
        f"- Hash-covered files: {len(records) - excluded_count}",
        f"- Explicit recursive exclusions: {excluded_count}",
        "- Embedded historical source-package archives: none",
        "- Prior-release lineage: digest references only; all active changes are merged",
        "- Source provenance: unpublished workspace; activation blocked",
        "- External governance signature: absent",
        "- Eight external activation gates: independently incomplete",
        "- Contract lifecycle: permanently not frozen",
        "",
        "## Files by extension",
        "",
    ]
    lines.extend(f"- `{extension}`: {count}" for extension, count in sorted(extensions.items()))
    lines.extend([
        "", "## Recursive exclusions", "",
        "The active inventory, checksum file, this human manifest, and validation report recursively describe package closure. Their own inventory hash and size fields are null; every other final regular file is size- and SHA-256-covered.",
        "", "## Documentation scope", "",
        "Vendored dependency documentation is excluded from first-party link-quality checks while every dependency byte remains hash-covered.", "",
    ])
    (ROOT / MANIFEST).write_text("\n".join(lines), encoding="utf-8")
    final = {path.relative_to(ROOT).as_posix(): path for path in files()}
    for record in records:
        relative = record["path"]
        if relative in RECURSIVE_EXCLUDED:
            if record["sha256"] is not None or record["size_bytes"] is not None:
                raise SystemExit(f"recursive field is not null: {relative}")
            continue
        path = final[relative]
        if record["sha256"] != digest(path) or record["size_bytes"] != path.stat().st_size:
            raise SystemExit(f"post-generation final-byte mismatch: {relative}")
    print(json.dumps({"file_count": len(records), "covered": len(records) - excluded_count, "excluded": sorted(RECURSIVE_EXCLUDED)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
