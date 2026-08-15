# Duotronic Witness Contract v1.6 — Draft 5.3.3

**Author:** Hugh Armstrong, TBI Contracting Inc  
**Date:** July 31, 2026  
**Status:** complete active corrective draft; living contract; permanently not frozen

## 1. Scope

Draft 5.3.3 carries the complete v1.6 corpus forward and closes the remaining
Draft 5.3.2 trust-boundary gaps around what actually runs as Lean and which
compiled bytes it may import. It preserves the evidence language, non-collapse
rules, replay semantics, positive-baseline mathematics, and the 5.3.1/5.3.2
content, signature, and lifecycle corrections.

This is a living contract. It is intentionally never frozen. “Complete” means
that the active draft is internally closed, packaged, and portable-validator
complete; it does not mean that revision has ended or theorem authority is
enabled in a deployment.

## 2. Canonical version and living-contract policy

`CANONICAL_CORPUS_v1_6_draft_5_3_3.json` is the only active root selector.
Historical descriptors and filenames remain replay evidence and cannot override
it. Missing, malformed, inconsistent, or unavailable canonical artifacts cause
boot failure.

The corpus separates three states:

1. **draft completeness** — all required portable phases pass;
2. **deployment authority activation** — the deployment has the approved real
   Lean image, strict evidence, protected keys, and external trust anchor; and
3. **freeze** — prohibited by the living-contract policy.

Strict Lean, TLC, hermetic integration, external signature, and human review
strengthen or activate authority. They never freeze the contract.

## 3. Permanent evidence/authority separation

- A claim is content.
- A proof artifact is evidence about a statement.
- A clean compiler execution is evidence that governed bytes processed an
  immutable source snapshot.
- A structured verifier result is evidence about declaration existence, type
  equality, source compilation, and axiom dependencies.
- A compiler witness binds that result to exact content, toolchain, environment,
  verifier, key, and trusted time.
- A proof witness binds the compiler witness to policy and claim identity.
- A non-collapse transition records a permitted epistemic change.
- A promotion gate records that the complete conjunction matched.
- A governance signature authorizes a lifecycle or supersession event; it does
  not make a mathematical claim true.
- A package checksum is internal integrity evidence, not an external trust root.

No object may self-certify another object on which its authority depends.

## 4. Governed compiler registry

A proof-check request selects only `compiler_profile_id`. It cannot supply Lake,
Lean, container-runtime, image, library, dependency, plugin, sandbox, or
timestamp paths or hashes.

The protected service loads a governance-signed
`governed_compiler_registry/v1`. Each profile independently binds:

```text
compiler_profile_id
toolchain
execution_image_digest
lake_executable_shake256_512
lean_executable_shake256_512
lean_stdlib_tree_shake256_512
dependency_closure_shake256_512
verifier_binary_shake256_512
sandbox_policy_shake256_512
authorized_axioms
valid_from / valid_until
```

Agreement between a caller-supplied executable and caller-supplied digest has no
authority. The actual Lean executable is separate from Lake. Image and
dependency-closure attestations must match the governed profile exactly.

The package contains schemas and runtime support, but no production private key
or external governance trust anchor. A deployment without those protected
inputs fails closed and leaves theorem authority disabled.

## 5. Immutable clean-source build

Before execution, the authority service:

1. resolves an already-ingested source bundle;
2. rejects source symlinks, executable files, `.olean`, `.ilean`, object files,
   native libraries/plugins, C/C++ sources, and shell executables;
3. hashes the accepted source tree;
4. copies it to a new isolated directory;
5. hashes the original again and hashes the copy;
6. requires all three digests to agree; and
7. changes the copied tree to read-only before execution.

The original source-tree digest and immutable-snapshot digest remain separate
fields even when equal. The deterministic generated module has a separate hash.
Submitted `lakefile.lean` and `lake-manifest.json` are recorded metadata; they
are not an executable command source for the verifier.

Any mutation during snapshot creation, prebuilt output, external artifact,
symlink, or native plugin causes rejection before Lean runs.

## 6. Deterministic statement-binding target

The generated filename derives from the claim, theorem, artifact, snapshot, and
compiler-profile digests:

```text
.witness_authority/Check_<32 lowercase hex characters>.lean
```

The generated module uses direct term binding:

```lean
import Submitted.Proof.Module
set_option autoImplicit false
set_option warningAsError true
example : (<claimed theorem statement>) := <fully qualified theorem name>
```

There is no randomized filename or tactic wrapper. Identical content and
compiler profile produce the same target and compiler-witness identifier. The
server timestamp may differ without changing content identity.

## 7. Hermetic execution boundary

The canonical sandbox profile requires:

- a digest-pinned image and protected, hash-pinned OCI runtime;
- no network namespace;
- read-only root filesystem and input mounts;
- an ephemeral writable output directory only;
- all capabilities dropped and no-new-privileges enabled;
- fixed unprivileged UID/GID;
- CPU, memory, process, temporary-storage, file, and wall-time limits;
- a minimal fixed locale and timezone environment; and
- no inherited `LEAN_PATH`, `ELAN_HOME`, `LAKE_HOME`, proxy variables, home
  directory, user configuration, or host caches.

The image builds every imported submitted module from source into a fresh
output tree and reports `prebuilt_artifacts_used = false`. Submitted Lake
configuration, macros, or native elaborator plugins cannot redefine the
governed verifier entrypoint or environment.

## 8. Structured Lean inspection

Human-readable stdout and stderr are diagnostic only. Regexes over `#print
axioms`, source text, comments, warnings, or declaration names have no authority.

The trusted verifier inspects Lean’s compiled environment and emits one
canonical `wc_lean_verifier_result/v1` JSON file. The result binds the request,
claim, statement, artifact, immutable snapshot, generated module, compiler
profile, Lake, actual Lean executable, stdlib, dependency closure, verifier
binary, and image. It states:

- whether the declaration exists;
- whether its elaborated type matches the claimed type;
- the transitive axiom set;
- whether submitted modules were built from source;
- whether any prebuilt artifact was used; and
- whether warnings were fatal.

Missing, noncanonical, duplicated, inconsistent, or digest-mismatched structured
output fails closed. `sorryAx`, `admit` through `sorryAx`, or any axiom outside
the profile’s explicit allowlist prevents `proved` status.

## 9. Compiler witness closure

A passing compiler witness cryptographically binds:

```text
claim_content_shake256_512
theorem_statement_shake256_512
proof_artifact_shake256_512
original_source_tree_shake256_512
immutable_snapshot_shake256_512
generated_witness_module_shake256_512
compiler_registry_shake256_512
lake_executable_shake256_512
lean_executable_shake256_512
lean_stdlib_tree_shake256_512
dependency_closure_shake256_512
execution_image_digest
sandbox_policy_shake256_512
verifier_binary_shake256_512
structured_result_shake256_512
build_output_shake256_512
```

It also binds the exact target, toolchain, command, axiom outcome, verifier,
key, signature, trusted timestamp source, and server time. The legacy
`compiler_executable_shake256_512` field equals the actual Lean executable digest; it
no longer labels Lake as the compiler.

## 10. Production request boundary

`executable/runtime/proof_check_service.py` connects the request-oriented API to
the protected runtime. A client provides claim data, a pre-ingested source-bundle
identifier, bundle-relative proof path, theorem name and statement, policy
reference, and governed compiler-profile identifier.

The request cannot contain executable paths, expected hashes, environment
variables, `created_at`, signatures, compiler conclusions, proof witnesses,
non-collapse approvals, lifecycle events, supersessions, or gates. Production
timestamps come from the authority service or a verified trusted-time witness.
Backdated or future-effective governance actions require explicit policy and
trusted-time evidence.

## 11. Governance-signed lifecycle and supersession

Draft 5.3.3 replaces unsigned lifecycle and generic supersession authority with:

- externally provisioned governance public-key registrations;
- signed governance authorization witnesses;
- signed `verifier_key_status_event/v2` records;
- signed `authority_supersession/v2` records; and
- signed authority-snapshot witnesses.

Each event binds the exact target, action, replacement when applicable, reason,
policy, authorization witness, effective time, recorded time, governance key,
payload hash, and signature. SQL verifies canonical JSON, ML-DSA-87 signature,
policy scope, authority principal, key validity, and target match before insert.

Unsigned Draft 5.3.2 v1 lifecycle rows remain historical evidence. They cannot
authorize a new 5.3.3 theorem gate. Terminal key states cannot be reactivated;
rotation creates a new key and signed event chain.

## 12. Deterministic authority replay

`wc_currently_valid_verifiers_v4` and `wc_authoritative_theorems_v2` are
convenience current-state views and may use database wall-clock time. They are
not canonical historical replay interfaces.

Historical evaluation creates a signed `authority_snapshot/v1` with explicit
`evaluated_at`. The views `wc_verifier_validity_as_of_v4` and
`wc_authoritative_theorems_as_of_v3` evaluate key windows, the latest signed
lifecycle event, signed supersessions, gate time, and signature bindings at that
fixed instant. Later revocation does not rewrite an earlier signed snapshot.

## 13. Theorem-promotion conjunction

An allowed theorem gate requires the same claim, theorem, artifact, policy,
proof, non-collapse transition, status transition, verifier, and key throughout,
plus all Draft 5.3.2 content/signature checks and these Draft 5.3.3 conditions:

1. governed compiler registry and valid profile;
2. immutable source snapshot matching the accepted source;
3. deterministic exact generated target;
4. clean source build with prebuilt/native artifacts rejected;
5. hermetic environment, no network, and enforced resource limits;
6. structured declaration/type/axiom inspection;
7. separate Lake, Lean, stdlib, dependency, verifier, sandbox, and image binding;
8. compiler-witness signature over every stored closure field;
9. signed governance authorization and latest signed active key event at gate
   time; and
10. no effective signed verifier, key, proof, compiler, or gate supersession.

A portable unit test, advisory check, or mocked runner is never a substitute for
a real governed-image result.

## 14. Non-collapse, replay, and positive-baseline mathematics

All 5.3.2 non-collapse and replay non-vacuity rules remain normative.
Computational evidence does not become theorem, policy approval does not become
fact, and identity transitions cannot equate protected categories such as
zero/absence, unknown/invalid, conjectural/theorem, or observation/proof.

The `positive-baseline-polygonal/v1` profile remains optional and
evidence-producing. Its boundary rule is:

```text
parent_input = child_codeword - child_baseline
```

An `even-payload-1` invariant requires runtime even-domain assertions at
construction, deserialization, child boundaries, and outputs. The type alone
does not enforce that restricted domain. Positive-baseline results follow the
ordinary proof and authority path if promoted.

## 15. Formal and executable assurance

The active TLA+ manifest includes ProofAuthority V2, V3, and V4. V4 models the
governed registry, bound toolchain, immutable clean build, structured inspection,
signed governance authorization, active key, recorded gate, and authority
snapshot relationship.

The portable suite uses simulated structured results to regression-test host
logic. It deliberately does not claim that Lean ran. The hermetic integration
runner executes real statement mismatch, comment-only declaration, `sorryAx`,
attributed axiom, stale `.olean`, and hostile project-metadata cases through the
approved image. If protected configuration or image is absent, that phase is an
authority-activation blocker.

Strict Lean and TLC remain external execution evidence. Formal models do not
prove the Python runtime, SQLite engine, cryptographic library, container
runtime, operating system, or deployment configuration correct.

## 16. Validation closure and disposition

Every required portable phase has exactly one descriptor identifier and one
report result. Missing, duplicate, failed, skipped, or unknown-status required
phases make the report fail. Optional strict phases are separately listed and
cannot be mistaken for completed evidence.

Draft 5.3.3 is a complete corrective development corpus. A deployment must keep
theorem authority disabled until its real hermetic Lean integration, applicable
strict checks, protected governance configuration, external trust anchor,
licensing decision, and human approval exist.

The contract remains permanently unfrozen after those conditions are met.
Future corrections create a new active draft and preserve this revision as
historical evidence.
