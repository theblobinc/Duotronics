# v1.5 to v1.6 Migration and Rollback Runbook v1.0

Status: canonical migration runbook.

## Preflight

1. Record current git commit.
2. Create database backup.
3. Create object-store backup.
4. Export current witness manifest.
5. Run MCP self-test.
6. Confirm free disk space.
7. Confirm maintenance window.

## Migration order

1. Apply schema compatibility migration for `step`.
2. Apply temporal witness tables.
3. Apply memory update, absence, and decay tables.
4. Apply MCP recurrence observation tables.
5. Deploy API/OpenAPI route changes.
6. Deploy MCP recurrence tools.
7. Deploy live overlay.
8. Run conformance tests.
9. Run replay smoke test.
10. Enable Firehose UI in read-only mode first.

## Rollback order

1. Disable write tools.
2. Stop new recurrence promotion.
3. Revert API/MCP deployment.
4. Restore previous service image.
5. Keep `step` column unless explicitly safe to drop.
6. Restore DB backup only if data corruption occurred.
7. Record rollback witness.

## Rollback witness

```yaml
RollbackWitness:
  rollback_id: string
  from_version: string
  to_version: string
  reason: string
  backup_id: string
  migrations_reverted: list[string]
  data_loss_expected: boolean
  reviewer: string
  completed_at: TemporalWitness
```

