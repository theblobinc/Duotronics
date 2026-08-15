from __future__ import annotations

import fcntl
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .crypto_primitives import shake256_hex
from .crypto_profile import (
    AppendOnlyKeyRegistry,
    PublicKeyRecord,
    generate_signing_key,
    sign_envelope,
    unb64,
    verify_envelope,
)

DEFAULT_PQ_KEY_ROOT = Path(os.environ.get("XAVI_PQ_KEY_DIR", "/runtime/data/crypto/pq_keys"))
_SIGNING_PURPOSES = {"witness", "evidence", "manifest"}


def _atomic_write(path: Path, data: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb", closefd=True) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
        os.chmod(path, mode)
    finally:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass


class PQKeyManager:
    """Persistent purpose-scoped ML-DSA key lifecycle for runtime authority boundaries.

    Secret keys never enter PostgreSQL or witness payloads. The append-only lifecycle
    registry is the authoritative active/revoked key state; public key records are
    stored alongside it for independent verification.
    """

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root) if root is not None else DEFAULT_PQ_KEY_ROOT
        self.root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.root, 0o700)
        self.public_dir = self.root / "public"
        self.secret_dir = self.root / "secret"
        self.public_dir.mkdir(parents=True, exist_ok=True)
        self.secret_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.public_dir, 0o700)
        os.chmod(self.secret_dir, 0o700)
        self.registry = AppendOnlyKeyRegistry(self.root / "lifecycle.jsonl")
        self.lock_path = self.root / ".lifecycle.lock"

    @staticmethod
    def _token(key_id: str) -> str:
        return shake256_hex(key_id)[:48]

    def _public_path(self, key_id: str) -> Path:
        return self.public_dir / f"{self._token(key_id)}.json"

    def _secret_path(self, key_id: str) -> Path:
        return self.secret_dir / f"{self._token(key_id)}.key"

    def _lock(self):
        self.lock_path.touch(mode=0o600, exist_ok=True)
        handle = self.lock_path.open("r+")
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        return handle

    def _records(self) -> dict[str, PublicKeyRecord]:
        records: dict[str, PublicKeyRecord] = {}
        if not self.public_dir.exists():
            return records
        for path in sorted(self.public_dir.glob("*.json")):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                record = PublicKeyRecord(**raw)
                records[record.key_id] = record
            except Exception:
                continue
        return records

    def _latest_active_id(self, purpose: str) -> str | None:
        revoked = self.registry.revoked_key_ids()
        inactive: set[str] = set(revoked)
        candidates: list[str] = []
        for event in self.registry.events():
            body = event.get("body") if isinstance(event.get("body"), dict) else {}
            if event.get("event_type") in {"register", "rotate"}:
                record = body.get("record") if isinstance(body.get("record"), dict) else None
                if record and record.get("purpose") == purpose and record.get("key_id"):
                    candidates.append(str(record["key_id"]))
            if event.get("event_type") in {"retire", "revoke", "destroy"} and body.get("key_id"):
                inactive.add(str(body["key_id"]))
        records = self._records()
        for key_id in reversed(candidates):
            record = records.get(key_id)
            if record and record.purpose == purpose and key_id not in inactive and self._secret_path(key_id).exists():
                return key_id
        return None

    def _create_signing_key_locked(self, purpose: str, predecessor_key_id: str | None, *, event_type: str) -> PublicKeyRecord:
        record, secret_key = generate_signing_key(purpose, predecessor_key_id=predecessor_key_id)
        _atomic_write(self._secret_path(record.key_id), secret_key, 0o600)
        _atomic_write(
            self._public_path(record.key_id),
            json.dumps(record.as_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n",
            0o600,
        )
        self.registry.append(event_type, {"record": record.as_dict(), "key_id": record.key_id, "purpose": purpose})
        return record

    def ensure_signing_key(self, purpose: str) -> PublicKeyRecord:
        if purpose not in _SIGNING_PURPOSES:
            raise ValueError(f"unsupported signing purpose: {purpose}")
        lock = self._lock()
        try:
            key_id = self._latest_active_id(purpose)
            if key_id:
                return self._records()[key_id]
            return self._create_signing_key_locked(purpose, None, event_type="register")
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def rotate_signing_key(self, purpose: str) -> dict[str, Any]:
        if purpose not in _SIGNING_PURPOSES:
            raise ValueError(f"unsupported signing purpose: {purpose}")
        lock = self._lock()
        try:
            predecessor = self._latest_active_id(purpose)
            record = self._create_signing_key_locked(purpose, predecessor, event_type="rotate")
            if predecessor:
                self.registry.append("retire", {"key_id": predecessor, "purpose": purpose, "successor_key_id": record.key_id})
            return {"purpose": purpose, "predecessor_key_id": predecessor, "active_key": record.as_dict()}
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def revoke_key(self, key_id: str, *, reason: str = "operator_revocation") -> dict[str, Any]:
        record = self.public_record(key_id)
        lock = self._lock()
        try:
            return self.registry.append("revoke", {"key_id": key_id, "purpose": record.purpose, "reason": reason})
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def public_record(self, key_id: str) -> PublicKeyRecord:
        record = self._records().get(str(key_id))
        if record is None:
            raise KeyError(f"unknown PQ signing key: {key_id}")
        return record

    def public_records(self) -> list[dict[str, Any]]:
        revoked = self.registry.revoked_key_ids()
        rows = []
        for record in self._records().values():
            row = record.as_dict()
            row["revoked"] = record.key_id in revoked
            row["active"] = self._latest_active_id(record.purpose) == record.key_id and record.key_id not in revoked
            rows.append(row)
        return sorted(rows, key=lambda row: (row["purpose"], row["created_at"], row["key_id"]))

    def sign(self, payload: dict[str, Any], *, purpose: str) -> dict[str, Any]:
        record = self.ensure_signing_key(purpose)
        secret_key = self._secret_path(record.key_id).read_bytes()
        return sign_envelope(payload, record, secret_key, purpose=purpose)

    def verify(self, envelope: dict[str, Any]) -> bool:
        key_id = str(envelope.get("key_id") or "")
        if not key_id:
            return False
        try:
            record = self.public_record(key_id)
        except KeyError:
            return False
        return verify_envelope(envelope, record, self.registry.revoked_key_ids())

    def status(self) -> dict[str, Any]:
        return {
            "schema": "duotronic-pq-key-manager-status/v1",
            "registry_chain_valid": self.registry.verify_chain(),
            "keys": self.public_records(),
            "revoked_key_ids": sorted(self.registry.revoked_key_ids()),
            "secret_key_count": len(list(self.secret_dir.glob("*.key"))),
        }
