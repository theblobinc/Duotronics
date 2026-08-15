#!/usr/bin/env python3
"""Export, ingest, inventory, and verify evidence for the 12 external gates.

The workflow never signs evidence. External issuers produce ML-DSA-87
signatures; the sandbox remains the authoritative verifier for each exact
probe result and contract subject.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
LOG_ROOT = ROOT / "logs"
EVIDENCE_ROOT = ROOT / "evidence"
REGISTRY = json.loads((ROOT / "activation_gate_registry_v1.json").read_text())
GATES = {item["gate_id"]: item for item in REGISTRY["gates"]}
RUN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex[:8])
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def run_dir(run_id: str) -> Path:
    if not RUN_RE.fullmatch(run_id):
        raise ValueError("invalid run id")
    result = (LOG_ROOT / run_id).resolve()
    if result.parent != LOG_ROOT.resolve():
        raise ValueError("run escaped log root")
    if not result.is_dir():
        raise FileNotFoundError(str(result))
    return result


def request_source(run: Path) -> Path:
    candidates = sorted(run.rglob("external-attestation-requests.json"))
    if len(candidates) != 1:
        raise ValueError(f"expected exactly one request file, found {len(candidates)}")
    return candidates[0]


def export_requests(args: argparse.Namespace) -> int:
    run = run_dir(args.run_id)
    source = request_source(run)
    value = json.loads(source.read_text())
    gates = value.get("requests", value if isinstance(value, list) else [])
    challenge_run_ids = {
        item.get("probe", {}).get("run_id")
        for item in gates
        if item.get("probe", {}).get("run_id")
    }
    if len(challenge_run_ids) != 1:
        raise ValueError("attestation requests must bind exactly one probe run")
    challenge_run_id = challenge_run_ids.pop()
    bundle = {
        "schema": "duotronic-external-attestation-request-bundle/v1",
        "contract_version": REGISTRY["contract_version"],
        "run_id": args.run_id,
        "challenge_run_id": challenge_run_id,
        "created_at": now(),
        "signature_suite_required": "ML-DSA-87",
        "payload_hash_required": "SHAKE256-512",
        "self_issuance_forbidden": sorted(
            gate_id for gate_id, gate in GATES.items() if gate.get("self_issuance_forbidden")
        ),
        "requests": gates,
        "authority_activated": False,
        "runtime_connected": False,
    }
    target = run / "attestation" / "request-bundle.json"
    atomic_json(target, bundle)
    print(json.dumps({"state": "exported", "path": str(target), "request_count": len(gates)}, indent=2))
    return 0


def ingest(args: argparse.Namespace) -> int:
    run = run_dir(args.run_id)
    source = Path(args.evidence_file).resolve()
    allowed = EVIDENCE_ROOT.resolve()
    if allowed not in source.parents or not source.is_file():
        raise ValueError("evidence file must be a regular file under harness/evidence")
    value = json.loads(source.read_text())
    gate_id = value.get("gate_id")
    if gate_id not in GATES:
        raise ValueError("unknown gate_id")
    if value.get("signature_suite") != "ML-DSA-87":
        raise ValueError("only ML-DSA-87 evidence is accepted")
    if value.get("contract_version") != REGISTRY["contract_version"]:
        raise ValueError("contract version mismatch")
    bundle_path = run / "attestation" / "request-bundle.json"
    if not bundle_path.is_file():
        raise ValueError("export the exact attestation request bundle before ingest")
    bundle = json.loads(bundle_path.read_text())
    requested = {item.get("gate_id"): item for item in bundle.get("requests", [])}
    request = requested.get(gate_id)
    if request is None:
        raise ValueError("gate was not requested by this run")
    if value.get("probe", {}).get("run_id") != bundle.get("challenge_run_id"):
        raise ValueError("evidence probe run does not match this challenge")
    if value.get("probe", {}).get("result_id") != request.get("measurement_id"):
        raise ValueError("evidence measurement does not match this challenge")
    inbox = run / "attestation" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    destination = inbox / f"{gate_id}.json"
    if destination.exists() and destination.read_bytes() != source.read_bytes():
        raise FileExistsError("different evidence already ingested for gate")
    shutil.copyfile(source, destination)
    atomic_json(run / "attestation" / "ingest-receipts" / f"{gate_id}.json", {
        "schema": "duotronic-external-attestation-ingest-receipt/v1",
        "run_id": args.run_id,
        "gate_id": gate_id,
        "ingested_at": now(),
        "source_name": source.name,
        "verification_state": "pending_sandbox_verification",
        "authority_activated": False,
    })
    print(json.dumps({"state": "ingested", "gate_id": gate_id, "path": str(destination)}, indent=2))
    return 0


def inventory(args: argparse.Namespace) -> int:
    run = run_dir(args.run_id)
    inbox = run / "attestation" / "inbox"
    present = sorted(path.stem for path in inbox.glob("*.json")) if inbox.is_dir() else []
    reports = sorted(run.rglob("aggregate-report.json"))
    latest = json.loads(reports[-1].read_text()) if reports else None
    result = {
        "schema": "duotronic-external-attestation-status/v1",
        "run_id": args.run_id,
        "gate_count": len(GATES),
        "evidence_present": present,
        "evidence_missing": sorted(set(GATES) - set(present)),
        "latest_aggregate_report": str(reports[-1]) if reports else None,
        "qualification_complete": bool(latest and latest.get("qualification_complete")),
        "runtime_handoff_eligible": bool(latest and latest.get("runtime_handoff_eligible")),
        "authority_activated": False,
        "runtime_connected": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="12-gate external-attestation workflow")
    sub = root.add_subparsers(dest="command", required=True)
    export = sub.add_parser("export-requests")
    export.add_argument("--run-id", required=True)
    load = sub.add_parser("ingest")
    load.add_argument("--run-id", required=True)
    load.add_argument("--evidence-file", required=True)
    status = sub.add_parser("status")
    status.add_argument("--run-id", required=True)
    return root


def main() -> int:
    args = parser().parse_args()
    if args.command == "export-requests":
        return export_requests(args)
    if args.command == "ingest":
        return ingest(args)
    if args.command == "status":
        return inventory(args)
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
