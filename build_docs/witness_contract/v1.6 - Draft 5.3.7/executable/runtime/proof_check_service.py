#!/usr/bin/env python3
"""Schema-enforced synchronous proof-check boundary for Draft 5.3.7."""

from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from proof_authority import (
    AuthorityFailure, CanonicalSchemaValidator, ProofAuthorityService, ProofPolicyResolver,
    _public_key_from_bytes, _safe_relative_path, canonical_bytes,
    load_production_authority_service, secure_read_bytes, sha256_bytes,
    validate_trusted_root_ancestry,
)


class DurableIdempotencyStore:
    """Bounded principal-scoped SQLite idempotency with expiring leases."""

    def __init__(
        self, path: Path, *, retention_seconds: int = 7 * 24 * 3600,
        lease_seconds: int = 30 * 60, maximum_completed_rows: int = 10000,
    ):
        self.path = Path(path)
        if not self.path.is_absolute():
            raise ValueError("idempotency database path must be absolute")
        if min(retention_seconds, lease_seconds, maximum_completed_rows) <= 0:
            raise ValueError("idempotency retention, lease, and row bounds must be positive")
        self.retention_seconds = retention_seconds
        self.lease_seconds = lease_seconds
        self.maximum_completed_rows = maximum_completed_rows
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
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
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.execute("PRAGMA busy_timeout=30000")
        return connection

    def acquire(self, principal_id: str, key: str, request_sha256: str) -> tuple[str, str | dict[str, Any] | None]:
        now = time.time()
        owner = uuid.uuid4().hex
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "DELETE FROM proof_check_idempotency WHERE state='completed' AND completed_at < ?",
                (now - self.retention_seconds,),
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
                connection.execute(
                    "INSERT INTO proof_check_idempotency VALUES (?,?,?,?,?,?,?,?,?)",
                    (principal_id, key, request_sha256, "inflight", owner, now + self.lease_seconds, None, now, None),
                )
                connection.execute("COMMIT")
                return "execute", owner
            prior_hash, state, lease_expires_at, result_json = row
            if prior_hash != request_sha256:
                connection.execute("ROLLBACK")
                raise ValueError("principal-scoped idempotency key was used for a different request")
            if state == "completed":
                connection.execute("COMMIT")
                return "completed", json.loads(result_json)
            if lease_expires_at is None or lease_expires_at <= now:
                connection.execute(
                    "UPDATE proof_check_idempotency SET lease_owner=?,lease_expires_at=? WHERE principal_id=? AND idempotency_key=?",
                    (owner, now + self.lease_seconds, principal_id, key),
                )
                connection.execute("COMMIT")
                return "execute", owner
            connection.execute("COMMIT")
            return "wait", None

    def complete(self, principal_id: str, key: str, owner: str, request_sha256: str, result: dict[str, Any]) -> None:
        canonical_result = canonical_bytes(result).decode("utf-8")
        now = time.time()
        with self._connect() as connection:
            changed = connection.execute(
                "UPDATE proof_check_idempotency SET state='completed',lease_owner=NULL,lease_expires_at=NULL,result_canonical_json=?,completed_at=? WHERE principal_id=? AND idempotency_key=? AND request_sha256=? AND state='inflight' AND lease_owner=?",
                (canonical_result, now, principal_id, key, request_sha256, owner),
            ).rowcount
            if changed != 1:
                raise RuntimeError("idempotency completion lease was lost")

    def abandon(self, principal_id: str, key: str, owner: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM proof_check_idempotency WHERE principal_id=? AND idempotency_key=? AND state='inflight' AND lease_owner=?",
                (principal_id, key, owner),
            )


class ProofCheckApplication:
    def __init__(
        self, authority: ProofAuthorityService, artifact_store: Path,
        policy_resolver: ProofPolicyResolver, *,
        idempotency_store: DurableIdempotencyStore | None = None,
        schema_validator: CanonicalSchemaValidator | None = None,
    ):
        self.authority = authority
        self.artifact_store = artifact_store.resolve()
        self.policy_resolver = policy_resolver
        self.schema_validator = schema_validator or CanonicalSchemaValidator(Path(__file__).resolve().parents[2] / "schemas")
        self.idempotency_store = idempotency_store or DurableIdempotencyStore((self.artifact_store / ".proof-check-idempotency.sqlite").resolve())

    def handle(self, request: dict[str, Any]) -> dict[str, Any]:
        try:
            self.schema_validator.validate("proof_check_request", request)
        except AuthorityFailure as error:
            raise ValueError(str(error)) from error
        request_sha256 = sha256_bytes(canonical_bytes(request))
        principal_id = request["subject_id"]
        idempotency_key = request["idempotency_key"]
        deadline = time.monotonic() + 660
        owner: str | None = None
        while owner is None:
            action, value = self.idempotency_store.acquire(principal_id, idempotency_key, request_sha256)
            if action == "completed":
                assert isinstance(value, dict)
                self.schema_validator.validate("proof_check_result", value)
                return json.loads(json.dumps(value))
            if action == "execute":
                owner = str(value)
                break
            if time.monotonic() >= deadline:
                raise TimeoutError("timed out waiting for an in-flight idempotent request")
            time.sleep(0.05)
        try:
            bundle_id = request["source_bundle_id"]
            relative = _safe_relative_path(request["proof_artifact_relative_path"], expected_suffix=".lean")
            resolved_policy = self.policy_resolver.resolve(
                request["policy_decision_id"], subject_id=principal_id,
                operation="proof_check", compiler_profile_id=request["compiler_profile_id"],
                source_bundle_id=bundle_id,
            )
            limits = resolved_policy.effective_limits()
            source_root = (self.artifact_store / bundle_id).resolve()
            source_root.relative_to(self.artifact_store)
            artifact = source_root.joinpath(*relative.parts).resolve()
            artifact.relative_to(source_root)
            compiler_witness = self.authority.verify(
                compiler_profile_id=request["compiler_profile_id"], claim_id=request["claim_id"],
                canonical_claim=request["canonical_claim"], theorem_statement=request["theorem_statement"],
                theorem_name=request["theorem_name"], proof_artifact=artifact, source_root=source_root,
                policy_decision_id=resolved_policy.policy_decision_id,
                policy_decision_sha256=resolved_policy.canonical_record_sha256,
                timeout_seconds=limits.timeout_seconds, effective_resource_limits=limits,
            )
            self.schema_validator.validate("compiler_witness", compiler_witness)
            if compiler_witness.get("policy_decision_id") != resolved_policy.policy_decision_id or compiler_witness.get("policy_decision_sha256") != resolved_policy.canonical_record_sha256:
                raise RuntimeError("authority returned a different policy binding")
            result = {
                "schema_version": "proof_check_service_result/v5",
                "request_id": request["request_id"], "idempotency_key": idempotency_key,
                "status": compiler_witness["result"], "claim_id": request["claim_id"],
                "policy_decision_id": resolved_policy.policy_decision_id,
                "policy_decision_sha256": resolved_policy.canonical_record_sha256,
                "source_bundle_id": bundle_id, "compiler_witness": compiler_witness,
            }
            self.schema_validator.validate("proof_check_result", result)
            self.idempotency_store.complete(principal_id, idempotency_key, owner, request_sha256, result)
            return json.loads(json.dumps(result))
        except Exception:
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
    store = DurableIdempotencyStore(
        Path(config["idempotency_database"]),
        retention_seconds=int(config["idempotency_retention_seconds"]),
        lease_seconds=int(config["idempotency_lease_seconds"]),
        maximum_completed_rows=int(config["idempotency_maximum_completed_rows"]),
    )
    return ProofCheckApplication(
        authority=load_production_authority_service(config_root), artifact_store=artifact_store,
        policy_resolver=ProofPolicyResolver(policy_registry, governance_key, schema_validator=validator),
        idempotency_store=store, schema_validator=validator,
    )


__all__ = ["DurableIdempotencyStore", "ProofCheckApplication", "load_production_application"]
