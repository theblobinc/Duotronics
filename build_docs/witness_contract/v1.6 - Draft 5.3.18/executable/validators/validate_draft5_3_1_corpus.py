#!/usr/bin/env python3
"""Fail-closed validator for the canonical Draft 5.3.1 development corpus."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import traceback
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

try:
    import cryptography
except Exception as error:
    cryptography = None
    CRYPTOGRAPHY_IMPORT_ERROR = error
else:
    CRYPTOGRAPHY_IMPORT_ERROR = None

try:
    import yaml
except Exception as error:  # required; recorded as a failed dependency phase
    yaml = None
    YAML_IMPORT_ERROR = error
else:
    YAML_IMPORT_ERROR = None

ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "DRAFT5_3_1_VALIDATION_REPORT.json"
EXPECTED_HISTORY_SHAKE256_512 = "437395d28c452f0a20937eaf562020afae2214edf01a8df2fe6dadd062201c22"


def shake256_512(path: Path) -> str:
    return hashlib.shake_256(path.read_bytes()).hexdigest(64)


def load_json(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def phase_descriptor() -> dict[str, Any]:
    descriptor = load_json("CANONICAL_CORPUS_v1_6_draft_5_3_1.json")
    assert_true(descriptor["active_version"] == "v1.6-draft-5.3.1", "active version mismatch")
    assert_true(descriptor["freeze_state"] == "not_frozen", "this build must remain not_frozen")
    refs = [
        "primary_contract", "start_here", "corpus_index", "inventory", "checksum_manifest",
        "human_manifest", "schema_registry", "validator", "canonical_openapi", "base_sql",
        "authority_migration", "formal_authority_profile", "mathematics_profile"
    ]
    missing = [descriptor[key] for key in refs if not (ROOT / descriptor[key]).is_file()]
    assert_true(not missing, f"descriptor references missing files: {missing}")
    resolver = (ROOT / "kernel/corpus_boot_and_canonical_resolver_v1_0.md").read_text(encoding="utf-8")
    for token in ("CANONICAL_CORPUS_v1_6_draft_5_3_1.json", "PACKAGE_INVENTORY_v1_6_draft_5_3_1.json", "CHECKSUMS_v1_6_draft_5_3_1.shake256_512"):
        assert_true(token in resolver, f"resolver does not boot canonical token {token}")
    return {"active_version": descriptor["active_version"], "required_phases": descriptor["required_validation_phases"]}


def phase_dependencies() -> dict[str, Any]:
    assert_true(yaml is not None, f"PyYAML unavailable: {YAML_IMPORT_ERROR}")
    assert_true(cryptography is not None, f"cryptography unavailable: {CRYPTOGRAPHY_IMPORT_ERROR}")
    node = shutil.which("node")
    assert_true(node is not None, "node is unavailable")
    for package in ("ajv", "ajv-formats"):
        assert_true((ROOT / "node_modules" / package).is_dir(), f"required validator dependency {package} is unavailable; run npm ci")
    con = sqlite3.connect(":memory:")
    try:
        assert_true(con.execute("SELECT json_array_length('[1,2]')").fetchone()[0] == 2, "SQLite JSON1 unavailable")
    finally:
        con.close()
    return {"python": sys.version.split()[0], "node": subprocess.check_output([node, "--version"], text=True).strip(), "yaml": getattr(yaml, "__version__", "available"), "cryptography": getattr(cryptography, "__version__", "available"), "sqlite_json1": True}


def phase_hash_closure() -> dict[str, Any]:
    inventory = load_json("PACKAGE_INVENTORY_v1_6_draft_5_3_1.json")
    records = inventory["files"]
    by_path = {record["path"]: record for record in records}
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and "node_modules" not in path.relative_to(ROOT).parts
    }
    assert_true(actual == set(by_path), f"inventory path mismatch; missing={sorted(actual-set(by_path))[:10]} extra={sorted(set(by_path)-actual)[:10]}")
    checksum_lines = (ROOT / "refs/manifest/CHECKSUMS_v1_6_draft_5_3_1.shake256_512").read_text(encoding="utf-8").splitlines()
    checksums = {}
    for line in checksum_lines:
        if not line.strip() or line.startswith("#"):
            continue
        digest, relative = line.split("  ", 1)
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
        assert_true(record["size_bytes"] == path.stat().st_size, f"inventory size mismatch: {relative}")
        digest = shake256_512(path)
        assert_true(record["shake256_512"] == digest, f"inventory hash mismatch: {relative}")
        assert_true(checksums.get(relative) == digest, f"checksum manifest mismatch: {relative}")
    assert_true(set(checksums) == {p for p, r in by_path.items() if not r["excluded_from_hash_closure"]}, "checksum path set mismatch")
    return {"file_count": len(records), "covered": covered, "excluded_generated": excluded}


def phase_schemas_and_fixtures() -> dict[str, Any]:
    command = ["node", "executable/validators/validate_draft5_3_1_schemas.mjs"]
    process = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=120)
    assert_true(process.returncode == 0, f"AJV validation failed:\n{process.stdout}\n{process.stderr}")
    result = json.loads(process.stdout)
    assert_true(result["status"] == "passed", "AJV phase did not report passed")
    return result


def phase_openapi_security() -> dict[str, Any]:
    assert_true(yaml is not None, "PyYAML is required")
    path = ROOT / "executable/openapi/draft5_3_1_evidence_language_openapi.yaml"
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))
    schemes = spec.get("components", {}).get("securitySchemes", {})
    assert_true("OAuth2" in schemes and "MutualTLS" in schemes, "OAuth2 and mutual TLS are required")
    assert_true(spec.get("security"), "top-level security is required")
    paths = spec["paths"]
    for authority_path in ("/v2/compiler-witnesses/{witness_id}", "/v2/proof-witnesses/{witness_id}", "/v2/theorem-promotion-gates/{gate_id}"):
        assert_true("get" in paths[authority_path], f"{authority_path} must be readable")
        assert_true("post" not in paths[authority_path] and "put" not in paths[authority_path] and "patch" not in paths[authority_path], f"{authority_path} exposes client authority writes")
    request_properties = spec["components"]["schemas"]["ProofCheckRequest"]["properties"]
    forbidden = {"result", "allowed", "compiler_witness", "proof_witness", "theorem_promotion_gate", "signature", "contains_sorry"}
    assert_true(not forbidden.intersection(request_properties), "proof-check request accepts authority outputs")
    assert_true("post" in paths["/v2/proof-checks"], "controlled proof-check endpoint missing")
    return {"paths": len(paths), "security_schemes": sorted(schemes), "authority_outputs_read_only": True}


def _expect_integrity_error(action: Callable[[], Any], label: str) -> None:
    try:
        action()
    except sqlite3.IntegrityError:
        return
    raise AssertionError(f"SQL adversarial action unexpectedly succeeded: {label}")


def _insert_happy_authority_chain(con: sqlite3.Connection) -> dict[str, str]:
    a, b, c, d, e, f = (ch * 128 for ch in "abcdef")
    one, two = "1" * 128, "2" * 128
    sig_a, sig_b = "A" * 43, "B" * 43
    now = "2026-07-31T12:00:00Z"
    con.execute("INSERT INTO wc_claims_v2 VALUES (?,?,?,?,?,?,?,?,?)", ("claim:proof", "evidence_claim/v2", "proof_claim", '{"statement":"P"}', a, "theorem P", b, "principal:hugh", now))
    con.execute("INSERT INTO wc_policy_decisions_v2 VALUES (?,?,?,?,?,?,?,?)", ("policy:allow", "policy_decision/v2", "claim:proof", "allow", "theorem_promotion", "principal:governance", "approved for strict check", now))
    con.execute("INSERT INTO wc_verifier_principals_v2 VALUES (?,?,?,?,?,?,?,?,?)", ("verifier:1", "verifier_principal/v2", "key:1", "ML-DSA-87", f, "active", now, None, now))
    con.execute("""INSERT INTO wc_lean_compiler_witnesses_v2 (
      lean_compiler_witness_id,schema_version,claim_id,claim_content_shake256_512,theorem_statement_shake256_512,
      proof_artifact_shake256_512,source_tree_shake256_512,lakefile_shake256_512,build_output_shake256_512,toolchain,command_json,
      execution_mode,result,contains_sorry,contains_admit,unapproved_axiom_count,theorem_name,theorem_status,
      verifier_principal_id,key_id,signature_algorithm,signed_payload_shake256_512,signature,created_at
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
      "lean:valid", "lean_compiler_witness/v2", "claim:proof", a, b, c, d, e, f,
      "leanprover/lean4:v4.29.1", '["lake","build"]', "strict", "passed", 0, 0, 0,
      "promotion_sound", "proved", "verifier:1", "key:1", "ML-DSA-87", one, sig_a, now))
    con.execute("""INSERT INTO wc_proof_witnesses_v2 (
      proof_witness_id,schema_version,claim_id,claim_content_shake256_512,theorem_statement_shake256_512,
      proof_artifact_shake256_512,lean_compiler_witness_id,theorem_name,theorem_status,policy_decision_id,
      verifier_principal_id,signed_payload_shake256_512,signature,created_at
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
      "proof:valid", "proof_witness/v2", "claim:proof", a, b, c, "lean:valid",
      "promotion_sound", "proved", "policy:allow", "verifier:1", two, sig_b, now))
    con.execute("INSERT INTO wc_non_collapse_transitions_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
      "nc:valid", "non_collapse_transition/v2", "claim:proof", "conjectural", "theorem", "proof_upgrade",
      "allowed", None, "proof:valid", "policy:allow", "strict proof upgrade", now))
    con.execute("INSERT INTO wc_claim_status_events_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
      "status:valid", "claim_status_event/v2", "claim:proof", "conjecture", "theorem", "prove", 1,
      "policy:allow", "proof:valid", "lean:valid", "nc:valid", now))
    con.execute("INSERT INTO wc_theorem_promotion_gates_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
      "gate:valid", "theorem_promotion_gate/v2", "claim:proof", a, b, "status:valid", "proof:valid",
      "lean:valid", "nc:valid", "policy:allow", "verifier:1", 1, None, now))
    return {"claim_hash": a, "theorem_hash": b, "artifact_hash": c, "now": now}


def phase_sql_authority() -> dict[str, Any]:
    con = sqlite3.connect(":memory:", isolation_level=None)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript((ROOT / "executable/sql/draft5_2_schema_additions.sql").read_text(encoding="utf-8"))
    con.executescript((ROOT / "migration/draft5_2_2_to_draft5_3_1.sql").read_text(encoding="utf-8"))
    assert_true(con.execute("SELECT generation FROM wc_schema_generations").fetchone()[0] == "v1.6-draft-5.3.1", "migration generation missing")
    values = _insert_happy_authority_chain(con)
    assert_true(con.execute("SELECT count(*) FROM wc_authoritative_theorems_v2").fetchone()[0] == 1, "happy theorem chain not authoritative")

    _expect_integrity_error(lambda: con.execute("UPDATE wc_lean_compiler_witnesses_v2 SET result='failed' WHERE lean_compiler_witness_id='lean:valid'"), "mutate compiler witness")
    _expect_integrity_error(lambda: con.execute("DELETE FROM wc_theorem_promotion_gates_v2 WHERE theorem_promotion_gate_id='gate:valid'"), "delete gate")
    _expect_integrity_error(lambda: con.execute("""INSERT INTO wc_theorem_promotion_gates_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        "gate:badhash", "theorem_promotion_gate/v2", "claim:proof", "9"* 128, values["theorem_hash"], "status:valid",
        "proof:valid", "lean:valid", "nc:valid", "policy:allow", "verifier:1", 1, None, values["now"])), "gate with wrong claim hash")

    con.execute("INSERT INTO wc_non_collapse_transitions_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
      "nc:denied", "non_collapse_transition/v2", "claim:proof", "conjectural", "theorem", "proof_upgrade",
      "denied", None, "proof:valid", "policy:allow", "denied path", values["now"]))
    _expect_integrity_error(lambda: con.execute("INSERT INTO wc_theorem_promotion_gates_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
      "gate:denied-nc", "theorem_promotion_gate/v2", "claim:proof", values["claim_hash"], values["theorem_hash"],
      "status:valid", "proof:valid", "lean:valid", "nc:denied", "policy:allow", "verifier:1", 1, None, values["now"])), "gate with denied/unrelated non-collapse path")

    _expect_integrity_error(lambda: con.execute("INSERT INTO wc_non_collapse_transitions_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
      "nc:identity-collapse", "non_collapse_transition/v2", "claim:proof", "zero", "absence", "identity",
      "allowed", None, None, "policy:allow", "forbidden collapse", values["now"])), "zero-to-absence identity collapse")

    con.execute("INSERT INTO wc_replay_manifests_v2 VALUES (?,?,?,?,?,?,?,?)", (
      "manifest:ok", "replay_assumption_manifest/v2", "deep_time_replay",
      '[{"assumption_id":"a1","required_for_pass":true,"status":"satisfied"}]', '["a1"]', "block", "3"* 128, values["now"]))
    con.execute("INSERT INTO wc_verification_grammars_v2 VALUES (?,?,?,?,?)", (
      "grammar:ok", "verification_grammar/v2", '[{"instruction_id":"i1"},{"instruction_id":"i2"}]', "4"* 128, values["now"]))
    con.execute("INSERT INTO wc_verification_results_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
      "result:ok", "verification_result/v2", "grammar:ok", "4"* 128, "manifest:ok", "3"* 128, "artifact:1", "pass",
      '[{"instruction_id":"i1","status":"pass"},{"instruction_id":"i2","status":"pass"}]', '["a1"]', "verifier:1", values["now"]))
    _expect_integrity_error(lambda: con.execute("INSERT INTO wc_verification_results_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
      "result:failed-step", "verification_result/v2", "grammar:ok", "4"* 128, "manifest:ok", "3"* 128, "artifact:2", "pass",
      '[{"instruction_id":"i1","status":"fail"},{"instruction_id":"i2","status":"pass"}]', '["a1"]', "verifier:1", values["now"])), "pass with failed instruction")

    con.execute("INSERT INTO wc_replay_manifests_v2 VALUES (?,?,?,?,?,?,?,?)", (
      "manifest:unsatisfied", "replay_assumption_manifest/v2", "deep_time_replay",
      '[{"assumption_id":"a2","required_for_pass":true,"status":"unknown"}]', '["a2"]', "block", "5"* 128, values["now"]))
    _expect_integrity_error(lambda: con.execute("INSERT INTO wc_verification_results_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
      "result:unsatisfied", "verification_result/v2", "grammar:ok", "4"* 128, "manifest:unsatisfied", "5"* 128, "artifact:3", "pass",
      '[{"instruction_id":"i1","status":"pass"},{"instruction_id":"i2","status":"pass"}]', '["a2"]', "verifier:1", values["now"])), "pass with unsatisfied assumption")
    assert_true(not con.execute("PRAGMA foreign_key_check").fetchall(), "foreign key check failed")
    tables = con.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name LIKE 'wc_%'").fetchone()[0]
    con.close()
    return {"v2_tables": tables, "happy_gate": True, "adversarial_gate_cases_rejected": 4, "immutability_cases_rejected": 2, "replay_non_vacuity_cases_rejected": 2}


def phase_positive_baseline_runtime() -> dict[str, Any]:
    process = subprocess.run([sys.executable, "executable/tests/test_positive_baseline.py"], cwd=ROOT, text=True, capture_output=True, timeout=120)
    assert_true(process.returncode == 0, f"positive-baseline tests failed:\n{process.stdout}\n{process.stderr}")
    return {"tests": 8, "stdout": process.stdout.strip(), "stderr": process.stderr.strip()}


def phase_proof_signature_runtime() -> dict[str, Any]:
    process = subprocess.run([sys.executable, "executable/tests/test_proof_authority.py"], cwd=ROOT, text=True, capture_output=True, timeout=120)
    assert_true(process.returncode == 0, f"proof-authority signature tests failed:\n{process.stdout}\n{process.stderr}")
    return {"tests": 3, "stdout": process.stdout.strip(), "stderr": process.stderr.strip(), "algorithm": "ML-DSA-87"}


def phase_historical_package() -> dict[str, Any]:
    archive = ROOT / "history/source_packages/v1.6 - Draft 5.2.2.zip"
    assert_true(shake256_512(archive) == EXPECTED_HISTORY_SHAKE256_512, "retained Draft 5.2.2 archive hash mismatch")
    with zipfile.ZipFile(archive) as package:
        bad = package.testzip()
        names = package.namelist()
    assert_true(bad is None, f"retained Draft 5.2.2 archive corrupt at {bad}")
    assert_true(len([name for name in names if not name.endswith('/')]) == 492, "retained archive does not contain 492 files")
    return {"shake256_512": EXPECTED_HISTORY_SHAKE256_512, "file_count": 492, "zip_integrity": "passed"}


def phase_formal_advisory() -> dict[str, Any]:
    lean = subprocess.run([sys.executable, "executable/formal/run_lean_build.py", "--mode", "advisory", "--json"], cwd=ROOT, text=True, capture_output=True, timeout=120)
    assert_true(lean.returncode == 0, f"Lean advisory runner failed: {lean.stdout} {lean.stderr}")
    lean_result = json.loads(lean.stdout)
    assert_true(not lean_result.get("forbidden_markers"), "Lean source has forbidden markers")
    assert_true(not lean_result.get("unapproved_axiom_files"), "Lean source has unapproved axioms")
    tla_text = (ROOT / "formal/draft5_3_1/ProofAuthorityV2.tla").read_text(encoding="utf-8")
    for invariant in ("GateRequiresBoundEvidence", "TheoremRequiresGate", "GateIsAppendOnly"):
        assert_true(invariant in tla_text, f"TLA model missing {invariant}")
    return {"lean_advisory_status": lean_result.get("status"), "strict_lean_executed": lean_result.get("lake_available", False), "tla_static_profile": "present", "strict_tlc_executed": False, "release_authority": False}


def run_phase(name: str, required: bool, function: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        details = function()
        return {"name": name, "required": required, "status": "passed", "details": details}
    except Exception as error:
        return {"name": name, "required": required, "status": "failed", "error": str(error), "traceback": traceback.format_exc()}


def main() -> int:
    phases = [
        run_phase("descriptor", True, phase_descriptor),
        run_phase("dependencies", True, phase_dependencies),
        run_phase("hash_closure", True, phase_hash_closure),
        run_phase("json_schemas_valid_fixtures_invalid_fixtures", True, phase_schemas_and_fixtures),
        run_phase("openapi_security", True, phase_openapi_security),
        run_phase("sql_migration_gate_adversarial_immutability_replay_non_vacuity", True, phase_sql_authority),
        run_phase("positive_baseline_runtime", True, phase_positive_baseline_runtime),
        run_phase("proof_signature_runtime", True, phase_proof_signature_runtime),
        run_phase("historical_package_integrity", True, phase_historical_package),
        run_phase("formal_advisory", False, phase_formal_advisory),
    ]
    failed_required = sum(1 for phase in phases if phase["required"] and phase["status"] != "passed")
    failed_optional = sum(1 for phase in phases if not phase["required"] and phase["status"] == "failed")
    report = {
        "schema_version": "draft5_3_1_validation_report/v1",
        "package_version": "v1.6-draft-5.3.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": "passed" if failed_required == 0 else "failed",
        "freeze_state": "not_frozen",
        "required_failed": failed_required,
        "required_skipped": 0,
        "optional_failed": failed_optional,
        "strict_release_evidence_complete": False,
        "phases": phases,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if failed_required == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
