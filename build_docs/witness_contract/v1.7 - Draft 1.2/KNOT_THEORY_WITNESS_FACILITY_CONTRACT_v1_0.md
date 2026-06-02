# Knot Theory Witness Facility Contract v1.0

## 1. Status

This file is normative for Duotronic Witness Contract v1.7 Draft 1.1 and supersedes any Draft 1 wording that treated knot theory as merely additive or second-class.

Knot theory support is a first-class mathematical witness facility. Specific invariant families may remain optional, but knot presentations, traces, authority paths, canonicalization, completeness claims, and equivalence claims are first-class objects when the facility is enabled.

## 2. First-class object model

The v1.7 Draft 1.1 knot layer defines these first-class witness objects:

- `KnotDiagramWitness`
- `KnotBraidWordWitness`
- `KnotReidemeisterMoveWitness`
- `KnotReidemeisterTraceWitness`
- `KnotInvariantWitness`
- `KnotInvariantCompletenessWitness`
- `KnotCanonicalizationWitness`
- `KnotEquivalenceAuthorityPath`
- `KnotEquivalenceWitness`

Every object above has schema, fixture, SQL persistence, OpenAPI surface, validator coverage, and Lean surface parity.

## 3. Non-collapse distinctions

A knot runtime MUST preserve these distinctions:

1. Diagram presentation is not knot type.
2. Braid word is not knot type.
3. Braid closure convention is not implicit.
4. Reidemeister move is not full trace.
5. Trace verification is not theorem proof.
6. Invariant equality is not equivalence unless the invariant is complete for the declared domain.
7. Completeness is domain-bounded and must be proof-backed.
8. Canonical hash equality is not equivalence without canonicalization domain and collision policy.
9. Authority path is not inline metadata.
10. Equivalence claim requires a first-class authority path.

## 4. Required syscalls

A v1.7 Draft 1.1 knot runtime MUST expose:

- `knot_encode`, accepting either `KnotDiagramWitness` or `KnotBraidWordWitness`
- `knot_move`
- `knot_trace`
- `knot_invariant`
- `knot_invariant_completeness`
- `knot_canonicalize`
- `knot_authority_path`
- `knot_equivalence`

## 5. Equivalence authority

`KnotEquivalenceWitness` MUST reference `KnotEquivalenceAuthorityPath` by `authority_path_id`. Inline authority arrays may be retained only as summaries and MUST NOT be treated as normative authority.

## 6. Completeness authority

A `KnotInvariantWitness` with `complete_for_domain = true` MUST reference:

- `KnotInvariantCompletenessWitness`
- `ProofWitness`
- `LeanCompilerWitness`

The completeness witness MUST name the domain. Completeness outside that domain is rejected.

## 7. Canonicalization authority

A `KnotCanonicalizationWitness` MUST declare canonicalization algorithm, canonical domain, hash algorithm, and collision policy. A canonical hash match cannot alone promote a knot equivalence claim.

## 8. Non-collapse categories

Knot transitions MUST use the promoted primitive categories `knot_diagram_presentation`, `knot_braid_presentation`, `knot_reidemeister_trace`, `knot_invariant_evidence`, `knot_canonical_form`, and `knot_equivalence_claim`.


## Draft 1.2 hardening addendum

Reidemeister witnesses MUST contain only Reidemeister/isotopy moves. Braid relations and Markov moves are separate first-class witnesses. Diagram `encoding_payload` MUST validate against a typed payload profile for planar diagram/PD code, Gauss code, Dowker-Thistlethwaite code, grid diagram, braid closure, or declared implementation-defined payload. Braid generator indices MUST be in `1..strand_count-1`; zero exponents are rejected unless a future version explicitly chooses a different policy. Invariant computation, invariant comparison, bounded-domain completeness, and proof-backed equivalence are distinct semantic classes.
