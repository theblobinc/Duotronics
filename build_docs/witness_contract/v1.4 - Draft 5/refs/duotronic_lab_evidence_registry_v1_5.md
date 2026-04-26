# Duotronic Lab Evidence Registry v1.5

**Status:** Source-spec baseline candidate  
**Version:** lab-evidence-registry@v1.5  
**Supersedes:** lab-evidence-registry@v1.4  
**Supersedes:** lab-evidence-registry@v1.3  
**Supersedes:** lab-evidence-registry@v1.2  
**Supersedes:** lab-evidence-registry@v1.1  
**Document kind:** Reference evidence registry with normative bounded-import rules  
**Primary purpose:** Import historical Duotronic grid, polygon, benchmark, adapter, external-engine, and profile-learning fixtures into the source corpus as executable lineage, schemas, fixtures, adapters, replay examples, and policy red-team material without overclaiming physics or redefining DPFC/Witness/Meta semantics.


## Document status tag key

| Tag | Meaning | Promotion rule |
|---|---|---|
| `normative` | Binding rule for this source document. | Must be followed by conforming implementations. |
| `reference` | Schema, example, implementation aid, explanation, or diagnostic guidance. | Useful for implementation; not new semantic authority unless cited by a normative rule. |
| `research` | Experimental candidate, benchmark, learned profile, or metric. | Must remain opt-in until promoted. |
| `future` | Planned work not active in this draft. | Must not be treated as live behavior. |
| `analogy` | Outside-domain comparison or motivation. | Must not be treated as proof. |


## 1. Scope

The Lab Evidence Registry imports historical and future lab work as:

1. schema lineage;
2. executable reference patterns;
3. fixture examples;
4. benchmark-suite examples;
5. gate-report examples;
6. adapter examples;
7. artifact-manifest examples;
8. external-engine parser examples;
9. profile-learning examples;
10. policy-shield red-team fixtures;
11. meta-runtime shadow-replay fixtures;
12. migration examples.

It does not import lab results as DPFC theorem proof, physical proof, source truth, language truth, or canonical runtime authority.

---

## 2. Evidence import rule

A lab artifact can become:

1. evidence bundle;
2. fixture;
3. benchmark;
4. adapter example;
5. normalizer test;
6. bridge test;
7. replay trace;
8. profile candidate source;
9. policy red-team case.

A lab artifact cannot directly become:

1. normative DPFC rule;
2. trusted external-domain claim;
3. production profile;
4. model-gating authority;
5. source reliability authority.

---

## 3. v1.4 lab classes

v1.4 adds lab classes for:

1. auto-profile learning runs;
2. Roman numeral profile synthesis;
3. English claim/evidence extraction;
4. glyphic visual segmentation;
5. model disagreement fixtures;
6. search/social contradiction fixtures;
7. distributed node replay fixtures;
8. source privacy and policy fixtures;
9. profile demotion examples.

---

## 4. Artifact manifest shape

```yaml
LabArtifactManifest:
  artifact_id: string
  lab_id: string
  artifact_kind: fixture | benchmark | adapter | replay_trace | profile_candidate | redteam | source_bundle
  source_hash: string
  schema_id: string
  profile_refs: []
  model_witness_refs: []
  expected_use: reference | research | conformance | redteam | migration
  prohibited_use: []
  import_status: candidate | research_valid | reference | rejected
```

---

## 5. Non-claims

Lab evidence is engineering evidence unless promoted by the appropriate contract. It is not proof by existence.


---

## 6. Draft 3 self-informing lab fixture classes

> **Status tag:** reference

Draft 3 adds lab fixture classes for:

1. chronological stream ingestion;
2. self-reference edge extraction;
3. personal-history record wrappers;
4. timeline canonicalization;
5. preference/habit/likely-action witness extraction;
6. high-speed lookup memory invalidation;
7. Redis-like index reference tests;
8. planner action candidate tests;
9. action outcome replay tests;
10. model diversity and oracle-risk red-team cases.

These fixtures are engineering evidence. They do not prove a self-model is true or a planner is rational.


---

## 7. Draft 4 implementation-hardening fixtures

> **Status tag:** reference

Draft 4 adds fixture classes for:

1. worked self-informing YouTube-like music loop;
2. planner-triggered profile-learning run;
3. policy-change proposal approval and rejection;
4. conflicting action candidates;
5. self-model invalidation after new evidence;
6. self-model invalidation after source deletion;
7. multi-actor scoping ambiguity;
8. high-speed loop resource violation;
9. likely-action-to-action conversion;
10. action outcome memory update.

These fixtures should be used before any implementation claims Draft 4 compatibility.


---

## 8. Draft 5 governance-hardening fixtures

> **Status tag:** reference

Draft 5 adds fixture classes for:

1. evidence purge request and authorization;
2. purge dependency graph construction;
3. purge cascade through lookup memory;
4. purge cascade through self-model snapshots;
5. purge impact on profile candidates;
6. replay with purge tombstones;
7. human review request and expiration;
8. human review decision feeding policy;
9. lazy action revalidation after self-model invalidation;
10. planner-triggered learning with forbidden promotion request;
11. uncalibrated diversity-weighted score observe-only behavior;
12. calibrated diversity threshold sandbox/restricted behavior.

These fixtures are required before a prototype claims Draft 5 governance compatibility.


---

## 9. Draft 5 completion-pass fixtures

> **Status tag:** reference

The completion pass adds fixtures for:

1. purge attestation generation;
2. purge attestation verification;
3. optional external purge notarization;
4. vector-store invalidation request/result;
5. graph-store invalidation request/result;
6. failed external index invalidation residual risk;
7. global human review timeout application;
8. human review expiration event;
9. meta-runtime replay with purge tombstones;
10. diversity score calibration threshold progression.

These fixtures distinguish internal prototype readiness from external-audit readiness.
