BEGIN;

CREATE SCHEMA IF NOT EXISTS srnn;

CREATE TABLE IF NOT EXISTS srnn.mcp_tool_observation_witnesses (
  observation_id TEXT PRIMARY KEY,
  tool_name TEXT NOT NULL,
  observed_temporal_witness_id TEXT,
  principal_id TEXT NOT NULL,
  principal_type TEXT NOT NULL,
  scopes JSONB NOT NULL DEFAULT '[]'::jsonb,
  request_payload_hash TEXT NOT NULL,
  response_payload_hash TEXT NOT NULL,
  policy_decision_id TEXT,
  ok BOOLEAN NOT NULL DEFAULT false,
  error TEXT,
  replay_identity_ref TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS srnn.recurrence_slot_lifecycle (
  slot_id TEXT PRIMARY KEY,
  loop_id TEXT NOT NULL,
  first_seen_temporal_witness_id TEXT,
  last_seen_temporal_witness_id TEXT,
  current_trust_status TEXT NOT NULL DEFAULT 'candidate',
  current_authority_t DOUBLE PRECISION NOT NULL DEFAULT 0,
  current_effective_authority_t DOUBLE PRECISION NOT NULL DEFAULT 0,
  decay_witness_id TEXT,
  lifecycle_counts JSONB NOT NULL DEFAULT '{}'::jsonb,
  last_update_id TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS srnn.replay_divergence_reports (
  report_id TEXT PRIMARY KEY,
  package_id TEXT NOT NULL,
  loop_id TEXT NOT NULL,
  divergence_score DOUBLE PRECISION NOT NULL,
  blocking_policy_rule TEXT,
  diff_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mcp_tool_observation_tool_time
  ON srnn.mcp_tool_observation_witnesses(tool_name, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_slot_lifecycle_loop
  ON srnn.recurrence_slot_lifecycle(loop_id, updated_at DESC);

COMMIT;
