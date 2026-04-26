import torch

from duotronic_wgrnn.cell import WGRNNCell
from duotronic_wgrnn.policy import WGRNNPolicy
from duotronic_wgrnn.witness import WitnessFeatureVector


def _witness(**overrides) -> WitnessFeatureVector:
    payload = {
        "witness_feature_vector_id": "wfv-memory",
        "confidence_score": 0.92,
        "contradiction_score": 0.05,
        "novelty_score": 0.3,
        "recurrence_score": 0.8,
        "replayability_score": 0.95,
        "policy_allow_write": True,
        "policy_allow_promote": False,
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


def test_candidate_write_changes_candidate_slot() -> None:
    cell = WGRNNCell(input_dim=3, hidden_dim=3, cell_dim=3, slot_dim=3, num_slots=2)
    before = cell.memory_bank.content_matrix.detach().clone()
    _h, _c, record = _step(cell, _witness())
    assert record.update_kind == "candidate_write"
    assert record.affected_slot_ids
    assert not torch.allclose(before, cell.memory_bank.content_matrix.detach())


def test_update_norm_never_exceeds_policy_limit() -> None:
    cell = WGRNNCell(input_dim=3, hidden_dim=3, cell_dim=3, slot_dim=3, num_slots=2)
    before = cell.memory_bank.content_matrix.detach().clone()
    policy = WGRNNPolicy(max_content_update_norm=0.03)
    _h, _c, record = _step(cell, _witness(), policy)
    changed = cell.memory_bank.content_matrix.detach() - before
    assert record.affected_slot_ids
    assert torch.linalg.vector_norm(changed[record.affected_slot_ids[0]]) <= 0.030001


def test_tombstoned_slots_are_not_updated() -> None:
    cell = WGRNNCell(input_dim=3, hidden_dim=3, cell_dim=3, slot_dim=3, num_slots=1)
    cell.memory_bank.slots[0].trust_status = "tombstoned"
    before = cell.memory_bank.content_matrix.detach().clone()
    _h, _c, record = _step(cell, _witness())
    assert record.update_kind == "no_op"
    assert torch.allclose(before, cell.memory_bank.content_matrix.detach())


def test_deprecated_slots_are_not_updated() -> None:
    cell = WGRNNCell(input_dim=3, hidden_dim=3, cell_dim=3, slot_dim=3, num_slots=1)
    cell.memory_bank.slots[0].trust_status = "deprecated"
    before = cell.memory_bank.content_matrix.detach().clone()
    _h, _c, record = _step(cell, _witness())
    assert record.update_kind == "no_op"
    assert torch.allclose(before, cell.memory_bank.content_matrix.detach())


def test_stable_slots_do_not_receive_direct_inline_writes() -> None:
    cell = WGRNNCell(input_dim=3, hidden_dim=3, cell_dim=3, slot_dim=3, num_slots=1)
    cell.memory_bank.slots[0].trust_status = "stable"
    before = cell.memory_bank.content_matrix.detach().clone()
    _h, _c, record = _step(cell, _witness(policy_allow_promote=True))
    assert record.update_kind == "no_op"
    assert torch.allclose(before, cell.memory_bank.content_matrix.detach())
