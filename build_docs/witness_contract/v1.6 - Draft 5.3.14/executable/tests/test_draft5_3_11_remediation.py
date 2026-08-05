#!/usr/bin/env python3
from __future__ import annotations

import json
import importlib.util
import io
import os
import pathlib
import shutil
import sqlite3
import stat
import sys
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timezone
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executable/runtime"))
sys.path.insert(0, str(ROOT / "executable/tests"))

import proof_authority as authority  # noqa: E402
import proof_check_service as service  # noqa: E402
from proof_check_wsgi import AUTHENTICATED_PRINCIPAL_ENVIRON_KEY, ProofCheckWSGI  # noqa: E402
from test_proof_check_service import FakeAuthority, FakePolicyResolver, RequestBoundaryValidator  # noqa: E402


def proof_request() -> dict:
    return {
        "request_id": "request:deadline", "idempotency_key": "idempotency:deadline",
        "compiler_profile_id": "profile:governed", "claim_id": "claim:1",
        "canonical_claim": {"statement": "True"}, "theorem_statement": "True",
        "theorem_name": "t", "source_bundle_id": "bundle-1",
        "proof_artifact_relative_path": "Proof.lean", "policy_decision_id": "policy:1",
    }


def load_module(name: str, relative: str):
    specification = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert specification and specification.loader
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


class TrustedRootTierTests(unittest.TestCase):
    class LoaderReached(RuntimeError):
        pass

    @staticmethod
    def _service_identity() -> tuple[int, int]:
        return (65534, 65534) if os.getuid() == 0 else (os.getuid(), os.getgid())

    @staticmethod
    def _chown(path: pathlib.Path, uid: int, gid: int) -> None:
        if os.getuid() == 0:
            try:
                os.chown(path, uid, gid, follow_symlinks=False)
            except OSError:
                # Some rootless test sandboxes prohibit unmapped ownership.
                pass

    def _base_directory(self) -> pathlib.Path:
        return pathlib.Path(tempfile.gettempdir())

    def _write_private(self, root: pathlib.Path, name: str, data: bytes, uid: int, gid: int) -> None:
        path = root / name
        path.write_bytes(data)
        path.chmod(0o600)
        self._chown(path, uid, gid)

    def _make_loader_root(self, parent: pathlib.Path, uid: int, gid: int) -> pathlib.Path:
        root = parent / "witness-authority"
        root.mkdir(mode=0o700)
        schemas = root / "schemas"
        schemas.mkdir(mode=0o700)
        artifact_store = root / "artifacts"
        artifact_store.mkdir(mode=0o700)
        for directory in (root, schemas, artifact_store):
            directory.chmod(0o700)
            self._chown(directory, uid, gid)

        governance = Ed25519PrivateKey.generate()
        verifier = Ed25519PrivateKey.generate()
        verifier_result = Ed25519PrivateKey.generate()
        private_format = (serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
        self._write_private(root, "governance.pem", governance.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo,
        ), uid, gid)
        self._write_private(root, "verifier.pem", verifier.private_bytes(*private_format), uid, gid)
        self._write_private(root, "verifier-result.pem", verifier_result.private_bytes(*private_format), uid, gid)
        self._write_private(root, "compiler-registry.json", authority.canonical_bytes({}), uid, gid)
        self._write_private(root, "policy-registry.json", authority.canonical_bytes({}), uid, gid)

        config = {
            "compiler_registry_file": "compiler-registry.json",
            "governance_public_key_file": "governance.pem",
            "verifier_private_key_file": "verifier.pem",
            "verifier_result_private_key_file": "verifier-result.pem",
            "oci_runtime_file": "oci-runtime",
            "oci_runtime_sha256": "0" * 64,
            "oci_runtime_version": "test",
            "verifier_principal_id": "principal:test",
            "key_id": "key:test",
            "authority_snapshot_id": "snapshot:test",
            "authority_ledger_high_water_sequence": 0,
            "artifact_store_root": str(artifact_store),
            "policy_registry_file": "policy-registry.json",
            "seccomp_profile_file": "seccomp.json",
            "seccomp_profile_sha256": "0" * 64,
            "authority_uid": uid,
            "authority_gid": gid,
            "platform_capability_file": "platform.json",
            "trusted_artifact_registry_file": "trusted-artifacts.json",
            "schema_root": "schemas",
            "idempotency_database": str(root / "cache.sqlite"),
            "idempotency_retention_seconds": 60,
            "idempotency_lease_seconds": 30,
            "idempotency_maximum_completed_rows": 10,
            "idempotency_maximum_inflight_rows": 10,
            "idempotency_maximum_inflight_rows_per_principal": 2,
            "idempotency_maximum_total_rows": 20,
            "idempotency_maximum_database_bytes": 1000000,
            "idempotency_maximum_cache_envelope_bytes": 100000,
            "cache_private_key_file": "cache-private.pem",
            "cache_public_key_file": "cache-public.pem",
            "cache_signing_registry_file": "cache-registry.json",
            "cache_registry_lineage_file": "cache-lineage.json",
            "cache_signer_principal_id": "principal:cache",
            "cache_signer_key_id": "key:cache",
            "cache_audit_private_key_file": "cache-audit-private.pem",
            "cache_audit_public_key_file": "cache-audit-public.pem",
            "cache_audit_log_file": "cache-audit-segments/cache-audit-0001.jsonl",
            "cache_audit_checkpoint_file": "cache-audit-checkpoints/cache-audit-0001.checkpoint.json",
            "cache_audit_segment_id": "cache:audit:segment:0001",
            "cache_audit_previous_sealed_segment_tail_sha256": None,
            "cache_audit_signer_principal_id": "principal:cache-audit",
            "cache_audit_signer_key_id": "key:cache-audit",
            "cache_audit_maximum_record_bytes": 262144,
            "cache_audit_maximum_log_bytes": 10485760,
            "cache_audit_maximum_records": 10000,
            "cache_audit_rotation_policy": "signed_sealed_segment_with_external_checkpoint",
        }
        self._write_private(root, "service-config.json", authority.canonical_bytes(config), uid, gid)
        return root

    def test_tiered_ancestry_accepts_system_owned_ancestors_and_private_service_root(self):
        uid = 65534

        def info(owner: int, mode: int) -> os.stat_result:
            return os.stat_result((stat.S_IFDIR | mode, 1, 1, 1, owner, owner, 0, 0, 0, 0))

        states = {10: info(0, 0o755), 11: info(0, 0o755), 12: info(uid, 0o700)}
        with patch.object(authority.os, "open", side_effect=[10, 11, 12]) as opened, patch.object(
            authority.os, "fstat", side_effect=lambda descriptor: states[descriptor],
        ), patch.object(authority.os, "close"):
            authority.validate_trusted_root_ancestry(pathlib.Path("/etc/witness-authority"), expected_uid=uid)
        self.assertEqual(opened.call_args_list[1].kwargs["dir_fd"], 10)
        self.assertEqual(opened.call_args_list[2].kwargs["dir_fd"], 11)
        self.assertTrue(all(item.args[1] & authority.O_NOFOLLOW for item in opened.call_args_list))

        states[11] = info(0, 0o775)
        with patch.object(authority.os, "open", side_effect=[10, 11]), patch.object(
            authority.os, "fstat", side_effect=lambda descriptor: states[descriptor],
        ), patch.object(authority.os, "close"), self.assertRaisesRegex(RuntimeError, "writable"):
            authority.validate_trusted_root_ancestry(pathlib.Path("/etc/witness-authority"), expected_uid=uid)
        states[11] = info(0, 0o755)
        states[12] = info(0, 0o700)
        with patch.object(authority.os, "open", side_effect=[10, 11, 12]), patch.object(
            authority.os, "fstat", side_effect=lambda descriptor: states[descriptor],
        ), patch.object(authority.os, "close"), self.assertRaisesRegex(RuntimeError, "service UID"):
            authority.validate_trusted_root_ancestry(pathlib.Path("/etc/witness-authority"), expected_uid=uid)

    def test_both_production_loaders_reach_schema_boundary_under_nonroot_identity(self):
        uid, gid = self._service_identity()
        with tempfile.TemporaryDirectory(prefix="witness-loader-test-", dir=self._base_directory()) as parent_name:
            root = self._make_loader_root(pathlib.Path(parent_name), uid, gid)
            real_check = authority._check_trusted_stat
            real_validate = authority.validate_trusted_root_ancestry

            def ownership_neutral_check(info, *, expected_uid, directory, link_count_one=True):
                return real_check(info, expected_uid=info.st_uid, directory=directory, link_count_one=link_count_one)

            def validate_as_etc_layout(requested_root, *, expected_uid):
                names = ["etc", "witness-authority"]
                if pathlib.Path(requested_root).name == "schemas":
                    names.append("schemas")
                descriptors = list(range(40, 41 + len(names)))
                states = {
                    descriptors[0]: os.stat_result((stat.S_IFDIR | 0o755, 1, 1, 1, 0, 0, 0, 0, 0, 0)),
                }
                for index, descriptor in enumerate(descriptors[1:]):
                    owner = 0 if index == 0 else expected_uid
                    mode = 0o755 if owner == 0 else 0o700
                    states[descriptor] = os.stat_result((stat.S_IFDIR | mode, 1, 1, 1, owner, owner, 0, 0, 0, 0))
                with patch.object(authority.os, "open", side_effect=descriptors), patch.object(
                    authority.os, "fstat", side_effect=lambda descriptor: states[descriptor],
                ), patch.object(authority.os, "close"):
                    real_validate(pathlib.Path("/").joinpath(*names), expected_uid=expected_uid)

            with patch.object(authority.os, "getuid", return_value=uid), patch.object(
                authority.os, "getgid", return_value=gid,
            ), patch.object(authority, "validate_trusted_root_ancestry", side_effect=validate_as_etc_layout), patch.object(
                service, "validate_trusted_root_ancestry", side_effect=validate_as_etc_layout,
            ), patch.object(authority, "_check_trusted_stat", side_effect=ownership_neutral_check), patch.object(
                authority, "CanonicalSchemaValidator", side_effect=self.LoaderReached("authority-loader-reached"),
            ):
                with self.assertRaisesRegex(self.LoaderReached, "authority-loader-reached"):
                    authority.load_production_authority_service(root)
            with (
                patch.object(service.os, "getuid", return_value=uid),
                patch.object(service.os, "getgid", return_value=gid),
                patch.object(service, "validate_trusted_root_ancestry", side_effect=validate_as_etc_layout),
                patch.object(authority, "validate_trusted_root_ancestry", side_effect=validate_as_etc_layout),
                patch.object(authority, "_check_trusted_stat", side_effect=ownership_neutral_check),
                patch.object(service, "CanonicalSchemaValidator", side_effect=self.LoaderReached("application-loader-reached")),
            ):
                with self.assertRaisesRegex(self.LoaderReached, "application-loader-reached"):
                    service.load_production_application(root)

    def test_root_execution_is_rejected_before_configuration_read(self):
        if os.getuid() == 0:
            with self.assertRaisesRegex(authority.AuthorityFailure, "non-root"):
                authority.load_production_authority_service(pathlib.Path("/nonexistent/witness-authority"))
            with self.assertRaisesRegex(authority.AuthorityFailure, "non-root"):
                service.load_production_application(pathlib.Path("/nonexistent/witness-authority"))
        else:
            with patch.object(authority.os, "getuid", return_value=0), patch.object(authority.os, "getgid", return_value=0):
                with self.assertRaisesRegex(authority.AuthorityFailure, "non-root"):
                    authority.load_production_authority_service(pathlib.Path("/nonexistent/witness-authority"))
                with self.assertRaisesRegex(authority.AuthorityFailure, "non-root"):
                    service.load_production_application(pathlib.Path("/nonexistent/witness-authority"))


class CacheChronologyAndRecoveryTests(unittest.TestCase):
    @staticmethod
    def record(status: str = "active", **changes) -> dict:
        record = {
            "key_id": "cache:key", "principal_id": "cache:principal",
            "public_key_base64url": "A" * 43,
            "authorization_scope": "idempotency_cache_envelope_signing",
            "status": status, "valid_from": "2026-01-01T00:00:00Z",
            "valid_until": "2027-01-01T00:00:00Z",
            "status_changed_at": "2026-01-01T00:00:00Z",
            "rotation_predecessor_key_id": None,
        }
        record.update(changes)
        return record

    def test_future_status_change_is_rejected_for_every_status(self):
        evaluated = datetime(2026, 8, 1, tzinfo=timezone.utc)
        cases = {
            "active": self.record(status_changed_at="2099-01-01T00:00:00Z", valid_until=None),
            "retired": self.record(status="retired", valid_until="2099-01-01T00:00:00Z", status_changed_at="2099-01-01T00:00:00Z"),
            "revoked": self.record(status="revoked", status_changed_at="2099-01-01T00:00:00Z", valid_until=None),
        }
        for status, record in cases.items():
            with self.subTest(status=status), self.assertRaisesRegex(RuntimeError, "future"):
                service.validate_cache_signing_registry_lineage({"keys": [record]}, evaluated_at=evaluated)

    def test_status_chronology_and_valid_rotation_are_explicit(self):
        evaluated = datetime(2026, 8, 1, tzinfo=timezone.utc)
        invalid = [
            self.record(status_changed_at="2025-12-31T23:59:59Z"),
            self.record(status="retired", valid_until="2026-06-01T00:00:00Z", status_changed_at="2026-05-31T00:00:00Z"),
            self.record(status="revoked", valid_until="2026-06-01T00:00:00Z", status_changed_at="2026-06-02T00:00:00Z"),
        ]
        for record in invalid:
            with self.assertRaises(RuntimeError):
                service.validate_cache_signing_registry_lineage({"keys": [record]}, evaluated_at=evaluated)
        retired = self.record(
            key_id="cache:old", status="retired", valid_from="2025-01-01T00:00:00Z",
            valid_until="2026-01-01T00:00:00Z", status_changed_at="2026-01-01T00:00:00Z",
        )
        active = self.record(rotation_predecessor_key_id="cache:old")
        by_id = service.validate_cache_signing_registry_lineage({"keys": [retired, active]}, evaluated_at=evaluated)
        self.assertEqual(set(by_id), {"cache:old", "cache:key"})

    def test_signed_validity_evidence_binds_status_change_time(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            bundle = root / "bundle-1"
            bundle.mkdir()
            (bundle / "Proof.lean").write_text("theorem t : True := by trivial\n", encoding="utf-8")
            application = service.ProofCheckApplication(
                FakeAuthority(), root, FakePolicyResolver(), schema_validator=RequestBoundaryValidator(),
            )
            application.handle(
                proof_request(), authenticated_principal_id="principal:1",
            )
            with closing(sqlite3.connect(root / ".proof-check-idempotency.sqlite")) as connection:
                envelope = authority.canonical_json_loads(connection.execute(
                    "SELECT result_canonical_json FROM proof_check_idempotency",
                ).fetchone()[0])
            evidence = envelope["cache_key_validity_evidence"]
            self.assertEqual(evidence["status_changed_at"], application.cache_key_record["status_changed_at"])
            self.assertEqual(envelope["schema_version"], "idempotency_cache_envelope/v3")
            application.idempotency_store.close()

    def test_registry_rotation_preserves_stale_row_and_requires_new_key(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            bundle = root / "bundle-1"
            bundle.mkdir()
            (bundle / "Proof.lean").write_text("theorem t : True := by trivial\n", encoding="utf-8")
            events: list[dict] = []
            proof_authority = FakeAuthority()
            application = service.ProofCheckApplication(
                proof_authority, root, FakePolicyResolver(), schema_validator=RequestBoundaryValidator(),
                cache_verification_evidence_sink=events.append,
            )
            request = proof_request()
            application.handle(request, authenticated_principal_id="principal:1")
            old_key_id = application.cache_signer_key_id
            new_key = Ed25519PrivateKey.generate()
            new_key_id = "cache-key:rotated"
            new_record = {
                "key_id": new_key_id, "principal_id": application.cache_signer_principal_id,
                "public_key_base64url": authority.public_key_raw_b64url(new_key.public_key()),
                "authorization_scope": "idempotency_cache_envelope_signing", "status": "active",
                "valid_from": "1970-01-01T00:00:00+00:00", "valid_until": None,
                "status_changed_at": "1970-01-01T00:00:00+00:00",
                "rotation_predecessor_key_id": old_key_id,
            }
            old_digest = application.cache_registry_sha256
            current_digest = "f" * 64
            lineage_digest = "d" * 64
            snapshots = {
                old_digest: service.GovernedCacheRegistrySnapshot(
                    registry_sha256=old_digest, registry_id="development:old",
                    registry_created_at="1970-01-01T00:00:00+00:00",
                    registry_signed_payload_sha256=old_digest,
                    records_by_id={old_key_id: application.cache_key_record},
                    verification_keys_by_id={old_key_id: application.cache_verification_key},
                    successor_registry_sha256=current_digest,
                    stale_replay_policy="authenticate_then_conflict", revoked_key_ids=frozenset(),
                    lineage_signed_payload_sha256=lineage_digest, lineage_created_at="1970-01-03T00:00:00+00:00",
                ),
                current_digest: service.GovernedCacheRegistrySnapshot(
                    registry_sha256=current_digest, registry_id="development:current",
                    registry_created_at="1970-01-02T00:00:00+00:00",
                    registry_signed_payload_sha256=current_digest,
                    records_by_id={new_key_id: new_record},
                    verification_keys_by_id={new_key_id: new_key.public_key()},
                    successor_registry_sha256=None,
                    stale_replay_policy="current_registry", revoked_key_ids=frozenset(),
                    lineage_signed_payload_sha256=lineage_digest, lineage_created_at="1970-01-03T00:00:00+00:00",
                ),
            }
            rotated = service.ProofCheckApplication(
                proof_authority, root, FakePolicyResolver(), schema_validator=RequestBoundaryValidator(),
                idempotency_store=application.idempotency_store,
                cache_signing_key=new_key, cache_verification_key=new_key.public_key(),
                cache_verification_keys_by_id={
                    old_key_id: application.cache_verification_key,
                    new_key_id: new_key.public_key(),
                },
                cache_signer_principal_id=application.cache_signer_principal_id,
                cache_signer_key_id=new_key_id, cache_key_record=new_record,
                cache_registry_sha256=current_digest,
                cache_registry_snapshots_by_sha256=snapshots,
                cache_verification_evidence_sink=events.append,
            )
            with self.assertRaisesRegex(authority.AuthorityFailure, "new idempotency key") as caught:
                rotated.handle(request, authenticated_principal_id="principal:1")
            self.assertEqual(caught.exception.code, "cache_key_rotation_requires_new_idempotency_key")
            with closing(sqlite3.connect(root / ".proof-check-idempotency.sqlite")) as connection:
                self.assertEqual(connection.execute("SELECT count(*) FROM proof_check_idempotency").fetchone()[0], 1)
            self.assertEqual(events[-1]["decision"], "reject_preserve_row_require_new_idempotency_key")
            rotated.idempotency_store.close()

    def test_wsgi_returns_stable_conflict_for_rotated_cache_row(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            bundle = root / "bundle-1"
            bundle.mkdir()
            (bundle / "Proof.lean").write_text("theorem t : True := by trivial\n", encoding="utf-8")
            application = service.ProofCheckApplication(
                FakeAuthority(), root, FakePolicyResolver(), schema_validator=RequestBoundaryValidator(),
            )
            request = proof_request()
            application.handle(request, authenticated_principal_id="principal:1")
            old_digest = application.cache_registry_sha256
            current_digest = "e" * 64
            lineage_digest = "d" * 64
            old_snapshot = service.GovernedCacheRegistrySnapshot(
                registry_sha256=old_digest, registry_id="development:old",
                registry_created_at="1970-01-01T00:00:00+00:00",
                registry_signed_payload_sha256=old_digest,
                records_by_id={application.cache_signer_key_id: application.cache_key_record},
                verification_keys_by_id={application.cache_signer_key_id: application.cache_verification_key},
                successor_registry_sha256=current_digest,
                stale_replay_policy="authenticate_then_conflict", revoked_key_ids=frozenset(),
                lineage_signed_payload_sha256=lineage_digest, lineage_created_at="1970-01-03T00:00:00+00:00",
            )
            current_snapshot = service.GovernedCacheRegistrySnapshot(
                registry_sha256=current_digest, registry_id="development:current",
                registry_created_at="1970-01-02T00:00:00+00:00",
                registry_signed_payload_sha256=current_digest,
                records_by_id={application.cache_signer_key_id: application.cache_key_record},
                verification_keys_by_id={application.cache_signer_key_id: application.cache_verification_key},
                successor_registry_sha256=None,
                stale_replay_policy="current_registry", revoked_key_ids=frozenset(),
                lineage_signed_payload_sha256=lineage_digest, lineage_created_at="1970-01-03T00:00:00+00:00",
            )
            application.cache_registry_sha256 = current_digest
            application.cache_registry_snapshots_by_sha256 = {
                old_digest: old_snapshot, current_digest: current_snapshot,
            }
            application.cache_registry_lineage_paths = service.validate_cache_registry_snapshot_lineage(
                application.cache_registry_snapshots_by_sha256,
                current_registry_sha256=current_digest, production_mode=True,
            )
            body = authority.canonical_bytes(request)
            status: list[str] = []
            response = b"".join(ProofCheckWSGI(application)({
                "REQUEST_METHOD": "POST", "PATH_INFO": "/v2/proof-checks",
                "CONTENT_TYPE": "application/json", "CONTENT_LENGTH": str(len(body)),
                "HTTP_IDEMPOTENCY_KEY": request["idempotency_key"],
                AUTHENTICATED_PRINCIPAL_ENVIRON_KEY: "principal:1", "wsgi.input": io.BytesIO(body),
            }, lambda value, _headers: status.append(value)))
            payload = authority.canonical_json_loads(response.decode("utf-8"))
            self.assertEqual(status, ["409 Conflict"])
            self.assertEqual(payload["error"], "cache_key_rotation_requires_new_idempotency_key")
            application.idempotency_store.close()


class CanonicalTrustedJsonTests(unittest.TestCase):
    def test_trusted_json_rejects_duplicates_and_noncanonical_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            root.chmod(0o700)
            path = root / "record.json"
            for text in ('{"status":"revoked","status":"active"}', '{"b":1, "a":2}', '{"n":1e0}'):
                path.write_text(text, encoding="utf-8")
                path.chmod(0o600)
                with self.assertRaisesRegex(RuntimeError, "canonical"):
                    authority.load_trusted_canonical_json(root, "record.json", expected_uid=os.getuid())
            path.write_bytes(authority.canonical_bytes({"a": 2, "b": 1}))
            self.assertEqual(
                authority.load_trusted_canonical_json(root, "record.json", expected_uid=os.getuid()),
                {"a": 2, "b": 1},
            )

    def test_descriptor_read_detects_identity_change_during_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            root.chmod(0o700)
            path = root / "record.json"
            path.write_bytes(authority.canonical_bytes({"value": 1}))
            path.chmod(0o600)
            real_fstat = os.fstat
            calls = 0

            def changed_after_read(descriptor):
                nonlocal calls
                calls += 1
                observed = real_fstat(descriptor)
                if calls == 3:
                    fields = list(observed)
                    fields[8] = observed.st_mtime + 1
                    return os.stat_result(fields)
                return observed

            with patch.object(authority.os, "fstat", side_effect=changed_after_read), self.assertRaisesRegex(RuntimeError, "changed while"):
                authority.load_trusted_canonical_json(root, "record.json", expected_uid=os.getuid())

    def test_authority_schema_documents_reject_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = pathlib.Path(directory) / "schemas"
            shutil.copytree(ROOT / "schemas", copied)
            target = copied / "cache_signing_registry_v2.schema.json"
            text = target.read_text(encoding="utf-8")
            target.write_text(text.replace('"title":', '"title": "duplicate",\n  "title":', 1), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                authority.CanonicalSchemaValidator(copied)

    def test_production_schema_loader_rejects_hardlink_ambiguity(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = pathlib.Path(directory) / "schemas"
            shutil.copytree(ROOT / "schemas", copied)
            target = copied / "cache_signing_registry_v2.schema.json"
            os.link(target, pathlib.Path(directory) / "second-name.schema.json")
            with self.assertRaisesRegex(RuntimeError, "hard-link"):
                authority.CanonicalSchemaValidator(copied, expected_uid=os.getuid())


class PythonMatrixAssemblyTests(unittest.TestCase):
    @staticmethod
    def run_record(target: str, exact: str, generated_at: str) -> dict:
        return {
            "schema_version": "python_interpreter_validation/v1",
            "package_version": "v1.6-draft-5.3.11",
            "target_python_version": target,
            "python_version": exact,
            "generated_at": generated_at,
            "count_source": "unittest.TestResult",
            "warning_detection": "independent_of_count_extraction",
            "tests_discovered": 239, "tests_run": 239, "tests_passed": 239,
            "tests_failed": 0, "tests_errored": 0, "tests_skipped": 0,
            "duplicate_test_ids": [], "normal_status": "passed",
            "development_warnings_as_errors_status": "passed", "warning_output_lines": [],
            "normal_command": [exact, "tests"], "warning_free_command": [exact, "-W", "error", "tests"],
            "normal_stdout_sha256": "0" * 64, "normal_stderr_sha256": "1" * 64,
            "development_stdout_sha256": "2" * 64, "development_stderr_sha256": "3" * 64,
        }

    def _patched_generator(self, directory: str):
        generator = load_module("draft5311_matrix_test", "executable/validators/generate_draft5_3_11_python_evidence.py")
        root = pathlib.Path(directory)
        generator.ROOT = root
        generator.EVIDENCE_DIR = root / "validation/python_matrix/draft5_3_11"
        generator.MATRIX_PATH = root / "DRAFT5_3_11_PYTHON_MATRIX_VALIDATION.json"
        generator.COUNTS_PATH = root / "DRAFT5_3_11_REGRESSION_COUNTS.json"
        generator.SUMMARY_PATH = root / "DRAFT5_3_11_VALIDATION_SUMMARY.txt"
        generator.METADATA_PATH = root / "PACKAGE_METADATA_v1_6_draft_5_3_11.json"
        generator.EVIDENCE_DIR.mkdir(parents=True)
        return generator

    def test_per_interpreter_records_merge_without_overwrite_or_contradiction(self):
        with tempfile.TemporaryDirectory() as directory:
            generator = self._patched_generator(directory)
            generator.write_json(generator.evidence_path("3.12"), self.run_record("3.12", "3.12.13", "2026-08-01T01:00:00+00:00"))
            generator.write_json(generator.evidence_path("3.13"), self.run_record("3.13", "3.13.5", "2026-08-01T02:00:00+00:00"))
            first = generator.merge()
            first_bytes = generator.MATRIX_PATH.read_bytes()
            second = generator.merge()
            self.assertEqual(first_bytes, generator.MATRIX_PATH.read_bytes())
            self.assertEqual(first, second)
            self.assertEqual(first["validated_python_versions"], ["3.12.13", "3.13.5"])
            self.assertEqual(first["unavailable_python_versions"], [])
            self.assertEqual(len({item["target_python_version"] for item in first["runs"]}), 2)

    def test_validated_and_unavailable_targets_must_be_disjoint(self):
        with tempfile.TemporaryDirectory() as directory:
            generator = self._patched_generator(directory)
            generator.write_json(generator.evidence_path("3.12"), self.run_record("3.12", "3.12.13", "2026-08-01T01:00:00+00:00"))
            generator.write_json(generator.unavailable_path("3.12"), {
                "schema_version": "python_interpreter_unavailable/v1", "package_version": "v1.6-draft-5.3.11",
                "target_python_version": "3.12", "generated_at": "2026-08-01T02:00:00+00:00",
                "status": "interpreter_unavailable", "reason": "contradiction",
            })
            generator.write_json(generator.unavailable_path("3.13"), {
                "schema_version": "python_interpreter_unavailable/v1", "package_version": "v1.6-draft-5.3.11",
                "target_python_version": "3.13", "generated_at": "2026-08-01T02:00:00+00:00",
                "status": "interpreter_unavailable", "reason": "missing",
            })
            with self.assertRaisesRegex(SystemExit, "overlap"):
                generator.merge()


if __name__ == "__main__":
    unittest.main()
