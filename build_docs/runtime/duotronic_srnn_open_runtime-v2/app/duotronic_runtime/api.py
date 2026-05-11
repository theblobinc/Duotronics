from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import Settings, get_settings
from .runtime_kernel import RuntimeKernel
from .http_mcp import register_xavi_runtime_mcp
from .mcp_protocol import register_real_mcp_protocol
from .actions_api import register_xavi_runtime_actions


class RunRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    steps: int = Field(default=1, ge=1, le=16)
    requested_action: str = "observe"
    model_name: str | None = None
    evidence_quality: float = Field(default=0.72, ge=0.0, le=1.0)


class ModelRegisterRequest(BaseModel):
    name: str
    provider: str
    model: str | None = None
    base_url: str | None = None
    default: bool = False
    enabled: bool = True
    description: str = ""


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


def require_api_key(settings: Settings, authorization: str | None) -> None:
    if not settings.runtime_api_key:
        return
    expected = f"Bearer {settings.runtime_api_key}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="missing or invalid bearer token")


def create_app() -> FastAPI:
    settings = get_settings()
    kernel = RuntimeKernel(settings)

    app = FastAPI(title="Duotronic SRNN Runtime Host", version="0.2.0", openapi_url="/fastapi/openapi.json")
    static_dir = __import__("pathlib").Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    register_xavi_runtime_mcp(app, kernel, settings)
    register_real_mcp_protocol(app, kernel, settings)
    register_xavi_runtime_actions(app, kernel, settings)

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
        kernel.migrate()
        return kernel.health()

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
        return {"items": kernel.model_provider.registry.list_models()}

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

    @app.get("/v1/formal/status")
    def formal_status() -> dict[str, Any]:
        return kernel.formal.status()

    @app.post("/v1/self-development/plan")
    def self_develop(req: SelfDevelopRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_api_key(settings, authorization)
        return kernel.self_development.plan(task=req.task, repo_ref=req.repo_ref)

    return app
