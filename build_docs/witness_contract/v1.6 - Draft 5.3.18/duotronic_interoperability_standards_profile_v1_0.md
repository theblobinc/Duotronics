# Duotronic Interoperability and Standards Profile v1.0

**Status:** Draft 2 normative standards profile  
**Purpose:** Align Duotronic internal protocols with widely usable external standards.

---

## 1. API standards

Transition HTTP APIs should publish:

1. OpenAPI 3.1 schema;
2. JSON Schema 2020-12 payload definitions;
3. RFC 9457-style problem detail responses;
4. idempotency-key support for mutation endpoints;
5. pagination with stable cursors;
6. HATEOAS-style links where useful for review tickets and object transitions.

---

## 2. Cryptographic standards

Authority-bearing objects must use:

```text
hash_algorithm: SHA3-256
signature_format: JWS or detached JWS
canonicalization: deterministic JSON canonicalization or declared byte serializer
```

Allowed transitional hashes:

```text
shake256_512
sha3-256
blake3
```

If a non-default hash is used, the algorithm must appear in the hash string.

---

## 3. Proof standards

Supported proof/prover identities must include:

1. proof assistant name;
2. version;
3. container or build hash;
4. dependency closure hash;
5. proof artifact hash;
6. checker result.

The corpus may interoperate with Dedukti, TPTP, SMT-LIB, Lean, Coq, Isabelle, Agda, Metamath, or other proof formats where a profile declares semantics.

---

## 4. Observability standards

Runtime traces should use:

1. W3C trace context;
2. OpenTelemetry semantic conventions where applicable;
3. Prometheus metrics naming;
4. structured JSON logs;
5. redacted sensitive fields.

---

## 5. MCP standards

MCP tool-call records must include:

```yaml
MCPToolCallWitness:
  server_name: string
  tool_name: string
  principal_id: string
  required_scope: string
  risk: string
  approval_required: boolean
  args_hash: string
  redacted_args_ref: string
  result_hash: string
  elapsed_ms: number
  ok: boolean
```

For mutating tools, the witness must also link backup and git-sync records where applicable.

---

## 6. Compatibility policy

Internal protocol innovation is allowed. External standards alignment is required when it improves tooling, safety, or implementation portability without weakening witness semantics.
