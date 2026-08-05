# Duotronic Replay Package Specification v1.0

**Status:** normative replay contract  
**Version:** replay-package@v1.0

## 1. Purpose

A replay package is a portable bundle that allows an implementation to verify how a canonical object, witness, mathematical claim, interpreter result, proof result, policy decision, or SRNN memory update was produced.

## 2. Replay package shape

```yaml
ReplayPackage:
  replay_package_id: string
  corpus_version: string
  target_refs: []
  dbp_envelopes: []
  evidence_refs: []
  artifact_manifest: []
  schema_manifest: []
  normalizer_manifest: []
  runtime_manifest: []
  policy_snapshot_refs: []
  expected_results:
    canonical_identity_hashes: []
    payload_hashes: []
    policy_decision_ids: []
  deterministic: boolean
  nondeterminism_declaration: string | null
  created_at: string
```

## 3. Artifact manifest

```yaml
ReplayArtifact:
  artifact_ref: string
  media_type: string
  size: integer
  sha256: string
  retention_policy: string
  purge_state: active | tombstoned | purged | external_unavailable
```

## 4. Verification process

```text
load replay package
-> verify manifest hashes
-> load schemas and normalizers
-> verify policy snapshot
-> verify runtime fingerprints or replay-equivalent profiles
-> recompute canonical identities
-> compare expected results
-> emit ReplayVerificationWitness
```

## 5. Determinism rule

If a computation is nondeterministic, the package must declare seeds, external dependencies, remote source hashes, model versions, and acceptable tolerance. Otherwise replay verification must fail closed.

## 6. Purge impact

If an artifact has been purged, replay may continue only if a purge tombstone and replay-impact record permit content-safe verification.

---

## Conformance note

This document is part of the v1.6 Draft 2 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
