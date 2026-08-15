# Post-Quantum Cryptographic Profile v1.0

## Suite identifier

`duotronic-pq1-shake256-512-mldsa87-mlkem1024-kmac256-aes256gcmsiv`

## Required primitives

| Purpose | Primitive | Governing reference | Contract rule |
| --- | --- | --- | --- |
| Content IDs, Merkle leaves/nodes, corpus closure | SHAKE256 with 64-byte output | FIPS 202 | Unique domain label for every object class and tree position |
| Authority signatures | ML-DSA-87 | FIPS 204 | Full parameter set; no pre-hash substitution outside the standard mode |
| Recipient key establishment | ML-KEM-1024 | FIPS 203 | Ciphertext and shared-secret validation must fail closed |
| Key derivation and keyed commitments | KMAC256 | SP 800-185 | Customization string binds suite, purpose, envelope, recipient, and epoch |
| Authenticated encryption | AES-256-GCM-SIV | RFC 8452 | Fresh 256-bit content key per object; canonical associated data |

The word post-quantum describes the standardized algorithm design and security target, not a timeless guarantee. The registry supports future suite replacement without changing object semantics.

## Domain framing

Each authority digest is computed as:

`SHAKE256(label || field_count || each(uint64_be(length) || bytes), 64)`

Labels are ASCII and include a trailing version, for example:

- `DUOTRONIC/SEMANTIC-CONTENT/v1`
- `DUOTRONIC/WITNESS-ENVELOPE/v1`
- `DUOTRONIC/ATTESTATION/v1`
- `DUOTRONIC/META-EDGE/v1`
- `DUOTRONIC/MERKLE-LEAF/v1`
- `DUOTRONIC/MERKLE-NODE/v1`
- `DUOTRONIC/CORPUS-FILE/v1`

## Key identifiers

A public key ID is the authority digest of the canonical object `{algorithm, parameter_set, public_key_bytes}` under `DUOTRONIC/PUBLIC-KEY/v1`. Principal identity and key identity are never conflated.

## KEM and encryption construction

For every object, the producer samples a fresh 32-byte content-key seed. The payload key is derived with KMAC256 from that seed and the canonical encryption context. For each recipient, ML-KEM encapsulation yields a shared secret; KMAC256 derives a key-wrap key bound to recipient key ID, envelope ID, suite ID, and key epoch. The content-key seed is wrapped with AES-256-GCM-SIV. Payload chunks are encrypted with independently derived keys and nonces bound to their exact index and total count.

## Provider requirements

The production provider must:

- expose exact algorithm identifiers and parameter sets;
- reject malformed public keys, ciphertexts, and signatures;
- pass startup known-answer and negative tests;
- avoid secret-dependent branching where the implementation claims constant-time behavior;
- provide provenance, version, build options, and binary digest;
- support governed key isolation or an external key service;
- never fall back to a weaker algorithm.

The portable corpus does not ship secret keys and does not emulate authority signatures.
