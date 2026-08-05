# Lean Proof Authority Contract v1.1

**Applies to:** Witness Contract v1.6 Draft 5.3.2  
**Status:** normative development contract; not frozen

## Authority boundary

A Lean compiler witness may report `passed/proved` only when the controlled verifier:

1. resolves an absolute Lake executable configured outside the request;
2. verifies its bytes against an independently configured SHA-256 digest;
3. requires the declared `lean-toolchain` to equal the authorized toolchain;
4. requires the proof artifact to be a regular importable `.lean` module inside the source root with no symlinked Lean sources;
5. generates a comment-free exact target importing that module;
6. checks the named theorem at the exact claimed theorem statement through an `example` declaration;
7. enables fatal warnings in both the generated source and compiler command;
8. requests Lean's compiled axiom dependencies for that declaration;
9. rejects missing axiom output, `sorryAx`, and every axiom outside the configured allowlist;
10. hashes the generated target, source tree, proof artifact, compiler executable, command output, claim, and theorem statement; and
11. signs the complete canonical witness payload with the effective verifier key.

Source regexes may be used for diagnostics but never to establish theorem existence, type equality, or axiom freedom.

## Database promotion

The compiler and proof payloads must each be inserted with a signature binding that:

- is valid canonical JSON;
- hashes to the stored payload digest;
- matches every stored authority field;
- verifies cryptographically under the registered Ed25519 public key; and
- refers to the same verifier principal and key as the gate.

The gate additionally requires the key to be currently valid, active at gate time, within its validity window at compilation/proof/gate time, and not revoked, retired, superseded, or generically superseded.

## Formal limitation

`Duotronic/ProofAuthorityV3.lean` states abstract consequences of these premises. Until strict Lake execution succeeds, those declarations are source artifacts rather than authoritative compiled proof evidence.
