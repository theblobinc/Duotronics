#!/usr/bin/env python3
"""Generate the complete lifecycle-classified Draft 5.3.5 schema registry."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "refs/schema_registry_v1_6_draft_5_3_5.json"

CANONICAL = {
    "evidence_claim_v2", "verifier_principal_v2", "verifier_key_v3", "governance_authority_v1",
    "governance_authorization_witness_v2", "trusted_time_witness_v1", "governed_compiler_registry_v2",
    "proof_policy_decision_v1", "proof_policy_registry_v1", "sandbox_template_v1", "source_snapshot_limits_v1",
    "effective_sandbox_invocation_v2", "lean_verifier_result_v3", "lean_compiler_witness_v4",
    "governance_event_v1", "authority_snapshot_v2", "authority_supersession_v3", "build_attestation_v2",
    "package_provenance_v1", "release_activation_evidence_v1", "proof_witness_v2",
    "non_collapse_transition_v2", "claim_status_event_v2", "theorem_promotion_gate_v3",
    "replay_assumption_manifest_v2", "verification_grammar_v2", "verification_result_v2",
    "positive_baseline_cell_v1", "proof_check_result_v3", "schema_registry_v1",
}

LEGACY = {
    "governed_compiler_registry_v1", "lean_verifier_result_v1", "lean_verifier_result_v2",
    "lean_compiler_witness", "lean_compiler_witness_v2", "lean_compiler_witness_v3",
    "governance_authorization_witness_v1", "theorem_promotion_gate", "theorem_promotion_gate_v2",
    "authority_snapshot_v1", "authority_supersession_v1", "authority_supersession_v2",
    "authority_signature_binding_v1", "verifier_key_status_event_v1", "verifier_key_status_event_v2",
    "effective_sandbox_invocation_v1", "build_attestation_v1", "evidence_claim", "proof_witness",
    "non_collapse_transition", "replay_assumption_manifest", "verification_grammar", "verification_result",
}


def schema_name(path: Path) -> str:
    name = path.name
    for suffix in (".schema.json", ".schema.yaml", ".schema.yml"):
        if name.endswith(suffix):
            return name[:-len(suffix)]
    raise ValueError(path)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.suffix == ".json" else yaml.safe_load(path.read_text(encoding="utf-8"))


def fixture_map() -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    valid: dict[str, list[str]] = {}; invalid: dict[str, list[str]] = {}
    for disposition, target in (("valid", valid), ("invalid", invalid)):
        candidates: dict[str, list[Path]] = {}
        for path in sorted((ROOT / "executable/tests/fixtures").glob(f"draft5_3_*/{disposition}/*.json")):
            record = json.loads(path.read_text(encoding="utf-8")); reference = record.get("schema_ref")
            if isinstance(reference, str):
                candidates.setdefault(reference, []).append(path)
        for reference, paths in candidates.items():
            latest_generation = max(path.parents[1].name for path in paths)
            target[reference] = [path.relative_to(ROOT).as_posix() for path in paths if path.parents[1].name == latest_generation]
    return valid, invalid


def main() -> int:
    valid, invalid = fixture_map(); entries = []
    schema_paths = sorted((ROOT / "schemas").glob("*.schema.*"), key=lambda path: path.name)
    for path in schema_paths:
        relative = path.relative_to(ROOT).as_posix(); name = schema_name(path); document = load(path)
        if name in CANONICAL:
            lifecycle = "canonical"; active = True; rationale = "Active Draft 5.3.5 API, persistence, witness, or validation surface."
        elif name in LEGACY:
            lifecycle = "legacy_compatibility"; active = False; rationale = "Read/replay compatibility only; new writes are forbidden."
        else:
            lifecycle = "experimental_research"; active = False; rationale = "Carried research or non-authoritative profile; excluded from active authority writes."
        valid_fixtures = valid.get(relative, [])
        if name == "proof_check_result_v3":
            valid_fixtures = ["runtime:test_openapi_proof_check_response_matches_application"]
        entries.append({
            "path": relative, "schema_id": document.get("$id") if isinstance(document, dict) else None,
            "lifecycle": lifecycle, "active_surface": active,
            "valid_fixtures": valid_fixtures, "invalid_fixtures": invalid.get(relative, []),
            "rationale": rationale,
        })
    discovered = {schema_name(path) for path in schema_paths}
    if not CANONICAL.issubset(discovered) or not LEGACY.issubset(discovered):
        raise SystemExit("schema classification names do not match the schema directory")
    registry = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "registry_version": "v1.6-draft-5.3.5", "active_version_scope": "v1.6-draft-5.3.5",
        "entries": entries,
        "rules": {
            "unknown_schema": "reject", "unclassified_active_surface": "reject",
            "legacy_new_write": "reject", "legacy_replay": "allow_with_generation_marker",
            "canonical_fixture_coverage": "valid_and_invalid_required",
            "strict_mode": "canonical_schemas_strict_true",
            "authority_output_creation": "server_only", "freeze_policy": "living_contract_never_freeze",
        },
        "strict_mode_exceptions": [],
    }
    OUTPUT.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
