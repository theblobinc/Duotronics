#!/usr/bin/env python3
"""Descriptor-reconciled fail-closed validator for Draft 5.3.3."""

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
DESCRIPTOR_PATH = ROOT / "CANONICAL_CORPUS_v1_6_draft_5_3_3.json"
REPORT_PATH = ROOT / "DRAFT5_3_3_VALIDATION_REPORT.json"
HISTORY_ARCHIVES = {
    "v1.6 - Draft 5.2.2.zip": ("437395d28c452f0a20937eaf562020afae2214edf01a8df2fe6dadd062201c22", 492),
    "v1.6 - Draft 5.3.1.zip": ("26608233721f6b56ce6dfe5dfe653029c421e72a551196e004d2b2d3d59de588", 560),
    "v1.6 - Draft 5.3.2.zip": ("57daa37189dcd8c0cf8cff990850393f4feaa70aeea9736b5edabffc58a37675", 1158),
}


class PhaseSkipped(RuntimeError):
    pass


def shake256_512(path: Path) -> str:
    return hashlib.shake_256(path.read_bytes()).hexdigest(64)


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
    return connection


def phase_descriptor() -> dict[str, Any]:
    descriptor = load_json(DESCRIPTOR_PATH.name)
    assert_true(descriptor["active_version"] == "v1.6-draft-5.3.3", "active version mismatch")
    assert_true(descriptor["freeze_state"] == "permanently_not_frozen", "living contract must remain permanently_not_frozen")
    assert_true(descriptor["lifecycle_policy"] == "living_contract_never_freeze", "living-contract policy mismatch")
    required = descriptor["required_validation_phases"]
    optional = descriptor["optional_validation_phases"]
    assert_true(required and len(required) == len(set(required)), "required phase identifiers must be nonempty and unique")
    assert_true(len(optional) == len(set(optional)), "optional phase identifiers must be unique")
    assert_true(not set(required).intersection(optional), "required and optional phase identifiers overlap")
    refs = [
        "primary_contract", "start_here", "corpus_index", "inventory", "checksum_manifest",
        "human_manifest", "schema_registry", "validator", "schema_validator", "canonical_openapi",
        "base_sql", "authority_migration", "proof_authority_runtime", "proof_check_service",
        "sandbox_profile", "formal_toolchain_manifest", "mathematics_profile",
    ]
    paths = [descriptor[key] for key in refs]
    paths.extend(descriptor["authority_migrations"])
    paths.extend(descriptor["formal_authority_profiles"])
    missing = [relative for relative in paths if not (ROOT / relative).is_file()]
    assert_true(not missing, f"descriptor references missing files: {missing}")
    resolver = (ROOT / "kernel/corpus_boot_and_canonical_resolver_v1_0.md").read_text(encoding="utf-8")
    for token in (DESCRIPTOR_PATH.name, "PACKAGE_INVENTORY_v1_6_draft_5_3_3.json", "CHECKSUMS_v1_6_draft_5_3_3.shake256_512"):
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
    inventory = load_json("PACKAGE_INVENTORY_v1_6_draft_5_3_3.json")
    records = inventory["files"]
    by_path = {record["path"]: record for record in records}
    assert_true(len(by_path) == len(records), "duplicate inventory paths")
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and not _is_runtime_cache(path)
    }
    assert_true(actual == set(by_path), f"inventory path mismatch; missing={sorted(actual-set(by_path))[:10]} extra={sorted(set(by_path)-actual)[:10]}")
    checksum_lines = (ROOT / "refs/manifest/CHECKSUMS_v1_6_draft_5_3_3.shake256_512").read_text(encoding="utf-8").splitlines()
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
        digest = shake256_512(path)
        assert_true(record["size_bytes"] == path.stat().st_size, f"inventory size mismatch: {relative}")
        assert_true(record["shake256_512"] == digest, f"inventory hash mismatch: {relative}")
        assert_true(checksums.get(relative) == digest, f"checksum mismatch: {relative}")
    expected_covered = {path for path, record in by_path.items() if not record["excluded_from_hash_closure"]}
    assert_true(set(checksums) == expected_covered, "checksum path set mismatch")
    return {"file_count": len(records), "covered": covered, "excluded_generated": excluded}


def _schema_phase(name: str) -> dict[str, Any]:
    command = ["node", "executable/validators/validate_draft5_3_3_schemas.mjs", "--phase", name]
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
    assert_true("v1.6-draft-5.3.3" in generations, "5.3.3 schema generation missing")
    columns = {row[1] for row in connection.execute("PRAGMA table_info(wc_lean_compiler_witnesses_v2)")}
    hardening = (
        "original_source_tree_shake256_512", "immutable_snapshot_shake256_512", "compiler_profile_id",
        "compiler_registry_shake256_512", "lake_executable_shake256_512", "lean_executable_shake256_512",
        "lean_stdlib_tree_shake256_512", "dependency_closure_shake256_512", "execution_image_digest",
        "sandbox_policy_shake256_512", "verifier_binary_shake256_512", "structured_result_shake256_512",
        "snapshot_verified_immutable", "clean_source_build", "prebuilt_artifacts_rejected",
        "hermetic_environment", "network_disabled", "resource_limits_enforced",
        "structured_inspection_complete", "trusted_timestamp_source",
    )
    for name in hardening:
        assert_true(name in columns, f"compiler witness hardening column missing: {name}")
    assert_true(not connection.execute("PRAGMA foreign_key_check").fetchall(), "foreign-key check failed")
    required_objects = (
        "wc_governance_authorities_v1", "wc_governance_authorization_witnesses_v1",
        "wc_verifier_key_status_events_v2", "wc_authority_supersessions_v2",
        "wc_authority_snapshots_v1", "wc_authoritative_theorems_as_of_v3",
        "wc_authority_signature_bindings_v2", "wc_currently_valid_verifiers_v4",
    )
    objects = connection.execute(
        f"SELECT count(*) FROM sqlite_master WHERE name IN ({','.join('?' for _ in required_objects)})",
        required_objects,
    ).fetchone()[0]
    connection.close()
    assert_true(objects == len(required_objects), "5.3.3 governance/as-of objects missing")
    return {"generations": generations, "hardening_columns": len(hardening), "governance_as_of_objects": objects}


def phase_sql_gate_adversarial() -> dict[str, Any]:
    tests = [
        "SqlAuthorityLifecycle533Tests.test_happy_hermetic_chain_creates_gate",
        "SqlAuthorityLifecycle533Tests.test_nonhermetic_compiler_cannot_create_gate",
        "SqlAuthorityLifecycle533Tests.test_revoked_key_cannot_create_gate",
        "SqlAuthorityLifecycle533Tests.test_expired_key_cannot_create_gate",
    ]
    return _run_python_tests("executable/tests/test_sql_authority_lifecycle_v533.py", tests)


def phase_sql_immutability() -> dict[str, Any]:
    tests = [
        "SqlAuthorityLifecycle533Tests.test_lifecycle_and_snapshot_tables_are_append_only",
        "SqlAuthorityLifecycle533Tests.test_compiler_signature_binding_covers_lean_digest",
    ]
    return _run_python_tests("executable/tests/test_sql_authority_lifecycle_v533.py", tests)


def phase_replay_non_vacuity() -> dict[str, Any]:
    connection = _new_database()
    now = "2026-07-31T12:00:00Z"
    connection.execute("INSERT INTO wc_verifier_principals_v2 VALUES (?,?,?,?,?,?,?,?,?)", ("verifier:replay", "verifier_principal/v2", "key:replay", "ML-DSA-87", "a" * 128, "active", now, None, now))
    connection.execute("INSERT INTO wc_replay_manifests_v2 VALUES (?,?,?,?,?,?,?,?)", ("manifest:ok", "replay_assumption_manifest/v2", "deep_time_replay", '[{"assumption_id":"a1","required_for_pass":true,"status":"satisfied"}]', '["a1"]', "block", "3" * 128, now))
    connection.execute("INSERT INTO wc_verification_grammars_v2 VALUES (?,?,?,?,?)", ("grammar:ok", "verification_grammar/v2", '[{"instruction_id":"i1"},{"instruction_id":"i2"}]', "4" * 128, now))
    connection.execute("INSERT INTO wc_verification_results_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("result:ok", "verification_result/v2", "grammar:ok", "4" * 128, "manifest:ok", "3" * 128, "artifact:1", "pass", '[{"instruction_id":"i1","status":"pass"},{"instruction_id":"i2","status":"pass"}]', '["a1"]', "verifier:replay", now))
    rejected = 0
    cases = [
        ("result:failed", '[{"instruction_id":"i1","status":"fail"},{"instruction_id":"i2","status":"pass"}]', '["a1"]'),
        ("result:missing", '[{"instruction_id":"i1","status":"pass"}]', '["a1"]'),
    ]
    for result_id, instructions, assumptions in cases:
        try:
            connection.execute("INSERT INTO wc_verification_results_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (result_id, "verification_result/v2", "grammar:ok", "4" * 128, "manifest:ok", "3" * 128, "artifact:bad", "pass", instructions, assumptions, "verifier:replay", now))
        except sqlite3.IntegrityError:
            rejected += 1
    connection.execute("INSERT INTO wc_replay_manifests_v2 VALUES (?,?,?,?,?,?,?,?)", ("manifest:unsatisfied", "replay_assumption_manifest/v2", "deep_time_replay", '[{"assumption_id":"a2","required_for_pass":true,"status":"unknown"}]', '["a2"]', "block", "5" * 128, now))
    try:
        connection.execute("INSERT INTO wc_verification_results_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("result:unsatisfied", "verification_result/v2", "grammar:ok", "4" * 128, "manifest:unsatisfied", "5" * 128, "artifact:bad2", "pass", '[{"instruction_id":"i1","status":"pass"},{"instruction_id":"i2","status":"pass"}]', '["a2"]', "verifier:replay", now))
    except sqlite3.IntegrityError:
        rejected += 1
    connection.close()
    assert_true(rejected == 3, f"replay adversarial rejection count mismatch: {rejected}")
    return {"happy_pass": True, "adversarial_cases_rejected": rejected}


def phase_openapi_security() -> dict[str, Any]:
    assert_true(yaml is not None, "PyYAML is required")
    spec = yaml.safe_load((ROOT / "executable/openapi/draft5_3_3_evidence_language_openapi.yaml").read_text(encoding="utf-8"))
    assert_true(spec["info"]["version"] == "v1.6-draft-5.3.3", "OpenAPI version mismatch")
    schemes = spec.get("components", {}).get("securitySchemes", {})
    assert_true("OAuth2" in schemes and "MutualTLS" in schemes and spec.get("security"), "OAuth2, mutual TLS, and top-level security are required")
    paths = spec["paths"]
    read_only = (
        "/v2/compiler-witnesses/{witness_id}",
        "/v2/proof-witnesses/{witness_id}",
        "/v2/theorem-promotion-gates/{gate_id}",
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
        "lake_executable", "lean_executable", "expected_lake_shake256_512", "requested_toolchain",
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


def phase_governed_compiler_registry() -> dict[str, Any]:
    tests = [
        "ProofAuthorityTests.test_bad_registry_signature_is_rejected",
        "ProofAuthorityTests.test_unknown_compiler_profile_is_rejected",
        "ProofAuthorityTests.test_request_api_has_no_path_hash_or_created_at_parameters",
        "ProofAuthorityTests.test_wrong_actual_lean_digest_cannot_pass",
    ]
    return _run_python_tests("executable/tests/test_proof_authority.py", tests)


def phase_immutable_snapshot_runtime() -> dict[str, Any]:
    tests = [
        "ProofAuthorityTests.test_prebuilt_olean_is_rejected_before_runner",
        "ProofAuthorityTests.test_native_plugin_is_rejected_before_runner",
        "ProofAuthorityTests.test_proof_outside_source_tree_is_rejected",
        "ProofAuthorityTests.test_symlinked_source_is_rejected",
        "ProofAuthorityTests.test_generated_target_and_witness_id_are_deterministic",
    ]
    return _run_python_tests("executable/tests/test_proof_authority.py", tests)


def phase_structured_lean_result() -> dict[str, Any]:
    tests = [
        "ProofAuthorityTests.test_human_readable_fake_axiom_output_cannot_pass",
        "ProofAuthorityTests.test_wrong_structured_request_hash_cannot_pass",
        "ProofAuthorityTests.test_duplicate_axiom_result_is_not_canonical",
        "ProofAuthorityTests.test_sorry_ax_fails",
        "ProofAuthorityTests.test_unauthorized_attributed_axiom_fails",
    ]
    return _run_python_tests("executable/tests/test_proof_authority.py", tests)


def phase_governance_event_authorization() -> dict[str, Any]:
    tests = [
        "SqlAuthorityLifecycle533Tests.test_unsigned_or_tampered_key_event_is_rejected",
        "SqlAuthorityLifecycle533Tests.test_governance_authorization_policy_binding_is_enforced",
        "SqlAuthorityLifecycle533Tests.test_revoked_key_cannot_create_gate",
    ]
    return _run_python_tests("executable/tests/test_sql_authority_lifecycle_v533.py", tests)


def phase_deterministic_authority_replay() -> dict[str, Any]:
    tests = ["SqlAuthorityLifecycle533Tests.test_as_of_snapshot_is_stable_after_later_revocation"]
    return _run_python_tests("executable/tests/test_sql_authority_lifecycle_v533.py", tests)


def phase_hermetic_sandbox_profile() -> dict[str, Any]:
    profile = load_json("authority/hermetic_lean_sandbox_profile_v1.json")
    assert_true(profile["network"] == "none" and profile["root_filesystem"] == "read_only", "sandbox is not networkless/read-only")
    assert_true(profile["linux_capabilities"] == "drop_all" and profile["no_new_privileges"] is True, "sandbox privilege controls missing")
    assert_true(profile["result_channel"] == "canonical_json_file_only" and profile["stdout_authority"] is False, "stdout remains authoritative")
    source = (ROOT / "executable/runtime/proof_authority.py").read_text(encoding="utf-8")
    for token in ("--network=none", "--read-only", "--cap-drop=ALL", "--pids-limit=128", "--pull=never"):
        assert_true(token in source, f"runtime omits sandbox control {token}")
    assert_true("env={**os.environ" not in source, "sandbox runner inherits the complete host environment")
    return {"profile_id": profile["profile_id"], "forbidden_source_artifacts": len(profile["forbidden_source_artifacts"]), "stdout_authority": False}


def phase_formal_manifest_coverage() -> dict[str, Any]:
    manifest = load_json("refs/formal_toolchain/tla_toolchain_manifest_v1_0.json")
    modules = {entry["module"]: entry for entry in manifest["tla_modules"]}
    for name in ("ProofAuthorityV2", "ProofAuthorityV3", "ProofAuthorityV4"):
        assert_true(name in modules, f"active strict TLA manifest omits {name}")
        assert_true((ROOT / modules[name]["spec"]).is_file() and (ROOT / modules[name]["config"]).is_file(), f"{name} spec/config missing")
    process = subprocess.run([sys.executable, "executable/formal/run_tla_model_check.py", "--mode", "advisory", "--json"], cwd=ROOT, text=True, capture_output=True, timeout=180, env=_subprocess_environment())
    assert_true(process.returncode == 0, f"TLA manifest/static check failed: {process.stdout} {process.stderr}")
    result = json.loads(process.stdout)
    assert_true(not result["static_errors"], f"TLA static errors: {result['static_errors']}")
    assert_true({"ProofAuthorityV2", "ProofAuthorityV3", "ProofAuthorityV4"}.issubset(result["modules_checked"]), "runner did not execute active authority manifest entries")
    lean_manifest = load_json("refs/formal_toolchain/lean_toolchain_manifest_v1_0.json")
    verifier_sources = lean_manifest.get("hermetic_verifier_sources", [])
    assert_true(verifier_sources and all((ROOT / path).is_file() for path in verifier_sources), "trusted Lean verifier source is absent from the manifest")
    assert_true(lean_manifest.get("authority_activation_requires_real_image") is True, "Lean manifest does not fail closed on real-image evidence")
    return {"modules_checked": result["modules_checked"], "tlc_available": result["tlc_available"], "strict_tlc_claimed": False, "hermetic_verifier_sources": verifier_sources}


def phase_historical_package_integrity() -> dict[str, Any]:
    results = []
    for filename, (expected_hash, expected_count) in HISTORY_ARCHIVES.items():
        archive = ROOT / "history/source_packages" / filename
        assert_true(shake256_512(archive) == expected_hash, f"retained archive hash mismatch: {filename}")
        with zipfile.ZipFile(archive) as package:
            bad = package.testzip()
            count = sum(not name.endswith("/") for name in package.namelist())
        assert_true(bad is None, f"retained archive corrupt at {bad}: {filename}")
        assert_true(count == expected_count, f"retained archive file-count mismatch: {filename}")
        results.append({"archive": filename, "shake256_512": expected_hash, "file_count": count})
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


def phase_external_signature() -> dict[str, Any]:
    status = load_json("refs/trust/RELEASE_SIGNATURE_STATUS_v1_6_draft_5_3_3.json")
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
    "sql_gate_adversarial": phase_sql_gate_adversarial,
    "sql_immutability": phase_sql_immutability,
    "replay_non_vacuity": phase_replay_non_vacuity,
    "openapi_security": phase_openapi_security,
    "positive_baseline_runtime": phase_positive_baseline_runtime,
    "proof_authority_runtime": phase_proof_authority_runtime,
    "proof_check_service_boundary": phase_proof_check_service_boundary,
    "governed_compiler_registry": phase_governed_compiler_registry,
    "immutable_snapshot_runtime": phase_immutable_snapshot_runtime,
    "structured_lean_result": phase_structured_lean_result,
    "governance_event_authorization": phase_governance_event_authorization,
    "deterministic_authority_replay": phase_deterministic_authority_replay,
    "hermetic_sandbox_profile": phase_hermetic_sandbox_profile,
    "formal_manifest_coverage": phase_formal_manifest_coverage,
    "historical_package_integrity": phase_historical_package_integrity,
}

OPTIONAL_PHASE_FUNCTIONS: dict[str, Callable[[], dict[str, Any]]] = {
    "strict_lean": phase_strict_lean,
    "strict_tlc": phase_strict_tlc,
    "hermetic_lean_integration": phase_hermetic_lean_integration,
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
        "schema_version": "draft5_3_3_validation_report/v1",
        "package_version": "v1.6-draft-5.3.3",
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
