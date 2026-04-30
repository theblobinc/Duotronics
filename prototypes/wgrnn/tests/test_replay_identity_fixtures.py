"""Phase C: Replay-identity stability test against fixture vectors.

These tests pin specific computed digests to known values. If the replay-identity
hashing logic or any input changes, these tests fail as regression anchors.

The fixture digest is computed deterministically from:
  - torch.manual_seed(17) cell (4x4 dims, 4 slots, 'sample-research-bank')
  - preset content_matrix rows 0 and 1
  - a fully-specified WitnessFeatureVector (wfv-fixture-v1)
  - default WGRNNPolicy (sandbox mode)

Regenerate the expected digest only when the hashing contract changes intentionally.
Run: python3 -c "from tests.test_replay_identity_fixtures import _compute_fixture_digest; print(_compute_fixture_digest())"
"""
from __future__ import annotations

import torch

from duotronic_wgrnn.cell import WGRNNCell
from duotronic_wgrnn.policy import WGRNNPolicy
from duotronic_wgrnn.replay import build_replay_identity
from duotronic_wgrnn.witness import WitnessFeatureVector


# ---------------------------------------------------------------------------
# Known fixture digest — update ONLY when the hashing contract changes.
# ---------------------------------------------------------------------------
FIXTURE_REPLAY_IDENTITY_DIGEST_V1 = (
    "sha256:e8b4a26831ff931cc7ece463d63e421776b7ef101056f07b4ab9bed36ac54fcd"
)


def _build_fixture_cell() -> WGRNNCell:
    torch.manual_seed(17)
    cell = WGRNNCell(
        input_dim=4,
        hidden_dim=4,
        cell_dim=4,
        slot_dim=4,
        num_slots=4,
        bank_id="sample-research-bank",
    )
    with torch.no_grad():
        cell.memory_bank.content_matrix[0] = torch.tensor([0.02, 0.01, 0.00, 0.03])
        cell.memory_bank.content_matrix[1] = torch.tensor([0.01, 0.03, 0.02, 0.00])
    return cell


def _build_fixture_witness() -> WitnessFeatureVector:
    return WitnessFeatureVector(
        witness_feature_vector_id="wfv-fixture-v1",
        confidence_score=0.92,
        contradiction_score=0.05,
        novelty_score=0.30,
        recurrence_score=0.80,
        replayability_score=0.95,
        policy_allow_write=True,
        policy_allow_promote=False,
        profile_requested_authority=0.80,
        normalizer_confidence=0.90,
        policy_limit=0.70,
        transport_validated=True,
        canonicalization_validated=True,
    )


def _compute_fixture_digest() -> str:
    cell = _build_fixture_cell()
    witness = _build_fixture_witness()
    policy = WGRNNPolicy()
    identity = build_replay_identity(
        replay_identity_id="replay-fixture-v1",
        cell_profile_id=cell.cell_profile_id,
        cell_profile_hash=cell._cell_profile_hash(),
        memory_bank=cell.memory_bank,
        witness=witness,
        policy=policy,
    )
    return identity.digest


# ---------------------------------------------------------------------------
# Fixture stability tests
# ---------------------------------------------------------------------------

def test_fixture_replay_identity_digest_is_stable() -> None:
    """Fixture digest MUST match the pinned value.

    If this test fails, the hashing contract changed. Update
    FIXTURE_REPLAY_IDENTITY_DIGEST_V1 only after a deliberate change.
    """
    assert _compute_fixture_digest() == FIXTURE_REPLAY_IDENTITY_DIGEST_V1


def test_fixture_digest_is_deterministic_across_calls() -> None:
    """Two calls to _compute_fixture_digest() MUST produce the same digest."""
    assert _compute_fixture_digest() == _compute_fixture_digest()


def test_fixture_digest_changes_on_content_matrix_mutation() -> None:
    """Mutating the memory bank content MUST change the digest."""
    original = _compute_fixture_digest()

    # Build the same cell but alter a content row
    cell = _build_fixture_cell()
    with torch.no_grad():
        cell.memory_bank.content_matrix[0] = torch.tensor([0.99, 0.99, 0.99, 0.99])
    witness = _build_fixture_witness()
    policy = WGRNNPolicy()
    identity = build_replay_identity(
        replay_identity_id="replay-fixture-v1",
        cell_profile_id=cell.cell_profile_id,
        cell_profile_hash=cell._cell_profile_hash(),
        memory_bank=cell.memory_bank,
        witness=witness,
        policy=policy,
    )
    assert identity.digest != original


def test_fixture_digest_changes_on_witness_mutation() -> None:
    """Mutating the witness MUST change the digest."""
    original = _compute_fixture_digest()

    cell = _build_fixture_cell()
    from dataclasses import replace
    witness = replace(_build_fixture_witness(), confidence_score=0.50)
    policy = WGRNNPolicy()
    identity = build_replay_identity(
        replay_identity_id="replay-fixture-v1",
        cell_profile_id=cell.cell_profile_id,
        cell_profile_hash=cell._cell_profile_hash(),
        memory_bank=cell.memory_bank,
        witness=witness,
        policy=policy,
    )
    assert identity.digest != original


def test_fixture_digest_changes_on_policy_mutation() -> None:
    """Mutating the policy thresholds MUST change the digest."""
    original = _compute_fixture_digest()

    cell = _build_fixture_cell()
    witness = _build_fixture_witness()
    mutated_policy = WGRNNPolicy(risk_limit=0.30)
    identity = build_replay_identity(
        replay_identity_id="replay-fixture-v1",
        cell_profile_id=cell.cell_profile_id,
        cell_profile_hash=cell._cell_profile_hash(),
        memory_bank=cell.memory_bank,
        witness=witness,
        policy=mutated_policy,
    )
    assert identity.digest != original


def test_fixture_forward_pass_record_digest_is_stable() -> None:
    """A full forward pass on the fixture cell MUST produce a stable record digest."""
    cell = _build_fixture_cell()
    witness = _build_fixture_witness()
    policy = WGRNNPolicy()
    _h, _c, record = cell(
        torch.ones(cell.input_dim),
        torch.zeros(cell.hidden_dim),
        torch.zeros(cell.cell_dim),
        witness,
        policy,
    )
    # The record digest excludes wall-clock timestamp — must be stable.
    digest_run1 = record.deterministic_digest

    # Rebuild and run again to confirm determinism.
    cell2 = _build_fixture_cell()
    _h2, _c2, record2 = cell2(
        torch.ones(cell2.input_dim),
        torch.zeros(cell2.hidden_dim),
        torch.zeros(cell2.cell_dim),
        _build_fixture_witness(),
        WGRNNPolicy(),
    )
    assert record2.deterministic_digest == digest_run1
