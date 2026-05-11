# SDK Threat Model Security Closure Plan

**Status:** Research specification draft  
**Version:** sdk-threat-closure@v1.0  
**Document kind:** Markdown specification  
**Primary purpose:** Translate the SDK STRIDE threat model into Draft 3 closure requirements.  
**Draft:** v1.6 Draft 3 updated source refresh  
**Generated:** 2026-04-30T18:15:00Z

---

## 1. Purpose

The SDK STRIDE threat model identifies several critical and high-priority gaps. This document converts those gaps into v1.6 Draft 3 closure requirements.

## 2. Critical closure requirements

### 2.1 Response integrity signatures

All API responses that can influence witness state, policy state, proof status, or claim promotion must include a verifiable response signature.

Minimum envelope extension:

```yaml
response_signature:
  algorithm: hmac-sha256 | rsa-pss-sha256 | ed25519
  key_id: string
  signed_fields:
    - ok
    - request_id
    - envelope_id
    - policy_decision_id
    - replay_identity_ref
    - result_hash
    - timestamp
  signature: string
```

SDKs must verify the signature before returning a successful high-authority result.

### 2.2 Request signatures and replay protection

Mutation-capable requests must include:

```yaml
request_signature:
  algorithm: hmac-sha256 | ed25519
  key_id: string
  timestamp: string
  nonce: string
  canonical_request_hash: string
  signature: string
```

The server must reject stale timestamps, reused nonces, body-hash mismatches, and unknown key IDs.

### 2.3 Fine-grained scopes

API keys must encode or resolve scopes, including at minimum:

- `duotronic:read`;
- `duotronic:witness:write`;
- `duotronic:policy:evaluate`;
- `duotronic:replay:create`;
- `duotronic:proof:submit`;
- `duotronic:claim:propose`;
- `duotronic:claim:promote`;
- `duotronic:admin:review`.

### 2.4 Append-only audit log verification

Audit records must be immutable or append-only and support integrity checking:

```yaml
AuditIntegrityRecord:
  audit_entry_id: string
  prev_hash: string
  entry_hash: string
  chain_hash: string
  timestamp_authority: string
  signer: string
  signature: string
```

## 3. High-priority closure requirements

1. TLS pinning documentation for high-assurance deployments.
2. Proof checker timeout and resource limits.
3. Constant-time comparison for signatures and tokens.
4. Generic 401/403 behavior for auth failures.
5. SDK-side timeout defaults.
6. Rate-limit response handling.

## 4. Corpus status ladder

| Item | Current status | Promotion requirement |
|---|---|---|
| SDK structure | observed | tests pass in CI |
| SDK auth helpers | observed | no credential logging test |
| Response validation | partial | signature verification added |
| Request signing | gap | implementation + replay tests |
| Scope authz | gap | server enforcement + SDK docs |
| Audit integrity | gap | append-only hash chain |
| Threat model | observed | review signoff |
