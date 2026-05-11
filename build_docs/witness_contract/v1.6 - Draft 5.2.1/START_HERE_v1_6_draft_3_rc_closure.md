# Start Here — Duotronic v1.6 Draft 3 RC Closure

Status: canonical entry point for the Draft 3 RC-closure redo.

Generated: 2026-04-30

## Why this redo exists

This corpus addresses the release-blocking issues called out in the Draft 3 review:

1. missing executable artifacts;
2. live `column "step" does not exist` cognition-loop bug;
3. difficult discoverability and mixed abstraction levels;
4. direct host mutation security gaps;
5. unclear runtime boundaries for cognition loops and MCP actors;
6. missing rollback/migration plan;
7. incomplete MCP recurrence surface and live overlay wiring.

## How to read the corpus

Start in this order:

```text
START_HERE_v1_6_draft_3_rc_closure.md
RC_BLOCKER_CLOSURE_MATRIX_v1_6_draft_3.md
implementation_readiness_gap_closure_v1_2.md
runtime/live_recurrent_witness_overlay_contract_v1_2.md
runtime/cognition_snapshot_migration_v1_2.md
mcp/mcp_recurrence_conformance_matrix_v1_2.md
security/stride_threat_model_v1_2.md
migration/v1_5_to_v1_6_migration_and_rollback_runbook_v1_0.md
refs/manifest/MANIFEST_v1_6_draft_3_rc_closure.md
```

Then read domain-specific files:

```text
executable/openapi/
executable/sql/
formal/tlaplus/
formal/lean4/
tests/
benchmarks/
architecture/
runtime/
mcp/
security/
```

## Document version rule

The canonical Draft 3 RC-closure documents use `v1_2` when they supersede same-day `v1_0`/`v1_1` documents.

Older same-day versions are retained under:

```text
refs/deprecated/draft3_superseded_same_day_docs/
```

They are historical context, not current implementation authority.

## Production-readiness boundary

This corpus closes documentation and design gaps. It does not claim that production deployment has passed all tests until the executable artifacts are run in the target environment and their evidence is attached as witness records.

