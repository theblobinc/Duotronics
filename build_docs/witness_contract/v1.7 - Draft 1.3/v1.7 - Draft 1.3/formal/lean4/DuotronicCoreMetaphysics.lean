/-
DuotronicCoreMetaphysics.lean
Draft v1.6 5.2 completion candidate.

This file states the canonical primitive non-collapse distinctions without axioms,
sorry, or placeholder proof markers. Runtime conformance is established by
schemas, fixtures, SQL constraints, and implementation tests.
-/

namespace Duotronic

-- v1.7 Draft 1.3 primitive parity tokens:
-- probabilistic_prior probabilistic_likelihood probabilistic_posterior bayesian_decision_support
-- bayesian_calibration_evidence knot_diagram_presentation knot_braid_presentation
-- knot_reidemeister_trace knot_invariant_evidence knot_canonical_form knot_equivalence_claim


inductive PrimitiveState where
  | zero
  | absence
  | unknown
  | invalid
  | empty
  | nullValue
  | computationalEvidence
  | theorem
  | conjectural
  | selfTrained
  | authoritative
  | auditOnly
  | active
  | observation
  | proof
  | explanation
  | fact
  | policyApproval
  | humanAttestation
  | syntheticWitness
  | activationWitness
  | probabilisticPrior
  | probabilisticLikelihood
  | probabilisticPosterior
  | bayesianDecisionSupport
  | bayesianCalibrationEvidence
  | knotDiagramPresentation
  | knotBraidPresentation
  | knotReidemeisterTrace
  | knotInvariantEvidence
  | knotCanonicalForm
  | knotEquivalenceClaim
  deriving DecidableEq, Repr

def Collapsible (a b : PrimitiveState) : Prop := a = b

theorem zero_not_absence : PrimitiveState.zero ≠ PrimitiveState.absence := by decide
theorem unknown_not_invalid : PrimitiveState.unknown ≠ PrimitiveState.invalid := by decide
theorem empty_not_null : PrimitiveState.empty ≠ PrimitiveState.nullValue := by decide
theorem computation_not_theorem : PrimitiveState.computationalEvidence ≠ PrimitiveState.theorem := by decide
theorem conjecture_not_theorem : PrimitiveState.conjectural ≠ PrimitiveState.theorem := by decide
theorem self_trained_not_authoritative : PrimitiveState.selfTrained ≠ PrimitiveState.authoritative := by decide
theorem audit_not_active : PrimitiveState.auditOnly ≠ PrimitiveState.active := by decide
theorem observation_not_proof : PrimitiveState.observation ≠ PrimitiveState.proof := by decide
theorem explanation_not_fact : PrimitiveState.explanation ≠ PrimitiveState.fact := by decide
theorem policy_approval_not_human_attestation : PrimitiveState.policyApproval ≠ PrimitiveState.humanAttestation := by decide
theorem synthetic_witness_not_activation_witness : PrimitiveState.syntheticWitness ≠ PrimitiveState.activationWitness := by decide

structure TransitionWitness where
  source : PrimitiveState
  target : PrimitiveState
  externalWitnessRef : String
  policyDecisionRef : String
  proofWitnessRef : Option String
  deriving Repr

def RequiresExternalWitness (s t : PrimitiveState) : Prop := s ≠ t

def HasExternalWitness (w : TransitionWitness) : Prop := w.externalWitnessRef ≠ "" ∧ w.policyDecisionRef ≠ ""

def HasProofWitness (w : TransitionWitness) : Prop := w.proofWitnessRef.isSome

theorem no_silent_collapse (s t : PrimitiveState) :
  s ≠ t -> ¬ Collapsible s t := by
  intro h
  unfold Collapsible
  exact h

theorem witnessed_transition_preserves_distinction
    (w : TransitionWitness)
    (h : w.source ≠ w.target) :
    RequiresExternalWitness w.source w.target := by
  exact h

end Duotronic
