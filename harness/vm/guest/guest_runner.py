#!/usr/bin/env python3
"""Confined guest entry point for the witness-contract VM.

Only named operations are exposed. Every contract tool and attestor runs through
this guest's rootless Podman/Compose installation; host Podman is never used.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HARNESS = Path("/srv/duotronic-harness")
RUN_ROOT = Path("/srv/duotronic-runs")
RUNTIME_STATE = RUN_ROOT / ".sandbox-runtime"
IMAGE = "localhost/duotronic-wc-activation-harness:5.3.17"
PROFILE = "sandbox-test-only"
DEFAULT_NAMESPACE = "duotronic://authority/sandbox/witness-harness-vm"
RUN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")
GATE_RE = re.compile(r"^[a-z][a-z0-9_]{0,79}$")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True,
        separators=(",", ":"),
    ).encode()


def duoid(label: str, value: Any) -> str:
    raw = hashlib.shake_256(label.encode() + b"\x00" + canonical_bytes(value)).digest(64)
    return "duoid:shake256-512:" + base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def confined_run(run_id: str) -> Path:
    if not RUN_RE.fullmatch(run_id):
        raise ValueError("invalid run id")
    root = RUN_ROOT.resolve()
    target = (root / run_id).resolve()
    if target.parent != root:
        raise ValueError("run path escaped root")
    return target


def capture(argv: list[str], *, timeout: int = 60, cwd: Path | None = None) -> dict[str, Any]:
    result = subprocess.run(
        argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=timeout, check=False,
    )
    return {
        "argv": argv,
        "exit_code": result.returncode,
        "stdout": result.stdout[-20000:],
        "stderr": result.stderr[-20000:],
    }


def select_contract_descriptor(corpus: Path) -> dict[str, Any]:
    """Select the newest valid v1.6 draft descriptor with a confined validator."""
    root = corpus.resolve()
    version_pattern = re.compile(r"^v1\.6-draft-([0-9]+)\.([0-9]+)\.([0-9]+)$")
    candidates: list[tuple[tuple[int, int, int], dict[str, Any]]] = []
    for path in root.glob("CANONICAL_CORPUS*.json"):
        try:
            descriptor = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        match = version_pattern.fullmatch(str(descriptor.get("active_version", "")))
        validator_relative = descriptor.get("validator")
        if not match or not isinstance(validator_relative, str):
            continue
        validator = (root / validator_relative).resolve()
        if not validator.is_relative_to(root) or not validator.is_file():
            continue
        candidates.append((tuple(int(value) for value in match.groups()), descriptor))
    if not candidates:
        raise RuntimeError("no valid canonical corpus descriptor with confined validator")
    return max(candidates, key=lambda item: item[0])[1]


def active_record() -> dict[str, Any] | None:
    path = RUNTIME_STATE / "authority.json"
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if (
        value.get("state") == "active"
        and value.get("authority_profile") == PROFILE
        and value.get("production_eligible") is False
    ):
        return value
    return None


def health() -> int:
    podman = capture(["podman", "--remote=false", "info", "--format", "json"])
    compose = capture(["podman", "--remote=false", "compose", "version"])
    active = active_record()
    payload = {
        "schema": "duotronic-witness-harness-guest-health/v2",
        "at": now(),
        "uid": os.geteuid(),
        "rootless": os.geteuid() != 0,
        "podman": podman,
        "compose": compose,
        "harness_present": (HARNESS / "activation_harness.py").is_file(),
        "runtime_connected": False,
        "production_runtime_connected": False,
        "production_authority_activated": False,
        "authority_activated": active is not None,
        "authority_scope": "sandbox-only" if active else "none",
        "sandbox_authority": active,
    }
    payload["ready"] = (
        payload["rootless"]
        and podman["exit_code"] == 0
        and compose["exit_code"] == 0
        and payload["harness_present"]
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ready"] else 2


def prepare(args: argparse.Namespace) -> int:
    run = confined_run(args.run_id)
    run.mkdir(parents=True, exist_ok=True)
    for name in ("corpus", "evidence", "guest"):
        (run / name).mkdir(parents=True, exist_ok=True)
    print(json.dumps({"state": "prepared", "run_id": args.run_id, "path": str(run)}))
    return 0


def prepare_source(args: argparse.Namespace) -> int:
    run = confined_run(args.run_id)
    bundle = run / "source.bundle"
    status_path = run / "source-status.json"
    if not bundle.is_file() or not status_path.is_file():
        raise FileNotFoundError("source bundle or source status missing")
    status_value = json.loads(status_path.read_text(encoding="utf-8"))
    source = run / "source"
    if source.exists():
        shutil.rmtree(source)
    clone = capture(["git", "clone", "--quiet", str(bundle), str(source)], timeout=300, cwd=run)
    if clone["exit_code"] != 0:
        print(json.dumps(clone, indent=2, sort_keys=True))
        return clone["exit_code"]
    origin = status_value.get("remote_origin")
    if isinstance(origin, str) and origin:
        capture(["git", "-C", str(source), "remote", "set-url", "origin", origin], timeout=30)
    clean = capture(
        ["git", "-C", str(source), "status", "--porcelain=v1", "--untracked-files=all"],
        timeout=30,
    )
    receipt = {
        "schema": "duotronic-witness-harness-source-binding/v2",
        "run_id": args.run_id,
        "prepared_at": now(),
        "host_source_clean": bool(status_value.get("clean")),
        "host_commit_id": status_value.get("commit_id"),
        "host_dirty_state_commitment": status_value.get("dirty_state_commitment"),
        "sandbox_checkout_clean": clean["exit_code"] == 0 and not clean["stdout"].strip(),
        "sandbox_snapshot_only": True,
        "production_eligible": False,
        "clone": clone,
    }
    (run / "guest" / "source-binding.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["sandbox_checkout_clean"] else 2


def copy_new_logs(run: Path, before_logs: set[str]) -> list[Path]:
    harness_logs = run / "harness-logs"
    harness_logs.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for path in (HARNESS / "logs").glob("*"):
        if path.is_dir() and path.name not in before_logs:
            target = harness_logs / path.name
            shutil.copytree(path, target, dirs_exist_ok=True)
            copied.append(target)
    return copied


def build_images(args: argparse.Namespace) -> int:
    run = confined_run(args.run_id)
    (run / "guest").mkdir(parents=True, exist_ok=True)
    before_logs = {path.name for path in (HARNESS / "logs").glob("*") if path.is_dir()}
    commands: list[list[str]] = []
    if args.layer in {"toolchain", "all"}:
        commands.append([
            sys.executable, str(HARNESS / "activation_harness.py"),
            "build-toolchain", "--timeout", str(args.timeout),
        ])
    if args.layer in {"thin", "all"}:
        commands.append([
            sys.executable, str(HARNESS / "activation_harness.py"),
            "build", "--timeout", str(args.timeout),
        ])
    results = []
    exit_code = 0
    for argv in commands:
        result = capture(argv, timeout=args.timeout + 300, cwd=HARNESS)
        results.append(result)
        if result["exit_code"] != 0:
            exit_code = result["exit_code"]
            break
    copy_new_logs(run, before_logs)
    report = {
        "schema": "duotronic-witness-harness-guest-build/v2",
        "run_id": args.run_id,
        "layer": args.layer,
        "results": results,
        "exit_code": exit_code,
        "runtime_connected": False,
        "production_runtime_connected": False,
        "production_authority_activated": False,
    }
    (run / "guest" / "guest-build.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return exit_code


def refresh_activation_image(run: Path, timeout: int) -> dict[str, Any]:
    """Rebuild the thin verifier layer so synchronized harness code is executed."""
    build = capture(
        [
            sys.executable,
            str(HARNESS / "activation_harness.py"),
            "build",
            "--timeout",
            str(timeout),
        ],
        timeout=timeout + 300,
        cwd=HARNESS,
    )
    inspect = capture(
        ["podman", "--remote=false", "image", "inspect", IMAGE],
        timeout=60,
        cwd=HARNESS,
    )
    receipt = {
        "schema": "duotronic-witness-harness-image-refresh/v1",
        "at": now(),
        "image": IMAGE,
        "build": build,
        "inspect": inspect,
        "passed": build["exit_code"] == 0 and inspect["exit_code"] == 0,
        "runtime_connected": False,
        "production_runtime_connected": False,
        "production_authority_activated": False,
    }
    (run / "guest" / "activation-image-refresh.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


def activation_pass(
    run: Path,
    *,
    gate: str | None,
    evidence_run_id: str | None,
    qualification_mode: str,
    timeout: int,
    authority_profile: str,
    authority_namespace: str,
) -> tuple[dict[str, Any], list[Path]]:
    corpus = run / "corpus"
    source = run / "source"
    evidence = run / "evidence"
    for required in (corpus, source, evidence):
        if not required.is_dir():
            raise FileNotFoundError(str(required))
    argv = [
        sys.executable, str(HARNESS / "activation_harness.py"), "run",
        "--corpus", str(corpus),
        "--source", str(source),
        "--evidence", str(evidence),
        "--qualification-mode", qualification_mode,
        "--authority-profile", authority_profile,
        "--authority-namespace", authority_namespace,
        "--contract-ref", select_contract_descriptor(corpus)["active_version"],
        "--timeout", str(timeout),
    ]
    if evidence_run_id:
        if not RUN_RE.fullmatch(evidence_run_id):
            raise ValueError("invalid evidence run id")
        argv.extend(["--evidence-run-id", evidence_run_id])
    if gate:
        if not GATE_RE.fullmatch(gate):
            raise ValueError("invalid gate")
        argv.extend(["--gate", gate])
    before_logs = {path.name for path in (HARNESS / "logs").glob("*") if path.is_dir()}
    result = capture(argv, timeout=timeout + 300, cwd=HARNESS)
    return result, copy_new_logs(run, before_logs)


def execute(args: argparse.Namespace) -> int:
    run = confined_run(args.run_id)
    guest_log = run / "guest"
    guest_log.mkdir(parents=True, exist_ok=True)
    started = now()
    result, copied = activation_pass(
        run,
        gate=args.gate,
        evidence_run_id=args.evidence_run_id,
        qualification_mode=args.qualification_mode,
        timeout=args.timeout,
        authority_profile=args.authority_profile,
        authority_namespace=args.authority_namespace,
    )
    result.update({
        "schema": "duotronic-witness-harness-guest-run/v2",
        "run_id": args.run_id,
        "started_at": started,
        "finished_at": now(),
        "harness_log_directories": [str(path) for path in copied],
        "runtime_connected": False,
        "production_runtime_connected": False,
        "production_authority_activated": False,
        "authority_profile": args.authority_profile,
    })
    (guest_log / "guest-run.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return result["exit_code"]


def newest_file(paths: list[Path], name: str) -> Path:
    matches = [path / name for path in paths if (path / name).is_file()]
    if not matches:
        raise FileNotFoundError(name)
    return max(matches, key=lambda path: path.stat().st_mtime_ns)


def attest_with_compose(run: Path, requests_path: Path, namespace: str, timeout: int) -> dict[str, Any]:
    evidence = run / "evidence"
    guest = run / "guest"
    compose_path = guest / "compose.sandbox-attestor.json"
    project = "duotronic-sandbox-attestor-" + re.sub(r"[^a-z0-9]", "", run.name.lower())[-24:]
    document = {
        "version": "3.8",
        "networks": {"attestor-isolated": {"internal": True}},
        "services": {
            "sandbox-attestor": {
                "image": IMAGE,
                "entrypoint": ["python3", "/opt/harness/sandbox_attestor.py"],
                "command": [
                    "--requests", f"/requests/{requests_path.name}",
                    "--evidence-dir", "/evidence",
                    "--authority-namespace", namespace,
                ],
                "networks": ["attestor-isolated"],
                "read_only": True,
                "user": f"{os.geteuid()}:{os.getegid()}",
                "userns_mode": "keep-id",
                "cap_drop": ["ALL"],
                "security_opt": ["no-new-privileges"],
                "pids_limit": 128,
                "mem_limit": "1g",
                "cpus": 2,
                "tmpfs": ["/tmp:rw,noexec,nosuid,nodev,size=128m"],
                "volumes": [
                    f"{requests_path.parent}:/requests:ro",
                    f"{evidence}:/evidence:rw",
                ],
                "restart": "no",
            }
        },
    }
    compose_path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    up = capture(
        [
            "podman", "--remote=false", "compose", "-f", str(compose_path),
            "-p", project, "up", "--abort-on-container-exit",
            "--exit-code-from", "sandbox-attestor",
        ],
        timeout=timeout,
        cwd=HARNESS,
    )
    down = capture(
        ["podman", "--remote=false", "compose", "-f", str(compose_path), "-p", project, "down"],
        timeout=180,
        cwd=HARNESS,
    )
    report = {
        "schema": "duotronic-sandbox-attestor-compose-run/v1",
        "at": now(),
        "project": project,
        "compose": str(compose_path),
        "up": up,
        "down": down,
        "host_podman_invoked": False,
        "guest_rootless_podman": True,
        "production_eligible": False,
    }
    (guest / "sandbox-attestor-compose-run.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if up["exit_code"] != 0 or down["exit_code"] != 0:
        raise RuntimeError("sandbox attestor Compose execution failed")
    manifest_path = evidence / "sandbox-attestation-manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError("sandbox attestor did not produce a manifest")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def attest_with_independent_compose(
    run: Path, requests_path: Path, namespace: str, timeout: int
) -> dict[str, Any]:
    evidence = run / "evidence"
    guest = run / "guest"
    source_root = run / "independent-evidence-sources"
    request_root = run / "independent-attestation-requests"
    source_root.mkdir(mode=0o700, exist_ok=False)
    request_root.mkdir(mode=0o700, exist_ok=False)
    bundle = json.loads(requests_path.read_text(encoding="utf-8"))
    requests = bundle.get("requests", [])
    if len(requests) != 12:
        raise ValueError("exactly 12 independent attestor sources are required")

    all_keys: list[dict[str, Any]] = []
    all_records: list[dict[str, Any]] = []
    source_receipts: list[dict[str, Any]] = []
    profile_registry_id: str | None = None
    cryptographic_profile: str | None = None

    for ordinal, request in enumerate(requests, 1):
        gate_id = str(request.get("gate_id") or "")
        if not GATE_RE.fullmatch(gate_id):
            raise ValueError("invalid gate id in attestation request")
        source_dir = source_root / f"{ordinal:02d}-{gate_id}"
        request_dir = request_root / f"{ordinal:02d}-{gate_id}"
        source_dir.mkdir(mode=0o700)
        request_dir.mkdir(mode=0o700)
        single_bundle = {**bundle, "requests": [request]}
        single_path = request_dir / "request.json"
        single_path.write_text(
            json.dumps(single_bundle, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        compose_path = guest / f"compose.sandbox-attestor-{ordinal:02d}-{gate_id}.json"
        project = (
            "duotronic-attestor-"
            + f"{ordinal:02d}-"
            + re.sub(r"[^a-z0-9]", "", run.name.lower())[-16:]
        )
        document = {
            "version": "3.8",
            "networks": {"attestor-isolated": {"internal": True}},
            "services": {
                "sandbox-attestor": {
                    "image": IMAGE,
                    "entrypoint": ["python3", "/opt/harness/sandbox_attestor.py"],
                    "command": [
                        "--requests", "/requests/request.json",
                        "--evidence-dir", "/evidence",
                        "--authority-namespace", namespace,
                    ],
                    "networks": ["attestor-isolated"],
                    "read_only": True,
                    "user": f"{os.geteuid()}:{os.getegid()}",
                    "userns_mode": "keep-id",
                    "cap_drop": ["ALL"],
                    "security_opt": ["no-new-privileges"],
                    "pids_limit": 128,
                    "mem_limit": "1g",
                    "cpus": 2,
                    "tmpfs": ["/tmp:rw,noexec,nosuid,nodev,size=128m"],
                    "volumes": [
                        f"{request_dir}:/requests:ro",
                        f"{source_dir}:/evidence:rw",
                    ],
                    "restart": "no",
                }
            },
        }
        compose_path.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        up = capture(
            [
                "podman", "--remote=false", "compose", "-f", str(compose_path),
                "-p", project, "up", "--abort-on-container-exit",
                "--exit-code-from", "sandbox-attestor",
            ],
            timeout=timeout,
            cwd=HARNESS,
        )
        down = capture(
            [
                "podman", "--remote=false", "compose", "-f", str(compose_path),
                "-p", project, "down",
            ],
            timeout=180,
            cwd=HARNESS,
        )
        if up["exit_code"] != 0 or down["exit_code"] != 0:
            raise RuntimeError(f"independent attestor failed for {gate_id}")
        evidence_path = source_dir / f"{gate_id}.json"
        trust_path = source_dir / "trust_registry.json"
        manifest_path = source_dir / "sandbox-attestation-manifest.json"
        if not all(path.is_file() for path in (evidence_path, trust_path, manifest_path)):
            raise RuntimeError(f"independent attestor output incomplete for {gate_id}")
        trust = json.loads(trust_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if len(trust.get("keys", [])) != 1 or manifest.get("evidence_count") != 1:
            raise RuntimeError(f"attestor source was not independent for {gate_id}")
        current_profile_id = trust.get("profile_registry_id")
        current_profile = trust.get("cryptographic_profile")
        if profile_registry_id not in {None, current_profile_id}:
            raise RuntimeError("attestor profile registry disagreement")
        if cryptographic_profile not in {None, current_profile}:
            raise RuntimeError("attestor cryptographic profile disagreement")
        profile_registry_id = current_profile_id
        cryptographic_profile = current_profile
        shutil.copy2(evidence_path, evidence / evidence_path.name)
        all_keys.extend(trust["keys"])
        all_records.extend(manifest["records"])
        source_receipts.append({
            "ordinal": ordinal,
            "gate_id": gate_id,
            "project": project,
            "source_directory": str(source_dir),
            "request_id": duoid(
                "DUOTRONIC/INDEPENDENT-ATTESTOR-REQUEST/v1", single_bundle
            ),
            "source_manifest_id": manifest.get("manifest_id"),
            "up": up,
            "down": down,
            "rootless_podman": True,
            "internal_network": True,
            "production_eligible": False,
        })

    if len(all_keys) != 12 or len({item["key_id"] for item in all_keys}) != 12:
        raise RuntimeError("12 distinct attestor keys were not produced")
    if len({item["issuer_id"] for item in all_keys}) != 12:
        raise RuntimeError("12 distinct attestor issuers were not produced")
    issued_at = now()
    trust = {
        "schema": "duotronic-sandbox-trust-registry/v2",
        "authority_profile": PROFILE,
        "authority_namespace": namespace,
        "evidence_environment": "witness-harness-vm",
        "production_eligible": False,
        "cryptographic_profile": cryptographic_profile,
        "profile_registry_id": profile_registry_id,
        "generated_at": issued_at,
        "revocations": [],
        "keys": all_keys,
        "independent_source_count": 12,
    }
    (evidence / "trust_registry.json").write_text(
        json.dumps(trust, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    merged = {
        "schema": "duotronic-sandbox-attestation-manifest/v2",
        "authority_profile": PROFILE,
        "authority_namespace": namespace,
        "production_eligible": False,
        "probe_run_id": requests[0]["probe"]["run_id"],
        "subject_id": bundle["subject_id"],
        "contract_version": bundle["contract_version"],
        "issued_at": issued_at,
        "issuer_count": 12,
        "evidence_count": 12,
        "independent_source_count": 12,
        "records": all_records,
        "source_receipts": source_receipts,
    }
    merged["manifest_id"] = duoid(
        "DUOTRONIC/INDEPENDENT-SANDBOX-ATTESTATION-MANIFEST/v1", merged
    )
    (evidence / "sandbox-attestation-manifest.json").write_text(
        json.dumps(merged, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    compose_report = {
        "schema": "duotronic-independent-attestor-compose-run/v2",
        "at": issued_at,
        "source_count": 12,
        "sources": source_receipts,
        "host_podman_invoked": False,
        "guest_rootless_podman": True,
        "production_eligible": False,
    }
    (guest / "sandbox-attestor-compose-run.json").write_text(
        json.dumps(compose_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return merged


def sandbox_activate(args: argparse.Namespace) -> int:
    run = confined_run(args.run_id)
    evidence = run / "evidence"
    guest = run / "guest"
    for required in (run / "corpus", run / "source", evidence, guest):
        if not required.is_dir():
            raise FileNotFoundError(str(required))
    image_refresh = refresh_activation_image(run, args.timeout)
    if not image_refresh["passed"]:
        print(json.dumps(image_refresh, indent=2, sort_keys=True))
        return 2
    for path in evidence.glob("*.json"):
        path.unlink()

    probe_result, probe_logs = activation_pass(
        run,
        gate=None,
        evidence_run_id=None,
        qualification_mode="full",
        timeout=args.timeout,
        authority_profile=PROFILE,
        authority_namespace=args.authority_namespace,
    )
    requests_path = newest_file(probe_logs, "external-attestation-requests.json")
    bundle = json.loads(requests_path.read_text(encoding="utf-8"))
    requests = bundle.get("requests", [])
    if len(requests) != 12 or any(item.get("probe", {}).get("exit_code") != 0 for item in requests):
        raise RuntimeError("all 12 sandbox probes must pass before evidence issuance")
    probe_run_ids = {item["probe"]["run_id"] for item in requests}
    if len(probe_run_ids) != 1:
        raise RuntimeError("probe requests do not bind one run")
    probe_run_id = probe_run_ids.pop()

    manifest = attest_with_independent_compose(run, requests_path, args.authority_namespace, args.timeout)
    verify_result, verify_logs = activation_pass(
        run,
        gate=None,
        evidence_run_id=probe_run_id,
        qualification_mode="full",
        timeout=args.timeout,
        authority_profile=PROFILE,
        authority_namespace=args.authority_namespace,
    )
    report_path = newest_file(verify_logs, "sandbox-report.json")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if (
        verify_result["exit_code"] != 0
        or report.get("verified_gate_count") != 12
        or report.get("selected_gate_count") != 12
        or report.get("activation_eligible") is not True
        or report.get("authority_profile") != PROFILE
        or report.get("production_eligible") is not False
    ):
        raise RuntimeError("sandbox verification did not qualify all 12 activation gates")

    activation = {
        "schema": "duotronic-sandbox-runtime-authority/v1",
        "state": "active",
        "activated_at": now(),
        "authority_activated": True,
        "authority_scope": "sandbox-only",
        "authority_profile": PROFILE,
        "authority_namespace": args.authority_namespace,
        "production_eligible": False,
        "production_authority_activated": False,
        "runtime_connected": False,
        "production_runtime_connected": False,
        "host_podman_invoked": False,
        "guest_rootless_podman": True,
        "controller_run_id": args.run_id,
        "probe_run_id": probe_run_id,
        "verification_run_id": report["run_id"],
        "contract_version": report["contract_version"],
        "subject_id": report["subject_id"],
        "verified_gate_count": 12,
        "attestation_manifest_id": manifest["manifest_id"],
        "attestation_issuer_count": manifest["issuer_count"],
        "verification_report": str(report_path),
    }
    activation["activation_id"] = duoid("DUOTRONIC/SANDBOX-RUNTIME-ACTIVATION/v1", activation)
    RUNTIME_STATE.mkdir(parents=True, exist_ok=True)
    for path in (guest / "sandbox-activation.json", RUNTIME_STATE / "authority.json"):
        path.write_text(json.dumps(activation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lifecycle = {
        "schema": "duotronic-sandbox-activation-lifecycle/v1",
        "probe_pass": probe_result,
        "attestation_manifest": manifest,
        "verification_pass": verify_result,
        "activation": activation,
    }
    (guest / "sandbox-activation-lifecycle.json").write_text(
        json.dumps(lifecycle, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(activation, indent=2, sort_keys=True))
    return 0


def paired_cycle(args: argparse.Namespace) -> int:
    """Build, exercise, and activate a paired corpus/runtime candidate in the VM."""
    run = confined_run(args.run_id)
    for required in (run / "corpus", run / "runtime-parent", run / "source", run / "external-data", run / "guest"):
        if not required.is_dir():
            raise FileNotFoundError(str(required))
    image_refresh = refresh_activation_image(run, args.timeout)
    if not image_refresh["passed"]:
        print(json.dumps(image_refresh, indent=2, sort_keys=True))
        return 2
    runtime_lab = capture(
        [
            sys.executable, str(HARNESS / "paired_vm_lab.py"),
            "--run-id", args.run_id,
            "--timeout", str(args.timeout),
        ],
        timeout=args.timeout * 3 + 1200,
        cwd=HARNESS,
    )
    activation_exit = 2
    activation: dict[str, Any] | None = None
    if runtime_lab["exit_code"] == 0:
        candidate = run / "paired-output" / "pair" / "corpus-candidate"
        if not candidate.is_dir() or candidate.is_symlink():
            raise FileNotFoundError("paired corpus candidate unavailable")
        parent = run / "parent-corpus"
        if parent.exists():
            shutil.rmtree(parent)
        os.replace(run / "corpus", parent)
        shutil.copytree(candidate, run / "corpus", symlinks=False)
        args.authority_namespace = DEFAULT_NAMESPACE
        activation_exit = sandbox_activate(args)
        activation_path = run / "guest" / "sandbox-activation.json"
        if activation_path.is_file():
            activation = json.loads(activation_path.read_text(encoding="utf-8"))

    lab_report_path = run / "guest" / "paired-cycle.json"
    lab_report = json.loads(lab_report_path.read_text(encoding="utf-8")) if lab_report_path.is_file() else {}
    active = (
        runtime_lab["exit_code"] == 0
        and activation_exit == 0
        and isinstance(activation, dict)
        and activation.get("authority_activated") is True
        and activation.get("production_eligible") is False
    )
    lab_report.update({
        "state": "active" if active else "blocked",
        "runtime_candidate_qualified": runtime_lab["exit_code"] == 0,
        "twelve_external_activation_gates": "passed" if active else "blocked",
        "verified_gate_count": 12 if active else 0,
        "activation": activation,
        "authority_activated": active,
        "authority_scope": "sandbox-only" if active else "none",
        "authority_profile": PROFILE,
        "production_eligible": False,
        "production_authority_activated": False,
        "production_runtime_connected": False,
    })
    lab_report_path.write_text(json.dumps(lab_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt = {
        "schema": "duotronic-paired-guest-operation/v2",
        "at": now(),
        "run_id": args.run_id,
        "operation": "paired-cycle",
        "runtime_lab": runtime_lab,
        "activation_exit_code": activation_exit,
        "activation": activation,
        "host_podman_invoked": False,
        "guest_rootless_podman": True,
        "authority_activated": active,
        "authority_scope": "sandbox-only" if active else "none",
        "authority_profile": PROFILE,
        "production_eligible": False,
        "production_authority_activated": False,
        "production_runtime_connected": False,
    }
    (run / "guest" / "paired-operation.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if active else (runtime_lab["exit_code"] or activation_exit or 2)


def cleanup(args: argparse.Namespace) -> int:
    run = confined_run(args.run_id)
    result = capture(
        [sys.executable, str(HARNESS / "activation_harness.py"), "cleanup"],
        timeout=args.timeout, cwd=HARNESS,
    )
    result.update({"run_id": args.run_id, "at": now()})
    if run.is_dir():
        (run / "guest").mkdir(parents=True, exist_ok=True)
        (run / "guest" / "cleanup.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return result["exit_code"]


def status() -> int:
    result = capture(
        [sys.executable, str(HARNESS / "activation_harness.py"), "status"],
        timeout=60, cwd=HARNESS,
    )
    active = active_record()
    result.update({
        "at": now(),
        "runtime_connected": False,
        "production_runtime_connected": False,
        "production_authority_activated": False,
        "authority_activated": active is not None,
        "authority_scope": "sandbox-only" if active else "none",
        "sandbox_authority": active,
    })
    print(json.dumps(result, indent=2, sort_keys=True))
    return result["exit_code"]


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Confined witness harness guest operations")
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("health")
    sub.add_parser("status")
    prepare_cmd = sub.add_parser("prepare")
    prepare_cmd.add_argument("--run-id", required=True)
    source_cmd = sub.add_parser("prepare-source")
    source_cmd.add_argument("--run-id", required=True)
    build_cmd = sub.add_parser("build")
    build_cmd.add_argument("--run-id", required=True)
    build_cmd.add_argument("--layer", choices=("toolchain", "thin", "all"), default="all")
    build_cmd.add_argument("--timeout", type=int, default=3600)
    run = sub.add_parser("execute")
    run.add_argument("--run-id", required=True)
    run.add_argument("--gate")
    run.add_argument("--evidence-run-id")
    run.add_argument("--qualification-mode", choices=("full", "targeted"), default="full")
    run.add_argument("--authority-profile", choices=("production", PROFILE), default="production")
    run.add_argument("--authority-namespace", default="duotronic://authority/production")
    run.add_argument("--timeout", type=int, default=1800)
    activate = sub.add_parser("sandbox-activate")
    activate.add_argument("--run-id", required=True)
    activate.add_argument("--authority-namespace", default=DEFAULT_NAMESPACE)
    activate.add_argument("--timeout", type=int, default=3600)
    pair = sub.add_parser("paired-cycle")
    pair.add_argument("--run-id", required=True)
    pair.add_argument("--timeout", type=int, default=3600)
    clean = sub.add_parser("cleanup")
    clean.add_argument("--run-id", required=True)
    clean.add_argument("--timeout", type=int, default=180)
    return root


def main() -> int:
    args = parser().parse_args()
    if args.command == "health":
        return health()
    if args.command == "status":
        return status()
    if args.command == "prepare":
        return prepare(args)
    if args.command == "prepare-source":
        return prepare_source(args)
    if args.command == "build":
        return build_images(args)
    if args.command == "execute":
        return execute(args)
    if args.command == "sandbox-activate":
        return sandbox_activate(args)
    if args.command == "paired-cycle":
        return paired_cycle(args)
    if args.command == "cleanup":
        return cleanup(args)
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
