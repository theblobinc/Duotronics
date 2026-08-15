# Agent Lab Mutation Safety Config Witness Profile - v1.6 Draft 4.1

Status: active Draft 4.1 governance profile.  
Generated: 2026-05-09.  
Extends: `duotronic_draft4_agent_lab_mutation_backup_witness_profile_v1_0.md`.

## Purpose

A backup record is not meaningful unless the active mutation-safety policy is
known. Draft 4.1 requires mutation evidence to capture the configuration that
controls preflight backup, auto-backup, git sync, git push, S3 backup, and remote
backup behavior.

## Canonical object

```yaml
MutationSafetyConfigWitness:
  schema: mutation-safety-config@v1
  observed_at: timestamp
  observed_by: string
  config_source: env | config_file | mcp_capability_report | runtime_status | unknown
  mcp_require_preflight_backup: boolean | unknown
  mcp_auto_backup_on_mutation: boolean | unknown
  mcp_auto_git_sync: boolean | unknown
  mcp_auto_git_push: boolean | unknown
  s3_backup_enabled: boolean | unknown
  remote_backup_enabled: boolean | unknown
  local_backup_root_configured: boolean | unknown
  config_source_digest: shake256_512 | null
  policy_explain_ref: string | null
```

## Mutation evidence extension

```yaml
AgentLabMutationWitnessExtension:
  mutation_id: string
  tool_name: string
  principal: string | null
  requested_path: string | null
  mutation_surface: file | repo | database | service | command | mixed
  preflight_backup_required: boolean
  preflight_backup_ref: string | null
  post_mutation_backup_ref: string | null
  git_sync_ref: string | null
  git_push_ref: string | null
  safety_config_ref: string
  semantic_validation_ref: string | null
  release_approval_ref: string | null
```

## Claim rules

1. Backup existence proves only that a backup artifact was created.
2. A mutation is not semantically approved unless a semantic validation witness
   exists.
3. A mutation is not release-approved unless an operator approval witness exists.
4. Auto git push MUST be treated as a higher-risk mode and explicitly disclosed
   in release bundles.
5. Missing config evidence downgrades mutation evidence to `incomplete`.
