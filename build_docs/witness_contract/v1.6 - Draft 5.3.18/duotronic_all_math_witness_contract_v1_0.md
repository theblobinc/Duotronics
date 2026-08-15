# Duotronic All-Math Witness Contract v1.0

**Status:** normative draft  
**Version:** all-math-witness@v1.0  
**Document kind:** Mathematical witness coverage contract

---

## 1. Purpose

This contract makes Duotronic witnesses cover every mathematical domain at the schema level.

Coverage means that any mathematical area can produce structured records for:

1. objects;
2. definitions;
3. notation;
4. assumptions;
5. claims;
6. proofs;
7. conjectures;
8. examples;
9. counterexamples;
10. computations;
11. diagrams;
12. algorithms;
13. reductions;
14. equivalences;
15. bridges;
16. citations;
17. formal proof artifacts;
18. interpreter outputs.

Coverage does not mean every theorem is already formalized.

---

## 2. Universal mathematical witness types

```yaml
MathObjectWitness:
  witness_id: string
  object_ref: string
  domain_id: string
  construction_source: definition | parser | computation | literature | formal_proof | imported_database | user_input
  context_ref: string
  trust_status: raw | candidate | canonicalized | rejected | deprecated
```

```yaml
MathClaimWitness:
  witness_id: string
  claim_kind: definition | lemma | theorem | proposition | corollary | conjecture | example | counterexample | computation_claim | equivalence | bridge | classification
  statement_ref: string
  object_refs: []
  assumptions_ref: string
  domain_id: string
  status: raw | parsed | conjectural | literature_supported | formally_verified | computationally_supported | disproven | rejected
  proof_witness_refs: []
  computation_witness_refs: []
  citation_refs: []
```

```yaml
MathProofWitness:
  witness_id: string
  proof_kind: informal | textbook | peer_reviewed | formal_kernel | proof_sketch | computational_proof | exhaustive_check | probabilistic_check
  claim_ref: string
  proof_payload_ref: string
  checker_ref: string | null
  proof_assistant: lean | coq | agda | isabelle | metamath | custom | none
  kernel_result: accepted | rejected | not_checked | not_applicable
  gaps: []
  status: candidate | checked | accepted | rejected | superseded
```

```yaml
MathCounterexampleWitness:
  witness_id: string
  claim_ref: string
  counterexample_object_refs: []
  verification_ref: string
  status: candidate | verified | rejected
```

---

## 3. Domain coverage registry

The domain registry must include at least:

1. logic and foundations;
2. set theory;
3. category theory;
4. algebra;
5. number theory;
6. representation theory;
7. algebraic geometry;
8. differential geometry;
9. topology;
10. analysis;
11. functional analysis;
12. probability and statistics;
13. combinatorics;
14. graph theory;
15. discrete mathematics;
16. dynamical systems;
17. differential equations;
18. numerical analysis;
19. optimization;
20. information theory;
21. mathematical physics;
22. computer algebra;
23. formal methods;
24. Langlands and arithmetic geometry.

---

## 4. Field-specific witness extensions

A domain may define extensions, but extensions must preserve universal fields.

Examples:

| Domain | Extension examples |
|---|---|
| topology | homotopy, homology, cohomology, fundamental group, spectral sequence |
| algebra | group action, module, ideal, quotient, representation, character |
| analysis | limit, convergence, norm, spectrum, operator, distribution |
| probability | measure space, random variable, distribution, estimator, confidence interval |
| geometry | manifold, bundle, connection, curvature, morphism |
| logic | formula, proof rule, model, satisfiability, consistency strength |
| computation | algorithm, complexity bound, reduction, randomized guarantee |
| Langlands | L-function, automorphic representation, Galois representation, functorial transfer |

---

## 5. Mathematical uncertainty

Uncertainty is first-class.

```yaml
MathUncertaintyRecord:
  uncertainty_id: string
  target_ref: string
  uncertainty_kind: unknown_truth | unresolved_conjecture | numerical_error | parser_ambiguity | notation_ambiguity | assumption_gap | proof_gap | source_conflict | heuristic_only
  severity: low | medium | high | blocking
  resolution_path: []
```

---

## 6. All-math query examples

The witness layer must support queries such as:

1. show all claims depending on the Riemann Hypothesis;
2. find all computations that support a conjecture but lack proof;
3. list theorem-backed functorial transfers for a group pair;
4. find counterexamples to a proposed equivalence;
5. compare two definitions under different notation profiles;
6. retrieve all proof artifacts checked by a specific proof assistant version;
7. trace all uses of a numerical approximation in a proof-like argument;
8. find all fields where a concept appears under different names.

---

## 7. Witness identity and replay

Every witness must record:

1. source identity;
2. parser or extractor version;
3. normalizer version;
4. context version;
5. assumptions;
6. status;
7. replay or non-replay reason;
8. policy decision if it affects runtime or promotion.


---

## v1.6 full-corpus upgrade note

This document is retained from the first v1.6 math-integration pass and is now part of the complete v1.6 Draft 2 corpus alongside all v1.5 Draft 2 carry-forward files.
