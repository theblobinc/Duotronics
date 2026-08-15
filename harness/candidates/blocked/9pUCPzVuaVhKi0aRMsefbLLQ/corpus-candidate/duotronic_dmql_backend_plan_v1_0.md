# Duotronic DMQL Backend Plan v1.0

**Status:** Draft 2 implementation plan  
**Purpose:** Define how the Duotronic Mathematical Query Language maps to PostgreSQL, Milvus/vector search, and witness stores.

---

## 1. Query classes

DMQL must support:

1. object lookup;
2. theorem/conjecture status search;
3. proof witness search;
4. computational evidence search;
5. Langlands object search;
6. interpreter result search;
7. contradiction search;
8. review ticket search;
9. MCP observation search.

---

## 2. PostgreSQL mapping

Relational indexes should cover:

```text
canonical_math_objects(object_id, family_id, status)
canonical_witness_facts(witness_id, object_id, trust_status)
proof_witnesses(target_object_id, checker_id, result)
interpreter_run_witnesses(runtime, result_status)
policy_decisions(action, approved, created_at)
human_review_tickets(status, ticket_kind, deadline)
mcp_tool_call_witnesses(tool_name, risk, principal_id, ok)
```

---

## 3. Vector search mapping

Vector indexes should cover:

1. theorem statement embeddings;
2. claim/evidence text;
3. proof summaries;
4. error messages;
5. mathematical domain descriptions;
6. user-facing documentation.

Vector results are never authority by themselves.

---

## 4. Example queries

```text
FIND theorem WHERE family = "number_theory" AND proof_checker = "lean"
FIND conjecture WHERE domain = "langlands" AND has_computational_evidence = true
FIND witness WHERE tool_name = "minecraft_ingest_multimodal_witness" AND ok = true
FIND object WHERE statement CONTAINS "automorphic L-function"
```

---

## 5. Result envelope

Every DMQL result must include:

```yaml
DMQLResult:
  result_id: string
  object_ref: string
  rank: number
  authority_scope: string
  trust_status: string
  evidence_refs: []
  query_trace_id: string
```
