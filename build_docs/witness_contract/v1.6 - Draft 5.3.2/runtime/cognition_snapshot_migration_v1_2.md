# Cognition Snapshot Migration v1.2

Status: mandatory migration profile.

## Problem

Older tools query `srnn_cognition_snapshots.step`. Some deployments store step only inside `state_json`, producing:

```text
column "step" does not exist
```

## Required behavior

A conforming Draft 3 runtime must support both:

1. top-level `step BIGINT`; and
2. fallback derivation from `state_json`.

## Derivation order

```text
native_index > step_count > step > 0
```

## Migration

Apply:

```text
executable/sql/001_cognition_step_and_witness_runtime.sql.md
```

## Replay boundary

`step` is compatibility metadata. It must not override a stronger `TemporalWitness` replay coordinate.

## Verification

Run:

```text
mcp_self_test
cognition_loops
cognition_snapshot(loop_id="chrono-main")
recurrent_witness_state(loop_id="chrono-main")
```

Closure requires no `column "step" does not exist` error.

