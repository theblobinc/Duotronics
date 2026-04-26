# Glyphic Script Visual-Semantic Learning as a Duotronic Research Profile v0.2

**Status:** Reference candidate profile  
**Version:** glyphic-script-visual-semantic@v0.2  
**Supersedes:** glyphic-script-visual-semantic@v0.1  
**Document kind:** Research/reference profile for visual-symbolic auto-profile learning  
**Primary purpose:** Define how the Duotronic engine can ingest visual scripts such as hieroglyphic-style or Mayan-style corpora as evidence, learn visual clusters and candidate readings, preserve uncertainty, and avoid treating visual segmentation or model translation as authority.

---

## 1. Research boundary

This profile is not a complete theory of any specific ancient script. It is an internal architecture profile for learning from visual-symbolic writing systems.

It is intended for use with:

1. image regions;
2. glyph segmentation;
3. visual cluster detection;
4. sign inventories;
5. candidate readings;
6. source alignments;
7. expert/reference corpora where available;
8. uncertainty-preserving witness objects.

---

## 2. Core rule

Visual identity, sign identity, reading, translation, and semantic claim are separate layers.

```text
image region
-> visual segmentation witness
-> glyph cluster witness
-> candidate sign witness
-> candidate reading witness
-> candidate semantic witness
```

The engine may trust an image-region hash without trusting a translation.

---

## 3. Object types

1. `ImageRegionWitness`
2. `SegmentationWitness`
3. `GlyphClusterWitness`
4. `CandidateSignWitness`
5. `DirectionalityWitness`
6. `ReadingHypothesisWitness`
7. `SemanticRoleHypothesisWitness`
8. `SourceAlignmentWitness`
9. `UncertaintyWitness`

---

## 4. Image region witness

```yaml
ImageRegionWitness:
  image_region_witness_id: string
  source_evidence_id: string
  raw_image_hash: string
  perceptual_hash_alg: string
  perceptual_hash_value: string
  region_coordinates: string
  segmentation_profile_id: string
  visual_region_hash: string
  quality_diagnostic: string | null
  trust_status: candidate | canonicalized | audit_only | rejected
```

---

## 5. Glyph cluster witness

```yaml
GlyphClusterWitness:
  glyph_cluster_witness_id: string
  image_region_witness_id: string
  cluster_id: string
  visual_features_hash: string
  candidate_sign_ids: []
  variant_of: string | null
  confidence: number | null
  ambiguity: low | medium | high | unresolved
```

---

## 6. Reading hypothesis witness

```yaml
ReadingHypothesisWitness:
  reading_hypothesis_id: string
  glyph_cluster_witness_ids: []
  proposed_readings: []
  source_alignment_refs: []
  model_witness_ids: []
  confidence: number | null
  uncertainty_notes: []
  trust_status: research_candidate | audit_only | rejected
```

A reading hypothesis is not a translation authority.

---

## 7. Auto-learning behavior

The engine may learn:

1. repeated visual forms;
2. clusters;
3. directionality cues;
4. ordering relations;
5. composite signs;
6. positional patterns;
7. source alignment patterns;
8. candidate semantic roles;
9. uncertainty zones;
10. weak or strong transliteration support.

---

## 8. Failure cases

1. treating visual similarity as semantic equivalence;
2. treating model translation as truth;
3. collapsing uncertain readings into a single answer;
4. losing source image hash;
5. using crop coordinates as semantic identity;
6. ignoring variant forms;
7. ignoring source context;
8. promoting profile without expert/reference fixtures.

---

## 9. Fixture set

Minimum fixtures:

1. repeated visual cluster examples;
2. near-duplicate visual variants;
3. ambiguous region boundaries;
4. known invalid segmentations;
5. conflicting readings;
6. source alignment examples;
7. no-reading examples;
8. image quality degradation examples;
9. cross-model segmentation disagreement examples;
10. policy audit-only examples.

---

## 10. Promotion target

This profile should remain research or sandbox until visual segmentation, source alignment, replay, and uncertainty preservation are reliable. Semantic translation should require a separate, stronger profile.


---

## 11. Draft 2 perceptual identity rule

> **Status tag:** normative for this profile

Raw byte hashes are not sufficient for glyphic visual canonicalization because slight rotation, scaling, lighting change, crop variation, compression, scanning artifacts, and manuscript degradation can change bytes without changing the intended visual sign.

A glyphic visual witness must separate:

1. raw image hash;
2. perceptual hash algorithm;
3. perceptual hash value;
4. segmentation profile;
5. region coordinates;
6. transformation normalization profile;
7. collision and variation risk.

### 11.1 Visual identity schema

```yaml
VisualIdentity:
  raw_image_hash: string
  perceptual_hash_alg: string
  perceptual_hash_version: string
  perceptual_hash_value: string
  transform_normalization:
    rotation_policy: none | normalize | preserve
    scale_policy: none | normalize | preserve
    lighting_policy: none | normalize | preserve
    crop_policy: strict | tolerant | profile_specific
  collision_policy:
    collision_possible: true
    collision_risk_class: low | medium | high | unknown
    collision_failure_action: audit_only | preserve_uncertainty | reject
```

### 11.2 Expected loss

Perceptual hash canonicalization may lose exact pixel identity and fine stylistic detail. That loss must be declared as expected loss.

Possible expected loss:

1. exact stroke texture;
2. color variation;
3. lighting variation;
4. minor rotation;
5. compression artifacts.

Possible prohibited loss:

1. sign boundary;
2. orientation when directionality matters;
3. neighboring glyph context;
4. source manuscript reference;
5. uncertainty class.

### 11.3 Collision rule

Because perceptual hashes can collide, a glyphic profile using perceptual hash identity must remain `research_profile` or `sandbox_runtime_profile` unless collision rates are benchmarked and policy-approved.
