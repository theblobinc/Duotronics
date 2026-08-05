#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import sqlite3
import sys
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executable/runtime"))
import proof_authority as authority


class PolicySqlTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:", isolation_level=None)
        self.addCleanup(self.connection.close)
        authority.register_sqlite_crypto_functions(self.connection); self.connection.execute("PRAGMA foreign_keys=ON")
        for relative in ("executable/sql/draft5_2_schema_additions.sql","migration/draft5_2_2_to_draft5_3_1.sql","migration/draft5_3_1_to_draft5_3_2.sql","migration/draft5_3_2_to_draft5_3_3.sql","migration/draft5_3_3_to_draft5_3_4.sql","migration/draft5_3_4_to_draft5_3_5.sql"):
            self.connection.executescript((ROOT / relative).read_text(encoding="utf-8"))
        self.key = Ed25519PrivateKey.generate(); public = self.key.public_key()
        self.connection.execute("INSERT INTO wc_governance_authorities_v1 VALUES (?,?,?,?,?,?,?,?,?,?)", ("gov:key:535","governance_authority/v1","principal:gov",authority.public_key_raw_b64url(public),authority.public_key_fingerprint(public),"2020-01-01T00:00:00Z","2099-01-01T00:00:00Z","provisioned","external:test","2020-01-01T00:00:00Z"))

    def records(self):
        decision = {"schema_version":"proof_policy_decision/v1","policy_decision_id":"policy:535","status":"active","subject_id":"principal:1","operation":"proof_check","compiler_profile_ids":["profile:1"],"source_bundle_ids":["bundle:1"],"resource_permissions":{"maximum_timeout_seconds":600,"maximum_source_bytes":1000},"valid_from":"2026-01-01T00:00:00Z","valid_until":"2027-01-01T00:00:00Z","supersedes_policy_decision_id":None,"governance_authority_id":"gov:key:535","created_at":"2026-07-31T00:00:00Z"}
        canonical = authority.canonical_text(decision); digest = authority.sha256_bytes(canonical.encode()); full = dict(decision, canonical_record_sha256=digest)
        registry = authority.sign_record({"schema_version":"proof_policy_registry/v1","registry_id":"registry:535","governance_key_id":"gov:key:535","decisions":[full],"created_at":"2026-07-31T00:00:00Z"}, self.key)
        return decision, canonical, digest, registry

    def insert_registry(self, registry):
        payload = authority.signed_payload_canonical_json(registry)
        self.connection.execute("INSERT INTO wc_proof_policy_registries_v1 VALUES (?,?,?,?,?,?,?)", ("registry:535","proof_policy_registry/v1","gov:key:535",payload,authority.sha256_bytes(payload.encode()),registry["signature"],"2026-07-31T00:00:00Z"))

    def test_policy_registry_membership_hash_and_immutability(self):
        decision, canonical, digest, registry = self.records(); self.insert_registry(registry)
        values = ("policy:535","proof_policy_decision/v1","registry:535",canonical,digest,"active","principal:1","proof_check",authority.canonical_text(["profile:1"]),authority.canonical_text(["bundle:1"]),"2026-01-01T00:00:00Z","2027-01-01T00:00:00Z",None,"2026-07-31T00:00:00Z")
        self.connection.execute("INSERT INTO wc_proof_policy_decisions_v1 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
        with self.assertRaises(sqlite3.IntegrityError): self.connection.execute("UPDATE wc_proof_policy_decisions_v1 SET status='revoked'")
        bad = list(values); bad[0] = "policy:other"; bad[4] = "0" * 64
        with self.assertRaises(sqlite3.IntegrityError): self.connection.execute("INSERT INTO wc_proof_policy_decisions_v1 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", bad)


if __name__ == "__main__": unittest.main()
