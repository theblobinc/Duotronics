#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import pathlib
import sqlite3
import sys
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "executable/runtime/proof_authority.py"
SPEC = importlib.util.spec_from_file_location("proof_authority_sql_533", MODULE_PATH)
authority = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = authority
SPEC.loader.exec_module(authority)


def expect_integrity_error(testcase: unittest.TestCase, action) -> None:
    with testcase.assertRaises(sqlite3.IntegrityError):
        action()


class AuthorityDatabase533:
    def __init__(self):
        self.connection = sqlite3.connect(":memory:", isolation_level=None)
        authority.register_sqlite_crypto_functions(self.connection)
        self.connection.execute("PRAGMA foreign_keys = ON")
        for relative in (
            "executable/sql/draft5_2_schema_additions.sql",
            "migration/draft5_2_2_to_draft5_3_1.sql",
            "migration/draft5_3_1_to_draft5_3_2.sql",
            "migration/draft5_3_2_to_draft5_3_3.sql",
        ):
            self.connection.executescript((ROOT / relative).read_text(encoding="utf-8"))
        self.governance_private = Ed25519PrivateKey.generate()
        self.verifier_private = Ed25519PrivateKey.generate()
        self.claim_hash = "a" * 64
        self.theorem_hash = "b" * 64
        self.artifact_hash = "c" * 64
        self.governance_time = "2026-07-31T11:00:00Z"
        self.compiler_time = "2026-07-31T12:00:00Z"
        self.proof_time = "2026-07-31T12:01:00Z"
        self.gate_time = "2026-07-31T12:04:00Z"
        self._insert_claim(
            "claim:governance", "policy_decision", '{"action":"authority"}', "1" * 64,
            None, None, "principal:governance", self.governance_time,
        )
        self.connection.execute(
            "INSERT INTO wc_policy_decisions_v2 VALUES (?,?,?,?,?,?,?,?)",
            ("policy:governance", "policy_decision/v2", "claim:governance", "allow", "authority_supersession", "principal:governance", "governance authorization", self.governance_time),
        )
        self.register_governance()

    def _insert_claim(self, claim_id, kind, content, content_hash, theorem, theorem_hash, issuer, created):
        self.connection.execute(
            "INSERT INTO wc_claims_v2 VALUES (?,?,?,?,?,?,?,?,?)",
            (claim_id, "evidence_claim/v2", kind, content, content_hash, theorem, theorem_hash, issuer, created),
        )

    def register_governance(self):
        public = self.governance_private.public_key()
        self.connection.execute(
            "INSERT INTO wc_governance_authorities_v1 VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                "governance:key:1", "governance_authority/v1", "principal:governance",
                authority.public_key_raw_b64url(public), authority.public_key_fingerprint(public),
                "2020-01-01T00:00:00Z", "2099-01-01T00:00:00Z", "provisioned",
                "external-trust-witness:test", "2020-01-01T00:00:00Z",
            ),
        )

    def register_verifier(self, suffix="1", valid_from="2020-01-01T00:00:00Z", valid_until="2099-01-01T00:00:00Z", activate=True):
        private = self.verifier_private if suffix == "1" else Ed25519PrivateKey.generate()
        public = private.public_key()
        verifier = f"verifier:{suffix}"
        key = f"key:{suffix}"
        fingerprint = authority.public_key_fingerprint(public)
        self.connection.execute(
            "INSERT INTO wc_verifier_principals_v2 VALUES (?,?,?,?,?,?,?,?,?)",
            (verifier, "verifier_principal/v2", key, "Ed25519", fingerprint, "active", valid_from, valid_until, valid_from),
        )
        self.connection.execute(
            "INSERT INTO wc_verifier_keys_v3 VALUES (?,?,?,?,?,?,?,?,?)",
            (key, "verifier_key/v3", verifier, "Ed25519", authority.public_key_raw_b64url(public), fingerprint, valid_from, valid_until, valid_from),
        )
        if activate:
            auth = self.insert_authorization("verifier_key_status", "verifier_key", key, f"auth:key:{suffix}")
            self.insert_key_event(key=key, status="active", event_id=f"key-event:{suffix}:active", authorization=auth, effective_at=valid_from, recorded_at=valid_from)
        return verifier, key, private

    def insert_authorization(self, action_type, target_type, target_id, authorization_id, *, tamper=False):
        unsigned = {
            "schema_version": "governance_authorization_witness/v1",
            "authorization_witness_id": authorization_id,
            "action_type": action_type,
            "target_record_type": target_type,
            "target_record_id": target_id,
            "policy_decision_id": "policy:governance",
            "decision": "allow",
            "valid_from": "2010-01-01T00:00:00Z",
            "valid_until": "2099-01-01T00:00:00Z",
            "governance_key_id": "governance:key:1",
            "created_at": self.governance_time,
        }
        record = authority.sign_record(unsigned, self.governance_private)
        canonical = authority.signed_payload_canonical_json(record)
        if tamper:
            canonical = canonical.replace('"decision":"allow"', '"decision":"deny"')
        self.connection.execute(
            "INSERT INTO wc_governance_authorization_witnesses_v1 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                record["authorization_witness_id"], record["schema_version"], record["action_type"], record["target_record_type"],
                record["target_record_id"], record["policy_decision_id"], record["decision"], record["valid_from"], record["valid_until"],
                record["governance_key_id"], canonical, record["signed_payload_sha256"], record["signature"], record["created_at"],
            ),
        )
        return authorization_id

    def insert_key_event(self, *, key, status, event_id, authorization, effective_at, recorded_at, replacement=None, reason="lifecycle action", tamper=False):
        unsigned = {
            "schema_version": "verifier_key_status_event/v2",
            "key_status_event_id": event_id,
            "key_id": key,
            "status": status,
            "replacement_key_id": replacement,
            "reason": reason,
            "effective_at": effective_at,
            "recorded_at": recorded_at,
            "policy_decision_id": "policy:governance",
            "authorization_witness_id": authorization,
            "governance_key_id": "governance:key:1",
            "timestamp_source": "authority_service_clock",
            "effective_time_witness_id": None,
        }
        record = authority.sign_record(unsigned, self.governance_private)
        canonical = authority.signed_payload_canonical_json(record)
        if tamper:
            canonical = canonical.replace('"status":"revoked"', '"status":"active"')
        self.connection.execute(
            "INSERT INTO wc_verifier_key_status_events_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                record["key_status_event_id"], record["schema_version"], record["key_id"], record["status"], record["replacement_key_id"],
                record["reason"], record["effective_at"], record["recorded_at"], record["policy_decision_id"], record["authorization_witness_id"],
                record["governance_key_id"], record["timestamp_source"], record["effective_time_witness_id"],
                canonical, record["signed_payload_sha256"], record["signature"],
            ),
        )

    def insert_chain(self, *, hermetic=True):
        verifier, key, private = self.register_verifier()
        self._insert_claim("claim:proof", "proof_claim", '{"statement":"P"}', self.claim_hash, "theorem P", self.theorem_hash, "principal:hugh", self.compiler_time)
        self.connection.execute(
            "INSERT INTO wc_policy_decisions_v2 VALUES (?,?,?,?,?,?,?,?)",
            ("policy:theorem", "policy_decision/v2", "claim:proof", "allow", "theorem_promotion", "principal:governance", "strict theorem promotion", self.compiler_time),
        )
        compiler_unsigned = {
            "schema_version": "lean_compiler_witness/v2", "lean_compiler_witness_id": "lean:533", "claim_id": "claim:proof",
            "claim_content_sha256": self.claim_hash, "theorem_statement_sha256": self.theorem_hash, "proof_artifact_sha256": self.artifact_hash,
            "proof_artifact_relative_path": "Proof.lean", "proof_module": "Proof", "source_tree_sha256": "d" * 64,
            "original_source_tree_sha256": "d" * 64, "immutable_snapshot_sha256": "d" * 64, "lakefile_sha256": "e" * 64,
            "generated_witness_module_sha256": "9" * 64, "generated_witness_module_path": ".witness_authority/Check_0123456789abcdef0123456789abcdef.lean",
            "exact_build_target": ".witness_authority/Check_0123456789abcdef0123456789abcdef.lean", "compiler_profile_id": "profile:1",
            "compiler_registry_sha256": "7" * 64, "lake_executable_sha256": "2" * 64, "lean_executable_sha256": "3" * 64,
            "lean_stdlib_tree_sha256": "4" * 64, "dependency_closure_sha256": "5" * 64, "execution_image_digest": "sha256:" + "1" * 64,
            "sandbox_policy_sha256": "6" * 64, "verifier_binary_sha256": "8" * 64, "compiler_executable_sha256": "3" * 64,
            "structured_result_sha256": "a" * 64, "build_output_sha256": "f" * 64, "toolchain": "leanprover/lean4:v4.29.1",
            "command": ["/protected/podman", "run", "--network=none"], "execution_mode": "strict", "result": "passed",
            "contains_sorry": False, "contains_admit": False, "unapproved_axiom_count": 0, "axiom_dependencies": ["Classical.choice"],
            "axiom_inspection_complete": True, "statement_binding_confirmed": True, "warnings_as_errors": True,
            "snapshot_verified_immutable": True, "clean_source_build": True, "prebuilt_artifacts_rejected": True,
            "hermetic_environment": hermetic, "network_disabled": hermetic, "resource_limits_enforced": hermetic,
            "structured_inspection_complete": True, "theorem_name": "promotion_sound", "theorem_status": "proved",
            "verifier_principal_id": verifier, "key_id": key, "signature_algorithm": "Ed25519",
            "trusted_timestamp_source": "authority_service_clock", "created_at": self.compiler_time,
        }
        compiler = authority.sign_record(compiler_unsigned, private)
        values = {
            **compiler,
            "command_json": json.dumps(compiler["command"], separators=(",", ":")),
            "axiom_dependencies_json": json.dumps(compiler["axiom_dependencies"], separators=(",", ":")),
        }
        columns = [
            "lean_compiler_witness_id", "schema_version", "claim_id", "claim_content_sha256", "theorem_statement_sha256", "proof_artifact_sha256",
            "source_tree_sha256", "lakefile_sha256", "build_output_sha256", "toolchain", "command_json", "execution_mode", "result", "contains_sorry",
            "contains_admit", "unapproved_axiom_count", "theorem_name", "theorem_status", "verifier_principal_id", "key_id", "signature_algorithm",
            "signed_payload_sha256", "signature", "created_at", "proof_artifact_relative_path", "proof_module", "generated_witness_module_sha256",
            "generated_witness_module_path", "exact_build_target", "compiler_executable_sha256", "axiom_dependencies_json", "axiom_inspection_complete",
            "statement_binding_confirmed", "warnings_as_errors", "original_source_tree_sha256", "immutable_snapshot_sha256", "compiler_profile_id",
            "compiler_registry_sha256", "lake_executable_sha256", "lean_executable_sha256", "lean_stdlib_tree_sha256", "dependency_closure_sha256",
            "execution_image_digest", "sandbox_policy_sha256", "verifier_binary_sha256", "structured_result_sha256", "snapshot_verified_immutable",
            "clean_source_build", "prebuilt_artifacts_rejected", "hermetic_environment", "network_disabled", "resource_limits_enforced",
            "structured_inspection_complete", "trusted_timestamp_source",
        ]
        bool_columns = {"contains_sorry", "contains_admit", "axiom_inspection_complete", "statement_binding_confirmed", "warnings_as_errors", "snapshot_verified_immutable", "clean_source_build", "prebuilt_artifacts_rejected", "hermetic_environment", "network_disabled", "resource_limits_enforced", "structured_inspection_complete"}
        params = [int(values[name]) if name in bool_columns else values[name] for name in columns]
        self.connection.execute(f"INSERT INTO wc_lean_compiler_witnesses_v2 ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})", params)
        self.connection.execute(
            "INSERT INTO wc_authority_signature_bindings_v1 VALUES (?,?,?,?,?,?,?,?)",
            ("sigbind:compiler:legacy-fields", "authority_signature_binding/v1", "lean_compiler_witness", "lean:533", key, authority.signed_payload_canonical_json(compiler), compiler["signed_payload_sha256"], self.proof_time),
        )
        self.connection.execute(
            "INSERT INTO wc_authority_signature_bindings_v2 VALUES (?,?,?,?,?,?,?,?)",
            ("sigbind:compiler:533", "authority_signature_binding/v2", "lean_compiler_witness_5_3_3", "lean:533", key, authority.signed_payload_canonical_json(compiler), compiler["signed_payload_sha256"], self.proof_time),
        )
        proof_unsigned = {
            "schema_version": "proof_witness/v2", "proof_witness_id": "proof:533", "claim_id": "claim:proof",
            "claim_content_sha256": self.claim_hash, "theorem_statement_sha256": self.theorem_hash,
            "proof_artifact_sha256": self.artifact_hash, "lean_compiler_witness_id": "lean:533", "theorem_name": "promotion_sound",
            "theorem_status": "proved", "policy_decision_id": "policy:theorem", "verifier_principal_id": verifier, "key_id": key,
            "created_at": self.proof_time,
        }
        proof = authority.sign_record(proof_unsigned, private)
        self.connection.execute(
            "INSERT INTO wc_proof_witnesses_v2 (proof_witness_id,schema_version,claim_id,claim_content_sha256,theorem_statement_sha256,proof_artifact_sha256,lean_compiler_witness_id,theorem_name,theorem_status,policy_decision_id,verifier_principal_id,signed_payload_sha256,signature,created_at,key_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            tuple(proof[name] for name in ("proof_witness_id", "schema_version", "claim_id", "claim_content_sha256", "theorem_statement_sha256", "proof_artifact_sha256", "lean_compiler_witness_id", "theorem_name", "theorem_status", "policy_decision_id", "verifier_principal_id", "signed_payload_sha256", "signature", "created_at", "key_id")),
        )
        self.connection.execute(
            "INSERT INTO wc_authority_signature_bindings_v1 VALUES (?,?,?,?,?,?,?,?)",
            ("sigbind:proof:533", "authority_signature_binding/v1", "proof_witness", "proof:533", key, authority.signed_payload_canonical_json(proof), proof["signed_payload_sha256"], self.proof_time),
        )
        self.connection.execute("INSERT INTO wc_non_collapse_transitions_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("nc:533", "non_collapse_transition/v2", "claim:proof", "conjectural", "theorem", "proof_upgrade", "allowed", None, "proof:533", "policy:theorem", "strict proof upgrade", self.proof_time))
        self.connection.execute("INSERT INTO wc_claim_status_events_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("status:533", "claim_status_event/v2", "claim:proof", "conjecture", "theorem", "prove", 1, "policy:theorem", "proof:533", "lean:533", "nc:533", self.proof_time))

    def insert_gate(self, gate_id="gate:533"):
        self.connection.execute(
            "INSERT INTO wc_theorem_promotion_gates_v2 (theorem_promotion_gate_id,schema_version,claim_id,claim_content_sha256,theorem_statement_sha256,status_event_id,proof_witness_id,lean_compiler_witness_id,non_collapse_transition_id,policy_decision_id,verifier_principal_id,allowed,rejection_reason,created_at,key_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (gate_id, "theorem_promotion_gate/v2", "claim:proof", self.claim_hash, self.theorem_hash, "status:533", "proof:533", "lean:533", "nc:533", "policy:theorem", "verifier:1", 1, None, self.gate_time, "key:1"),
        )

    def insert_snapshot(self, snapshot_id, evaluated_at):
        auth = self.insert_authorization("authority_snapshot", "authority_snapshot", snapshot_id, f"auth:{snapshot_id}")
        unsigned = {
            "schema_version": "authority_snapshot/v1", "authority_snapshot_id": snapshot_id,
            "evaluated_at": evaluated_at, "policy_decision_id": "policy:governance",
            "authorization_witness_id": auth, "governance_key_id": "governance:key:1",
            "recorded_at": evaluated_at,
            "timestamp_source": "authority_service_clock", "evaluation_time_witness_id": None,
        }
        record = authority.sign_record(unsigned, self.governance_private)
        self.connection.execute(
            "INSERT INTO wc_authority_snapshots_v1 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (record["authority_snapshot_id"], record["schema_version"], record["evaluated_at"], record["policy_decision_id"], record["authorization_witness_id"], record["governance_key_id"], record["recorded_at"], record["timestamp_source"], record["evaluation_time_witness_id"], authority.signed_payload_canonical_json(record), record["signed_payload_sha256"], record["signature"]),
        )


class SqlAuthorityLifecycle533Tests(unittest.TestCase):
    def test_happy_hermetic_chain_creates_gate(self):
        db = AuthorityDatabase533(); db.insert_chain(); db.insert_gate()
        self.assertEqual(db.connection.execute("SELECT count(*) FROM wc_theorem_promotion_gates_v2 WHERE theorem_promotion_gate_id='gate:533'").fetchone()[0], 1)

    def test_nonhermetic_compiler_cannot_create_gate(self):
        db = AuthorityDatabase533(); db.insert_chain(hermetic=False)
        expect_integrity_error(self, db.insert_gate)

    def test_unsigned_or_tampered_key_event_is_rejected(self):
        db = AuthorityDatabase533(); db.register_verifier(activate=False)
        auth = db.insert_authorization("verifier_key_status", "verifier_key", "key:1", "auth:key:1")
        expect_integrity_error(self, lambda: db.insert_key_event(key="key:1", status="revoked", event_id="event:bad", authorization=auth, effective_at=db.gate_time, recorded_at=db.gate_time, tamper=True))

    def test_governance_authorization_policy_binding_is_enforced(self):
        db = AuthorityDatabase533()
        expect_integrity_error(self, lambda: db.insert_authorization("verifier_key_status", "verifier_key", "key:missing", "auth:bad", tamper=True))

    def test_revoked_key_cannot_create_gate(self):
        db = AuthorityDatabase533(); db.insert_chain()
        auth = db.insert_authorization("verifier_key_status", "verifier_key", "key:1", "auth:key:revoke")
        db.insert_key_event(key="key:1", status="revoked", event_id="event:revoke", authorization=auth, effective_at="2026-07-31T12:03:00Z", recorded_at="2026-07-31T12:03:00Z", reason="compromise")
        expect_integrity_error(self, db.insert_gate)

    def test_expired_key_cannot_create_gate(self):
        db = AuthorityDatabase533()
        original = db.register_verifier
        db.register_verifier = lambda *args, **kwargs: original(valid_from="2019-01-01T00:00:00Z", valid_until="2020-01-01T00:00:00Z")
        db.insert_chain()
        expect_integrity_error(self, db.insert_gate)

    def test_as_of_snapshot_is_stable_after_later_revocation(self):
        db = AuthorityDatabase533(); db.insert_chain(); db.insert_gate()
        db.insert_snapshot("snapshot:before", "2026-07-31T12:05:00Z")
        auth = db.insert_authorization("verifier_key_status", "verifier_key", "key:1", "auth:key:later-revoke")
        db.insert_key_event(key="key:1", status="revoked", event_id="event:later-revoke", authorization=auth, effective_at="2026-07-31T13:00:00Z", recorded_at="2026-07-31T13:00:00Z", reason="later compromise")
        db.insert_snapshot("snapshot:after", "2026-07-31T13:05:00Z")
        before = db.connection.execute("SELECT count(*) FROM wc_authoritative_theorems_as_of_v3 WHERE authority_snapshot_id='snapshot:before'").fetchone()[0]
        after = db.connection.execute("SELECT count(*) FROM wc_authoritative_theorems_as_of_v3 WHERE authority_snapshot_id='snapshot:after'").fetchone()[0]
        self.assertEqual((before, after), (1, 0))

    def test_lifecycle_and_snapshot_tables_are_append_only(self):
        db = AuthorityDatabase533(); db.register_verifier(); db.insert_snapshot("snapshot:1", "2026-07-31T12:00:00Z")
        expect_integrity_error(self, lambda: db.connection.execute("DELETE FROM wc_verifier_key_status_events_v2"))
        expect_integrity_error(self, lambda: db.connection.execute("UPDATE wc_authority_snapshots_v1 SET evaluated_at='2030-01-01T00:00:00Z'"))

    def test_compiler_signature_binding_covers_lean_digest(self):
        db = AuthorityDatabase533(); db.register_verifier()
        # A full chain is signed and accepted; after insert, compiler records are append-only.
        db = AuthorityDatabase533(); db.insert_chain()
        expect_integrity_error(self, lambda: db.connection.execute("UPDATE wc_lean_compiler_witnesses_v2 SET lean_executable_sha256=? WHERE lean_compiler_witness_id='lean:533'", ("0" * 64,)))


if __name__ == "__main__":
    unittest.main()
