from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SCHEMA_VERSION = "xavi-owner-memory-v1"
DEFAULT_ROOT = Path(os.environ.get(
    "XAVI_OWNER_MEMORY_DIR",
    "/datastore2/xavi/data/duotronic-runtime/runtime-data/owner_memory",
))
_LABEL_RE = re.compile(r"^[A-Za-z0-9_.:/@+-]{1,240}$")
ALLOWED_KINDS = {"secret", "credential", "fact", "preference", "identity", "procedure", "source", "other"}
ALLOWED_PRIVACY = {"public", "internal", "private", "restricted"}
ALLOWED_RETENTION = {"ephemeral", "bounded", "audit", "release", "owner"}
ALLOWED_MODES = {"recurrent_memory", "retrieval", "task_execution", "parameter_training", "heldout_eval"}


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _now_ms() -> int:
    return int(time.time() * 1000)


def _validate_label(value: Any) -> str:
    label = str(value or "").strip()
    if not _LABEL_RE.fullmatch(label):
        raise ValueError("label must match ^[A-Za-z0-9_.:/@+-]{1,240}$")
    return label


def _normalize_modes(value: Any, *, privacy_class: str, kind: str) -> list[str]:
    if value is None:
        if privacy_class == "restricted" or kind in {"secret", "credential"}:
            return ["recurrent_memory", "retrieval", "task_execution"]
        return ["recurrent_memory", "retrieval", "task_execution", "parameter_training"]
    if not isinstance(value, list):
        raise ValueError("learning_modes must be a list")
    modes = sorted({str(x).strip() for x in value if str(x).strip()})
    unknown = [x for x in modes if x not in ALLOWED_MODES]
    if unknown:
        raise ValueError("unsupported learning_modes: " + ",".join(unknown))
    return modes


class OwnerMemory:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root) if root is not None else DEFAULT_ROOT
        self.db_path = self.root / "owner_memory.sqlite3"
        self.key_path = self.root / "owner_memory.aes256.key"

    def _ensure_root(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.root, 0o700)
        except OSError:
            pass

    def _key(self) -> bytes:
        self._ensure_root()
        if not self.key_path.exists():
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            fd = os.open(self.key_path, flags, 0o600)
            try:
                os.write(fd, secrets.token_bytes(32))
                os.fsync(fd)
            finally:
                os.close(fd)
        raw = self.key_path.read_bytes()
        if len(raw) != 32:
            raise RuntimeError("owner-memory key must be exactly 32 bytes")
        try:
            os.chmod(self.key_path, 0o600)
        except OSError:
            pass
        return raw

    def _connect(self) -> sqlite3.Connection:
        self._ensure_root()
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS owner_knowledge (
          knowledge_id TEXT PRIMARY KEY,
          namespace TEXT NOT NULL,
          label TEXT NOT NULL,
          kind TEXT NOT NULL,
          privacy_class TEXT NOT NULL,
          retention_class TEXT NOT NULL,
          learning_modes_json TEXT NOT NULL,
          source_json TEXT NOT NULL,
          metadata_json TEXT NOT NULL,
          value_digest TEXT NOT NULL,
          nonce BLOB NOT NULL,
          ciphertext BLOB NOT NULL,
          created_at_ms INTEGER NOT NULL,
          updated_at_ms INTEGER NOT NULL,
          active INTEGER NOT NULL DEFAULT 1,
          UNIQUE(namespace, label)
        );
        CREATE INDEX IF NOT EXISTS owner_knowledge_kind_idx ON owner_knowledge(kind, active);
        CREATE INDEX IF NOT EXISTS owner_knowledge_privacy_idx ON owner_knowledge(privacy_class, active);
        """)
        try:
            os.chmod(self.db_path, 0o600)
        except OSError:
            pass
        return conn

    @staticmethod
    def _knowledge_id(namespace: str, label: str) -> str:
        return "okn_" + hashlib.sha256(f"{namespace}\0{label}".encode("utf-8")).hexdigest()[:40]

    @staticmethod
    def _aad(meta: dict[str, Any]) -> bytes:
        return _canonical({
            "schema_version": SCHEMA_VERSION,
            "knowledge_id": meta["knowledge_id"],
            "namespace": meta["namespace"],
            "label": meta["label"],
            "kind": meta["kind"],
            "privacy_class": meta["privacy_class"],
            "retention_class": meta["retention_class"],
            "learning_modes": meta["learning_modes"],
        })

    def put(self, args: dict[str, Any]) -> dict[str, Any]:
        namespace = _validate_label(args.get("namespace") or "owner")
        label = _validate_label(args.get("label"))
        kind = str(args.get("kind") or "fact").strip()
        if kind not in ALLOWED_KINDS:
            raise ValueError("unsupported kind")
        privacy_class = str(args.get("privacy_class") or ("restricted" if kind in {"secret", "credential"} else "private")).strip()
        if privacy_class not in ALLOWED_PRIVACY:
            raise ValueError("unsupported privacy_class")
        retention_class = str(args.get("retention_class") or "owner").strip()
        if retention_class not in ALLOWED_RETENTION:
            raise ValueError("unsupported retention_class")
        modes = _normalize_modes(args.get("learning_modes"), privacy_class=privacy_class, kind=kind)
        if "value" not in args:
            raise ValueError("value is required")
        value = args.get("value")
        source = args.get("source") if isinstance(args.get("source"), dict) else {}
        metadata = args.get("metadata") if isinstance(args.get("metadata"), dict) else {}
        knowledge_id = self._knowledge_id(namespace, label)
        meta = {
            "knowledge_id": knowledge_id,
            "namespace": namespace,
            "label": label,
            "kind": kind,
            "privacy_class": privacy_class,
            "retention_class": retention_class,
            "learning_modes": modes,
        }
        plaintext = _canonical({"schema_version": SCHEMA_VERSION, "value": value})
        nonce = secrets.token_bytes(12)
        ciphertext = AESGCM(self._key()).encrypt(nonce, plaintext, self._aad(meta))
        now = _now_ms()
        value_digest = _sha(value)
        with self._connect() as conn:
            row = conn.execute("SELECT created_at_ms FROM owner_knowledge WHERE knowledge_id=?", (knowledge_id,)).fetchone()
            created = int(row["created_at_ms"]) if row else now
            conn.execute("""
            INSERT INTO owner_knowledge
            (knowledge_id,namespace,label,kind,privacy_class,retention_class,learning_modes_json,source_json,metadata_json,value_digest,nonce,ciphertext,created_at_ms,updated_at_ms,active)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)
            ON CONFLICT(knowledge_id) DO UPDATE SET
              namespace=excluded.namespace,label=excluded.label,kind=excluded.kind,
              privacy_class=excluded.privacy_class,retention_class=excluded.retention_class,
              learning_modes_json=excluded.learning_modes_json,source_json=excluded.source_json,
              metadata_json=excluded.metadata_json,value_digest=excluded.value_digest,
              nonce=excluded.nonce,ciphertext=excluded.ciphertext,updated_at_ms=excluded.updated_at_ms,active=1
            """, (
                knowledge_id, namespace, label, kind, privacy_class, retention_class,
                json.dumps(modes, sort_keys=True), json.dumps(source, sort_keys=True), json.dumps(metadata, sort_keys=True),
                value_digest, nonce, ciphertext, created, now,
            ))
            conn.commit()
        return {
            "schema_version": SCHEMA_VERSION,
            **meta,
            "value_digest": value_digest,
            "source_digest": _sha(source),
            "metadata_digest": _sha(metadata),
            "created_at_ms": created,
            "updated_at_ms": now,
            "active": True,
            "encrypted_at_rest": True,
        }

    def _metadata(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "knowledge_id": row["knowledge_id"],
            "namespace": row["namespace"],
            "label": row["label"],
            "kind": row["kind"],
            "privacy_class": row["privacy_class"],
            "retention_class": row["retention_class"],
            "learning_modes": json.loads(row["learning_modes_json"]),
            "source": json.loads(row["source_json"]),
            "metadata": json.loads(row["metadata_json"]),
            "value_digest": row["value_digest"],
            "created_at_ms": int(row["created_at_ms"]),
            "updated_at_ms": int(row["updated_at_ms"]),
            "active": bool(row["active"]),
            "encrypted_at_rest": True,
        }

    def get(self, args: dict[str, Any]) -> dict[str, Any]:
        knowledge_id = str(args.get("knowledge_id") or "").strip()
        namespace = str(args.get("namespace") or "owner").strip()
        label = str(args.get("label") or "").strip()
        with self._connect() as conn:
            if knowledge_id:
                row = conn.execute("SELECT * FROM owner_knowledge WHERE knowledge_id=? AND active=1", (knowledge_id,)).fetchone()
            else:
                label = _validate_label(label)
                namespace = _validate_label(namespace)
                row = conn.execute("SELECT * FROM owner_knowledge WHERE namespace=? AND label=? AND active=1", (namespace, label)).fetchone()
        if not row:
            raise KeyError("owner knowledge item not found")
        meta = self._metadata(row)
        plaintext = AESGCM(self._key()).decrypt(row["nonce"], row["ciphertext"], self._aad(meta))
        decoded = json.loads(plaintext.decode("utf-8"))
        value = decoded.get("value")
        if _sha(value) != row["value_digest"]:
            raise RuntimeError("owner knowledge digest mismatch")
        return {**meta, "value": value}

    def search(self, args: dict[str, Any]) -> dict[str, Any]:
        query = str(args.get("query") or "").strip().lower()
        namespace = str(args.get("namespace") or "").strip()
        kind = str(args.get("kind") or "").strip()
        privacy_class = str(args.get("privacy_class") or "").strip()
        limit = max(1, min(int(args.get("limit") or 50), 200))
        clauses = ["active=1"]
        params: list[Any] = []
        if namespace:
            clauses.append("namespace=?"); params.append(namespace)
        if kind:
            clauses.append("kind=?"); params.append(kind)
        if privacy_class:
            clauses.append("privacy_class=?"); params.append(privacy_class)
        if query:
            clauses.append("(lower(label) LIKE ? OR lower(metadata_json) LIKE ? OR lower(source_json) LIKE ?)")
            q = f"%{query}%"; params.extend([q,q,q])
        params.append(limit)
        sql = "SELECT * FROM owner_knowledge WHERE " + " AND ".join(clauses) + " ORDER BY updated_at_ms DESC LIMIT ?"
        with self._connect() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
        return {"schema_version": SCHEMA_VERSION, "count": len(rows), "items": [self._metadata(r) for r in rows]}

    def list(self, args: dict[str, Any]) -> dict[str, Any]:
        payload = dict(args or {})
        payload.setdefault("query", "")
        return self.search(payload)
