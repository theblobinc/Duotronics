from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def sha256_ref(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def now_ms() -> int:
    return int(time.time() * 1000)


@dataclass(frozen=True)
class CorpusRef:
    version: str = "unresolved"
    digest: str = "sha256:unresolved"
    manifest_ref: str = "unresolved"

    def to_dict(self) -> dict[str, Any]:
        return {"version": self.version, "digest": self.digest, "manifest_ref": self.manifest_ref}


@dataclass
class WitnessEnvelope:
    witness_type: str
    payload: dict[str, Any]
    force: str = "observe"
    observer_id: str = "srnn-runtime"
    corpus: CorpusRef = field(default_factory=CorpusRef)
    status: str = "recorded"
    created_at_ms: int = field(default_factory=now_ms)
    witness_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        base = {
            "witness_type": self.witness_type,
            "force": self.force,
            "observer_id": self.observer_id,
            "corpus": self.corpus.to_dict(),
            "status": self.status,
            "payload": self.payload,
            "created_at_ms": self.created_at_ms,
        }
        base["payload_digest"] = sha256_ref(self.payload)
        base["witness_id"] = self.witness_id or "witness_" + hashlib.sha256(canonical_json(base).encode("utf-8")).hexdigest()[:24]
        return base


@dataclass
class EvidenceClaim:
    subject: str
    predicate: str
    object: Any
    claim_kind: str = "observation"
    claim_status: str = "observed"
    epistemic_status: str = "observed"
    force: str = "observe"
    support: list[str] = field(default_factory=list)
    corpus: CorpusRef = field(default_factory=CorpusRef)
    created_at_ms: int = field(default_factory=now_ms)

    def to_dict(self) -> dict[str, Any]:
        body = {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "claim_kind": self.claim_kind,
            "claim_status": self.claim_status,
            "epistemic_status": self.epistemic_status,
            "force": self.force,
            "support": self.support,
            "corpus": self.corpus.to_dict(),
            "created_at_ms": self.created_at_ms,
        }
        body["claim_digest"] = sha256_ref(body)
        body["claim_id"] = "claim_" + body["claim_digest"].split(":", 1)[1][:24]
        return body


class NonCollapseEngine:
    """Guardrails that stop weak evidence from silently becoming strong authority."""

    FORBIDDEN: set[tuple[str, str]] = {
        ("model_output", "truth"),
        ("model_output", "theorem"),
        ("computed", "theorem"),
        ("simulation", "proof"),
        ("policy_approved", "truth"),
        ("self_trained", "authoritative"),
        ("retrieval_hit", "fact"),
        ("embedding", "evidence_of_truth"),
        ("generated_media", "external_observation"),
    }

    def check_transition(self, *, source_status: str, target_status: str, witnesses: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        witnesses = witnesses or []
        pair = (source_status, target_status)
        proof_witness = any(w.get("witness_type") in {"LeanProofWitness", "ProofAuthorityWitness"} and w.get("status") in {"accepted", "recorded"} for w in witnesses)
        release_witness = any(w.get("witness_type") in {"HumanApprovalWitness", "ReleaseGateWitness"} and w.get("status") in {"accepted", "recorded"} for w in witnesses)
        allowed = True
        reasons: list[str] = []
        if pair in self.FORBIDDEN:
            allowed = False
            reasons.append(f"forbidden epistemic collapse: {source_status} -> {target_status}")
        if target_status in {"theorem", "proof"} and not proof_witness:
            allowed = False
            reasons.append("proof/theorem promotion requires a proof authority witness")
        if target_status in {"authoritative", "production", "released"} and not release_witness:
            allowed = False
            reasons.append("authority or production promotion requires a release/human approval witness")
        if allowed and not reasons:
            reasons.append("transition remains inside declared evidence force")
        return {
            "engine": "duotronic-non-collapse-v1",
            "source_status": source_status,
            "target_status": target_status,
            "allowed": allowed,
            "decision": "allow" if allowed else "deny",
            "reasons": reasons,
            "witness_count": len(witnesses),
        }


class EvidenceKernel:
    def __init__(self, observer_id: str = "srnn-runtime", corpus: CorpusRef | None = None) -> None:
        self.observer_id = observer_id
        self.corpus = corpus or CorpusRef()
        self.non_collapse = NonCollapseEngine()

    def witness(self, witness_type: str, payload: dict[str, Any], *, force: str = "observe", status: str = "recorded") -> dict[str, Any]:
        return WitnessEnvelope(witness_type=witness_type, payload=payload, force=force, observer_id=self.observer_id, corpus=self.corpus, status=status).to_dict()

    def claim(self, *, subject: str, predicate: str, object: Any, claim_kind: str = "observation", claim_status: str = "observed", epistemic_status: str = "observed", force: str = "observe", support: list[str] | None = None) -> dict[str, Any]:
        return EvidenceClaim(subject=subject, predicate=predicate, object=object, claim_kind=claim_kind, claim_status=claim_status, epistemic_status=epistemic_status, force=force, support=support or [], corpus=self.corpus).to_dict()

    def model_output_witness(self, *, provider: str, model: str, prompt: str, response_text: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {
            "provider": provider,
            "model": model,
            "prompt_digest": sha256_ref(prompt),
            "output_digest": sha256_ref(response_text),
            "sampling_params": params or {},
            "non_collapse": {
                "model_output_is_truth": False,
                "model_confidence_is_proof": False,
                "model_response_is_authority": False,
            },
        }
        return self.witness("ModelOutputWitness", payload, force="propose")


def nla_activation_witness_contract_v1(
    *,
    nla_witness: dict[str, Any],
    source_model: dict[str, Any],
    loop_id: str,
    node_id: str,
    policy_mode: str = "audit_only",
) -> dict[str, Any]:
    """Project the legacy runtime NLA witness into the current v1 contract shape.

    This is a compatibility bridge: it preserves old runtime fields while exposing
    the newer schema_version/source_model/activation/fidelity/lifecycle/policy keys
    expected by the current witness contract.
    """
    activation = nla_witness.get("activation") or {}
    verbalizer = nla_witness.get("verbalizer") or {}
    reconstructor = nla_witness.get("reconstructor") or {}
    fidelity = nla_witness.get("fidelity") or {}
    lifecycle = nla_witness.get("lifecycle") or {}
    policy = nla_witness.get("policy") or {}

    created_ms = int(nla_witness.get("created_at_ms") or now_ms())
    created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(created_ms / 1000))

    backend = str(source_model.get("provider") or source_model.get("backend") or "unknown")
    if backend not in {"transformers", "sglang", "llama_server", "ollama", "other", "unknown"}:
        backend = "other"

    confidence = fidelity.get("cosine_similarity")
    if confidence is None:
        confidence = fidelity.get("confidence")
    try:
        confidence = max(0.0, min(1.0, float(confidence)))
    except Exception:
        confidence = 0.0

    status = str(fidelity.get("fidelity_status") or fidelity.get("status") or "unscored")
    if status not in {"high", "medium", "low", "failed", "unscored", "quarantined"}:
        status = "quarantined" if lifecycle.get("quarantined") else "unscored"

    current_state = str(lifecycle.get("state") or lifecycle.get("current_state") or status)
    if current_state not in {
        "requested", "captured", "verbalized", "scored", "accepted",
        "accepted_single_use_only", "diagnostic_only", "unscored_diagnostic",
        "quarantined", "human_review_pending", "human_review_accepted",
        "human_review_rejected", "promotable", "promoted_to_meta",
        "promoted_to_hyper", "expired", "failed"
    }:
        current_state = "quarantined" if status in {"low", "quarantined", "failed"} else "diagnostic_only"

    return {
        "schema_version": "nla-activation-witness/v1",
        "witness_id": str(nla_witness.get("witness_id") or "nla_" + sha256_ref(nla_witness).split(":", 1)[1][:20]),
        "request_id": None,
        "loop_id": str(loop_id or nla_witness.get("loop_id") or "loop-main"),
        "created_at": created_at,
        "source_model": {
            "model_id": str(source_model.get("model") or source_model.get("name") or "unknown"),
            "model_revision": None,
            "backend": backend,
            "backend_capability": "hidden_states_unavailable" if backend == "ollama" else "unknown",
            "layer_index": 0,
            "token_index": None,
            "pooling_rule": "runtime_shim",
            "d_model": int(len((nla_witness.get("activation") or {}).get("activation_vector", [])) or 1),
            "token_text_hash": None,
        },
        "activation": {
            "vector_ref": str(activation.get("activation_vector_ref") or "inline:sandbox-vector"),
            "vector_sha256": str(activation.get("activation_digest") or "sha256:" + "0" * 64),
            "norm_l2": float(activation.get("norm") or 0.0),
            "dtype": "float32",
            "capture_time_utc": created_at,
            "retention_class": "audit_artifact",
            "transcript_ref": None,
            "redaction_status": "none",
        },
        "verbalizer": {
            "av_model_id": str(verbalizer.get("av_model") or "deterministic-av-shim-v1"),
            "av_model_revision": None,
            "av_checkpoint_sha256": None,
            "sidecar_ref": verbalizer.get("sidecar_ref"),
            "sidecar_digest": str(verbalizer.get("response_integrity") or verbalizer.get("prompt_integrity") or "sha256:" + "0" * 64),
            "prompt_template_hash": str(verbalizer.get("prompt_integrity") or "sha256:" + "0" * 64),
            "injection_scale": None,
            "injection_token_id": None,
            "explanation_text": str(verbalizer.get("explanation_text") or ""),
            "raw_generation_ref": None,
            "explanation_tags_valid": bool(verbalizer.get("parser_status") in {"parsed", "passed"} or verbalizer.get("explanation_tags_valid") is True),
        },
        "reconstructor": {
            "ar_available": reconstructor.get("mse") is not None or reconstructor.get("cosine") is not None,
            "ar_model_id": reconstructor.get("ar_model"),
            "ar_model_revision": None,
            "ar_checkpoint_sha256": None,
            "reconstruction_vector_ref": reconstructor.get("reconstruction_ref"),
            "reconstruction_vector_sha256": reconstructor.get("reconstruction_digest"),
            "mse": reconstructor.get("mse"),
            "cosine_similarity": reconstructor.get("cosine") if reconstructor.get("cosine") is not None else reconstructor.get("cosine_similarity"),
        },
        "fidelity": {
            "status": status,
            "confidence": confidence,
            "repeat_stability": fidelity.get("repeat_stability"),
            "parser_valid": fidelity.get("parser_status") in {"passed", "parsed"} or bool(fidelity.get("parser_valid")),
            "sidecar_valid": bool(fidelity.get("sidecar_valid", False)),
            "replay_valid": bool(fidelity.get("replay_valid", False)),
            "contradiction_pressure_delta": None,
            "novelty_delta": None,
            "recurrence_family": None,
            "human_review_required": bool((policy or {}).get("human_review_required", True)),
        },
        "lifecycle": {
            "current_state": current_state,
            "previous_state": None,
            "transition_reason": "compatibility_projection_from_legacy_runtime_witness",
            "transitioned_at": created_at,
            "review_ref": None,
            "expiry_at": None,
        },
        "policy": {
            "mode": str(policy.get("mode") or policy_mode or "audit_only"),
            "may_influence_response": bool(policy.get("may_influence_response", False)),
            "may_write_memory": bool(policy.get("may_write_memory", False)),
            "may_promote_witness": bool(policy.get("may_promote_witness", False)),
            "may_trigger_mutation": bool(policy.get("may_trigger_mutation", False)),
        },
    }
