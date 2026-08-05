#!/usr/bin/env python3
"""Authenticated, cache-verifying proof-check boundary for Draft 5.3.12."""

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
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from proof_authority import (
    AuthorityFailure, CanonicalSchemaValidator, ProofAuthorityService, ProofPolicyResolver,
    _b64url_decode, _private_key_from_bytes, _public_key_from_bytes, _safe_relative_path, canonical_bytes,
    canonical_json_loads, public_key_raw_b64url,
    load_production_authority_service, load_trusted_canonical_json, secure_read_bytes, sha256_bytes, sign_record,
    validate_trusted_root_ancestry, verify_record,
)


IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class DurableIdempotencyStore:
    """Principal-scoped SQLite cache with bounded leases and untrusted rows."""

    SCHEMA_VERSION = 2
    TABLE = "proof_check_idempotency"
    METADATA_TABLE = "idempotency_schema_metadata"
    INDEXES = {"proof_check_idempotency_completed", "proof_check_idempotency_state_lease"}
    TABLE_SQL = """CREATE TABLE proof_check_idempotency (
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
    )"""
    METADATA_SQL = """CREATE TABLE idempotency_schema_metadata (
        schema_version INTEGER PRIMARY KEY NOT NULL CHECK (schema_version = 2),
        canonical_schema_sha256 TEXT NOT NULL CHECK (
            length(canonical_schema_sha256) = 64
            AND canonical_schema_sha256 NOT GLOB '*[^0-9a-f]*'
        )
    )"""
    INDEX_SQL = {
        "proof_check_idempotency_completed":
            "CREATE INDEX proof_check_idempotency_completed ON proof_check_idempotency(state, completed_at)",
        "proof_check_idempotency_state_lease":
            "CREATE INDEX proof_check_idempotency_state_lease ON proof_check_idempotency(state, lease_expires_at)",
    }
    TABLE_XINFO = (
        (0, "principal_id", "TEXT", 1, None, 1, 0),
        (1, "idempotency_key", "TEXT", 1, None, 2, 0),
        (2, "request_sha256", "TEXT", 1, None, 0, 0),
        (3, "state", "TEXT", 1, None, 0, 0),
        (4, "lease_owner", "TEXT", 0, None, 0, 0),
        (5, "lease_expires_at", "REAL", 0, None, 0, 0),
        (6, "result_canonical_json", "TEXT", 0, None, 0, 0),
        (7, "created_at", "REAL", 1, None, 0, 0),
        (8, "completed_at", "REAL", 0, None, 0, 0),
    )
    METADATA_XINFO = (
        (0, "schema_version", "INTEGER", 1, None, 1, 0),
        (1, "canonical_schema_sha256", "TEXT", 1, None, 0, 0),
    )
    INDEX_LAYOUT = {
        "proof_check_idempotency_completed": {
            "unique": 0, "origin": "c", "partial": 0,
            "xinfo": ((0, 3, "state", 0, "BINARY", 1), (1, 8, "completed_at", 0, "BINARY", 1), (2, -1, None, 0, "BINARY", 0)),
        },
        "proof_check_idempotency_state_lease": {
            "unique": 0, "origin": "c", "partial": 0,
            "xinfo": ((0, 3, "state", 0, "BINARY", 1), (1, 5, "lease_expires_at", 0, "BINARY", 1), (2, -1, None, 0, "BINARY", 0)),
        },
        "sqlite_autoindex_proof_check_idempotency_1": {
            "unique": 1, "origin": "pk", "partial": 0,
            "xinfo": ((0, 0, "principal_id", 0, "BINARY", 1), (1, 1, "idempotency_key", 0, "BINARY", 1), (2, -1, None, 0, "BINARY", 0)),
        },
    }

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
            if existing_version == 0:
                existing_objects = connection.execute(
                    "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
                ).fetchall()
                if existing_objects:
                    raise RuntimeError("unversioned idempotency database is not empty")
                self._create_sqlite_schema(connection)
            elif existing_version == 1:
                self._verify_predecessor_sqlite_schema(connection)
                self._migrate_verified_v1_to_v2(connection)
            elif existing_version != self.SCHEMA_VERSION:
                raise RuntimeError("unsupported idempotency SQLite schema version")
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

    @staticmethod
    def _remaining_seconds(deadline_monotonic: float | None) -> float:
        if deadline_monotonic is None:
            return 30.0
        remaining = deadline_monotonic - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("request-wide deadline expired before SQLite operation")
        return min(30.0, remaining)

    def _connect(self, deadline_monotonic: float | None = None) -> sqlite3.Connection:
        self._secure_database_files()
        target = f"/proc/self/fd/{self._directory_fd}/{self.path.name}"
        timeout_seconds = self._remaining_seconds(deadline_monotonic)
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(target, timeout=timeout_seconds, isolation_level=None)
            busy_timeout_ms = max(1, min(30000, int(timeout_seconds * 1000)))
            connection.execute(f"PRAGMA busy_timeout={busy_timeout_ms}")
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=FULL")
            self._secure_database_files()
            if self._initialized:
                self._verify_sqlite_schema(connection)
            self._remaining_seconds(deadline_monotonic)
            return connection
        except Exception:
            if connection is not None:
                connection.close()
            raise

    @staticmethod
    def _normalize_schema_sql(value: str | None) -> str | None:
        return None if value is None else re.sub(r"\s+", " ", value.strip())

    @classmethod
    def _schema_descriptor(cls, *, include_metadata: bool) -> dict[str, Any]:
        master = [
            ("index", name, cls.TABLE, cls._normalize_schema_sql(sql))
            for name, sql in sorted(cls.INDEX_SQL.items())
        ]
        master.extend([
            ("index", "sqlite_autoindex_proof_check_idempotency_1", cls.TABLE, None),
            ("table", cls.TABLE, cls.TABLE, cls._normalize_schema_sql(cls.TABLE_SQL)),
        ])
        tables: dict[str, Any] = {cls.TABLE: cls.TABLE_XINFO}
        if include_metadata:
            master.append(("table", cls.METADATA_TABLE, cls.METADATA_TABLE, cls._normalize_schema_sql(cls.METADATA_SQL)))
            tables[cls.METADATA_TABLE] = cls.METADATA_XINFO
        return {
            "master": sorted(master),
            "tables": tables,
            "indexes": cls.INDEX_LAYOUT,
        }

    @classmethod
    def canonical_schema_sha256(cls) -> str:
        return sha256_bytes(canonical_bytes(cls._schema_descriptor(include_metadata=True)))

    @classmethod
    def _create_sqlite_schema(cls, connection: sqlite3.Connection) -> None:
        connection.execute("BEGIN IMMEDIATE")
        try:
            connection.execute(cls.TABLE_SQL)
            connection.execute(cls.METADATA_SQL)
            for sql in cls.INDEX_SQL.values():
                connection.execute(sql)
            connection.execute(
                f"INSERT INTO {cls.METADATA_TABLE}(schema_version,canonical_schema_sha256) VALUES (?,?)",
                (cls.SCHEMA_VERSION, cls.canonical_schema_sha256()),
            )
            connection.execute(f"PRAGMA user_version={cls.SCHEMA_VERSION}")
            connection.execute("COMMIT")
        except Exception:
            cls._rollback(connection)
            raise

    @classmethod
    def _migrate_verified_v1_to_v2(cls, connection: sqlite3.Connection) -> None:
        connection.execute("BEGIN IMMEDIATE")
        try:
            connection.execute(cls.METADATA_SQL)
            connection.execute(
                f"INSERT INTO {cls.METADATA_TABLE}(schema_version,canonical_schema_sha256) VALUES (?,?)",
                (cls.SCHEMA_VERSION, cls.canonical_schema_sha256()),
            )
            connection.execute(f"PRAGMA user_version={cls.SCHEMA_VERSION}")
            connection.execute("COMMIT")
        except Exception:
            cls._rollback(connection)
            raise

    @classmethod
    def _verify_exact_schema_objects(cls, connection: sqlite3.Connection, *, include_metadata: bool) -> None:
        expected = cls._schema_descriptor(include_metadata=include_metadata)
        observed_master = [
            (kind, name, table, cls._normalize_schema_sql(sql))
            for kind, name, table, sql in connection.execute(
                "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
            ).fetchall()
        ]
        if observed_master != expected["master"]:
            raise RuntimeError("idempotency SQLite schema normalized table/index SQL mismatch")
        for table, expected_xinfo in expected["tables"].items():
            observed_xinfo = tuple(connection.execute(f"PRAGMA table_xinfo({table})").fetchall())
            if observed_xinfo != tuple(expected_xinfo):
                raise RuntimeError(f"idempotency SQLite schema table_xinfo mismatch: {table}")
        index_list = {
            row[1]: {"unique": row[2], "origin": row[3], "partial": row[4]}
            for row in connection.execute(f"PRAGMA index_list({cls.TABLE})").fetchall()
        }
        expected_index_list = {
            name: {key: value for key, value in layout.items() if key != "xinfo"}
            for name, layout in cls.INDEX_LAYOUT.items()
        }
        if index_list != expected_index_list:
            raise RuntimeError("idempotency SQLite schema index_list mismatch")
        for name, layout in cls.INDEX_LAYOUT.items():
            if tuple(connection.execute(f"PRAGMA index_xinfo({name})").fetchall()) != tuple(layout["xinfo"]):
                raise RuntimeError(f"idempotency SQLite schema index_xinfo mismatch: {name}")

    @classmethod
    def _verify_predecessor_sqlite_schema(cls, connection: sqlite3.Connection) -> None:
        if connection.execute("PRAGMA quick_check").fetchone() != ("ok",):
            raise RuntimeError("idempotency SQLite integrity check failed before migration")
        if int(connection.execute("PRAGMA user_version").fetchone()[0]) != 1:
            raise RuntimeError("idempotency SQLite predecessor schema version mismatch")
        cls._verify_exact_schema_objects(connection, include_metadata=False)

    def _verify_sqlite_schema(self, connection: sqlite3.Connection) -> None:
        quick_check = connection.execute("PRAGMA quick_check").fetchone()
        if quick_check != ("ok",):
            raise RuntimeError("idempotency SQLite integrity check failed")
        integrity_check = connection.execute("PRAGMA integrity_check(1)").fetchone()
        if integrity_check != ("ok",):
            raise RuntimeError("idempotency SQLite full integrity check failed")
        if int(connection.execute("PRAGMA user_version").fetchone()[0]) != self.SCHEMA_VERSION:
            raise RuntimeError("idempotency SQLite schema version mismatch")
        self._verify_exact_schema_objects(connection, include_metadata=True)
        metadata = connection.execute(
            f"SELECT schema_version,canonical_schema_sha256 FROM {self.METADATA_TABLE}"
        ).fetchall()
        if metadata != [(self.SCHEMA_VERSION, self.canonical_schema_sha256())]:
            raise RuntimeError("idempotency SQLite canonical schema digest mismatch")

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

    def acquire(self, principal_id: str, key: str, request_sha256: str, *, deadline_monotonic: float | None = None) -> tuple[str, str | dict[str, Any] | None]:
        now = time.time()
        owner = uuid.uuid4().hex
        with closing(self._connect(deadline_monotonic)) as connection:
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

    def complete(self, principal_id: str, key: str, owner: str, request_sha256: str, envelope: dict[str, Any], *, deadline_monotonic: float | None = None) -> None:
        canonical_result = canonical_bytes(envelope).decode("utf-8")
        encoded_size = len(canonical_result.encode("utf-8"))
        if encoded_size > self.maximum_cache_envelope_bytes:
            raise RuntimeError("idempotency cache envelope byte limit exceeded")
        if self._database_size() + 2 * encoded_size + 65536 >= self.maximum_database_bytes:
            raise RuntimeError("idempotency database completion byte limit exceeded")
        now = time.time()
        with closing(self._connect(deadline_monotonic)) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                changed = connection.execute(
                    "UPDATE proof_check_idempotency SET state='completed',lease_owner=NULL,lease_expires_at=NULL,result_canonical_json=?,completed_at=? WHERE principal_id=? AND idempotency_key=? AND request_sha256=? AND state='inflight' AND lease_owner=? AND lease_expires_at>?",
                    (canonical_result, now, principal_id, key, request_sha256, owner, now),
                ).rowcount
                if changed != 1:
                    raise RuntimeError("idempotency completion lease was lost")
                self._remaining_seconds(deadline_monotonic)
                connection.execute("COMMIT")
                connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                try:
                    self._remaining_seconds(deadline_monotonic)
                except TimeoutError:
                    connection.execute("BEGIN IMMEDIATE")
                    connection.execute(
                        "DELETE FROM proof_check_idempotency WHERE principal_id=? AND idempotency_key=? AND state='completed' AND request_sha256=?",
                        (principal_id, key, request_sha256),
                    )
                    connection.execute("COMMIT")
                    connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    raise
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

    def renew(self, principal_id: str, key: str, owner: str, request_sha256: str, *, deadline_monotonic: float | None = None) -> bool:
        """Atomically extend only the live lease owned by this exact worker."""
        now = time.time()
        with closing(self._connect(deadline_monotonic)) as connection:
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

    def abandon(self, principal_id: str, key: str, owner: str, *, deadline_monotonic: float | None = None) -> None:
        with closing(self._connect(deadline_monotonic)) as connection:
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


def _parse_registry_datetime(value: str, field: str) -> datetime:
    if not isinstance(value, str):
        raise RuntimeError(f"cache-signing registry {field} must be an RFC 3339 date-time")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise RuntimeError(f"cache-signing registry {field} is malformed") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RuntimeError(f"cache-signing registry {field} must include a UTC offset")
    return parsed.astimezone(timezone.utc)


def validate_cache_signing_registry_lineage(
    registry: dict[str, Any], *, evaluated_at: datetime | None = None,
) -> dict[str, dict[str, Any]]:
    """Validate unique, time-coherent, complete, acyclic cache-key lineage."""
    now = (evaluated_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    keys = registry.get("keys")
    if not isinstance(keys, list) or not keys:
        raise RuntimeError("cache-signing registry contains no keys")
    by_id: dict[str, dict[str, Any]] = {}
    parsed_times: dict[str, tuple[datetime, datetime | None, datetime]] = {}
    for record in keys:
        key_id = record.get("key_id") if isinstance(record, dict) else None
        if not isinstance(key_id, str) or not IDENTIFIER.fullmatch(key_id) or key_id in by_id:
            raise RuntimeError("cache-signing registry key identifiers are invalid or duplicated")
        valid_from = _parse_registry_datetime(record.get("valid_from"), f"{key_id}.valid_from")
        valid_until_value = record.get("valid_until")
        valid_until = None if valid_until_value is None else _parse_registry_datetime(valid_until_value, f"{key_id}.valid_until")
        status_changed = _parse_registry_datetime(record.get("status_changed_at"), f"{key_id}.status_changed_at")
        status = record.get("status")
        if status not in {"active", "retired", "revoked"}:
            raise RuntimeError("cache-signing registry status is invalid")
        if valid_until is not None and valid_from >= valid_until:
            raise RuntimeError("cache-signing registry validity interval is empty or reversed")
        if status_changed < valid_from:
            raise RuntimeError("cache-signing registry status predates key validity")
        if status_changed > now:
            raise RuntimeError("cache-signing registry status change lies in the future")
        if status == "active" and valid_until is not None and status_changed >= valid_until:
            raise RuntimeError("active cache-signing status is outside the key validity interval")
        if status == "retired":
            if valid_until is None or status_changed != valid_until:
                raise RuntimeError("retired cache-signing status must take effect exactly at valid_until")
        if status == "revoked" and valid_until is not None and status_changed > valid_until:
            raise RuntimeError("revoked cache-signing status change is after valid_until")
        by_id[key_id] = record
        parsed_times[key_id] = (valid_from, valid_until, status_changed)
    for key_id, record in by_id.items():
        predecessor_id = record.get("rotation_predecessor_key_id")
        if predecessor_id is None:
            continue
        predecessor = by_id.get(predecessor_id)
        if predecessor is None:
            raise RuntimeError("cache-signing rotation predecessor is missing")
        if predecessor_id == key_id:
            raise RuntimeError("cache-signing rotation lineage contains a self-cycle")
        if (
            predecessor.get("principal_id") != record.get("principal_id")
            or predecessor.get("authorization_scope") != record.get("authorization_scope")
        ):
            raise RuntimeError("cache-signing rotation predecessor changes principal or scope")
        if parsed_times[predecessor_id][0] >= parsed_times[key_id][0]:
            raise RuntimeError("cache-signing rotation predecessor is not older than its successor")
        if predecessor.get("status") not in {"retired", "revoked"}:
            raise RuntimeError("cache-signing rotation predecessor remains active")
        if parsed_times[predecessor_id][2] > parsed_times[key_id][0]:
            raise RuntimeError("cache-signing successor predates predecessor retirement or revocation")
    for root in by_id:
        visited: set[str] = set()
        current: str | None = root
        while current is not None:
            if current in visited:
                raise RuntimeError("cache-signing rotation lineage contains a cycle")
            visited.add(current)
            current = by_id[current].get("rotation_predecessor_key_id")
    return by_id


@dataclass(frozen=True)
class GovernedCacheRegistrySnapshot:
    """One governance-signed cache registry plus its signed successor policy."""

    registry_sha256: str
    registry_id: str
    registry_created_at: str
    registry_signed_payload_sha256: str
    records_by_id: dict[str, dict[str, Any]]
    verification_keys_by_id: dict[str, Ed25519PublicKey]
    successor_registry_sha256: str | None
    stale_replay_policy: str
    revoked_key_ids: frozenset[str]
    lineage_signed_payload_sha256: str | None


def build_governed_cache_registry_snapshot(
    registry: dict[str, Any], governance_key: Ed25519PublicKey, *,
    successor_registry_sha256: str | None,
    stale_replay_policy: str,
    revoked_key_ids: frozenset[str] = frozenset(),
    lineage_signed_payload_sha256: str | None,
    evaluated_at: datetime | None = None,
) -> GovernedCacheRegistrySnapshot:
    """Validate a signed immutable registry before extracting any replay key."""
    if not verify_record(registry, governance_key):
        raise RuntimeError("cache-signing registry governance signature is invalid")
    registry_sha256 = sha256_bytes(canonical_bytes(registry))
    if successor_registry_sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", successor_registry_sha256):
        raise RuntimeError("historical cache-registry successor digest is invalid")
    if stale_replay_policy not in {"current_registry", "authenticate_then_conflict"}:
        raise RuntimeError("historical cache-registry replay policy is invalid")
    created_at = _parse_registry_datetime(registry.get("created_at"), "registry.created_at")
    records = validate_cache_signing_registry_lineage(registry, evaluated_at=evaluated_at or created_at)
    if not revoked_key_ids.issubset(records):
        raise RuntimeError("historical cache-registry revocation policy names an unknown key")
    keys: dict[str, Ed25519PublicKey] = {}
    for key_id, record in records.items():
        raw = _b64url_decode(record.get("public_key_base64url", ""))
        if len(raw) != 32:
            raise RuntimeError("cache-signing registry contains a non-Ed25519 public key")
        keys[key_id] = Ed25519PublicKey.from_public_bytes(raw)
    return GovernedCacheRegistrySnapshot(
        registry_sha256=registry_sha256,
        registry_id=str(registry.get("registry_id", "")),
        registry_created_at=registry["created_at"],
        registry_signed_payload_sha256=registry["signed_payload_sha256"],
        records_by_id=records,
        verification_keys_by_id=keys,
        successor_registry_sha256=successor_registry_sha256,
        stale_replay_policy=stale_replay_policy,
        revoked_key_ids=frozenset(revoked_key_ids),
        lineage_signed_payload_sha256=lineage_signed_payload_sha256,
    )


def validate_cache_registry_snapshot_lineage(
    snapshots: dict[str, GovernedCacheRegistrySnapshot], *, current_registry_sha256: str,
    production_mode: bool,
) -> dict[str, tuple[str, ...]]:
    """Require every governed historical snapshot to terminate at the current registry."""
    if current_registry_sha256 not in snapshots:
        raise ValueError("cache registry snapshots omit the current registry")
    current = snapshots[current_registry_sha256]
    if current.registry_sha256 != current_registry_sha256:
        raise ValueError("cache registry snapshot map key differs from its canonical digest")
    if current.successor_registry_sha256 is not None or current.stale_replay_policy != "current_registry":
        raise ValueError("current cache registry has a historical successor or stale policy")
    paths: dict[str, tuple[str, ...]] = {}
    for digest_value, snapshot in snapshots.items():
        if digest_value != snapshot.registry_sha256:
            raise ValueError("cache registry snapshot map key differs from its canonical digest")
        if production_mode and snapshot.lineage_signed_payload_sha256 is None:
            raise ValueError("production cache registry snapshot lacks signed lineage evidence")
        if snapshot.lineage_signed_payload_sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", snapshot.lineage_signed_payload_sha256):
            raise ValueError("cache registry snapshot lineage digest is invalid")
        if digest_value != current_registry_sha256:
            if snapshot.stale_replay_policy != "authenticate_then_conflict" or snapshot.successor_registry_sha256 is None:
                raise ValueError("historical cache registry lacks a fail-closed successor policy")
        visited: list[str] = []
        cursor: str | None = digest_value
        while cursor != current_registry_sha256:
            if cursor is None or cursor not in snapshots:
                raise ValueError("historical cache registry lineage does not reach the current registry")
            if cursor in visited:
                raise ValueError("historical cache registry lineage contains a cycle")
            visited.append(cursor)
            successor = snapshots[cursor].successor_registry_sha256
            if successor in visited:
                raise ValueError("historical cache registry lineage contains a cycle")
            if successor is not None and successor in snapshots:
                predecessor_time = _parse_registry_datetime(snapshots[cursor].registry_created_at, "historical.registry_created_at")
                successor_time = _parse_registry_datetime(snapshots[successor].registry_created_at, "successor.registry_created_at")
                if predecessor_time >= successor_time:
                    raise ValueError("historical cache registry chronology is not strictly increasing")
            cursor = successor
        paths[digest_value] = tuple([*visited, current_registry_sha256])
    return paths


def load_governed_cache_registry_snapshots(
    config_root: Path, lineage_relative_path: str, *, expected_uid: int,
    schema_validator: CanonicalSchemaValidator, governance_key: Ed25519PublicKey,
    current_registry: dict[str, Any], evaluated_at: datetime,
) -> dict[str, GovernedCacheRegistrySnapshot]:
    """Load governance-signed historical registries through the protected root."""
    lineage = load_trusted_canonical_json(config_root, lineage_relative_path, expected_uid=expected_uid)
    schema_validator.validate("cache_registry_lineage", lineage)
    if not verify_record(lineage, governance_key):
        raise RuntimeError("cache registry lineage governance signature is invalid")
    lineage_created_at = _parse_registry_datetime(lineage.get("created_at"), "lineage.created_at")
    if lineage_created_at > evaluated_at:
        raise RuntimeError("cache registry lineage was created in the future")
    current_digest = sha256_bytes(canonical_bytes(current_registry))
    if lineage.get("current_registry_sha256") != current_digest:
        raise RuntimeError("cache registry lineage does not bind the selected current registry")
    lineage_payload_sha256 = lineage["signed_payload_sha256"]
    snapshots: dict[str, GovernedCacheRegistrySnapshot] = {
        current_digest: build_governed_cache_registry_snapshot(
            current_registry, governance_key,
            successor_registry_sha256=None, stale_replay_policy="current_registry",
            lineage_signed_payload_sha256=lineage_payload_sha256, evaluated_at=evaluated_at,
        ),
    }
    seen_files: set[str] = set()
    for entry in lineage["historical_registries"]:
        registry_digest = entry["registry_sha256"]
        registry_file = entry["registry_file"]
        if registry_digest == current_digest or registry_digest in snapshots or registry_file in seen_files:
            raise RuntimeError("cache registry lineage contains a duplicate current, digest, or file entry")
        seen_files.add(registry_file)
        historical_registry = load_trusted_canonical_json(config_root, registry_file, expected_uid=expected_uid)
        schema_validator.validate("cache_signing_registry", historical_registry)
        if sha256_bytes(canonical_bytes(historical_registry)) != registry_digest:
            raise RuntimeError("historical cache registry digest differs from its signed lineage")
        snapshots[registry_digest] = build_governed_cache_registry_snapshot(
            historical_registry, governance_key,
            successor_registry_sha256=entry["successor_registry_sha256"],
            stale_replay_policy=entry["stale_replay_policy"],
            revoked_key_ids=frozenset(entry["revoked_key_ids"]),
            lineage_signed_payload_sha256=lineage_payload_sha256,
        )
    validate_cache_registry_snapshot_lineage(snapshots, current_registry_sha256=current_digest, production_mode=True)
    return snapshots


class ProofCheckApplication:
    def __init__(
        self, authority: ProofAuthorityService, artifact_store: Path,
        policy_resolver: ProofPolicyResolver, *,
        idempotency_store: DurableIdempotencyStore | None = None,
        schema_validator: CanonicalSchemaValidator | None = None,
        cache_signing_key: Ed25519PrivateKey | None = None,
        cache_verification_key: Ed25519PublicKey | None = None,
        cache_verification_keys_by_id: dict[str, Ed25519PublicKey] | None = None,
        compiler_witness_verification_key: Ed25519PublicKey | None = None,
        cache_signer_principal_id: str = "cache-signer:development",
        cache_signer_key_id: str = "cache-key:development",
        cache_key_record: dict[str, Any] | None = None,
        cache_registry_sha256: str | None = None,
        cache_registry_snapshots_by_sha256: dict[str, GovernedCacheRegistrySnapshot] | None = None,
        cache_clock: Callable[[], datetime] | None = None,
        cache_verification_evidence_sink: Callable[[dict[str, Any]], None] | None = None,
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
        self.cache_verification_keys_by_id = dict(cache_verification_keys_by_id or {
            self.cache_signer_key_id: self.cache_verification_key,
        })
        selected_verification_key = self.cache_verification_keys_by_id.get(self.cache_signer_key_id)
        if selected_verification_key is None or public_key_raw_b64url(selected_verification_key) != public_key_raw_b64url(self.cache_verification_key):
            raise ValueError("cache verification keyring omits or changes the selected signing key")
        if (
            self.cache_signer_key_id == self.authority_key_id
            or self.cache_signer_principal_id == self.authority_principal_id
            or public_key_raw_b64url(self.cache_verification_key) == public_key_raw_b64url(self.compiler_witness_verification_key)
        ):
            raise ValueError("cache and compiler-witness signing authorities must be distinct")
        self.cache_clock = cache_clock or (lambda: datetime.now(timezone.utc))
        if cache_key_record is None:
            if production_mode:
                raise ValueError("production requires a governed cache-key lifecycle record")
            cache_key_record = {
                "key_id": self.cache_signer_key_id,
                "principal_id": self.cache_signer_principal_id,
                "public_key_base64url": public_key_raw_b64url(self.cache_verification_key),
                "authorization_scope": "idempotency_cache_envelope_signing",
                "status": "active", "valid_from": "1970-01-01T00:00:00+00:00",
                "valid_until": None, "status_changed_at": "1970-01-01T00:00:00+00:00",
                "rotation_predecessor_key_id": None,
            }
        self.cache_key_record = dict(cache_key_record)
        self.cache_registry_sha256 = cache_registry_sha256 or sha256_bytes(canonical_bytes({
            "development_cache_key": self.cache_key_record,
        }))
        if not re.fullmatch(r"[0-9a-f]{64}", self.cache_registry_sha256):
            raise ValueError("cache-signing registry snapshot digest is invalid")
        if cache_registry_snapshots_by_sha256 is None:
            cache_registry_snapshots_by_sha256 = {
                self.cache_registry_sha256: GovernedCacheRegistrySnapshot(
                    registry_sha256=self.cache_registry_sha256,
                    registry_id="development:current",
                    registry_created_at=self.cache_key_record["status_changed_at"],
                    registry_signed_payload_sha256=self.cache_registry_sha256,
                    records_by_id={self.cache_signer_key_id: self.cache_key_record},
                    verification_keys_by_id=dict(self.cache_verification_keys_by_id),
                    successor_registry_sha256=None,
                    stale_replay_policy="current_registry",
                    revoked_key_ids=frozenset(),
                    lineage_signed_payload_sha256=None,
                ),
            }
        self.cache_registry_snapshots_by_sha256 = dict(cache_registry_snapshots_by_sha256)
        self.cache_registry_lineage_paths = validate_cache_registry_snapshot_lineage(
            self.cache_registry_snapshots_by_sha256,
            current_registry_sha256=self.cache_registry_sha256,
            production_mode=production_mode,
        )
        current_snapshot = self.cache_registry_snapshots_by_sha256[self.cache_registry_sha256]
        current_record = current_snapshot.records_by_id.get(self.cache_signer_key_id)
        current_key = current_snapshot.verification_keys_by_id.get(self.cache_signer_key_id)
        if current_record != self.cache_key_record or current_key is None or public_key_raw_b64url(current_key) != public_key_raw_b64url(self.cache_verification_key):
            raise ValueError("current cache registry snapshot changes the selected signing authority")
        self.cache_verification_evidence_sink = cache_verification_evidence_sink or (lambda evidence: None)
        self._cache_key_validity_decision(use="signing")

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

    def _cache_key_validity_decision(
        self, *, use: str, signed_at: datetime | None = None, evaluated_at: datetime | None = None,
    ) -> dict[str, Any]:
        if use not in {"signing", "replay"}:
            raise ValueError("unknown cache-key validity use")
        record = self.cache_key_record
        now = (evaluated_at or self.cache_clock()).astimezone(timezone.utc)
        valid_from = _parse_registry_datetime(record.get("valid_from"), "selected.valid_from")
        valid_until_value = record.get("valid_until")
        valid_until = None if valid_until_value is None else _parse_registry_datetime(valid_until_value, "selected.valid_until")
        status_changed = _parse_registry_datetime(record.get("status_changed_at"), "selected.status_changed_at")
        if (
            record.get("key_id") != self.cache_signer_key_id
            or record.get("principal_id") != self.cache_signer_principal_id
            or record.get("authorization_scope") != "idempotency_cache_envelope_signing"
            or record.get("public_key_base64url") != public_key_raw_b64url(self.cache_verification_key)
        ):
            raise AuthorityFailure("cache_integrity_invalid", "cache key differs from its governed registry authorization")
        if record.get("status") != "active":
            raise AuthorityFailure("cache_integrity_invalid", "retired or revoked cache keys cannot sign or replay cache rows")
        if status_changed > now:
            raise AuthorityFailure("cache_integrity_invalid", "cache key status change lies in the future")
        if status_changed < valid_from or (valid_until is not None and status_changed >= valid_until):
            raise AuthorityFailure("cache_integrity_invalid", "cache key status chronology is outside its governed validity interval")
        if now < valid_from or now < status_changed or (valid_until is not None and now >= valid_until):
            raise AuthorityFailure("cache_integrity_invalid", "cache key is outside its governed validity interval")
        if signed_at is not None:
            signed_at = signed_at.astimezone(timezone.utc)
            if signed_at < valid_from or (valid_until is not None and signed_at >= valid_until) or signed_at > now:
                raise AuthorityFailure("cache_integrity_invalid", "cache row signing time is outside the governed key interval")
        return {
            "schema_version": "cache_key_validity_evidence/v1",
            "registry_sha256": self.cache_registry_sha256,
            "key_id": self.cache_signer_key_id,
            "principal_id": self.cache_signer_principal_id,
            "status": "active",
            "valid_from": record["valid_from"],
            "valid_until": record.get("valid_until"),
            "status_changed_at": record["status_changed_at"],
            "rotation_predecessor_key_id": record.get("rotation_predecessor_key_id"),
            "use": use,
            "decision": "active_time_valid_rotation_valid",
            "evaluated_at": now.isoformat(),
        }

    @staticmethod
    def _check_deadline(deadline_monotonic: float, stage: str) -> float:
        remaining = deadline_monotonic - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"request-wide deadline expired {stage}")
        return remaining

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

    def _cache_envelope(
        self, result: dict[str, Any], request: dict[str, Any], principal_id: str,
        request_sha256: str, deadline_monotonic: float,
    ) -> dict[str, Any]:
        self._check_deadline(deadline_monotonic, "before cache-envelope signing")
        signed_at = self.cache_clock().astimezone(timezone.utc)
        validity_evidence = self._cache_key_validity_decision(
            use="signing", signed_at=signed_at, evaluated_at=signed_at,
        )
        identity = {
            "request_sha256": request_sha256, "authenticated_principal_id": principal_id,
            "compiler_witness_signed_payload_sha256": result["compiler_witness"]["signed_payload_sha256"],
        }
        unsigned = {
            "schema_version": "idempotency_cache_envelope/v3",
            "cache_envelope_id": "cache:" + sha256_bytes(canonical_bytes(identity)),
            "request_sha256": request_sha256, "request_id": request["request_id"],
            "idempotency_key": request["idempotency_key"], "authenticated_principal_id": principal_id,
            "claim_id": request["claim_id"], "compiler_profile_id": request["compiler_profile_id"],
            "policy_decision_id": result["policy_decision_id"],
            "policy_decision_sha256": result["policy_decision_sha256"],
            "source_bundle_id": request["source_bundle_id"],
            "cache_signer_principal_id": self.cache_signer_principal_id,
            "cache_signer_key_id": self.cache_signer_key_id,
            "cache_registry_sha256": self.cache_registry_sha256,
            "cache_signed_at": signed_at.isoformat(),
            "cache_key_validity_evidence": validity_evidence,
            "result": result,
        }
        envelope = sign_record(unsigned, self.cache_signing_key)
        self._check_deadline(deadline_monotonic, "after cache-envelope signing")
        self.schema_validator.validate("idempotency_cache_envelope", envelope)
        self._check_deadline(deadline_monotonic, "after cache-envelope validation")
        return envelope

    @staticmethod
    def _validate_snapshot_signing_evidence(
        envelope: dict[str, Any], snapshot: GovernedCacheRegistrySnapshot,
        record: dict[str, Any], signed_at: datetime,
    ) -> dict[str, Any]:
        """Reconstruct the old signing decision only after signature authentication."""
        if record.get("status") != "active":
            raise AuthorityFailure(
                "cache_integrity_invalid",
                "cache row signer was retired or revoked and was not active in its signed registry snapshot",
            )
        valid_from = _parse_registry_datetime(record.get("valid_from"), "historical.valid_from")
        valid_until_value = record.get("valid_until")
        valid_until = None if valid_until_value is None else _parse_registry_datetime(valid_until_value, "historical.valid_until")
        status_changed = _parse_registry_datetime(record.get("status_changed_at"), "historical.status_changed_at")
        if signed_at < valid_from or signed_at < status_changed or (valid_until is not None and signed_at >= valid_until):
            raise AuthorityFailure("cache_integrity_invalid", "cache row signing time is outside its historical governed key interval")
        evidence = envelope.get("cache_key_validity_evidence")
        expected = {
            "schema_version": "cache_key_validity_evidence/v1",
            "registry_sha256": snapshot.registry_sha256,
            "key_id": record["key_id"], "principal_id": record["principal_id"], "status": "active",
            "valid_from": record["valid_from"], "valid_until": record.get("valid_until"),
            "status_changed_at": record["status_changed_at"],
            "rotation_predecessor_key_id": record.get("rotation_predecessor_key_id"),
            "use": "signing", "decision": "active_time_valid_rotation_valid",
            "evaluated_at": envelope.get("cache_signed_at"),
        }
        if not isinstance(evidence, dict) or evidence != expected:
            raise AuthorityFailure("cache_integrity_invalid", "cache signing-time validity evidence is invalid")
        return evidence

    def _cached_result(
        self, envelope: dict[str, Any], request: dict[str, Any], principal_id: str,
        request_sha256: str, resolved_policy,
    ) -> dict[str, Any]:
        # Replay order: canonical parse; schema; signer lookup; signature;
        # signed snapshot lineage; stale evidence; stable conflict.
        self.schema_validator.validate("idempotency_cache_envelope", envelope)
        stored_key_id = envelope.get("cache_signer_key_id")
        stored_registry_sha256 = envelope.get("cache_registry_sha256")
        snapshot = self.cache_registry_snapshots_by_sha256.get(stored_registry_sha256)
        if snapshot is None:
            raise AuthorityFailure("cache_integrity_invalid", "idempotency-cache registry snapshot is unknown or ungoverned")
        stored_verification_key = snapshot.verification_keys_by_id.get(stored_key_id)
        stored_record = snapshot.records_by_id.get(stored_key_id)
        if stored_verification_key is None or stored_record is None:
            raise AuthorityFailure("cache_integrity_invalid", "idempotency-cache signer is absent from its governed registry snapshot")
        if not verify_record(envelope, stored_verification_key):
            raise AuthorityFailure("cache_integrity_invalid", "idempotency-cache envelope signature is invalid")
        lineage_paths = validate_cache_registry_snapshot_lineage(
            self.cache_registry_snapshots_by_sha256,
            current_registry_sha256=self.cache_registry_sha256,
            production_mode=any(item.lineage_signed_payload_sha256 is not None for item in self.cache_registry_snapshots_by_sha256.values()),
        )
        signed_at = _parse_registry_datetime(envelope.get("cache_signed_at"), "cache_signed_at")
        signing_evidence = self._validate_snapshot_signing_evidence(envelope, snapshot, stored_record, signed_at)
        if envelope.get("cache_signer_principal_id") != stored_record.get("principal_id"):
            raise AuthorityFailure("cache_integrity_invalid", "idempotency-cache signer principal differs from its governed snapshot")
        if stored_registry_sha256 != self.cache_registry_sha256:
            if stored_key_id in snapshot.revoked_key_ids:
                raise AuthorityFailure("cache_integrity_invalid", "revoked historical cache signer cannot support rotation classification")
            if snapshot.stale_replay_policy != "authenticate_then_conflict":
                raise AuthorityFailure("cache_integrity_invalid", "historical cache registry has no governed stale-row policy")
            stale_evidence = {
                "schema_version": "cache_stale_row_evidence/v2",
                "cache_envelope_id": envelope["cache_envelope_id"],
                "stored_cache_registry_sha256": stored_registry_sha256,
                "current_cache_registry_sha256": self.cache_registry_sha256,
                "historical_registry_id": snapshot.registry_id,
                "historical_registry_signed_payload_sha256": snapshot.registry_signed_payload_sha256,
                "registry_lineage_signed_payload_sha256": snapshot.lineage_signed_payload_sha256,
                "cache_signer_key_id": stored_key_id,
                "cache_signer_principal_id": stored_record["principal_id"],
                "signature_verified": True, "registry_lineage_verified": True,
                "registry_lineage_path": list(lineage_paths[stored_registry_sha256]),
                "historical_replay_policy": snapshot.stale_replay_policy,
                "decision": "reject_preserve_row_require_new_idempotency_key",
                "reason": "authenticated_cache_signing_registry_replaced_or_rotated",
                "evaluated_at": self.cache_clock().astimezone(timezone.utc).isoformat(),
            }
            self.schema_validator.validate("cache_stale_row_evidence", stale_evidence)
            self.cache_verification_evidence_sink(stale_evidence)
            raise AuthorityFailure(
                "cache_key_rotation_requires_new_idempotency_key",
                "authenticated cached result uses a superseded cache-signing registry; submit a new idempotency key",
            )
        replay_evidence = self._cache_key_validity_decision(use="replay", signed_at=signed_at)
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
        self.cache_verification_evidence_sink({
            "schema_version": "cache_verification_evidence/v1",
            "cache_envelope_id": envelope["cache_envelope_id"],
            "cache_registry_sha256": self.cache_registry_sha256,
            "signing_decision": signing_evidence,
            "replay_decision": replay_evidence,
            "compiler_witness_signed_payload_sha256": result["compiler_witness"]["signed_payload_sha256"],
        })
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
        self._check_deadline(deadline, "before idempotency acquisition")
        owner: str | None = None
        while owner is None:
            action, value = self.idempotency_store.acquire(
                principal_id, idempotency_key, request_sha256, deadline_monotonic=deadline,
            )
            if action == "completed":
                assert isinstance(value, dict)
                self._check_deadline(deadline, "before cached-result verification")
                cached = self._cached_result(value, request, principal_id, request_sha256, resolved_policy)
                self._check_deadline(deadline, "after cached-result verification")
                return cached
            if action == "execute":
                owner = str(value)
                break
            if time.monotonic() >= deadline:
                raise TimeoutError("timed out waiting for an in-flight idempotent request")
            time.sleep(0.05)
        stop_heartbeat = threading.Event()
        lease_lost = threading.Event()

        def renew_lease() -> None:
            # Keep the heartbeat proportional even for deliberately short
            # stress-test leases.  A 50 ms floor could consume most of a
            # sub-second lease and lose ownership under ordinary contention.
            interval = max(0.001, min(30.0, self.idempotency_store.lease_seconds / 3.0))
            while not stop_heartbeat.wait(interval):
                try:
                    if not self.idempotency_store.renew(
                        principal_id, idempotency_key, owner, request_sha256,
                        deadline_monotonic=deadline,
                    ):
                        lease_lost.set()
                        return
                except Exception:
                    lease_lost.set()
                    return

        heartbeat = threading.Thread(target=renew_lease, name="idempotency-lease-renewal", daemon=True)
        heartbeat.start()
        try:
            self._check_deadline(deadline, "before authority execution")
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
            self._check_deadline(deadline, "after authority execution and witness signing")
            self.schema_validator.validate("compiler_witness", compiler_witness)
            self._check_deadline(deadline, "after compiler-witness validation")
            result = {
                "schema_version": "proof_check_service_result/v7",
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
            self._check_deadline(deadline, "after final result-binding validation")
            envelope = self._cache_envelope(result, request, principal_id, request_sha256, deadline)
            stop_heartbeat.set()
            heartbeat.join(timeout=2)
            self._check_deadline(deadline, "before final lease renewal")
            if lease_lost.is_set() or not self.idempotency_store.renew(
                principal_id, idempotency_key, owner, request_sha256,
                deadline_monotonic=deadline,
            ):
                raise RuntimeError("idempotency execution lease was lost before publication")
            self._check_deadline(deadline, "after final lease renewal")
            self._check_deadline(deadline, "before durable cache completion")
            self.idempotency_store.complete(
                principal_id, idempotency_key, owner, request_sha256, envelope,
                deadline_monotonic=deadline,
            )
            self._check_deadline(deadline, "after durable cache completion")
            return json.loads(json.dumps(result))
        except Exception:
            stop_heartbeat.set()
            heartbeat.join(timeout=2)
            self.idempotency_store.abandon(principal_id, idempotency_key, owner)
            raise


def load_production_application(config_root: Path = Path("/etc/witness-authority")) -> ProofCheckApplication:
    expected_uid = os.getuid()
    if expected_uid == 0 or os.getgid() == 0:
        raise AuthorityFailure("root_execution_forbidden", "production proof-check application must run as a non-root service identity")
    validate_trusted_root_ancestry(config_root, expected_uid=expected_uid)
    config = load_trusted_canonical_json(config_root, "service-config.json", expected_uid=expected_uid)
    artifact_store = Path(config["artifact_store_root"])
    if not artifact_store.is_absolute() or not artifact_store.is_dir() or artifact_store.is_symlink():
        raise RuntimeError("artifact store must be an absolute non-symlink directory")
    governance_key = _public_key_from_bytes(secure_read_bytes(config_root, config["governance_public_key_file"], expected_uid=os.getuid()))
    policy_registry = load_trusted_canonical_json(config_root, config["policy_registry_file"], expected_uid=expected_uid)
    schema_relative = _safe_relative_path(config["schema_root"])
    schemas = config_root.joinpath(*schema_relative.parts)
    validate_trusted_root_ancestry(schemas, expected_uid=expected_uid)
    validator = CanonicalSchemaValidator(schemas, expected_uid=expected_uid)
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
        secure_read_bytes(config_root, config["cache_private_key_file"], expected_uid=expected_uid)
    )
    cache_verification_key = _public_key_from_bytes(
        secure_read_bytes(config_root, config["cache_public_key_file"], expected_uid=expected_uid)
    )
    if public_key_raw_b64url(cache_signing_key.public_key()) != public_key_raw_b64url(cache_verification_key):
        raise RuntimeError("cache private and public keys do not form one Ed25519 keypair")
    cache_registry = load_trusted_canonical_json(
        config_root, config["cache_signing_registry_file"], expected_uid=expected_uid,
    )
    validator.validate("cache_signing_registry", cache_registry)
    if not verify_record(cache_registry, governance_key):
        raise RuntimeError("cache-signing registry governance signature is invalid")
    now = datetime.now(timezone.utc)
    cache_registry_by_id = validate_cache_signing_registry_lineage(cache_registry, evaluated_at=now)
    configured_cache_record = cache_registry_by_id.get(config["cache_signer_key_id"])
    if configured_cache_record is None:
        raise RuntimeError("configured cache signing key is absent from the governed registry")
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
    valid_from = _parse_registry_datetime(configured_cache_record["valid_from"], "selected.valid_from")
    valid_until = None if configured_cache_record["valid_until"] is None else _parse_registry_datetime(configured_cache_record["valid_until"], "selected.valid_until")
    status_changed = _parse_registry_datetime(configured_cache_record["status_changed_at"], "selected.status_changed_at")
    if status_changed > now or status_changed < valid_from or now < status_changed or (valid_until is not None and (status_changed >= valid_until or now >= valid_until)):
        raise RuntimeError("cache signing key is outside its governed validity interval")
    cache_verification_keys_by_id = {
        key_id: Ed25519PublicKey.from_public_bytes(_b64url_decode(record["public_key_base64url"]))
        for key_id, record in cache_registry_by_id.items()
    }
    cache_registry_snapshots = load_governed_cache_registry_snapshots(
        config_root, config["cache_registry_lineage_file"], expected_uid=expected_uid,
        schema_validator=validator, governance_key=governance_key,
        current_registry=cache_registry, evaluated_at=now,
    )
    return ProofCheckApplication(
        authority=authority, artifact_store=artifact_store,
        policy_resolver=ProofPolicyResolver(policy_registry, governance_key, schema_validator=validator),
        idempotency_store=store, schema_validator=validator,
        cache_signing_key=cache_signing_key, cache_verification_key=cache_verification_key,
        cache_verification_keys_by_id=cache_verification_keys_by_id,
        cache_signer_principal_id=config["cache_signer_principal_id"],
        cache_signer_key_id=config["cache_signer_key_id"],
        cache_key_record=configured_cache_record,
        cache_registry_sha256=sha256_bytes(canonical_bytes(cache_registry)),
        cache_registry_snapshots_by_sha256=cache_registry_snapshots,
        production_mode=True,
    )


__all__ = [
    "DurableIdempotencyStore", "ProofCheckApplication", "load_production_application",
    "GovernedCacheRegistrySnapshot", "build_governed_cache_registry_snapshot",
    "load_governed_cache_registry_snapshots", "validate_cache_registry_snapshot_lineage",
    "validate_cache_signing_registry_lineage",
]
