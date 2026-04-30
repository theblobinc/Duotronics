# Duotronic Conformance Test Suite v1.0

**Status:** normative conformance contract  
**Version:** conformance-suite@v1.0

## 1. Conformance levels

```text
C0 corpus-reader: can parse corpus and manifests
C1 envelope: validates DBP v2 envelopes and hashes
C2 witness: creates evidence, candidate, and canonical witness records
C3 math: handles CanonicalMathObject and MathClaim lifecycle
C4 runtime: runs interpreter/proof jobs in sandbox with witnesses
C5 policy: enforces policy decisions and overrides
C6 replay: creates and verifies replay packages
C7 distributed: federates nodes and task delegation safely
C8 srnn: handles SRNN oracle/task/witness-event integration
```

## 2. Required tests

1. DBP envelope valid/invalid cases.
2. Canonical identity stability across serialization.
3. Evidence bundle immutability.
4. Candidate-to-canonical witness transition.
5. Policy deny on missing scope.
6. Interpreter sandbox timeout.
7. Proof checker accepted proof fixture.
8. Math claim status transition reject without evidence.
9. Langlands bridge stored as conjectural/computational evidence, not theorem.
10. Replay package hash verification.
11. SRNN oracle job persists `witness_event_id` when result includes it.
12. MCP endpoint malformed response becomes audit-only/reject.

## 3. Fixture pack

The Markdown fixture pack is `refs/fixtures/duotronic_fixtures_v1_6_markdown_pack.md`. Machine-readable JSON fixtures may be generated from it but must retain source hashes.

## 4. Certification output

```yaml
ConformanceReport:
  implementation_id: string
  implementation_version: string
  corpus_version: v1.6-draft-2
  conformance_level: C0-C8
  test_results: []
  failures: []
  policy_snapshot_id: string
  generated_at: string
```

## 5. Failure rule

An implementation may claim only the highest level for which all lower-level tests pass. A failed security or policy test blocks all production-oriented claims.

---

## Conformance note

This document is part of the v1.6 Draft 2 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
