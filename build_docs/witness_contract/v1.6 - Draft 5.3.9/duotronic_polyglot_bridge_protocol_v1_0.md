# Duotronic Polyglot Bridge Protocol v1.0

**Status:** normative implementation contract  
**Version:** polyglot-bridge@v1.0  
**Document kind:** JSON-RPC wire protocol for Lisp, Julia, Python, and future math runtimes

## 1. Scope

This protocol governs language runtimes used by the code interpreter and math kernels. It covers Lisp/SBCL symbolic specialists, Julia math kernels, Python transition services, and future proof/math engines that use the same bridge model.

## 2. Transport

The default bridge is JSON-RPC 2.0 over one of:

1. subprocess stdin/stdout for local isolated runtimes;
2. localhost HTTP for supervised sidecars;
3. Unix domain socket for hardened local workers;
4. DBP task queue for asynchronous jobs.

Network bridge use outside localhost requires mTLS and policy approval.

## 3. Common request envelope

```yaml
BridgeRequest:
  jsonrpc: "2.0"
  id: string
  method: string
  params:
    bridge_version: "1.0"
    runtime_profile_id: string
    request_kind: eval | kernel_call | proof_check | normalize | health | shutdown
    input_envelope: DBPv2Envelope
    resource_limits:
      cpu_ms: integer
      wall_ms: integer
      memory_mb: integer
      stdout_bytes: integer
      stderr_bytes: integer
    replay:
      replay_identity_ref: string
      deterministic_required: boolean
    policy_decision_id: string
```

## 4. Common response envelope

```yaml
BridgeResponse:
  jsonrpc: "2.0"
  id: string
  result:
    ok: boolean
    output_envelope: DBPv2Envelope | null
    stdout_hash: string | null
    stderr_hash: string | null
    artifacts: []
    resource_usage:
      cpu_ms: integer
      wall_ms: integer
      memory_peak_mb: integer
    replay_identity_ref: string
    runtime_fingerprint: string
  error:
    code: string
    message: string
    data: object
```

## 5. Methods

```text
duotronic.runtime.health
duotronic.runtime.eval
duotronic.runtime.kernel_call
duotronic.runtime.normalize
duotronic.runtime.proof_check
duotronic.runtime.cancel
duotronic.runtime.shutdown
```

## 6. Lisp/SBCL bridge

Lisp is a symbolic specialist layer. Required properties:

1. deterministic JSON serialization;
2. circuit breaker after repeated timeouts or malformed responses;
3. no canonical database writes;
4. parity fixtures against Python for declared algorithms such as `phi_step`;
5. result emitted as `InterpreterRunWitness` or `NormalizerWitness`.

Example method:

```json
{
  "jsonrpc": "2.0",
  "id": "req-lisp-001",
  "method": "duotronic.runtime.kernel_call",
  "params": {
    "bridge_version": "1.0",
    "runtime_profile_id": "sbcl-symbolic-v1",
    "request_kind": "kernel_call",
    "function": "phi_step",
    "args": [{"state": [1, 2, 3], "t": 12}]
  }
}
```

## 7. Julia bridge

Julia is a math-kernel layer, not policy authority. Required properties:

1. package environment lockfile;
2. deterministic seed capture;
3. artifact hash capture;
4. no durable writes except declared output artifacts;
5. failure converted to witness state, not silent fallback.

## 8. Python bridge

Python/FastAPI is the transition backend. Python interpreter runs must be isolated from the API process when executing untrusted or user-provided code.

## 9. Circuit breaker

```yaml
CircuitBreaker:
  failure_window_s: 300
  timeout_threshold: 3
  malformed_response_threshold: 2
  memory_violation_threshold: 1
  open_duration_s: 120
  half_open_probe_count: 1
```

An open circuit returns `runtime_unavailable` and creates an ops witness.

## 10. Authority boundary

Runtime output is never self-promoting. Every bridge result must be canonicalized and policy-gated before it may update a mathematical claim, witness memory, or task outcome.

---

## Conformance note

This document is part of the v1.6 Draft 2 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
