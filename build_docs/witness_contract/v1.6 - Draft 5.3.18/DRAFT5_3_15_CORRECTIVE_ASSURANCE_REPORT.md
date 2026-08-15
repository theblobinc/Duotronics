# Draft 5.3.15 Corrective Assurance Report

## Verdict boundary

Draft 5.3.15 closes the portable Draft 5.3.14 findings concerning coordinated local rollback, arbitrary successor ancestry, terminal-seal capacity, request-thread blocking, unbounded log reads, failed checkpoint cleanup, audit-key lifecycle, path protection, validator external cancellation, and production non-root loader execution.

This is not an authority-activation statement. The corpus remains permanently not frozen and non-authoritative. No portable test substitutes for the eight independent external gates.

## Independently anchored audit state

A signed local checkpoint is consistency evidence, not monotonic authority. The active design requires an independently protected anchor state containing the segment identity, sequence, tail digest, predecessor-seal context, key-registry binding, monotonic epoch, and signature. Startup compares the verified local state with the live anchor. Coordinated restoration of both local files therefore fails unless the independent anchor is also improperly rolled back.

Genesis and successor transitions are distinct governed operations. Genesis requires a signed authorization. A successor requires a signed transition plus verified predecessor terminal record, sealed checkpoint, anchored tail, signer validity, and registry identity. There is no API that treats an arbitrary 64-hex string as proof of predecessor existence.

## Rotation and recovery

Normal event limits exclude reserved terminal-seal capacity. The implementation refuses a normal append before it would consume the guaranteed seal slot or byte reserve. Segment sealing remains possible at the normal capacity boundary.

Checkpoint replacement is crash-aware and cleans every uncommitted temporary on failure. If a signed log record was durably appended while the checkpoint remained older, ordinary startup fails closed. Recovery requires a governance-signed authorization, verifies the dangling record and anchor state, updates the checkpoint through the governed path, and emits signed recovery evidence.

## Publication isolation and deadline semantics

The proof service does not hold audit signing material or directly mutate audit storage. It sends a canonical request with a deterministic event identifier to a separately owned publisher and verifies a signed durability receipt under the governed audit-key registry. Socket connect, send, and receipt read are bounded by the request-wide monotonic deadline. A blocking storage syscall is isolated to the publisher process/service and cannot indefinitely block the proof-service request thread.

The event identifier is stable across retries. A client timeout is therefore reconciled by querying or resubmitting the same identifier rather than creating duplicate audit records.

## Bounded verification and storage policy

The audit reader uses `fstat()` before allocation, rejects size violations immediately, streams accepted input under a hard byte counter, and checks the deadline per chunk. The sink walks complete ancestry without following symlinks, verifies owner, mode, identity stability, and private directory policy, and requires the anchor/publisher protection domain to be distinct from the proof-service identity.

## Audit authority lifecycle

Governance-signed audit and anchor registries carry authorization scope, validity windows, active/retired/revoked state, rotation predecessor, registry lineage, and historical verification keys. Every authority-bearing audit artifact binds the applicable registry digest and key-validity evidence. Retired historical keys remain available only for verification; revoked or out-of-scope keys fail closed.

## Validator and production execution

The validator has top-level SIGTERM/SIGINT cleanup. It terminates the active worker process group, enumerates token-bound escaped descendants, sends bounded TERM/KILL sequences, and reaps before exit. Cancellation regressions require zero surviving descendants.

The production integration harness executed both real loaders after actual transition to UID/GID 65534. The configured publisher endpoint is owned by UID 65533, the service database is owned by UID/GID 65534 with private mode, root-owned ancestors are immutable, and the service trust root is private. The result is a pass, not an environment substitution.

## Authority boundary

The eight external gates remain separate: strict Lean, strict TLC, governed hermetic image execution, signed OCI image build attestation, signed verifier executable attestation, reproducible inspector build attestation, clean committed-source provenance, and external governance authorization. Until all are independently supplied and verified, theorem authority, promotion authority, and release authority remain disabled.
