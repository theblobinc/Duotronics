# Duotronic Runtime Recurrence Tuning Profile v1.2

Status: canonical Draft 3 RC-closure profile.

See `runtime/live_recurrent_witness_overlay_contract_v1_2.md`, `runtime/cognition_snapshot_migration_v1_2.md`, and `mcp/mcp_recurrence_conformance_matrix_v1_2.md`.

The normative requirements are:

- TemporalWitness for replay identity.
- MemoryUpdateRecord for every L2 update.
- AbsenceWitness for missing ticks.
- DecayIntentWitness for slot decay.
- Per-slot decay, not global decay.
- Similarity thresholds are reference defaults only.
- Theorem promotion requires proof/checker authority, not similarity.

