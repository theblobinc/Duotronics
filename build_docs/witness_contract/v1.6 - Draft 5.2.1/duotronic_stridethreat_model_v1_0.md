# Duotronic STRIDE Threat Model v1.0

**Status:** Draft 2 normative security profile  
**Purpose:** Provide a systematic threat model across Duotronics, SRNN, MCP tooling, polyglot interpreters, and mathematical witness authority.

---

## 1. Components in scope

1. Public or internal HTTP APIs.
2. MCP server endpoint.
3. Repository tools and git worktrees.
4. Direct filesystem and system-command MCP tools.
5. PostgreSQL, Milvus, Redis, and backup stores.
6. Interpreter sandboxes for Python, Julia, Lisp/SBCL.
7. Proof assistant integrations.
8. SRNN task queue and oracle jobs.
9. Multimodal witness ingest.
10. Minecraft/Mineflayer bridge tools.
11. Human review interface.
12. Policy engine.
13. DBP v2 envelope transport.

---

## 2. STRIDE matrix

| Threat | Example | Mitigation |
|---|---|---|
| Spoofing | Fake node submits witness as trusted runtime | mTLS or signed DBP envelope, principal IDs, key rotation |
| Tampering | Mutating canonical witness payload after policy approval | content hashes, append-only audit, JWS signatures, database constraints |
| Repudiation | Operator denies approving high-risk MCP command | audit records, redacted argument hashes, signed decisions |
| Information disclosure | Interpreter reads secrets or `.env` | deny secret paths, sandbox mounts, redacted logs |
| Denial of service | long-running Julia or Lisp process | timeout, memory/CPU limits, circuit breaker |
| Elevation of privilege | MCP tool executes host command without correct scope | scope checks, approval, policy veto, high-risk defaults |

---

## 3. Direct mutation tool threat model

Direct mutation tools include:

```text
write_file_system
execute_system_command
```

These tools are higher risk than ordinary repository worktree tools.

Required controls:

1. disabled by default in production unless an explicit policy snapshot enables them;
2. require scope `mcp:write` for filesystem writes;
3. require scope `mcp:ops-request` for host command execution;
4. must emit a `MutationToolCallWitness`;
5. must redact sensitive arguments before audit persistence;
6. must attempt backup and git sync when mutation sync is enabled;
7. must never write secret contents into normal artifact logs;
8. must be visible in admin interface;
9. must support emergency disable.

---

## 4. Lisp/SBCL bridge threat model

Threat: malicious expression attempts host escape, file read, or infinite computation.

Required mitigations:

1. JSON-RPC bridge process is isolated.
2. Only allowlisted functions are callable.
3. Raw `eval` is forbidden outside sandbox research mode.
4. Process has CPU and memory limits.
5. Filesystem is read-only unless explicitly mounted.
6. Network is disabled by default.
7. Circuit breaker trips on timeout, repeated failure, memory excess, or protocol violation.
8. Every call emits `PolyglotBridgeCallWitness`.

---

## 5. Minecraft/Mineflayer action threat model

Minecraft action tools can mutate an external world.

Tools such as collect, attack, follow, look_at, chat, pathfind, and stop_follow require action policy.

Threats:

1. unintended griefing or hostile action;
2. unbounded autonomous follow/combat loop;
3. action executed under stale world state;
4. spoofed bot ID;
5. external server terms/policy violation.

Mitigations:

1. approval-required policy for external actions;
2. bounded radius and count parameters;
3. stale world-state gate;
4. action outcome witness;
5. replayable episode export;
6. emergency bot stop.

---

## 6. Proof-system threat model

Threats:

1. forged proof artifact;
2. proof accepted by untrusted checker version;
3. theorem promoted from computation only;
4. proof checker compromised;
5. proof artifact references unavailable dependencies.

Mitigations:

1. proof hash and dependency hashes;
2. checker registry;
3. proof-status separation;
4. independent re-check option;
5. human-review or policy approval for high-value theorem status.

---

## 7. Incident states

```text
suspected_spoofing
canonical_hash_mismatch
unaudited_mutation_detected
sandbox_escape_attempt
policy_bypass_attempt
untrusted_checker_acceptance
stale_world_action_block
mcp_scope_violation
backup_sync_failure
cognition_schema_mismatch
```

Any incident state must produce a witness record and policy decision.
