# Trusted verifier source profile

`WitnessAuthority/Verifier.lean` is the environment-inspection core required in
the approved verifier image. It resolves the compiled declaration, compares its
elaborated type, collects transitive axioms with Lean’s environment API, and
performs exact axiom allowlisting.

The production image entrypoint must additionally parse the canonical request,
build submitted modules into a fresh output directory, attest the image/toolchain
closure, call this core, and atomically write one canonical structured result.
The entrypoint and this module are covered by `verifier_binary_shake256_512` and the
execution-image digest. Neither ordinary Lean output nor a source-provided macro
is accepted as a substitute.

This portable corpus does not claim that the module compiled here; that claim is
reserved for the real hermetic integration result.
