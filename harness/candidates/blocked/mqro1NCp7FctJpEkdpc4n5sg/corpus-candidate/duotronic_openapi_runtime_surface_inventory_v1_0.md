# OpenAPI Runtime Surface Inventory

**Status:** Research specification draft  
**Version:** openapi-runtime-surface@v1.0  
**Document kind:** Markdown specification  
**Primary purpose:** Inventory the current Duotronic v1.6 API surface for Draft 3.  
**Draft:** v1.6 Draft 3 updated source refresh  
**Generated:** 2026-04-30T18:15:00Z

---

## 1. Purpose

This document records the implemented OpenAPI-facing runtime surface so the corpus can track the difference between prose specification and actual API shape.

## 2. Endpoint inventory

```yaml
duotronic_v1_api:
  prefix: /duotronic/v1
  endpoints:
    - GET /health
    - GET /version
    - GET /capabilities
    - GET /math/objects
    - GET /math/objects/{object_id}
    - GET /math/claims
    - GET /math/domains
    - POST /math/query
    - GET /dbp/envelopes
    - GET /dbp/envelopes/{envelope_id}
    - POST /dbp/wrap
    - GET /witnesses
    - GET /witnesses/{event_id}
    - GET /replay/status
    - POST /policy/decide
    - POST /replay/packages
    - GET /replay/verify/{package_id}
    - POST /interpreter/run
    - GET /interpreter/runs
    - GET /langlands/objects
    - GET /langlands/claims
    - GET /math/proofs
    - GET /math/conjectures
    - GET /admin/review/queue
```

## 3. Implementation notes

The current router uses a standard response envelope and graceful degradation for tables that are not present. This is correct for a draft implementation but must be tightened for release:

- missing tables should have structured component status;
- error responses should use HTTP status codes, not only envelope `ok=false`;
- response schemas should be declared in OpenAPI rather than mostly `{}`;
- all mutation-capable endpoints should require request signatures and scopes.

## 4. OpenAPI schema hardening backlog

1. Add explicit Pydantic response models.
2. Add explicit request models for all POST endpoints.
3. Add auth/security scheme definitions.
4. Add standard error schema.
5. Add response signature schema.
6. Add replay identity and policy decision references to all relevant responses.
7. Add examples for each endpoint.
