# Trusted Lean verifier implementation — Draft 5.3.4

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

`formal/draft5_3_4/lean/WitnessAuthority/Verifier.lean` is the Lean environment
inspector source. A deployment must replace the Containerfile digest marker,
reproducibly build the source into `executable/trusted_verifier/build/inspect-lean`,
create a signed build attestation, and place
the exact measurements in the governance-signed compiler registry. The
portable corpus does not contain a production signing key or claim that this
image has been built. The absent build output is deliberate: the Containerfile
fails closed until an externally measured and attested executable is supplied.

The authoritative integration command is
`python3 executable/formal/run_hermetic_proof_authority_integration.py --json`.
It remains a release gate and fails closed when the governed deployment
configuration is unavailable.
