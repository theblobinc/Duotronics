#!/usr/bin/env python3
"""Rootless-Podman paired corpus/runtime lab, executed only inside the VM."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HARNESS = Path("/srv/duotronic-harness")
RUN_ROOT = Path("/srv/duotronic-runs")
ACTIVATION_IMAGE = "localhost/duotronic-wc-activation-harness:5.3.17"
RUN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def capture(argv: list[str], *, timeout: int, cwd: Path | None = None) -> dict[str, Any]:
    try:
        result = subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        return {"argv": argv, "exit_code": result.returncode, "stdout": result.stdout[-30000:], "stderr": result.stderr[-30000:]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"argv": argv, "exit_code": 127, "stdout": "", "stderr": str(exc)}


def compose(path: Path, project: str, *args: str, timeout: int) -> dict[str, Any]:
    return capture(["podman", "--remote=false", "compose", "-f", str(path), "-p", project, *args], timeout=timeout, cwd=path.parent)


def confined_run(run_id: str) -> Path:
    if not RUN_RE.fullmatch(run_id):
        raise ValueError("invalid paired-lab run id")
    root = RUN_ROOT.resolve()
    run = (root / run_id).resolve()
    if run.parent != root:
        raise ValueError("paired-lab run escaped root")
    return run


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def materializer_compose(run: Path, output: Path, proposal: Path | None) -> Path:
    command = [
        "materialize", "--parent-corpus", "/inputs/corpus", "--parent-runtime", "/inputs/runtime",
        "--output", "/output/pair", "--policy", "/policy/paired_candidate_policy_v1.json",
        "--external-data", "/inputs/external",
    ]
    volumes = [
        f"{run / 'corpus'}:/inputs/corpus:ro",
        f"{run / 'runtime-parent'}:/inputs/runtime:ro",
        f"{run / 'external-data'}:/inputs/external:ro",
        f"{output}:/output:rw",
        f"{HARNESS}:/policy:ro",
    ]
    if proposal:
        command.extend(["--proposal", "/proposal/proposal.json"])
        volumes.append(f"{proposal.parent}:/proposal:ro")
    document = {
        "version": "3.8",
        "networks": {"pair-isolated": {"internal": True}},
        "services": {
            "paired-materializer": {
                "image": ACTIVATION_IMAGE,
                "entrypoint": ["python3", "/opt/harness/paired_candidate.py"],
                "command": command,
                "networks": ["pair-isolated"],
                "read_only": True,
                "user": f"{os.geteuid()}:{os.getegid()}",
                "userns_mode": "keep-id",
                "cap_drop": ["ALL"],
                "security_opt": ["no-new-privileges"],
                "pids_limit": 256,
                "mem_limit": "2g",
                "cpus": 3,
                "tmpfs": ["/tmp:rw,noexec,nosuid,nodev,size=256m"],
                "volumes": volumes,
                "restart": "no",
            }
        },
    }
    path = run / "guest" / "compose.paired-materializer.json"
    write_json(path, document)
    return path


def runtime_compose(pair: Path, image: str) -> Path:
    runtime = pair / "runtime-candidate"
    corpus = pair / "corpus-candidate"
    config = pair / "sandbox-config"
    pair_manifest = json.loads((pair / "paired-candidate.json").read_text(encoding="utf-8"))
    binding = json.loads((runtime / "config/paired_binding.json").read_text(encoding="utf-8"))
    runtime_data = pair.parent / "runtime-data"
    runtime_data.mkdir(mode=0o700, exist_ok=False)
    if config.exists():
        shutil.rmtree(config)
    shutil.copytree(runtime / "config", config, dirs_exist_ok=True)
    write_json(config / "active_witness_contract.json", {
        "schema": "duotronic-active-witness-contract/v1",
        "directory_name": corpus.name,
        "authority_profile": "sandbox-test-only",
        "authority_namespace": "duotronic://authority/sandbox/witness-harness-vm",
        "production_eligible": False,
        "activated_at": now(),
    })
    document = {
        "version": "3.8",
        "networks": {"runtime-isolated": {"internal": True}},
        "services": {
            "postgres": {
                "image": "docker.io/library/postgres:16-alpine",
                "environment": {"POSTGRES_USER": "duotronic_sandbox", "POSTGRES_PASSWORD": "duotronic_sandbox_ephemeral", "POSTGRES_DB": "duotronic_sandbox"},
                "networks": ["runtime-isolated"],
                "tmpfs": ["/var/lib/postgresql/data:rw,nosuid,nodev,size=1024m"],
                "healthcheck": {"test": ["CMD-SHELL", "pg_isready -U duotronic_sandbox -d duotronic_sandbox"], "interval": "3s", "timeout": "3s", "retries": 30},
                "restart": "no",
            },
            "redis": {
                "image": "docker.io/library/redis:7-alpine",
                "command": ["redis-server", "--save", "", "--appendonly", "no"],
                "networks": ["runtime-isolated"], "tmpfs": ["/data:rw,nosuid,nodev,size=256m"], "restart": "no",
            },
            "runtime-candidate": {
                "build": {"context": str(runtime), "dockerfile": "Containerfile"},
                "image": image,
                "read_only": True,
                "userns_mode": "keep-id",
                "cap_drop": ["ALL"], "security_opt": ["no-new-privileges"],
                "pids_limit": 512, "mem_limit": "4g", "cpus": 4,
                "tmpfs": ["/tmp:rw,noexec,nosuid,nodev,size=256m"],
                "environment": {
                    "APP_ENV": "sandbox", "DATABASE_URL": "postgresql://duotronic_sandbox:duotronic_sandbox_ephemeral@postgres:5432/duotronic_sandbox",
                    "CORPUS_DIR": "/runtime/corpus", "CORPUS_HISTORY_DIR": "/runtime/corpus-history",
                    "ACTIVE_WITNESS_CONTRACT_STATE": "/runtime/config/active_witness_contract.json", "RUNTIME_DATA_DIR": "/runtime/data",
                    "WG_RNN_RUNTIME_MODE": "sandbox", "NLA_POLICY_MODE": "audit_only",
                    "DUOTRONIC_PAIR_ID": str(pair_manifest["pair_id"]),
                    "DUOTRONIC_CORPUS_ROOT_ID": str(binding["corpus_root_id"]),
                    "DUOTRONIC_CRYPTO_PROFILE": str(binding["cryptographic_profile"]),
                    "DUOTRONIC_PROFILE_REGISTRY_ID": str(binding["profile_registry_id"]),
                    "DUOTRONIC_BINDING_ID": str(binding["binding_id"]),
                    "NLA_ALLOW_INFLUENCE_RESPONSE": "0", "NLA_ALLOW_MEMORY_WRITE": "0", "NLA_ALLOW_PROMOTE_WITNESS": "0",
                    "OLLAMA_ENABLED": "0", "LLAMA_CPP_ENABLED": "0", "MILVUS_ENABLED": "0",
                    "XAVI_MCP_ENABLED": "0", "XAVI_MCP_REPO_TOOLS_ENABLED": "0", "XAVI_OPS_ENABLED": "0",
                    "CODE_INTERPRETER_ENABLED": "0", "XAVI_TOOLS_ENABLED": "0",
                },
                "volumes": [f"{corpus}:/runtime/corpus:ro", f"{pair}:/runtime/corpus-history:ro", f"{config}:/runtime/config:ro", f"{runtime_data}:/runtime/data:rw"],
                "depends_on": {"postgres": {"condition": "service_healthy"}, "redis": {"condition": "service_started"}},
                "networks": ["runtime-isolated"],
                "restart": "no",
            },
        },
    }
    path = pair.parent / "compose.runtime-candidate.json"
    write_json(path, document)
    return path


def container_id(project: str) -> str:
    result = capture(["podman", "--remote=false", "ps", "-q", "--filter", f"label=io.podman.compose.project={project}", "--filter", "label=com.docker.compose.service=runtime-candidate"], timeout=30)
    if result["exit_code"] != 0 or not result["stdout"].strip():
        raise RuntimeError("runtime candidate container was not found")
    return result["stdout"].splitlines()[0].strip()


def wait_health(cid: str, timeout: int) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        state = capture(["podman", "--remote=false", "inspect", "--format", "{{.State.Status}}", cid], timeout=20)
        if state.get("stdout", "").strip() != "running":
            return {**state, "exit_code": 125, "stderr": "runtime candidate stopped before health"}
        last = exec_json(cid, "GET", "/health")
        if last.get("exit_code") == 0:
            return last
        time.sleep(3)
    return {**last, "exit_code": 124, "stderr": "runtime candidate health timeout"}


def exec_json(cid: str, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    script = "import json,urllib.request;"
    if payload is None:
        script += f"r=urllib.request.urlopen('http://127.0.0.1:8080{path}',timeout=15);print(r.read().decode())"
    else:
        encoded = json.dumps(payload, separators=(",", ":"))
        script += f"d={encoded!r}.encode();q=urllib.request.Request('http://127.0.0.1:8080{path}',data=d,headers={{'Content-Type':'application/json'}},method={method!r});r=urllib.request.urlopen(q,timeout=30);print(r.read().decode())"
    return capture(["podman", "--remote=false", "exec", cid, "python", "-c", script], timeout=60)


def run_cycle(args: argparse.Namespace) -> int:
    run = confined_run(args.run_id)
    required = [run / "corpus", run / "runtime-parent", run / "external-data", run / "guest"]
    for path in required:
        if not path.is_dir():
            raise FileNotFoundError(path)
    output = run / "paired-output"
    output.mkdir(parents=True, exist_ok=False)
    proposal = run / "proposal" / "proposal.json"
    if not proposal.is_file():
        proposal = None
    materializer = materializer_compose(run, output, proposal)
    materializer_project = "duotronic-pair-materialize-" + re.sub(r"[^a-z0-9]", "", args.run_id.lower())[-20:]
    mat_up = compose(materializer, materializer_project, "up", "--abort-on-container-exit", "--exit-code-from", "paired-materializer", timeout=args.timeout)
    mat_down = compose(materializer, materializer_project, "down", timeout=180)
    pair = output / "pair"
    if mat_up["exit_code"] != 0 or mat_down["exit_code"] != 0 or not (pair / "paired-candidate.json").is_file():
        report = {"schema": "duotronic-paired-vm-cycle/v1", "state": "blocked", "phase": "materialize", "materializer_up": mat_up, "materializer_down": mat_down, "production_eligible": False}
        write_json(run / "guest" / "paired-cycle.json", report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    tag = "localhost/duotronic-runtime-candidate:" + re.sub(r"[^a-z0-9]", "", args.run_id.lower())[-24:]
    runtime_file = runtime_compose(pair, tag)
    runtime_project = "duotronic-pair-runtime-" + re.sub(r"[^a-z0-9]", "", args.run_id.lower())[-20:]
    build = compose(runtime_file, runtime_project, "build", "runtime-candidate", timeout=args.timeout)
    up = compose(runtime_file, runtime_project, "up", "-d", timeout=args.timeout) if build["exit_code"] == 0 else {"exit_code": 125, "stderr": "build failed", "stdout": "", "argv": []}
    test: dict[str, Any] = {"exit_code": 125, "stderr": "runtime not started", "stdout": "", "argv": []}
    health: dict[str, Any] = {"exit_code": 125, "stderr": "runtime not started", "stdout": "", "argv": []}
    health_api = plan_api = openapi = health
    crypto_scan = pair_binding = health
    cid = None
    if up["exit_code"] == 0:
        try:
            cid = container_id(runtime_project)
            test = capture(["podman", "--remote=false", "exec", cid, "python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "/app/tests"], timeout=args.timeout)
            crypto_scan = capture([
                "podman", "--remote=false", "exec", cid, "python",
                "/app/app/duotronic_runtime/crypto_policy_scan.py",
                "/app/app", "/app/ops_agent", "/app/tests",
            ], timeout=min(args.timeout, 600))
            pair_binding = capture([
                "podman", "--remote=false", "exec", cid, "python", "-c",
                "import json; from duotronic_runtime.runtime_contract import verify_mounted_pair; print(json.dumps(verify_mounted_pair(),sort_keys=True))",
            ], timeout=120)
            health = wait_health(cid, min(args.timeout, 300))
            if health["exit_code"] == 0:
                health_api = exec_json(cid, "GET", "/health")
                openapi = exec_json(cid, "GET", "/openapi.json")
                plan_api = exec_json(cid, "POST", "/v1/self-development/plan", {"task": "Analyze the paired sandbox corpus and runtime candidate; propose bounded documentation, schema, test, or runtime improvements without production authority.", "repo_ref": "vm-sandbox-paired-candidate"})
        except Exception as exc:
            health = {"exit_code": 70, "stderr": str(exc), "stdout": "", "argv": []}
    logs = compose(runtime_file, runtime_project, "logs", timeout=120)
    down = compose(runtime_file, runtime_project, "down", timeout=300)
    data_cleanup: dict[str, Any]
    runtime_data = pair.parent / "runtime-data"
    try:
        if runtime_data.parent != pair.parent or runtime_data.is_symlink():
            raise ValueError("runtime data cleanup escaped paired output")
        shutil.rmtree(runtime_data)
        data_cleanup = {"exit_code": 0, "path": str(runtime_data), "removed": True}
    except Exception as exc:
        data_cleanup = {"exit_code": 70, "path": str(runtime_data), "removed": False, "stderr": str(exc)}
    passed = all(item.get("exit_code") == 0 for item in (
        build, test, crypto_scan, pair_binding, up, health, health_api,
        openapi, plan_api, logs, down, data_cleanup,
    ))
    report = {
        "schema": "duotronic-paired-vm-cycle/v1", "at": now(), "run_id": args.run_id,
        "state": "candidate-qualified-for-gates" if passed else "blocked",
        "pair_manifest": json.loads((pair / "paired-candidate.json").read_text()),
        "runtime_image": tag, "runtime_container_id": cid,
        "checks": {"materializer_up": mat_up, "materializer_down": mat_down, "runtime_build": build, "runtime_tests": test, "forbidden_active_cryptography": crypto_scan, "mounted_pair_binding": pair_binding, "runtime_up": up, "runtime_health": health, "health_api": health_api, "openapi": openapi, "self_development_plan": plan_api, "runtime_logs": logs, "runtime_down": down, "runtime_data_cleanup": data_cleanup},
        "twelve_external_activation_gates": "pending" if passed else "not_reached",
        "authority_activated": False, "authority_scope": "none", "authority_profile": "sandbox-test-only",
        "production_eligible": False, "production_authority_activated": False, "production_runtime_connected": False,
        "host_podman_invoked": False, "guest_rootless_podman": True,
    }
    write_json(run / "guest" / "paired-cycle.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="VM-only paired corpus/runtime sandbox lab")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--timeout", type=int, default=3600)
    return run_cycle(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
