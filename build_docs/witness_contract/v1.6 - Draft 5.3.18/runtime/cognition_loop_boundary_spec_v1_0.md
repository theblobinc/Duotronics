# Cognition Loop Boundary Specification v1.0

Status: canonical Draft 3 boundary document.

## Process ownership

A cognition loop may run as:

1. in-process daemon loop;
2. separate worker/service;
3. MCP-managed actor;
4. test fixture loop.

Each loop must declare its mode.

```yaml
CognitionLoopRuntime:
  loop_id: string
  node_id: string
  runtime_mode: in_process | worker_service | mcp_actor | fixture
  owner_process: string
  heartbeat_interval_s: number
  state_store: postgres | sqlite | redis | memory | mixed
  witness_store: postgres | sqlite | object_store | mixed
  failure_policy: quarantine | restart | degrade_authority | stop
```

## Failure boundaries

L2 failure must not silently promote stale memory. L3 failure must not mutate policy defaults. L4 proposal failure must not alter canonical architecture. L5 failure must leave governance-sensitive changes pending.

## Scaling rule

Loop state can be sharded by loop ID, but replay packages must contain enough temporal and memory update records to reconstruct each shard.

