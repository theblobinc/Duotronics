# Duotronic Use Case Examples v1.0

**Status:** reference walkthroughs  
**Version:** use-case-examples@v1.0

## 1. Add a new theorem

```text
submit statement
-> normalize notation
-> create CanonicalMathObject references
-> create MathClaim(status=normalized_claim)
-> submit proof artifact
-> run proof checker in sandbox
-> create ProofCheckerRunWitness
-> policy evaluate theorem promotion
-> human review if required
-> status transition to machine_checked_theorem or rejected
-> replay package created
```

Key rule: a theorem is not accepted because a human or model says it is true. It is accepted only under a configured proof authority or review policy.

## 2. Langlands computational experiment

Example: compute local Euler factors for a modular-form candidate and compare to an elliptic-curve L-function sample.

```text
register elliptic curve object
-> register modular form object
-> register claimed bridge
-> run Python/Sage/PARI computation in sandbox
-> create InterpreterRunWitness
-> create LocalFactorCheckWitness
-> set bridge status=computational_evidence
-> policy prevents theorem promotion unless proof witness exists
```

The experiment may support a claim. It does not prove the global correspondence by itself.

## 3. Multimodal WG-RNN update

```text
video frame payload
-> multimodal ingest schema validation
-> temporal deltas for tracks
-> SRNN oracle job
-> identity oracle emits witness_event_id
-> WGRNN feature vector
-> policy-gated memory update
-> MemoryUpdateRecord
-> replay identity preserved
```

Fast recurrent state may help scheduling or memory. It does not become external-world truth.

## 4. MCP endpoint introspection

```text
operator submits MCP query
-> policy preflight checks endpoint profile
-> MCP JSON-RPC request
-> response captured as SRNNMCPQueryWitness
-> facts extracted as candidate witnesses
-> canonicalization if schema known
-> no direct authority unless endpoint profile permits
```

---

## Conformance note

This document is part of the v1.6 Draft 2 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
