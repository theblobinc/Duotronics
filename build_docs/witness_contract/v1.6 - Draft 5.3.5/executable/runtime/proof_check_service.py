#!/usr/bin/env python3
"""Synchronous request boundary for the Draft 5.3.5 proof-check service.

The client selects a governed compiler profile and an already-ingested source
bundle.  Executable paths, hashes, timestamps, authority outputs, and host
environment fields are rejected.  Deployment adapters may call
``ProofCheckApplication.handle`` from the authenticated OpenAPI endpoint.
"""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Any

from proof_authority import (
    ProofAuthorityService, ProofPolicyResolver, _public_key_from_bytes,
    canonical_bytes, sha256_bytes, load_production_authority_service,
    secure_read_bytes, validate_trusted_root_ancestry,
)


ARTIFACT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
REQUEST_FIELDS = frozenset({
    "request_id", "idempotency_key", "subject_id",
    "compiler_profile_id", "claim_id", "canonical_claim", "theorem_statement",
    "theorem_name", "source_bundle_id", "proof_artifact_relative_path",
    "policy_decision_id",
})


class ProofCheckApplication:
    def __init__(self, authority: ProofAuthorityService, artifact_store: Path, policy_resolver: ProofPolicyResolver):
        self.authority = authority
        self.artifact_store = artifact_store.resolve()
        self.policy_resolver = policy_resolver
        self._idempotency: dict[str, tuple[str, dict[str, Any]]] = {}
        self._inflight: dict[str, tuple[str, threading.Event]] = {}
        self._idempotency_lock = threading.Lock()

    def handle(self, request: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(request, dict) or set(request) != REQUEST_FIELDS:
            raise ValueError("proof-check request fields do not match the canonical request contract")
        if not isinstance(request["request_id"], str) or not ARTIFACT_ID.fullmatch(request["request_id"]):
            raise ValueError("invalid request identifier")
        if not isinstance(request["idempotency_key"], str) or not ARTIFACT_ID.fullmatch(request["idempotency_key"]):
            raise ValueError("invalid idempotency key")
        request_sha256 = sha256_bytes(canonical_bytes(request))
        idempotency_key = request["idempotency_key"]
        while True:
            with self._idempotency_lock:
                prior = self._idempotency.get(idempotency_key)
                if prior is not None:
                    if prior[0] != request_sha256:
                        raise ValueError("idempotency key was already used for a different request")
                    return json.loads(json.dumps(prior[1]))
                active = self._inflight.get(idempotency_key)
                if active is None:
                    completion = threading.Event()
                    self._inflight[idempotency_key] = (request_sha256, completion)
                    break
                if active[0] != request_sha256:
                    raise ValueError("idempotency key is in flight for a different request")
                completion = active[1]
            completion.wait()
        try:
            bundle_id = request["source_bundle_id"]
            relative = request["proof_artifact_relative_path"]
            if not isinstance(bundle_id, str) or not ARTIFACT_ID.fullmatch(bundle_id):
                raise ValueError("invalid source bundle identifier")
            if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
                raise ValueError("proof artifact must be a bundle-relative path")
            resolved_policy = self.policy_resolver.resolve(
                request["policy_decision_id"], subject_id=request["subject_id"],
                operation="proof_check", compiler_profile_id=request["compiler_profile_id"],
                source_bundle_id=bundle_id,
            )
            source_root = (self.artifact_store / bundle_id).resolve()
            try:
                source_root.relative_to(self.artifact_store)
            except ValueError as error:
                raise ValueError("source bundle escapes the configured artifact store") from error
            artifact = (source_root / relative).resolve()
            compiler_witness = self.authority.verify(
                compiler_profile_id=request["compiler_profile_id"], claim_id=request["claim_id"],
                canonical_claim=request["canonical_claim"], theorem_statement=request["theorem_statement"],
                theorem_name=request["theorem_name"], proof_artifact=artifact, source_root=source_root,
                policy_decision_id=resolved_policy.policy_decision_id,
                policy_decision_sha256=resolved_policy.canonical_record_sha256,
            )
            if compiler_witness.get("policy_decision_id") != resolved_policy.policy_decision_id or compiler_witness.get("policy_decision_sha256") != resolved_policy.canonical_record_sha256:
                raise RuntimeError("authority returned a result with a different policy binding")
            result = {
                "schema_version": "proof_check_service_result/v3", "request_id": request["request_id"],
                "idempotency_key": idempotency_key, "status": compiler_witness["result"],
                "claim_id": request["claim_id"], "policy_decision_id": resolved_policy.policy_decision_id,
                "policy_decision_sha256": resolved_policy.canonical_record_sha256,
                "source_bundle_id": bundle_id, "compiler_witness": compiler_witness,
            }
        except Exception:
            with self._idempotency_lock:
                active = self._inflight.pop(idempotency_key, None)
                if active is not None:
                    active[1].set()
            raise
        with self._idempotency_lock:
            self._idempotency[idempotency_key] = (request_sha256, result)
            active = self._inflight.pop(idempotency_key)
            active[1].set()
            return json.loads(json.dumps(result))


def load_production_application(config_root: Path = Path("/etc/witness-authority")) -> ProofCheckApplication:
    import os
    validate_trusted_root_ancestry(config_root, expected_uid=os.getuid())
    config = json.loads(secure_read_bytes(config_root, "service-config.json", expected_uid=os.getuid()).decode("utf-8"))
    artifact_store = Path(config["artifact_store_root"])
    if not artifact_store.is_absolute() or not artifact_store.is_dir() or artifact_store.is_symlink():
        raise RuntimeError("artifact store must be an absolute non-symlink directory")
    governance_key = _public_key_from_bytes(secure_read_bytes(config_root, config["governance_public_key_file"], expected_uid=os.getuid()))
    policy_registry = json.loads(secure_read_bytes(config_root, config["policy_registry_file"], expected_uid=os.getuid()).decode("utf-8"))
    return ProofCheckApplication(
        authority=load_production_authority_service(config_root),
        artifact_store=artifact_store,
        policy_resolver=ProofPolicyResolver(policy_registry, governance_key),
    )


__all__ = ["ProofCheckApplication", "load_production_application"]
