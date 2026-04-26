from dataclasses import replace

import torch

from duotronic_wgrnn.cell import WGRNNCell
from duotronic_wgrnn.policy import WGRNNPolicy
from duotronic_wgrnn.records import MemoryUpdateRecord
from duotronic_wgrnn.replay import build_replay_identity
from duotronic_wgrnn.witness import WitnessFeatureVector


def _cell() -> WGRNNCell:
    torch.manual_seed(1)
    return WGRNNCell(input_dim=2, hidden_dim=2, cell_dim=2, slot_dim=2, num_slots=2)


def _witness(**overrides) -> WitnessFeatureVector:
    payload = {
        "witness_feature_vector_id": "wfv-replay",
        "confidence_score": 0.8,
        "profile_requested_authority": 0.8,
        "normalizer_confidence": 0.8,
        "policy_limit": 0.8,
        "transport_validated": True,
        "canonicalization_validated": True,
    }
    payload.update(overrides)
    return WitnessFeatureVector(**payload)


def _identity(cell: WGRNNCell, witness: WitnessFeatureVector, policy: WGRNNPolicy):
    return build_replay_identity(
        replay_identity_id="replay-test",
        cell_profile_id=cell.cell_profile_id,
        cell_profile_hash="sha256:cell",
        memory_bank=cell.memory_bank,
        witness=witness,
        policy=policy,
    )


def test_same_input_same_digest() -> None:
    witness = _witness()
    policy = WGRNNPolicy()
    assert _identity(_cell(), witness, policy).digest == _identity(_cell(), witness, policy).digest


def test_different_witness_changes_digest() -> None:
    policy = WGRNNPolicy()
    assert _identity(_cell(), _witness(confidence_score=0.8), policy).digest != _identity(_cell(), _witness(confidence_score=0.7), policy).digest


def test_different_policy_threshold_changes_digest() -> None:
    witness = _witness()
    assert _identity(_cell(), witness, WGRNNPolicy()).digest != _identity(_cell(), witness, WGRNNPolicy(risk_limit=0.5)).digest


def test_wall_clock_timestamp_does_not_alter_record_digest() -> None:
    record = MemoryUpdateRecord(
        memory_update_record_id="mur-1",
        memory_bank_id="bank",
        step_id="step",
        witness_feature_vector_id="wfv",
        gate_values_before_clamp={"g_write": 0.1},
        gate_values_after_clamp={"g_write": 0.1},
        authority_t=0.1,
        affected_slot_ids=[0],
        update_kind="candidate_write",
        trust_status="candidate",
        timestamp="2026-01-01T00:00:00Z",
    )
    shifted = replace(record, timestamp="2026-04-26T00:00:00Z")
    assert record.deterministic_digest == shifted.deterministic_digest
