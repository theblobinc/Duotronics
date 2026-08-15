#!/usr/bin/env python3
"""Materialize and inspect a paired witness-corpus/runtime development candidate.

This program is intended to run inside the witness-harness VM. Parent snapshots
are read-only. A proposal may only write or replace confined candidate files.
No operation publishes, stages, or activates a production runtime.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from pq_crypto import PROFILE_NAME as CRYPTO_PROFILE_NAME, registry_identity

SCHEMA = "duotronic-paired-candidate/v1"
PROPOSAL_SCHEMA = "duotronic-paired-change-proposal/v1"
PROFILE = "sandbox-test-only"
DEFAULT_NAMESPACE = "duotronic://authority/sandbox/witness-harness-vm"
IGNORED = {".git", ".lake", ".pytest_cache", "__pycache__", ".mypy_cache", ".hypothesis", ".venv"}
SECRET_RE = re.compile(r"(?i)(password|private[_-]?key|secret|token|api[_-]?key)\s*[:=]")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def frame(*parts: bytes) -> bytes:
    out = bytearray()
    for part in parts:
        out.extend(len(part).to_bytes(8, "big"))
        out.extend(part)
    return bytes(out)


def duoid(label: str, *parts: bytes) -> str:
    raw = hashlib.shake_256(frame(label.encode(), *parts)).digest(64)
    return "duoid:shake256-512:" + base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def regular_files(root: Path) -> Iterable[tuple[Path, str]]:
    root = root.resolve(strict=True)
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in IGNORED for part in rel.parts):
            continue
        yield path, rel.as_posix()


def tree_identity(root: Path, label: str) -> dict[str, Any]:
    leaves: list[str] = []
    count = total = 0
    for path, rel in regular_files(root):
        data = path.read_bytes()
        leaves.append(duoid(label + "/FILE/v1", rel.encode(), data))
        count += 1
        total += len(data)
    root_id = duoid(label + "/TREE/v1", canonical(leaves), str(count).encode(), str(total).encode())
    return {"id": root_id, "file_count": count, "bytes": total, "leaf_ids": leaves}


def confined(root: Path, relative: str) -> Path:
    if not relative or relative.startswith("/") or "\x00" in relative:
        raise ValueError("candidate path must be relative")
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError("candidate path escaped root")
    return candidate


def allowed(relative: str, target: str, policy: dict[str, Any]) -> bool:
    prefixes = policy[f"allowed_{target}_prefixes"]
    return relative in policy.get("allowed_root_files", []) or any(relative.startswith(prefix) for prefix in prefixes)


def copy_parent(source: Path, destination: Path) -> None:
    if destination.exists():
        raise FileExistsError(destination)
    shutil.copytree(source, destination, symlinks=False, ignore=shutil.ignore_patterns(*IGNORED))


def proposal_id(proposal: dict[str, Any]) -> str:
    value = {key: child for key, child in proposal.items() if key != "proposal_id"}
    return duoid("DUOTRONIC/PAIRED-CHANGE-PROPOSAL/v1", canonical(value))


def apply_proposal(proposal: dict[str, Any], corpus: Path, runtime: Path, policy: dict[str, Any]) -> list[dict[str, Any]]:
    if proposal.get("schema") != PROPOSAL_SCHEMA:
        raise ValueError("unsupported proposal schema")
    expected = proposal_id(proposal)
    if proposal.get("proposal_id") not in {None, expected}:
        raise ValueError("proposal identity mismatch")
    changes = proposal.get("changes")
    if not isinstance(changes, list) or len(changes) > int(policy["maximum_changed_files_per_cycle"]):
        raise ValueError("proposal change count exceeds policy")
    written = 0
    receipts: list[dict[str, Any]] = []
    roots = {"corpus": corpus, "runtime": runtime}
    for index, change in enumerate(changes):
        if not isinstance(change, dict) or change.get("target") not in roots:
            raise ValueError(f"invalid change target at index {index}")
        target = str(change["target"])
        relative = str(change.get("path", ""))
        if not allowed(relative, target, policy):
            raise ValueError(f"path not allowed by paired-candidate policy: {target}:{relative}")
        path = confined(roots[target], relative)
        action = change.get("action")
        content = change.get("content")
        if action not in {"write_text", "replace_text"} or not isinstance(content, str):
            raise ValueError("only write_text and replace_text are supported")
        payload = content.encode("utf-8")
        written += len(payload)
        if written > int(policy["maximum_written_bytes_per_cycle"]):
            raise ValueError("proposal byte budget exceeded")
        before = path.read_bytes() if path.is_file() else b""
        if action == "replace_text":
            old = change.get("old")
            if not isinstance(old, str) or not path.is_file():
                raise ValueError("replace_text requires an existing file and old text")
            current = before.decode("utf-8")
            occurrences = current.count(old)
            if occurrences != int(change.get("expected_occurrences", 1)):
                raise ValueError(f"replace occurrence mismatch for {target}:{relative}")
            payload = current.replace(old, content, occurrences).encode("utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        receipts.append({
            "target": target,
            "path": relative,
            "action": action,
            "before_id": duoid("DUOTRONIC/CANDIDATE-FILE-BEFORE/v1", before),
            "after_id": duoid("DUOTRONIC/CANDIDATE-FILE-AFTER/v1", payload),
            "bytes": len(payload),
        })
    return receipts


def snapshot_external(root: Path | None, policy: dict[str, Any]) -> dict[str, Any]:
    if root is None or not root.exists():
        return {"present": False, "snapshot_id": duoid("DUOTRONIC/EXTERNAL-DATA-SNAPSHOT/v1", b"absent"), "files": 0, "bytes": 0, "secret_markers": []}
    identity = tree_identity(root, "DUOTRONIC/EXTERNAL-DATA")
    limits = policy["external_data"]
    if identity["file_count"] > int(limits["maximum_files"]) or identity["bytes"] > int(limits["maximum_total_bytes"]):
        raise ValueError("external snapshot exceeds policy limits")
    markers: list[str] = []
    for path, rel in regular_files(root):
        if path.stat().st_size <= 1_000_000 and path.suffix.lower() in {".json", ".yaml", ".yml", ".env", ".txt"}:
            if SECRET_RE.search(path.read_text(encoding="utf-8", errors="ignore")):
                markers.append(rel)
    if markers and limits.get("credentials_in_snapshots_forbidden", True):
        raise ValueError("external snapshot contains possible credential material")
    return {"present": True, "snapshot_id": identity["id"], "files": identity["file_count"], "bytes": identity["bytes"], "secret_markers": markers, "read_only": True}


def recurrent_witness(parent: dict[str, Any], candidate: dict[str, Any], external: dict[str, Any], changes: int) -> dict[str, Any]:
    semantic = [
        math.log1p(parent["corpus"]["file_count"]), math.log1p(parent["runtime"]["file_count"]),
        math.log1p(candidate["corpus"]["file_count"]), math.log1p(candidate["runtime"]["file_count"]),
        math.log1p(external["files"]), math.log1p(external["bytes"]), float(changes), 1.0,
    ]
    seed = hashlib.shake_256(canonical([parent["corpus"]["id"], parent["runtime"]["id"]])).digest(64)
    state: list[float] = []
    for index, value in enumerate(semantic):
        weight = (int.from_bytes(seed[index * 4:index * 4 + 4], "big") / 2**32) * 2 - 1
        prior = state[index - 1] if index else 0.0
        state.append(round(math.tanh(weight * value + 0.25 * prior), 12))
    positive_baseline = [round(value + 2.0, 12) for value in state]
    body = {
        "schema": "duotronic-witness-gated-recurrent-state/v1",
        "role": "candidate-proposal-and-diagnostic-only",
        "semantic_state": state,
        "positive_baseline_state": positive_baseline,
        "baseline": 2.0,
        "parent_pair": {"corpus_id": parent["corpus"]["id"], "runtime_id": parent["runtime"]["id"]},
        "candidate_pair": {"corpus_id": candidate["corpus"]["id"], "runtime_id": candidate["runtime"]["id"]},
        "external_snapshot_id": external["snapshot_id"],
        "authority_created": False,
    }
    body["witness_id"] = duoid("DUOTRONIC/WITNESS-GATED-RECURRENT-STATE/v1", canonical(body))
    return body


def run(argv: list[str], cwd: Path, timeout: int) -> dict[str, Any]:
    try:
        result = subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        return {"argv": argv, "exit_code": result.returncode, "stdout": result.stdout[-20000:], "stderr": result.stderr[-20000:]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"argv": argv, "exit_code": 127, "stdout": "", "stderr": str(exc)}


def find_validator(corpus: Path) -> Path | None:
    candidates: list[tuple[tuple[int, int, int], Path]] = []
    version_re = re.compile(r"^v1\.6-draft-(\d+)\.(\d+)\.(\d+)$")
    for descriptor_path in corpus.glob("CANONICAL_CORPUS*.json"):
        try:
            descriptor = json.loads(descriptor_path.read_text())
            match = version_re.fullmatch(str(descriptor.get("active_version", "")))
            validator = confined(corpus, str(descriptor.get("validator", "")))
            if match and validator.is_file():
                candidates.append((tuple(map(int, match.groups())), validator))
        except Exception:
            continue
    return max(candidates, default=((), None), key=lambda row: row[0])[1]


def prepare_pair_contract(corpus: Path, runtime: Path) -> dict[str, Any]:
    profile_path = runtime / "config/cryptographic_profile_registry_v1.json"
    interface_path = runtime / "config/runtime_interface_v1.json"
    if not profile_path.is_file() or not interface_path.is_file():
        raise ValueError("runtime cryptographic profile or interface registry missing")
    profile_registry = json.loads(profile_path.read_text(encoding="utf-8"))
    interface = json.loads(interface_path.read_text(encoding="utf-8"))
    harness_registry_path = Path(__file__).with_name("cryptographic_profile_registry_v1.json")
    harness_registry = json.loads(harness_registry_path.read_text(encoding="utf-8"))
    if profile_registry != harness_registry:
        raise ValueError("runtime and harness cryptographic profile registries differ")
    if (
        profile_registry.get("active_profile") != CRYPTO_PROFILE_NAME
        or interface.get("schema") != "duotronic-runtime-interface/v1"
    ):
        raise ValueError("runtime profile or interface version is unsupported")
    profile_id = registry_identity(profile_registry)
    corpus_interface = {
        "schema": "duotronic-corpus-runtime-interface-declaration/v1",
        "api_version": interface["api_version"],
        "manifest_schema": interface["manifest_schema"],
        "cryptographic_profile": CRYPTO_PROFILE_NAME,
        "profile_registry_id": profile_id,
        "required_capabilities": interface["required_capabilities"],
        "unknown_noncritical_fields": "preserve",
        "unknown_critical_fields": "read-only",
        "partial_upgrade_allowed": False,
    }
    corpus_interface["declaration_id"] = duoid(
        "DUOTRONIC/CORPUS-RUNTIME-INTERFACE-DECLARATION/v1",
        canonical(corpus_interface),
    )
    declaration_path = corpus / "runtime/CORPUS_RUNTIME_INTERFACE_v1.json"
    declaration_path.parent.mkdir(parents=True, exist_ok=True)
    declaration_path.write_text(
        json.dumps(corpus_interface, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    corpus_identity = tree_identity(corpus, "DUOTRONIC/CANDIDATE-CORPUS")
    runtime_source_identity = tree_identity(runtime, "DUOTRONIC/CANDIDATE-RUNTIME-SOURCE")
    binding = {
        "schema": "duotronic-paired-runtime-binding/v1",
        "corpus_root_id": corpus_identity["id"],
        "runtime_source_id": runtime_source_identity["id"],
        "cryptographic_profile": CRYPTO_PROFILE_NAME,
        "profile_registry_id": profile_id,
        "api_version": interface["api_version"],
        "manifest_schema": interface["manifest_schema"],
        "partial_upgrade_allowed": False,
        "unknown_noncritical_fields": "preserve",
        "unknown_critical_fields": "read-only",
    }
    binding["binding_id"] = duoid(
        "DUOTRONIC/PAIRED-RUNTIME-BINDING/v1", canonical(binding)
    )
    binding_path = runtime / "config/paired_binding.json"
    binding_path.write_text(
        json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "corpus": corpus_identity,
        "runtime": tree_identity(runtime, "DUOTRONIC/CANDIDATE-RUNTIME"),
        "runtime_source": runtime_source_identity,
        "profile_registry_id": profile_id,
        "binding": binding,
        "interface": interface,
        "corpus_interface": corpus_interface,
    }


def pair_compatibility_check(corpus: Path, runtime: Path) -> dict[str, Any]:
    try:
        pair_manifest = json.loads(
            (runtime.parent / "paired-candidate.json").read_text(encoding="utf-8")
        )
        binding = json.loads(
            (runtime / "config/paired_binding.json").read_text(encoding="utf-8")
        )
        profile_registry = json.loads(
            (runtime / "config/cryptographic_profile_registry_v1.json").read_text(
                encoding="utf-8"
            )
        )
        interface = json.loads(
            (runtime / "config/runtime_interface_v1.json").read_text(encoding="utf-8")
        )
        declaration = json.loads(
            (corpus / "runtime/CORPUS_RUNTIME_INTERFACE_v1.json").read_text(
                encoding="utf-8"
            )
        )
        corpus_id = tree_identity(corpus, "DUOTRONIC/CANDIDATE-CORPUS")["id"]
        runtime_id = tree_identity(runtime, "DUOTRONIC/CANDIDATE-RUNTIME")["id"]
        profile_id = registry_identity(profile_registry)
        checks = {
            "pair_schema": pair_manifest.get("schema") == SCHEMA,
            "corpus_id": pair_manifest.get("candidate", {}).get("corpus_id") == corpus_id,
            "runtime_id": pair_manifest.get("candidate", {}).get("runtime_id") == runtime_id,
            "binding_schema": binding.get("schema") == "duotronic-paired-runtime-binding/v1",
            "binding_corpus": binding.get("corpus_root_id") == corpus_id,
            "profile": binding.get("cryptographic_profile") == CRYPTO_PROFILE_NAME,
            "profile_registry": binding.get("profile_registry_id") == profile_id,
            "interface_schema": interface.get("schema") == "duotronic-runtime-interface/v1",
            "declaration_profile": declaration.get("profile_registry_id") == profile_id,
            "api_match": declaration.get("api_version") == binding.get("api_version"),
            "manifest_schema_match": declaration.get("manifest_schema")
            == binding.get("manifest_schema"),
            "partial_upgrade_rejected": binding.get("partial_upgrade_allowed") is False,
            "unknown_noncritical_preserved": binding.get("unknown_noncritical_fields")
            == "preserve",
            "unknown_critical_read_only": binding.get("unknown_critical_fields")
            == "read-only",
        }
        return {
            "exit_code": 0 if all(checks.values()) else 2,
            "checks": checks,
            "corpus_root_id": corpus_id,
            "runtime_id": runtime_id,
            "profile_registry_id": profile_id,
        }
    except Exception as exc:
        return {"exit_code": 2, "checks": {}, "error": repr(exc)}


def evaluate(corpus: Path, runtime: Path, timeout: int) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    validator = find_validator(corpus)
    checks["corpus_portable_validation"] = run([sys.executable, str(validator)], corpus, timeout) if validator else {"exit_code": 2, "stderr": "validator not found", "stdout": "", "argv": []}
    checks["runtime_compile"] = run([sys.executable, "-m", "compileall", "-q", "app", "tests"], runtime, min(timeout, 600))
    if (runtime / "tests").is_dir():
        checks["runtime_unit_tests"] = run([sys.executable, "-m", "pytest", "-q", "tests"], runtime, timeout)
    else:
        checks["runtime_unit_tests"] = {"exit_code": 2, "stderr": "tests directory not found", "stdout": "", "argv": []}
    scanner = Path(__file__).with_name("crypto_policy_scan.py")
    checks["forbidden_active_cryptography"] = run(
        [sys.executable, str(scanner), str(runtime / "app"), str(runtime / "ops_agent"), str(runtime / "tests")],
        runtime,
        min(timeout, 600),
    )
    pq_test = Path(__file__).with_name("pq_crypto.py")
    checks["post_quantum_provider_self_test"] = run(
        [sys.executable, str(pq_test)], runtime, min(timeout, 600)
    )
    checks["corpus_runtime_compatibility"] = pair_compatibility_check(corpus, runtime)
    checks["production_boundary"] = {
        "exit_code": 0,
        "sandbox_profile": PROFILE,
        "production_eligible": False,
        "production_credentials_loaded": False,
    }
    passed = all(value.get("exit_code") == 0 for value in checks.values())
    return {"passed": passed, "checks": checks}


def materialize(args: argparse.Namespace) -> dict[str, Any]:
    policy = json.loads(args.policy.read_text())
    if policy.get("authority_profile") != PROFILE or policy.get("production_eligible") is not False:
        raise ValueError("paired candidate policy must remain sandbox-only")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    corpus_candidate = out / "corpus-candidate"
    runtime_candidate = out / "runtime-candidate"
    copy_parent(args.parent_corpus, corpus_candidate)
    copy_parent(args.parent_runtime, runtime_candidate)
    parent = {
        "corpus": tree_identity(args.parent_corpus, "DUOTRONIC/PARENT-CORPUS"),
        "runtime": tree_identity(args.parent_runtime, "DUOTRONIC/PARENT-RUNTIME"),
    }
    proposal = json.loads(args.proposal.read_text()) if args.proposal else {"schema": PROPOSAL_SCHEMA, "changes": []}
    proposal["proposal_id"] = proposal_id(proposal)
    receipts = apply_proposal(proposal, corpus_candidate, runtime_candidate, policy)
    prepared = prepare_pair_contract(corpus_candidate, runtime_candidate)
    candidate = {
        "corpus": prepared["corpus"],
        "runtime": prepared["runtime"],
    }
    external = snapshot_external(args.external_data, policy)
    recurrent = recurrent_witness(parent, candidate, external, len(receipts))
    manifest = {
        "schema": SCHEMA,
        "created_at": now(),
        "parent": {"corpus_id": parent["corpus"]["id"], "runtime_id": parent["runtime"]["id"]},
        "candidate": {"corpus_id": candidate["corpus"]["id"], "runtime_id": candidate["runtime"]["id"]},
        "authority": {"profile": PROFILE, "namespace": policy.get("authority_namespace", DEFAULT_NAMESPACE), "production_eligible": False},
        "lineage": {"proposal_id": proposal["proposal_id"], "changes": receipts, "external_snapshot_id": external["snapshot_id"], "parent_snapshots_immutable": True},
        "recursive_witness": recurrent,
        "cryptographic_profile": {
            "name": CRYPTO_PROFILE_NAME,
            "registry_id": prepared["profile_registry_id"],
            "status": "candidate-pending-provider-and-policy-gates",
        },
        "runtime_interface": {
            "api_version": prepared["interface"]["api_version"],
            "manifest_schema": prepared["interface"]["manifest_schema"],
            "binding_id": prepared["binding"]["binding_id"],
            "runtime_source_id": prepared["runtime_source"]["id"],
            "partial_upgrade_allowed": False,
        },
        "checks": {
            "state": "pending",
            "forbidden_active_cryptography": "pending",
            "post_quantum_provider_self_test": "pending",
            "corpus_runtime_compatibility": "pending",
            "twelve_external_activation_gates": "pending",
        },
        "outputs": {"corpus": str(corpus_candidate), "runtime": str(runtime_candidate)},
    }
    manifest["pair_id"] = duoid("DUOTRONIC/PAIRED-CANDIDATE/v1", canonical(manifest))
    (out / "paired-candidate.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (out / "proposal.json").write_text(json.dumps(proposal, indent=2, sort_keys=True) + "\n")
    (out / "external-snapshot.json").write_text(json.dumps(external, indent=2, sort_keys=True) + "\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Paired corpus/runtime candidate lab")
    sub = parser.add_subparsers(dest="command", required=True)
    mat = sub.add_parser("materialize")
    mat.add_argument("--parent-corpus", type=Path, required=True)
    mat.add_argument("--parent-runtime", type=Path, required=True)
    mat.add_argument("--output", type=Path, required=True)
    mat.add_argument("--policy", type=Path, required=True)
    mat.add_argument("--external-data", type=Path)
    mat.add_argument("--proposal", type=Path)
    ev = sub.add_parser("evaluate")
    ev.add_argument("--corpus", type=Path, required=True)
    ev.add_argument("--runtime", type=Path, required=True)
    ev.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    if args.command == "materialize":
        result = materialize(args)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    result = evaluate(args.corpus, args.runtime, args.timeout)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
