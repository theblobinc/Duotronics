#!/usr/bin/env python3
"""Dependency-free portable validator for Contract 5.3.18."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from identity import canonical_bytes, corpus_file_id, duoid

ROOT = Path(__file__).resolve().parents[1]
PARENT_ROOT_ID = "duoid:shake256-512:PwumHENNZOLdwjqnhCyzcycfDDhNmEIweoUd5Fxc46fXMpYS-7TrWGObq7xJYyDZkqYaC8wXa1cucGeKPrJBcw"
ACTIVE_SCHEMAS = {
    "authority_domain_v1.schema.json",
    "probe_measurement_v1.schema.json",
    "revalidation_measurement_v1.schema.json",
    "evidence_graph_edge_v1.schema.json",
    "activation_state_vector_v1.schema.json",
    "evidence_checkpoint_v1.schema.json",
}


def load(path: Path) -> Any:
    def no_duplicates(items):
        value = {}
        for key, child in items:
            if key in value:
                raise ValueError(f"duplicate key {key!r} in {path}")
            value[key] = child
        return value
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)


def validate_schema(path: Path, value: dict[str, Any]) -> None:
    if value.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValueError(f"{path}: wrong schema dialect")
    if not str(value.get("$id", "")).startswith("duotronic://schemas/"):
        raise ValueError(f"{path}: invalid schema identifier")
    if value.get("type") != "object" or value.get("additionalProperties") is not False:
        raise ValueError(f"{path}: active schema is not a closed object")
    properties = value.get("properties")
    required = value.get("required")
    if not isinstance(properties, dict) or not isinstance(required, list):
        raise ValueError(f"{path}: malformed properties or required list")
    if not set(required).issubset(properties):
        raise ValueError(f"{path}: required field missing from properties")
    def visit(node):
        if isinstance(node, dict):
            if "pattern" in node:
                re.compile(node["pattern"])
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)
    visit(value)


def validate(root: Path) -> list[str]:
    failures = []
    required = [
        "CANONICAL_CORPUS_v1_6_draft_5_3_18.json",
        "COMPLETE_CORPUS_CONTENT_MAP_v1_6_draft_5_3_18.json",
        "PACKAGE_PROVENANCE_v1_6_draft_5_3_18.json",
        "MANIFEST_v1_6_draft_5_3_18.json",
        "RELATION_REGISTRY_v1_6_draft_5_3_18.json",
        "SCHEMA_REGISTRY_v1_6_draft_5_3_18.json",
        "duotronic_witness_contract_v1_6_draft_5_3_18.md",
        "runtime/RUNTIME_MIGRATION_CHECKLIST_5_3_18.md",
        "migration/5_3_17_TO_5_3_18.md",
        "executable/runtime/evidence_graph_v5318.py",
        "benchmarks/benchmark_evidence_graph_v5318.py",
        "formal/lean4/AuthorityDomainV5318.lean",
        "formal/tlaplus/AuthorityDomainV5318.tla",
        "formal/tlaplus/AuthorityDomainV5318.cfg",
    ]
    for relative in required:
        if not (root / relative).is_file():
            failures.append(f"missing required file: {relative}")

    try:
        descriptor = load(root / required[0])
        if descriptor.get("active_version") != "v1.6-draft-5.3.18":
            failures.append("canonical descriptor version mismatch")
        if descriptor.get("authority_default") != "disabled":
            failures.append("portable authority must default disabled")
        if descriptor.get("release_authority") is not False:
            failures.append("development corpus cannot carry release authority")
        if descriptor.get("production_eligible") is not False:
            failures.append("development corpus cannot be production eligible")
        if descriptor.get("parent_corpus_root_id") != PARENT_ROOT_ID:
            failures.append("parent corpus root mismatch")
    except Exception as error:
        failures.append(f"descriptor validation failed: {error}")

    schema_map = {}
    for name in sorted(ACTIVE_SCHEMAS):
        path = root / "schemas" / name
        try:
            value = load(path)
            validate_schema(path, value)
            relative = path.relative_to(root).as_posix()
            schema_map[value["$id"]] = (relative, corpus_file_id(relative, path.read_bytes()))
        except Exception as error:
            failures.append(str(error))
    try:
        registry = load(root / "SCHEMA_REGISTRY_v1_6_draft_5_3_18.json")
        registered = {
            row["schema_id"]: (row["path"], row["file_id"])
            for row in registry["schemas"] if row["activation"] == "active_5_3_18"
            and Path(row["path"]).name in ACTIVE_SCHEMAS
        }
        if registered != schema_map:
            failures.append("active 5.3.18 schema registry mismatch")
    except Exception as error:
        failures.append(f"schema registry validation failed: {error}")

    try:
        registry = load(root / "RELATION_REGISTRY_v1_6_draft_5_3_18.json")
        relations = {row["relation_type"]: row for row in registry["relations"]}
        for name, row in relations.items():
            inverse = relations[row["inverse"]]
            if inverse["inverse"] != name:
                failures.append(f"relation inverse is not involutive: {name}")
            if row["symmetric"] and row["inverse"] != name:
                failures.append(f"symmetric relation has a distinct inverse: {name}")
        needed = {"measured_by", "attested_by", "revalidated_by", "satisfies_gate",
                  "aggregated_by", "activated_by", "bound_to_registry"}
        if not needed.issubset(relations):
            failures.append("activation evidence relations are incomplete")
    except Exception as error:
        failures.append(f"relation registry validation failed: {error}")

    try:
        parent = load(root / "MANIFEST_v1_6_draft_5_3_17.json")
        if parent.get("corpus_root_id") != PARENT_ROOT_ID:
            failures.append("retained parent manifest root mismatch")
        for row in parent["files"]:
            path = root / row["path"]
            if not path.is_file():
                failures.append(f"retained parent file missing: {row['path']}")
                continue
            data = path.read_bytes()
            if len(data) != row["size_bytes"] or corpus_file_id(row["path"], data) != row["file_id"]:
                failures.append(f"retained parent file changed: {row['path']}")
    except Exception as error:
        failures.append(f"parent retention validation failed: {error}")

    try:
        path = root / "MANIFEST_v1_6_draft_5_3_18.json"
        manifest = load(path)
        expected_paths = {
            item.relative_to(root).as_posix()
            for item in root.rglob("*")
            if item.is_file()
            and item.name not in {path.name, "VALIDATION_REPORT_5_3_18.json"}
            and "__pycache__" not in item.parts
            and not item.name.startswith(".workspace")
        }
        rows = manifest["files"]
        ordered = [row["path"] for row in rows]
        if ordered != sorted(expected_paths) or set(ordered) != expected_paths:
            failures.append("5.3.18 manifest membership or ordering mismatch")
        if manifest.get("file_count") != len(rows):
            failures.append("5.3.18 manifest count mismatch")
        expected_root = duoid("DUOTRONIC/CORPUS-ROOT/v1", canonical_bytes(rows))
        if manifest.get("corpus_root_id") != expected_root:
            failures.append("5.3.18 corpus root mismatch")
        for row in rows:
            data = (root / row["path"]).read_bytes()
            if len(data) != row["size_bytes"] or corpus_file_id(row["path"], data) != row["file_id"]:
                failures.append(f"5.3.18 manifest entry mismatch: {row['path']}")
    except Exception as error:
        failures.append(f"5.3.18 manifest validation failed: {error}")

    return failures


def main() -> int:
    failures = validate(ROOT)
    report = {
        "schema_version": "validation_report/v1",
        "contract_version": "v1.6-draft-5.3.18",
        "status": "pass" if not failures else "fail",
        "failure_count": len(failures),
        "failures": failures,
        "production_authority_activated": False,
    }
    (ROOT / "VALIDATION_REPORT_5_3_18.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
