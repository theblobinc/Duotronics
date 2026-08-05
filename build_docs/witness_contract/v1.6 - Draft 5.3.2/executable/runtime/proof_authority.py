#!/usr/bin/env python3
"""Fail-closed Lean proof authority for Witness Contract Draft 5.3.2.

The verifier compiles a generated module which imports the submitted proof
artifact and asks Lean to check the named declaration at the exact claimed
type.  Lean's compiled axiom report, not a source-text search, decides whether
the theorem depends on ``sorryAx`` or another unauthorized axiom.

The caller must supply an absolute, independently pinned Lake executable and
its SHA-256 digest.  PATH lookup is deliberately forbidden.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


LEAN_IDENTIFIER = re.compile(r"^(?:[A-Za-z_][A-Za-z0-9_']*\.)*[A-Za-z_][A-Za-z0-9_']*$")
SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
AXIOM_LIST = re.compile(r"depends on axioms:\s*\[([^\]]*)\]", re.DOTALL)
NO_AXIOMS = re.compile(r"does not depend on any axioms")
DEFAULT_AUTHORIZED_AXIOMS = frozenset({"propext", "Quot.sound", "Classical.choice"})
TREE_FILES = frozenset({"lean-toolchain", "lakefile.lean", "lake-manifest.json"})


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def canonical_text(value: Any) -> str:
    return canonical_bytes(value).decode("utf-8")


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


def public_key_raw_b64url(key: Ed25519PublicKey) -> str:
    raw = key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return _b64url(raw)


def public_key_fingerprint(key: Ed25519PublicKey) -> str:
    raw = key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return sha256_bytes(raw)


def signed_payload(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key not in {"signed_payload_sha256", "signature"}}


def signed_payload_canonical_json(record: dict[str, Any]) -> str:
    return canonical_text(signed_payload(record))


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


def register_sqlite_crypto_functions(connection: sqlite3.Connection) -> None:
    """Register deterministic functions required by the 5.3.2 SQL guards.

    A database that does not register these functions cannot insert a signature
    verification binding and therefore cannot create an authoritative gate.
    """

    def sql_sha256(value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        return sha256_bytes(value.encode("utf-8"))

    def sql_key_fingerprint(public_key_b64url: Any) -> str | None:
        try:
            return sha256_bytes(_b64url_decode(str(public_key_b64url)))
        except (TypeError, ValueError):
            return None

    def sql_ed25519_verify(public_key_b64url: Any, payload: Any, signature: Any) -> int:
        try:
            key = Ed25519PublicKey.from_public_bytes(_b64url_decode(str(public_key_b64url)))
            key.verify(_b64url_decode(str(signature)), str(payload).encode("utf-8"))
            return 1
        except (InvalidSignature, TypeError, ValueError):
            return 0

    def sql_is_canonical_json(value: Any) -> int:
        try:
            text = str(value)
            return int(canonical_text(json.loads(text)) == text)
        except (TypeError, ValueError, json.JSONDecodeError):
            return 0

    connection.create_function("wc_sha256", 1, sql_sha256, deterministic=True)
    connection.create_function("wc_public_key_fingerprint", 1, sql_key_fingerprint, deterministic=True)
    connection.create_function("wc_ed25519_verify", 3, sql_ed25519_verify, deterministic=True)
    connection.create_function("wc_is_canonical_json", 1, sql_is_canonical_json, deterministic=True)


def _tree_paths(source_root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in source_root.rglob("*"):
        if path.is_symlink():
            continue
        if path.is_file() and (path.suffix == ".lean" or path.name in TREE_FILES):
            paths.append(path)
    return sorted(paths, key=lambda item: item.relative_to(source_root).as_posix())


def content_tree_sha256(source_root: Path) -> str:
    digest = hashlib.sha256()
    for path in _tree_paths(source_root):
        relative = path.relative_to(source_root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _proof_module(source_root: Path, proof_artifact: Path) -> str:
    relative = proof_artifact.relative_to(source_root)
    if relative.suffix != ".lean":
        raise ValueError("proof artifact must be a .lean source file")
    parts = (*relative.parts[:-1], relative.stem)
    if not parts or any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_']*", part) for part in parts):
        raise ValueError("proof artifact path is not a valid importable Lean module")
    return ".".join(parts)


def _validate_statement(statement: str) -> None:
    if not statement or len(statement.encode("utf-8")) > 65536:
        raise ValueError("claimed theorem statement is empty or exceeds 65536 bytes")
    if any(ord(character) < 0x20 for character in statement) or any(token in statement for token in ("\u2028", "\u2029", "--", "/-", "-/")):
        raise ValueError("claimed theorem statement must be one comment-free Lean term")


def generated_witness_module(*, proof_module: str, theorem_statement: str, theorem_name: str) -> str:
    _validate_statement(theorem_statement)
    if not LEAN_IDENTIFIER.fullmatch(theorem_name):
        raise ValueError("theorem_name is not a valid fully qualified Lean identifier")
    return (
        f"import {proof_module}\n"
        "set_option autoImplicit false\n"
        "set_option warningAsError true\n"
        f"example : ({theorem_statement}) := by\n"
        f"  exact {theorem_name}\n"
        f"#print axioms {theorem_name}\n"
    )


def _inspect_axioms(output: str) -> tuple[bool, list[str]]:
    matches = AXIOM_LIST.findall(output)
    if matches:
        values = [item.strip().strip("'\"") for item in matches[-1].split(",") if item.strip()]
        return True, sorted(set(values))
    if NO_AXIOMS.search(output):
        return True, []
    return False, []


def _safe_read_hash(path: Path) -> str:
    return sha256_bytes(path.read_bytes()) if path.is_file() else sha256_bytes(b"")


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
    lake_executable: Path | None = None,
    expected_lake_sha256: str | None = None,
    authorized_axioms: Iterable[str] = DEFAULT_AUTHORIZED_AXIOMS,
    created_at: str | None = None,
    timeout_seconds: int = 600,
) -> dict[str, Any]:
    """Compile an exact statement-binding module and sign the fail-closed result."""

    source_root = source_root.resolve()
    proof_input = proof_artifact
    proof_artifact = proof_artifact.resolve()
    lakefile = source_root / "lakefile.lean"
    toolchain_file = source_root / "lean-toolchain"
    claim_hash = sha256_bytes(canonical_bytes(canonical_claim))
    theorem_hash = sha256_bytes(theorem_statement.encode("utf-8"))
    artifact_hash = _safe_read_hash(proof_artifact)
    lakefile_hash = _safe_read_hash(lakefile)
    declared_toolchain = toolchain_file.read_text(encoding="utf-8").strip() if toolchain_file.is_file() else ""

    result = "failed_static_scan"
    theorem_status = "failed"
    proof_module = "invalid"
    generated_hash = sha256_bytes(b"")
    generated_relative = "unavailable"
    exact_build_target = "unavailable"
    compiler_hash = sha256_bytes(b"")
    command = ["unavailable"]
    axiom_dependencies: list[str] = []
    axiom_inspection_complete = False
    statement_binding_confirmed = False
    warnings_as_errors = False
    precondition_errors: list[str] = []
    generated_path: Path | None = None

    if not source_root.is_dir():
        precondition_errors.append("source_root is not a directory")
    if not proof_artifact.is_file():
        precondition_errors.append("proof artifact is not a regular file")
    try:
        proof_artifact.relative_to(source_root)
    except ValueError:
        precondition_errors.append("proof artifact is outside source_root")
    if proof_input.is_symlink() or any(parent.is_symlink() for parent in proof_input.parents if parent != source_root.parent):
        precondition_errors.append("proof artifact path contains a symbolic link")
    if not lakefile.is_file() or not toolchain_file.is_file():
        precondition_errors.append("Lean project metadata is incomplete")
    if declared_toolchain != toolchain:
        precondition_errors.append("declared Lean toolchain does not match the authorized toolchain")
    if not LEAN_IDENTIFIER.fullmatch(theorem_name):
        precondition_errors.append("invalid theorem identifier")
    try:
        _validate_statement(theorem_statement)
    except ValueError as error:
        precondition_errors.append(str(error))
    try:
        proof_module = _proof_module(source_root, proof_artifact)
    except ValueError as error:
        precondition_errors.append(str(error))
    symlinked_sources = [path.relative_to(source_root).as_posix() for path in source_root.rglob("*.lean") if path.is_symlink()]
    if symlinked_sources:
        precondition_errors.append(f"symbolic-link Lean sources are forbidden: {symlinked_sources[:3]}")

    lake: Path | None = None
    if not precondition_errors:
        if lake_executable is None or expected_lake_sha256 is None:
            result = "toolchain_unavailable"
            precondition_errors.append("an absolute pinned Lake executable and expected SHA-256 are required; PATH lookup is forbidden")
        elif not lake_executable.is_absolute():
            result = "toolchain_unavailable"
            precondition_errors.append("Lake executable path must be absolute")
        else:
            lake = lake_executable.resolve()
            if not lake.is_file() or not os.access(lake, os.X_OK):
                result = "toolchain_unavailable"
                precondition_errors.append("configured Lake executable is unavailable or not executable")
            elif not SHA256_HEX.fullmatch(expected_lake_sha256):
                result = "toolchain_unavailable"
                precondition_errors.append("expected Lake executable SHA-256 is invalid")
            else:
                compiler_hash = sha256_bytes(lake.read_bytes())
                if compiler_hash != expected_lake_sha256:
                    result = "toolchain_unavailable"
                    precondition_errors.append("Lake executable digest does not match the independent pin")

    execution: dict[str, Any]
    if precondition_errors:
        execution = {
            "returncode": None,
            "stdout": "",
            "stderr": "; ".join(precondition_errors),
            "timed_out": False,
            "declared_toolchain": declared_toolchain,
        }
    else:
        assert lake is not None
        generated_directory = source_root / ".witness_authority"
        generated_directory.mkdir(mode=0o700, exist_ok=True)
        module_text = generated_witness_module(
            proof_module=proof_module,
            theorem_statement=theorem_statement,
            theorem_name=theorem_name,
        )
        descriptor = sha256_bytes(canonical_bytes({"claim": claim_hash, "theorem": theorem_hash, "artifact": artifact_hash}))[:24]
        handle, generated_name = tempfile.mkstemp(prefix=f"Check_{descriptor}_", suffix=".lean", dir=generated_directory)
        os.close(handle)
        generated_path = Path(generated_name)
        try:
            generated_path.write_text(module_text, encoding="utf-8")
            generated_relative = generated_path.relative_to(source_root).as_posix()
            generated_hash = sha256_bytes(generated_path.read_bytes())
            exact_build_target = generated_relative
            command = [str(lake), "env", "lean", "-DwarningAsError=true", exact_build_target]
            tree_hash = content_tree_sha256(source_root)
            warnings_as_errors = True
            try:
                completed = subprocess.run(
                    command,
                    cwd=source_root,
                    text=True,
                    capture_output=True,
                    timeout=timeout_seconds,
                    env={**os.environ, "LEAN_ABORT_ON_PANIC": "1"},
                )
                execution = {
                    "returncode": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                    "timed_out": False,
                    "declared_toolchain": declared_toolchain,
                }
                combined = f"{completed.stdout}\n{completed.stderr}"
                if completed.returncode == 0:
                    axiom_inspection_complete, axiom_dependencies = _inspect_axioms(combined)
                    statement_binding_confirmed = axiom_inspection_complete
                    contains_sorry = any(name == "sorryAx" or name.endswith(".sorryAx") for name in axiom_dependencies)
                    unauthorized = sorted(set(axiom_dependencies) - set(authorized_axioms))
                    if contains_sorry:
                        result = "failed_lake_build"
                        theorem_status = "sorry_stub"
                    elif not axiom_inspection_complete:
                        result = "failed_lake_build"
                        theorem_status = "failed"
                    elif unauthorized:
                        result = "failed_lake_build"
                        theorem_status = "axiom_dependent"
                    else:
                        result = "passed"
                        theorem_status = "proved"
                else:
                    result = "failed_lake_build"
                    theorem_status = "failed"
            except subprocess.TimeoutExpired as error:
                execution = {
                    "returncode": None,
                    "stdout": error.stdout or "",
                    "stderr": error.stderr or "",
                    "timed_out": True,
                    "declared_toolchain": declared_toolchain,
                }
                result = "failed_lake_build"
                theorem_status = "failed"
        finally:
            if generated_path is not None:
                generated_path.unlink(missing_ok=True)
            try:
                generated_directory.rmdir()
            except OSError:
                pass

    if "tree_hash" not in locals():
        tree_hash = content_tree_sha256(source_root) if source_root.is_dir() else sha256_bytes(b"")
    contains_sorry = any(name == "sorryAx" or name.endswith(".sorryAx") for name in axiom_dependencies)
    unauthorized_axioms = sorted(set(axiom_dependencies) - set(authorized_axioms))
    contains_admit = False  # Lean elaborates both sorry/admit through sorryAx; source spelling is non-authoritative.
    build_output_hash = sha256_bytes(canonical_bytes(execution))
    created_at = created_at or datetime.now(timezone.utc).isoformat()
    unsigned = {
        "schema_version": "lean_compiler_witness/v2",
        "lean_compiler_witness_id": "lean:" + sha256_bytes(canonical_bytes({
            "claim": claim_hash,
            "theorem": theorem_hash,
            "artifact": artifact_hash,
            "tree": tree_hash,
            "generated": generated_hash,
            "compiler": compiler_hash,
            "output": build_output_hash,
        }))[:32],
        "claim_id": claim_id,
        "claim_content_sha256": claim_hash,
        "theorem_statement_sha256": theorem_hash,
        "proof_artifact_sha256": artifact_hash,
        "proof_artifact_relative_path": (
            proof_artifact.relative_to(source_root).as_posix()
            if source_root.is_dir() and proof_artifact.is_relative_to(source_root)
            else "unavailable"
        ),
        "proof_module": proof_module,
        "source_tree_sha256": tree_hash,
        "lakefile_sha256": lakefile_hash,
        "generated_witness_module_sha256": generated_hash,
        "generated_witness_module_path": generated_relative,
        "exact_build_target": exact_build_target,
        "compiler_executable_sha256": compiler_hash,
        "build_output_sha256": build_output_hash,
        "toolchain": toolchain,
        "command": command,
        "execution_mode": "strict",
        "result": result,
        "contains_sorry": contains_sorry,
        "contains_admit": contains_admit,
        "unapproved_axiom_count": len(unauthorized_axioms),
        "axiom_dependencies": axiom_dependencies,
        "axiom_inspection_complete": axiom_inspection_complete,
        "statement_binding_confirmed": statement_binding_confirmed,
        "warnings_as_errors": warnings_as_errors,
        "theorem_name": theorem_name,
        "theorem_status": theorem_status,
        "verifier_principal_id": verifier_principal_id,
        "key_id": key_id,
        "signature_algorithm": "Ed25519",
        "signed_payload_sha256": "",  # removed by sign_record before signing
        "signature": "",  # removed by sign_record before signing
        "created_at": created_at,
    }
    return sign_record(unsigned, private_key)
