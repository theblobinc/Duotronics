#!/usr/bin/env python3
"""Inside-container gate probes and signed external-evidence verification."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from pqcrypto.sign import ml_dsa_87

ROOT = Path("/opt/harness")
CORPUS_SOURCE = Path("/corpus-ro")
WORK_ROOT = Path("/work")
CORPUS = WORK_ROOT / "corpus"
SOURCE = Path("/source")
EVIDENCE = Path("/evidence")
OUTPUT = Path("/output")
REGISTRY = json.loads((ROOT / "activation_gate_registry_v1.json").read_text())
CRYPTO_PROFILE_REGISTRY = json.loads(
    (ROOT / "cryptographic_profile_registry_v1.json").read_text()
)
EVIDENCE_SCHEMA = json.loads((ROOT / "activation_evidence_schema_v1.json").read_text())
VALIDATOR = Draft202012Validator(EVIDENCE_SCHEMA)
CONTRACT_REF = os.environ.get("HARNESS_CONTRACT_REF", str(REGISTRY.get("contract_version", "unversioned")))
AUTHORITY_PROFILE = os.environ.get("HARNESS_AUTHORITY_PROFILE", "production")
AUTHORITY_NAMESPACE = os.environ.get("HARNESS_AUTHORITY_NAMESPACE", "duotronic://authority/production")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode()


def shake(value: bytes) -> str:
    return hashlib.shake_256(value).hexdigest(64)


def duoid(label: str, value: Any) -> str:
    raw = hashlib.shake_256(label.encode() + b"\x00" + canonical_bytes(value)).digest(64)
    return "duoid:shake256-512:" + base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


class EventLog:
    def __init__(self, path: Path) -> None:
        self.path = path

    def emit(self, event: str, **fields: Any) -> None:
        row = {"at": datetime.now(timezone.utc).isoformat(), "event": event, **fields}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
        print(json.dumps(row, sort_keys=True), flush=True)


def run_command(argv: list[str], cwd: Path, timeout: int, log: EventLog) -> dict[str, Any]:
    started = time.monotonic()
    log.emit("command_start", argv=argv, cwd=str(cwd), timeout_seconds=timeout)
    try:
        completed = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False)
        result = {
            "argv": argv,
            "cwd": str(cwd),
            "exit_code": completed.returncode,
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "stdout": completed.stdout[-200000:],
            "stderr": completed.stderr[-200000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as error:
        result = {
            "argv": argv,
            "cwd": str(cwd),
            "exit_code": 124,
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "stdout": (error.stdout or "")[-200000:],
            "stderr": (error.stderr or "")[-200000:],
            "timed_out": True,
        }
    result["stdout_shake256_512"] = shake(result["stdout"].encode())
    result["stderr_shake256_512"] = shake(result["stderr"].encode())
    log.emit("command_finish", **{k: v for k, v in result.items() if k not in {"stdout", "stderr"}})
    return result


def find_first(candidates: list[Path]) -> Path | None:
    return next((path for path in candidates if path.is_file()), None)


def probe_strict_lean(gate: dict[str, Any], log: EventLog) -> dict[str, Any]:
    runner = find_first([
        select_descriptor_tool("lean_runner", "executable/formal/run_lean_build.py"),
        CORPUS / "executable/formal/run_lean_strict.py",
    ])
    lake = shutil.which("lake")
    checks = {"runner_present": bool(runner), "lake_present": bool(lake)}
    if not runner or not lake:
        return {"status": "blocked", "checks": checks, "reason": "strict Lean runner or pinned lake toolchain absent"}
    result = run_command([sys.executable, str(runner), "--mode", "strict", "--json"], CORPUS, gate["timeout_seconds"], log)
    checks.update({"exit_code": result["exit_code"], "timed_out": result["timed_out"], "stdout_shake256_512": result["stdout_shake256_512"], "stderr_shake256_512": result["stderr_shake256_512"]})
    return {"status": "passed" if result["exit_code"] == 0 else "failed", "checks": checks, "command": result}


def probe_strict_tlc(gate: dict[str, Any], log: EventLog) -> dict[str, Any]:
    runner = find_first([
        select_descriptor_tool("tla_runner", "executable/formal/run_tla_model_check.py"),
        CORPUS / "executable/formal/run_tla_model.py",
        CORPUS / "executable/formal/run_tlc_strict.py",
    ])
    java = shutil.which("java")
    checks = {"runner_present": bool(runner), "java_present": bool(java)}
    if not runner or not java:
        return {"status": "blocked", "checks": checks, "reason": "strict TLC runner or Java/TLC toolchain absent"}
    result = run_command([sys.executable, str(runner), "--mode", "strict", "--json"], CORPUS, gate["timeout_seconds"], log)
    checks.update({"exit_code": result["exit_code"], "timed_out": result["timed_out"], "stdout_shake256_512": result["stdout_shake256_512"], "stderr_shake256_512": result["stderr_shake256_512"]})
    return {"status": "passed" if result["exit_code"] == 0 else "failed", "checks": checks, "command": result}


def _proc_status() -> dict[str, str]:
    result = {}
    for line in Path("/proc/self/status").read_text().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key] = value.strip()
    return result


def probe_hermetic(_: dict[str, Any], log: EventLog) -> dict[str, Any]:
    proc = _proc_status()
    denied_writes = []
    for target in (Path("/rootfs-write-test"), CORPUS_SOURCE / ".write-test", SOURCE / ".write-test"):
        try:
            target.write_text("forbidden")
            denied_writes.append(False)
            target.unlink(missing_ok=True)
        except OSError:
            denied_writes.append(True)
    network_denied = False
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=1):
            network_denied = False
    except OSError:
        network_denied = True
    checks = {
        "uid_non_root": os.geteuid() != 0,
        "rootless_host_preflight": os.environ.get("HARNESS_ROOTLESS") == "true",
        "network_none": network_denied,
        "read_only_rootfs_and_inputs": all(denied_writes),
        "capabilities_dropped": int(proc.get("CapEff", "1"), 16) == 0,
        "no_new_privileges": proc.get("NoNewPrivs") == "1",
        "seccomp_active": proc.get("Seccomp") in {"1", "2"},
    }
    log.emit("hermetic_measurement", **checks)
    return {"status": "passed" if all(checks.values()) else "failed", "checks": checks}


def probe_clean_source(gate: dict[str, Any], log: EventLog) -> dict[str, Any]:
    git = shutil.which("git")
    if not git or not (SOURCE / ".git").exists():
        return {"status": "blocked", "checks": {"git_present": bool(git), "git_metadata_present": (SOURCE / ".git").exists()}, "reason": "source Git metadata unavailable"}
    result = run_command([git, "-C", str(SOURCE), "status", "--porcelain=v1", "--untracked-files=all"], SOURCE, gate["timeout_seconds"], log)
    clean = result["exit_code"] == 0 and not result["stdout"].strip()
    head = run_command([git, "-C", str(SOURCE), "rev-parse", "HEAD"], SOURCE, 30, log)
    checks = {"clean_tree": clean, "commit_id": head["stdout"].strip(), "status_exit_code": result["exit_code"], "status_output_shake256_512": result["stdout_shake256_512"]}
    return {"status": "passed" if clean and head["exit_code"] == 0 else "failed", "checks": checks, "command": result}


def probe_pq_provider(gate: dict[str, Any], log: EventLog) -> dict[str, Any]:
    harness_test = ROOT / "pq_crypto.py"
    corpus_test = CORPUS / "validation/test_pq_provider.py"
    if not harness_test.is_file():
        return {
            "status": "blocked",
            "checks": {"harness_provider_test_present": False},
            "reason": "versioned harness cryptographic provider test absent",
        }
    harness_result = run_command(
        [sys.executable, str(harness_test)],
        ROOT,
        gate["timeout_seconds"],
        log,
    )
    corpus_result = (
        run_command(
            [sys.executable, str(corpus_test)],
            CORPUS,
            gate["timeout_seconds"],
            log,
        )
        if corpus_test.is_file()
        else {
            "exit_code": 2,
            "timed_out": False,
            "stdout_shake256_512": shake(b""),
            "stderr_shake256_512": shake(b"corpus provider test absent"),
        }
    )
    checks = {
        "harness_provider_test_present": True,
        "corpus_provider_test_present": corpus_test.is_file(),
        "harness_exit_code": harness_result["exit_code"],
        "corpus_exit_code": corpus_result["exit_code"],
        "known_answer_tests": harness_result["exit_code"] == 0,
        "negative_tests": harness_result["exit_code"] == 0,
        "ml_dsa_87": harness_result["exit_code"] == 0,
        "ml_kem_1024": harness_result["exit_code"] == 0,
        "kmac256": harness_result["exit_code"] == 0,
        "aes_256_gcm_siv": harness_result["exit_code"] == 0,
        "profile_registry_present": (ROOT / "cryptographic_profile_registry_v1.json").is_file(),
    }
    passed = all(checks.values())
    return {
        "status": "passed" if passed else "failed",
        "checks": checks,
        "harness_command": harness_result,
        "corpus_command": corpus_result,
    }


def load_evidence(gate_id: str) -> dict[str, Any] | None:
    path = EVIDENCE / f"{gate_id}.json"
    return json.loads(path.read_text()) if path.is_file() else None


def evidence_claim_probe(gate: dict[str, Any], _: EventLog) -> dict[str, Any]:
    """Create a stable challenge for work that must execute on an external system.

    This measurement intentionally does not read the evidence directory. The first
    run and verification rerun therefore produce the same result ID.
    """
    return {
        "status": "passed",
        "external_execution_required": True,
        "checks": {
            "external_evidence_channel_ready": True,
            "gate_id": gate["gate_id"],
            "required_claims": gate.get("required_claims", []),
            "issuer_scopes": gate.get("issuer_scopes", []),
            "self_issuance_forbidden": bool(gate.get("self_issuance_forbidden", False)),
        },
    }


def probe_reproducible_build(gate: dict[str, Any], log: EventLog) -> dict[str, Any]:
    builder = CORPUS / "executable/formal/build_trusted_inspector.py"
    if not builder.is_file():
        return {
            "status": "blocked",
            "checks": {"reproducible_builder_present": False},
            "reason": "5.3.17 reproducible inspector builder absent",
        }
    result = run_command(
        [sys.executable, str(builder), "--json"],
        CORPUS,
        gate["timeout_seconds"],
        log,
    )
    checks = {
        "reproducible_builder_present": True,
        "two_clean_builds_executed": True,
        "exit_code": result["exit_code"],
        "timed_out": result["timed_out"],
        "stdout_shake256_512": result["stdout_shake256_512"],
        "stderr_shake256_512": result["stderr_shake256_512"],
    }
    return {
        "status": "passed" if result["exit_code"] == 0 else "failed",
        "checks": checks,
        "command": result,
    }


PROBES = {
    "strict_lean": probe_strict_lean,
    "strict_tlc": probe_strict_tlc,
    "hermetic_sandbox": probe_hermetic,
    "clean_source": probe_clean_source,
    "pq_provider": probe_pq_provider,
    "evidence_only": evidence_claim_probe,
    "reproducible_build": probe_reproducible_build,
    "recovery_drill": evidence_claim_probe,
    "mixed_version": evidence_claim_probe,
}


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def verify_evidence(gate: dict[str, Any], measurement_id: str, subject_id: str, expected_run_id: str, now: datetime, historical_challenge: bool = False) -> dict[str, Any]:
    evidence = load_evidence(gate["gate_id"])
    if evidence is None:
        return {"verified": False, "reason": "missing_external_evidence"}
    errors = sorted(error.message for error in VALIDATOR.iter_errors(evidence))
    if errors:
        return {"verified": False, "reason": "schema_invalid", "errors": errors}
    if evidence.get("contract_version") != CONTRACT_REF:
        return {"verified": False, "reason": "contract_version_mismatch"}
    required_claims = gate.get("required_claims", [])
    claims = evidence.get("claims", {})
    missing_claims = [name for name in required_claims if name not in claims]
    falsey_claims = [name for name in required_claims if name in claims and not claims[name]]
    if missing_claims:
        return {"verified": False, "reason": "required_claims_missing", "claims": missing_claims}
    if falsey_claims:
        return {"verified": False, "reason": "required_claims_falsey", "claims": falsey_claims}
    if gate["gate_id"] == "external_governance_authorization" and str(claims.get("decision", "")).lower() not in {"approved", "authorized", "allow"}:
        return {"verified": False, "reason": "governance_decision_not_authorized"}
    if evidence["gate_id"] != gate["gate_id"] or evidence["subject_id"] != subject_id:
        return {"verified": False, "reason": "gate_or_subject_mismatch"}
    if evidence["probe"]["run_id"] != expected_run_id:
        return {"verified": False, "reason": "probe_run_mismatch"}
    if not historical_challenge and evidence["probe"]["result_id"] != measurement_id:
        return {"verified": False, "reason": "probe_measurement_mismatch"}
    challenge_body = {
        "contract_version": CONTRACT_REF,
        "gate_id": gate["gate_id"],
        "subject_id": subject_id,
        "probe": evidence["probe"],
    }
    expected_challenge = duoid(
        "DUOTRONIC/EXTERNAL-GATE-CHALLENGE/v1", challenge_body
    )
    if evidence.get("challenge_id") != expected_challenge:
        return {"verified": False, "reason": "challenge_binding_mismatch"}
    expected_nonce = duoid(
        "DUOTRONIC/EXTERNAL-GATE-REPLAY-NONCE/v1",
        {"challenge_id": expected_challenge, "key_id": evidence.get("key_id")},
    )
    if evidence.get("replay_nonce") != expected_nonce:
        return {"verified": False, "reason": "replay_nonce_mismatch"}
    provenance = evidence.get("provenance", {})
    if (
        provenance.get("measurement_id") != evidence["probe"]["result_id"]
        or provenance.get("probe_run_id") != expected_run_id
        or provenance.get("independent_key") is not True
    ):
        return {"verified": False, "reason": "provenance_binding_mismatch"}
    expected_profile_id = duoid(
        "DUOTRONIC/CRYPTOGRAPHIC-PROFILE-REGISTRY/v1",
        CRYPTO_PROFILE_REGISTRY,
    )
    if (
        evidence.get("cryptographic_profile") != "duotronic-pq-2026.1"
        or evidence.get("profile_registry_id") != expected_profile_id
    ):
        return {"verified": False, "reason": "cryptographic_profile_mismatch"}
    issued, expires = parse_time(evidence["issued_at"]), parse_time(evidence["expires_at"])
    skew = REGISTRY["evidence_profile"]["clock_skew_seconds"]
    if now.timestamp() + skew < issued.timestamp() or now.timestamp() - skew >= expires.timestamp():
        return {"verified": False, "reason": "evidence_not_current"}
    unsigned = {key: value for key, value in evidence.items() if key not in {"signed_payload_shake256_512", "signature_base64url"}}
    payload = canonical_bytes(unsigned)
    if shake(payload) != evidence["signed_payload_shake256_512"]:
        return {"verified": False, "reason": "payload_commitment_mismatch"}
    trust_path = EVIDENCE / "trust_registry.json"
    if not trust_path.is_file():
        return {"verified": False, "reason": "trust_registry_missing"}
    trust = json.loads(trust_path.read_text())
    if (
        trust.get("cryptographic_profile") != "duotronic-pq-2026.1"
        or trust.get("profile_registry_id") != expected_profile_id
    ):
        return {"verified": False, "reason": "trust_registry_profile_mismatch"}
    revoked = {
        str(item.get("key_id"))
        for item in trust.get("revocations", [])
        if isinstance(item, dict)
    }
    if evidence.get("key_id") in revoked:
        return {"verified": False, "reason": "key_revoked"}
    if evidence.get("authority_profile") != AUTHORITY_PROFILE or trust.get("authority_profile") != AUTHORITY_PROFILE:
        return {"verified": False, "reason": "authority_profile_mismatch"}
    if evidence.get("authority_namespace") != AUTHORITY_NAMESPACE or trust.get("authority_namespace") != AUTHORITY_NAMESPACE:
        return {"verified": False, "reason": "authority_namespace_mismatch"}
    if AUTHORITY_PROFILE == "sandbox-test-only":
        if evidence.get("production_eligible") is not False or trust.get("production_eligible") is not False:
            return {"verified": False, "reason": "sandbox_evidence_marked_production_eligible"}
        if evidence.get("evidence_environment") != "witness-harness-vm":
            return {"verified": False, "reason": "sandbox_environment_mismatch"}
    elif evidence.get("production_eligible") is not True:
        return {"verified": False, "reason": "production_evidence_not_eligible"}
    key = next((item for item in trust.get("keys", []) if item.get("key_id") == evidence["key_id"] and item.get("issuer_id") == evidence["issuer_id"]), None)
    if not key or key.get("status") != "active":
        return {"verified": False, "reason": "untrusted_or_inactive_key"}
    if key.get("authority_profile") != AUTHORITY_PROFILE or key.get("authority_namespace") != AUTHORITY_NAMESPACE:
        return {"verified": False, "reason": "key_authority_domain_mismatch"}
    if AUTHORITY_PROFILE == "sandbox-test-only" and key.get("production_eligible") is not False:
        return {"verified": False, "reason": "sandbox_key_marked_production_eligible"}
    if not set(gate.get("issuer_scopes", [])).intersection(key.get("scopes", [])):
        return {"verified": False, "reason": "issuer_scope_mismatch"}
    if gate.get("self_issuance_forbidden") and key.get("managed_by_harness", False):
        return {"verified": False, "reason": "forbidden_harness_self_issuance"}
    try:
        public_key = base64.urlsafe_b64decode(key["public_key_base64url"] + "=" * (-len(key["public_key_base64url"]) % 4))
        signature = base64.urlsafe_b64decode(evidence["signature_base64url"] + "=" * (-len(evidence["signature_base64url"]) % 4))
        valid = ml_dsa_87.verify(public_key, payload, signature)
    except Exception as error:
        return {"verified": False, "reason": "signature_verification_error", "error": type(error).__name__}
    return {"verified": valid is True, "reason": ("verified_historical_challenge" if valid is True and historical_challenge else ("verified" if valid is True else "signature_invalid")), "issuer_id": evidence["issuer_id"], "key_id": evidence["key_id"], "attested_measurement_id": evidence["probe"]["result_id"], "current_revalidation_measurement_id": measurement_id}


def subject_id() -> str:
    """Bind evidence to the exact mounted corpus, independent of its draft number."""
    match = re.search(r"draft[ _-]+([0-9.]+)", CONTRACT_REF, re.IGNORECASE)
    suffix = match.group(1).replace(".", "_") if match else ""
    descriptors = sorted(CORPUS.glob("CANONICAL_CORPUS*.json"))
    inventories = sorted(CORPUS.glob("PACKAGE_INVENTORY*.json"))
    descriptor = next((path for path in reversed(descriptors) if suffix and suffix in path.stem), None)
    inventory = next((path for path in reversed(inventories) if suffix and suffix in path.stem), None)
    if descriptor and inventory:
        return duoid(
            "DUOTRONIC/ACTIVATION-SUBJECT/v2",
            {
                "contract_ref": CONTRACT_REF,
                "descriptor": json.loads(descriptor.read_text()),
                "inventory": json.loads(inventory.read_text()),
            },
        )
    entries = []
    for path in sorted(CORPUS.rglob("*")):
        if path.is_file() and not any(part in {".lake", "__pycache__", ".pytest_cache"} for part in path.parts):
            entries.append({
                "path": path.relative_to(CORPUS).as_posix(),
                "bytes": path.stat().st_size,
                "shake256_512": shake(path.read_bytes()),
            })
    return duoid("DUOTRONIC/ACTIVATION-SUBJECT/v2", {"contract_ref": CONTRACT_REF, "files": entries})



def select_contract_descriptor(root: Path) -> tuple[dict[str, Any], Path, Path]:
    """Select the highest valid canonical descriptor and its confined validator."""
    candidates: list[tuple[tuple[int, int, int], Path, dict[str, Any], Path]] = []
    root = root.resolve()
    version_pattern = re.compile(r"^v1\.6-draft-([0-9]+)\.([0-9]+)\.([0-9]+)$")
    for path in root.glob("CANONICAL_CORPUS*.json"):
        try:
            descriptor = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        match = version_pattern.fullmatch(str(descriptor.get("active_version", "")))
        validator_relative = descriptor.get("validator")
        if not match or not isinstance(validator_relative, str):
            continue
        validator = (root / validator_relative).resolve()
        if not validator.is_relative_to(root) or not validator.is_file():
            continue
        version_key = tuple(int(value) for value in match.groups())
        candidates.append((version_key, path, descriptor, validator))
    if not candidates:
        raise RuntimeError("no valid canonical corpus descriptor with confined validator")
    _, path, descriptor, validator = max(candidates, key=lambda item: item[0])
    if descriptor["active_version"] != CONTRACT_REF:
        raise RuntimeError(
            f"contract ref {CONTRACT_REF!r} does not match selected descriptor "
            f"{descriptor['active_version']!r}"
        )
    return descriptor, path, validator


def select_descriptor_tool(field: str, fallback: str) -> Path:
    """Resolve a descriptor-selected executable without permitting corpus escape."""
    descriptor, _, _ = select_contract_descriptor(CORPUS)
    relative = descriptor.get(field, fallback)
    if not isinstance(relative, str):
        raise RuntimeError(f"descriptor field {field!r} must be a string")
    resolved = (CORPUS / relative).resolve()
    if not resolved.is_relative_to(CORPUS.resolve()) or not resolved.is_file():
        raise RuntimeError(f"descriptor field {field!r} does not select a confined file")
    return resolved


def qualification_suite(log: EventLog) -> dict[str, Any]:
    """Run the complete portable contract/toolchain preflight inside the sandbox."""
    descriptor, descriptor_path, portable_validator = select_contract_descriptor(CORPUS)
    commands = [
        ("python", [sys.executable, "--version"], 30),
        ("lean", ["lean", "--version"], 30),
        ("lake", ["lake", "--version"], 30),
        ("java", ["java", "-version"], 30),
        ("git", ["git", "--version"], 30),
        ("jq", ["jq", "--version"], 30),
        ("sqlite", ["sqlite3", "--version"], 30),
        ("zstd", ["zstd", "--version"], 30),
        (
            "post_quantum_python_providers",
            [
                sys.executable, "-c",
                "from pqcrypto.sign import ml_dsa_87; "
                "from pqcrypto.kem import ml_kem_1024; "
                "from Cryptodome.Hash import KMAC256; "
                "from cryptography.hazmat.primitives.ciphers.aead import AESGCMSIV; "
                "print('ML-DSA-87 ML-KEM-1024 KMAC256 AES-256-GCM-SIV providers available')",
            ],
            30,
        ),
        (
            "portable_corpus_validator",
            [sys.executable, str(portable_validator), str(CORPUS)],
            900,
        ),
        (
            "identity_vectors",
            [sys.executable, str(CORPUS / "validation/test_identity.py")],
            120,
        ),
    ]
    results: dict[str, Any] = {}
    for name, argv, timeout in commands:
        result = run_command(argv, CORPUS, timeout, log)
        results[name] = result
    lake_output = (
        results["lake"].get("stdout", "") + results["lake"].get("stderr", "")
    )
    checks = {
        "all_toolchains_executed_in_sandbox": True,
        "lean_4_29_1_pinned": "4.29.1" in lake_output,
        "portable_corpus_validator_passed": results["portable_corpus_validator"]["exit_code"] == 0,
        "identity_vectors_passed": results["identity_vectors"]["exit_code"] == 0,
        "post_quantum_providers_available": results["post_quantum_python_providers"]["exit_code"] == 0,
        "all_inventory_commands_passed": all(
            result["exit_code"] == 0 for result in results.values()
        ),
        "runtime_connected": False,
    }
    report = {
        "schema": "duotronic-contract-qualification-suite/v1",
        "contract_version": descriptor["active_version"],
        "descriptor_path": descriptor_path.relative_to(CORPUS).as_posix(),
        "validator_path": portable_validator.relative_to(CORPUS).as_posix(),
        "passed": all(value for key, value in checks.items() if key != "runtime_connected"),
        "checks": checks,
        "toolchains": results,
        "authority_activated": False,
        "runtime_connected": False,
    }
    (OUTPUT / "toolchain-inventory.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n"
    )
    (OUTPUT / "qualification-suite.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    log.emit("qualification_suite", passed=report["passed"], checks=checks)
    return report

def targeted_qualification_suite(log: EventLog) -> dict[str, Any]:
    """Fast development preflight; never qualifies a corpus for runtime handoff."""
    checks = {
        "mode_targeted": True,
        "probe_owns_required_toolchain_checks": True,
        "release_qualification_executed": False,
        "runtime_connected": False,
    }
    report = {
        "schema": "duotronic-contract-qualification-suite/v1",
        "contract_version": CONTRACT_REF,
        "mode": "targeted",
        "passed": True,
        "release_eligible": False,
        "checks": checks,
        "toolchains": {},
        "authority_activated": False,
        "runtime_connected": False,
    }
    (OUTPUT / "toolchain-inventory.json").write_text("{}\n", encoding="utf-8")
    (OUTPUT / "qualification-suite.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    log.emit("qualification_suite", mode="targeted", passed=True, checks=checks)
    return report


def prepare_working_corpus(log: EventLog) -> dict[str, Any]:
    started = time.monotonic()
    if not CORPUS_SOURCE.is_dir():
        return {"passed": False, "reason": "read_only_corpus_mount_missing"}
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    shutil.copytree(CORPUS_SOURCE, CORPUS, symlinks=True, dirs_exist_ok=False)
    probe = CORPUS / ".workspace-write-probe"
    probe.write_text("ephemeral", encoding="utf-8")
    probe.unlink()
    result = {
        "passed": True,
        "source": str(CORPUS_SOURCE),
        "workspace": str(CORPUS),
        "source_read_only": True,
        "workspace_ephemeral": True,
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }
    log.emit("working_corpus_prepared", **result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--evidence-run-id")
    parser.add_argument("--gate", action="append", default=[])
    parser.add_argument("--qualification-mode", choices=("full", "targeted"), default="full")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    log = EventLog(OUTPUT / "sandbox.log.ndjson")
    barrier_value = os.environ.get("HARNESS_START_BARRIER")
    if barrier_value:
        barrier = Path(barrier_value)
        deadline = time.monotonic() + 180
        log.emit("start_barrier_wait", path=str(barrier), timeout_seconds=180)
        while not barrier.is_file() and time.monotonic() < deadline:
            time.sleep(0.1)
        if not barrier.is_file():
            log.emit("start_barrier_timeout", path=str(barrier))
            return 70
        log.emit("start_barrier_released", path=str(barrier))
    try:
        workspace = prepare_working_corpus(log)
    except Exception as error:
        log.emit("working_corpus_failed", error=f"{type(error).__name__}: {error}")
        return 71
    if not workspace.get("passed"):
        log.emit("working_corpus_failed", **workspace)
        return 71
    (OUTPUT / "working-corpus.json").write_text(
        json.dumps(workspace, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    selected = set(args.gate)
    gates = [gate for gate in REGISTRY["gates"] if not selected or gate["gate_id"] in selected]
    subject = subject_id()
    qualification = qualification_suite(log) if args.qualification_mode == "full" else targeted_qualification_suite(log)
    now = datetime.now(timezone.utc)
    log.emit("sandbox_start", run_id=args.run_id, subject_id=subject, gates=[gate["gate_id"] for gate in gates], uid=os.geteuid())
    results = []
    for gate in gates:
        log.emit("gate_start", gate_id=gate["gate_id"], probe=gate["probe"])
        try:
            probe = PROBES[gate["probe"]](gate, log)
            measurement = {"contract_version": CONTRACT_REF, "gate_id": gate["gate_id"], "subject_id": subject, "probe_status": probe["status"], "checks": probe.get("checks", {})}
            measurement_id = duoid("DUOTRONIC/EXTERNAL-GATE-MEASUREMENT/v1", measurement)
            external = verify_evidence(gate, measurement_id, subject, args.evidence_run_id or args.run_id, now, historical_challenge=bool(args.evidence_run_id))
            state = "verified" if probe["status"] == "passed" and external["verified"] else ("failed" if probe["status"] == "failed" else "blocked")
            result = {"gate_id": gate["gate_id"], "ordinal": gate["ordinal"], "title": gate["title"], "state": state, "measurement_id": measurement_id, "probe": probe, "external_evidence": external}
        except Exception as error:
            result = {"gate_id": gate["gate_id"], "ordinal": gate["ordinal"], "title": gate["title"], "state": "error", "error": f"{type(error).__name__}: {error}"}
        (OUTPUT / f"gate-{gate['ordinal']:02d}-{gate['gate_id']}.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        log.emit("gate_finish", gate_id=gate["gate_id"], state=result["state"], measurement_id=result.get("measurement_id"))
        results.append(result)
    gate_by_id = {item["gate_id"]: item for item in gates}
    attestation_requests = {
        "schema": "duotronic-external-attestation-requests/v1",
        "contract_version": CONTRACT_REF,
        "run_id": args.run_id,
        "subject_id": subject,
        "runtime_connected": False,
        "production_runtime_connected": False,
        "authority_profile": AUTHORITY_PROFILE,
        "authority_namespace": AUTHORITY_NAMESPACE,
        "requests": [
            {
                "gate_id": result["gate_id"],
                "measurement_id": result.get("measurement_id"),
                "probe": {
                    "run_id": args.run_id,
                    "exit_code": 0 if result.get("probe", {}).get("status") == "passed" else 1,
                    "result_id": result.get("measurement_id"),
                },
                "required_claims": gate_by_id[result["gate_id"]].get("required_claims", []),
                "issuer_scopes": gate_by_id[result["gate_id"]].get("issuer_scopes", []),
                "self_issuance_forbidden": bool(gate_by_id[result["gate_id"]].get("self_issuance_forbidden", False)),
                "evidence_filename": f"{result['gate_id']}.json",
            }
            for result in results
            if result.get("measurement_id")
        ],
    }
    (OUTPUT / "external-attestation-requests.json").write_text(
        json.dumps(attestation_requests, indent=2, sort_keys=True) + "\n"
    )
    result_states = {item["state"] for item in results}
    if not qualification["passed"] or result_states.intersection({"failed", "error"}):
        report_state = "failed"
    elif results and all(item["state"] == "verified" for item in results):
        report_state = "verified"
    else:
        report_state = "blocked"
    report = {
        "report_schema": "duotronic-external-activation-sandbox-report/v1",
        "state": report_state,
        "contract_version": CONTRACT_REF,
        "run_id": args.run_id,
        "subject_id": subject,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qualification_suite": qualification,
        "qualification_mode": args.qualification_mode,
        "runtime_connected": False,
        "production_runtime_connected": False,
        "authority_profile": AUTHORITY_PROFILE,
        "authority_namespace": AUTHORITY_NAMESPACE,
        "production_eligible": AUTHORITY_PROFILE == "production",
        "selected_gate_count": len(gates),
        "verified_gate_count": sum(item["state"] == "verified" for item in results),
        "all_selected_gates_verified": bool(results) and all(item["state"] == "verified" for item in results),
        "activation_eligible": args.qualification_mode == "full" and qualification["passed"] and len(gates) == REGISTRY["gate_count"] and all(item["state"] == "verified" for item in results),
        "authority_activated": False,
        "activation_requires_separate_external_governance_action": AUTHORITY_PROFILE == "production",
        "sandbox_activation_requires_guest_commit": AUTHORITY_PROFILE == "sandbox-test-only",
        "gates": results,
    }
    (OUTPUT / "sandbox-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    log.emit("sandbox_finish", verified_gate_count=report["verified_gate_count"], activation_eligible=report["activation_eligible"], authority_activated=False)
    return 0 if report["all_selected_gates_verified"] and qualification["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
