# Release Notes — Duotronic Witness Contract v1.6 Draft 5.3.4

**Revision class:** corrective security, determinism, and authority binding  
**Status:** corrective development draft; theorem and promotion authority disabled  
**Freeze:** permanently not frozen

## Corrected

- Split submitted Lean compilation from trusted result production. The
  untrusted domain has no request, result, signing-key, registry, database, or
  governance mount.
- Added private exclusive atomic result publication and authorized Ed25519
  verifier-result signatures.
- Reordered proof processing so all artifact and metadata hashes derive from a
  sealed immutable snapshot.
- Added content-addressed snapshot IDs, normalized tree digests, hard-link and
  special-node rejection, copy-race detection, and post-execution revalidation.
- Added complete verifier, Lean, Lake, stdlib, dependency, image, OCI runtime,
  and effective sandbox invocation bindings.
- Added monotonic signed authority-event sequences, ledger high-water snapshots,
  event-set roots, and explicit backdated correction policy.
- Added exact governance action scopes and authorization validity intervals.
- Made release activation governance-signed and append-only, and made the SQL
  theorem gate independently verify the compiler profile, verifier-result
  signature, ledger-cutoff lifecycle state, and exact approval event.
- Added typed, acyclic supersession with existing-record and nonrevoked
  replacement requirements.
- Added structural Lean type comparison, dependency closure, axiom closure,
  `sorryAx`, forbidden-axiom, and unsafe-declaration fields.
- Corrected package, lockfile, OpenAPI, schema registry, manifest, and active
  version metadata to Draft 5.3.4.

## Added

- `lean_compiler_witness/v3`
- `wc_lean_verifier_result/v2`
- `governed_compiler_registry/v2`
- `authority_snapshot/v2`
- `governance_event/v1`
- `authority_supersession/v3`
- `EffectiveSandboxInvocation/v1`
- source/build attestation schema
- ProofAuthority V5
- trusted compile and verifier entry points
- 5.3.3→5.3.4 SQL migration and runbook
- result-channel, snapshot-race, trust-root, event-ledger, backdating,
  supersession, and version-consistency regression coverage

## Authority disposition

The portable corpus deliberately contains no release-activation row. Strict
Lean, strict TLC, real governed-image integration, image and verifier build
attestations, and an external governance signature remain activation evidence.
Their absence is reported without promoting mocks or portable tests to
authority.

All prior source packages remain byte-for-byte preserved.
