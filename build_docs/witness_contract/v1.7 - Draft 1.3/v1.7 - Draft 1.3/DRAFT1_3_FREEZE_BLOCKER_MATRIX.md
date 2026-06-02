# Draft 1.3 Freeze Blocker Matrix

| Blocker | Status | Draft 1.3 disposition |
| --- | --- | --- |
| Schema-to-SQL required-field drift | Closed for active first-class v1.7 Bayesian/knot schemas | Enforced by `refs/schema_sql_persistence_registry_v1_7_draft_1_3.json` and validator persistence checks. |
| Malformed Reidemeister/Markov SQL guard test | Closed | Validator now uses explicit column lists and verifies the enum CHECK rejection path. |
| SQL fixture round trips | Closed for valid fixtures | Validator inserts every valid active fixture into an in-memory SQLite database and checks persisted required fields. |
| SQL semantic boundary ambiguity | Closed by contract | `RUNTIME_SQL_SEMANTIC_BOUNDARY_v1_7_draft_1_3.md` declares SQL persistence/coarse-guard authority and validator/kernel semantic authority. |
| TLA separation-only Bayesian/knot module | Improved, not freeze-closed | TLA now includes record-level Bayesian replay and authority-path invariants. Strict TLC remains a freeze blocker if TLC is unavailable. |
| OpenAPI minimal responses | Improved, not final API freeze | Draft 1.3 adds structured validation, conflict, lookup, and computed replay response surfaces. |
| Strict Lean/Lake build | Open in this environment | Remains freeze blocker until strict Lake build is recorded. |
| Strict TLC run | Open in this environment | Remains freeze blocker until strict TLC run is recorded. |


Draft 1.3 redo coverage hardening:
- Validator supports skip-aware stage orchestration and partial reports.
- Active Draft 1.3 registry aliases added.
- Positive fixtures cover every promoted enum branch.
- Duplicate Bayesian hypothesis IDs are semantic rejections.
- Typed knot encodings now have deeper semantic validators and negative fixtures.
