#!/usr/bin/env python3
"""Production launcher for the governed cache-audit anchor service.

The bundled file-backed anchor is deliberately development-only.  This launcher
refuses an authoritative configuration unless an independently monotonic backend
is supplied by the deployment.  It still provides a complete production-shape
entry point for non-authoritative integration and fail-closed testing.
"""
from __future__ import annotations

import argparse
import os
import signal
import threading
from datetime import datetime, timezone
from pathlib import Path

from cache_audit import validate_governed_signing_registry
from cache_audit_services import AuditAnchorServer, FileBackedMonotonicAnchorStore
from proof_authority import (
    CanonicalSchemaValidator, _private_key_from_bytes, _public_key_from_bytes,
    load_trusted_canonical_json, public_key_raw_b64url, secure_read_bytes,
    validate_trusted_root_ancestry,
)


def _drop(uid: int, gid: int, supplementary_gids: list[int]) -> None:
    if os.geteuid() == 0:
        os.setgroups(supplementary_gids)
        os.setgid(gid)
        os.setuid(uid)
    if os.geteuid() != uid or os.getegid() != gid:
        raise RuntimeError("cache audit anchor launcher identity does not match configuration")


def load_anchor_server(config_root: Path) -> AuditAnchorServer:
    bootstrap = load_trusted_canonical_json(config_root, "anchor-service-config.json", expected_uid=os.geteuid())
    allowed = {
        "schema_version", "service_uid", "service_gid", "supplementary_gids",
        "schema_root", "governance_public_key_file", "anchor_private_key_file",
        "anchor_public_key_file", "anchor_registry_file", "anchor_key_id",
        "anchor_principal_id", "ledger_path", "socket_path", "publisher_uid",
        "publisher_gid", "publisher_principal_id", "publisher_request_public_key_file",
        "publisher_request_key_id", "authoritative", "provision_ledger",
    }
    if set(bootstrap) != allowed or bootstrap.get("schema_version") != "cache_audit_anchor_service_config/v1":
        raise RuntimeError("cache audit anchor service configuration is not canonical")
    _drop(int(bootstrap["service_uid"]), int(bootstrap["service_gid"]), [int(v) for v in bootstrap["supplementary_gids"]])
    expected_uid = os.geteuid()
    validate_trusted_root_ancestry(config_root, expected_uid=expected_uid)
    config = load_trusted_canonical_json(config_root, "anchor-service-config.json", expected_uid=expected_uid)
    schema_root = config_root / config["schema_root"]
    validator = CanonicalSchemaValidator(schema_root, expected_uid=expected_uid)
    governance_key = _public_key_from_bytes(secure_read_bytes(config_root, config["governance_public_key_file"], expected_uid=expected_uid))
    registry = load_trusted_canonical_json(config_root, config["anchor_registry_file"], expected_uid=expected_uid)
    registry_sha256, records, verification_keys = validate_governed_signing_registry(
        registry, governance_key, schema_validator=validator,
        surface="cache_audit_anchor_registry", required_scope="cache_audit_monotonic_anchor_signing",
        evaluated_at=datetime.now(timezone.utc),
    )
    key_id = config["anchor_key_id"]
    record = records.get(key_id)
    if record is None or record.get("principal_id") != config["anchor_principal_id"]:
        raise RuntimeError("configured anchor key is not governed")
    signing_key = _private_key_from_bytes(secure_read_bytes(config_root, config["anchor_private_key_file"], expected_uid=expected_uid))
    public_key = _public_key_from_bytes(secure_read_bytes(config_root, config["anchor_public_key_file"], expected_uid=expected_uid))
    if public_key_raw_b64url(signing_key.public_key()) != public_key_raw_b64url(public_key):
        raise RuntimeError("anchor private and public keys do not match")
    if public_key_raw_b64url(public_key) != public_key_raw_b64url(verification_keys[key_id]):
        raise RuntimeError("anchor key does not match governed registry")
    if bool(config["authoritative"]):
        raise RuntimeError("file-backed anchor is development-only and cannot enable authority")
    store = FileBackedMonotonicAnchorStore(
        Path(config["ledger_path"]), signing_key, key_id=key_id,
        signer_principal_id=config["anchor_principal_id"],
        anchor_registry_sha256=registry_sha256, anchor_registry_records=records,
        schema_validator=validator, provision=bool(config["provision_ledger"]), expected_uid=expected_uid,
    )
    publisher_request_key = _public_key_from_bytes(
        secure_read_bytes(config_root, config["publisher_request_public_key_file"], expected_uid=expected_uid)
    )
    return AuditAnchorServer(
        Path(config["socket_path"]), store, schema_validator=validator,
        publisher_uid=int(config["publisher_uid"]), publisher_gid=int(config["publisher_gid"]),
        publisher_principal_id=config["publisher_principal_id"],
        request_verification_keys={config["publisher_request_key_id"]: publisher_request_key},
        socket_uid=expected_uid, socket_gid=os.getegid(),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-root", default="/etc/witness-audit-anchor")
    args = parser.parse_args()
    server = load_anchor_server(Path(args.config_root))
    stop = threading.Event()
    def shutdown(_signum: int, _frame: object) -> None:
        if not stop.is_set():
            stop.set()
            threading.Thread(target=server.server.shutdown, daemon=True).start()
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    try:
        server.server.serve_forever(poll_interval=0.1)
    finally:
        server.server.server_close()
        try:
            server.server.socket_path.unlink()
        except FileNotFoundError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
