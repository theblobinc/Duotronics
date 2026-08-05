import Duotronic.ProofAuthority

namespace Duotronic

inductive WitnessKind where
  | evidenceClaim
  | compoundClaimWitness
  | inferenceWitness
  | verificationResult
  | replayAssumptionManifest
  | authorityDelegationChain
  | claimStatusTransition
  | nonCollapseTransition
  | taskStepWitness
  | taskResultWitness
  | conflictAdjudicationWitness
  | kernelTransaction
  | replaySign
  | verificationGrammar
  | leanCompilerWitness
  | proofWitness
  deriving DecidableEq, Repr

inductive Syscall where
  | observe
  | compose
  | infer
  | verify
  | replay
  | delegate
  | promote
  | compute
  | adjudicate
  | rollback
  | export
  | checkProof
  deriving DecidableEq, Repr

def Syscall.requiredWitness : Syscall -> List WitnessKind
  | Syscall.observe => [WitnessKind.evidenceClaim]
  | Syscall.compose => [WitnessKind.compoundClaimWitness]
  | Syscall.infer => [WitnessKind.inferenceWitness]
  | Syscall.verify => [WitnessKind.verificationResult]
  | Syscall.replay => [WitnessKind.replayAssumptionManifest, WitnessKind.verificationResult]
  | Syscall.delegate => [WitnessKind.authorityDelegationChain]
  | Syscall.promote => [WitnessKind.claimStatusTransition, WitnessKind.nonCollapseTransition]
  | Syscall.compute => [WitnessKind.taskStepWitness, WitnessKind.taskResultWitness]
  | Syscall.adjudicate => [WitnessKind.conflictAdjudicationWitness]
  | Syscall.rollback => [WitnessKind.kernelTransaction]
  | Syscall.export => [WitnessKind.replaySign, WitnessKind.verificationGrammar]
  | Syscall.checkProof => [WitnessKind.leanCompilerWitness, WitnessKind.proofWitness]

def Syscall.HasRequiredWitness (s : Syscall) (k : WitnessKind) : Prop :=
  k ∈ s.requiredWitness

theorem check_proof_requires_lean_compiler_witness :
    Syscall.HasRequiredWitness Syscall.checkProof WitnessKind.leanCompilerWitness := by
  unfold Syscall.HasRequiredWitness Syscall.requiredWitness
  simp

theorem check_proof_requires_proof_witness :
    Syscall.HasRequiredWitness Syscall.checkProof WitnessKind.proofWitness := by
  unfold Syscall.HasRequiredWitness Syscall.requiredWitness
  simp

theorem promote_requires_status_transition :
    Syscall.HasRequiredWitness Syscall.promote WitnessKind.claimStatusTransition := by
  unfold Syscall.HasRequiredWitness Syscall.requiredWitness
  simp

theorem promote_requires_non_collapse_transition :
    Syscall.HasRequiredWitness Syscall.promote WitnessKind.nonCollapseTransition := by
  unfold Syscall.HasRequiredWitness Syscall.requiredWitness
  simp

end Duotronic
