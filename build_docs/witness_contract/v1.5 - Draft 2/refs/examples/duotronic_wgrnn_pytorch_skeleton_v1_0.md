# Duotronic WG-RNN PyTorch Implementation Skeleton v1.0

**Status:** Reference implementation skeleton  
**Version:** wgrnn-pytorch-skeleton@v1.0  
**Document kind:** Reference implementation example  
**Primary purpose:** Provide a PyTorch-compatible class skeleton for the Witness-Gated Recurrent Cell (WG-RNN) that implementers can use as a starting point for Prototype v1, consistent with the normative rules in `duotronic_witness_gated_recurrent_cell_contract_v1_0.md`.

> **Research note.** This skeleton is a starting point for experimentation. It does not constitute a production implementation. Stable production use requires the full promotion path: fixtures, replay traces, retention diagnostics, purge cascade tests, policy approval, and Family Registry handoff.

---

## 1. Scope

This skeleton covers Prototype v1 scope:

1. LSTM-style fast recurrence conditioned on witness features;
2. an external slot-based memory bank (16–64 slots);
3. witness feature vector (`WitnessFeatureVector`) as a structured input;
4. write, decay, quarantine, and promotion gates;
5. hard policy clamps;
6. slot attention;
7. candidate and quarantine slot updates;
8. a `MemoryUpdateRecord` stub.

It does not cover:

- contradiction branching (Prototype v2);
- local plasticity adapters (Prototype v3);
- full `SlotPromotionRequest` workflow (governed separately);
- purge cascade hooks (governed separately);
- distributed cluster integration (governed separately).

---

## 2. Dependencies

```python
# Python 3.10+
# torch >= 2.0
import torch
import torch.nn as nn
import torch.nn.functional as F
from dataclasses import dataclass, field
from typing import Optional
import hashlib
import json
import time
```

---

## 3. WitnessFeatureVector dataclass

This is the structured control input.  
It must be derived from `CanonicalWitnessFact` objects, not raw inputs.

```python
@dataclass
class WitnessFeatureVector:
    """
    Structured witness control signal.
    Must be derived from CanonicalWitnessFact or policy-approved CandidateWitness.
    Scores are in [0, 1] unless otherwise noted.
    """
    witness_feature_vector_id: str

    # Evidence quality scores
    confidence_score: float = 0.0
    contradiction_score: float = 0.0
    novelty_score: float = 0.0
    recurrence_score: float = 0.0
    source_integrity: float = 0.0
    source_diversity: float = 0.0
    replayability_score: float = 0.0
    staleness_score: float = 0.0
    invalidation_score: float = 0.0
    action_risk: float = 0.0

    # Policy booleans (must be derived from explicit policy decisions)
    policy_allow_write: bool = False
    policy_allow_promote: bool = False
    human_review_required: bool = False

    # Authority inputs
    profile_requested_authority: float = 0.0
    normalizer_confidence: float = 0.0
    policy_limit: float = 0.0
    transport_validated: bool = False
    canonicalization_validated: bool = False

    trust_status: str = "candidate"  # candidate | canonicalized | audit_only | rejected

    def to_tensor(self, device: torch.device) -> torch.Tensor:
        """
        Convert scalar fields to a fixed-dimension feature vector.
        Dimension: 12 (scores) + 3 (bool policy flags) + 3 (authority scalars) = 18.
        """
        values = [
            self.confidence_score,
            self.contradiction_score,
            self.novelty_score,
            self.recurrence_score,
            self.source_integrity,
            self.source_diversity,
            self.replayability_score,
            self.staleness_score,
            self.invalidation_score,
            self.action_risk,
            float(self.policy_allow_write),
            float(self.policy_allow_promote),
            float(self.human_review_required),
            self.profile_requested_authority,
            self.normalizer_confidence,
            self.policy_limit,
            float(self.transport_validated),
            float(self.canonicalization_validated),
        ]
        return torch.tensor(values, dtype=torch.float32, device=device)

    def compute_authority(self) -> float:
        """
        authority = min(profile_requested_authority, confidence_score,
                        normalizer_confidence, policy_limit)
        Zero if transport or canonicalization validation failed.
        """
        if not self.transport_validated or not self.canonicalization_validated:
            return 0.0
        return min(
            self.profile_requested_authority,
            self.confidence_score,
            self.normalizer_confidence,
            self.policy_limit,
        )
```

---

## 4. WGRNNPolicy dataclass

Policy thresholds for gate clamping.  
Gate threshold fields must not be tuned autonomously.

```python
@dataclass
class WGRNNPolicy:
    """
    Policy thresholds for the WG-RNN cell.
    Gate threshold adaptation is NOT allowed autonomously.
    """
    runtime_mode: str = "sandbox"  # audit_only | sandbox | restricted | normal
    learning_mode: str = "sandbox"  # blocked | audit_only | sandbox | active

    # Clamp thresholds
    threshold_invalidate: float = 0.80
    min_replay: float = 0.50
    max_contradiction: float = 0.70
    high_novelty_threshold: float = 0.80
    low_confidence_threshold: float = 0.50
    risk_limit: float = 0.75
    candidate_write_upper_bound: float = 0.10
    promotion_threshold: float = 0.85
    split_contradiction_threshold: float = 0.75

    # Limits
    max_memory_slots: int = 64
    max_content_update_norm: float = 0.10
    max_fast_weight_update_norm: float = 0.05

    # Flags
    content_adaptation_allowed: bool = False
    replay_required_for_updates: bool = True
```

---

## 5. MemorySlot dataclass

```python
@dataclass
class MemorySlot:
    """
    A single persistent memory slot in the WG-RNN bank.
    """
    slot_id: int
    memory_bank_id: str
    trust_status: str = "candidate"  # candidate | quarantined | stable | deprecated | tombstoned
    stability_score: float = 0.0
    contradiction_score: float = 0.0
    novelty_score: float = 0.0
    recurrence_score: float = 0.0
    last_written_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: str(time.time()))
    canonical_witness_fact_refs: list = field(default_factory=list)
    memory_update_record_refs: list = field(default_factory=list)
    replay_identity: str = ""
    policy_decision_id: Optional[str] = None
    purge_tombstone_id: Optional[str] = None
```

---

## 6. MemoryBank

A bank of `K` memory slots backed by a float tensor.

```python
class MemoryBank(nn.Module):
    """
    Slot-based persistent witness memory.

    content_matrix: (K, slot_dim) tensor of slot content vectors.
    slots: list of MemorySlot metadata objects.
    """

    def __init__(self, bank_id: str, num_slots: int, slot_dim: int, device: torch.device):
        super().__init__()
        self.bank_id = bank_id
        self.num_slots = num_slots
        self.slot_dim = slot_dim
        self.device = device

        # Learnable initial content is okay; updates are governed at runtime.
        self.content_matrix = nn.Parameter(
            torch.zeros(num_slots, slot_dim, device=device)
        )
        self.slots = [
            MemorySlot(slot_id=k, memory_bank_id=bank_id)
            for k in range(num_slots)
        ]

    def read(self, attention_weights: torch.Tensor) -> torch.Tensor:
        """
        Weighted read: r = attention @ content_matrix.
        attention_weights: (K,) or (batch, K)
        Returns: (slot_dim,) or (batch, slot_dim)
        """
        # attention_weights: (K,)  ->  (1, K) @ (K, D) -> (1, D) -> (D,)
        return attention_weights @ self.content_matrix  # (slot_dim,)

    def apply_update(
        self,
        delta: torch.Tensor,
        slot_id: int,
        trust_status: str,
        witness: WitnessFeatureVector,
    ) -> None:
        """
        Apply a bounded content delta to a specific slot.
        Does NOT change slot trust_status here; that is governed externally.
        """
        with torch.no_grad():
            self.content_matrix[slot_id] += delta
            slot = self.slots[slot_id]
            slot.last_written_at = str(time.time())
            slot.trust_status = trust_status
            slot.stability_score = min(
                1.0,
                slot.stability_score
                + witness.recurrence_score * (1.0 - witness.contradiction_score) * 0.05,
            )
            slot.contradiction_score = witness.contradiction_score
```

---

## 7. WGRNNCell

The main cell module.

```python
class WGRNNCell(nn.Module):
    """
    Witness-Gated Recurrent Cell (WG-RNN).

    Implements the normative rules from:
        duotronic_witness_gated_recurrent_cell_contract_v1_0.md

    Architecture:
        - LSTM-style fast recurrence (h_t, c_t) conditioned on witness features.
        - Slot-based persistent witness memory.
        - Four witness-specific gates: write, decay, quarantine, promote.
        - Hard policy clamps before any memory update.
        - MemoryUpdateRecord stub for every step.
    """

    WITNESS_DIM = 18  # matches WitnessFeatureVector.to_tensor() output dim

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        cell_dim: int,
        slot_dim: int,
        num_slots: int,
        policy_context_dim: int = 0,
        bank_id: str = "default-bank",
        device: Optional[torch.device] = None,
    ):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.cell_dim = cell_dim
        self.slot_dim = slot_dim
        self.num_slots = num_slots
        self.device = device or torch.device("cpu")
        self.bank_id = bank_id

        w_dim = self.WITNESS_DIM
        p_dim = policy_context_dim
        r_dim = slot_dim  # memory read output

        in_dim = input_dim + hidden_dim + r_dim + w_dim + p_dim

        # --- Fast LSTM-style recurrence gates ---
        self.fast_input_gate = nn.Linear(in_dim, cell_dim)
        self.fast_forget_gate = nn.Linear(in_dim, cell_dim)
        self.fast_output_gate = nn.Linear(in_dim, hidden_dim)
        self.fast_candidate = nn.Linear(in_dim, cell_dim)

        # --- Slot query projection ---
        self.query_proj = nn.Linear(input_dim + hidden_dim + w_dim, slot_dim)

        # --- Witness-specific memory gates ---
        self.write_gate_net = nn.Linear(in_dim, 1)
        self.decay_gate_net = nn.Linear(in_dim, 1)
        self.quarantine_gate_net = nn.Linear(in_dim, 1)
        self.promote_gate_net = nn.Linear(in_dim, 1)

        # --- Candidate slot content projection ---
        self.slot_candidate_proj = nn.Linear(
            input_dim + hidden_dim + slot_dim + w_dim + p_dim, slot_dim
        )

        # --- Memory bank ---
        self.memory_bank = MemoryBank(
            bank_id=bank_id,
            num_slots=num_slots,
            slot_dim=slot_dim,
            device=self.device,
        )

        self.to(self.device)

    # ------------------------------------------------------------------
    # Forward step
    # ------------------------------------------------------------------

    def forward(
        self,
        x_t: torch.Tensor,
        h_prev: torch.Tensor,
        c_prev: torch.Tensor,
        witness: WitnessFeatureVector,
        policy: WGRNNPolicy,
        policy_context: Optional[torch.Tensor] = None,
    ) -> tuple:
        """
        One WG-RNN step.

        Args:
            x_t:            (input_dim,) input embedding vector.
            h_prev:         (hidden_dim,) prior fast hidden state.
            c_prev:         (cell_dim,) prior fast cell state.
            witness:        WitnessFeatureVector (structured, derived from canonical evidence).
            policy:         WGRNNPolicy governing gate clamps.
            policy_context: optional (policy_context_dim,) policy tensor.

        Returns:
            h_t, c_t, memory_update_record (dict stub)
        """
        # ------------------------------------------------------------------
        # 0. Authority check: if transport or canonicalization fails, no-op.
        # ------------------------------------------------------------------
        authority = witness.compute_authority()
        if authority == 0.0:
            record = self._no_op_record(witness, reason="authority_zero")
            return h_prev, c_prev, record

        if not witness.policy_allow_write and not witness.policy_allow_promote:
            record = self._no_op_record(witness, reason="policy_blocked")
            return h_prev, c_prev, record

        # ------------------------------------------------------------------
        # 1. Witness tensor
        # ------------------------------------------------------------------
        w = witness.to_tensor(self.device)

        # ------------------------------------------------------------------
        # 2. Slot query and memory read
        # ------------------------------------------------------------------
        q = self.query_proj(torch.cat([x_t, h_prev, w]))
        attention = self._slot_attention(q, h_prev)
        r = self.memory_bank.read(attention)

        # ------------------------------------------------------------------
        # 3. Build combined input vector
        # ------------------------------------------------------------------
        combined_parts = [x_t, h_prev, r, w]
        if policy_context is not None:
            combined_parts.append(policy_context)
        combined = torch.cat(combined_parts)

        # ------------------------------------------------------------------
        # 4. Fast LSTM-style recurrence
        # ------------------------------------------------------------------
        u = torch.tanh(self.fast_candidate(combined))
        i = torch.sigmoid(self.fast_input_gate(combined))
        f = torch.sigmoid(self.fast_forget_gate(combined))
        o = torch.sigmoid(self.fast_output_gate(combined))

        c_t = f * c_prev + i * u
        h_t = o * torch.tanh(c_t)

        # ------------------------------------------------------------------
        # 5. Witness-specific gate computation (raw, before clamps)
        # ------------------------------------------------------------------
        g_write_raw = torch.sigmoid(self.write_gate_net(combined)).item()
        g_decay_raw = torch.sigmoid(self.decay_gate_net(combined)).item()
        g_quarantine_raw = torch.sigmoid(self.quarantine_gate_net(combined)).item()
        g_promote_raw = torch.sigmoid(self.promote_gate_net(combined)).item()

        gates_before = {
            "g_write": g_write_raw,
            "g_decay": g_decay_raw,
            "g_quarantine": g_quarantine_raw,
            "g_promote": g_promote_raw,
        }

        # ------------------------------------------------------------------
        # 6. Hard policy clamps (normative — must not be bypassed)
        # ------------------------------------------------------------------
        g_write, g_decay, g_quarantine, g_promote = self._apply_policy_clamps(
            g_write_raw, g_decay_raw, g_quarantine_raw, g_promote_raw,
            witness, policy
        )

        gates_after = {
            "g_write": g_write,
            "g_decay": g_decay,
            "g_quarantine": g_quarantine,
            "g_promote": g_promote,
        }

        # ------------------------------------------------------------------
        # 7. Memory updates
        # ------------------------------------------------------------------
        affected_slot_ids = []

        if g_write > 0.0 or g_decay > 0.0:
            affected_slot_ids = self._update_memory_slots(
                x_t=x_t,
                h_t=h_t,
                attention=attention,
                g_write=g_write,
                g_decay=g_decay,
                g_quarantine=g_quarantine,
                g_promote=g_promote,
                witness=witness,
                policy=policy,
                policy_context=policy_context,
            )

        # ------------------------------------------------------------------
        # 8. Create MemoryUpdateRecord (replayable stub)
        # ------------------------------------------------------------------
        record = self._create_memory_update_record(
            witness=witness,
            gates_before=gates_before,
            gates_after=gates_after,
            authority=authority,
            affected_slot_ids=affected_slot_ids,
        )

        return h_t, c_t, record

    # ------------------------------------------------------------------
    # Slot attention
    # ------------------------------------------------------------------

    def _slot_attention(
        self, query: torch.Tensor, h_prev: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute per-slot attention weights.
        Returns: (num_slots,) softmax weights.
        """
        # Simple dot-product attention against slot content vectors.
        scores = self.memory_bank.content_matrix @ query  # (K,)
        return F.softmax(scores, dim=0)

    # ------------------------------------------------------------------
    # Policy clamps (normative)
    # ------------------------------------------------------------------

    def _apply_policy_clamps(
        self,
        g_write: float,
        g_decay: float,
        g_quarantine: float,
        g_promote: float,
        witness: WitnessFeatureVector,
        policy: WGRNNPolicy,
    ) -> tuple:
        """
        Apply the mandatory hard clamps from the WG-RNN contract section 9.
        These override all learned gate values.
        """
        # 9.1 Write clamp
        if not witness.policy_allow_write:
            g_write = 0.0
        if witness.invalidation_score > policy.threshold_invalidate:
            g_write = 0.0

        # 9.2 Promotion clamp
        if witness.replayability_score < policy.min_replay:
            g_promote = 0.0
        if witness.contradiction_score > policy.max_contradiction:
            g_promote = 0.0
        if not witness.policy_allow_promote:
            g_promote = 0.0

        # 9.3 Quarantine clamp (forced HIGH)
        if (
            witness.novelty_score > policy.high_novelty_threshold
            and witness.confidence_score < policy.low_confidence_threshold
        ):
            g_quarantine = 1.0

        # 9.4 Human review clamp
        if witness.human_review_required:
            g_promote = 0.0
            g_write = min(g_write, policy.candidate_write_upper_bound)

        # 9.5 Action risk clamp
        if witness.action_risk > policy.risk_limit:
            g_write = 0.0

        # 9.6 Transport / canonicalization clamp (already handled in authority check,
        # but enforced here too for belt-and-suspenders)
        if not witness.transport_validated or not witness.canonicalization_validated:
            g_write = 0.0
            g_promote = 0.0

        return g_write, g_decay, g_quarantine, g_promote

    # ------------------------------------------------------------------
    # Memory slot updates
    # ------------------------------------------------------------------

    def _update_memory_slots(
        self,
        x_t: torch.Tensor,
        h_t: torch.Tensor,
        attention: torch.Tensor,
        g_write: float,
        g_decay: float,
        g_quarantine: float,
        g_promote: float,
        witness: WitnessFeatureVector,
        policy: WGRNNPolicy,
        policy_context: Optional[torch.Tensor],
    ) -> list:
        """
        Update candidate/quarantine/stable slots based on clamped gates.
        Returns list of affected slot IDs.
        """
        affected = []

        for k, slot in enumerate(self.memory_bank.slots):
            if slot.trust_status == "tombstoned" or slot.trust_status == "deprecated":
                continue

            attn_k = attention[k].item()
            g_write_k = attn_k * g_write

            # Compute candidate slot content
            slot_content_k = self.memory_bank.content_matrix[k].detach()
            combined_slot = torch.cat(
                [x_t, h_t, slot_content_k]
                + ([witness.to_tensor(self.device)])
                + ([policy_context] if policy_context is not None else [])
            )
            m_tilde_k = torch.tanh(self.slot_candidate_proj(combined_slot))

            if g_quarantine >= 1.0 or (
                witness.novelty_score > policy.high_novelty_threshold
                and witness.confidence_score < policy.low_confidence_threshold
            ):
                # Write to quarantine slot
                if slot.trust_status in ("candidate",):
                    if g_write_k > 0.0:
                        delta = g_write_k * (m_tilde_k - slot_content_k)
                        delta = self._clamp_delta(delta, policy.max_content_update_norm)
                        self.memory_bank.apply_update(delta, k, "quarantined", witness)
                        affected.append(k)
            elif slot.trust_status in ("candidate", "quarantined"):
                # Standard candidate write
                if g_write_k > 0.0:
                    decay_factor = 1.0 - g_decay
                    delta = (
                        decay_factor * (-slot_content_k)  # decay component
                        + g_write_k * (1.0 - g_quarantine) * (m_tilde_k - slot_content_k)
                    )
                    delta = self._clamp_delta(delta, policy.max_content_update_norm)
                    self.memory_bank.apply_update(delta, k, slot.trust_status, witness)
                    affected.append(k)
                elif g_decay > 0.0:
                    decay_delta = -g_decay * slot_content_k
                    decay_delta = self._clamp_delta(decay_delta, policy.max_content_update_norm)
                    self.memory_bank.apply_update(decay_delta, k, slot.trust_status, witness)
                    affected.append(k)
            elif slot.trust_status == "stable":
                # Stable memory: decay only; promotion writes are a separate governed flow.
                if g_decay > 0.0:
                    decay_delta = -g_decay * slot_content_k
                    decay_delta = self._clamp_delta(decay_delta, policy.max_content_update_norm)
                    self.memory_bank.apply_update(decay_delta, k, "stable", witness)
                    affected.append(k)
                # NOTE: promotion_write to stable slots requires a SlotPromotionRequest.
                # That is a governed external flow, not handled inline here.

        return affected

    @staticmethod
    def _clamp_delta(delta: torch.Tensor, max_norm: float) -> torch.Tensor:
        norm = delta.norm()
        if norm > max_norm:
            delta = delta * (max_norm / (norm + 1e-8))
        return delta

    # ------------------------------------------------------------------
    # Record helpers
    # ------------------------------------------------------------------

    def _no_op_record(self, witness: WitnessFeatureVector, reason: str) -> dict:
        return {
            "update_kind": "no_op",
            "reason": reason,
            "witness_feature_vector_id": witness.witness_feature_vector_id,
            "authority_t": 0.0,
            "affected_slot_ids": [],
        }

    def _create_memory_update_record(
        self,
        witness: WitnessFeatureVector,
        gates_before: dict,
        gates_after: dict,
        authority: float,
        affected_slot_ids: list,
    ) -> dict:
        """
        Stub for MemoryUpdateRecord.
        A production implementation must persist this to a replayable log.
        """
        return {
            "memory_update_record_id": hashlib.sha256(
                json.dumps({
                    "witness_id": witness.witness_feature_vector_id,
                    "ts": time.time(),
                    "slots": affected_slot_ids,
                }).encode()
            ).hexdigest()[:16],
            "update_kind": (
                "no_op" if not affected_slot_ids
                else "candidate_write"
            ),
            "witness_feature_vector_id": witness.witness_feature_vector_id,
            "gate_values_before_clamp": gates_before,
            "gate_values_after_clamp": gates_after,
            "authority_t": authority,
            "affected_slot_ids": affected_slot_ids,
            "trust_status": witness.trust_status,
            # replay field is a stub; production must bind full WGRNNReplayIdentity
            "replay": {
                "deterministic_required": True,
                "replay_trace_id": None,
            },
        }
```

---

## 8. Prototype v1 usage example

This is a minimal loop showing the cell in use.  
No GPU training. No global backprop.  
State evolves from chronological evidence.

```python
def run_prototype_v1_loop():
    device = torch.device("cpu")

    cell = WGRNNCell(
        input_dim=64,
        hidden_dim=128,
        cell_dim=128,
        slot_dim=64,
        num_slots=16,
        device=device,
    )

    policy = WGRNNPolicy(
        runtime_mode="sandbox",
        learning_mode="sandbox",
        content_adaptation_allowed=False,
    )

    # Initial state
    h = torch.zeros(128, device=device)
    c = torch.zeros(128, device=device)

    # Simulate a chronological event stream.
    # In production, each event goes through:
    # raw event -> EvidenceBundle -> CandidateWitness -> CanonicalWitnessFact -> WitnessFeatureVector
    events = [
        {
            "id": "wfv-001",
            "confidence": 0.72, "contradiction": 0.05, "novelty": 0.40,
            "recurrence": 0.30, "replayability": 0.80,
            "allow_write": True, "allow_promote": False,
            "transport_ok": True, "canon_ok": True,
        },
        {
            "id": "wfv-002",
            "confidence": 0.85, "contradiction": 0.05, "novelty": 0.30,
            "recurrence": 0.65, "replayability": 0.92,
            "allow_write": True, "allow_promote": False,
            "transport_ok": True, "canon_ok": True,
        },
        {
            "id": "wfv-003",  # high novelty, low confidence -> quarantine
            "confidence": 0.25, "contradiction": 0.10, "novelty": 0.92,
            "recurrence": 0.10, "replayability": 0.55,
            "allow_write": True, "allow_promote": False,
            "transport_ok": True, "canon_ok": True,
        },
        {
            "id": "wfv-004",  # transport failed -> no-op
            "confidence": 0.99, "contradiction": 0.00, "novelty": 0.10,
            "recurrence": 0.90, "replayability": 0.98,
            "allow_write": True, "allow_promote": True,
            "transport_ok": False, "canon_ok": True,
        },
    ]

    for ev in events:
        x_t = torch.randn(64, device=device)  # placeholder for real embedding

        witness = WitnessFeatureVector(
            witness_feature_vector_id=ev["id"],
            confidence_score=ev["confidence"],
            contradiction_score=ev["contradiction"],
            novelty_score=ev["novelty"],
            recurrence_score=ev["recurrence"],
            replayability_score=ev["replayability"],
            source_integrity=0.90,
            source_diversity=0.70,
            staleness_score=0.05,
            invalidation_score=0.00,
            action_risk=0.10,
            policy_allow_write=ev["allow_write"],
            policy_allow_promote=ev["allow_promote"],
            human_review_required=False,
            profile_requested_authority=0.75,
            normalizer_confidence=0.85,
            policy_limit=0.70,
            transport_validated=ev["transport_ok"],
            canonicalization_validated=ev["canon_ok"],
            trust_status="canonicalized",
        )

        h, c, record = cell(x_t, h, c, witness, policy)

        print(
            f"event={ev['id']}  "
            f"update_kind={record['update_kind']}  "
            f"authority={record['authority_t']:.3f}  "
            f"slots={record['affected_slot_ids']}"
        )
```

---

## 9. What is explicitly not done here

The following are intentionally omitted from this skeleton and are governed separately:

1. **SlotPromotionRequest** workflow: promotion to stable status requires external replay, retention diagnostics, policy approval.
2. **Contradiction branching / SlotSplitRecord**: Prototype v2 scope.
3. **SlotConsolidationRecord / MemorySlotPruneRecord**: governed externally.
4. **Purge cascade hooks**: governed by `duotronic_evidence_purge_and_privacy_deletion_contract_v1_0.md`.
5. **Human review integration**: `duotronic_human_review_and_escalation_protocol_v1_0.md`.
6. **Full WGRNNReplayIdentity binding**: production stubs only.
7. **Local plasticity adapters (fast-weight Hebbian update)**: Prototype v3 scope.
8. **Distributed cluster integration**: DBP S2 session and `TaskOutcomeWitness` links.

---

## 10. Prototype progression checklist

| Phase | Scope | Notes |
|---|---|---|
| **Prototype v1** | LSTM core + slot memory + 4 witness gates + policy clamps | This skeleton |
| **Prototype v2** | + contradiction branching + candidate vs stable classes + replay score | Add `SlotSplitRecord` flow |
| **Prototype v3** | + local plasticity adapters + slot merge/split + action gating | Hebbian fast-weight update |
| **Production** | Full promotion path, replay fixtures, retention diagnostics, policy approval | Not in scope here |

---

## 11. Relationship to the normative contract

Every behavior in this skeleton is derived from:

```text
refs/duotronic_witness_gated_recurrent_cell_contract_v1_0.md
```

If this skeleton conflicts with the normative contract, the normative contract takes precedence.
