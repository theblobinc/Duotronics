# Duotronic Witness Contract v1.6 — Draft 5.3.5

**Author:** Hugh Armstrong, TBI Contracting Inc  
**Date:** July 31, 2026  
**Status:** completed corrective development draft  
**Theorem authority:** disabled by default  
**Promotion authority:** disabled by default  
**Release authority:** false  
**Freeze status:** permanently not frozen

## 1. Scope and precedence

Draft 5.3.5 carries the complete v1.6 corpus forward and corrects the
proof-execution, policy, sandbox, API, schema-lifecycle, resource-bound,
packaging, and provenance defects identified in the independent review of
Draft 5.3.4. Earlier evidence-language, replay, non-collapse,
positive-baseline, bijective-mathematics, governance, and historical material
remains present.

`CANONICAL_CORPUS_v1_6_draft_5_3_5.json` is the sole active root selector.
Earlier descriptors and exact source archives are historical replay evidence;
they cannot override the active root.

## 2. Living-contract policy

This contract is permanently not frozen. A completed draft is an internally
coherent, reproducibly validated revision, not the end of revision. Portable
corpus conformance, deployment eligibility, theorem activation, external
release authorization, and continuing revision are distinct states.

Portable success never activates theorem authority. Missing strict Lean,
strict TLC, governed-image execution, reproducible image/binary attestations,
committed-source provenance, or external governance evidence leaves authority
disabled without being mislabeled as a portable test failure.

## 3. Non-collapse of evidence and authority

A claim, proof artifact, compiled environment, trusted inspection, verifier
result, compiler witness, proof witness, policy decision, lifecycle event,
authority snapshot, theorem gate, promotion decision, package checksum, and
external signature are distinct records. No record self-certifies a record on
which its authority depends.

Computation is not theorem. A policy approval is not mathematical truth. A
signed result is not accepted unless its signer, policy, exact execution
closure, effective controls, and historical cutoff are governed. An internal
checksum closure is not an external trust root.

## 4. Canonical synchronous request boundary

The only active proof-check endpoint is synchronous
`POST /v2/proof-checks`. A client supplies a request ID, idempotency key,
subject ID, claim, theorem statement and fully qualified theorem name, an
ingested source-bundle ID, a normalized bundle-relative `.lean` artifact path,
an immutable policy-decision ID, and a governed compiler-profile ID.

The client cannot supply executable paths or hashes, OCI runtime or image
identity, environment, timestamps, verifier conclusions, axiom results,
signatures, lifecycle events, snapshots, gates, or release evidence. Absolute
paths, traversal, backslashes, NULs, source symlinks, or artifacts outside the
approved bundle fail before execution. The `Idempotency-Key` header must equal
the canonical body key. Reuse with an identical request returns the original
result; reuse with different content is rejected. The OpenAPI response is the
canonical result, not an unimplemented job resource.

## 5. Immutable policy authorization

Before source snapshotting or OCI startup, the service resolves
`policy_decision_id` through a governance-signed
`proof_policy_registry/v1`. The decision is canonical, immutable, and
content-addressed. Resolution checks identifier syntax, canonical record hash,
registry membership, decision status, subject, operation, compiler profile,
sandbox-policy bundle, effective time, expiry, revocation, and supersession.

The policy ID and record hash are bound into the verifier request, signed
verifier result, compiler witness, synchronous API result, deterministic
witness identity, database gate, and replay record. An outer adapter may not
relabel the result. Changing either value changes the signed payloads and
semantic identity. A superseded policy remains replayable by exact historical
hash but is not eligible for a new decision after its effective replacement.

## 6. FD-relative, bounded source snapshot

The authority service opens the accepted source root once and traverses from
that directory descriptor. Every component is opened relative to a verified
parent with no-follow semantics. Deterministic normalized ordering, containment,
regular-file type, link count, non-executable mode, supported ownership, and
stable identity are checked while content is streamed into a new private tree.

The snapshot rejects symlinks at any component, unsupported hard links,
devices, sockets, FIFOs, sparse files, prebuilt Lean output, native
objects/plugins, executable files, normalized/case-folding collisions, and
mutation between enumeration and read. It enforces governed bounds on total
files, directories, bytes, individual bytes, path depth, path length,
directory entries, and wall-clock time. Hashing and copying are streamed; no
whole hostile source file is required in memory.

Files are sealed `0444` and directories `0555`. Tree, artifact,
`lakefile.lean`, `lake-manifest.json`, `lean-toolchain`, and imported-source
identities are calculated only from the sealed snapshot. The mutable caller
path is never consulted afterward. The content-addressed snapshot identifier
is `sha256:<tree digest>` and is reverified after execution.

## 7. Deterministic theorem binding

The service creates a separately sealed generated module at a deterministic
path and builds that exact target. Its authority-bearing declaration is:

```lean
import Submitted.Proof.Module
set_option autoImplicit false
set_option warningAsError true
namespace WitnessAuthorityGenerated
theorem BoundClaim : (ExpectedType) := FullyQualified.theoremName
end WitnessAuthorityGenerated
```

The generated module content, declaration name, target path, request, and
snapshot inputs are hashed. A name in a comment, a theorem of another type, an
unimported artifact, stale `.olean`, or an unrelated successful target cannot
satisfy this binding.

## 8. Two-domain command model

The governed image declares no fixed `ENTRYPOINT`. The host selects exactly one
wrapper with an explicit OCI `--entrypoint` override. The image name is followed
only by that wrapper's arguments.

- The untrusted domain executes only `/opt/witness-authority/bin/compile-lean`.
- The trusted domain executes only `/opt/witness-authority/bin/verify-lean`.

The untrusted domain receives sealed source and generated inputs plus a bounded
compiler-artifact handoff. It receives no verifier request, inspection output,
final result storage, signing key, registry, authority database, governance
key, host configuration, home, cache, network, or container socket.

The trusted domain receives sealed read-only inputs, the canonical verifier
request, profile, and effective invocation plus a private bounded inspection
output. It has a `trusted_inspection_mount`, not a final-result mount. Neither
domain can access the final signed-result directory or signing key. Mount
records bind source, destination, mode, domain, purpose, and lifecycle.

## 9. Effective sandbox invocation

`EffectiveSandboxInvocation/v2` is the single source from which the OCI adapter
generates commands. It binds the runtime executable and measured version-output
hash, immutable image digest, exact entrypoint and arguments, `/work` working
directory, fixed non-root UID/GID, network mode, read-only root, capability
drop, no-new-privileges, seccomp file and hash, AppArmor profile, SELinux
label/options, user namespace, process/memory/CPU/file/open-file/time limits,
minimal environment, and complete mount manifest.

Each required control has a concrete Docker/Podman-compatible flag, a measured
runtime fact, or an explicit fail-closed rejection. Unsupported required
controls cannot be silently omitted. Immutable policy files are securely read
before their paths and hashes are accepted. UID or GID zero is forbidden.

The model separates `requested_controls`, `applied_controls`, and
`verified_controls`. Requested controls must equal applied controls for an
eligible run, and every required control must be verified by runtime
inspection. Configured claims are never relabeled as measured facts. The
normalized effective argv and immutable referenced-policy hashes determine the
sandbox invocation digest.

## 10. Measured runtime and security state

At startup and before authority use, the service executes the governed OCI
runtime's deterministic version command, normalizes its bounded output, and
compares both runtime executable hash and version-output identity with the
governed profile. A configured version string is not measurement.

The trusted inspector records effective UID/GID, working directory, mount
modes, read-only root, capability state, no-new-privileges, seccomp mode,
user-namespace mapping, network exposure, AppArmor/SELinux labels, file/open
file limits, and cgroup-backed resource facts available to the platform. A
control that cannot be observed remains unverified and prevents authority
eligibility where the policy requires it.

## 11. Bounded process execution

OCI runtime, compiler, verifier, and inspector processes run in new process
groups. Stdout and stderr are streamed with separate and combined quotas.
Timeout or quota exhaustion terminates the process group and descendants. The
record distinguishes timeout, output-limit exhaustion, compiler failure, and
verifier failure, and binds bounded diagnostic bytes plus stream hashes and the
retention policy. Host and in-container limits must agree.

## 12. Trusted Lean inspector

Source regexes, comments, declaration-name searches, pretty printing, and
ordinary stdout have no proof authority. The dedicated Lake executable target
`witnessAuthorityInspector` owns a stable CLI. Strict Lean validation must build
`Duotronic`, `WitnessAuthority`, and that exact executable target.

The governed inspector resolves the compiled declaration, elaborates the
expected type in the same environment, compares expressions under the governed
definitional-equality policy, records expected and actual expression hashes,
collects direct and transitive dependencies, queries the compiled axiom closure,
and rejects `sorryAx`, unauthorized axioms, unsafe declarations, unresolved
declarations, and forbidden native/foreign dependencies.

A deployment build attestation must bind source-tree hash, exact command,
Lean/Lake/toolchain identities, dependency lock state, output binary hash,
image/layer identity, and the exact binary copied into the image. Independent
builds must agree before reproducible-build activation may pass.

## 13. Trusted result publication

The inspection directory is private to the trusted domain and bounded. A
protected host authority rechecks the canonical inspection, effective
invocation, policy binding, registry, and signatures. Only the host signs and
atomically publishes the final verifier result.

Final publication requires a private directory and regular single-link file,
strict owner/mode and size, canonical UTF-8 JSON, duplicate-key rejection,
exclusive no-follow creation, file `fsync`, atomic no-replace publication, and
parent-directory `fsync`. Pre-existing paths, links, oversized output,
noncanonical JSON, invalid UTF-8, races, or ownership changes fail closed.

## 14. Compiler witness v4

`lean_compiler_witness/v4` binds claim, theorem type, artifact, sealed snapshot,
generated theorem, exact build targets, separate Lake/Lean/stdlib/dependency/
inspector/image/runtime identities, measured runtime version hash, sandbox
template and effective invocation, requested/applied/verified control sets,
stream hashes and output-limit status, policy-decision ID and hash, signed
verifier result, structural type and axiom results, authority snapshot and
ledger cutoff, deterministic semantic ID, server time, and final signature.

The semantic identity excludes unique run IDs and timestamps but includes
every authority-bearing input. Equivalent semantic inputs must produce stable
content identities; policy, execution-control, theorem, source, or toolchain
changes must change them.

## 15. Trust-root loading

Production configuration is loaded relative to one verified trusted directory
descriptor. Absolute paths and traversal are rejected. The root, referenced
directories, and files must have the expected owner and must not be group- or
world-writable. Files are regular, non-symlink, single-link objects opened
descriptor-relatively with no-follow semantics. Hashing occurs only from the
verified open descriptor.

These rules cover configuration, policy and compiler registries, keys, OCI
runtime, seccomp and sandbox policy, migrations, inspector executable, image
metadata, and dependency manifests.

## 16. Signed authority ledger and historical replay

Every authority-relevant action is an append-only signed governance event with
an immutable monotonic sequence and exact action scope. Current key, compiler,
policy, promotion, supersession, release, and snapshot status is derived from
events rather than unsigned row mutation.

An `authority_snapshot/v2` binds effective time, ledger high-water sequence,
ordered event-set root, policy/query versions, creator authorization,
supersession fields, and signature. Replay applies both
`effective_at <= as_of_effective_time` and
`event_sequence <= ledger_high_water_sequence`. A later event may affect a new
snapshot but cannot rewrite an existing signed historical result. Backdated
events require explicit correction authority and affected snapshot identities.

## 17. Typed supersession

A supersession is valid only when original and replacement exist under the
declared type, differ, form no cycle, use an eligible replacement, and carry an
exact signed supersession action. Records remain append-only. Policy replay
uses the historical record hash; new execution uses the effective authorized
replacement.

## 18. Schema lifecycle authority

`refs/schema_registry_v1_6_draft_5_3_5.json` classifies every schema as
canonical, legacy compatibility, archival/historical, experimental/research,
or forbidden/removed and records lifecycle plus active-version scope. Active
API, persistence, witness, and write surfaces may use only registered canonical
schemas. Unclassified schemas fail validation.

The validator compiles every registered schema, enforces strict AJV for the
canonical set, resolves unique `$id` and `$ref` paths, rejects duplicate
versions or registry paths, and requires positive and negative Draft 5.3.5
fixtures for every canonical authority schema. Legacy fixtures do not promote a
legacy schema to active authority.

## 19. Persistence and theorem gates

The Draft 5.3.5 migration adds immutable signed proof-policy registries and
policy decisions, v4 compiler witnesses, and v4 theorem gates. A gate requires
exact claim/theorem/artifact/snapshot/generated-target/toolchain/image/runtime/
sandbox/policy/signature bindings, an allowed relevant non-collapse path,
cutoff-visible key and profile lifecycle, and cutoff-visible promotion approval.

The portable database includes no production release activation. Authoritative
views therefore return no new Draft 5.3.5 theorem authority unless all signed
deployment evidence exists. Direct Boolean insertion cannot activate authority.
Records are append-only; corrections supersede.

## 20. Formal and mathematical integration

ProofAuthority V6 models exact domain dispatch, requested/applied/verified
control closure, non-root execution, measured runtime identity, policy binding,
bounded source/output resources, registry classification, committed provenance,
and external activation. The strict TLA manifest includes V6 and its
configuration; static name coverage is not TLC execution.

All positive-baseline, bijective-numeration, polygonal-cell, and non-collapse
mathematics remain active as computational-evidence profiles. The child rule is
`parent_input = child_codeword - child_baseline`. Restricted even-payload
invariants require explicit runtime assertions at construction,
deserialization, child boundaries, and outputs. Mathematical computation never
bypasses proof, policy, governance, snapshot, or promotion gates.

## 21. Package provenance and manifest closure

The package provenance record binds repository, source reference, commit SHA,
subtree path/digest, generator name/version/hash, base revision,
transformation/change-set identity, and clean/dirty status. A local uncommitted
build is truthfully classified `unpublished_workspace` and is not a final
source-provenance activation artifact.

The recursive package inventory covers every member. Self-referential generated
artifacts exclude only unstable cryptographic/size fields, use explicit `null`
values, and state the excluded fields and reason. Every nonexcluded member is
verified against final packaged bytes. Vendored dependency documentation is
checked for dependency integrity but excluded from first-party link quality.

## 22. Validation profiles

The portable profile reconciles every declared required phase by canonical ID
and fails on missing, duplicate, failed, skipped, or unknown required phases.
It verifies Python with resource warnings as errors, schemas and fixtures, SQL
migration and lifecycle behavior, policy binding, OCI argv construction,
sandbox control mapping, source/output limits, synchronous API conformance,
formal manifest coverage, entrypoint/version consistency, provenance fields,
historical archives, and final-byte inventory closure.

Strict Lean, strict TLC, real governed-image execution and runtime inspection,
two independent inspector/image build attestations, committed clean-source
provenance, and external governance signature are activation blockers. A
development package may report them incomplete; it may not report them passed
or enable authority.

## 23. Error, observability, and retention

Authority failures use stable machine-readable codes. Logs may record execution
ID, profile, policy hash, snapshot, stage duration, bounded resource use,
failure code, image/runtime identity, and signature status. Logs must not expose
private keys, arbitrary environment, undeclared host paths, or submitted source
beyond governed retention.

Issued witnesses, policy decisions, and snapshots remain verifiable. Deleting
mutable submissions or intermediate output cannot silently destroy evidence
required to validate an issued authority record.

## 24. Disposition

Draft 5.3.5 is a completed standalone corrective corpus when every required
portable phase passes against final archive bytes. It is not activation-ready
while any governed external/toolchain/provenance gate is incomplete. Its
canonical default is:

```text
Status: completed corrective development draft
Theorem authority: disabled by default
Promotion authority: disabled by default
Release authority: false
Freeze status: permanently not frozen
Source provenance: unpublished_workspace until committed-source evidence exists
```
