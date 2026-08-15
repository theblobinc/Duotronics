# SDK, Formal Models, and Security Profile v1.1

Status: observed plus release closure plan.

## SDK packages

Observed packages:

```text
sdk/duotronic-python/
sdk/duotronic-javascript/
```

The Python SDK runner was fixed in commit `44ec052` to execute tests inside `sdk/duotronic-python` and set `PYTHONPATH` to `src`.

## Formal models

Observed formal model artifacts:

```text
formal_models/tlaplus/TaskDelegationAndPolicyCoreSpec.tla
formal_models/lean4/DuotronicCore.lean
```

## Proof status vocabulary

| Status | Meaning |
|---|---|
| Complete proof | Checked proof with no trusted hole. |
| Proof stub | Statement exists but proof is incomplete. |
| Model specified | TLA+ model exists. |
| Model checked | TLA+ model has a checked configuration. |

No production claim may cite a proof stub as completed.

## Security closure items

The SDK threat model identifies critical work:

1. response integrity signatures;
2. request authentication signatures;
3. fine-grained API key scopes;
4. immutable audit log verification;
5. TLS pinning documentation;
6. proof verification hardening.

## Signed request target

```yaml
SignedApiRequest:
  method: string
  path: string
  body_sha3_256: string
  timestamp_ms: integer
  nonce: string
  key_id: string
  signature_alg: HMAC-SHAKE256_512 | ML-DSA-87
  signature: string
```

## Signed response target

```yaml
SignedApiResponse:
  request_id: string
  response_body_sha3_256: string
  policy_decision_id: string | null
  replay_identity_ref: string | null
  timestamp_ms: integer
  signer_id: string
  signature_alg: HMAC-SHAKE256_512 | ML-DSA-87
  signature: string
```

## Release gate

Before production RC:

- Python SDK tests pass from SDK root.
- JavaScript build/tests pass.
- OpenAPI validates.
- Threat model checklist is closed or explicitly deferred.
- Lean proof stubs are labeled honestly.
- Request/response signing is implemented or release-gated.

