#!/usr/bin/env python3
"""Descriptor-reconciled fail-closed validator for Draft 5.3.4."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import traceback
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

sys.dont_write_bytecode = True

try:
    import cryptography
except Exception as error:
    cryptography = None
    CRYPTOGRAPHY_IMPORT_ERROR = error
else:
    CRYPTOGRAPHY_IMPORT_ERROR = None

try:
    import yaml
except Exception as error:
    yaml = None
    YAML_IMPORT_ERROR = error
else:
    YAML_IMPORT_ERROR = None

ROOT = Path(__file__).resolve().parents[2]
DESCRIPTOR_PATH = ROOT / "CANONICAL_CORPUS_v1_6_draft_5_3_4.json"
REPORT_PATH = ROOT / "DRAFT5_3_4_VALIDATION_REPORT.json"
HISTORY_ARCHIVES = {
    "v1.6 - Draft 5.2.2.zip": ("437395d28c452f0a20937eaf562020afae2214edf01a8df2fe6dadd062201c22", 492),
    "v1.6 - Draft 5.3.1.zip": ("26608233721f6b56ce6dfe5dfe653029c421e72a551196e004d2b2d3d59de588", 560),
    "v1.6 - Draft 5.3.2.zip": ("57daa37189dcd8c0cf8cff990850393f4feaa70aeea9736b5edabffc58a37675", 1158),
    "v1.6 - Draft 5.3.3.zip": ("b02165cffa8b95b41a210f06b5e734e9592472a9c29630c07bb0ea318c7c3cb1", 1238),
}


class PhaseSkipped(RuntimeError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _is_runtime_cache(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return "__pycache__" in relative.parts or path.suffix == ".pyc"


def reconcile_required_phases(required: list[str], results: list[dict[str, Any]]) -> dict[str, Any]:
    """Derive closure sets from descriptor identifiers and actual results."""
    required_counts = Counter(required)
    result_counts = Counter(result.get("name") for result in results)
    result_by_name = {result["name"]: result for result in results if result.get("name") in required_counts}
    missing = sorted(name for name in required_counts if result_counts[name] == 0)
    duplicates = sorted(
        name for name in required_counts
        if required_counts[name] != 1 or result_counts[name] > 1
    )
    failed = sorted(name for name, result in result_by_name.items() if result.get("status") == "failed")
    skipped = sorted(name for name, result in result_by_name.items() if result.get("status") == "skipped")
    nonpassing = sorted(
        name for name, result in result_by_name.items()
        if result.get("status") not in {"passed", "failed", "skipped"}
    )
    all_passed = not missing and not duplicates and not failed and not skipped and not nonpassing and len(result_by_name) == len(required_counts)
    return {
        "required_missing": missing,
        "required_duplicates": duplicates,
        "required_failed": failed,
        "required_skipped": skipped,
        "required_noncanonical_status": nonpassing,
        "all_required_passed": all_passed,
    }


def _subprocess_environment() -> dict[str, str]:
    import os
    return {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}


def _run_python_tests(script: str, tests: list[str], timeout: int = 180) -> dict[str, Any]:
    command = [sys.executable, script, *tests]
    process = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=timeout, env=_subprocess_environment())
    assert_true(process.returncode == 0, f"tests failed: {' '.join(command)}\n{process.stdout}\n{process.stderr}")
    match = re.search(r"Ran (\d+) tests?", process.stderr + process.stdout)
    return {
        "tests": int(match.group(1)) if match else len(tests),
        "stdout": process.stdout.strip(),
        "stderr": process.stderr.strip(),
    }


def _load_authority_module():
    path = ROOT / "executable/runtime/proof_authority.py"
    spec = importlib.util.spec_from_file_location("proof_authority_validator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _new_database() -> sqlite3.Connection:
    authority = _load_authority_module()
    connection = sqlite3.connect(":memory:", isolation_level=None)
    authority.register_sqlite_crypto_functions(connection)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript((ROOT / "executable/sql/draft5_2_schema_additions.sql").read_text(encoding="utf-8"))
    connection.executescript((ROOT / "migration/draft5_2_2_to_draft5_3_1.sql").read_text(encoding="utf-8"))
    connection.executescript((ROOT / "migration/draft5_3_1_to_draft5_3_2.sql").read_text(encoding="utf-8"))
    connection.executescript((ROOT / "migration/draft5_3_2_to_draft5_3_3.sql").read_text(encoding="utf-8"))
    connection.executescript((ROOT / "migration/draft5_3_3_to_draft5_3_4.sql").read_text(encoding="utf-8"))
    return connection


def phase_descriptor() -> dict[str, Any]:
    descriptor = load_json(DESCRIPTOR_PATH.name)
    assert_true(descriptor["active_version"] == "v1.6-draft-5.3.4", "active version mismatch")
    assert_true(descriptor["freeze_state"] == "permanently_not_frozen", "living contract must remain permanently_not_frozen")
    assert_true(descriptor["lifecycle_policy"] == "living_contract_never_freeze", "living-contract policy mismatch")
    required = descriptor["required_validation_phases"]
    optional = descriptor["optional_validation_phases"]
    assert_true(required and len(required) == len(set(required)), "required phase identifiers must be nonempty and unique")
    assert_true(len(optional) == len(set(optional)), "optional phase identifiers must be unique")
    assert_true(not set(required).intersection(optional), "required and optional phase identifiers overlap")
    refs = [
        "primary_contract", "spec_change_request", "start_here", "corpus_index", "inventory", "checksum_manifest",
        "human_manifest", "schema_registry", "validator", "schema_validator", "canonical_openapi",
        "base_sql", "authority_migration", "proof_authority_runtime", "proof_check_service",
        "trusted_compiler", "trusted_verifier", "trusted_verifier_lean_source",
        "result_channel_security_profile", "retention_observability_profile",
        "sandbox_profile", "formal_toolchain_manifest", "mathematics_profile", "migration_runbook",
        "corrective_assurance_report", "build_attestation_status", "release_gate_status",
    ]
    paths = [descriptor[key] for key in refs]
    paths.extend(descriptor["authority_migrations"])
    paths.extend(descriptor["formal_authority_profiles"])
    missing = [relative for relative in paths if not (ROOT / relative).is_file()]
    assert_true(not missing, f"descriptor references missing files: {missing}")
    resolver = (ROOT / "kernel/corpus_boot_and_canonical_resolver_v1_0.md").read_text(encoding="utf-8")
    for token in (DESCRIPTOR_PATH.name, "PACKAGE_INVENTORY_v1_6_draft_5_3_4.json", "CHECKSUMS_v1_6_draft_5_3_4.sha256"):
        assert_true(token in resolver, f"resolver does not boot canonical token {token}")
    accounting = _run_python_tests("executable/tests/test_validator_phase_reconciliation.py", [])
    return {"active_version": descriptor["active_version"], "required_phase_count": len(required), "phase_accounting_tests": accounting["tests"]}


def phase_dependencies() -> dict[str, Any]:
    assert_true(yaml is not None, f"PyYAML unavailable: {YAML_IMPORT_ERROR}")
    assert_true(cryptography is not None, f"cryptography unavailable: {CRYPTOGRAPHY_IMPORT_ERROR}")
    node = shutil.which("node")
    assert_true(node is not None, "node is unavailable")
    vendor = ROOT / "executable/validators/vendor/node_modules"
    for package in ("ajv", "ajv-formats", "fast-deep-equal", "fast-uri", "json-schema-traverse", "require-from-string"):
        assert_true((vendor / package).is_dir(), f"vendored validator dependency missing: {package}")
    connection = sqlite3.connect(":memory:")
    try:
        assert_true(connection.execute("SELECT json_array_length('[1,2]')").fetchone()[0] == 2, "SQLite JSON1 unavailable")
    finally:
        connection.close()
    return {
        "python": sys.version.split()[0],
        "node": subprocess.check_output([node, "--version"], text=True).strip(),
        "yaml": getattr(yaml, "__version__", "available"),
        "cryptography": getattr(cryptography, "__version__", "available"),
        "sqlite_json1": True,
        "schema_dependencies": "vendored_hash_covered",
    }


def phase_hash_closure() -> dict[str, Any]:
    inventory = load_json("PACKAGE_INVENTORY_v1_6_draft_5_3_4.json")
    records = inventory["files"]
    by_path = {record["path"]: record for record in records}
    assert_true(len(by_path) == len(records), "duplicate inventory paths")
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and not _is_runtime_cache(path)
    }
    assert_true(actual == set(by_path), f"inventory path mismatch; missing={sorted(actual-set(by_path))[:10]} extra={sorted(set(by_path)-actual)[:10]}")
    checksum_lines = (ROOT / "refs/manifest/CHECKSUMS_v1_6_draft_5_3_4.sha256").read_text(encoding="utf-8").splitlines()
    checksums: dict[str, str] = {}
    for line in checksum_lines:
        if not line.strip() or line.startswith("#"):
            continue
        digest, relative = line.split("  ", 1)
        assert_true(relative not in checksums, f"duplicate checksum path: {relative}")
        checksums[relative] = digest
    covered = 0
    excluded = 0
    for relative, record in by_path.items():
        path = ROOT / relative
        if record["excluded_from_hash_closure"]:
            excluded += 1
            assert_true(relative not in checksums, f"excluded file appears in checksum manifest: {relative}")
            continue
        covered += 1
        digest = sha256(path)
        assert_true(record["size_bytes"] == path.stat().st_size, f"inventory size mismatch: {relative}")
        assert_true(record["sha256"] == digest, f"inventory hash mismatch: {relative}")
        assert_true(checksums.get(relative) == digest, f"checksum mismatch: {relative}")
    expected_covered = {path for path, record in by_path.items() if not record["excluded_from_hash_closure"]}
    assert_true(set(checksums) == expected_covered, "checksum path set mismatch")
    return {"file_count": len(records), "covered": covered, "excluded_generated": excluded}


def _schema_phase(name: str) -> dict[str, Any]:
    command = ["node", "executable/validators/validate_draft5_3_4_schemas.mjs", "--phase", name]
    process = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=180)
    assert_true(process.returncode == 0, f"AJV {name} failed:\n{process.stdout}\n{process.stderr}")
    result = json.loads(process.stdout)
    assert_true(result["phase"] == name and result["status"] == "passed", f"AJV phase identity/status mismatch: {result}")
    return result


def phase_json_schemas() -> dict[str, Any]:
    return _schema_phase("json_schemas")


def phase_valid_fixtures() -> dict[str, Any]:
    return _schema_phase("valid_fixtures")


def phase_invalid_fixtures() -> dict[str, Any]:
    return _schema_phase("invalid_fixtures")


def phase_sql_migration() -> dict[str, Any]:
    connection = _new_database()
    generations = [row[0] for row in connection.execute("SELECT generation FROM wc_schema_generations ORDER BY generation")]
    assert_true("v1.6-draft-5.3.4" in generations, "5.3.4 schema generation missing")
    columns = {row[1] for row in connection.execute("PRAGMA table_info(wc_lean_compiler_witnesses_v3)")}
    hardening = {
        "semantic_witness_content_id", "immutable_snapshot_id", "immutable_snapshot_tree_sha256",
        "proof_artifact_relative_path", "proof_artifact_sha256", "generated_binding_module_sha256",
        "generated_binding_request_sha256", "compiler_profile_id", "verifier_result_payload_sha256",
        "verifier_result_signer_key_id", "verifier_result_signed_payload_canonical_json", "verifier_result_signature", "expected_type_expression_hash",
        "actual_type_expression_hash", "axiom_set_sha256", "statement_binding_confirmed",
        "snapshot_verified_immutable", "result_channel_isolated", "authority_snapshot_id",
        "authority_ledger_high_water_sequence",
    }
    assert_true(hardening.issubset(columns), f"compiler witness v3 columns missing: {sorted(hardening-columns)}")
    profile_columns = {row[1] for row in connection.execute("PRAGMA table_info(wc_compiler_profiles_v2)")}
    profile_binding = {
        "oci_runtime_version", "lean_stdlib_tree_sha256", "verifier_source_revision",
        "verifier_build_attestation_id", "verifier_result_signer_key_id",
        "verifier_result_public_key_base64url", "valid_from", "valid_until",
        "governance_key_id", "signed_payload_canonical_json", "signed_payload_sha256", "signature",
    }
    assert_true(profile_binding.issubset(profile_columns), f"compiler profile binding columns missing: {sorted(profile_binding-profile_columns)}")
    assert_true(not connection.execute("PRAGMA foreign_key_check").fetchall(), "foreign-key check failed")
    required_objects = (
        "wc_governance_action_scope_map_v1", "wc_governance_authorization_witnesses_v2",
        "wc_authority_record_index_v1", "wc_compiler_profiles_v2", "wc_lean_compiler_witnesses_v3",
        "wc_authority_events_v1", "wc_authority_snapshots_v2", "wc_authority_events_as_of_snapshot_v1",
        "wc_authority_supersessions_v3", "wc_release_activation_evidence_v1",
        "wc_theorem_promotion_gates_v3", "wc_authoritative_theorems_v3",
    )
    objects = connection.execute(
        f"SELECT count(*) FROM sqlite_master WHERE name IN ({','.join('?' for _ in required_objects)})",
        required_objects,
    ).fetchone()[0]
    connection.close()
    assert_true(objects == len(required_objects), "5.3.4 governance/as-of objects missing")
    return {"generations": generations, "compiler_witness_v3_binding_columns": len(hardening), "compiler_profile_governance_columns": len(profile_binding), "authority_objects": objects}


def phase_sql_event_ledger() -> dict[str, Any]:
    tests = [
        "SqlAuthorityLifecycle534Tests.test_monotonic_signed_event_is_accepted",
        "SqlAuthorityLifecycle534Tests.test_tampered_event_wrong_scope_and_duplicate_sequence_are_rejected",
        "SqlAuthorityLifecycle534Tests.test_backdated_event_requires_explicit_correction_authorization",
        "SqlAuthorityLifecycle534Tests.test_snapshot_rejects_wrong_event_root_and_future_cutoff",
    ]
    return _run_python_tests("executable/tests/test_sql_authority_lifecycle_v534.py", tests)


def phase_sql_typed_supersession() -> dict[str, Any]:
    tests = [
        "SqlAuthorityLifecycle534Tests.test_typed_supersession_happy_path_and_self_reference",
        "SqlAuthorityLifecycle534Tests.test_supersession_rejects_nonexistent_wrong_type_cycle_and_revoked_replacement",
    ]
    return _run_python_tests("executable/tests/test_sql_authority_lifecycle_v534.py", tests)


def phase_sql_immutability() -> dict[str, Any]:
    return _run_python_tests(
        "executable/tests/test_sql_authority_lifecycle_v534.py",
        [
            "SqlAuthorityLifecycle534Tests.test_snapshot_event_and_authorization_records_are_append_only",
            "SqlAuthorityLifecycle534Tests.test_release_activation_requires_signed_complete_external_evidence_and_is_immutable",
        ],
    )


def phase_historical_snapshot_stability() -> dict[str, Any]:
    return _run_python_tests(
        "executable/tests/test_sql_authority_lifecycle_v534.py",
        ["SqlAuthorityLifecycle534Tests.test_ledger_cutoff_keeps_prior_snapshot_stable_after_later_backdated_event"],
    )


def phase_replay_non_vacuity() -> dict[str, Any]:
    connection = _new_database()
    now = "2026-07-31T12:00:00Z"
    connection.execute("INSERT INTO wc_verifier_principals_v2 VALUES (?,?,?,?,?,?,?,?,?)", ("verifier:replay", "verifier_principal/v2", "key:replay", "Ed25519", "a" * 64, "active", now, None, now))
    connection.execute("INSERT INTO wc_replay_manifests_v2 VALUES (?,?,?,?,?,?,?,?)", ("manifest:ok", "replay_assumption_manifest/v2", "deep_time_replay", '[{"assumption_id":"a1","required_for_pass":true,"status":"satisfied"}]', '["a1"]', "block", "3" * 64, now))
    connection.execute("INSERT INTO wc_verification_grammars_v2 VALUES (?,?,?,?,?)", ("grammar:ok", "verification_grammar/v2", '[{"instruction_id":"i1"},{"instruction_id":"i2"}]', "4" * 64, now))
    connection.execute("INSERT INTO wc_verification_results_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("result:ok", "verification_result/v2", "grammar:ok", "4" * 64, "manifest:ok", "3" * 64, "artifact:1", "pass", '[{"instruction_id":"i1","status":"pass"},{"instruction_id":"i2","status":"pass"}]', '["a1"]', "verifier:replay", now))
    rejected = 0
    cases = [
        ("result:failed", '[{"instruction_id":"i1","status":"fail"},{"instruction_id":"i2","status":"pass"}]', '["a1"]'),
        ("result:missing", '[{"instruction_id":"i1","status":"pass"}]', '["a1"]'),
    ]
    for result_id, instructions, assumptions in cases:
        try:
            connection.execute("INSERT INTO wc_verification_results_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (result_id, "verification_result/v2", "grammar:ok", "4" * 64, "manifest:ok", "3" * 64, "artifact:bad", "pass", instructions, assumptions, "verifier:replay", now))
        except sqlite3.IntegrityError:
            rejected += 1
    connection.execute("INSERT INTO wc_replay_manifests_v2 VALUES (?,?,?,?,?,?,?,?)", ("manifest:unsatisfied", "replay_assumption_manifest/v2", "deep_time_replay", '[{"assumption_id":"a2","required_for_pass":true,"status":"unknown"}]', '["a2"]', "block", "5" * 64, now))
    try:
        connection.execute("INSERT INTO wc_verification_results_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("result:unsatisfied", "verification_result/v2", "grammar:ok", "4" * 64, "manifest:unsatisfied", "5" * 64, "artifact:bad2", "pass", '[{"instruction_id":"i1","status":"pass"},{"instruction_id":"i2","status":"pass"}]', '["a2"]', "verifier:replay", now))
    except sqlite3.IntegrityError:
        rejected += 1
    connection.close()
    assert_true(rejected == 3, f"replay adversarial rejection count mismatch: {rejected}")
    return {"happy_pass": True, "adversarial_cases_rejected": rejected}


def phase_openapi_security() -> dict[str, Any]:
    assert_true(yaml is not None, "PyYAML is required")
    spec = yaml.safe_load((ROOT / "executable/openapi/draft5_3_4_evidence_language_openapi.yaml").read_text(encoding="utf-8"))
    assert_true(spec["info"]["version"] == "v1.6-draft-5.3.4", "OpenAPI version mismatch")
    schemes = spec.get("components", {}).get("securitySchemes", {})
    assert_true("OAuth2" in schemes and "MutualTLS" in schemes and spec.get("security"), "OAuth2, mutual TLS, and top-level security are required")
    paths = spec["paths"]
    read_only = (
        "/v2/compiler-witnesses/{witness_id}",
        "/v2/proof-witnesses/{witness_id}",
        "/v2/theorem-promotion-gates/{gate_id}",
        "/v3/theorem-promotion-gates/{gate_id}",
        "/v3/verifier-keys/{key_id}",
        "/v3/verifier-keys/{key_id}/status-events",
    )
    for path in read_only:
        assert_true("get" in paths[path], f"{path} must be readable")
        assert_true(not {"post", "put", "patch", "delete"}.intersection(paths[path]), f"{path} exposes authority mutation")
    request_properties = spec["components"]["schemas"]["ProofCheckRequest"]["properties"]
    forbidden = {
        "result", "allowed", "compiler_witness", "proof_witness", "theorem_promotion_gate",
        "signature", "contains_sorry", "key_status_event", "signature_binding", "created_at",
        "lake_executable", "lean_executable", "expected_lake_sha256", "requested_toolchain",
        "execution_image_digest", "environment",
    }
    assert_true(not forbidden.intersection(request_properties), "proof-check request accepts authority outputs")
    assert_true("compiler_profile_id" in request_properties, "proof-check request lacks governed compiler-profile reference")
    assert_true("post" in paths["/v4/governance/verifier-key-status-actions"], "signed lifecycle request endpoint missing")
    assert_true("get" in paths["/v4/authoritative-theorems"], "deterministic as-of authority endpoint missing")
    return {"paths": len(paths), "security_schemes": sorted(schemes), "authority_outputs_read_only": True}


def phase_positive_baseline_runtime() -> dict[str, Any]:
    result = _run_python_tests("executable/tests/test_positive_baseline.py", [])
    assert_true(result["tests"] == 8, f"positive-baseline test count mismatch: {result['tests']}")
    return result


def phase_proof_authority_runtime() -> dict[str, Any]:
    result = _run_python_tests("executable/tests/test_proof_authority.py", [])
    assert_true(result["tests"] >= 22, f"proof-authority regression count too small: {result['tests']}")
    return {**result, "authority_mode": "governed_profile_immutable_snapshot_structured_result", "real_lean_claimed": False}


def phase_proof_check_service_boundary() -> dict[str, Any]:
    result = _run_python_tests("executable/tests/test_proof_check_service.py", [])
    assert_true(result["tests"] == 3, f"proof-check service boundary test count mismatch: {result['tests']}")
    return {**result, "request_paths_hashes_environment_timestamps": "rejected"}


def phase_result_channel_isolation() -> dict[str, Any]:
    tests = [
        "ProofAuthorityTests.test_missing_isolation_property_cannot_pass",
        "ProofAuthorityTests.test_untrusted_domain_has_no_request_or_result_mount",
        "ProofAuthorityTests.test_atomic_result_publication_rejects_symlink_hardlink_and_oversize",
        "ProofAuthorityTests.test_atomic_result_is_private_canonical_signed_and_single_link",
        "ProofAuthorityTests.test_private_result_reader_rejects_wrong_mode_and_noncanonical_json",
    ]
    return _run_python_tests("executable/tests/test_proof_authority.py", tests)


def phase_snapshot_derived_digests() -> dict[str, Any]:
    tests = [
        "ProofAuthorityTests.test_artifact_and_metadata_hashes_come_from_snapshot",
        "ProofAuthorityTests.test_mutation_before_snapshot_is_captured_not_prehashed",
        "ProofAuthorityTests.test_source_mutation_during_snapshot_is_rejected",
        "ProofAuthorityTests.test_metadata_and_transitive_import_mutation_during_snapshot_is_rejected",
        "ProofAuthorityTests.test_mutation_of_original_after_sealing_has_no_effect",
        "ProofAuthorityTests.test_mutation_of_sealed_snapshot_is_detected_after_execution",
        "ProofAuthorityTests.test_symlink_hardlink_fifo_prebuilt_and_native_source_are_rejected",
    ]
    return _run_python_tests("executable/tests/test_proof_authority.py", tests)


def phase_signed_verifier_result() -> dict[str, Any]:
    tests = [
        "ProofAuthorityTests.test_valid_signed_result_passes_and_binds_complete_closure",
        "ProofAuthorityTests.test_result_must_have_authorized_signature",
        "ProofAuthorityTests.test_true_source_claimed_false_fails",
        "ProofAuthorityTests.test_comment_only_declaration_fails",
        "ProofAuthorityTests.test_sorry_forbidden_axiom_and_unsafe_dependency_fail",
        "ProofAuthorityTests.test_result_identity_mismatches_and_noncanonical_sets_fail",
    ]
    return _run_python_tests("executable/tests/test_proof_authority.py", tests)


def phase_trust_root_loading() -> dict[str, Any]:
    return _run_python_tests(
        "executable/tests/test_proof_authority.py",
        [
            "ProofAuthorityTests.test_bad_registry_unknown_profile_and_toolchain_mismatch_are_rejected",
            "ProofAuthorityTests.test_trusted_root_loader_rejects_group_write_symlink_hardlink_and_traversal",
            "ProofAuthorityTests.test_request_api_cannot_supply_paths_hashes_environment_or_timestamp",
        ],
    )


def phase_effective_sandbox_invocation() -> dict[str, Any]:
    profile = load_json("authority/hermetic_lean_sandbox_profile_v2.json")
    assert_true(profile["result_channel_architecture"] == "untrusted_compile_then_trusted_signed_verifier", "two-domain sandbox is not canonical")
    untrusted = profile["untrusted_compilation_domain"]
    trusted = profile["trusted_verifier_domain"]
    assert_true(untrusted["verifier_request_mount"] == "absent" and untrusted["final_result_mount"] == "absent", "untrusted compiler can access trusted result controls")
    assert_true(trusted["inspection_file"] == "regular_0600_single_link_exclusive_atomic", "trusted inspection publication invariant missing")
    assert_true(trusted["final_result_mount"] == "absent", "final signed result is mounted into a container domain")
    controls = profile["runtime_controls"]
    assert_true(controls["network_mode"] == "none" and controls["read_only_rootfs"] is True, "sandbox network/rootfs policy is not fail-closed")
    source = (ROOT / "executable/runtime/proof_authority.py").read_text(encoding="utf-8")
    for token in ("--network=none", "--read-only", "--cap-drop=ALL", "--pids-limit", "--pull=never", "EffectiveSandboxInvocation"):
        assert_true(token in source, f"runtime omits effective sandbox binding {token}")
    tests = _run_python_tests(
        "executable/tests/test_proof_authority.py",
        ["ProofAuthorityTests.test_untrusted_domain_has_no_request_or_result_mount", "ProofAuthorityTests.test_result_identity_mismatches_and_noncanonical_sets_fail"],
    )
    return {"profile_id": profile["profile_id"], "effective_invocation_bound": True, "tests": tests["tests"]}


def phase_governance_scope_authorization() -> dict[str, Any]:
    tests = [
        "SqlAuthorityLifecycle534Tests.test_full_signed_authority_chain_is_accepted_only_after_release_activation",
        "SqlAuthorityLifecycle534Tests.test_tampered_trusted_result_and_missing_profile_activation_are_rejected",
        "SqlAuthorityLifecycle534Tests.test_tampered_event_wrong_scope_and_duplicate_sequence_are_rejected",
        "SqlAuthorityLifecycle534Tests.test_expired_authorization_and_wrong_typed_target_are_rejected",
        "SqlAuthorityLifecycle534Tests.test_backdated_event_requires_explicit_correction_authorization",
        "SqlAuthorityLifecycle534Tests.test_theorem_authority_is_disabled_without_external_release_evidence",
        "SqlAuthorityLifecycle534Tests.test_release_activation_requires_signed_complete_external_evidence_and_is_immutable",
    ]
    return _run_python_tests("executable/tests/test_sql_authority_lifecycle_v534.py", tests)


def phase_deterministic_witness_identity() -> dict[str, Any]:
    tests = [
        "ProofAuthorityTests.test_generated_module_is_deterministic_minimal_and_read_only",
        "ProofAuthorityTests.test_event_set_root_is_ordered_and_duplicate_safe",
        "ProofAuthorityTests.test_valid_signed_result_passes_and_binds_complete_closure",
    ]
    return _run_python_tests("executable/tests/test_proof_authority.py", tests)


def phase_formal_manifest_coverage() -> dict[str, Any]:
    manifest = load_json("refs/formal_toolchain/tla_toolchain_manifest_v1_0.json")
    modules = {entry["module"]: entry for entry in manifest["tla_modules"]}
    for name in ("ProofAuthorityV2", "ProofAuthorityV3", "ProofAuthorityV4", "ProofAuthorityV5"):
        assert_true(name in modules, f"active strict TLA manifest omits {name}")
        assert_true((ROOT / modules[name]["spec"]).is_file() and (ROOT / modules[name]["config"]).is_file(), f"{name} spec/config missing")
    process = subprocess.run([sys.executable, "executable/formal/run_tla_model_check.py", "--mode", "advisory", "--json"], cwd=ROOT, text=True, capture_output=True, timeout=180, env=_subprocess_environment())
    assert_true(process.returncode == 0, f"TLA manifest/static check failed: {process.stdout} {process.stderr}")
    result = json.loads(process.stdout)
    assert_true(not result["static_errors"], f"TLA static errors: {result['static_errors']}")
    assert_true({"ProofAuthorityV2", "ProofAuthorityV3", "ProofAuthorityV4", "ProofAuthorityV5"}.issubset(result["modules_checked"]), "runner did not execute active authority manifest entries")
    lean_manifest = load_json("refs/formal_toolchain/lean_toolchain_manifest_v1_0.json")
    verifier_sources = lean_manifest.get("hermetic_verifier_sources", [])
    assert_true(verifier_sources and all((ROOT / path).is_file() for path in verifier_sources), "trusted Lean verifier source is absent from the manifest")
    assert_true(lean_manifest.get("authority_activation_requires_real_image") is True, "Lean manifest does not fail closed on real-image evidence")
    return {"modules_checked": result["modules_checked"], "tlc_available": result["tlc_available"], "strict_tlc_claimed": False, "hermetic_verifier_sources": verifier_sources}


def phase_version_consistency() -> dict[str, Any]:
    expected = "v1.6-draft-5.3.4"
    descriptor = load_json(DESCRIPTOR_PATH.name)
    metadata = load_json("PACKAGE_METADATA_v1_6_draft_5_3_4.json")
    registry = load_json("refs/schema_registry_v1_6_draft_5_3_4.json")
    package = load_json("package.json")
    lock = load_json("package-lock.json")
    tla = load_json("refs/formal_toolchain/tla_toolchain_manifest_v1_0.json")
    gate_status = load_json("DRAFT5_3_4_RELEASE_GATE_STATUS.json")
    assert_true(descriptor["active_version"] == metadata["version"] == expected, "descriptor/package metadata version mismatch")
    assert_true(package["version"] == "1.6.5-3-4" and lock["version"] == package["version"], "npm package/lock version mismatch")
    assert_true(package["name"].endswith("draft-5-3-4-validation") and lock["name"] == package["name"], "npm package/lock identity mismatch")
    assert_true(registry.get("registry_version") == expected, "schema registry version mismatch")
    registered_schemas = set(registry["canonical_schemas"]) | set(registry["legacy_read_schemas"])
    assert_true(all((ROOT / path).is_file() for path in registered_schemas), "schema registry references a missing schema")
    required_new_schemas = {
        "schemas/governed_compiler_registry_v2.schema.json", "schemas/lean_verifier_result_v2.schema.json",
        "schemas/lean_compiler_witness_v3.schema.json", "schemas/governance_authorization_witness_v2.schema.json",
        "schemas/governance_event_v1.schema.json", "schemas/authority_snapshot_v2.schema.json",
        "schemas/authority_supersession_v3.schema.json", "schemas/theorem_promotion_gate_v3.schema.json",
        "schemas/release_activation_evidence_v1.schema.json",
    }
    assert_true(required_new_schemas.issubset(set(registry["canonical_schemas"])), "canonical registry omits a Draft 5.3.4 schema")
    for fixture in (ROOT / "executable/tests/fixtures/draft5_3_4").glob("*/*.json"):
        wrapper = json.loads(fixture.read_text(encoding="utf-8"))
        assert_true((ROOT / str(wrapper.get("schema_ref", ""))).is_file(), f"active fixture references a missing schema: {fixture.name}")
    assert_true("Draft 5.3.4" in tla["package"] and any(item["module"] == "ProofAuthorityV5" for item in tla["tla_modules"]), "formal manifest version/active model mismatch")
    assert_true(gate_status["gates"]["H_corpus_consistency"] == "portable_pass", "release Gate H is not reconciled to portable validation")
    assert_true('v!"5.3.4"' in (ROOT / "lakefile.lean").read_text(encoding="utf-8"), "Lake package version mismatch")
    assert_true((ROOT / "migration/draft5_3_3_to_draft5_3_4.sql").is_file(), "active migration filename does not identify 5.3.4")
    for relative in ("START_HERE.md", "CORPUS_INDEX_v1_6_draft_5_3_4.md", "duotronic_witness_contract_v1_6_draft_5_3_4.md", "RELEASE_NOTES_v1_6_draft_5_3_4.md"):
        assert_true("5.3.4" in (ROOT / relative).read_text(encoding="utf-8"), f"active document lacks 5.3.4 identity: {relative}")
    for report_path in ROOT.glob("DRAFT5_3_4*.json"):
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert_true(report.get("package_version") == expected, f"active report version mismatch: {report_path.name}")
    return {"active_version": expected, "npm_version": package["version"], "formal_model": "ProofAuthorityV5", "legacy_files_scoped_as_history": True}


def phase_historical_package_integrity() -> dict[str, Any]:
    results = []
    for filename, (expected_hash, expected_count) in HISTORY_ARCHIVES.items():
        archive = ROOT / "history/source_packages" / filename
        assert_true(sha256(archive) == expected_hash, f"retained archive hash mismatch: {filename}")
        with zipfile.ZipFile(archive) as package:
            bad = package.testzip()
            count = sum(not name.endswith("/") for name in package.namelist())
        assert_true(bad is None, f"retained archive corrupt at {bad}: {filename}")
        assert_true(count == expected_count, f"retained archive file-count mismatch: {filename}")
        results.append({"archive": filename, "sha256": expected_hash, "file_count": count})
    return {"archives": results}


def phase_strict_lean() -> dict[str, Any]:
    process = subprocess.run([sys.executable, "executable/formal/run_lean_build.py", "--mode", "strict", "--json"], cwd=ROOT, text=True, capture_output=True, timeout=600, env=_subprocess_environment())
    result = json.loads(process.stdout)
    if not result.get("lake_available"):
        raise PhaseSkipped("strict Lean unavailable; deployment theorem authority remains disabled")
    assert_true(process.returncode == 0 and result.get("status") == "pass", f"strict Lean failed: {result}")
    return result


def phase_strict_tlc() -> dict[str, Any]:
    process = subprocess.run([sys.executable, "executable/formal/run_tla_model_check.py", "--mode", "strict", "--json"], cwd=ROOT, text=True, capture_output=True, timeout=600, env=_subprocess_environment())
    result = json.loads(process.stdout)
    if not result.get("tlc_available"):
        raise PhaseSkipped("strict TLC unavailable; formal deployment assurance remains incomplete")
    assert_true(process.returncode == 0 and result.get("status") == "pass", f"strict TLC failed: {result}")
    expected = {entry["module"] for entry in load_json("refs/formal_toolchain/tla_toolchain_manifest_v1_0.json")["tla_modules"]}
    passed = {item["module"] for item in result["tlc_results"] if item["return_code"] == 0}
    assert_true(passed == expected, f"strict TLC did not pass every manifest module: expected={sorted(expected)} passed={sorted(passed)}")
    return result


def phase_hermetic_lean_integration() -> dict[str, Any]:
    process = subprocess.run(
        [sys.executable, "executable/formal/run_hermetic_proof_authority_integration.py", "--json"],
        cwd=ROOT, text=True, capture_output=True, timeout=1200, env=_subprocess_environment(),
    )
    result = json.loads(process.stdout)
    if not result.get("real_lean_executed"):
        raise PhaseSkipped("approved hermetic Lean image/configuration unavailable; theorem authority remains disabled")
    assert_true(process.returncode == 0 and result.get("status") == "passed", f"real hermetic Lean integration failed: {result}")
    return result


def _build_attestation(subject_type: str) -> dict[str, Any]:
    status = load_json("DRAFT5_3_4_BUILD_ATTESTATION_STATUS.json")
    matches = [item for item in status.get("attestations", []) if item.get("subject_type") == subject_type]
    if not matches:
        raise PhaseSkipped(f"signed {subject_type} build attestation absent; execution closure remains incomplete")
    attestation = matches[-1]
    assert_true(attestation.get("verified") is True and attestation.get("trusted_builder") is True, f"{subject_type} attestation is not verified from a trusted builder")
    assert_true(attestation.get("schema_version") == "build_attestation/v1", f"{subject_type} attestation schema mismatch")
    return attestation


def phase_oci_image_build_attestation() -> dict[str, Any]:
    return _build_attestation("oci_image")


def phase_verifier_executable_build_attestation() -> dict[str, Any]:
    return _build_attestation("trusted_verifier_executable")


def phase_external_signature() -> dict[str, Any]:
    status = load_json("refs/trust/RELEASE_SIGNATURE_STATUS_v1_6_draft_5_3_4.json")
    if not status.get("external_signature_present"):
        raise PhaseSkipped("external governance signature absent; package is not an external trust root")
    assert_true(status.get("governance_trust_anchor_accepted"), "external signature is not accepted as a governance trust anchor")
    return status


REQUIRED_PHASE_FUNCTIONS: dict[str, Callable[[], dict[str, Any]]] = {
    "descriptor": phase_descriptor,
    "dependencies": phase_dependencies,
    "hash_closure": phase_hash_closure,
    "json_schemas": phase_json_schemas,
    "valid_fixtures": phase_valid_fixtures,
    "invalid_fixtures": phase_invalid_fixtures,
    "sql_migration": phase_sql_migration,
    "sql_event_ledger": phase_sql_event_ledger,
    "sql_typed_supersession": phase_sql_typed_supersession,
    "sql_immutability": phase_sql_immutability,
    "historical_snapshot_stability": phase_historical_snapshot_stability,
    "replay_non_vacuity": phase_replay_non_vacuity,
    "openapi_security": phase_openapi_security,
    "positive_baseline_runtime": phase_positive_baseline_runtime,
    "proof_authority_runtime": phase_proof_authority_runtime,
    "proof_check_service_boundary": phase_proof_check_service_boundary,
    "result_channel_isolation": phase_result_channel_isolation,
    "snapshot_derived_digests": phase_snapshot_derived_digests,
    "signed_verifier_result": phase_signed_verifier_result,
    "trust_root_loading": phase_trust_root_loading,
    "effective_sandbox_invocation": phase_effective_sandbox_invocation,
    "governance_scope_authorization": phase_governance_scope_authorization,
    "deterministic_witness_identity": phase_deterministic_witness_identity,
    "formal_manifest_coverage": phase_formal_manifest_coverage,
    "version_consistency": phase_version_consistency,
    "historical_package_integrity": phase_historical_package_integrity,
}

OPTIONAL_PHASE_FUNCTIONS: dict[str, Callable[[], dict[str, Any]]] = {
    "strict_lean": phase_strict_lean,
    "strict_tlc": phase_strict_tlc,
    "hermetic_lean_integration": phase_hermetic_lean_integration,
    "oci_image_build_attestation": phase_oci_image_build_attestation,
    "verifier_executable_build_attestation": phase_verifier_executable_build_attestation,
    "external_signature": phase_external_signature,
}


def run_phase(name: str, required: bool, function: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    try:
        details = function()
        status = "passed"
        error = None
    except PhaseSkipped as exception:
        details = None
        status = "skipped"
        error = str(exception)
    except Exception as exception:
        details = None
        status = "failed"
        error = str(exception)
        trace = traceback.format_exc()
    result: dict[str, Any] = {
        "name": name,
        "required": required,
        "status": status,
        "duration_seconds": round((datetime.now(timezone.utc) - started).total_seconds(), 6),
    }
    if details is not None:
        result["details"] = details
    if error is not None:
        result["error"] = error
    if status == "failed":
        result["traceback"] = trace
    return result


def main() -> int:
    try:
        descriptor = json.loads(DESCRIPTOR_PATH.read_text(encoding="utf-8"))
        required = descriptor.get("required_validation_phases", [])
        optional = descriptor.get("optional_validation_phases", [])
    except Exception:
        descriptor = {}
        required = ["descriptor"]
        optional = []

    phases: list[dict[str, Any]] = []
    for name in dict.fromkeys(required):
        function = REQUIRED_PHASE_FUNCTIONS.get(name)
        if function is not None:
            phases.append(run_phase(name, True, function))
    for name in dict.fromkeys(optional):
        function = OPTIONAL_PHASE_FUNCTIONS.get(name)
        if function is not None:
            phases.append(run_phase(name, False, function))

    reconciliation = reconcile_required_phases(required, phases)
    optional_results = [phase for phase in phases if not phase["required"]]
    activation_evidence_complete = bool(optional_results) and all(phase["status"] == "passed" for phase in optional_results)
    report = {
        "schema_version": "draft5_3_4_validation_report/v1",
        "package_version": "v1.6-draft-5.3.4",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": "passed" if reconciliation["all_required_passed"] else "failed",
        "freeze_state": "permanently_not_frozen",
        "lifecycle_policy": "living_contract_never_freeze",
        **reconciliation,
        "required_failed_count": len(reconciliation["required_failed"]),
        "required_skipped_count": len(reconciliation["required_skipped"]),
        "required_missing_count": len(reconciliation["required_missing"]),
        "optional_failed": sorted(phase["name"] for phase in optional_results if phase["status"] == "failed"),
        "optional_skipped": sorted(phase["name"] for phase in optional_results if phase["status"] == "skipped"),
        "authority_activation_evidence_complete": activation_evidence_complete,
        "theorem_authority_enabled_by_portable_validation": False,
        "phases": phases,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["overall_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
