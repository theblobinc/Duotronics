# Lean trusted-inspector source — Draft 5.3.6

`WitnessAuthority.Verifier` implements structural declaration inspection,
axiom-closure collection, `sorryAx` rejection, forbidden-axiom filtering, and
unsafe-dependency rejection through Lean APIs.

`WitnessAuthority.InspectorMain` is the dedicated executable root with a stable
CLI. It loads the compiled generated binding module through Lean's governed
module search path, resolves `WitnessAuthorityGenerated.BoundClaim` and the
submitted theorem in the same environment, and emits structured type,
dependency, axiom, `sorryAx`, and safety data. It is built by the
`witnessAuthorityInspector` Lake target. The portable corpus validates the
source and target contract statically; authority activation still requires a
strict build, two reproducible governed builds, matching attested binary hash,
and successful real-image inspection. Until those external gates pass, theorem
authority remains disabled.
