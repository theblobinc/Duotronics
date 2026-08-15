# Duotronic v1.6 Draft 3 Next Steps

**Status:** Research specification draft  
**Version:** next-steps@v1.6-draft-3  
**Document kind:** Implementation next steps  
**Primary purpose:** List concrete implementation actions after applying Draft 3.  
**Draft:** v1.6 Draft 3  
**Generated:** 2026-04-30T17:40:00Z

---

## 1. Immediate implementation tasks

1. Add MCP recurrence query tools:
   - `query_gap_ratio`
   - `query_slot_lifecycle_stats`
   - `query_replay_divergence`
   - `query_quarantine_age`
2. Add MCP write tools only after policy review:
   - `write_witness`
   - `propose_decay`
   - `emit_meta_diagnostics`
3. Persist `MCPToolAvailabilityWitness` records from each manifest snapshot.
4. Persist `TemporalGapSummary` every runtime window.
5. Ensure every L2 tick has a witness record.
6. Add fixture tests for `AbsenceWitness` and `DecayIntentWitness`.
7. Update dashboards to show silent gap ratio, quarantine age, and replay divergence.

## 2. Source follow-up

1. Add typed schema tests for `live_recurrent_witness` payloads.
2. Add direct mutation tool tests for allowed-root rejection.
3. Add policy tests for stdio principal role mapping.
4. Add MCP self-test coverage for `MCP_ALLOWED_HOST_ROOT` and mutation sync settings.
5. Add a migration path from current cognition snapshot tables to Draft 3-compatible shape.

## 3. Corpus follow-up

1. Keep manifest documents under `refs/manifest/`.
2. Mark all target tools as unavailable unless verified.
3. Update the conformance suite with Draft 3 runtime recurrence tests.
4. Publish a fixture pack for temporal gaps and absence witnesses.
