# Duotronic Witness Contract v1.6 Draft 5.3.15

This is a standalone, permanently-not-frozen corrective development corpus. Begin with `CANONICAL_CORPUS_v1_6_draft_5_3_15.json`, then follow `START_HERE.md`.

Draft 5.3.15 moves cache-audit authority outside the proof-service trust domain. Production proof workers no longer hold the audit private key or write audit segments directly. They submit deterministic event identifiers to a separately owned Unix-socket publisher and accept only governance-authorized signed durability receipts.

The audit publisher maintains signed JSONL segments, signed local checkpoints, and a separately privileged monotonic anchor. Restoring an older matching local log/checkpoint pair is rejected because it no longer matches the external anchor. Genesis requires a governance-signed authorization. Successor segments require a governance-signed transition that proves the predecessor's terminal record, sealed checkpoint, anchored tail, and signer authorization; arbitrary predecessor hashes are not accepted.

Normal-event capacity excludes a reserved terminal-seal slot and byte budget. Oversized logs are rejected by `fstat()` before allocation and are verified by bounded streaming reads. Failed checkpoint writes remove temporary files, and a governance-authorized recovery operation can reconcile a completely signed dangling terminal record while emitting signed recovery evidence.

Audit signing and anchor keys are governed by signed lifecycle registries that preserve historical verification keys and bind scope, validity intervals, active/retired/revoked status, and rotation predecessors into records, checkpoints, seals, transitions, anchor states, and receipts.

The request thread is hard-bounded at the audit publication boundary. Durable writes occur in a separately supervised publisher process or service. The client uses the request-wide monotonic deadline for connect, send, and receipt read; deterministic event identifiers reconcile ambiguous timeout completion without duplicate records.

The validator installs SIGTERM/SIGINT cleanup handlers, tracks a cryptographically random per-run descendant token, and terminates/reaps the active phase worker, escaped descendants, and nested regression children before exit.

The real production-loader harness now passes in this environment. UID/GID 65534 is used for the proof service, UID 65533 owns the audit publisher endpoint, both production loaders passed after real `setgid`/`setuid`, and the idempotency store uses private-parent absolute-path SQLite without requiring a `/proc` bind mount.

Run the documented workflow with each available target interpreter:

```sh
python3 executable/validators/generate_draft5_3_15_python_evidence.py --record-only
python3 executable/validators/generate_draft5_3_15_python_evidence.py --merge-only
python3 executable/validators/build_schema_registry_v5315.py
node executable/validators/validate_draft5_3_15_schemas.mjs --phase all
python3 executable/validators/build_draft5_3_15_manifests.py
python3 executable/validators/validate_draft5_3_15_corpus.py
```

Schema-registry regeneration is tested from absence and must reproduce the packaged registry byte-for-byte.

Portable audit and production-loader findings are closed in this revision. The remaining authority gates require genuine external toolchains, builds, provenance, or signatures. They are not self-certified by the corpus, and theorem, promotion, and release authority remain disabled until independently completed.
