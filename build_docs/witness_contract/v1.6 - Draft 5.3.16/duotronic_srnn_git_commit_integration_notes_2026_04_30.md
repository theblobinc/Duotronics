# SRNN Git Commit Integration Notes — 2026-04-30

**Status:** Draft 2 source integration note

## 1. Duotronics repository

Observed current relevant Duotronics commit:

```text
ac46d00 — new v1.6 draft 1
```

Draft 2 is a corpus continuation and should be committed as a new v1.6 Draft 2 corpus path.

## 2. SRNN server commits integrated

### 2.1 `3b52b6a` — Auto-register identity oracle adapters

Behavior:

1. Importing `srnn.oracles` registers built-in identity adapters.
2. Identity adapters convert structured payloads into WG-RNN witness events.
3. Heavyweight ML model installation is not required for these identity paths.

Draft 2 impact:

- Oracle adapter registration is now documented as normal backend behavior.
- The corpus treats structured payload adapters as witness bridges.

### 2.2 Direct filesystem and command execution MCP tools

Behavior:

1. Adds `write_file_system`.
2. Adds `execute_system_command`.
3. Adds auto backup/git sync controls:
   - `MCP_AUTO_BACKUP_ON_MUTATION`
   - `MCP_AUTO_GIT_SYNC`
   - `MCP_AUTO_GIT_PUSH`
4. Redacts sensitive fields in audit logs.

Draft 2 impact:

- Mutation tools are classified as high-risk or elevated-risk.
- Backup and git sync become required mutation witnesses.
- Audit redaction is normative.

### 2.3 Identity oracle adapters for temporal witnesses

Behavior:

- Adds adapters for world state, action, reward, video, object tracking, optical flow, temporal action, audio segment, music, sound event, speech transcript, speech synthesis, projection, prediction error, cross-modal binding, AV sync, speech-action binding, and oracle consensus.

Draft 2 impact:

- Witness families are expanded to cover structured temporal and multimodal evidence.

### 2.4 Multimodal ingest service

Behavior:

- FastAPI ingest service receives RTSP/WebRTC detections.
- Validates strict frame witness schemas.
- Computes temporal deltas.
- Forwards to MCP `minecraft_ingest_multimodal_witness`.

Draft 2 impact:

- Multimodal runtime profile v1.1 added.

### 2.5 Minecraft MCP action/witness tools

Behavior:

- Adds collect, attack, follow, stop_follow, look_at, and multimodal ingest tools.
- Adds policy scope and approval entries.

Draft 2 impact:

- External Minecraft actions are modeled as policy-gated action witnesses.

### 2.6 Job worker witness event persistence

Behavior:

- Oracle job worker copies `witness_event_id` from oracle result payload into job success record.

Draft 2 impact:

- Task queue schema requires `witness_event_id` as an output linkage field.

---

## 3. Integration rule

The corpus should treat repository commits as source evidence. A code change is not a spec change until a corpus document records the behavior and maps it to witness, policy, and replay semantics.
