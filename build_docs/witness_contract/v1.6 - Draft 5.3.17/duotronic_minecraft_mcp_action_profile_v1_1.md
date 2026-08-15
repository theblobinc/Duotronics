# Minecraft MCP Action Profile v1.1

**Status:** Draft 2 runtime profile  
**Supersedes:** Minecraft action portions of v1.6 Draft 1

---

## 1. Modes

```text
disabled
http_bridge
local_sidecar
```

Observed Draft 2 state:

```text
mode = disabled
bridge_exists = true
```

Installed capability is not active capability.

---

## 2. Tool classes

### 2.1 Observation tools

```text
minecraft_status
minecraft_runtime_status
minecraft_list_bots
minecraft_bot_status
minecraft_world_snapshot
minecraft_inventory
minecraft_nearby_entities
minecraft_nearby_blocks
minecraft_recent_events
minecraft_export_episode
```

### 2.2 External action tools

```text
minecraft_spawn_bot
minecraft_stop_bot
minecraft_bot_chat
minecraft_bot_action
minecraft_bot_pathfind
minecraft_collect_blocks
minecraft_attack_nearest
minecraft_follow_entity
minecraft_stop_follow
minecraft_look_at
```

### 2.3 Witness ingest tools

```text
minecraft_ingest_reward
minecraft_ingest_multimodal_witness
```

---

## 3. Policy

External action tools require:

```yaml
risk: external_action
required_scope: mcp:minecraft-action
approval_required: true
```

Witness ingest tools may use:

```yaml
risk: db_write
required_scope: mcp:write
approval_required: false
```

subject to source validation and payload limits.

---

## 4. Action witness path

```text
WorldStateWitness
-> ActionCandidateWitness
-> PolicyDecision
-> MinecraftActionExecutionRecord
-> MinecraftActionOutcomeWitness
-> EpisodeReplaySlice
```

---

## 5. Bounds

External actions must declare bounded parameters:

1. radius maximum;
2. count maximum;
3. message length maximum;
4. pathfinding range;
5. follow distance;
6. timeout;
7. stale-world-state threshold.

---

## 6. Emergency controls

Required emergency controls:

```text
minecraft_stop_bot
minecraft_stop_bridge
policy_disable_minecraft_actions
```

---

## 7. Replay

Any action must be replayable as:

```yaml
MinecraftEpisodeReplay:
  bot_id: string
  start_tick: integer
  end_tick: integer
  event_refs: []
  action_refs: []
  world_state_refs: []
  outcome_refs: []
```
