# RC Blocker Closure Matrix — v1.6 Draft 3

Status: canonical RC-closure matrix.

| Blocker | Previous state | Draft 3 RC-closure action | Status |
|---|---|---|---|
| Missing executable OpenAPI | Prose-only API contract in older drafts. | Added `executable/openapi/duotronic_openapi_v1_6_draft_3_rc1.yaml.md`. | Closed as documentation artifact; must be exported to `.yaml` and validated in CI. |
| Missing SQL migrations | Schema documented but not executable. | Added `executable/sql/001_cognition_step_and_witness_runtime.sql.md` and `002_mcp_recurrence_tools_schema.sql.md`. | Closed as migration artifact; must be run in staging. |
| Missing formal models | Plans existed, artifact status unclear. | Added TLA+ and Lean markdown source artifacts under `formal/`. | Closed as artifact; some proofs remain explicitly stubbed. |
| Live `step` bug | `cognition_loops` returns `column "step" does not exist`. | Added mandatory migration/runbook and compatibility SQL. | Open until migration applied and MCP returns loop data. |
| No Start Here guide | Corpus hard to navigate. | Added `START_HERE_v1_6_draft_3_rc_closure.md`. | Closed. |
| Direct mutation tools under-specified | Direct host writes and commands present but insufficient enforcement text. | Added `security/direct_mutation_tool_enforcement_v1_2.md`. | Closed as policy; runtime enforcement must be verified. |
| Missing STRIDE | Threat model planned/incomplete. | Added `security/stride_threat_model_v1_2.md`. | Closed as documentation artifact. |
| Over-complex runtime stack | Polyglot stack not justified. | Added `architecture/polyglot_runtime_justification_v1_0.md`. | Closed as design rationale. |
| Undefined cognition boundaries | Loop/process ownership unclear. | Added `runtime/cognition_loop_boundary_spec_v1_0.md`. | Closed. |
| Missing rollback plan | Upgrade and rollback vague. | Added `migration/v1_5_to_v1_6_migration_and_rollback_runbook_v1_0.md`. | Closed as runbook. |
| Incomplete MCP recurrence surface | Verified vs target tools mixed. | Added `mcp/mcp_recurrence_conformance_matrix_v1_2.md` and `mcp/mcp_recurrence_tool_api_contract_v1_2.md`. | Closed as contract; runtime implementation may remain open. |
| Duplicate same-day docs | v1.0 and v1.1 existed side-by-side. | Superseded by v1.2 files and moved old files to `refs/deprecated`. | Closed. |
| No benchmarks | Signing/replay performance not defined. | Added `benchmarks/witness_runtime_benchmark_plan_v1_0.md`. | Closed as benchmark plan; measurements must be captured. |

## RC rule

A release candidate may not be declared until each row marked "must be run" has a successful witness record or a signed deferral.

