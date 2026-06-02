# Duotronic Mathematical Query Language v1.0

**Status:** reference query contract  
**Version:** math-query-language@v1.0

## 1. Purpose

DMQL is a minimal query layer for mathematical objects, claims, witnesses, proof status, computations, and Langlands bridges. It can be implemented as API JSON, CLI flags, or a textual query syntax.

## 2. JSON query shape

```yaml
MathQuery:
  select: objects | claims | witnesses | bridges | interpreter_runs | proof_runs
  where:
    domain: []
    object_kind: []
    status: []
    contains_symbols: []
    source_refs: []
    policy_mode: []
    created_after: string | null
    created_before: string | null
  include:
    evidence: boolean
    replay: boolean
    policy: boolean
    contradictions: boolean
  limit: integer
```

## 3. Text syntax

```text
FIND claims WHERE domain = langlands AND status IN (conjecture, computational_evidence)
FIND objects WHERE object_kind = LFunction AND notation CONTAINS "GL(2)"
TRACE claim <claim_id> INCLUDE evidence,policy,replay
FIND bridges WHERE bridge_kind = functorial_transfer AND status = conjectural
```

## 4. Authority rule

Search results are not proof. Query ranking is not truth. A result may expose status, evidence, and proof witnesses; it must not upgrade status.

## 5. MCP-backed query

Queries may ask an SRNN MCP endpoint for runtime state only through `duotronic_srnn_mcp_endpoint_query_contract_v1_0.md`. MCP answers enter as evidence or diagnostics unless a registered endpoint profile grants stronger authority.

---

## Conformance note

This document is part of the v1.6 Draft 2 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
