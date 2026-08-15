# STRIDE Threat Model v1.2

Status: completed Draft 3 security artifact.

## Scope

This threat model covers witness contracts, MCP tools, SRNN recurrence, API/SDK access, proof artifacts, replay packages, and direct mutation tools.

## Spoofing

| Threat | Mitigation |
|---|---|
| API principal spoofing | Signed requests, scoped credentials, nonce/timestamp checks. |
| MCP principal spoofing | Explicit principal resolution, transport security, audit log. |
| Witness source spoofing | Source identity binding and policy decision IDs. |

## Tampering

| Threat | Mitigation |
|---|---|
| Witness payload tampering | Content hash, envelope signature, append-only storage. |
| Replay package tampering | Manifest hash and replay identity refs. |
| Direct file mutation | Worktree isolation, allowed-root enforcement, audit diff. |

## Repudiation

| Threat | Mitigation |
|---|---|
| User denies mutation | DirectMutationAudit with principal and diff hash. |
| Runtime denies promotion | MemoryUpdateRecord and policy decision ID. |
| Proof checker result disputed | ProofCheckerRunWitness with tool version and artifact hash. |

## Information disclosure

| Threat | Mitigation |
|---|---|
| Secrets in logs | Redaction for password, token, secret, key, authorization. |
| Proof/source exposure | Access control and hash references. |
| Firehose UI leaks | UI redaction and scope-aware display. |

## Denial of service

| Threat | Mitigation |
|---|---|
| MCP tool spam | Rate limits and policy scopes. |
| Proof verification overload | Timeouts and queue isolation. |
| Memory slot explosion | Per-slot decay, prune policies, slot lifecycle metrics. |
| Replay package bloat | Size limits and streaming manifests. |

## Elevation of privilege

| Threat | Mitigation |
|---|---|
| Read key performs write | Fine-grained scopes. |
| L3 mutates policy | L3 clamps and L4/L5 escalation. |
| Direct command bypasses review | Approval-gated high-risk ops and allowed-root checks. |
| Similarity promotes theorem | Proof authority required; similarity cannot promote theorem status. |

## Required release evidence

- request signing test;
- response signing test;
- direct mutation denied-path test;
- MCP scope boundary test;
- replay tamper detection test;
- firehose redaction test.

