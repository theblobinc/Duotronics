# Release Notes — v1.6 Draft 5.3.6

Draft 5.3.6 is a completed standalone corrective development corpus and remains
permanently not frozen. It does not claim theorem, promotion, or release
authority.

## Corrected in 5.3.6

- The Lean inspector performs actual definitional equality, structural
  expression fingerprinting, and recursive dependency/axiom inspection; a
  Boolean dependency result cannot satisfy the canonical schema.
- One sealed invocation object produces and hashes the exact executed OCI argv,
  including private host paths, tmpfs quotas, resource flags, image and wrapper.
- Policy timeout and source limits flow into the effective limits, verifier
  request, signed result, compiler witness, API result, and semantic identity.
- Boundary records are schema-validated before signing or persistence.
- Requested, emitted, accepted, measured, and derived controls are distinct;
  missing observations are unverified and exactly one governed LSM is required.
- The trusted verifier consumes an exact schema-validated `.olean` handoff
  manifest and verifies its paths, modes, sizes, digests, set, and aggregate.
- Idempotency is durable, bounded, principal-scoped, lease-based, and recoverable
  after a crashed worker rather than process-local memory.
- Compiler artifact, aggregate handoff, inspection, and final publication limits
  are independent.
- A governance-signed trusted-artifact registry closes loader/attestation scope
  for migrations, inspector, image metadata, and dependency manifests.

## Activation blockers retained

Strict Lean, strict TLC, governed-image execution and runtime inspection, two
matching inspector/image build attestations, clean committed-source provenance,
and an external governance signature are absent unless separately supplied and
verified. The portable corpus cannot pass those gates on their behalf.
