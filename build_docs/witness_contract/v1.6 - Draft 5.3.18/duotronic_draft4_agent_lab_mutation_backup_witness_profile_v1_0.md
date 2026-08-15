# Draft 4 Agent Lab Mutation Backup Witness Profile v1.0

Status: Draft 4 governance profile.
Generated: 2026-05-08

## Scope

Recent SRNN commits show Agent Lab/MCP backup log records associated with
automated `execute_system_command` activity and service-restart preflight
activity. This profile defines how those backup records should be interpreted.

## Backup record model

```yaml
AgentLabBackupWitness:
  kind: backup
  backup_id: string
  reason: string
  timestamp: timestamp
  file_count: integer
  archive_size: integer
  trigger: string
  job_id: string|null
  requested_by: string|null
  approved_by: string|null
  source_commit: string
```

## Authority boundary

A backup record proves that a backup event was recorded. It does not prove:

- the command was safe;
- the mutation was policy-approved;
- the semantic result was correct;
- the service restart succeeded;
- rollback was tested;
- the change should be promoted to release authority.

Draft 4 therefore classifies backup-log commits as audit evidence and mutation
process evidence.

## Required promotion checks

Before an automated mutation can become release-authoritative, the implementation
must also provide:

1. policy decision record;
2. changed file list;
3. diff or artifact digest;
4. preflight backup record;
5. test or validation output;
6. rollback instruction or rollback artifact;
7. human approval when the target path is release-sensitive;
8. final state observation.

## Relation to Draft 3

Draft 3 introduced stricter mutation policy and direct-mutation tool controls.
Draft 4 extends the evidence layer so that backup records are useful without
mistaking them for approval records.
