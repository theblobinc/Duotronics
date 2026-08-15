from __future__ import annotations

import json
import math
from typing import Any

from .crypto_primitives import shake256_ref
from .models import NaturalLanguageActivationWitness, now_ms, stable_id


def cosine(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    dot = sum(float(a[i]) * float(b[i]) for i in range(n))
    na = math.sqrt(sum(float(a[i]) ** 2 for i in range(n)))
    nb = math.sqrt(sum(float(b[i]) ** 2 for i in range(n)))
    if na == 0 or nb == 0:
        return 0.0
    return max(-1.0, min(1.0, dot / (na * nb)))


def mse(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return 1.0
    return sum((float(a[i]) - float(b[i])) ** 2 for i in range(n)) / n


def activation_digest(v: list[float]) -> str:
    return shake256_ref([round(float(x), 6) for x in v])


class ActivationVerbalizer:
    """Deterministic AV shim: activation -> natural language explanation."""

    def explain(self, activation: list[float], *, prompt: str, response_text: str) -> dict[str, Any]:
        if not activation:
            text = "No activation signal was captured."
            top = []
        else:
            ranked = sorted(enumerate(activation), key=lambda item: abs(item[1]), reverse=True)[:5]
            top = [{"index": i, "value": round(v, 4)} for i, v in ranked]
            polarity = "positive" if sum(activation) >= 0 else "negative"
            text = (
                f"Captured WG-RNN state shows {polarity} recurrent pressure with "
                f"dominant dimensions {', '.join(str(t['index']) for t in top)}. "
                "This is a diagnostic NLA explanation, not model intent or proof."
            )
        return {
            "av_model": "deterministic-av-shim-v1",
            "prompt_integrity": shake256_ref(prompt),
            "response_integrity": shake256_ref(response_text),
            "explanation_text": text,
            "dominant_dimensions": top,
            "parser_status": "parsed" if text else "empty",
        }


class ActivationReconstructor:
    """Deterministic AR shim: natural language explanation -> activation estimate."""

    def reconstruct(self, explanation: dict[str, Any], dim: int) -> dict[str, Any]:
        out = [0.0] * dim
        for item in explanation.get("dominant_dimensions", []):
            try:
                idx = int(item.get("index", 0))
                val = float(item.get("value", 0.0))
            except Exception:
                continue
            if 0 <= idx < dim:
                out[idx] = val
        # Add a small stable floor from explanation text to avoid a fake perfect reconstruction.
        text = str(explanation.get("explanation_text", ""))
        for i, ch in enumerate(text.encode("utf-8", errors="ignore")[: dim * 2]):
            out[i % dim] += ((ch % 7) - 3) * 0.001
        return {
            "ar_model": "deterministic-ar-shim-v1",
            "reconstruction_vector": [round(max(-1.0, min(1.0, x)), 6) for x in out],
            "reconstruction_ref": "inline:deterministic-ar-shim-v1",
        }


class NLAFidelityGate:
    def __init__(self, *, min_cosine: float, max_mse: float, min_repeat_stability: float) -> None:
        self.min_cosine = float(min_cosine)
        self.max_mse = float(max_mse)
        self.min_repeat_stability = float(min_repeat_stability)

    def score(self, activation: list[float], reconstruction: list[float], explanation: dict[str, Any]) -> dict[str, Any]:
        cos = cosine(activation, reconstruction)
        err = mse(activation, reconstruction)
        parser_ok = explanation.get("parser_status") == "parsed"
        repeat_stability = max(0.0, min(1.0, 1.0 - err * 3.0))
        accepted = parser_ok and cos >= self.min_cosine and err <= self.max_mse and repeat_stability >= self.min_repeat_stability
        status = "accepted" if accepted else "quarantined"
        if cos >= 0.90 and err <= self.max_mse / 2:
            fidelity_status = "high"
        elif accepted:
            fidelity_status = "medium"
        else:
            fidelity_status = "low"
        return {
            "parser_status": "passed" if parser_ok else "failed",
            "reconstruction_status": "passed" if cos >= self.min_cosine and err <= self.max_mse else "failed",
            "cosine_similarity": round(cos, 6),
            "mse": round(err, 6),
            "repeat_stability": round(repeat_stability, 6),
            "fidelity_status": fidelity_status,
            "accepted": accepted,
            "lifecycle_state": status,
        }


class NLAWitnessFactory:
    def __init__(self, *, loop_id: str, node_id: str, min_cosine: float, max_mse: float, min_repeat_stability: float) -> None:
        self.loop_id = loop_id
        self.node_id = node_id
        self.av = ActivationVerbalizer()
        self.ar = ActivationReconstructor()
        self.gate = NLAFidelityGate(min_cosine=min_cosine, max_mse=max_mse, min_repeat_stability=min_repeat_stability)

    def create(
        self,
        *,
        activation: list[float],
        prompt: str,
        response_text: str,
        source_model: dict[str, Any],
        policy_flags: dict[str, Any],
        wg_rnn_update_id: str | None,
    ) -> NaturalLanguageActivationWitness:
        explanation = self.av.explain(activation, prompt=prompt, response_text=response_text)
        reconstruction = self.ar.reconstruct(explanation, len(activation))
        fidelity = self.gate.score(activation, reconstruction["reconstruction_vector"], explanation)
        policy = {
            "mode": policy_flags.get("mode", "audit_only"),
            "may_influence_response": bool(policy_flags.get("may_influence_response", False) and fidelity["accepted"]),
            "may_write_memory": bool(policy_flags.get("may_write_memory", False) and fidelity["accepted"]),
            "may_promote_witness": bool(policy_flags.get("may_promote_witness", False) and fidelity["accepted"]),
            "human_review_required": not fidelity["accepted"] or fidelity["fidelity_status"] != "high",
        }
        witness_payload = {
            "loop_id": self.loop_id,
            "node_id": self.node_id,
            "activation_digest": activation_digest(activation),
            "explanation": explanation.get("explanation_text"),
            "fidelity": fidelity,
            "wg_rnn_update_id": wg_rnn_update_id,
        }
        return NaturalLanguageActivationWitness(
            witness_id=stable_id("nla", witness_payload),
            loop_id=self.loop_id,
            node_id=self.node_id,
            source_model=source_model,
            activation={
                "activation_vector_ref": "inline:sandbox-vector",
                "activation_digest": activation_digest(activation),
                "norm": round(math.sqrt(sum(x * x for x in activation)), 6),
                "capture_timestamp_ms": now_ms(),
            },
            verbalizer=explanation,
            reconstructor={k: v for k, v in reconstruction.items() if k != "reconstruction_vector"} | {
                "reconstruction_digest": activation_digest(reconstruction["reconstruction_vector"]),
                "mse": fidelity["mse"],
                "cosine": fidelity["cosine_similarity"],
            },
            fidelity=fidelity,
            lifecycle={
                "state": fidelity["lifecycle_state"],
                "captured": True,
                "verbalized": True,
                "scored": True,
                "accepted": fidelity["accepted"],
                "quarantined": not fidelity["accepted"],
                "promoted": False,
            },
            policy=policy,
            wg_rnn_update_id=wg_rnn_update_id,
            created_at_ms=now_ms(),
        )
