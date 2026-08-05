# Proof-authority service boundary — Draft 5.3.9

`proof_check_service.py` is the authenticated synchronous request adapter for
the proof-check operation. The caller body does not contain `subject_id`.
Verified OAuth2/mTLS middleware supplies `witness.authenticated_principal_id`
to the WSGI environment; a missing or malformed principal is rejected before
policy resolution, cache access, or proof execution. The verified principal is
bound into policy resolution, idempotency scope, verifier request, signed
verifier result, compiler witness, cache envelope, and outer service result.

Production configuration lives outside the corpus under a protected
`/etc/witness-authority` root. It contains governance trust anchors, signed
compiler and policy registries, witness/result/cache signing keys, pinned OCI
runtime, measured runtime-version identity, immutable seccomp policy, explicit
non-root UID/GID, artifact-store root, and bounded idempotency settings. None
may be supplied by an API request.

## OCI and measured control evidence

The OCI adapter derives exact argv from `EffectiveSandboxInvocation/v5`.
Ephemeral host paths remain in the signed invocation and execution-evidence
identity, but are excluded from `semantic_witness_content_id`. The control
states are intentionally distinct:

1. `requested_controls` — policy requires the control;
2. `emitted_controls` — exact OCI argv encodes it;
3. `accepted_controls` — the running domain supplies measured acceptance;
4. `applied_controls` — measured application is reported;
5. `measured_controls` — a governed observation passed;
6. `derived_controls` — a signed host-side topology derivation passed.

Every requested control requires exactly one governed measurement class.
`explicit_entrypoint` is measured from the executing command identity.
`environment_allowlist` uses `--unsetenv-all`, literal values, separately
declared runtime-created keys, and a complete comparison of the actual process
environment key set. Any undeclared key fails the authority path.

Compilation and trusted inspection each produce a separate
`domain_execution_evidence/v1` record from the trusted launcher and OCI
runtime inspection layer. Each record binds its invocation digest, exact argv,
mounts, runtime identity, requested/emitted/accepted/applied/measured controls,
resource limits, request-budget observations, return state, and handoff state.
The untrusted compiler never attests to its own confinement.

Both domains share one monotonic request deadline. Only the remaining budget is
passed to each stage. Writable request directories are created for the keep-ID
service identity. After compilation, the host verifies ownership, rejects
links and special files, fsyncs the handoff, and seals files `0440` and
directories `0550` before the trusted domain mounts it read-only.

## Idempotency cache trust model

SQLite rows are untrusted storage, never authority records. Completed entries
contain an Ed25519-signed `idempotency_cache_envelope/v1`. Every hit:

- re-resolves the current policy and source-bundle scope;
- verifies the envelope signature and `signed_payload_sha256`;
- verifies the compiler-witness signature and authorized signer identity;
- checks request, principal, claim, theorem, profile, policy, source bundle,
  artifact path, idempotency key, and request hash bindings;
- requires the outer status to equal the signed witness result.

The database, parent directory, WAL, and SHM identities, ownership, and modes
are checked through retained directory-relative identity. Exact SQLite schema
version, object set, layout, and `quick_check` must pass. Cached JSON must be
canonical and duplicate-free. Every connection is explicitly closed.
Completed, in-flight, per-principal, total-row, lease-expiry, and database-byte
bounds are enforced at admission and completion, with a
`(state, lease_expires_at)` cleanup index. Active execution renews its lease;
only the live exact owner can renew or publish.

Production cache envelopes use a distinct Ed25519 key, principal, cache-only
authorization scope, rotation record, and governance-signed verification
registry. Reuse of the compiler-witness key or identity is rejected.

## Portability and authority status

The portable runtime supports Python 3.12 and 3.13. Regression counts come
from `unittest.TestResult`, while warning detection is independent of verbose
output parsing. Both normal and `python -X dev -W error` executions are
required to pass without skips or warning lines.

This corpus contains no production private key, external governance trust
anchor, built OCI image attestation, or completed external release evidence.
Theorem, promotion, and release authority therefore remain disabled. The
lifecycle is permanently not frozen.
