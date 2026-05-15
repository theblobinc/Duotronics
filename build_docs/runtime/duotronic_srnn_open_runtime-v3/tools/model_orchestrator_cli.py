#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from duotronic_runtime.model_orchestrator import ModelOrchestrator  # noqa: E402


def _records_from_runtime_models_file(path: str) -> list[dict[str, Any]]:
    if not path or not Path(path).exists():
        return []
    data = json.loads(Path(path).read_text())
    if isinstance(data, dict):
        items = data.get("items", [])
    elif isinstance(data, list):
        items = data
    else:
        items = []
    return [item for item in items if isinstance(item, dict)]


def _records_from_ollama_tags_data(data: Any, source: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    if isinstance(data, dict) and "models" in data:
        models = data.get("models", [])
    elif isinstance(data, dict):
        # Support the MCP inventory shape: {"11434": {"models": [...]}, ...}
        models = []
        for port, payload in data.items():
            if isinstance(payload, dict):
                for item in payload.get("models", []) or []:
                    if isinstance(item, dict):
                        item = dict(item)
                        item.setdefault("source_port", str(port))
                        models.append(item)
    elif isinstance(data, list):
        models = data
    else:
        models = []

    for item in models:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("model")
        model = item.get("model") or name
        if not name and not model:
            continue
        records.append({
            "name": f"ollama:{name}",
            "model": model,
            "provider": "ollama",
            "enabled": True,
            "discovered": True,
            "inventory_source": source,
            "details": item.get("details", {}),
        })
    return records


def _records_from_ollama_tags_file(path: str) -> list[dict[str, Any]]:
    if not path or not Path(path).exists():
        return []
    return _records_from_ollama_tags_data(json.loads(Path(path).read_text()), f"file:{path}")


def _records_from_ollama_url(url: str) -> list[dict[str, Any]]:
    if not url:
        return []
    base = url.rstrip("/")
    tags_url = base if base.endswith("/api/tags") else f"{base}/api/tags"
    with urllib.request.urlopen(tags_url, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))
    return _records_from_ollama_tags_data(data, tags_url)


def load_runtime_records(args: argparse.Namespace) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    records.extend(_records_from_runtime_models_file(args.runtime_models))
    records.extend(_records_from_ollama_tags_file(args.ollama_tags))
    for url in args.ollama_url or []:
        records.extend(_records_from_ollama_url(url))
    return records


def load_orchestrator(args: argparse.Namespace) -> ModelOrchestrator:
    return ModelOrchestrator(Path(args.manifest), runtime_models=load_runtime_records(args))


def cmd_catalog(args: argparse.Namespace) -> int:
    orch = load_orchestrator(args)
    data = orch.catalog()
    if args.json:
        print(json.dumps(data, indent=2))
        return 0
    print(f"manifest: {data.get('manifest_path')}")
    print(f"models: {len(data.get('models', []))}")
    for model in data.get("models", []):
        installed = "installed" if model.get("installed") else "missing"
        desired = "desired" if model.get("desired") else "optional"
        caps = ",".join(model.get("capabilities", []))
        print(f"- {model['id']} [{model.get('tier')}] {installed} {desired} caps={caps}")
    return 0


def _pull_command(args: argparse.Namespace, tag: str) -> str:
    if args.pull_command_style == "ollama":
        return f"ollama pull {tag}"
    pull_url = args.pull_url.rstrip("/")
    if not pull_url.endswith("/api/pull"):
        pull_url = f"{pull_url}/api/pull"
    payload = json.dumps({"name": tag})
    return f"curl -fsS {pull_url} -H 'Content-Type: application/json' -d '{payload}'"


def cmd_download_plan(args: argparse.Namespace) -> int:
    orch = load_orchestrator(args)
    catalog = orch.catalog()
    missing = [m for m in catalog.get("models", []) if m.get("desired") and not m.get("installed")]
    installed = [m for m in catalog.get("models", []) if m.get("desired") and m.get("installed")]
    if args.json:
        print(json.dumps({"installed_desired": installed, "missing_desired": missing}, indent=2))
        return 0
    if installed:
        print("# Desired models already present in the supplied runtime/Ollama inventory")
        for model in installed:
            tag = model.get("storage", {}).get("ollama_tag") or model.get("id")
            print(f"# installed: {tag}")
        print()
    if not missing:
        print("All desired Ollama-tagged models in the manifest appear installed in the supplied inventory.")
        return 0
    print("# Missing desired model pull commands")
    if args.pull_command_style == "http":
        print(f"# Using Ollama HTTP pull endpoint: {args.pull_url.rstrip('/')}/api/pull")
        print("# On tbi-production-4, prefer --pull-url http://127.0.0.1:11436 for the local duotronic-ollama container.")
    for model in missing:
        tag = model.get("storage", {}).get("ollama_tag") or model.get("id")
        if tag:
            print(_pull_command(args, tag))
    return 0


def cmd_route_preview(args: argparse.Namespace) -> int:
    orch = load_orchestrator(args)
    data = orch.route_preview({
        "task": args.task,
        "capability": args.capability,
        "tokens_estimate": args.tokens_estimate,
        "needs_tools": args.needs_tools,
        "needs_vision": args.needs_vision,
        "prefer_backend": args.prefer_backend,
        "allow_experimental": args.allow_experimental,
        "slow_mode": args.slow_mode,
    })
    print(json.dumps(data, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Model orchestrator catalog/route helper")
    parser.add_argument("--manifest", default=str(ROOT / "config" / "model_orchestrator.json"))
    parser.add_argument("--runtime-models", default="", help="Optional JSON file from /v1/models")
    parser.add_argument("--ollama-tags", default="", help="Optional JSON file from Ollama /api/tags or MCP inventory")
    parser.add_argument("--ollama-url", action="append", default=[], help="Optional Ollama base URL; may be passed more than once, e.g. --ollama-url http://127.0.0.1:11434 --ollama-url http://127.0.0.1:11436")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--pull-command-style", choices=["http", "ollama"], default="http")
    parser.add_argument("--pull-url", default="http://127.0.0.1:11436", help="Ollama HTTP base URL or /api/pull URL used when printing download-plan commands")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("catalog")
    sub.add_parser("download-plan")

    route = sub.add_parser("route-preview")
    route.add_argument("--task", default="small_chat")
    route.add_argument("--capability", default=None)
    route.add_argument("--tokens-estimate", type=int, default=2048)
    route.add_argument("--needs-tools", action="store_true")
    route.add_argument("--needs-vision", action="store_true")
    route.add_argument("--prefer-backend", default=None)
    route.add_argument("--allow-experimental", action="store_true")
    route.add_argument("--slow-mode", action="store_true")

    args = parser.parse_args()
    if args.cmd == "catalog":
        return cmd_catalog(args)
    if args.cmd == "download-plan":
        return cmd_download_plan(args)
    if args.cmd == "route-preview":
        return cmd_route_preview(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
