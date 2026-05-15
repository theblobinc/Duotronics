from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any

import httpx

from .api import create_app
from .config import get_settings
from .corpus_agent import build_agentic_plan, scan_corpus
from .db import Store
from .runtime_kernel import RuntimeKernel


def emit(obj: Any) -> None:
    print(json.dumps(obj, indent=2, default=str))


async def http_health(url: str) -> int:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(url.rstrip("/") + "/health")
            emit(r.json())
            return 0 if r.status_code == 200 else 1
    except Exception as exc:
        emit({"error": str(exc)})
        return 1


async def http_run(url: str, prompt: str, action: str, steps: int) -> int:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url.rstrip("/") + "/v1/run", json={"prompt": prompt, "requested_action": action, "steps": steps})
        emit(r.json())
        return 0 if r.status_code < 400 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="duotronic-runtime")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_health = sub.add_parser("health")
    p_health.add_argument("--url", default="http://127.0.0.1:8080")

    p_migrate = sub.add_parser("migrate")

    p_run = sub.add_parser("run")
    p_run.add_argument("prompt")
    p_run.add_argument("--url", default="http://127.0.0.1:8080")
    p_run.add_argument("--action", default="observe")
    p_run.add_argument("--steps", type=int, default=1)

    p_corpus = sub.add_parser("corpus-plan")
    p_inspect = sub.add_parser("corpus-inspect")
    p_modules = sub.add_parser("modules")
    p_formal = sub.add_parser("formal-status")
    p_self = sub.add_parser("self-development-plan")
    p_self.add_argument("task")

    args = parser.parse_args(argv)
    settings = get_settings()
    if args.cmd == "health":
        return asyncio.run(http_health(args.url))
    if args.cmd == "migrate":
        Store(settings).migrate()
        emit({"migrated": True, "database_url": "configured"})
        return 0
    if args.cmd == "run":
        return asyncio.run(http_run(args.url, args.prompt, args.action, args.steps))
    if args.cmd == "corpus-plan":
        emit(RuntimeKernel(settings).corpus_plan())
        return 0
    if args.cmd == "corpus-inspect":
        emit(RuntimeKernel(settings).corpus_manager.inspect())
        return 0
    if args.cmd == "modules":
        emit(RuntimeKernel(settings).modules.capability_report())
        return 0
    if args.cmd == "formal-status":
        emit(RuntimeKernel(settings).formal.status())
        return 0
    if args.cmd == "self-development-plan":
        emit(RuntimeKernel(settings).self_development.plan(args.task))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
