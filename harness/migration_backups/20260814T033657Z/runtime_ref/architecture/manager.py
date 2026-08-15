from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field

from runtime_ref.policy.constraints import PolicyShieldSnapshot, classify_risk


@dataclass
class ArchitectureDeltaProposal:
    proposal_id: str = ""
    schema_version: str = "architecture-delta-proposal@v1"
    proposal_type: str = "gate_mix"
    parent_generation: int = 0
    candidate_generation: int = 0
    mutations: list[dict] = field(default_factory=list)
    risk_tier: str = "low"
    requires_schema_migration: bool = False
    migration_plan_id: str | None = None
    approval_required: bool = False
    review_bundle_id: str | None = None
    objective_bundle_hash: str = ""
    replay_spec_hash: str = ""
    status: str = "proposed"
    proposed_at: str = ""

    def __post_init__(self) -> None:
        if not self.proposal_id:
            self.proposal_id = f"delta-{uuid.uuid4().hex[:8]}"
        if not self.proposed_at:
            self.proposed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    @property
    def proposal_hash(self) -> str:
        payload = json.dumps(
            {
                "proposal_type": self.proposal_type,
                "parent_generation": self.parent_generation,
                "candidate_generation": self.candidate_generation,
                "mutations": self.mutations,
                "migration_plan_id": self.migration_plan_id,
            },
            sort_keys=True,
        )
        return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "proposal_id": self.proposal_id,
            "schema_version": self.schema_version,
            "proposal_type": self.proposal_type,
            "parent_generation": self.parent_generation,
            "candidate_generation": self.candidate_generation,
            "mutations": list(self.mutations),
            "risk_tier": self.risk_tier,
            "requires_schema_migration": self.requires_schema_migration,
            "migration_plan_id": self.migration_plan_id,
            "approval_required": self.approval_required,
            "review_bundle_id": self.review_bundle_id,
            "objective_bundle_hash": self.objective_bundle_hash,
            "replay_spec_hash": self.replay_spec_hash,
            "status": self.status,
            "proposed_at": self.proposed_at,
            "proposal_hash": self.proposal_hash,
        }

    @classmethod
    def from_dict(cls, payload: dict | None) -> "ArchitectureDeltaProposal":
        if not payload:
            return cls()
        return cls(**{key: value for key, value in payload.items() if key in cls.__dataclass_fields__})


@dataclass
class ArchitecturalWitness:
    schema_version: str = "architectural-witness@v1"
    family_value_ema: dict[str, float] = field(default_factory=dict)
    family_cost_ema: dict[str, float] = field(default_factory=dict)
    gate_importance_ema: dict[str, float] = field(default_factory=dict)
    candidate_queue: list[dict] = field(default_factory=list)
    review_history: list[dict] = field(default_factory=list)
    incumbent_generation: int = 0
    rollback_generation: int | None = None
    promotion_budget: int = 1

    def update_telemetry(
        self,
        family_values: dict[str, float],
        family_costs: dict[str, float],
        gate_importance: dict[str, float] | None = None,
        *,
        alpha: float = 0.05,
    ) -> None:
        for family, value in family_values.items():
            previous = self.family_value_ema.get(family, value)
            self.family_value_ema[family] = (1 - alpha) * previous + alpha * value
        for family, cost in family_costs.items():
            previous = self.family_cost_ema.get(family, cost)
            self.family_cost_ema[family] = (1 - alpha) * previous + alpha * cost
        if gate_importance:
            for gate, value in gate_importance.items():
                previous = self.gate_importance_ema.get(gate, value)
                self.gate_importance_ema[gate] = (1 - alpha) * previous + alpha * value

    def _finalize_proposal(self, proposal: ArchitectureDeltaProposal, policy: PolicyShieldSnapshot) -> ArchitectureDeltaProposal:
        proposal.risk_tier = classify_risk(
            {
                "type": proposal.proposal_type,
                "requires_schema_migration": proposal.requires_schema_migration,
                "memory_mb_delta": 0,
                "adapter_rank_delta": 0,
            },
            policy.approval_policy,
        ).value
        proposal.approval_required = policy.requires_operator_approval(
            {
                "type": proposal.proposal_type,
                "requires_schema_migration": proposal.requires_schema_migration,
            }
        )
        self.candidate_queue.append(proposal.to_dict())
        return proposal

    def propose_enable_family(self, family_id: str, policy: PolicyShieldSnapshot, *, replay_spec_hash: str = "") -> ArchitectureDeltaProposal:
        proposal = ArchitectureDeltaProposal(
            proposal_type="enable_family",
            parent_generation=self.incumbent_generation,
            candidate_generation=self.incumbent_generation + 1,
            mutations=[{"type": "enable_family", "family_id": family_id}],
            objective_bundle_hash=policy.objective_bundle_hash,
            replay_spec_hash=replay_spec_hash,
        )
        return self._finalize_proposal(proposal, policy)

    def propose_prune_family(self, family_id: str, policy: PolicyShieldSnapshot, *, replay_spec_hash: str = "") -> ArchitectureDeltaProposal:
        proposal = ArchitectureDeltaProposal(
            proposal_type="prune_family",
            parent_generation=self.incumbent_generation,
            candidate_generation=self.incumbent_generation + 1,
            mutations=[{"type": "prune_family", "family_id": family_id}],
            objective_bundle_hash=policy.objective_bundle_hash,
            replay_spec_hash=replay_spec_hash,
        )
        return self._finalize_proposal(proposal, policy)

    def propose_gate_mix(
        self,
        gate_name: str,
        field_name: str,
        delta: float,
        policy: PolicyShieldSnapshot,
        *,
        replay_spec_hash: str = "",
    ) -> ArchitectureDeltaProposal:
        proposal = ArchitectureDeltaProposal(
            proposal_type="gate_mix",
            parent_generation=self.incumbent_generation,
            candidate_generation=self.incumbent_generation + 1,
            mutations=[{"type": "gate_mix", "gate": gate_name, "field": field_name, "delta": delta}],
            objective_bundle_hash=policy.objective_bundle_hash,
            replay_spec_hash=replay_spec_hash,
        )
        return self._finalize_proposal(proposal, policy)

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "family_value_ema": dict(self.family_value_ema),
            "family_cost_ema": dict(self.family_cost_ema),
            "gate_importance_ema": dict(self.gate_importance_ema),
            "candidate_queue": list(self.candidate_queue),
            "review_history": list(self.review_history),
            "incumbent_generation": self.incumbent_generation,
            "rollback_generation": self.rollback_generation,
            "promotion_budget": self.promotion_budget,
        }

    @classmethod
    def from_dict(cls, payload: dict | None) -> "ArchitecturalWitness":
        if not payload:
            return cls()
        return cls(**{key: value for key, value in payload.items() if key in cls.__dataclass_fields__})
