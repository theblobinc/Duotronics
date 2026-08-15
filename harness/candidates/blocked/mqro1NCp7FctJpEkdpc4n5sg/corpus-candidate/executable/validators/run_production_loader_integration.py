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
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import warnings
from datetime import datetime, timezone

from cryptography.hazmat.primitives import serialization
from executable.runtime.pq_provider import MLDSA87PrivateKey

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executable/runtime"))

import proof_authority as authority  # noqa: E402
import proof_check_service as service  # noqa: E402
from cache_audit import (  # noqa: E402
    SignedAppendOnlyAuditSink, UnixSocketAuditAnchorClient, UnixSocketAuditPublisherClient,
)
from cache_audit_services import (  # noqa: E402
    AuditAnchorServer, AuditPublisherServer, DurableEventIdIndex,
    FileBackedMonotonicAnchorStore,
)


SERVICE_UID = 65534
SERVICE_GID = 65534
PUBLISHER_UID = 65533
PUBLISHER_GID = 65533
ANCHOR_UID = 65532
ANCHOR_GID = 65532
UNRELATED_UID = 65531
UNRELATED_GID = 65531


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
    return hashlib.shake_256(data).hexdigest(64)


def _private_pem(key: MLDSA87PrivateKey) -> bytes:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def _public_pem(key: MLDSA87PrivateKey) -> bytes:
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


def _prepare_fixture(chroot_root: pathlib.Path) -> dict:
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

    governance = MLDSA87PrivateKey.generate()
    witness = MLDSA87PrivateKey.generate()
    verifier_result = MLDSA87PrivateKey.generate()
    cache = MLDSA87PrivateKey.generate()
    audit_record_key = MLDSA87PrivateKey.generate()
    audit_receipt_key = MLDSA87PrivateKey.generate()
    audit_anchor_key = MLDSA87PrivateKey.generate()
    proof_request_key = MLDSA87PrivateKey.generate()
    publisher_request_key = MLDSA87PrivateKey.generate()
    runtime_path, runtime_shake256_512 = _copy_runtime_and_dependencies(chroot_root, trust_root)

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
            "oci_image_digest": "shake256-512:" + "1" * 128,
            "oci_runtime_shake256_512": runtime_shake256_512, "oci_runtime_version": "version",
            "lake_executable_shake256_512": "2" * 128, "lean_executable_shake256_512": "3" * 128,
            "lean_stdlib_tree_shake256_512": "4" * 128, "dependency_closure_shake256_512": "5" * 128,
            "verifier_executable_shake256_512": "6" * 128,
            "verifier_source_revision": "integration:source",
            "verifier_build_attestation_id": "attestation:integration",
            "sandbox_policy_shake256_512": "7" * 128,
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
        "canonical_record_shake256_512": authority.shake256_512_bytes(authority.canonical_bytes(decision_without_hash)),
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
            {"artifact_id": "migration:integration", "role": "database_migrations", "verification_mode": "direct_trusted_root_file", "relative_path": "migration.sql", "shake256_512": _digest(migration), "attestation_id": None},
            {"artifact_id": "inspector:integration", "role": "trusted_inspector", "verification_mode": "governance_signed_build_attestation", "relative_path": None, "shake256_512": "8" * 128, "attestation_id": "attestation:inspector"},
            {"artifact_id": "image:integration", "role": "oci_image_metadata", "verification_mode": "governance_signed_build_attestation", "relative_path": None, "shake256_512": "9" * 128, "attestation_id": "attestation:image"},
            {"artifact_id": "dependencies:integration", "role": "dependency_manifest", "verification_mode": "direct_trusted_root_file", "relative_path": "deps.json", "shake256_512": _digest(dependencies), "attestation_id": None},
        ],
        "created_at": "2026-08-01T00:00:00Z",
    }, governance)
    write("trusted-artifacts.json", authority.canonical_bytes(trusted_artifacts))

    platform = {
        "schema_version": "platform_capability_probe/v1", "probe_status": "measured",
        "platform_id": "platform:loader-integration",
        "supported_controls": sorted(authority.OciSandboxRunner.REQUIRED_CONTROLS),
        "lsm": {"kind": "apparmor", "profile": "witness-integration"},
        "observed_at": "2026-08-01T00:00:00Z", "evidence_shake256_512": "a" * 128,
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
    cache_registry_digest = authority.shake256_512_bytes(authority.canonical_bytes(cache_registry))
    cache_lineage = authority.sign_record({
        "schema_version": "cache_registry_lineage/v1", "lineage_id": "cache:lineage:integration",
        "governance_key_id": "governance:key:integration",
        "current_registry_shake256_512": cache_registry_digest, "historical_registries": [],
        "created_at": "2026-08-01T00:00:00Z",
    }, governance)
    write("cache-lineage.json", authority.canonical_bytes(cache_lineage))

    write("governance.pem", _public_pem(governance))
    write("verifier.pem", _private_pem(witness))
    write("verifier-result.pem", _private_pem(verifier_result))
    write("cache-private.pem", _private_pem(cache))
    write("cache-public.pem", _public_pem(cache))
    write("cache-audit-public.pem", _public_pem(audit_receipt_key))
    write("cache-audit-request-private.pem", _private_pem(proof_request_key))

    def signing_record(key_id: str, principal_id: str, key: MLDSA87PrivateKey, scope: str) -> dict:
        return {
            "key_id": key_id, "principal_id": principal_id,
            "public_key_base64url": authority.public_key_raw_b64url(key.public_key()),
            "authorization_scope": scope, "status": "active",
            "valid_from": "2026-01-01T00:00:00Z", "valid_until": None,
            "status_changed_at": "2026-01-01T00:00:00Z",
            "rotation_predecessor_key_id": None,
        }

    record_record = signing_record(
        "cache:audit:record:key:integration", "cache:audit:publisher:integration",
        audit_record_key, "cache_audit_record_signing",
    )
    receipt_record = signing_record(
        "cache:audit:receipt:key:integration", "cache:audit:publisher:integration",
        audit_receipt_key, "cache_audit_receipt_signing",
    )
    anchor_record = signing_record(
        "cache:audit:anchor:key:integration", "cache:audit:anchor:integration",
        audit_anchor_key, "cache_audit_monotonic_anchor_signing",
    )
    def signed_registry(schema_version: str, registry_id: str, record: dict) -> dict:
        return authority.sign_record({
            "schema_version": schema_version, "registry_id": registry_id,
            "governance_key_id": "governance:key:integration",
            "created_at": "2026-08-01T00:00:00Z", "keys": [record],
        }, governance)
    record_registry = signed_registry("cache_audit_signing_registry/v1", "cache:audit:record:registry:integration", record_record)
    receipt_registry = signed_registry("cache_audit_signing_registry/v1", "cache:audit:receipt:registry:integration", receipt_record)
    anchor_registry = signed_registry("cache_audit_anchor_registry/v1", "cache:audit:anchor:registry:integration", anchor_record)
    write("cache-audit-registry.json", authority.canonical_bytes(receipt_registry))

    config = {
        "compiler_registry_file": "compiler-registry.json", "governance_public_key_file": "governance.pem",
        "verifier_private_key_file": "verifier.pem", "verifier_result_private_key_file": "verifier-result.pem",
        "oci_runtime_file": "oci-runtime", "oci_runtime_shake256_512": runtime_shake256_512, "oci_runtime_version": "version",
        "verifier_principal_id": "verifier:integration", "key_id": "witness:key:integration",
        "authority_snapshot_id": "snapshot:integration", "authority_ledger_high_water_sequence": 1,
        "artifact_store_root": "/etc/witness-authority/artifacts", "policy_registry_file": "policy-registry.json",
        "seccomp_profile_file": "seccomp.json", "seccomp_profile_shake256_512": _digest(seccomp),
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
        "idempotency_sqlite_connection_mode": "private_parent_absolute_path",
        "cache_audit_public_key_file": "cache-audit-public.pem",
        "cache_audit_signing_registry_file": "cache-audit-registry.json",
        "cache_audit_signer_principal_id": receipt_record["principal_id"],
        "cache_audit_signer_key_id": receipt_record["key_id"],
        "cache_audit_request_private_key_file": "cache-audit-request-private.pem",
        "cache_audit_request_signer_key_id": "cache:audit:proof-request:key:integration",
        "cache_audit_request_principal_id": "cache:audit:proof-service:integration",
        "cache_audit_publisher_socket": "/run/witness-audit/publisher.sock",
        "cache_audit_publisher_uid": PUBLISHER_UID,
        "cache_audit_publisher_gid": PUBLISHER_GID,
        "cache_audit_publisher_socket_mode": 0o660,
    }
    write("service-config.json", authority.canonical_bytes(config))


    for directory in (schemas, artifacts, trust_root):
        directory.chmod(0o700)
        os.chown(directory, SERVICE_UID, SERVICE_GID)
    return {
        "governance": governance, "record_key": audit_record_key,
        "receipt_key": audit_receipt_key, "anchor_key": audit_anchor_key,
        "proof_request_key": proof_request_key, "publisher_request_key": publisher_request_key,
        "record_record": record_record, "receipt_record": receipt_record, "anchor_record": anchor_record,
        "record_registry": record_registry, "receipt_registry": receipt_registry, "anchor_registry": anchor_registry,
    }


def _make_private_directory(path: pathlib.Path, uid: int, gid: int, mode: int = 0o700) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.chown(path, uid, gid)
    os.chmod(path, mode)


def _read_ready(descriptor: int, child: int, name: str) -> None:
    payload = os.read(descriptor, 65536)
    os.close(descriptor)
    if payload != b"ready\n":
        try:
            os.kill(child, 9)
        except ProcessLookupError:
            pass
        os.waitpid(child, 0)
        raise RuntimeError(f"{name} failed before readiness:\n" + payload.decode("utf-8", errors="replace"))


def _stop_child(child: int) -> None:
    try:
        os.kill(child, 15)
    except ProcessLookupError:
        pass
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        try:
            waited, _status = os.waitpid(child, os.WNOHANG)
        except ChildProcessError:
            return
        if waited == child:
            return
        time.sleep(0.02)
    try:
        os.kill(child, 9)
    except ProcessLookupError:
        pass
    try:
        os.waitpid(child, 0)
    except ChildProcessError:
        pass


def run_integration() -> dict:
    if os.geteuid() != 0:
        raise EnvironmentUnavailable("production-shape cross-UID integration requires a root launcher before identity drops")
    warnings.filterwarnings("ignore", message=".*multi-threaded.*fork.*", category=DeprecationWarning)
    with tempfile.TemporaryDirectory(prefix="witness-loader-chroot-") as directory:
        chroot_root = pathlib.Path(directory)
        material = _prepare_fixture(chroot_root)
        validator = authority.CanonicalSchemaValidator(ROOT / "schemas")
        governance_key = material["governance"].public_key()
        record_registry_sha = authority.shake256_512_bytes(authority.canonical_bytes(material["record_registry"]))
        receipt_registry_sha = authority.shake256_512_bytes(authority.canonical_bytes(material["receipt_registry"]))
        anchor_registry_sha = authority.shake256_512_bytes(authority.canonical_bytes(material["anchor_registry"]))
        record_records = {material["record_record"]["key_id"]: material["record_record"]}
        receipt_records = {material["receipt_record"]["key_id"]: material["receipt_record"]}
        anchor_records = {material["anchor_record"]["key_id"]: material["anchor_record"]}
        record_keys = {material["record_record"]["key_id"]: material["record_key"].public_key()}
        receipt_keys = {material["receipt_record"]["key_id"]: material["receipt_key"].public_key()}
        anchor_keys = {material["anchor_record"]["key_id"]: material["anchor_key"].public_key()}

        # Root-owned system ancestors and three distinct private service domains.
        for relative in ("run", "var", "var/lib"):
            path = chroot_root / relative
            path.mkdir(parents=True, exist_ok=True)
            os.chown(path, 0, 0)
            os.chmod(path, 0o755)
        _make_private_directory(chroot_root / "run/witness-audit-anchor", ANCHOR_UID, ANCHOR_GID, 0o750)
        _make_private_directory(chroot_root / "run/witness-audit", PUBLISHER_UID, PUBLISHER_GID, 0o750)
        _make_private_directory(chroot_root / "var/lib/witness-audit-anchor", ANCHOR_UID, ANCHOR_GID)
        publisher_root = chroot_root / "var/lib/witness-audit-publisher"
        _make_private_directory(publisher_root, PUBLISHER_UID, PUBLISHER_GID)
        for child_name in ("segments", "checkpoints", "index", "recovery"):
            _make_private_directory(publisher_root / child_name, PUBLISHER_UID, PUBLISHER_GID)

        anchor_socket = pathlib.Path("/run/witness-audit-anchor/anchor.sock")
        publisher_socket = pathlib.Path("/run/witness-audit/publisher.sock")
        anchor_namespace = "cache:audit:namespace:integration"
        segment_id = "cache:audit:segment:integration:0001"
        genesis = authority.sign_record({
            "schema_version": "cache_audit_genesis_authorization/v1",
            "authorization_id": "cache:audit:genesis:integration",
            "segment_id": segment_id,
            "anchor_namespace": anchor_namespace,
            "audit_signing_registry_shake256_512": record_registry_sha,
            "anchor_registry_shake256_512": anchor_registry_sha,
            "decision": "authorize_audit_genesis",
            "created_at": "2026-08-02T00:00:00Z",
        }, material["governance"])

        # Anchor service: UID/GID 65532, accepts only the authenticated publisher.
        anchor_r, anchor_w = os.pipe()
        anchor_pid = os.fork()
        if anchor_pid == 0:
            os.close(anchor_r)
            try:
                os.chroot(chroot_root); os.chdir("/")
                os.setgroups([]); os.setgid(ANCHOR_GID); os.setuid(ANCHOR_UID)
                store = FileBackedMonotonicAnchorStore(
                    pathlib.Path("/var/lib/witness-audit-anchor/anchor.jsonl"), material["anchor_key"],
                    key_id=material["anchor_record"]["key_id"],
                    signer_principal_id=material["anchor_record"]["principal_id"],
                    anchor_registry_shake256_512=anchor_registry_sha, anchor_registry_records=anchor_records,
                    schema_validator=validator, provision=True, expected_uid=ANCHOR_UID,
                )
                server = AuditAnchorServer(
                    anchor_socket, store, schema_validator=validator,
                    publisher_uid=PUBLISHER_UID, publisher_gid=PUBLISHER_GID,
                    publisher_principal_id="cache:audit:publisher:integration",
                    request_verification_keys={"cache:audit:publisher-request:key:integration": material["publisher_request_key"].public_key()},
                    socket_uid=ANCHOR_UID, socket_gid=ANCHOR_GID,
                )
                os.write(anchor_w, b"ready\n"); os.close(anchor_w)
                server.server.serve_forever(poll_interval=0.05)
                os._exit(0)
            except BaseException:
                os.write(anchor_w, traceback.format_exc().encode("utf-8", errors="replace")); os.close(anchor_w)
                os._exit(1)
        os.close(anchor_w)
        _read_ready(anchor_r, anchor_pid, "anchor service")

        def start_publisher(*, provision: bool) -> int:
            ready_r, ready_w = os.pipe()
            child = os.fork()
            if child == 0:
                os.close(ready_r)
                try:
                    os.chroot(chroot_root); os.chdir("/")
                    os.setgroups([ANCHOR_GID]); os.setgid(PUBLISHER_GID); os.setuid(PUBLISHER_UID)
                    anchor_client = UnixSocketAuditAnchorClient(
                        anchor_socket, anchor_namespace=anchor_namespace,
                        verification_keys_by_id=anchor_keys, anchor_registry_shake256_512=anchor_registry_sha,
                        anchor_registry_records=anchor_records, schema_validator=validator,
                        request_signing_key=material["publisher_request_key"],
                        request_signer_key_id="cache:audit:publisher-request:key:integration",
                        peer_principal_id="cache:audit:publisher:integration",
                        expected_socket_uid=ANCHOR_UID, expected_socket_gid=ANCHOR_GID,
                        expected_socket_mode=0o660,
                    )
                    sink = SignedAppendOnlyAuditSink(
                        pathlib.Path("/var/lib/witness-audit-publisher/segments/segment-0001.jsonl"),
                        pathlib.Path("/var/lib/witness-audit-publisher/checkpoints/segment-0001.checkpoint.json"),
                        material["record_key"], record_keys,
                        segment_id=segment_id,
                        signer_principal_id=material["record_record"]["principal_id"],
                        signer_key_id=material["record_record"]["key_id"],
                        audit_signing_registry_shake256_512=record_registry_sha,
                        audit_registry_records=record_records, schema_validator=validator,
                        maximum_record_bytes=65536, maximum_log_bytes=4 * 1024 * 1024,
                        maximum_event_records=32, terminal_seal_reserved_bytes=65536,
                        anchor_client=anchor_client, anchor_namespace=anchor_namespace,
                        anchor_registry_shake256_512=anchor_registry_sha,
                        provision=provision, governance_key=governance_key,
                        genesis_authorization=genesis if provision else None,
                        storage_root=pathlib.Path("/var/lib/witness-audit-publisher"),
                        expected_uid=PUBLISHER_UID,
                        recovery_consumed_ledger_path=pathlib.Path("/var/lib/witness-audit-publisher/recovery/consumed.jsonl"),
                    )
                    index = DurableEventIdIndex(
                        pathlib.Path("/var/lib/witness-audit-publisher/index/events.sqlite"),
                        expected_uid=PUBLISHER_UID,
                    )
                    publisher = AuditPublisherServer(
                        publisher_socket, lambda: sink,
                        receipt_signing_key=material["receipt_key"],
                        receipt_key_id=material["receipt_record"]["key_id"],
                        receipt_signer_principal_id=material["receipt_record"]["principal_id"],
                        receipt_signing_registry_shake256_512=receipt_registry_sha,
                        receipt_registry_records=receipt_records,
                        schema_validator=validator, event_index=index,
                        proof_service_uid=SERVICE_UID, proof_service_gid=SERVICE_GID,
                        proof_service_principal_id="cache:audit:proof-service:integration",
                        request_verification_keys={"cache:audit:proof-request:key:integration": material["proof_request_key"].public_key()},
                        socket_uid=PUBLISHER_UID, socket_gid=PUBLISHER_GID,
                    )
                    os.write(ready_w, b"ready\n"); os.close(ready_w)
                    publisher.server.serve_forever(poll_interval=0.05)
                    os._exit(0)
                except BaseException:
                    os.write(ready_w, traceback.format_exc().encode("utf-8", errors="replace")); os.close(ready_w)
                    os._exit(1)
            os.close(ready_w)
            _read_ready(ready_r, child, "publisher service")
            return child

        publisher_pid = start_publisher(provision=True)
        try:
            event = json.loads((ROOT / "executable/tests/fixtures/draft5_3_15/valid/cache_verification_evidence_v1.json").read_text(encoding="utf-8"))["payload"]

            def proof_roundtrip() -> dict:
                read_fd, write_fd = os.pipe()
                child = os.fork()
                if child == 0:
                    os.close(read_fd)
                    try:
                        os.chroot(chroot_root); os.chdir("/")
                        os.setgroups([PUBLISHER_GID]); os.setgid(SERVICE_GID); os.setuid(SERVICE_UID)
                        config_root = pathlib.Path("/etc/witness-authority")
                        authority_service = authority.load_production_authority_service(config_root)
                        application = service.load_production_application(config_root)
                        first = application.cache_verification_evidence_sink(event, deadline_monotonic=time.monotonic() + 5.0)
                        second = application.cache_verification_evidence_sink(event, deadline_monotonic=time.monotonic() + 5.0)
                        database = config_root / "idempotency.sqlite"
                        result = {
                            "status": "passed", "authority_loader": "passed", "application_loader": "passed",
                            "effective_uid": os.geteuid(), "effective_gid": os.getegid(),
                            "authority_profile_count": len(authority_service.profiles),
                            "historical_registry_count": len(application.cache_registry_snapshots_by_shake256_512) - 1,
                            "first_receipt_decision": first["decision"],
                            "duplicate_receipt_decision": second["decision"],
                            "receipt_signature_verified": True,
                            "idempotency_sqlite_connection_mode": application.idempotency_store.connection_mode,
                            "sqlite_owner": database.stat().st_uid,
                            "sqlite_mode": oct(database.stat().st_mode & 0o777),
                        }
                        application.idempotency_store.close()
                        os.write(write_fd, authority.canonical_bytes(result)); os.close(write_fd); os._exit(0)
                    except BaseException:
                        os.write(write_fd, traceback.format_exc().encode("utf-8", errors="replace")); os.close(write_fd); os._exit(1)
                os.close(write_fd)
                chunks = []
                while True:
                    chunk = os.read(read_fd, 65536)
                    if not chunk: break
                    chunks.append(chunk)
                os.close(read_fd)
                waited, status = os.waitpid(child, 0)
                payload = b"".join(chunks)
                if waited != child or not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
                    raise RuntimeError("proof-service integration child failed:\n" + payload.decode("utf-8", errors="replace"))
                return authority.canonical_json_loads(payload.decode("utf-8"))

            first_run = proof_roundtrip()
            # Restart the publisher and prove global event-ID reconciliation survives.
            _stop_child(publisher_pid)
            publisher_pid = start_publisher(provision=False)
            restart_run = proof_roundtrip()

            # An unrelated UID with filesystem group access and even a copied request key
            # is rejected by SO_PEERCRED before publisher dispatch.
            denied_r, denied_w = os.pipe()
            denied_pid = os.fork()
            if denied_pid == 0:
                os.close(denied_r)
                try:
                    os.chroot(chroot_root); os.chdir("/")
                    os.setgroups([PUBLISHER_GID]); os.setgid(UNRELATED_GID); os.setuid(UNRELATED_UID)
                    client = UnixSocketAuditPublisherClient(
                        publisher_socket, verification_keys_by_id=receipt_keys,
                        receipt_signing_registry_shake256_512=receipt_registry_sha,
                        receipt_registry_records=receipt_records, schema_validator=validator,
                        request_signing_key=material["proof_request_key"],
                        request_signer_key_id="cache:audit:proof-request:key:integration",
                        peer_principal_id="cache:audit:proof-service:integration",
                        expected_socket_uid=PUBLISHER_UID, expected_socket_gid=PUBLISHER_GID,
                        expected_socket_mode=0o660,
                    )
                    client(event, deadline_monotonic=time.monotonic() + 3.0)
                    os.write(denied_w, b"unexpected_accept"); os._exit(1)
                except Exception as error:
                    os.write(denied_w, ("denied:" + str(error)).encode("utf-8", errors="replace")); os._exit(0)
            os.close(denied_w)
            denied_payload = os.read(denied_r, 65536).decode("utf-8", errors="replace")
            os.close(denied_r)
            _waited, denied_status = os.waitpid(denied_pid, 0)
            if not os.WIFEXITED(denied_status) or os.WEXITSTATUS(denied_status) != 0 or not denied_payload.startswith("denied:"):
                raise RuntimeError("unrelated UID was not rejected by the publisher")

            # Verify durable artifacts and anchor advancement after the service restart.
            ledger_lines = (chroot_root / "var/lib/witness-audit-anchor/anchor.jsonl").read_text(encoding="utf-8").splitlines()
            log_lines = (chroot_root / "var/lib/witness-audit-publisher/segments/segment-0001.jsonl").read_text(encoding="utf-8").splitlines()
            checkpoint = authority.canonical_json_loads((chroot_root / "var/lib/witness-audit-publisher/checkpoints/segment-0001.checkpoint.json").read_text(encoding="utf-8").rstrip("\n"))
            return {
                "schema_version": "production_loader_integration_evidence/v1",
                "package_version": "v1.6-draft-5.3.16",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "execution_model": "three_identity_chroot_so_peercred_signed_requests_real_publisher_anchor_round_trip",
                "configuration_path": "/etc/witness-authority",
                **first_run,
                "restart_application_loader": restart_run["application_loader"],
                "restart_duplicate_receipt_decision": restart_run["first_receipt_decision"],
                "proof_service_uid": SERVICE_UID, "publisher_uid": PUBLISHER_UID, "anchor_uid": ANCHOR_UID,
                "publisher_socket_mode": "0660", "anchor_socket_mode": "0660",
                "unrelated_uid_denied": True, "unrelated_uid": UNRELATED_UID,
                "publisher_server_started": True, "anchor_server_started": True,
                "publication_round_trip_executed": True, "durable_record_count": len(log_lines),
                "anchor_state_count": len(ledger_lines), "anchor_advanced": len(ledger_lines) >= 2,
                "checkpoint_sequence": checkpoint["sequence"],
                "global_event_idempotency_survived_restart": restart_run["first_receipt_decision"] == "already_committed",
                "file_anchor_authoritative": False,
                "activation_anchor_requirement": "external_monotonic_backend_required",
                "root_execution_rejection_retained": True,
            }
        finally:
            _stop_child(publisher_pid)
            _stop_child(anchor_pid)


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
                "package_version": "v1.6-draft-5.3.15",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "execution_model": "chroot_then_setgid_setuid_actual_loaders_private_parent_sqlite",
                "configuration_path": "/etc/witness-authority",
                "authority_loader": "not_executed", "application_loader": "not_executed",
                "status": "environment_unavailable", "reason": str(error),
                "environment_probe": capability,
            }
    else:
        evidence = {
            "schema_version": "production_loader_integration_evidence/v1",
            "package_version": "v1.6-draft-5.3.15",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "execution_model": "chroot_then_setgid_setuid_actual_loaders_private_parent_sqlite",
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
