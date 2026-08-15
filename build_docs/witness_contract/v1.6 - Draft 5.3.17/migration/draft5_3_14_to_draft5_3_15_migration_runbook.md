# Migration Runbook — Draft 5.3.14 to Draft 5.3.15

## 1. Stop publication traffic

Stop proof-check workers before changing audit trust domains. Preserve every Draft 5.3.14 segment, checkpoint, key, and configuration as read-only migration evidence. Do not relabel an old local checkpoint as an external anchor.

## 2. Provision governed registries

Create governance-signed audit-signing and anchor registries. Record each key ID, principal, scope, validity interval, status, rotation predecessor, historical verification key, registry lineage, and governance signature. Audit signing material must be available only to the publisher; anchor signing material must be available only to the independent anchor authority.

## 3. Authorize genesis or transition

For a new chain, obtain a governance-signed genesis authorization. For continuity from an existing chain, first seal the predecessor under the governed procedure, verify its terminal record and checkpoint, anchor the terminal tail externally, and issue a signed transition. Never provision a successor from a manually supplied predecessor hash.

## 4. Separate service identities

Run the proof service, publisher, and privileged anchor under distinct identities or equivalent protection domains. The proof service receives only publisher and anchor public verification material plus IPC endpoints. It must not receive audit or anchor private keys or direct write access to audit storage.

## 5. Configure storage

Create private segment, checkpoint, database, and socket directories with explicit owners and modes. Verify complete no-follow ancestry. Configure normal event limits separately from total segment limits and reserve terminal-seal capacity.

## 6. Migrate local audit evidence

Import only through a governed migration operation. Verify every historical record and embedded event under its historical registry. Record the exact predecessor terminal digest and external anchor state. If the predecessor cannot be governed and sealed, begin a separately authorized genesis and retain the old chain as non-continuous historical evidence.

## 7. Configure idempotent publisher IPC

Enable deterministic event identifiers and signed durability receipts. Set request-wide IPC timeouts. Test retry after an intentionally ambiguous client timeout and require one logical audit event.

## 8. Exercise recovery

Inject checkpoint write failure. Confirm temporary cleanup, ordinary startup failure, governance-authorized recovery, signed recovery evidence, and restored checkpoint/anchor equality. Recovery authorization must be narrow, expiring, and single-purpose.

## 9. Execute production loaders

Run `python3 executable/validators/run_production_loader_integration.py`. Require both real loaders to pass after non-root identity transition, distinct publisher ownership, private SQLite ownership/mode, canonical registry loading, and root execution rejection.

## 10. Validate the corpus

Generate current Python evidence, regenerate the schema registry from absence, validate schemas and fixtures, rebuild manifests, and run `python3 executable/validators/validate_draft5_3_15_corpus.py`. Then run the bounded reliability orchestrator and perform an externally supervised cancellation test requiring zero descendants.

## 11. Preserve authority status

The migration closes portable audit and loader findings only. Keep theorem, promotion, and release authority disabled until strict Lean, strict TLC, governed image execution, signed build attestations, reproducible inspector builds, clean committed-source provenance, and external governance authorization all pass.
