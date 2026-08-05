# Duotronics Witness Contract v1.6 — Draft 5.3.14 Review

## Executive verdict

Draft 5.3.14 materially closes the Draft 5.3.13 findings concerning:

- exact stale-cache envelope binding;
- event-schema validation;
- absent-artifact schema-registry regeneration;
- one-sided audit-log or checkpoint rollback;
- ordinary missing-state startup behavior;
- deadline propagation into the audit path;
- corrected current-revision documentation.

No path was found that returns an unauthorized cached or newly generated proof result.

The package is suitable to publish as a **permanently-not-frozen, non-authoritative corrective corpus**.

It is not ready for authority activation. The central remaining issue is that the local log/checkpoint construction is consistency-checkpointed but not independently rollback-resistant. Restoring a matching older log and matching older signed checkpoint is accepted. Segment ancestry and seal-capacity behavior also remain incomplete, and the request deadline is not a hard wall-clock bound around blocking file I/O.

All eight external activation gates remain incomplete, and authority remains correctly disabled.

---

## Independently verified

| Check | Result |
|---|---:|
| Submitted ZIP SHA-256 | `625126b9e223f08c0cbf9faf0895d6b6d61077a63bdf606d57d5bb45c89c7a2a` |
| ZIP integrity | Passed |
| ZIP entries | 2,018 |
| Regular files / inventory records | 1,838 |
| Directory entries | 180 |
| SHA-256-covered files | 1,834 |
| Recursive exclusions | 4 |
| Covered hash/size mismatches | 0 |
| Duplicate ZIP paths | 0 |
| Embedded ZIP files | 0 |
| Packaged runtime caches | 0 |
| Schemas compiled | 117 |
| Strict canonical schemas | 45 |
| Valid fixtures accepted | 45 |
| Adversarial fixtures rejected | 47 |
| Direct Python 3.13.5 tests | 290/290 |
| Direct warning-as-error tests | 290/290 |
| Direct warning lines | 0 |
| Packaged required validation | 94/94 |
| Packaged optional activation phases | 8 skipped |
| Current Python 3.12 claim | Explicitly unavailable |
| Theorem/promotion/release authority | Disabled |
| Freeze state | Permanently not frozen |

The four recursive exclusions are correct and carry both `sha256: null` and `size_bytes: null`:

1. `DRAFT5_3_14_VALIDATION_REPORT.json`
2. `PACKAGE_INVENTORY_v1_6_draft_5_3_14.json`
3. `refs/manifest/CHECKSUMS_v1_6_draft_5_3_14.sha256`
4. `refs/manifest/MANIFEST_v1_6_draft_5_3_14_complete.md`

The corrected Draft 5.3.14 registry generator reproduced the packaged registry byte-for-byte after the packaged registry was removed.

### Validator qualification

The direct normal and warning-free suites, schema validation, fixtures, registry regeneration, inventory, and manifest generation reproduced successfully under Python 3.13.5.

The packaged validation report records 94/94 required phases in 144.680136 seconds, and the packaged reliability record reports one complete run in 147.791212 seconds.

An independent complete clean workflow did not return before a 15-minute outer limit. It remained in `exact_test_discovery_count`, even though that phase completed in approximately 11 seconds when run directly from both the original and regenerated clean copies. Terminating the outer validator also left its isolated phase worker and regression child alive. This is recorded as an orchestration and cancellation-path qualification rather than a test failure.

---

# Confirmed improvements

## Stale-cache evidence v4

The current evidence binds:

- complete signed envelope payload digest;
- canonical full-envelope digest;
- original envelope signature;
- principal and idempotency slot;
- request and claim;
- policy and source;
- proof artifact;
- compiler-witness signed payload;
- historical registry and lineage chronology.

## Embedded event validation

The audit sink:

- allowlists event schema versions;
- validates events before append;
- canonicalizes and hashes the event;
- validates events again during startup replay;
- rejects unknown and outer/inner version-mismatched events.

## Missing state and one-sided truncation

Ordinary startup no longer creates a missing audit log or checkpoint. A log-only truncation, checkpoint-only rollback, missing log, malformed event, and mismatched checkpoint fail closed.

## Regeneration

`README.md` now invokes:

```text
python3 executable/validators/build_schema_registry_v5314.py
```

Removing the current registry and running that command reproduced the packaged registry SHA-256 exactly.

---

# High-severity findings

## H-01 — Coordinated rollback of both the log and checkpoint is accepted

**Activation blocker:** Yes.

### Evidence

Startup reconstructs the current log tail and compares it with the signed checkpoint:

- `proof_check_service.py:94-101`
- `proof_check_service.py:238-279`

The checkpoint is stored in a different directory, but:

- both paths remain below the same configured trust root;
- both are writable by the same service trust domain;
- both are signed by the same in-process audit key;
- no independently monotonic sequence or externally anchored expected tail is consulted.

Production enforces only that the two immediate parent directories differ:

- `proof_check_service.py:90-91`
- `proof_check_service.py:1774-1790`

### Independent reproduction

1. Provision the segment.
2. Append record 1.
3. Save the log and checkpoint bytes.
4. Append record 2.
5. Restore both saved record-1 files.
6. Restart the sink.

Result:

```text
coordinated rollback accepted sequence 1
```

### Impact

The implementation detects a mismatch between the two local files. It does not detect a coordinated restore of a previously valid pair.

Therefore the statements that old-segment restoration and checkpoint rollback are categorically rejected are too broad. The construction is not rollback-resistant against an actor or backup process able to restore both paths.

### Required correction

Use an independently protected monotonic anchor that the proof service cannot rewrite:

- remote append-only transparency service;
- WORM/object-lock storage;
- TPM/HSM monotonic state;
- root-owned helper with a narrower write protocol;
- governance-signed external tail checkpoints.

The service should verify:

- expected segment ID;
- expected sequence;
- expected tail;
- checkpoint epoch or monotonic counter;
- prior sealed-segment tail.

Different sibling directories under the same service-owned root are not sufficient by themselves.

---

## H-02 — Successor segments do not prove that their predecessor was sealed

**Activation blocker:** Yes.

### Evidence

`previous_sealed_segment_tail_sha256` is accepted when it is any lowercase 64-hex value:

- `proof_check_service.py:53`
- `proof_check_service.py:86-87`

Provisioning does not load or validate:

- the predecessor segment;
- the predecessor checkpoint;
- a terminal seal event;
- a governance-signed segment transition.

### Independent reproduction

A new segment was provisioned successfully with:

```text
previous_sealed_segment_tail_sha256 =
ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
```

without any predecessor segment or seal record.

### Impact

The successor binds a configured string, but does not establish that the string identifies an actual governed terminal seal.

The assurance statement that an unsealed successor or unrelated genesis cannot begin is procedural rather than enforced by the portable implementation.

### Required correction

Successor provisioning must consume and verify one of:

- predecessor sealed checkpoint plus terminal record;
- governance-signed segment transition attestation;
- externally anchored predecessor-tail statement.

Require a separately authorized genesis record when no predecessor exists.

---

## H-03 — A segment that reaches its configured capacity cannot be sealed

**Activation blocker:** Yes for dependable segment rotation.

### Evidence

Every append, including the terminal seal, is rejected when:

```python
sequence_before >= maximum_records
```

at `proof_check_service.py:344-347`.

`seal_segment()` uses the same append path:

- `proof_check_service.py:416-435`

Normal event publication is allowed to consume the final configured record slot. The same issue can occur when normal events leave insufficient byte capacity for the terminal seal record.

### Independent reproduction

With `maximum_records=1`:

1. append one valid event;
2. call `seal_segment()`.

Result:

```text
RuntimeError: cache audit segment is full and requires governed rotation
```

The segment is full but cannot perform the governed rotation operation required to leave that segment.

### Required correction

Reserve capacity for the terminal seal:

- distinguish event-record capacity from terminal-seal capacity;
- reject normal appends before the reserved seal slot or byte reserve is consumed;
- or permit one terminal seal beyond the normal event maximum.

Add exact record-count and byte-boundary tests.

---

## H-04 — Audit publication detects deadline overrun after blocking I/O rather than bounding it

**Activation blocker:** Yes for a strict request-wide deadline claim.

### Evidence

The code performs synchronous `fsync()` calls:

- audit record: `proof_check_service.py:389`
- checkpoint file: `proof_check_service.py:317`
- directories: `proof_check_service.py:324-331`

A regular-file `fsync()` has no userspace timeout.

After an audit-record fsync overruns the deadline, the implementation intentionally disables subsequent deadline checks so that it can complete checkpoint and directory persistence:

```python
deadline_monotonic=None if append_overran else deadline_monotonic
```

at `proof_check_service.py:391-396`.

This preserves local consistency but means the request deadline is not a hard execution bound.

### Independent reproduction

With:

- request deadline: 0.01 seconds;
- each injected fsync delay: 0.20 seconds;

the sink returned a timeout after approximately:

```text
0.812 seconds
```

The operation failed closed, but it exceeded the deadline by roughly 80 times.

### Impact

A stalled filesystem or audit device can block a request indefinitely, despite the stated deadline governance.

### Required correction

Move durable audit publication into a separately supervised process or service whose entire lifetime can be bounded. Use an idempotent event identifier so that ambiguous timeout completion can be safely reconciled.

If synchronous filesystem publication remains, documentation must distinguish:

- deadline-overrun detection;
- hard wall-clock bounded execution.

They are not the same guarantee.

---

# Medium-severity findings

## M-01 — Audit-log size is enforced only after the whole file is read

`_read_descriptor()` reads until EOF into memory:

- `proof_check_service.py:164-171`

Only afterward does `_verify_descriptor()` compare the result to `maximum_log_bytes`:

- `proof_check_service.py:185-189`

### Independent reproduction

A 5 MiB log was used with a configured maximum of 2 KiB.

The sink rejected it, but only after reading all:

```text
5,242,880 bytes
```

### Required correction

- check `fstat().st_size` before reading;
- stream with a hard byte counter;
- stop at `maximum_log_bytes + 1`;
- check the deadline during every read.

---

## M-02 — Failed checkpoint writes leave temporary files and an unrecoverable log/checkpoint mismatch

`_write_checkpoint()` creates a random temporary file but does not unlink it when write or fsync fails:

- `proof_check_service.py:306-322`

### Independent reproduction

A checkpoint-fsync failure left:

```text
.checkpoint.<random>.tmp
```

in the checkpoint directory.

The audit log contained the newly appended record while the checkpoint still described sequence zero.

### Impact

Repeated storage failures can accumulate temporary files. The segment then fails closed with log-ahead-of-checkpoint state, but no executable governed repair mechanism is supplied.

### Required correction

- unlink temporary files on every pre-replace failure;
- add a governed recovery tool for a fully signed dangling final record;
- record recovery as a signed audit event or external transition.

---

## M-03 — Audit signing identity has no governance registry or lifecycle

The production loader verifies:

- audit private/public keypair equality;
- separation from cache and compiler-witness keys.

It does not load a governance-signed audit-key registry containing:

- authorization scope;
- validity interval;
- status;
- revocation;
- rotation predecessor;
- historical verification keys.

Relevant loader region:

- `proof_check_service.py:1763-1790`

### Impact

Audit records and checkpoints identify a key ID and principal, but those identities are local configuration assertions rather than governance-authorized lifecycle records.

Audit-key rotation across segments is not independently verifiable.

### Required correction

Add a governance-signed `cache_audit_signing_registry` and bind its digest and validity decision into:

- audit records;
- checkpoints;
- segment seals;
- successor transition attestations.

---

## M-04 — Audit parent-directory protection is documentary rather than enforced

`_secure_parent()` verifies only that the immediate parent is a real directory:

- `proof_check_service.py:110-114`

Provisioning creates missing parent directories without a private mode argument. In an independent run, the created `segments` and `checkpoints` directories were mode `0755`.

The production loader requires distinct parent directories but does not verify their:

- owner;
- mode;
- full ancestry;
- independent mount or protection domain.

The private trust-root mode may provide effective protection in a correct deployment, but the audit sink itself does not enforce the documented directory policy.

---

## M-05 — External termination of the validator leaves isolated descendants alive

The validator has strong internal timeout cleanup, but no top-level SIGTERM/SIGINT cleanup for the currently active phase worker.

### Independent reproduction

The full validator was terminated immediately after its regression substage started.

Before termination:

```text
parent validator
phase worker
structured regression child
```

After the parent exited with SIGTERM, both descendants were still alive.

### Required correction

Install top-level signal handlers that terminate and reap the active phase worker process group and all enumerated escaped descendants before exiting.

---

## M-06 — Complete validator runtime was not independently reproducible in this environment

The isolated `exact_test_discovery_count` phase passed in approximately 11 seconds.

A complete clean validator run remained at that phase until a 15-minute outer limit and then left an orphaned worker. The packaged report and reliability evidence show successful approximately 145–148 second runs.

This appears intermittent or environment-sensitive. It does not invalidate the direct 290-test result, but the next revision should include repeated complete runs under an independent runner and test external cancellation paths.

---

# Production integration status

The production non-root harness remains correctly marked:

```text
environment_unavailable
```

The package accurately states:

- UID/GID 65534 was representable;
- `/proc` could not be bind-mounted into the chroot;
- fd-anchored SQLite could not execute;
- neither production loader is represented as passing.

This remains an activation blocker rather than a portable corpus defect.

---

# External activation gates

All eight remain incomplete:

1. strict Lean;
2. strict TLC;
3. governed hermetic Lean image execution;
4. signed OCI image build attestation;
5. signed verifier executable attestation;
6. reproducible inspector build attestation;
7. clean committed-source provenance;
8. external governance authorization.

---

# Recommended Draft 5.3.15 order of work

## P0 — Establish real rollback resistance

1. Add an external or independently monotonic audit-tail anchor.
2. Reject coordinated log/checkpoint rollback.
3. Governance-authorize genesis and every successor transition.
4. Verify the predecessor terminal seal during successor provisioning.

## P1 — Correct segment rotation boundaries

5. Reserve record and byte capacity for the terminal seal.
6. Add full-capacity and near-byte-limit rotation tests.
7. Add a governed recovery path for log-ahead-of-checkpoint failures.

## P2 — Make deadline claims exact

8. Move audit durability into a bounded supervised worker/service.
9. Stream and bound log reads.
10. Clean temporary checkpoint files on all failures.
11. Document whether the guarantee is hard wall-clock bounding or only fail-closed overrun detection.

## P3 — Govern audit authority

12. Add audit-key status, validity, rotation, revocation, and historical verification.
13. Bind audit registry identity into every audit artifact.

## P4 — Harden validator cancellation

14. Add SIGTERM/SIGINT descendant cleanup.
15. Repeat full validators under independent process supervisors.
16. Preserve cancellation and orphan-check evidence.

## P5 — Complete activation

17. Run the real non-root loader harness.
18. Complete all eight external gates.

---

# Publication recommendation

Draft 5.3.14 can be pushed as a non-authoritative corrective corpus.

Suggested release wording:

> Draft 5.3.14 closes the Draft 5.3.13 one-sided audit rollback, request-evidence binding, event-schema, and regeneration findings at the portable implementation level. The corpus remains permanently not frozen and non-authoritative. Authority activation remains blocked pending independently anchored rollback resistance, verified predecessor-seal transitions, seal-capacity-safe rotation, hard-bounded audit publication, successful real non-root production loading, and all eight external activation gates.
