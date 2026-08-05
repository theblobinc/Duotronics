# End-to-End Integration Test Suite v1.0

Status: required RC test plan.

## Test groups

1. API health and OpenAPI validation.
2. SQL migration and rollback dry run.
3. MCP manifest and policy explanation.
4. Recurrence tools conformance.
5. Live overlay no-error test.
6. Cognition snapshot migration test.
7. Direct mutation denied-path tests.
8. Proof/interchange fixture tests.
9. Replay package determinism test.
10. Firehose read-only display and redaction test.

## Required commands

```bash
python -m pytest tests/test_duotronic_draft2_phase3_suite.py -q
python -m pytest tests/test_duotronic_openapi_export.py -q
python -m pytest tests/test_duotronic_v1_6_conformance.py tests/test_duotronic_v1_6_tier2_conformance.py -q
```

## MCP checks

```text
mcp_self_test
mcp_tool_manifest
policy_explain(write_witness)
policy_explain(propose_decay)
cognition_loops
recurrent_witness_state(loop_id="chrono-main")
```

## Pass criterion

A release candidate requires a test evidence bundle with command, commit, environment, output hash, and reviewer.

