# External activation evidence protocol

This protocol lets MCP drive contract-development activations that must run outside the chat environment while keeping the Witness Contract corpus isolated from the live runtime.

## Two-pass flow

1. Run the selected `witness_activation_gate_<gate_id>` MCP command.
2. The Compose sandbox runs the local preconditions and writes `external-attestation-requests.json`.
3. Send the selected request, corpus subject commitment, image metadata, and relevant probe outputs to an independently authorized external executor.
4. The executor performs the real activation/build/ceremony/drill in its governed environment.
5. Its attestor constructs the evidence envelope below, signs the restricted canonical JSON payload with ML-DSA-87, and returns only the public envelope.
6. Put it at `harness/evidence/<gate_id>.json`.
7. Rerun the same MCP gate command. The sandbox recomputes the stable measurement and verifies claims, time bounds, subject, result ID, issuer scope, trust status, self-issuance policy, payload commitment, and signature.

The first pass is expected to return blocked because evidence is absent. The result ID remains stable as long as the contract subject and relevant deterministic probe checks are unchanged.

## Unsigned payload

The signed payload is the complete evidence object except `signed_payload_shake256_512` and `signature_base64url`. Serialize with UTF-8 JSON using sorted keys, `,` and `:` separators, and no NaN/Infinity.

Required top-level fields:

- `schema`: `duotronic-external-gate-evidence/v1`
- `contract_version`: `v1.6-draft-5.3.17`
- `gate_id`, `subject_id`, `issuer_id`, and `key_id`
- UTC `issued_at` and `expires_at`
- nonempty values for every gate-specific item under `claims`
- `probe.run_id`, `probe.exit_code`, and the request's `probe.result_id`
- `signature_suite`: `ML-DSA-87`

Set `signed_payload_shake256_512` to the lowercase 128-hex-character SHAKE256 digest of the canonical unsigned payload with a 64-byte output. Sign the same canonical bytes with ML-DSA-87 and encode the signature as unpadded base64url.

## Trust registry

`harness/evidence/trust_registry.json` contains only public keys:

```json
{
  "schema": "duotronic-external-attestor-trust-registry/v1",
  "keys": [
    {
      "issuer_id": "independent-formal-verifier-1",
      "key_id": "mldsa87-formal-2026-01",
      "status": "active",
      "scopes": ["formal-verifier"],
      "managed_by_harness": false,
      "public_key_base64url": "UNPADDED_ML_DSA_87_PUBLIC_KEY"
    }
  ]
}
```

The private key must remain in the external attestor/HSM. For `external_governance_authorization` and `production_key_ceremony`, `managed_by_harness` must be false and the signing service must be operationally independent of the harness.

## Fail-closed results

A missing, stale, malformed, falsey-claim, wrong-subject, wrong-measurement, wrong-scope, inactive-key, self-issued, commitment-mismatch, or invalid-signature envelope leaves the gate blocked/failed. No failure path connects to runtime or changes authority.
