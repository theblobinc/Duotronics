from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field


@dataclass
class ArchitectureReviewBundle:
    bundle_id: str = ""
    schema_version: str = "architecture-review-bundle@v1"
    proposal_id: str = ""
    proposal_hash: str = ""
    parent_generation: int = 0
    candidate_generation: int = 0
    structured_diff: list[dict] = field(default_factory=list)
    risk_tier: str = "low"
    objective_bundle_hash: str = ""
    replay_spec_hash: str = ""
    migration_plan_ref: str | None = None
    rollback_snapshot_id: str = ""
    rollback_restore_verified: bool = False
    reviewer_notes: str = ""

    def __post_init__(self) -> None:
        if not self.bundle_id:
            self.bundle_id = f"review-{uuid.uuid4().hex[:8]}"

    def to_dict(self) -> dict:
        return {
            "bundle_id": self.bundle_id,
            "schema_version": self.schema_version,
            "proposal_id": self.proposal_id,
            "proposal_hash": self.proposal_hash,
            "parent_generation": self.parent_generation,
            "candidate_generation": self.candidate_generation,
            "structured_diff": list(self.structured_diff),
            "risk_tier": self.risk_tier,
            "objective_bundle_hash": self.objective_bundle_hash,
            "replay_spec_hash": self.replay_spec_hash,
            "migration_plan_ref": self.migration_plan_ref,
            "rollback_snapshot_id": self.rollback_snapshot_id,
            "rollback_restore_verified": self.rollback_restore_verified,
            "reviewer_notes": self.reviewer_notes,
        }

    @classmethod
    def from_dict(cls, payload: dict | None) -> "ArchitectureReviewBundle":
        if not payload:
            return cls()
        return cls(**{key: value for key, value in payload.items() if key in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


@dataclass
class ApprovalRecord:
    bundle_id: str = ""
    schema_version: str = "approval-record@v1"
    proposal_hash: str = ""
    risk_tier: str = ""
    objective_bundle_hash: str = ""
    approver_id: str = ""
    decision: str = ""
    decision_source: str = "human"
    decision_time: str = ""
    expires_at: str | None = None
    conditions: list[str] = field(default_factory=list)
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.decision_time:
            self.decision_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    @property
    def is_approved(self) -> bool:
        return self.decision in {"approved", "approved_with_conditions"}

    def to_dict(self) -> dict:
        return {
            "bundle_id": self.bundle_id,
            "schema_version": self.schema_version,
            "proposal_hash": self.proposal_hash,
            "risk_tier": self.risk_tier,
            "objective_bundle_hash": self.objective_bundle_hash,
            "approver_id": self.approver_id,
            "decision": self.decision,
            "decision_source": self.decision_source,
            "decision_time": self.decision_time,
            "expires_at": self.expires_at,
            "conditions": list(self.conditions),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, payload: dict | None) -> "ApprovalRecord":
        if not payload:
            return cls()
        return cls(**{key: value for key, value in payload.items() if key in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)
