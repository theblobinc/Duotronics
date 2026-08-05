# Corpus Migration Witness Specification v1.0

**Status:** normative migration object specification  
**Version:** corpus-migration-witness@v1.0

## 1. Purpose

A `CorpusMigrationWitness` records how a document, schema, profile, object shape, fixture, or runtime contract moved from one corpus version to another.

## 2. Schema

```yaml
CorpusMigrationWitness:
  migration_witness_id: string
  source_corpus_version: string
  target_corpus_version: string
  source_path: string
  target_path: string
  source_hash: string | null
  target_hash: string | null
  migration_kind: retained | renamed | superseded | converted | split | merged | deprecated | removed
  semantic_change: none | additive | narrowing | breaking | unknown
  replay_impact: none | replay_equivalence | replay_with_adapter | migration_required | replay_blocked
  authority_impact: none | policy_required | human_review_required
  evidence_refs: []
  policy_decision_id: string
  created_at: string
```

## 3. Required use

A migration witness is required when:

1. a v1.5 document is carried into v1.6;
2. JSON or binary assets are represented as Markdown in the Markdown-only package;
3. schema fields are added, removed, or renamed;
4. a profile changes status;
5. a mathematical claim changes authority status;
6. runtime backend authority changes.

## 4. Replay impact meanings

`replay_equivalence` means old records replay to the same canonical identity. `replay_with_adapter` means an adapter must be loaded. `migration_required` means old records cannot be interpreted under v1.6 without a migration step. `replay_blocked` means the old object is retained only as historical evidence.

---

## Conformance note

This document is part of the v1.6 Draft 2 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
