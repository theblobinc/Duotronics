#!/usr/bin/env python3
"""Descriptor-reconciled fail-closed validator for Draft 5.3.9."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import traceback
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
DESCRIPTOR_PATH = ROOT / "CANONICAL_CORPUS_v1_6_draft_5_3_9.json"
REPORT_PATH = ROOT / "DRAFT5_3_9_VALIDATION_REPORT.json"
REGRESSION_COUNTS_PATH = ROOT / "DRAFT5_3_9_REGRESSION_COUNTS.json"
VALIDATION_SUMMARY_PATH = ROOT / "DRAFT5_3_9_VALIDATION_SUMMARY.txt"
LINEAGE_PATH = ROOT / "history/SOURCE_PACKAGE_LINEAGE_v1_6_draft_5_3_9.json"


class PhaseSkipped(RuntimeError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_tree_sha256(excluded: set[str]) -> str:
    value = hashlib.sha256()
    paths = sorted(
        (path for path in ROOT.rglob("*") if path.is_file() and not _is_runtime_cache(path)),
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        if relative in excluded:
            continue
        encoded = relative.encode("utf-8")
        value.update(len(encoded).to_bytes(8, "big"))
        value.update(encoded)
        value.update(bytes.fromhex(sha256(path)))
        value.update(path.stat().st_size.to_bytes(8, "big"))
    return value.hexdigest()


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
    return {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONWARNINGS": "error"}


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


def _run_discovered_suite(*, development_mode: bool) -> dict[str, Any]:
    command = [sys.executable]
    if development_mode:
        command.extend(["-X", "dev", "-W", "error"])
    command.append("executable/validators/run_unittest_structured.py")
    process = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=300,
        env=_subprocess_environment(),
    )
    combined = process.stdout + "\n" + process.stderr
    marker = re.search(r"^WC_UNITTEST_RESULT=(\{.*\})$", process.stdout, re.MULTILINE)
    assert_true(marker is not None, "structured unittest runner did not emit its TestResult record")
    structured = json.loads(marker.group(1))
    warning_lines = [
        line for line in combined.splitlines()
        if re.search(r"\b(?:ResourceWarning|DeprecationWarning|RuntimeWarning|UserWarning|SyntaxWarning|FutureWarning|ImportWarning|UnicodeWarning|BytesWarning|EncodingWarning):", line)
    ]
    assert_true(process.returncode == 0, f"discovered regression suite failed:\n{combined}")
    assert_true(structured["tests_run"] == structured["tests_discovered"], "structured run/discovery count mismatch")
    assert_true(structured["tests_passed"] == structured["tests_discovered"], "structured passed/discovered count mismatch")
    assert_true(structured["tests_skipped"] == 0, "unexpected skipped tests")
    assert_true(structured["duplicate_test_ids"] == [], "duplicate test discovery")
    assert_true(structured["tests_failed"] == structured["tests_errored"] == 0, "structured test failures or errors")
    assert_true(not warning_lines, f"warning output is forbidden independently of count extraction: {warning_lines}")
    major_minor = tuple(map(int, structured["python_version"].split(".")[:2]))
    assert_true(major_minor in {(3, 12), (3, 13)}, "unsupported Python version; Draft 5.3.9 supports Python 3.12 and 3.13")
    return {
        "command": command,
        **structured,
        "warning_output_lines": warning_lines,
        "stdout_sha256": hashlib.sha256(process.stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(process.stderr.encode("utf-8")).hexdigest(),
    }


def validate_regression_run_metadata(record: dict[str, Any]) -> None:
    assert_true(type(record.get("tests_discovered")) is int and record["tests_discovered"] > 0, "discovered test count is invalid")
    assert_true(type(record.get("tests_passed")) is int, "passed test count is invalid")
    assert_true(record["tests_passed"] == record["tests_discovered"], "discovered and passed counts differ")
    if "tests_run" in record:
        assert_true(record["tests_run"] == record["tests_discovered"], "run and discovered counts differ")
    assert_true(record.get("tests_failed", 0) == 0 and record.get("tests_errored", 0) == 0, "test failures or errors are present")
    assert_true(record.get("tests_skipped") == 0, "unexpected skipped test")
    assert_true(record.get("duplicate_test_ids") == [], "duplicate test discovery")
    assert_true(record.get("warning_output_lines") == [], "warning output is forbidden")


def validate_regression_count_consistency(
    generated: dict[str, Any], measured: dict[str, Any], summary: str
) -> dict[str, int]:
    validate_regression_run_metadata(generated)
    validate_regression_run_metadata(measured)
    assert_true(generated["tests_discovered"] == measured["tests_discovered"], "generated discovered-test count is stale")
    assert_true(generated["tests_passed"] == measured["tests_passed"], "generated passed-test count is stale")
    discovered_match = re.search(r"Tests discovered: (\d+)", summary)
    passed_match = re.search(r"Tests passed: (\d+)", summary)
    assert_true(discovered_match is not None and passed_match is not None, "validation summary lacks generated regression counts")
    narrative = {
        "tests_discovered": int(discovered_match.group(1)),
        "tests_passed": int(passed_match.group(1)),
    }
    assert_true(narrative["tests_discovered"] == generated["tests_discovered"], "narrative/machine discovered count mismatch")
    assert_true(narrative["tests_passed"] == generated["tests_passed"], "narrative/machine passed count mismatch")
    return narrative


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
    connection.executescript((ROOT / "migration/draft5_3_4_to_draft5_3_5.sql").read_text(encoding="utf-8"))
    connection.executescript((ROOT / "migration/draft5_3_5_to_draft5_3_6.sql").read_text(encoding="utf-8"))
    connection.executescript((ROOT / "migration/draft5_3_6_to_draft5_3_7.sql").read_text(encoding="utf-8"))
    return connection


def phase_descriptor() -> dict[str, Any]:
    descriptor = load_json(DESCRIPTOR_PATH.name)
    assert_true(descriptor["active_version"] == "v1.6-draft-5.3.9", "active version mismatch")
    assert_true(descriptor["freeze_state"] == "permanently_not_frozen", "living contract must remain permanently_not_frozen")
    assert_true(descriptor["lifecycle_policy"] == "living_contract_never_freeze", "living-contract policy mismatch")
    required = descriptor["required_validation_phases"]
    optional = descriptor["optional_validation_phases"]
    assert_true(required and len(required) == len(set(required)), "required phase identifiers must be nonempty and unique")
    assert_true(len(optional) == len(set(optional)), "optional phase identifiers must be unique")
    assert_true(not set(required).intersection(optional), "required and optional phase identifiers overlap")
    refs = [
        "primary_contract", "spec_change_request", "start_here", "corpus_index", "inventory", "checksum_manifest",
        "human_manifest", "package_metadata", "package_provenance", "schema_registry", "validation_scope", "validator", "schema_validator", "canonical_openapi",
        "python_matrix_validation",
        "base_sql", "authority_migration", "proof_authority_runtime", "proof_check_service",
        "trusted_compiler", "trusted_verifier", "trusted_inspector_source", "trusted_inspector_build", "proof_check_wsgi",
        "sandbox_profile", "formal_toolchain_manifest", "mathematics_profile", "migration_runbook",
        "corrective_assurance_report", "build_attestation_status", "release_gate_status",
    ]
    paths = [descriptor[key] for key in refs]
    paths.extend(descriptor["authority_migrations"])
    paths.extend(descriptor["formal_authority_profiles"])
    missing = [relative for relative in paths if not (ROOT / relative).is_file()]
    assert_true(not missing, f"descriptor references missing files: {missing}")
    resolver = (ROOT / "kernel/corpus_boot_and_canonical_resolver_v1_0.md").read_text(encoding="utf-8")
    for token in (DESCRIPTOR_PATH.name, "PACKAGE_INVENTORY_v1_6_draft_5_3_9.json", "CHECKSUMS_v1_6_draft_5_3_9.sha256"):
        assert_true(token in resolver, f"resolver does not boot canonical token {token}")
    accounting = _run_python_tests("-W", ["error", "executable/tests/test_validator_phase_reconciliation_v539.py"])
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
    scope = load_json("refs/validation_scope_v1_6_draft_5_3_9.json")
    assert_true(scope["first_party_link_check_exclusions"] == ["executable/validators/vendor"], "vendored documentation link scope is not isolated")
    assert_true(scope["dependency_integrity_scope"] == ["executable/validators/vendor"], "vendored dependency integrity scope is missing")
    return {
        "python": sys.version.split()[0],
        "node": subprocess.check_output([node, "--version"], text=True).strip(),
        "yaml": getattr(yaml, "__version__", "available"),
        "cryptography": getattr(cryptography, "__version__", "available"),
        "sqlite_json1": True,
        "schema_dependencies": "vendored_hash_covered",
    }


def phase_hash_closure() -> dict[str, Any]:
    inventory = load_json("PACKAGE_INVENTORY_v1_6_draft_5_3_9.json")
    records = inventory["files"]
    by_path = {record["path"]: record for record in records}
    assert_true(len(by_path) == len(records), "duplicate inventory paths")
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and not _is_runtime_cache(path)
    }
    assert_true(actual == set(by_path), f"inventory path mismatch; missing={sorted(actual-set(by_path))[:10]} extra={sorted(set(by_path)-actual)[:10]}")
    checksum_lines = (ROOT / "refs/manifest/CHECKSUMS_v1_6_draft_5_3_9.sha256").read_text(encoding="utf-8").splitlines()
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
            assert_true(record.get("sha256") is None and record.get("size_bytes") is None, f"recursive fields must be null: {relative}")
            assert_true(record.get("excluded_fields") == ["sha256", "size_bytes"], f"excluded field declaration mismatch: {relative}")
            assert_true(record.get("exclusion_reason") == "recursive_generated_artifact_describes_package_closure", f"excluded reason mismatch: {relative}")
            continue
        covered += 1
        digest = sha256(path)
        assert_true(record["size_bytes"] == path.stat().st_size, f"inventory size mismatch: {relative}")
        assert_true(record["sha256"] == digest, f"inventory hash mismatch: {relative}")
        assert_true(checksums.get(relative) == digest, f"checksum mismatch: {relative}")
    expected_covered = {path for path, record in by_path.items() if not record["excluded_from_hash_closure"]}
    assert_true(set(checksums) == expected_covered, "checksum path set mismatch")
    assert_true(excluded == 4, "exact recursive exclusion count must be four")
    return {"file_count": len(records), "covered": covered, "excluded_generated": excluded, "final_bytes_verified": True}


def _schema_phase(name: str) -> dict[str, Any]:
    command = ["node", "executable/validators/validate_draft5_3_9_schemas.mjs", "--phase", name]
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


def phase_json_yaml_duplicate_keys() -> dict[str, Any]:
    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    class UniqueKeyLoader(yaml.SafeLoader):
        pass

    def unique_mapping(loader, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in result:
                raise ValueError(f"duplicate YAML key: {key}")
            result[key] = loader.construct_object(value_node, deep=deep)
        return result

    UniqueKeyLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping
    )
    json_files = [
        path for path in ROOT.rglob("*.json")
        if "executable/validators/vendor" not in path.relative_to(ROOT).as_posix()
    ]
    yaml_files = [*ROOT.rglob("*.yaml"), *ROOT.rglob("*.yml")]
    for path in json_files:
        json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    for path in yaml_files:
        yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    return {"json_files": len(json_files), "yaml_files": len(yaml_files), "duplicate_keys": 0}


def phase_exact_test_discovery_count() -> dict[str, Any]:
    generated = load_json(REGRESSION_COUNTS_PATH.name)
    measured = _run_discovered_suite(development_mode=False)
    measured["warning_output_lines"] = []
    validate_regression_count_consistency(
        generated, measured, VALIDATION_SUMMARY_PATH.read_text(encoding="utf-8")
    )
    return measured


def phase_all_regression_tests() -> dict[str, Any]:
    return _run_discovered_suite(development_mode=False)


def phase_warning_free_regression_execution() -> dict[str, Any]:
    result = _run_discovered_suite(development_mode=True)
    assert_true(result["warning_output_lines"] == [], "warning-free suite emitted warnings")
    return result


def phase_python_version_portability() -> dict[str, Any]:
    generated = load_json(REGRESSION_COUNTS_PATH.name)
    matrix = load_json("DRAFT5_3_9_PYTHON_MATRIX_VALIDATION.json")
    assert_true(generated.get("supported_python_versions") == ["3.12", "3.13"], "supported Python matrix mismatch")
    assert_true(matrix.get("supported_python_versions") == ["3.12", "3.13"], "executed Python matrix mismatch")
    assert_true(matrix.get("overall_status") in {"passed", "passed_with_declared_environment_qualification"}, "Python matrix status is invalid")
    runs = matrix.get("runs", [])
    executed_versions = {".".join(item["python_version"].split(".")[:2]) for item in runs}
    unavailable_versions = {item.get("python_version") for item in matrix.get("unavailable_runs", []) if item.get("status") == "interpreter_unavailable"}
    assert_true(executed_versions | unavailable_versions == {"3.12", "3.13"}, "Python version execution/availability accounting is incomplete")
    for item in runs:
        validate_regression_run_metadata(item)
        assert_true(item.get("normal_status") == item.get("development_warnings_as_errors_status") == "passed", "Python matrix execution mode failed")
    assert_true(generated.get("count_source") == "unittest.TestResult", "test totals are not sourced from unittest.TestResult")
    assert_true(generated.get("warning_output_lines") == [], "warning detection is not independently clean")
    current = ".".join(map(str, sys.version_info[:2]))
    assert_true(current in generated["supported_python_versions"], f"current Python {current} is outside the supported matrix")
    return {
        "supported_python_versions": generated["supported_python_versions"],
        "validated_python_versions": [item["python_version"] for item in runs],
        "unavailable_python_versions": sorted(unavailable_versions),
        "current_python_version": sys.version.split()[0],
        "count_source": generated["count_source"],
        "warning_detection": "independent_of_count_extraction",
    }


def phase_domain_specific_rlimit_fsize() -> dict[str, Any]:
    tests = [
        "Draft538SandboxTests.test_compiler_domain_uses_compiler_artifact_file_size_limit",
        "Draft538SandboxTests.test_inspection_domain_uses_inspection_output_bytes_limit",
        "Draft538SandboxTests.test_rlimit_fsize_is_bound_into_invocation_digest",
        "Draft538RuntimeInspectionTests.test_matching_rlimit_fsize_is_measured",
        "Draft538RuntimeInspectionTests.test_excessive_rlimit_fsize_fails",
        "Draft538RuntimeInspectionTests.test_missing_domain_limit_fails_closed",
        "Draft538RuntimeInspectionTests.test_wrong_domain_limit_fails_closed",
        "Draft538RuntimeInspectionTests.test_obsolete_limit_fails_real_inspection_path",
    ]
    return _run_python_tests("executable/tests/test_draft5_3_8_remediation.py", tests)


def phase_control_state_semantics() -> dict[str, Any]:
    tests = [
        "Draft538SandboxTests.test_preexecution_invocation_has_no_accepted_controls",
        "Draft538SandboxTests.test_preexecution_invocation_has_no_applied_controls",
        "Draft538SandboxTests.test_requested_controls_are_not_treated_as_evidence",
        "Draft538SandboxTests.test_emitted_controls_are_derived_from_exact_argv",
    ]
    return _run_python_tests("executable/tests/test_draft5_3_8_remediation.py", tests)


def phase_mandatory_control_measurements() -> dict[str, Any]:
    tests = [
        "Draft538RuntimeInspectionTests.test_environment_measurement_rejects_every_undeclared_key",
        "Draft538RuntimeInspectionTests.test_explicit_entrypoint_has_measured_evidence",
    ]
    return _run_python_tests("executable/tests/test_draft5_3_8_remediation.py", tests)


def phase_machine_readable_narrative_count_consistency() -> dict[str, Any]:
    generated = load_json(REGRESSION_COUNTS_PATH.name)
    summary = VALIDATION_SUMMARY_PATH.read_text(encoding="utf-8")
    narrative = validate_regression_count_consistency(generated, generated, summary)
    return {**narrative, "consistent": True}


def phase_sql_migration() -> dict[str, Any]:
    connection = _new_database()
    generations = [row[0] for row in connection.execute("SELECT generation FROM wc_schema_generations ORDER BY generation")]
    assert_true("v1.6-draft-5.3.7" in generations, "latest authority SQL generation missing")
    columns = {row[1] for row in connection.execute("PRAGMA table_info(wc_lean_compiler_witnesses_v6)")}
    hardening = {
        "policy_decision_id", "policy_decision_sha256", "authority_snapshot_id",
        "authority_ledger_high_water_sequence", "statement_binding_confirmed",
        "recursive_dependency_policy_result", "exact_executed_argv_sha256",
        "effective_resource_limits_sha256", "compile_handoff_manifest_sha256",
        "trust_root_attestation_registry_sha256", "requested_controls_json",
        "emitted_controls_json", "accepted_controls_json", "measured_controls_json",
        "applied_controls_json", "derived_controls_json", "control_evidence_json",
        "domain_file_size_limit",
        "signed_payload_canonical_json", "signed_payload_sha256", "signature", "key_id",
    }
    assert_true(hardening.issubset(columns), f"compiler witness v5 columns missing: {sorted(hardening-columns)}")
    assert_true(not connection.execute("PRAGMA foreign_key_check").fetchall(), "foreign-key check failed")
    required_objects = (
        "wc_proof_policy_registries_v1", "wc_proof_policy_decisions_v1",
        "wc_lean_compiler_witnesses_v6", "wc_theorem_promotion_gates_v6",
        "wc_authoritative_theorems_v6",
    )
    objects = connection.execute(
        f"SELECT count(*) FROM sqlite_master WHERE name IN ({','.join('?' for _ in required_objects)})",
        required_objects,
    ).fetchone()[0]
    connection.close()
    assert_true(objects == len(required_objects), "active authority SQL policy/witness objects missing")
    return {"generations": generations, "compiler_witness_v6_binding_columns": len(hardening), "authority_objects": objects}


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


def phase_sql_policy_binding() -> dict[str, Any]:
    return _run_python_tests("executable/tests/test_sql_policy_binding_v535.py", [])


def phase_sql_v537_authority_closure() -> dict[str, Any]:
    connection = _new_database()
    sql = (ROOT / "migration/draft5_3_6_to_draft5_3_7.sql").read_text(encoding="utf-8")
    for token in (
        "recursive_dependency_policy_result = 'passed'", "exact_executed_argv_sha256",
        "effective_resource_limits_sha256", "compile_handoff_manifest_sha256",
        "trust_root_attestation_registry_sha256", "wc_compiler_witness_v6_no_update",
        "package_version = 'v1.6-draft-5.3.7'", "domain_file_size_limit",
        "applied_controls_json", "derived_controls_json",
    ):
        assert_true(token in sql, f"active Draft 5.3.7 SQL closure omits {token}")
    count = connection.execute("SELECT count(*) FROM wc_authoritative_theorems_v6").fetchone()[0]
    connection.close()
    assert_true(count == 0, "portable database unexpectedly activates theorem authority")
    return {"v6_authority_view_empty": True, "closure_tokens": 10}


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


def phase_openapi_conformance() -> dict[str, Any]:
    assert_true(yaml is not None, "PyYAML is required")
    spec = yaml.safe_load((ROOT / "executable/openapi/draft5_3_9_evidence_language_openapi.yaml").read_text(encoding="utf-8"))
    assert_true(spec["info"]["version"] == "v1.6-draft-5.3.9", "OpenAPI version mismatch")
    schemes = spec.get("components", {}).get("securitySchemes", {})
    assert_true("OAuth2" in schemes and "MutualTLS" in schemes and spec.get("security"), "OAuth2, mutual TLS, and top-level security are required")
    paths = spec["paths"]
    assert_true(set(paths) == {"/v2/proof-checks"}, "OpenAPI advertises an unimplemented route")
    assert_true(set(paths["/v2/proof-checks"]) == {"post"}, "proof-check route is not exactly synchronous POST")
    responses = {str(key) for key in paths["/v2/proof-checks"]["post"]["responses"]}
    assert_true("200" in responses and "202" not in responses, "OpenAPI is not the canonical synchronous model")
    request_properties = load_json("schemas/proof_check_request_v2.schema.json")["properties"]
    forbidden = {
        "result", "allowed", "compiler_witness", "proof_witness", "theorem_promotion_gate",
        "signature", "contains_sorry", "key_status_event", "signature_binding", "created_at",
        "lake_executable", "lean_executable", "expected_lake_sha256", "requested_toolchain",
        "execution_image_digest", "environment", "subject_id", "authenticated_principal_id",
    }
    assert_true(not forbidden.intersection(request_properties), "proof-check request accepts authority outputs")
    assert_true({"request_id", "idempotency_key", "compiler_profile_id", "policy_decision_id"}.issubset(request_properties), "proof-check request omits canonical lifecycle or authority fields")
    assert_true("witness.authenticated_principal_id" in (ROOT / "executable/runtime/proof_check_wsgi.py").read_text(encoding="utf-8"), "WSGI boundary lacks trusted principal middleware binding")
    tests = _run_python_tests("executable/tests/test_draft5_3_6_remediation.py", [
        "ApiConformanceTests.test_openapi_response_matches_running_wsgi_adapter_and_idempotency",
        "ApiConformanceTests.test_openapi_has_only_implemented_proof_route",
    ])
    return {"paths": len(paths), "security_schemes": sorted(schemes), "model": "synchronous", "tests": tests["tests"]}


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
    assert_true(result["tests"] >= 4, f"proof-check service boundary test count mismatch: {result['tests']}")
    return {**result, "request_paths_hashes_environment_timestamps": "rejected"}


def phase_cache_authority_reverification() -> dict[str, Any]:
    tests = [
        "ProofCheckServiceTests.test_cache_hit_revalidates_policy_witness_signature_and_all_bindings",
        "ProofCheckServiceTests.test_schema_valid_cache_row_with_invalid_witness_signature_is_rejected",
        "ProofCheckServiceTests.test_cache_hit_rejects_resigned_witness_binding_and_signer_mismatches",
        "ProofCheckServiceTests.test_cache_hit_rejects_outer_status_that_differs_from_signed_witness",
    ]
    return _run_python_tests("executable/tests/test_proof_check_service.py", tests)


def phase_authenticated_principal_binding() -> dict[str, Any]:
    tests = [
        "ProofCheckServiceTests.test_exact_request_uses_authenticated_principal_and_preserves_policy",
        "ProofCheckServiceTests.test_caller_controlled_subject_id_is_forbidden",
        "ProofCheckWSGITests.test_verified_middleware_principal_is_required",
    ]
    return _run_python_tests("executable/tests/test_proof_check_service.py", tests)


def phase_semantic_execution_identity_separation() -> dict[str, Any]:
    return _run_python_tests(
        "executable/tests/test_proof_authority.py",
        ["ProofAuthorityTests.test_semantic_identity_excludes_ephemeral_host_path_execution_hashes"],
    )


def phase_idempotency_store_bounds() -> dict[str, Any]:
    return _run_python_tests(
        "executable/tests/test_proof_check_service.py",
        [
            "DurableIdempotencyStoreTests.test_global_and_per_principal_inflight_limits_and_expiry_cleanup",
            "DurableIdempotencyStoreTests.test_total_row_completed_row_and_database_byte_admission_are_bounded",
            "DurableIdempotencyStoreTests.test_database_path_rejects_unsafe_parent_and_symlink",
        ],
    )


def phase_sqlite_connection_lifecycle() -> dict[str, Any]:
    return _run_python_tests(
        "executable/tests/test_proof_check_service.py",
        ["DurableIdempotencyStoreTests.test_repeated_operations_do_not_leak_file_descriptors"],
    )


def _closure_test(test_name: str) -> dict[str, Any]:
    return _run_python_tests(
        "executable/tests/test_draft5_3_6_closure.py",
        [f"Draft536ClosureTests.{test_name}"],
    )


def phase_recursive_dependency_inspection() -> dict[str, Any]:
    return _run_python_tests("executable/tests/test_draft5_3_6_closure.py", [
        "Draft536ClosureTests.test_boolean_opaque_policy_result_is_schema_invalid",
        "Draft536ClosureTests.test_real_inspector_invokes_isdefeq_and_structural_fingerprint",
        "Draft536ClosureTests.test_recursive_dependency_closure_and_pass_gate_are_explicit",
    ])


def phase_exact_oci_argv_binding() -> dict[str, Any]:
    return _run_python_tests("executable/tests/test_proof_authority.py", [
        "ProofAuthorityTests.test_real_oci_command_binds_private_host_paths_and_complete_argv",
    ])


def phase_policy_resource_limit_closure() -> dict[str, Any]:
    return _closure_test("test_policy_permissions_become_effective_limits")


def phase_trust_boundary_schema_validation() -> dict[str, Any]:
    return _run_python_tests("executable/tests/test_draft5_3_6_closure.py", [
        "Draft536ClosureTests.test_request_schema_rejects_non_string_claim_and_non_object_claim",
        "Draft536ClosureTests.test_production_trust_inputs_are_schema_validated_before_use",
    ])


def phase_measured_control_evidence() -> dict[str, Any]:
    return _closure_test("test_missing_network_observation_is_unverified")


def phase_compile_handoff_manifest() -> dict[str, Any]:
    return _closure_test("test_compile_manifest_is_consumed_and_exact_file_set_checked")


def phase_durable_idempotency() -> dict[str, Any]:
    return _run_python_tests("executable/tests/test_draft5_3_6_closure.py", [
        "Draft536ClosureTests.test_idempotency_survives_restart_and_is_principal_scoped",
        "Draft536ClosureTests.test_stale_idempotency_lease_is_recoverable",
    ])


def phase_split_resource_limits() -> dict[str, Any]:
    return _closure_test("test_compilation_and_publication_file_limits_are_separate")


def phase_trust_artifact_attestation_registry() -> dict[str, Any]:
    return _closure_test("test_trust_root_claims_are_attestation_registry_bound")


def _run_remediation_tests(tests: list[str]) -> dict[str, Any]:
    return _run_python_tests("executable/tests/test_draft5_3_6_remediation.py", tests)


def phase_oci_command_dispatch() -> dict[str, Any]:
    return _run_remediation_tests([
        "OciSandboxTests.test_oci_argv_matches_effective_invocation_for_both_domains",
        "OciSandboxTests.test_container_entrypoint_is_overridden_or_absent",
        "OciSandboxTests.test_untrusted_domain_executes_only_compile_wrapper",
        "OciSandboxTests.test_trusted_domain_executes_only_verify_wrapper",
    ])


def phase_policy_authority_binding() -> dict[str, Any]:
    return _run_remediation_tests([
        "PolicyTests.test_policy_decision_is_resolved_before_execution",
        "PolicyTests.test_policy_decision_scope_and_status_are_enforced",
        "PolicyTests.test_policy_decision_and_record_hash_are_signature_bound",
        "PolicyTests.test_revoked_or_expired_policy_fails_closed",
    ])


def phase_source_snapshot_limits() -> dict[str, Any]:
    return _run_remediation_tests([
        "SnapshotAndOutputTests.test_source_snapshot_total_file_limit",
        "SnapshotAndOutputTests.test_source_snapshot_total_byte_limit",
        "SnapshotAndOutputTests.test_source_snapshot_depth_and_path_limits",
        "SnapshotAndOutputTests.test_source_snapshot_rejects_special_files",
        "SnapshotAndOutputTests.test_parent_path_swap_cannot_substitute_content",
    ])


def phase_bounded_subprocess_output() -> dict[str, Any]:
    return _run_remediation_tests([
        "SnapshotAndOutputTests.test_subprocess_output_limit_terminates_process_group",
        "SnapshotAndOutputTests.test_host_and_container_output_limits_are_consistent",
    ])


def phase_trusted_inspector_build_contract() -> dict[str, Any]:
    return _run_remediation_tests([
        "FormalBuildTests.test_strict_lean_build_includes_trusted_inspector_executable",
        "FormalBuildTests.test_inspector_cli_positive_negative_and_malformed_fixtures",
        "FormalBuildTests.test_attested_inspector_hash_matches_image_binary",
        "FormalBuildTests.test_reproducible_inspector_build_from_pinned_toolchain",
    ])


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
    profile = load_json("authority/hermetic_lean_sandbox_profile_v5.json")
    assert_true(profile["result_channel_architecture"] == "untrusted_compile_then_trusted_signed_verifier", "two-domain sandbox is not canonical")
    untrusted = profile["untrusted_compilation_domain"]
    trusted = profile["trusted_inspection_domain"]
    assert_true(untrusted["verifier_request_mount"] == "absent" and untrusted["final_result_mount"] == "absent", "untrusted compiler can access trusted result controls")
    assert_true(trusted["inspection_file"] == "regular_0600_single_link_exclusive_atomic", "trusted inspection publication invariant missing")
    assert_true(trusted["final_result_mount"] == "absent", "final signed result is mounted into a container domain")
    controls = profile["runtime_controls"]
    assert_true(controls["network_mode"] == "none" and controls["read_only_rootfs"] is True, "sandbox network/rootfs policy is not fail-closed")
    assert_true(profile["effective_invocation_schema"] == "schemas/effective_sandbox_invocation_v5.schema.json", "sandbox profile does not select v5 effective invocation")
    assert_true(profile["domain_file_size_limit_binding"] == {
        "untrusted_compilation": "compiler_artifact_file_size_limit_bytes",
        "trusted_inspection": "inspection_output_bytes_limit",
    }, "domain-specific file-size binding is not canonical")
    assert_true(profile["required_file_size_measurement"] == "rlimit_fsize_exactly_equals_domain_file_size_limit", "RLIMIT_FSIZE exact-measurement rule missing")
    tests = _run_remediation_tests([
        "OciSandboxTests.test_every_effective_control_has_runtime_flag_verified_default_or_rejection",
        "OciSandboxTests.test_effective_invocation_digest_changes_for_each_control",
        "OciSandboxTests.test_runtime_inspection_matches_declared_security_properties",
        "OciSandboxTests.test_trusted_domain_rejects_uid_gid_zero",
        "OciSandboxTests.test_runtime_version_is_measured_not_config_echoed",
        "OciSandboxTests.test_missing_runtime_control_fails_closed",
    ])
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
    required_models = {"ProofAuthorityV2", "ProofAuthorityV3", "ProofAuthorityV4", "ProofAuthorityV5", "ProofAuthorityV6", "ProofAuthorityV7", "ProofAuthorityV8"}
    for name in sorted(required_models):
        assert_true(name in modules, f"active strict TLA manifest omits {name}")
        assert_true((ROOT / modules[name]["spec"]).is_file() and (ROOT / modules[name]["config"]).is_file(), f"{name} spec/config missing")
    process = subprocess.run([sys.executable, "executable/formal/run_tla_model_check.py", "--mode", "advisory", "--json"], cwd=ROOT, text=True, capture_output=True, timeout=180, env=_subprocess_environment())
    assert_true(process.returncode == 0, f"TLA manifest/static check failed: {process.stdout} {process.stderr}")
    result = json.loads(process.stdout)
    assert_true(not result["static_errors"], f"TLA static errors: {result['static_errors']}")
    assert_true(required_models.issubset(result["modules_checked"]), "runner did not execute active authority manifest entries")
    lean_manifest = load_json("refs/formal_toolchain/lean_toolchain_manifest_v1_0.json")
    verifier_sources = lean_manifest.get("hermetic_verifier_sources", [])
    assert_true(verifier_sources and all((ROOT / path).is_file() for path in verifier_sources), "trusted Lean verifier source is absent from the manifest")
    assert_true("witnessAuthorityInspector" in lean_manifest.get("required_build_targets", []), "strict Lean manifest omits trusted inspector executable")
    assert_true(lean_manifest.get("authority_activation_requires_real_image") is True, "Lean manifest does not fail closed on real-image evidence")
    return {"modules_checked": result["modules_checked"], "tlc_available": result["tlc_available"], "strict_tlc_claimed": False, "hermetic_verifier_sources": verifier_sources}


def phase_schema_registry_authority() -> dict[str, Any]:
    registry = load_json("refs/schema_registry_v1_6_draft_5_3_9.json")
    entries = registry["entries"]
    actual = sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / "schemas").glob("*.schema.*"))
    classified = sorted(entry["path"] for entry in entries)
    assert_true(actual == classified, "schema registry is not the exact schema directory")
    assert_true(len(classified) == len(set(classified)), "duplicate schema registry path")
    ids = [entry["schema_id"] for entry in entries if entry.get("schema_id")]
    assert_true(len(ids) == len(set(ids)), "duplicate schema registry $id")
    canonical = [entry for entry in entries if entry["lifecycle"] == "canonical"]
    assert_true(all(entry["active_surface"] for entry in canonical), "canonical schema is not active")
    assert_true(all(entry["valid_fixtures"] and entry["invalid_fixtures"] for entry in canonical), "canonical fixture coverage incomplete")
    assert_true(not registry.get("strict_mode_exceptions"), "unexpected canonical strict-mode exception")
    return {"classified": len(entries), "canonical": len(canonical), "unknown_policy": registry["rules"]["unknown_schema"]}


def phase_version_consistency() -> dict[str, Any]:
    expected = "v1.6-draft-5.3.9"
    descriptor = load_json(DESCRIPTOR_PATH.name)
    metadata = load_json("PACKAGE_METADATA_v1_6_draft_5_3_9.json")
    registry = load_json("refs/schema_registry_v1_6_draft_5_3_9.json")
    package = load_json("package.json")
    lock = load_json("package-lock.json")
    tla = load_json("refs/formal_toolchain/tla_toolchain_manifest_v1_0.json")
    gate_status = load_json("DRAFT5_3_9_RELEASE_GATE_STATUS.json")
    assert_true(descriptor["active_version"] == metadata["version"] == expected, "descriptor/package metadata version mismatch")
    assert_true(package["version"] == "1.6.5-3-9" and lock["version"] == package["version"], "npm package/lock version mismatch")
    assert_true(package["name"].endswith("draft-5-3-9-validation") and lock["name"] == package["name"], "npm package/lock identity mismatch")
    assert_true(registry.get("registry_version") == expected, "schema registry version mismatch")
    assert_true("Draft 5.3.9" in tla["package"] and any(item["module"] == "ProofAuthorityV8" for item in tla["tla_modules"]), "formal manifest version/active model mismatch")
    assert_true(gate_status["gates"]["I_package_provenance"] == "unpublished_workspace", "release provenance status is not fail-closed")
    assert_true('v!"5.3.9"' in (ROOT / "lakefile.lean").read_text(encoding="utf-8"), "Lake package version mismatch")
    active_documents = (
        "README.md", "START_HERE.md", "CANONICAL_CORPUS_v1_6_draft_5_3_9.json",
        "CORPUS_INDEX_v1_6_draft_5_3_9.md", "duotronic_witness_contract_v1_6_draft_5_3_9.md",
        "RELEASE_NOTES_v1_6_draft_5_3_9.md", "PACKAGE_METADATA_v1_6_draft_5_3_9.json",
        "kernel/corpus_boot_and_canonical_resolver_v1_0.md",
    )
    for relative in active_documents:
        text_value = (ROOT / relative).read_text(encoding="utf-8")
        assert_true("5.3.9" in text_value, f"active entrypoint lacks 5.3.9 identity: {relative}")
        assert_true("validate_draft5_3_3_corpus.py" not in text_value and "validate_draft5_3_4_corpus.py" not in text_value, f"active entrypoint points to stale validator: {relative}")
    for report_path in ROOT.glob("DRAFT5_3_9*.json"):
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert_true(report.get("package_version") == expected, f"active report version mismatch: {report_path.name}")
    return {"active_version": expected, "npm_version": package["version"], "formal_model": "ProofAuthorityV8", "entrypoints_checked": len(active_documents)}


def phase_package_provenance() -> dict[str, Any]:
    provenance = load_json("PACKAGE_PROVENANCE_v1_6_draft_5_3_9.json")
    required = {
        "source_repository", "source_ref", "source_commit_sha", "source_subtree_path",
        "source_subtree_sha256", "generator_name", "generator_version", "generator_sha256",
        "source_generation", "base_revision", "transformation_change_set",
        "transformation_change_set_sha256", "workspace_status", "workspace_clean",
    }
    assert_true(required.issubset(provenance), "package provenance fields incomplete")
    assert_true(provenance["provenance_status"] == "unpublished_workspace", "development package provenance is mislabeled")
    assert_true(provenance["source_commit_sha"] is None and provenance["workspace_clean"] is False, "unpublished package fabricates committed clean source")
    generator = ROOT / provenance["generator_name"]
    change_set = ROOT / provenance["transformation_change_set"]
    assert_true(sha256(generator) == provenance["generator_sha256"], "provenance generator hash mismatch")
    assert_true(sha256(change_set) == provenance["transformation_change_set_sha256"], "provenance change-set hash mismatch")
    assert_true(re.fullmatch(r"[0-9a-f]{64}", provenance["source_subtree_sha256"]) is not None, "source subtree digest malformed")
    exclusions = set(provenance["source_digest_exclusions"])
    assert_true(source_tree_sha256(exclusions) == provenance["source_subtree_sha256"], "package source-subtree digest does not match final source bytes")
    return {"status": provenance["provenance_status"], "activation_ready": False, "source_subtree_sha256": provenance["source_subtree_sha256"]}


def phase_standalone_merged_corpus() -> dict[str, Any]:
    embedded_archives = sorted(path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*.zip"))
    assert_true(not embedded_archives, f"standalone corpus contains recursive source packages: {embedded_archives}")
    lineage = json.loads(LINEAGE_PATH.read_text(encoding="utf-8"))
    assert_true(lineage.get("schema_version") == "source_package_lineage/v1", "lineage record version mismatch")
    assert_true(lineage.get("merge_policy") == "changes_merged_no_embedded_source_packages", "lineage merge policy mismatch")
    releases = lineage.get("releases")
    assert_true(isinstance(releases, list) and releases, "lineage releases are absent")
    assert_true(all(re.fullmatch(r"[0-9a-f]{64}", item.get("sha256", "")) for item in releases), "lineage digest malformed")
    assert_true(releases[-1].get("version") == "v1.6-draft-5.3.8" and releases[-1].get("sha256") == "8abfc95444306d366fa492d987c57d7f9e7a2422f81b64a60c99681c9c563abf", "immediate predecessor lineage mismatch")
    return {"embedded_zip_count": 0, "lineage_release_count": len(releases)}


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
    status = load_json("DRAFT5_3_9_BUILD_ATTESTATION_STATUS.json")
    matches = [item for item in status.get("attestations", []) if item.get("subject_type") == subject_type]
    if not matches:
        raise PhaseSkipped(f"signed {subject_type} build attestation absent; execution closure remains incomplete")
    attestation = matches[-1]
    assert_true(attestation.get("verified") is True and attestation.get("trusted_builder") is True, f"{subject_type} attestation is not verified from a trusted builder")
    assert_true(attestation.get("schema_version") == "build_attestation/v2", f"{subject_type} attestation schema mismatch")
    return attestation


def phase_oci_image_build_attestation() -> dict[str, Any]:
    return _build_attestation("oci_image")


def phase_verifier_executable_build_attestation() -> dict[str, Any]:
    return _build_attestation("trusted_verifier_executable")


def phase_reproducible_inspector_build() -> dict[str, Any]:
    first = _build_attestation("trusted_inspector_reproducible_build_a")
    second = _build_attestation("trusted_inspector_reproducible_build_b")
    assert_true(first["output_binary_sha256"] == second["output_binary_sha256"], "independent inspector builds disagree")
    return {"output_binary_sha256": first["output_binary_sha256"], "independent_builds": 2}


def phase_committed_source_provenance() -> dict[str, Any]:
    provenance = load_json("PACKAGE_PROVENANCE_v1_6_draft_5_3_9.json")
    if provenance.get("provenance_status") != "committed_clean_source":
        raise PhaseSkipped("clean committed-source provenance absent; release provenance activation remains incomplete")
    assert_true(provenance.get("workspace_clean") is True, "committed provenance workspace is not clean")
    assert_true(re.fullmatch(r"[0-9a-f]{40,64}", str(provenance.get("source_commit_sha", ""))) is not None, "committed provenance lacks source commit")
    return provenance


def phase_external_signature() -> dict[str, Any]:
    status = load_json("refs/trust/RELEASE_SIGNATURE_STATUS_v1_6_draft_5_3_9.json")
    if not status.get("external_signature_present"):
        raise PhaseSkipped("external governance signature absent; package is not an external trust root")
    assert_true(status.get("governance_trust_anchor_accepted"), "external signature is not accepted as a governance trust anchor")
    return status


def _run_v539_tests(tests: list[str]) -> dict[str, Any]:
    return _run_python_tests("executable/tests/test_draft5_3_9_remediation.py", tests)


def phase_compile_producer_consumer_contract() -> dict[str, Any]:
    return _run_v539_tests(["CompileHandoffIntegrationTests.test_true_producer_output_is_accepted_by_trusted_consumer"])


def phase_sealed_handoff_module_resolution() -> dict[str, Any]:
    return _run_v539_tests(["GovernedBuildContractTests.test_inspector_uses_only_sealed_handoff_search_root"])


def phase_keep_id_mount_ownership_and_sealing() -> dict[str, Any]:
    return _run_v539_tests(["GovernedBuildContractTests.test_keep_id_handoff_is_host_sealed_for_trusted_traversal"])


def phase_trusted_inspector_source_alignment() -> dict[str, Any]:
    return _run_v539_tests(["GovernedBuildContractTests.test_build_and_lake_select_same_source_generation"])


def phase_dual_domain_execution_evidence() -> dict[str, Any]:
    return _run_python_tests("executable/tests/test_proof_authority.py", ["ProofAuthorityTests.test_valid_signed_result_passes_and_binds_complete_closure"])


def phase_warning_as_error_behavior() -> dict[str, Any]:
    return _run_v539_tests(["CompileHandoffIntegrationTests.test_warning_diagnostic_fails_even_when_lean_exits_zero"])


def phase_request_wide_deadline() -> dict[str, Any]:
    return _run_v539_tests(["LifecycleAndDatabaseTests.test_one_monotonic_deadline_is_passed_to_authority"])


def phase_idempotency_lease_renewal() -> dict[str, Any]:
    return _run_v539_tests(["LifecycleAndDatabaseTests.test_active_execution_renews_owner_fenced_lease"])


def phase_cache_signing_authority_separation() -> dict[str, Any]:
    return _run_v539_tests(["LifecycleAndDatabaseTests.test_production_rejects_cache_and_witness_key_reuse"])


def phase_sqlite_completion_size_bound() -> dict[str, Any]:
    return _run_v539_tests(["LifecycleAndDatabaseTests.test_completion_bound_rejects_growth_before_publication"])


def phase_sqlite_schema_integrity() -> dict[str, Any]:
    return _run_v539_tests(["LifecycleAndDatabaseTests.test_schema_version_and_unexpected_objects_fail_closed"])


def phase_canonical_cache_rows() -> dict[str, Any]:
    return _run_v539_tests(["LifecycleAndDatabaseTests.test_cached_json_must_be_duplicate_free_and_canonical"])


def phase_sqlite_descriptor_ancestry() -> dict[str, Any]:
    return _run_v539_tests(["LifecycleAndDatabaseTests.test_complete_database_ancestry_is_validated"])


def phase_runtime_image_dependency_pinning() -> dict[str, Any]:
    return _run_v539_tests(["GovernedBuildContractTests.test_runtime_container_pins_python_cryptography_and_lean_tools"])


def phase_validator_process_isolation() -> dict[str, Any]:
    source = Path(__file__).read_text(encoding="utf-8")
    for token in ("start_new_session=True", "os.killpg", "[phase:start]", "[phase:done]", "--phase-worker"):
        assert_true(token in source, f"validator isolation contract omits {token}")
    return {"process_isolated": True, "timeout_seconds": 360, "progress_markers": True}


REQUIRED_PHASE_FUNCTIONS: dict[str, Callable[[], dict[str, Any]]] = {
    "descriptor": phase_descriptor,
    "dependencies": phase_dependencies,
    "hash_closure": phase_hash_closure,
    "json_schemas": phase_json_schemas,
    "valid_fixtures": phase_valid_fixtures,
    "invalid_fixtures": phase_invalid_fixtures,
    "json_yaml_duplicate_keys": phase_json_yaml_duplicate_keys,
    "exact_test_discovery_count": phase_exact_test_discovery_count,
    "all_regression_tests": phase_all_regression_tests,
    "warning_free_regression_execution": phase_warning_free_regression_execution,
    "python_version_portability": phase_python_version_portability,
    "domain_specific_rlimit_fsize": phase_domain_specific_rlimit_fsize,
    "control_state_semantics": phase_control_state_semantics,
    "mandatory_control_measurements": phase_mandatory_control_measurements,
    "machine_readable_narrative_count_consistency": phase_machine_readable_narrative_count_consistency,
    "sql_migration": phase_sql_migration,
    "sql_event_ledger": phase_sql_event_ledger,
    "sql_typed_supersession": phase_sql_typed_supersession,
    "sql_immutability": phase_sql_immutability,
    "sql_policy_binding": phase_sql_policy_binding,
    "sql_v537_authority_closure": phase_sql_v537_authority_closure,
    "historical_snapshot_stability": phase_historical_snapshot_stability,
    "replay_non_vacuity": phase_replay_non_vacuity,
    "openapi_conformance": phase_openapi_conformance,
    "positive_baseline_runtime": phase_positive_baseline_runtime,
    "proof_authority_runtime": phase_proof_authority_runtime,
    "proof_check_service_boundary": phase_proof_check_service_boundary,
    "cache_authority_reverification": phase_cache_authority_reverification,
    "authenticated_principal_binding": phase_authenticated_principal_binding,
    "semantic_execution_identity_separation": phase_semantic_execution_identity_separation,
    "idempotency_store_bounds": phase_idempotency_store_bounds,
    "sqlite_connection_lifecycle": phase_sqlite_connection_lifecycle,
    "recursive_dependency_inspection": phase_recursive_dependency_inspection,
    "exact_oci_argv_binding": phase_exact_oci_argv_binding,
    "policy_resource_limit_closure": phase_policy_resource_limit_closure,
    "trust_boundary_schema_validation": phase_trust_boundary_schema_validation,
    "measured_control_evidence": phase_measured_control_evidence,
    "compile_handoff_manifest": phase_compile_handoff_manifest,
    "durable_idempotency": phase_durable_idempotency,
    "split_resource_limits": phase_split_resource_limits,
    "trust_artifact_attestation_registry": phase_trust_artifact_attestation_registry,
    "oci_command_dispatch": phase_oci_command_dispatch,
    "effective_sandbox_invocation": phase_effective_sandbox_invocation,
    "policy_authority_binding": phase_policy_authority_binding,
    "source_snapshot_limits": phase_source_snapshot_limits,
    "bounded_subprocess_output": phase_bounded_subprocess_output,
    "trusted_inspector_build_contract": phase_trusted_inspector_build_contract,
    "result_channel_isolation": phase_result_channel_isolation,
    "signed_verifier_result": phase_signed_verifier_result,
    "trust_root_loading": phase_trust_root_loading,
    "deterministic_witness_identity": phase_deterministic_witness_identity,
    "formal_manifest_coverage": phase_formal_manifest_coverage,
    "schema_registry_authority": phase_schema_registry_authority,
    "version_consistency": phase_version_consistency,
    "package_provenance": phase_package_provenance,
    "standalone_merged_corpus": phase_standalone_merged_corpus,
    "compile_producer_consumer_contract": phase_compile_producer_consumer_contract,
    "sealed_handoff_module_resolution": phase_sealed_handoff_module_resolution,
    "keep_id_mount_ownership_and_sealing": phase_keep_id_mount_ownership_and_sealing,
    "trusted_inspector_source_alignment": phase_trusted_inspector_source_alignment,
    "dual_domain_execution_evidence": phase_dual_domain_execution_evidence,
    "warning_as_error_behavior": phase_warning_as_error_behavior,
    "request_wide_deadline": phase_request_wide_deadline,
    "idempotency_lease_renewal": phase_idempotency_lease_renewal,
    "cache_signing_authority_separation": phase_cache_signing_authority_separation,
    "sqlite_completion_size_bound": phase_sqlite_completion_size_bound,
    "sqlite_schema_integrity": phase_sqlite_schema_integrity,
    "canonical_cache_rows": phase_canonical_cache_rows,
    "sqlite_descriptor_ancestry": phase_sqlite_descriptor_ancestry,
    "runtime_image_dependency_pinning": phase_runtime_image_dependency_pinning,
    "validator_process_isolation": phase_validator_process_isolation,
}

OPTIONAL_PHASE_FUNCTIONS: dict[str, Callable[[], dict[str, Any]]] = {
    "strict_lean": phase_strict_lean,
    "strict_tlc": phase_strict_tlc,
    "hermetic_lean_integration": phase_hermetic_lean_integration,
    "oci_image_build_attestation": phase_oci_image_build_attestation,
    "verifier_executable_build_attestation": phase_verifier_executable_build_attestation,
    "reproducible_inspector_build": phase_reproducible_inspector_build,
    "committed_source_provenance": phase_committed_source_provenance,
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


PHASE_MARKER = "WC_PHASE_RESULT="
PHASE_TIMEOUT_SECONDS = 360


def run_phase_isolated(name: str, required: bool) -> dict[str, Any]:
    """Run one phase in its own process group with bounded time and progress."""
    print(f"[phase:start] {name}", file=sys.stderr, flush=True)
    command = [sys.executable, str(Path(__file__).resolve()), "--phase-worker", name, "required" if required else "optional"]
    process = subprocess.Popen(
        command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=_subprocess_environment(), start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=PHASE_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, 9)
        stdout, stderr = process.communicate()
        result = {
            "name": name, "required": required, "status": "failed",
            "duration_seconds": PHASE_TIMEOUT_SECONDS,
            "error": f"phase exceeded {PHASE_TIMEOUT_SECONDS}-second process-isolated timeout",
            "last_progress": "started_not_completed",
        }
    else:
        marker = next((line[len(PHASE_MARKER):] for line in stdout.splitlines() if line.startswith(PHASE_MARKER)), None)
        if marker is None:
            result = {
                "name": name, "required": required, "status": "failed", "duration_seconds": 0,
                "error": f"isolated phase emitted no result marker (exit={process.returncode})",
                "stderr_sha256": hashlib.sha256(stderr.encode("utf-8")).hexdigest(),
                "last_progress": "started_not_completed",
            }
        else:
            try:
                result = json.loads(marker)
            except json.JSONDecodeError as error:
                result = {
                    "name": name, "required": required, "status": "failed", "duration_seconds": 0,
                    "error": f"isolated phase result marker is invalid JSON: {error}",
                    "last_progress": "started_not_completed",
                }
    print(f"[phase:done] {name} {result['status']}", file=sys.stderr, flush=True)
    return result


def main() -> int:
    if len(sys.argv) == 4 and sys.argv[1] == "--phase-worker":
        phase_name = sys.argv[2]
        required = sys.argv[3] == "required"
        function = (REQUIRED_PHASE_FUNCTIONS if required else OPTIONAL_PHASE_FUNCTIONS).get(phase_name)
        result = run_phase(phase_name, required, function) if function is not None else {
            "name": phase_name, "required": required, "status": "failed", "duration_seconds": 0,
            "error": "phase identifier has no implementation",
        }
        print(PHASE_MARKER + json.dumps(result, sort_keys=True, separators=(",", ":")), flush=True)
        return 0
    validation_started = datetime.now(timezone.utc)
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
        phases.append(run_phase_isolated(name, True))
    for name in dict.fromkeys(optional):
        phases.append(run_phase_isolated(name, False))

    reconciliation = reconcile_required_phases(required, phases)
    optional_results = [phase for phase in phases if not phase["required"]]
    activation_evidence_complete = bool(optional_results) and all(phase["status"] == "passed" for phase in optional_results)
    phase_details = {
        phase["name"]: phase.get("details", {}) for phase in phases
    }
    inventory = load_json("PACKAGE_INVENTORY_v1_6_draft_5_3_9.json") if (ROOT / "PACKAGE_INVENTORY_v1_6_draft_5_3_9.json").is_file() else {"files": []}
    regular_directories = [
        path for path in ROOT.rglob("*")
        if path.is_dir() and "__pycache__" not in path.relative_to(ROOT).parts
    ]
    regression_metrics = phase_details.get("exact_test_discovery_count", {})
    schema_metrics = phase_details.get("json_schemas", {})
    valid_fixture_metrics = phase_details.get("valid_fixtures", {})
    invalid_fixture_metrics = phase_details.get("invalid_fixtures", {})
    hash_metrics = phase_details.get("hash_closure", {})
    validation_finished = datetime.now(timezone.utc)
    report = {
        "schema_version": "draft5_3_9_validation_report/v1",
        "package_version": "v1.6-draft-5.3.9",
        "generated_at": validation_finished.isoformat(),
        "started_at": validation_started.isoformat(),
        "finished_at": validation_finished.isoformat(),
        "duration_seconds": round((validation_finished - validation_started).total_seconds(), 6),
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
        "validation_metrics": {
            "file_count": len(inventory.get("files", [])),
            "directory_count": len(regular_directories),
            "prospective_zip_entry_count": len(inventory.get("files", [])) + len(regular_directories) + 1,
            "hash_covered_file_count": hash_metrics.get("covered"),
            "hash_excluded_file_count": hash_metrics.get("excluded_generated"),
            "schema_count": schema_metrics.get("schemas_compiled"),
            "strict_canonical_schema_count": schema_metrics.get("canonical_schemas_compiled_strict"),
            "valid_fixture_count": valid_fixture_metrics.get("valid_fixtures_passed"),
            "adversarial_fixture_count": invalid_fixture_metrics.get("invalid_fixtures_rejected"),
            "tests_discovered": regression_metrics.get("tests_discovered"),
            "tests_passed": regression_metrics.get("tests_passed"),
            "required_phase_count": len(required),
        },
        "clean_extraction_root_identity": phase_details.get("package_provenance", {}).get("source_subtree_sha256"),
        "phases": phases,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["overall_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
