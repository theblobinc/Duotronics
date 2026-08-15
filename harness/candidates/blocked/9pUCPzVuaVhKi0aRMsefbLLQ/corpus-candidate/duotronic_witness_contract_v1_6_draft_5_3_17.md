# Duotronic Witness Contract v1.6 - Draft 5.3.17

## Status

This is a completed, standalone development-contract release. It is permanently not frozen and non-authoritative until every external activation gate succeeds. Theorem, promotion, and operational release authority default to disabled.

## 1. Non-collapse authority rule

A result becomes authoritative only when its semantic content, envelope, attestations, dependencies, policy, chronology, and applicable external-gate evidence are independently valid. Search scores, recurrent state, model output, similarity, stochastic discovery, and portable regression results are evidence only. They never promote a claim by themselves.

Conflicting valid claims remain distinct typed objects connected by explicit conflict edges. The runtime must not silently merge, overwrite, or average them into one asserted truth.

## 2. Canonical representation

Authority-bearing JSON uses RFC 8785 JSON Canonicalization Scheme bytes. Authority objects prohibit binary floating-point values, duplicate keys, non-finite numbers, ambiguous Unicode, untagged byte strings, and implicit defaults. Quantities that require exact decimals use canonical decimal strings. Bytes use unpadded base64url.

Every digest operation uses a registered domain label and length-prefixed fields. Concatenating unframed values is forbidden.

## 3. Three-layer identity

The contract separates identity into three layers:

1. `semantic_content_id` identifies the canonical semantic body. It excludes creation time, observer, host, signer, transport, and storage location unless one of those is the explicit subject of the claim.
2. `envelope_id` identifies the semantic content in a corpus, policy, observer, dependency, and chronology context.
3. `attestation_id` identifies a cryptographic statement over an envelope, including suite, key, signature, and registry binding.

All three use `SHAKE256-512` with distinct domain labels. The output format is `duoid:shake256-512:<base64url-64-bytes>`.

## 4. Post-quantum cryptographic profile

Authority-bearing signatures use `ML-DSA-87`. Recipient key establishment uses `ML-KEM-1024`. Payload protection uses `AES-256-GCM-SIV` with a content-encryption key derived by `KMAC256` from the KEM shared secret and the complete envelope context. Authority identities and Merkle nodes use `SHAKE256-512`.

Implementations must use a validated provider, perform algorithm and parameter self-tests at boot, keep secret keys outside witness objects, zeroize transient shared secrets where supported, and fail closed when the required provider is unavailable. A placeholder or simulated signature is never valid authority evidence.

## 5. Signed payload

The signature input is the canonical `SignaturePayload/v1` object containing:

- contract version and cryptographic profile;
- envelope ID and semantic content ID;
- signer principal ID and key ID;
- signer registry ID and policy ID;
- purpose and authority scope;
- creation time, validity interval, and nonce;
- dependency-root ID and external-gate snapshot ID.

The signature envelope is validated against `schemas/signature_envelope_v1.schema.json`. Signatures are verified before interpreting authority status.

## 6. Encrypted payload

Encryption is optional for public evidence and mandatory for governed confidential evidence. Each encrypted object uses a fresh content-encryption key. Every recipient receives an `ML-KEM-1024` encapsulation of key material. The AEAD associated data is the canonical encryption context and binds contract version, profile, semantic content ID, envelope ID, content type, recipients, policy, and chunk position.

Nonce reuse under one content-encryption key is forbidden even though the selected AEAD is misuse resistant. Streaming objects use independently authenticated chunks and a signed final chunk manifest.

## 7. Meta-object connections

Connections are first-class `MetaObjectEdge/v1` objects. An edge canonically binds:

- source semantic content ID;
- relation type from a versioned relation registry;
- target semantic content ID;
- optional context semantic content ID;
- assumption-manifest ID;
- policy ID;
- validity interval and supersession state.

The `edge_content_id` excludes observation time and storage metadata. An `edge_envelope_id` adds chronology, observer, corpus, and policy evaluation. Relation types are directional unless the registry declares a symmetric inverse rule.

Graph reachability or similarity is not proof. Every authoritative derived connection must name the rule, input edge IDs, verifier witness, and policy that justified it.

## 8. Duotronic witness dynamics

The object witness `W_t` is a canonical, compact summary of a realized chronicle packet. The recurrent witness state `W~_t` carries family persistence, callback residue, contradiction pressure, coherence drift, regime evidence, and retrieval keys through an explicit update rule.

`W_t` and `W~_t` are separate from cryptographic attestations. Recurrent state can propose candidates and influence branch-local ranking, but cannot alter semantic IDs or satisfy authority gates. Binary signatures used for Hamming-distance retrieval are sidecars only and must be reranked against canonical objects.

## 9. Merkle batching

High-volume observations may be grouped in ordered Merkle segments using domain-separated `SHAKE256-512` leaves and nodes. A segment root may receive one `ML-DSA-87` checkpoint signature, with inclusion proofs for members. Individual signatures remain required where policy demands them, including governance changes, release activation, theorem promotion, key-registry changes, and recovery authorization.

## 10. Key and suite agility

Algorithms are selected by registry ID, not code constants. Every signed or encrypted object carries its exact suite ID. Registries are themselves signed, versioned, scoped, time-bounded, and hash-linked. Removal of a suite never reinterprets historical records under another suite.

Unknown critical extensions fail closed. Unknown noncritical extensions are preserved byte-for-byte for replay. Downgrade from the active profile is forbidden unless a separately signed migration policy explicitly permits read-only legacy verification.

## 11. Discovery and deterministic verification

Quantum, stochastic, heuristic, analog, neural, and approximate producers emit candidates plus `DiscoveryRunWitness` and `AssumptionManifest` objects. They cannot emit authoritative results. A deterministic verifier in a governed execution domain must validate a compact certificate and emit `DeterministicCertificateVerificationWitness` before promotion is considered.

## 12. Corpus and runtime loading

The runtime loads `CANONICAL_CORPUS_v1_6_draft_5_3_17.json`, verifies the complete manifest, resolves all registries and schemas, runs cryptographic known-answer tests, checks database migration state, and only then accepts writes. A missing or unrecognized descriptor is fatal; deriving an unversioned corpus is prohibited.

## 13. Migration

Legacy authority records remain readable only in an isolated replay namespace. They are never silently rewritten or treated as native 5.3.17 authority. Migration creates new semantic identities, new envelopes, and new post-quantum attestations, and records a typed mapping witness from each legacy object.

## 14. External activation gates

Authority remains disabled until all of the following independently pass:

1. strict Lean verification;
2. strict TLC model checking;
3. governed hermetic image execution;
4. signed image build attestation;
5. signed verifier build attestation;
6. reproducible trusted-inspector build;
7. clean committed-source provenance;
8. external governance authorization;
9. validated post-quantum provider attestation;
10. production key ceremony and registry activation;
11. encrypted persistence and recovery drill;
12. mixed-version replay and rollback-resistance drill.

Portable validation cannot satisfy an external gate.

## 15. Cache integrity and replay

Cached envelopes canonically bind principal, idempotency slot, request, claim, policy, source, proof artifact, compiler profile, compiler witness, result, signer, cryptographic suite, and chronology before historical rotation classification. Cache identities and registry lineage use domain-framed `SHAKE256-512`; cache attestations use `ML-DSA-87`. A global durable publisher-domain event-ID index survives sealing, successor provisioning, restart, timeout reconciliation, and key rotation. Replay of a consumed recovery authorization fails closed.

## 16. Service authentication

Proof-service to publisher and publisher to anchor mutations require both operating-system peer-credential allowlisting and an `ML-DSA-87` signature over the canonical request. The request binds operation, principal, payload commitment, deadline, request ID, nonce, target service, exact socket identity, suite ID, and signer registry. Root is not implicitly trusted. World-writable sockets and ambiguous peer identity fail closed.

## 17. Audit-key lifecycle

Every record, receipt, checkpoint, seal, recovery artifact, and anchor state resolves the applicable governance-signed registry snapshot and recomputes signer status, validity, revocation, principal, scope, suite, and rotation lineage at the artifact timestamp. Rotation cycles fail. Record, receipt, checkpoint/recovery, anchor, governance, and release scopes remain distinct. Private and shared-secret key material never enters witness objects.

## 18. Anchor and segment semantics

Inside a segment, an anchor accepts only an exact idempotent no-op or `sequence = previous + 1`. Namespace, epoch, segment, registry commitments, transition authorization, and predecessor binding are immutable. Every new state binds the previous anchor-state `SHAKE256-512` commitment. A successor requires a governance-signed transition, verified sealed checkpoint, actual terminal record, current anchor, and valid signer lifecycle. The canonical terminal-record commitment equals both checkpoint and anchor tails.

The file-backed anchor is development-only and cannot enable authority because its storage owner may restore an older valid prefix. Activation requires an independent monotonic trust domain. Normal event capacity reserves a terminal-seal slot and byte budget.

## 19. Recovery and durability

Recovery authorizations require `created_at <= now < expires_at`, a short maximum lifetime, exact before-state and file identities, suite and registry bindings, and one-time durable consumption. All writes use complete-write loops. Logs and ledgers are size-checked before allocation and read in bounded chunks. Partial writes, storage exhaustion, temporary cleanup, crash restart, and rollback detection are governed and tested.

## 20. Production execution topology

The production integration preserves process separation between proof execution, publication, and anchoring. Both proof loaders run only after privilege drop. A real event must be durably published, its signature and receipt verified, the anchor advanced, restart replay reconciled as an exact duplicate, and unrelated principals denied. ML-DSA private-key operations and ML-KEM decapsulation occur only in their assigned trust domains.

## 21. Retained mathematical and formal corpus

All prior Duotronic mathematics, recurrence laws, witness mappings, polygon-family calculus, language and canon contracts, observer semantics, Lean developments, TLA+ models, runtime profiles, and research notes remain part of this release. The cryptographic migration changes commitment, authentication, key-establishment, and encryption mechanisms; it does not discard or silently redefine the mathematical witness content. Where older text named a retired cryptographic field, 5.3.17 uses the corresponding suite-bound field and records compatibility through explicit migration witnesses.

## 22. Whole-corpus conformance

A conforming 5.3.17 distribution contains the complete predecessor corpus plus the 5.3.17 surfaces. It publishes a path-bound manifest for every file, a schema registry, suite and relation registries, a baseline-retention content map, portable identity vectors, and an authority-gate status record. A reduced overlay, missing historical mathematics, omitted runtime implementation, or unregistered schema is not a complete 5.3.17 corpus.
