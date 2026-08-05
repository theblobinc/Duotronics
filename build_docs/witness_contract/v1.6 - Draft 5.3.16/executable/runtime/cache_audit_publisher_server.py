#!/usr/bin/env python3
"""Production launcher for the authenticated cache-audit publisher service."""
from __future__ import annotations

import argparse
import os
import signal
import threading
from datetime import datetime, timezone
from pathlib import Path

from cache_audit import SignedAppendOnlyAuditSink, UnixSocketAuditAnchorClient, validate_governed_signing_registry
from cache_audit_services import AuditPublisherServer, DurableEventIdIndex
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
        raise RuntimeError("cache audit publisher launcher identity does not match configuration")


def load_publisher_server(config_root: Path) -> AuditPublisherServer:
    bootstrap = load_trusted_canonical_json(config_root, "publisher-service-config.json", expected_uid=os.geteuid())
    allowed = {
        "schema_version", "service_uid", "service_gid", "supplementary_gids", "schema_root",
        "governance_public_key_file", "record_private_key_file", "record_public_key_file",
        "record_registry_file", "record_key_id", "record_principal_id",
        "receipt_private_key_file", "receipt_public_key_file", "receipt_registry_file",
        "receipt_key_id", "receipt_principal_id", "publisher_request_private_key_file",
        "publisher_request_key_id", "publisher_principal_id", "anchor_public_key_file",
        "anchor_registry_file", "anchor_socket_path", "anchor_socket_uid", "anchor_socket_gid",
        "anchor_socket_mode", "proof_request_public_key_file", "proof_request_key_id",
        "proof_service_uid", "proof_service_gid", "proof_service_principal_id",
        "publisher_socket_path", "segment_id", "log_path", "checkpoint_path",
        "event_index_path", "recovery_consumed_ledger_path", "maximum_event_records",
        "maximum_log_bytes", "terminal_seal_reserve_bytes", "provision_segment",
    }
    if set(bootstrap) != allowed or bootstrap.get("schema_version") != "cache_audit_publisher_service_config/v1":
        raise RuntimeError("cache audit publisher service configuration is not canonical")
    _drop(int(bootstrap["service_uid"]), int(bootstrap["service_gid"]), [int(v) for v in bootstrap["supplementary_gids"]])
    expected_uid = os.geteuid()
    validate_trusted_root_ancestry(config_root, expected_uid=expected_uid)
    config = load_trusted_canonical_json(config_root, "publisher-service-config.json", expected_uid=expected_uid)
    validator = CanonicalSchemaValidator(config_root / config["schema_root"], expected_uid=expected_uid)
    governance_key = _public_key_from_bytes(secure_read_bytes(config_root, config["governance_public_key_file"], expected_uid=expected_uid))

    def registry(name: str, surface: str, scope: str):
        value = load_trusted_canonical_json(config_root, config[name], expected_uid=expected_uid)
        return validate_governed_signing_registry(
            value, governance_key, schema_validator=validator, surface=surface,
            required_scope=scope, evaluated_at=datetime.now(timezone.utc),
        )

    record_sha, record_records, record_keys = registry("record_registry_file", "cache_audit_signing_registry", "cache_audit_record_signing")
    receipt_sha, receipt_records, receipt_keys = registry("receipt_registry_file", "cache_audit_signing_registry", "cache_audit_receipt_signing")
    anchor_sha, anchor_records, anchor_keys = registry("anchor_registry_file", "cache_audit_anchor_registry", "cache_audit_monotonic_anchor_signing")

    def private_pair(private_file: str, public_file: str, key_id: str, governed: dict):
        private = _private_key_from_bytes(secure_read_bytes(config_root, config[private_file], expected_uid=expected_uid))
        public = _public_key_from_bytes(secure_read_bytes(config_root, config[public_file], expected_uid=expected_uid))
        if public_key_raw_b64url(private.public_key()) != public_key_raw_b64url(public):
            raise RuntimeError("configured audit keypair does not match")
        if public_key_raw_b64url(public) != public_key_raw_b64url(governed[key_id]):
            raise RuntimeError("configured audit keypair is not governed")
        return private

    record_key = private_pair("record_private_key_file", "record_public_key_file", config["record_key_id"], record_keys)
    receipt_key = private_pair("receipt_private_key_file", "receipt_public_key_file", config["receipt_key_id"], receipt_keys)
    publisher_request_key = _private_key_from_bytes(secure_read_bytes(config_root, config["publisher_request_private_key_file"], expected_uid=expected_uid))
    anchor_client = UnixSocketAuditAnchorClient(
        Path(config["anchor_socket_path"]), verification_keys_by_id=anchor_keys,
        anchor_signing_registry_sha256=anchor_sha, anchor_registry_records=anchor_records,
        schema_validator=validator, request_signing_key=publisher_request_key,
        request_signer_key_id=config["publisher_request_key_id"],
        peer_principal_id=config["publisher_principal_id"],
        expected_socket_uid=int(config["anchor_socket_uid"]), expected_socket_gid=int(config["anchor_socket_gid"]),
        expected_socket_mode=int(config["anchor_socket_mode"]),
    )
    def sink_factory() -> SignedAppendOnlyAuditSink:
        return SignedAppendOnlyAuditSink(
            Path(config["log_path"]), record_key, key_id=config["record_key_id"],
            signer_principal_id=config["record_principal_id"], audit_signing_registry_sha256=record_sha,
            audit_registry_records=record_records, schema_validator=validator,
            segment_id=config["segment_id"], checkpoint_path=Path(config["checkpoint_path"]),
            anchor_client=anchor_client, provision=bool(config["provision_segment"]),
            maximum_event_records=int(config["maximum_event_records"]),
            maximum_log_bytes=int(config["maximum_log_bytes"]),
            terminal_seal_reserve_bytes=int(config["terminal_seal_reserve_bytes"]),
            recovery_consumed_ledger_path=Path(config["recovery_consumed_ledger_path"]),
        )
    proof_request_key = _public_key_from_bytes(secure_read_bytes(config_root, config["proof_request_public_key_file"], expected_uid=expected_uid))
    index = DurableEventIdIndex(Path(config["event_index_path"]), expected_uid=expected_uid)
    return AuditPublisherServer(
        Path(config["publisher_socket_path"]), sink_factory,
        receipt_signing_key=receipt_key, receipt_key_id=config["receipt_key_id"],
        receipt_signer_principal_id=config["receipt_principal_id"],
        receipt_signing_registry_sha256=receipt_sha, receipt_registry_records=receipt_records,
        schema_validator=validator, event_index=index,
        proof_service_uid=int(config["proof_service_uid"]), proof_service_gid=int(config["proof_service_gid"]),
        proof_service_principal_id=config["proof_service_principal_id"],
        request_verification_keys={config["proof_request_key_id"]: proof_request_key},
        socket_uid=expected_uid, socket_gid=os.getegid(),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-root", default="/etc/witness-audit-publisher")
    args = parser.parse_args()
    server = load_publisher_server(Path(args.config_root))
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
