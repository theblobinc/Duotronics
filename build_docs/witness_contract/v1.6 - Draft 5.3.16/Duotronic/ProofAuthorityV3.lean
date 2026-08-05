namespace Duotronic.V3

structure CompilerAuthority where
  statementBound : Bool
  generatedTargetIsExact : Bool
  axiomInspectionComplete : Bool
  noSorryAx : Bool
  noUnapprovedAxioms : Bool
  warningsAsErrors : Bool
  deriving DecidableEq, Repr

def CompilerAuthority.Valid (c : CompilerAuthority) : Prop :=
  c.statementBound = true ∧
  c.generatedTargetIsExact = true ∧
  c.axiomInspectionComplete = true ∧
  c.noSorryAx = true ∧
  c.noUnapprovedAxioms = true ∧
  c.warningsAsErrors = true

structure EffectiveKey where
  status : String
  validFromTick : Nat
  validUntilTick : Nat
  superseded : Bool
  deriving DecidableEq, Repr

def EffectiveKey.ValidAt (k : EffectiveKey) (tick : Nat) : Prop :=
  k.status = "active" ∧
  k.validFromTick ≤ tick ∧
  tick ≤ k.validUntilTick ∧
  k.superseded = false

structure PromotionAuthority where
  allowed : Bool
  compiler : CompilerAuthority
  compilerSignatureValid : Bool
  proofSignatureValid : Bool
  key : EffectiveKey
  gateTick : Nat
  deriving Repr

def PromotionAuthority.CurrentlyAuthoritative (g : PromotionAuthority) : Prop :=
  g.allowed = true ∧
  g.compiler.Valid ∧
  g.compilerSignatureValid = true ∧
  g.proofSignatureValid = true ∧
  g.key.ValidAt g.gateTick

theorem current_authority_binds_claimed_statement
    (g : PromotionAuthority) (h : g.CurrentlyAuthoritative) :
    g.compiler.statementBound = true := by
  rcases h with ⟨_, compilerValid, _, _, _⟩
  exact compilerValid.1

theorem current_authority_has_compiled_axiom_inspection
    (g : PromotionAuthority) (h : g.CurrentlyAuthoritative) :
    g.compiler.axiomInspectionComplete = true ∧
    g.compiler.noSorryAx = true ∧
    g.compiler.noUnapprovedAxioms = true := by
  rcases h with ⟨_, compilerValid, _, _, _⟩
  rcases compilerValid with ⟨_, _, inspection, noSorry, noAxioms, _⟩
  exact ⟨inspection, noSorry, noAxioms⟩

theorem current_authority_has_verified_signatures_and_effective_key
    (g : PromotionAuthority) (h : g.CurrentlyAuthoritative) :
    g.compilerSignatureValid = true ∧
    g.proofSignatureValid = true ∧
    g.key.ValidAt g.gateTick := by
  rcases h with ⟨_, _, compilerSignature, proofSignature, keyValid⟩
  exact ⟨compilerSignature, proofSignature, keyValid⟩

end Duotronic.V3
