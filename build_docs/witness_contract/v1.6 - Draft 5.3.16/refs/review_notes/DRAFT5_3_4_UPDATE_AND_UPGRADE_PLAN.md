# Duotronic Witness Contract v1.6 Draft 5.3.4

## Update and Upgrade Plan

**Proposed revision:** v1.6 Draft 5.3.4
**Revision type:** Corrective security, determinism, and authority-binding release
**Primary objective:** Close the remaining proof-authority trust-boundary gaps identified in Draft 5.3.3 and prepare the corpus for a future authority-enabled release.

---

## 1. Revision goals

Draft 5.3.4 should focus on converting the proof-authority path from a largely well-specified design into a verifiably closed execution and governance system.

The revision should:

1. Prevent submitted Lean code from influencing the verifier result channel.
2. Bind every proof digest to the exact immutable bytes compiled.
3. Make historical authority snapshots immutable under later backdated events.
4. Bind the real OCI runtime, verifier executable, Lean toolchain, dependency closure, and sandbox invocation to the resulting witness.
5. Harden configuration, registry, key, and runtime file loading against symlinks, ownership ambiguity, and group/world write access.
6. Strengthen SQL type integrity, policy scope enforcement, and lifecycle authorization.
7. Add real hermetic integration tests rather than relying only on subprocess mocks.
8. Eliminate stale package metadata and version inconsistencies.
9. Keep theorem authority disabled until all mandatory release gates pass.

---

# 2. Mandatory P0 changes

The following changes are release blockers. Draft 5.3.4 should not be described as proof-authority-ready unless every P0 item is implemented and tested.

## P0.1 Separate submitted Lean execution from the verifier result channel

### Current problem

The 5.3.3 design gives the proof-processing container writable access to `/output/verifier-result.json`. Submitted Lean code may execute `IO`, spawn processes, or attempt filesystem manipulation. As a result, code being verified can potentially create, overwrite, race, or replace the same result file that the host later treats as authoritative.

A structured JSON result is not trustworthy merely because it has the expected format. The result must be produced through a channel that submitted code cannot access.

### Required architecture

Split proof verification into two security domains:

1. **Untrusted compilation domain**

   * Receives only the immutable submitted source snapshot.
   * Has no writable access to the final result directory.
   * Has no access to governance keys, compiler registry files, authority databases, or host configuration.
   * Produces only bounded intermediate compiler artifacts through a dedicated handoff channel.

2. **Trusted verifier domain**

   * Runs trusted verifier code from the approved image.
   * Reads the bounded intermediate compiler output.
   * Inspects the loaded Lean environment, theorem declaration, theorem type, and axiom set.
   * Produces the canonical verifier result.
   * Is the only process permitted to publish the final result.

### Required filesystem design

The final result directory should:

* Be created by the host with mode `0700`.
* Be owned by the authority-service UID.
* Never be mounted writable into the untrusted compilation domain.
* Reject symbolic links.
* Reject files with link count other than one.
* Reject non-regular files.
* Enforce a strict maximum result size.
* Use exclusive creation.
* Use `O_NOFOLLOW`.
* Be published atomically through write, `fsync`, rename, and parent-directory `fsync`.

The trusted verifier should write to a temporary file such as:

```text
verifier-result.json.tmp.<nonce>
```

and atomically rename it to:

```text
verifier-result.json
```

only after canonicalization and internal validation are complete.

### Preferred result-signing model

The structured verifier result should be signed inside the approved verifier image or by a separate host-side authority component using a verifier-result signing key.

The signed payload should bind:

* Request identifier
* Snapshot tree digest
* Proof artifact digest
* Generated binding module digest
* Compiler registry record identifier
* Lean executable digest
* Lake executable digest
* Verifier executable digest
* Dependency closure digest
* OCI image digest
* OCI runtime digest
* Effective sandbox invocation digest
* Theorem declaration
* Expected type digest
* Actual type digest
* Axiom set
* Exit status
* Timeout status
* Execution start and finish timestamps
* Result schema version

The host must reject unsigned results and results signed by a key not authorized for the selected verifier profile.

### New tests

Add real adversarial tests for:

* `#eval` attempting to write the final result path
* `#eval` attempting to create a symlink at the result path
* Spawned child process attempting delayed result replacement
* Submitted code attempting to read the verifier request
* Submitted code attempting to enumerate `/output`
* Oversized output
* Result-file race
* Result-file hard-link creation
* Container termination while a child process remains alive
* Fake canonical JSON emitted by submitted code

### Acceptance criteria

* Submitted code has no filesystem path to the final result directory.
* A fake result generated by submitted code is never accepted.
* The host accepts only a signed result from the trusted verifier domain.
* All result publication invariants are enforced by code and regression tests.

---

## P0.2 Derive all artifact hashes from the immutable snapshot

### Current problem

Draft 5.3.3 calculates the original proof artifact hash before the immutable snapshot is created. The source can change between the initial hash and the snapshot operation. This permits a witness to bind one digest while compiling different bytes.

### Required processing order

The authority service must use this sequence:

1. Validate the submitted source path at the request boundary.
2. Create an immutable snapshot.
3. Seal the snapshot against mutation.
4. Calculate the complete snapshot tree digest.
5. Calculate every per-file digest from files inside the sealed snapshot.
6. Generate the statement-binding module outside the original source tree or in a separately sealed generated-input area.
7. Calculate the generated-module digest.
8. Construct the verifier request from only snapshot-derived and generated-input-derived values.
9. Execute the verifier against the sealed snapshot.
10. Verify that the result binds the same snapshot and generated-module digests.
11. Create and sign the final compiler witness.

No digest used for proof authority should be calculated from the mutable caller-controlled source path after snapshot creation.

### Required witness fields

Add or clarify:

```text
submitted_source_locator
immutable_snapshot_id
immutable_snapshot_tree_sha256
proof_artifact_relative_path
proof_artifact_sha256
lakefile_sha256
lake_manifest_sha256
lean_toolchain_sha256
generated_binding_module_sha256
generated_binding_request_sha256
```

The `proof_artifact_relative_path` must be normalized and validated to prevent traversal.

### Snapshot hardening

The snapshot implementation should:

* Reject symlinks unless the contract explicitly defines safe symlink semantics.
* Reject device files, sockets, FIFOs, and hard-link ambiguity.
* Normalize file order.
* Normalize metadata included in the tree digest.
* Define whether executable bits are semantically relevant.
* Reject files that change during copy.
* Verify the final sealed tree again before execution.
* Mount the snapshot read-only into the container.
* Use a content-addressed snapshot identifier.

### New tests

Add tests that mutate:

* The theorem source between request validation and snapshot creation
* The theorem source during snapshot creation
* `lakefile.lean`
* `lake-manifest.json`
* `lean-toolchain`
* A transitive imported `.lean` file
* A file after snapshot sealing
* A path through symlink substitution
* A file through hard-link mutation

### Acceptance criteria

* The witness artifact digest always equals the bytes compiled.
* Any mutation before snapshot completion causes rejection or is captured by the snapshot.
* Any mutation after snapshot sealing has no effect on execution.
* The original mutable source path is never used as a proof-authority input after sealing.

---

## P0.3 Bind historical authority snapshots to an immutable ledger cutoff

### Current problem

An authority snapshot currently evaluates events using effective timestamps but does not bind the event set used for evaluation. A later-recorded event with an earlier effective date can retroactively alter the meaning of an already signed snapshot.

### Required event-ledger model

Every authority-relevant event must receive an immutable monotonic sequence number at insertion time.

Examples include:

* Verifier-key activation
* Verifier-key retirement
* Verifier-key revocation
* Compiler-profile activation
* Compiler-profile revocation
* Promotion-gate approval
* Promotion-gate withdrawal
* Supersession
* Policy authorization
* Authority snapshot creation

Add a sequence such as:

```text
authority_event_sequence INTEGER PRIMARY KEY AUTOINCREMENT
```

or an equivalent append-only ledger sequence.

### Required snapshot binding

Every signed authority snapshot must include:

```text
snapshot_id
as_of_effective_time
ledger_high_water_sequence
event_set_root_sha256
authority_policy_version
snapshot_query_version
created_at
created_by_principal
authorization_witness_id
snapshot_signature
```

All snapshot queries must apply both:

```text
effective_at <= as_of_effective_time
authority_event_sequence <= ledger_high_water_sequence
```

A later event may affect a newly created snapshot but must never alter the result of an existing signed snapshot.

### Event-set root

Preferably calculate a canonical event-set Merkle root or canonical aggregate digest over all authority events through the high-water sequence.

The snapshot verifier should recompute the root before accepting the snapshot.

### Backdated events

Backdated events should be allowed only under an explicit correction policy.

A backdated event must include:

* Correction reason
* Authorizing governance decision
* Prior affected snapshot identifiers
* Whether the correction is prospective only or requires formal snapshot supersession
* A signed correction witness

A backdated event must not silently rewrite prior authority history.

### New tests

Add tests showing:

1. A snapshot is created at sequence N.
2. A later event is inserted at sequence N+1 with an earlier `effective_at`.
3. Re-evaluating the original snapshot still returns the original authority set.
4. A new snapshot reflects the later event.
5. Event-set root verification fails after unauthorized database mutation.
6. Snapshot supersession requires an explicit signed governance event.

### Acceptance criteria

* Signed snapshots are stable forever unless explicitly superseded.
* Later backdated events cannot alter prior snapshot evaluation.
* Historical replay is deterministic from snapshot payload plus ledger contents through the bound cutoff.

---

# 3. P1 security and integrity upgrades

## P1.1 Harden generated-module mount permissions

The temporary generated-module mount root must be traversable by the unprivileged container UID while remaining non-writable.

Recommended permissions:

```text
generated mount root: 0555
generated module directory: 0555
generated module file: 0444
```

The runtime should verify these modes before container launch.

Add an integration test that runs as UID/GID `65534:65534` and confirms:

* The generated module is readable.
* The directory is traversable.
* No file in the generated mount can be changed or created.

---

## P1.2 Remove the host-world-writable result directory

Replace mode `0777` with a private authority-service directory.

Recommended controls:

* Directory mode `0700`
* Result file mode `0600`
* Fixed expected owner UID and GID
* `openat` relative to a trusted directory descriptor
* `O_NOFOLLOW`
* `O_CREAT | O_EXCL`
* Maximum result size
* Regular-file and link-count checks
* Atomic rename
* Cleanup on failure

The service should fail closed if any ownership or mode check fails.

---

## P1.3 Enforce the sandbox policy rather than merely hashing it

The sandbox-policy digest must describe the actual executed constraints.

Create a canonical `EffectiveSandboxInvocation` object containing:

```text
oci_runtime_path
oci_runtime_sha256
oci_runtime_version
image_reference
image_digest
entrypoint
arguments
container_uid
container_gid
network_mode
read_only_rootfs
capability_drop_set
security_options
seccomp_profile_sha256
apparmor_profile
selinux_label
user_namespace_mode
pid_limit
memory_limit
cpu_limit
file_size_limit
open_file_limit
timeout
environment_allowlist
mount_manifest
working_directory
```

Canonicalize and hash this object before execution.

After container creation, inspect the runtime configuration and verify it matches the approved invocation where the runtime supports inspection.

The final witness should bind:

```text
sandbox_policy_sha256
effective_sandbox_invocation_sha256
oci_runtime_sha256
oci_runtime_version
```

### Minimum runtime controls

The proof container should use:

* No network
* Read-only root filesystem
* Dropped capabilities
* `no-new-privileges`
* Fixed non-root UID/GID
* Bounded PID count
* Bounded memory
* Bounded CPU
* Bounded output size
* Bounded runtime
* Empty or minimal environment
* No host user home
* No Docker socket
* No authority database
* No governance keys
* No host compiler cache
* No writable source mount
* Explicit tmpfs only where needed

---

## P1.4 Harden production trust-root loading

Configuration and key loading should reject ambiguous filesystem authority.

### Required checks

For the configuration root and every referenced file:

* Resolve relative to a trusted root directory descriptor.
* Reject absolute paths unless explicitly permitted by policy.
* Reject `..` traversal.
* Reject symlinks.
* Reject group-write and world-write permission.
* Require expected owner UID.
* Require regular files.
* Require link count of one where feasible.
* Require parent directories to satisfy the same ownership and write restrictions.
* Open with `openat` and `O_NOFOLLOW`.
* Hash after opening the verified file descriptor.
* Avoid separate path-check and path-open operations.

The service should not load from a `0770`, `0775`, `0777`, group-writable, or world-writable root.

### Files requiring these checks

* Authority service configuration
* Compiler registry
* Verifier registry
* Public key registry
* Private signing key references
* OCI runtime path
* Sandbox policy
* Governance policy
* SQL migration directory
* Verifier executable
* Image metadata
* Dependency manifests

### New tests

Test:

* Group-writable root
* Group-writable parent directory
* Symlinked registry
* Symlinked runtime
* Hard-linked key file
* Registry outside the trust root
* Ownership mismatch
* File replacement between validation and open
* Relative traversal
* Bind-mounted mutable configuration

---

## P1.5 Bind the real verifier executable and runtime closure

The approved profile should bind all executable components that can affect proof processing.

Add registry fields for:

```text
verifier_executable_sha256
lean_executable_sha256
lake_executable_sha256
oci_runtime_sha256
oci_image_digest
lean_stdlib_tree_sha256
dependency_closure_sha256
verifier_source_revision
verifier_build_attestation_id
```

The service should measure or verify these at startup and again before authority execution where practical.

A compiler profile should become inactive if any measured digest differs from its governed registry record.

---

## P1.6 Provide the actual trusted verifier implementation

The revision must include the source and build provenance for the executable identified as:

```text
/opt/witness-authority/bin/verify-lean
```

The implementation should:

1. Parse a versioned canonical request.
2. Load the immutable snapshot.
3. Load the generated binding module.
4. Resolve the theorem declaration from the Lean environment.
5. Compare actual and expected theorem types structurally.
6. Collect axioms programmatically.
7. Reject `sorryAx`, undeclared axioms, forbidden axioms, and unresolved declarations.
8. Emit canonical structured output.
9. Sign the result or pass it through a protected signing boundary.
10. Return bounded, explicit failure codes.

The repository should include:

* Source
* Build instructions
* Reproducible build configuration
* Executable digest
* Source-to-binary attestation
* Unit tests
* Real-image integration tests

---

# 4. SQL and governance upgrades

## P1.7 Add typed existence checks to supersession records

A supersession must not refer to nonexistent or wrong-type records.

Before insertion, verify:

* `superseded_record_id` exists.
* `replacement_record_id` exists.
* Both records match the declared `record_type`.
* The replacement is not the same record.
* The replacement is not already superseded in an incompatible chain.
* The supersession does not create a cycle.
* The replacement is valid under the applicable authority policy.
* The authorization witness is valid at the event time.

Create type-specific foreign-key bridge tables or validated triggers rather than relying only on free-form record identifiers.

### Required tests

* Nonexistent superseded record
* Nonexistent replacement
* Wrong record type
* Self-supersession
* Supersession cycle
* Replacement already revoked
* Expired authorization witness
* Invalid governance policy scope

---

## P1.8 Split governance policy scopes by action

Replace the broad `authority_supersession` scope with explicit scopes.

Recommended scopes:

```text
verifier_key_activate
verifier_key_retire
verifier_key_revoke
compiler_profile_activate
compiler_profile_revoke
promotion_gate_approve
promotion_gate_withdraw
authority_record_supersede
authority_snapshot_create
authority_snapshot_supersede
backdated_event_authorize
```

Create an explicit action-to-scope mapping table and require exact scope compatibility.

All governance authorization checks must enforce:

```text
valid_from <= event_time
valid_until IS NULL OR event_time < valid_until
```

They should also enforce principal, policy version, action type, target type, and target identifier.

---

## P1.9 Make lifecycle events first-class signed records

Every lifecycle event should have:

* Event identifier
* Event sequence
* Event type
* Target type
* Target identifier
* Effective time
* Recorded time
* Reason code
* Human-readable rationale
* Authorization witness
* Governance policy version
* Canonical payload hash
* Signer key identifier
* Signature

Avoid unsigned direct status mutation.

Current status should be derived from the append-only event ledger.

---

# 5. Lean and proof-verification upgrades

## P1.10 Use structural theorem-type comparison

The trusted verifier should compare theorem types using Lean expressions after elaboration, not only source strings or pretty-printed output.

Record both:

```text
expected_type_expression_hash
actual_type_expression_hash
```

Also record the normalization policy used for comparison.

The contract should define whether the comparison is:

* Definitional equality
* Syntactic equality after canonical normalization
* Alpha-equivalence
* Universe-level normalized equality
* Equality under reducibility settings

The selected rule must be stable, versioned, and tested.

---

## P1.11 Programmatically collect the axiom closure

The verifier should inspect the declaration’s dependency and axiom closure through Lean APIs.

The result should contain:

```text
direct_dependencies
transitive_dependencies_root
axiom_set
forbidden_axiom_set
sorry_ax_present
unsafe_dependency_present
opaque_dependency_policy_result
```

The authority policy should explicitly define:

* Allowed foundational axioms
* Forbidden axioms
* Treatment of classical axioms
* Treatment of quotient soundness
* Treatment of choice
* Treatment of unsafe declarations
* Treatment of foreign-function or native-code dependencies

---

## P1.12 Reduce generated binding-module complexity

Prefer a minimal generated binding expression such as:

```lean
example : ExpectedType := FullyQualified.theoremName
```

Avoid unnecessary tactic execution.

The generated module should:

* Use a deterministic filename.
* Use a deterministic module name.
* Contain no caller-provided commands other than safely encoded identifiers and expected type syntax.
* Be hashed before execution.
* Be mounted read-only.
* Be included in the verifier request and result.

The module name and path should derive from canonical request data, not randomness.

---

# 6. Integration and adversarial test plan

## P1.13 Real Lean integration suite

The revision should include a CI job using the exact governed image digest.

### Required success cases

* Valid theorem with no forbidden axioms
* Valid theorem using permitted axioms
* Deterministic repeat verification
* Historical replay with the same snapshot
* Multiple modules and transitive imports

### Required rejection cases

* Claimed type mismatch
* Missing declaration
* Comment-only declaration
* `sorry`
* `admit`
* Hidden `sorryAx`
* Forbidden axiom
* Unsafe declaration
* Stale `.olean`
* Injected `.olean`
* Modified `lakefile.lean`
* Modified `lean-toolchain`
* Modified dependency
* Symlinked source
* Hard-linked mutable source
* Proof source mutation during submission
* Generated-module mutation
* Fake structured result
* Result symlink
* Result race
* `#eval` file write
* Process spawning
* Network access
* Host environment access
* Host-cache access
* Timeout
* Memory exhaustion
* PID exhaustion
* Oversized stdout/stderr
* Orphaned subprocess after timeout
* Invalid UTF-8 output
* Duplicate JSON keys
* Non-canonical result JSON
* Wrong result signature
* Revoked verifier-result signing key
* Mismatched image digest
* Mismatched OCI runtime digest
* Mismatched sandbox invocation digest

---

## P1.14 Reproducibility tests

Run the same request multiple times and require stable values for:

* Snapshot digest
* Artifact digest
* Generated-module digest
* Expected type digest
* Actual type digest
* Axiom-set digest
* Compiler profile identifier
* Sandbox invocation digest
* Semantic verifier result

Fields expected to differ, such as execution timestamps or unique execution identifiers, must be clearly separated from deterministic semantic identity.

Define a deterministic witness-content identifier based on canonical semantic fields.

---

## P1.15 Historical authority tests

Test:

* Key activation and retirement
* Key revocation
* Compiler profile revocation
* Promotion-gate withdrawal
* Supersession chains
* Snapshot creation at a ledger cutoff
* Later backdated event
* Snapshot stability
* Explicit snapshot supersession
* Invalid event-set root
* Duplicate event sequence
* Database mutation
* Policy-version migration

---

# 7. Metadata and corpus consistency

## P1.16 Update package metadata to 5.3.4

Update:

* `package.json`
* `package-lock.json`
* Corpus manifest
* Release notes
* Validation report titles
* Schema identifiers
* OpenAPI version
* SQL migration identifiers
* Test fixture version fields
* Generated report version fields

Remove stale references to:

```text
duotronic-witness-contract-v1-6-draft-5-3-2-validation
1.6.5-3-2
```

The validator should fail if package metadata does not match the corpus revision.

---

## P1.17 Add a version-consistency validation phase

Create a required validation phase that checks version agreement across:

* Main contract
* Release notes
* Manifest
* Package metadata
* OpenAPI
* JSON Schemas
* SQL schema version
* Migration filenames
* Lean modules
* TLA+ modules
* Test fixtures
* Generated reports

Any stale version string should fail the corpus validation.

---

# 8. Recommended P2 improvements

## P2.1 Add source and build attestations

Produce signed build attestations for:

* Trusted verifier executable
* OCI image
* Lean toolchain
* Dependency closure
* Validation package

Use a standard provenance format where possible.

---

## P2.2 Add canonical error taxonomy

Define stable result codes such as:

```text
snapshot_creation_failed
snapshot_mutation_detected
artifact_digest_mismatch
generated_module_digest_mismatch
compiler_profile_inactive
runtime_digest_mismatch
sandbox_policy_mismatch
verifier_result_missing
verifier_result_invalid
verifier_result_signature_invalid
theorem_declaration_missing
theorem_type_mismatch
forbidden_axiom_present
sorry_axiom_present
unsafe_dependency_present
resource_limit_exceeded
verification_timeout
authority_snapshot_invalid
ledger_cutoff_mismatch
governance_authorization_invalid
```

Error codes should be machine-readable and must not expose sensitive host paths.

---

## P2.3 Add observability without leaking proof inputs

Record:

* Execution identifier
* Profile identifier
* Snapshot identifier
* Stage durations
* Resource usage
* Failure code
* Image digest
* Runtime digest
* Result signature status

Do not log:

* Private signing material
* Unredacted environment
* Sensitive host paths
* Arbitrary submitted source unless explicitly allowed by retention policy

---

## P2.4 Define retention and deletion semantics

Specify how long the system retains:

* Submitted mutable source
* Immutable snapshots
* Generated modules
* Intermediate compiler output
* Final structured results
* Signed compiler witnesses
* Authority snapshots
* Failed-verification artifacts

Deletion must not destroy the ability to validate already issued authority records unless the contract explicitly defines an archival or revocation process.

---

## P2.5 Add database migration and rollback documentation

Provide a Draft 5.3.3 to 5.3.4 migration plan covering:

* New event-sequence column or table
* Snapshot high-water sequence
* Event-set root
* New governance scopes
* New lifecycle event schema
* New compiler witness fields
* Backfill behavior
* Existing record compatibility
* Rollback limitations

Do not silently reinterpret existing signed 5.3.3 records as 5.3.4 records.

---

# 9. Proposed schema changes

## 9.1 Compiler witness

Add:

```text
immutable_snapshot_id
immutable_snapshot_tree_sha256
proof_artifact_relative_path
proof_artifact_sha256
generated_binding_module_sha256
generated_binding_request_sha256
verifier_executable_sha256
lean_executable_sha256
lake_executable_sha256
lean_stdlib_tree_sha256
dependency_closure_sha256
oci_image_digest
oci_runtime_sha256
oci_runtime_version
sandbox_policy_sha256
effective_sandbox_invocation_sha256
verifier_result_payload_sha256
verifier_result_signer_key_id
verifier_result_signature
expected_type_expression_hash
actual_type_expression_hash
axiom_set_sha256
authority_snapshot_id
authority_ledger_high_water_sequence
```

## 9.2 Authority snapshot

Add:

```text
ledger_high_water_sequence
event_set_root_sha256
snapshot_query_version
governance_policy_version
supersedes_snapshot_id
supersession_reason
```

## 9.3 Governance event

Add:

```text
authority_event_sequence
action_scope
target_type
target_id
effective_at
recorded_at
canonical_payload_sha256
authorization_witness_id
signer_key_id
signature
```

---

# 10. Proposed implementation sequence

## Phase 1: Close the result-channel boundary

1. Split untrusted compilation and trusted result production.
2. Remove writable result access from submitted code.
3. Add signed verifier results.
4. Harden host-side result-file handling.
5. Add result-channel adversarial tests.

## Phase 2: Correct snapshot and digest ordering

1. Snapshot first.
2. Seal snapshot.
3. Hash only snapshot contents.
4. Generate and hash deterministic binding module.
5. Verify result-to-request digest consistency.
6. Add mutation and race tests.

## Phase 3: Make historical authority immutable

1. Add immutable event sequence.
2. Add snapshot ledger cutoff.
3. Add event-set root.
4. Update all as-of views.
5. Add backdated-event policy.
6. Add snapshot stability tests.

## Phase 4: Bind the execution closure

1. Add verifier executable digest.
2. Add OCI runtime digest and version.
3. Add effective sandbox invocation object.
4. Add dependency closure digest.
5. Enforce runtime/profile matching.
6. Add mismatch tests.

## Phase 5: Harden trust roots and governance

1. Replace path-based checks with descriptor-based safe loading.
2. Reject group/world writable roots.
3. Add typed supersession checks.
4. Split governance scopes.
5. Enforce authorization validity intervals.
6. Add lifecycle and supersession tests.

## Phase 6: Run real hermetic integration

1. Build the governed image.
2. Run the real Lean verifier.
3. Run all adversarial cases.
4. Capture signed integration evidence.
5. Run strict Lean and strict TLC.
6. Generate final corrective assurance report.

---

# 11. Required release evidence

Draft 5.3.4 should include:

* Complete portable validator report
* Real Lean integration report
* OCI image build attestation
* Verifier executable build attestation
* Compiler and dependency closure manifest
* Sandbox invocation conformance report
* Snapshot mutation test report
* Result-channel isolation report
* Historical snapshot stability report
* SQL governance test report
* Strict Lean result
* Strict TLC result
* External governance signature over the final release manifest

Each report should identify:

* Exact source revision
* Exact image digest
* Exact executable digests
* Exact test count
* Passed, failed, skipped, and unavailable cases
* Whether the evidence is release-authoritative

---

# 12. Draft 5.3.4 release gates

## Gate A: Result-channel isolation

Pass only if submitted code cannot create, replace, influence, or race the final verifier result.

## Gate B: Snapshot-to-artifact identity

Pass only if all proof-artifact hashes are derived from the exact sealed snapshot compiled.

## Gate C: Historical snapshot immutability

Pass only if later-recorded backdated events cannot alter an existing signed snapshot.

## Gate D: Execution closure identity

Pass only if the witness binds the verifier executable, Lean executable, Lake executable, dependency closure, OCI image, OCI runtime, and effective sandbox invocation.

## Gate E: Real integration

Pass only if the exact governed image successfully completes the real Lean adversarial suite.

## Gate F: Governance integrity

Pass only if lifecycle, supersession, snapshot, and backdated-event actions require valid action-specific authorization.

## Gate G: Formal validation

Pass only if strict Lean and strict TLC complete successfully under the declared authoritative toolchains.

## Gate H: Corpus consistency

Pass only if every required validation phase succeeds and every version identifier matches Draft 5.3.4.

## Gate I: External release authorization

Pass only if the final manifest and release evidence receive the required external governance signature.

---

# 13. Recommended release status language

Until every mandatory gate passes, use:

```text
Status: corrective development draft
Theorem authority: disabled
Promotion authority: disabled
Release authority: false
Freeze status: not frozen
```

After all technical gates pass but before external governance approval, use:

```text
Status: release candidate
Theorem authority: technically eligible but not activated
Promotion authority: disabled pending governance approval
Release authority: false
Freeze status: pending external authorization
```

Only after all gates and governance signatures pass should the revision claim proof-authority readiness.

---

# 14. Definition of done

Draft 5.3.4 is complete when:

1. Submitted Lean code cannot access or influence the final result channel.
2. Artifact hashes are calculated only from a sealed immutable snapshot.
3. Signed historical snapshots bind an immutable event-ledger cutoff.
4. The actual verifier and complete execution closure are cryptographically bound.
5. Sandbox-policy claims are derived from the executed invocation.
6. Production trust roots reject symlinks, unsafe ownership, and group/world write access.
7. Supersession and lifecycle events have typed, signed, action-specific authorization.
8. The real governed Lean image passes the adversarial integration suite.
9. Strict Lean and strict TLC succeed.
10. Package, schema, manifest, report, and fixture versions are internally consistent.
11. The final release manifest is externally signed.
12. The corpus continues to fail closed whenever any required evidence is absent.
