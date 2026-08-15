#!/usr/bin/env python3
"""Regenerate the complete 5.3.18 schema registry."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "validation"))
from identity import corpus_file_id  # noqa: E402

ACTIVE = {
    "encrypted_payload_v1.schema.json",
    "legacy_mapping_witness_v1.schema.json",
    "meta_object_edge_v1.schema.json",
    "recurrent_witness_state_v1.schema.json",
    "semantic_content_v1.schema.json",
    "signature_envelope_v1.schema.json",
    "witness_envelope_v1.schema.json",
    "authority_domain_v1.schema.json",
    "probe_measurement_v1.schema.json",
    "revalidation_measurement_v1.schema.json",
    "evidence_graph_edge_v1.schema.json",
    "activation_state_vector_v1.schema.json",
    "evidence_checkpoint_v1.schema.json",
}


def main() -> int:
    entries = []
    for path in sorted((ROOT / "schemas").glob("*.schema.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        relative = path.relative_to(ROOT).as_posix()
        active = path.name in ACTIVE
        entries.append({
            "activation": "active_5_3_18" if active else "retained_migrated_compatibility",
            "file_id": corpus_file_id(relative, path.read_bytes()),
            "path": relative,
            "schema_id": document["$id"],
        })
    registry = {
        "active_schema_count": sum(item["activation"] == "active_5_3_18" for item in entries),
        "registry_version": "schema_registry/v11",
        "retained_migrated_schema_count": sum(item["activation"] != "active_5_3_18" for item in entries),
        "schemas": entries,
    }
    output = ROOT / "SCHEMA_REGISTRY_v1_6_draft_5_3_18.json"
    output.write_text(json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "schemas": len(entries)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
