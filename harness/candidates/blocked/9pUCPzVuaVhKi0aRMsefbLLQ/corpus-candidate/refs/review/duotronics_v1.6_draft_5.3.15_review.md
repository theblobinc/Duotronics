# Duotronics Witness Contract v1.6 — Draft 5.3.15 Review

## Executive verdict

Draft 5.3.15 is a major architectural improvement over Draft 5.3.14.

It materially closes the earlier portable findings concerning:

- proof-service possession of the audit private key;
- request-thread blocking on durable audit I/O;
- local coordinated log/checkpoint rollback by the proof service;
- successor-segment governance inputs;
- terminal-seal capacity;
- bounded log reads;
- temporary checkpoint cleanup;
- audit-signing registry introduction;
- storage ancestry checks;
- validator external-cancellation cleanup;
- real non-root production-loader construction.

No path was found that returns an unauthorized cached or newly generated proof result.

The package is suitable to publish as a **permanently-not-frozen, non-authoritative corrective corpus**.

It is **not ready for authority activation**. The remaining portable findings are concentrated in the new audit service boundary:

1. audit-key lifecycle evidence is not re-evaluated when records and receipts are created or replayed;
2. the publisher and anchor Unix-socket servers do not authenticate connecting processes;
3. the portable file-backed anchor is not strictly monotonic and can accept state rewrites or storage rollback;
4. successor provisioning does not prove that the supplied terminal record is the actual anchored tail;
5. event idempotency is limited to the active segment;
6. recovery authorizations are not checked for expiry or replay;
7. the production integration evidence verifies loader construction, not a real publisher/anchor round trip.

All eight external activation gates remain incomplete, and authority remains correctly disabled.

---

## Independently verified

| Check | Result |
|---|---:|
| Submitted ZIP SHAKE256-512 | `f33d2c682afe312668c9d6256da59784a43cd91b29b73881109690b2709ce800` |
| ZIP integrity | Passed |
| ZIP entries | 2,101 |
| Regular files / inventory records | 1,915 |
| SHAKE256-512-covered files | 1,911 |
| Recursive exclusions | 4 |
| Covered hash or size mismatches | 0 |
| Duplicate ZIP paths | 0 |
| Embedded ZIP files | 0 |
| Packaged Python cache artifacts | 0 |
| Schemas compiled | 129 |
| Strict canonical schemas | 54 |
| Valid fixtures accepted | 54 |
| Adversarial fixtures rejected | 56 |
| Independent normal tests | 303/303 under Python 3.13.5 |
| Independent warnings-as-errors tests | 303/303 |
| Independent required validation | 101/101 passed |
| Independent validator duration | 211.601873 seconds |
| Independent surviving phase descendants | 0 |
| Current Python 3.12 claim | Explicitly unavailable |
| Theorem/promotion/release authority | Disabled |
| Freeze state | Permanently not frozen |

The four recursive exclusions are correctly represented with `shake256_512: null` and `size_bytes: null`:

1. `DRAFT5_3_15_VALIDATION_REPORT.json`
2. `PACKAGE_INVENTORY_v1_6_draft_5_3_15.json`
3. `refs/manifest/CHECKSUMS_v1_6_draft_5_3_15.shake256_512`
4. `refs/manifest/MANIFEST_v1_6_draft_5_3_15_complete.md`

The independently regenerated validation report recorded:

- 101 required phases passed;
- zero required failures, skips, duplicates, or missing phases;
- eight external activation phases skipped;
- 303 tests discovered and passed;
- zero surviving phase descendants.

The independent run was slower than the packaged run, but it completed successfully.

---

# Closure of Draft 5.3.14 findings

## Materially closed

### Proof-service audit-key separation

Production proof-service loading now constructs a Unix-socket publication client and does not load the audit private key.

The configured publisher UID must be:

- non-root; and
- different from the proof-service UID.

### Bounded request thread

The proof service sends a deterministic event identifier over a Unix socket and waits only until the request deadline. It verifies a signed publication receipt before treating publication as successful.

### Segment capacity

Normal events are bounded separately from the terminal seal, and a terminal-seal byte reserve is enforced.

### Bounded log reads

The log size is checked with `fstat()` before allocation. Accepted logs are read in bounded chunks with deadline checks.

### Checkpoint temporary cleanup

Temporary checkpoint files are removed on failed pre-replacement operations.

### Audit registries

Audit signing and anchor registry schemas are present, and the proof-service loader validates a governance-signed audit signing registry.

### Storage separation

The audit publisher and proof service use distinct identities in the provided production-loader fixture. The SQLite database is created under the proof-service UID with mode `0600`.

### Validator cancellation

The validator includes external SIGTERM/SIGINT cancellation tests and packaged evidence records zero surviving descendants.

---

# High-severity findings

## H-01 — Audit-key validity and revocation are not enforced at record or receipt use

**Activation blocker:** Yes.

### Evidence

`validate_governed_signing_registry()` verifies:

- registry signature;
- unique key IDs;
- scope;
- basic timestamp parsing;
- predecessor existence.

It does not reject rotation cycles or enforce complete predecessor chronology.

`SignedAppendOnlyAuditSink` receives a precomputed `audit_key_validity_evidence` object. Construction checks only that:

- the evidence schema is valid;
- its decision string says `active_time_valid_rotation_valid`;
- its registry hash matches.

The sink does not recompute the decision using its current clock before each record or seal.

During startup replay, `_verify_descriptor()` verifies:

- the record signature using any key in `verification_keys_by_id`;
- the evidence schema;
- evidence registry hash and key ID.

It does not reconstruct the evidence from the governed registry record, compare all lifecycle fields, or evaluate the key at `record.created_at`.

`UnixSocketAuditPublisherClient` accepts a receipt signed by any key in its verification-key map. It does not require the currently authorized receipt key or re-evaluate the signer’s lifecycle.

### Independent reproductions

- A two-key rotation cycle was accepted by the registry validator.
- Key evidence valid only through September 2026 was reused to create a record dated January 2099.
- A log record signed by a historical key with self-asserted active evidence passed descriptor replay.
- A publication receipt signed by an old verification key was accepted by the proof-service client.

### Impact

A retired, expired, or revoked audit key can remain usable in records or receipts when the key remains in the historical verification set.

This does not directly authorize a theorem. It does undermine the authenticity of the audit evidence required for stale-cache classification and durable-publication proof.

### Required correction

For every record, checkpoint, seal, anchor state, recovery record, and receipt:

1. resolve the signer from the applicable governance-signed registry snapshot;
2. validate rotation lineage and reject cycles;
3. reconstruct key-validity evidence;
4. evaluate status and validity at the artifact’s signed timestamp;
5. verify principal and authorization scope;
6. bind the registry snapshot digest into the signed artifact;
7. define explicit historical acceptance rules for retired versus revoked keys.

Receipts should identify a dedicated receipt-signing scope rather than reusing the general record-signing scope.

---

## H-02 — Audit publisher and anchor servers do not authenticate Unix-socket peers

**Activation blocker:** Yes.

### Evidence

`GovernedUnixServer` creates a Unix stream socket and applies a filesystem mode. Its request handler canonical-parses a line and dispatches it.

Neither the publisher nor anchor service checks Linux `SO_PEERCRED` or another authenticated peer identity.

`AuditPublisherServer.dispatch()` accepts any request with a matching event hash and idempotency identifier, then causes the publisher to sign a durability receipt.

`AuditAnchorServer.dispatch()` accepts unsigned read and compare-and-swap operations. The anchor signs the caller-supplied next state if its internal transition check accepts it.

The production-loader integration fixture creates its placeholder publisher socket with mode `0666`.

### Independent reproductions

When socket filesystem permissions permitted access:

- an unrelated UID connected to the publisher socket and received a valid publisher-signed receipt;
- an unrelated UID connected to the anchor socket and caused the anchor to sign an attacker-selected genesis namespace and segment.

### Impact

Filesystem mode is the only caller-control boundary. A mode, group, ACL, deployment, or launcher mistake can turn the publisher and anchor signing services into local signing oracles.

The anchor interface is particularly sensitive because compare-and-swap requests are not signed by an authorized publisher identity.

### Required correction

- Verify `SO_PEERCRED` on every accepted connection.
- Configure an explicit UID/GID allowlist per operation.
- Permit only the proof-service UID to publish evidence.
- Permit only the audit-publisher UID to mutate the anchor.
- Consider allowing broader read-only anchor access separately.
- Reject world-writable sockets.
- Verify socket owner, group, exact mode, inode identity, and complete ancestry.
- Add a signed or MAC-authenticated request envelope for defense in depth.
- Include peer UID/GID/PID and request identity in operational audit evidence.

---

## H-03 — The portable anchor transition and storage model is not strictly monotonic

**Activation blocker:** Yes.

### Evidence

For updates inside one segment, `_validate_transition()` rejects only sequence decreases.

It does not require:

- an exact `sequence + 1` transition;
- an exact idempotent no-op;
- immutable registry hashes;
- immutable transition authorization;
- a predecessor-state digest;
- a tail change that corresponds to one verified audit record.

### Independent reproductions

- A state at sequence zero was rewritten at sequence zero from a null tail to a non-null tail.
- The same rewrite changed the audit-signing registry hash.
- The rewritten state was accepted and signed by the anchor.

The provided `FileBackedMonotonicAnchorStore` stores signed states in a local append-only-by-convention file. Restoring the ledger bytes from sequence one to a previously saved valid sequence-zero prefix was accepted after restart.

### Impact

Process and UID separation protects the anchor from the proof service, but the portable file store is not independently monotonic against:

- its storage owner;
- root;
- filesystem rollback;
- backup restoration;
- privileged host compromise.

The name “monotonic anchor” therefore overstates the guarantee of the portable file implementation.

### Required correction

Require exact transition invariants:

- same segment: either exact no-op or `sequence == previous + 1`;
- immutable namespace, epoch, registry hashes, transition authorization, and predecessor segment binding;
- tail and segment status derived from a verified audit operation;
- successor: exactly one epoch increase and verified sealed predecessor.

For activation, use an external monotonic trust domain such as:

- TPM/HSM monotonic state;
- WORM/object-lock storage;
- remote transparency service;
- independent quorum-backed append-only service.

The local file-backed store can remain as a non-authoritative development implementation if labeled accordingly.

---

## H-04 — Successor provisioning does not prove that the supplied terminal record is the anchored tail

**Activation blocker:** Yes.

### Evidence

Successor provisioning verifies:

- predecessor checkpoint schema and signature;
- supplied terminal-record schema and signature;
- terminal event schema;
- governance transition signature;
- transition fields and hashes;
- checkpoint tail equals the current anchor tail;
- terminal-record sequence equals checkpoint sequence.

It does not require:

```text
SHAKE256-512(canonical supplied terminal record)
    == predecessor_checkpoint.tail_record_shake256_512
    == current_anchor.tail_record_shake256_512
```

It also does not require the supplied terminal record’s outer or embedded segment ID to equal the predecessor segment.

### Independent reproduction

A valid signed terminal seal record for `cache:audit:segment:other` was supplied with the same sequence as the real predecessor checkpoint.

A governance-signed transition referenced that unrelated record’s digest.

Successor provisioning accepted it even though the anchored predecessor segment was `cache:audit:segment:0001`.

### Impact

The transition attestation can be internally inconsistent while still passing the portable verifier.

External governance remains a trust root, but the runtime should reject contradictory governance input rather than relying on the signer never making a mistake.

### Required correction

Verify the supplied terminal record against the actual predecessor:

- canonical terminal-record SHAKE256-512 equals the checkpoint and anchor tail;
- terminal outer segment ID equals predecessor segment ID;
- embedded seal event segment ID equals predecessor segment ID;
- record sequence equals checkpoint sequence;
- previous-record hash and seal event predecessor tail agree with the predecessor log;
- checkpoint, anchor, record, and transition all bind the same registry snapshots.

---

## H-05 — Event idempotency is only segment-local

**Activation blocker:** Yes for the broad exactly-once audit-publication claim.

### Evidence

Event reconciliation searches the records of the active segment for the deterministic event identifier.

The anchor does not maintain a global event-ID set or index, and successor provisioning does not transfer an event-ID commitment.

### Independent reproduction

The same canonical event was:

1. committed in segment 1;
2. followed by a terminal seal;
3. submitted again after provisioning segment 2.

Both submissions returned:

```text
committed
```

rather than the second returning `already_committed`.

### Impact

A timeout, retry, failover, or delayed delivery that crosses a segment rotation can create duplicate audit records.

The current idempotency guarantee is accurate only within one segment.

### Required correction

Maintain a global, durable event-ID commitment across segments. Options include:

- event-ID index owned by the anchor;
- segment-level Merkle or Bloom commitments plus exact lookup storage;
- dedicated idempotency database in the publisher trust domain;
- externally anchored transparency log with unique event IDs.

Successor provisioning must carry forward the global idempotency state.

---

## H-06 — Recovery authorization expiry and replay are not enforced

**Activation blocker:** Yes.

### Evidence

Recovery methods verify the authorization schema and governance signature.

They do not evaluate:

- `created_at`;
- `expires_at`;
- current time;
- one-time use of `authorization_id`;
- prior recovery evidence;
- revocation.

The temporary-cleanup path checks only segment ID and action before deleting every matching service-owned temporary checkpoint file.

### Independent reproduction

A recovery authorization that expired in January 2020 was accepted in the current execution and deleted a matching checkpoint temporary file.

### Impact

A captured old authorization can be replayed indefinitely.

For dangling-tail reconciliation, replay may alter anchor and checkpoint state. For cleanup, it may delete files created by a later incident.

### Required correction

- Enforce `created_at <= now < expires_at`.
- Require a short maximum authorization lifetime.
- Maintain a durable consumed-authorization ledger.
- Bind authorization to exact before-state, candidate file set, file identities, and operation.
- Reject replay even when the filesystem has returned to a similar state.
- Define and implement every recovery action declared by the schema, or remove unsupported actions.

---

# Medium-severity and integration findings

## M-01 — Production non-root evidence validates loaders, not end-to-end audit publication

The supplied evidence correctly proves:

- real `setgid`/`setuid`;
- authority-loader construction;
- application-loader construction;
- service-owned SQLite;
- root-execution rejection;
- distinct configured publisher UID.

It does not prove:

- startup of `AuditPublisherServer`;
- startup of `AuditAnchorServer`;
- publisher-to-anchor communication;
- proof-service-to-publisher peer authentication;
- event publication;
- receipt verification;
- audit record durability;
- anchor advancement;
- service restart and replay.

The harness creates a listening placeholder Unix socket and then loads the application. It does not accept or process a publication request.

The loader can also construct successfully before the endpoint is exercised because the publication client verifies the socket only when called.

### Required correction

Extend the integration to execute a full cross-UID round trip:

1. root/anchor service;
2. publisher service under UID 65533;
3. proof service under UID 65534;
4. publish a real stale-cache event;
5. verify the receipt;
6. verify record, checkpoint, anchor, and idempotency;
7. restart all services and replay;
8. test denied UIDs and wrong socket modes.

---

## M-02 — No production launcher or configuration loader starts the publisher or anchor services

The package contains library classes for:

- `AuditPublisherServer`;
- `AuditAnchorServer`;
- `FileBackedMonotonicAnchorStore`.

Outside tests, no executable entrypoint instantiates these servers or runs `serve_forever()`.

The proof-service production loader validates the public audit signing registry, but no corresponding production service loader was found that:

- loads the audit private key;
- selects the governed current key;
- validates anchor key lifecycle;
- constructs the segment;
- starts publisher and anchor listeners;
- drops to the configured UIDs;
- manages shutdown, restart, rotation, and recovery.

### Required correction

Add production entrypoints and service contracts for both services, with:

- canonical configuration;
- governance-signed key registries;
- UID/GID drop;
- socket ownership and peer policy;
- readiness and health checks;
- restart behavior;
- signal handling;
- segment rotation;
- recovery mode;
- zero private-key exposure to the proof process.

---

## M-03 — File-backed anchor durability code needs low-level write and lifecycle hardening

The file-backed anchor:

- performs a single `os.write()` rather than looping on short writes;
- keeps one ledger up to 64 MiB without a governed rotation mechanism;
- does not hash-chain each state to its predecessor state;
- cannot independently detect valid-prefix ledger rollback.

### Required correction

- Use complete-write loops.
- Add state predecessor digests.
- Add governed anchor-ledger segmentation and external tail anchoring.
- Define compaction or retention without destroying monotonic evidence.
- Test short writes, ENOSPC, partial filesystem failure, and restart recovery.

---

# External activation gates

The supplied release status correctly leaves all eight incomplete:

1. strict Lean;
2. strict TLC;
3. governed hermetic Lean image execution;
4. signed OCI image build attestation;
5. signed verifier executable attestation;
6. independently reproducible inspector builds;
7. clean committed and published source provenance;
8. external governance authorization.

Portable validation does not enable theorem, promotion, or release authority.

---

# Recommended Draft 5.3.16 priority order

## P0 — Authenticate service boundaries

1. Enforce `SO_PEERCRED` on publisher and anchor connections.
2. Add exact socket owner/group/mode rules.
3. Sign or MAC publisher and anchor requests.
4. Add denied-peer and socket-misconfiguration tests.

## P1 — Enforce audit-key lifecycle at every artifact

5. Reject registry cycles and incoherent rotations.
6. Recompute key validity at record, receipt, checkpoint, seal, anchor, and recovery timestamps.
7. Separate receipt-signing and record-signing scopes.
8. Enforce revoked-key replay policy.

## P2 — Correct anchor semantics

9. Require exact sequence transitions and immutable governance fields.
10. Hash-chain anchor states.
11. Verify terminal records against the actual anchored tail.
12. Replace or clearly demote the rollbackable file-backed anchor for activation.

## P3 — Complete audit idempotency and recovery

13. Make event idempotency global across segments.
14. Enforce recovery authorization expiry and one-time use.
15. Bind cleanup authorization to exact temporary-file identities.
16. Add governed recovery-state persistence.

## P4 — Complete production services

17. Add publisher and anchor production launchers.
18. Run a real three-identity proof-service → publisher → anchor integration.
19. Verify restart, rotation, denied peers, timeout reconciliation, and recovery.

## P5 — Complete external gates

20. Run strict Lean and strict TLC.
21. Build and execute the governed image.
22. Produce image, verifier, and reproducible-inspector attestations.
23. Publish and bind committed source.
24. Obtain external governance authorization.

---

# Minimum acceptance bar for Draft 5.3.16

- An expired or revoked audit key cannot create or replay a record or receipt.
- Rotation cycles are rejected.
- Unapproved local UIDs cannot call publisher or anchor mutation operations.
- Same-sequence anchor rewrites and file-ledger rollback are rejected or externally detected.
- A successor accepts only the actual anchored terminal record.
- Repeated event IDs remain idempotent across segment rotation.
- Expired or replayed recovery authorizations are rejected.
- The production integration performs a real cross-UID publication and anchor update.
- The complete Python 3.13 validator remains clean.
- Authority remains disabled until all eight external gates are independently complete.

---

# Publication recommendation

Draft 5.3.15 can be pushed as a non-authoritative corrective corpus.

Suggested release wording:

> Draft 5.3.15 separates proof execution from audit signing and durable publication, adds a distinct non-root publisher identity, supervised request deadlines, governed segment transitions and recovery, bounded streaming verification, and real non-root loader construction. The corpus remains permanently not frozen and non-authoritative. Authority activation remains blocked pending authenticated publisher/anchor peer identities, per-artifact audit-key lifecycle enforcement, strict external-anchor monotonicity, cross-segment audit idempotency, production audit-service integration, and all eight external activation gates.
