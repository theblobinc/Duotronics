#!/usr/bin/env python3
"""Independent, test-only attestation authority for the witness sandbox VM.

This program runs in its own rootless Podman container. It consumes an exact
activation challenge, creates one ephemeral ML-DSA-87 issuer per gate, writes
only public trust material and signed evidence, and can never issue
production-eligible authority.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from pqcrypto.sign import ml_dsa_87

PROFILE = "sandbox-test-only"
CRYPTO_PROFILE = "duotronic-pq-2026.1"
ENVIRONMENT = "witness-harness-vm"
DEFAULT_NAMESPACE = "duotronic://authority/sandbox/witness-harness-vm"
ROOT = Path("/opt/harness")
PROFILE_REGISTRY = json.loads(
    (ROOT / "cryptographic_profile_registry_v1.json").read_text(encoding="utf-8")
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True,
        separators=(",", ":"),
    ).encode()


def shake(value: bytes) -> str:
    return hashlib.shake_256(value).hexdigest(64)


def duoid(label: str, value: Any) -> str:
    raw = hashlib.shake_256(label.encode() + b"\x00" + canonical_bytes(value)).digest(64)
    return "duoid:shake256-512:" + base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def claim_value(name: str, request: dict[str, Any], bundle: dict[str, Any]) -> Any:
    gate_id = request["gate_id"]
    subject_id = bundle["subject_id"]
    contract_version = bundle["contract_version"]
    values: dict[str, Any] = {
        "decision": "approved",
        "contract_version": contract_version,
        "corpus_root_id": subject_id,
        "gate_snapshot_id": duoid("DUOTRONIC/SANDBOX-GATE-SNAPSHOT/v1", request),
        "subject_image_digest": duoid("DUOTRONIC/SANDBOX-IMAGE/v1", request),
        "source_revision": subject_id,
        "builder_identity": f"sandbox-builder:{gate_id}",
        "dependency_closure_id": duoid("DUOTRONIC/SANDBOX-DEPENDENCIES/v1", request),
        "verifier_artifact_id": duoid("DUOTRONIC/SANDBOX-VERIFIER/v1", request),
        "build_a_artifact_id": request["measurement_id"],
        "build_b_artifact_id": request["measurement_id"],
        "commit_id": subject_id,
        "remote_origin": "sandbox-bound-source-snapshot",
        "reviewed_revision": request["measurement_id"],
    }
    return values.get(name, True)


def validate_bundle(bundle: dict[str, Any]) -> None:
    if bundle.get("schema") != "duotronic-external-attestation-requests/v1":
        raise ValueError("unsupported attestation request schema")
    requests = bundle.get("requests")
    if not isinstance(requests, list) or len(requests) not in {1, 12}:
        raise ValueError("attestor accepts one independently isolated gate or the complete 12-gate bundle")
    if len({item.get("gate_id") for item in requests}) != len(requests):
        raise ValueError("gate requests must be unique")
    run_ids = {item.get("probe", {}).get("run_id") for item in requests}
    if len(run_ids) != 1 or None in run_ids:
        raise ValueError("requests must bind one exact probe run")
    for item in requests:
        if item.get("probe", {}).get("exit_code") != 0:
            raise ValueError(f"probe did not pass: {item.get('gate_id')}")
        if item.get("measurement_id") != item.get("probe", {}).get("result_id"):
            raise ValueError(f"measurement binding mismatch: {item.get('gate_id')}")


def issue(bundle: dict[str, Any], evidence_dir: Path, namespace: str) -> dict[str, Any]:
    validate_bundle(bundle)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    issued = datetime.now(timezone.utc)
    expires = issued + timedelta(hours=24)
    keys: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []

    for request in bundle["requests"]:
        gate_id = request["gate_id"]
        public_key, secret_key = ml_dsa_87.generate_keypair()
        issuer_id = f"duotronic-sandbox-attestor:{gate_id}"
        key_id = duoid(
            "DUOTRONIC/SANDBOX-ATTESTOR-KEY/v1",
            {"gate_id": gate_id, "public_key": b64(public_key), "namespace": namespace},
        )
        claims = {
            name: claim_value(name, request, bundle)
            for name in request.get("required_claims", [])
        }
        claims.update({
            "sandbox_only": True,
            "production_eligible": False,
            "independent_attestor_container": True,
            "exact_probe_bound": True,
        })
        challenge_body = {
            "contract_version": bundle["contract_version"],
            "gate_id": gate_id,
            "subject_id": bundle["subject_id"],
            "probe": request["probe"],
        }
        challenge_id = duoid(
            "DUOTRONIC/EXTERNAL-GATE-CHALLENGE/v1", challenge_body
        )
        replay_nonce = duoid(
            "DUOTRONIC/EXTERNAL-GATE-REPLAY-NONCE/v1",
            {"challenge_id": challenge_id, "key_id": key_id},
        )
        source_instance_id = duoid(
            "DUOTRONIC/INDEPENDENT-ATTESTOR-INSTANCE/v1",
            {"gate_id": gate_id, "key_id": key_id, "challenge_id": challenge_id},
        )
        unsigned = {
            "schema": "duotronic-external-gate-evidence/v2",
            "contract_version": bundle["contract_version"],
            "gate_id": gate_id,
            "subject_id": bundle["subject_id"],
            "issuer_id": issuer_id,
            "key_id": key_id,
            "challenge_id": challenge_id,
            "replay_nonce": replay_nonce,
            "source_instance_id": source_instance_id,
            "provenance": {
                "source_kind": "independent-sandbox-external-attestor",
                "isolation": "distinct-rootless-podman-attestor",
                "measurement_id": request["measurement_id"],
                "probe_run_id": request["probe"]["run_id"],
                "independent_key": True,
            },
            "cryptographic_profile": CRYPTO_PROFILE,
            "profile_registry_id": duoid(
                "DUOTRONIC/CRYPTOGRAPHIC-PROFILE-REGISTRY/v1",
                PROFILE_REGISTRY,
            ),
            "issued_at": issued.isoformat(),
            "expires_at": expires.isoformat(),
            "claims": claims,
            "probe": request["probe"],
            "authority_profile": PROFILE,
            "authority_namespace": namespace,
            "evidence_environment": ENVIRONMENT,
            "production_eligible": False,
            "signature_suite": "ML-DSA-87",
        }
        payload = canonical_bytes(unsigned)
        signature = ml_dsa_87.sign(secret_key, payload)
        evidence = {
            **unsigned,
            "signed_payload_shake256_512": shake(payload),
            "signature_base64url": b64(signature),
        }
        filename = request.get("evidence_filename") or f"{gate_id}.json"
        (evidence_dir / filename).write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        keys.append({
            "issuer_id": issuer_id,
            "key_id": key_id,
            "public_key_base64url": b64(public_key),
            "status": "active",
            "scopes": request.get("issuer_scopes", []),
            "managed_by_harness": False,
            "managed_by": "independent-sandbox-attestation-container",
            "authority_profile": PROFILE,
            "authority_namespace": namespace,
            "production_eligible": False,
        })
        records.append({
            "gate_id": gate_id,
            "issuer_id": issuer_id,
            "key_id": key_id,
            "evidence_file": filename,
            "evidence_id": duoid("DUOTRONIC/SANDBOX-EVIDENCE/v1", evidence),
        })

    trust = {
        "schema": "duotronic-sandbox-trust-registry/v1",
        "authority_profile": PROFILE,
        "authority_namespace": namespace,
        "evidence_environment": ENVIRONMENT,
        "production_eligible": False,
        "cryptographic_profile": CRYPTO_PROFILE,
        "profile_registry_id": duoid(
            "DUOTRONIC/CRYPTOGRAPHIC-PROFILE-REGISTRY/v1", PROFILE_REGISTRY
        ),
        "generated_at": issued.isoformat(),
        "revocations": [],
        "keys": keys,
    }
    (evidence_dir / "trust_registry.json").write_text(
        json.dumps(trust, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {
        "schema": "duotronic-sandbox-attestation-manifest/v1",
        "authority_profile": PROFILE,
        "authority_namespace": namespace,
        "production_eligible": False,
        "probe_run_id": bundle["requests"][0]["probe"]["run_id"],
        "subject_id": bundle["subject_id"],
        "contract_version": bundle["contract_version"],
        "issued_at": issued.isoformat(),
        "issuer_count": len(keys),
        "evidence_count": len(records),
        "records": records,
    }
    manifest["manifest_id"] = duoid("DUOTRONIC/SANDBOX-ATTESTATION-MANIFEST/v1", manifest)
    (evidence_dir / "sandbox-attestation-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue VM-sandbox-only gate evidence")
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--authority-namespace", default=DEFAULT_NAMESPACE)
    args = parser.parse_args()
    bundle = json.loads(args.requests.read_text(encoding="utf-8"))
    result = issue(bundle, args.evidence_dir, args.authority_namespace)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
