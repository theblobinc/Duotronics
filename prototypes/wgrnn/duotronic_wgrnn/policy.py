from __future__ import annotations

from dataclasses import asdict, dataclass


RUNTIME_MODES = {"audit_only", "sandbox", "restricted", "normal"}
LEARNING_MODES = {"blocked", "audit_only", "sandbox", "active"}
THRESHOLD_FIELDS = (
    "threshold_invalidate",
    "min_replay",
    "max_contradiction",
    "high_novelty_threshold",
    "low_confidence_threshold",
    "risk_limit",
    "candidate_write_upper_bound",
    "promotion_threshold",
    "split_contradiction_threshold",
    "max_content_update_norm",
    "max_fast_weight_update_norm",
)


@dataclass(slots=True)
class WGRNNPolicy:
    runtime_mode: str = "sandbox"
    learning_mode: str = "sandbox"
    threshold_invalidate: float = 0.80
    min_replay: float = 0.50
    max_contradiction: float = 0.70
    high_novelty_threshold: float = 0.80
    low_confidence_threshold: float = 0.50
    risk_limit: float = 0.75
    candidate_write_upper_bound: float = 0.10
    promotion_threshold: float = 0.85
    split_contradiction_threshold: float = 0.75
    max_memory_slots: int = 64
    max_content_update_norm: float = 0.10
    max_fast_weight_update_norm: float = 0.05
    content_adaptation_allowed: bool = False
    replay_required_for_updates: bool = True

    def validate_policy(self) -> None:
        if self.runtime_mode not in RUNTIME_MODES:
            raise ValueError(f"unsupported runtime_mode: {self.runtime_mode}")
        if self.learning_mode not in LEARNING_MODES:
            raise ValueError(f"unsupported learning_mode: {self.learning_mode}")
        for field_name in THRESHOLD_FIELDS:
            value = float(getattr(self, field_name))
            if value < 0.0 or value > 1.0:
                raise ValueError(f"{field_name} outside [0, 1]: {value}")
        if self.max_memory_slots < 1:
            raise ValueError("max_memory_slots must be positive")

    def to_json_dict(self) -> dict:
        return asdict(self)
