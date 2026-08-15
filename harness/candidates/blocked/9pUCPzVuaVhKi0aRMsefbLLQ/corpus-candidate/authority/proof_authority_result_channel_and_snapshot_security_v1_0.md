# Proof Authority Result-Channel and Snapshot Security v1.0

This profile is normative for Draft 5.3.4. It defines the two-domain mount
boundary, private result publication, snapshot-first processing order, source
filesystem rejection rules, deterministic generated input, trusted result
signature, and post-execution snapshot verification described in Sections 5–8
of the active contract.

The untrusted domain must not receive a path to the verifier request, final
result, signing key, registry, authority database, or governance state. A JSON
object created by submitted code is never a verifier result. The trusted
verifier domain emits only a private canonical inspection. A separate protected
host authority component must sign and publish the final canonical result,
binding the request, sealed snapshot, artifact,
generated module, execution closure, structural type, dependency closure, axiom
closure, exit state, timeout state, and timestamps.

Any uncertainty about mount isolation, ownership, link identity, canonical JSON,
signature authority, snapshot stability, or digest equality is a denial.
