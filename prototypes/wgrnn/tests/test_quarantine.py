import torch

from duotronic_wgrnn.cell import WGRNNCell
from duotronic_wgrnn.policy import WGRNNPolicy
from duotronic_wgrnn.witness import WitnessFeatureVector


def test_high_novelty_low_confidence_emits_quarantine_write() -> None:
    cell = WGRNNCell(input_dim=3, hidden_dim=3, cell_dim=3, slot_dim=3, num_slots=1)
    witness = WitnessFeatureVector(
        witness_feature_vector_id="wfv-quarantine",
        confidence_score=0.31,
        contradiction_score=0.1,
        novelty_score=0.94,
        recurrence_score=0.1,
        replayability_score=0.55,
        policy_allow_write=True,
        policy_allow_promote=True,
        profile_requested_authority=0.8,
        normalizer_confidence=0.9,
        policy_limit=0.7,
        transport_validated=True,
        canonicalization_validated=True,
    )
    _h, _c, record = cell(
        torch.ones(3),
        torch.zeros(3),
        torch.zeros(3),
        witness,
        WGRNNPolicy(),
    )
    assert record.update_kind == "quarantine_write"
    assert record.gate_values_after_clamp["g_quarantine"] == 1.0
    assert record.gate_values_after_clamp["g_promote"] == 0.0
    assert cell.memory_bank.slots[0].trust_status == "quarantined"
