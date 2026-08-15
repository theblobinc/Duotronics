BEGIN;

CREATE SCHEMA IF NOT EXISTS srnn;

-- Fix live bug: column "step" does not exist.
ALTER TABLE IF EXISTS srnn.srnn_cognition_snapshots
  ADD COLUMN IF NOT EXISTS step BIGINT NOT NULL DEFAULT 0;

DO $$
BEGIN
  IF to_regclass('srnn.srnn_cognition_snapshots') IS NOT NULL THEN
    BEGIN
      UPDATE srnn.srnn_cognition_snapshots
      SET step = COALESCE(
        NULLIF((state_json::jsonb ->> 'native_index'), '')::BIGINT,
        NULLIF((state_json::jsonb ->> 'step_count'), '')::BIGINT,
        NULLIF((state_json::jsonb ->> 'step'), '')::BIGINT,
        0
      )
      WHERE state_json IS NOT NULL
        AND btrim(state_json) <> ''
        AND left(btrim(state_json), 1) = '{';
    EXCEPTION WHEN OTHERS THEN
      RAISE NOTICE 'step backfill skipped for some rows: %', SQLERRM;
    END;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_srnn_cognition_snapshots_step
  ON srnn.srnn_cognition_snapshots(step);

CREATE TABLE IF NOT EXISTS srnn.temporal_witnesses (
  temporal_witness_id TEXT PRIMARY KEY,
  origin TEXT NOT NULL,
  clock_family TEXT NOT NULL,
  tick_family TEXT NOT NULL,
  count BIGINT NOT NULL,
  canonical_ts DOUBLE PRECISION,
  observed_at DOUBLE PRECISION,
  ingested_at DOUBLE PRECISION,
  source_clock TEXT,
  binding_confidence DOUBLE PRECISION NOT NULL DEFAULT 0,
  authority_t DOUBLE PRECISION NOT NULL DEFAULT 0,
  freshness_state TEXT NOT NULL DEFAULT 'unknown',
  ttl_class TEXT NOT NULL DEFAULT 'policy_bound',
  replay_identity_ref TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS srnn.memory_update_records (
  update_id TEXT PRIMARY KEY,
  loop_id TEXT NOT NULL,
  node_id TEXT NOT NULL,
  temporal_witness_id TEXT REFERENCES srnn.temporal_witnesses(temporal_witness_id),
  slot_id TEXT,
  update_kind TEXT NOT NULL,
  trust_status TEXT NOT NULL,
  gate_values_before_clamp JSONB NOT NULL DEFAULT '{}'::jsonb,
  gate_values_after_clamp JSONB NOT NULL DEFAULT '{}'::jsonb,
  authority_t DOUBLE PRECISION NOT NULL DEFAULT 0,
  effective_authority_t DOUBLE PRECISION NOT NULL DEFAULT 0,
  policy_decision_id TEXT,
  replay_identity_ref TEXT NOT NULL,
  witness_event_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_memory_update_loop_time
  ON srnn.memory_update_records(loop_id, created_at DESC);

CREATE TABLE IF NOT EXISTS srnn.absence_witnesses (
  absence_witness_id TEXT PRIMARY KEY,
  expected_source TEXT NOT NULL,
  expected_temporal_witness_id TEXT REFERENCES srnn.temporal_witnesses(temporal_witness_id),
  absence_kind TEXT NOT NULL,
  decay_intent JSONB NOT NULL DEFAULT '{}'::jsonb,
  authority_scope TEXT NOT NULL,
  trust_status TEXT NOT NULL DEFAULT 'candidate',
  policy_decision_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS srnn.decay_intent_witnesses (
  decay_witness_id TEXT PRIMARY KEY,
  slot_id TEXT NOT NULL,
  curve_family TEXT NOT NULL,
  half_life_s DOUBLE PRECISION,
  proposed_rate DOUBLE PRECISION NOT NULL,
  proposed_by TEXT NOT NULL,
  reason TEXT NOT NULL,
  policy_decision_id TEXT,
  effective_from_temporal_witness_id TEXT REFERENCES srnn.temporal_witnesses(temporal_witness_id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMIT;
