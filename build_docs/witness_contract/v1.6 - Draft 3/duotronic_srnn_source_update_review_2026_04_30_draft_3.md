# SRNN Source Update Review for v1.6 Draft 3

**Status:** Research specification draft  
**Version:** srnn-source-review@2026-04-30-draft-3  
**Document kind:** Source review note  
**Primary purpose:** Document current SRNN repository changes that affect the v1.6 Draft 3 corpus.  
**Draft:** v1.6 Draft 3  
**Generated:** 2026-04-30T17:40:00Z

---

## 1. Scope

This note records current SRNN source behavior observed for Draft 3. It is not a full code audit. It identifies source changes that require corresponding specification coverage.

## 2. Current source updates

### 2.1 Identity oracle auto-registration

The oracle package imports the identity adapters as an import side effect. This makes structured temporal witness payload adapters available when the oracle package is imported.

Specification impact:

- `duotronic_srnn_task_queue_schema_v1_0.md` remains valid.
- Draft 3 adds explicit recognition that identity adapters may be a built-in registry population path.
- A runtime must still expose registry contents through diagnostics before treating adapters as available.

### 2.2 Stdio principal policy

The MCP stdio helper can default local VS Code stdio sessions to `local_admin` through `MCP_STDIO_PRINCIPAL`. The principal resolver maps configured roles to scope sets.

Specification impact:

- Draft 3 adds `duotronic_stdio_principal_policy_v1_0.md`.
- Stdio transport must be treated as a privileged local transport and not equivalent to unauthenticated remote MCP.

### 2.3 Direct mutation allowed root

Direct filesystem and command tools now check an allowed host root before executing writes or commands. The environment variable is represented as `MCP_ALLOWED_HOST_ROOT`, defaulting to `/var/www/xavi`.

Specification impact:

- Draft 3 upgrades direct mutation security requirements in `duotronic_direct_mutation_tools_security_addendum_v1_1.md`.
- Mutating tools require scope, audit logging, redaction, root bounding, and mutation sync records.

### 2.4 Live recurrent witness overlay

Daemon status now includes a `live_recurrent_witness` payload read from `ShuffleSession.read_live_recurrent_witness_overlay`. The overlay can include temporal state, recurrent temporal state, runtime last update record, effective authority, freshness state, and TTL class.

Specification impact:

- Draft 3 adds `duotronic_live_recurrent_witness_overlay_contract_v1_0.md`.

### 2.5 Cognition snapshot step derivation

Cognition state tooling no longer assumes a physical `step` column in snapshot tables. It derives step from `state_json` keys such as `native_index`, `step_count`, or `step`.

Specification impact:

- Draft 2's cognition-loop migration note remains valid and is strengthened by Draft 3.
- Schema readers must tolerate older and newer snapshot shapes.

### 2.6 Stale evidence behavior tests

Current tests assert stale ephemeral evidence is quarantined from promotion and stale slow-changing evidence degrades temporal authority.

Specification impact:

- Draft 3 formalizes stale-evidence handling in the recurrence tuning profile.

## 3. Required follow-up

1. Expose runtime slot lifecycle metrics through MCP.
2. Add explicit absence and gap ratio query endpoints.
3. Align source implementation of decay proposals with `DecayIntentWitness`.
4. Persist MCP tool availability snapshots as witness records.
