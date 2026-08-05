# SDK and OpenAPI Integration Profile

**Status:** Research specification draft  
**Version:** sdk-openapi-profile@v1.1  
**Document kind:** Markdown specification  
**Primary purpose:** Document how Python/JavaScript SDKs and OpenAPI artifacts integrate with the v1.6 runtime.  
**Draft:** v1.6 Draft 3 updated source refresh  
**Generated:** 2026-04-30T18:15:00Z

---

## 1. Purpose

This profile upgrades the previous API documentation by tying it to the current implementation artifacts: the FastAPI router, OpenAPI export, Python SDK, and JavaScript/TypeScript SDK.

## 2. Runtime API surface

The implemented API surface is grouped as follows:

| Group | Endpoints | Corpus status |
|---|---|---|
| Runtime meta | `/health`, `/version`, `/capabilities` | implementation observed |
| Math canon | `/math/objects`, `/math/claims`, `/math/domains`, `/math/query` | implementation observed |
| DBP v2 | `/dbp/envelopes`, `/dbp/envelopes/{id}`, `/dbp/wrap` | implementation observed |
| Witnesses | `/witnesses`, `/witnesses/{event_id}` | implementation observed |
| Replay | `/replay/status`, `/replay/packages`, `/replay/verify/{package_id}` | implementation observed |
| Policy | `/policy/decide` | implementation observed |
| Interpreter | `/interpreter/run`, `/interpreter/runs` | implementation observed |
| Langlands | `/langlands/objects`, `/langlands/claims` | implementation observed |
| Proofs | `/math/proofs`, `/math/conjectures` | implementation observed |
| Review | `/admin/review/queue` | implementation observed |

## 3. SDK role

The SDKs are transport helpers. They do not create canonical truth.

SDKs may:

- submit requests;
- parse response envelopes;
- validate response shapes;
- expose typed models;
- surface request IDs, envelope IDs, policy decision IDs, and replay identity refs.

SDKs must not:

- promote claims without server policy;
- declare proof validity locally;
- override policy decisions;
- treat local computation as proof;
- hide partial/error responses.

## 4. Response envelope requirements

Every SDK method must preserve:

```yaml
ApiResponse:
  ok: boolean
  request_id: string
  envelope_id: string
  policy_decision_id: string
  replay_identity_ref: string
  result: object | array | scalar | null
  error: string
```

## 5. Code generation rule

OpenAPI-generated SDK clients are allowed under generated-artifact policy, but generated files must preserve:

1. authentication header behavior;
2. timeout configuration;
3. response envelope validation;
4. error transparency;
5. no credential logging;
6. no local proof promotion.

## 6. Release blockers

Before marking SDK/OpenAPI as release-candidate ready, complete:

- response signature verification in SDKs;
- request signing helpers in SDKs;
- scope annotation per SDK method;
- replay identity preservation tests;
- SDK tests against a live or mocked OpenAPI server;
- schema generation stability checks.
