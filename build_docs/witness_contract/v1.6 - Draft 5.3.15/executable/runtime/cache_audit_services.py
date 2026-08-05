#!/usr/bin/env python3
"""Separately supervised audit publisher and monotonic-anchor services.

These services are deployment primitives.  The proof service is only a client;
it does not own the audit signing key, local audit segment, or monotonic anchor
state in production.
"""
from __future__ import annotations

import copy
import fcntl
import os
import socketserver
import stat
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from cache_audit import InMemoryMonotonicAuditAnchor, SignedAppendOnlyAuditSink
from proof_authority import (
    CanonicalSchemaValidator, canonical_bytes, canonical_json_loads, sha256_bytes,
    sign_record, verify_record,
)

O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)


class FileBackedMonotonicAnchorStore:
    """Privileged append-only anchor ledger with signed monotonic states."""
    def __init__(
        self, ledger_path: Path, signing_key: Ed25519PrivateKey, *, key_id: str,
        schema_validator: CanonicalSchemaValidator, provision: bool = False,
        expected_uid: int | None = None,
    ):
        self.path = Path(ledger_path)
        self.signing_key = signing_key
        self.verification_key = signing_key.public_key()
        self.key_id = key_id
        self.schema_validator = schema_validator
        self.expected_uid = os.getuid() if expected_uid is None else expected_uid
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
    def state_sha256(state: dict[str, Any] | None) -> str | None:
        return None if state is None else sha256_bytes(canonical_bytes(state))

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
            InMemoryMonotonicAuditAnchor._validate_transition(previous, state)
            previous = state
        return previous

    def _read_locked(self) -> dict[str, Any] | None:
        descriptor = os.open(self.path, os.O_RDWR | O_NOFOLLOW)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            size = os.fstat(descriptor).st_size
            if size > 64 * 1024 * 1024:
                raise RuntimeError("audit anchor ledger exceeds its governed bound")
            data = b""
            while len(data) < size:
                chunk = os.read(descriptor, min(65536, size - len(data)))
                if not chunk:
                    raise RuntimeError("audit anchor ledger changed during read")
                data += chunk
            return self._verify_lines(data)
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def read(self) -> dict[str, Any] | None:
        return copy.deepcopy(self._read_locked())

    def compare_and_swap(self, expected_state_sha256: str | None, unsigned_state: dict[str, Any]) -> dict[str, Any]:
        descriptor = os.open(self.path, os.O_APPEND | os.O_RDWR | O_NOFOLLOW)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            os.lseek(descriptor, 0, os.SEEK_SET)
            data = b""
            size = os.fstat(descriptor).st_size
            while len(data) < size:
                chunk = os.read(descriptor, min(65536, size - len(data)))
                if not chunk:
                    raise RuntimeError("audit anchor ledger changed during compare-and-swap")
                data += chunk
            current = self._verify_lines(data)
            if self.state_sha256(current) != expected_state_sha256:
                raise RuntimeError("audit anchor compare-and-swap precondition failed")
            InMemoryMonotonicAuditAnchor._validate_transition(current, unsigned_state)
            state = sign_record({**unsigned_state, "anchor_key_id": self.key_id}, self.signing_key)
            self.schema_validator.validate("cache_audit_anchor_state", state)
            encoded = canonical_bytes(state) + b"\n"
            os.lseek(descriptor, 0, os.SEEK_END)
            os.write(descriptor, encoded)
            os.fsync(descriptor)
            directory = os.open(self.path.parent, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
            try: os.fsync(directory)
            finally: os.close(directory)
            return copy.deepcopy(state)
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)


class _BoundedLineHandler(socketserver.StreamRequestHandler):
    maximum_request_bytes = 4 * 1024 * 1024

    def handle(self) -> None:
        raw = self.rfile.readline(self.maximum_request_bytes + 1)
        if len(raw) > self.maximum_request_bytes or not raw.endswith(b"\n"):
            response = {"status": "error", "error": "request exceeds the canonical line bound"}
        else:
            try:
                request = canonical_json_loads(raw[:-1].decode("utf-8"))
                response = self.server.dispatch(request)  # type: ignore[attr-defined]
            except Exception as error:
                response = {"status": "error", "error": f"{type(error).__name__}: {str(error)[:2048]}"}
        try:
            self.wfile.write(canonical_bytes(response) + b"\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            # A hard-deadline client is allowed to abandon a slow request.
            pass


class GovernedUnixServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, socket_path: Path, dispatch: Callable[[dict[str, Any]], dict[str, Any]], *, socket_mode: int = 0o660):
        self.socket_path = Path(socket_path)
        self.socket_path.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
        try: self.socket_path.unlink()
        except FileNotFoundError: pass
        self.dispatch = dispatch
        super().__init__(str(self.socket_path), _BoundedLineHandler)
        os.chmod(self.socket_path, socket_mode)

    def close_and_unlink(self) -> None:
        self.shutdown(); self.server_close()
        try: self.socket_path.unlink()
        except FileNotFoundError: pass


class AuditAnchorServer:
    def __init__(self, socket_path: Path, store: FileBackedMonotonicAnchorStore):
        self.store = store
        self.server = GovernedUnixServer(socket_path, self.dispatch)

    def dispatch(self, request: dict[str, Any]) -> dict[str, Any]:
        operation = request.get("operation")
        if operation == "read":
            return {"status": "ok", "state": self.store.read()}
        if operation == "compare_and_swap":
            state = request.get("new_state")
            if not isinstance(state, dict):
                raise RuntimeError("audit anchor compare-and-swap state is absent")
            return {"status": "ok", "state": self.store.compare_and_swap(request.get("expected_state_sha256"), state)}
        raise RuntimeError("unknown audit anchor operation")


class AuditPublisherServer:
    """Owns the audit signing key and durable segment outside the proof service."""
    def __init__(
        self, socket_path: Path, sink_factory: Callable[[], SignedAppendOnlyAuditSink], *,
        receipt_signing_key: Ed25519PrivateKey, receipt_key_id: str,
        audit_signing_registry_sha256: str, schema_validator: CanonicalSchemaValidator,
        clock: Callable[[], datetime] | None = None,
    ):
        self.sink_factory = sink_factory
        self.receipt_signing_key = receipt_signing_key
        self.receipt_key_id = receipt_key_id
        self.audit_signing_registry_sha256 = audit_signing_registry_sha256
        self.schema_validator = schema_validator
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.server = GovernedUnixServer(socket_path, self.dispatch)

    def dispatch(self, request: dict[str, Any]) -> dict[str, Any]:
        if request.get("operation") != "publish":
            raise RuntimeError("unknown cache audit publisher operation")
        event = request.get("event")
        if not isinstance(event, dict):
            raise RuntimeError("cache audit publisher event is absent")
        event_bytes = canonical_bytes(event)
        event_sha = sha256_bytes(event_bytes)
        event_id = "event:" + event_sha
        if request.get("event_sha256") != event_sha or request.get("event_idempotency_key") != event_id:
            raise RuntimeError("cache audit publisher request digest is invalid")
        result = self.sink_factory()(event, deadline_monotonic=None)
        record = result["record"]
        anchor = result["anchor"]
        unsigned = {
            "schema_version": "cache_audit_publication_receipt/v1",
            "event_idempotency_key": event_id, "event_sha256": event_sha,
            "audit_record_id": record["audit_record_id"], "segment_id": record["segment_id"],
            "sequence": record["sequence"],
            "anchor_state_sha256": sha256_bytes(canonical_bytes(anchor)),
            "audit_signing_registry_sha256": self.audit_signing_registry_sha256,
            "audit_signer_key_id": self.receipt_key_id,
            "decision": "already_committed" if result["status"] == "already_committed" else "durably_committed",
            "completed_at": self.clock().astimezone(timezone.utc).isoformat(),
        }
        receipt = sign_record(unsigned, self.receipt_signing_key)
        self.schema_validator.validate("cache_audit_publication_receipt", receipt)
        return {"status": "ok", "receipt": receipt}


__all__ = [
    "FileBackedMonotonicAnchorStore", "GovernedUnixServer", "AuditAnchorServer", "AuditPublisherServer",
]
