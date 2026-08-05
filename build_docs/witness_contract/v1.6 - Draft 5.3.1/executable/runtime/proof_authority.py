#!/usr/bin/env python3
"""Server-side content binding and Ed25519 witness signing for Draft 5.3.1.

This module belongs inside the controlled verifier boundary. API clients submit
references, not the result fields passed to ``run_strict_lake_build``.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def load_private_key(path: Path) -> Ed25519PrivateKey:
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("configured verifier key is not Ed25519")
    return key


def load_public_key(path: Path) -> Ed25519PublicKey:
    key = serialization.load_pem_public_key(path.read_bytes())
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("configured verifier key is not Ed25519")
    return key


def public_key_fingerprint(key: Ed25519PublicKey) -> str:
    raw = key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return sha256_bytes(raw)


def signed_payload(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key not in {"signed_payload_sha256", "signature"}}


def sign_record(record: dict[str, Any], private_key: Ed25519PrivateKey) -> dict[str, Any]:
    unsigned = signed_payload(record)
    payload = canonical_bytes(unsigned)
    result = dict(unsigned)
    result["signed_payload_sha256"] = sha256_bytes(payload)
    result["signature"] = _b64url(private_key.sign(payload))
    return result


def verify_record(record: dict[str, Any], public_key: Ed25519PublicKey) -> bool:
    try:
        payload = canonical_bytes(signed_payload(record))
        if record.get("signed_payload_sha256") != sha256_bytes(payload):
            return False
        public_key.verify(_b64url_decode(record["signature"]), payload)
        return True
    except (InvalidSignature, KeyError, TypeError, ValueError):
        return False


def content_tree_sha256(source_root: Path) -> str:
    included = sorted(
        path for path in source_root.rglob("*")
        if path.is_file() and (path.suffix == ".lean" or path.name in {"lean-toolchain", "lakefile.lean", "lake-manifest.json"})
    )
    digest = hashlib.sha256()
    for path in included:
        relative = path.relative_to(source_root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        file_digest = hashlib.sha256(path.read_bytes()).digest()
        digest.update(file_digest)
    return digest.hexdigest()


def _scan_forbidden_markers(source_root: Path) -> tuple[bool, bool, int]:
    contains_sorry = False
    contains_admit = False
    unapproved_axioms = 0
    for path in source_root.rglob("*.lean"):
        text = path.read_text(encoding="utf-8")
        contains_sorry = contains_sorry or any(line.lstrip().startswith("sorry") or " by sorry" in line for line in text.splitlines())
        contains_admit = contains_admit or any(line.lstrip().startswith("admit") or " by admit" in line for line in text.splitlines())
        unapproved_axioms += sum(1 for line in text.splitlines() if line.lstrip().startswith("axiom "))
    return contains_sorry, contains_admit, unapproved_axioms


def run_strict_lake_build(
    *,
    claim_id: str,
    canonical_claim: dict[str, Any],
    theorem_statement: str,
    theorem_name: str,
    proof_artifact: Path,
    source_root: Path,
    toolchain: str,
    verifier_principal_id: str,
    key_id: str,
    private_key: Ed25519PrivateKey,
    created_at: str | None = None,
    timeout_seconds: int = 600,
) -> dict[str, Any]:
    """Run strict ``lake build`` and sign the resulting content-bound record.

    A missing toolchain, timeout, compiler failure, forbidden marker, or axiom
    produces a signed non-passing witness. Only ``result == passed`` can enter a
    promotion chain.
    """
    source_root = source_root.resolve()
    proof_artifact = proof_artifact.resolve()
    lakefile = source_root / "lakefile.lean"
    toolchain_file = source_root / "lean-toolchain"
    claim_hash = sha256_bytes(canonical_bytes(canonical_claim))
    theorem_hash = sha256_bytes(theorem_statement.encode("utf-8"))
    artifact_hash = sha256_bytes(proof_artifact.read_bytes())
    tree_hash = content_tree_sha256(source_root)
    lakefile_hash = sha256_bytes(lakefile.read_bytes()) if lakefile.is_file() else sha256_bytes(b"")
    contains_sorry, contains_admit, unapproved_axioms = _scan_forbidden_markers(source_root)
    declared_toolchain = toolchain_file.read_text(encoding="utf-8").strip() if toolchain_file.is_file() else ""
    toolchain_matches = declared_toolchain == toolchain
    theorem_pattern = re.compile(rf"^\s*(?:protected\s+|private\s+)?theorem\s+{re.escape(theorem_name)}(?:\s|:)", re.MULTILINE)
    theorem_declared = any(theorem_pattern.search(path.read_text(encoding="utf-8")) for path in source_root.rglob("*.lean"))
    command = ["lake", "build"]
    lake = shutil.which("lake")
    if contains_sorry or contains_admit or unapproved_axioms or not toolchain_matches or not theorem_declared:
        execution = {"returncode": None, "stdout": "", "stderr": "static authority precondition failed", "timed_out": False, "declared_toolchain": declared_toolchain, "theorem_declared": theorem_declared}
        result = "failed_static_scan"
    elif lake is None:
        execution = {"returncode": None, "stdout": "", "stderr": "lake unavailable", "timed_out": False}
        result = "toolchain_unavailable"
    else:
        try:
            completed = subprocess.run(command, cwd=source_root, text=True, capture_output=True, timeout=timeout_seconds)
            execution = {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr, "timed_out": False}
            result = "passed" if completed.returncode == 0 else "failed_lake_build"
        except subprocess.TimeoutExpired as error:
            execution = {"returncode": None, "stdout": error.stdout or "", "stderr": error.stderr or "", "timed_out": True}
            result = "failed_lake_build"
    build_output_hash = sha256_bytes(canonical_bytes(execution))
    theorem_status = "proved" if result == "passed" else ("sorry_stub" if contains_sorry or contains_admit else "axiom_dependent" if unapproved_axioms else "failed")
    created_at = created_at or datetime.now(timezone.utc).isoformat()
    unsigned = {
        "schema_version": "lean_compiler_witness/v2",
        "lean_compiler_witness_id": "lean:" + sha256_bytes(canonical_bytes({"claim": claim_hash, "theorem": theorem_hash, "artifact": artifact_hash, "tree": tree_hash, "output": build_output_hash}))[:32],
        "claim_id": claim_id,
        "claim_content_sha256": claim_hash,
        "theorem_statement_sha256": theorem_hash,
        "proof_artifact_sha256": artifact_hash,
        "source_tree_sha256": tree_hash,
        "lakefile_sha256": lakefile_hash,
        "build_output_sha256": build_output_hash,
        "toolchain": toolchain,
        "command": command,
        "execution_mode": "strict",
        "result": result,
        "contains_sorry": contains_sorry,
        "contains_admit": contains_admit,
        "unapproved_axiom_count": unapproved_axioms,
        "theorem_name": theorem_name,
        "theorem_status": theorem_status,
        "verifier_principal_id": verifier_principal_id,
        "key_id": key_id,
        "signature_algorithm": "Ed25519",
        "created_at": created_at,
    }
    return sign_record(unsigned, private_key)
