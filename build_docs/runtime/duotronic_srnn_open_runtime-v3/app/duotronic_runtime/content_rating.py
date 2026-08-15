from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx

from .crypto_primitives import canonical_json, shake256_ref


RATING_ORDER = {"safe": 0, "suggestive": 1, "adult": 2, "graphic": 3, "unknown": 4}
POLICIES: dict[str, dict[str, Any]] = {
    "public_u18": {"allow": ["safe"], "unknown": "block", "description": "Conservative public/anonymous profile."},
    "registered_default": {"allow": ["safe", "suggestive"], "unknown": "warn", "description": "Default registered-user profile."},
    "restricted": {"allow": ["safe", "suggestive", "adult", "graphic"], "unknown": "warn", "description": "Broader authenticated/admin profile; classification remains visible."},
    "observe_only": {"allow": ["safe", "suggestive", "adult", "graphic", "unknown"], "unknown": "allow", "description": "Record classification without filtering."},
}


def _endpoints() -> list[str]:
    raw = os.environ.get("XAVI_CONTENT_RATING_URLS") or os.environ.get("XAVI_CONTENT_RATING_URL") or os.environ.get("XAVI_NSFW_API_URL") or ""
    out: list[str] = []
    for part in raw.split(","):
        item = part.strip().rstrip("/")
        if item and item not in out:
            out.append(item)
    return out


def _score(value: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, min(float(value), 1.0))
    except Exception:
        return default


def _normalize_label(value: Any) -> str:
    text = str(value or "unknown").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "sfw": "safe", "general": "safe", "normal": "safe", "neutral": "safe",
        "sexy": "suggestive", "suggestive_content": "suggestive", "racy": "suggestive",
        "nsfw": "adult", "explicit": "adult", "porn": "adult", "pornographic": "adult", "sexual": "adult",
        "violence": "graphic", "gore": "graphic", "graphic_violence": "graphic",
    }
    text = aliases.get(text, text)
    return text if text in RATING_ORDER else "unknown"


def _normalize_observer(endpoint: str, payload: Any) -> dict[str, Any]:
    body = payload if isinstance(payload, dict) else {"raw": payload}
    nested = body.get("rating") if isinstance(body.get("rating"), dict) else body
    label = _normalize_label(nested.get("label") or nested.get("class") or nested.get("rating") or nested.get("category"))
    confidence = _score(nested.get("confidence", nested.get("score", nested.get("probability", 0.0))))
    categories = nested.get("categories") if isinstance(nested.get("categories"), dict) else {}
    # Common binary NSFW output fallback.
    nsfw = nested.get("nsfw")
    if label == "unknown" and isinstance(nsfw, (int, float)):
        p = _score(nsfw)
        label = "adult" if p >= 0.5 else "safe"
        confidence = max(p, 1.0 - p)
    elif label == "unknown" and isinstance(nsfw, bool):
        label = "adult" if nsfw else "safe"
        confidence = 1.0
    return {
        "observer": str(body.get("observer") or body.get("model") or endpoint),
        "endpoint": endpoint,
        "label": label,
        "confidence": confidence,
        "categories": categories,
        "raw_digest": shake256_ref(canonical_json(body)),
    }


def _aggregate(observers: list[dict[str, Any]]) -> dict[str, Any]:
    usable = [o for o in observers if o.get("label") in RATING_ORDER and o.get("label") != "unknown"]
    if not usable:
        return {"label": "unknown", "confidence": 0.0, "agreement": 0.0, "observer_count": len(observers), "usable_observer_count": 0}
    # Conservative ensemble: highest-severity credible observer wins; retain disagreement explicitly.
    usable.sort(key=lambda o: (RATING_ORDER.get(str(o.get("label")), 4), float(o.get("confidence") or 0.0)), reverse=True)
    chosen = usable[0]
    same = sum(1 for o in usable if o.get("label") == chosen.get("label"))
    return {
        "label": chosen["label"],
        "confidence": float(chosen.get("confidence") or 0.0),
        "agreement": same / max(1, len(usable)),
        "observer_count": len(observers),
        "usable_observer_count": len(usable),
    }


def _decision(label: str, policy: str) -> dict[str, Any]:
    profile = POLICIES.get(policy) or POLICIES["public_u18"]
    if label == "unknown":
        action = str(profile.get("unknown") or "block")
        allowed = action == "allow"
    else:
        allowed = label in set(profile.get("allow") or [])
        action = "allow" if allowed else "block"
    return {"profile": policy if policy in POLICIES else "public_u18", "allowed": allowed, "action": action, "description": profile.get("description")}


@dataclass
class ContentRatingRuntime:
    kernel: Any

    def capability(self) -> dict[str, Any]:
        endpoints = _endpoints()
        return {
            "schema_version": "xavi-content-rating-capability/v1",
            "configured": bool(endpoints),
            "observer_count": len(endpoints),
            "endpoint_count": len(endpoints),
            "policies": {k: {"allow": v["allow"], "unknown": v["unknown"]} for k, v in POLICIES.items()},
            "env": "XAVI_CONTENT_RATING_URLS|XAVI_CONTENT_RATING_URL|XAVI_NSFW_API_URL",
        }

    async def observe(
        self,
        *,
        text: str | None = None,
        url: str | None = None,
        image_url: str | None = None,
        media_ref: str | None = None,
        policy: str = "public_u18",
        context: dict[str, Any] | None = None,
        timeout_seconds: float = 8.0,
    ) -> dict[str, Any]:
        endpoints = _endpoints()
        request_body = {
            "schema_version": "xavi-content-rating-request/v1",
            "text": str(text or "")[:16000] or None,
            "url": str(url or "")[:4096] or None,
            "image_url": str(image_url or "")[:4096] or None,
            "media_ref": str(media_ref or "")[:4096] or None,
            "context": context if isinstance(context, dict) else {},
        }
        if not any(request_body.get(k) for k in ("text", "url", "image_url", "media_ref")):
            raise ValueError("content rating requires text, url, image_url, or media_ref")

        async def call(endpoint: str) -> dict[str, Any]:
            try:
                async with httpx.AsyncClient(timeout=max(1.0, min(float(timeout_seconds), 20.0))) as client:
                    response = await client.post(endpoint + "/v1/rate", json=request_body)
                    response.raise_for_status()
                    return {"ok": True, **_normalize_observer(endpoint, response.json())}
            except Exception as exc:
                return {"ok": False, "observer": endpoint, "endpoint": endpoint, "label": "unknown", "confidence": 0.0, "error": exc.__class__.__name__}

        observers = await asyncio.gather(*[call(e) for e in endpoints]) if endpoints else []
        aggregate = _aggregate(observers)
        decision = _decision(str(aggregate.get("label") or "unknown"), policy)
        observed_at_ms = int(time.time() * 1000)
        body = {
            "schema_version": "xavi-content-rating-observation/v1",
            "input_digest": shake256_ref(canonical_json(request_body)),
            "configured": bool(endpoints),
            "status": "rated" if aggregate.get("usable_observer_count") else "observer_unavailable",
            "aggregate": aggregate,
            "decision": decision,
            "observers": observers,
            "observed_at_ms": observed_at_ms,
            "authority": "content_rating_observation_not_truth",
        }
        witness = self.kernel.evidence.witness(
            "ContentRatingObservationWitness",
            body,
            force="observe",
            status=str(body["status"]),
        )
        return {**body, "witness": witness}
