# Backend Runtime Registry v1.0

**Status:** normative registry

| Runtime/store | Role | Authority limit |
|---|---|---|
| Python/FastAPI | transition API and worker implementation | may implement, may not define permanent semantic authority by language alone |
| Rust | major final control-plane candidate | may own final control plane only after policy/corpus decision |
| Lisp/SBCL | symbolic specialist layer | JSON-RPC only; circuit breaker required; no direct canonical writes |
| Julia | math kernels | isolated worker; no direct canonical writes |
| PostgreSQL | canonical transactional store | durable truth after migration |
| Milvus | vector/semantic retrieval | advisory retrieval only |
| Redis | cache/pubsub/coordination/meta-object exchange | ephemeral only |
| PHP | transitional frontend/proxy/OAuth remnants | no new backend authority |
| SQLite | legacy compatibility | no new code paths |
