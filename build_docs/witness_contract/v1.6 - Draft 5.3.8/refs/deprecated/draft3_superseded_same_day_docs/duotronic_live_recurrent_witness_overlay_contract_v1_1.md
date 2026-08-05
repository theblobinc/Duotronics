# Live Recurrent Witness Overlay Contract

**Status:** Research specification draft  
**Version:** live-recurrent-overlay@v1.1  
**Document kind:** Markdown specification  
**Primary purpose:** Update the live recurrent witness overlay contract based on current SRNN source.  
**Draft:** v1.6 Draft 3 updated source refresh  
**Generated:** 2026-04-30T18:15:00Z

---

## 1. Purpose

The live recurrent witness overlay is the status-facing summary of the current cognition/WG-RNN state. It lets the daemon and MCP tools expose recurrence without requiring callers to inspect full snapshot rows.

## 2. Canonical loop preference

Default preferred loop order:

1. `chrono-main`
2. `social-main`
3. `contrastive-main`
4. `narrator-main`
5. `explore-main`
6. `storyboard-main`
7. `thematic-main`
8. `social-bsky-main`
9. `main`
10. `global`
11. `chronological`

Test loops are excluded unless explicitly requested. Test-loop patterns include:

- `witness-int`;
- prefix `test-`;
- suffix `-test`;
- prefix `fixture-`;
- suffix `-fixture`;
- names containing `integration`;
- names containing `mock`.

## 3. Overlay fields

```yaml
LiveRecurrentWitnessOverlay:
  loop_id: string
  node_id: string
  step_count: integer
  dominant_sector: string
  family_mass: object
  open_callbacks: object
  sector_trace: object
  regime_evidence: object
  contradiction_pressure: float
  coherence_drift: float
  temporal_state: object
  recurrent_temporal: object
  wg_rnn_runtime_last_update_record: object
  effective_authority_t: float
  freshness_state: string
  ttl_class: string
```

## 4. Daemon status integration

Daemon status should include:

```yaml
status:
  cognition: object
  live_recurrent_witness: LiveRecurrentWitnessOverlay | {}
```

The daemon must treat overlay read failure as non-fatal and return `{}`.

## 5. Authority rule

The overlay's `effective_authority_t` is read from:

1. `recurrent_witness.temporal.effective_authority_t`;
2. fallback `temporal_state.effective_authority_t`;
3. fallback `0.0`.

## 6. Use in corpus validation

The overlay is the preferred source for runtime dashboards that monitor:

- temporal authority;
- freshness;
- current dominant sector;
- last WG-RNN update;
- quarantine conditions;
- loop selection correctness.
