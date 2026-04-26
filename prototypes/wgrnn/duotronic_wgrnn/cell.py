from __future__ import annotations

import itertools
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

from .memory import MemoryBank
from .policy import WGRNNPolicy
from .records import MemoryUpdateRecord
from .replay import build_replay_identity, hash_tensor
from .witness import WitnessFeatureVector


class WGRNNCell(nn.Module):
    WITNESS_DIM = 18

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        cell_dim: int,
        slot_dim: int,
        num_slots: int,
        policy_context_dim: int = 0,
        bank_id: str = "research-bank",
        device: Optional[torch.device] = None,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.cell_dim = cell_dim
        self.slot_dim = slot_dim
        self.num_slots = num_slots
        self.policy_context_dim = policy_context_dim
        self.device = device or torch.device("cpu")
        self.bank_id = bank_id
        self.cell_profile_id = "wgrnn-research-prototype@v0.1"
        self._record_counter = itertools.count(1)

        combined_dim = input_dim + hidden_dim + slot_dim + self.WITNESS_DIM + policy_context_dim
        self.fast_input_gate = nn.Linear(combined_dim, cell_dim)
        self.fast_forget_gate = nn.Linear(combined_dim, cell_dim)
        self.fast_output_gate = nn.Linear(combined_dim, hidden_dim)
        self.fast_candidate = nn.Linear(combined_dim, cell_dim)
        self.query_proj = nn.Linear(input_dim + hidden_dim + self.WITNESS_DIM, slot_dim)
        self.write_gate_net = nn.Linear(combined_dim, 1)
        self.decay_gate_net = nn.Linear(combined_dim, 1)
        self.quarantine_gate_net = nn.Linear(combined_dim, 1)
        self.promote_gate_net = nn.Linear(combined_dim, 1)
        self.slot_candidate_proj = nn.Linear(input_dim + hidden_dim + slot_dim + self.WITNESS_DIM + policy_context_dim, slot_dim)
        self.memory_bank = MemoryBank(bank_id=bank_id, num_slots=num_slots, slot_dim=slot_dim, device=self.device)
        self.to(self.device)

    def forward(
        self,
        x_t: torch.Tensor,
        h_prev: torch.Tensor,
        c_prev: torch.Tensor,
        witness: WitnessFeatureVector,
        policy: WGRNNPolicy,
        policy_context: Optional[torch.Tensor] = None,
    ) -> tuple[torch.Tensor, torch.Tensor, MemoryUpdateRecord]:
        witness.validate_bounds()
        policy.validate_policy()
        x_t = x_t.to(self.device)
        h_prev = h_prev.to(self.device)
        c_prev = c_prev.to(self.device)
        policy_context = self._policy_context(policy_context)
        authority = witness.compute_authority()

        if authority == 0.0:
            return h_prev, c_prev, self._no_op_record(witness, policy, authority, reason="authority_zero")

        w = witness.to_tensor(self.device)
        query = self.query_proj(torch.cat([x_t, h_prev, w]))
        attention = self._slot_attention(query, h_prev)
        memory_read = self.memory_bank.read(attention)
        combined = torch.cat([x_t, h_prev, memory_read, w, policy_context])

        fast_candidate = torch.tanh(self.fast_candidate(combined))
        fast_input = torch.sigmoid(self.fast_input_gate(combined))
        fast_forget = torch.sigmoid(self.fast_forget_gate(combined))
        fast_output = torch.sigmoid(self.fast_output_gate(combined))
        c_t = fast_forget * c_prev + fast_input * fast_candidate
        h_t = fast_output * torch.tanh(c_t)

        gates_before = {
            "g_write": float(torch.sigmoid(self.write_gate_net(combined)).item()),
            "g_decay": float(torch.sigmoid(self.decay_gate_net(combined)).item()),
            "g_quarantine": float(torch.sigmoid(self.quarantine_gate_net(combined)).item()),
            "g_promote": float(torch.sigmoid(self.promote_gate_net(combined)).item()),
        }
        g_write, g_decay, g_quarantine, g_promote = self._apply_policy_clamps(
            gates_before["g_write"],
            gates_before["g_decay"],
            gates_before["g_quarantine"],
            gates_before["g_promote"],
            witness,
            policy,
        )
        gates_after = {
            "g_write": g_write,
            "g_decay": g_decay,
            "g_quarantine": g_quarantine,
            "g_promote": g_promote,
        }

        target_slot_id = int(torch.argmax(attention).item())
        slot_candidate_input = torch.cat([x_t, h_prev, memory_read, w, policy_context])
        slot_candidate = torch.tanh(self.slot_candidate_proj(slot_candidate_input))
        record = self._update_memory_slots(
            slot_candidate,
            target_slot_id,
            witness,
            policy,
            gates_before,
            gates_after,
            authority,
        )
        return h_t, c_t, record

    def _policy_context(self, policy_context: Optional[torch.Tensor]) -> torch.Tensor:
        if self.policy_context_dim == 0:
            return torch.empty(0, device=self.device)
        if policy_context is None:
            return torch.zeros(self.policy_context_dim, device=self.device)
        return policy_context.to(self.device)

    def _slot_attention(self, query: torch.Tensor, h_prev: torch.Tensor) -> torch.Tensor:
        del h_prev
        logits = self.memory_bank.content_matrix.detach() @ query
        if torch.allclose(logits, torch.zeros_like(logits)):
            return torch.ones(self.num_slots, device=self.device) / self.num_slots
        return F.softmax(logits, dim=0)

    def _apply_policy_clamps(
        self,
        g_write: float,
        g_decay: float,
        g_quarantine: float,
        g_promote: float,
        witness: WitnessFeatureVector,
        policy: WGRNNPolicy,
    ) -> tuple[float, float, float, float]:
        authority = witness.compute_authority()
        if authority == 0.0:
            return 0.0, g_decay, g_quarantine, 0.0
        if not witness.policy_allow_write:
            g_write = 0.0
        if witness.invalidation_score > policy.threshold_invalidate:
            g_write = 0.0
        if witness.replayability_score < policy.min_replay:
            g_promote = 0.0
        if witness.contradiction_score > policy.max_contradiction:
            g_promote = 0.0
        if not witness.policy_allow_promote:
            g_promote = 0.0
        if witness.novelty_score > policy.high_novelty_threshold and witness.confidence_score < policy.low_confidence_threshold:
            g_quarantine = 1.0
            g_promote = 0.0
        if witness.human_review_required:
            g_promote = 0.0
            g_write = min(g_write, policy.candidate_write_upper_bound)
        if witness.action_risk > policy.risk_limit:
            g_write = 0.0
        return tuple(round(max(0.0, min(value, 1.0)), 6) for value in (g_write, g_decay, g_quarantine, g_promote))

    def _update_memory_slots(
        self,
        candidate_content: torch.Tensor,
        target_slot_id: int,
        witness: WitnessFeatureVector,
        policy: WGRNNPolicy,
        gates_before: dict[str, float],
        gates_after: dict[str, float],
        authority: float,
    ) -> MemoryUpdateRecord:
        g_write = gates_after["g_write"]
        g_quarantine = gates_after["g_quarantine"]
        slot = self.memory_bank.slots[target_slot_id]
        replay_identity = build_replay_identity(
            replay_identity_id=f"replay-{witness.witness_feature_vector_id}",
            cell_profile_id=self.cell_profile_id,
            cell_profile_hash=self._cell_profile_hash(),
            memory_bank=self.memory_bank,
            witness=witness,
            policy=policy,
        )

        if g_write <= 0.0 or not slot.writable_inline():
            update_kind = "no_op"
            affected_slot_ids: list[int] = []
            trust_status = slot.trust_status
        else:
            trust_status = "quarantined" if g_quarantine >= 1.0 else "candidate"
            update_kind = "quarantine_write" if trust_status == "quarantined" else "candidate_write"
            delta = g_write * (candidate_content.detach() - self.memory_bank.content_matrix[target_slot_id].detach())
            delta = self._clamp_delta(delta, policy.max_content_update_norm)
            record_id = self._next_record_id(witness)
            updated = self.memory_bank.apply_update(
                delta,
                target_slot_id,
                trust_status,
                witness,
                record_id=record_id,
                replay_identity=replay_identity.digest,
            )
            affected_slot_ids = [target_slot_id] if updated else []
            if not updated:
                update_kind = "no_op"
            return self._create_memory_update_record(
                record_id,
                witness,
                gates_before,
                gates_after,
                authority,
                affected_slot_ids,
                update_kind,
                trust_status,
                replay_identity.digest,
            )

        return self._create_memory_update_record(
            self._next_record_id(witness),
            witness,
            gates_before,
            gates_after,
            authority,
            affected_slot_ids,
            update_kind,
            trust_status,
            replay_identity.digest,
        )

    def _clamp_delta(self, delta: torch.Tensor, max_norm: float) -> torch.Tensor:
        norm = torch.linalg.vector_norm(delta)
        if norm <= max_norm or norm == 0:
            return delta
        return delta * (max_norm / norm)

    def _create_memory_update_record(
        self,
        record_id: str,
        witness: WitnessFeatureVector,
        gates_before: dict[str, float],
        gates_after: dict[str, float],
        authority: float,
        affected_slot_ids: list[int],
        update_kind: str,
        trust_status: str,
        replay_digest: str | None,
    ) -> MemoryUpdateRecord:
        return MemoryUpdateRecord(
            memory_update_record_id=record_id,
            memory_bank_id=self.memory_bank.bank_id,
            step_id=f"step-{witness.witness_feature_vector_id}",
            witness_feature_vector_id=witness.witness_feature_vector_id,
            gate_values_before_clamp={key: round(value, 6) for key, value in gates_before.items()},
            gate_values_after_clamp={key: round(value, 6) for key, value in gates_after.items()},
            authority_t=round(authority, 6),
            affected_slot_ids=affected_slot_ids,
            update_kind=update_kind,
            trust_status=trust_status,
            replay_identity_ref=replay_digest,
            policy_decision_id="policy-sandbox-clamp",
            input_refs=[witness.witness_feature_vector_id],
        )

    def _no_op_record(
        self,
        witness: WitnessFeatureVector,
        policy: WGRNNPolicy,
        authority: float,
        *,
        reason: str,
    ) -> MemoryUpdateRecord:
        del policy, reason
        zero_gates = {"g_write": 0.0, "g_decay": 0.0, "g_quarantine": 0.0, "g_promote": 0.0}
        return self._create_memory_update_record(
            self._next_record_id(witness),
            witness,
            zero_gates,
            zero_gates,
            authority,
            [],
            "no_op",
            "candidate",
            None,
        )

    def _next_record_id(self, witness: WitnessFeatureVector) -> str:
        return f"mur-{witness.witness_feature_vector_id}-{next(self._record_counter):04d}"

    def _cell_profile_hash(self) -> str:
        return hash_tensor(torch.tensor([self.input_dim, self.hidden_dim, self.cell_dim, self.slot_dim, self.num_slots], dtype=torch.float32))
