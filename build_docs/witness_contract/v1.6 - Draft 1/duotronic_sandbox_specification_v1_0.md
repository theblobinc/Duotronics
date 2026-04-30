# Duotronic Sandbox Specification v1.0

**Status:** normative runtime safety contract  
**Version:** sandbox-spec@v1.0  
**Document kind:** interpreter and bridge sandbox hardening specification

## 1. Scope

This document governs execution sandboxes for Python, Julia, Lisp/SBCL, proof assistants, and external math tools. It also applies to sidecar inference workers when they process untrusted payloads.

## 2. Sandbox profiles

```yaml
SandboxProfile:
  sandbox_profile_id: string
  isolation_kind: process | container | microvm | remote_worker
  network_policy: disabled | allowlisted | unrestricted_policy_exception
  filesystem_policy: scratch_only | read_only_inputs | declared_outputs
  cpu_limit_ms: integer
  memory_limit_mb: integer
  wall_clock_limit_ms: integer
  stdout_limit_bytes: integer
  stderr_limit_bytes: integer
  seccomp_profile_ref: string | null
  apparmor_profile_ref: string | null
  user_namespace: boolean
  no_new_privileges: boolean
```

## 3. Minimum local sandbox

For a local prototype, the minimum acceptable sandbox for user or model-generated code is:

1. non-root process;
2. temporary working directory;
3. read-only input artifact mount;
4. declared output artifact directory;
5. CPU, wall clock, memory, stdout, and stderr limits;
6. network disabled by default;
7. no direct credentials in environment;
8. no direct canonical database credentials.

## 4. Production candidate sandbox

A production candidate should use OCI containers plus seccomp/AppArmor or an equivalent microVM/gVisor/Firecracker profile. A conforming deployment must record the selected mechanism as a `SandboxProfile` and emit runtime fingerprints.

## 5. Network policy

```text
network disabled -> default for math/interpreter runs
allowlisted -> specific package mirrors or internal MCP endpoints
unrestricted_policy_exception -> human-reviewed exception only
```

A run with network access cannot be deterministic unless all remote content hashes are pinned.

## 6. Filesystem policy

1. Input artifacts are mounted read-only.
2. Output artifacts are written to a scratch path and copied by the supervisor after hashing.
3. Interpreter code may not write to the repository, canonical PostgreSQL, Redis, Milvus, or host paths.
4. Temporary files are purged after artifact capture unless retention policy requires preservation.

## 7. Result capture

The sandbox supervisor must capture:

```yaml
InterpreterRunCapture:
  run_id: string
  exit_code: integer
  stdout_hash: string
  stderr_hash: string
  output_artifact_refs: []
  resource_usage: object
  runtime_fingerprint: string
  sandbox_profile_id: string
  replay_identity_ref: string
```

## 8. Failure states

```text
sandbox_timeout
sandbox_memory_limit
sandbox_stdout_limit
sandbox_policy_veto
sandbox_network_denied
sandbox_filesystem_violation
sandbox_malformed_output
sandbox_runtime_crash
```

Failure is a witness state. It must not silently retry under weaker settings.

## 9. Proof checker exception

A proof checker may run in a more privileged cached environment only if the proof authority profile declares the environment, dependency lock, and replay method. The checker still cannot write canonical claim status directly.

---

## Conformance note

This document is part of the v1.6 Draft 1 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
