# Trusted inspector reproducible-build protocol — Draft 5.3.9

The sole active inspector source root is `formal/draft5_3_6/lean`; the sole
target is `witnessAuthorityInspector`. `lakefile.lean`,
`Containerfile.inspector-build`, `Containerfile`,
`build_trusted_inspector.py`, the trusted-artifact registry, and runtime
documentation must all resolve to that exact generation.

Two independent builds must use:

- the pinned `lean-toolchain` and locked dependency state;
- the digest-pinned builder image;
- `HOME=/nonexistent`, `SOURCE_DATE_EPOCH=0`, and the documented locale;
- exactly `lake build witnessAuthorityInspector`;
- only `lean-toolchain`, `lakefile.lean`, and the selected source root as build
  inputs.

Run `python3 executable/formal/build_trusted_inspector.py --json` in the
governed builder. Both output hashes and the complete selected-source tree hash
must match. The runtime image must copy those exact bytes to
`/opt/witness-authority/bin/inspect-lean`; the measured digest must equal the
governance-signed build attestation and compiler profile.

The portable corpus deliberately records the digest-pinned OCI build and
external attestation phases as incomplete. No missing image, builder, or key is
converted into portable authority evidence.
