# Duotronic v1.6 Draft 2 Full Upgrade Corpus

**Status:** generated draft corpus  
**Version:** v1.6-draft-2-full-upgrade  
**Primary purpose:** Preserve the complete v1.5 Draft 2 corpus coverage while upgrading every document path to the v1.6 backend, mathematical canon, Langlands integration, polyglot runtime, and code-interpreter plan.

## What changed from the first v1.6 zip

The first v1.6 draft only emitted a compact math-integration set. This full upgrade keeps the v1.5 Draft 2 source coverage and adds v1.6 rewrite wrappers for every listed v1.5 corpus artifact.

Coverage retained from v1.5 Draft 2:

- 55 source artifacts listed in the v1.5 release manifest;
- all core documents;
- all reference contracts and registries;
- all research profiles;
- all examples;
- all review notes;
- Markdown replacements for the JSON schema/manifest and PNG diagram artifacts.

## v1.6 backend spine

The v1.6 corpus binds Duotronics to this backend spine:

| Layer | v1.6 rule |
|---|---|
| Transactional truth | PostgreSQL-compatible durable store through DBP v2 object envelopes |
| Semantic retrieval | Milvus-compatible vector index; advisory/retrieval only |
| Coordination | Redis-compatible ephemeral cache/pubsub/queue/meta-object exchange |
| Transition API | Python/FastAPI remains active reference implementation |
| Final control plane | Rust remains a major candidate, target-neutral in specs |
| Symbolic specialist | Lisp/SBCL via JSON-RPC bridge with circuit breaker |
| Math kernels | Julia isolated as math-kernel runtime |
| Code interpreter | Python, Julia, Lisp execution through `InterpreterRunWitness` |
| Legacy PHP | transitional only; no new backend authority |

## v1.6 mathematical canon spine

The v1.6 corpus replaces polygon-only mathematical framing with a general Mathematical Canon. DPFC and polygon families remain available as carried-forward representational/research components, but they are no longer the whole math core.

The Mathematical Canon supports:

1. objects from all mathematical domains;
2. theorem, conjecture, definition, example, counterexample, computation, and analogy status;
3. proof and proof-checker witnesses;
4. interpreter-run witnesses;
5. bridges between domains;
6. Langlands objects and correspondences as first-class canon objects;
7. policy-gated promotion and demotion.

## v1.6 Langlands rule

Langlands is integrated as a first-class mathematical domain, not merely as an optional profile. The corpus canonizes the representation of Langlands objects, claims, bridges, evidence, and computations. It does not silently promote open conjectures to theorems.

## Important directories

- `README_v1_6_draft_1.md` — this overview.
- `MANIFEST_v1_6_full_upgrade.md` — complete file inventory and coverage mapping.
- `duotronic_mathematical_canon_contract_v1_0.md` — broad math canon.
- `duotronic_langlands_canon_contract_v1_0.md` — Langlands canon.
- `duotronic_all_math_witness_contract_v1_0.md` — all-domain math witnesses.
- `duotronic_code_interpreter_plan_v1_0.md` — interpreter plan.
- `refs/source_review_srnn_server_2026_04_30.md` — latest SRNN review integration.
- `refs/v1_5_to_v1_6_coverage_map.md` — exact v1.5 to v1.6 path map.

## Conformance rule

A v1.6 implementation must not claim corpus conformance unless it can show:

1. all v1.5 Draft 2 paths are either upgraded in place, redirected, or represented by a Markdown compatibility record;
2. every v1.6 mathematical object has a domain profile and claim status;
3. every interpreter run is a witness, not proof by default;
4. every backend write declares authority class, store target, replay identity, and policy decision;
5. every SRNN queue-to-witness path records witness event IDs when available.


## Implementation-readiness pass

This package has been updated after the v1.6 Draft 2 gap review. It now includes API, database, DBP envelope, policy engine, polyglot bridge, security, sandbox, deployment, operations, migration, governance, conformance, replay, admin, query-language, SRNN task queue, and MCP endpoint query specifications.

Start with:

1. `IMPLEMENTATION_READINESS_GAP_CLOSURE_v1_6_draft_1.md`
2. `duotronic_api_contract_v1_0.md`
3. `duotronic_database_schema_v1_0.md`
4. `duotronic_dbp_v2_envelope_spec.md`
5. `duotronic_policy_engine_spec_v1_0.md`
6. `duotronic_srnn_mcp_endpoint_query_contract_v1_0.md`
