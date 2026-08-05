# Duotronic Direct Mutation Tools Security Addendum v1.1

**Status:** Research specification draft  
**Version:** direct-mutation-security@v1.1  
**Document kind:** Security addendum  
**Primary purpose:** Upgrade the Draft 2 direct mutation tools profile with allowed-root, redaction, auto-backup, and git-sync constraints.  
**Draft:** v1.6 Draft 3  
**Generated:** 2026-04-30T17:40:00Z

---

## 1. Tools covered

This addendum applies to direct host mutation tools such as:

```text
write_file_system
execute_system_command
```

## 2. Required controls

A conforming runtime must implement:

1. scope enforcement;
2. allowed-root enforcement;
3. argument redaction in audit logs;
4. timeout limits for commands;
5. backup-before-or-after mutation records;
6. git status and sync records where repository mutation is expected;
7. failure records when sync fails;
8. policy metadata discoverable through `policy_explain`.

## 3. Allowed root

```yaml
DirectMutationAllowedRoot:
  env_var: MCP_ALLOWED_HOST_ROOT
  default_reference_value: /var/www/xavi
  applies_to:
    - write_file_system.path
    - execute_system_command.cwd
```

The tool must reject paths outside the allowed root unless an explicit higher policy grants a narrower exception.

## 4. Auto mutation sync

Reference environment controls:

```yaml
AutoMutationSync:
  MCP_AUTO_BACKUP_ON_MUTATION: true
  MCP_AUTO_GIT_SYNC: true
  MCP_AUTO_GIT_PUSH: true
```

The sync result should be recorded as a mutation witness:

```yaml
DirectMutationSyncWitness:
  tool_name: string
  target_path_or_cwd: string
  backup_enabled: boolean
  backup_ok: boolean
  git_sync_enabled: boolean
  git_sync_ok: boolean
  latest_commit: string | null
  push_ok: boolean | null
  retried_after_rebase: boolean | null
```

## 5. Redaction

Audit logs must redact fields whose keys include:

```text
password
sudo_password
admin_key
api_key
token
secret
authorization
```

## 6. Policy warning

Direct mutation tools are implementation accelerators. They must not become a replacement for reviewed worktree patches in production changes.
