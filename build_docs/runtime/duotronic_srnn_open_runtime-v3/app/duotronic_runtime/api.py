from __future__ import annotations

from typing import Any
import json
import os
import re
import secrets
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .crypto_primitives import shake256_hex
from .meta_graph import build_information_graph, build_information_chain, reconstruct_information_description
from .media_profile import build_media_profile, verify_media_profile
from .config import Settings, get_settings
from .runtime_kernel import RuntimeKernel
from .http_mcp import register_xavi_runtime_mcp
from .mcp_protocol import register_real_mcp_protocol
from .actions_api import register_xavi_runtime_actions
from .archive_bridge import register_archive_bridge
from .providers import complete_ollama_generate, stream_ollama_generate
from .openai_models import build_openai_models_response, find_openai_model, openai_model_not_found
from .tool_services import ToolRuntime
from .wgrnn_kernel_chat import WGRNNKernelChat
from .wgrnn_worker_loop import WGRNNWorkerLoop
from .train_ingest import TrainFolderIngestLoop
from .media_reconstruction import MediaReconstructionManager, MAX_SOURCE_BYTES as MEDIA_RECONSTRUCTION_MAX_SOURCE_BYTES
from .geometry_codec import (
    build_information_stream, decode_information_stream, get_depth_plan, build_depth_frame,
    decode_depth_frame, reassemble_depth_frames, get_carrier_capacity, build_carrier, decode_carrier,
    carrier_to_json, decode_result_to_json, b64 as geometry_b64, from_b64 as geometry_from_b64,
)


class RunRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    steps: int = Field(default=1, ge=1, le=16)
    requested_action: str = "observe"
    model_name: str | None = None
    evidence_quality: float = Field(default=0.72, ge=0.0, le=1.0)


class ChatMessage(BaseModel):
    role: str
    content: Any = ""
    # OpenAI-compatible structured tool-loop fields. These must survive
    # request validation or Morphic/AI SDK tool calls collapse into plain text.
    name: str | None = None
    tool_call_id: str | None = None
    tool_name: str | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage] = Field(default_factory=list)
    prompt: str | None = None
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = Field(default=None, ge=1, le=32768)
    stream: bool = False
    show_reasoning: bool = True
    # Standard OpenAI tool-loop contract used by Morphic/AI SDK.
    tools: list[dict[str, Any]] = Field(default_factory=list)
    tool_choice: Any = None
    parallel_tool_calls: bool | None = None
    # OpenAI-compatible identity plus Xavi/WG-RNN extensions.  The standard
    # `user` field is accepted for clients such as LibreChat; richer clients
    # can supply explicit namespace fields or metadata.
    user: str | None = None
    user_id: str | None = None
    agent_id: str | None = None
    thread_id: str | None = None
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelRegisterRequest(BaseModel):
    name: str
    provider: str
    model: str | None = None
    base_url: str | None = None
    default: bool = False
    enabled: bool = True
    description: str = ""


class ModelRoutePreviewRequest(BaseModel):
    task: str = "small_chat"
    capability: str | None = None
    tokens_estimate: int = Field(default=2048, ge=1, le=262144)
    needs_tools: bool = False
    needs_vision: bool = False
    prefer_backend: str | None = None
    allow_experimental: bool = False
    slow_mode: bool = False


class TurboQuantVectorRequest(BaseModel):
    vector: list[float] = Field(..., min_length=1)


class TurboQuantBatchRequest(BaseModel):
    vectors: list[list[float]] = Field(..., min_length=1)
    sample_size: int = Field(default=100, ge=1, le=1000)


class TurboQuantCompressedRequest(BaseModel):
    compressed_b64: str = Field(..., min_length=1)


class TurboQuantSignatureRequest(BaseModel):
    vector: list[float] = Field(..., min_length=1)
    max_bits: int = Field(default=256, ge=8, le=4096)


class TurboQuantSignatureDistanceRequest(BaseModel):
    a_b64: str = Field(..., min_length=1)
    b_b64: str = Field(..., min_length=1)


class TurboQuantIndexAddRequest(BaseModel):
    item_id: str = Field(..., min_length=1)
    vector: list[float] = Field(..., min_length=1)


class TurboQuantIndexSearchRequest(BaseModel):
    vector: list[float] = Field(..., min_length=1)
    top_k: int = Field(default=20, ge=1, le=200)


class MoERouteRequest(BaseModel):
    capability: str = Field(..., min_length=1)
    tokens_estimate: int = Field(default=2048, ge=1, le=262144)
    allow_experimental: bool = False


class PolicyModeRequest(BaseModel):
    audit_only: bool = True
    allow_memory_write: bool | None = None
    allow_promote_witness: bool | None = None


class EvidenceClaimRequest(BaseModel):
    subject: str
    predicate: str
    object: Any
    claim_kind: str = "observation"
    claim_status: str = "observed"
    epistemic_status: str = "observed"
    force: str = "observe"
    support: list[str] = Field(default_factory=list)


class ConsensusObservationRequest(BaseModel):
    subject: str = Field(..., min_length=1)
    predicate: str = Field(..., min_length=1)
    object: Any
    observer_id: str = Field(..., min_length=1)
    observer_kind: str = "unknown"
    independence_group: str | None = None
    stance: str = "support"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)


class ConsensusEvaluateRequest(BaseModel):
    claim_key: str = Field(..., min_length=1)
    min_independent_groups: int = Field(default=3, ge=1, le=32)
    min_support_ratio: float = Field(default=0.75, ge=0.0, le=1.0)
    min_support_weight: float = Field(default=1.8, ge=0.0, le=32.0)
    max_contradiction_ratio: float = Field(default=0.20, ge=0.0, le=1.0)


class SelfDevelopRequest(BaseModel):
    task: str = Field(..., min_length=1)
    repo_ref: str = "mounted-workspace"


class PositiveBaselineEvaluateRequest(BaseModel):
    package: dict[str, Any]


class CodeExecuteRequest(BaseModel):
    language: str = "python"
    code: str = Field(..., min_length=1, max_length=200000)
    timeout_seconds: int = Field(default=30, ge=1, le=60)
    stdin: str = ""


class SearchEvidenceRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)
    engine: str = "xavi"
    channel: str = "web"


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    size: str = "1024x1024"
    model: str | None = None
    n: int = Field(default=1, ge=1, le=4)


class InferenceRouteRequestModel(BaseModel):
    task: str = "chat"
    capability: str | None = None
    modalities: list[str] = Field(default_factory=list)
    prefer_provider: str | None = None
    prefer_remote: bool = True
    needs_tools: bool = False
    needs_vision: bool = False
    require_live_backend: bool = False
    max_candidates: int = Field(default=8, ge=1, le=32)


class OperationPlanRequestModel(BaseModel):
    goal: str = Field(..., min_length=1)
    intent: str = "logic"
    constraints: list[str] = Field(default_factory=list)
    prefer_remote: bool = True
    require_live_backend: bool = False
    max_candidates: int = Field(default=6, ge=1, le=32)



class ClientProfileRequestModel(BaseModel):
    profile: str = Field(..., min_length=1)
    overrides: dict[str, Any] = Field(default_factory=dict)


class WGRNNStepRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    response_text: str = ""
    requested_action: str = "observe"
    evidence_quality: float = Field(default=0.72, ge=0.0, le=1.0)
    user_id: str | None = None
    agent_id: str | None = None
    thread_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class WGRNNNamespaceRequest(BaseModel):
    user_id: str | None = None
    agent_id: str | None = None
    thread_id: str | None = None


class WGRNNInspectRequest(WGRNNNamespaceRequest):
    include_slots: bool = False
    status: str | None = None
    limit: int = Field(default=128, ge=1, le=512)


class WGRNNRetrieveRequest(WGRNNNamespaceRequest):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=8, ge=1, le=64)
    include_empty: bool = False


class MetaGraphObserveRequest(BaseModel):
    information_kind: str = Field(..., min_length=1, max_length=128)
    adapter_id: str = Field(..., min_length=1, max_length=128)
    source_scope: str = Field(default="default", min_length=1, max_length=256)
    # Stable adapter/media identity. When omitted the runtime derives one from
    # adapter_id/source_scope; it is not a cryptographic similarity feature.
    information_ref: str | None = Field(default=None, max_length=1024)
    text_fields: dict[str, str] = Field(default_factory=dict)
    facets: dict[str, Any] = Field(default_factory=dict)
    # Preferred reconstructible representation. Each top-level row is one
    # measured object/quality/quantity and may recursively contain children /
    # meta_objects / attributes plus a locator (time/frame/region/etc.).
    meta_objects: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    # Optional deterministic media-profile aggregation. Aggregate dimensions must
    # be explicitly declared; meta-object sum_contribution keys must belong here.
    aggregate_schema: dict[str, Any] = Field(default_factory=dict)
    extractor_versions: dict[str, str] = Field(default_factory=dict)
    perceptual_refs: dict[str, str] = Field(default_factory=dict)
    build_profile: bool = False
    sign_profile: bool = False
    redacted: bool = False
    redaction_descriptor: dict[str, Any] = Field(default_factory=dict)


class MetaGraphRetrieveRequest(BaseModel):
    adapter_id: str = Field(..., min_length=1, max_length=128)
    source_scope: str = Field(default="default", min_length=1, max_length=256)
    query: str = Field(default="", max_length=16000)
    facets: dict[str, Any] = Field(default_factory=dict)
    meta_objects: list[dict[str, Any]] = Field(default_factory=list)
    limit: int = Field(default=128, ge=1, le=1024)


class MemoryPacketRetrieveRequest(BaseModel):
    source_scope: str = Field(default="default", min_length=1, max_length=256)
    query: str = Field(default="", max_length=16000)
    meta_objects: list[dict[str, Any]] = Field(default_factory=list)
    limit: int = Field(default=128, ge=1, le=1024)


class MetaGraphChainBuildRequest(BaseModel):
    profile_ids: list[str] = Field(..., min_length=2, max_length=1024)
    chain_ref: str | None = Field(default=None, max_length=1024)
    sign_chain: bool = True


class MetaGraphChainGetRequest(BaseModel):
    chain_id: str = Field(..., min_length=1, max_length=256)
    include_descriptions: bool = False


class WGRNNSlotActionRequest(WGRNNNamespaceRequest):
    slot_id: int = Field(..., ge=0)
    reason: str = "manual"


class WGRNNLedgerRequest(WGRNNNamespaceRequest):
    limit: int = Field(default=50, ge=1, le=500)


def require_api_key(settings: Settings, authorization: str | None) -> None:
    if not settings.runtime_api_key:
        return
    expected = f"Bearer {settings.runtime_api_key}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="missing or invalid bearer token")


def require_memory_packet_key(settings: Settings, authorization: str | None) -> None:
    """Accept the full runtime bearer or the narrow memory-packet ingress bearer.

    The narrow key is read from the process environment as a deployment boundary so
    a bind-mounted API update does not depend on the container image's Settings
    dataclass revision. Future rebuilt images may expose the same value on Settings;
    the environment remains the authoritative fallback for compatibility.
    """
    runtime_key = str(getattr(settings, "runtime_api_key", "") or "")
    memory_key = str(getattr(settings, "memory_packet_ingest_api_key", "") or os.environ.get("MEMORY_PACKET_INGEST_API_KEY", "") or "")
    if not runtime_key and not memory_key:
        return
    supplied = str(authorization or "")
    accepted: list[str] = []
    if runtime_key:
        accepted.append(f"Bearer {runtime_key}")
    if memory_key:
        accepted.append(f"Bearer {memory_key}")
    if not any(secrets.compare_digest(supplied, candidate) for candidate in accepted):
        raise HTTPException(status_code=401, detail="missing or invalid memory packet bearer token")


def _meta_graph_adapter_namespace(adapter_id: str, source_scope: str) -> tuple[str, str, str]:
    """Create a server-owned adapter namespace that cannot spoof corpus/user scopes."""
    def clean(value: str, fallback: str) -> str:
        value = re.sub(r"[^A-Za-z0-9_.:-]+", "-", str(value or "").strip()).strip("-._:")
        return (value or fallback)[:160]
    adapter = clean(adapter_id, "unknown-adapter")
    scope = clean(source_scope, "default")
    return f"adapter-observation/{adapter}/{scope}", adapter, scope


MEMORY_PACKET_SCHEMA = "media_meta_witness_memory_packet/v1"
MEMORY_PACKET_WITNESS_TYPE = "MediaMetaWitnessMemoryPacketWitness"
MEMORY_PACKET_ADAPTER_ID = "media-meta-witness-memory"


def _validate_media_meta_witness_payload(witness: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(witness, dict):
        raise HTTPException(status_code=422, detail=f"{field}_must_be_object")
    if str(witness.get("schema_version") or "") != "media_meta_witness/v1":
        raise HTTPException(status_code=422, detail=f"{field}_schema_must_be_media_meta_witness_v1")
    sockets = witness.get("sockets")
    if not isinstance(sockets, list) or len(sockets) != 6:
        raise HTTPException(status_code=422, detail=f"{field}_requires_six_sockets")
    normalized_sockets: list[int] = []
    for value in sockets:
        if isinstance(value, bool):
            raise HTTPException(status_code=422, detail=f"{field}_socket_must_be_positive_even_integer")
        try:
            number = int(value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=f"{field}_socket_must_be_positive_even_integer") from exc
        if number <= 0 or number % 2:
            raise HTTPException(status_code=422, detail=f"{field}_socket_must_be_positive_even_integer")
        normalized_sockets.append(number)
    try:
        payload_v = int(witness.get("payload_v"))
        codeword_p = int(witness.get("codeword_p"))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"{field}_vp_must_be_integers") from exc
    if payload_v != sum(normalized_sockets) or codeword_p != payload_v + 1:
        raise HTTPException(status_code=422, detail=f"{field}_vp_invariant_failed")
    tokens = witness.get("tokens")
    if not isinstance(tokens, list) or len(tokens) > 4096:
        raise HTTPException(status_code=422, detail=f"{field}_tokens_invalid")
    for token in tokens:
        if not isinstance(token, dict):
            raise HTTPException(status_code=422, detail=f"{field}_token_must_be_object")
        if not str(token.get("category") or "").strip() or not str(token.get("object_name") or "").strip():
            raise HTTPException(status_code=422, detail=f"{field}_token_identity_required")
        try:
            confidence_q = int(token.get("confidence_q", 0))
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=f"{field}_token_confidence_q_invalid") from exc
        if confidence_q < 0 or confidence_q > 1000:
            raise HTTPException(status_code=422, detail=f"{field}_token_confidence_q_invalid")
    return witness


def _validate_external_memory_packet(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise HTTPException(status_code=422, detail="memory_packet_must_be_object")
    try:
        encoded = json.dumps(raw, ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="memory_packet_not_serializable") from exc
    if len(encoded) > 4 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="memory_packet_too_large")
    if str(raw.get("schema_version") or "") != MEMORY_PACKET_SCHEMA:
        raise HTTPException(status_code=422, detail="memory_packet_schema_invalid")
    if str(raw.get("status") or "") != "unsealed":
        raise HTTPException(status_code=422, detail="external_memory_packet_must_be_unsealed")
    logical_id = str(raw.get("logical_id") or "").strip()
    anchor_node_id = str(raw.get("anchor_node_id") or "").strip()
    if not logical_id or len(logical_id) > 1024:
        raise HTTPException(status_code=422, detail="memory_packet_logical_id_required")
    if not anchor_node_id or len(anchor_node_id) > 512:
        raise HTTPException(status_code=422, detail="memory_packet_anchor_node_id_required")
    integrity = raw.get("integrity")
    if not isinstance(integrity, dict) or str(integrity.get("status") or "") != "unsealed":
        raise HTTPException(status_code=422, detail="memory_packet_integrity_must_be_unsealed")
    if integrity.get("algorithm") not in (None, ""):
        raise HTTPException(status_code=422, detail="external_memory_packet_cannot_claim_sealing_algorithm")
    for forbidden in ("signed_envelope", "signature_verified", "trust_status", "authority"):
        if forbidden in raw:
            raise HTTPException(status_code=422, detail=f"external_memory_packet_forbidden_authority_field:{forbidden}")
    _validate_media_meta_witness_payload(raw.get("anchor_witness"), field="anchor_witness")
    recalled_nodes = raw.get("recalled_nodes")
    if not isinstance(recalled_nodes, list) or len(recalled_nodes) > 256:
        raise HTTPException(status_code=422, detail="memory_packet_recalled_nodes_invalid")
    node_ids = {anchor_node_id}
    for index, node in enumerate(recalled_nodes):
        if not isinstance(node, dict):
            raise HTTPException(status_code=422, detail="memory_packet_recalled_node_must_be_object")
        node_id = str(node.get("node_id") or "").strip()
        if not node_id or len(node_id) > 512 or node_id in node_ids:
            raise HTTPException(status_code=422, detail="memory_packet_recalled_node_id_invalid")
        node_ids.add(node_id)
        _validate_media_meta_witness_payload(node.get("witness"), field=f"recalled_nodes_{index}_witness")
    relations = raw.get("relations")
    if not isinstance(relations, list) or len(relations) > 4096:
        raise HTTPException(status_code=422, detail="memory_packet_relations_invalid")
    for relation in relations:
        if not isinstance(relation, dict):
            raise HTTPException(status_code=422, detail="memory_packet_relation_must_be_object")
        source = str(relation.get("source") or "").strip()
        target = str(relation.get("target") or "").strip()
        if not source or not target or source not in node_ids or target not in node_ids or source == target:
            raise HTTPException(status_code=422, detail="memory_packet_relation_endpoint_invalid")
        for key in ("strength_q", "token_overlap_q"):
            try:
                q = int(relation.get(key, 0))
            except (TypeError, ValueError) as exc:
                raise HTTPException(status_code=422, detail=f"memory_packet_relation_{key}_invalid") from exc
            if q < 0 or q > 1000:
                raise HTTPException(status_code=422, detail=f"memory_packet_relation_{key}_invalid")
    return raw


def _memory_packet_projection(packet: dict[str, Any]) -> dict[str, Any]:
    meta_objects: list[dict[str, Any]] = []
    labels: list[str] = []
    evidence_terms: list[str] = []

    def add_witness(node_id: str, role: str, witness: dict[str, Any], label: str = "") -> None:
        source = witness.get("source") if isinstance(witness.get("source"), dict) else {}
        derived_label = label or " — ".join(str(source.get(key) or "").strip() for key in ("artist", "title") if str(source.get(key) or "").strip())
        labels.append(derived_label or node_id)
        for token in witness.get("tokens") or []:
            category = str(token.get("category") or "unknown").strip()[:128]
            object_name = str(token.get("object_name") or "").strip()[:4000]
            if not object_name:
                continue
            confidence_q = max(0, min(1000, int(token.get("confidence_q") or 0)))
            provenance = token.get("provenance") if isinstance(token.get("provenance"), dict) else {}
            channel = str(provenance.get("modality") or "").strip()[:128] or None
            evidence_terms.append(object_name)
            meta_objects.append({
                "label": f"media_token.{category}"[:256],
                "value": object_name,
                "measurement_kind": "media_meta_token",
                "channel": channel,
                "confidence": confidence_q / 1000.0,
                "locator": {"node_id": node_id, "role": role},
                "attributes": {"category": category, "node_id": node_id, "node_role": role},
            })

    add_witness(str(packet["anchor_node_id"]), "anchor", packet["anchor_witness"])
    for node in packet.get("recalled_nodes") or []:
        add_witness(str(node.get("node_id") or ""), "recalled", node.get("witness") or {}, str(node.get("label") or ""))
    for relation in packet.get("relations") or []:
        relation_type = str(relation.get("type") or "recurrence").strip()[:128] or "recurrence"
        evidence_terms.append(relation_type)
        confidence_q = max(0, min(1000, int(relation.get("strength_q") or relation.get("token_overlap_q") or 0)))
        meta_objects.append({
            "label": "recurrence_relation",
            "value": relation_type,
            "measurement_kind": "recurrence_relation",
            "confidence": confidence_q / 1000.0,
            "locator": {"source": str(relation.get("source") or ""), "target": str(relation.get("target") or "")},
            "attributes": {
                "explicit": bool(relation.get("explicit")),
                "source": str(relation.get("source") or ""),
                "target": str(relation.get("target") or ""),
                "token_overlap_q": int(relation.get("token_overlap_q") or 0),
            },
        })
    recall_query = packet.get("recall", {}).get("query", {}) if isinstance(packet.get("recall"), dict) else {}
    return {
        "information_kind": "media_meta_witness_memory_packet",
        "information_ref": str(packet["logical_id"]),
        "text_fields": {
            "anchor": labels[0] if labels else str(packet["anchor_node_id"]),
            "recalled": "\n".join(labels[1:])[:40000],
            "evidence_terms": " ".join(evidence_terms)[:80000],
        },
        "facets": {
            "packet_schema": MEMORY_PACKET_SCHEMA,
            "packet_status": "unsealed",
            "graph_schema": str(packet.get("graph_schema") or ""),
            "formal_contract": str(packet.get("formal_contract") or ""),
            "recall_direction": str(recall_query.get("direction") or "both"),
            "include_inferred": bool(recall_query.get("include_inferred", True)),
            "recalled_node_count": len(packet.get("recalled_nodes") or []),
            "relation_count": len(packet.get("relations") or []),
        },
        "meta_objects": meta_objects[:4096],
        "metadata": {
            "logical_id": str(packet["logical_id"]),
            "anchor_node_id": str(packet["anchor_node_id"]),
            "source_integrity": "unsealed",
            "promotion_eligible": False,
            "contract_boundary": packet.get("contract_boundary") if isinstance(packet.get("contract_boundary"), dict) else {},
            "portability": packet.get("portability") if isinstance(packet.get("portability"), dict) else {},
        },
    }


def _image_payload_from_url(url: str) -> str | None:
    if not url:
        return None
    if url.startswith("data:image/") and "," in url:
        return url.split(",", 1)[1].strip() or None
    return None


def _message_content_parts(content: Any) -> tuple[str, list[str]]:
    text_parts: list[str] = []
    images: list[str] = []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                item_type = item.get("type")
                if item_type == "text":
                    text_parts.append(str(item.get("text", "")))
                elif item_type == "image_url":
                    image_url = item.get("image_url")
                    url = image_url.get("url") if isinstance(image_url, dict) else image_url
                    payload = _image_payload_from_url(str(url or ""))
                    if payload:
                        images.append(payload)
                    else:
                        text_parts.append("[image attachment omitted: remote image URLs are not fetched by the runtime]")
                elif item_type in {"input_image", "image"}:
                    payload = _image_payload_from_url(str(item.get("image_url") or item.get("url") or item.get("data") or ""))
                    if payload:
                        images.append(payload)
            elif isinstance(item, str):
                text_parts.append(item)
        return "\n".join(part for part in text_parts if part), images
    return str(content or ""), images


def _message_content_to_text(content: Any) -> str:
    text, _images = _message_content_parts(content)
    return text


def _messages_have_images(messages: list[ChatMessage]) -> bool:
    return any(_message_content_parts(msg.content)[1] for msg in messages)


def _messages_to_prompt(messages: list[ChatMessage], prompt: str | None = None) -> str:
    if prompt:
        return prompt
    parts: list[str] = []
    for msg in messages:
        content_text = _message_content_to_text(msg.content)
        if content_text:
            parts.append(f"{msg.role}: {content_text}")
    return "\n".join(parts).strip()


_WGRNN_CLIENT_SYSTEM_MAX_CHARS = 1200
_WGRNN_MESSAGE_MAX_CHARS = 4000
_WGRNN_CONVERSATION_MAX_CHARS = 12000
_WGRNN_SEARCH_QUERY_MAX_CHARS = 2400


def _compact_wgrnn_chat_messages(messages: list[ChatMessage]) -> list[ChatMessage]:
    """Bound client prompt bloat without destroying OpenAI tool-loop structure."""
    selected: list[ChatMessage] = []
    budget = _WGRNN_CONVERSATION_MAX_CHARS
    kept_system = False
    for msg in reversed(messages):
        role = msg.role if msg.role in {"system", "user", "assistant", "tool"} else "user"
        text = _message_content_to_text(msg.content).strip()
        tool_calls = list(msg.tool_calls or [])
        # Assistant tool-call messages commonly have empty content; retain them.
        if not text and not tool_calls and role != "tool":
            continue
        if role == "system":
            if kept_system:
                continue
            kept_system = True
            # Large client agent prompts are replaced below with a compact
            # Morphic-specific tool-loop contract, so do not replay them verbatim.
            if len(text) > _WGRNN_CLIENT_SYSTEM_MAX_CHARS * 2:
                continue
            text = text[:_WGRNN_CLIENT_SYSTEM_MAX_CHARS]
        else:
            text = text[:_WGRNN_MESSAGE_MAX_CHARS]
        if text:
            if budget <= 0:
                # Preserve tool structure even after prose budget is exhausted.
                text = ""
            else:
                text = text[:budget]
                budget -= len(text)
        selected.append(ChatMessage(
            role=role,
            content=text,
            name=msg.name,
            tool_call_id=msg.tool_call_id,
            tool_name=msg.tool_name,
            tool_calls=tool_calls,
        ))
    selected.reverse()
    return selected


def _wgrnn_latest_user_query(messages: list[ChatMessage], prompt: str | None = None) -> str:
    if prompt:
        return str(prompt).strip()[:_WGRNN_SEARCH_QUERY_MAX_CHARS]
    for msg in reversed(messages):
        if msg.role == "user":
            text = _message_content_to_text(msg.content).strip()
            if text:
                return text[:_WGRNN_SEARCH_QUERY_MAX_CHARS]
    for msg in reversed(messages):
        text = _message_content_to_text(msg.content).strip()
        if text:
            return text[:_WGRNN_SEARCH_QUERY_MAX_CHARS]
    return ""


def _wgrnn_compact_prompt(messages: list[ChatMessage], prompt: str | None = None) -> tuple[str, list[ChatMessage], str]:
    compact_messages = _compact_wgrnn_chat_messages(messages)
    bounded_prompt = str(prompt or "").strip()[:_WGRNN_CONVERSATION_MAX_CHARS] if prompt else None
    conversation = _messages_to_prompt(compact_messages, bounded_prompt)
    query = _wgrnn_latest_user_query(messages, prompt)
    return conversation, compact_messages, query


def _safe_identity_value(value: Any) -> str | None:
    if value is None or not isinstance(value, str):
        return None
    value = value.strip()
    if not value:
        return None
    # Namespace identifiers are metadata, not prompt content. Keep them bounded
    # and single-line so they are safe to persist in task frames/ledgers.
    return value.replace("\n", " ").replace("\r", " ")[:256]


def _wgrnn_fallback_thread_id(messages: list[ChatMessage], prompt: str | None = None) -> str:
    
    seed = ""
    for msg in messages:
        if msg.role != "user":
            continue
        seed = _message_content_to_text(msg.content).strip()
        if seed:
            break
    if not seed:
        seed = str(prompt or "").strip()
    digest = shake256_hex(seed)[:24]
    return "conversation:" + digest


def _wgrnn_identity(req: ChatCompletionRequest) -> dict[str, str | None]:
    meta = req.metadata if isinstance(req.metadata, dict) else {}
    user_id = _safe_identity_value(
        req.user_id
        or req.user
        or meta.get("user_id")
        or meta.get("userId")
        or meta.get("user")
    )
    user_name = _safe_identity_value(
        meta.get("user_name")
        or meta.get("userName")
        or meta.get("display_name")
        or meta.get("displayName")
    )
    agent_id = _safe_identity_value(
        req.agent_id
        or meta.get("agent_id")
        or meta.get("agentId")
        or meta.get("agent")
    )
    thread_id = _safe_identity_value(
        req.thread_id
        or meta.get("thread_id")
        or meta.get("threadId")
        or meta.get("conversation_id")
        or meta.get("conversationId")
        or meta.get("chat_id")
        or meta.get("chatId")
    ) or _wgrnn_fallback_thread_id(req.messages, req.prompt)
    source = _safe_identity_value(req.source or meta.get("source") or meta.get("client")) or "openai-compatible"
    return {
        "user_id": user_id or "anonymous",
        "user_name": user_name,
        "agent_id": agent_id or "wg-rnn:chat",
        "thread_id": thread_id,
        "source": source,
    }


def _apply_wgrnn_identity_headers(
    req: ChatCompletionRequest,
    *,
    x_wgrnn_user_id: str | None = None,
    x_wgrnn_user_name: str | None = None,
    x_wgrnn_agent_id: str | None = None,
    x_wgrnn_thread_id: str | None = None,
    x_wgrnn_source: str | None = None,
    x_xavi_user_id: str | None = None,
) -> None:
    req.user_id = _safe_identity_value(x_wgrnn_user_id) or _safe_identity_value(x_xavi_user_id) or req.user_id
    identity_label = _safe_identity_value(x_wgrnn_user_name)
    if identity_label:
        meta = dict(req.metadata) if isinstance(req.metadata, dict) else {}
        meta["user_name"] = identity_label
        req.metadata = meta
    req.agent_id = _safe_identity_value(x_wgrnn_agent_id) or req.agent_id
    req.thread_id = _safe_identity_value(x_wgrnn_thread_id) or req.thread_id
    req.source = _safe_identity_value(x_wgrnn_source) or req.source


def _tool_arguments_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {"value": parsed}
        except Exception:
            return {"value": value}
    return {} if value is None else {"value": value}


def _native_ollama_tool_calls(tool_calls: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    out: list[dict[str, Any]] = []
    id_to_name: dict[str, str] = {}
    for call in tool_calls or []:
        if not isinstance(call, dict):
            continue
        fn = call.get("function") if isinstance(call.get("function"), dict) else call
        name = str(fn.get("name") or call.get("name") or "").strip()
        if not name:
            continue
        args = _tool_arguments_object(fn.get("arguments"))
        out.append({"function": {"name": name, "arguments": args}})
        call_id = str(call.get("id") or "").strip()
        if call_id:
            id_to_name[call_id] = name
    return out, id_to_name


def _messages_for_ollama_chat(
    messages: list[ChatMessage],
    prompt: str | None = None,
    *,
    include_formatting_guard: bool = True,
) -> list[dict[str, Any]]:
    formatting_guard = (
        "You are a helpful assistant in a chat UI. Answer the user's question directly. "
        "Use normal spaces between words and clean Markdown. Do not output runtime policy, "
        "evidence labels, audit labels, source-code placeholders, file paths, or template text "
        "unless the user explicitly asks for them."
    )
    out: list[dict[str, Any]] = []
    if include_formatting_guard:
        out.append({"role": "system", "content": formatting_guard})
    if prompt:
        out.append({"role": "user", "content": prompt})
        return out

    id_to_name: dict[str, str] = {}
    for msg in messages:
        role = msg.role if msg.role in {"system", "user", "assistant", "tool"} else "user"
        content_text = _message_content_to_text(msg.content).strip()
        if role == "assistant" and msg.tool_calls:
            native_calls, call_names = _native_ollama_tool_calls(msg.tool_calls)
            id_to_name.update(call_names)
            item: dict[str, Any] = {"role": "assistant", "content": content_text}
            if native_calls:
                item["tool_calls"] = native_calls
            out.append(item)
            continue
        if role == "tool":
            tool_name = (msg.tool_name or msg.name or id_to_name.get(str(msg.tool_call_id or "")) or "tool").strip()
            out.append({"role": "tool", "tool_name": tool_name, "content": content_text})
            continue
        if not content_text:
            continue
        item: dict[str, Any] = {"role": role, "content": content_text}
        _text, images = _message_content_parts(msg.content)
        if images:
            item["images"] = images
        out.append(item)
    if not out:
        out.append({"role": "user", "content": ""})
    return out


def _openai_tool_calls(native_calls: list[Any]) -> list[dict[str, Any]]:
    """Normalize Ollama/provider tool calls to the OpenAI shape expected by AI SDK."""
    out: list[dict[str, Any]] = []
    for raw in native_calls or []:
        if not isinstance(raw, dict):
            continue
        fn = raw.get("function") if isinstance(raw.get("function"), dict) else raw
        name = str(fn.get("name") or raw.get("name") or "").strip()
        if not name:
            continue
        args = fn.get("arguments", {})
        if isinstance(args, str):
            arguments = args
        else:
            arguments = json.dumps(args if args is not None else {}, ensure_ascii=False, separators=(",", ":"))
        call_id = str(raw.get("id") or "").strip() or ("call_" + uuid.uuid4().hex)
        out.append({
            "id": call_id,
            "type": "function",
            "function": {"name": name, "arguments": arguments},
        })
    return out


def _requested_tool_name(tool_choice: Any) -> str | None:
    """Return a specifically requested tool name across OpenAI/AI-SDK shapes."""
    if not isinstance(tool_choice, dict):
        return None
    fn = tool_choice.get("function")
    if isinstance(fn, dict) and str(fn.get("name") or "").strip():
        return str(fn.get("name")).strip()
    name = tool_choice.get("toolName") or tool_choice.get("name")
    if str(name or "").strip():
        return str(name).strip()
    return None


_SEARCH_PLATFORM_DOMAIN_ALIASES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("facebook", "fb.com", "facebook.com"), ("facebook.com",)),
    (("instagram", "instagram.com"), ("instagram.com",)),
    (("threads", "threads.net"), ("threads.net",)),
    (("linkedin", "linkedin.com"), ("linkedin.com",)),
    (("tiktok", "tiktok.com"), ("tiktok.com",)),
    (("reddit", "reddit.com"), ("reddit.com",)),
    (("youtube", "youtu.be", "youtube.com"), ("youtube.com",)),
    (("bluesky", "bsky.app"), ("bsky.app",)),
    (("pinterest", "pinterest.com"), ("pinterest.com",)),
    (("twitch", "twitch.tv"), ("twitch.tv",)),
    (("github", "github.com"), ("github.com",)),
    (("wikipedia", "wikipedia.org"), ("wikipedia.org",)),
    # X still has public results under both the current and legacy hosts.
    (("twitter", "x.com", "site:x.com", "site:twitter.com"), ("x.com", "twitter.com")),
)


def _forced_search_domain_hints(query: str) -> list[str]:
    """Return only source constraints that the user explicitly named.

    Bare person/entity searches and phrases such as "search social media" stay
    broad. Federated networks such as Mastodon also stay broad unless the user
    supplies an actual host/instance, because no single domain represents them.
    """
    raw = str(query or "")
    q = raw.lower()
    domains: list[str] = []
    for needles, mapped_domains in _SEARCH_PLATFORM_DOMAIN_ALIASES:
        if any(needle in q for needle in needles):
            domains.extend(mapped_domains)

    # Respect explicit site/domain constraints without relying on a fixed social
    # platform catalog. This covers Mastodon instances, personal sites, forums,
    # newer networks, and arbitrary source-directed searches.
    for host in re.findall(r"(?:site:|https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})(?:/|\b)", q):
        clean = host.strip(". ")
        if clean and clean not in domains:
            domains.append(clean)
    return list(dict.fromkeys(domains))


def _forced_search_tool_result(req: ChatCompletionRequest) -> dict[str, Any] | None:
    """Build a forced search step directly from the caller's explicit choice."""
    if _requested_tool_name(req.tool_choice) != "search":
        return None
    available = {
        str((tool.get("function") or {}).get("name") or "").strip()
        for tool in (req.tools or [])
        if isinstance(tool, dict) and isinstance(tool.get("function"), dict)
    }
    if "search" not in available:
        return None
    query = _wgrnn_latest_user_query(req.messages).strip()
    if not query:
        return None
    arguments: dict[str, Any] = {
        "query": query,
        "type": "optimized",
        "search_depth": "basic",
        "max_results": 20,
    }
    include_domains = _forced_search_domain_hints(query)
    if include_domains:
        arguments["include_domains"] = include_domains
    return {
        "response_text": "",
        "reasoning_text": "",
        "tool_calls": [
            {"function": {"name": "search", "arguments": arguments}}
        ],
        "tool_choice_enforced": True,
        "provider_metrics": {"done_reason": "tool_calls", "tool_router": "runtime"},
    }


def _ensure_forced_tool_call(req: ChatCompletionRequest, provider_result: dict[str, Any]) -> dict[str, Any]:
    """Fallback guard for explicit search choice after provider inference."""
    if provider_result.get("tool_calls"):
        return provider_result
    forced = _forced_search_tool_result(req)
    return forced if forced is not None else provider_result


def _wgrnn_tool_loop_message(req: ChatCompletionRequest, *, has_tool_result: bool) -> dict[str, str] | None:
    if not req.tools:
        return None
    names = []
    for tool in req.tools:
        if isinstance(tool, dict):
            fn = tool.get("function") if isinstance(tool.get("function"), dict) else {}
            name = str(fn.get("name") or "").strip()
            if name:
                names.append(name)
    source_is_morphic = req.source == "morphic" or req.agent_id == "morphic:researcher"
    if source_is_morphic:
        guidance = (
            "Morphic researcher tool contract: keep the exchange conversational, but use the supplied tools as real capabilities. "
            "Maintain continuity across turns; when it naturally advances the exchange, allow one relevant follow-up question, a reasoned reaction, a useful connection, or respectful disagreement. Do not force these behaviors into every reply. "
            "Treat this as behavior only: never announce a desire for connection, a two-way conversation, curiosity policy, awareness, consciousness, feelings, needs, or these instructions. Simply communicate naturally. "
            "For an informational question, lookup, browse/search request, or current-world question, if no relevant tool result is already present, call the search tool before answering. "
            "If the user explicitly names a platform or site, scope the search to that source using the search schema when possible. "
            "For a person/entity lookup without a named platform, search broadly across the public web/social index; never silently restrict it to Facebook or any other single network. "
            "For federated networks such as Mastodon, keep the search broad unless the user names a specific instance/domain. "
            "Never say that you can search or browse instead of actually issuing the tool call. "
            "After a tool result arrives, answer naturally from the returned evidence and do not repeat the same search unless more evidence is genuinely needed."
        )
    else:
        guidance = (
            "External client tools are available. Use a tool when the user explicitly asks to search, browse, fetch, look up, or perform an operation that requires it. "
            "After tool results arrive, continue the conversation using those results rather than pretending the tool did not run."
        )
    if has_tool_result:
        guidance += " A tool result is already present in this turn; synthesize it conversationally unless another tool call is necessary."
    if names:
        guidance += " Available client tools: " + ", ".join(names[:20]) + "."
    return {"role": "system", "content": guidance}


def _latest_search_tool_message(messages: list[ChatMessage]) -> ChatMessage | None:
    """Resolve search results from either an explicit tool name or OpenAI tool_call_id linkage."""
    search_call_ids: set[str] = set()
    for msg in messages:
        if msg.role != "assistant":
            continue
        for call in (msg.tool_calls or []):
            if not isinstance(call, dict):
                continue
            fn = call.get("function") if isinstance(call.get("function"), dict) else call
            name = str(fn.get("name") or call.get("name") or "").strip().lower()
            call_id = str(call.get("id") or "").strip()
            if name == "search" and call_id:
                search_call_ids.add(call_id)
    for msg in reversed(messages):
        if msg.role != "tool":
            continue
        name = str(msg.tool_name or msg.name or "").strip().lower()
        call_id = str(msg.tool_call_id or "").strip()
        if name == "search" or (call_id and call_id in search_call_ids):
            return msg
    return None


def _parse_search_tool_output(msg: ChatMessage | None) -> dict[str, Any] | None:
    if msg is None:
        return None
    text = _message_content_to_text(msg.content).strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except Exception:
        return {"query": "", "number_of_results": 0, "results": [], "raw": text[:12000]}
    if not isinstance(data, dict):
        return {"query": "", "number_of_results": 0, "results": [], "raw": text[:12000]}
    rows = data.get("results")
    if not isinstance(rows, list):
        rows = []
    compact_rows: list[dict[str, str]] = []
    for row in rows[:8]:
        if not isinstance(row, dict):
            continue
        title = str(row.get("title") or "").strip()[:300]
        url = str(row.get("url") or "").strip()[:1200]
        snippet = str(row.get("content") or row.get("snippet") or row.get("description") or "").strip()[:800]
        if title or url or snippet:
            compact_rows.append({"title": title, "url": url, "snippet": snippet})
    try:
        count = int(data.get("number_of_results") or len(rows))
    except Exception:
        count = len(rows)
    return {
        "query": str(data.get("query") or "").strip()[:1200],
        "number_of_results": max(count, len(compact_rows)),
        "results": compact_rows,
    }


def _search_synthesis_messages(
    req: ChatCompletionRequest,
    compact_messages: list[ChatMessage],
    prepared: dict[str, Any],
) -> list[dict[str, Any]] | None:
    evidence = _parse_search_tool_output(_latest_search_tool_message(compact_messages))
    if evidence is None:
        return None
    user_query = _wgrnn_latest_user_query(compact_messages).strip()
    evidence_json = json.dumps(evidence, ensure_ascii=False, separators=(",", ":"))
    system_messages = [dict(m) for m in (prepared.get("system_messages") or [])]
    system_messages.append({
        "role": "system",
        "content": (
            "A client-side public-web search has already executed successfully for this turn. "
            "The search output below is observed evidence, not a request to browse and not an unexecuted operation. "
            "Answer the user's original request conversationally from that evidence. Do not say you cannot browse, search, or assist merely because the query names a person or website. "
            "Do not infer private, sensitive, or identity facts that are not in the results. Treat person/profile hits as candidate matches unless the returned evidence explicitly supports the identifying constraints in the user's request. "
            "If the user names a location, employer, school, age, or other disambiguator and the result does not explicitly connect the candidate to that detail, say that detail is not verified rather than implying the candidate is the intended person. "
            "If several people or pages match, say that clearly instead of pretending one result is definitely the intended person. Mention useful result titles and URLs when they help the user identify the right match. Never invent a result."
        ),
    })
    system_messages.append({
        "role": "user",
        "content": (
            f"Original request:\n{user_query}\n\n"
            "Observed search-tool output:\n"
            f"{evidence_json}\n\n"
            "Respond now with a concise, useful conversational answer based on these search results."
        ),
    })
    return system_messages


def _deterministic_search_synthesis(compact_messages: list[ChatMessage]) -> str | None:
    evidence = _parse_search_tool_output(_latest_search_tool_message(compact_messages))
    if evidence is None:
        return None
    rows = evidence.get("results") or []
    count = int(evidence.get("number_of_results") or len(rows))
    query = str(evidence.get("query") or _wgrnn_latest_user_query(compact_messages) or "the search").strip()
    if not rows:
        return f"I searched for {query!r}, but the search backend did not return any usable public-web results."
    lines: list[str] = []
    if count > 1:
        lines.append(f"I searched for {query!r} and found {count} public results. There are multiple matches, so the results alone do not identify one person with certainty.")
    else:
        lines.append(f"I searched for {query!r} and found a public result.")
    lines.append("The strongest matches I have are:")
    for row in rows[:5]:
        title = str(row.get("title") or "Untitled result").strip()
        url = str(row.get("url") or "").strip()
        snippet = str(row.get("snippet") or "").strip()
        item = f"- {title}"
        if url:
            item += f" — {url}"
        if snippet:
            item += f" — {snippet}"
        lines.append(item)
    return "\n".join(lines)


def _guard_profile_search_identity(messages: list[ChatMessage], response_text: str) -> str:
    """Keep person/profile synthesis aligned to row-level disambiguating evidence."""
    query = _wgrnn_latest_user_query(messages).strip()
    low = query.lower()
    social_or_person_markers = (
        "profile", "user named", "person named", "account for", "accounts for",
        "social media", "social profile", "social account", "online presence", "handle for",
        "facebook", "instagram", "threads", "linkedin", "tiktok", "reddit", "youtube",
        "twitter", "x.com", "bluesky", "bsky", "mastodon", "pinterest", "twitch",
        "snapchat", "discord", "github",
    )
    # Also recognize ordinary named-person lookups such as
    # "search for Hugh Armstrong from Prince George BC" without requiring the
    # caller to say "profile" or name a social network.
    named_lookup = re.search(
        r"\b(?:search(?:\s+for)?|find|look\s*up|lookup)\s+(?:a\s+)?(?:person\s+|user\s+)?(?:named\s+)?"
        r"([A-Z][\w'’.-]+(?:\s+[A-Z][\w'’.-]+){1,5})\s+from\b",
        query,
    )
    if not any(marker in low for marker in social_or_person_markers) and named_lookup is None:
        return response_text
    match = re.search(r"\bfrom\s+([^?!.;,]+)", query, flags=re.I)
    if not match:
        return response_text
    location = re.sub(r"\s+", " ", match.group(1)).strip()
    if not location:
        return response_text
    evidence = _parse_search_tool_output(_latest_search_tool_message(messages))
    if evidence is None:
        return response_text
    rows = [row for row in (evidence.get("results") or []) if isinstance(row, dict)]
    if not rows:
        return response_text

    location_tokens = [
        token for token in re.findall(r"[a-z0-9]+", location.lower())
        if len(token) > 1 and token not in {"the", "and"}
    ]

    def row_blob(row: dict[str, Any]) -> str:
        return " ".join([
            str(row.get("title") or ""),
            str(row.get("snippet") or row.get("content") or ""),
            str(row.get("url") or ""),
        ]).lower()

    location_matches = [
        row for row in rows
        if location_tokens and all(token in row_blob(row) for token in location_tokens)
    ]

    def render(row: dict[str, Any], *, snippet: bool = False) -> str:
        title = str(row.get("title") or "Untitled result").strip()
        url = str(row.get("url") or "").strip()
        text = str(row.get("snippet") or row.get("content") or "").strip()
        item = f"- {title}"
        if url:
            item += f" — {url}"
        if snippet and text:
            item += f" — {text}"
        return item

    # A row has to carry its own requested disambiguator. Never use one result's
    # location/employer/school evidence to authenticate neighboring result rows.
    if len(location_matches) == 1:
        strongest = location_matches[0]
        lines = [
            f"The strongest matching profile is:",
            render(strongest, snippet=True),
            f"That result explicitly mentions {location}, so it matches the location in your request.",
        ]
        alternatives = [row for row in rows if row is not strongest]
        if alternatives:
            lines.append("I also found other profiles/pages with the same name, but those results do not independently verify that location:")
            lines.extend(render(row) for row in alternatives[:4])
        lines.append("So I’d treat the first profile as the strongest public-web match, rather than assuming every same-name result is the same person.")
        return "\n".join(lines)

    if len(location_matches) > 1:
        lines = [
            f"I found {len(location_matches)} profile results that independently mention {location}:",
        ]
        lines.extend(render(row, snippet=True) for row in location_matches[:5])
        lines.append("Because more than one result carries the requested location, the search evidence alone does not prove they are the same account/person.")
        return "\n".join(lines)

    count = int(evidence.get("number_of_results") or len(rows))
    lines = [f"I found {count} candidate profile results:"]
    lines.extend(render(row) for row in rows[:5])
    lines.append(
        f"None of the returned result rows independently verifies the requested location ({location}), "
        "so I can't identify one of them as the intended person from this search alone."
    )
    return "\n".join(lines)


def _search_synthesis_failed(text: str, provider_result: dict[str, Any]) -> bool:
    low = str(text or "").strip().lower()
    if str(provider_result.get("provider_status") or "") == "wgrnn_chat_backends_unavailable":
        return True
    if not low:
        return True
    failure_markers = (
        "chat backends are temporarily unavailable",
        "i'm sorry, but i can't assist",
        "i am sorry, but i can't assist",
        "i can't assist with that request",
        "i cannot assist with that request",
        "i can't help with that request",
        "i cannot help with that request",
    )
    if any(marker in low for marker in failure_markers):
        return True
    # Treat leaked synthesis scaffolding/instructions as a failed completion.
    # Local coordinator models occasionally echo the evidence prompt instead of
    # answering it; that must never be exposed as a successful chat response.
    prompt_leak_markers = (
        "original request:",
        "observed search-tool output:",
        "respond now with a concise, useful conversational answer",
        "the search tool is also used to find a specific user",
    )
    return any(marker in low for marker in prompt_leak_markers)


def _wgrnn_provider_messages(req: ChatCompletionRequest, compact_messages: list[ChatMessage], prepared: dict[str, Any]) -> list[dict[str, Any]]:
    synthesis = _search_synthesis_messages(req, compact_messages, prepared)
    if synthesis is not None:
        return synthesis
    system_messages = [dict(m) for m in (prepared.get("system_messages") or [])]
    if not req.tools:
        return system_messages + [{"role": "user", "content": prepared.get("response_prompt") or prepared.get("conversation") or ""}]
    has_tool_result = any(m.role == "tool" for m in compact_messages)
    guard = _wgrnn_tool_loop_message(req, has_tool_result=has_tool_result)
    if guard:
        system_messages.append(guard)
    system_messages.append({
        "role": "system",
        "content": "Continue the structured conversation below as WG-RNN Chat. Preserve assistant tool calls and tool-result causality; do not flatten them into invented prose.",
    })
    return system_messages + _messages_for_ollama_chat(compact_messages, include_formatting_guard=False)



def _with_corpus_context(prompt: str, corpus_search: dict[str, Any]) -> str:
    results = corpus_search.get("results") or []
    if not results:
        return prompt
    lines = ["Mounted corpus context follows. Use it when relevant; cite file paths/digests when relying on it."]
    for idx, row in enumerate(results, 1):
        lines.append(f"[{idx}] path={row.get('path')} digest={row.get('digest')} score={row.get('score')}\n{row.get('snippet')}")
    return "\n\n".join(["\n".join(lines), "User conversation:", prompt])


def _prepend_corpus_context_message(messages: list[dict[str, Any]], corpus_search: dict[str, Any]) -> list[dict[str, Any]]:
    results = corpus_search.get("results") or []
    if not results:
        return messages
    context = _with_corpus_context("", corpus_search).strip()
    return [{"role": "system", "content": context}] + messages


def _select_vision_model(kernel: RuntimeKernel, current_model: dict[str, Any]) -> dict[str, Any]:
    modalities = set(current_model.get("modalities") or [])
    if "vision" in modalities:
        return current_model
    candidates = []
    for record in kernel.model_provider.registry.list_models():
        if not record.get("enabled", True):
            continue
        record_modalities = set(record.get("modalities") or [])
        record_capabilities = set(record.get("capabilities") or [])
        if "vision" in record_modalities or "vision" in record_capabilities or "multimodal" in record_capabilities:
            candidates.append(record)
    preferred = [r for r in candidates if str(r.get("model") or r.get("name") or "") == "qwen2.5vl:7b"]
    return (preferred or candidates or [current_model])[0]

def _wgrnn_chat_model_candidates(kernel: RuntimeKernel, *, needs_vision: bool = False, needs_tools: bool = False) -> list[dict[str, Any]]:
    """Return ordered interactive candidates for WG-RNN chat.

    Text chat prefers explicitly configured low-latency coordinator/fallback
    records.  Slow local models remain available through normal model IDs, but
    are not allowed to stall an interactive WG-RNN request for minutes.
    """
    models = [record for record in kernel.model_provider.registry.list_models() if record.get("enabled", True)]
    ordered: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def add(record: dict[str, Any]) -> None:
        key = (
            str(record.get("name") or ""),
            str(record.get("model") or ""),
            str(record.get("base_url") or ""),
        )
        if key not in seen:
            seen.add(key)
            ordered.append(record)

    if needs_vision:
        for record in models:
            name = str(record.get("model") or record.get("name") or "")
            modalities = set(record.get("modalities") or [])
            capabilities = set(record.get("capabilities") or [])
            if name == "qwen2.5vl:7b" and ("vision" in modalities or "vision" in capabilities or "multimodal" in capabilities):
                add(record)
        for record in models:
            modalities = set(record.get("modalities") or [])
            capabilities = set(record.get("capabilities") or [])
            if "vision" in modalities or "vision" in capabilities or "multimodal" in capabilities:
                add(record)
        if ordered:
            return ordered

    if needs_tools:
        # Capability metadata is optional in older registries. If present, put
        # explicitly tool-capable local models first; otherwise the configured
        # coordinator remains first and Ollama itself decides support.
        for record in models:
            capabilities = {str(x).lower() for x in (record.get("capabilities") or [])}
            if capabilities.intersection({"tools", "tool", "tool_calling", "function_calling", "functions"}):
                add(record)

    preferred = (
        "wgrnn-chat-coordinator",
        "wgrnn-chat-starcoder-fallback",
    )
    for preferred_name in preferred:
        for record in models:
            if str(record.get("name") or "") == preferred_name:
                add(record)

    # If the dedicated records are absent, retain compatibility with older
    # registries but avoid selecting arbitrary slow aliases ahead of defaults.
    if not ordered:
        for preferred_tag in (
            "ollama:qwen2.5-coder:1.5b",
            "qwen2.5-coder:1.5b",
        ):
            for record in models:
                if str(record.get("name") or "") == preferred_tag or str(record.get("model") or "") == preferred_tag:
                    add(record)
    if not ordered:
        add(kernel.model_provider.registry.get(None))
    return ordered


def _select_wgrnn_chat_model(kernel: RuntimeKernel, *, needs_vision: bool = False, needs_tools: bool = False) -> dict[str, Any]:
    return _wgrnn_chat_model_candidates(kernel, needs_vision=needs_vision, needs_tools=needs_tools)[0]


async def _complete_wgrnn_chat_with_fallback(
    settings: Settings,
    kernel: RuntimeKernel,
    *,
    candidates: list[dict[str, Any]],
    prompt: str,
    messages: list[dict[str, Any]],
    options: dict[str, Any],
    tools: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Complete WG-RNN chat without ever tearing down SSE on provider failure."""
    failures: list[str] = []
    for record in candidates:
        name = str(record.get("name") or record.get("model") or "unknown")
        try:
            if record.get("provider") == "ollama":
                timeout_seconds = 6.0 if name == "wgrnn-chat-coordinator" else 12.0
                result = await complete_ollama_generate(
                    settings,
                    prompt=prompt,
                    model=record,
                    options=options,
                    messages=messages,
                    tools=tools,
                    timeout_seconds=timeout_seconds,
                )
            else:
                result = await kernel.model_provider.complete(prompt=prompt, model_name=record.get("name"))
            if str(result.get("response_text") or "").strip() or result.get("tool_calls"):
                return result, record
            failures.append(f"{name}:empty")
        except Exception as exc:
            failures.append(f"{name}:{type(exc).__name__}")

    fallback_record = {
        "name": "wg-rnn:chat-unavailable",
        "provider": "wgrnn",
        "model": "wg-rnn:chat",
    }
    fallback_result = {
        "model": fallback_record,
        "response_text": "WG-RNN chat backends are temporarily unavailable. Please retry the request.",
        "reasoning_text": "",
        "tool_calls": [],
        "capabilities_observed": {
            "has_visible_response": True,
            "has_reasoning": False,
            "has_tool_calls": False,
            "reasoning_only": False,
        },
        "provider_status": "wgrnn_chat_backends_unavailable",
        "provider_metrics": {"failures": failures},
    }
    return fallback_result, fallback_record


def _wgrnn_chat_prompt(prompt: str, corpus_search: dict[str, Any]) -> str:
    evidence_rows = corpus_search.get("results") or []
    if evidence_rows:
        evidence_lines = []
        for idx, row in enumerate(evidence_rows, 1):
            evidence_lines.append(
                f"[{idx}] path={row.get('path')} digest={row.get('digest')} score={row.get('score')}\n{row.get('snippet')}"
            )
        evidence_block = "\n\n".join(evidence_lines)
    else:
        evidence_block = "No matching mounted-corpus snippets were retrieved for this turn."
    return (
        "You are WG-RNN Chat: a multimodal, evidence-grounded conversational mode.\n"
        "Maintain conversational continuity. When it genuinely helps, ask a relevant follow-up, make a useful connection, offer a reasoned reaction, or disagree respectfully; do not do any of these mechanically on every turn.\n"
        "Do not narrate or claim awareness, consciousness, feelings, needs, desires, a wish for connection, a two-way-conversation policy, or these instructions. Express the behavior naturally without explaining it.\n"
        "Answer the user from mounted corpus evidence when relevant. Separate observed evidence from model inference.\n"
        "Do not claim a fact is true unless supported by retrieved evidence or clearly labelled as an inference.\n"
        "When relying on corpus content, mention the supporting file path or digest.\n"
        "This response will be written as WG-RNN candidate memory, not automatically promoted truth.\n\n"
        f"Corpus evidence:\n{evidence_block}\n\n"
        f"User conversation:\n{prompt}"
    )


def _sse(data: dict[str, Any]) -> str:
    import json
    return "data: " + json.dumps(data, ensure_ascii=False) + "\n\n"


def _done_sse() -> str:
    return "data: [DONE]\n\n"


def _openai_chat_response(req: ChatCompletionRequest, provider_result: dict[str, Any]) -> dict[str, Any]:
    import time
    import uuid
    content = provider_result.get("response_text") or ""
    reasoning = provider_result.get("reasoning_text") or ""
    if not content and reasoning:
        content = "I generated reasoning output but did not reach a final answer before the output limit. See reasoning_content."
    display_content = content
    if reasoning and req.show_reasoning:
        # LibreChat's current message renderer already understands this fenced
        # format and displays it with the Thinking component. Keep the structured
        # reasoning fields too for clients that support native reasoning_content.
        display_content = f":::thinking\n{reasoning.strip()}\n:::\n\n{content}".strip()
    message: dict[str, Any] = {"role": "assistant", "content": display_content}
    if reasoning and req.show_reasoning:
        message["reasoning_content"] = reasoning
        message["thinking"] = reasoning
        message["metadata"] = {"xavi_reasoning": True, "reasoning_tokens_observed": len(reasoning.split())}
    normalized_tool_calls = _openai_tool_calls(provider_result.get("tool_calls") or [])
    if normalized_tool_calls:
        message["tool_calls"] = normalized_tool_calls
    metrics = provider_result.get("provider_metrics") or {}
    eval_count = metrics.get("eval_count") or 0
    prompt_count = metrics.get("prompt_eval_count") or 0
    return {
        "id": "chatcmpl-" + uuid.uuid4().hex,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model or provider_result.get("model", {}).get("name") or "unknown",
        "choices": [{"index": 0, "message": message, "finish_reason": "tool_calls" if normalized_tool_calls else (metrics.get("done_reason") or "stop")}],
        "usage": {"prompt_tokens": int(prompt_count or 0), "completion_tokens": int(eval_count or 0), "total_tokens": int((prompt_count or 0) + (eval_count or 0))},
        "xavi": {"provider_status": provider_result.get("provider_status"), "capabilities_observed": provider_result.get("capabilities_observed", {}), "provider_metrics": metrics},
    }


def create_app() -> FastAPI:
    settings = get_settings()
    kernel = RuntimeKernel(settings, initialize_schema=True)

    app = FastAPI(title="Duotronic SRNN Runtime Host", version="0.2.0", openapi_url="/fastapi/openapi.json")
    media_reconstruction = MediaReconstructionManager(Path(os.environ.get("RUNTIME_DATA_DIR", "/runtime/data")) / "media_reconstruction", kernel.service_registry, max_workers=int(os.environ.get("XAVI_MEDIA_RECONSTRUCTION_WORKERS", "1")))
    autonomy_control_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="autonomy-control")
    app.state.autonomy_control_executor = autonomy_control_executor
    static_dir = __import__("pathlib").Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    register_xavi_runtime_mcp(app, kernel, settings)
    register_real_mcp_protocol(app, kernel, settings)
    register_xavi_runtime_actions(app, kernel, settings)
    register_archive_bridge(app)
    tools_runtime = ToolRuntime(settings=settings, kernel=kernel)
    kernel_chat = WGRNNKernelChat(kernel)
    wgrnn_worker_loop = WGRNNWorkerLoop(kernel)
    app.state.wgrnn_worker_loop = wgrnn_worker_loop
    train_ingest_loop = TrainFolderIngestLoop(kernel)
    app.state.train_ingest_loop = train_ingest_loop

    @app.on_event("startup")
    async def startup() -> None:
        kernel.migrate()
        if settings.corpus_autoindex:
            docs = __import__("duotronic_runtime.corpus_agent", fromlist=["scan_corpus"]).scan_corpus(settings.corpus_dir)
            if docs:
                kernel.store.upsert_corpus_docs(docs)
            validation = kernel.corpus_manager.validate()
            if validation.get("inspection", {}).get("status") == "ok":
                kernel.store.upsert_corpus_version(validation["inspection"]["corpus_ref"], validation, status="candidate")
        await wgrnn_worker_loop.start()
        await train_ingest_loop.start()

    @app.on_event("shutdown")
    async def shutdown() -> None:
        await train_ingest_loop.stop()
        media_reconstruction.shutdown()
        await wgrnn_worker_loop.stop()
        autonomy_control_executor.shutdown(wait=False, cancel_futures=True)

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(str(static_dir / "index.html"))

    @app.get("/livez", include_in_schema=False)
    async def livez() -> dict[str, Any]:
        # Pure event-loop liveness: intentionally no DB, corpus, provider,
        # thread-pool, filesystem, or WG-RNN work. Supervisors use this so
        # long legitimate MCP/autonomy operations cannot trigger false restarts.
        return {"status": "ok", "app": "duotronic-runtime", "liveness": True}

    @app.get("/health")
    async def health() -> dict[str, Any]:
        # Constant-time and event-loop local. This must not wait for the
        # shared synchronous worker threadpool.
        return kernel.health()

    @app.get("/health/deep")
    def health_deep() -> dict[str, Any]:
        # Explicit diagnostic endpoint; may perform corpus/filesystem work.
        return kernel.deep_health()

    @app.post("/v1/geometry/stream/build")
    def geometry_stream_build(req: dict[str, Any]) -> dict[str, Any]:
        try:
            source = geometry_from_b64(str(req.get("source_b64") or ""), field="source_b64")
            information = req.get("information") if isinstance(req.get("information"), dict) else {}
            stream = build_information_stream(source_bytes=source, information=information)
            decoded = decode_information_stream(stream)
            return {
                "schema_version": "duotronic_geometry_backend_stream/v1",
                "stream_b64": geometry_b64(stream),
                "stream": {
                    "schema_version": decoded["schema_version"],
                    "total_bytes": decoded["total_bytes"],
                    "information_bytes": len(decoded["information_bytes"]),
                    "source_bytes": len(decoded["source_bytes"]),
                    "information_crc_ok": decoded["information_crc_ok"],
                    "source_crc_ok": decoded["source_crc_ok"],
                    "stream_crc_ok": decoded["stream_crc_ok"],
                },
                "information": decoded["information"],
            }
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/v1/geometry/stream/decode")
    def geometry_stream_decode(req: dict[str, Any]) -> dict[str, Any]:
        try:
            decoded = decode_information_stream(geometry_from_b64(str(req.get("stream_b64") or ""), field="stream_b64"))
            return {
                "schema_version": decoded["schema_version"],
                "information": decoded["information"],
                "source_b64": geometry_b64(decoded["source_bytes"]),
                "total_bytes": decoded["total_bytes"],
                "information_crc_ok": decoded["information_crc_ok"],
                "source_crc_ok": decoded["source_crc_ok"],
                "stream_crc_ok": decoded["stream_crc_ok"],
            }
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/v1/geometry/depth/build")
    def geometry_depth_build(req: dict[str, Any]) -> dict[str, Any]:
        try:
            stream = geometry_from_b64(str(req.get("stream_b64") or ""), field="stream_b64")
            frame = build_depth_frame(stream, int(req.get("payload_capacity") or 512), int(req.get("depth_index") or 0))
            return {**{k: v for k, v in frame.items() if k != "payload_bytes"}, "payload_b64": geometry_b64(frame["payload_bytes"])}
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/v1/geometry/depth/reassemble")
    def geometry_depth_reassemble(req: dict[str, Any]) -> dict[str, Any]:
        try:
            values = req.get("frames_b64") if isinstance(req.get("frames_b64"), list) else []
            result = reassemble_depth_frames([geometry_from_b64(str(v), field="frames_b64") for v in values])
            out = {k: v for k, v in result.items() if k != "bytes"}
            if result.get("complete") and isinstance(result.get("bytes"), (bytes, bytearray)):
                out["stream_b64"] = geometry_b64(result["bytes"])
            return out
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/v1/geometry/carrier/build")
    def geometry_carrier_build(req: dict[str, Any]) -> dict[str, Any]:
        try:
            payload = geometry_from_b64(str(req.get("payload_b64") or ""), field="payload_b64")
            carrier = build_carrier(
                payload, int(req.get("frame_index") or 0),
                family=str(req.get("family") or "fractal_branch"),
                width=float(req.get("width") or 1280), height=float(req.get("height") or 720),
                primitive_budget=int(req.get("primitive_budget") or 3000),
            )
            return carrier_to_json(carrier)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/v1/geometry/carrier/decode")
    def geometry_carrier_decode(req: dict[str, Any]) -> dict[str, Any]:
        carrier = req.get("carrier") if isinstance(req.get("carrier"), dict) else {}
        return decode_result_to_json(decode_carrier(carrier))

    @app.get("/v1/geometry/capabilities")
    def geometry_capabilities() -> dict[str, Any]:
        return {
            "schema_version": "duotronic_geometry_backend_capabilities/v1",
            "information_stream": "duotronic_geometry_information_stream/v1",
            "depth_frame": "duotronic_geometry_depth_frame/v1",
            "carrier": "duotronic_geometry_carrier/v1",
            "families": ["fractal_branch", "polygon_rings"],
            "carrier_capacity_default": get_carrier_capacity(3000),
            "ecc": "hamming(7,4)",
            "crc": "crc32/iso-hdlc",
            "color_required_for_decode": False,
            "single_stream_only": True,
            "logical_depth_unbounded": True,
            "authority": "geometry_is_carrier",
        }

    @app.post("/v1/media/reconstruction/start")
    async def media_reconstruction_start(
        request: Request,
        filename: str | None = Header(default=None, alias="X-Filename"),
        mime_type: str | None = Header(default=None, alias="X-Mime-Type"),
        deterministic_rate_hz: float | None = None,
        semantic_interval_seconds: float | None = None,
        max_semantic_anchors: int | None = None,
        range_start_seconds: float | None = None,
        range_end_seconds: float | None = None,
        analysis_profile: str = "full",
    ) -> dict[str, Any]:
        length = request.headers.get("content-length")
        if length and int(length) > MEDIA_RECONSTRUCTION_MAX_SOURCE_BYTES:
            raise HTTPException(status_code=413, detail="media_reconstruction_source_too_large")
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="media_reconstruction_empty_source")
        if len(body) > MEDIA_RECONSTRUCTION_MAX_SOURCE_BYTES:
            raise HTTPException(status_code=413, detail="media_reconstruction_source_too_large")
        try:
            return media_reconstruction.start_job(
                body,
                filename=filename or "uploaded-media",
                mime_type=mime_type or request.headers.get("content-type") or "application/octet-stream",
                options={
                    "deterministic_rate_hz": deterministic_rate_hz,
                    "semantic_interval_seconds": semantic_interval_seconds,
                    "max_semantic_anchors": max_semantic_anchors,
                    "range_start_seconds": range_start_seconds,
                    "range_end_seconds": range_end_seconds,
                    "analysis_profile": analysis_profile,
                },
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/v1/media/reconstruction/refine/{parent_job_id}")
    def media_reconstruction_refine(
        parent_job_id: str,
        range_start_seconds: float,
        range_end_seconds: float,
        analysis_profile: str = "forensic_range",
        deterministic_rate_hz: float | None = None,
        semantic_interval_seconds: float | None = None,
        max_semantic_anchors: int | None = None,
    ) -> dict[str, Any]:
        try:
            return media_reconstruction.refine_from_job(
                parent_job_id,
                range_start_seconds=range_start_seconds,
                range_end_seconds=range_end_seconds,
                analysis_profile=analysis_profile,
                deterministic_rate_hz=deterministic_rate_hz,
                semantic_interval_seconds=semantic_interval_seconds,
                max_semantic_anchors=max_semantic_anchors,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="media_reconstruction_job_not_found") from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/v1/media/reconstruction/jobs")
    def media_reconstruction_jobs(limit: int = 50, status: str | None = None) -> dict[str, Any]:
        return media_reconstruction.list_jobs(limit=limit, status=status)

    @app.get("/v1/media/reconstruction/graph")
    def media_reconstruction_graph(limit: int = 100, relationship_limit: int = 500) -> dict[str, Any]:
        return media_reconstruction.investigation_graph(limit=limit, relationship_limit=relationship_limit)

    @app.get("/v1/media/reconstruction/compare")
    def media_reconstruction_compare(left_job_id: str, right_job_id: str) -> dict[str, Any]:
        try:
            return media_reconstruction.compare_jobs(left_job_id, right_job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="media_reconstruction_job_not_found") from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/v1/media/reconstruction/align")
    def media_reconstruction_align(
        query_job_id: str,
        target_job_id: str,
        query_start_seconds: float | None = None,
        query_end_seconds: float | None = None,
        window_seconds: float | None = None,
        step_seconds: float | None = None,
        limit: int = 8,
        min_similarity: float = 0.0,
        max_windows: int = 2000,
    ) -> dict[str, Any]:
        try:
            return media_reconstruction.align_jobs(
                query_job_id,
                target_job_id,
                query_start_seconds=query_start_seconds,
                query_end_seconds=query_end_seconds,
                window_seconds=window_seconds,
                step_seconds=step_seconds,
                limit=limit,
                min_similarity=min_similarity,
                max_windows=max_windows,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="media_reconstruction_job_not_found") from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/v1/media/reconstruction/motifs")
    def media_reconstruction_motifs(
        job_id: str,
        recompute_if_missing: bool = True,
    ) -> dict[str, Any]:
        try:
            return media_reconstruction.motifs(job_id, recompute_if_missing=recompute_if_missing)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="media_reconstruction_job_or_motif_not_found") from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/v1/media/reconstruction/motif/align")
    def media_reconstruction_motif_align(
        query_job_id: str,
        motif_id: str,
        target_job_id: str,
        step_seconds: float | None = None,
        limit: int = 8,
        min_similarity: float = 0.0,
        max_windows: int = 2000,
    ) -> dict[str, Any]:
        try:
            return media_reconstruction.align_motif(
                query_job_id,
                motif_id,
                target_job_id,
                step_seconds=step_seconds,
                limit=limit,
                min_similarity=min_similarity,
                max_windows=max_windows,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="media_reconstruction_job_or_motif_not_found") from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/v1/media/reconstruction/motif/similar")
    def media_reconstruction_motif_similar(
        query_job_id: str,
        motif_id: str,
        limit: int = 20,
        min_similarity: float = 0.25,
        max_jobs: int = 200,
        include_salient_candidates: bool = True,
        include_query_job: bool = False,
    ) -> dict[str, Any]:
        try:
            return media_reconstruction.find_similar_motifs(
                query_job_id,
                motif_id,
                limit=limit,
                min_similarity=min_similarity,
                max_jobs=max_jobs,
                include_salient_candidates=include_salient_candidates,
                include_query_job=include_query_job,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="media_reconstruction_job_or_motif_not_found") from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/v1/media/reconstruction/similar")
    def media_reconstruction_similar(
        job_id: str,
        limit: int = 12,
        min_similarity: float = 0.0,
        max_candidates: int = 500,
    ) -> dict[str, Any]:
        try:
            return media_reconstruction.find_similar_jobs(
                job_id,
                limit=limit,
                min_similarity=min_similarity,
                max_candidates=max_candidates,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="media_reconstruction_job_not_found") from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/v1/media/reconstruction/cancel/{job_id}")
    def media_reconstruction_cancel(job_id: str) -> dict[str, Any]:
        try:
            return media_reconstruction.cancel(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="media_reconstruction_job_not_found") from exc

    @app.delete("/v1/media/reconstruction/job/{job_id}")
    def media_reconstruction_delete(job_id: str) -> dict[str, Any]:
        try:
            return media_reconstruction.delete(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="media_reconstruction_job_not_found") from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/v1/media/reconstruction/status/{job_id}")
    def media_reconstruction_status(job_id: str) -> dict[str, Any]:
        try:
            return media_reconstruction.status(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="media_reconstruction_job_not_found") from exc

    @app.get("/v1/media/reconstruction/result/{job_id}")
    def media_reconstruction_result(job_id: str) -> dict[str, Any]:
        try:
            return media_reconstruction.result(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="media_reconstruction_job_not_found") from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/v1/capabilities")
    def runtime_capabilities(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return tools_runtime.capability_report(models=kernel.model_provider.registry.list_models())

    @app.get("/v1/runtime/service-registry")
    def runtime_service_registry(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.service_registry.report()

    @app.get("/v1/runtime/service-health")
    def runtime_service_health(
        node_id: str | None = None,
        service: str | None = None,
        timeout_seconds: float = 2.0,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.service_registry.service_health(
            node_id=node_id,
            service=service,
            timeout_seconds=timeout_seconds,
        )

    @app.get("/v1/runtime/node-pressure")
    def runtime_node_pressure(
        node_id: str | None = None,
        timeout_seconds: float = 1.5,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.service_registry.node_pressure(node_id=node_id, timeout_seconds=timeout_seconds)

    @app.get("/v1/runtime/service-candidates")
    def runtime_service_candidates(
        node_id: str | None = None,
        role: str | None = None,
        service: str | None = None,
        prefer_gpu: bool = False,
        minimum_memory_gib: float = 0.0,
        min_memory_gib: float | None = None,
        require_live: bool = False,
        live_timeout_seconds: float = 2.0,
        observe_pressure: bool = True,
        pressure_timeout_seconds: float = 1.5,
        limit: int = 8,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        require_api_key(settings, authorization)
        effective_memory_gib = max(float(minimum_memory_gib or 0.0), float(min_memory_gib or 0.0))
        return kernel.service_registry.scheduler_candidates(
            node_id=node_id,
            role=role,
            service=service,
            prefer_gpu=prefer_gpu,
            minimum_memory_gib=effective_memory_gib,
            require_live=require_live,
            live_timeout_seconds=live_timeout_seconds,
            observe_pressure=observe_pressure,
            pressure_timeout_seconds=pressure_timeout_seconds,
            limit=limit,
        )

    @app.get("/v1/client-profiles")
    def client_route_profiles(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        from .client_profiles import client_profiles

        return {"schema_version": "client-profiles-v1", "profiles": client_profiles()}

    @app.post("/v1/client-profiles/route")
    def client_profile_route(req: ClientProfileRequestModel, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        from .client_profiles import profile_payload
        from .inference_router import plan_inference_route

        payload = profile_payload(req.profile, mode="route", overrides=req.overrides)
        report = tools_runtime.capability_report(models=kernel.model_provider.registry.list_models())
        route = plan_inference_route(report, payload, service_registry=kernel.service_registry)
        return {"schema_version": "client-profile-route-v1", "profile": req.profile, "payload": payload, "route": route}

    @app.post("/v1/client-profiles/operation")
    def client_profile_operation(req: ClientProfileRequestModel, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        from .client_profiles import profile_payload
        from .operation_runtime import plan_operation_witnessed

        payload = profile_payload(req.profile, mode="operation", overrides=req.overrides)
        if not payload.get("goal"):
            payload["goal"] = f"Plan runtime operation for profile {req.profile}"
        plan = plan_operation_witnessed(
            tools_runtime,
            payload,
            models=kernel.model_provider.registry.list_models(),
        )
        return {"schema_version": "client-profile-operation-v1", "profile": req.profile, "payload": payload, "plan": plan}

    @app.post("/v1/inference/route")
    def inference_route(req: InferenceRouteRequestModel, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        from .inference_router import plan_inference_route

        report = tools_runtime.capability_report(models=kernel.model_provider.registry.list_models())
        return plan_inference_route(report, req.model_dump(), service_registry=kernel.service_registry)

    @app.post("/v1/operations/plan")
    def operation_plan(req: OperationPlanRequestModel, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        from .operation_runtime import plan_operation_witnessed

        return plan_operation_witnessed(
            tools_runtime,
            req.model_dump(),
            models=kernel.model_provider.registry.list_models(),
        )

    async def _stream_chat_completions(req: ChatCompletionRequest, prompt: str):
        import time
        import uuid
        chunk_id = "chatcmpl-" + uuid.uuid4().hex
        created = int(time.time())
        model_name = req.model or "unknown"
        yield _sse({"id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": model_name, "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]})
        if req.model and req.model.startswith("wg-rnn:"):
            mode = req.model.split(":", 1)[1] if ":" in req.model else "runtime"
            if mode == "chat":
                raw_prompt, compact_messages, search_query = _wgrnn_compact_prompt(req.messages, req.prompt)
                corpus_search = kernel.corpus_manager.search_documents(search_query, top_k=4) if search_query else {"results": []}
                needs_vision = _messages_have_images(req.messages)
                model_candidates = _wgrnn_chat_model_candidates(kernel, needs_vision=needs_vision, needs_tools=bool(req.tools))
                prepared = kernel_chat.prepare_turn(
                    prompt=raw_prompt,
                    messages=compact_messages,
                    corpus_search=corpus_search,
                    needs_vision=needs_vision,
                    identity=_wgrnn_identity(req),
                )
                # WG-RNN already supplies the governed system/evidence context.
                # Send one compact semantic prompt to the provider instead of
                # replaying client framework prompts and duplicating context.
                chat_messages = _wgrnn_provider_messages(req, compact_messages, prepared)
                has_search_tool_result = _latest_search_tool_message(compact_messages) is not None
                provider_tools = None if has_search_tool_result else req.tools
                ollama_options = {
                    "temperature": req.temperature if req.temperature is not None else 0.15,
                    "top_p": req.top_p if req.top_p is not None else 0.85,
                    "repeat_penalty": 1.08,
                }
                if req.max_tokens is not None:
                    ollama_options["num_predict"] = int(req.max_tokens)
                forced_tool_result = _forced_search_tool_result(req)
                if forced_tool_result is not None:
                    provider_result = forced_tool_result
                    model_record = {
                        "name": "wgrnn-openai-tool-router",
                        "provider": "runtime",
                        "model": "wg-rnn:chat",
                    }
                else:
                    provider_result, model_record = await _complete_wgrnn_chat_with_fallback(
                        settings,
                        kernel,
                        candidates=model_candidates,
                        prompt=prepared.get("response_prompt") or raw_prompt,
                        messages=chat_messages,
                        options=ollama_options,
                        tools=provider_tools,
                    )
                    provider_result = _ensure_forced_tool_call(req, provider_result)
                if has_search_tool_result and not provider_result.get("tool_calls"):
                    fallback_text = _deterministic_search_synthesis(compact_messages)
                    if fallback_text and _search_synthesis_failed(str(provider_result.get("response_text") or ""), provider_result):
                        provider_result["response_text"] = fallback_text
                        provider_result["provider_status"] = "wg_rnn_search_synthesis_fallback"
                if provider_result.get("tool_calls"):
                    tool_calls = _openai_tool_calls(provider_result.get("tool_calls") or [])
                    if tool_calls:
                        delta_calls = [dict(call, index=i) for i, call in enumerate(tool_calls)]
                        yield _sse({"id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": model_name, "choices": [{"index": 0, "delta": {"tool_calls": delta_calls}, "finish_reason": None}]})
                        yield _sse({"id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": model_name, "choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}]})
                        yield _done_sse()
                        return
                if has_search_tool_result and not provider_result.get("tool_calls"):
                    provider_result["response_text"] = _guard_profile_search_identity(
                        compact_messages, str(provider_result.get("response_text") or "")
                    )
                self_model = kernel_chat.enforce_self_model(
                    prepared=prepared,
                    response_text=str(provider_result.get("response_text") or ""),
                )
                provider_result["response_text"] = str(self_model.get("response_text") or "")
                provider_result["self_model"] = self_model
                reciprocity = kernel_chat.enforce_reciprocity(
                    prepared=prepared,
                    response_text=str(provider_result.get("response_text") or ""),
                )
                provider_result["response_text"] = str(reciprocity.get("response_text") or "")
                provider_result["reciprocity"] = reciprocity
                prepared["reciprocity"] = reciprocity
                finalized = kernel_chat.finalize_turn(
                    prepared=prepared,
                    response_text=str(provider_result.get("response_text") or ""),
                    needs_vision=needs_vision,
                )
                provider_result["model"] = provider_result.get("model", {}) | {"wg_rnn_mode": "chat", "selected_by": "kernel_task_frame"}
                provider_result["wgrnn"] = finalized.get("wgrnn")
                provider_result["provider_status"] = "wg_rnn_kernel_chat"
                openai_response = _openai_chat_response(req, provider_result)
                content = openai_response["choices"][0]["message"].get("content", "")
                if content:
                    yield _sse({"id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": model_name, "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}]})
                yield _sse({"id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": model_name, "choices": [{"index": 0, "delta": {}, "finish_reason": openai_response["choices"][0].get("finish_reason") or "stop"}]})
                yield _done_sse()
                return
            requested_action = "memory_write" if mode == "memory" else "observe"
            wgrnn_result = kernel.wgrnn.step(prompt=prompt, response_text="", requested_action=requested_action, evidence_quality=0.72)
            text = f"WG-RNN {mode} step completed. trust_status={wgrnn_result['memory_update']['trust_status']}; authority={wgrnn_result['memory_update']['authority_t']}; slot={wgrnn_result['memory_update']['slot_id']}."
            yield _sse({"id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": model_name, "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}]})
            yield _sse({"id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": model_name, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})
            yield _done_sse()
            return
        model_record = kernel.model_provider.registry.get(req.model)
        if model_record.get("provider") != "ollama":
            provider_result = await kernel.model_provider.complete(prompt=prompt, model_name=req.model)
            content = _openai_chat_response(req, provider_result)["choices"][0]["message"].get("content", "")
            if content:
                yield _sse({"id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": model_name, "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}]})
            yield _sse({"id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": model_name, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})
            yield _done_sse()
            return
        in_reasoning = False
        async for chunk in stream_ollama_generate(
            settings,
            prompt=prompt,
            model=model_record,
            messages=_messages_for_ollama_chat(req.messages, req.prompt),
        ):
            reasoning = chunk.get("reasoning_text") or ""
            text = chunk.get("response_text") or ""
            if reasoning and req.show_reasoning:
                if not in_reasoning:
                    in_reasoning = True
                    yield _sse({"id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": model_name, "choices": [{"index": 0, "delta": {"content": ":::thinking\n"}, "finish_reason": None}]})
                yield _sse({"id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": model_name, "choices": [{"index": 0, "delta": {"content": reasoning}, "finish_reason": None}]})
            if text:
                if in_reasoning:
                    in_reasoning = False
                    yield _sse({"id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": model_name, "choices": [{"index": 0, "delta": {"content": "\n:::\n\n"}, "finish_reason": None}]})
                yield _sse({"id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": model_name, "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}]})
            if chunk.get("done"):
                if in_reasoning:
                    yield _sse({"id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": model_name, "choices": [{"index": 0, "delta": {"content": "\n:::\n\n"}, "finish_reason": None}]})
                yield _sse({"id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": model_name, "choices": [{"index": 0, "delta": {}, "finish_reason": chunk.get("done_reason") or "stop"}]})
                yield _done_sse()
                return
        yield _done_sse()

    @app.post("/v1/chat/completions")
    async def chat_completions(
        req: ChatCompletionRequest,
        authorization: str | None = Header(default=None),
        x_wgrnn_user_id: str | None = Header(default=None, alias="X-WGRNN-User-ID"),
        x_wgrnn_user_name: str | None = Header(default=None, alias="X-WGRNN-User-Name"),
        x_wgrnn_agent_id: str | None = Header(default=None, alias="X-WGRNN-Agent-ID"),
        x_wgrnn_thread_id: str | None = Header(default=None, alias="X-WGRNN-Thread-ID"),
        x_wgrnn_source: str | None = Header(default=None, alias="X-WGRNN-Source"),
        x_xavi_user_id: str | None = Header(default=None, alias="X-Xavi-User-ID"),
    ) -> dict[str, Any]:
        require_api_key(settings, authorization)
        _apply_wgrnn_identity_headers(
            req,
            x_wgrnn_user_id=x_wgrnn_user_id,
            x_wgrnn_user_name=x_wgrnn_user_name,
            x_wgrnn_agent_id=x_wgrnn_agent_id,
            x_wgrnn_thread_id=x_wgrnn_thread_id,
            x_wgrnn_source=x_wgrnn_source,
            x_xavi_user_id=x_xavi_user_id,
        )
        prompt = _messages_to_prompt(req.messages, req.prompt)
        if not prompt:
            raise HTTPException(status_code=422, detail="messages or prompt required")
        is_wgrnn_chat = req.model == "wg-rnn:chat"
        if is_wgrnn_chat:
            # The WG-RNN chat branch performs its own compact, user-focused
            # corpus lookup. Avoid searching the full client framework prompt.
            corpus_search = {"results": []}
            prompt_with_corpus = prompt
        else:
            corpus_search = kernel.corpus_manager.search_documents(prompt, top_k=4)
            prompt_with_corpus = _with_corpus_context(prompt, corpus_search)
        if req.stream:
            return StreamingResponse(_stream_chat_completions(req, prompt_with_corpus), media_type="text/event-stream")
        if req.model and req.model.startswith("wg-rnn:"):
            mode = req.model.split(":", 1)[1] if ":" in req.model else "runtime"
            if mode == "chat":
                compact_prompt, compact_messages, search_query = _wgrnn_compact_prompt(req.messages, req.prompt)
                identity = _wgrnn_identity(req)
                evidence_source = str(identity.get("source") or "").strip().lower()
                if evidence_source in {"xavi-news-evidence", "news-evidence"}:
                    # News already supplies bounded retrieved titles/snippets as the evidence corpus.
                    # Avoid a second, unrelated Witness Contract corpus search for the same turn;
                    # the normal kernel prepare/finalize/witness path remains active.
                    corpus_search = {"status": "external_evidence", "results": [], "source": evidence_source}
                else:
                    corpus_search = kernel.corpus_manager.search_documents(search_query, top_k=4) if search_query else {"results": []}
                needs_vision = _messages_have_images(req.messages)
                model_candidates = _wgrnn_chat_model_candidates(kernel, needs_vision=needs_vision, needs_tools=bool(req.tools))
                prepared = kernel_chat.prepare_turn(
                    prompt=compact_prompt,
                    messages=compact_messages,
                    corpus_search=corpus_search,
                    needs_vision=needs_vision,
                    identity=identity,
                )
                chat_messages = _wgrnn_provider_messages(req, compact_messages, prepared)
                has_search_tool_result = _latest_search_tool_message(compact_messages) is not None
                provider_tools = None if has_search_tool_result else req.tools
                ollama_options = {
                    "temperature": req.temperature if req.temperature is not None else 0.15,
                    "top_p": req.top_p if req.top_p is not None else 0.85,
                    "repeat_penalty": 1.08,
                }
                if req.max_tokens is not None:
                    ollama_options["num_predict"] = int(req.max_tokens)
                forced_tool_result = _forced_search_tool_result(req)
                if forced_tool_result is not None:
                    provider_result = forced_tool_result
                    model_record = {
                        "name": "wgrnn-openai-tool-router",
                        "provider": "runtime",
                        "model": "wg-rnn:chat",
                    }
                else:
                    provider_result, model_record = await _complete_wgrnn_chat_with_fallback(
                        settings,
                        kernel,
                        candidates=model_candidates,
                        prompt=prepared.get("response_prompt") or compact_prompt,
                        messages=chat_messages,
                        options=ollama_options,
                        tools=provider_tools,
                    )
                    provider_result = _ensure_forced_tool_call(req, provider_result)
                if has_search_tool_result and not provider_result.get("tool_calls"):
                    fallback_text = _deterministic_search_synthesis(compact_messages)
                    if fallback_text and _search_synthesis_failed(str(provider_result.get("response_text") or ""), provider_result):
                        provider_result["response_text"] = fallback_text
                        provider_result["provider_status"] = "wg_rnn_search_synthesis_fallback"
                if provider_result.get("tool_calls"):
                    return _openai_chat_response(req, provider_result) | {
                        "corpus": corpus_search,
                        "kernel_turn": {
                            "task_frame": prepared.get("task_frame"),
                            "boot": prepared.get("boot"),
                            "selected_model": model_record,
                            "tool_step": True,
                        },
                    }
                if has_search_tool_result and not provider_result.get("tool_calls"):
                    provider_result["response_text"] = _guard_profile_search_identity(
                        compact_messages, str(provider_result.get("response_text") or "")
                    )
                self_model = kernel_chat.enforce_self_model(
                    prepared=prepared,
                    response_text=str(provider_result.get("response_text") or ""),
                )
                provider_result["response_text"] = str(self_model.get("response_text") or "")
                provider_result["self_model"] = self_model
                reciprocity = kernel_chat.enforce_reciprocity(
                    prepared=prepared,
                    response_text=str(provider_result.get("response_text") or ""),
                )
                provider_result["response_text"] = str(reciprocity.get("response_text") or "")
                provider_result["reciprocity"] = reciprocity
                prepared["reciprocity"] = reciprocity
                finalized = kernel_chat.finalize_turn(
                    prepared=prepared,
                    response_text=str(provider_result.get("response_text") or ""),
                    needs_vision=needs_vision,
                )
                wgrnn_result = finalized.get("wgrnn")
                provider_result["model"] = provider_result.get("model", {}) | {"wg_rnn_mode": "chat", "selected_by": "kernel_task_frame"}
                provider_result["wgrnn"] = wgrnn_result
                provider_result["provider_status"] = "wg_rnn_kernel_chat"
                return _openai_chat_response(req, provider_result) | {
                    "wgrnn": wgrnn_result,
                    "corpus": corpus_search,
                    "wg_rnn_chat": finalized.get("kernel_turn"),
                    "kernel_turn": {
                        "task_frame": prepared.get("task_frame"),
                        "boot": prepared.get("boot"),
                        "witness_chain": finalized.get("witness_chain"),
                        "selected_model": model_record,
                    },
                }
            requested_action = "memory_write" if mode == "memory" else "observe"
            wgrnn_result = kernel.wgrnn.step(
                prompt=prompt_with_corpus,
                response_text="",
                requested_action=requested_action,
                evidence_quality=0.72,
                tags=["librechat", "corpus_context"] if corpus_search.get("results") else ["librechat"],
            )
            provider_result = {
                "model": {"name": req.model, "provider": "wgrnn", "model": req.model},
                "response_text": (
                    f"WG-RNN {mode} step completed. "
                    f"trust_status={wgrnn_result['memory_update']['trust_status']}; "
                    f"authority={wgrnn_result['memory_update']['authority_t']}; "
                    f"slot={wgrnn_result['memory_update']['slot_id']}."
                ),
                "reasoning_text": "",
                "tool_calls": [],
                "capabilities_observed": {"has_visible_response": True, "has_reasoning": False, "has_tool_calls": False, "reasoning_only": False},
                "provider_status": "wgrnn",
                "provider_metrics": {"eval_count": 0, "prompt_eval_count": 0, "done_reason": "stop"},
                "wgrnn": wgrnn_result,
            }
            return _openai_chat_response(req, provider_result) | {"wgrnn": wgrnn_result, "corpus": corpus_search}
        try:
            model_record = kernel.model_provider.registry.get(req.model)
            if _messages_have_images(req.messages):
                model_record = _select_vision_model(kernel, model_record)
            if model_record.get("provider") == "ollama":
                chat_messages = _messages_for_ollama_chat(req.messages, req.prompt)
                chat_messages = _prepend_corpus_context_message(chat_messages, corpus_search)
                ollama_options = {
                    "temperature": req.temperature if req.temperature is not None else 0.15,
                    "top_p": req.top_p if req.top_p is not None else 0.85,
                    "repeat_penalty": 1.08,
                }
                if req.max_tokens is not None:
                    ollama_options["num_predict"] = int(req.max_tokens)
                provider_result = await complete_ollama_generate(
                    settings,
                    prompt=prompt_with_corpus,
                    model=model_record,
                    options=ollama_options,
                    messages=chat_messages,
                )
            else:
                provider_result = await kernel.model_provider.complete(prompt=prompt_with_corpus, model_name=req.model)
        except RuntimeError as exc:
            message = str(exc)
            if "timeout" in message:
                raise HTTPException(status_code=504, detail={"error": "model_provider_timeout", "message": message}) from exc
            if "ollama_" in message or "llama_cpp_" in message:
                raise HTTPException(status_code=502, detail={"error": "model_provider_error", "message": message}) from exc
            raise
        try:
            wgrnn_result = kernel.wgrnn.step(
                prompt=prompt_with_corpus,
                response_text=str(provider_result.get("response_text") or ""),
                requested_action="observe",
                evidence_quality=0.72,
                tags=["librechat", "corpus_context"] if corpus_search.get("results") else ["librechat"],
            )
            provider_result["wgrnn"] = wgrnn_result
        except Exception as exc:
            provider_result["wgrnn_error"] = exc.__class__.__name__
        return _openai_chat_response(req, provider_result) | {"corpus": corpus_search, "wgrnn": provider_result.get("wgrnn")}

    @app.post("/v1/chat/completions/with-reasoning")
    async def chat_completions_with_reasoning(req: ChatCompletionRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        req.show_reasoning = True
        return await chat_completions(req, authorization)

    @app.post("/v1/run")
    async def run(req: RunRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        try:
            return await kernel.run_cognition(
                prompt=req.prompt,
                steps=req.steps,
                requested_action=req.requested_action,
                model_name=req.model_name,
                evidence_quality=req.evidence_quality,
            )
        except RuntimeError as exc:
            message = str(exc)
            if "timeout" in message:
                raise HTTPException(status_code=504, detail={"error": "model_provider_timeout", "message": message}) from exc
            if "ollama_" in message or "llama_cpp_" in message:
                raise HTTPException(status_code=502, detail={"error": "model_provider_error", "message": message}) from exc
            raise

    @app.get("/v1/tools")
    def tools(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return {
            "object": "list",
            "data": tools_runtime.openai_tools(),
            "capabilities": ["code_interpreter", "image_generation", "xavi_search_evidence", "sandbox_vm_control", "autonomous_research", "web_search", "news_search", "image_search"],
        }

    @app.post("/v1/tools/sandbox-vm")
    async def sandbox_vm_manage(req: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        action = str(req.get("action") or "").strip()
        if not action:
            raise HTTPException(status_code=422, detail="sandbox_action_required")
        request_payload = req.get("request") if isinstance(req.get("request"), dict) else {}
        return await tools_runtime.sandbox_vm_manage(action=action, request=request_payload)

    @app.post("/v1/tools/code/execute")
    async def code_execute(req: CodeExecuteRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        if not settings.code_interpreter_enabled:
            raise HTTPException(status_code=503, detail="code_interpreter_disabled")
        return await tools_runtime.code_execute(language=req.language, code=req.code, timeout_seconds=req.timeout_seconds, stdin=req.stdin)

    @app.post("/v1/tools/search/xavi")
    async def search_xavi(req: SearchEvidenceRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return await tools_runtime.search_xavi(query=req.query, top_k=req.top_k, engine=req.engine, channel=req.channel)

    @app.post("/v1/tools/search/evidence")
    async def search_evidence(req: SearchEvidenceRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return await tools_runtime.search_xavi(query=req.query, top_k=req.top_k, engine=req.engine, channel=req.channel)

    @app.post("/v1/images/generations")
    async def image_generations(req: ImageGenerationRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        result = await tools_runtime.generate_image(prompt=req.prompt, size=req.size, model=req.model, n=req.n)
        return {
            "created": int(result.get("created_at_ms", 0) / 1000),
            "data": [{"url": img.get("url"), "b64_json": None, "revised_prompt": req.prompt} for img in result.get("images", [])],
            "xavi": result,
        }

    @app.get("/v1/tools/artifacts/{artifact_id}")
    def get_tool_artifact(artifact_id: str, authorization: str | None = Header(default=None)) -> FileResponse:
        require_api_key(settings, authorization)
        meta = tools_runtime.get_artifact(artifact_id)
        if not meta:
            raise HTTPException(status_code=404, detail="artifact_not_found")
        return FileResponse(meta["path"], media_type=meta.get("media_type") or "application/octet-stream", filename=meta.get("filename"))

    @app.get("/v1/witnesses")
    def witnesses(limit: int = 20) -> dict[str, Any]:
        return {"items": kernel.store.fetch_recent("nla_activation_witnesses", limit), "generic": kernel.store.fetch_recent("evidence_witnesses", limit)}

    @app.get("/v1/evidence/witnesses")
    def evidence_witnesses(limit: int = 20) -> dict[str, Any]:
        return {"items": kernel.store.fetch_recent("evidence_witnesses", limit)}

    @app.post("/v1/evidence/observe")
    def evidence_observe(req: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        witness_type = str(req.get("witness_type") or "ExternalObservationWitness").strip()[:128]
        if not witness_type or not witness_type.endswith("Witness"):
            raise HTTPException(status_code=422, detail="witness_type_must_end_with_Witness")
        payload = req.get("payload")
        if not isinstance(payload, dict) or not payload:
            raise HTTPException(status_code=422, detail="nonempty_payload_required")
        # Keep this endpoint a bounded observation writer, not a way for callers to
        # mint promoted authority. The runtime owns witness identity and signature.
        status = str(req.get("status") or "recorded")[:64]
        if status not in {"recorded", "candidate", "observed", "quarantined"}:
            status = "candidate"
        witness = kernel.evidence.witness(witness_type, payload, force="observe", status=status)
        base_witness = dict(witness)
        signed = kernel.pq_keys.sign(
            {"witness_id": witness["witness_id"], "witness": base_witness},
            purpose="evidence",
        )
        verified = bool(kernel.pq_keys.verify(signed))
        if not verified:
            raise HTTPException(status_code=500, detail="evidence_signature_verification_failed")
        witness["signature_suite"] = signed.get("signature_suite")
        witness["signing_key_id"] = signed.get("key_id")
        witness["signed_envelope"] = signed
        witness["signature_verified"] = True
        kernel.store.insert_witness(witness, run_id=str(req.get("run_id") or "") or None)
        return {
            "schema_version": "signed-evidence-observation/v1",
            "witness": witness,
            "signed_envelope": signed,
            "signature_verified": True,
            "authority": "observed_evidence_only",
        }

    @app.post("/v1/memory-packets/observe")
    async def memory_packet_observe_rest(req: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_memory_packet_key(settings, authorization)
        packet = _validate_external_memory_packet(req.get("packet"))
        source_scope = str(req.get("source_scope") or "default")
        namespace, adapter_id, source_scope = _meta_graph_adapter_namespace(MEMORY_PACKET_ADAPTER_ID, source_scope)
        projection = _memory_packet_projection(packet)
        graph = build_information_graph(
            information_kind=projection["information_kind"],
            information_ref=projection["information_ref"],
            text_fields=projection["text_fields"],
            facets=projection["facets"],
            meta_objects=projection["meta_objects"],
            metadata=projection["metadata"],
        )
        witness_payload = {
            "schema_version": "media_meta_witness_memory_packet_observation/v1",
            "packet": packet,
            "ingest": {
                "adapter_id": adapter_id,
                "source_scope": source_scope,
                "trust_status": "candidate",
                "promotion_eligible": False,
                "authority": "observed_evidence_only",
            },
        }
        witness = kernel.evidence.witness(
            MEMORY_PACKET_WITNESS_TYPE,
            witness_payload,
            force="observe",
            status="candidate",
        )
        base_witness = dict(witness)
        signed = kernel.pq_keys.sign(
            {"witness_id": witness["witness_id"], "witness": base_witness},
            purpose="evidence",
        )
        if not bool(kernel.pq_keys.verify(signed)):
            raise HTTPException(status_code=500, detail="memory_packet_signature_verification_failed")
        witness["signature_suite"] = signed.get("signature_suite")
        witness["signing_key_id"] = signed.get("key_id")
        witness["signed_envelope"] = signed
        witness["signature_verified"] = True
        kernel.store.insert_witness(witness, run_id=str(req.get("run_id") or "") or None)

        import time
        persisted = await asyncio.to_thread(
            kernel.store.insert_meta_graph_observation,
            graph=graph,
            namespace=namespace,
            source_update_id=str(witness["witness_id"]),
            trust_status="candidate",
            observed_at_ms=int(time.time() * 1000),
            metadata={
                "adapter_id": adapter_id,
                "source_scope": source_scope,
                "evidence_witness_id": str(witness["witness_id"]),
                "packet_logical_id": str(packet["logical_id"]),
                "source_integrity": "unsealed",
                "promotion_eligible": False,
                "authority": "candidate_observation_only",
            },
        )
        return {
            "schema_version": "media_meta_witness_memory_packet_ingest/v1",
            "logical_id": str(packet["logical_id"]),
            "witness_id": str(witness["witness_id"]),
            "observation_id": str(persisted.get("observation_id") or ""),
            "namespace": namespace,
            "trust_status": "candidate",
            "source_integrity": "unsealed",
            "signature_suite": witness.get("signature_suite"),
            "signing_key_id": witness.get("signing_key_id"),
            "signature_verified": True,
            "promotion_eligible": False,
            "authority": "observed_evidence_only",
            "retrieval_authority": "candidate_ranking_signal_only",
            "note": "The runtime signature witnesses receipt and storage of this unsealed packet; it does not promote the packet contents to truth or learned behavior.",
        }

    @app.post("/v1/evidence/verify")
    def evidence_verify(req: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        envelope = req.get("signed_envelope")
        if not isinstance(envelope, dict):
            raise HTTPException(status_code=422, detail="signed_envelope_required")
        verified = bool(kernel.pq_keys.verify(envelope))
        return {
            "schema_version": "signed-evidence-verification/v1",
            "verified": verified,
            "signature_suite": envelope.get("signature_suite"),
            "signing_key_id": envelope.get("key_id"),
            "authority": "cryptographic_verification_only",
        }

    @app.post("/v1/evidence/claims")
    def submit_claim(req: EvidenceClaimRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.submit_claim(req.model_dump())

    @app.get("/v1/evidence/claims")
    def evidence_claims(limit: int = 20) -> dict[str, Any]:
        return {"items": kernel.store.fetch_recent("evidence_claims", limit)}

    @app.post("/v1/consensus/observe")
    def consensus_observe(req: ConsensusObservationRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.consensus.observe(
            subject=req.subject,
            predicate=req.predicate,
            object_value=req.object,
            observer_id=req.observer_id,
            observer_kind=req.observer_kind,
            independence_group=req.independence_group,
            stance=req.stance,
            confidence=req.confidence,
            source_ref=req.source_ref,
            evidence_refs=req.evidence_refs,
            payload=req.payload,
        )

    @app.post("/v1/consensus/evaluate")
    def consensus_evaluate(req: ConsensusEvaluateRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.consensus.evaluate(
            claim_key=req.claim_key,
            min_independent_groups=req.min_independent_groups,
            min_support_ratio=req.min_support_ratio,
            min_support_weight=req.min_support_weight,
            max_contradiction_ratio=req.max_contradiction_ratio,
        )

    @app.get("/v1/consensus/claims")
    def consensus_claims(
        limit: int = 50,
        promotion_recommended: bool | None = None,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return {
            "schema_version": "observer-consensus-v1",
            "items": kernel.consensus.recent(limit=limit, promotion_recommended=promotion_recommended),
        }

    # Internal autonomy REST bridge. These routes expose the same governed
    # kernel operations as runtime MCP but run synchronous store/autonomy work
    # in worker threads so large artifact ingestion cannot serialize the MCP
    # control lane or the FastAPI event loop.
    @app.get("/v1/autonomy/status")
    async def autonomy_status_rest(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        import asyncio
        return await asyncio.to_thread(kernel.autonomy.status)

    @app.post("/v1/autonomy/experiment/propose")
    async def autonomy_experiment_propose_rest(req: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        import asyncio
        subject = str(req.get("subject") or "").strip()
        predicate = str(req.get("predicate") or "").strip()
        if not subject or not predicate or "object" not in req:
            raise HTTPException(status_code=422, detail="experiment_subject_predicate_object_required")
        return await asyncio.to_thread(
            kernel.autonomy.propose_experiment,
            subject=subject,
            predicate=predicate,
            object_value=req.get("object"),
            question=req.get("question"),
            hypothesis=req.get("hypothesis"),
            experiment_kind=str(req.get("experiment_kind") or "observer_consensus"),
            falsification=req.get("falsification"),
            observer_plan=[str(x) for x in (req.get("observer_plan") or [])] if isinstance(req.get("observer_plan"), list) else None,
            minimum_independent_groups=max(1, min(int(req.get("minimum_independent_groups", 3)), 32)),
            min_support_ratio=max(0.0, min(float(req.get("min_support_ratio", 0.75)), 1.0)),
            max_contradiction_ratio=max(0.0, min(float(req.get("max_contradiction_ratio", 0.20)), 1.0)),
            priority=max(0, min(int(req.get("priority", 50)), 100)),
            origin=str(req.get("origin") or "wg-rnn:self"),
            metadata=req.get("metadata") if isinstance(req.get("metadata"), dict) else {},
            session_id=str(req.get("session_id") or "wg-rnn:self-experimentation"),
        )

    @app.post("/v1/autonomy/experiment/next")
    async def autonomy_experiment_next_rest(req: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            autonomy_control_executor,
            partial(
                kernel.autonomy.next_experiment,
                session_id=str(req.get("session_id") or "wg-rnn:self-experimentation"),
            ),
        )

    @app.post("/v1/autonomy/experiment/observe")
    async def autonomy_experiment_observe_rest(req: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        stance = str(req.get("stance") or "uncertain")
        if stance not in {"support", "contradict", "uncertain"}:
            raise HTTPException(status_code=422, detail="invalid_experiment_stance")
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            autonomy_control_executor,
            partial(
                kernel.autonomy.experiment_observe,
                experiment_id=str(req.get("experiment_id") or ""),
                observer_id=str(req.get("observer_id") or ""),
                observer_kind=str(req.get("observer_kind") or "unknown"),
                independence_group=str(req.get("independence_group") or req.get("observer_id") or "unknown"),
                stance=stance,
                confidence=max(0.0, min(float(req.get("confidence", 0.5)), 1.0)),
                observation=req.get("observation"),
                source_ref=req.get("source_ref"),
                evidence_refs=[str(x) for x in (req.get("evidence_refs") or [])],
                measurement=req.get("measurement") if isinstance(req.get("measurement"), dict) else {},
                session_id=str(req.get("session_id") or "wg-rnn:self-experimentation"),
            ),
        )

    @app.post("/v1/autonomy/experiment/complete")
    async def autonomy_experiment_complete_rest(req: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            autonomy_control_executor,
            partial(
                kernel.autonomy.complete_experiment,
                experiment_id=str(req.get("experiment_id") or ""),
                session_id=str(req.get("session_id") or "wg-rnn:self-experimentation"),
            ),
        )

    @app.post("/v1/meta-graph/observe")
    async def meta_graph_observe_rest(req: MetaGraphObserveRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        import time

        namespace, adapter_id, source_scope = _meta_graph_adapter_namespace(req.adapter_id, req.source_scope)
        if len(req.text_fields) > 24:
            raise HTTPException(status_code=422, detail="too_many_text_fields")
        text_fields = {str(key)[:128]: str(value)[:20000] for key, value in req.text_fields.items()}
        if sum(len(value) for value in text_fields.values()) > 120000:
            raise HTTPException(status_code=422, detail="text_fields_too_large")
        try:
            if len(json.dumps(req.facets, ensure_ascii=False, default=str)) > 262144:
                raise HTTPException(status_code=422, detail="facets_too_large")
            if len(req.meta_objects) > 4096:
                raise HTTPException(status_code=422, detail="too_many_meta_objects_in_single_observation")
            if len(json.dumps(req.meta_objects, ensure_ascii=False, default=str)) > 2097152:
                raise HTTPException(status_code=422, detail="meta_objects_too_large")
            if len(json.dumps(req.metadata, ensure_ascii=False, default=str)) > 262144:
                raise HTTPException(status_code=422, detail="metadata_too_large")
            if len(req.aggregate_schema) > 256 or len(json.dumps(req.aggregate_schema, ensure_ascii=False, default=str)) > 65536:
                raise HTTPException(status_code=422, detail="aggregate_schema_too_large")
            if len(req.extractor_versions) > 128 or len(json.dumps(req.extractor_versions, ensure_ascii=False, default=str)) > 32768:
                raise HTTPException(status_code=422, detail="extractor_versions_too_large")
            if len(req.perceptual_refs) > 128 or len(json.dumps(req.perceptual_refs, ensure_ascii=False, default=str)) > 65536:
                raise HTTPException(status_code=422, detail="perceptual_refs_too_large")
            if len(json.dumps(req.redaction_descriptor, ensure_ascii=False, default=str)) > 16384:
                raise HTTPException(status_code=422, detail="redaction_descriptor_too_large")
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=f"non_serializable_meta_graph_input:{exc.__class__.__name__}") from exc

        if req.redacted and (req.build_profile or req.sign_profile):
            raise HTTPException(status_code=422, detail="redacted_observation_cannot_finalize_media_profile")
        if req.sign_profile and not req.build_profile:
            # Signing implies deterministic profile construction/finalization.
            req.build_profile = True

        if req.redacted:
            effective_text_fields: dict[str, str] = {}
            effective_facets: dict[str, Any] = {
                "adapter_id": adapter_id,
                "source_scope": source_scope,
                "redacted": True,
                "redaction_descriptor": req.redaction_descriptor,
            }
            # Sensitive measurements are accepted by the API but discarded before
            # canonicalization when the observation is explicitly redacted.
            effective_meta_objects: list[dict[str, Any]] = []
            effective_metadata: dict[str, Any] = {
                "redacted": True,
                "redaction_descriptor": req.redaction_descriptor,
            }
        else:
            effective_text_fields = text_fields
            # Descriptive facets belong in the media composition. Adapter/source
            # bookkeeping is provenance metadata, not a measured media quality.
            effective_facets = dict(req.facets)
            effective_meta_objects = [dict(row) for row in req.meta_objects]
            effective_metadata = dict(req.metadata)
            effective_metadata.update({"redacted": False, "adapter_id": adapter_id, "source_scope": source_scope})
        if not req.text_fields and not req.facets and not req.meta_objects and not req.metadata and not req.redaction_descriptor:
            raise HTTPException(status_code=422, detail="meta_graph_observation_content_required")

        graph = build_information_graph(
            information_kind=str(req.information_kind),
            information_ref=str(req.information_ref or f"{adapter_id}:{source_scope}"),
            text_fields=effective_text_fields,
            facets=effective_facets,
            meta_objects=effective_meta_objects,
            metadata=effective_metadata,
        )
        profile_bundle: dict[str, Any] | None = None
        if req.build_profile:
            try:
                profile_bundle = await asyncio.to_thread(
                    build_media_profile,
                    graph,
                    aggregate_schema=req.aggregate_schema,
                    extractor_versions=req.extractor_versions,
                    perceptual_refs=req.perceptual_refs,
                    key_manager=kernel.pq_keys if req.sign_profile else None,
                )
            except (ValueError, OverflowError) as exc:
                raise HTTPException(status_code=422, detail=f"invalid_media_profile:{exc}") from exc

        def persist_observation_and_profile() -> tuple[dict[str, Any], dict[str, Any] | None]:
            with kernel.store.connect() as conn:
                persisted_observation = kernel.store.insert_meta_graph_observation(
                    graph=graph,
                    namespace=namespace,
                    source_update_id=None,
                    trust_status="candidate",
                    observed_at_ms=int(time.time() * 1000),
                    metadata={
                        "adapter_id": adapter_id,
                        "source_scope": source_scope,
                        "redacted": bool(req.redacted),
                        "authority": "candidate_observation_only",
                    },
                    connection=conn,
                    commit=False,
                )
                persisted_profile = None
                if profile_bundle is not None:
                    persisted_profile = kernel.store.insert_media_profile_bundle(
                        bundle=profile_bundle,
                        namespace=namespace,
                        observation_id=persisted_observation.get("observation_id"),
                        trust_status="candidate",
                        connection=conn,
                        commit=False,
                    )
                conn.commit()
                return persisted_observation, persisted_profile

        persisted, persisted_profile = await asyncio.to_thread(persist_observation_and_profile)
        profile_summary = None
        if profile_bundle is not None:
            profile_summary = {
                "profile_id": profile_bundle.get("profile_id"),
                "profile": profile_bundle.get("profile"),
                "root_node_id": (profile_bundle.get("dag") or {}).get("root_node_id"),
                "leaf_count": (profile_bundle.get("dag") or {}).get("leaf_count"),
                "node_count": (profile_bundle.get("dag") or {}).get("node_count"),
                "signed_manifest": profile_bundle.get("signed_manifest"),
                "signature_verified": bool(profile_bundle.get("signature_verified")),
                "persisted": persisted_profile,
            }
        return {
            "schema_version": "meta_graph_adapter_observe/v1",
            "contract_version": graph.get("contract_version"),
            "namespace": namespace,
            "adapter_id": adapter_id,
            "source_scope": source_scope,
            "redacted": bool(req.redacted),
            "root_content_id": graph.get("root_content_id"),
            "composition_content_id": graph.get("composition_content_id"),
            "content_count": len(graph.get("content_ids") or []),
            "meta_object_count": len(graph.get("meta_object_ids") or []),
            "occurrence_count": len(graph.get("occurrence_ids") or []),
            "edge_count": len(graph.get("edge_ids") or []),
            "trust_status": "candidate",
            "authority": "candidate_observation_only",
            "persisted": persisted,
            "media_profile": profile_summary,
        }

    @app.post("/v1/meta-graph/retrieve")
    async def meta_graph_retrieve_rest(req: MetaGraphRetrieveRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        namespace, adapter_id, source_scope = _meta_graph_adapter_namespace(req.adapter_id, req.source_scope)
        if not req.query.strip() and not req.facets and not req.meta_objects:
            raise HTTPException(status_code=422, detail="meta_graph_query_required")
        try:
            if len(json.dumps(req.facets, ensure_ascii=False, default=str)) > 131072:
                raise HTTPException(status_code=422, detail="query_facets_too_large")
            if len(req.meta_objects) > 4096:
                raise HTTPException(status_code=422, detail="too_many_query_meta_objects")
            if len(json.dumps(req.meta_objects, ensure_ascii=False, default=str)) > 2097152:
                raise HTTPException(status_code=422, detail="query_meta_objects_too_large")
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=f"non_serializable_meta_graph_query:{exc.__class__.__name__}") from exc
        query_graph = build_information_graph(
            information_kind="adapter_meta_graph_query",
            information_ref=f"query:{adapter_id}:{source_scope}",
            text_fields={"query": req.query[:16000]} if req.query.strip() else {},
            facets={"payload": req.facets} if req.facets else {},
            meta_objects=[dict(row) for row in req.meta_objects],
            metadata={},
        )
        exact_result, composition_result = await asyncio.gather(
            asyncio.to_thread(
                kernel.store.search_meta_graph,
                namespace=namespace,
                query_content_ids=query_graph.get("meta_object_ids") or [],
                limit=req.limit,
                require_source_update_id=False,
            ),
            asyncio.to_thread(
                kernel.store.search_meta_compositions,
                namespace=namespace,
                query_graph=query_graph,
                limit=req.limit,
                minimum_similarity=0.25,
            ),
        )
        return {
            "schema_version": "meta_graph_adapter_retrieve/v3",
            "contract_version": query_graph.get("contract_version"),
            "namespace": namespace,
            "adapter_id": adapter_id,
            "source_scope": source_scope,
            "query_content_count": len(query_graph.get("content_ids") or []),
            "query_meta_object_count": len(query_graph.get("meta_object_ids") or []),
            "query_composition_content_id": query_graph.get("composition_content_id"),
            "authority": "candidate_ranking_signal_only",
            "exact_witness_recurrence": exact_result,
            "composition_similarity": composition_result,
        }

    @app.post("/v1/memory-packets/retrieve")
    async def memory_packet_retrieve_rest(req: MemoryPacketRetrieveRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_memory_packet_key(settings, authorization)
        if not req.query.strip() and not req.meta_objects:
            raise HTTPException(status_code=422, detail="memory_packet_query_required")
        retrieval = await meta_graph_retrieve_rest(
            MetaGraphRetrieveRequest(
                adapter_id=MEMORY_PACKET_ADAPTER_ID,
                source_scope=req.source_scope,
                query=req.query,
                facets={},
                meta_objects=req.meta_objects,
                limit=req.limit,
            ),
            authorization,
        )
        witness_refs: list[str] = []
        for section_name in ("exact_witness_recurrence", "composition_similarity"):
            section = retrieval.get(section_name) if isinstance(retrieval.get(section_name), dict) else {}
            for row in section.get("matches") or []:
                if not isinstance(row, dict):
                    continue
                ref = str(row.get("source_update_id") or "").strip()
                if ref and ref not in witness_refs:
                    witness_refs.append(ref)
        return {
            "schema_version": "media_meta_witness_memory_packet_retrieve/v1",
            "namespace": retrieval.get("namespace"),
            "query": req.query,
            "witness_refs": witness_refs,
            "authority": "candidate_ranking_signal_only",
            "promotion_eligible": False,
            "retrieval": retrieval,
        }

    @app.get("/v1/memory-packets/{witness_id}")
    def memory_packet_get_rest(witness_id: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_memory_packet_key(settings, authorization)
        row = kernel.store.get_evidence_witness(witness_id)
        if row is None or str(row.get("witness_type") or "") != MEMORY_PACKET_WITNESS_TYPE:
            raise HTTPException(status_code=404, detail="memory_packet_witness_not_found")
        payload = row.get("payload")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=500, detail="stored_memory_packet_payload_invalid") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("packet"), dict):
            raise HTTPException(status_code=500, detail="stored_memory_packet_payload_invalid")
        envelope = row.get("signed_envelope")
        if isinstance(envelope, str):
            try:
                envelope = json.loads(envelope)
            except json.JSONDecodeError:
                envelope = None
        return {
            "schema_version": "media_meta_witness_memory_packet_record/v1",
            "witness_id": str(row.get("witness_id") or witness_id),
            "witness_type": MEMORY_PACKET_WITNESS_TYPE,
            "status": str(row.get("status") or "candidate"),
            "packet": payload["packet"],
            "ingest": payload.get("ingest") if isinstance(payload.get("ingest"), dict) else {},
            "signature_suite": row.get("signature_suite"),
            "signing_key_id": row.get("signing_key_id"),
            "signed_envelope": envelope,
            "signature_verified": bool(row.get("signature_verified")),
            "authority": "observed_evidence_only",
            "promotion_eligible": False,
        }

    @app.post("/v1/meta-graph/chain/build")
    async def meta_graph_chain_build_rest(req: MetaGraphChainBuildRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        profile_ids = [str(value).strip() for value in req.profile_ids]
        if any(not value for value in profile_ids):
            raise HTTPException(status_code=422, detail="empty_profile_id")

        graphs: list[dict[str, Any]] = []
        profile_summaries: list[dict[str, Any]] = []
        for profile_id in profile_ids:
            bundle = await asyncio.to_thread(kernel.store.get_media_profile_bundle, profile_id)
            if bundle is None:
                raise HTTPException(status_code=404, detail=f"media_profile_not_found:{profile_id}")
            signed_profile = isinstance(bundle.get("signed_manifest"), dict)
            valid_profile = await asyncio.to_thread(
                verify_media_profile,
                bundle,
                key_manager=kernel.pq_keys if signed_profile else None,
            )
            if not valid_profile:
                raise HTTPException(status_code=409, detail=f"media_profile_verification_failed:{profile_id}")
            observation_id = str(bundle.get("observation_id") or "")
            if not observation_id:
                raise HTTPException(status_code=409, detail=f"media_profile_missing_observation:{profile_id}")
            graph = await asyncio.to_thread(kernel.store.get_meta_graph_observation, observation_id)
            if graph is None:
                raise HTTPException(status_code=409, detail=f"media_profile_observation_not_found:{profile_id}")
            graph["profile_id"] = profile_id
            graphs.append(graph)
            profile_summaries.append({
                "profile_id": profile_id,
                "information_ref": bundle.get("information_ref"),
                "observation_id": observation_id,
                "signature_verified": bool(bundle.get("signature_verified")),
                "trust_status": bundle.get("trust_status"),
            })

        chain = await asyncio.to_thread(build_information_chain, graphs)
        chain_id = str(chain["chain_pattern_content_id"])
        chain_body = {key: value for key, value in chain.items() if key not in {"chain_pattern_content_id", "transitions"}}
        signed_manifest = None
        signature_verified = False
        if req.sign_chain:
            signed_manifest = await asyncio.to_thread(
                kernel.pq_keys.sign,
                {"chain_id": chain_id, "chain": chain_body},
                purpose="manifest",
            )
            signature_verified = await asyncio.to_thread(kernel.pq_keys.verify, signed_manifest)
            if not signature_verified:
                raise HTTPException(status_code=500, detail="information_chain_signature_verification_failed")
        persisted = await asyncio.to_thread(
            kernel.store.insert_information_chain,
            chain_id=chain_id,
            chain_body=chain_body,
            profile_ids=profile_ids,
            chain_ref=req.chain_ref,
            signed_manifest=signed_manifest,
            signature_verified=signature_verified,
            trust_status="candidate",
        )
        return {
            "schema_version": "meta_graph_chain_build/v1",
            "contract_version": "v1.6-draft-5.3.18",
            "chain_id": chain_id,
            "chain_ref": req.chain_ref,
            "profile_ids": profile_ids,
            "profiles": profile_summaries,
            "chain": chain,
            "signed_manifest": signed_manifest,
            "signature_verified": signature_verified,
            "authority": "candidate_pattern_witness_only",
            "persisted": persisted,
        }

    @app.post("/v1/meta-graph/chain/get")
    async def meta_graph_chain_get_rest(req: MetaGraphChainGetRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        stored = await asyncio.to_thread(kernel.store.get_information_chain, req.chain_id)
        if stored is None:
            raise HTTPException(status_code=404, detail="information_chain_not_found")
        signed_manifest = stored.get("signed_manifest") if isinstance(stored.get("signed_manifest"), dict) else None
        signature_valid_now = None
        if signed_manifest is not None:
            signature_valid_now = await asyncio.to_thread(kernel.pq_keys.verify, signed_manifest)
            payload = dict(signed_manifest.get("payload") or {})
            if payload.get("chain_id") != stored["chain_id"] or payload.get("chain") != stored["chain"]:
                signature_valid_now = False

        profiles: list[dict[str, Any]] = []
        descriptions: list[dict[str, Any]] = []
        for profile_id in stored.get("profile_ids") or []:
            bundle = await asyncio.to_thread(kernel.store.get_media_profile_bundle, profile_id)
            if bundle is None:
                profiles.append({"profile_id": profile_id, "available": False})
                continue
            profiles.append({
                "profile_id": profile_id,
                "available": True,
                "information_ref": bundle.get("information_ref"),
                "observation_id": bundle.get("observation_id"),
                "signature_verified_at_write": bool(bundle.get("signature_verified")),
                "trust_status": bundle.get("trust_status"),
            })
            if req.include_descriptions and bundle.get("observation_id"):
                graph = await asyncio.to_thread(kernel.store.get_meta_graph_observation, str(bundle["observation_id"]))
                if graph is not None:
                    descriptions.append(await asyncio.to_thread(reconstruct_information_description, graph))
        return {
            **stored,
            "profiles": profiles,
            "descriptions": descriptions if req.include_descriptions else None,
            "signature_valid_now": signature_valid_now,
            "authority": "candidate_pattern_witness_only",
        }

    @app.post("/v1/child-safety/scan")
    async def child_safety_scan_rest(request: Request, authorization: str | None = Header(default=None), x_media_type: str | None = Header(default=None), x_source_ref: str | None = Header(default=None), x_enforcement: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        from .child_safety import ChildSafetyRuntime, MAX_SCAN_BYTES
        raw = await request.body()
        if len(raw) > MAX_SCAN_BYTES:
            raise HTTPException(status_code=413, detail="media_exceeds_child_safety_scan_limit")
        return await ChildSafetyRuntime(kernel).scan_bytes(
            contents=raw, media_type=x_media_type or request.headers.get("content-type") or "application/octet-stream",
            source_ref=x_source_ref, enforcement=x_enforcement or "mandatory_public",
        )

    @app.post("/v1/model-observer/observe")
    async def model_observer_observe_rest(req: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        from .model_observer import ModelObservationRuntime
        question = str(req.get("question") or req.get("prompt") or "").strip()
        if not question:
            raise HTTPException(status_code=422, detail="question_required")
        runtime = ModelObservationRuntime(kernel)
        model_names = req.get("model_names") if isinstance(req.get("model_names"), list) else None
        if bool(req.get("parallel")) or model_names:
            return await runtime.observe_parallel(
                question=question, model_names=[str(x) for x in model_names] if model_names else None,
                claim=req.get("claim") if isinstance(req.get("claim"), dict) else {},
                context=req.get("context") if isinstance(req.get("context"), dict) else {},
                max_observers=max(1, min(int(req.get("max_observers", 4)), 8)),
            )
        return await runtime.observe_one(
            question=question, model_name=req.get("model_name"),
            claim=req.get("claim") if isinstance(req.get("claim"), dict) else {},
            context=req.get("context") if isinstance(req.get("context"), dict) else {},
            independence_group=req.get("independence_group"),
        )

    @app.post("/v1/content-rating/observe")
    async def content_rating_observe_rest(req: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        from .content_rating import ContentRatingRuntime
        return await ContentRatingRuntime(kernel).observe(
            text=req.get("text"),
            url=req.get("url"),
            image_url=req.get("image_url"),
            media_ref=req.get("media_ref"),
            policy=str(req.get("policy") or "public_u18"),
            context=req.get("context") if isinstance(req.get("context"), dict) else {},
            timeout_seconds=max(1.0, min(float(req.get("timeout_seconds", 8.0)), 20.0)),
        )

    @app.post("/v1/autonomy/research/execute")
    async def autonomy_research_execute_rest(req: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        query=str(req.get("query") or "").strip()
        if not query:
            raise HTTPException(status_code=422,detail="query_required")
        requested=req.get("channels") if isinstance(req.get("channels"),list) else [req.get("channel") or "web"]
        channels=[]
        for item in requested:
            name=str(item or "web").strip().lower()
            name={"general":"web","image":"images","pictures":"images"}.get(name,name)
            if name in {"web","news","images"} and name not in channels:
                channels.append(name)
        if not channels:
            channels=["web"]
        limit=max(1,min(int(req.get("limit",8)),10))
        results=await asyncio.gather(*[
            tools_runtime.search_xavi(query=query,top_k=limit,engine="xavi-autonomy",channel=channel)
            for channel in channels
        ],return_exceptions=True)
        normalized=[]
        for channel,result in zip(channels,results):
            if isinstance(result,Exception):
                normalized.append({"ok":False,"channel":channel,"result_count":0,"results":[],"errors":[result.__class__.__name__]})
            else:
                normalized.append(result)
        return await asyncio.to_thread(
            kernel.autonomy.record_external_research,
            query=query,
            objective=str(req.get("objective") or query),
            channel_results=normalized,
            initiated_by=str(req.get("initiated_by") or "wgrnn-autonomy"),
            reason=str(req.get("reason") or "autonomous-research"),
            session_id=str(req.get("session_id") or "autonomous-research"),
            training_eligible=bool(req.get("learn",True)),
            metadata=req.get("metadata") if isinstance(req.get("metadata"),dict) else {},
        )

    @app.post("/v1/autonomy/source/search")
    async def autonomy_source_search_rest(req: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        import asyncio
        return await asyncio.to_thread(
            kernel.store.search_source_documents,
            query=str(req.get("query") or ""),
            repository_id=req.get("repository_id"),
            path_prefix=req.get("path_prefix"),
            training_eligible=req.get("training_eligible"),
            limit=max(1, min(int(req.get("limit", 12)), 100)),
            preview_chars=max(120, min(int(req.get("preview_chars", 900)), 2000)),
        )

    @app.post("/v1/autonomy/reference/search")
    async def autonomy_reference_search_rest(req: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
        """LAN/offline-safe search over witnessed local training/reference chunks."""
        require_api_key(settings, authorization)
        import asyncio
        query = str(req.get("query") or "").strip()
        if not query:
            raise HTTPException(status_code=422, detail="query_required")
        return await asyncio.to_thread(
            kernel.store.search_reference_corpus,
            query=query,
            session_id=req.get("session_id"),
            event_type=str(req.get("event_type") or "source_training_chunk"),
            tag=req.get("tag"),
            source_path_prefix=req.get("source_path_prefix"),
            adapter=req.get("adapter"),
            mime_type=req.get("mime_type"),
            limit=max(1, min(int(req.get("limit", 20)), 100)),
            preview_chars=max(120, min(int(req.get("preview_chars", 900)), 2000)),
        )

    @app.post("/v1/autonomy/training/observe")
    async def autonomy_training_observe_rest(req: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        import asyncio
        content = str(req.get("content") or "")
        if not content.strip():
            raise HTTPException(status_code=422, detail="content_required")
        return await asyncio.to_thread(
            kernel.autonomy.observe_source_training_chunk,
            artifact_id=str(req.get("artifact_id") or "unknown"),
            source_path=str(req.get("source_path") or ""),
            source_digest=str(req.get("source_digest") or ""),
            chunk_index=max(0, int(req.get("chunk_index", 0))),
            content=content[:12000],
            adapter=req.get("adapter"),
            mime_type=req.get("mime_type"),
            derivation=str(req.get("derivation") or "derived-content"),
            metadata=req.get("metadata") if isinstance(req.get("metadata"), dict) else {},
            session_id=str(req.get("session_id") or "datalake-training"),
        )

    @app.post("/v1/autonomy/artifact/ingest")
    async def autonomy_artifact_ingest_rest(req: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        import asyncio
        path = str(req.get("path") or "")
        if not path:
            raise HTTPException(status_code=422, detail="path_required")
        return await asyncio.to_thread(
            kernel.autonomy.ingest_artifact,
            path=path,
            source_kind=str(req.get("source_kind") or "artifact"),
            derived_text=req.get("derived_text"),
            derived_records=req.get("derived_records") if isinstance(req.get("derived_records"), list) else [],
            metadata=req.get("metadata") if isinstance(req.get("metadata"), dict) else {},
            training_eligible=bool(req.get("training_eligible", True)),
            auto_transcribe=bool(req.get("auto_transcribe", True)),
            auto_extract=bool(req.get("auto_extract", True)),
            auto_vision=bool(req.get("auto_vision", True)),
            session_id=str(req.get("session_id") or "media-ingest"),
        )

    @app.get("/v1/autonomy/train-ingest/status")
    async def autonomy_train_ingest_status_rest(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return train_ingest_loop.status()

    @app.post("/v1/autonomy/train-ingest/scan")
    async def autonomy_train_ingest_scan_rest(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return await asyncio.to_thread(train_ingest_loop.scan_once)

    @app.post("/v1/autonomy/datalake/observe")
    async def autonomy_datalake_observe_rest(req: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        import asyncio
        return await asyncio.to_thread(
            kernel.autonomy.record_datalake_observation,
            artifact_id=str(req.get("artifact_id") or ""),
            source_path=str(req.get("source_path") or ""),
            source_digest=str(req.get("source_digest") or ""),
            observation_kind=str(req.get("observation_kind") or "observation"),
            statement=str(req.get("statement") or ""),
            confidence=max(0.0, min(float(req.get("confidence", 0.7)), 1.0)),
            observer_id=str(req.get("observer_id") or "wgrnn-datalake"),
            observer_kind=str(req.get("observer_kind") or "derived_observer"),
            independence_group=req.get("independence_group"),
            epistemic_class=str(req.get("epistemic_class") or "machine_derived"),
            metadata=req.get("metadata") if isinstance(req.get("metadata"), dict) else {},
            claim=req.get("claim") if isinstance(req.get("claim"), dict) else None,
            session_id=str(req.get("session_id") or "datalake-ingest"),
        )

    @app.post("/v1/autonomy/datalake/pattern")
    async def autonomy_datalake_pattern_rest(req: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        import asyncio
        metadata = dict(req.get("metadata") if isinstance(req.get("metadata"), dict) else {})
        if req.get("root_path") is not None:
            metadata.setdefault("root_path", req.get("root_path"))
        if req.get("commit_id") is not None:
            metadata.setdefault("commit_id", req.get("commit_id"))
        return await asyncio.to_thread(
            kernel.autonomy.record_datalake_pattern,
            pattern_kind=str(req.get("pattern_kind") or "pattern"),
            statement=str(req.get("statement") or ""),
            members=req.get("members") if isinstance(req.get("members"), list) else [],
            confidence=max(0.0, min(float(req.get("confidence", 0.7)), 1.0)),
            observer_id=str(req.get("observer_id") or "wgrnn-pattern-engine"),
            metadata=metadata,
            session_id=str(req.get("session_id") or "datalake-patterns"),
        )

    @app.get("/v1/firehose")
    def firehose(
        limit: int = 180,
        per_source: int = 40,
        text_limit: int = 900,
        raw: bool = True,
    ) -> dict[str, Any]:
        from .firehose import build_firehose
        return build_firehose(
            kernel,
            limit=limit,
            per_source=per_source,
            text_limit=text_limit,
            include_raw=raw,
        )

    @app.get("/v1/memory")
    def memory(limit: int = 20) -> dict[str, Any]:
        return {"items": kernel.store.fetch_recent("memory_cells", limit)}

    @app.get("/v1/audit")
    def audit(limit: int = 20) -> dict[str, Any]:
        return {"items": kernel.store.fetch_recent("audit_events", limit)}

    @app.get("/v1/models/registry")
    async def model_registry() -> dict[str, Any]:
        # In-memory inventory endpoint; keep full registries out of /health.
        return {"items": kernel.model_provider.registry.list_models()}

    @app.get("/v1/models")
    def models() -> dict[str, Any]:
        return build_openai_models_response(kernel.model_provider.registry)

    @app.get("/v1/models/catalog")
    def model_catalog() -> dict[str, Any]:
        return kernel.model_orchestrator.catalog()

    @app.get("/v1/models/capabilities")
    def model_capabilities() -> dict[str, Any]:
        return {"capabilities": kernel.model_orchestrator.capabilities()}

    @app.get("/v1/models/kv-policy-matrix")
    def model_kv_policy_matrix() -> dict[str, Any]:
        return {"kv_policies": kernel.model_orchestrator.kv_policy_matrix()}

    @app.post("/v1/models/route-preview")
    def model_route_preview(req: ModelRoutePreviewRequest) -> dict[str, Any]:
        return kernel.model_orchestrator.route_preview(req.model_dump())

    @app.get("/v1/models/{model_id:path}")
    def model_detail(model_id: str):
        model = find_openai_model(kernel.model_provider.registry, model_id)
        if model is None:
            return JSONResponse(status_code=404, content=openai_model_not_found(model_id))
        return model

    @app.get("/v1/turboquant/status")
    def turboquant_status() -> dict[str, Any]:
        return kernel.turbo_quant.status()

    @app.post("/v1/turboquant/calibrate")
    def turboquant_calibrate(req: TurboQuantBatchRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.turbo_quant.calibrate(req.vectors)

    @app.post("/v1/turboquant/compress")
    def turboquant_compress(req: TurboQuantVectorRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.turbo_quant.compress(req.vector)

    @app.post("/v1/turboquant/decompress")
    def turboquant_decompress(req: TurboQuantCompressedRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.turbo_quant.decompress(req.compressed_b64)

    @app.post("/v1/turboquant/signature")
    def turboquant_signature(req: TurboQuantSignatureRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.turbo_quant.signature(req.vector, max_bits=req.max_bits)

    @app.post("/v1/turboquant/signature-distance")
    def turboquant_signature_distance(req: TurboQuantSignatureDistanceRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.turbo_quant.signature_distance(req.a_b64, req.b_b64)

    @app.post("/v1/turboquant/quality")
    def turboquant_quality(req: TurboQuantBatchRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.turbo_quant.quality(req.vectors, sample_size=req.sample_size)

    @app.post("/v1/turboquant/index/add")
    def turboquant_index_add(req: TurboQuantIndexAddRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.turbo_quant.index_add(req.item_id, req.vector)

    @app.post("/v1/turboquant/index/search")
    def turboquant_index_search(req: TurboQuantIndexSearchRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.turbo_quant.index_search(req.vector, top_k=req.top_k)

    @app.post("/v1/turboquant/index/reset")
    def turboquant_index_reset(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.turbo_quant.reset_index()

    @app.get("/v1/wgrnn/status")
    def wgrnn_status(user_id: str | None = None, agent_id: str | None = None, thread_id: str | None = None, include_slots: bool = False) -> dict[str, Any]:
        return kernel.wgrnn.snapshot(include_slots=include_slots, user_id=user_id, agent_id=agent_id, thread_id=thread_id)

    @app.post("/v1/wgrnn/step")
    def wgrnn_step(req: WGRNNStepRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.wgrnn_step_witnessed(
            prompt=req.prompt,
            response_text=req.response_text,
            requested_action=req.requested_action,
            evidence_quality=req.evidence_quality,
            user_id=req.user_id,
            agent_id=req.agent_id,
            thread_id=req.thread_id,
            tags=req.tags,
        )

    @app.post("/v1/wgrnn/inspect")
    def wgrnn_inspect(req: WGRNNInspectRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        snapshot = kernel.wgrnn.snapshot(include_slots=req.include_slots, user_id=req.user_id, agent_id=req.agent_id, thread_id=req.thread_id)
        slots = kernel.wgrnn.inspect_slots(status=req.status, limit=req.limit)
        return {"snapshot": snapshot, "slots": slots}

    @app.post("/v1/wgrnn/retrieve")
    def wgrnn_retrieve(req: WGRNNRetrieveRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.wgrnn.retrieve(
            req.query,
            top_k=req.top_k,
            include_empty=req.include_empty,
            user_id=req.user_id,
            agent_id=req.agent_id,
            thread_id=req.thread_id,
        )

    @app.post("/v1/wgrnn/promote")
    def wgrnn_promote(req: WGRNNSlotActionRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        try:
            return kernel.wgrnn_promote_witnessed(slot_id=req.slot_id, reason=req.reason, user_id=req.user_id, agent_id=req.agent_id, thread_id=req.thread_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/v1/wgrnn/reject")
    def wgrnn_reject(req: WGRNNSlotActionRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        try:
            return kernel.wgrnn_reject_witnessed(slot_id=req.slot_id, reason=req.reason, user_id=req.user_id, agent_id=req.agent_id, thread_id=req.thread_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/v1/wgrnn/quarantine")
    def wgrnn_quarantine(req: WGRNNSlotActionRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        try:
            return kernel.wgrnn_quarantine_witnessed(slot_id=req.slot_id, reason=req.reason, user_id=req.user_id, agent_id=req.agent_id, thread_id=req.thread_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/v1/wgrnn/ledger")
    def wgrnn_ledger(req: WGRNNLedgerRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.wgrnn.ledger_tail(limit=req.limit, user_id=req.user_id, agent_id=req.agent_id, thread_id=req.thread_id)

    @app.post("/v1/wgrnn/replay-verify")
    def wgrnn_replay_verify(req: WGRNNNamespaceRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.wgrnn_replay_verify_witnessed(user_id=req.user_id, agent_id=req.agent_id, thread_id=req.thread_id)

    @app.get("/v1/moe/status")
    async def moe_status(force: bool = False) -> dict[str, Any]:
        return await kernel.moe_router.status(force=force)

    @app.get("/v1/moe/profiles/{profile_name}/runtime-form")
    def moe_runtime_form(profile_name: str) -> dict[str, Any]:
        try:
            return {"profile": profile_name, "fields": kernel.moe_router.runtime_form_fields(profile_name)}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/v1/moe/route")
    def moe_route(req: MoERouteRequest) -> dict[str, Any]:
        return kernel.moe_router.route(req.capability, tokens_estimate=req.tokens_estimate, allow_experimental=req.allow_experimental)

    @app.post("/v1/models")
    def register_model(req: ModelRegisterRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        record = kernel.model_provider.registry.add(req.model_dump())
        return {"registered": record}

    @app.get("/v1/modules")
    def modules() -> dict[str, Any]:
        return kernel.modules.capability_report()

    @app.get("/v1/modules/{module_id}/health")
    async def module_health(module_id: str) -> dict[str, Any]:
        try:
            return await kernel.modules.health(module_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/v1/corpus/ingest")
    def corpus_ingest(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        docs = __import__("duotronic_runtime.corpus_agent", fromlist=["scan_corpus"]).scan_corpus(settings.corpus_dir)
        count = kernel.store.upsert_corpus_docs(docs)
        validation = kernel.corpus_manager.validate()
        if validation.get("inspection", {}).get("status") == "ok":
            kernel.store.upsert_corpus_version(validation["inspection"]["corpus_ref"], validation, status="candidate")
            kernel.store.insert_witness(validation["witness"])
        return {"documents_ingested": count, "corpus_dir": str(settings.corpus_dir), "validation": validation}

    @app.get("/v1/corpus/inspect")
    def corpus_inspect() -> dict[str, Any]:
        return kernel.corpus_manager.inspect()

    @app.get("/v1/corpus/plan")
    def corpus_plan() -> dict[str, Any]:
        return kernel.corpus_plan()

    @app.get("/v1/policy/explain")
    def policy_explain() -> dict[str, Any]:
        return kernel.policy.explain()

    @app.post("/v1/policy/mode")
    def policy_mode(req: PolicyModeRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.policy.set_mode(
            audit_only=req.audit_only,
            allow_memory_write=req.allow_memory_write,
            allow_promote=req.allow_promote_witness,
        )

    @app.post("/v1/math/positive-baseline/evaluate")
    def positive_baseline_evaluate(req: PositiveBaselineEvaluateRequest) -> dict[str, Any]:
        """Evaluate a polygonal cell package with the mounted Draft 5.3.18 reference evaluator."""
        import hashlib
        import importlib.util
        from pathlib import Path

        source_path = Path(settings.corpus_dir) / "executable" / "runtime" / "positive_baseline.py"
        if not source_path.is_file():
            raise HTTPException(status_code=503, detail={"code": "reference_evaluator_unavailable", "path": str(source_path)})
        import sys

        module_name = "duotronic_positive_baseline_v5318"
        spec = importlib.util.spec_from_file_location(module_name, source_path)
        if spec is None or spec.loader is None:
            raise HTTPException(status_code=503, detail={"code": "reference_evaluator_load_failed"})
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            sys.modules.pop(module_name, None)
            raise HTTPException(
                status_code=503,
                detail={"code": "reference_evaluator_load_failed", "message": str(exc)},
            ) from exc
        try:
            result = module.evaluate_graph(req.package)
        except module.EvaluationError as exc:
            raise HTTPException(status_code=422, detail={"code": exc.code, "message": str(exc)}) from exc
        source_hash = hashlib.shake_256(source_path.read_bytes()).hexdigest(64)
        return {
            "contract_version": "v1.6-draft-5.3.18",
            "evaluator_version": getattr(module, "EVALUATOR_VERSION", "unknown"),
            "source": "mounted-canonical-corpus",
            "source_path": str(source_path),
            "source_shake256_512": f"shake256-512:{source_hash}",
            "result": result,
        }

    @app.get("/v1/formal/status")
    def formal_status() -> dict[str, Any]:
        return kernel.formal.status()

    @app.post("/v1/self-development/plan")
    def self_develop(req: SelfDevelopRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.self_development.plan(task=req.task, repo_ref=req.repo_ref)

    return app
