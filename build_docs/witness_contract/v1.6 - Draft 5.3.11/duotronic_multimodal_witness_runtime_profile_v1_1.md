# Multimodal Witness Runtime Profile v1.1

**Status:** Draft 2 runtime profile  
**Purpose:** Specify current video/audio/image/CV/sensor/fused witness ingestion based on SRNN multimodal pipeline and MCP tools.

---

## 1. Ingest path

```text
RTSP/WebRTC/CV worker
-> multimodal ingest service
-> schema validation
-> temporal delta enrichment
-> MCP minecraft_ingest_multimodal_witness
-> SRNN world/oracle job queue
-> WG-RNN witness event
```

---

## 2. Frame witness schema

```yaml
FrameWitness:
  schema: xavi.multimodal.frame_witness.v1
  stream:
    stream_id: string
    transport: rtsp | webrtc | other
    source_uri: string
    modality: video | audio | image | cv | sensor | fused
  frame:
    frame_id: string
    ts_ms: integer
    width: integer
    height: integer
    coordinate_space: pixel | normalized
  objects:
    - label: string
      confidence: number
      track_id: string | null
      bbox:
        x: number
        y: number
        w: number
        h: number
      temporal:
        dx_px: number
        dy_px: number
        speed_px_s: number
        area_delta_px2: number
        dt_ms: integer
```

---

## 3. Required validation

1. modality in allowlist;
2. positive frame dimensions;
3. confidence between 0 and 1;
4. bbox width/height positive;
5. detection count bounded;
6. source stream registered or auto-registered with audit flag;
7. payload JSON parseable;
8. MCP tool result recorded.

---

## 4. Authority rule

Multimodal observations are raw or candidate witnesses by default.

They may support:

1. object tracking;
2. temporal action inference;
3. audio-visual sync;
4. speech-action binding;
5. world-state support;
6. prediction-error updates.

They may not prove mathematical facts or truth claims without profile-specific bridge rules.

---

## 5. Temporal identity

Temporal identity must include:

```text
stream_id
frame_id
ts_ms
track_id where present
source_uri hash
model/oracle id
```

---

## 6. Current implementation notes

Draft 2 reflects:

1. FastAPI service endpoints: `/health`, `/schema`, `/streams/register`, `/streams`, `/streams/{stream_id}/ingest`, `/ingest/frame`;
2. NVENC/NVDEC deployment blueprint for GPU VM;
3. temporal enrichment fields;
4. MCP forwarding to `minecraft_ingest_multimodal_witness`.

## Draft 4 carry-forward update - 2026-05-08

This document is retained in the v1.6 Draft 4 corpus as part of the full Draft 3
carry-forward. Draft 4 adds newer SRNN Server runtime observations rather than
removing this baseline. For current Draft 4 interpretation, read:

- `README_v1_6_draft_4.md`
- `duotronic_draft4_srnn_source_refresh_2026_05_08.md`
- `duotronic_srnn_federated_runtime_stack_profile_v1_0.md`
- `duotronic_srnn_gpu_worker_llama_server_runtime_profile_v1_0.md`
- `runtime/llama_server_runtime_readiness_contract_v1_0.md`

Draft 4 updates the runtime boundary with the current SRNN compose stack,
per-node `wg-rnn` service, GPU-worker llama-server large-model path, runtime
model manifest/smoke/bench endpoints, memlock diagnostics, and Agent Lab/MCP
backup-log witness handling. This update does not claim live production
certification; it records the source-observed contract and follow-up validation
requirements.
