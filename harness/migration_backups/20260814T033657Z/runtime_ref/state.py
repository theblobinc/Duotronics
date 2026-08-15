from __future__ import annotations

from dataclasses import dataclass, field

from runtime_ref.architecture.manager import ArchitecturalWitness
from runtime_ref.meta.witness import MetaRecurrentWitness
from runtime_ref.policy.constraints import PolicyShieldSnapshot


@dataclass
class RuntimeState:
    schema_version: str = "runtime-state@v1"
    l1_witness_summary: dict = field(default_factory=dict)
    l2_recurrent_state: dict = field(default_factory=dict)
    l2m_lookup_summary: dict = field(default_factory=dict)
    l3_meta_recurrent_witness: dict = field(default_factory=dict)
    l4_architectural_witness: dict = field(default_factory=dict)
    l5_policy_shield: dict = field(default_factory=dict)
    active_meta_object_bundle: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        l3 = self.l3_meta_recurrent_witness or MetaRecurrentWitness().to_dict()
        l4 = self.l4_architectural_witness or ArchitecturalWitness().to_dict()
        l5 = self.l5_policy_shield or PolicyShieldSnapshot().to_dict()
        return {
            "schema_version": self.schema_version,
            "l1_witness_summary": dict(self.l1_witness_summary),
            "l2_recurrent_state": dict(self.l2_recurrent_state),
            "l2m_lookup_summary": dict(self.l2m_lookup_summary),
            "l3_meta_recurrent_witness": dict(l3),
            "l4_architectural_witness": dict(l4),
            "l5_policy_shield": dict(l5),
            "active_meta_object_bundle": dict(self.active_meta_object_bundle),
        }

    @classmethod
    def from_dict(cls, payload: dict | None) -> "RuntimeState":
        if not payload:
            return cls()
        return cls(**{key: value for key, value in payload.items() if key in cls.__dataclass_fields__})
