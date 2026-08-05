# Release Notes — Witness Contract v1.6 Draft 5.3.3

**Status:** complete living corrective draft; permanently not frozen.

## Corrected trust boundary

- Removed request-level compiler paths, hashes, environment, and timestamps.
- Added a governance-signed compiler-profile registry.
- Bound Lake, actual Lean, stdlib, dependency closure, verifier binary, sandbox
  policy, and execution image separately.
- Added immutable source snapshots, before/after/copy hash reconciliation,
  deterministic generated targets, and prebuilt/native artifact rejection.
- Added a no-network, read-only, resource-limited OCI sandbox profile.
- Replaced stdout axiom parsing with canonical structured verifier-result input.
- Added a production request adapter resolving pre-ingested source bundles only.
- Added signed governance authorization, signed v2 key lifecycle, signed v2
  supersession, and signed authority-snapshot database records.
- Added deterministic as-of authority views while retaining current-time views as
  convenience-only interfaces.
- Added ProofAuthority V4 and a real-image integration runner.

## Regression coverage

The portable suite covers statement mismatch, comment-only declarations,
`sorryAx`, attributed axioms, external artifacts, stale `.olean`, native
plugins, malicious project metadata, registry-signature tampering, actual Lean
digest mismatch, unstructured/fake output, deterministic witnesses, signed
lifecycle authorization, revocation, expiry, immutable records, and stable
historical authority snapshots.

## Authority disposition

Portable validation proves corpus closure only. Real theorem authority remains
disabled until a deployment supplies a protected externally anchored governance
configuration and passes the real hermetic Lean integration and applicable
strict checks. The contract is never frozen; future work advances the active
draft while preserving this corpus.
