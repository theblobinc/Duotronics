#!/usr/bin/env python3
"""Run both production loaders as a real non-root UID in an /etc-style chroot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
from datetime import datetime, timezone

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executable/runtime"))

import proof_authority as authority  # noqa: E402
import proof_check_service as service  # noqa: E402


SERVICE_UID = 65534
SERVICE_GID = 65534


class EnvironmentUnavailable(RuntimeError):
    """The launcher cannot provide a required production-shape kernel facility."""



def _identifier_map(name: str) -> str:
    try:
        return pathlib.Path(f"/proc/self/{name}_map").read_text(encoding="ascii").strip()
    except (FileNotFoundError, PermissionError):
        return "unavailable"


def probe_execution_environment() -> dict:
    """Prove the launcher can create objects owned by the intended service UID/GID."""
    if os.geteuid() != 0:
        return {
            "status": "environment_unavailable",
            "reason": "production-shape chroot integration requires a root launcher before setuid",
            "effective_uid": os.geteuid(), "effective_gid": os.getegid(),
            "uid_map": _identifier_map("uid"), "gid_map": _identifier_map("gid"),
        }
    with tempfile.TemporaryDirectory(prefix="witness-loader-id-probe-") as directory:
        probe = pathlib.Path(directory) / "service-owned"
        probe.write_bytes(b"")
        try:
            os.chown(probe, SERVICE_UID, SERVICE_GID)
        except OSError as error:
            return {
                "status": "environment_unavailable",
                "reason": f"intended non-root UID/GID cannot be represented: {error}",
                "effective_uid": os.geteuid(), "effective_gid": os.getegid(),
                "intended_service_uid": SERVICE_UID, "intended_service_gid": SERVICE_GID,
                "uid_map": _identifier_map("uid"), "gid_map": _identifier_map("gid"),
            }
        owned = probe.stat()
        if (owned.st_uid, owned.st_gid) != (SERVICE_UID, SERVICE_GID):
            return {
                "status": "environment_unavailable",
                "reason": "ownership transition did not produce the intended service identity",
                "effective_uid": os.geteuid(), "effective_gid": os.getegid(),
                "observed_uid": owned.st_uid, "observed_gid": owned.st_gid,
                "uid_map": _identifier_map("uid"), "gid_map": _identifier_map("gid"),
            }
    return {
        "status": "available", "effective_uid": os.geteuid(), "effective_gid": os.getegid(),
        "intended_service_uid": SERVICE_UID, "intended_service_gid": SERVICE_GID,
        "uid_map": _identifier_map("uid"), "gid_map": _identifier_map("gid"),
    }


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _private_pem(key: Ed25519PrivateKey) -> bytes:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def _public_pem(key: Ed25519PrivateKey) -> bytes:
    return key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def _copy_runtime_and_dependencies(chroot_root: pathlib.Path, trust_root: pathlib.Path) -> tuple[pathlib.Path, str]:
    source = pathlib.Path("/bin/echo").resolve(strict=True)
    destination = trust_root / "oci-runtime"
    shutil.copyfile(source, destination)
    destination.chmod(0o700)
    os.chown(destination, SERVICE_UID, SERVICE_GID)
    completed = subprocess.run(
        ["ldd", str(source)], text=True, capture_output=True, check=True,
    )
    dependency_paths = set(re.findall(r"(?:=>\s+)?(/[A-Za-z0-9_+.,/@=-][^\s()]*)", completed.stdout))
    if not dependency_paths:
        raise RuntimeError("unable to enumerate dynamic runtime dependencies")
    for source_name in sorted(dependency_paths):
        dependency = pathlib.Path(source_name)
        if not dependency.is_file():
            raise RuntimeError(f"runtime dependency is absent: {dependency}")
        target = chroot_root / dependency.relative_to("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.parent.chmod(0o755)
        shutil.copyfile(dependency, target)
        target.chmod(0o755 if os.access(dependency, os.X_OK) else 0o644)
    return pathlib.Path("/etc/witness-authority/oci-runtime"), _digest(destination.read_bytes())


def _prepare_fixture(chroot_root: pathlib.Path) -> None:
    chroot_root.chmod(0o755)
    etc = chroot_root / "etc"
    etc.mkdir(mode=0o755)
    trust_root = etc / "witness-authority"
    trust_root.mkdir(mode=0o700)
    schemas = trust_root / "schemas"
    artifacts = trust_root / "artifacts"
    schemas.mkdir(mode=0o700)
    artifacts.mkdir(mode=0o700)

    for source in sorted((ROOT / "schemas").glob("*.schema.json")):
        target = schemas / source.name
        shutil.copyfile(source, target)
        target.chmod(0o600)
        os.chown(target, SERVICE_UID, SERVICE_GID)

    def write(name: str, data: bytes, mode: int = 0o600) -> None:
        target = trust_root / name
        target.write_bytes(data)
        target.chmod(mode)
        os.chown(target, SERVICE_UID, SERVICE_GID)

    governance = Ed25519PrivateKey.generate()
    witness = Ed25519PrivateKey.generate()
    verifier_result = Ed25519PrivateKey.generate()
    cache = Ed25519PrivateKey.generate()
    cache_audit = Ed25519PrivateKey.generate()
    runtime_path, runtime_sha256 = _copy_runtime_and_dependencies(chroot_root, trust_root)

    seccomp = authority.canonical_bytes({})
    write("seccomp.json", seccomp)
    migration = b"-- governed test migration\n"
    dependencies = authority.canonical_bytes({"closure": "loader-integration"})
    write("migration.sql", migration)
    write("deps.json", dependencies)

    compiler_registry = authority.sign_record({
        "schema_version": "governed_compiler_registry/v2",
        "registry_id": "compiler:registry:integration",
        "governance_key_id": "governance:key:integration",
        "profiles": [{
            "compiler_profile_id": "profile:integration", "toolchain": "lean:test",
            "image_reference": "registry.invalid/witness/integration",
            "oci_image_digest": "sha256:" + "1" * 64,
            "oci_runtime_sha256": runtime_sha256, "oci_runtime_version": "version",
            "lake_executable_sha256": "2" * 64, "lean_executable_sha256": "3" * 64,
            "lean_stdlib_tree_sha256": "4" * 64, "dependency_closure_sha256": "5" * 64,
            "verifier_executable_sha256": "6" * 64,
            "verifier_source_revision": "integration:source",
            "verifier_build_attestation_id": "attestation:integration",
            "sandbox_policy_sha256": "7" * 64,
            "verifier_result_signer_key_id": "verifier-result:key:integration",
            "verifier_result_public_key_base64url": authority.public_key_raw_b64url(verifier_result.public_key()),
            "authorized_axioms": ["Classical.choice", "Quot.sound", "propext"],
            "valid_from": "2026-01-01T00:00:00Z", "valid_until": None,
        }],
        "created_at": "2026-08-01T00:00:00Z",
    }, governance)
    write("compiler-registry.json", authority.canonical_bytes(compiler_registry))

    decision_without_hash = {
        "schema_version": "proof_policy_decision/v1", "policy_decision_id": "policy:integration",
        "status": "active", "subject_id": "*", "operation": "proof_check",
        "compiler_profile_ids": ["profile:integration"], "source_bundle_ids": ["*"],
        "resource_permissions": {"maximum_timeout_seconds": 60, "maximum_source_bytes": 1048576},
        "valid_from": "2026-01-01T00:00:00Z", "valid_until": None,
        "supersedes_policy_decision_id": None, "governance_authority_id": "governance:key:integration",
        "created_at": "2026-08-01T00:00:00Z",
    }
    decision = {
        **decision_without_hash,
        "canonical_record_sha256": authority.sha256_bytes(authority.canonical_bytes(decision_without_hash)),
    }
    policy_registry = authority.sign_record({
        "schema_version": "proof_policy_registry/v1", "registry_id": "policy:registry:integration",
        "governance_key_id": "governance:key:integration", "decisions": [decision],
        "created_at": "2026-08-01T00:00:00Z",
    }, governance)
    write("policy-registry.json", authority.canonical_bytes(policy_registry))

    trusted_artifacts = authority.sign_record({
        "schema_version": "trusted_artifact_attestation_registry/v1",
        "registry_id": "trusted:artifacts:integration", "governance_key_id": "governance:key:integration",
        "artifacts": [
            {"artifact_id": "migration:integration", "role": "database_migrations", "verification_mode": "direct_trusted_root_file", "relative_path": "migration.sql", "sha256": _digest(migration), "attestation_id": None},
            {"artifact_id": "inspector:integration", "role": "trusted_inspector", "verification_mode": "governance_signed_build_attestation", "relative_path": None, "sha256": "8" * 64, "attestation_id": "attestation:inspector"},
            {"artifact_id": "image:integration", "role": "oci_image_metadata", "verification_mode": "governance_signed_build_attestation", "relative_path": None, "sha256": "9" * 64, "attestation_id": "attestation:image"},
            {"artifact_id": "dependencies:integration", "role": "dependency_manifest", "verification_mode": "direct_trusted_root_file", "relative_path": "deps.json", "sha256": _digest(dependencies), "attestation_id": None},
        ],
        "created_at": "2026-08-01T00:00:00Z",
    }, governance)
    write("trusted-artifacts.json", authority.canonical_bytes(trusted_artifacts))

    platform = {
        "schema_version": "platform_capability_probe/v1", "probe_status": "measured",
        "platform_id": "platform:loader-integration",
        "supported_controls": sorted(authority.OciSandboxRunner.REQUIRED_CONTROLS),
        "lsm": {"kind": "apparmor", "profile": "witness-integration"},
        "observed_at": "2026-08-01T00:00:00Z", "evidence_sha256": "a" * 64,
    }
    write("platform.json", authority.canonical_bytes(platform))

    cache_record = {
        "key_id": "cache:key:integration", "principal_id": "cache:principal:integration",
        "public_key_base64url": authority.public_key_raw_b64url(cache.public_key()),
        "authorization_scope": "idempotency_cache_envelope_signing", "status": "active",
        "valid_from": "2026-01-01T00:00:00Z", "valid_until": None,
        "status_changed_at": "2026-01-01T00:00:00Z", "rotation_predecessor_key_id": None,
    }
    cache_registry = authority.sign_record({
        "schema_version": "cache_signing_registry/v2", "registry_id": "cache:registry:integration",
        "governance_key_id": "governance:key:integration", "created_at": "2026-08-01T00:00:00Z",
        "keys": [cache_record],
    }, governance)
    write("cache-registry.json", authority.canonical_bytes(cache_registry))
    cache_registry_digest = authority.sha256_bytes(authority.canonical_bytes(cache_registry))
    cache_lineage = authority.sign_record({
        "schema_version": "cache_registry_lineage/v1", "lineage_id": "cache:lineage:integration",
        "governance_key_id": "governance:key:integration",
        "current_registry_sha256": cache_registry_digest, "historical_registries": [],
        "created_at": "2026-08-01T00:00:00Z",
    }, governance)
    write("cache-lineage.json", authority.canonical_bytes(cache_lineage))

    write("governance.pem", _public_pem(governance))
    write("verifier.pem", _private_pem(witness))
    write("verifier-result.pem", _private_pem(verifier_result))
    write("cache-private.pem", _private_pem(cache))
    write("cache-public.pem", _public_pem(cache))
    write("cache-audit-private.pem", _private_pem(cache_audit))
    write("cache-audit-public.pem", _public_pem(cache_audit))

    config = {
        "compiler_registry_file": "compiler-registry.json", "governance_public_key_file": "governance.pem",
        "verifier_private_key_file": "verifier.pem", "verifier_result_private_key_file": "verifier-result.pem",
        "oci_runtime_file": "oci-runtime", "oci_runtime_sha256": runtime_sha256, "oci_runtime_version": "version",
        "verifier_principal_id": "verifier:integration", "key_id": "witness:key:integration",
        "authority_snapshot_id": "snapshot:integration", "authority_ledger_high_water_sequence": 1,
        "artifact_store_root": "/etc/witness-authority/artifacts", "policy_registry_file": "policy-registry.json",
        "seccomp_profile_file": "seccomp.json", "seccomp_profile_sha256": _digest(seccomp),
        "authority_uid": SERVICE_UID, "authority_gid": SERVICE_GID,
        "platform_capability_file": "platform.json", "trusted_artifact_registry_file": "trusted-artifacts.json",
        "schema_root": "schemas", "idempotency_database": "/etc/witness-authority/idempotency.sqlite",
        "idempotency_retention_seconds": 3600, "idempotency_lease_seconds": 60,
        "idempotency_maximum_completed_rows": 100, "idempotency_maximum_inflight_rows": 10,
        "idempotency_maximum_inflight_rows_per_principal": 2, "idempotency_maximum_total_rows": 120,
        "idempotency_maximum_database_bytes": 10485760, "idempotency_maximum_cache_envelope_bytes": 1048576,
        "cache_private_key_file": "cache-private.pem", "cache_public_key_file": "cache-public.pem",
        "cache_signing_registry_file": "cache-registry.json", "cache_registry_lineage_file": "cache-lineage.json",
        "cache_signer_principal_id": cache_record["principal_id"], "cache_signer_key_id": cache_record["key_id"],
        "cache_audit_private_key_file": "cache-audit-private.pem",
        "cache_audit_public_key_file": "cache-audit-public.pem",
        "cache_audit_log_file": "cache-audit.jsonl",
        "cache_audit_signer_principal_id": "cache:audit:principal:integration",
        "cache_audit_signer_key_id": "cache:audit:key:integration",
        "cache_audit_maximum_record_bytes": 262144,
        "cache_audit_maximum_log_bytes": 10485760,
        "cache_audit_maximum_records": 10000,
        "cache_audit_rotation_policy": "manual_governance_sealed_segment",
    }
    write("service-config.json", authority.canonical_bytes(config))

    for directory in (schemas, artifacts, trust_root):
        directory.chmod(0o700)
        os.chown(directory, SERVICE_UID, SERVICE_GID)


def run_integration() -> dict:
    if os.geteuid() != 0:
        raise EnvironmentUnavailable("production-shape chroot integration requires a root test launcher before setuid")
    with tempfile.TemporaryDirectory(prefix="witness-loader-chroot-") as directory:
        chroot_root = pathlib.Path(directory)
        _prepare_fixture(chroot_root)
        proc_target = chroot_root / "proc"
        proc_target.mkdir(mode=0o755)
        mounted_proc = False
        try:
            completed = subprocess.run(
                ["mount", "--bind", "/proc", str(proc_target)],
                text=True, capture_output=True, check=False,
            )
            if completed.returncode != 0:
                reason = (completed.stderr or completed.stdout or "mount --bind /proc failed").strip()
                raise EnvironmentUnavailable(
                    "production-shape chroot requires a procfs projection for fd-anchored SQLite: " + reason
                )
            mounted_proc = True
            read_fd, write_fd = os.pipe()
            child = os.fork()
            if child == 0:
                os.close(read_fd)
                try:
                    os.chroot(chroot_root)
                    os.chdir("/")
                    os.setgroups([])
                    os.setgid(SERVICE_GID)
                    os.setuid(SERVICE_UID)
                    config_root = pathlib.Path("/etc/witness-authority")
                    authority_service = authority.load_production_authority_service(config_root)
                    application = service.load_production_application(config_root)
                    result = {
                        "status": "passed", "authority_loader": "passed", "application_loader": "passed",
                        "effective_uid": os.geteuid(), "effective_gid": os.getegid(),
                        "filesystem_anchor_owner": 0, "system_ancestor_owner": 0,
                        "trust_root_owner": SERVICE_UID, "trust_root_mode": "0700",
                        "root_execution_rejection_retained": True,
                        "authority_profile_count": len(authority_service.profiles),
                        "historical_registry_count": len(application.cache_registry_snapshots_by_sha256) - 1,
                        "cache_audit_sink": "dedicated_key_signed_append_only_chain",
                        "cache_audit_log_owner": (config_root / "cache-audit.jsonl").stat().st_uid,
                        "cache_audit_log_mode": oct((config_root / "cache-audit.jsonl").stat().st_mode & 0o777),
                    }
                    application.idempotency_store.close()
                    os.write(write_fd, authority.canonical_bytes(result))
                    os._exit(0)
                except BaseException:
                    os.write(write_fd, traceback.format_exc().encode("utf-8", errors="replace"))
                    os._exit(1)
            os.close(write_fd)
            chunks = []
            while True:
                chunk = os.read(read_fd, 65536)
                if not chunk:
                    break
                chunks.append(chunk)
            os.close(read_fd)
            waited, status = os.waitpid(child, 0)
            payload = b"".join(chunks)
            if waited != child or not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
                raise RuntimeError("non-root production-loader child failed:\n" + payload.decode("utf-8", errors="replace"))
            result = authority.canonical_json_loads(payload.decode("utf-8"))
            return {
                "schema_version": "production_loader_integration_evidence/v1",
                "package_version": "v1.6-draft-5.3.13",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "execution_model": "chroot_procfs_then_setgid_setuid_actual_loaders",
                "configuration_path": "/etc/witness-authority",
                **result,
            }
        finally:
            if mounted_proc:
                subprocess.run(["umount", str(proc_target)], check=False, capture_output=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument(
        "--allow-unavailable", action="store_true",
        help="emit a fail-closed environment_unavailable record instead of failing the command",
    )
    arguments = parser.parse_args()
    capability = probe_execution_environment()
    if capability["status"] == "available":
        try:
            evidence = {**run_integration(), "environment_probe": capability}
        except EnvironmentUnavailable as error:
            evidence = {
                "schema_version": "production_loader_integration_evidence/v1",
                "package_version": "v1.6-draft-5.3.13",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "execution_model": "chroot_procfs_then_setgid_setuid_actual_loaders",
                "configuration_path": "/etc/witness-authority",
                "authority_loader": "not_executed", "application_loader": "not_executed",
                "status": "environment_unavailable", "reason": str(error),
                "environment_probe": capability,
            }
    else:
        evidence = {
            "schema_version": "production_loader_integration_evidence/v1",
            "package_version": "v1.6-draft-5.3.13",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "execution_model": "chroot_procfs_then_setgid_setuid_actual_loaders",
            "configuration_path": "/etc/witness-authority",
            "authority_loader": "not_executed", "application_loader": "not_executed",
            **capability,
        }
    text = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    if arguments.output:
        output = pathlib.Path(arguments.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    if evidence["status"] != "passed" and not arguments.allow_unavailable:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
