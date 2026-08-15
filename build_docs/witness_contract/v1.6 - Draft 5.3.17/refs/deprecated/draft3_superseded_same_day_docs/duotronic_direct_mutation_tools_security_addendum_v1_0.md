# Direct Mutation Tools Security Addendum v1.0

**Status:** Draft 2 normative security addendum  
**Purpose:** Govern MCP tools that can directly write files or execute host commands.

---

## 1. Tools in scope

```text
write_file_system
execute_system_command
```

---

## 2. Risk classification

| Tool | Risk | Required scope |
|---|---|---|
| `write_file_system` | repo_write / host_write | `mcp:write` |
| `execute_system_command` | service_mutation / host_command | `mcp:ops-request` |

---

## 3. Required witness record

```yaml
DirectMutationToolWitness:
  mutation_id: string
  tool_name: write_file_system | execute_system_command
  principal_id: string
  required_scope: string
  path_or_cwd: string
  command_hash: string | null
  content_hash: string | null
  redacted_args_hash: string
  used_sudo: boolean
  timeout_seconds: integer
  result_ok: boolean
  returncode: integer | null
  stdout_hash: string | null
  stderr_hash: string | null
  backup_snapshot_ref: string | null
  git_sync_ref: string | null
  policy_decision_id: string
  audit_record_id: string
```

---

## 4. Sudo rule

`execute_system_command` with `use_sudo=true` is a critical operation.

Requirements:

1. never store sudo password;
2. redact sudo password in audit logs;
3. require explicit policy decision;
4. require backup snapshot unless waived;
5. require operator-visible audit record.

---

## 5. Auto backup and git sync

If auto backup/git sync is enabled, a mutation should produce:

```text
MutationToolCallWitness
-> BackupSnapshotWitness
-> GitSyncWitness
-> ResultWitness
```

If backup or git sync fails, the mutation result may still be recorded, but runtime must mark:

```text
mutation_sync_status = partial | failed
```

---

## 6. Production default

For production mode:

```text
write_file_system: disabled unless break-glass policy allows
execute_system_command: disabled unless break-glass policy allows
```

For development mode:

```text
write_file_system: allowed under mcp:write
execute_system_command: allowed under mcp:ops-request with audit
```

---

## 7. Emergency disable

The Policy Shield must be able to disable all direct mutation tools by setting:

```text
direct_mutation_tools_enabled = false
```
