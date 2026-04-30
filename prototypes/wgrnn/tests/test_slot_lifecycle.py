"""Phase C: Slot lifecycle (write / quarantine / decay / promote) instrumented with replay records.

Each lifecycle transition MUST emit a MemoryUpdateRecord with:
- correct update_kind
- replay_identity_ref set (non-None, sha256: prefixed) for write paths
- trust_status consistent with the resulting slot state
- affected_slot_ids reflecting the mutated slot(s)
"""
from __future__ import annotations

import pytest
import torch

from duotronic_wgrnn.cell import WGRNNCell
from duotronic_wgrnn.policy import WGRNNPolicy
from duotronic_wgrnn.witness import WitnessFeatureVector


def _cell(**overrides) -> WGRNNCell:
    kwargs = dict(input_dim=3, hidden_dim=3, cell_dim=3, slot_dim=3, num_slots=2, bank_id="lifecycle-test-bank")
    kwargs.update(overrides)
    torch.manual_seed(42)
    return WGRNNCell(**kwargs)


def _witness(**overrides) -> WitnessFeatureVector:
    payload = {
        "witness_feature_vector_id": "wfv-lifecycle",
        "confidence_score": 0.9,
        "contradiction_score": 0.05,
        "novelty_score": 0.3,
        "recurrence_score": 0.8,
        "replayability_score": 0.95,
        "policy_allow_write": True,
        "policy_allow_promote": True,
        "profile_requested_authority": 0.8,
        "normalizer_confidence": 0.9,
        "policy_limit": 0.7,
        "transport_validated": True,
        "canonicalization_validated": True,
    }
    payload.update(overrides)
    return WitnessFeatureVector(**payload)


def _step(cell: WGRNNCell, witness: WitnessFeatureVector, policy: WGRNNPolicy | None = None):
    return cell(
        torch.ones(cell.input_dim),
        torch.zeros(cell.hidden_dim),
        torch.zeros(cell.cell_dim),
        witness,
        policy or WGRNNPolicy(),
    )


# ---------------------------------------------------------------------------
# candidate_write lifecycle
# ---------------------------------------------------------------------------

def test_candidate_write_replay_identity_ref_is_set() -> None:
    _h, _c, record = _step(_cell(), _witness())
    assert record.update_kind == "candidate_write"
    assert record.replay_identity_ref is not None
    assert record.replay_identity_ref.startswith("sha256:")


def test_candidate_write_policy_decision_id_is_set() -> None:
    _h, _c, record = _step(_cell(), _witness())
    assert record.update_kind == "candidate_write"
    assert record.policy_decision_id is not None


def test_candidate_write_slot_trust_status_is_candidate() -> None:
    cell = _cell()
    _h, _c, record = _step(cell, _witness())
    assert record.update_kind == "candidate_write"
    assert record.trust_status == "candidate"
    assert cell.memory_bank.slots[record.affected_slot_ids[0]].trust_status == "candidate"


def test_candidate_write_affected_slot_ids_nonempty() -> None:
    _h, _c, record = _step(_cell(), _witness())
    assert record.update_kind == "candidate_write"
    assert len(record.affected_slot_ids) > 0


# ---------------------------------------------------------------------------
# quarantine_write lifecycle
# ---------------------------------------------------------------------------

def test_quarantine_write_replay_identity_ref_is_set() -> None:
    _h, _c, record = _step(
        _cell(),
        _witness(novelty_score=0.95, confidence_score=0.25),
    )
    assert record.update_kind == "quarantine_write"
    assert record.replay_identity_ref is not None
    assert record.replay_identity_ref.startswith("sha256:")


def test_quarantine_write_trust_status_is_quarantined() -> None:
    cell = _cell()
    _h, _c, record = _step(cell, _witness(novelty_score=0.95, confidence_score=0.25))
    assert record.update_kind == "quarantine_write"
    assert record.trust_status == "quarantined"
    assert cell.memory_bank.slots[record.affected_slot_ids[0]].trust_status == "quarantined"


def test_quarantine_write_g_quarantine_is_one() -> None:
    _h, _c, record = _step(_cell(), _witness(novelty_score=0.95, confidence_score=0.25))
    assert record.update_kind == "quarantine_write"
    assert record.gate_values_after_clamp["g_quarantine"] == 1.0


# ---------------------------------------------------------------------------
# stable_decay lifecycle
# ---------------------------------------------------------------------------

def test_stable_decay_emits_record_with_correct_kind() -> None:
    cell = _cell()
    record = cell.apply_stable_decay(
        slot_id=0,
        decay_rate=0.1,
        witness=_witness(witness_feature_vector_id="wfv-decay"),
        policy=WGRNNPolicy(),
    )
    assert record.update_kind == "stable_decay"


def test_stable_decay_replay_identity_ref_is_set() -> None:
    cell = _cell()
    record = cell.apply_stable_decay(
        slot_id=0,
        decay_rate=0.1,
        witness=_witness(witness_feature_vector_id="wfv-decay-ref"),
        policy=WGRNNPolicy(),
    )
    assert record.replay_identity_ref is not None
    assert record.replay_identity_ref.startswith("sha256:")


def test_stable_decay_reduces_content_norm() -> None:
    cell = _cell()
    with torch.no_grad():
        cell.memory_bank.content_matrix[0] = torch.ones(cell.slot_dim)
    before_norm = float(torch.linalg.vector_norm(cell.memory_bank.content_matrix[0].detach()))
    cell.apply_stable_decay(
        slot_id=0,
        decay_rate=0.2,
        witness=_witness(witness_feature_vector_id="wfv-decay-norm"),
        policy=WGRNNPolicy(),
    )
    after_norm = float(torch.linalg.vector_norm(cell.memory_bank.content_matrix[0].detach()))
    assert after_norm < before_norm


def test_stable_decay_affected_slot_ids_contains_target() -> None:
    cell = _cell()
    record = cell.apply_stable_decay(
        slot_id=1,
        decay_rate=0.05,
        witness=_witness(witness_feature_vector_id="wfv-decay-slot"),
        policy=WGRNNPolicy(),
    )
    assert 1 in record.affected_slot_ids


def test_stable_decay_out_of_range_rate_raises() -> None:
    cell = _cell()
    with pytest.raises(ValueError, match="decay_rate"):
        cell.apply_stable_decay(
            slot_id=0,
            decay_rate=1.5,
            witness=_witness(witness_feature_vector_id="wfv-decay-bad"),
            policy=WGRNNPolicy(),
        )


def test_stable_decay_zero_rate_is_identity() -> None:
    cell = _cell()
    with torch.no_grad():
        cell.memory_bank.content_matrix[0] = torch.tensor([0.5, 0.6, 0.7])
    before = cell.memory_bank.content_matrix[0].detach().clone()
    cell.apply_stable_decay(
        slot_id=0,
        decay_rate=0.0,
        witness=_witness(witness_feature_vector_id="wfv-decay-zero"),
        policy=WGRNNPolicy(),
    )
    assert torch.allclose(before, cell.memory_bank.content_matrix[0].detach())


# ---------------------------------------------------------------------------
# promotion_write lifecycle
# ---------------------------------------------------------------------------

def test_slot_promotion_emits_promotion_write_above_threshold() -> None:
    cell = _cell()
    cell.memory_bank.slots[0].trust_status = "candidate"
    cell.memory_bank.slots[0].stability_score = 0.95  # above promotion_threshold=0.85
    record = cell.apply_slot_promotion(
        slot_id=0,
        witness=_witness(witness_feature_vector_id="wfv-promote"),
        policy=WGRNNPolicy(),
    )
    assert record.update_kind == "promotion_write"
    assert record.trust_status == "stable"
    assert cell.memory_bank.slots[0].trust_status == "stable"


def test_slot_promotion_noop_below_threshold() -> None:
    cell = _cell()
    cell.memory_bank.slots[0].trust_status = "candidate"
    cell.memory_bank.slots[0].stability_score = 0.5  # below promotion_threshold=0.85
    record = cell.apply_slot_promotion(
        slot_id=0,
        witness=_witness(witness_feature_vector_id="wfv-promote-low"),
        policy=WGRNNPolicy(),
    )
    assert record.update_kind == "no_op"
    assert cell.memory_bank.slots[0].trust_status == "candidate"


def test_slot_promotion_noop_when_policy_allow_promote_false() -> None:
    cell = _cell()
    cell.memory_bank.slots[0].trust_status = "candidate"
    cell.memory_bank.slots[0].stability_score = 0.95
    record = cell.apply_slot_promotion(
        slot_id=0,
        witness=_witness(witness_feature_vector_id="wfv-promote-blocked", policy_allow_promote=False),
        policy=WGRNNPolicy(),
    )
    assert record.update_kind == "no_op"
    assert cell.memory_bank.slots[0].trust_status == "candidate"


def test_slot_promotion_noop_for_already_stable_slot() -> None:
    cell = _cell()
    cell.memory_bank.slots[0].trust_status = "stable"
    cell.memory_bank.slots[0].stability_score = 0.99
    record = cell.apply_slot_promotion(
        slot_id=0,
        witness=_witness(witness_feature_vector_id="wfv-promote-stable"),
        policy=WGRNNPolicy(),
    )
    assert record.update_kind == "no_op"
    assert cell.memory_bank.slots[0].trust_status == "stable"


def test_slot_promotion_noop_for_tombstoned_slot() -> None:
    cell = _cell()
    cell.memory_bank.slots[0].trust_status = "tombstoned"
    cell.memory_bank.slots[0].stability_score = 0.99
    record = cell.apply_slot_promotion(
        slot_id=0,
        witness=_witness(witness_feature_vector_id="wfv-promote-tombstoned"),
        policy=WGRNNPolicy(),
    )
    assert record.update_kind == "no_op"


def test_slot_promotion_replay_identity_ref_is_set() -> None:
    cell = _cell()
    cell.memory_bank.slots[0].stability_score = 0.95
    record = cell.apply_slot_promotion(
        slot_id=0,
        witness=_witness(witness_feature_vector_id="wfv-promote-ref"),
        policy=WGRNNPolicy(),
    )
    assert record.replay_identity_ref is not None
    assert record.replay_identity_ref.startswith("sha256:")


def test_slot_promotion_affected_slot_ids_contains_target() -> None:
    cell = _cell()
    cell.memory_bank.slots[0].trust_status = "candidate"
    cell.memory_bank.slots[0].stability_score = 0.95
    record = cell.apply_slot_promotion(
        slot_id=0,
        witness=_witness(witness_feature_vector_id="wfv-promote-slot"),
        policy=WGRNNPolicy(),
    )
    assert record.update_kind == "promotion_write"
    assert 0 in record.affected_slot_ids
