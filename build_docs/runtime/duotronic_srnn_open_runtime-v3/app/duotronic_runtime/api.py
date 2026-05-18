from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import Settings, get_settings
from .runtime_kernel import RuntimeKernel
from .http_mcp import register_xavi_runtime_mcp
from .mcp_protocol import register_real_mcp_protocol
from .actions_api import register_xavi_runtime_actions
from .providers import complete_ollama_generate, stream_ollama_generate
from .tool_services import ToolRuntime


class RunRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    steps: int = Field(default=1, ge=1, le=16)
    requested_action: str = "observe"
    model_name: str | None = None
    evidence_quality: float = Field(default=0.72, ge=0.0, le=1.0)


class ChatMessage(BaseModel):
    role: str
    content: Any = ""


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage] = Field(default_factory=list)
    prompt: str | None = None
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = Field(default=None, ge=1, le=32768)
    stream: bool = False
    show_reasoning: bool = True


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


class SelfDevelopRequest(BaseModel):
    task: str = Field(..., min_length=1)
    repo_ref: str = "mounted-workspace"


class CodeExecuteRequest(BaseModel):
    language: str = "python"
    code: str = Field(..., min_length=1, max_length=200000)
    timeout_seconds: int = Field(default=30, ge=1, le=60)
    stdin: str = ""


class SearchEvidenceRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)
    engine: str = "xavi"


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


def _message_content_to_text(content: Any) -> str:
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(str(item.get("text", "")))
            elif isinstance(item, str):
                text_parts.append(item)
        return "\n".join(text_parts)
    return str(content or "")


def _messages_to_prompt(messages: list[ChatMessage], prompt: str | None = None) -> str:
    if prompt:
        return prompt
    parts: list[str] = []
    for msg in messages:
        content_text = _message_content_to_text(msg.content)
        if content_text:
            parts.append(f"{msg.role}: {content_text}")
    return "\n".join(parts).strip()


def _messages_for_ollama_chat(messages: list[ChatMessage], prompt: str | None = None) -> list[dict[str, str]]:
    formatting_guard = (
        "You are a helpful assistant in a chat UI. Answer the user's question directly. "
        "Use normal spaces between words and clean Markdown. Do not output runtime policy, "
        "evidence labels, audit labels, source-code placeholders, file paths, or template text "
        "unless the user explicitly asks for them."
    )
    out: list[dict[str, str]] = [{"role": "system", "content": formatting_guard}]
    if prompt:
        out.append({"role": "user", "content": prompt})
        return out
    for msg in messages:
        role = msg.role if msg.role in {"system", "user", "assistant", "tool"} else "user"
        content_text = _message_content_to_text(msg.content).strip()
        if not content_text:
            continue
        if role == "system":
            # Preserve caller system guidance while keeping our UI formatting guard first.
            out.append({"role": "system", "content": content_text})
        elif role == "tool":
            out.append({"role": "user", "content": content_text})
        else:
            out.append({"role": role, "content": content_text})
    if len(out) == 1:
        out.append({"role": "user", "content": ""})
    return out


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
    if provider_result.get("tool_calls"):
        message["tool_calls"] = provider_result["tool_calls"]
    metrics = provider_result.get("provider_metrics") or {}
    eval_count = metrics.get("eval_count") or 0
    prompt_count = metrics.get("prompt_eval_count") or 0
    return {
        "id": "chatcmpl-" + uuid.uuid4().hex,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model or provider_result.get("model", {}).get("name") or "unknown",
        "choices": [{"index": 0, "message": message, "finish_reason": metrics.get("done_reason") or "stop"}],
        "usage": {"prompt_tokens": int(prompt_count or 0), "completion_tokens": int(eval_count or 0), "total_tokens": int((prompt_count or 0) + (eval_count or 0))},
        "xavi": {"provider_status": provider_result.get("provider_status"), "capabilities_observed": provider_result.get("capabilities_observed", {}), "provider_metrics": metrics},
    }


def create_app() -> FastAPI:
    settings = get_settings()
    kernel = RuntimeKernel(settings)

    app = FastAPI(title="Duotronic SRNN Runtime Host", version="0.2.0", openapi_url="/fastapi/openapi.json")
    static_dir = __import__("pathlib").Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    register_xavi_runtime_mcp(app, kernel, settings)
    register_real_mcp_protocol(app, kernel, settings)
    register_xavi_runtime_actions(app, kernel, settings)
    tools_runtime = ToolRuntime(settings=settings, kernel=kernel)

    @app.on_event("startup")
    def startup() -> None:
        kernel.migrate()
        if settings.corpus_autoindex:
            docs = __import__("duotronic_runtime.corpus_agent", fromlist=["scan_corpus"]).scan_corpus(settings.corpus_dir)
            if docs:
                kernel.store.upsert_corpus_docs(docs)
            validation = kernel.corpus_manager.validate()
            if validation.get("inspection", {}).get("status") == "ok":
                kernel.store.upsert_corpus_version(validation["inspection"]["corpus_ref"], validation, status="candidate")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(str(static_dir / "index.html"))

    @app.get("/health")
    def health() -> dict[str, Any]:
        return kernel.health()

    @app.get("/v1/capabilities")
    def runtime_capabilities(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return tools_runtime.capability_report(models=kernel.model_provider.registry.list_models())

    @app.get("/v1/client-profiles")
    def client_route_profiles(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        from .client_profiles import client_profiles

        return {"schema_version": "client-profiles-v1", "profiles": client_profiles()}

    @app.post("/v1/inference/route")
    def inference_route(req: InferenceRouteRequestModel, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        from .inference_router import plan_inference_route

        report = tools_runtime.capability_report(models=kernel.model_provider.registry.list_models())
        return plan_inference_route(report, req.model_dump())

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
            requested_action = "memory_write" if mode == "memory" else "observe"
            wgrnn_result = kernel.wgrnn.step(prompt=prompt, response_text="", requested_action=requested_action, evidence_quality=0.72)
            text = f"WG-RNN {mode} step completed. trust_status={wgrnn_result['memory_update']['trust_status']}; authority={wgrnn_result['memory_update']['authority_t']}; slot={wgrnn_result['memory_update']['slot_id']}."
            yield _sse({"id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": model_name, "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}], "wgrnn": wgrnn_result})
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
    async def chat_completions(req: ChatCompletionRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        prompt = _messages_to_prompt(req.messages, req.prompt)
        if not prompt:
            raise HTTPException(status_code=422, detail="messages or prompt required")
        if req.stream:
            return StreamingResponse(_stream_chat_completions(req, prompt), media_type="text/event-stream")
        if req.model and req.model.startswith("wg-rnn:"):
            mode = req.model.split(":", 1)[1] if ":" in req.model else "runtime"
            requested_action = "memory_write" if mode == "memory" else "observe"
            wgrnn_result = kernel.wgrnn.step(
                prompt=prompt,
                response_text="",
                requested_action=requested_action,
                evidence_quality=0.72,
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
            return _openai_chat_response(req, provider_result) | {"wgrnn": wgrnn_result}
        try:
            model_record = kernel.model_provider.registry.get(req.model)
            if model_record.get("provider") == "ollama":
                provider_result = await complete_ollama_generate(
                    settings,
                    prompt=prompt,
                    model=model_record,
                    messages=_messages_for_ollama_chat(req.messages, req.prompt),
                )
            else:
                provider_result = await kernel.model_provider.complete(prompt=prompt, model_name=req.model)
        except RuntimeError as exc:
            message = str(exc)
            if "timeout" in message:
                raise HTTPException(status_code=504, detail={"error": "model_provider_timeout", "message": message}) from exc
            if "ollama_" in message or "llama_cpp_" in message:
                raise HTTPException(status_code=502, detail={"error": "model_provider_error", "message": message}) from exc
            raise
        return _openai_chat_response(req, provider_result)

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
            "capabilities": ["code_interpreter", "image_generation", "xavi_search_evidence"],
        }

    @app.post("/v1/tools/code/execute")
    async def code_execute(req: CodeExecuteRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        if not settings.code_interpreter_enabled:
            raise HTTPException(status_code=503, detail="code_interpreter_disabled")
        return await tools_runtime.code_execute(language=req.language, code=req.code, timeout_seconds=req.timeout_seconds, stdin=req.stdin)

    @app.post("/v1/tools/search/xavi")
    async def search_xavi(req: SearchEvidenceRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return await tools_runtime.search_xavi(query=req.query, top_k=req.top_k, engine=req.engine)

    @app.post("/v1/tools/search/evidence")
    async def search_evidence(req: SearchEvidenceRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return await tools_runtime.search_xavi(query=req.query, top_k=req.top_k, engine=req.engine)

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

    @app.post("/v1/evidence/claims")
    def submit_claim(req: EvidenceClaimRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.submit_claim(req.model_dump())

    @app.get("/v1/evidence/claims")
    def evidence_claims(limit: int = 20) -> dict[str, Any]:
        return {"items": kernel.store.fetch_recent("evidence_claims", limit)}

    @app.get("/v1/memory")
    def memory(limit: int = 20) -> dict[str, Any]:
        return {"items": kernel.store.fetch_recent("memory_cells", limit)}

    @app.get("/v1/audit")
    def audit(limit: int = 20) -> dict[str, Any]:
        return {"items": kernel.store.fetch_recent("audit_events", limit)}

    @app.get("/v1/models")
    def models() -> dict[str, Any]:
        models = kernel.model_provider.registry.list_openai_chat_models()
        data: list[dict[str, Any]] = []
        seen: set[str] = set()
        for model in models:
            if not model.get("enabled", True):
                continue
            model_id = str(model.get("name") or model.get("model") or "").strip()
            if not model_id or model_id in seen:
                continue
            seen.add(model_id)
            data.append(
                {
                    "id": model_id,
                    "object": "model",
                    "created": 0,
                    "owned_by": str(model.get("provider") or "xavi"),
                    "permission": [],
                    "root": str(model.get("model") or model_id),
                    "parent": None,
                }
            )
            if model_id.startswith("ollama:"):
                raw_id = model_id.removeprefix("ollama:")
                if raw_id and raw_id not in seen:
                    seen.add(raw_id)
                    data.append(
                        {
                            "id": raw_id,
                            "object": "model",
                            "created": 0,
                            "owned_by": "ollama",
                            "permission": [],
                            "root": raw_id,
                            "parent": model_id,
                        }
                    )
        return {"object": "list", "data": data}

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

    @app.get("/v1/formal/status")
    def formal_status() -> dict[str, Any]:
        return kernel.formal.status()

    @app.post("/v1/self-development/plan")
    def self_develop(req: SelfDevelopRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.self_development.plan(task=req.task, repo_ref=req.repo_ref)

    return app
