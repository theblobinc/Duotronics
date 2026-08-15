# Migration Note - v1.6 Draft 3 to Draft 4

Status: Draft 4 migration note.
Generated: 2026-05-08

## Migration type

This is a corpus migration, not a destructive schema migration.

## Steps

1. Copy the complete Draft 4 directory into `build_docs/witness_contract/`.
2. Keep Draft 3 in place until Draft 4 is reviewed.
3. Update repository-level README links from Draft 3 to Draft 4 only after the
   Draft 4 manifest and validation report are accepted.
4. Do not delete Draft 3 manifests; Draft 4 relies on them for carry-forward
   traceability.
5. If applying to SRNN Server docs, place the same corpus under an appropriate
   `docs/duotronic/witness_contract/v1.6-draft-4/` path.

## Runtime migration checks

- Confirm node compose profiles match the Draft 4 federated runtime stack.
- Confirm `wg-rnn` is intentionally enabled or explicitly deferred per node.
- Confirm GPU worker large model files exist before requiring smoke tests.
- Confirm memlock and IPC_LOCK support before treating `mlock` as effective.
- Confirm Agent Lab backup logs are preserved before automated mutation.
