# Duotronic Migration Runbook v1.6

**Status:** normative migration runbook  
**Version:** migration-runbook-v1.6@v1.0

## 1. Purpose

This runbook upgrades a v1.5 Draft 2 corpus/runtime prototype to the v1.6 Draft 1 mathematical-canon and backend-spine model without losing replay compatibility.

## 2. Migration phases

```text
phase 0: freeze source corpus and runtime writes
phase 1: inventory v1.5 documents, schemas, profiles, witnesses, fixtures
phase 2: generate CorpusMigrationWitness records
phase 3: create v1.6 PostgreSQL schemas
phase 4: import DBP envelopes and canonical identity records
phase 5: migrate witness facts and evidence bundles
phase 6: migrate DPFC profiles into Mathematical Canon bridge records
phase 7: add Langlands/math-domain registries
phase 8: configure interpreter/proof runtime profiles
phase 9: replay sample records
phase 10: enable v1.6 writes in audit-only mode
phase 11: promote selected profiles to sandbox/restricted/normal runtime
```

## 3. Required preflight

1. v1.5 source corpus hash manifest.
2. Database backup.
3. Artifact backup.
4. Policy snapshot export.
5. Replay fixture set.
6. Human review queue drain or freeze.

## 4. Corpus migration witness

Every carried-forward document must produce:

```yaml
CorpusMigrationWitness:
  source_version: v1.5-draft-2
  target_version: v1.6-draft-1
  source_path: string
  target_path: string
  migration_kind: retained | renamed | superseded | converted | deprecated
  semantic_change: none | additive | breaking
  replay_impact: none | replay_equivalence | migration_required
  evidence_refs: []
```

## 5. DPFC migration

DPFC objects remain valid as a representational discipline. They must be wrapped as `CanonicalMathObject` or `MathFamilyDeclaration` records when used inside the broader v1.6 canon.

## 6. Witness migration

Old witness records must not be reinterpreted silently. They migrate through:

```text
old witness row
-> source hash verification
-> schema mapping
-> DBP v2 envelope
-> canonical identity preservation check
-> policy mode assignment
-> replay package update
```

## 7. SRNN migration

SRNN task/oracle rows must add or derive:

```text
loop_id
node_id
oracle_job_id
input_artifact_ref
replay_identity_ref
witness_event_id when emitted
temporal_meta_objects
```

## 8. Rollback

Rollback requires:

1. restoring v1.5 canonical store backup;
2. disabling v1.6 writes;
3. preserving v1.6 audit log as migration evidence;
4. marking v1.6 migrated objects as not active.

## 9. Acceptance criteria

Migration is successful only if:

1. all v1.5 manifest entries have migration witnesses;
2. conformance fixture pack passes;
3. sample replay packages verify;
4. policy engine rejects unauthorized promotions;
5. interpreter runs are sandboxed;
6. SRNN oracle jobs preserve witness-event links where emitted.

---

## Conformance note

This document is part of the v1.6 Draft 1 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
