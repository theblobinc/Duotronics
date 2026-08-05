# Lean trusted-inspector source — Draft 5.3.4

`WitnessAuthority/Verifier.lean` implements structural theorem-type comparison
with `isDefEq`, programmatic axiom-closure collection with `collectAxioms`,
direct dependency collection, `sorryAx` rejection, forbidden-axiom filtering,
and unsafe-declaration rejection.

This source is intended to be compiled into
`/opt/witness-authority/bin/inspect-lean` by the governed image build. Its
executable digest and source-to-binary attestation must be inserted into the
signed compiler registry before the profile can be activated. Absence of that
attestation leaves theorem authority disabled.
