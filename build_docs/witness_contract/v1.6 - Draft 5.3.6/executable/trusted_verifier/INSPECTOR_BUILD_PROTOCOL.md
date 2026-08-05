# Trusted inspector reproducible-build protocol — Draft 5.3.5

The authoritative Lake target is `witnessAuthorityInspector`. Two independent
builds must use the pinned `lean-toolchain`, the same locked dependency state,
an approved digest-pinned build image, `SOURCE_DATE_EPOCH=0`, and the exact
command `lake build witnessAuthorityInspector`.

Run `python3 executable/formal/build_trusted_inspector.py --json` in the governed
builder. Both output hashes must match. The final runtime image must copy those
exact bytes to `/opt/witness-authority/bin/inspect-lean`; its measured digest
must equal the signed `build_attestation/v2` and compiler profile. The portable
corpus records this as incomplete because the governed image and external
attestation key are intentionally absent.
