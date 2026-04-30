# SRNN Backend Drift Closure v1.0

Status: source-refresh integration note.

## Observed drift

Draft 3 saw multiple SRNN backend changes in one day, including:

- SDK and formal model implementation.
- OpenAPI export.
- Cognition step migration.
- Proof interchange fixtures.
- Mutation policy.
- Live recurrent witness overlay.
- Stale evidence behavior.
- Python SDK test-runner correction.
- WGRNN Firehose package changes.

## Closure rule

Every backend drift item must be classified as:

```yaml
BackendDriftRecord:
  change_id: string
  source_commit: string
  affected_contracts: list[string]
  migration_required: boolean
  test_required: list[string]
  docs_updated: boolean
  runtime_verified: boolean
```

## Draft 2 queue compatibility warning

Do not point a Draft 3 runtime at a Draft 2 task queue schema without an explicit compatibility adapter. Silent witness promotion mismatches are more dangerous than hard failures.

