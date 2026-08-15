# Runtime update status for Contract 5.3.17

This file distinguishes code and data delivered in the standalone corpus from work that must still be integrated and proven in the deployed Duotronics runtime. The contract corpus is complete; production authority remains disabled.

## Completed in this corpus

- Complete 5.3.16 baseline retained and full-tree cryptographic naming migration applied.
- SHAKE256-512 streaming commitments and domain-framed identity helpers.
- ML-DSA-87 and ML-KEM-1024 provider adapter using `pqcrypto`.
- KMAC256 derivation using PyCryptodomeX and AES-256-GCM-SIV payload protection using `cryptography`.
- Fail-closed provider availability and parameter-length checks.
- Runtime signature/key wrappers, raw public-key loading, protected private-key envelope, SQL crypto functions, and widened SQL constraints.
- All 141 schemas registered; active signature, public-key, KEM, digest, and ciphertext constraints updated.
- Test and reference fixtures migrated to the new commitment widths and suite identifiers.
- Canonical semantic, envelope, attestation, edge, and corpus-file identity vectors.
- Whole-corpus manifest, content-retention map, schema-registry regeneration, and forbidden-primitive scan.
- 5.3.17 provider/identity tests and migrated retained regression suite.

## Required in the deployed runtime before 5.3.17 writes

1. Wire `executable/runtime/pq_provider.py` or an API-compatible validated HSM/provider into every signing, verification, encapsulation, decapsulation, KDF, and AEAD call site.
2. Install and pin `requirements-pq-runtime.txt`; run provider known-answer and negative tests in the governed production image and attest the exact binaries.
3. Move ML-DSA secret keys and ML-KEM decapsulation keys into the governed key service; the JSON private-key envelope is an interchange format, not a production keystore.
4. Apply idempotent database migrations for 128-character hex commitments, 3,456-character public keys, 6,170-character signatures, ML-KEM material, suite IDs, registry snapshots, and encryption context.
5. Rebuild event, cache, receipt, checkpoint, seal, anchor, and recovery chains under the new suite. Never reinterpret existing records in place.
6. Implement isolated read-only legacy replay and emit mapping witnesses when selected records are re-identified and re-attested.
7. Normalize meta-object edges and add directional/source/target/relation indexes, inverse-rule enforcement, supersession, and conflict-preserving queries.
8. Load contract adapters from the verified descriptor and registry; remove version and algorithm conditionals from services.
9. Add read/write/verify/decrypt/migrate capability negotiation and unknown-critical-extension failure behavior to API and MCP surfaces.
10. Bind semantic IDs, envelope IDs, attestation IDs, policies, registries, profile IDs, and external-gate snapshots through cache and idempotency paths.
11. Implement encrypted persistence, recipient rotation, chunk manifests, recovery, key zeroization, and rollback-resistance drills.
12. Rerun the five Linux integration tests blocked in the portable sandbox: four Unix-socket/peer-credential tests and one process-tree cancellation test.
13. Run strict Lean and TLC, governed hermetic execution, reproducible builds, production key ceremony, mixed-version replay, and all remaining external activation gates.

## Preparation for later contracts

- Keep schemas, algorithms, relation types, extensions, and gates registry-driven.
- Maintain one immutable adapter per contract and support side-by-side read-only replay.
- Separate software rollback from authority rollback; unknown newer critical data forces read-only behavior.
- Dual-run candidate adapters and emit non-collapsed comparison witnesses before activation.
- Preserve semantic identities across signer rotation while creating new envelopes and attestations.
- Treat recurrent state, search signatures, compression, learned weights, and quantum/stochastic discovery as non-authoritative sidecars until deterministic governed verification succeeds.
