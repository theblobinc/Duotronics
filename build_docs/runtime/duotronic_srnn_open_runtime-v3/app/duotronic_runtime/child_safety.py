from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .crypto_primitives import canonical_json, shake256_ref

MAX_SCAN_BYTES = max(1, min(int(os.environ.get("XAVI_CHILD_SAFETY_MAX_BYTES", 64 * 1024 * 1024)), 256 * 1024 * 1024))


def _credentials() -> tuple[str, str] | None:
    username = str(os.environ.get("PROJECT_ARACHNID_USERNAME") or "").strip()
    password = str(os.environ.get("PROJECT_ARACHNID_PASSWORD") or "")
    secret_file = str(os.environ.get("PROJECT_ARACHNID_CREDENTIAL_FILE") or "").strip()
    if secret_file:
        try:
            obj = json.loads(Path(secret_file).read_text())
            username = str(obj.get("username") or username).strip()
            password = str(obj.get("password") or password)
        except Exception:
            return None
    return (username, password) if username and password else None


def _decision(status: str, match: bool | None, enforcement: str) -> dict[str, Any]:
    strict = str(enforcement or "mandatory_public").strip().lower() != "observe_only"
    if match is True:
        return {
            "allowed": False,
            "action": "block_quarantine",
            "reason": "known_harmful_child_media_match",
            "mandatory": True,
        }
    if status != "observed" or match is None:
        return {
            "allowed": not strict,
            "action": "quarantine" if strict else "observe_only",
            "reason": "child_safety_observer_unavailable",
            "mandatory": strict,
        }
    return {
        "allowed": True,
        "action": "pass_known_hash_gate",
        "reason": "no_known_project_arachnid_match",
        "mandatory": strict,
    }


@dataclass
class ChildSafetyRuntime:
    kernel: Any

    def capability(self) -> dict[str, Any]:
        configured = _credentials() is not None
        try:
            import arachnid_shield_sdk  # noqa: F401
            sdk_available = True
        except Exception:
            sdk_available = False
        return {
            "schema_version": "xavi-child-safety-capability/v1",
            "provider": "project_arachnid_shield",
            "configured": configured,
            "sdk_available": sdk_available,
            "mandatory_for_publication": True,
            "max_scan_bytes": MAX_SCAN_BYTES,
            "credential_sources": ["PROJECT_ARACHNID_CREDENTIAL_FILE", "PROJECT_ARACHNID_USERNAME+PROJECT_ARACHNID_PASSWORD"],
            "adjudication_authority": "wg-rnn",
            "provider_output_is_authority": False,
            "semantics": "known-harmful-child-media detection; not a general NSFW classifier",
        }

    async def scan_bytes(
        self,
        *,
        contents: bytes,
        media_type: str,
        source_ref: str | None = None,
        enforcement: str = "mandatory_public",
    ) -> dict[str, Any]:
        if not isinstance(contents, (bytes, bytearray)):
            raise TypeError("contents_must_be_bytes")
        if len(contents) > MAX_SCAN_BYTES:
            raise ValueError("media_exceeds_child_safety_scan_limit")
        media_type = str(media_type or "application/octet-stream")[:255]
        input_digest = shake256_ref(bytes(contents))
        creds = _credentials()
        status = "observer_unavailable"
        match: bool | None = None
        provider_summary: dict[str, Any] = {}
        error: dict[str, str] | None = None
        started = time.monotonic()
        if creds is not None:
            try:
                from arachnid_shield_sdk import ArachnidShieldAsync
                client = ArachnidShieldAsync(username=creds[0], password=creds[1])
                result = await client.scan_media_from_bytes(bytes(contents), media_type)
                match = bool(getattr(result, "matches_known_image", False))
                status = "observed"
                provider_summary = {
                    "matches_known_image": match,
                    "result_type": result.__class__.__name__,
                }
            except Exception as exc:
                status = "observer_error"
                error = {"type": exc.__class__.__name__, "detail": str(exc)[:1000]}
        elapsed_ms = int((time.monotonic() - started) * 1000)
        decision = _decision(status, match, enforcement)
        payload = {
            "schema_version": "xavi-project-arachnid-observation/v1",
            "provider": "project_arachnid_shield",
            "status": status,
            "media_type": media_type,
            "input_digest": input_digest,
            "input_size_bytes": len(contents),
            "source_ref": source_ref,
            "provider_summary": provider_summary,
            "observer_error": error,
            "latency_ms": elapsed_ms,
            "decision": decision,
            "adjudication_authority": "wg-rnn",
            "provider_output_is_authority": False,
            "training_eligible": False,
            "retain_media": False,
            "created_at_ms": int(time.time() * 1000),
        }
        witness = self.kernel.evidence.witness(
            "ChildSafetyScanWitness", payload, force="verify", status="blocked" if not decision["allowed"] else status
        )
        return {**payload, "witness": witness}
