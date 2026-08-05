## Review verdict

Draft 5.3.5 is a substantial improvement over Draft 5.3.4.

I independently confirmed:

* ZIP SHA-256: `6a417c9363f29867b5dadafd8ac484b9e43371d451049cb7391a31669f96390c`
* 1,427 packaged files
* 1,423 hash-covered files
* Four properly documented recursive exclusions with both `sha256` and `size_bytes` set to `null`
* Zero covered-file hash or size mismatches
* All 32 required validation phases pass from a fresh extraction
* All 112 Python tests pass with warnings treated as errors
* 81 registered schemas, of which 79 JSON schemas compile
* 30 canonical strict schemas
* 30 valid and 32 adversarial fixtures behave as expected
* Retained Draft 5.2.2 through Draft 5.3.4 archives pass their integrity checks
* Authority remains correctly disabled

**Draft 5.3.5 is suitable to push as a living, non-authoritative draft corpus.** It is not ready for theorem-authority activation.

The description that OCI, policy, inspector, and API issues are “corrected” should be softened to **“materially remediated, with activation-level closure still pending.”**

## Critical issues

### 1. Dependency-policy result is schema-invalid and not enforced

`InspectorMain.lean` emits:

```json
"opaque_dependency_policy_result": true
```

But both canonical schemas require:

```json
"opaque_dependency_policy_result": "passed"
```

or `"failed"` / `"not_evaluated"`.

The Boolean is copied into the verifier result, and neither the trusted wrapper nor the host authority requires this policy result to equal `"passed"` before declaring success.

There are deeper related gaps:

* The inspector sets the opaque-dependency policy to true whenever the declarations exist.
* It does not perform a separately defined opaque/native/foreign dependency-policy evaluation.
* `transitive_dependencies_root` is only a hash of the direct type dependencies plus axiom set, not a recursively computed dependency closure.
* Unsafe inspection covers the theorem and constants appearing directly in its type, not the entire declaration dependency graph.

**Required fix:** implement a full recursive dependency inspection, emit the canonical string enum, require `"passed"` at every pass gate, and schema-validate the real inspector result before signing.

### 2. The signed sandbox invocation does not bind the actual OCI command

`EffectiveSandboxInvocation.sha256` hashes the logical dataclass, but `_command()` accepts a separate `runtime_mounts` argument.

I reproduced two different OCI commands—with different host source paths, mount modes, and an additional undeclared mount—that had the **same invocation SHA-256**.

The invocation also omits command-affecting details such as:

* hard-coded tmpfs mounts and sizes;
* host mount bindings;
* stdout, stderr, and combined output quotas.

This contradicts the contract statement that the normalized effective argv determines the invocation digest.

**Required fix:** generate logical mounts and runtime mounts from one sealed object, reject all divergence, and bind the complete normalized executed argv into the signed result.

## High-priority issues

### 3. The inspector claims `isDefEq` but never executes it

`Verifier.lean` defines `inspectDeclaration`, which correctly calls `isDefEq`. `InspectorMain.lean` does not call that function.

Instead it:

* sets `declaration_type_matches` to true whenever both declarations exist;
* pretty-prints both types with `toString`;
* hashes those strings;
* requires string-hash equality at the host layer.

The generated binding module still provides an important Lean type-checking gate, so this is not the same as accepting an arbitrary mismatched theorem. However, the witness inaccurately claims governed definitional equality and gives pretty printing authority that the contract explicitly denies.

**Required fix:** invoke `inspectDeclaration` in `MetaM` and replace pretty-print hashes with a stable structural expression fingerprint.

### 4. Signed policy resource limits are ignored

The policy schema requires:

* `maximum_timeout_seconds`
* `maximum_source_bytes`

The resolver verifies policy identity, status, time, subject, operation, compiler profile, and bundle scope, but does not apply these resource permissions.

Execution still uses:

* a default 600-second timeout;
* the global 512 MiB snapshot limit.

A signed policy allowing only one byte or one second would therefore not be enforced.

**Required fix:** place validated resource limits in `ResolvedPolicyDecision`, derive effective limits from policy/profile/deployment maxima, and bind those limits into the request, sandbox invocation, result, witness, and semantic identity.

### 5. API and server-generated objects are not schema-validated

The synchronous OpenAPI model is now aligned at a high level, but the implementation does not enforce the full request schema.

The application boundary does not directly validate all OpenAPI types and limits, including:

* `claim_id`
* `canonical_claim`
* `subject_id`
* `compiler_profile_id`
* normalized POSIX proof paths

The authority service also does not require `claim_id` to be a string or `canonical_claim` to be an object.

No production code validates the completed:

* verifier result;
* compiler witness;
* proof-check service result

against their canonical schemas before signing or returning them.

The current API conformance test checks only whether required keys are present, not whether the complete response conforms to the schema.

**Required fix:** perform local, fail-closed JSON Schema validation at every trust boundary and before every signature.

### 6. Some “measured” controls are still configured or ambiguous

Examples:

* `applied_controls` is set equal to `requested_controls` before runtime execution.
* `supported_controls` defaults to all required controls without a platform capability probe.
* `environment_allowlist` is verified by comparing the invocation field to a hard-coded list, not by inspecting the actual wrapper environment.
* The image defines `PYTHONPATH`, but this is absent from the declared environment allowlist.
* A missing `/sys/class/net` directory produces an empty interface set, which incorrectly satisfies the current `network_none` subset test.
* AppArmor and SELinux are both mandatory and both inferred from the same `/proc/self/attr/current` value.
* `result_channel_isolated` is inserted host-side when structured output exists rather than being associated with a dedicated observed or derived evidence record.

**Required fix:** distinguish requested, emitted, accepted, and measured controls; treat missing observations as unverified; and create governed platform-specific LSM profiles.

## Medium-priority issues

### 7. The compile handoff manifest is never consumed

`compile_lean.py` writes `compile-manifest.json`, but no trusted component reads it.

The trusted inspector does import with trust level zero. The pinned Lean source confirms that the third `importModules` argument is the trust level, and the inspector passes `0`; Lean documents that only trust levels greater than zero assume imported constants are correct. Therefore, I am **not** carrying forward the earlier suspected “imports automatically trust the untrusted `.olean`” issue.  ([GitHub][1])

However, the exact `.olean` set and artifact hashes are still not bound for replay and forensic purposes.

The trusted domain should validate the handoff manifest, exact file set, paths, modes, and hashes.

### 8. Idempotency is process-local and unbounded

Completed and in-flight requests are retained in unbounded in-memory dictionaries.

This means:

* restarts lose idempotency;
* multiple workers can duplicate execution;
* memory use grows indefinitely;
* a dead worker can leave waiters blocked;
* keys are not scoped by authenticated principal.

Use a bounded durable idempotency store with atomic claim/completion, retention, stale-inflight recovery, and request-hash binding.

### 9. The one-megabyte file-size limit also applies to compilation

The untrusted compiler receives the same 1 MiB `RLIMIT_FSIZE` associated with result publication.

A legitimate `.olean` file can exceed that size, causing valid larger projects to fail during real-image execution.

Use separate limits for:

* individual compiler artifacts;
* total handoff size;
* trusted inspection output;
* final result publication.

### 10. Trust-root coverage is broader in the contract than in the loader

The contract states that descriptor-relative trusted loading covers migrations, the inspector executable, image metadata, and dependency manifests.

The production loader directly secures configuration, keys, registries, OCI runtime, and seccomp profile, but not every artifact listed in that statement.

Either extend the trusted loader/attestation resolver or narrow the contract to distinguish direct trusted-root loading from signed-attestation verification.

## Status of the original remediation list

| Draft 5.3.4 remediation               | Current status             |
| ------------------------------------- | -------------------------- |
| OCI entrypoint dispatch               | Resolved structurally      |
| Sandbox flags and observations        | Partially resolved         |
| Policy ID and hash binding            | Resolved                   |
| Policy resource enforcement           | Still missing              |
| Trusted inspector target              | Resolved structurally      |
| Inspector semantics                   | Still incomplete           |
| Runtime identity and non-root domains | Resolved structurally      |
| Snapshot traversal and limits         | Resolved in portable tests |
| Bounded subprocess output             | Resolved in portable tests |
| Schema classification                 | Resolved                   |
| Synchronous OpenAPI model             | Mostly resolved            |
| Runtime schema enforcement            | Still missing              |
| README/version references             | Resolved                   |
| Recursive manifest metadata           | Resolved                   |
| Inspection/result mount terminology   | Resolved                   |
| Committed-source provenance           | Correctly pending          |
| SQLite warning cleanup                | Resolved                   |
| Required link checks                  | Passing                    |

## Publication recommendation

The package can be pushed now with its current authority-disabled status.

Suggested summary wording:

> Draft 5.3.5 materially remediates the Draft 5.3.4 portable implementation defects. Full activation closure remains pending production-shape schema validation, complete dependency-policy inspection, exact executed-argv binding, policy resource enforcement, real governed-image execution, strict Lean/TLC verification, reproducible build attestations, committed-source provenance, and external governance authorization.

## Files

* [Detailed Draft 5.3.5 review](sandbox:/mnt/data/duotronics_v1.6_draft_5.3.5_review.md)
* [Machine-readable findings](sandbox:/mnt/data/duotronics_v1.6_draft_5.3.5_findings.json)
* [Fresh 32-phase validator output](sandbox:/mnt/data/draft535_fresh_validator.log)
* [Complete 112-test output](sandbox:/mnt/data/draft535_all_tests.log)

[1]: https://github.com/leanprover/lean4/blob/master/src/Lean/Environment.lean "https://github.com/leanprover/lean4/blob/master/src/Lean/Environment.lean"
