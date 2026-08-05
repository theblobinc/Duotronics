# Mathematical Domain Registry v1.0

**Status:** reference draft  
**Version:** mathematical-domain-registry@v1.0

---

## 1. Registry purpose

This registry provides the minimum domain coverage required for v1.6 all-math witnesses.

Each domain must declare object families, claim types, proof styles, computation styles, equality modes, and bridge patterns.

---

## 2. Registered domains

| Domain ID | Object examples | Claim examples | Common equality modes |
|---|---|---|---|
| foundations.logic | formula, proof rule, model, theory | consistency, completeness, satisfiability | syntactic, semantic equivalence |
| foundations.set_theory | set, ordinal, cardinal, forcing notion | independence, consistency strength | extensional, forcing equivalence |
| category_theory | category, functor, natural transformation, adjunction | equivalence, universal property | isomorphism, equivalence |
| algebra.group_theory | group, subgroup, action, representation | classification, isomorphism | isomorphism, presentation equivalence |
| algebra.ring_theory | ring, ideal, module, algebra | exactness, factorization | isomorphism, Morita equivalence |
| number_theory | integer, prime, field, ideal, Galois group | reciprocity, distribution, modularity | equality, isomorphism |
| langlands | L-function, automorphic rep, Galois rep, transfer | correspondence, functoriality | conjectural correspondence, theorem-backed bridge |
| algebraic_geometry | scheme, morphism, sheaf, stack | representability, smoothness, cohomology | isomorphism, derived equivalence |
| geometry.differential | manifold, bundle, connection, curvature | geodesic, curvature identity | diffeomorphism, gauge equivalence |
| topology | space, homotopy, homology, spectrum | invariance, classification | homeomorphism, homotopy equivalence |
| analysis.real_complex | function, limit, integral, distribution | convergence, analyticity | pointwise, a.e., distributional |
| functional_analysis | Banach space, Hilbert space, operator | boundedness, spectrum | isometry, unitary equivalence |
| probability_statistics | measure, random variable, estimator | convergence, confidence, independence | distributional equality |
| combinatorics | graph, matroid, design, poset | enumeration, extremal bound | isomorphism |
| dynamical_systems | flow, map, invariant measure | stability, chaos, ergodicity | conjugacy, semi-conjugacy |
| differential_equations | ODE, PDE, weak solution | existence, uniqueness, regularity | classical/weak equivalence |
| numerical_analysis | algorithm, discretization, error bound | convergence, stability | tolerance-bounded |
| optimization | objective, feasible region, dual | optimality, duality gap | exact or approximate optimum |
| information_theory | entropy, code, channel | capacity, coding theorem | operational equivalence |
| mathematical_physics | field, symmetry, path integral, operator algebra | duality, conservation, quantization | gauge/duality equivalence |
| computer_algebra | symbolic expression, Gröbner basis, CAS result | simplification, elimination | normal-form equality |
| formal_methods | program, spec, invariant, proof artifact | refinement, safety, liveness | bisimulation, kernel equality |

---

## 3. Universal edges

```yaml
MathDependencyEdge:
  edge_id: string
  source_ref: string
  target_ref: string
  edge_kind: uses_definition | proves | depends_on | generalizes | specializes | is_counterexample_to | analogous_to | computed_by | formalizes | conjecturally_corresponds_to
  status: raw | candidate | verified | rejected
```

---

## 4. Required fixture minimum

Each domain must eventually provide:

1. one canonical object;
2. one definition;
3. one theorem or theorem-like claim;
4. one conjecture or open problem if relevant;
5. one computation witness;
6. one example;
7. one invalid object fixture;
8. one notation ambiguity fixture.


---

## v1.6 full-corpus upgrade note

This document is retained from the first v1.6 math-integration pass and is now part of the complete v1.6 Draft 2 corpus alongside all v1.5 Draft 2 carry-forward files.
