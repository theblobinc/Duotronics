# Cognition Step Migration and Snapshot Profile

**Status:** Research specification draft  
**Version:** cognition-step-migration@v1.1  
**Document kind:** Markdown specification  
**Primary purpose:** Document compatible `step` handling and snapshot rules for cognition state.  
**Draft:** v1.6 Draft 3 updated source refresh  
**Generated:** 2026-04-30T18:15:00Z

---

## 1. Purpose

The previous Draft 3 noted a cognition-loop schema issue around `step`. The current source adds both a compatibility migration and runtime derivation logic. This profile makes both patterns canonical.

## 2. Compatibility migration

The additive migration may add:

```sql
ALTER TABLE srnn.srnn_cognition_snapshots
ADD COLUMN IF NOT EXISTS step BIGINT NOT NULL DEFAULT 0;
```

It may backfill `step` from:

1. `state_json.native_index`;
2. `state_json.step_count`;
3. `state_json.step`;
4. fallback `0`.

The migration is safe to rerun and should create an index on `step`.

## 3. Runtime derivation rule

Even when the physical column exists, tools should remain compatible with snapshots where `step` must be derived from `state_json`.

Normative derivation order:

```text
native_index > step_count > step > 0
```

## 4. First temporal snapshot rule

When a cognition loop receives its first temporal state, the runtime should save a snapshot immediately, even if the usual periodic snapshot interval has not elapsed.

Reason: temporal state initialization changes replay semantics and must be recoverable.

## 5. Query rule

Tools must not hard-fail because `step` is missing. They must either:

1. read the physical `step` column if present; or
2. derive step from JSON; or
3. return a schema-diagnostic witness.

## 6. Diagnostic witness

```yaml
CognitionStepCompatibilityWitness:
  table: srnn_cognition_snapshots
  physical_step_column_present: boolean
  derivation_used: native_index | step_count | step | fallback_zero
  row_count_checked: integer
  incompatible_rows: integer
  migration_recommended: boolean
```
