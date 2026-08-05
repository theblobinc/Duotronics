# Duotronic Witness Contract v1.6 — Next-Revision Remediation Checklist

**Suggested target revision:** v1.6 Draft 5.3.5  
**Based on:** independent review of Draft 5.3.4  
**Purpose:** convert the review findings into implementation tasks, validation requirements, and release acceptance criteria.

## Release policy for the next revision

Until the critical and high-priority items below are complete and tested:

- keep `theorem_authority_default` disabled;
- do not claim governed OCI integration is operational;
- do not treat the portable validator as proof that sandbox controls actually ran;
- do not issue final build attestations for the trusted verifier image;
- continue to mark strict Lean, strict TLC, real-image integration, external signatures, and governance activation as incomplete when they have not actually run.

The intentionally absent governed image digest and externally built inspector binary may remain fail-closed during development. They must not be confused with the implementation defects below, which must be fixed before those artifacts can be safely activated.

---

# A. Critical release blockers

## A1. Correct OCI entrypoint and command dispatch

**Affected files**

- `executable/trusted_verifier/Containerfile`
- `executable/runtime/proof_authority.py`
- related runtime/unit/integration tests

**Problem**

The image declares `verify-lean` as its `ENTRYPOINT`, while the runtime appends the requested domain executable after the image name. This causes `compile-lean` or `verify-lean` to become arguments to the existing entrypoint instead of the executable being invoked. The intended untrusted compiler and trusted verifier domains therefore cannot be dispatched correctly.

**Required changes**

- Choose one authoritative command model:
  - preferably pass an explicit OCI `--entrypoint` override for each domain; or
  - remove the fixed image `ENTRYPOINT` and always supply the executable explicitly.
- Change the runtime command builder so `invocation.entrypoint` selects the executable and only `invocation.arguments` are appended as command arguments.
- Ensure the untrusted invocation executes only the compiler wrapper.
- Ensure the trusted invocation executes only the verifier/inspector wrapper.
- Prevent either domain from receiving the other domain’s executable path as an argument.
- Document the final command model in the contract, runtime README, and image README.

**Required tests**

- Evaluate the final OCI argv together with the actual `Containerfile` configuration.
- Test both untrusted and trusted domain commands.
- Assert that the first executable inside the container is exactly the expected domain executable.
- Add a real-image smoke test that proves each wrapper is reached independently.

**Done when**

A built image can execute both domain commands successfully, and the test suite proves that the actual executable selected in each domain matches the canonical invocation record.

---

## A2. Make the effective sandbox record identical to the controls actually applied

**Affected files**

- `executable/runtime/proof_authority.py`
- `executable/validators/validate_draft5_3_4_corpus.py` or its next-revision replacement
- sandbox policy/configuration files
- witness contract sandbox sections

**Problem**

The serialized and hashed `EffectiveSandboxInvocation` records controls such as seccomp, AppArmor, SELinux, user namespaces, and `/work` as the working directory, but the emitted OCI command does not apply all of them. The current digest can therefore describe a stronger sandbox than the one that actually ran. `security_properties` is also returned as a hard-coded declaration rather than measured or verified runtime state.

**Required changes**

- Use `EffectiveSandboxInvocation` as the single source of truth for command generation.
- Create a runtime-adapter layer that maps every declared control to a concrete Docker/Podman-compatible option.
- Apply the configured working directory explicitly.
- Apply or explicitly reject the configured seccomp profile.
- Apply or explicitly reject the configured AppArmor profile.
- Apply or explicitly reject the configured SELinux label/options.
- Apply or explicitly reject the configured user-namespace mode.
- Keep existing network, read-only filesystem, capability, privilege, mount, process, memory, CPU, and user controls in the same canonical model.
- Fail closed when the selected OCI runtime cannot support a required control.
- Hash the normalized effective argv plus the hashes of immutable policy files actually referenced by that argv.
- Separate requested controls, applied controls, and verified controls in the result model.
- Do not emit a security property as verified merely because it appeared in configuration.
- Capture runtime inspection evidence where the runtime supports it.
- Update the contract so it states exactly which properties are configuration-bound and which are runtime-measured.

**Required tests**

- For every effective control, assert that there is a concrete runtime flag, a verified immutable default, or an explicit fail-closed rejection.
- Compare the canonical invocation serialization with the emitted OCI argv.
- Mutate each control and verify the invocation digest changes.
- Remove runtime support for a required control and verify startup/execution fails closed.
- Run real-container inspection tests for user, working directory, mounts, network, read-only root, capabilities, and security profiles where the platform exposes them.

**Done when**

The signed invocation digest represents the exact command and policy files used, and no witness claims a security property that was neither applied nor verified.

---

## A3. Resolve, authorize, and cryptographically bind `policy_decision_id`

**Affected files**

- `executable/runtime/proof_check_service.py`
- `executable/runtime/proof_authority.py`
- OpenAPI request/response schemas
- compiler/verifier witness schemas
- policy storage/resolution layer
- deterministic identity and signature code

**Problem**

`policy_decision_id` is required and echoed, but it is not resolved to a policy record, checked for authorization, passed into proof verification, included in the compiler witness, or covered by the signature. A successful result can therefore be relabeled with another policy ID without changing the authority calculation.

**Required changes**

- Add a policy resolver at the request boundary.
- Validate identifier syntax and canonical identity.
- Resolve an immutable policy decision record.
- Verify status, scope, authority, effective time, expiry/revocation state, subject, operation, compiler/verifier profile, and resource permissions as applicable.
- Compute or retrieve a canonical hash for the resolved policy record.
- Pass the policy decision ID and canonical record hash into `ProofAuthorityService.verify()`.
- Include both values in the canonical verifier request.
- Include both values in the signed verifier result.
- Include both values in the compiler witness and deterministic witness identity.
- Reject unresolved, revoked, expired, out-of-scope, or unauthorized decisions before starting OCI execution.
- Prevent an outer API wrapper from replacing the bound policy ID after verification.
- Define behavior for policy supersession and replay.

**Required tests**

- Valid authorized policy succeeds.
- Unknown, malformed, revoked, expired, and out-of-scope policies fail before execution.
- Changing only the policy ID or policy hash changes the signed request/result and witness ID.
- A response cannot be relabeled with another policy ID and still validate.
- Replay resolves the same immutable policy record or explicitly reports supersession.

**Done when**

Every accepted proof result is inseparably bound to the exact authorized policy decision that permitted it.

---

# B. High-priority implementation and security work

## B1. Add a reproducible build target for the trusted Lean inspector

**Affected files**

- `formal/draft5_3_4/lean/WitnessAuthority/Verifier.lean` or next-revision path
- Lake configuration and Lean package files
- `executable/formal/run_lean_build.py`
- `executable/trusted_verifier/Containerfile`
- `executable/trusted_verifier/README.md`
- build-attestation schemas and generators

**Required changes**

- Create a dedicated Lake executable target for the trusted inspector.
- Add a concrete `main` entrypoint and stable CLI contract.
- Pin the Lean/Lake/toolchain version used to build it.
- Add a reproducible build script or pinned multi-stage container build.
- Make strict Lean validation compile the exact inspector target, not only the main `Duotronic` package.
- Test the inspector against positive, negative, malformed, and adversarial fixtures.
- Record the source-tree hash, build command, toolchain identity, dependency lock state, output binary hash, and image layer/build identity in the build attestation.
- Ensure the binary copied into the final trusted image is the same binary covered by the attestation.

**Done when**

Strict Lean validation proves the trusted inspector source compiles, a reproducible process produces the expected binary, and the final image contains the attested binary hash.

---

## B2. Measure the actual OCI runtime version and reject root execution

**Affected files**

- `executable/runtime/proof_authority.py`
- protected runtime configuration
- startup validation tests

**Required changes**

- Execute a deterministic runtime-version command at service startup.
- Normalize and compare the measured version to the governed expected runtime identity.
- Optionally bind both executable digest and normalized version output hash.
- Do not accept a configured version string as evidence of the installed runtime version.
- Require explicitly configured non-root UID and GID for the authority domains.
- Reject UID `0` or GID `0`.
- Do not default trusted execution to the service process identity when it may be root.
- Preserve the non-root image user unless an explicitly governed non-root override is supplied.
- Add startup tests under root and non-root host contexts.

**Done when**

Startup fails closed on runtime-version mismatch or root domain identity, and witnesses bind the measured runtime identity.

---

## B3. Make source snapshot traversal race-resistant and resource-bounded

**Affected files**

- source enumeration/snapshot functions in `executable/runtime/proof_authority.py`
- request limits/configuration
- security and adversarial tests

**Required changes**

- Open the source root once and retain a directory file descriptor.
- Traverse child components relative to directory FDs with `openat`/`openat2` or the safest platform-equivalent mechanism.
- Apply no-follow semantics to every path component, not only the final file.
- Verify file type, ownership/permissions as required, link count where relevant, and containment beneath the approved root.
- Detect replacement between enumeration and read.
- Add aggregate limits for:
  - total files;
  - total directories;
  - total source bytes;
  - individual file bytes;
  - maximum path depth;
  - maximum path length;
  - maximum directory entries;
  - snapshot wall-clock time.
- Stream file hashing and copying instead of reading whole files into memory.
- Reject special files, devices, sockets, FIFOs, and unsupported hard links.
- Define deterministic ordering and path normalization.

**Required tests**

- Parent-directory symlink swap race.
- Final-component symlink.
- Deep tree, huge file count, oversized aggregate content, long paths, sparse files, and special files.
- Mutation during snapshot.
- Duplicate/case-colliding normalized paths on relevant platforms.

**Done when**

An attacker who can mutate the submitted source tree cannot escape the source root or substitute content, and host resource use is bounded before container execution begins.

---

## B4. Bound subprocess output while it is produced

**Affected files**

- host OCI subprocess calls in `executable/runtime/proof_authority.py`
- `executable/trusted_verifier/compile_lean.py`
- `executable/trusted_verifier/verify_lean.py`

**Required changes**

- Replace `capture_output=True` for untrusted or potentially noisy processes.
- Stream stdout and stderr into capped pipes/files.
- Enforce separate and combined output quotas.
- Terminate the child when a quota is exceeded.
- Retain a bounded diagnostic prefix or tail plus a hash of the full retained stream policy.
- Record `output_limit_exceeded` distinctly from compiler/verifier failure.
- Set limits at both host-runtime and in-container wrapper layers.
- Ensure timeouts terminate process groups and descendants, not only the immediate process.

**Done when**

No compiler, verifier, inspector, or OCI runtime process can force unbounded host memory use through output.

---

## B5. Make the schema registry authoritative and complete

**Affected files**

- `refs/schema_registry_v1_6_draft_5_3_4.json` or next-revision registry
- all files under `schemas/`
- schema validators and fixture runners
- OpenAPI/schema references

**Required changes**

- Classify every schema as one of:
  - canonical;
  - legacy compatibility;
  - archival/historical;
  - experimental/research;
  - forbidden/removed.
- Add an explicit lifecycle/status field and active-version scope.
- Make the validator load schema sets from the registry rather than blindly walking the directory.
- Reject unclassified schemas on active API, persistence, witness, and write surfaces.
- Decide and document the status of the following currently unclassified schemas:

  `authority_delegation_chain`, `authority_signature_binding_v1`, `authority_supersession_v1`, `claim_status_transition`, `composition_policy`, `compound_claim_witness`, `conflict_adjudication_witness`, `corpus_rule_resolution_witness`, `execution_trace`, `inference_witness`, `kernel_error_witness`, `kernel_state`, `kernel_transaction`, `logical_memory_cell`, `logical_observer_profile`, `nla_activation_witness`, `nla_self_training_witness`, `non_collapse_state`, `observer_capability_token`, `observer_task`, `policy_decision_evidence_extension`, `pragmatic_context`, `replay_sign`, `resource_budget_witness`, `task_frame`, `task_result_witness`, `task_step_witness`, `temporal_scope_witness`, `verifier_key_status_event_v1`, `verifier_key_status_event_v2`.

- Add positive and negative Draft 5.3.5 fixtures for every canonical authority schema.
- At minimum, add missing fixture coverage for:
  - `governance_authority_v1`;
  - `governed_compiler_registry_v2`;
  - `lean_verifier_result_v2`.
- Either register or remove active fixtures for:
  - `authority_signature_binding_v1`;
  - `authority_supersession_v1`;
  - `verifier_key_status_event_v1`;
  - `verifier_key_status_event_v2`.
- Run AJV in strict mode where possible.
- Document any schema requiring a strict-mode exception and test that exception explicitly.
- Validate that all `$id`, `$ref`, version, and registry paths are unique and resolvable.

**Done when**

Every schema has an explicit governed status, every canonical schema has valid and invalid fixtures, and active validation behavior is derived from the registry.

---

## B6. Align OpenAPI with the actual proof-check service

**Affected files**

- `executable/openapi/draft5_3_4_evidence_language_openapi.yaml` or next revision
- `executable/runtime/proof_check_service.py`
- application adapter/router
- generated client/conformance tests

**Decision required**

Choose one canonical API model:

1. **Asynchronous model:** `POST /v2/proof-checks` returns HTTP 202 and a `ProofCheckJob`; `GET /v2/proof-checks/{job_id}` returns lifecycle/status/results.
2. **Synchronous model:** `POST /v2/proof-checks` blocks and returns the canonical proof-check result directly, with documented timeout and retry behavior.

**Required changes**

- Implement the selected model exactly.
- Remove schemas/routes from OpenAPI that are not implemented, or implement them.
- Make status codes and response bodies match the specification.
- Define idempotency, retry, timeout, cancellation, and duplicate-submission semantics.
- Ensure policy resolution and authority binding occur in the documented request lifecycle.
- Add end-to-end OpenAPI conformance tests against the actual application adapter.
- Validate emitted examples against the schema.

**Done when**

A generated client can call the running service and receive responses that conform exactly to the canonical OpenAPI contract.

---

# C. Medium-priority consistency, packaging, and provenance work

## C1. Update all root entrypoints and version references

**Affected files**

- `README.md`
- `START_HERE.md`
- package metadata
- canonical corpus descriptor
- release notes/indexes
- validator command examples
- any `5.3.3` or stale `5.3.4` strings after the next version is selected

**Required changes**

- Update the root README from Draft 5.3.3 to the next revision.
- Point to the correct contract, descriptor, validator, report, and package metadata.
- Search the active corpus for stale version strings and obsolete filenames.
- Distinguish intentional historical references from active pointers.
- Extend version-consistency validation to every designated entrypoint document, not a small allowlist.
- Prefer deriving repeated filenames/version pointers from the canonical descriptor or generator inputs.

**Done when**

A new user following only the root README reaches and validates the active revision without encountering stale paths.

---

## C2. Fix recursive manifest/inventory metadata

**Affected files**

- `executable/validators/build_draft5_3_4_manifests.py` or next-revision generator
- package inventory schema/data
- checksums and human manifest generators
- corpus validator

**Required changes**

- Decide how self-referential generated artifacts are represented.
- Recommended approach: exclude only their cryptographic self-hashes while still validating nonrecursive metadata that can be stable.
- For recursive values that cannot be stable, omit them or set them explicitly to `null` with an exclusion reason.
- Alternatively, implement a deterministic fixed-point/two-pass generation process if the format permits it.
- Do not record stale `size_bytes` values.
- Validate actual sizes for excluded artifacts when size is declared.
- Record why each file is excluded and which fields are excluded.
- Add a post-generation verification pass that opens the final packaged files, not pre-write in-memory values.

**Done when**

Every declared size matches the final file, and every excluded field is explicitly justified rather than silently skipped.

---

## C3. Correct the sandbox-template mount terminology and semantics

**Affected files**

- `executable/runtime/proof_authority.py`
- sandbox invocation/template schema
- contract diagrams and prose
- related tests

**Required changes**

- Replace `trusted_result_mount: true` with a term that describes the actual private inspection output mount, such as `trusted_inspection_mount: true`.
- Keep final signed-result storage absent from both containers.
- Define each mount by source, destination, mode, domain, purpose, and lifecycle.
- Add a schema for the sandbox template.
- Assert semantic equivalence between the high-level template and the concrete mount manifest.
- Ensure mount names cannot imply authority access that does not exist.

**Done when**

The template, contract, concrete OCI command, and signed mount manifest all describe the same filesystem architecture.

---

## C4. Bind the final package to exact source provenance

**Clarification incorporated**

Draft 5.3.4 not appearing in the GitHub repository is expected because the repository update has not been pushed yet. The fix is not to publish an unfinished draft. The fix is to make the final next-revision package identify the exact source state from which it was built.

**Affected files**

- package metadata
- canonical corpus descriptor
- release manifest
- validator
- release/build workflow

**Required changes**

- Add:
  - `source_repository`;
  - `source_ref` or release tag;
  - `source_commit_sha`;
  - `source_subtree_path`;
  - `source_subtree_sha256` or Git tree identity;
  - generator name/version/hash;
  - source generation/base revision;
  - transformation/change-set identity;
  - clean/dirty workspace status.
- Build the release from a clean, committed source state.
- Verify the recorded commit exists and the subtree content matches the package inputs.
- Avoid circular provenance:
  - recommended two-step process: commit source changes first, generate the package referencing that source commit, then commit/tag release artifacts separately; or
  - define a canonical source-tree digest that excludes generated self-referential release metadata.
- For local development packages, explicitly label provenance as `unpublished_workspace` and do not treat them as final release artifacts.

**Done when**

Anyone can check out the recorded source commit, run the governed generator, and reproduce or explain every active file in the release package.

---

# D. Low-priority cleanup

## D1. Close SQLite connections in tests

**Affected files**

- `executable/tests/test_sql_authority_lifecycle_v533.py`
- related fixtures/helpers

**Required changes**

- Use context managers or explicit `close()` calls.
- Ensure rollback/cleanup occurs on test failure.
- Run CI with `ResourceWarning` promoted to an error.

**Done when**

The full test run emits no unclosed-database warnings.

---

## D2. Repair or isolate broken links in vendored AJV documentation

**Affected files**

- vendored AJV README/package documentation
- link checker configuration

**Required changes**

- Either vendor the complete upstream documentation set or exclude vendored documentation from first-party link checks.
- Keep dependency integrity checks separate from first-party documentation quality checks.

**Done when**

The link checker reports no unexplained failures and does not treat intentionally incomplete vendored docs as first-party release defects.

---

# E. Validator and test-suite changes required for the next revision

Add the following release gates. Names may be adapted to the project’s naming conventions.

## OCI and sandbox gates

- `test_oci_argv_matches_effective_invocation_for_both_domains`
- `test_container_entrypoint_is_overridden_or_absent`
- `test_untrusted_domain_executes_only_compile_wrapper`
- `test_trusted_domain_executes_only_verify_wrapper`
- `test_every_effective_control_has_runtime_flag_verified_default_or_rejection`
- `test_effective_invocation_digest_changes_for_each_control`
- `test_runtime_inspection_matches_declared_security_properties`
- `test_trusted_domain_rejects_uid_gid_zero`
- `test_runtime_version_is_measured_not_config_echoed`

## Policy-authority gates

- `test_policy_decision_is_resolved_before_execution`
- `test_policy_decision_scope_and_status_are_enforced`
- `test_policy_decision_and_record_hash_are_signature_bound`
- `test_policy_relabeling_invalidates_result`
- `test_revoked_or_expired_policy_fails_closed`

## Formal/build gates

- `test_strict_lean_build_includes_trusted_inspector_executable`
- `test_inspector_cli_positive_negative_and_malformed_fixtures`
- `test_attested_inspector_hash_matches_image_binary`
- `test_reproducible_inspector_build_from_pinned_toolchain`

## Filesystem/resource gates

- `test_source_snapshot_parent_component_symlink_race`
- `test_source_snapshot_rejects_special_files`
- `test_source_snapshot_total_file_limit`
- `test_source_snapshot_total_byte_limit`
- `test_source_snapshot_depth_and_path_limits`
- `test_subprocess_output_limit_terminates_process_group`
- `test_host_and_container_output_limits_are_consistent`

## Schema/API gates

- `test_every_schema_is_registry_classified`
- `test_unclassified_schema_cannot_enter_active_surface`
- `test_every_canonical_schema_has_valid_and_invalid_fixtures`
- `test_schema_ids_and_refs_are_unique_and_resolvable`
- `test_openapi_proof_check_response_matches_application`
- `test_all_openapi_routes_have_runtime_implementations`
- `test_runtime_examples_validate_against_openapi`

## Packaging/documentation gates

- `test_all_entrypoint_documents_match_active_version`
- `test_no_unapproved_stale_active_version_references`
- `test_excluded_manifest_metadata_is_self_consistent`
- `test_final_package_inventory_matches_final_bytes`
- `test_package_metadata_binds_upstream_commit_and_subtree`
- `test_release_is_generated_from_clean_source_state`
- `test_no_resource_warnings`

The validator should fail when these gates are skipped for a release profile that claims the corresponding capability. Development profiles may mark them incomplete, but must not report them as passed.

---

# F. Recommended revision workflow

## Phase 1 — Core fixes

1. Fix OCI entrypoint dispatch.
2. Refactor command generation around the canonical effective invocation.
3. Bind policy decisions into authorization, signatures, and witness identity.
4. Add the trusted inspector build target.
5. Harden source traversal and output/resource handling.
6. Select and implement the canonical synchronous or asynchronous API model.

## Phase 2 — Governance and consistency

7. Complete the schema registry and fixtures.
8. Correct sandbox mount terminology.
9. Update the contract and all active documentation to match actual runtime semantics.
10. Add source provenance fields and a noncircular release workflow.
11. Repair manifest generation and final-byte validation.

## Phase 3 — Validation

12. Add the new unit, adversarial, conformance, and real-image tests.
13. Run Python tests with warnings as errors.
14. Run schema validation in strict mode with documented exceptions.
15. Run strict Lean including the trusted inspector target.
16. Run strict TLC with the governed toolchain.
17. Build the exact OCI image and run real two-domain integration tests.
18. Inspect the running container controls and compare them to the signed invocation.

## Phase 4 — Release generation

19. Commit the source revision intended for release.
20. Generate the package from a clean checkout of that commit.
21. Record source commit/subtree and generator identity.
22. Generate inventories, checksums, reports, and human manifests in their final order.
23. Run a final validation pass against the packaged bytes.
24. Produce build attestations and external signatures only from the final governed artifacts.
25. Enable theorem authority only if all mandatory activation gates pass.

---

# G. Minimum acceptance bar for the next revision

The next revision should not be considered activation-ready unless all of the following are true:

- the two OCI domains execute the intended binaries;
- the canonical sandbox record equals the effective runtime command and applied controls;
- root execution is rejected;
- the actual OCI runtime identity is measured;
- policy authorization is resolved and signature-bound;
- the trusted Lean inspector is reproducibly built and included in strict validation;
- source traversal and subprocess output are bounded against hostile inputs;
- OpenAPI and runtime behavior conform end to end;
- every schema is registry-classified and every canonical authority schema has positive and negative fixtures;
- all active documentation points to the new revision;
- package inventory metadata matches the final packaged bytes;
- the final package identifies the exact source commit/subtree from which it was generated;
- strict Lean, strict TLC, real-image integration, build attestation, and external governance gates are either truly passed or explicitly marked incomplete;
- `theorem_authority_default` remains disabled unless every required activation gate genuinely passes.

