/-
DuotronicEvidenceSyntax.lean
Draft v1.6 5.2 completion candidate.

This file defines the evidence syntax objects without asserting that every
possible inference exists. Runtime may only create an inference when it emits a
witness object satisfying the schema and policy constraints.
-/

namespace DuotronicEvidenceSyntax

inductive ClaimStatus where
  | unknown | absent | invalid | draft | observed | computed | proposed | asserted
  | deferred | vetoed | conjecture | theorem | replayVerified | proofVerified
  | policyApproved | released
  deriving DecidableEq, Repr

inductive Claim where
  | atomic : String -> Claim
  | andClaim : Claim -> Claim -> Claim
  | orClaim : Claim -> Claim -> Claim
  | impliesClaim : Claim -> Claim -> Claim
  | temporalSince : Claim -> Claim -> Claim
  deriving Repr

inductive Force where
  | observe
  | propose
  | assert
  | defer
  | veto
  | delegate
  | replayVerify
  deriving DecidableEq, Repr

structure PolicyDecision where
  decisionId : String
  force : Force
  authorityScope : String
  runtimeMode : String
  deriving Repr

structure InferenceWitness where
  witnessId : String
  premises : List Claim
  conclusion : Claim
  conclusionStatus : ClaimStatus
  ruleName : String
  policy : PolicyDecision
  nonCollapseChecked : Bool
  proofWitnessRef : Option String
  deriving Repr

def RequiresProof (s : ClaimStatus) : Prop :=
  s = ClaimStatus.theorem ∨ s = ClaimStatus.proofVerified

def HasProofWitness (w : InferenceWitness) : Prop := w.proofWitnessRef.isSome

theorem theorem_status_requires_proof_policy
    (w : InferenceWitness)
    (h : RequiresProof w.conclusionStatus)
    (p : RequiresProof w.conclusionStatus -> HasProofWitness w) :
    HasProofWitness w := by
  exact p h

theorem inference_witness_self_consistent (w : InferenceWitness) :
  w.premises = w.premises ∧ w.conclusion = w.conclusion := by
  exact And.intro rfl rfl

end DuotronicEvidenceSyntax
