# Glyphic Script Visual-Semantic Learning as a Duotronic Research Profile v0.1

**Status:** Reference candidate profile  
**Version:** glyphic-script-visual-semantic@v0.1  
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
  image_hash: string
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
