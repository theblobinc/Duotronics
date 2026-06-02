# Polyglot Runtime Justification v1.0

Status: design rationale.

## Problem

The stack includes Python/FastAPI, PostgreSQL, Milvus, Redis, Lisp/SBCL, Julia, JavaScript/TypeScript SDKs, and optional PHP/UI surfaces. This must be justified to avoid accidental complexity.

## Runtime roles

| Runtime | Role | Required? |
|---|---|---|
| Python/FastAPI | Primary API, orchestration, policy, interpreter control. | Required. |
| PostgreSQL | Durable witness, math, policy, recurrence, migration storage. | Required for production. |
| Redis | Low-latency pub/sub and cache. | Optional but recommended. |
| Milvus/vector DB | Embedding/vector retrieval. | Optional for semantic retrieval. |
| Lisp/SBCL | Symbolic bridge and homoiconic profile experiments. | Optional; not truth authority. |
| Julia | Numeric/math kernels and scientific computation. | Optional; not proof authority. |
| JavaScript/TypeScript | SDK and UI clients. | Required for web clients. |
| PHP/UI packages | Legacy or portal integration surface. | Optional transitional. |

## Governance rule

Optional runtimes cannot define canonical truth. They produce computational evidence or display state. Canonical promotion requires witness identity, policy, replay, and proof/checker authority where applicable.

## Integration tests required

- Python API health.
- DB migration.
- Redis unavailable fallback.
- Vector DB unavailable fallback.
- Lisp disabled fallback.
- Julia disabled fallback.
- SDK request/response schema test.

