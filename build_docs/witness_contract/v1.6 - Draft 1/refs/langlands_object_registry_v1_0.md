# Langlands Object Registry v1.0

**Status:** reference draft  
**Version:** langlands-object-registry@v1.0

---

## 1. Object kinds

| Object kind | Side | Canonical identity fields |
|---|---|---|
| GlobalField | arithmetic | field polynomial or construction, embeddings, discriminant, normalizer |
| LocalField | local arithmetic | base, completion place, residue field, uniformizer policy |
| Place | local/global | base field, valuation/equivalence class, archimedean flag |
| AdeleRing | global harmonic | base field, place set, restricted product policy |
| IdeleClassGroup | global class field | base field, topology profile |
| ReductiveGroup | group side | root datum, base field, form, pinning if used |
| DualGroup | dual side | root datum dual, coefficient field, Galois action |
| LGroup | bridge side | dual group, Weil/Galois action, semidirect product data |
| AutomorphicRepresentation | automorphic | group, local components, central character, conductor, normalization |
| GaloisRepresentation | arithmetic | base field, coefficient field, dimension, traces, ramification |
| WeilDeligneRepresentation | local arithmetic | Weil group rep, nilpotent operator, Frobenius semisimplification |
| ModularForm | automorphic/classical | weight, level, character, q-expansion, normalization |
| EllipticCurve | arithmetic geometry | Weierstrass model, base field, conductor, minimal model status |
| LFunction | analytic/arithmetic | local factors, normalization, conductor, gamma factors |
| EulerFactor | analytic local | place, polynomial/factor expression, ramification status |
| GammaFactor | archimedean | archimedean place, parameters, normalization |
| EpsilonFactor | functional equation | local/global flag, root number, conductor data |
| HeckeEigenpacket | automorphic | Hecke algebra profile, eigenvalues by place |
| SatakeParameter | local unramified | conjugacy class in dual group |
| TraceFormulaRecord | harmonic analysis | test functions, geometric side, spectral side, equality status |
| FunctorialTransferCandidate | bridge | L-group homomorphism, source/target reps, preservation claims |
| LocalLanglandsPacket | local correspondence | group, parameter, packet members, component group |
| GeometricLanglandsObject | geometric | curve, group, sheaf/D-module/local system, Hecke eigen data |

---

## 2. Claim kinds

1. `LFunctionEqualityClaim`
2. `LocalFactorMatchClaim`
3. `FunctionalEquationClaim`
4. `AnalyticContinuationClaim`
5. `FunctorialTransferClaim`
6. `LocalGlobalCompatibilityClaim`
7. `ModularityClaim`
8. `ReciprocityClaim`
9. `TraceFormulaIdentityClaim`
10. `GeometricEigensheafClaim`

---

## 3. Preservation checks

A bridge in this registry must declare which of the following are preserved:

1. local L-factors;
2. global L-functions;
3. epsilon factors;
4. conductors;
5. root numbers;
6. central characters;
7. infinitesimal characters;
8. Hecke eigenvalues;
9. Frobenius traces;
10. ramification data;
11. functional equation normalization;
12. cohomological degree or sheaf category.

---

## 4. Status fields

Allowed bridge status values:

```text
definition
theorem_case
partial_theorem
conjectural
computational_evidence
analogy_only
false_candidate
unknown
```

---

## 5. Fixture IDs

Suggested fixture IDs:

1. `langlands.fixture.riemann_zeta.v1`
2. `langlands.fixture.dirichlet_character_mod_4.v1`
3. `langlands.fixture.quadratic_dedekind_zeta.v1`
4. `langlands.fixture.elliptic_curve_modularity_record.v1`
5. `langlands.fixture.unramified_satake_gl2.v1`
6. `langlands.fixture.functorial_transfer_candidate.v1`
7. `langlands.fixture.geometric_eigensheaf_placeholder.v1`


---

## v1.6 full-corpus upgrade note

This document is retained from the first v1.6 math-integration pass and is now part of the complete v1.6 Draft 1 corpus alongside all v1.5 Draft 2 carry-forward files.
