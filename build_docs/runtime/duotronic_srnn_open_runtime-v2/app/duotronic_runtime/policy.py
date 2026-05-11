from __future__ import annotations

from typing import Any


class PolicyEngine:
    """Small explicit policy gate for the reference runtime."""

    def __init__(self, *, nla_policy_mode: str, allow_influence: bool, allow_memory_write: bool, allow_promote: bool) -> None:
        self.nla_policy_mode = nla_policy_mode
        self.allow_influence = allow_influence
        self.allow_memory_write = allow_memory_write
        self.allow_promote = allow_promote

    def nla_flags(self) -> dict[str, Any]:
        return {
            "mode": self.nla_policy_mode,
            "may_influence_response": self.allow_influence,
            "may_write_memory": self.allow_memory_write,
            "may_promote_witness": self.allow_promote,
        }

    def decide(self, *, requested_action: str, wg_rnn_update: dict[str, Any], nla_witness: dict[str, Any]) -> dict[str, Any]:
        reasons: list[str] = []
        allowed = True
        action = requested_action or "observe"
        authority = float(wg_rnn_update.get("authority_t", 0.0) or 0.0)
        trust_status = str(wg_rnn_update.get("trust_status", "quarantine"))
        nla_policy = nla_witness.get("policy", {}) if isinstance(nla_witness, dict) else {}
        fidelity = nla_witness.get("fidelity", {}) if isinstance(nla_witness, dict) else {}

        if action == "memory_write":
            if not self.allow_memory_write:
                allowed = False
                reasons.append("NLA memory writes disabled by runtime policy")
            if not nla_policy.get("may_write_memory", False):
                allowed = False
                reasons.append("NLA witness may_write_memory gate is false")
            if trust_status != "candidate":
                allowed = False
                reasons.append(f"WG-RNN update trust_status is {trust_status}")
            if authority < 0.55:
                allowed = False
                reasons.append("WG-RNN authority below memory write threshold")
        elif action == "promote_witness":
            if not self.allow_promote:
                allowed = False
                reasons.append("NLA witness promotion disabled by runtime policy")
            if not nla_policy.get("may_promote_witness", False):
                allowed = False
                reasons.append("NLA witness may_promote_witness gate is false")
            if fidelity.get("fidelity_status") != "high":
                allowed = False
                reasons.append("NLA promotion requires high fidelity")
        elif action == "influence_response":
            if not self.allow_influence or not nla_policy.get("may_influence_response", False):
                allowed = False
                reasons.append("NLA influence-response is disabled or not gated")
        else:
            reasons.append("Observation-only action; audit evidence permitted")

        if not reasons:
            reasons.append("All configured gates passed")

        return {
            "policy_engine": "duotronic-reference-policy-v1",
            "requested_action": action,
            "decision": "allow" if allowed else "deny",
            "allowed": allowed,
            "authority_t": authority,
            "reasons": reasons,
            "non_collapse": {
                "model_output_is_truth": False,
                "nla_explanation_is_intent": False,
                "policy_approval_is_proof": False,
                "computation_is_theorem": False,
            },
        }

    def explain(self) -> dict[str, Any]:
        return {
            "summary": "NLA is audit evidence by default. WG-RNN owns governed memory updates. Policy gates decide whether evidence may influence response, memory, or promotion.",
            "nla_policy_mode": self.nla_policy_mode,
            "allow_influence_response": self.allow_influence,
            "allow_memory_write": self.allow_memory_write,
            "allow_promote_witness": self.allow_promote,
            "rules": [
                "NLA explanations are diagnostic evidence, not hidden intent.",
                "NLA cannot write memory unless both .env policy and witness fidelity gates allow it.",
                "WG-RNN updates can be candidate, quarantine, promoted, or rejected.",
                "Model output, transport validity, semantic validity, and authority remain separate.",
            ],
        }
