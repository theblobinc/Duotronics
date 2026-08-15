# Runtime migration checklist for Contract 5.3.17

The runtime is not 5.3.17 compatible until every P0 item passes. P1 items make subsequent contract releases data-driven rather than code-driven. P2 items implement the newer Duotronic witness and graph capabilities without confusing them with authority.

## P0 - required for correct 5.3.17 operation

| ID | Runtime area | Required update | Acceptance evidence |
| --- | --- | --- | --- |
| P0-01 | Corpus loader | Discover the exact canonical descriptor named by deployment; reject missing, ambiguous, unversioned, or derived manifests. | Boot fails on no manifest, duplicate active descriptors, unknown descriptor version, or wrong corpus root. |
| P0-02 | Corpus closure | Verify every manifest entry with domain-separated SHAKE256-512; remove large-file digest skipping. Stream large files instead. | Byte mutation in any file, including files above 5 MiB, prevents activation. |
| P0-03 | Crypto provider | Add a provider interface for SHAKE256-512, ML-DSA-87, ML-KEM-1024, KMAC256, and AES-256-GCM-SIV. | Startup known-answer, malformed-input, and negative-signature tests pass; unavailable provider fails closed. |
| P0-04 | Key registry | Implement signed, scoped, time-bounded principal, signing-key, KEM-key, and suite registries. | Rotation, expiry, revocation, scope confusion, and downgrade tests pass. |
| P0-05 | Canonicalization | Centralize RFC 8785 canonicalization; reject duplicate keys, floats, ambiguous byte encodings, implicit defaults, and non-normalized text. | Cross-language canonical-byte vectors match exactly. |
| P0-06 | Identity API | Replace one generic digest helper with domain-framed `semantic_content_id`, `envelope_id`, `attestation_id`, `edge_content_id`, and Merkle functions. | Identical semantic bodies remain identical across time/signers; distinct domains never collide in vectors. |
| P0-07 | Evidence models | Remove timestamps and runtime metadata from semantic claim identity. Put chronology and observer data in the envelope. | Repeating the same claim at a later time preserves semantic ID and creates a new envelope ID. |
| P0-08 | Signature path | Sign and verify canonical `SignaturePayload/v1`; do not sign ad hoc JSON dictionaries. | Any field mutation, key-registry mismatch, purpose mismatch, or critical-extension mismatch invalidates verification. |
| P0-09 | Encryption path | Implement per-object content keys, ML-KEM recipient encapsulations, KMAC context binding, AEAD associated data, chunk manifests, and key zeroization. | Wrong recipient, context, envelope, chunk index, tag, or key epoch fails decryption. |
| P0-10 | Database schema | Widen digest/key/signature/ciphertext columns; add algorithm and profile IDs; stop assuming fixed legacy lengths. | ML-DSA-87 signatures and ML-KEM-1024 keys/ciphertexts round-trip without truncation. |
| P0-11 | Meta-object edges | Add normalized `meta_object_edges` storage and indexes on `(source_id, relation_type)` and `(target_id, relation_type)` with a unique edge content ID. | Directional traversal, inverse rules, supersession, and conflict preservation are behaviorally tested. |
| P0-12 | Audit chain | Rebuild event, checkpoint, seal, receipt, anchor, and recovery hashes/signatures under the active profile. | Full publish, rotate, restart, reconcile, recovery, and rollback-resistance tests pass. |
| P0-13 | Cache | Key cache entries by semantic/envelope IDs plus policy and profile; bind cached authority to a verified attestation. | Signer rotation does not duplicate semantic content; stale or wrong-profile authority is rejected. |
| P0-14 | API/MCP | Expose contract version, descriptor ID, crypto profile, supported critical extensions, and authority state in health and evidence responses. | Clients can negotiate read/write support and cannot submit a write under an unsupported profile. |
| P0-15 | Migration | Isolate legacy reads, generate mapping witnesses, re-identify and re-attest selected records, and prevent in-place reinterpretation. | Mixed-version replay proves old records remain immutable and new authority is native 5.3.17. |
| P0-16 | Secrets | Move private signing and decapsulation keys out of JSON/config/database rows into a governed key service or protected provider. | Logs, traces, exceptions, backups, and database dumps contain no private key or shared-secret material. |
| P0-17 | Tests | Replace source-string assertions with behavioral, adversarial, cross-version, and vector tests. | Tests exercise canonical bytes, crypto failure paths, graph semantics, migrations, restarts, and concurrency. |
| P0-18 | Deployment | Pin provider/library versions and binary digests; record container, CPU feature, and provider attestations. | Rebuilt deployment produces the same governed provider identity or fails provenance closure. |

## P1 - contract-version agility

| ID | Runtime area | Required update | Acceptance evidence |
| --- | --- | --- | --- |
| P1-01 | Contract registry | Add a `ContractAdapter` interface selected by descriptor version and capability flags. | Two contract versions can be loaded side by side for replay without conditionals spread across services. |
| P1-02 | Schema registry | Resolve schemas by immutable schema ID and digest; cache compiled validators by registry snapshot. | Adding a noncritical schema requires data/config only; registry mutation invalidates the cache. |
| P1-03 | Algorithm registry | Resolve hash, signature, KEM, KDF, and AEAD implementations from suite objects. | A test-only successor suite can be added without database or evidence-model rewrites. |
| P1-04 | Extension handling | Implement critical/noncritical extension rules and lossless unknown-field preservation. | Unknown critical data fails closed; unknown noncritical data survives replay unchanged. |
| P1-05 | Capability negotiation | Publish read, write, verify, migrate, and decrypt capability separately per contract/profile. | A node may verify an older profile without being permitted to create it. |
| P1-06 | Data migration framework | Make migrations idempotent, resumable, checkpointed, and evidence-emitting. | Crash-and-resume and duplicate-run tests produce one consistent result. |
| P1-07 | Dual-run rollout | Support shadow verification by current and candidate adapters before activation. | Differences produce non-collapsed comparison witnesses and block automatic promotion. |
| P1-08 | Observability | Tag metrics, logs, traces, and audit records with contract/profile/schema IDs. | Operators can isolate failures by version without logging secrets or plaintext. |
| P1-09 | Rollback | Separate software rollback from authority rollback; never make a new native record disappear. | Older software becomes read-only when it cannot understand newer critical data. |
| P1-10 | Release gates | Drive activation from a machine-readable gate registry, not environment booleans. | Authority becomes enabled only from one complete, verified external-gate snapshot. |

## P2 - Duotronic witness and meta-object capability

| ID | Runtime area | Required update | Acceptance evidence |
| --- | --- | --- | --- |
| P2-01 | Object witness | Implement canonical `W_t` generation as a typed summary of base object and local meta-object packet. | Same canonical packet produces the same object witness across nodes. |
| P2-02 | Recurrent witness | Persist versioned `W~_t` with update-rule ID, prior-state ID, decay/regime fields, and replay inputs. | Replaying the same chronicle reproduces the same recurrent witness trajectory. |
| P2-03 | Retrieval sidecar | Store fixed binary search signatures and use Hamming/popcount for first-pass candidate generation. | Sidecar changes cannot change authority; candidates are reranked against canonical objects. |
| P2-04 | Graph inference | Represent derived connections with rule ID, input edge IDs, assumption manifest, verifier witness, and policy. | Graph reachability alone never creates an authoritative relation. |
| P2-05 | Online reinforcement | Keep Hebbian/reinforcement weights branch-local and non-authoritative until governed aggregation. | Model updates cannot mutate canonical edge objects. |
| P2-06 | Trace compression | Add tensor-train or other versioned compression only as a replay sidecar with canonical source-root binding. | Decompression is bounded and source-root verified; loss does not alter authority. |
| P2-07 | Positive-baseline diagnostics | Permit zero-free/tensor state representations for runtime diagnostics and worker calculations. | Conversion boundaries are explicit and standard canonical objects remain interoperable. |
| P2-08 | Merkle batching | Batch high-volume observation attestations into signed roots with inclusion proofs. | Inclusion, exclusion, ordering, odd-leaf, and segment-boundary vectors pass. |

## Current code hotspots

The existing runtime areas most likely to change are:

- `corpus_manager.py`: descriptor discovery, complete streaming closure, version negotiation;
- `evidence.py`: layered IDs, canonical edges, object/recurrent witness separation;
- `db.py` and SQL migrations: variable-length crypto material, registries, normalized edge tables;
- `formal_observers.py`: governed provider/toolchain attestations and deterministic verifier outputs;
- `runtime_kernel.py`: adapter selection, critical extensions, authority gate snapshot;
- `session_ledger.py`: new chain IDs, signatures, encryption context, mixed-version replay;
- `api.py`, `http_mcp.py`, and `mcp_protocol.py`: capability discovery and profile-aware inputs/outputs;
- `tests/`: behavioral conformance, vectors, negative crypto cases, migration, concurrency, replay.

See `RUNTIME_UPDATE_STATUS_5_3_17.md` for the split between completed reference-corpus work and deployment/runtime work that remains external to this release.
