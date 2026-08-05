#!/usr/bin/env python3
"""Governed, externally anchored cache-audit persistence for Draft 5.3.15.

The proof service owns the local segment and checkpoint, but the expected tail is
held by an independent monotonic anchor.  Production publication is performed by
``SupervisedAuditPublisher`` so a blocked filesystem operation cannot hold the
request thread beyond its deadline.  Deterministic event identifiers permit
safe reconciliation after an ambiguous timeout.
"""
from __future__ import annotations

import copy
import fcntl
import json
import os
import re
import select
import signal
import socket
import stat
import threading
import time
import uuid
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from proof_authority import (
    AuthorityFailure, CanonicalSchemaValidator, canonical_bytes, canonical_json_loads,
    public_key_raw_b64url, sha256_bytes, sign_record, verify_record,
)

IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)


def _utc(clock: Callable[[], datetime]) -> str:
    return clock().astimezone(timezone.utc).isoformat()


def _parse_time(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as error:
        raise RuntimeError(f"{field} is not an RFC3339 timestamp") from error
    if parsed.tzinfo is None:
        raise RuntimeError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def validate_governed_signing_registry(
    registry: dict[str, Any], governance_key: Ed25519PublicKey, *,
    schema_validator: CanonicalSchemaValidator, surface: str, required_scope: str,
    evaluated_at: datetime,
) -> tuple[str, dict[str, dict[str, Any]], dict[str, Ed25519PublicKey]]:
    """Validate an audit/anchor key registry and return all historical keys."""
    schema_validator.validate(surface, registry)
    if not verify_record(registry, governance_key):
        raise RuntimeError(f"{surface} governance signature is invalid")
    digest = sha256_bytes(canonical_bytes(registry))
    records: dict[str, dict[str, Any]] = {}
    keys: dict[str, Ed25519PublicKey] = {}
    for record in registry["keys"]:
        key_id = record["key_id"]
        if key_id in records:
            raise RuntimeError(f"{surface} contains duplicate key identifiers")
        if record["authorization_scope"] != required_scope:
            raise RuntimeError(f"{surface} contains an incorrectly scoped key")
        valid_from = _parse_time(record["valid_from"], f"{key_id}.valid_from")
        valid_until = None if record["valid_until"] is None else _parse_time(record["valid_until"], f"{key_id}.valid_until")
        changed = _parse_time(record["status_changed_at"], f"{key_id}.status_changed_at")
        if changed < valid_from or (valid_until is not None and changed >= valid_until):
            raise RuntimeError(f"{surface} contains incoherent key chronology")
        predecessor = record["rotation_predecessor_key_id"]
        if predecessor is not None and predecessor == key_id:
            raise RuntimeError(f"{surface} contains a self-rotation")
        import base64
        value = record["public_key_base64url"]
        padded = value + "=" * ((4 - len(value) % 4) % 4)
        try:
            raw = base64.urlsafe_b64decode(padded.encode("ascii"))
            key = Ed25519PublicKey.from_public_bytes(raw)
        except Exception as error:
            raise RuntimeError(f"{surface} contains an invalid Ed25519 public key") from error
        records[key_id] = copy.deepcopy(record)
        keys[key_id] = key
    for record in records.values():
        predecessor = record["rotation_predecessor_key_id"]
        if predecessor is not None and predecessor not in records:
            raise RuntimeError(f"{surface} rotation predecessor is absent")
    return digest, records, keys


def key_validity_evidence(
    *, registry_sha256: str, record: dict[str, Any], evaluated_at: datetime,
    required_status: str = "active",
) -> dict[str, Any]:
    now = evaluated_at.astimezone(timezone.utc)
    valid_from = _parse_time(record["valid_from"], "valid_from")
    valid_until = None if record["valid_until"] is None else _parse_time(record["valid_until"], "valid_until")
    changed = _parse_time(record["status_changed_at"], "status_changed_at")
    decision = (
        "active_time_valid_rotation_valid"
        if record["status"] == required_status and valid_from <= now and changed <= now and (valid_until is None or now < valid_until)
        else "inactive_or_time_invalid"
    )
    return {
        "schema_version": "cache_audit_key_validity_evidence/v1",
        "registry_sha256": registry_sha256,
        "key_id": record["key_id"],
        "principal_id": record["principal_id"],
        "authorization_scope": record["authorization_scope"],
        "status": record["status"],
        "valid_from": record["valid_from"],
        "valid_until": record["valid_until"],
        "status_changed_at": record["status_changed_at"],
        "rotation_predecessor_key_id": record["rotation_predecessor_key_id"],
        "decision": decision,
        "evaluated_at": now.isoformat(),
    }


class AuditAnchorClient:
    """Minimal external monotonic anchor contract."""
    def read(self) -> dict[str, Any] | None:  # pragma: no cover - interface
        raise NotImplementedError

    def compare_and_swap(self, expected_state_sha256: str | None, unsigned_state: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover - interface
        raise NotImplementedError


class InMemoryMonotonicAuditAnchor(AuditAnchorClient):
    """Test anchor with signed, monotonic compare-and-swap semantics."""
    def __init__(
        self, signing_key: Ed25519PrivateKey, *, key_id: str,
        schema_validator: CanonicalSchemaValidator,
    ):
        self.signing_key = signing_key
        self.verification_key = signing_key.public_key()
        self.key_id = key_id
        self.schema_validator = schema_validator
        self._state: dict[str, Any] | None = None
        self._lock = threading.Lock()

    @staticmethod
    def state_sha256(state: dict[str, Any] | None) -> str | None:
        return None if state is None else sha256_bytes(canonical_bytes(state))

    def read(self) -> dict[str, Any] | None:
        with self._lock:
            return copy.deepcopy(self._state)

    @staticmethod
    def _validate_transition(current: dict[str, Any] | None, new: dict[str, Any]) -> None:
        if current is None:
            if new["anchor_epoch"] != 0 or new["sequence"] != 0 or new["segment_status"] != "open":
                raise RuntimeError("audit anchor genesis is not canonical")
            return
        if new["anchor_namespace"] != current["anchor_namespace"]:
            raise RuntimeError("audit anchor namespace changed")
        if new["segment_id"] == current["segment_id"]:
            if new["anchor_epoch"] != current["anchor_epoch"]:
                raise RuntimeError("audit anchor epoch changed inside a segment")
            if new["sequence"] < current["sequence"]:
                raise RuntimeError("audit anchor sequence rollback")
            if current["segment_status"] == "sealed" and new != current:
                raise RuntimeError("sealed audit anchor state is immutable")
            if current["segment_status"] == "open" and new["segment_status"] not in {"open", "sealed"}:
                raise RuntimeError("audit anchor segment status is invalid")
        else:
            if current["segment_status"] != "sealed":
                raise RuntimeError("audit anchor successor requires a sealed predecessor")
            if new["anchor_epoch"] != current["anchor_epoch"] + 1 or new["sequence"] != 0:
                raise RuntimeError("audit anchor successor epoch is invalid")
            if new["previous_sealed_segment_tail_sha256"] != current["tail_record_sha256"]:
                raise RuntimeError("audit anchor successor does not bind the predecessor tail")

    def compare_and_swap(self, expected_state_sha256: str | None, unsigned_state: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if self.state_sha256(self._state) != expected_state_sha256:
                raise AuthorityFailure("cache_audit_integrity_invalid", "external audit anchor compare-and-swap failed")
            self._validate_transition(self._state, unsigned_state)
            state = sign_record({**unsigned_state, "anchor_key_id": self.key_id}, self.signing_key)
            self.schema_validator.validate("cache_audit_anchor_state", state)
            self._state = state
            return copy.deepcopy(state)


class UnixSocketAuditAnchorClient(AuditAnchorClient):
    """Client for a separately privileged monotonic anchor helper."""
    def __init__(
        self, socket_path: Path, *, anchor_namespace: str,
        verification_keys_by_id: Mapping[str, Ed25519PublicKey],
        anchor_registry_sha256: str, schema_validator: CanonicalSchemaValidator,
        expected_socket_uid: int = 0, timeout_seconds: float = 5.0,
    ):
        self.socket_path = Path(socket_path)
        self.anchor_namespace = anchor_namespace
        self.verification_keys_by_id = dict(verification_keys_by_id)
        self.anchor_registry_sha256 = anchor_registry_sha256
        self.schema_validator = schema_validator
        self.expected_socket_uid = expected_socket_uid
        self.timeout_seconds = timeout_seconds
        if not self.socket_path.is_absolute():
            raise ValueError("audit anchor socket path must be absolute")

    def _verify_socket(self) -> None:
        info = self.socket_path.lstat()
        if not stat.S_ISSOCK(info.st_mode) or info.st_uid != self.expected_socket_uid:
            raise RuntimeError("audit anchor endpoint is not the expected privileged Unix socket")
        parent = self.socket_path.parent
        while True:
            item = parent.lstat()
            if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode):
                raise RuntimeError("audit anchor socket ancestry is unsafe")
            if item.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
                sticky_root = item.st_uid == 0 and bool(item.st_mode & stat.S_ISVTX)
                if not sticky_root:
                    raise RuntimeError("audit anchor socket ancestry is group/world writable")
            if parent == parent.parent:
                break
            parent = parent.parent

    def _request(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        self._verify_socket()
        encoded = canonical_bytes(payload) + b"\n"
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(self.timeout_seconds)
            client.connect(str(self.socket_path))
            client.sendall(encoded)
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = client.recv(65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > 1024 * 1024:
                    raise RuntimeError("audit anchor response exceeds its bound")
                chunks.append(chunk)
                if b"\n" in chunk:
                    break
        raw = b"".join(chunks)
        if not raw.endswith(b"\n") or raw.count(b"\n") != 1:
            raise RuntimeError("audit anchor response is not one canonical record")
        response = canonical_json_loads(raw[:-1].decode("utf-8"))
        if response.get("status") != "ok":
            raise AuthorityFailure("cache_audit_integrity_invalid", str(response.get("error", "audit anchor rejected the operation")))
        state = response.get("state")
        if state is None:
            return None
        self.schema_validator.validate("cache_audit_anchor_state", state)
        key = self.verification_keys_by_id.get(state.get("anchor_key_id"))
        if key is None or not verify_record(state, key):
            raise RuntimeError("audit anchor state signature is invalid")
        if state.get("anchor_namespace") != self.anchor_namespace or state.get("anchor_registry_sha256") != self.anchor_registry_sha256:
            raise RuntimeError("audit anchor state is outside the governed namespace or registry")
        return state

    def read(self) -> dict[str, Any] | None:
        return self._request({"operation": "read", "anchor_namespace": self.anchor_namespace})

    def compare_and_swap(self, expected_state_sha256: str | None, unsigned_state: dict[str, Any]) -> dict[str, Any]:
        state = self._request({
            "operation": "compare_and_swap", "anchor_namespace": self.anchor_namespace,
            "expected_state_sha256": expected_state_sha256, "new_state": unsigned_state,
        })
        if state is None:
            raise RuntimeError("audit anchor compare-and-swap returned no state")
        return state


class SignedAppendOnlyAuditSink:
    """Signed JSONL segment with local checkpoint and external monotonic anchor."""

    EVENT_SCHEMA_SURFACES = {
        "cache_stale_row_evidence/v4": "cache_stale_row_evidence",
        "cache_verification_evidence/v1": "cache_verification_evidence",
        "cache_audit_segment_seal/v2": "cache_audit_segment_seal",
        "cache_audit_recovery_evidence/v1": "cache_audit_recovery_evidence",
    }

    def __init__(
        self, path: Path, checkpoint_path: Path,
        signing_key: Ed25519PrivateKey, verification_keys_by_id: Mapping[str, Ed25519PublicKey], *,
        segment_id: str, signer_principal_id: str, signer_key_id: str,
        audit_signing_registry_sha256: str, audit_key_validity_evidence: dict[str, Any],
        schema_validator: CanonicalSchemaValidator,
        maximum_record_bytes: int, maximum_log_bytes: int, maximum_event_records: int,
        terminal_seal_reserved_bytes: int,
        anchor_client: AuditAnchorClient, anchor_namespace: str, anchor_registry_sha256: str,
        rotation_policy: str = "governed_external_anchor_and_signed_segment_transition",
        clock: Callable[[], datetime] | None = None,
        monotonic: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
        fsync: Callable[[int], None] | None = None,
        provision: bool = False,
        governance_key: Ed25519PublicKey | None = None,
        genesis_authorization: dict[str, Any] | None = None,
        transition_attestation: dict[str, Any] | None = None,
        predecessor_checkpoint: dict[str, Any] | None = None,
        predecessor_terminal_record: dict[str, Any] | None = None,
        storage_root: Path | None = None,
        expected_uid: int | None = None,
        enforce_private_ancestry: bool = True,
        recovery_mode: bool = False,
    ):
        self.path = Path(path)
        self.checkpoint_path = Path(checkpoint_path)
        self.signing_key = signing_key
        self.verification_keys_by_id = dict(verification_keys_by_id)
        self.segment_id = segment_id
        self.signer_principal_id = signer_principal_id
        self.signer_key_id = signer_key_id
        self.audit_signing_registry_sha256 = audit_signing_registry_sha256
        self.audit_key_validity_evidence = copy.deepcopy(audit_key_validity_evidence)
        self.schema_validator = schema_validator
        self.maximum_record_bytes = int(maximum_record_bytes)
        self.maximum_log_bytes = int(maximum_log_bytes)
        self.maximum_event_records = int(maximum_event_records)
        self.terminal_seal_reserved_bytes = int(terminal_seal_reserved_bytes)
        self.anchor_client = anchor_client
        self.anchor_namespace = anchor_namespace
        self.anchor_registry_sha256 = anchor_registry_sha256
        self.rotation_policy = rotation_policy
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.monotonic = monotonic or time.monotonic
        self.sleep = sleep or time.sleep
        self.fsync = fsync or os.fsync
        self.storage_root = Path(storage_root) if storage_root is not None else Path(os.path.commonpath([self.path.parent, self.checkpoint_path.parent]))
        self.expected_uid = os.getuid() if expected_uid is None else expected_uid
        self.enforce_private_ancestry = enforce_private_ancestry
        self.recovery_mode = recovery_mode
        self._lock = threading.Lock()
        if not IDENTIFIER.fullmatch(segment_id) or not IDENTIFIER.fullmatch(anchor_namespace):
            raise ValueError("cache audit segment or anchor namespace identifier is not canonical")
        if rotation_policy != "governed_external_anchor_and_signed_segment_transition":
            raise ValueError("cache audit rotation policy is not governed")
        if self.maximum_record_bytes < 1024 or self.maximum_log_bytes < 2 * self.maximum_record_bytes:
            raise ValueError("cache audit byte bounds are invalid")
        if self.maximum_event_records < 0:
            raise ValueError("cache audit event-record bound is invalid")
        if self.terminal_seal_reserved_bytes < self.maximum_record_bytes:
            raise ValueError("terminal seal reserve must be at least one maximum record")
        if public_key_raw_b64url(signing_key.public_key()) != public_key_raw_b64url(self.verification_keys_by_id.get(signer_key_id, signing_key.public_key())):
            raise ValueError("cache audit signing key is not the governed current key")
        self.schema_validator.validate("cache_audit_key_validity_evidence", self.audit_key_validity_evidence)
        if self.audit_key_validity_evidence.get("decision") != "active_time_valid_rotation_valid":
            raise ValueError("cache audit signer is not actively governed")
        if self.audit_key_validity_evidence.get("registry_sha256") != self.audit_signing_registry_sha256:
            raise ValueError("cache audit key evidence does not bind the configured registry")
        if self.path.parent.resolve() == self.checkpoint_path.parent.resolve():
            raise ValueError("audit log and local checkpoint require distinct private directories")
        if provision:
            self._provision_segment(
                governance_key=governance_key, genesis_authorization=genesis_authorization,
                transition_attestation=transition_attestation,
                predecessor_checkpoint=predecessor_checkpoint,
                predecessor_terminal_record=predecessor_terminal_record,
            )
        anchor = self.anchor_client.read()
        if anchor is None:
            raise AuthorityFailure("cache_audit_integrity_invalid", "external monotonic audit anchor is missing")
        self._verify_anchor_state(anchor)
        self.previous_sealed_segment_tail_sha256 = anchor["previous_sealed_segment_tail_sha256"]
        descriptor = self._open_locked_log(deadline_monotonic=None)
        try:
            sequence, tail, _records = self._verify_descriptor(descriptor, deadline_monotonic=None)
            checkpoint = self._load_checkpoint()
            if not self.recovery_mode:
                self._verify_checkpoint(checkpoint, sequence=sequence, tail=tail, anchor=anchor)
            self._sequence = sequence
            self._previous_record_sha256 = tail
            self._segment_status = checkpoint["segment_status"]
            self._anchor_state = anchor
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    @staticmethod
    def _state_digest(state: dict[str, Any] | None) -> str | None:
        return None if state is None else sha256_bytes(canonical_bytes(state))

    def _deadline_check(self, deadline_monotonic: float | None, stage: str) -> None:
        if deadline_monotonic is not None and self.monotonic() >= deadline_monotonic:
            raise TimeoutError(f"cache audit deadline expired {stage}")

    def _secure_parent(self, path: Path, *, create: bool) -> None:
        if create:
            path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            os.chmod(path.parent, 0o700)
        if path.parent.is_symlink() or not path.parent.is_dir():
            raise RuntimeError("cache audit parent must be a real directory")
        if not self.enforce_private_ancestry:
            return
        root = self.storage_root.resolve()
        parent = path.parent.resolve()
        try:
            parent.relative_to(root)
        except ValueError as error:
            raise RuntimeError("cache audit path is outside its governed storage root") from error
        current = root
        for component in parent.relative_to(root).parts:
            current = current / component
            info = current.lstat()
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                raise RuntimeError("cache audit ancestry contains an unsafe component")
            if info.st_uid != self.expected_uid or stat.S_IMODE(info.st_mode) != 0o700:
                raise RuntimeError("cache audit ancestry is not private and service-owned")

    def _verify_governance_record(self, surface: str, record: dict[str, Any] | None, governance_key: Ed25519PublicKey | None) -> dict[str, Any]:
        if record is None or governance_key is None:
            raise RuntimeError(f"{surface} is required")
        self.schema_validator.validate(surface, record)
        if not verify_record(record, governance_key):
            raise RuntimeError(f"{surface} governance signature is invalid")
        return record

    def _provision_segment(
        self, *, governance_key: Ed25519PublicKey | None,
        genesis_authorization: dict[str, Any] | None,
        transition_attestation: dict[str, Any] | None,
        predecessor_checkpoint: dict[str, Any] | None,
        predecessor_terminal_record: dict[str, Any] | None,
    ) -> None:
        self._secure_parent(self.path, create=True)
        self._secure_parent(self.checkpoint_path, create=True)
        if self.path.exists() or self.checkpoint_path.exists():
            raise RuntimeError("cache audit provisioning refuses an existing log or checkpoint")
        current_anchor = self.anchor_client.read()
        if current_anchor is None:
            authorization = self._verify_governance_record("cache_audit_genesis_authorization", genesis_authorization, governance_key)
            expected = {
                "segment_id": self.segment_id, "anchor_namespace": self.anchor_namespace,
                "audit_signing_registry_sha256": self.audit_signing_registry_sha256,
                "anchor_registry_sha256": self.anchor_registry_sha256,
                "decision": "authorize_audit_genesis",
            }
            if any(authorization.get(key) != value for key, value in expected.items()):
                raise RuntimeError("audit genesis authorization does not bind this segment")
            previous_tail = None
            transition_digest = authorization["signed_payload_sha256"]
            epoch = 0
        else:
            self._verify_anchor_state(current_anchor, require_current_segment=False)
            if current_anchor["segment_status"] != "sealed":
                raise RuntimeError("audit successor requires a sealed anchored predecessor")
            transition = self._verify_governance_record("cache_audit_segment_transition", transition_attestation, governance_key)
            if predecessor_checkpoint is None or predecessor_terminal_record is None:
                raise RuntimeError("successor provisioning requires predecessor checkpoint and terminal record")
            self.schema_validator.validate("cache_audit_checkpoint", predecessor_checkpoint)
            predecessor_key = self.verification_keys_by_id.get(predecessor_checkpoint.get("audit_signer_key_id"))
            if predecessor_key is None or not verify_record(predecessor_checkpoint, predecessor_key):
                raise RuntimeError("predecessor sealed checkpoint signature is invalid")
            self.schema_validator.validate("cache_audit_record", predecessor_terminal_record)
            terminal_key = self.verification_keys_by_id.get(predecessor_terminal_record.get("audit_signer_key_id"))
            if terminal_key is None or not verify_record(predecessor_terminal_record, terminal_key):
                raise RuntimeError("predecessor terminal record signature is invalid")
            terminal_event = canonical_json_loads(predecessor_terminal_record["event_canonical_json"])
            self._validate_event(terminal_event, "cache_audit_segment_seal/v2")
            predecessor_checkpoint_sha = sha256_bytes(canonical_bytes(predecessor_checkpoint))
            predecessor_terminal_sha = sha256_bytes(canonical_bytes(predecessor_terminal_record))
            expected = {
                "predecessor_segment_id": current_anchor["segment_id"],
                "predecessor_sealed_checkpoint_sha256": predecessor_checkpoint_sha,
                "predecessor_terminal_record_sha256": predecessor_terminal_sha,
                "predecessor_tail_record_sha256": current_anchor["tail_record_sha256"],
                "predecessor_anchor_state_sha256": self._state_digest(current_anchor),
                "successor_segment_id": self.segment_id,
                "successor_anchor_epoch": current_anchor["anchor_epoch"] + 1,
                "audit_signing_registry_sha256": self.audit_signing_registry_sha256,
                "anchor_registry_sha256": self.anchor_registry_sha256,
                "decision": "authorize_successor_segment",
            }
            if any(transition.get(key) != value for key, value in expected.items()):
                raise RuntimeError("audit segment transition does not prove the sealed predecessor")
            if predecessor_checkpoint.get("segment_status") != "sealed" or predecessor_checkpoint.get("tail_record_sha256") != current_anchor["tail_record_sha256"]:
                raise RuntimeError("predecessor checkpoint is not the anchored terminal checkpoint")
            if predecessor_terminal_record.get("sequence") != predecessor_checkpoint.get("sequence"):
                raise RuntimeError("predecessor terminal record is not the sealed checkpoint tail")
            previous_tail = current_anchor["tail_record_sha256"]
            transition_digest = transition["signed_payload_sha256"]
            epoch = current_anchor["anchor_epoch"] + 1
        descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_RDWR | O_NOFOLLOW, 0o600)
        try:
            os.fchmod(descriptor, 0o600)
            self.fsync(descriptor)
        finally:
            os.close(descriptor)
        self._fsync_directory(self.path.parent, deadline_monotonic=None)
        unsigned_anchor = self._anchor_unsigned(
            epoch=epoch, sequence=0, tail=None, segment_status="open",
            previous_tail=previous_tail, transition_digest=transition_digest,
        )
        try:
            anchor = self.anchor_client.compare_and_swap(self._state_digest(current_anchor), unsigned_anchor)
            self.previous_sealed_segment_tail_sha256 = previous_tail
            self._write_checkpoint(sequence=0, tail=None, segment_status="open", anchor=anchor, deadline_monotonic=None)
        except Exception:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
            raise

    def _anchor_unsigned(
        self, *, epoch: int, sequence: int, tail: str | None, segment_status: str,
        previous_tail: str | None, transition_digest: str,
    ) -> dict[str, Any]:
        return {
            "schema_version": "cache_audit_anchor_state/v1",
            "anchor_namespace": self.anchor_namespace,
            "anchor_epoch": epoch,
            "segment_id": self.segment_id,
            "sequence": sequence,
            "tail_record_sha256": tail,
            "segment_status": segment_status,
            "previous_sealed_segment_tail_sha256": previous_tail,
            "transition_authorization_sha256": transition_digest,
            "audit_signing_registry_sha256": self.audit_signing_registry_sha256,
            "anchor_registry_sha256": self.anchor_registry_sha256,
            "updated_at": _utc(self.clock),
        }

    def _verify_anchor_state(self, anchor: dict[str, Any], *, require_current_segment: bool = True) -> None:
        self.schema_validator.validate("cache_audit_anchor_state", anchor)
        if (
            anchor.get("anchor_namespace") != self.anchor_namespace
            or (require_current_segment and anchor.get("segment_id") != self.segment_id)
            or anchor.get("audit_signing_registry_sha256") != self.audit_signing_registry_sha256
            or anchor.get("anchor_registry_sha256") != self.anchor_registry_sha256
        ):
            raise AuthorityFailure("cache_audit_integrity_invalid", "external audit anchor does not bind this segment and governance state")

    def _open_locked_log(self, *, deadline_monotonic: float | None) -> int:
        self._secure_parent(self.path, create=False)
        try:
            descriptor = os.open(self.path, os.O_APPEND | os.O_RDWR | O_NOFOLLOW)
        except FileNotFoundError as error:
            raise AuthorityFailure("cache_audit_integrity_invalid", "provisioned cache audit segment is missing") from error
        try:
            while True:
                self._deadline_check(deadline_monotonic, "before lock acquisition")
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if deadline_monotonic is None:
                        self.sleep(0.01)
                    else:
                        remaining = deadline_monotonic - self.monotonic()
                        if remaining <= 0:
                            raise TimeoutError("cache audit lock acquisition exceeded the request deadline")
                        self.sleep(min(0.01, remaining))
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600 or info.st_uid != self.expected_uid:
                raise RuntimeError("cache audit log is not one private service-owned regular file")
            return descriptor
        except Exception:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)
            raise

    def _read_descriptor(self, descriptor: int, *, deadline_monotonic: float | None) -> bytes:
        size = os.fstat(descriptor).st_size
        if size > self.maximum_log_bytes:
            raise RuntimeError("cache audit log exceeds its governed byte bound")
        os.lseek(descriptor, 0, os.SEEK_SET)
        remaining = size
        chunks: list[bytes] = []
        while remaining:
            self._deadline_check(deadline_monotonic, "during bounded chain read")
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                raise RuntimeError("cache audit log changed during bounded read")
            chunks.append(chunk)
            remaining -= len(chunk)
        extra = os.read(descriptor, 1)
        if extra:
            raise RuntimeError("cache audit log grew during bounded read")
        return b"".join(chunks)

    def _validate_event(self, event: dict[str, Any], expected_version: str | None = None) -> str:
        if not isinstance(event, dict):
            raise RuntimeError("cache audit event is not an object")
        version = event.get("schema_version")
        if not isinstance(version, str) or version not in self.EVENT_SCHEMA_SURFACES:
            raise RuntimeError("cache audit event schema version is unknown")
        if expected_version is not None and version != expected_version:
            raise RuntimeError("cache audit outer and embedded event schema versions differ")
        self.schema_validator.validate(self.EVENT_SCHEMA_SURFACES[version], event)
        return version

    def _verify_descriptor(
        self, descriptor: int, *, deadline_monotonic: float | None,
    ) -> tuple[int, str | None, list[dict[str, Any]]]:
        data = self._read_descriptor(descriptor, deadline_monotonic=deadline_monotonic)
        if data and not data.endswith(b"\n"):
            raise RuntimeError("cache audit log ends with a partial record")
        previous: str | None = None
        records: list[dict[str, Any]] = []
        seal_seen = False
        normal_count = 0
        for raw_line in data.splitlines():
            self._deadline_check(deadline_monotonic, "during chain verification")
            if len(raw_line) + 1 > self.maximum_record_bytes:
                raise RuntimeError("cache audit record exceeds its governed byte bound")
            try:
                record = canonical_json_loads(raw_line.decode("utf-8"))
            except (UnicodeDecodeError, ValueError) as error:
                raise RuntimeError("cache audit log contains non-canonical JSON") from error
            if canonical_bytes(record) != raw_line:
                raise RuntimeError("cache audit log contains non-canonical JSON")
            self.schema_validator.validate("cache_audit_record", record)
            key = self.verification_keys_by_id.get(record.get("audit_signer_key_id"))
            if key is None or not verify_record(record, key):
                raise RuntimeError("cache audit record signature or historical key is invalid")
            sequence = len(records) + 1
            if (
                record.get("segment_id") != self.segment_id
                or record.get("sequence") != sequence
                or record.get("previous_audit_record_sha256") != previous
                or record.get("previous_sealed_segment_tail_sha256") != self.previous_sealed_segment_tail_sha256
                or record.get("audit_signing_registry_sha256") != self.audit_signing_registry_sha256
                or record.get("anchor_namespace") != self.anchor_namespace
                or record.get("anchor_registry_sha256") != self.anchor_registry_sha256
            ):
                raise RuntimeError("cache audit segment, sequence, governance, or hash chain is invalid")
            evidence = record.get("audit_key_validity_evidence")
            self.schema_validator.validate("cache_audit_key_validity_evidence", evidence)
            if evidence.get("registry_sha256") != self.audit_signing_registry_sha256 or evidence.get("key_id") != record.get("audit_signer_key_id"):
                raise RuntimeError("cache audit record key-validity evidence is invalid")
            event_json = record.get("event_canonical_json", "")
            try:
                event = canonical_json_loads(event_json)
            except ValueError as error:
                raise RuntimeError("cache audit event is not canonical JSON") from error
            if canonical_bytes(event).decode("utf-8") != event_json or sha256_bytes(event_json.encode("utf-8")) != record.get("event_sha256"):
                raise RuntimeError("cache audit event digest is invalid")
            version = self._validate_event(event, str(record.get("event_schema_version", "")))
            event_id = "event:" + sha256_bytes(canonical_bytes(event))
            if record.get("event_idempotency_key") != event_id:
                raise RuntimeError("cache audit event idempotency key is invalid")
            identity = {
                "segment_id": self.segment_id, "sequence": sequence,
                "previous_audit_record_sha256": previous,
                "previous_sealed_segment_tail_sha256": self.previous_sealed_segment_tail_sha256,
                "event_sha256": record["event_sha256"], "event_idempotency_key": event_id,
                "audit_signer_key_id": record["audit_signer_key_id"],
                "audit_signing_registry_sha256": self.audit_signing_registry_sha256,
                "anchor_namespace": self.anchor_namespace,
            }
            if record.get("audit_record_id") != "audit:" + sha256_bytes(canonical_bytes(identity)):
                raise RuntimeError("cache audit record identifier is invalid")
            is_seal = version == "cache_audit_segment_seal/v2"
            if seal_seen or (is_seal and sequence != len(data.splitlines())):
                raise RuntimeError("cache audit terminal seal is not terminal")
            if is_seal:
                seal_seen = True
            else:
                normal_count += 1
            if normal_count > self.maximum_event_records or sequence > self.maximum_event_records + 1:
                raise RuntimeError("cache audit log exceeds its governed record bound")
            previous = sha256_bytes(raw_line)
            records.append(record)
        return len(records), previous, records

    def _load_checkpoint(self) -> dict[str, Any]:
        self._secure_parent(self.checkpoint_path, create=False)
        try:
            descriptor = os.open(self.checkpoint_path, os.O_RDONLY | O_NOFOLLOW)
        except FileNotFoundError as error:
            raise AuthorityFailure("cache_audit_integrity_invalid", "cache audit local checkpoint is missing") from error
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600 or info.st_uid != self.expected_uid:
                raise RuntimeError("cache audit checkpoint is not one private service-owned regular file")
            if info.st_size > self.maximum_record_bytes:
                raise RuntimeError("cache audit checkpoint exceeds its governed byte bound")
            raw = b""
            remaining = info.st_size
            while remaining:
                chunk = os.read(descriptor, min(65536, remaining))
                if not chunk:
                    raise RuntimeError("cache audit checkpoint changed during read")
                raw += chunk
                remaining -= len(chunk)
        finally:
            os.close(descriptor)
        if not raw.endswith(b"\n") or raw.count(b"\n") != 1:
            raise RuntimeError("cache audit checkpoint must contain one terminal newline")
        checkpoint = canonical_json_loads(raw[:-1].decode("utf-8"))
        if canonical_bytes(checkpoint) + b"\n" != raw:
            raise RuntimeError("cache audit checkpoint is not canonical JSON")
        self.schema_validator.validate("cache_audit_checkpoint", checkpoint)
        key = self.verification_keys_by_id.get(checkpoint.get("audit_signer_key_id"))
        if key is None or not verify_record(checkpoint, key):
            raise RuntimeError("cache audit checkpoint signature is invalid")
        return checkpoint

    def _verify_checkpoint(self, checkpoint: dict[str, Any], *, sequence: int, tail: str | None, anchor: dict[str, Any]) -> None:
        if (
            checkpoint.get("segment_id") != self.segment_id
            or checkpoint.get("sequence") != sequence
            or checkpoint.get("tail_record_sha256") != tail
            or checkpoint.get("previous_sealed_segment_tail_sha256") != self.previous_sealed_segment_tail_sha256
            or checkpoint.get("audit_signer_key_id") != self.signer_key_id
            or checkpoint.get("audit_signing_registry_sha256") != self.audit_signing_registry_sha256
            or checkpoint.get("anchor_namespace") != self.anchor_namespace
            or checkpoint.get("anchor_state_sha256") != self._state_digest(anchor)
            or checkpoint.get("anchor_epoch") != anchor.get("anchor_epoch")
            or checkpoint.get("segment_status") != anchor.get("segment_status")
            or anchor.get("sequence") != sequence
            or anchor.get("tail_record_sha256") != tail
        ):
            raise AuthorityFailure("cache_audit_integrity_invalid", "local audit state differs from the independently monotonic anchor")

    def _checkpoint_record(self, *, sequence: int, tail: str | None, segment_status: str, anchor: dict[str, Any]) -> dict[str, Any]:
        unsigned = {
            "schema_version": "cache_audit_checkpoint/v2",
            "segment_id": self.segment_id, "sequence": sequence,
            "tail_record_sha256": tail,
            "previous_sealed_segment_tail_sha256": self.previous_sealed_segment_tail_sha256,
            "audit_signer_key_id": self.signer_key_id,
            "audit_signing_registry_sha256": self.audit_signing_registry_sha256,
            "audit_key_validity_evidence": self.audit_key_validity_evidence,
            "anchor_namespace": self.anchor_namespace,
            "anchor_registry_sha256": self.anchor_registry_sha256,
            "anchor_epoch": anchor["anchor_epoch"],
            "anchor_state_sha256": self._state_digest(anchor),
            "segment_status": segment_status,
            "checkpoint_created_at": _utc(self.clock),
        }
        record = sign_record(unsigned, self.signing_key)
        self.schema_validator.validate("cache_audit_checkpoint", record)
        return record

    def _write_checkpoint(
        self, *, sequence: int, tail: str | None, segment_status: str,
        anchor: dict[str, Any], deadline_monotonic: float | None,
    ) -> None:
        self._deadline_check(deadline_monotonic, "before checkpoint signing")
        self._secure_parent(self.checkpoint_path, create=True)
        encoded = canonical_bytes(self._checkpoint_record(sequence=sequence, tail=tail, segment_status=segment_status, anchor=anchor)) + b"\n"
        temporary = self.checkpoint_path.with_name(f".{self.checkpoint_path.name}.{uuid.uuid4().hex}.tmp")
        descriptor = -1
        try:
            descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | O_NOFOLLOW, 0o600)
            os.fchmod(descriptor, 0o600)
            written = 0
            while written < len(encoded):
                self._deadline_check(deadline_monotonic, "during checkpoint write")
                amount = os.write(descriptor, encoded[written:])
                if amount <= 0:
                    raise OSError("cache audit checkpoint write made no progress")
                written += amount
            self.fsync(descriptor)
            self._deadline_check(deadline_monotonic, "after checkpoint fsync")
            os.close(descriptor); descriptor = -1
            os.replace(temporary, self.checkpoint_path)
            self._fsync_directory(self.checkpoint_path.parent, deadline_monotonic=deadline_monotonic)
        except Exception:
            if descriptor >= 0:
                os.close(descriptor)
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            raise

    def _fsync_directory(self, path: Path, *, deadline_monotonic: float | None) -> None:
        self._deadline_check(deadline_monotonic, "before directory fsync")
        descriptor = os.open(path, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
        try:
            self.fsync(descriptor)
        finally:
            os.close(descriptor)
        self._deadline_check(deadline_monotonic, "after directory fsync")

    def _build_record(self, evidence: dict[str, Any], *, sequence: int, previous: str | None) -> tuple[dict[str, Any], bytes, str]:
        version = self._validate_event(evidence)
        event_bytes = canonical_bytes(evidence)
        event_sha256 = sha256_bytes(event_bytes)
        event_id = "event:" + event_sha256
        identity = {
            "segment_id": self.segment_id, "sequence": sequence,
            "previous_audit_record_sha256": previous,
            "previous_sealed_segment_tail_sha256": self.previous_sealed_segment_tail_sha256,
            "event_sha256": event_sha256, "event_idempotency_key": event_id,
            "audit_signer_key_id": self.signer_key_id,
            "audit_signing_registry_sha256": self.audit_signing_registry_sha256,
            "anchor_namespace": self.anchor_namespace,
        }
        unsigned = {
            "schema_version": "cache_audit_record/v3",
            "audit_record_id": "audit:" + sha256_bytes(canonical_bytes(identity)),
            "event_idempotency_key": event_id,
            "segment_id": self.segment_id, "sequence": sequence,
            "previous_audit_record_sha256": previous,
            "previous_sealed_segment_tail_sha256": self.previous_sealed_segment_tail_sha256,
            "event_schema_version": version,
            "event_canonical_json": event_bytes.decode("utf-8"), "event_sha256": event_sha256,
            "audit_signer_principal_id": self.signer_principal_id,
            "audit_signer_key_id": self.signer_key_id,
            "audit_signing_registry_sha256": self.audit_signing_registry_sha256,
            "audit_key_validity_evidence": self.audit_key_validity_evidence,
            "anchor_namespace": self.anchor_namespace,
            "anchor_registry_sha256": self.anchor_registry_sha256,
            "rotation_policy": self.rotation_policy,
            "created_at": _utc(self.clock),
        }
        record = sign_record(unsigned, self.signing_key)
        self.schema_validator.validate("cache_audit_record", record)
        encoded = canonical_bytes(record) + b"\n"
        if len(encoded) > self.maximum_record_bytes:
            raise RuntimeError("cache audit record exceeds its governed byte bound")
        return record, encoded, event_id

    def _append_locked(
        self, descriptor: int, evidence: dict[str, Any], *, deadline_monotonic: float | None,
        segment_status_after: str, is_terminal_seal: bool,
    ) -> dict[str, Any]:
        sequence_before, previous_before, records = self._verify_descriptor(descriptor, deadline_monotonic=deadline_monotonic)
        anchor_before = self.anchor_client.read()
        if anchor_before is None:
            raise AuthorityFailure("cache_audit_integrity_invalid", "external audit anchor is missing")
        checkpoint = self._load_checkpoint()
        self._verify_checkpoint(checkpoint, sequence=sequence_before, tail=previous_before, anchor=anchor_before)
        if checkpoint["segment_status"] != "open":
            raise AuthorityFailure("cache_audit_integrity_invalid", "sealed cache audit segment cannot accept new records")
        event_id = "event:" + sha256_bytes(canonical_bytes(evidence))
        matches = [record for record in records if record.get("event_idempotency_key") == event_id]
        if matches:
            if len(matches) != 1 or matches[0]["event_sha256"] != event_id.split(":", 1)[1]:
                raise AuthorityFailure("cache_audit_integrity_invalid", "audit event idempotency collision")
            return {"status": "already_committed", "record": matches[0], "checkpoint": checkpoint, "anchor": anchor_before}
        normal_count = sum(record["event_schema_version"] != "cache_audit_segment_seal/v2" for record in records)
        if is_terminal_seal:
            if any(record["event_schema_version"] == "cache_audit_segment_seal/v2" for record in records):
                raise AuthorityFailure("cache_audit_integrity_invalid", "cache audit segment is already sealed")
        elif normal_count >= self.maximum_event_records:
            raise RuntimeError("cache audit normal-event capacity is exhausted; terminal seal capacity remains reserved")
        sequence = sequence_before + 1
        record, encoded, event_id = self._build_record(evidence, sequence=sequence, previous=previous_before)
        current_size = os.fstat(descriptor).st_size
        if is_terminal_seal:
            if current_size + len(encoded) > self.maximum_log_bytes:
                raise RuntimeError("reserved terminal seal capacity is insufficient")
        elif current_size + len(encoded) + self.terminal_seal_reserved_bytes > self.maximum_log_bytes:
            raise RuntimeError("cache audit normal-event byte capacity is exhausted; terminal seal capacity remains reserved")
        self._deadline_check(deadline_monotonic, "before audit append")
        os.lseek(descriptor, 0, os.SEEK_END)
        written = 0
        while written < len(encoded):
            self._deadline_check(deadline_monotonic, "during audit append")
            amount = os.write(descriptor, encoded[written:])
            if amount <= 0:
                raise OSError("cache audit append made no progress")
            written += amount
        self.fsync(descriptor)
        self._deadline_check(deadline_monotonic, "after audit-record fsync")
        tail = sha256_bytes(encoded[:-1])
        unsigned_anchor = self._anchor_unsigned(
            epoch=anchor_before["anchor_epoch"], sequence=sequence, tail=tail,
            segment_status=segment_status_after,
            previous_tail=self.previous_sealed_segment_tail_sha256,
            transition_digest=anchor_before["transition_authorization_sha256"],
        )
        anchor_after = self.anchor_client.compare_and_swap(self._state_digest(anchor_before), unsigned_anchor)
        self._deadline_check(deadline_monotonic, "after external anchor commit")
        self._write_checkpoint(
            sequence=sequence, tail=tail, segment_status=segment_status_after,
            anchor=anchor_after, deadline_monotonic=deadline_monotonic,
        )
        self._fsync_directory(self.path.parent, deadline_monotonic=deadline_monotonic)
        self._sequence = sequence
        self._previous_record_sha256 = tail
        self._segment_status = segment_status_after
        self._anchor_state = anchor_after
        return {"status": "committed", "record": record, "checkpoint": self._load_checkpoint(), "anchor": anchor_after}

    def __call__(self, evidence: dict[str, Any], *, deadline_monotonic: float | None = None) -> dict[str, Any]:
        with self._lock:
            descriptor = self._open_locked_log(deadline_monotonic=deadline_monotonic)
            try:
                return self._append_locked(
                    descriptor, evidence, deadline_monotonic=deadline_monotonic,
                    segment_status_after="open", is_terminal_seal=False,
                )
            finally:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
                os.close(descriptor)

    def seal_segment(self, *, deadline_monotonic: float | None = None) -> dict[str, Any]:
        with self._lock:
            descriptor = self._open_locked_log(deadline_monotonic=deadline_monotonic)
            try:
                sequence, tail, _records = self._verify_descriptor(descriptor, deadline_monotonic=deadline_monotonic)
                event = {
                    "schema_version": "cache_audit_segment_seal/v2",
                    "segment_id": self.segment_id,
                    "sealed_event_count": sequence,
                    "terminal_record_sequence": sequence + 1,
                    "sealed_predecessor_tail_sha256": tail,
                    "previous_sealed_segment_tail_sha256": self.previous_sealed_segment_tail_sha256,
                    "audit_signing_registry_sha256": self.audit_signing_registry_sha256,
                    "audit_key_validity_evidence": self.audit_key_validity_evidence,
                    "anchor_namespace": self.anchor_namespace,
                    "anchor_registry_sha256": self.anchor_registry_sha256,
                    "decision": "terminal_segment_seal",
                    "sealed_at": _utc(self.clock),
                }
                result = self._append_locked(
                    descriptor, event, deadline_monotonic=deadline_monotonic,
                    segment_status_after="sealed", is_terminal_seal=True,
                )
                return result["checkpoint"]
            finally:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
                os.close(descriptor)

    def _signed_recovery_evidence(self, *, action: str, before: dict[str, Any], after: dict[str, Any], authorization: dict[str, Any]) -> dict[str, Any]:
        unsigned = {
            "schema_version": "cache_audit_recovery_evidence/v1",
            "recovery_id": "recovery:" + sha256_bytes(canonical_bytes({"segment_id": self.segment_id, "action": action, "authorization": authorization["signed_payload_sha256"]})),
            "segment_id": self.segment_id, "action": action,
            "before_state": before, "after_state": after,
            "recovery_authorization_sha256": authorization["signed_payload_sha256"],
            "audit_signing_registry_sha256": self.audit_signing_registry_sha256,
            "audit_signer_key_id": self.signer_key_id,
            "recovered_at": _utc(self.clock),
        }
        record = sign_record(unsigned, self.signing_key)
        self.schema_validator.validate("cache_audit_recovery_evidence", record)
        return record

    def recover_dangling_tail(
        self, authorization: dict[str, Any], governance_key: Ed25519PublicKey, *,
        evidence_path: Path,
    ) -> dict[str, Any]:
        """Reconcile a fully signed log tail after interrupted checkpoint/anchor commit."""
        self._verify_governance_record("cache_audit_recovery_authorization", authorization, governance_key)
        descriptor = self._open_locked_log(deadline_monotonic=None)
        try:
            sequence, tail, _records = self._verify_descriptor(descriptor, deadline_monotonic=None)
            checkpoint = self._load_checkpoint()
            anchor = self.anchor_client.read()
            if anchor is None:
                raise AuthorityFailure("cache_audit_integrity_invalid", "external audit anchor is missing")
            expected = {
                "segment_id": self.segment_id,
                "action": "reconcile_signed_dangling_tail",
                "checkpoint_sequence_before": checkpoint["sequence"],
                "checkpoint_tail_before": checkpoint["tail_record_sha256"],
                "log_sequence_after": sequence,
                "log_tail_after": tail,
                "decision": "authorize_governed_recovery",
            }
            if any(authorization.get(key) != value for key, value in expected.items()):
                raise RuntimeError("recovery authorization does not bind the observed state")
            before = {"checkpoint_sequence": checkpoint["sequence"], "checkpoint_tail": checkpoint["tail_record_sha256"], "anchor_state_sha256": self._state_digest(anchor)}
            if sequence != checkpoint["sequence"] + 1:
                raise RuntimeError("governed recovery only accepts one fully signed dangling tail record")
            if anchor["sequence"] == checkpoint["sequence"]:
                last_event = canonical_json_loads(_records[-1]["event_canonical_json"])
                status = "sealed" if last_event["schema_version"] == "cache_audit_segment_seal/v2" else "open"
                unsigned_anchor = self._anchor_unsigned(
                    epoch=anchor["anchor_epoch"], sequence=sequence, tail=tail, segment_status=status,
                    previous_tail=self.previous_sealed_segment_tail_sha256,
                    transition_digest=anchor["transition_authorization_sha256"],
                )
                anchor = self.anchor_client.compare_and_swap(self._state_digest(anchor), unsigned_anchor)
            elif anchor["sequence"] != sequence or anchor["tail_record_sha256"] != tail:
                raise RuntimeError("external anchor is neither before nor at the signed dangling tail")
            self._write_checkpoint(
                sequence=sequence, tail=tail, segment_status=anchor["segment_status"],
                anchor=anchor, deadline_monotonic=None,
            )
            after = {"checkpoint_sequence": sequence, "checkpoint_tail": tail, "anchor_state_sha256": self._state_digest(anchor)}
            evidence = self._signed_recovery_evidence(action="reconcile_signed_dangling_tail", before=before, after=after, authorization=authorization)
            self._write_recovery_evidence(evidence_path, evidence)
            return evidence
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def cleanup_checkpoint_temporaries(
        self, authorization: dict[str, Any], governance_key: Ed25519PublicKey, *, evidence_path: Path,
    ) -> dict[str, Any]:
        self._verify_governance_record("cache_audit_recovery_authorization", authorization, governance_key)
        if authorization.get("segment_id") != self.segment_id or authorization.get("action") != "remove_orphan_checkpoint_temporaries":
            raise RuntimeError("temporary cleanup authorization does not bind this segment")
        pattern = f".{self.checkpoint_path.name}.*.tmp"
        removed: list[str] = []
        for path in sorted(self.checkpoint_path.parent.glob(pattern)):
            info = path.lstat()
            if stat.S_ISREG(info.st_mode) and info.st_uid == self.expected_uid:
                path.unlink()
                removed.append(path.name)
        before = {"temporary_count": len(removed), "temporary_names_sha256": sha256_bytes(canonical_bytes(removed))}
        after = {"temporary_count": 0, "temporary_names_sha256": sha256_bytes(canonical_bytes([]))}
        evidence = self._signed_recovery_evidence(action="remove_orphan_checkpoint_temporaries", before=before, after=after, authorization=authorization)
        self._write_recovery_evidence(evidence_path, evidence)
        return evidence

    def _write_recovery_evidence(self, path: Path, evidence: dict[str, Any]) -> None:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(path.parent, 0o700)
        encoded = canonical_bytes(evidence) + b"\n"
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | O_NOFOLLOW, 0o600)
        try:
            os.write(descriptor, encoded)
            self.fsync(descriptor)
        finally:
            os.close(descriptor)
        self._fsync_directory(path.parent, deadline_monotonic=None)



class UnixSocketAuditPublisherClient:
    """Hard-deadline client for a separately supervised audit persistence service."""
    def __init__(
        self, socket_path: Path, *, verification_keys_by_id: Mapping[str, Ed25519PublicKey],
        audit_signing_registry_sha256: str, schema_validator: CanonicalSchemaValidator,
        expected_socket_uid: int, maximum_response_bytes: int = 4 * 1024 * 1024,
    ):
        self.socket_path = Path(socket_path)
        self.verification_keys_by_id = dict(verification_keys_by_id)
        self.audit_signing_registry_sha256 = audit_signing_registry_sha256
        self.schema_validator = schema_validator
        self.expected_socket_uid = int(expected_socket_uid)
        self.maximum_response_bytes = int(maximum_response_bytes)
        if not self.socket_path.is_absolute():
            raise ValueError("audit publisher socket path must be absolute")

    def _verify_endpoint(self) -> None:
        info = self.socket_path.lstat()
        if not stat.S_ISSOCK(info.st_mode) or info.st_uid != self.expected_socket_uid:
            raise RuntimeError("audit publisher endpoint is not owned by the governed worker identity")
        parent = self.socket_path.parent
        while True:
            item = parent.lstat()
            if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode):
                raise RuntimeError("audit publisher socket ancestry is unsafe")
            if item.st_mode & stat.S_IWOTH:
                sticky_root = item.st_uid == 0 and bool(item.st_mode & stat.S_ISVTX)
                if not sticky_root:
                    raise RuntimeError("audit publisher socket ancestry is world writable")
            if parent == parent.parent:
                break
            parent = parent.parent

    def __call__(self, evidence: dict[str, Any], *, deadline_monotonic: float) -> dict[str, Any]:
        remaining = deadline_monotonic - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("cache audit publisher deadline expired before connection")
        self._verify_endpoint()
        event_bytes = canonical_bytes(evidence)
        event_sha256 = sha256_bytes(event_bytes)
        request = {
            "operation": "publish",
            "event_idempotency_key": "event:" + event_sha256,
            "event_sha256": event_sha256,
            "event": evidence,
        }
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(remaining)
            client.connect(str(self.socket_path))
            client.sendall(canonical_bytes(request) + b"\n")
            chunks: list[bytes] = []
            total = 0
            while True:
                remaining = deadline_monotonic - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("cache audit publisher exceeded the hard request deadline")
                client.settimeout(remaining)
                chunk = client.recv(65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > self.maximum_response_bytes:
                    raise RuntimeError("cache audit publisher response exceeds its governed bound")
                chunks.append(chunk)
                if b"\n" in chunk:
                    break
        raw = b"".join(chunks)
        if not raw.endswith(b"\n") or raw.count(b"\n") != 1:
            raise RuntimeError("cache audit publisher returned no canonical receipt")
        response = canonical_json_loads(raw[:-1].decode("utf-8"))
        if response.get("status") != "ok":
            raise RuntimeError(str(response.get("error", "cache audit publisher rejected the event")))
        receipt = response.get("receipt")
        self.schema_validator.validate("cache_audit_publication_receipt", receipt)
        key = self.verification_keys_by_id.get(receipt.get("audit_signer_key_id"))
        if key is None or not verify_record(receipt, key):
            raise RuntimeError("cache audit publication receipt signature is invalid")
        if (
            receipt.get("event_idempotency_key") != request["event_idempotency_key"]
            or receipt.get("event_sha256") != event_sha256
            or receipt.get("audit_signing_registry_sha256") != self.audit_signing_registry_sha256
        ):
            raise RuntimeError("cache audit publication receipt does not bind the submitted event")
        return receipt

def _supervised_child(write_fd: int, sink_factory: Callable[[], SignedAppendOnlyAuditSink], evidence: dict[str, Any]) -> None:
    try:
        os.setsid()
    except OSError:
        pass
    try:
        result = sink_factory()(evidence, deadline_monotonic=None)
        payload = {"status": "ok", "result": result}
    except BaseException as error:  # child serializes a bounded error, parent fails closed
        payload = {"status": "error", "error_type": type(error).__name__, "error": str(error)[:2048]}
    try:
        os.write(write_fd, canonical_bytes(payload) + b"\n")
    finally:
        os.close(write_fd)
    os._exit(0 if payload["status"] == "ok" else 1)


class SupervisedAuditPublisher:
    """Fork-isolated publisher with a hard request-thread wall-clock bound."""
    def __init__(self, sink_factory: Callable[[], SignedAppendOnlyAuditSink], *, kill_grace_seconds: float = 0.02):
        self.sink_factory = sink_factory
        self.kill_grace_seconds = kill_grace_seconds

    @staticmethod
    def _reap_later(pid: int) -> None:
        def reap() -> None:
            try:
                os.waitpid(pid, 0)
            except ChildProcessError:
                pass
        threading.Thread(target=reap, name=f"audit-reaper-{pid}", daemon=True).start()

    def __call__(self, evidence: dict[str, Any], *, deadline_monotonic: float) -> dict[str, Any]:
        remaining = deadline_monotonic - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("cache audit publication deadline expired before supervision")
        read_fd, write_fd = os.pipe()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*multi-threaded.*fork.*", category=DeprecationWarning)
            pid = os.fork()
        if pid == 0:  # pragma: no cover - exercised through parent integration tests
            os.close(read_fd)
            _supervised_child(write_fd, self.sink_factory, evidence)
        os.close(write_fd)
        os.set_blocking(read_fd, False)
        chunks: list[bytes] = []
        try:
            while True:
                remaining = deadline_monotonic - time.monotonic()
                if remaining <= 0:
                    try:
                        os.killpg(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        try: os.kill(pid, signal.SIGKILL)
                        except ProcessLookupError: pass
                    self._reap_later(pid)
                    raise TimeoutError("cache audit publication exceeded the hard request deadline")
                ready, _, _ = select.select([read_fd], [], [], remaining)
                if not ready:
                    continue
                chunk = os.read(read_fd, 65536)
                if not chunk:
                    break
                chunks.append(chunk)
                if sum(map(len, chunks)) > 4 * 1024 * 1024:
                    raise RuntimeError("supervised audit worker response exceeds its bound")
                if b"\n" in chunk:
                    break
            try:
                _pid, status = os.waitpid(pid, 0)
            except ChildProcessError:
                status = 1
            raw = b"".join(chunks)
            if not raw.endswith(b"\n") or raw.count(b"\n") != 1:
                raise RuntimeError("supervised audit worker returned no canonical result")
            payload = canonical_json_loads(raw[:-1].decode("utf-8"))
            if payload.get("status") != "ok" or status != 0:
                raise RuntimeError(str(payload.get("error", "supervised audit worker failed")))
            return payload["result"]
        finally:
            os.close(read_fd)


__all__ = [
    "AuditAnchorClient", "InMemoryMonotonicAuditAnchor", "UnixSocketAuditAnchorClient",
    "SignedAppendOnlyAuditSink", "SupervisedAuditPublisher", "UnixSocketAuditPublisherClient",
    "validate_governed_signing_registry", "key_validity_evidence",
]
