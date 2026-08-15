from __future__ import annotations

import asyncio
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any

from .crypto_primitives import canonical_json, shake256_ref


STANCE_VALUES = {"support", "contradict", "uncertain", "mixed"}


def _bounded_text(value: Any, limit: int = 12000) -> str:
    return str(value or "")[:limit]


def _parse_structured_response(text: str) -> dict[str, Any]:
    raw = str(text or "").strip()
    parsed: dict[str, Any] = {}
    candidates = [raw]
    m = re.search(r"\{.*\}", raw, flags=re.S)
    if m:
        candidates.insert(0, m.group(0))
    for candidate in candidates:
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                parsed = obj
                break
        except Exception:
            pass
    stance = str(parsed.get("stance") or "uncertain").strip().lower()
    if stance not in STANCE_VALUES:
        low = raw.lower()
        if any(tok in low for tok in ["contradict", "false", "incorrect", "not supported"]):
            stance = "contradict"
        elif any(tok in low for tok in ["support", "consistent with", "appears true", "confirmed"]):
            stance = "support"
        else:
            stance = "uncertain"
    try:
        confidence = max(0.0, min(float(parsed.get("confidence", 0.5)), 1.0))
    except Exception:
        confidence = 0.5
    observation = _bounded_text(parsed.get("observation") or parsed.get("answer") or raw)
    rationale = _bounded_text(parsed.get("rationale") or parsed.get("summary") or "", 4000)
    evidence = parsed.get("evidence") if isinstance(parsed.get("evidence"), list) else []
    return {
        "stance": stance,
        "confidence": confidence,
        "observation": observation,
        "rationale": rationale,
        "evidence": [str(x)[:2000] for x in evidence[:32]],
    }


def _observer_prompt(question: str, claim: dict[str, Any] | None, context: dict[str, Any] | None) -> str:
    payload = {
        "question": _bounded_text(question, 12000),
        "claim": claim if isinstance(claim, dict) else {},
        "context": context if isinstance(context, dict) else {},
    }
    return (
        "You are an independent evidence observer inside the Duotronics/WG-RNN system. "
        "You are NOT the authority and must not promote your own answer to truth. "
        "Evaluate the question/claim and return JSON with keys: stance (support|contradict|uncertain|mixed), "
        "confidence (0..1), observation, rationale, evidence (list). Be concise and distinguish facts from inference.\n"
        + canonical_json(payload)
    )


@dataclass
class ModelObservationRuntime:
    kernel: Any

    def capability(self) -> dict[str, Any]:
        models = self.kernel.model_provider.registry.list_models()
        items = []
        for record in models:
            if not record.get("enabled", True):
                continue
            items.append({
                "name": record.get("name"),
                "provider": record.get("provider"),
                "model": record.get("model"),
                "base_url": record.get("base_url"),
                "capabilities": list(record.get("capabilities") or []),
                "modalities": list(record.get("modalities") or []),
                "observer_kind": "model_observer",
                "observer_authority": False,
                "adjudication_authority": "wg-rnn",
            })
        return {
            "schema_version": "wg-rnn-model-observer-capability/v1",
            "configured": bool(items),
            "observer_count": len(items),
            "items": items,
            "adjudication_authority": "wg-rnn",
            "observer_outputs_are_truth": False,
        }

    async def observe_one(
        self,
        *,
        question: str,
        model_name: str | None = None,
        claim: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        independence_group: str | None = None,
    ) -> dict[str, Any]:
        started = time.monotonic()
        prompt = _observer_prompt(question, claim, context)
        try:
            timeout_seconds = max(3.0, min(float(os.environ.get("XAVI_MODEL_OBSERVER_TIMEOUT_SECONDS", "25")), 60.0))
            result = await asyncio.wait_for(
                self.kernel.model_provider.complete(prompt=prompt, model_name=model_name),
                timeout=timeout_seconds,
            )
            provider_error = None
        except Exception as exc:
            result = {
                "model": self.kernel.model_provider.registry.get(model_name),
                "response_text": "",
                "provider_status": "observer_error",
                "provider_metrics": {},
                "capabilities_observed": [],
            }
            provider_error = {"type": exc.__class__.__name__, "detail": str(exc)[:1000]}
        elapsed_ms = int((time.monotonic() - started) * 1000)
        model = result.get("model") if isinstance(result.get("model"), dict) else {}
        provider = str(model.get("provider") or result.get("provider_status") or "unknown")
        resolved_name = str(model.get("name") or model.get("model") or model_name or "unknown")
        parsed = _parse_structured_response(result.get("response_text") or "")
        if provider_error is not None:
            parsed = {"stance": "uncertain", "confidence": 0.0, "observation": "Model observer unavailable for this request.", "rationale": provider_error["detail"], "evidence": []}
        backend = str(model.get("base_url") or model.get("endpoint") or provider or "unknown").rstrip("/")
        group = str(independence_group or f"model-backend:{provider}:{backend}")
        body = {
            "schema_version": "wg-rnn-model-observation/v1",
            "observer_id": f"model:{provider}:{resolved_name}",
            "observer_kind": "model_observer",
            "independence_group": group,
            "provider": provider,
            "model": resolved_name,
            "backend": backend,
            "question_digest": shake256_ref(question),
            "claim_digest": shake256_ref(canonical_json(claim or {})),
            "prompt_digest": shake256_ref(prompt),
            "response_digest": shake256_ref(result.get("response_text") or ""),
            "stance": parsed["stance"],
            "confidence": parsed["confidence"],
            "observation": parsed["observation"],
            "rationale": parsed["rationale"],
            "evidence": parsed["evidence"],
            "latency_ms": elapsed_ms,
            "provider_status": result.get("provider_status"),
            "provider_metrics": result.get("provider_metrics") if isinstance(result.get("provider_metrics"), dict) else {},
            "observer_error": provider_error,
            "status": "observer_error" if provider_error is not None else "observed",
            "capabilities_observed": result.get("capabilities_observed") if isinstance(result.get("capabilities_observed"), list) else [],
            "adjudication_authority": "wg-rnn",
            "observer_output_is_truth": False,
            "authority": "candidate_evidence_observer_only",
            "created_at_ms": int(time.time() * 1000),
        }
        witness = self.kernel.evidence.witness(
            "ModelObserverWitness", body, force="propose", status=body["status"]
        )
        return {**body, "witness": witness}

    async def observe_parallel(
        self,
        *,
        question: str,
        model_names: list[str] | None = None,
        claim: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        max_observers: int = 4,
    ) -> dict[str, Any]:
        available = [r for r in self.kernel.model_provider.registry.list_models() if r.get("enabled", True)]
        requested = [str(x) for x in (model_names or []) if str(x).strip()]
        if not requested:
            seen: set[tuple[str, str, str]] = set()
            ranked = sorted(available, key=lambda r: (
                0 if str(r.get("name") or "").startswith("wgrnn-chat-") else 1,
                1 if str(r.get("provider") or "") == "echo" else 0,
                str(r.get("name") or ""),
            ))
            for r in ranked:
                if str(r.get("provider") or "") == "echo":
                    continue
                base = str(r.get("base_url") or "")
                if base.startswith("http://ollama:"):
                    continue
                key = (str(r.get("provider") or ""), base, str(r.get("model") or r.get("name") or ""))
                if key in seen:
                    continue
                seen.add(key)
                requested.append(str(r.get("name") or r.get("model") or ""))
                if len(requested) >= max(1, min(int(max_observers), 8)):
                    break
        requested = requested[: max(1, min(int(max_observers), 8))]
        results = await asyncio.gather(*[
            self.observe_one(question=question, model_name=name, claim=claim, context=context)
            for name in requested
        ], return_exceptions=True)
        observations: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        for name, result in zip(requested, results):
            if isinstance(result, Exception):
                errors.append({"model": name, "error": result.__class__.__name__, "detail": str(result)[:500]})
            else:
                observations.append(result)
        stance_counts: dict[str, int] = {}
        groups = set()
        for obs in observations:
            stance_counts[obs["stance"]] = stance_counts.get(obs["stance"], 0) + 1
            groups.add(obs["independence_group"])
        summary = {
            "schema_version": "wg-rnn-model-observer-batch/v1",
            "question_digest": shake256_ref(question),
            "requested_models": requested,
            "observation_count": len(observations),
            "error_count": len(errors),
            "independent_groups": len(groups),
            "stance_counts": stance_counts,
            "observations": observations,
            "errors": errors,
            "adjudication_authority": "wg-rnn",
            "promotion_performed": False,
            "authority": "candidate_evidence_bundle_only",
            "created_at_ms": int(time.time() * 1000),
        }
        witness_payload = {k: v for k, v in summary.items()}
        summary["witness"] = self.kernel.evidence.witness(
            "ModelObserverBatchWitness", witness_payload, force="propose", status="observed"
        )
        return summary
