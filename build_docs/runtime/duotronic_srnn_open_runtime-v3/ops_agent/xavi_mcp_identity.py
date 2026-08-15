from __future__ import annotations

try:
    from .xavi_crypto import kmac256_hex, shake256_hex, shake256_ref
except ImportError:
    from xavi_crypto import kmac256_hex, shake256_hex, shake256_ref

import hmac
import json
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

_SESSION_RE = re.compile(r"^mcp_[0-9a-f]{32}\.[0-9a-f]{24}$")
_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9_.:@+-]+")


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return shake256_ref(raw)


def _slug(value: str, fallback: str) -> str:
    out = _SAFE_ID_RE.sub("-", str(value or "").strip()).strip("-")
    return (out or fallback)[:96]


def _sig(raw: str, secret: str) -> str:
    return kmac256_hex(secret, raw, custom=b"Xavi-MCP-Identity-v1")[:24]


def issue_session_id(secret: str) -> str:
    raw = uuid.uuid4().hex
    return f"mcp_{raw}.{_sig(raw, secret)}"


def valid_session_id(value: str | None, secret: str) -> bool:
    if not value or not _SESSION_RE.fullmatch(value):
        return False
    raw, supplied = value[4:].split(".", 1)
    return hmac.compare_digest(supplied, _sig(raw, secret))


def issue_connection_id() -> str:
    return "conn_" + uuid.uuid4().hex


def stable_agent_id(*, client_name: str, device_id: str = "", account_scope: str = "", explicit_agent_id: str = "") -> str:
    if explicit_agent_id:
        return "agent:" + _slug(explicit_agent_id, "mcp-client")
    label = _slug(client_name, "mcp-client")
    fingerprint = shake256_hex(f"{label}\n{device_id}\n{account_scope}")[:20]
    return f"agent:{label}:{fingerprint}"


def issue_work_id() -> str:
    return "work_" + uuid.uuid4().hex


def issue_delegation_id() -> str:
    return "dlg_" + uuid.uuid4().hex


def issue_lease_id() -> str:
    return "lease_" + uuid.uuid4().hex


@dataclass(frozen=True)
class ChatIdentity:
    agent_id: str
    session_id: str
    connection_id: str
    client_name: str
    device_id_digest: str
    account_scope_digest: str
    created_at_ms: int
    resumed: bool = False
    parent_session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def public_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Delegation:
    delegation_id: str
    work_id: str
    delegator_session_id: str
    delegate_session_id: str | None
    objective: str
    parent_work_id: str | None = None
    required_capabilities: tuple[str, ...] = ()
    resource_hints: dict[str, Any] = field(default_factory=dict)
    created_at_ms: int = 0
    status: str = "queued"

    def public_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResourceLease:
    lease_id: str
    work_id: str
    session_id: str
    resource_type: str
    resource_id: str
    quantity: float
    unit: str
    expires_at_ms: int
    exclusive: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def public_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_chat_identity(*, secret: str, client_name: str, device_id: str = "", account_scope: str = "", explicit_agent_id: str = "", candidate_session_id: str | None = None, parent_session_id: str | None = None, metadata: dict[str, Any] | None = None) -> ChatIdentity:
    resumed = valid_session_id(candidate_session_id, secret)
    session_id = str(candidate_session_id) if resumed else issue_session_id(secret)
    return ChatIdentity(
        agent_id=stable_agent_id(client_name=client_name, device_id=device_id, account_scope=account_scope, explicit_agent_id=explicit_agent_id),
        session_id=session_id,
        connection_id=issue_connection_id(),
        client_name=_slug(client_name, "mcp-client"),
        device_id_digest=_digest(device_id or "unknown-device"),
        account_scope_digest=_digest(account_scope or "unknown-account"),
        created_at_ms=int(time.time() * 1000),
        resumed=resumed,
        parent_session_id=parent_session_id,
        metadata=dict(metadata or {}),
    )


def new_delegation(*, delegator_session_id: str, objective: str, delegate_session_id: str | None = None, work_id: str | None = None, parent_work_id: str | None = None, required_capabilities: list[str] | tuple[str, ...] | None = None, resource_hints: dict[str, Any] | None = None) -> Delegation:
    objective = str(objective or "").strip()
    if not objective:
        raise ValueError("objective is required")
    return Delegation(
        delegation_id=issue_delegation_id(),
        work_id=work_id or issue_work_id(),
        delegator_session_id=delegator_session_id,
        delegate_session_id=delegate_session_id,
        objective=objective,
        parent_work_id=parent_work_id,
        required_capabilities=tuple(sorted(set(required_capabilities or []))),
        resource_hints=dict(resource_hints or {}),
        created_at_ms=int(time.time() * 1000),
    )


def new_resource_lease(*, work_id: str, session_id: str, resource_type: str, resource_id: str, quantity: float, unit: str, ttl_seconds: int, exclusive: bool = False, metadata: dict[str, Any] | None = None) -> ResourceLease:
    resource_type = _slug(resource_type, "resource")
    resource_id = _slug(resource_id, "default")
    quantity = float(quantity)
    ttl_seconds = int(ttl_seconds)
    if quantity <= 0:
        raise ValueError("quantity must be > 0")
    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be > 0")
    return ResourceLease(
        lease_id=issue_lease_id(), work_id=work_id, session_id=session_id,
        resource_type=resource_type, resource_id=resource_id, quantity=quantity,
        unit=_slug(unit, "unit"), expires_at_ms=int(time.time() * 1000) + ttl_seconds * 1000,
        exclusive=bool(exclusive), metadata=dict(metadata or {}),
    )


def identity_trace(identity: ChatIdentity, *, work_id: str | None = None, delegation_id: str | None = None) -> dict[str, Any]:
    body = {"agent_id": identity.agent_id, "session_id": identity.session_id, "connection_id": identity.connection_id, "work_id": work_id, "delegation_id": delegation_id}
    return body | {"trace_digest": _digest(body)}
