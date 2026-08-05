#!/usr/bin/env python3
"""Generate the complete lifecycle-classified Draft 5.3.14 schema registry."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "refs/schema_registry_v1_6_draft_5_3_14.json"

CANONICAL = {
    "evidence_claim_v2", "verifier_principal_v2", "verifier_key_v3", "governance_authority_v1",
    "governance_authorization_witness_v2", "trusted_time_witness_v1", "governed_compiler_registry_v2",
    "proof_policy_decision_v1", "proof_policy_registry_v1", "sandbox_template_v1", "source_snapshot_limits_v1",
    "effective_sandbox_invocation_v5", "lean_verifier_request_v5", "lean_inspector_result_v1", "lean_compile_handoff_v3",
    "lean_verifier_result_v6", "lean_compiler_witness_v8", "proof_check_request_v2", "proof_check_result_v7",
    "idempotency_cache_envelope_v3", "cache_signing_registry_v2", "cache_registry_lineage_v1",
    "cache_stale_row_evidence_v4", "cache_verification_evidence_v1", "cache_audit_record_v2",
    "cache_audit_checkpoint_v1", "cache_audit_segment_seal_v1", "domain_execution_evidence_v1",
    "trusted_artifact_attestation_registry_v1", "platform_capability_probe_v1",
    "governance_event_v1", "authority_snapshot_v2", "authority_supersession_v3", "build_attestation_v2",
    "package_provenance_v1", "release_activation_evidence_v1", "proof_witness_v2",
    "non_collapse_transition_v2", "claim_status_event_v2", "theorem_promotion_gate_v3",
    "replay_assumption_manifest_v2", "verification_grammar_v2", "verification_result_v2",
    "positive_baseline_cell_v1", "schema_registry_v1",
}

LEGACY = {
    "governed_compiler_registry_v1", "lean_verifier_result_v1", "lean_verifier_result_v2",
    "lean_compiler_witness", "lean_compiler_witness_v2", "lean_compiler_witness_v3",
    "governance_authorization_witness_v1", "theorem_promotion_gate", "theorem_promotion_gate_v2",
    "authority_snapshot_v1", "authority_supersession_v1", "authority_supersession_v2",
    "authority_signature_binding_v1", "verifier_key_status_event_v1", "verifier_key_status_event_v2",
    "effective_sandbox_invocation_v1", "effective_sandbox_invocation_v2", "effective_sandbox_invocation_v3",
    "lean_verifier_result_v3", "lean_verifier_result_v4", "lean_compiler_witness_v4", "lean_compiler_witness_v5",
    "effective_sandbox_invocation_v4", "lean_verifier_request_v4", "lean_verifier_result_v5", "lean_compiler_witness_v6",
    "proof_check_request_v1", "proof_check_result_v3", "proof_check_result_v4", "proof_check_result_v5", "build_attestation_v1", "evidence_claim", "proof_witness",
    "lean_compile_handoff_v2", "lean_compiler_witness_v7", "proof_check_result_v6",
    "idempotency_cache_envelope_v1", "idempotency_cache_envelope_v2", "cache_signing_registry_v1",
    "non_collapse_transition", "replay_assumption_manifest", "verification_grammar", "verification_result",
    "cache_stale_row_evidence_v2", "cache_stale_row_evidence_v3", "cache_audit_record_v1",
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
            lifecycle = "canonical"; active = True; rationale = "Active Draft 5.3.14 API, persistence, witness, or validation surface."
        elif name in LEGACY:
            lifecycle = "legacy_compatibility"; active = False; rationale = "Read/replay compatibility only; new writes are forbidden."
        else:
            lifecycle = "experimental_research"; active = False; rationale = "Carried research or non-authoritative profile; excluded from active authority writes."
        valid_fixtures = valid.get(relative, [])
        runtime_valid = {
            "effective_sandbox_invocation_v5": "runtime:test_effective_invocation_schema_boundary",
            "lean_verifier_request_v5": "runtime:test_authenticated_verifier_request_schema_boundary",
            "lean_verifier_result_v6": "runtime:test_signed_verifier_result_schema_boundary",
            "lean_compile_handoff_v3": "runtime:test_trusted_consumer_recomputes_ordered_complete_compile_commands",
            "lean_compiler_witness_v8": "runtime:test_compiler_witness_schema_boundary",
            "proof_check_request_v2": "runtime:test_authenticated_proof_check_request_schema_boundary",
            "proof_check_result_v7": "runtime:test_openapi_proof_check_response_matches_application",
            "idempotency_cache_envelope_v3": "runtime:test_signed_validity_evidence_binds_status_change_time",
            "cache_signing_registry_v2": "runtime:test_future_expired_retired_and_revoked_keys_fail_closed",
            "cache_registry_lineage_v1": "runtime:test_authenticated_predecessor_row_emits_evidence_then_returns_stable_conflict",
            "cache_stale_row_evidence_v4": "runtime:test_bound_historical_row_emits_self_contained_exact_envelope_evidence",
            "cache_verification_evidence_v1": "runtime:test_signed_append_only_chain_is_durable_and_startup_verified",
            "cache_audit_record_v2": "runtime:test_signed_append_only_chain_is_durable_and_startup_verified",
            "cache_audit_checkpoint_v1": "runtime:test_valid_prefix_truncation_is_rejected_by_checkpoint",
            "cache_audit_segment_seal_v1": "runtime:test_segment_seal_and_successor_predecessor_binding",
            "domain_execution_evidence_v1": "runtime:test_dual_domain_execution_evidence",
        }
        if name in runtime_valid:
            valid_fixtures = [runtime_valid[name]]
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
        "registry_version": "v1.6-draft-5.3.14", "active_version_scope": "v1.6-draft-5.3.14",
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
