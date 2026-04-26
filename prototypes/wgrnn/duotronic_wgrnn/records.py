from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Optional

from .time_utils import current_timestamp


UPDATE_KINDS = {
    "no_op",
    "candidate_write",
    "quarantine_write",
    "stable_decay",
    "promotion_write",
    "split",
    "consolidation",
    "prune",
    "tombstone",
}


@dataclass(slots=True)
class MemoryUpdateRecord:
    memory_update_record_id: str
    memory_bank_id: str
    step_id: str
    witness_feature_vector_id: str
    gate_values_before_clamp: dict[str, float]
    gate_values_after_clamp: dict[str, float]
    authority_t: float
    affected_slot_ids: list[int]
    update_kind: str
    trust_status: str
    timestamp: str = field(default_factory=current_timestamp)
    replay_identity_ref: Optional[str] = None
    policy_decision_id: Optional[str] = None
    input_refs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.update_kind not in UPDATE_KINDS:
            raise ValueError(f"unsupported update_kind: {self.update_kind}")

    def to_json_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json_dict(cls, data: dict) -> "MemoryUpdateRecord":
        return cls(**data)

    def deterministic_hash_payload(self) -> dict:
        payload = self.to_json_dict()
        payload.pop("timestamp", None)
        return payload

    @property
    def deterministic_digest(self) -> str:
        payload = json.dumps(self.deterministic_hash_payload(), sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()
