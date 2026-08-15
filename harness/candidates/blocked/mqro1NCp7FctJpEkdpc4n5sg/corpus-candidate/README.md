# Witness Contract 5.3.17 complete corpus

5.3.17 replaces the legacy classical cryptographic profile with a versioned, post-quantum-first suite:

- `SHAKE256-512` for authority-bearing content identities and Merkle nodes;
- `ML-DSA-87` for authority-bearing signatures;
- `ML-KEM-1024` for recipient key establishment;
- `KMAC256` for domain-separated key derivation and keyed commitments;
- `AES-256-GCM-SIV` for authenticated payload encryption.

The package also separates semantic content identity, chronology-bearing envelope identity, cryptographic attestation identity, recurrent witness state, and non-authoritative search sidecars. This prevents timestamps or signer rotation from changing the identity of the underlying claim.

This release is built from the complete 5.3.16 corpus, not from a reduced overlay. It retains the entire contract lineage, Duotronic mathematical canon, formal Lean and TLA+ models, authority and security profiles, all schemas, SQL, fixtures, validators, tests, runtime services, migration records, and prior validation evidence. Files that named the retired cryptographic profile are migrated across the full tree; the original 5.3.16 entry-point documents are additionally retained under `history/v1_6_draft_5_3_16_root_surfaces/`.

Use `COMPLETE_CORPUS_CONTENT_MAP_v1_6_draft_5_3_17.json` to verify baseline retention and `MANIFEST_v1_6_draft_5_3_17.json` to verify every current file. A runtime selects behavior from the canonical descriptor and registries; it must not hard-code a contract version or algorithm.

Regenerate the current schema registry with `python3 executable/validators/build_schema_registry_v5317.py`. The older registry-regeneration tests remain in the corpus but are explicitly superseded because applying a predecessor generator to migrated schemas would reproduce neither the predecessor nor the current registry.
