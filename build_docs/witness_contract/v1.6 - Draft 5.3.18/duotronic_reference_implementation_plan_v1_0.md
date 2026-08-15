# Duotronic Reference Implementation Plan v1.0

**Status:** Draft 2 reference implementation roadmap  
**Purpose:** Define the minimum runnable implementation needed to demonstrate v1.6 conformance.

---

## 1. Minimum target

A minimal reference implementation must provide:

1. FastAPI transition API;
2. PostgreSQL schema and migrations;
3. Redis queue for ephemeral coordination;
4. Milvus or vector-index adapter for semantic search;
5. Python interpreter sandbox;
6. Julia bridge stub;
7. Lisp/SBCL bridge stub;
8. proof checker runner stub;
9. policy engine;
10. human review queue;
11. MCP observation ingester;
12. conformance fixture runner.

---

## 2. Demo path

The first demo should:

1. create a `CanonicalMathObject` for a simple theorem;
2. attach an informal claim witness;
3. run a Python computation witness;
4. reject theorem promotion without proof;
5. attach a Lean/Coq placeholder proof witness;
6. run checker in mocked accepted mode;
7. require human review;
8. promote to theorem only after policy approval;
9. export replay package;
10. query via DMQL.

---

## 3. Docker compose stack

Minimum services:

```text
duotronic-api
duotronic-postgres
duotronic-redis
duotronic-vector
duotronic-worker
duotronic-sandbox-python
duotronic-sandbox-julia
duotronic-sandbox-sbcl
duotronic-admin-web
```

---

## 4. Conformance levels

```text
L0: schema-only
L1: API plus database
L2: policy plus replay
L3: interpreter sandbox
L4: proof-checker integration
L5: MCP/SRNN integration
L6: distributed node federation
```

Draft 2 expects the first implementation to target L3 or L4 before any production deployment.
