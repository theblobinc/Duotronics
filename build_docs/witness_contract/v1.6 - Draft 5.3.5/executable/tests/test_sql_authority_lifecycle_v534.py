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
SPEC = importlib.util.spec_from_file_location("proof_authority_sql_534", ROOT / "executable/runtime/proof_authority.py")
authority = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = authority
SPEC.loader.exec_module(authority)


def rejected(testcase: unittest.TestCase, action) -> None:
    with testcase.assertRaises(sqlite3.IntegrityError):
        action()


class AuthorityDatabase534:
    def __init__(self):
        self.connection = sqlite3.connect(":memory:", isolation_level=None)
        authority.register_sqlite_crypto_functions(self.connection)
        self.connection.execute("PRAGMA foreign_keys = ON")
        for relative in (
            "executable/sql/draft5_2_schema_additions.sql",
            "migration/draft5_2_2_to_draft5_3_1.sql",
            "migration/draft5_3_1_to_draft5_3_2.sql",
            "migration/draft5_3_2_to_draft5_3_3.sql",
            "migration/draft5_3_3_to_draft5_3_4.sql",
        ):
            self.connection.executescript((ROOT / relative).read_text(encoding="utf-8"))
        self.governance_private = Ed25519PrivateKey.generate()
        self.result_private = Ed25519PrivateKey.generate()
        public = self.governance_private.public_key()
        self.connection.execute(
            "INSERT INTO wc_governance_authorities_v1 VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("governance:key:534", "governance_authority/v1", "principal:governance", authority.public_key_raw_b64url(public),
             authority.public_key_fingerprint(public), "2020-01-01T00:00:00Z", "2099-01-01T00:00:00Z",
             "provisioned", "external-trust:test", "2020-01-01T00:00:00Z"),
        )

    def close(self):
        connection = getattr(self, "connection", None)
        if connection is not None:
            connection.close(); self.connection = None

    def __enter__(self): return self
    def __exit__(self, *_): self.close()
    def __del__(self): self.close()

    def register_record(self, record_type: str, record_id: str, recorded_at="2026-07-31T10:00:00Z"):
        self.connection.execute("INSERT INTO wc_authority_record_index_v1 VALUES (?,?,?)", (record_type, record_id, recorded_at))

    def add_profile(self, profile_id: str):
        unsigned = {
            "schema_version": "compiler_profile/v2", "compiler_profile_id": profile_id,
            "registry_sha256": "a" * 64, "oci_image_digest": "sha256:" + "b" * 64,
            "oci_runtime_sha256": "c" * 64, "oci_runtime_version": "podman version 5.4.0",
            "verifier_executable_sha256": "d" * 64, "lean_executable_sha256": "e" * 64,
            "lake_executable_sha256": "f" * 64, "lean_stdlib_tree_sha256": "0" * 64,
            "dependency_closure_sha256": "1" * 64, "sandbox_policy_sha256": "2" * 64,
            "verifier_source_revision": "git:0123456789abcdef", "verifier_build_attestation_id": "attestation:verifier:1",
            "verifier_result_signer_key_id": "result-key:1",
            "verifier_result_public_key_base64url": authority.public_key_raw_b64url(self.result_private.public_key()),
            "valid_from": "2026-01-01T00:00:00Z", "valid_until": "2027-01-01T00:00:00Z",
            "governance_key_id": "governance:key:534", "created_at": "2026-07-31T10:00:00Z",
        }
        signed = authority.sign_record(unsigned, self.governance_private)
        self.connection.execute(
            "INSERT INTO wc_compiler_profiles_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (profile_id, unsigned["schema_version"], unsigned["registry_sha256"], unsigned["oci_image_digest"],
             unsigned["oci_runtime_sha256"], unsigned["oci_runtime_version"], unsigned["verifier_executable_sha256"],
             unsigned["lean_executable_sha256"], unsigned["lake_executable_sha256"], unsigned["lean_stdlib_tree_sha256"],
             unsigned["dependency_closure_sha256"], unsigned["sandbox_policy_sha256"], unsigned["verifier_source_revision"],
             unsigned["verifier_build_attestation_id"], unsigned["verifier_result_signer_key_id"],
             unsigned["verifier_result_public_key_base64url"], unsigned["valid_from"], unsigned["valid_until"],
             unsigned["governance_key_id"], authority.signed_payload_canonical_json(signed),
             signed["signed_payload_sha256"], signed["signature"], unsigned["created_at"]),
        )

    def add_verifier(self, key_id="key:534", principal_id="verifier:534"):
        self.verifier_private = Ed25519PrivateKey.generate()
        public = self.verifier_private.public_key()
        fingerprint = authority.public_key_fingerprint(public)
        self.connection.execute(
            "INSERT INTO wc_verifier_principals_v2 VALUES (?,?,?,?,?,?,?,?,?)",
            (principal_id, "verifier_principal/v2", key_id, "Ed25519", fingerprint, "active",
             "2026-01-01T00:00:00Z", "2027-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
        )
        self.connection.execute(
            "INSERT INTO wc_verifier_keys_v3 VALUES (?,?,?,?,?,?,?,?,?)",
            (key_id, "verifier_key/v3", principal_id, "Ed25519", authority.public_key_raw_b64url(public),
             fingerprint, "2026-01-01T00:00:00Z", "2027-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
        )
        self.event("verifier_key_activate", "verifier_key_activate", "verifier_key", key_id, "event:key:activate")
        return key_id

    def add_compiler_witness(self, snapshot_id: str, cutoff: int, *, witness_id="lean:534", result_tamper=False):
        result_unsigned = {
            "schema_version": "wc_lean_verifier_result/v2", "status": "passed", "request_id": "request:534",
            "request_sha256": "0" * 64, "compiler_profile_id": "profile:534",
            "claim_content_sha256": "1" * 64, "theorem_statement_sha256": "2" * 64,
            "proof_artifact_sha256": "3" * 64, "immutable_snapshot_id": "sha256:" + "4" * 64,
            "immutable_snapshot_tree_sha256": "4" * 64, "generated_binding_module_sha256": "5" * 64,
            "effective_sandbox_invocation_sha256": "6" * 64,
        }
        result_signed = authority.sign_record(result_unsigned, self.result_private)
        result_payload = authority.signed_payload_canonical_json(result_signed)
        witness_unsigned = {
            "schema_version": "lean_compiler_witness/v3", "lean_compiler_witness_id": witness_id,
            "semantic_witness_content_id": "lean-semantic:" + "7" * 64, "claim_id": "claim:534",
            "claim_content_sha256": "1" * 64, "theorem_statement_sha256": "2" * 64,
            "immutable_snapshot_id": "sha256:" + "4" * 64, "immutable_snapshot_tree_sha256": "4" * 64,
            "proof_artifact_relative_path": "Proof.lean", "proof_artifact_sha256": "3" * 64,
            "generated_binding_module_sha256": "5" * 64, "generated_binding_request_sha256": "8" * 64,
            "compiler_profile_id": "profile:534", "verifier_result_payload_sha256": result_signed["signed_payload_sha256"],
            "verifier_result_signer_key_id": "result-key:1", "verifier_result_signature": result_signed["signature"],
            "expected_type_expression_hash": "9" * 64, "actual_type_expression_hash": "9" * 64,
            "axiom_set_sha256": "a" * 64, "result": "passed", "theorem_status": "proved",
            "statement_binding_confirmed": 1, "snapshot_verified_immutable": 1, "result_channel_isolated": 1,
            "authority_snapshot_id": snapshot_id, "authority_ledger_high_water_sequence": cutoff,
            "key_id": "key:534", "created_at": "2026-07-31T12:32:00Z",
        }
        witness_signed = authority.sign_record(witness_unsigned, self.verifier_private)
        if result_tamper:
            result_payload = result_payload.replace('"status":"passed"', '"status":"failed"')
        columns = list(witness_unsigned) + ["verifier_result_signed_payload_canonical_json", "signed_payload_canonical_json", "signed_payload_sha256", "signature"]
        values = [witness_unsigned[name] for name in witness_unsigned] + [
            result_payload, authority.signed_payload_canonical_json(witness_signed),
            witness_signed["signed_payload_sha256"], witness_signed["signature"],
        ]
        self.connection.execute(
            f"INSERT INTO wc_lean_compiler_witnesses_v3 ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
            values,
        )

    def activate_release(self):
        unsigned = {
            "schema_version": "release_activation_evidence/v1", "package_version": "v1.6-draft-5.3.4",
            "result_channel_isolation": 1, "snapshot_identity": 1, "historical_snapshot_immutability": 1,
            "execution_closure_identity": 1, "real_lean_integration": 1, "strict_lean": 1, "strict_tlc": 1,
            "external_governance_signature": 1, "signer_key_id": "governance:key:534",
            "created_at": "2026-07-31T12:33:00Z",
        }
        signed = authority.sign_record(unsigned, self.governance_private)
        self.connection.execute(
            "INSERT INTO wc_release_activation_evidence_v1 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (unsigned["package_version"], 1, 1, 1, 1, 1, 1, 1, 1, unsigned["signer_key_id"],
             unsigned["created_at"], authority.signed_payload_canonical_json(signed), signed["signed_payload_sha256"], signed["signature"]),
        )

    def add_gate(self, gate_id="gate:534", witness_id="lean:534", snapshot_id="snapshot:534", approval_event_id="event:gate:approve"):
        self.connection.execute(
            "INSERT INTO wc_theorem_promotion_gates_v3 VALUES (?,?,?,?,?)",
            (gate_id, witness_id, snapshot_id, approval_event_id, "2026-07-31T12:34:00Z"),
        )

    def authorization(self, scope: str, target_type: str, target_id: str, auth_id: str, *,
                      valid_from="2026-01-01T00:00:00Z", valid_until="2027-01-01T00:00:00Z", tamper=False):
        unsigned = {
            "schema_version": "governance_authorization_witness/v2", "authorization_witness_id": auth_id,
            "action_scope": scope, "target_type": target_type, "target_id": target_id,
            "principal_id": "principal:governance", "governance_policy_version": "governance-policy/5.3.4",
            "decision": "allow", "valid_from": valid_from, "valid_until": valid_until,
            "signer_key_id": "governance:key:534", "created_at": "2026-07-31T09:00:00Z",
        }
        signed = authority.sign_record(unsigned, self.governance_private)
        canonical = authority.signed_payload_canonical_json(signed)
        if tamper:
            canonical = canonical.replace('"decision":"allow"', '"decision":"deny"')
        self.connection.execute(
            "INSERT INTO wc_governance_authorization_witnesses_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (auth_id, unsigned["schema_version"], scope, target_type, target_id, unsigned["principal_id"],
             unsigned["governance_policy_version"], unsigned["decision"], valid_from, valid_until,
             unsigned["signer_key_id"], canonical, signed["signed_payload_sha256"], signed["signature"], unsigned["created_at"]),
        )
        return auth_id

    def event(self, event_type: str, scope: str, target_type: str, target_id: str, event_id: str, *,
              effective_at="2026-07-31T12:00:00Z", recorded_at="2026-07-31T12:00:00Z",
              authorization_id: str | None = None, sequence: int | None = None, tamper=False,
              tamper_column=False,
              is_backdated=False, backdate_authorization_id=None, prior_snapshots=None,
              correction_mode="not_applicable"):
        authorization_id = authorization_id or self.authorization(scope, target_type, target_id, f"auth:{event_id}")
        sequence = sequence or self.connection.execute("SELECT COALESCE(max(authority_event_sequence),0)+1 FROM wc_authority_events_v1").fetchone()[0]
        unsigned = {
            "schema_version": "governance_event/v1", "authority_event_sequence": sequence, "event_id": event_id,
            "event_type": event_type, "action_scope": scope, "target_type": target_type, "target_id": target_id,
            "effective_at": effective_at, "recorded_at": recorded_at, "reason_code": "governed_action",
            "rationale": "test governance action", "governance_policy_version": "governance-policy/5.3.4",
            "authorization_witness_id": authorization_id, "signer_key_id": "governance:key:534",
            "is_backdated": bool(is_backdated), "correction_reason": "backdated correction" if is_backdated else None,
            "prior_affected_snapshot_ids": prior_snapshots or [], "correction_mode": correction_mode,
            "backdate_authorization_witness_id": backdate_authorization_id,
        }
        signed = authority.sign_record(unsigned, self.governance_private)
        canonical = authority.signed_payload_canonical_json(signed)
        if tamper:
            canonical = canonical.replace('"reason_code":"governed_action"', '"reason_code":"tampered"')
        self.connection.execute(
            "INSERT INTO wc_authority_events_v1 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (sequence, event_id, unsigned["schema_version"], event_type, scope, target_type, target_id,
             effective_at, recorded_at, "column_tamper" if tamper_column else unsigned["reason_code"], unsigned["rationale"], unsigned["governance_policy_version"],
             authorization_id, unsigned["signer_key_id"], int(is_backdated), unsigned["correction_reason"],
             json.dumps(unsigned["prior_affected_snapshot_ids"], separators=(",", ":")), correction_mode,
             backdate_authorization_id, canonical, signed["signed_payload_sha256"], signed["signature"]),
        )
        return event_id

    def event_root(self, cutoff: int) -> str:
        events = self.connection.execute(
            "SELECT authority_event_sequence, canonical_payload_sha256 FROM wc_authority_events_v1 WHERE authority_event_sequence <= ? ORDER BY authority_event_sequence",
            (cutoff,),
        ).fetchall()
        return authority.authority_event_set_root(events)

    def snapshot(self, snapshot_id: str, cutoff: int, *, as_of="2026-07-31T12:30:00Z", root_override=None):
        auth = self.authorization("authority_snapshot_create", "authority_snapshot", snapshot_id, f"auth:{snapshot_id}")
        unsigned = {
            "schema_version": "authority_snapshot/v2", "snapshot_id": snapshot_id,
            "as_of_effective_time": as_of, "ledger_high_water_sequence": cutoff,
            "event_set_root_sha256": root_override or self.event_root(cutoff),
            "authority_policy_version": "governance-policy/5.3.4", "snapshot_query_version": "authority_as_of_cutoff/v1",
            "created_at": "2026-07-31T12:31:00Z", "created_by_principal": "principal:governance",
            "authorization_witness_id": auth, "signer_key_id": "governance:key:534",
            "supersedes_snapshot_id": None, "supersession_reason": None,
        }
        signed = authority.sign_record(unsigned, self.governance_private)
        self.connection.execute(
            "INSERT INTO wc_authority_snapshots_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (snapshot_id, unsigned["schema_version"], as_of, cutoff, unsigned["event_set_root_sha256"],
             unsigned["authority_policy_version"], unsigned["snapshot_query_version"], unsigned["created_at"],
             unsigned["created_by_principal"], auth, unsigned["signer_key_id"], None, None,
             authority.signed_payload_canonical_json(signed), signed["signed_payload_sha256"], signed["signature"]),
        )


class SqlAuthorityLifecycle534Tests(unittest.TestCase):
    def test_full_signed_authority_chain_is_accepted_only_after_release_activation(self):
        db = AuthorityDatabase534()
        db.add_verifier(); db.add_profile("profile:534")
        db.event("compiler_profile_activate", "compiler_profile_activate", "compiler_profile", "profile:534", "event:profile:activate")
        db.event("promotion_gate_approve", "promotion_gate_approve", "promotion_gate", "gate:534", "event:gate:approve")
        db.snapshot("snapshot:534", 3)
        db.add_compiler_witness("snapshot:534", 3)
        rejected(self, db.add_gate)
        db.activate_release(); db.add_gate()
        self.assertEqual(db.connection.execute("SELECT count(*) FROM wc_authoritative_theorems_v3").fetchone()[0], 1)

    def test_tampered_trusted_result_and_missing_profile_activation_are_rejected(self):
        db = AuthorityDatabase534()
        db.add_verifier(); db.add_profile("profile:534")
        db.event("compiler_profile_activate", "compiler_profile_activate", "compiler_profile", "profile:534", "event:profile:activate")
        db.event("promotion_gate_approve", "promotion_gate_approve", "promotion_gate", "gate:534", "event:gate:approve")
        db.snapshot("snapshot:534", 3)
        rejected(self, lambda: db.add_compiler_witness("snapshot:534", 3, result_tamper=True))

        missing = AuthorityDatabase534()
        missing.add_verifier(); missing.add_profile("profile:534")
        missing.event("promotion_gate_approve", "promotion_gate_approve", "promotion_gate", "gate:534", "event:gate:approve")
        missing.snapshot("snapshot:534", 2)
        missing.add_compiler_witness("snapshot:534", 2)
        missing.activate_release()
        rejected(self, missing.add_gate)

    def test_monotonic_signed_event_is_accepted(self):
        db = AuthorityDatabase534(); db.add_profile("profile:a")
        db.event("compiler_profile_activate", "compiler_profile_activate", "compiler_profile", "profile:a", "event:activate")
        self.assertEqual(db.connection.execute("SELECT authority_event_sequence FROM wc_authority_events_v1").fetchone()[0], 1)

    def test_tampered_event_wrong_scope_and_duplicate_sequence_are_rejected(self):
        db = AuthorityDatabase534(); db.add_profile("profile:a")
        auth = db.authorization("compiler_profile_activate", "compiler_profile", "profile:a", "auth:a")
        rejected(self, lambda: db.event("compiler_profile_activate", "compiler_profile_activate", "compiler_profile", "profile:a", "event:tampered", authorization_id=auth, tamper=True))
        rejected(self, lambda: db.event("compiler_profile_activate", "compiler_profile_activate", "compiler_profile", "profile:a", "event:column-tampered", authorization_id=auth, tamper_column=True))
        wrong = db.authorization("compiler_profile_revoke", "compiler_profile", "profile:a", "auth:wrong")
        rejected(self, lambda: db.event("compiler_profile_activate", "compiler_profile_activate", "compiler_profile", "profile:a", "event:wrong", authorization_id=wrong))
        db.event("compiler_profile_activate", "compiler_profile_activate", "compiler_profile", "profile:a", "event:ok", authorization_id=auth)
        rejected(self, lambda: db.event("compiler_profile_revoke", "compiler_profile_revoke", "compiler_profile", "profile:a", "event:duplicate", sequence=1))

    def test_expired_authorization_and_wrong_typed_target_are_rejected(self):
        db = AuthorityDatabase534(); db.add_profile("profile:a")
        expired = db.authorization("compiler_profile_activate", "compiler_profile", "profile:a", "auth:expired", valid_from="2020-01-01T00:00:00Z", valid_until="2021-01-01T00:00:00Z")
        rejected(self, lambda: db.event("compiler_profile_activate", "compiler_profile_activate", "compiler_profile", "profile:a", "event:expired", authorization_id=expired))
        db.register_record("verifier_key", "record:wrong")
        auth = db.authorization("compiler_profile_activate", "compiler_profile", "record:wrong", "auth:type")
        rejected(self, lambda: db.event("compiler_profile_activate", "compiler_profile_activate", "compiler_profile", "record:wrong", "event:type", authorization_id=auth))

    def test_backdated_event_requires_explicit_correction_authorization(self):
        db = AuthorityDatabase534(); db.add_profile("profile:a")
        db.event("compiler_profile_activate", "compiler_profile_activate", "compiler_profile", "profile:a", "event:first")
        revoke_auth = db.authorization("compiler_profile_revoke", "compiler_profile", "profile:a", "auth:revoke")
        rejected(self, lambda: db.event("compiler_profile_revoke", "compiler_profile_revoke", "compiler_profile", "profile:a", "event:backdated-bad", authorization_id=revoke_auth, effective_at="2026-07-31T11:00:00Z", recorded_at="2026-07-31T13:00:00Z"))
        backdate_auth = db.authorization("backdated_event_authorize", "authority_event", "event:backdated-ok", "auth:backdate")
        db.event("compiler_profile_revoke", "compiler_profile_revoke", "compiler_profile", "profile:a", "event:backdated-ok", authorization_id=revoke_auth, effective_at="2026-07-31T11:00:00Z", recorded_at="2026-07-31T13:00:00Z", is_backdated=True, backdate_authorization_id=backdate_auth, prior_snapshots=["snapshot:old"], correction_mode="requires_snapshot_supersession")
        self.assertEqual(db.connection.execute("SELECT is_backdated FROM wc_authority_events_v1 WHERE event_id='event:backdated-ok'").fetchone()[0], 1)

    def test_ledger_cutoff_keeps_prior_snapshot_stable_after_later_backdated_event(self):
        db = AuthorityDatabase534(); db.add_profile("profile:a")
        db.event("compiler_profile_activate", "compiler_profile_activate", "compiler_profile", "profile:a", "event:activate")
        db.snapshot("snapshot:one", 1)
        before = db.connection.execute("SELECT event_id FROM wc_authority_events_as_of_snapshot_v1 WHERE snapshot_id='snapshot:one' ORDER BY authority_event_sequence").fetchall()
        revoke = db.authorization("compiler_profile_revoke", "compiler_profile", "profile:a", "auth:revoke")
        back = db.authorization("backdated_event_authorize", "authority_event", "event:revoke", "auth:back")
        db.event("compiler_profile_revoke", "compiler_profile_revoke", "compiler_profile", "profile:a", "event:revoke", authorization_id=revoke, effective_at="2026-07-31T11:30:00Z", recorded_at="2026-07-31T13:00:00Z", is_backdated=True, backdate_authorization_id=back, prior_snapshots=["snapshot:one"], correction_mode="requires_snapshot_supersession")
        after = db.connection.execute("SELECT event_id FROM wc_authority_events_as_of_snapshot_v1 WHERE snapshot_id='snapshot:one' ORDER BY authority_event_sequence").fetchall()
        db.snapshot("snapshot:two", 2)
        current = db.connection.execute("SELECT event_id FROM wc_authority_events_as_of_snapshot_v1 WHERE snapshot_id='snapshot:two' ORDER BY authority_event_sequence").fetchall()
        self.assertEqual(before, after); self.assertEqual(before, [("event:activate",)]); self.assertEqual(current, [("event:activate",), ("event:revoke",)])

    def test_snapshot_rejects_wrong_event_root_and_future_cutoff(self):
        db = AuthorityDatabase534(); db.add_profile("profile:a")
        db.event("compiler_profile_activate", "compiler_profile_activate", "compiler_profile", "profile:a", "event:activate")
        rejected(self, lambda: db.snapshot("snapshot:bad-root", 1, root_override="0" * 64))
        rejected(self, lambda: db.snapshot("snapshot:future", 2))

    def test_snapshot_event_and_authorization_records_are_append_only(self):
        db = AuthorityDatabase534(); db.add_profile("profile:a")
        db.event("compiler_profile_activate", "compiler_profile_activate", "compiler_profile", "profile:a", "event:activate")
        db.snapshot("snapshot:one", 1)
        for sql in (
            "UPDATE wc_authority_events_v1 SET rationale='changed' WHERE event_id='event:activate'",
            "DELETE FROM wc_authority_snapshots_v2 WHERE snapshot_id='snapshot:one'",
            "UPDATE wc_governance_authorization_witnesses_v2 SET decision='allow'",
        ):
            rejected(self, lambda statement=sql: db.connection.execute(statement))

    def test_typed_supersession_happy_path_and_self_reference(self):
        db = AuthorityDatabase534(); db.add_profile("profile:a"); db.add_profile("profile:b")
        event = db.event("authority_record_supersede", "authority_record_supersede", "compiler_profile", "profile:a", "event:supersede")
        db.connection.execute("INSERT INTO wc_authority_supersessions_v3 VALUES (?,?,?,?,?,?,?,?)", ("sup:a-b", "authority_supersession/v3", "compiler_profile", "profile:a", "profile:b", "replacement", event, "2026-07-31T12:00:00Z"))
        self.assertEqual(db.connection.execute("SELECT replacement_record_id FROM wc_authority_supersessions_v3").fetchone()[0], "profile:b")
        db2 = AuthorityDatabase534(); db2.add_profile("profile:a")
        event2 = db2.event("authority_record_supersede", "authority_record_supersede", "compiler_profile", "profile:a", "event:self")
        rejected(self, lambda: db2.connection.execute("INSERT INTO wc_authority_supersessions_v3 VALUES (?,?,?,?,?,?,?,?)", ("sup:self", "authority_supersession/v3", "compiler_profile", "profile:a", "profile:a", "self", event2, "2026-07-31T12:00:00Z")))

    def test_supersession_rejects_nonexistent_wrong_type_cycle_and_revoked_replacement(self):
        db = AuthorityDatabase534(); db.add_profile("profile:a"); db.add_profile("profile:b"); db.add_profile("profile:c")
        event = db.event("authority_record_supersede", "authority_record_supersede", "compiler_profile", "profile:a", "event:a-b")
        rejected(self, lambda: db.connection.execute("INSERT INTO wc_authority_supersessions_v3 VALUES (?,?,?,?,?,?,?,?)", ("sup:missing", "authority_supersession/v3", "compiler_profile", "profile:a", "missing", "bad", event, "2026-07-31T12:00:00Z")))
        db.register_record("verifier_key", "wrong-type")
        rejected(self, lambda: db.connection.execute("INSERT INTO wc_authority_supersessions_v3 VALUES (?,?,?,?,?,?,?,?)", ("sup:type", "authority_supersession/v3", "compiler_profile", "profile:a", "wrong-type", "bad", event, "2026-07-31T12:00:00Z")))
        db.connection.execute("INSERT INTO wc_authority_supersessions_v3 VALUES (?,?,?,?,?,?,?,?)", ("sup:a-b", "authority_supersession/v3", "compiler_profile", "profile:a", "profile:b", "replace", event, "2026-07-31T12:00:00Z"))
        event_cycle = db.event("authority_record_supersede", "authority_record_supersede", "compiler_profile", "profile:b", "event:b-a")
        rejected(self, lambda: db.connection.execute("INSERT INTO wc_authority_supersessions_v3 VALUES (?,?,?,?,?,?,?,?)", ("sup:b-a", "authority_supersession/v3", "compiler_profile", "profile:b", "profile:a", "cycle", event_cycle, "2026-07-31T12:00:00Z")))
        revoke = db.event("compiler_profile_revoke", "compiler_profile_revoke", "compiler_profile", "profile:c", "event:revoke-c")
        event_replace = db.event("authority_record_supersede", "authority_record_supersede", "compiler_profile", "profile:b", "event:b-c", effective_at="2026-07-31T12:01:00Z", recorded_at="2026-07-31T12:01:00Z")
        rejected(self, lambda: db.connection.execute("INSERT INTO wc_authority_supersessions_v3 VALUES (?,?,?,?,?,?,?,?)", ("sup:b-c", "authority_supersession/v3", "compiler_profile", "profile:b", "profile:c", "revoked", event_replace, "2026-07-31T12:01:00Z")))

    def test_theorem_authority_is_disabled_without_external_release_evidence(self):
        db = AuthorityDatabase534()
        self.assertEqual(db.connection.execute("SELECT count(*) FROM wc_release_activation_evidence_v1").fetchone()[0], 0)
        self.assertEqual(db.connection.execute("SELECT count(*) FROM wc_authoritative_theorems_v3").fetchone()[0], 0)

    def test_release_activation_requires_signed_complete_external_evidence_and_is_immutable(self):
        db = AuthorityDatabase534()
        rejected(self, lambda: db.connection.execute(
            "INSERT INTO wc_release_activation_evidence_v1 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("v1.6-draft-5.3.4", 1, 1, 1, 1, 1, 1, 1, 1, "governance:key:534",
             "2026-07-31T12:00:00Z", "{}", authority.sha256_bytes(b"{}"), "invalid"),
        ))
        unsigned = {
            "schema_version": "release_activation_evidence/v1", "package_version": "v1.6-draft-5.3.4",
            "result_channel_isolation": 1, "snapshot_identity": 1, "historical_snapshot_immutability": 1,
            "execution_closure_identity": 1, "real_lean_integration": 1, "strict_lean": 1, "strict_tlc": 1,
            "external_governance_signature": 1, "signer_key_id": "governance:key:534",
            "created_at": "2026-07-31T12:00:00Z",
        }
        signed = authority.sign_record(unsigned, db.governance_private)
        db.connection.execute(
            "INSERT INTO wc_release_activation_evidence_v1 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (unsigned["package_version"], 1, 1, 1, 1, 1, 1, 1, 1, unsigned["signer_key_id"],
             unsigned["created_at"], authority.signed_payload_canonical_json(signed),
             signed["signed_payload_sha256"], signed["signature"]),
        )
        self.assertEqual(db.connection.execute("SELECT count(*) FROM wc_release_activation_evidence_v1").fetchone()[0], 1)
        rejected(self, lambda: db.connection.execute("UPDATE wc_release_activation_evidence_v1 SET signature='changed'"))
        rejected(self, lambda: db.connection.execute("DELETE FROM wc_release_activation_evidence_v1"))


if __name__ == "__main__":
    unittest.main()
