# Implementation Readiness Gap Closure — v1.6 Draft 2

## 1. Closure status

Draft 2 closes the second-wave gaps identified after the v1.6 Draft 1 implementation-ready package.

## 2. Newly closed gaps

| Area | Draft 1 state | Draft 2 closure |
|---|---|---|
| Formal semantics | prose and schemas | proof-assistant and TLA+ modeling plan |
| Threat model | general security | STRIDE matrix by component |
| Proof artifacts | proof witness sketches | proof interchange and certificate profile |
| Human review | broad protocol | ticket state machine and decision packet |
| Standards alignment | internal protocols | OpenAPI, problem details, JWS, SHA3-256 profile |
| MCP live tooling | endpoint contract only | live manifest/capability/self-test snapshots |
| Direct host mutation | not fully modeled | mutation-tool security addendum |
| Cognition schema drift | not captured | migration note for `step` column mismatch |
| Minecraft capability | tool docs only | installed-disabled-active state distinction |
| Observability | operations prose | OpenTelemetry and Prometheus naming profile |
| Community readiness | governance sketch | reference implementation and SDK plan |

## 3. Remaining Draft 2 open items

These are intentionally not closed because they require code or repository action:

1. Produce an executable OpenAPI file from `duotronic_api_contract_v1_0.md`.
2. Produce machine-readable SQL migrations from `duotronic_database_schema_v1_0.md`.
3. Add a real Lean or Coq model repository.
4. Add a TLA+ model for task delegation and policy gates.
5. Fix the live cognition loop schema mismatch reported by MCP (`column "step" does not exist`).
6. Verify whether Playwright browser binaries should be installed for browser tools.
7. Decide whether direct host mutation tools remain enabled in normal production.
8. Create SDK packages.
9. Add proof interchange test fixtures.

## 4. Draft 2 promotion rule

A future v1.6 release candidate should not be cut until:

1. MCP self-test is green;
2. all database schema checks pass without fallback warnings;
3. cognition tools return stable schemas;
4. mutation tools are disabled by default or governed by an approved high-risk policy;
5. proof and interpreter witnesses have fixture coverage;
6. security threat model mitigations are either implemented or explicitly waived.
