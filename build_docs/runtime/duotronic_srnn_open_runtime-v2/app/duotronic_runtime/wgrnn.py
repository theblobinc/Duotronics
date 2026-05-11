from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from .models import WGRNNMemoryUpdate, now_ms, stable_id


def _clamp01(v: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, min(1.0, float(v)))
    except Exception:
        return default


def _digest_vector(values: list[float]) -> str:
    payload = json.dumps([round(float(v), 8) for v in values], separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()


def text_feature_vector(text: str, dim: int = 32) -> list[float]:
    """Deterministic small feature vector used for sandbox-mode recurrence.

    This is not a model embedding. It is a predictable runtime shim that lets the
    witness/memory/policy flow run anywhere without GPUs or model downloads.
    """
    dim = max(4, int(dim))
    buckets = [0.0] * dim
    if not text:
        return buckets
    for i, ch in enumerate(text.encode("utf-8", errors="ignore")):
        buckets[(ch + i) % dim] += ((ch % 31) + 1) / 32.0
    norm = math.sqrt(sum(v * v for v in buckets)) or 1.0
    return [round(v / norm, 6) for v in buckets]


class WGRNNRuntime:
    """SRNN-facing WG-RNN shim with governed memory writes.

    Mirrors the production SRNN bridge idea: WG-RNN owns authoritative memory
    updates; this fallback path remains deterministic and serializable.
    """

    def __init__(self, *, loop_id: str, node_id: str, state_dim: int = 32, slot_dim: int = 32, num_slots: int = 64) -> None:
        self.loop_id = loop_id
        self.node_id = node_id
        self.state_dim = max(int(state_dim), 4)
        self.slot_dim = max(int(slot_dim), 4)
        self.num_slots = max(int(num_slots), 4)
        self.h = [0.0] * self.state_dim
        self.c = [0.0] * self.state_dim
        self.memory_bank = [[0.0] * self.slot_dim for _ in range(self.num_slots)]
        self.step_count = 0

    def snapshot(self) -> dict[str, Any]:
        return {
            "loop_id": self.loop_id,
            "node_id": self.node_id,
            "state_dim": self.state_dim,
            "slot_dim": self.slot_dim,
            "num_slots": self.num_slots,
            "step_count": self.step_count,
            "h": self.h,
            "c": self.c,
            "memory_bank_digest": _digest_vector([x for slot in self.memory_bank for x in slot[:4]]),
        }

    def step(self, *, prompt: str, response_text: str, requested_action: str = "observe", evidence_quality: float = 0.72) -> dict[str, Any]:
        self.step_count += 1
        text = f"{requested_action}\n{prompt}\n{response_text}"
        x = text_feature_vector(text, self.state_dim)
        confidence = _clamp01(evidence_quality, 0.5)
        contradiction = _clamp01(1.0 - confidence, 0.0)
        action_risk = 0.35 if requested_action in {"memory_write", "promote_witness", "external_action"} else 0.1
        authority = _clamp01(0.62 * confidence + 0.22 * (1.0 - contradiction) - action_risk * 0.18, 0.0)

        self.h = [round(max(-1.0, min(1.0, self.h[i] * 0.90 + x[i] * 0.10)), 6) for i in range(self.state_dim)]
        self.c = [round(max(-1.0, min(1.0, self.c[i] * 0.94 + self.h[i] * 0.06)), 6) for i in range(self.state_dim)]

        dominant_key = requested_action or "observe"
        slot_id = abs(hash(dominant_key + prompt[:64])) % self.num_slots
        slot = self.memory_bank[slot_id]
        update_kind = "candidate_write" if authority >= 0.50 and requested_action != "promote_witness" else "quarantine_write"
        trust_status = "candidate" if update_kind == "candidate_write" else "quarantine"
        for i in range(min(self.slot_dim, len(self.h))):
            slot[i] = round(max(-1.0, min(1.0, slot[i] * 0.88 + self.h[i] * authority * 0.12)), 6)
        self.memory_bank[slot_id] = slot

        state_digest = _digest_vector(self.h + self.c + slot[: min(8, len(slot))])
        update_payload = {
            "loop_id": self.loop_id,
            "node_id": self.node_id,
            "slot_id": slot_id,
            "step_count": self.step_count,
            "authority": authority,
            "state_digest": state_digest,
        }
        update = WGRNNMemoryUpdate(
            update_id=stable_id("wgrnn_update", update_payload),
            loop_id=self.loop_id,
            node_id=self.node_id,
            slot_id=slot_id,
            update_kind=update_kind,
            trust_status=trust_status,
            authority_t=round(authority, 6),
            confidence=round(confidence, 6),
            contradiction=round(contradiction, 6),
            affected_slot_ids=[slot_id],
            replay_identity_ref="sha256:" + hashlib.sha256(json.dumps(update_payload, sort_keys=True).encode()).hexdigest(),
            state_digest=state_digest,
            created_at_ms=now_ms(),
        )
        return {
            "runtime_status": "authoritative_shim",
            "activation_vector": list(self.h),
            "memory_update": update.to_dict(),
            "snapshot": self.snapshot(),
        }
