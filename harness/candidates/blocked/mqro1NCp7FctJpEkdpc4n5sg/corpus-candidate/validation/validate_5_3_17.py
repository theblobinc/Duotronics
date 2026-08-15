#!/usr/bin/env python3
"""Dependency-free portable validator for Contract 5.3.17."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from identity import canonical_bytes, corpus_file_id, duoid, edge_content_id, semantic_content_id


def duplicate_free_load(path: Path) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for key, value in items:
            if key in output:
                raise ValueError(f"duplicate key {key!r} in {path}")
            output[key] = value
        return output
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)


ACTIVE_SCHEMAS = {
    "encrypted_payload_v1.schema.json", "legacy_mapping_witness_v1.schema.json",
    "meta_object_edge_v1.schema.json", "recurrent_witness_state_v1.schema.json",
    "semantic_content_v1.schema.json", "signature_envelope_v1.schema.json",
    "witness_envelope_v1.schema.json",
}


def validate_schema(path: Path, schema: dict[str, Any], *, active: bool) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValueError(f"{path}: unsupported schema declaration")
    if not isinstance(schema.get("$id"), str) or not schema["$id"]:
        raise ValueError(f"{path}: missing stable schema id")
    if active and not schema["$id"].startswith("duotronic://schemas/"):
        raise ValueError(f"{path}: active schema id is outside the 5.3.17 namespace")
    if active and (schema.get("type") != "object" or schema.get("additionalProperties") is not False):
        raise ValueError(f"{path}: authority schemas must be closed objects")
    properties = schema.get("properties")
    required = schema.get("required")
    if not isinstance(properties, dict) or not isinstance(required, list):
        raise ValueError(f"{path}: properties/required are malformed")
    if not set(required).issubset(properties):
        raise ValueError(f"{path}: required fields are absent from properties")
    def visit(node: Any) -> None:
        if isinstance(node, dict):
            pattern = node.get("pattern")
            if pattern is not None:
                re.compile(pattern)
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)
    visit(schema)


def validate(root: Path) -> list[str]:
    failures: list[str] = []
    required = [
        "CANONICAL_CORPUS_v1_6_draft_5_3_17.json",
        "MANIFEST_v1_6_draft_5_3_17.json",
        "SCHEMA_REGISTRY_v1_6_draft_5_3_17.json",
        "SUITE_REGISTRY_v1_6_draft_5_3_17.json",
        "RELATION_REGISTRY_v1_6_draft_5_3_17.json",
        "duotronic_witness_contract_v1_6_draft_5_3_17.md",
        "runtime/RUNTIME_MIGRATION_CHECKLIST_5_3_17.md",
        "runtime/RUNTIME_UPDATE_STATUS_5_3_17.md",
        "vectors/identity_vectors.json",
        "COMPLETE_CORPUS_CONTENT_MAP_v1_6_draft_5_3_17.json",
        "CORPUS_INDEX_v1_6_draft_5_3_17.md",
        "PACKAGE_INVENTORY_v1_6_draft_5_3_17.json",
        "PACKAGE_PROVENANCE_v1_6_draft_5_3_17.json",
        "executable/runtime/pq_provider.py",
        "requirements-pq-runtime.txt",
    ]
    for name in required:
        if not (root / name).is_file():
            failures.append(f"missing required file: {name}")

    forbidden = [
        ("ed" + "25519").encode(),
        ("sha" + "-" + "256").encode(),
        ("sha" + "256").encode(),
        ("hashlib." + "sha" + "256").encode(),
    ]
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().lower().encode()
        data = path.read_bytes().lower()
        for token in forbidden:
            if token in relative or token in data:
                failures.append(f"forbidden legacy primitive token in {path.relative_to(root)}")

    schema_ids: set[str] = set()
    schema_by_id: dict[str, tuple[str, str]] = {}
    for path in sorted((root / "schemas").glob("*.schema.json")):
        try:
            schema = duplicate_free_load(path)
            validate_schema(path, schema, active=path.name in ACTIVE_SCHEMAS)
            if schema["$id"] in schema_ids:
                raise ValueError(f"duplicate schema id {schema['$id']}")
            schema_ids.add(schema["$id"])
            relative = path.relative_to(root).as_posix()
            schema_by_id[schema["$id"]] = (relative, corpus_file_id(relative, path.read_bytes()))
        except Exception as error:
            failures.append(str(error))

    schema_registry_path = root / "SCHEMA_REGISTRY_v1_6_draft_5_3_17.json"
    if schema_registry_path.is_file():
        try:
            registry = duplicate_free_load(schema_registry_path)
            registered = {
                item["schema_id"]: (item["path"], item["file_id"])
                for item in registry["schemas"]
            }
            if registered != schema_by_id:
                failures.append("schema registry membership or digest mismatch")
        except Exception as error:
            failures.append(f"schema registry validation failed: {error}")

    vectors_path = root / "vectors/identity_vectors.json"
    if vectors_path.is_file():
        try:
            vectors = duplicate_free_load(vectors_path)
            for vector in vectors["semantic_content"]:
                actual = semantic_content_id(vector["content_type"], vector["body"])
                if actual != vector["expected_id"]:
                    failures.append(f"semantic vector mismatch: {vector['name']}")
            for vector in vectors["meta_object_edges"]:
                actual = edge_content_id(vector["edge"])
                if actual != vector["expected_id"]:
                    failures.append(f"edge vector mismatch: {vector['name']}")
        except Exception as error:
            failures.append(f"identity vector validation failed: {error}")

    manifest_path = root / "MANIFEST_v1_6_draft_5_3_17.json"
    if manifest_path.is_file():
        try:
            manifest = duplicate_free_load(manifest_path)
            expected_paths = {
                item.relative_to(root).as_posix()
                for item in root.rglob("*")
                if item.is_file() and item.name not in {manifest_path.name, "VALIDATION_REPORT.json"}
                and "__pycache__" not in item.parts
            }
            entries = manifest["files"]
            ordered_paths = [entry["path"] for entry in entries]
            manifest_paths = set(ordered_paths)
            if expected_paths != manifest_paths:
                failures.append("manifest file membership mismatch")
            if len(ordered_paths) != len(manifest_paths):
                failures.append("manifest contains duplicate paths")
            if ordered_paths != sorted(ordered_paths):
                failures.append("manifest paths are not canonically ordered")
            if manifest.get("file_count") != len(entries):
                failures.append("manifest file count mismatch")
            if manifest.get("path_binding") is not True:
                failures.append("manifest path binding is disabled")
            expected_root = duoid(
                "DUOTRONIC/CORPUS-ROOT/v1",
                canonical_bytes(entries),
            )
            if manifest.get("corpus_root_id") != expected_root:
                failures.append("manifest corpus root mismatch")
            for entry in entries:
                data = (root / entry["path"]).read_bytes()
                if len(data) != entry["size_bytes"]:
                    failures.append(f"manifest size mismatch: {entry['path']}")
                if corpus_file_id(entry["path"], data) != entry["file_id"]:
                    failures.append(f"manifest digest mismatch: {entry['path']}")
        except Exception as error:
            failures.append(f"manifest validation failed: {error}")

    descriptor_path = root / "CANONICAL_CORPUS_v1_6_draft_5_3_17.json"
    if descriptor_path.is_file():
        try:
            descriptor = duplicate_free_load(descriptor_path)
            if descriptor.get("active_version") != "v1.6-draft-5.3.17":
                failures.append("descriptor active version mismatch")
            if descriptor.get("authority_default") != "disabled" or descriptor.get("release_authority") is not False:
                failures.append("portable corpus must not activate authority")
            if descriptor.get("hash_profile") != "SHAKE256-512":
                failures.append("descriptor hash profile mismatch")
        except Exception as error:
            failures.append(f"descriptor validation failed: {error}")

    content_map_path = root / "COMPLETE_CORPUS_CONTENT_MAP_v1_6_draft_5_3_17.json"
    if content_map_path.is_file():
        try:
            content_map = duplicate_free_load(content_map_path)
            if content_map.get("baseline_file_count") != 1968:
                failures.append("complete-corpus baseline file count mismatch")
            if content_map.get("baseline_retained_file_count") != 1968:
                failures.append("complete-corpus retained file count mismatch")
            if content_map.get("baseline_missing_file_count") != 0 or content_map.get("retention_status") != "complete":
                failures.append("complete-corpus baseline retention failed")
        except Exception as error:
            failures.append(f"complete-corpus map validation failed: {error}")

    suite_path = root / "SUITE_REGISTRY_v1_6_draft_5_3_17.json"
    if suite_path.is_file():
        try:
            suite_registry = duplicate_free_load(suite_path)
            suites = {item["suite_id"]: item for item in suite_registry["suites"]}
            active = suites[suite_registry["active_suite_id"]]
            expected = {
                "authority_hash": "SHAKE256-512", "authority_hash_output_bytes": 64,
                "signature": "ML-DSA-87", "kem": "ML-KEM-1024",
                "kdf": "KMAC256", "aead": "AES-256-GCM-SIV",
            }
            if any(active.get(key) != value for key, value in expected.items()):
                failures.append("active cryptographic suite mismatch")
        except Exception as error:
            failures.append(f"suite registry validation failed: {error}")

    relation_path = root / "RELATION_REGISTRY_v1_6_draft_5_3_17.json"
    if relation_path.is_file():
        try:
            relation_registry = duplicate_free_load(relation_path)
            relations = {item["relation_type"]: item for item in relation_registry["relations"]}
            for name, item in relations.items():
                inverse = relations[item["inverse"]]
                if inverse["inverse"] != name:
                    failures.append(f"relation inverse is not involutive: {name}")
                if item["symmetric"] and item["inverse"] != name:
                    failures.append(f"symmetric relation has a distinct inverse: {name}")
        except Exception as error:
            failures.append(f"relation registry validation failed: {error}")

    return failures


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    failures = validate(root)
    report = {
        "contract_version": "v1.6-draft-5.3.17",
        "failure_count": len(failures),
        "failures": failures,
        "portable_status": "passed" if not failures else "failed",
        "authority_activated": False
    }
    print(canonical_bytes(report).decode("utf-8"))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
