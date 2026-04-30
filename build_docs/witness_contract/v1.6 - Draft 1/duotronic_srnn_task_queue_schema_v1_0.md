# SRNN Task Queue and Oracle Schema v1.0

**Status:** normative SRNN integration contract  
**Version:** srnn-task-queue-schema@v1.0

## 1. Purpose

This document records the v1.6 task/oracle/witness loop needed by the SRNN backend. It incorporates loop IDs, node IDs, oracle job IDs, input artifact refs, replay identity refs, temporal meta objects, and persisted witness event IDs.

## 2. Oracle job input

```yaml
SRNNOracleJob:
  job_id: string
  loop_id: string
  node_id: string
  oracle_id: string
  oracle_kind: string
  input_payload: object
  input_artifact_ref: string | null
  replay_identity_ref: string | null
  status: queued | running | succeeded | failed | cancelled
  created_at: string
```

Before an oracle adapter runs, the worker must inject defaults when missing:

```text
loop_id = chrono-main
node_id = main
oracle_job_id = job_id
input_artifact_ref = job.input_artifact_ref or empty
replay_identity_ref = job.replay_identity_ref or generated replay ref
```

## 3. Oracle result

```yaml
SRNNOracleResult:
  oracle_id: string
  oracle_kind: string
  payload: object
  confidence: number
  output_ref: string | null
  input_artifact_ref: string | null
  output_artifact_ref: string | null
  replayable: boolean
  error: string | null
```

If `payload.witness_event_id` is present, job success must persist it to `srnn.oracle_jobs.witness_event_id`.

## 4. Temporal meta object

```yaml
TemporalMetaObject:
  canonical_ts: number
  observed_at: number
  ingested_at: number
  source_clock: event_time | wall_clock | media_time | game_tick | monotonic | unknown
  binding_confidence: number
  temporal_edge_weight: number
```

## 5. Truth contract

```yaml
OracleTruthContract:
  source_clock: string
  binding_confidence: number
  replay_identity_ref: string
  oracle_trust_status: candidate | canonicalized | audit_only | rejected | quarantine
  cross_oracle_confirmations: []
  requires_second_oracle: boolean
```

## 6. Witness families

Recognized v1.6 SRNN witness families include:

```text
video_frame
object_track
motion_field
temporal_action
audio_segment
music_feature
sound_event
speech_transcript
speech_synthesis
audio_visual_sync
movement_track
kinematic_state
projection
prediction_error
world_state
agent_pose
entity_state
game_event
control_action
reward_outcome
cross_modal_binding
speech_action_binding
oracle_consensus
```

## 7. Identity oracle adapters

Identity oracle adapters are allowed for already-structured payloads. They close queue-to-witness flow without requiring heavyweight ML models. They must preserve `oracle_id` contracts so real model adapters can replace them later.

## 8. Failure states

```text
oracle_missing
oracle_disabled
oracle_timeout
oracle_malformed_result
witness_event_id_missing
temporal_binding_low_confidence
second_oracle_required
replay_identity_missing
```

---

## Conformance note

This document is part of the v1.6 Draft 1 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
