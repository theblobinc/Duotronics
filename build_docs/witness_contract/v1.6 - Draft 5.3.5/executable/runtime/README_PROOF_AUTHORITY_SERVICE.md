# Proof-authority service boundary — Draft 5.3.5

`proof_check_service.py` is the canonical request adapter for the proof-check
operation. It synchronously resolves the authenticated subject, immutable
policy decision, pre-ingested source bundle, and governed compiler profile
before OCI execution. The policy identifier and canonical record hash are
included in the verifier request, signed verifier result, compiler witness, and
deterministic witness identity.

Production configuration lives outside the corpus under a protected
`/etc/witness-authority` root. It contains the governance trust anchor,
governance-signed compiler and policy registries, verifier signing key, pinned
OCI runtime, measured runtime-version identity, immutable seccomp policy,
explicit non-root UID/GID, and artifact-store root. None may be supplied by an
API request.

The OCI adapter derives argv from `EffectiveSandboxInvocation/v2`. It uses an
explicit `--entrypoint` and `--workdir`, maps every required control to a
runtime option, and distinguishes requested, applied, and in-container verified
controls. The untrusted domain has no control or inspection mount; the trusted
domain has a private inspection mount but never the final signed-result store.

The supplied runtime fails closed if the protected configuration, registry
signature, OCI runtime digest, compiler profile, source snapshot, structured
verifier result, or authority signing operation cannot be validated. The corpus
does not contain a production private key or external governance trust anchor.
