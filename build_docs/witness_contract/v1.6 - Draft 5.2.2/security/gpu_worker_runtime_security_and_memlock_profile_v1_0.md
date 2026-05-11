# GPU Worker Runtime Security and Memlock Profile v1.0

Status: Draft 4 security profile.
Generated: 2026-05-08

## Scope

This profile covers GPU worker runtime controls that can affect system security,
resource isolation, and operational stability.

## Security-sensitive runtime flags

- `no_mmap` changes how model weights are mapped and can affect failure mode,
  memory pressure, and filesystem interaction.
- `mlock` requests memory locking and requires kernel/container capability and
  limit support.
- `n_cpu_moe` changes CPU offload behavior for mixture-of-experts models.
- `cache_type_k` and `cache_type_v` change KV cache representation and can
  affect memory use and output/performance characteristics.
- `prompt_compaction_mode` changes the prompt payload seen by the model.

## Memlock verification

A conforming runtime must not equate `mlock=true` with confirmed locked memory.
It must record:

```yaml
MemlockDiagnostics:
  mlock_requested: boolean
  ipc_lock_capability: boolean
  memlock_limit: string
  mlock_confirmed: boolean
  mlock_log_failure: boolean
```

## Authentication boundary

The GPU worker supports federation mode where SSH tunnel topology supplies the
authentication boundary, and legacy mode where an API key header is checked.
Draft 4 requires deployments to record which mode is active.

## Failure policy

If a requested security-sensitive runtime flag cannot be confirmed, the system
must either:

- downgrade the readiness level;
- mark the feature unsupported;
- block release promotion;
- or require explicit operator override with evidence.
