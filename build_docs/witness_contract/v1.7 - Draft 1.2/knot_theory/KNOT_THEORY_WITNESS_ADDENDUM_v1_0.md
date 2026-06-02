# Knot Theory Witness Addendum v1.0

## 1. Status

This addendum is normative for Duotronic Witness Contract v1.7 Draft 1 when knot-theory support is enabled. It is additive over the inherited evidence-language, proof-authority, non-collapse, replay, and policy rules.

## 2. Purpose

The addendum defines typed witness objects for knot theory workflows. It lets a runtime represent knot diagrams, braid words, Reidemeister move traces, invariant computations, and equivalence claims without silently confusing representation, computation, invariant evidence, and proof authority.

## 3. Non-collapse distinctions

A knot-theory runtime MUST preserve these distinctions:

1. A diagram is not automatically a knot type.
2. A braid word is not automatically a closed braid equivalence class.
3. A Reidemeister move trace is a transition witness, not an invariant computation.
4. An invariant value is not a proof of equivalence unless the invariant is declared complete for the domain and backed by proof authority.
5. Two diagrams with equal invariant values are not necessarily equivalent.
6. Orientation, mirror image, framing, labeling, and component ordering may not be silently discarded.
7. A simplification trace is not a theorem unless proof authority promotes it.
8. A computed invariant is not a human-attested mathematical fact.
9. A probabilistic candidate match is not a knot equivalence witness.
10. A canonical hash collision or mismatch is an invalid or indeterminate state, not a theorem.

## 4. Object model

### 4.1 KnotDiagramWitness

A `KnotDiagramWitness` declares a diagram presentation. It may use planar-diagram notation, Gauss code, Dowker-Thistlethwaite code, grid diagram data, or an implementation-defined encoding. It must include encoding type, orientation policy, component count, crossing count when known, and canonicalization status.

### 4.2 KnotBraidWordWitness

A `KnotBraidWordWitness` declares a braid representation with strand count, generator sequence, closure convention, orientation policy, and source authority. It may be linked to a diagram witness.

### 4.3 KnotReidemeisterMoveWitness

A `KnotReidemeisterMoveWitness` records an allowed diagram transition. It must identify source diagram, target diagram, move type, affected crossings or arcs when available, and whether the move has been checked by a deterministic verifier.

### 4.4 KnotInvariantWitness

A `KnotInvariantWitness` records a computed or proved invariant. It must declare invariant kind, domain, normalization convention, value, computation method, source diagram or braid reference, replay data, and proof authority if theorem-level use is intended.

### 4.5 KnotEquivalenceWitness

A `KnotEquivalenceWitness` records a claim that two knot presentations denote the same knot type or link type under a declared equivalence relation. It must include at least one authority path:

- explicit Reidemeister trace,
- verified braid relation/Markov trace,
- canonical normal form with collision policy,
- proof witness and Lean compiler witness,
- external theorem authority witness.

Invariant equality alone is insufficient unless the invariant is declared complete for the domain and that completeness claim is itself proof-witnessed.

## 5. Required syscalls

A v1.7 knot-theory runtime MUST expose these logical syscalls:

- `knot_encode`: requires `KnotDiagramWitness` or `KnotBraidWordWitness`.
- `knot_move`: requires `KnotReidemeisterMoveWitness`.
- `knot_invariant`: requires `KnotInvariantWitness`.
- `knot_equivalence`: requires `KnotEquivalenceWitness` and one declared authority path.

## 6. Equivalence authority ladder

The following authority levels are ordered from weaker to stronger:

1. `candidate`: human or model-generated candidate relation.
2. `computed_support`: invariant or heuristic support.
3. `trace_verified`: deterministic Reidemeister or braid trace verified.
4. `canonical_form_verified`: canonical normal form match under declared collision policy.
5. `proof_verified`: theorem-level proof authority attached.

A runtime may use weaker authority as search guidance, but may not promote it to stronger authority without an explicit non-collapse transition and required witnesses.

## 7. Invariant witness rule

A knot invariant witness MUST record its normalization convention. For example, polynomial invariants are ambiguous without choices about variable, orientation, mirror, writhe normalization, and sign conventions. Missing normalization places the witness in `candidate` or `computed_support` status only.

## 8. Reidemeister trace rule

A Reidemeister trace MUST be ordered, replayable, and typechecked. Each step must identify source and target diagram references. A runtime may compress traces, but the replay grammar must recover or verify the transition sequence.

## 9. Bayesian interaction

Bayesian logic may be used to rank likely equivalence, select promising simplification moves, or estimate confidence in a computational pipeline. Bayesian support is not mathematical proof and cannot satisfy `knot_equivalence` authority by itself.

## 10. Formal proof interaction

If a knot equivalence claim is promoted to theorem/proof-verified status, the inherited Lean/Lake proof authority rules apply. The claim must carry proof witness, Lean compiler witness, theorem promotion gate, policy decision, and non-collapse transition.

## 11. Failure states

A runtime MUST fail closed for:

- missing diagram encoding type,
- crossing count mismatch without declared reason,
- equivalence claim without authority path,
- invariant used as equivalence proof without completeness authority,
- hidden orientation or mirror policy,
- replay trace unavailable for a trace-verified claim,
- proof-level claim without proof authority,
- Bayesian confidence used as equivalence authority.
