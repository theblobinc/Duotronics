#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import json

V3 = Path("/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3")
MODELS = V3 / "config/models.json"

ALIASES = [
    ("xavi-vscode-fast", "qwen2.5-coder:1.5b", "http://ollama:11434", "local_fast", "selection_explain,small_edit,fallback"),
    ("xavi-vscode-balanced", "qwen2.5-coder:3b", "http://ollama:11434", "local_balanced", "single_file_edit,code_review,chat"),
    ("xavi-vscode-agent", "qwen2.5-coder:xavi-agent", "http://host.containers.internal:11434", "gpu_mesh", "multi_file_edit,agent_chat,refactor"),
    ("xavi-vscode-deep", "qwen2.5-coder:7b", "http://host.containers.internal:11434", "remote_gpu_or_cpu", "repo_reasoning,architecture,long_context_planning"),
    ("xavi-vscode-copilot", "xavi-copilot-agent:latest", "http://host.containers.internal:11434", "gpu_mesh", "copilot_chat,custom_xavi_behavior,tool_augmented_agent"),
]

data = json.loads(MODELS.read_text())
models = data.setdefault("models", [])
backup = MODELS.with_name(MODELS.name + ".backup-mcp-" + datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"))
backup.write_text(MODELS.read_text())

def upsert(record):
    for i, item in enumerate(models):
        if item.get("name") == record["name"]:
            models[i] = record
            return
    models.append(record)

for name, model, base_url, tier, recommended in ALIASES:
    upsert({"name": name, "provider": "ollama", "model": model, "base_url": base_url, "enabled_env": "OLLAMA_ENABLED", "default": False, "description": f"VS Code model alias for {name}.", "metadata": {"xavi_role": name.replace("xavi-", "").replace("-", "_"), "hardware_tier": tier, "recommended_for": recommended.split(",")}})
MODELS.write_text(json.dumps(data, indent=2) + "\n")
print(json.dumps({"ok": True, "path": str(MODELS), "backup": str(backup), "aliases": [{"name": name, "model": model, "base_url": base_url} for name, model, base_url, _, _ in ALIASES]}, indent=2))
