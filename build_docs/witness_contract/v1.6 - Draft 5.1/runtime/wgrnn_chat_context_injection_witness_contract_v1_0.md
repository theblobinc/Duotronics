# WG-RNN Chat Context Injection Witness Contract

Status: active Draft 4.1 runtime contract.  
Generated: 2026-05-09.  
Applies to: browser/chat, API chat, Agent Lab chat, and any model prompt that
injects SRNN/WG-RNN cognition state.

## Purpose

WG-RNN runtime state may influence chat behavior through prompt context. That
injection path is a witness boundary. Draft 4.1 requires the injected context to
be explicit, freshness-bounded, authority-scoped, and claim-constrained.

## Canonical object

```yaml
WGRNNChatContextInjectionWitness:
  schema: wgrnn-chat-context-injection@v1
  loop_id: string
  node_id: string
  request_id: string | null
  snapshot_updated_at: timestamp | null
  snapshot_source: cognition_state | diagnostics | mcp | cache | none
  contract_view_schema: srnn-wgrnn-contract-view@v1
  readiness_status: ready | warming | degraded | missing | unknown
  authority_t: number | null
  runtime_mode: sandbox | audit_only | restricted | production | unknown
  learning_mode: sandbox | audit_only | blocked | enabled | unknown
  witness_vector_present: boolean
  derived_inputs_present: boolean
  recall_context_present: boolean
  recall_context_count: integer
  temporal_freshness_policy_applied: boolean
  freshness_max_age_seconds: integer | null
  model_claim_constraint: no_unwitnessed_memory_or_capability_claims
  prompt_context_hash: sha256
  response_witness_ref: string | null
```

## Required prompt constraints

Any prompt that receives WG-RNN witness state MUST include the following logic,
whether as system text, policy metadata, or structured tool context:

1. Do not claim durable memory updates unless a witness update is present.
2. Do not claim runtime authority beyond the injected authority mode.
3. Do not claim live system status unless the readiness witness is fresh.
4. Treat recall context as evidence, not as guaranteed truth.
5. Surface missing or stale cognition state as uncertainty.
6. Keep the model-response boundary separate from the runtime-state boundary.

## Freshness rules

```yaml
WGRNNChatFreshnessPolicy:
  ready_max_age_seconds: 120
  degraded_max_age_seconds: 600
  missing_state_behavior: answer_without_memory_claims
  stale_state_behavior: disclose_stale_context_if_material
  unavailable_state_behavior: no_memory_or_runtime_claims
```

## Validation

A Draft 4.1 conformance test SHOULD assert that chat context construction emits
or can reconstruct this witness object for each request that injects cognition
state.
