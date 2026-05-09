# Corpus Review — v1.6 Draft 1 to v1.6 Draft 2

## 1. Review goal

Draft 1 made v1.6 implementable. Draft 2 makes it more production-ready by closing remaining gaps surfaced by reviewer notes, live MCP endpoint observations, and current SRNN repository state.

## 2. Problems identified

Reviewer notes identified these gaps:

1. formal semantics not yet specified;
2. no systematic STRIDE threat model;
3. proof interchange and cryptographic standards underdefined;
4. human review workflow too coarse;
5. interpreter witnesses not yet unified with proof-carrying computation;
6. decentralized trust optional path not documented;
7. reference implementation path needed more detail;
8. SDK and OpenAPI generation not specified;
9. DMQL backend and indexing implementation not specified;
10. observability formats not specified.

Live MCP observations added these gaps:

1. live tool registry must be reflected as a witnessable surface;
2. direct filesystem and system-command tools create a higher-risk mutation class;
3. audit redaction exists and must become normative for mutation tools;
4. auto backup/git sync exists and must be specified as a mutation witness path;
5. `cognition_loops` failed against a missing `step` column, creating a schema migration concern;
6. Minecraft bridge is present but disabled, so docs must distinguish installed capability from active runtime mode;
7. MCP endpoint fallback results must be modeled as degraded-but-usable observations.

## 3. Draft 2 resolutions

Draft 2 adds:

| Gap | New or upgraded document |
|---|---|
| Formal semantics | `duotronic_formal_semantics_and_verification_v1_0.md` |
| Threat model | `duotronic_stridethreat_model_v1_0.md` |
| Proof interchange | `duotronic_proof_interchange_and_certificates_v1_0.md` |
| Human review state machine | `duotronic_human_review_state_machine_v1_0.md` |
| Standards alignment | `duotronic_interoperability_standards_profile_v1_0.md` |
| Proof-carrying computation | `duotronic_proof_interchange_and_certificates_v1_0.md` |
| MCP integration | `duotronic_mcp_server_tooling_integration_v1_0.md` |
| MCP runtime observations | `duotronic_mcp_runtime_observation_log_2026_04_30.md` |
| Mutation tools | `duotronic_direct_mutation_tools_security_addendum_v1_0.md` |
| Cognition loop schema mismatch | `duotronic_cognition_loop_migration_note_v1_0.md` |
| Observability | `duotronic_observability_opentelemetry_profile_v1_0.md` |
| Production checklist | `duotronic_production_release_checklist_v1_0.md` |

## 4. Compatibility statement

No v1.5 or v1.6 Draft 1 concept is removed by this review. Draft 2 constrains, expands, and operationalizes existing behavior.
