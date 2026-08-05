#!/usr/bin/env python3
"""Authenticated, cache-verifying proof-check boundary for Draft 5.3.9."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import stat
import threading
import time
import uuid
from contextlib import closing
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from proof_authority import (
    AuthorityFailure, CanonicalSchemaValidator, ProofAuthorityService, ProofPolicyResolver,
    _private_key_from_bytes, _public_key_from_bytes, _safe_relative_path, canonical_bytes,
    canonical_json_loads, public_key_raw_b64url,
    load_production_authority_service, secure_read_bytes, sha256_bytes, sign_record,
    validate_trusted_root_ancestry, verify_record,
)


IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class DurableIdempotencyStore:
    """Principal-scoped SQLite cache with bounded leases and untrusted rows."""

    SCHEMA_VERSION = 1
    TABLE = "proof_check_idempotency"
    INDEXES = {"proof_check_idempotency_completed", "proof_check_idempotency_state_lease"}

    def __init__(
        self, path: Path, *, retention_seconds: int = 7 * 24 * 3600,
        lease_seconds: int = 30 * 60, maximum_completed_rows: int = 10000,
        maximum_inflight_rows: int = 1000, maximum_inflight_rows_per_principal: int = 16,
        maximum_total_rows: int = 11000, maximum_database_bytes: int = 128 * 1024 * 1024,
        maximum_cache_envelope_bytes: int | None = None,
        expected_uid: int | None = None,
    ):
        self.path = Path(path)
        self.expected_uid = os.getuid() if expected_uid is None else expected_uid
        bounds = (
            retention_seconds, lease_seconds, maximum_completed_rows, maximum_inflight_rows,
            maximum_inflight_rows_per_principal, maximum_total_rows, maximum_database_bytes,
        )
        if not self.path.is_absolute():
            raise ValueError("idempotency database path must be absolute")
        if min(bounds) <= 0 or maximum_total_rows < maximum_completed_rows:
            raise ValueError("idempotency retention, lease, row, and byte bounds must be positive and coherent")
        self.retention_seconds = retention_seconds
        self.lease_seconds = lease_seconds
        self.maximum_completed_rows = maximum_completed_rows
        self.maximum_inflight_rows = maximum_inflight_rows
        self.maximum_inflight_rows_per_principal = maximum_inflight_rows_per_principal
        self.maximum_total_rows = maximum_total_rows
        self.maximum_database_bytes = maximum_database_bytes
        if maximum_cache_envelope_bytes is None:
            maximum_cache_envelope_bytes = min(4 * 1024 * 1024, max(1024, (maximum_database_bytes - 65536) // 4))
        if maximum_cache_envelope_bytes <= 0:
            raise ValueError("cache-envelope byte limit must be positive")
        self.maximum_cache_envelope_bytes = maximum_cache_envelope_bytes
        self._initialized = False
        self._prepare_secure_path()
        with closing(self._connect()) as connection:
            existing_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if existing_version not in {0, self.SCHEMA_VERSION}:
                raise RuntimeError("unsupported idempotency SQLite schema version")
            connection.executescript(
                """
                PRAGMA journal_mode=WAL;
                PRAGMA synchronous=FULL;
                CREATE TABLE IF NOT EXISTS proof_check_idempotency (
                    principal_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    request_sha256 TEXT NOT NULL,
                    state TEXT NOT NULL CHECK (state IN ('inflight','completed')),
                    lease_owner TEXT,
                    lease_expires_at REAL,
                    result_canonical_json TEXT,
                    created_at REAL NOT NULL,
                    completed_at REAL,
                    PRIMARY KEY (principal_id, idempotency_key)
                );
                CREATE INDEX IF NOT EXISTS proof_check_idempotency_completed
                    ON proof_check_idempotency(state, completed_at);
                CREATE INDEX IF NOT EXISTS proof_check_idempotency_state_lease
                    ON proof_check_idempotency(state, lease_expires_at);
                """
            )
            connection.execute(f"PRAGMA user_version={self.SCHEMA_VERSION}")
            self._verify_sqlite_schema(connection)
        self._initialized = True
        self._secure_database_files()

    def _prepare_secure_path(self) -> None:
        parent = self.path.parent
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        current_fd = os.open(parent.anchor, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0))
        try:
            for part in parent.parts[1:]:
                next_fd = os.open(part, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0), dir_fd=current_fd)
                component = os.fstat(next_fd)
                if not stat.S_ISDIR(component.st_mode):
                    os.close(next_fd)
                    raise RuntimeError("idempotency database ancestry contains an unsafe component")
                writable = component.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
                sticky_root = component.st_uid == 0 and bool(component.st_mode & stat.S_ISVTX)
                if writable and not sticky_root:
                    os.close(next_fd)
                    raise RuntimeError("idempotency database ancestry is group/world writable")
                os.close(current_fd)
                current_fd = next_fd
            self._directory_fd = current_fd
            current_fd = -1
        finally:
            if current_fd >= 0:
                os.close(current_fd)
        info = os.fstat(self._directory_fd)
        if info.st_uid != self.expected_uid or info.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
            self.close()
            raise RuntimeError("idempotency parent ownership or mode is unsafe")
        try:
            os.stat(self.path.name, dir_fd=self._directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            try:
                descriptor = os.open(
                    self.path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                    0o600, dir_fd=self._directory_fd,
                )
            except Exception:
                self.close()
                raise
            else:
                os.close(descriptor)
        self._secure_database_files()

    def _secure_database_files(self) -> None:
        names = (self.path.name, self.path.name + "-wal", self.path.name + "-shm")
        directory_fd = getattr(self, "_directory_fd", None)
        for name in names:
            try:
                info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False) if directory_fd is not None else (self.path.parent / name).lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise RuntimeError(f"unsafe SQLite file identity: {name}")
            if info.st_uid != self.expected_uid:
                raise RuntimeError(f"unsafe SQLite file owner: {name}")
            if stat.S_IMODE(info.st_mode) != 0o600:
                os.chmod(name, 0o600, dir_fd=directory_fd, follow_symlinks=False)

    def _database_size(self) -> int:
        total = 0
        for name in (self.path.name, self.path.name + "-wal", self.path.name + "-shm"):
            try:
                total += os.stat(name, dir_fd=self._directory_fd, follow_symlinks=False).st_size
            except FileNotFoundError:
                pass
        return total

    def _connect(self) -> sqlite3.Connection:
        self._secure_database_files()
        target = f"/proc/self/fd/{self._directory_fd}/{self.path.name}"
        connection = sqlite3.connect(target, timeout=30, isolation_level=None)
        connection.execute("PRAGMA busy_timeout=30000")
        self._secure_database_files()
        if self._initialized:
            self._verify_sqlite_schema(connection)
        return connection

    def _verify_sqlite_schema(self, connection: sqlite3.Connection) -> None:
        quick_check = connection.execute("PRAGMA quick_check").fetchone()
        if quick_check != ("ok",):
            raise RuntimeError("idempotency SQLite integrity check failed")
        if int(connection.execute("PRAGMA user_version").fetchone()[0]) != self.SCHEMA_VERSION:
            raise RuntimeError("idempotency SQLite schema version mismatch")
        objects = connection.execute(
            "SELECT type,name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
        ).fetchall()
        expected = sorted([("table", self.TABLE), *(("index", name) for name in self.INDEXES)])
        if objects != expected:
            raise RuntimeError("idempotency SQLite schema contains unexpected or missing objects")
        columns = [row[1] for row in connection.execute(f"PRAGMA table_info({self.TABLE})")]
        if columns != [
            "principal_id", "idempotency_key", "request_sha256", "state", "lease_owner",
            "lease_expires_at", "result_canonical_json", "created_at", "completed_at",
        ]:
            raise RuntimeError("idempotency SQLite table layout mismatch")

    def close(self) -> None:
        descriptor = getattr(self, "_directory_fd", None)
        if descriptor is not None:
            os.close(descriptor)
            self._directory_fd = None

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    @staticmethod
    def _rollback(connection: sqlite3.Connection) -> None:
        if connection.in_transaction:
            connection.execute("ROLLBACK")

    def acquire(self, principal_id: str, key: str, request_sha256: str) -> tuple[str, str | dict[str, Any] | None]:
        now = time.time()
        owner = uuid.uuid4().hex
        with closing(self._connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "DELETE FROM proof_check_idempotency WHERE state='completed' AND completed_at < ?",
                    (now - self.retention_seconds,),
                )
                connection.execute(
                    "DELETE FROM proof_check_idempotency WHERE state='inflight' AND lease_expires_at IS NOT NULL AND lease_expires_at <= ?",
                    (now,),
                )
                excess = connection.execute(
                    "SELECT max(count(*) - ?, 0) FROM proof_check_idempotency WHERE state='completed'",
                    (self.maximum_completed_rows,),
                ).fetchone()[0]
                if excess:
                    connection.execute(
                        "DELETE FROM proof_check_idempotency WHERE rowid IN (SELECT rowid FROM proof_check_idempotency WHERE state='completed' ORDER BY completed_at ASC LIMIT ?)",
                        (excess,),
                    )
                row = connection.execute(
                    "SELECT request_sha256,state,lease_expires_at,result_canonical_json FROM proof_check_idempotency WHERE principal_id=? AND idempotency_key=?",
                    (principal_id, key),
                ).fetchone()
                if row is None:
                    total_rows = connection.execute("SELECT count(*) FROM proof_check_idempotency").fetchone()[0]
                    inflight_rows = connection.execute("SELECT count(*) FROM proof_check_idempotency WHERE state='inflight'").fetchone()[0]
                    principal_inflight = connection.execute(
                        "SELECT count(*) FROM proof_check_idempotency WHERE state='inflight' AND principal_id=?", (principal_id,),
                    ).fetchone()[0]
                    if total_rows >= self.maximum_total_rows:
                        raise RuntimeError("idempotency total-row admission limit reached")
                    if inflight_rows >= self.maximum_inflight_rows or principal_inflight >= self.maximum_inflight_rows_per_principal:
                        raise RuntimeError("idempotency in-flight admission limit reached")
                    if self._database_size() >= self.maximum_database_bytes:
                        raise RuntimeError("idempotency database byte admission limit reached")
                    connection.execute(
                        "INSERT INTO proof_check_idempotency VALUES (?,?,?,?,?,?,?,?,?)",
                        (principal_id, key, request_sha256, "inflight", owner, now + self.lease_seconds, None, now, None),
                    )
                    connection.execute("COMMIT")
                    return "execute", owner
                prior_hash, state, _lease_expires_at, result_json = row
                if prior_hash != request_sha256:
                    raise ValueError("principal-scoped idempotency key was used for a different request")
                if state == "completed":
                    connection.execute("COMMIT")
                    try:
                        parsed = canonical_json_loads(result_json)
                    except (TypeError, ValueError) as error:
                        raise RuntimeError("completed idempotency row is not canonical duplicate-free JSON") from error
                    return "completed", parsed
                connection.execute("COMMIT")
                return "wait", None
            except Exception:
                self._rollback(connection)
                raise
            finally:
                self._secure_database_files()

    def complete(self, principal_id: str, key: str, owner: str, request_sha256: str, envelope: dict[str, Any]) -> None:
        canonical_result = canonical_bytes(envelope).decode("utf-8")
        encoded_size = len(canonical_result.encode("utf-8"))
        if encoded_size > self.maximum_cache_envelope_bytes:
            raise RuntimeError("idempotency cache envelope byte limit exceeded")
        if self._database_size() + 2 * encoded_size + 65536 >= self.maximum_database_bytes:
            raise RuntimeError("idempotency database completion byte limit exceeded")
        now = time.time()
        with closing(self._connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                changed = connection.execute(
                    "UPDATE proof_check_idempotency SET state='completed',lease_owner=NULL,lease_expires_at=NULL,result_canonical_json=?,completed_at=? WHERE principal_id=? AND idempotency_key=? AND request_sha256=? AND state='inflight' AND lease_owner=? AND lease_expires_at>?",
                    (canonical_result, now, principal_id, key, request_sha256, owner, now),
                ).rowcount
                if changed != 1:
                    raise RuntimeError("idempotency completion lease was lost")
                connection.execute("COMMIT")
                connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                if self._database_size() > self.maximum_database_bytes:
                    connection.execute("BEGIN IMMEDIATE")
                    connection.execute(
                        "DELETE FROM proof_check_idempotency WHERE principal_id=? AND idempotency_key=? AND state='completed' AND request_sha256=?",
                        (principal_id, key, request_sha256),
                    )
                    connection.execute("COMMIT")
                    connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    raise RuntimeError("idempotency database exceeded its byte limit during completion")
            except Exception:
                self._rollback(connection)
                raise
            finally:
                self._secure_database_files()

    def renew(self, principal_id: str, key: str, owner: str, request_sha256: str) -> bool:
        """Atomically extend only the live lease owned by this exact worker."""
        now = time.time()
        with closing(self._connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                changed = connection.execute(
                    "UPDATE proof_check_idempotency SET lease_expires_at=? WHERE principal_id=? AND idempotency_key=? AND request_sha256=? AND state='inflight' AND lease_owner=? AND lease_expires_at>?",
                    (now + self.lease_seconds, principal_id, key, request_sha256, owner, now),
                ).rowcount
                connection.execute("COMMIT")
                return changed == 1
            except Exception:
                self._rollback(connection)
                raise
            finally:
                self._secure_database_files()

    def abandon(self, principal_id: str, key: str, owner: str) -> None:
        with closing(self._connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "DELETE FROM proof_check_idempotency WHERE principal_id=? AND idempotency_key=? AND state='inflight' AND lease_owner=?",
                    (principal_id, key, owner),
                )
                connection.execute("COMMIT")
            except Exception:
                self._rollback(connection)
                raise
            finally:
                self._secure_database_files()


class ProofCheckApplication:
    def __init__(
        self, authority: ProofAuthorityService, artifact_store: Path,
        policy_resolver: ProofPolicyResolver, *,
        idempotency_store: DurableIdempotencyStore | None = None,
        schema_validator: CanonicalSchemaValidator | None = None,
        cache_signing_key: Ed25519PrivateKey | None = None,
        cache_verification_key: Ed25519PublicKey | None = None,
        compiler_witness_verification_key: Ed25519PublicKey | None = None,
        cache_signer_principal_id: str = "cache-signer:development",
        cache_signer_key_id: str = "cache-key:development",
        production_mode: bool = False,
    ):
        self.authority = authority
        self.artifact_store = artifact_store.resolve()
        self.policy_resolver = policy_resolver
        self.schema_validator = schema_validator or CanonicalSchemaValidator(Path(__file__).resolve().parents[2] / "schemas")
        self.idempotency_store = idempotency_store or DurableIdempotencyStore((self.artifact_store / ".proof-check-idempotency.sqlite").resolve())
        authority_signing_key = getattr(authority, "signing_key", None)
        if cache_signing_key is None:
            if production_mode:
                raise ValueError("production requires a distinct protected idempotency-cache signing key")
            cache_signing_key = Ed25519PrivateKey.generate()
        self.cache_signing_key = cache_signing_key
        self.cache_verification_key = cache_verification_key or self.cache_signing_key.public_key()
        self.compiler_witness_verification_key = compiler_witness_verification_key or (
            authority_signing_key.public_key() if authority_signing_key is not None else None
        )
        if self.compiler_witness_verification_key is None:
            raise ValueError("an authorized compiler-witness verification key is required")
        self.authority_key_id = str(getattr(authority, "key_id", ""))
        self.authority_principal_id = str(getattr(authority, "verifier_principal_id", ""))
        if not self.authority_key_id or not self.authority_principal_id:
            raise ValueError("authorized compiler-witness signer identity is required")
        self.cache_signer_key_id = self._principal(cache_signer_key_id)
        self.cache_signer_principal_id = self._principal(cache_signer_principal_id)
        if (
            self.cache_signer_key_id == self.authority_key_id
            or self.cache_signer_principal_id == self.authority_principal_id
            or public_key_raw_b64url(self.cache_verification_key) == public_key_raw_b64url(self.compiler_witness_verification_key)
        ):
            raise ValueError("cache and compiler-witness signing authorities must be distinct")

    @staticmethod
    def _principal(value: str) -> str:
        if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
            raise ValueError("trusted authentication middleware did not supply a canonical principal")
        return value

    def _resolve_policy(self, request: dict[str, Any], principal_id: str):
        return self.policy_resolver.resolve(
            request["policy_decision_id"], subject_id=principal_id,
            operation="proof_check", compiler_profile_id=request["compiler_profile_id"],
            source_bundle_id=request["source_bundle_id"],
        )

    def _validate_result_bindings(
        self, result: dict[str, Any], request: dict[str, Any], principal_id: str,
        request_sha256: str, resolved_policy,
    ) -> None:
        self.schema_validator.validate("proof_check_result", result)
        witness = result.get("compiler_witness")
        self.schema_validator.validate("compiler_witness", witness)
        if not verify_record(witness, self.compiler_witness_verification_key):
            raise AuthorityFailure("cache_integrity_invalid", "compiler-witness signature or signed payload is invalid")
        if witness.get("key_id") != self.authority_key_id or witness.get("verifier_principal_id") != self.authority_principal_id:
            raise AuthorityFailure("cache_integrity_invalid", "compiler-witness signer is not authorized")
        claim_hash = sha256_bytes(canonical_bytes(request["canonical_claim"]))
        theorem_hash = sha256_bytes(request["theorem_statement"].encode("utf-8"))
        exact_result = {
            "request_id": request["request_id"], "request_sha256": request_sha256,
            "idempotency_key": request["idempotency_key"], "authenticated_principal_id": principal_id,
            "claim_id": request["claim_id"], "claim_content_sha256": claim_hash,
            "theorem_statement_sha256": theorem_hash, "compiler_profile_id": request["compiler_profile_id"],
            "policy_decision_id": resolved_policy.policy_decision_id,
            "policy_decision_sha256": resolved_policy.canonical_record_sha256,
            "source_bundle_id": request["source_bundle_id"],
            "proof_artifact_relative_path": request["proof_artifact_relative_path"],
        }
        if any(result.get(key) != value for key, value in exact_result.items()):
            raise AuthorityFailure("cache_integrity_invalid", "cached outer result differs from the current authenticated request")
        exact_witness = {
            "service_request_id": request["request_id"], "authenticated_principal_id": principal_id,
            "source_bundle_id": request["source_bundle_id"], "claim_id": request["claim_id"],
            "claim_content_sha256": claim_hash, "theorem_statement_sha256": theorem_hash,
            "compiler_profile_id": request["compiler_profile_id"],
            "policy_decision_id": resolved_policy.policy_decision_id,
            "policy_decision_sha256": resolved_policy.canonical_record_sha256,
            "proof_artifact_relative_path": request["proof_artifact_relative_path"],
        }
        if any(witness.get(key) != value for key, value in exact_witness.items()):
            raise AuthorityFailure("cache_integrity_invalid", "cached compiler witness differs from the current authenticated request")
        if result.get("status") != witness.get("result"):
            raise AuthorityFailure("cache_integrity_invalid", "outer result status differs from the signed compiler witness")

    def _cache_envelope(self, result: dict[str, Any], request: dict[str, Any], principal_id: str, request_sha256: str) -> dict[str, Any]:
        identity = {
            "request_sha256": request_sha256, "authenticated_principal_id": principal_id,
            "compiler_witness_signed_payload_sha256": result["compiler_witness"]["signed_payload_sha256"],
        }
        unsigned = {
            "schema_version": "idempotency_cache_envelope/v1",
            "cache_envelope_id": "cache:" + sha256_bytes(canonical_bytes(identity)),
            "request_sha256": request_sha256, "request_id": request["request_id"],
            "idempotency_key": request["idempotency_key"], "authenticated_principal_id": principal_id,
            "claim_id": request["claim_id"], "compiler_profile_id": request["compiler_profile_id"],
            "policy_decision_id": result["policy_decision_id"],
            "policy_decision_sha256": result["policy_decision_sha256"],
            "source_bundle_id": request["source_bundle_id"],
            "cache_signer_principal_id": self.cache_signer_principal_id,
            "cache_signer_key_id": self.cache_signer_key_id,
            "result": result,
        }
        envelope = sign_record(unsigned, self.cache_signing_key)
        self.schema_validator.validate("idempotency_cache_envelope", envelope)
        return envelope

    def _cached_result(
        self, envelope: dict[str, Any], request: dict[str, Any], principal_id: str,
        request_sha256: str, resolved_policy,
    ) -> dict[str, Any]:
        self.schema_validator.validate("idempotency_cache_envelope", envelope)
        if not verify_record(envelope, self.cache_verification_key):
            raise AuthorityFailure("cache_integrity_invalid", "idempotency-cache envelope signature is invalid")
        expected = {
            "request_sha256": request_sha256, "request_id": request["request_id"],
            "idempotency_key": request["idempotency_key"], "authenticated_principal_id": principal_id,
            "claim_id": request["claim_id"], "compiler_profile_id": request["compiler_profile_id"],
            "policy_decision_id": resolved_policy.policy_decision_id,
            "policy_decision_sha256": resolved_policy.canonical_record_sha256,
            "source_bundle_id": request["source_bundle_id"],
            "cache_signer_principal_id": self.cache_signer_principal_id,
            "cache_signer_key_id": self.cache_signer_key_id,
        }
        if any(envelope.get(key) != value for key, value in expected.items()):
            raise AuthorityFailure("cache_integrity_invalid", "idempotency-cache envelope binding mismatch")
        result = envelope["result"]
        self._validate_result_bindings(result, request, principal_id, request_sha256, resolved_policy)
        return json.loads(json.dumps(result))

    def handle(self, request: dict[str, Any], *, authenticated_principal_id: str) -> dict[str, Any]:
        principal_id = self._principal(authenticated_principal_id)
        try:
            self.schema_validator.validate("proof_check_request", request)
        except AuthorityFailure as error:
            raise ValueError(str(error)) from error
        request_sha256 = sha256_bytes(canonical_bytes(request))
        idempotency_key = request["idempotency_key"]
        resolved_policy = self._resolve_policy(request, principal_id)
        limits = resolved_policy.effective_limits()
        deadline = time.monotonic() + limits.timeout_seconds
        owner: str | None = None
        while owner is None:
            action, value = self.idempotency_store.acquire(principal_id, idempotency_key, request_sha256)
            if action == "completed":
                assert isinstance(value, dict)
                return self._cached_result(value, request, principal_id, request_sha256, resolved_policy)
            if action == "execute":
                owner = str(value)
                break
            if time.monotonic() >= deadline:
                raise TimeoutError("timed out waiting for an in-flight idempotent request")
            time.sleep(0.05)
        stop_heartbeat = threading.Event()
        lease_lost = threading.Event()

        def renew_lease() -> None:
            interval = max(0.05, min(30.0, self.idempotency_store.lease_seconds / 3.0))
            while not stop_heartbeat.wait(interval):
                try:
                    if not self.idempotency_store.renew(principal_id, idempotency_key, owner, request_sha256):
                        lease_lost.set()
                        return
                except Exception:
                    lease_lost.set()
                    return

        heartbeat = threading.Thread(target=renew_lease, name="idempotency-lease-renewal", daemon=True)
        heartbeat.start()
        try:
            bundle_id = request["source_bundle_id"]
            relative = _safe_relative_path(request["proof_artifact_relative_path"], expected_suffix=".lean")
            source_root = (self.artifact_store / bundle_id).resolve()
            source_root.relative_to(self.artifact_store)
            artifact = source_root.joinpath(*relative.parts).resolve()
            artifact.relative_to(source_root)
            compiler_witness = self.authority.verify(
                compiler_profile_id=request["compiler_profile_id"], claim_id=request["claim_id"],
                canonical_claim=request["canonical_claim"], theorem_statement=request["theorem_statement"],
                theorem_name=request["theorem_name"], proof_artifact=artifact, source_root=source_root,
                service_request_id=request["request_id"], authenticated_principal_id=principal_id,
                source_bundle_id=bundle_id, policy_decision_id=resolved_policy.policy_decision_id,
                policy_decision_sha256=resolved_policy.canonical_record_sha256,
                timeout_seconds=limits.timeout_seconds, effective_resource_limits=limits,
                request_deadline_monotonic=deadline,
            )
            self.schema_validator.validate("compiler_witness", compiler_witness)
            result = {
                "schema_version": "proof_check_service_result/v6",
                "request_id": request["request_id"], "request_sha256": request_sha256,
                "idempotency_key": idempotency_key, "authenticated_principal_id": principal_id,
                "status": compiler_witness["result"], "claim_id": request["claim_id"],
                "claim_content_sha256": sha256_bytes(canonical_bytes(request["canonical_claim"])),
                "theorem_statement_sha256": sha256_bytes(request["theorem_statement"].encode("utf-8")),
                "compiler_profile_id": request["compiler_profile_id"],
                "policy_decision_id": resolved_policy.policy_decision_id,
                "policy_decision_sha256": resolved_policy.canonical_record_sha256,
                "source_bundle_id": bundle_id,
                "proof_artifact_relative_path": relative.as_posix(),
                "compiler_witness": compiler_witness,
            }
            self._validate_result_bindings(result, request, principal_id, request_sha256, resolved_policy)
            envelope = self._cache_envelope(result, request, principal_id, request_sha256)
            stop_heartbeat.set()
            heartbeat.join(timeout=2)
            if lease_lost.is_set() or not self.idempotency_store.renew(principal_id, idempotency_key, owner, request_sha256):
                raise RuntimeError("idempotency execution lease was lost before publication")
            self.idempotency_store.complete(principal_id, idempotency_key, owner, request_sha256, envelope)
            return json.loads(json.dumps(result))
        except Exception:
            stop_heartbeat.set()
            heartbeat.join(timeout=2)
            self.idempotency_store.abandon(principal_id, idempotency_key, owner)
            raise


def load_production_application(config_root: Path = Path("/etc/witness-authority")) -> ProofCheckApplication:
    validate_trusted_root_ancestry(config_root, expected_uid=os.getuid())
    config = json.loads(secure_read_bytes(config_root, "service-config.json", expected_uid=os.getuid()).decode("utf-8"))
    artifact_store = Path(config["artifact_store_root"])
    if not artifact_store.is_absolute() or not artifact_store.is_dir() or artifact_store.is_symlink():
        raise RuntimeError("artifact store must be an absolute non-symlink directory")
    governance_key = _public_key_from_bytes(secure_read_bytes(config_root, config["governance_public_key_file"], expected_uid=os.getuid()))
    policy_registry = json.loads(secure_read_bytes(config_root, config["policy_registry_file"], expected_uid=os.getuid()).decode("utf-8"))
    schema_relative = _safe_relative_path(config["schema_root"])
    schemas = config_root.joinpath(*schema_relative.parts)
    validate_trusted_root_ancestry(schemas, expected_uid=os.getuid())
    validator = CanonicalSchemaValidator(schemas)
    validator.validate("proof_policy_registry", policy_registry)
    authority = load_production_authority_service(config_root)
    store = DurableIdempotencyStore(
        Path(config["idempotency_database"]),
        retention_seconds=int(config["idempotency_retention_seconds"]),
        lease_seconds=int(config["idempotency_lease_seconds"]),
        maximum_completed_rows=int(config["idempotency_maximum_completed_rows"]),
        maximum_inflight_rows=int(config["idempotency_maximum_inflight_rows"]),
        maximum_inflight_rows_per_principal=int(config["idempotency_maximum_inflight_rows_per_principal"]),
        maximum_total_rows=int(config["idempotency_maximum_total_rows"]),
        maximum_database_bytes=int(config["idempotency_maximum_database_bytes"]),
        maximum_cache_envelope_bytes=int(config["idempotency_maximum_cache_envelope_bytes"]),
    )
    cache_signing_key = _private_key_from_bytes(
        secure_read_bytes(config_root, config["cache_private_key_file"], expected_uid=os.getuid())
    )
    cache_verification_key = _public_key_from_bytes(
        secure_read_bytes(config_root, config["cache_public_key_file"], expected_uid=os.getuid())
    )
    if public_key_raw_b64url(cache_signing_key.public_key()) != public_key_raw_b64url(cache_verification_key):
        raise RuntimeError("cache private and public keys do not form one Ed25519 keypair")
    cache_registry = canonical_json_loads(
        secure_read_bytes(config_root, config["cache_signing_registry_file"], expected_uid=os.getuid()).decode("utf-8")
    )
    validator.validate("cache_signing_registry", cache_registry)
    if not verify_record(cache_registry, governance_key):
        raise RuntimeError("cache-signing registry governance signature is invalid")
    matching_cache_keys = [
        key for key in cache_registry["keys"]
        if key["key_id"] == config["cache_signer_key_id"]
        and key["principal_id"] == config["cache_signer_principal_id"]
        and key["status"] == "active"
        and key["authorization_scope"] == "idempotency_cache_envelope_signing"
        and key["public_key_base64url"] == public_key_raw_b64url(cache_verification_key)
    ]
    if len(matching_cache_keys) != 1:
        raise RuntimeError("cache signing key lacks one active scoped registry authorization")
    return ProofCheckApplication(
        authority=authority, artifact_store=artifact_store,
        policy_resolver=ProofPolicyResolver(policy_registry, governance_key, schema_validator=validator),
        idempotency_store=store, schema_validator=validator,
        cache_signing_key=cache_signing_key, cache_verification_key=cache_verification_key,
        cache_signer_principal_id=config["cache_signer_principal_id"],
        cache_signer_key_id=config["cache_signer_key_id"], production_mode=True,
    )


__all__ = ["DurableIdempotencyStore", "ProofCheckApplication", "load_production_application"]
