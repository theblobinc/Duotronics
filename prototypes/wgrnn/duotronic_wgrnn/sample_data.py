from __future__ import annotations

import torch

from .witness import WitnessFeatureVector


SAMPLE_EVENTS = [
    {
        "id": "wfv-001-valid-candidate-write",
        "confidence": 0.92,
        "contradiction": 0.05,
        "novelty": 0.30,
        "recurrence": 0.80,
        "replayability": 0.95,
        "allow_write": True,
        "allow_promote": False,
        "transport_ok": True,
        "canon_ok": True,
    },
    {
        "id": "wfv-002-quarantine",
        "confidence": 0.31,
        "contradiction": 0.10,
        "novelty": 0.94,
        "recurrence": 0.10,
        "replayability": 0.55,
        "allow_write": True,
        "allow_promote": False,
        "transport_ok": True,
        "canon_ok": True,
    },
    {
        "id": "wfv-003-transport-failed",
        "confidence": 0.99,
        "contradiction": 0.00,
        "novelty": 0.10,
        "recurrence": 0.90,
        "replayability": 0.98,
        "allow_write": True,
        "allow_promote": True,
        "transport_ok": False,
        "canon_ok": True,
    },
    {
        "id": "wfv-004-invalidation-block",
        "confidence": 0.90,
        "contradiction": 0.05,
        "novelty": 0.20,
        "recurrence": 0.60,
        "replayability": 0.90,
        "allow_write": True,
        "allow_promote": False,
        "transport_ok": True,
        "canon_ok": True,
        "invalidation": 0.95,
    },
]


def witness_from_event(event: dict) -> WitnessFeatureVector:
    return WitnessFeatureVector(
        witness_feature_vector_id=event["id"],
        confidence_score=float(event["confidence"]),
        contradiction_score=float(event["contradiction"]),
        novelty_score=float(event["novelty"]),
        recurrence_score=float(event["recurrence"]),
        replayability_score=float(event["replayability"]),
        invalidation_score=float(event.get("invalidation", 0.0)),
        action_risk=float(event.get("action_risk", 0.0)),
        policy_allow_write=bool(event["allow_write"]),
        policy_allow_promote=bool(event["allow_promote"]),
        profile_requested_authority=0.80,
        normalizer_confidence=0.90,
        policy_limit=0.70,
        transport_validated=bool(event["transport_ok"]),
        canonicalization_validated=bool(event["canon_ok"]),
        trust_status="canonicalized" if event["canon_ok"] else "candidate",
    )


def embedding_for_event(index: int, input_dim: int) -> torch.Tensor:
    base = torch.linspace(0.1, 0.4, input_dim)
    return base + index * 0.05
