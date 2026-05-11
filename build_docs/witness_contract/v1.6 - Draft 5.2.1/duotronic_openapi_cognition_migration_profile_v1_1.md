# OpenAPI and Cognition Migration Profile v1.1

Status: observed plus normative integration.

## API route families

Observed Duotronic v1.6 API families:

- health, version, capabilities;
- math objects, claims, domains, query;
- DBP envelopes and wrapping;
- witnesses;
- replay status and package creation;
- policy decision;
- interpreter runs;
- Langlands objects and claims;
- math proofs and conjectures;
- admin review queue.

## Response envelope

```yaml
ApiResponse:
  ok: boolean
  request_id: string
  envelope_id: string
  policy_decision_id: string
  replay_identity_ref: string
  result: object | list | null
  error: string
```

## Cognition step migration

Historical tools assumed a top-level `step` column in `srnn_cognition_snapshots`.

Compatible strategies:

1. add and backfill a `step` column;
2. derive step from `state_json`;
3. use both.

Reference derivation:

```text
native_index > step_count > step > 0
```

The derived integer step must not override a stronger `TemporalWitness`.

## Live recurrent witness overlay

Expected shape:

```yaml
LiveRecurrentWitnessOverlay:
  loop_id: string
  node_id: string
  step: integer
  updated_at: string
  dominant_sector: string
  family_mass: object
  open_callbacks: object
  sector_trace: object
  regime_evidence: object
  contradiction_pressure: number
  coherence_drift: number
  temporal_state: object
  recurrent_temporal: object
  wg_rnn_runtime_last_update_record: object
  effective_authority_t: number
  freshness_state: string
  ttl_class: string
```

Canonical loop IDs should be preferred over test loops unless a caller explicitly requests a test loop.

