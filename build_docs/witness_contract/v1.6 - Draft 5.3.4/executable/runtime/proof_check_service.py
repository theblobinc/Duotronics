#!/usr/bin/env python3
"""Request boundary for the Draft 5.3.4 proof-check service.

The client selects a governed compiler profile and an already-ingested source
bundle.  Executable paths, hashes, timestamps, authority outputs, and host
environment fields are rejected.  Deployment adapters may call
``ProofCheckApplication.handle`` from the authenticated OpenAPI endpoint.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from proof_authority import ProofAuthorityService, load_production_authority_service, secure_read_bytes, validate_trusted_root_ancestry


ARTIFACT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
REQUEST_FIELDS = frozenset({
    "compiler_profile_id", "claim_id", "canonical_claim", "theorem_statement",
    "theorem_name", "source_bundle_id", "proof_artifact_relative_path",
    "policy_decision_id",
})


class ProofCheckApplication:
    def __init__(self, authority: ProofAuthorityService, artifact_store: Path):
        self.authority = authority
        self.artifact_store = artifact_store.resolve()

    def handle(self, request: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(request, dict) or set(request) != REQUEST_FIELDS:
            raise ValueError("proof-check request fields do not match the canonical request contract")
        bundle_id = request["source_bundle_id"]
        relative = request["proof_artifact_relative_path"]
        if not isinstance(bundle_id, str) or not ARTIFACT_ID.fullmatch(bundle_id):
            raise ValueError("invalid source bundle identifier")
        if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError("proof artifact must be a bundle-relative path")
        source_root = (self.artifact_store / bundle_id).resolve()
        try:
            source_root.relative_to(self.artifact_store)
        except ValueError as error:
            raise ValueError("source bundle escapes the configured artifact store") from error
        artifact = (source_root / relative).resolve()
        compiler_witness = self.authority.verify(
            compiler_profile_id=request["compiler_profile_id"],
            claim_id=request["claim_id"],
            canonical_claim=request["canonical_claim"],
            theorem_statement=request["theorem_statement"],
            theorem_name=request["theorem_name"],
            proof_artifact=artifact,
            source_root=source_root,
        )
        return {
            "schema_version": "proof_check_service_result/v2",
            "status": compiler_witness["result"],
            "claim_id": request["claim_id"],
            "policy_decision_id": request["policy_decision_id"],
            "source_bundle_id": bundle_id,
            "compiler_witness": compiler_witness,
        }


def load_production_application(config_root: Path = Path("/etc/witness-authority")) -> ProofCheckApplication:
    import os
    validate_trusted_root_ancestry(config_root, expected_uid=os.getuid())
    config = json.loads(secure_read_bytes(config_root, "service-config.json", expected_uid=os.getuid()).decode("utf-8"))
    artifact_store = Path(config["artifact_store_root"])
    if not artifact_store.is_absolute() or not artifact_store.is_dir() or artifact_store.is_symlink():
        raise RuntimeError("artifact store must be an absolute non-symlink directory")
    return ProofCheckApplication(
        authority=load_production_authority_service(config_root),
        artifact_store=artifact_store,
    )


__all__ = ["ProofCheckApplication", "load_production_application"]
