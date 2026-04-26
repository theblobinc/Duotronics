# Duotronic Model Diversity and Adjudication Governance v1.1

**Status:** Source-spec baseline candidate  
**Version:** model-diversity-adjudication-governance@v1.1  
**Supersedes:** model-diversity-adjudication-governance@v1.0  
**Document kind:** Normative model diversity, bias, oracle-risk, and adjudication governance guide  
**Primary purpose:** Define how Duotronic systems avoid treating a single model or homogeneous model family as an oracle by recording model diversity, known bias, adjudication behavior, disagreement, source dependence, and policy constraints.

---

## 1. Scope

This guide applies whenever Duotronic uses models to:

1. extract witnesses;
2. segment data;
3. translate or classify content;
4. propose profiles;
5. propose actions;
6. rank sources;
7. summarize evidence;
8. adjudicate claims;
9. detect contradictions;
10. gate other models;
11. plan decisions.

The guide covers language models, vision models, audio models, embedding models, classifiers, rankers, rule-based systems, symbolic engines, search systems, reinforcement learners, and hybrid systems.

---

## 2. Central rule

> **Status tag:** normative

No model is an oracle.

A model output is a model witness. It is evidence about what that model produced under a declared inference profile.

The system may trust a model output only after validation, cross-checking where required, canonicalization, replay or equivalence checks where required, and policy gating.

---

## 3. Oracle-risk classes

```yaml
OracleRiskProfile:
  oracle_risk_profile_id: string
  model_id: string
  model_version: string
  model_family: llm | vision | audio | embedding | classifier | ranker | symbolic | rule_based | hybrid | custom
  training_data_overlap_class: unknown | high | medium | low | independent | not_applicable
  architecture_diversity_class: same_family | related_family | different_family | non_ml | unknown
  known_biases: []
  known_failure_modes: []
  calibration_profile_id: string | null
  allowed_authority: audit_only | sandbox | restricted | normal
```

If multiple models share high training-data overlap and similar architecture, their agreement must not be treated as strong independent corroboration.

---

## 4. Model diversity set

A model diversity set declares which models are intentionally combined.

```yaml
ModelDiversitySet:
  model_diversity_set_id: string
  purpose: segmentation | translation | claim_extraction | profile_synthesis | action_planning | contradiction_detection | search_ranking | custom
  model_refs: []
  diversity_dimensions:
    - architecture
    - training_data
    - provider
    - modality
    - rule_based
    - symbolic
    - human_review
  minimum_independence_requirement: string
  failure_policy: preserve_uncertainty | require_more_models | audit_only | reject
```

The system should prefer diverse evidence sources:

1. different architectures;
2. different training data;
3. different modalities;
4. rule-based checks;
5. symbolic constraints;
6. source-grounded retrieval;
7. human review where policy requires.

---

## 5. Adjudication record

```yaml
ModelAdjudicationRecord:
  adjudication_id: string
  target_ref: string
  model_witness_ids: []
  model_diversity_set_id: string
  agreement_summary:
    agreeing_models: []
    disagreeing_models: []
    agreement_fields: []
    disagreement_fields: []
  independence_assessment:
    likely_independent: true | false | unknown
    training_overlap_notes: []
    architecture_overlap_notes: []
  contradiction_refs: []
  uncertainty_refs: []
  decision:
    action: accept_for_scope | preserve_uncertainty | audit_only | require_more_evidence | reject | human_review
    authority_scope: representation_identity | claim_support | profile_support | action_support | custom
  policy_decision_id: string
```

Agreement without independence is weak support.

---

## 6. Bias and shared-failure handling

The system must watch for:

1. all models hallucinating the same unsupported source;
2. all models sharing common internet-corpus bias;
3. translation models overconfident in low-resource scripts;
4. vision models treating visual similarity as semantic identity;
5. sentiment models misreading sarcasm;
6. social-source rankers amplifying popularity;
7. personal-history models overfitting recent behavior;
8. planners optimizing the wrong objective.

When shared failure is suspected, the system should:

1. preserve uncertainty;
2. ask for different model families;
3. invoke rule-based or symbolic checks;
4. search for source evidence;
5. add red-team fixtures;
6. reduce authority;
7. require human review if policy requires.

---

## 7. Diversity-weighted agreement

The system may compute a diversity-weighted agreement score.

```yaml
DiversityWeightedAgreement:
  score_id: string
  adjudication_id: string
  raw_agreement_score: number
  independence_weight: number
  source_grounding_weight: number
  contradiction_penalty: number
  uncertainty_penalty: number
  final_score: number
  allowed_use: observe | audit_only | sandbox | restricted | normal
```

A score without calibration and baseline is observe-only.

---

## 8. External oracle critique boundary

Duotronic does not eliminate the problem that external models can be biased, incomplete, or wrong.

Duotronic mitigates the problem by:

1. making model reliance explicit;
2. storing model witnesses rather than hidden oracle calls;
3. comparing diverse models;
4. preserving disagreement;
5. requiring evidence lineage;
6. separating model confidence from authority;
7. letting policy reduce or block authority;
8. supporting red-team and falsifier nodes;
9. recording source and training-overlap uncertainty.

This is a governance and evidence framework, not an alignment proof.

---

## 9. Non-claims

This guide does not prove that diverse models are unbiased. It defines how to measure and govern diversity, disagreement, and shared-failure risk.


---

## 10. Draft 5 calibration and threshold guidance

> **Status tag:** normative

A `DiversityWeightedAgreement` score is observe-only unless calibrated.

Calibration requires:

1. calibration dataset or fixture suite;
2. target task definition;
3. model diversity set;
4. independence assessment method;
5. known failure cases;
6. threshold definitions;
7. retention diagnostic baseline;
8. policy-approved allowed use.

### 10.1 Calibration profile

```yaml
DiversityScoreCalibrationProfile:
  calibration_profile_id: string
  target_task: segmentation | translation | claim_extraction | profile_synthesis | action_planning | contradiction_detection | source_reliability | custom
  model_diversity_set_id: string
  calibration_fixture_pack_id: string
  baseline_metric_ids: []
  thresholds:
    observe_min: number | null
    audit_only_min: number | null
    sandbox_min: number | null
    restricted_min: number | null
    normal_min: number | null
  failure_modes: []
  valid_time_range:
    start: string
    end: string | null
  policy_decision_id: string
```

### 10.2 Default threshold authority

Without calibration:

```text
allowed_use = observe
```

With calibration, a score may support only the maximum allowed use declared in the calibration profile and policy decision.

### 10.3 Threshold caution

A high score does not prove truth. It means a calibrated diversity/adjudication metric supports a declared authority scope.

The system must still preserve:

1. contradiction records;
2. uncertainty records;
3. source lineage;
4. model independence limits;
5. policy restrictions.

---

## 11. Completion-pass practical threshold guidance

> **Status tag:** reference

Initial implementations should treat `DiversityWeightedAgreement` as observe-only.

A practical bootstrap policy may use the following authority progression:

| Calibration state | Allowed use |
|---|---|
| no calibration fixture pack | observe only |
| fixture pack exists but no thresholds | audit-only diagnostics |
| thresholds exist but no failure-mode review | sandbox only |
| thresholds and failure modes reviewed | restricted use by policy |
| thresholds, baselines, retention diagnostics, and policy approval | normal use for declared scope only |

Recommended first prototype behavior:

```yaml
DiversityWeightedAgreement:
  allowed_use: observe
```

until the system has enough fixtures to measure false agreement, shared failure, and contradiction preservation.
