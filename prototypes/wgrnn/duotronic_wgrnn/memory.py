from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

import torch
import torch.nn as nn

from .witness import WitnessFeatureVector
from .time_utils import current_timestamp


MEMORY_SLOT_STATUSES = {"candidate", "quarantined", "stable", "deprecated", "tombstoned"}
WRITABLE_SLOT_STATUSES = {"candidate", "quarantined"}


@dataclass(slots=True)
class MemorySlot:
    slot_id: int
    memory_bank_id: str
    trust_status: str = "candidate"
    stability_score: float = 0.0
    contradiction_score: float = 0.0
    novelty_score: float = 0.0
    recurrence_score: float = 0.0
    last_written_at: Optional[str] = None
    created_at: str = field(default_factory=current_timestamp)
    canonical_witness_fact_refs: list[str] = field(default_factory=list)
    memory_update_record_refs: list[str] = field(default_factory=list)
    replay_identity: str = ""
    policy_decision_id: Optional[str] = None
    purge_tombstone_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.trust_status not in MEMORY_SLOT_STATUSES:
            raise ValueError(f"unsupported memory slot status: {self.trust_status}")

    def writable_inline(self) -> bool:
        return self.trust_status in WRITABLE_SLOT_STATUSES

    def to_json_dict(self) -> dict:
        return asdict(self)


class MemoryBank(nn.Module):
    def __init__(self, bank_id: str, num_slots: int, slot_dim: int, device: torch.device):
        super().__init__()
        if num_slots < 1:
            raise ValueError("num_slots must be positive")
        if slot_dim < 1:
            raise ValueError("slot_dim must be positive")
        self.bank_id = bank_id
        self.num_slots = num_slots
        self.slot_dim = slot_dim
        self.device = device
        self.content_matrix = nn.Parameter(torch.zeros(num_slots, slot_dim, device=device))
        self.slots = [MemorySlot(slot_id=slot_id, memory_bank_id=bank_id) for slot_id in range(num_slots)]

    def read(self, attention_weights: torch.Tensor) -> torch.Tensor:
        return attention_weights @ self.content_matrix

    def apply_update(
        self,
        delta: torch.Tensor,
        slot_id: int,
        trust_status: str,
        witness: WitnessFeatureVector,
        *,
        record_id: str | None = None,
        replay_identity: str | None = None,
    ) -> bool:
        slot = self.slots[slot_id]
        if not slot.writable_inline():
            return False
        if trust_status not in {"candidate", "quarantined"}:
            return False
        with torch.no_grad():
            self.content_matrix[slot_id] += delta.to(self.device)
            slot.last_written_at = current_timestamp()
            slot.trust_status = trust_status
            slot.stability_score = min(
                1.0,
                slot.stability_score + witness.recurrence_score * (1.0 - witness.contradiction_score) * 0.05,
            )
            slot.contradiction_score = witness.contradiction_score
            slot.novelty_score = witness.novelty_score
            slot.recurrence_score = witness.recurrence_score
            if record_id:
                slot.memory_update_record_refs.append(record_id)
            if replay_identity:
                slot.replay_identity = replay_identity
        return True

    def to_json_dict(self) -> dict:
        return {
            "bank_id": self.bank_id,
            "num_slots": self.num_slots,
            "slot_dim": self.slot_dim,
            "content_matrix": self.content_matrix.detach().cpu().tolist(),
            "slots": [slot.to_json_dict() for slot in self.slots],
        }
