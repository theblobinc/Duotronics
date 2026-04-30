# Duotronic Proof and Conjecture Witness Contract v1.0

**Status:** normative draft  
**Version:** proof-conjecture-witness@v1.0

---

## 1. Purpose

This contract prevents mathematical status collapse. A theorem, conjecture, proof sketch, computational check, literature citation, and model-generated explanation are different witness classes.

---

## 2. Claim status ladder

```text
raw_statement
parsed_statement
well_typed_statement
definition
example
counterexample_candidate
computational_evidence
literature_supported
proof_sketch
peer_reviewed_proof
formalized_proof
kernel_checked_theorem
conjecture
open_problem
retracted
rejected
```

---

## 3. Proof witness requirements

A proof witness must declare:

1. claim reference;
2. proof body or external source reference;
3. assumptions;
4. logical framework;
5. theorem dependencies;
6. proof checker, if any;
7. gaps or informal steps;
8. human review status;
9. reproducibility status.

---

## 4. Conjecture witness requirements

```yaml
ConjectureWitness:
  conjecture_id: string
  statement_ref: string
  domain_id: string
  known_cases: []
  related_theorems: []
  computational_evidence_refs: []
  obstruction_refs: []
  counterexample_search_refs: []
  status: open | partially_resolved | resolved_true | resolved_false | retracted | unknown
```

---

## 5. Computation is not proof by default

A computation can become theorem-level only if the relevant proof profile allows it, for example:

1. exhaustive finite check with verified bounds;
2. certified interval arithmetic;
3. proof assistant kernel check;
4. independently replayed symbolic derivation;
5. formally verified algorithm plus checked input certificate.

Otherwise it remains computational evidence.

---

## 6. Literature witness

```yaml
LiteratureWitness:
  literature_id: string
  source_type: book | paper | preprint | database | lecture_notes | formal_library | repository | other
  bibliographic_ref: string
  claim_refs: []
  quote_or_location_ref: string | null
  reliability_status: peer_reviewed | standard_reference | preprint | informal | unknown
  extraction_status: raw | parsed | human_checked | rejected
```

---

## 7. Model output boundary

Model output may propose:

1. a parsing;
2. a proof sketch;
3. a conjecture classification;
4. a possible bridge;
5. a counterexample search plan.

Model output may not directly promote a claim to theorem.

---

## 8. Contradiction handling

If two mathematical claims conflict, the system must create a `MathContradictionRecord`.

```yaml
MathContradictionRecord:
  contradiction_id: string
  claim_refs: []
  conflict_kind: direct_negation | assumption_mismatch | notation_mismatch | domain_mismatch | counterexample | source_conflict | proof_gap
  severity: low | medium | high | blocking
  resolution_status: unresolved | resolved_by_context | resolved_by_counterexample | resolved_by_retraction | human_review_required
```


---

## v1.6 full-corpus upgrade note

This document is retained from the first v1.6 math-integration pass and is now part of the complete v1.6 Draft 1 corpus alongside all v1.5 Draft 2 carry-forward files.
