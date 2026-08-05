namespace Duotronic.V2

structure ContentBinding where
  claimId : String
  claimHash : String
  theoremHash : String
  proofArtifactHash : String
  deriving DecidableEq, Repr

structure CompilerWitness where
  binding : ContentBinding
  compilerWitnessId : String
  verifierId : String
  policyId : String
  strictExecution : Bool
  passed : Bool
  noSorry : Bool
  noAdmit : Bool
  noUnapprovedAxioms : Bool
  signatureValid : Bool
  deriving DecidableEq, Repr

structure ProofWitness where
  binding : ContentBinding
  proofWitnessId : String
  compilerWitnessId : String
  verifierId : String
  policyId : String
  proved : Bool
  signatureValid : Bool
  deriving DecidableEq, Repr

structure NonCollapseTransition where
  claimId : String
  proofWitnessId : String
  policyId : String
  sourceCategory : String
  targetCategory : String
  transitionKind : String
  allowed : Bool
  deriving DecidableEq, Repr

structure StatusEvent where
  claimId : String
  proofWitnessId : String
  compilerWitnessId : String
  nonCollapseTransitionId : String
  policyId : String
  sourceStatus : String
  targetStatus : String
  allowed : Bool
  deriving DecidableEq, Repr

structure PromotionGate where
  binding : ContentBinding
  compiler : CompilerWitness
  proof : ProofWitness
  nonCollapseId : String
  nonCollapse : NonCollapseTransition
  statusEvent : StatusEvent
  policyAllows : Bool
  verifierActive : Bool
  allowed : Bool
  deriving Repr

def PromotionGate.Valid (g : PromotionGate) : Prop :=
  g.allowed = true ∧
  g.policyAllows = true ∧
  g.verifierActive = true ∧
  g.compiler.binding = g.binding ∧
  g.proof.binding = g.binding ∧
  g.compiler.compilerWitnessId = g.proof.compilerWitnessId ∧
  g.compiler.verifierId = g.proof.verifierId ∧
  g.compiler.policyId = g.proof.policyId ∧
  g.compiler.strictExecution = true ∧
  g.compiler.passed = true ∧
  g.compiler.noSorry = true ∧
  g.compiler.noAdmit = true ∧
  g.compiler.noUnapprovedAxioms = true ∧
  g.compiler.signatureValid = true ∧
  g.proof.proved = true ∧
  g.proof.signatureValid = true ∧
  g.nonCollapse.claimId = g.binding.claimId ∧
  g.nonCollapse.proofWitnessId = g.proof.proofWitnessId ∧
  g.nonCollapse.policyId = g.proof.policyId ∧
  g.nonCollapse.sourceCategory = "conjectural" ∧
  g.nonCollapse.targetCategory = "theorem" ∧
  g.nonCollapse.transitionKind = "proof_upgrade" ∧
  g.nonCollapse.allowed = true ∧
  g.statusEvent.claimId = g.binding.claimId ∧
  g.statusEvent.proofWitnessId = g.proof.proofWitnessId ∧
  g.statusEvent.compilerWitnessId = g.compiler.compilerWitnessId ∧
  g.statusEvent.nonCollapseTransitionId = g.nonCollapseId ∧
  g.statusEvent.policyId = g.proof.policyId ∧
  g.statusEvent.sourceStatus = "conjecture" ∧
  g.statusEvent.targetStatus = "theorem" ∧
  g.statusEvent.allowed = true

theorem valid_gate_is_content_bound (g : PromotionGate) (h : g.Valid) :
    g.compiler.binding = g.binding ∧ g.proof.binding = g.binding := by
  exact ⟨h.2.2.2.1, h.2.2.2.2.1⟩

theorem valid_gate_has_strict_passing_compiler (g : PromotionGate) (h : g.Valid) :
    g.compiler.strictExecution = true ∧
    g.compiler.passed = true ∧
    g.compiler.noSorry = true ∧
    g.compiler.noAdmit = true ∧
    g.compiler.noUnapprovedAxioms = true := by
  rcases h with ⟨_, _, _, _, _, _, _, _, hStrict, hPass, hSorry, hAdmit, hAxioms, _⟩
  exact ⟨hStrict, hPass, hSorry, hAdmit, hAxioms⟩

theorem valid_gate_has_relevant_noncollapse_path (g : PromotionGate) (h : g.Valid) :
    g.nonCollapse.claimId = g.binding.claimId ∧
    g.nonCollapse.proofWitnessId = g.proof.proofWitnessId ∧
    g.nonCollapse.sourceCategory = "conjectural" ∧
    g.nonCollapse.targetCategory = "theorem" ∧
    g.nonCollapse.transitionKind = "proof_upgrade" ∧
    g.nonCollapse.allowed = true := by
  rcases h with ⟨_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, hClaim, hProof, _, hSource, hTarget, hKind, hAllowed, _⟩
  exact ⟨hClaim, hProof, hSource, hTarget, hKind, hAllowed⟩

end Duotronic.V2
