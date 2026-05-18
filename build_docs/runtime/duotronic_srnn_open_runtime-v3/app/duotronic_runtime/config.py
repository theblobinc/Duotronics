from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def bool_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except Exception:
        return default


def int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except Exception:
        return default


@dataclass(frozen=True)
class Settings:
    app_host: str = os.environ.get("APP_HOST", "0.0.0.0")
    app_port: int = int_env("APP_PORT", 8080)
    app_env: str = os.environ.get("APP_ENV", "sandbox")
    log_level: str = os.environ.get("LOG_LEVEL", "info")

    database_url: str = os.environ.get(
        "DATABASE_URL",
        "postgresql://duotronic:duotronic_dev_password_change_me@postgres:5432/duotronic_runtime",
    )

    node_id: str = os.environ.get("SRNN_NODE_ID", "local-sandbox")
    node_role: str = os.environ.get("SRNN_NODE_ROLE", "coordinator")
    wg_rnn_state_dim: int = int_env("WG_RNN_STATE_DIM", 32)
    wg_rnn_slot_dim: int = int_env("WG_RNN_SLOT_DIM", 32)
    wg_rnn_num_slots: int = int_env("WG_RNN_NUM_SLOTS", 64)
    wg_rnn_runtime_mode: str = os.environ.get("WG_RNN_RUNTIME_MODE", "sandbox")

    nla_policy_mode: str = os.environ.get("NLA_POLICY_MODE", "audit_only")
    nla_min_cosine: float = float_env("NLA_MIN_COSINE", 0.82)
    nla_max_mse: float = float_env("NLA_MAX_MSE", 0.25)
    nla_min_repeat_stability: float = float_env("NLA_MIN_REPEAT_STABILITY", 0.70)
    nla_allow_influence_response: bool = bool_env("NLA_ALLOW_INFLUENCE_RESPONSE", False)
    nla_allow_memory_write: bool = bool_env("NLA_ALLOW_MEMORY_WRITE", False)
    nla_allow_promote_witness: bool = bool_env("NLA_ALLOW_PROMOTE_WITNESS", False)

    milvus_enabled: bool = bool_env("MILVUS_ENABLED", False)
    milvus_host: str = os.environ.get("MILVUS_HOST", "milvus")
    milvus_port: int = int_env("MILVUS_PORT", 19530)
    milvus_collection: str = os.environ.get("MILVUS_COLLECTION", "duotronic_witness_vectors")

    ollama_enabled: bool = bool_env("OLLAMA_ENABLED", False)
    ollama_host: str = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
    ollama_default_model: str = os.environ.get("OLLAMA_DEFAULT_MODEL", "llama3.2:1b")
    ollama_timeout_seconds: float = float_env("OLLAMA_TIMEOUT_SECONDS", 180.0)

    llama_cpp_enabled: bool = bool_env("LLAMA_CPP_ENABLED", False)
    llama_cpp_base_url: str = os.environ.get("LLAMA_CPP_BASE_URL", "http://llama-cpp:8080/v1")
    llama_cpp_default_model: str = os.environ.get("LLAMA_CPP_DEFAULT_MODEL", "local-gguf")
    llama_cpp_timeout_seconds: float = float_env("LLAMA_CPP_TIMEOUT_SECONDS", 180.0)

    corpus_dir: Path = Path(os.environ.get("CORPUS_DIR", "/runtime/corpus"))
    corpus_autoindex: bool = bool_env("CORPUS_AUTOINDEX", True)
    runtime_data_dir: Path = Path(os.environ.get("RUNTIME_DATA_DIR", "/runtime/data"))
    model_registry_path: Path = Path(os.environ.get("MODEL_REGISTRY_PATH", "/runtime/config/models.json"))
    model_orchestrator_path: Path = Path(os.environ.get("MODEL_ORCHESTRATOR_PATH", "/runtime/config/model_orchestrator.json"))
    module_registry_path: Path = Path(os.environ.get("MODULE_REGISTRY_PATH", "/runtime/config/modules.json"))
    policy_pack_path: Path = Path(os.environ.get("POLICY_PACK_PATH", "/runtime/config/policy_pack.json"))

    runtime_api_key: str = os.environ.get("RUNTIME_API_KEY", "")

    xavi_mcp_enabled: bool = bool_env("XAVI_MCP_ENABLED", False)
    xavi_mcp_api_key: str = os.environ.get("XAVI_MCP_API_KEY", "")

    xavi_mcp_repo_tools_enabled: bool = bool_env("XAVI_MCP_REPO_TOOLS_ENABLED", False)
    xavi_repo_root: Path = Path(os.environ.get("XAVI_REPO_ROOT", "/workspace/Duotronics"))
    xavi_worktree_root: Path = Path(os.environ.get("XAVI_WORKTREE_ROOT", "/runtime/data/worktrees"))
    xavi_repo_approval_secret: str = os.environ.get("XAVI_REPO_APPROVAL_SECRET", "")

    xavi_ops_enabled: bool = bool_env("XAVI_OPS_ENABLED", False)
    xavi_ops_url: str = os.environ.get("XAVI_OPS_URL", "http://host.containers.internal:8091")
    xavi_ops_api_key: str = os.environ.get("XAVI_OPS_API_KEY", "")

    xavi_search_url: str = os.environ.get("XAVI_SEARCH_URL", os.environ.get("SEARCH_API_URL", ""))
    xavi_search_api_key: str = os.environ.get("XAVI_SEARCH_API_KEY", os.environ.get("SEARCH_API_KEY", ""))
    stable_diffusion_url: str = os.environ.get("STABLE_DIFFUSION_URL", os.environ.get("IMAGE_GENERATION_URL", ""))
    code_interpreter_enabled: bool = bool_env("CODE_INTERPRETER_ENABLED", True)
    tools_enabled: bool = bool_env("XAVI_TOOLS_ENABLED", True)


def get_settings() -> Settings:
    return Settings()
