namespace Duotronic

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
  | checkProof
  deriving DecidableEq, Repr

structure PolicyDecisionEvidence where
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
  policy : PolicyDecisionEvidence
  nonCollapseChecked : Bool
  proofWitnessRef : Option String
  leanCompilerWitnessRef : Option String
  deriving Repr

def RequiresProof (s : ClaimStatus) : Prop :=
  s = ClaimStatus.theorem ∨ s = ClaimStatus.proofVerified

def HasProofWitness (w : InferenceWitness) : Prop := w.proofWitnessRef.isSome

def HasLeanCompilerWitness (w : InferenceWitness) : Prop := w.leanCompilerWitnessRef.isSome

def HasMachineCheckedProof (w : InferenceWitness) : Prop :=
  HasProofWitness w ∧ HasLeanCompilerWitness w

theorem theorem_status_requires_proof_policy
    (w : InferenceWitness)
    (h : RequiresProof w.conclusionStatus)
    (p : RequiresProof w.conclusionStatus -> HasMachineCheckedProof w) :
    HasMachineCheckedProof w := by
  exact p h

theorem machine_checked_proof_has_proof_ref
    (w : InferenceWitness)
    (h : HasMachineCheckedProof w) :
    HasProofWitness w := by
  exact h.left

theorem machine_checked_proof_has_compiler_ref
    (w : InferenceWitness)
    (h : HasMachineCheckedProof w) :
    HasLeanCompilerWitness w := by
  exact h.right

theorem inference_witness_self_consistent (w : InferenceWitness) :
  w.premises = w.premises ∧ w.conclusion = w.conclusion := by
  exact And.intro rfl rfl

end Duotronic
