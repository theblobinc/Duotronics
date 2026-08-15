# Release Notes — v1.6 Draft 5.3.15

Draft 5.3.15 is a standalone, permanently-not-frozen, non-authoritative corrective development corpus based on Draft 5.3.14. It embeds no predecessor ZIPs; predecessor hashes are informational lineage only.

## Portable activation blockers closed

### Independently monotonic audit anchoring

The local segment and checkpoint are no longer treated as sufficient rollback authority. Every accepted state is compared with an independently protected monotonic anchor reached through a narrow client interface. Restoring an older matching local log/checkpoint pair fails because the anchor sequence, segment, and tail cannot move backward with service-owned files.

The portable implementation includes an in-memory conformance anchor for tests and a Unix-socket anchor client/server contract. Production deployment must place the anchor in a trust domain the proof service and audit publisher cannot roll back together, such as a privileged helper, hardware monotonic state, WORM storage, or a remote transparency service.

### Governed genesis and verified successor transitions

Genesis requires a governance-signed authorization. Successor provisioning accepts no raw predecessor-tail argument. It verifies a governance-signed transition, the predecessor terminal seal record, sealed checkpoint, signer authorization, and live anchored predecessor tail before creating a new segment.

### Seal-capacity-safe rotation

Normal event capacity is distinct from total segment capacity. The sink reserves one terminal-seal record and a conservative byte budget before accepting normal events, so a segment that reaches its normal-event boundary can still be sealed. Exact record, byte, seal-only, insufficient-reserve, and concurrent seal/append cases are covered.

### Hard-bounded request-thread publication

The proof service no longer performs audit `fsync()` itself and no longer holds the audit private key. It submits a deterministic event identifier to a separately supervised Unix-socket publisher and waits only within the request-wide monotonic budget. The publisher returns a governance-authorized signed durability receipt. A blocked storage operation may outlive the client request only inside the isolated publisher domain; it cannot hold the proof-service request thread indefinitely. Idempotent event identifiers permit safe reconciliation after ambiguous timeouts.

### Bounded verification and governed recovery

Audit startup checks `fstat()` before reading and rejects an oversized file before allocation. Accepted logs are verified with bounded streaming reads and per-chunk deadline checks. Failed pre-replacement checkpoint writes remove temporary files. A governance-authorized repair path can reconcile a fully signed dangling terminal record and emits signed recovery evidence; it does not silently rewrite history.

### Governed audit-key lifecycle

Governance-signed registries bind audit and anchor key IDs, principals, scopes, validity intervals, active/retired/revoked status, rotation predecessors, registry lineage, and historical verification keys. Records, checkpoints, seals, transitions, anchor states, recovery evidence, and publication receipts bind the registry digest and validity decision.

### Audit path protection

The sink verifies complete no-follow ancestry, expected owner and modes, stable directory/file identities, private segment/checkpoint directories, and distinct protection domains. Provisioning creates private directories rather than relying on process umask defaults.

### Validator cancellation safety

Top-level SIGTERM/SIGINT handling tracks the active phase worker group plus escaped descendants using a per-run token, terminates them, and performs bounded reaping. External cancellation regressions cover normal suites and intentionally escaped descendants.

### Real non-root production-loader execution

The packaged harness passed both real loaders after `setgroups`, `setgid`, and `setuid`. The proof service ran as UID/GID 65534. The audit publisher endpoint was owned by distinct UID 65533. SQLite used a service-private parent with absolute-path opening, avoiding the previous chroot `/proc` dependency. Root execution remains rejected.

## Portable validation scope

The active descriptor contains 101 required phases and eight optional external authority phases. Current-revision test, schema, fixture, Python, inventory, manifest, validator, and reliability totals are generated from final package bytes and recorded in the validation report rather than hard-coded in these notes.

## Authority status

Strict Lean, strict TLC, governed hermetic image execution, signed OCI image build attestation, signed verifier executable attestation, reproducible inspector build attestation, clean committed-source provenance, and external governance authorization remain independently incomplete unless corresponding external evidence is supplied. Theorem, promotion, and release authority remain disabled.
