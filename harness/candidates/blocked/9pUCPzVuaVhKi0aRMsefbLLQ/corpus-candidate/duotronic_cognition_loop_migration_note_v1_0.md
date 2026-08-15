# Cognition Loop Migration Note v1.0

**Status:** Draft 2 migration note  
**Observed issue:** MCP `cognition_loops` returned `column "step" does not exist`.

---

## 1. Interpretation

The live tool expected a `step` column that was not present in the current backing schema. This indicates one of:

1. database schema is older than the tool code;
2. tool query has drifted from the actual table;
3. fallback endpoint maps to a different schema;
4. migration was not applied;
5. read-only query targets the wrong database or view.

---

## 2. Required schema compatibility rule

Any cognition loop table or view used by MCP must expose a stable query surface:

```yaml
CognitionLoopView:
  loop_id: string
  latest_step: integer
  latest_snapshot_ts: string
  state_hash: string
  runtime_status: string
```

If raw storage uses a different field name, create a view or compatibility alias.

---

## 3. Migration plan

1. Identify actual table queried by `cognition_loops`.
2. Add a compatibility view named `cognition_loop_summary_v1`.
3. Map `step` or equivalent source field to `latest_step`.
4. Update MCP query to use the view.
5. Add test fixture.
6. Record `SchemaMigrationWitness`.
7. Re-run `mcp_self_test` and `cognition_loops`.

---

## 4. Release blocker

A release candidate must not ship with cognition tools returning schema errors.
