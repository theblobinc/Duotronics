#!/usr/bin/env python3
"""Authenticated audit publisher and anchor services for Draft 5.3.16.

The proof service, publisher, and anchor are separate Unix identities.  Every
mutation is authorized twice: Linux peer credentials and a signed canonical
request envelope.  The file-backed anchor remains a development implementation;
a production activation requires an independently monotonic backend.
"""
from __future__ import annotations

import copy
import fcntl
import json
import os
import socket
import socketserver
import sqlite3
import stat
import struct
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from executable.runtime.pq_provider import MLDSA87PrivateKey, MLDSA87PublicKey

from cache_audit import (
    InMemoryMonotonicAuditAnchor, SignedAppendOnlyAuditSink,
    socket_identity_shake256_512, verify_artifact_key_lifecycle,
)
from proof_authority import (
    CanonicalSchemaValidator, canonical_bytes, canonical_json_loads, shake256_512_bytes,
    sign_record, verify_record,
)

O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
SO_PEERCRED = getattr(socket, "SO_PEERCRED", 17)


def _write_all(descriptor: int, data: bytes) -> None:
    written = 0
    while written < len(data):
        amount = os.write(descriptor, data[written:])
        if amount <= 0:
            raise OSError("complete write made no progress")
        written += amount


def _peer_start_time(pid: int) -> int | None:
    try:
        fields = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").split()
        return int(fields[21])
    except (OSError, ValueError, IndexError):
        return None


class FileBackedMonotonicAnchorStore:
    """Development-only signed anchor ledger.

    The state transition logic is strict and hash-chained, but local storage can
    still be restored by its owner or host administrator.  ``authoritative`` is
    therefore always false.  Activation launchers must use an external monotonic
    implementation instead.
    """
    authoritative = False

    def __init__(
        self, ledger_path: Path, signing_key: MLDSA87PrivateKey, *, key_id: str,
        signer_principal_id: str, anchor_registry_shake256_512: str,
        anchor_registry_records: Mapping[str, dict[str, Any]],
        schema_validator: CanonicalSchemaValidator, provision: bool = False,
        expected_uid: int | None = None, maximum_ledger_bytes: int = 64 * 1024 * 1024,
        clock: Callable[[], datetime] | None = None,
    ):
        self.path = Path(ledger_path)
        self.signing_key = signing_key
        self.verification_key = signing_key.public_key()
        self.key_id = key_id
        self.signer_principal_id = signer_principal_id
        self.anchor_registry_shake256_512 = anchor_registry_shake256_512
        self.anchor_registry_records = {k: copy.deepcopy(v) for k, v in anchor_registry_records.items()}
        self.schema_validator = schema_validator
        self.expected_uid = os.getuid() if expected_uid is None else expected_uid
        self.maximum_ledger_bytes = int(maximum_ledger_bytes)
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.path.parent, 0o700)
        if provision:
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_RDWR | O_NOFOLLOW, 0o600)
            os.close(descriptor)
        if not self.path.exists():
            raise RuntimeError("privileged audit anchor ledger is not provisioned")
        self._verify_file_identity()
        self._read_locked()

    @staticmethod
    def state_shake256_512(state: dict[str, Any] | None) -> str | None:
        return None if state is None else shake256_512_bytes(canonical_bytes(state))

    def _verify_file_identity(self) -> None:
        info = self.path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != self.expected_uid or stat.S_IMODE(info.st_mode) != 0o600:
            raise RuntimeError("privileged audit anchor ledger identity is unsafe")
        parent = self.path.parent.lstat()
        if parent.st_uid != self.expected_uid or stat.S_IMODE(parent.st_mode) != 0o700:
            raise RuntimeError("privileged audit anchor directory is not private")

    def _verify_lines(self, data: bytes) -> dict[str, Any] | None:
        if data and not data.endswith(b"\n"):
            raise RuntimeError("audit anchor ledger ends with a partial record")
        previous: dict[str, Any] | None = None
        for line in data.splitlines():
            state = canonical_json_loads(line.decode("utf-8"))
            if canonical_bytes(state) != line:
                raise RuntimeError("audit anchor ledger contains non-canonical JSON")
            self.schema_validator.validate("cache_audit_anchor_state", state)
            if state.get("anchor_key_id") != self.key_id or not verify_record(state, self.verification_key):
                raise RuntimeError("audit anchor ledger signature is invalid")
            verify_artifact_key_lifecycle(
                registry_shake256_512=self.anchor_registry_shake256_512,
                registry_records=self.anchor_registry_records,
                key_id=state.get("anchor_key_id"),
                principal_id=state.get("anchor_signer_principal_id"),
                required_scope="cache_audit_monotonic_anchor_signing",
                artifact_timestamp=state.get("updated_at"),
                embedded_evidence=state.get("anchor_key_validity_evidence"),
                schema_validator=self.schema_validator,
                allow_retired_historical=True,
            )
            if state.get("previous_anchor_state_shake256_512") != self.state_shake256_512(previous):
                raise RuntimeError("audit anchor ledger predecessor-state hash is invalid")
            InMemoryMonotonicAuditAnchor._validate_transition(previous, state)
            previous = state
        return previous

    def _read_locked(self) -> dict[str, Any] | None:
        descriptor = os.open(self.path, os.O_RDWR | O_NOFOLLOW)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            size = os.fstat(descriptor).st_size
            if size > self.maximum_ledger_bytes:
                raise RuntimeError("audit anchor ledger exceeds its governed bound")
            data = bytearray()
            while len(data) < size:
                chunk = os.read(descriptor, min(65536, size - len(data)))
                if not chunk:
                    raise RuntimeError("audit anchor ledger changed during read")
                data.extend(chunk)
            return self._verify_lines(bytes(data))
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def read(self) -> dict[str, Any] | None:
        return copy.deepcopy(self._read_locked())

    def compare_and_swap(self, expected_state_shake256_512: str | None, unsigned_state: dict[str, Any]) -> dict[str, Any]:
        descriptor = os.open(self.path, os.O_APPEND | os.O_RDWR | O_NOFOLLOW)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            os.lseek(descriptor, 0, os.SEEK_SET)
            size = os.fstat(descriptor).st_size
            if size > self.maximum_ledger_bytes:
                raise RuntimeError("audit anchor ledger exceeds its governed bound")
            data = bytearray()
            while len(data) < size:
                chunk = os.read(descriptor, min(65536, size - len(data)))
                if not chunk:
                    raise RuntimeError("audit anchor ledger changed during compare-and-swap")
                data.extend(chunk)
            current = self._verify_lines(bytes(data))
            if self.state_shake256_512(current) != expected_state_shake256_512:
                raise RuntimeError("audit anchor compare-and-swap precondition failed")
            if unsigned_state.get("previous_anchor_state_shake256_512") != self.state_shake256_512(current):
                raise RuntimeError("audit anchor request does not bind the current state")
            InMemoryMonotonicAuditAnchor._validate_transition(current, unsigned_state)
            validity = verify_artifact_key_lifecycle(
                registry_shake256_512=self.anchor_registry_shake256_512,
                registry_records=self.anchor_registry_records,
                key_id=self.key_id, principal_id=self.signer_principal_id,
                required_scope="cache_audit_monotonic_anchor_signing",
                artifact_timestamp=unsigned_state.get("updated_at"),
                embedded_evidence=None, schema_validator=self.schema_validator,
            )
            state = sign_record({
                **unsigned_state, "anchor_key_id": self.key_id,
                "anchor_signer_principal_id": self.signer_principal_id,
                "anchor_key_validity_evidence": validity,
            }, self.signing_key)
            self.schema_validator.validate("cache_audit_anchor_state", state)
            encoded = canonical_bytes(state) + b"\n"
            if size + len(encoded) > self.maximum_ledger_bytes:
                raise RuntimeError("audit anchor ledger capacity is exhausted and requires governed rotation")
            os.lseek(descriptor, 0, os.SEEK_END)
            _write_all(descriptor, encoded)
            os.fsync(descriptor)
            directory = os.open(self.path.parent, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            return copy.deepcopy(state)
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)


class DurableEventIdIndex:
    """Publisher-domain global idempotency index that survives segment rotation."""
    def __init__(self, path: Path, *, expected_uid: int | None = None):
        self.path = Path(path)
        self.expected_uid = os.getuid() if expected_uid is None else expected_uid
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.path.parent, 0o700)
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute("CREATE TABLE IF NOT EXISTS committed_events (event_id TEXT PRIMARY KEY, event_shake256_512 TEXT NOT NULL, result_json TEXT NOT NULL, committed_at TEXT NOT NULL)")
            connection.commit()
        finally:
            connection.close()
        os.chmod(self.path, 0o600)
        info = self.path.lstat()
        if info.st_uid != self.expected_uid or stat.S_IMODE(info.st_mode) != 0o600:
            raise RuntimeError("publisher idempotency index identity is unsafe")

    def get(self, event_id: str) -> dict[str, Any] | None:
        connection = sqlite3.connect(self.path)
        try:
            row = connection.execute("SELECT result_json FROM committed_events WHERE event_id=?", (event_id,)).fetchone()
            return None if row is None else canonical_json_loads(row[0])
        finally:
            connection.close()

    def commit(self, event_id: str, event_shake256_512: str, result: dict[str, Any], committed_at: str) -> dict[str, Any]:
        encoded = canonical_bytes(result).decode("utf-8")
        connection = sqlite3.connect(self.path, timeout=5, isolation_level="IMMEDIATE")
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT event_shake256_512,result_json FROM committed_events WHERE event_id=?", (event_id,)).fetchone()
            if row is not None:
                if row[0] != event_shake256_512:
                    raise RuntimeError("global audit event idempotency collision")
                connection.rollback()
                return canonical_json_loads(row[1])
            connection.execute(
                "INSERT INTO committed_events(event_id,event_shake256_512,result_json,committed_at) VALUES(?,?,?,?)",
                (event_id, event_shake256_512, encoded, committed_at),
            )
            connection.commit()
            return result
        finally:
            connection.close()


class _BoundedLineHandler(socketserver.StreamRequestHandler):
    maximum_request_bytes = 4 * 1024 * 1024

    def handle(self) -> None:
        credentials = self.request.getsockopt(socket.SOL_SOCKET, SO_PEERCRED, struct.calcsize("3i"))
        pid, uid, gid = struct.unpack("3i", credentials)
        peer = {"pid": pid, "uid": uid, "gid": gid, "start_time_ticks": _peer_start_time(pid)}
        raw = self.rfile.readline(self.maximum_request_bytes + 1)
        if len(raw) > self.maximum_request_bytes or not raw.endswith(b"\n"):
            response = {"status": "error", "error": "request exceeds the canonical line bound"}
        else:
            try:
                request = canonical_json_loads(raw[:-1].decode("utf-8"))
                payload = self.server.authenticate(request, peer)  # type: ignore[attr-defined]
                response = self.server.dispatch(payload, peer)  # type: ignore[attr-defined]
            except Exception as error:
                response = {"status": "error", "error": f"{type(error).__name__}: {str(error)[:2048]}"}
        try:
            self.wfile.write(canonical_bytes(response) + b"\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass


class GovernedUnixServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(
        self, socket_path: Path, dispatch: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]], *,
        schema_validator: CanonicalSchemaValidator, target_service: str,
        allowed_peer_principals: Mapping[tuple[int, int], str],
        request_verification_keys_by_principal: Mapping[str, Mapping[str, MLDSA87PublicKey]],
        socket_uid: int | None = None, socket_gid: int | None = None,
        socket_mode: int = 0o660, parent_mode: int = 0o750,
    ):
        if socket_mode & 0o002:
            raise ValueError("governed Unix socket cannot be world writable")
        self.socket_path = Path(socket_path)
        self.schema_validator = schema_validator
        self.target_service = target_service
        self.allowed_peer_principals = dict(allowed_peer_principals)
        self.request_verification_keys_by_principal = {p: dict(v) for p, v in request_verification_keys_by_principal.items()}
        self._seen_request_ids: set[str] = set()
        self._seen_lock = threading.Lock()
        self.socket_path.parent.mkdir(mode=parent_mode, parents=True, exist_ok=True)
        os.chmod(self.socket_path.parent, parent_mode)
        try:
            self.socket_path.unlink()
        except FileNotFoundError:
            pass
        self.dispatch = dispatch
        super().__init__(str(self.socket_path), _BoundedLineHandler)
        uid = os.getuid() if socket_uid is None else int(socket_uid)
        gid = os.getgid() if socket_gid is None else int(socket_gid)
        if os.geteuid() == 0:
            os.chown(self.socket_path, uid, gid)
            os.chown(self.socket_path.parent, uid, gid)
        os.chmod(self.socket_path, socket_mode)
        info = self.socket_path.lstat()
        parent = self.socket_path.parent.lstat()
        if (
            not stat.S_ISSOCK(info.st_mode) or info.st_uid != uid or info.st_gid != gid
            or stat.S_IMODE(info.st_mode) != socket_mode
            or parent.st_uid != uid or parent.st_gid != gid or stat.S_IMODE(parent.st_mode) != parent_mode
        ):
            self.server_close()
            raise RuntimeError("governed Unix socket identity or ancestry is invalid")
        self.socket_identity_shake256_512 = socket_identity_shake256_512(self.socket_path)

    def authenticate(self, request: dict[str, Any], peer: dict[str, Any]) -> dict[str, Any]:
        self.schema_validator.validate("cache_audit_service_request", request)
        operation = request.get("operation")
        principal = self.allowed_peer_principals.get((peer["uid"], peer["gid"]))
        if principal is None or principal != request.get("peer_principal_id"):
            raise PermissionError("Unix peer credentials are not authorized for this service")
        if request.get("target_service") != self.target_service:
            raise PermissionError("authenticated request targets a different service")
        if request.get("socket_identity_shake256_512") != self.socket_identity_shake256_512:
            raise PermissionError("authenticated request does not bind this socket identity")
        if request.get("deadline_unix_ns", 0) <= time.time_ns():
            raise TimeoutError("authenticated service request is expired")
        payload = request.get("payload")
        if not isinstance(payload, dict) or request.get("payload_shake256_512") != shake256_512_bytes(canonical_bytes(payload)):
            raise RuntimeError("authenticated service request payload digest is invalid")
        if payload.get("operation") != operation:
            raise RuntimeError("authenticated service operation does not match its payload")
        keys = self.request_verification_keys_by_principal.get(principal, {})
        key = keys.get(request.get("request_signer_key_id"))
        if key is None or not verify_record(request, key):
            raise PermissionError("authenticated service request signature is invalid")
        request_id = request["request_id"]
        with self._seen_lock:
            if request_id in self._seen_request_ids:
                raise PermissionError("authenticated service request was replayed")
            if len(self._seen_request_ids) >= 10000:
                self._seen_request_ids.clear()
            self._seen_request_ids.add(request_id)
        return payload

    def close_and_unlink(self) -> None:
        self.shutdown()
        self.server_close()
        try:
            self.socket_path.unlink()
        except FileNotFoundError:
            pass


class AuditAnchorServer:
    def __init__(
        self, socket_path: Path, store: FileBackedMonotonicAnchorStore, *,
        schema_validator: CanonicalSchemaValidator,
        publisher_uid: int, publisher_gid: int, publisher_principal_id: str,
        request_verification_keys: Mapping[str, MLDSA87PublicKey],
        socket_uid: int | None = None, socket_gid: int | None = None,
    ):
        self.store = store
        self.server = GovernedUnixServer(
            socket_path, self.dispatch, schema_validator=schema_validator,
            target_service="cache_audit_anchor",
            allowed_peer_principals={(publisher_uid, publisher_gid): publisher_principal_id},
            request_verification_keys_by_principal={publisher_principal_id: request_verification_keys},
            socket_uid=socket_uid, socket_gid=socket_gid, socket_mode=0o660,
        )

    def dispatch(self, request: dict[str, Any], peer: dict[str, Any]) -> dict[str, Any]:
        operation = request.get("operation")
        if operation == "read":
            return {"status": "ok", "state": self.store.read(), "peer": peer}
        if operation == "compare_and_swap":
            state = request.get("new_state")
            if not isinstance(state, dict):
                raise RuntimeError("audit anchor compare-and-swap state is absent")
            return {
                "status": "ok",
                "state": self.store.compare_and_swap(request.get("expected_state_shake256_512"), state),
                "peer": peer,
            }
        raise RuntimeError("unknown audit anchor operation")


class AuditPublisherServer:
    """Owns record and receipt keys, global idempotency, and durable segments."""
    def __init__(
        self, socket_path: Path, sink_factory: Callable[[], SignedAppendOnlyAuditSink], *,
        receipt_signing_key: MLDSA87PrivateKey, receipt_key_id: str,
        receipt_signer_principal_id: str, receipt_signing_registry_shake256_512: str,
        receipt_registry_records: Mapping[str, dict[str, Any]],
        schema_validator: CanonicalSchemaValidator,
        event_index: DurableEventIdIndex,
        proof_service_uid: int, proof_service_gid: int, proof_service_principal_id: str,
        request_verification_keys: Mapping[str, MLDSA87PublicKey],
        socket_uid: int | None = None, socket_gid: int | None = None,
        clock: Callable[[], datetime] | None = None,
    ):
        self.sink_factory = sink_factory
        self.receipt_signing_key = receipt_signing_key
        self.receipt_key_id = receipt_key_id
        self.receipt_signer_principal_id = receipt_signer_principal_id
        self.receipt_signing_registry_shake256_512 = receipt_signing_registry_shake256_512
        self.receipt_registry_records = {k: copy.deepcopy(v) for k, v in receipt_registry_records.items()}
        self.schema_validator = schema_validator
        self.event_index = event_index
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.server = GovernedUnixServer(
            socket_path, self.dispatch, schema_validator=schema_validator,
            target_service="cache_audit_publisher",
            allowed_peer_principals={(proof_service_uid, proof_service_gid): proof_service_principal_id},
            request_verification_keys_by_principal={proof_service_principal_id: request_verification_keys},
            socket_uid=socket_uid, socket_gid=socket_gid, socket_mode=0o660,
        )

    def _receipt(self, result: dict[str, Any], event_id: str, event_sha: str, decision: str) -> dict[str, Any]:
        record = result["record"]
        anchor = result["anchor"]
        completed_at = self.clock().astimezone(timezone.utc).isoformat()
        validity = verify_artifact_key_lifecycle(
            registry_shake256_512=self.receipt_signing_registry_shake256_512,
            registry_records=self.receipt_registry_records,
            key_id=self.receipt_key_id, principal_id=self.receipt_signer_principal_id,
            required_scope="cache_audit_receipt_signing",
            artifact_timestamp=completed_at, embedded_evidence=None,
            schema_validator=self.schema_validator,
        )
        unsigned = {
            "schema_version": "cache_audit_publication_receipt/v2",
            "event_idempotency_key": event_id, "event_shake256_512": event_sha,
            "audit_record_id": record["audit_record_id"], "segment_id": record["segment_id"],
            "sequence": record["sequence"],
            "anchor_state_shake256_512": shake256_512_bytes(canonical_bytes(anchor)),
            "receipt_signing_registry_shake256_512": self.receipt_signing_registry_shake256_512,
            "receipt_signer_principal_id": self.receipt_signer_principal_id,
            "receipt_signer_key_id": self.receipt_key_id,
            "receipt_key_validity_evidence": validity,
            "decision": decision,
            "completed_at": completed_at,
        }
        receipt = sign_record(unsigned, self.receipt_signing_key)
        self.schema_validator.validate("cache_audit_publication_receipt", receipt)
        return receipt

    def dispatch(self, request: dict[str, Any], peer: dict[str, Any]) -> dict[str, Any]:
        if request.get("operation") != "publish":
            raise RuntimeError("unknown cache audit publisher operation")
        event = request.get("event")
        if not isinstance(event, dict):
            raise RuntimeError("cache audit publisher event is absent")
        event_bytes = canonical_bytes(event)
        event_sha = shake256_512_bytes(event_bytes)
        event_id = "event:" + event_sha
        if request.get("event_shake256_512") != event_sha or request.get("event_idempotency_key") != event_id:
            raise RuntimeError("cache audit publisher request digest is invalid")
        existing = self.event_index.get(event_id)
        if existing is not None:
            receipt = self._receipt(existing, event_id, event_sha, "already_committed")
            return {"status": "ok", "receipt": receipt, "peer": peer}
        result = self.sink_factory()(event, deadline_monotonic=None)
        durable = self.event_index.commit(event_id, event_sha, result, self.clock().astimezone(timezone.utc).isoformat())
        decision = "already_committed" if result["status"] == "already_committed" else "durably_committed"
        receipt = self._receipt(durable, event_id, event_sha, decision)
        return {"status": "ok", "receipt": receipt, "peer": peer}


__all__ = [
    "FileBackedMonotonicAnchorStore", "DurableEventIdIndex", "GovernedUnixServer",
    "AuditAnchorServer", "AuditPublisherServer",
]
