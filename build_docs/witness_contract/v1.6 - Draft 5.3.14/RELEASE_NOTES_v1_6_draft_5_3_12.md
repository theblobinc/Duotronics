# Release Notes — v1.6 Draft 5.3.12

Draft 5.3.12 is a standalone, permanently unfrozen, non-authoritative corrective development corpus based on Draft 5.3.11. It embeds no predecessor ZIPs; predecessor hashes are informational lineage only.

## Closed Draft 5.3.11 findings

- Required-phase subprocesses write to size-bounded temporary files instead of captured pipes. Timeout handling closes parent descriptors, enumerates descendants, sends bounded TERM/KILL sequences, and performs bounded reaping without a second unbounded `communicate()`.
- Full-suite subprocesses emit nested substage start/done markers. The intentional-hang regression includes a descendant that escapes the worker process group and inherits its output descriptors.
- Cache replay canonical-parses and schema-validates a row, resolves its signer in the governed current or historical registry, verifies the row signature, verifies the signed registry lineage, and only then emits stale-row evidence and returns the stable rotation conflict.
- Unknown, forged, altered, or policy-revoked historical signers produce `cache_integrity_invalid`; they cannot enter the rotation-specific audit classification path.
- Production configuration includes a signed cache-registry-lineage document and governed historical registry files. Lineage must be complete, acyclic, chronologically ordered, and terminate at the current registry.
- Lease heartbeats retain a proportional interval for deliberately short leases instead of imposing a 50 ms floor; lease loss and final publication remain owner-fenced.
- A production-shape integration harness constructs root-owned immutable `/` and `/etc` ancestors, a service-owned mode-0700 `/etc/witness-authority`, canonical keys/configuration/schemas/signed registries, then executes both actual loaders after chroot and a real `setgid`/`setuid` transition.

## Environment qualification

This build sandbox maps only UID/GID 0 and rejects ownership of files by UID/GID 65534. The production integration harness therefore emitted a hash-covered `environment_unavailable` record and did not execute either loader here. It fails by default unless `--allow-unavailable` is explicitly used for evidence generation. This is not passing production integration evidence and authority remains disabled.

Final test, schema, fixture, required-phase, and package-closure totals are generated from the exact shipped bytes. Python 3.13 is targeted but is not claimed unless a current-revision interpreter record is present.

Measured current-revision results are 261/261 tests on Python 3.12.13 and 3.13.5, clean in normal and warnings-as-errors modes; 110 schemas compiled; 41 strict canonical schemas; 41 valid fixtures accepted; and 43 adversarial fixtures rejected. The complete 85-phase validator passed ten consecutive times per interpreter with bounded capture, complete reaping, and no surviving descendants.

## Authority status

Strict Lean, strict TLC, governed-image execution, signed OCI image build attestation, signed verifier executable attestation, reproducible inspector build attestation, clean committed-source provenance, and external governance authorization remain incomplete. Theorem, promotion, and release authority remain disabled.
