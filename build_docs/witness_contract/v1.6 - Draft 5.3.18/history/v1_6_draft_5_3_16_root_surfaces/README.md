# Duotronic Witness Contract v1.6 Draft 5.3.16

This is a standalone, permanently-not-frozen corrective development corpus. Begin with `CANONICAL_CORPUS_v1_6_draft_5_3_16.json`, then follow `START_HERE.md`.

Draft 5.3.16 authenticates every proof-service → publisher and publisher → anchor mutation with both Linux `SO_PEERCRED` and a signed canonical request bound to the exact socket identity. Publisher and anchor sockets require governed owners, groups, modes, real inode types, and no-follow ancestry; world-writable endpoints are rejected and root is not implicitly authorized.

Audit-key lifecycle is recomputed from governance-signed registries for every record, receipt, checkpoint, seal, recovery artifact, and anchor state at that artifact's timestamp. Rotation cycles, expired keys, revoked keys, scope confusion, and self-asserted validity evidence fail closed. Record, receipt, recovery, and monotonic-anchor signing scopes are distinct.

Anchor transitions are strict and hash-chained. Within a segment, only an exact idempotent no-op or `sequence = previous + 1` is accepted; namespace, epoch, registries, transition authorization, and predecessor bindings are immutable. Successor provisioning verifies that the canonical terminal-record SHAKE256-512 equals both the sealed checkpoint tail and the anchored tail and that the outer record and embedded seal identify the actual predecessor segment.

The portable file-backed anchor is explicitly development-only and cannot enable authority. Activation still requires an independently monotonic trust domain such as TPM/HSM state, WORM/object-lock storage, a remote transparency service, or an independently privileged monotonic helper with rollback detection.

Publisher-domain event idempotency is stored in a durable global index and survives segment sealing, successor provisioning, publisher restart, and ambiguous client timeouts. Recovery authorizations have a bounded lifetime, bind exact file identities and before-state, and are recorded in a durable one-time-consumption ledger.

Production launchers now exist for the publisher and anchor services. The production integration executes a real three-identity chain:

```text
proof service UID/GID 65534
    → publisher UID/GID 65533
        → anchor UID/GID 65532
```

The integration proves both production loaders passed after `setgid`/`setuid`, publishes and verifies a signed receipt, uses private-parent absolute-path SQLite, persists a record and checkpoint, advances the anchor, restarts the publisher, reconciles the duplicate globally, and rejects an unrelated UID through `SO_PEERCRED` even when that process has socket-group access and a copied request key.

Run the documented workflow with each available target interpreter:

```sh
python3 executable/validators/generate_draft5_3_16_python_evidence.py --record-only
python3 executable/validators/generate_draft5_3_16_python_evidence.py --merge-only
python3 executable/validators/build_schema_registry_v5316.py
node executable/validators/validate_draft5_3_16_schemas.mjs --phase all
python3 executable/validators/run_production_loader_integration.py --output validation/production_loader/draft5_3_16_nonroot_loader_evidence.json
python3 executable/validators/build_draft5_3_16_manifests.py
python3 executable/validators/validate_draft5_3_16_corpus.py
```

Schema-registry regeneration is tested from absence and must reproduce the packaged registry byte-for-byte. Python 3.12 evidence is included only when a current-revision interpreter actually executes the workflow.

Portable publisher/anchor boundary findings are closed at the non-authoritative implementation level. The eight external activation gates still require genuine external toolchains, builds, committed-source provenance, and governance signatures. Theorem, promotion, and release authority remain disabled until all eight are independently complete.
