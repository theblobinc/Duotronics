import Duotronic.EvidenceSyntax

namespace Duotronic

inductive LeanCompilerResult where
  | passed
  | failed
  | unavailable
  deriving DecidableEq, Repr

inductive TheoremArtifactStatus where
  | proved
  | failed
  | sorryStub
  | axiomDependent
  | sourceHashMismatch
  deriving DecidableEq, Repr

structure LeanCompilerWitness where
  witnessId : String
  toolchain : String
  lakefileHash : String
  sourceTreeHash : String
  command : String
  result : LeanCompilerResult
  containsSorry : Bool
  containsAdmit : Bool
  unapprovedAxiomCount : Nat
  compiledModules : List String
  deriving Repr

def LeanCompilerWitness.IsPassing (w : LeanCompilerWitness) : Prop :=
  w.result = LeanCompilerResult.passed ∧
  w.containsSorry = false ∧
  w.containsAdmit = false ∧
  w.unapprovedAxiomCount = 0

structure TheoremStatus where
  theoremName : String
  artifactStatus : TheoremArtifactStatus
  fileHash : String
  sourceHashMatches : Bool
  axiomNames : List String
  deriving Repr

def TheoremStatus.IsAccepted (s : TheoremStatus) : Prop :=
  s.artifactStatus = TheoremArtifactStatus.proved ∧
  s.sourceHashMatches = true ∧
  s.axiomNames = []

structure ProofWitness where
  proofWitnessId : String
  claimId : String
  theoremName : String
  compiler : LeanCompilerWitness
  theoremStatus : TheoremStatus
  policyDecisionId : String
  deriving Repr

def ProofWitness.Valid (w : ProofWitness) : Prop :=
  w.compiler.IsPassing ∧
  w.theoremStatus.IsAccepted ∧
  w.theoremName = w.theoremStatus.theoremName ∧
  w.theoremName ≠ "" ∧
  w.policyDecisionId ≠ ""

structure ClaimStatusTransition where
  claimId : String
  sourceStatus : ClaimStatus
  targetStatus : ClaimStatus
  transitionKind : String
  allowed : Bool
  proofWitness : Option ProofWitness
  deriving Repr

def TransitionRequiresLeanProof (t : ClaimStatusTransition) : Prop :=
  RequiresProof t.targetStatus

def TransitionHasValidLeanProof (t : ClaimStatusTransition) : Prop :=
  match t.proofWitness with
  | some p => p.Valid
  | none => False

def TheoremPromotionAllowed (t : ClaimStatusTransition) : Prop :=
  t.allowed = true ∧ TransitionHasValidLeanProof t

theorem valid_proof_witness_has_passing_compiler
    (w : ProofWitness)
    (h : ProofWitness.Valid w) :
    w.compiler.IsPassing := by
  exact h.left

theorem valid_proof_witness_has_accepted_theorem_status
    (w : ProofWitness)
    (h : ProofWitness.Valid w) :
    w.theoremStatus.IsAccepted := by
  exact h.right.left

theorem theorem_promotion_requires_valid_lean_proof
    (t : ClaimStatusTransition)
    (h : TheoremPromotionAllowed t) :
    TransitionHasValidLeanProof t := by
  exact h.right

theorem theorem_promotion_carries_passing_compiler
    (t : ClaimStatusTransition)
    (hAllowed : TheoremPromotionAllowed t)
    (p : ProofWitness)
    (hProof : t.proofWitness = some p) :
    p.compiler.IsPassing := by
  have hValid : TransitionHasValidLeanProof t := hAllowed.right
  unfold TransitionHasValidLeanProof at hValid
  rw [hProof] at hValid
  exact valid_proof_witness_has_passing_compiler p hValid

end Duotronic
