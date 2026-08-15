# WGRNN Firehose Integration Profile v1.0

Status: observed working-tree profile.

## Purpose

The WGRNN Firehose package is an emerging UI/runtime surface for observing high-volume WG-RNN activity. Draft 3 Completed records it as a visualization and interaction layer, not a canonical truth layer.

## Observed package layout

```text
packages/wgrnn_firehose/
  API.md
  controller.php
  css/wgrnn-firehose.css
  js/main.js
  js/constants.js
  js/utils.js
  js/mixins/hud.js
  js/mixins/line-builders.js
  js/mixins/normalizer.js
  js/mixins/renderer.js
  js/mixins/stream-manager.js
  single_pages/
  controllers/
```

## Role in v1.6 Draft 3

The Firehose package should expose or render:

- live recurrence events;
- gate values;
- temporal authority;
- stale/fresh state;
- quarantine and promotion flow;
- memory slot lifecycle;
- replay divergence signals;
- policy clamp and L3/L4/L5 diagnostics.

## Authority boundary

Firehose UI output is observation evidence. It is not canonical memory unless linked to witness event IDs and replay identity records.

## Required witness linkage

Each displayed firehose event should include, when available:

```yaml
FirehoseDisplayEvent:
  event_id: string
  witness_event_id: string | null
  temporal_witness_id: string | null
  memory_update_id: string | null
  loop_id: string
  node_id: string
  update_kind: string
  trust_status: string
  effective_authority_t: number
  freshness_state: string
  policy_decision_id: string | null
  replay_identity_ref: string | null
```

## Frontend modularization rule

The observed move toward `constants.js`, `utils.js`, and mixins is good. The Firehose UI should keep these concerns separate:

- constants: schema names, thresholds, event names;
- normalizer: maps API/MCP payloads into stable UI event records;
- stream manager: connection and backoff behavior;
- renderer: visual state;
- HUD: summary metrics;
- line builders: event text and trace rows.

## Security rule

The Firehose UI must not expose raw secrets, auth headers, admin keys, tokens, or full proof sources unless policy allows them.

## Replay rule

Any UI event that triggers a state-changing action must be replay-linked through a policy decision and a witness event.

