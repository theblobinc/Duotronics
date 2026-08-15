# Duotronic Witness Contract v1.6 — Draft 5.3.4

**Author:** Hugh Armstrong, TBI Contracting Inc  
**Date:** July 31, 2026  
**Status:** corrective development draft  
**Theorem authority:** disabled  
**Promotion authority:** disabled  
**Release authority:** false  
**Freeze status:** permanently not frozen

## 1. Scope and precedence

Draft 5.3.4 carries the complete v1.6 corpus forward and corrects the remaining
proof-authority boundaries identified in Draft 5.3.3. It preserves all earlier
evidence-language, replay, non-collapse, positive-baseline, bijective
mathematics, governance, and historical material. Its active delta governs
result-channel separation, snapshot-first identity, immutable ledger-cutoff
replay, execution-closure measurement, action-scoped governance, typed
supersession, structural Lean inspection, and fail-closed release evidence.

`CANONICAL_CORPUS_v1_6_draft_5_3_4.json` is the sole active root selector.
Earlier descriptors are replay evidence and cannot override it.

## 2. Living-contract policy

This contract is never frozen. A completed draft is an internally coherent,
validated revision, not the end of revision. Portable corpus conformance,
deployment technical eligibility, theorem activation, external release
authorization, and continuing revision remain distinct states.

Passing portable tests does not activate theorem authority. Missing real-image,
formal, attestation, or external-governance evidence leaves authority disabled
without invalidating the draft as a research and implementation corpus.

## 3. Non-collapse of evidence and authority

A claim, proof artifact, compilation, structured inspection, compiler witness,
proof witness, policy decision, lifecycle event, authority snapshot, promotion
gate, and release signature are distinct records. No object self-certifies an
object on which its authority depends.

Computation is not theorem; policy approval is not mathematical truth; a signed
result is not accepted unless its signer and execution closure are governed; a
package checksum is internal integrity evidence, not an external trust root;
and an effective time is not a complete historical identity without a ledger
cutoff.

## 4. Request boundary

A proof-check client may supply only claim content, theorem statement and name,
an ingested source-bundle identifier, a normalized bundle-relative `.lean`
artifact path, a policy reference, and a governed compiler-profile identifier.

The client cannot supply executable paths or digests, OCI runtime or image
identity, environment, timestamps, verifier conclusions, axiom results,
signatures, lifecycle events, snapshots, gates, or release evidence. Absolute
paths, `..`, backslashes, NUL characters, symlink substitution, and artifacts
outside the bundle are rejected.

## 5. Snapshot-first proof identity

The authority service performs these steps in order:

1. validate the submitted locator without treating its bytes as authoritative;
2. copy the accepted source tree into a new private snapshot;
3. reject symlinks, hard links, devices, sockets, FIFOs, prebuilt Lean output,
   native objects/plugins, executable files, and files that change while read;
4. re-read source identities to detect changes to already copied files;
5. seal files to `0444` and directories to `0555`;
6. calculate a normalized ordered tree digest from the sealed copy;
7. derive artifact, `lakefile.lean`, `lake-manifest.json`, `lean-toolchain`, and
   imported-file identities only from the sealed copy;
8. create a separately sealed deterministic binding module;
9. construct the verifier request only from snapshot-, claim-, and
   generated-input-derived values;
10. execute against a read-only snapshot mount;
11. re-verify the sealed tree after execution; and
12. require the trusted result to bind the same request and execution closure.

The mutable caller path is not consulted for proof identity after sealing. The
snapshot identifier is content addressed as `shake256_512:<tree digest>`.

## 6. Deterministic binding module

The generated module is minimal:

```lean
import Submitted.Proof.Module
set_option autoImplicit false
set_option warningAsError true
example : (ExpectedType) := FullyQualified.theoremName
```

Its deterministic path is
`WitnessAuthorityGenerated/Check_<32 lowercase hex>.lean`. The generated root
and directory are `0555`; the module is `0444`. Submitted input cannot create or
modify files there.

## 7. Two-domain verification architecture

The untrusted compilation domain receives only the sealed source, sealed
generated module, and a bounded compiler-artifact handoff. It receives no
verifier request, final result mount, signing key, registry, authority database,
governance key, host configuration, home, host cache, network, or container
socket. Submitted Lean therefore has no filesystem path to the final result.

The trusted verifier domain reads the sealed inputs, bounded handoff, canonical
request, and effective sandbox invocation. It invokes a governed Lean inspector
against the compiled environment, measures approved executables, and constructs
a private canonical inspection. A separate protected host authority component
verifies that inspection, signs the canonical verifier result with the governed
verifier-result key, and atomically publishes it. No container domain receives
the final signed-result mount or signing key.

## 8. Result publication

The final directory is owned by the authority-service UID at mode `0700` and is
never mounted into either container domain. Publication requires a regular `0600`
file, expected owner, link count one, strict size bound, canonical UTF-8 JSON,
duplicate-key rejection, exclusive `O_NOFOLLOW` creation, file `fsync`, atomic
no-replace publication, and parent-directory `fsync`.

A pre-existing path, symlink, hard link, oversized output, noncanonical JSON,
invalid UTF-8, race, wrong owner, wrong mode, or changed inode fails closed. The
host accepts no result lacking a valid ML-DSA-87 signature from the result key
governed by the selected profile.

## 9. Governed execution closure

`governed_compiler_registry/v2` independently binds:

```text
verifier_executable_shake256_512
lean_executable_shake256_512
lake_executable_shake256_512
oci_runtime_shake256_512 and oci_runtime_version
oci_image_digest
lean_stdlib_tree_shake256_512
dependency_closure_shake256_512
verifier_source_revision and verifier_build_attestation_id
sandbox_policy_shake256_512
verifier_result_signer_key_id and public key
```

The service measures these components at startup and before authority execution
where practical. A mismatch makes the profile inactive.

## 10. Effective sandbox invocation

The sandbox-policy hash is not treated as proof that controls ran. The runtime
constructs and hashes a canonical `EffectiveSandboxInvocation` containing the
actual runtime, image, entrypoint, arguments, UID/GID, network mode, read-only
root, capability drop, security options, seccomp/AppArmor/SELinux references,
user namespace, PID/memory/CPU/file/open-file/time limits, environment
allowlist, mount manifest, and working directory.

The trusted result and compiler witness bind that invocation digest, OCI runtime
digest, and version. Minimum controls are no network, read-only root, all
capabilities dropped, no-new-privileges, fixed non-root identity, bounded
resources, minimal environment, and read-only source inputs.

## 11. Structural Lean inspection

Source regexes, comments, declaration-name searches, pretty printing, and
ordinary stdout have no proof authority. The governed Lean inspector resolves
the compiled declaration, elaborates the expected type in the same environment,
compares expressions using versioned definitional equality
`lean_isDefEq_reducibility_regular/v1`, records expected and actual expression
hashes, collects direct dependencies and a transitive root, collects the axiom
closure through Lean APIs, and rejects `sorryAx`, undeclared or forbidden
axioms, unsafe declarations, unresolved declarations, and forbidden native or
foreign dependencies.

The selected policy explicitly governs `propext`, quotient soundness,
classical choice, unsafe definitions, opacity, and foreign/native code.

## 12. Compiler witness v3

A `lean_compiler_witness/v3` binds the submitted locator for audit, immutable
snapshot ID and tree hash, normalized artifact path and hash, Lakefile,
manifest and toolchain hashes, generated module and request hashes, complete
execution closure, signed verifier result, structural type hashes, dependency
and axiom identities, authority snapshot and ledger cutoff, deterministic
semantic content ID, server time, and final witness signature.

The semantic identity excludes execution timestamps and unique run metadata.
Identical semantic inputs must produce stable snapshot, artifact, generated
input, type, axiom, sandbox, and witness-content identities.

## 13. Trust-root loading

Production configuration is loaded relative to a trusted directory descriptor.
Absolute paths and traversal are rejected unless an explicit deployment policy
defines an exception. The root, referenced directories, and files must have the
expected owner and must not be group- or world-writable. Files must be regular,
single-link where feasible, non-symlink objects opened with `openat` and
`O_NOFOLLOW`. Hashing occurs only after the verified descriptor is open.

These rules cover configuration, compiler and verifier registries, keys, OCI
runtime, sandbox and governance policy, migrations, verifier executable, image
metadata, and dependency manifests.

## 14. Signed authority-event ledger

Every authority-relevant action is an append-only `governance_event/v1`
assigned the next immutable sequence. Exact action scopes exist for verifier-key
activation/retirement/revocation, compiler-profile activation/revocation,
promotion approval/withdrawal, record supersession, snapshot creation or
supersession, and backdated-event authorization.

The signed event binds sequence, type, scope, typed target, effective and
recorded time, reason, policy, authorization, signer, correction evidence,
payload hash, and signature. Authorization checks enforce principal, exact
action scope, target type and ID, policy version, and half-open validity window.
Current status is derived from events; direct unsigned status mutation is not
authority.

## 15. Ledger-bound historical snapshots

An `authority_snapshot/v2` binds:

```text
snapshot_id
as_of_effective_time
ledger_high_water_sequence
event_set_root_shake256_512
authority_policy_version and snapshot_query_version
created_at and created_by_principal
authorization_witness_id
supersession fields
snapshot signature
```

Replay queries apply both `effective_at <= as_of_effective_time` and
`authority_event_sequence <= ledger_high_water_sequence`. The event-set root is
recomputed over ordered event sequence and payload hashes through the cutoff.
A later event, including one with an earlier effective time, may affect a new
snapshot but cannot alter an existing signed snapshot.

Backdated events require a correction reason, separate action-specific
authorization, affected snapshot IDs, correction mode, and signed witness. They
never silently rewrite history.

## 16. Typed supersession

A supersession is valid only when both record IDs exist under the declared
type, differ, form no cycle, use a nonrevoked replacement, and carry an exact
`authority_record_supersede` event valid at the effective time. Original
records remain append-only.

## 17. Release and theorem gates

Draft 5.3.4 gates cover result isolation, snapshot identity, historical
immutability, execution closure, real governed-image integration, governance
integrity, strict Lean and TLC, corpus consistency, and external authorization.

The portable database contains no release-activation record. Authoritative
theorem views therefore return no rows and theorem-gate insertion fails until
all external evidence is validly signed. A release-activation record is itself
canonical, hash-bound, ML-DSA-87-signed by a valid governance trust root, and
append-only; direct Boolean insertion cannot activate authority. A theorem
gate additionally requires a governance-signed compiler profile, independently
signed verifier-result payload, profile and verifier-key activation inside the
bound ledger cutoff, and a cutoff-visible approval event for the exact gate.
This denial is deliberate. Satisfying
the gates may activate a governed deployment but never freezes the contract.

## 18. Error taxonomy, observability, and retention

Authority failures use stable machine-readable codes defined by the runtime and
API. Logs may record execution, profile, snapshot, stage duration, resource
usage, failure code, image/runtime identity, and signature status. They must not
expose private keys, arbitrary host environment, sensitive paths, or submitted
source outside the declared retention policy.

Issued witnesses and snapshots must remain verifiable. Deletion of mutable
submissions, generated inputs, intermediate output, failed artifacts, or
snapshots must not silently destroy evidence required to validate an issued
authority record.

## 19. Formal, integration, and attestation evidence

ProofAuthority V5 models result isolation, snapshot-derived identity,
execution closure, monotonic event sequence, ledger-cutoff snapshots,
backdated-event stability, and release-gated theorem authority.

The corpus contains trusted compiler/verifier source, a structural Lean
inspector, container build recipe, real-image integration runner, and portable
adversarial tests. It contains no production signing key and never substitutes
a mock for real Lean. Strict Lean, strict TLC, governed-image integration,
verifier/image build attestations, and external governance signature remain
explicit activation evidence.

## 20. Mathematical integration

All Draft 5.3.3 positive-baseline and bijective mathematics remain active as
computational-evidence profiles. The child rule remains
`parent_input = child_codeword - child_baseline`. Restricted even-payload
invariants require explicit runtime assertions at construction,
deserialization, child boundaries, and outputs. Mathematical computation never
bypasses proof, governance, snapshot, or promotion gates.

## 21. Disposition

Draft 5.3.4 is complete when all required portable phases pass. It is not an
authority-enabled release while any real integration, formal, attestation, or
external-authorization gate is absent. The correct default is:

```text
Status: corrective development draft
Theorem authority: disabled
Promotion authority: disabled
Release authority: false
Freeze status: permanently not frozen
```
