# Duotronics Witness Contract v1.6 — Draft 5.3.13 Review

## Executive verdict

Draft 5.3.13 materially closes the three Draft 5.3.12 stale-cache findings:

- every current request, idempotency-slot, principal, claim, policy, source, artifact, result, and compiler-witness binding is checked before historical rotation classification;
- historical registry creation is required to precede the cache-signing time;
- production mode requires a dedicated-key signed audit sink and fails closed when publication fails.

No new path was found that returns an unauthorized cached or newly generated proof result.

The package is suitable to publish as a **permanently-not-frozen, non-authoritative development corpus**.

It is not ready for authority activation. The largest remaining portable issue is that the local audit chain is not rollback-resistant: valid-prefix truncation or complete deletion of the audit file is accepted as a shorter or new chain. A second activation-level issue is that audit publication is not governed by the request-wide deadline and can block indefinitely on the audit-file lock.

The documented schema-registry regeneration command is also incorrect and currently succeeds only because the correct Draft 5.3.13 registry is already present in the ZIP.

---

## Independently verified

| Check | Result |
|---|---:|
| Submitted ZIP SHA-256 | `6b9229cd3d463053328bed84ce59585638b74bd6e2193667e48af6863305f733` |
| ZIP integrity | Passed |
| ZIP entries | 1,958 |
| Regular files / inventory records | 1,783 |
| Directory records | 175 ZIP directory entries |
| SHA-256-covered files | 1,779 |
| Recursive exclusions | 4 |
| Covered hash/size mismatches | 0 |
| Embedded ZIP files | 0 |
| Packaged runtime-cache files | 0 |
| Schemas compiled | 112 |
| Strict canonical schemas | 42 |
| Valid fixtures accepted | 42 |
| Adversarial fixtures rejected | 44 |
| Direct Python 3.13.5 test evidence | 274/274 normal and warning-free |
| Packaged required validation | 89/89 |
| Packaged optional activation phases | 8 skipped |
| Current Python 3.12 claim | Explicitly unavailable |
| Theorem/promotion/release authority | Disabled |
| Freeze state | Permanently not frozen |

The four recursive exclusions are correctly represented with both `sha256` and `size_bytes` set to `null`:

1. `DRAFT5_3_13_VALIDATION_REPORT.json`
2. `PACKAGE_INVENTORY_v1_6_draft_5_3_13.json`
3. `refs/manifest/CHECKSUMS_v1_6_draft_5_3_13.sha256`
4. `refs/manifest/MANIFEST_v1_6_draft_5_3_13_complete.md`

The supplied Python 3.13.5 validator log and packaged validation report are internally consistent:

- 89 required phases passed;
- eight optional external phases skipped;
- 274 tests discovered and passed;
- zero required failures, skips, duplicates, or missing phases;
- zero surviving descendants in the completed packaged run.

### Independent validator qualification

The direct Python evidence generator reproduced:

- 274/274 normal tests;
- 274/274 warning-as-error tests;
- zero skips;
- zero warning lines.

Schema compilation, fixtures, inventory closure, and manifest generation also reproduced.

Two independent attempts to run the entire monolithic validator did not return within the review windows. Both remained inside repeated full regression phases rather than reporting a failed phase. Because the direct suites pass and the supplied complete log is coherent, this is recorded as a performance/reproducibility qualification rather than a confirmed validation failure.

---

# Draft 5.3.12 finding closure

## Closed

### Historical envelope transplantation

The historical replay branch now authenticates the envelope and then calls `_validate_cache_envelope_bindings()` before rotation classification.

The binding check covers:

- request SHA-256;
- request ID;
- idempotency key;
- authenticated principal;
- claim ID and claim-content hash;
- theorem hash through the outer result and compiler witness;
- compiler profile;
- policy ID and canonical policy hash;
- source bundle;
- proof artifact path;
- compiler-witness signature, signer, signed payload, result, and request bindings.

A transplanted historical envelope therefore fails as `cache_integrity_invalid` without stale evidence.

### Registry chronology

`_validate_snapshot_signing_evidence()` now requires:

```text
historical_registry.created_at <= cache_signed_at
```

Registry-lineage validation also requires the lineage creation time to be at or after every registry it references, and predecessor/successor registry creation remains strictly increasing.

### Durable production sink

Production mode rejects application construction without an evidence sink. The production loader creates a dedicated `SignedAppendOnlyAuditSink` using an audit keypair that must differ from both:

- the cache-envelope signing key; and
- the compiler-witness signing key.

Each append:

- takes an exclusive file lock;
- re-verifies the complete current chain;
- uses canonical JSON;
- signs the record;
- appends using `O_APPEND`;
- fsyncs the record file;
- enforces record-count and byte limits;
- fails closed through `cache_audit_publication_failed`.

Independent worker objects re-read the locked tail before selecting sequence and predecessor values.

---

# Remaining findings

## H-01 — The audit chain does not detect rollback, valid-prefix truncation, or deletion

**Severity:** High  
**Activation blocker:** Yes if the stale-cache audit trail is required evidence.

### Evidence

`SignedAppendOnlyAuditSink` verifies that the records currently present form a valid signed hash chain. It does not retain or verify an independently protected expected tail.

At startup it opens the configured path with `O_CREAT`. Therefore:

- a missing audit file is silently recreated as an empty chain;
- a file truncated to any valid signed prefix is accepted as a shorter valid chain;
- replacement by an older valid segment is not distinguishable from the current segment.

### Independent reproduction

A two-record valid audit log was truncated to its first complete signed record.

A new sink instance accepted it with:

```text
sequence = 1
```

The audit file was then deleted. A new sink instance recreated it and accepted:

```text
sequence = 0
```

No signing key was required to perform the truncation or deletion; only write access to the audit path was required.

### Impact

The current construction is hash-chained and alteration-evident for surviving records, but it is not rollback-evident or deletion-evident.

A same-UID sibling process, operator error, filesystem restore, or attacker able to modify the audit directory can erase the most recent rotation evidence without detection. A new valid branch can then begin from the shortened tail.

### Required correction

1. Separate audit-log provisioning from normal startup.
   - Production startup must not silently create a missing previously initialized segment.
2. Persist the expected sequence and tail hash in an independently protected checkpoint.
3. Prefer an external append-only or WORM/transparency service.
4. Chain every new segment to a governance-signed terminal record from the prior segment.
5. On startup require:
   - the log exists;
   - the segment identity is expected;
   - the sequence and tail equal the protected checkpoint;
   - no rollback to an earlier valid prefix occurred.
6. Treat missing, shortened, or replaced logs as `cache_audit_integrity_invalid`.

### Required regressions

- truncation to a valid prefix is rejected;
- complete file deletion is rejected;
- replacement with an older fully valid segment is rejected;
- segment rotation preserves a signed predecessor-tail binding;
- two workers cannot initialize competing genesis segments.

---

## H-02 — Stale-cache audit publication is outside the request-wide deadline

**Severity:** High  
**Activation blocker:** Yes for the request-wide timeout contract.

### Evidence

`handle()` checks the deadline before calling `_cached_result()` and after it returns.

For a historical row, `_cached_result()`:

1. validates the row;
2. calls the audit sink;
3. immediately raises `cache_key_rotation_requires_new_idempotency_key`.

Because it raises rather than returns, the post-call deadline check in `handle()` is never executed.

The audit sink itself:

- takes a blocking `flock(LOCK_EX)` with no timeout;
- scans and verifies the complete bounded log;
- writes and fsyncs with no remaining-budget parameter.

### Independent reproduction

With a governed request timeout of one second and an evidence sink delayed for 1.25 seconds, the service returned:

```text
cache_key_rotation_requires_new_idempotency_key
```

after approximately 1.25 seconds instead of returning a timeout or audit-publication failure.

### Impact

A stale-cache request can exceed its governed request budget and still return the rotation-specific response.

A worker holding the audit lock can also block another request beyond the deadline.

### Required correction

- Pass the monotonic deadline into `_cached_result`, `_publish_cache_evidence`, and the audit sink.
- Acquire `flock` using nonblocking attempts bounded by the remaining time.
- Check the deadline:
  - before lock acquisition;
  - after chain verification;
  - before append;
  - after file fsync;
  - after directory fsync.
- Return a stable timeout or `cache_audit_publication_failed` error when persistence cannot complete within budget.
- Bind audit-publication elapsed time into operational evidence.

---

## M-01 — The documented regeneration workflow builds the wrong schema registry

**Severity:** Medium  
**Release reproducibility issue:** Yes

### Evidence

`README.md` instructs:

```sh
python3 executable/validators/build_schema_registry_v5312.py
```

The package includes the correct current generator:

```text
executable/validators/build_schema_registry_v5313.py
```

The Draft 5.3.12 generator writes:

```text
refs/schema_registry_v1_6_draft_5_3_12.json
```

It does not generate the current Draft 5.3.13 registry.

### Independent reproduction

After removing:

```text
refs/schema_registry_v1_6_draft_5_3_13.json
```

and running the README command, the current registry remained absent.

The next documented command failed with `ENOENT` while opening the missing Draft 5.3.13 registry.

### Impact

The documented workflow validates already-packaged bytes but is not a complete from-source regeneration workflow for the current schema registry.

### Required correction

Replace the README command with:

```sh
python3 executable/validators/build_schema_registry_v5313.py
```

Add a required validator phase that:

1. copies the source tree;
2. removes the generated current registry;
3. runs the documented generator;
4. compares the regenerated bytes with the packaged registry.

---

## M-02 — The root README describes the predecessor revision’s changes and an obsolete harness limitation

**Severity:** Medium documentation issue

The root README says Draft 5.3.13 adds bounded validator capture/reaping and initial authenticated historical replay. Those were primarily Draft 5.3.12 changes.

It also says the sandbox cannot represent the intended non-root UID. The current integration evidence instead says UID/GID 65534 is representable, but bind-mounting `/proc` into the chroot is denied.

The release notes and corrective assurance report contain the correct Draft 5.3.13 description.

### Required correction

Update the root README to summarize:

- full request/slot binding before rotation classification;
- registry-existence chronology;
- stale-evidence v3;
- dedicated signed audit chain;
- the actual `/proc` mount limitation.

---

## M-03 — Audit records do not independently bind the exact cache envelope

**Severity:** Medium audit-hardening issue

`cache_stale_row_evidence/v3` includes:

- `cache_envelope_id`;
- request and witness bindings;
- signer and registry identities;
- signing and registry timestamps.

It does not include:

- the cache envelope’s `signed_payload_sha256`;
- a canonical full-envelope SHA-256;
- the envelope signature.

`cache_envelope_id` is derived from request SHA-256, principal, and compiler-witness signed-payload SHA-256. It is not a digest of the complete signed envelope.

### Impact

The signed audit record attests that envelope verification succeeded, but it is not independently sufficient to identify and re-verify the exact original envelope if the SQLite row is later lost or corrupted.

### Recommended correction

Add at least:

- `cache_envelope_signed_payload_sha256`;
- `cache_envelope_canonical_sha256`;
- optionally the original envelope signature.

Validate these before publishing the audit event.

---

## M-04 — Embedded audit events are canonical but not schema-validated during audit startup

**Severity:** Medium audit-hardening issue

Audit startup verifies:

- record schema;
- record signature;
- event canonical JSON;
- event digest;
- sequence and chain.

It does not dispatch `event_schema_version` to the corresponding event schema and validate the embedded event.

The current stale branch validates `cache_stale_row_evidence/v3` before publication, but current-cache replay evidence has no equivalent canonical schema enforcement in the sink.

### Recommended correction

- Maintain an allowlisted audit-event schema registry.
- Validate each event before signing and again during startup verification.
- Require `event_schema_version` to equal the embedded event’s `schema_version`.
- Reject unknown event versions.

---

# Production integration status

The non-root production harness remains correctly marked:

```text
environment_unavailable
```

The current evidence is more precise than the root README:

- UID/GID 65534 can be represented;
- the harness cannot bind-mount `/proc` into the chroot;
- fd-anchored SQLite therefore cannot execute there;
- neither production loader is represented as passing.

This is honest and fail-closed.

Before activation, execute the harness in an environment that provides:

- multiple real UIDs/GIDs;
- a secured `/etc/witness-authority`-style trust root;
- the required procfs projection or a replacement fd-anchored SQLite mechanism;
- actual calls to both production loaders;
- ownership and mode evidence for SQLite, WAL, SHM, audit log, and keys.

---

# External activation gates

All eight remain incomplete:

1. strict Lean;
2. strict TLC;
3. governed hermetic Lean-image execution;
4. signed OCI image build attestation;
5. signed verifier executable attestation;
6. reproducible inspector build attestation;
7. clean committed-source provenance;
8. external governance authorization.

The package correctly treats all eight as optional skipped phases and keeps theorem, promotion, and release authority disabled.

---

# Recommended Draft 5.3.14 order of work

## P0 — Make the audit trail rollback-evident

1. Add an externally protected audit-tail checkpoint.
2. Reject missing, truncated, or rolled-back audit segments.
3. Define signed segment sealing and rotation.
4. Add deletion, valid-prefix truncation, and old-segment replacement tests.

## P1 — Bound audit publication by the request deadline

5. Make lock acquisition deadline-aware.
6. Make verification, append, and fsync deadline-aware.
7. Return a stable fail-closed error on budget exhaustion.

## P2 — Repair regeneration and documentation

8. Use `build_schema_registry_v5313.py` in the README.
9. Add from-absent-artifact regeneration tests.
10. Update the README’s revision summary and actual harness limitation.

## P3 — Strengthen audit self-containment

11. Bind the exact cache-envelope digest into stale evidence.
12. Schema-validate embedded audit events at append and startup.

## P4 — Complete production and external gates

13. Run the real non-root loader integration.
14. Run strict Lean and strict TLC.
15. Build and execute the governed image.
16. Produce image, verifier, and inspector attestations.
17. Bind the committed repository source.
18. Obtain external governance authorization.

---

# Publication recommendation

Draft 5.3.13 can be pushed as a non-authoritative corrective corpus.

Suggested release wording:

> Draft 5.3.13 closes the Draft 5.3.12 stale-cache binding, historical-registry chronology, and durable audit-publication findings at the portable implementation level. The corpus remains permanently not frozen and non-authoritative. Authority activation remains disabled pending rollback-resistant audit anchoring, deadline-bounded audit publication, successful real non-root production-loader execution, and all eight external activation gates.
