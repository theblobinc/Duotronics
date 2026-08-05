# Trusted Lean verifier implementation — Draft 5.3.5

This directory contains the two execution-domain entry points used by the
governed image:

- `compile_lean.py` runs with submitted source, generated input, and a bounded
  handoff mount. It cannot see the verifier request, signing key, governance
  state, or final result directory.
- `verify_lean.py` runs only after compilation. It measures the governed
  executables, invokes the trusted Lean inspector, validates its structural
  environment result, and publishes one private canonical inspection through
  exclusive no-follow I/O. A separate protected host authority component then
  signs and atomically publishes the final verifier result; no container
  receives the final-result directory or result-signing key.

The image has no fixed `ENTRYPOINT`. The host always supplies exactly one
OCI `--entrypoint`: `/opt/witness-authority/bin/compile-lean` for the untrusted
domain or `/opt/witness-authority/bin/verify-lean` for the trusted domain. The
selected wrapper is never appended as an argument to another wrapper.

`formal/draft5_3_5/lean/WitnessAuthority/Verifier.lean` is the Lean environment
inspector source. A deployment must replace the Containerfile digest marker,
reproducibly build the source into `executable/trusted_verifier/build/inspect-lean`,
create a signed build attestation, and place
the exact measurements in the governance-signed compiler registry. The
portable corpus does not contain a production signing key or claim that this
image has been built. The absent build output is deliberate: the Containerfile
fails closed until an externally measured and attested executable is supplied.

The dedicated build target is `lake build witnessAuthorityInspector`; the
two-build protocol is in `INSPECTOR_BUILD_PROTOCOL.md`.

The authoritative integration command is
`python3 executable/formal/run_hermetic_proof_authority_integration.py --json`.
It remains a release gate and fails closed when the governed deployment
configuration is unavailable.
