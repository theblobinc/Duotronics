#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import pathlib
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timezone
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executable/runtime"))
sys.path.insert(0, str(ROOT / "executable/tests"))

import proof_authority as authority  # noqa: E402
import proof_check_service as service  # noqa: E402
from test_proof_check_service import FakeAuthority, FakePolicyResolver, RequestBoundaryValidator  # noqa: E402


def proof_request() -> dict:
    return {
        "request_id": "request:historical", "idempotency_key": "idempotency:historical",
        "compiler_profile_id": "profile:governed", "claim_id": "claim:1",
        "canonical_claim": {"statement": "True"}, "theorem_statement": "True",
        "theorem_name": "t", "source_bundle_id": "bundle-1",
        "proof_artifact_relative_path": "Proof.lean", "policy_decision_id": "policy:1",
    }


class CacheEvidenceValidator(RequestBoundaryValidator):
    def validate(self, surface, value):
        if surface in {"proof_check_request", "cache_stale_row_evidence"}:
            self.real.validate(surface, value)


class HistoricalCacheAuthenticationTests(unittest.TestCase):
    NOW = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    OLD_TIME = datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc)

    @staticmethod
    def key_record(key_id: str, key: Ed25519PrivateKey, *, valid_from: str) -> dict:
        return {
            "key_id": key_id, "principal_id": "cache:principal",
            "public_key_base64url": authority.public_key_raw_b64url(key.public_key()),
            "authorization_scope": "idempotency_cache_envelope_signing",
            "status": "active", "valid_from": valid_from, "valid_until": None,
            "status_changed_at": valid_from, "rotation_predecessor_key_id": None,
        }

    @staticmethod
    def registry(governance: Ed25519PrivateKey, registry_id: str, created_at: str, record: dict) -> dict:
        return authority.sign_record({
            "schema_version": "cache_signing_registry/v2", "registry_id": registry_id,
            "governance_key_id": "governance:key", "created_at": created_at,
            "keys": [record],
        }, governance)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temporary.name)
        bundle = self.root / "bundle-1"
        bundle.mkdir()
        (bundle / "Proof.lean").write_text("theorem t : True := by trivial\n", encoding="utf-8")
        self.governance = Ed25519PrivateKey.generate()
        self.old_key = Ed25519PrivateKey.generate()
        self.new_key = Ed25519PrivateKey.generate()
        self.old_record = self.key_record("cache:key:old", self.old_key, valid_from="2026-01-01T00:00:00Z")
        self.new_record = self.key_record("cache:key:current", self.new_key, valid_from="2026-07-01T00:00:00Z")
        self.old_registry = self.registry(self.governance, "cache:registry:old", "2026-02-01T00:00:00Z", self.old_record)
        self.current_registry = self.registry(self.governance, "cache:registry:current", "2026-08-01T00:00:00Z", self.new_record)
        self.old_digest = authority.sha256_bytes(authority.canonical_bytes(self.old_registry))
        self.current_digest = authority.sha256_bytes(authority.canonical_bytes(self.current_registry))
        self.lineage = authority.sign_record({
            "schema_version": "cache_registry_lineage/v1", "lineage_id": "cache:lineage:1",
            "governance_key_id": "governance:key", "current_registry_sha256": self.current_digest,
            "historical_registries": [{
                "registry_sha256": self.old_digest, "registry_file": "cache-registry-old.json",
                "successor_registry_sha256": self.current_digest,
                "stale_replay_policy": "authenticate_then_conflict", "revoked_key_ids": [],
            }],
            "created_at": "2026-08-01T00:00:00Z",
        }, self.governance)
        self.authority = FakeAuthority()
        self.validator = CacheEvidenceValidator()
        self.events: list[dict] = []
        old_application = service.ProofCheckApplication(
            self.authority, self.root, FakePolicyResolver(), schema_validator=self.validator,
            cache_signing_key=self.old_key, cache_verification_key=self.old_key.public_key(),
            cache_verification_keys_by_id={self.old_record["key_id"]: self.old_key.public_key()},
            cache_signer_principal_id=self.old_record["principal_id"],
            cache_signer_key_id=self.old_record["key_id"], cache_key_record=self.old_record,
            cache_registry_sha256=self.old_digest, cache_clock=lambda: self.OLD_TIME,
        )
        old_application.handle(proof_request(), authenticated_principal_id="principal:1")
        self.store = old_application.idempotency_store

    def tearDown(self):
        self.store.close()
        self.temporary.cleanup()

    def snapshots(self, *, revoked: bool = False) -> dict[str, service.GovernedCacheRegistrySnapshot]:
        lineage_digest = self.lineage["signed_payload_sha256"]
        return {
            self.old_digest: service.build_governed_cache_registry_snapshot(
                self.old_registry, self.governance.public_key(),
                successor_registry_sha256=self.current_digest,
                stale_replay_policy="authenticate_then_conflict",
                revoked_key_ids=frozenset({self.old_record["key_id"]} if revoked else set()),
                lineage_signed_payload_sha256=lineage_digest, lineage_created_at=self.lineage["created_at"],
            ),
            self.current_digest: service.build_governed_cache_registry_snapshot(
                self.current_registry, self.governance.public_key(),
                successor_registry_sha256=None, stale_replay_policy="current_registry",
                lineage_signed_payload_sha256=lineage_digest, lineage_created_at=self.lineage["created_at"], evaluated_at=self.NOW,
            ),
        }

    def current_application(self, *, revoked: bool = False) -> service.ProofCheckApplication:
        return service.ProofCheckApplication(
            self.authority, self.root, FakePolicyResolver(), schema_validator=self.validator,
            idempotency_store=self.store,
            cache_signing_key=self.new_key, cache_verification_key=self.new_key.public_key(),
            cache_verification_keys_by_id={self.new_record["key_id"]: self.new_key.public_key()},
            cache_signer_principal_id=self.new_record["principal_id"],
            cache_signer_key_id=self.new_record["key_id"], cache_key_record=self.new_record,
            cache_registry_sha256=self.current_digest,
            cache_registry_snapshots_by_sha256=self.snapshots(revoked=revoked),
            cache_clock=lambda: self.NOW, cache_verification_evidence_sink=self.events.append,
        )

    def stored_envelope(self) -> dict:
        with closing(sqlite3.connect(self.root / ".proof-check-idempotency.sqlite")) as connection:
            raw = connection.execute("SELECT result_canonical_json FROM proof_check_idempotency").fetchone()[0]
        return authority.canonical_json_loads(raw)

    def replace_stored_envelope(self, envelope: dict) -> None:
        with closing(sqlite3.connect(self.root / ".proof-check-idempotency.sqlite")) as connection:
            connection.execute(
                "UPDATE proof_check_idempotency SET result_canonical_json=?",
                (authority.canonical_bytes(envelope).decode("utf-8"),),
            )
            connection.commit()

    def assert_integrity_without_rotation_evidence(self, application: service.ProofCheckApplication) -> None:
        with self.assertRaises(authority.AuthorityFailure) as caught:
            application.handle(proof_request(), authenticated_principal_id="principal:1")
        self.assertEqual(caught.exception.code, "cache_integrity_invalid")
        self.assertEqual(self.events, [])

    def test_authenticated_predecessor_row_emits_evidence_then_returns_stable_conflict(self):
        application = self.current_application()
        with self.assertRaises(authority.AuthorityFailure) as caught:
            application.handle(proof_request(), authenticated_principal_id="principal:1")
        self.assertEqual(caught.exception.code, "cache_key_rotation_requires_new_idempotency_key")
        self.assertEqual(len(self.events), 1)
        evidence = self.events[0]
        self.assertTrue(evidence["signature_verified"])
        self.assertTrue(evidence["registry_lineage_verified"])
        self.assertEqual(evidence["registry_lineage_path"], [self.old_digest, self.current_digest])
        self.assertEqual(evidence["schema_version"], "cache_stale_row_evidence/v4")

    def test_forged_unknown_signer_is_integrity_failure_not_rotation(self):
        envelope = self.stored_envelope()
        envelope["cache_signer_key_id"] = "cache:key:unknown"
        envelope = authority.sign_record(envelope, Ed25519PrivateKey.generate())
        self.replace_stored_envelope(envelope)
        self.assert_integrity_without_rotation_evidence(self.current_application())

    def test_altered_historical_row_cannot_emit_rotation_evidence(self):
        envelope = self.stored_envelope()
        envelope["claim_id"] = "claim:altered"
        self.replace_stored_envelope(envelope)
        self.assert_integrity_without_rotation_evidence(self.current_application())

    def test_revoked_historical_signer_follows_integrity_policy(self):
        self.assert_integrity_without_rotation_evidence(self.current_application(revoked=True))

    def test_lineage_cycle_and_unknown_successor_are_rejected(self):
        snapshots = self.snapshots()
        old = snapshots[self.old_digest]
        snapshots[self.old_digest] = service.GovernedCacheRegistrySnapshot(
            **{**old.__dict__, "successor_registry_sha256": self.old_digest},
        )
        with self.assertRaisesRegex(ValueError, "cycle"):
            service.validate_cache_registry_snapshot_lineage(
                snapshots, current_registry_sha256=self.current_digest, production_mode=True,
            )


class ValidatorBoundedReapingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import importlib.util
        path = ROOT / "executable/validators/validate_draft5_3_12_corpus.py"
        specification = importlib.util.spec_from_file_location("draft5312_validator_test", path)
        cls.validator = importlib.util.module_from_spec(specification)
        assert specification and specification.loader
        sys.modules[specification.name] = cls.validator
        specification.loader.exec_module(cls.validator)

    def test_escaped_nested_descendant_is_killed_without_pipe_or_unbounded_communicate(self):
        result = self.validator.run_phase_isolated("__validator_intentional_hang", True, timeout_seconds=0.15)
        self.assertTrue(result["timed_out"])
        self.assertEqual(result["capture_backend"], "rlimit_bounded_temporary_files")
        self.assertTrue(result["parent_capture_descriptors_closed"])
        self.assertTrue(result["bounded_reap"])
        self.assertEqual(result["surviving_descendants"], [])
        source = (ROOT / "executable/validators/validate_draft5_3_12_corpus.py").read_text(encoding="utf-8")
        self.assertNotIn("process.communicate()", source)

    def test_process_identity_prevents_signals_after_pid_reuse(self):
        with patch.object(self.validator, "_pid_start_time", return_value=999), patch.object(os, "kill") as kill:
            self.validator._signal_identities({(123, 111)}, 15)
        kill.assert_not_called()


class ProductionLoaderIntegrationContractTests(unittest.TestCase):
    @staticmethod
    def source() -> str:
        return (ROOT / "executable/validators/run_production_loader_integration.py").read_text(encoding="utf-8")

    def test_harness_uses_real_chroot_nonroot_identity_and_both_loaders(self):
        source = self.source()
        for token in (
            'config_root = pathlib.Path("/etc/witness-authority")',
            "os.chroot(chroot_root)", "os.setgroups([])", "os.setgid(SERVICE_GID)",
            "os.setuid(SERVICE_UID)", "authority.load_production_authority_service(config_root)",
            "service.load_production_application(config_root)",
        ):
            self.assertIn(token, source)

    def test_unavailable_environment_is_explicit_and_fail_closed(self):
        source = self.source()
        self.assertIn('"status": "environment_unavailable"', source)
        self.assertIn("--allow-unavailable", source)
        self.assertIn("if evidence[\"status\"] != \"passed\" and not arguments.allow_unavailable", source)


if __name__ == "__main__":
    unittest.main()
