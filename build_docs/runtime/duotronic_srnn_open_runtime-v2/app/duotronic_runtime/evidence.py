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
