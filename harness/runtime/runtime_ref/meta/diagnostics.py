from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum


class RejectionReason(str, Enum):
    LOW_EVIDENCE = "low_evidence"
    LOW_CONFIDENCE = "low_confidence"
    HARD_VIOLATION = "hard_violation"
    OBJECTIVE_REGRESSION = "objective_regression"
    POLICY_FREEZE = "policy_freeze"
    STALE_OBJECTIVE_BUNDLE = "stale_objective_bundle"
    STALE_REPLAY_IDENTITY = "stale_replay_identity"
    ESTIMATOR_FAILURE = "estimator_failure"


class AcceptanceDecision(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    FALLBACK = "fallback"


@dataclass
class MetaDiagnostics:
    diagnostic_id: str = ""
    schema_version: str = "meta-diagnostics@v1"
    epoch_step_count: int = 0
    timestamp: str = ""
    estimator_id: str = "finite_difference_meta_estimator"
    estimator_version: str = "fd-meta@v1"
    objective_version: str = ""
    objective_hash: str = ""
    reducer_version: str = ""
    metric_bundle_hash: str = ""
    objective_bundle_hash: str = ""
    replay_spec_hash: str = ""
    replay_identity: str = ""
    seed: int = 0
    active_coordinates: list[str] = field(default_factory=list)
    gradient_estimate: dict[str, float] = field(default_factory=dict)
    meta_momentum: dict[str, float] = field(default_factory=dict)
    candidate_update: dict[str, float] = field(default_factory=dict)
    controller_confidence: float = 0.0
    coverage_ratio: float = 0.0
    telemetry_coverage: float = 0.0
    objective_dispersion: float = 0.0
    sufficient_evidence: bool = False
    eval_count: int = 0
    acceptance_decision: str = ""
    rejection_reasons: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.diagnostic_id:
            self.diagnostic_id = f"l3diag-{uuid.uuid4().hex[:12]}"
        if not self.timestamp:
            self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def to_dict(self) -> dict:
        return {
            "diagnostic_id": self.diagnostic_id,
            "schema_version": self.schema_version,
            "epoch_step_count": self.epoch_step_count,
            "timestamp": self.timestamp,
            "estimator_id": self.estimator_id,
            "estimator_version": self.estimator_version,
            "objective_version": self.objective_version,
            "objective_hash": self.objective_hash,
            "reducer_version": self.reducer_version,
            "metric_bundle_hash": self.metric_bundle_hash,
            "objective_bundle_hash": self.objective_bundle_hash,
            "replay_spec_hash": self.replay_spec_hash,
            "replay_identity": self.replay_identity,
            "seed": self.seed,
            "active_coordinates": list(self.active_coordinates),
            "gradient_estimate": dict(self.gradient_estimate),
            "meta_momentum": dict(self.meta_momentum),
            "candidate_update": dict(self.candidate_update),
            "controller_confidence": round(self.controller_confidence, 4),
            "coverage_ratio": round(self.coverage_ratio, 4),
            "telemetry_coverage": round(self.telemetry_coverage, 4),
            "objective_dispersion": round(self.objective_dispersion, 4),
            "sufficient_evidence": self.sufficient_evidence,
            "eval_count": self.eval_count,
            "acceptance_decision": self.acceptance_decision,
            "rejection_reasons": list(self.rejection_reasons),
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "MetaDiagnostics":
        return cls(**{key: value for key, value in payload.items() if key in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def make_fallback_diagnostic(
    epoch_step: int,
    reason: RejectionReason,
    *,
    l5_bundle_hash: str = "",
    replay_spec_hash: str = "",
    replay_identity: str = "",
) -> MetaDiagnostics:
    return MetaDiagnostics(
        epoch_step_count=epoch_step,
        objective_bundle_hash=l5_bundle_hash,
        replay_spec_hash=replay_spec_hash,
        replay_identity=replay_identity,
        controller_confidence=0.0,
        coverage_ratio=0.0,
        telemetry_coverage=0.0,
        sufficient_evidence=False,
        acceptance_decision=AcceptanceDecision.FALLBACK.value,
        rejection_reasons=[reason.value],
    )
