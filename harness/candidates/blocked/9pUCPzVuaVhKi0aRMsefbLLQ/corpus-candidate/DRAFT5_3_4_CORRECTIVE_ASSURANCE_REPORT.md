# Draft 5.3.4 Corrective Assurance Report

## Disposition

Draft 5.3.4 closes the portable host, schema, SQL, and governance defects
identified in the supplied update plan. It remains a corrective development
draft with theorem, promotion, and release authority disabled.

## Corrective evidence

| Boundary | Enforced by | Portable evidence |
|---|---|---|
| Submitted code cannot reach final result | separate OCI mount manifests; no control/result mounts in compile domain | result-channel adversarial tests |
| Final result is trusted | private `0700` directory; exclusive/no-follow `0600` publication; ML-DSA-87 result signature | symlink, hard-link, oversize, canonicalization, signer tests |
| Artifact digest equals compiled bytes | snapshot-before-hash order and post-run tree verification | source/metadata/import mutation tests |
| Historical decisions do not change | monotonic event sequence, snapshot cutoff, event-set root | later backdated-event snapshot stability tests |
| Execution constraints are bound | `EffectiveSandboxInvocation` and governed runtime/image/executable fields | profile, result, and invocation mismatch tests |
| Governance is action-specific | exact scope map, typed targets, validity windows, signed events | wrong-scope, expired authorization, wrong-type tests |
| Release activation cannot self-attest | complete canonical activation payload, governance signature, trust-root validity, and append-only SQL | unsigned, incomplete, mutation, deletion, and pre-activation theorem-gate tests |
| SQL theorem authority preserves independent proof evidence | governance-signed profile, verifier-result signature, outer witness signature, cutoff-visible key/profile activation and exact gate approval | real-key happy chain, tampered result, and missing activation tests |
| Supersession is typed and acyclic | composite foreign keys and SQL cycle/revocation guards | nonexistent, self, type, cycle, revoked replacement tests |
| Lean result is semantic | structural type hashes and programmatic dependency/axiom fields | mismatch, missing declaration, `sorryAx`, forbidden and unsafe cases |
| Corpus version is singular | required version-consistency validation phase | active-file metadata scan |

## Deliberately unavailable release evidence

- strict root Lean build under the declared authoritative toolchain;
- strict TLC execution of every active model;
- real governed OCI-image adversarial integration;
- signed OCI image build attestation;
- signed verifier source-to-binary attestation; and
- external governance signature over the final descriptor and checksum closure.

These are not reported as passed. The portable database contains no release
activation evidence, and the authoritative theorem view is empty.

## Living-contract status

The contract remains permanently not frozen. Future evidence or corrections do
not mutate this archive; they produce signed evidence or a new active revision.
