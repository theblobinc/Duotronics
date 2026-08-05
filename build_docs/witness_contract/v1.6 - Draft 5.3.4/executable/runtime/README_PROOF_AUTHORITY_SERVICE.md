# Proof-authority service boundary — Draft 5.3.3

`proof_check_service.py` is the canonical request adapter for the proof-check
operation. It resolves only pre-ingested source-bundle identifiers and forwards
only a governed `compiler_profile_id` to `ProofAuthorityService`.

Production configuration lives outside the corpus under a protected
`/etc/witness-authority` root. It contains the governance trust anchor,
governance-signed compiler registry, verifier signing key, pinned OCI runtime,
and artifact-store root. None of those values may be supplied by an API request.

The supplied runtime fails closed if the protected configuration, registry
signature, OCI runtime digest, compiler profile, source snapshot, structured
verifier result, or authority signing operation cannot be validated. The corpus
does not contain a production private key or external governance trust anchor.
