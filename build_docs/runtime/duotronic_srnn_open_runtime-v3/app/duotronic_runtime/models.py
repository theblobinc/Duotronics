from __future__ import annotations

from dataclasses import dataclass, asdict
import json
import time
from typing import Any, Literal

from .crypto_primitives import stable_shake_id


def stable_id(prefix: str, payload: Any, length: int = 20) -> str:
    return stable_shake_id(prefix, payload, length=length)


def now_ms() -> int:
    return int(time.time() * 1000)


@dataclass
class ModelRecord:
    name: str
    provider: str
    model: str | None = None
    base_url: str | None = None
    default: bool = False
    description: str = ""
    enabled: bool = True


@dataclass
class WGRNNMemoryUpdate:
    update_id: str
    loop_id: str
    node_id: str
    slot_id: int
    update_kind: Literal["candidate_write", "quarantine_write", "promote", "noop"]
    trust_status: Literal["candidate", "quarantine", "promoted", "rejected"]
    authority_t: float
    confidence: float
    contradiction: float
    affected_slot_ids: list[int]
    replay_identity_ref: str
    state_digest: str
    created_at_ms: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NaturalLanguageActivationWitness:
    witness_id: str
    loop_id: str
    node_id: str
    source_model: dict[str, Any]
    activation: dict[str, Any]
    verbalizer: dict[str, Any]
    reconstructor: dict[str, Any]
    fidelity: dict[str, Any]
    lifecycle: dict[str, Any]
    policy: dict[str, Any]
    wg_rnn_update_id: str | None
    created_at_ms: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RuntimeRunResult:
    run_id: str
    loop_id: str
    node_id: str
    prompt: str
    response_text: str
    model: dict[str, Any]
    requested_action: str
    wg_rnn: dict[str, Any]
    nla_witness: dict[str, Any]
    policy_decision: dict[str, Any]
    memory: dict[str, Any]
    created_at_ms: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
