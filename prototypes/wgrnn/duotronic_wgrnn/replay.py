from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Optional

import torch

from .memory import MemoryBank
from .policy import WGRNNPolicy
from .witness import WitnessFeatureVector


def _canonical_hash(payload: object) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return "sha256:" + hashlib.sha256(data).hexdigest()


def hash_tensor(tensor: torch.Tensor) -> str:
    detached = tensor.detach().cpu().contiguous()
    return _canonical_hash(
        {
            "dtype": str(detached.dtype),
            "shape": list(detached.shape),
            "values": detached.tolist(),
        }
    )


def hash_memory_bank(memory_bank: MemoryBank) -> str:
    return _canonical_hash(memory_bank.to_json_dict())


def hash_witness(witness: WitnessFeatureVector) -> str:
    return _canonical_hash(witness.to_json_dict())


def hash_policy(policy: WGRNNPolicy) -> str:
    return _canonical_hash(policy.to_json_dict())


@dataclass(slots=True)
class WGRNNReplayIdentity:
    replay_identity_id: str
    cell_profile_id: str
    cell_profile_hash: str
    memory_bank_id: str
    prior_memory_bank_hash: str
    witness_feature_vector_hash: str
    policy_snapshot_id: str
    clamp_threshold_hash: str
    slot_allocation_policy_hash: str
    transport_replay_identity_ref: Optional[str]
    purge_state_hash: str
    human_review_state_hash: str
    digest: str

    def to_json_dict(self) -> dict:
        return asdict(self)


def build_replay_identity(
    *,
    replay_identity_id: str,
    cell_profile_id: str,
    cell_profile_hash: str,
    memory_bank: MemoryBank,
    witness: WitnessFeatureVector,
    policy: WGRNNPolicy,
    policy_snapshot_id: str = "policy-sandbox-default",
    slot_allocation_policy_hash: str = "sha256:first-writable-slot",
    transport_replay_identity_ref: Optional[str] = None,
    purge_state_hash: str = "sha256:no-purge-state",
    human_review_state_hash: str = "sha256:no-human-review-state",
) -> WGRNNReplayIdentity:
    prior_memory_bank_hash = hash_memory_bank(memory_bank)
    witness_hash = hash_witness(witness)
    policy_hash = hash_policy(policy)
    clamp_threshold_hash = _canonical_hash(
        {
            "threshold_invalidate": policy.threshold_invalidate,
            "min_replay": policy.min_replay,
            "max_contradiction": policy.max_contradiction,
            "high_novelty_threshold": policy.high_novelty_threshold,
            "low_confidence_threshold": policy.low_confidence_threshold,
            "risk_limit": policy.risk_limit,
            "candidate_write_upper_bound": policy.candidate_write_upper_bound,
            "promotion_threshold": policy.promotion_threshold,
            "split_contradiction_threshold": policy.split_contradiction_threshold,
        }
    )
    digest_payload = {
        "cell_profile_hash": cell_profile_hash,
        "cell_profile_id": cell_profile_id,
        "clamp_threshold_hash": clamp_threshold_hash,
        "human_review_state_hash": human_review_state_hash,
        "memory_bank_id": memory_bank.bank_id,
        "policy_hash": policy_hash,
        "policy_snapshot_id": policy_snapshot_id,
        "prior_memory_bank_hash": prior_memory_bank_hash,
        "purge_state_hash": purge_state_hash,
        "slot_allocation_policy_hash": slot_allocation_policy_hash,
        "transport_replay_identity_ref": transport_replay_identity_ref,
        "witness_feature_vector_hash": witness_hash,
    }
    return WGRNNReplayIdentity(
        replay_identity_id=replay_identity_id,
        cell_profile_id=cell_profile_id,
        cell_profile_hash=cell_profile_hash,
        memory_bank_id=memory_bank.bank_id,
        prior_memory_bank_hash=prior_memory_bank_hash,
        witness_feature_vector_hash=witness_hash,
        policy_snapshot_id=policy_snapshot_id,
        clamp_threshold_hash=clamp_threshold_hash,
        slot_allocation_policy_hash=slot_allocation_policy_hash,
        transport_replay_identity_ref=transport_replay_identity_ref,
        purge_state_hash=purge_state_hash,
        human_review_state_hash=human_review_state_hash,
        digest=_canonical_hash(digest_payload),
    )
