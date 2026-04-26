from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch


SCORE_FIELDS = (
    "confidence_score",
    "contradiction_score",
    "novelty_score",
    "recurrence_score",
    "source_integrity",
    "source_diversity",
    "replayability_score",
    "staleness_score",
    "invalidation_score",
    "action_risk",
    "profile_requested_authority",
    "normalizer_confidence",
    "policy_limit",
)


@dataclass(slots=True)
class WitnessFeatureVector:
    witness_feature_vector_id: str
    confidence_score: float = 0.0
    contradiction_score: float = 0.0
    novelty_score: float = 0.0
    recurrence_score: float = 0.0
    source_integrity: float = 0.0
    source_diversity: float = 0.0
    replayability_score: float = 0.0
    staleness_score: float = 0.0
    invalidation_score: float = 0.0
    action_risk: float = 0.0
    policy_allow_write: bool = False
    policy_allow_promote: bool = False
    human_review_required: bool = False
    profile_requested_authority: float = 0.0
    normalizer_confidence: float = 0.0
    policy_limit: float = 0.0
    transport_validated: bool = False
    canonicalization_validated: bool = False
    trust_status: str = "candidate"

    def validate_bounds(self) -> None:
        for field_name in SCORE_FIELDS:
            value = float(getattr(self, field_name))
            if value < 0.0 or value > 1.0:
                raise ValueError(f"{field_name} outside [0, 1]: {value}")

    def compute_authority(self) -> float:
        self.validate_bounds()
        if not self.transport_validated or not self.canonicalization_validated:
            return 0.0
        return min(
            self.profile_requested_authority,
            self.confidence_score,
            self.normalizer_confidence,
            self.policy_limit,
        )

    def to_tensor(self, device: "torch.device") -> "torch.Tensor":
        import torch

        self.validate_bounds()
        values = [
            self.confidence_score,
            self.contradiction_score,
            self.novelty_score,
            self.recurrence_score,
            self.source_integrity,
            self.source_diversity,
            self.replayability_score,
            self.staleness_score,
            self.invalidation_score,
            self.action_risk,
            float(self.policy_allow_write),
            float(self.policy_allow_promote),
            float(self.human_review_required),
            self.profile_requested_authority,
            self.normalizer_confidence,
            self.policy_limit,
            float(self.transport_validated),
            float(self.canonicalization_validated),
        ]
        return torch.tensor(values, dtype=torch.float32, device=device)

    def to_json_dict(self) -> dict:
        return asdict(self)
