from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field


def _stable_json(payload: dict) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


@dataclass
class ShadowReplaySpec:
    spec_id: str = ""
    schema_version: str = "shadow-replay-spec@v1"
    version: int = 1
    seed: int = 0
    sequence_ids: list[str] = field(default_factory=list)
    slice_boundaries: list[list[int]] = field(default_factory=list)
    recent_window_size: int = 256
    normalization_version: str = "meta-bundle@v1"
    objective_version: str = ""
    objective_hash: str = ""
    reducer_version: str = ""
    metric_bundle_hash: str = ""
    objective_bundle_hash: str = ""
    regime_targets: dict[str, float] = field(default_factory=dict)
    stress_tags: list[str] = field(default_factory=list)
    required_sentinels: list[str] = field(default_factory=list)
    coverage_substitutions: list[str] = field(default_factory=list)
    coverage_deficit: list[str] = field(default_factory=list)
    fallback_strategy: str = "approved_synthetic_registry"
    materialized_at: str = ""
    replay_spec_hash: str = ""

    def __post_init__(self) -> None:
        if not self.spec_id:
            self.spec_id = f"replay-{uuid.uuid4().hex[:12]}"
        if not self.materialized_at:
            self.materialized_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if not self.replay_spec_hash:
            self.replay_spec_hash = self.compute_hash()

    def material_payload(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "version": self.version,
            "seed": self.seed,
            "sequence_ids": list(self.sequence_ids),
            "slice_boundaries": [list(boundary) for boundary in self.slice_boundaries],
            "recent_window_size": self.recent_window_size,
            "normalization_version": self.normalization_version,
            "objective_bundle_hash": self.objective_bundle_hash,
            "required_sentinels": list(self.required_sentinels),
        }

    def compute_hash(self) -> str:
        digest = hashlib.sha256(_stable_json(self.material_payload()).encode()).hexdigest()[:16]
        return f"sha256:{digest}"

    @property
    def replay_identity(self) -> str:
        return f"{self.replay_spec_hash}:{self.objective_bundle_hash}"

    def validate_coverage(self, policy: dict | None = None) -> dict:
        policy = policy or {}
        issues: list[str] = []
        min_sequences = int(policy.get("min_sequences", 32))
        min_steps = int(policy.get("min_steps", 2048))
        sequence_count = len(self.sequence_ids)
        step_count = sum(max(boundary[1] - boundary[0], 0) for boundary in self.slice_boundaries)
        if sequence_count < min_sequences and step_count < min_steps:
            issues.append(
                f"insufficient_size:{sequence_count}_sequences:{step_count}_steps"
            )
        if self.coverage_deficit:
            issues.append("coverage_deficit:" + ",".join(sorted(self.coverage_deficit)))
        return {
            "schema_version": "shadow-replay-validation@v1",
            "valid": not issues,
            "issues": issues,
            "sequence_count": sequence_count,
            "step_count": step_count,
            "replay_spec_hash": self.replay_spec_hash,
            "replay_identity": self.replay_identity,
        }

    def to_dict(self) -> dict:
        return {
            "spec_id": self.spec_id,
            "schema_version": self.schema_version,
            "version": self.version,
            "seed": self.seed,
            "sequence_ids": list(self.sequence_ids),
            "slice_boundaries": [list(boundary) for boundary in self.slice_boundaries],
            "recent_window_size": self.recent_window_size,
            "normalization_version": self.normalization_version,
            "objective_version": self.objective_version,
            "objective_hash": self.objective_hash,
            "reducer_version": self.reducer_version,
            "metric_bundle_hash": self.metric_bundle_hash,
            "objective_bundle_hash": self.objective_bundle_hash,
            "regime_targets": dict(self.regime_targets),
            "stress_tags": list(self.stress_tags),
            "required_sentinels": list(self.required_sentinels),
            "coverage_substitutions": list(self.coverage_substitutions),
            "coverage_deficit": list(self.coverage_deficit),
            "fallback_strategy": self.fallback_strategy,
            "materialized_at": self.materialized_at,
            "replay_spec_hash": self.replay_spec_hash,
            "replay_identity": self.replay_identity,
        }

    @classmethod
    def from_dict(cls, payload: dict | None) -> "ShadowReplaySpec":
        if not payload:
            return cls()
        fields = {key: value for key, value in payload.items() if key in cls.__dataclass_fields__}
        return cls(**fields)
