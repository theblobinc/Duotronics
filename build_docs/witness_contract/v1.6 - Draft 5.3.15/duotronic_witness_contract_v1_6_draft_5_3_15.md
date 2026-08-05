# Duotronic Witness Contract v1.6 — Draft 5.3.15

## Status

This is a completed corrective development corpus that is **permanently not frozen** and **non-authoritative**. Theorem, promotion, and release authority default to disabled.

## 1. Core authority rule

A proof result is authoritative only when every required binding, trust artifact, runtime control, formal gate, build attestation, source-provenance record, and external governance authorization is present and verified. Portable tests establish regression behavior only; they cannot activate authority.

## 2. Cache and request binding

Cached envelopes are duplicate-rejecting canonical JSON and must bind the current authenticated principal, idempotency slot, request digest and ID, claim and content digest, policy, source bundle, proof artifact, compiler profile, compiler witness, result, signer, and signing chronology. Historical rotation classification occurs only after all bindings and signatures pass. A mismatch is `cache_integrity_invalid`, not normal rotation.

## 3. Audit trust separation

The proof service does not possess the audit private key and does not directly write audit files. It submits a canonical event with a deterministic event identifier to a separately owned publisher. The publisher performs durable storage and returns a signed receipt whose key, scope, status, validity, rotation lineage, and registry digest are governance-authorized.

## 4. Independently monotonic anchor

Local log and checkpoint agreement is insufficient to establish rollback resistance. Each accepted audit state must match an independently protected monotonic anchor outside the joint rollback domain of the proof service, publisher log, and local checkpoint. Missing, stale, decreased, or conflicting anchor state fails closed.

The portable interface supports a privileged Unix-socket anchor service. Deployments may use a root-owned narrow helper, TPM/HSM monotonic state, WORM/object-lock storage, or a remote transparency service, provided the proof and audit service identities cannot rewrite prior anchor state.

## 5. Governed genesis and segment succession

Genesis requires a dedicated governance-signed authorization. A successor segment requires a governance-signed transition and verification of the predecessor terminal seal record, sealed checkpoint, anchored terminal tail, key validity, and registry identity. A caller-provided digest by itself is never predecessor proof.

Normal append capacity excludes a terminal-seal record and byte reserve. Once normal capacity is exhausted, the segment can still append its required seal and transition through the governed successor protocol.

## 6. Recovery

An audit record may become durable before checkpoint replacement. Ordinary startup treats log-ahead-of-checkpoint state as an integrity condition and does not silently repair it. Recovery requires a scoped, time-valid governance authorization; it verifies the exact dangling signed record and anchor, updates state atomically, and emits signed recovery evidence. Temporary checkpoint files are removed on every failed pre-replacement path.

## 7. Deadline and idempotency

The proof-service request thread is hard-bounded at the publisher IPC boundary. Connect, send, and receipt read use the remaining monotonic request budget. Durable filesystem calls occur in the isolated publisher domain. A deterministic event ID permits retry and reconciliation when the client times out after an ambiguous publication outcome.

## 8. Bounded audit verification

Audit files are rejected by `fstat()` before reading when their declared size exceeds policy. Accepted files are read in bounded chunks under a hard byte counter and deadline checks. Records, embedded events, signatures, hash links, sequence, segment identity, registry evidence, seals, checkpoints, and anchor state are validated canonically.

## 9. Storage ancestry and identities

All sensitive paths are resolved using no-follow descriptor walks. Complete ancestry, ownership, modes, link counts, type, and stable identities are checked. Service, publisher, and anchor trust domains must be distinct where required by policy. Provisioned sensitive directories are private by construction.

## 10. Production loader execution

The packaged non-root harness executed both real loaders after `setgroups`, `setgid`, and `setuid` to UID/GID 65534. The publisher socket is owned by distinct UID 65533. The service database uses a private-parent absolute path and is service-owned with private mode. Root execution remains invalid.

## 11. Validator reliability

Required phases execute in isolated process groups with bounded capture and descendant reaping. Top-level SIGTERM/SIGINT handlers terminate the active worker group and token-identified escaped descendants before exit. Current-revision Python evidence is recorded separately for each target; unavailable interpreters receive no inherited claim.

## 12. External activation gates

Authority remains disabled until all eight external gates pass independently:

1. strict Lean;
2. strict TLC;
3. governed hermetic Lean image execution;
4. signed OCI image build attestation;
5. signed verifier executable attestation;
6. reproducible inspector build attestation;
7. clean committed-source provenance;
8. external governance authorization.

Failure, absence, unavailability, or skipped execution of any gate is not a pass.
