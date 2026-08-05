# Duotronic Witness Contract v1.6 Draft 5.3.14

This is a standalone, permanently-not-frozen, non-authoritative corrective development corpus. Begin with `CANONICAL_CORPUS_v1_6_draft_5_3_14.json`, then follow `START_HERE.md`.

Draft 5.3.14 strengthens the dedicated cache-audit path. Production startup now requires an explicitly provisioned audit segment and a separately stored signed tail checkpoint. The checkpoint binds the segment ID, sequence, current tail, predecessor sealed-segment tail, signer, status, and creation time. Valid-prefix truncation, log deletion, older-segment restoration, checkpoint mismatch, competing genesis, and appends to a sealed segment fail closed.

Audit publication is governed by the request-wide monotonic deadline. Lock acquisition uses nonblocking retries, and chain verification, append, file synchronization, signed-checkpoint replacement, and directory synchronization are checked against the remaining budget. A publication that cannot complete within budget returns `cache_audit_publication_failed`; it cannot return a successful rotation classification after expiration.

Historical stale-row evidence is now `cache_stale_row_evidence/v4`. It additionally binds the cache envelope's signed-payload SHA-256, canonical full-envelope SHA-256, and original signature. The audit sink allowlists event schema versions and validates embedded events both before append and during startup replay.

The production integration harness accurately records that UID/GID 65534 was representable, but bind-mounting `/proc` into the chroot was denied. Descriptor-anchored SQLite and both real production loaders therefore remain `environment_unavailable`, not passed. Authority remains fail-closed.

The corpus contains merged current source only. Earlier source-package ZIPs are not embedded. `history/SOURCE_PACKAGE_LINEAGE_v1_6_draft_5_3_14.json` records predecessor digests without making them runtime authority inputs.

Run the documented workflow with each available target interpreter:

```sh
python3 executable/validators/generate_draft5_3_14_python_evidence.py --record-only
python3 executable/validators/generate_draft5_3_14_python_evidence.py --merge-only
python3 executable/validators/build_schema_registry_v5314.py
node executable/validators/validate_draft5_3_14_schemas.mjs --phase all
python3 executable/validators/build_draft5_3_14_manifests.py
python3 executable/validators/validate_draft5_3_14_corpus.py
```

The schema-registry phase is tested from absence: the current registry is deleted in a temporary source copy, regenerated, and required to match the packaged bytes exactly.

The eight external activation gates remain independently incomplete. Theorem, promotion, and release authority remain disabled.
