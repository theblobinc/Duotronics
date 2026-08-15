# Direct Mutation Tool Enforcement v1.2

Status: canonical security policy; supersedes earlier addenda.

## Scope

Applies to direct host mutation tools such as:

```text
write_file_system
execute_system_command
apply_patch
commit_worktree
request_service_restart
request_stack_deploy
```

## Required enforcement layers

1. Principal scope check.
2. Tool policy check.
3. Allowed-root or worktree boundary check.
4. Path denylist for secrets and environment files.
5. Mandatory audit redaction for passwords, tokens, secrets, keys, and authorization headers.
6. Backup preflight for high-risk mutations.
7. Git diff capture.
8. Human approval for external action, service mutation, production deploy, or policy-sensitive changes.

## Default policy

```yaml
direct_mutation_default:
  enabled_by_default: false_for_production
  allowed_root_required: true
  worktree_required_for_repo_changes: true
  audit_redaction_required: true
  backup_required: true
  auto_git_sync_allowed: dev_only
  production_approval_required: true
```

## Prohibited without manual review

- policy engine mutation;
- witness identity hashing mutation;
- replay identity hashing mutation;
- proof status mutation;
- theorem/conjecture status mutation;
- auth or signing changes;
- direct production database writes.

## Required audit record

```yaml
DirectMutationAudit:
  mutation_id: string
  tool_name: string
  principal_id: string
  risk: string
  scope: string
  approval_required: boolean
  approval_id: string | null
  allowed_root: string
  target_path_or_cwd: string
  backup_id: string | null
  git_diff_hash: string | null
  ok: boolean
  error: string | null
```

## Draft 4 carry-forward update - 2026-05-08

This document is retained in the v1.6 Draft 4 corpus as part of the full Draft 3
carry-forward. Draft 4 adds newer SRNN Server runtime observations rather than
removing this baseline. For current Draft 4 interpretation, read:

- `README_v1_6_draft_4.md`
- `duotronic_draft4_srnn_source_refresh_2026_05_08.md`
- `duotronic_srnn_federated_runtime_stack_profile_v1_0.md`
- `duotronic_srnn_gpu_worker_llama_server_runtime_profile_v1_0.md`
- `runtime/llama_server_runtime_readiness_contract_v1_0.md`

Draft 4 updates the runtime boundary with the current SRNN compose stack,
per-node `wg-rnn` service, GPU-worker llama-server large-model path, runtime
model manifest/smoke/bench endpoints, memlock diagnostics, and Agent Lab/MCP
backup-log witness handling. This update does not claim live production
certification; it records the source-observed contract and follow-up validation
requirements.
