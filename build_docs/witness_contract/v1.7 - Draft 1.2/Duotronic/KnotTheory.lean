namespace Duotronic

inductive KnotEncodingType where
  | planarDiagram
  | gaussCode
  | dowkerThistlethwaite
  | gridDiagram
  | braidClosure
  | implementationDefined
  deriving DecidableEq, Repr

inductive ReidemeisterMove where
  | R1
  | R1Inverse
  | R2
  | R2Inverse
  | R3
  | isotopyRelabeled
  deriving DecidableEq, Repr

inductive KnotAuthorityLevel where
  | candidate
  | computedSupport
  | traceVerified
  | canonicalFormVerified
  | proofVerified
  | rejected
  deriving DecidableEq, Repr

structure KnotDiagramWitness where
  diagramId : String
  encodingType : KnotEncodingType
  componentCount : Nat
  crossingCount : Option Nat
  orientationPolicy : String
  nonCollapseTransitionId : String
  deriving Repr

structure KnotBraidWordWitness where
  braidId : String
  strandCount : Nat
  closureConvention : String
  orientationPolicy : String
  nonCollapseTransitionId : String
  deriving Repr

structure KnotReidemeisterMoveWitness where
  moveWitnessId : String
  sourceDiagramId : String
  targetDiagramId : String
  moveType : ReidemeisterMove
  checked : Bool
  nonCollapseTransitionId : String
  deriving Repr

structure KnotBraidRelationWitness where
  braidRelationWitnessId : String
  sourceBraidId : String
  targetBraidId : String
  relationType : String
  checked : Bool
  nonCollapseTransitionId : String
  deriving Repr

structure KnotMarkovMoveWitness where
  markovMoveWitnessId : String
  sourceBraidId : String
  targetBraidId : String
  markovMoveType : String
  checked : Bool
  nonCollapseTransitionId : String
  deriving Repr

structure KnotPresentationTransitionWitness where
  presentationTransitionWitnessId : String
  sourceObjectRef : String
  targetObjectRef : String
  transitionKind : String
  transitionWitnessRef : String
  deriving Repr

structure KnotReidemeisterTraceWitness where
  traceWitnessId : String
  sourceDiagramId : String
  targetDiagramId : String
  moveRefsNonempty : Bool
  traceVerified : Bool
  nonCollapseTransitionId : String
  deriving Repr

structure KnotCanonicalizationWitness where
  canonicalizationWitnessId : String
  sourceObjectRef : String
  canonicalFormHash : String
  collisionPolicy : String
  nonCollapseTransitionId : String
  deriving Repr

structure KnotInvariantWitness where
  invariantWitnessId : String
  sourceObjectRef : String
  invariantKind : String
  normalizationConvention : String
  completeForDomain : Bool
  completenessWitnessRef : Option String
  proofWitnessRef : Option String
  leanCompilerWitnessRef : Option String
  deriving Repr

structure KnotInvariantCompletenessWitness where
  completenessWitnessId : String
  invariantWitnessId : String
  domainRef : String
  proofWitnessRef : String
  leanCompilerWitnessRef : String
  deriving Repr

structure KnotEquivalenceAuthorityPath where
  authorityPathId : String
  sourceObjectRef : String
  targetObjectRef : String
  pathNonempty : Bool
  authorityLevel : KnotAuthorityLevel
  nonCollapseTransitionId : String
  policyDecisionId : String
  deriving Repr

structure KnotEquivalenceWitness where
  equivalenceWitnessId : String
  sourceObjectRef : String
  targetObjectRef : String
  authorityLevel : KnotAuthorityLevel
  authorityPathId : String
  nonCollapseTransitionId : String
  policyDecisionId : String
  deriving Repr

def HasAuthorityPath (w : KnotEquivalenceWitness) : Prop := w.authorityPathId ≠ ""
def HasKnotPolicyDecision (w : KnotEquivalenceWitness) : Prop := w.policyDecisionId ≠ ""
def HasKnotNonCollapseTransition (w : KnotEquivalenceWitness) : Prop := w.nonCollapseTransitionId ≠ ""
def KnotEquivalenceAuthorized (w : KnotEquivalenceWitness) : Prop :=
  HasAuthorityPath w ∧ HasKnotPolicyDecision w ∧ HasKnotNonCollapseTransition w

def KnotTraceReplayable (w : KnotReidemeisterTraceWitness) : Prop :=
  w.moveRefsNonempty = true ∧ w.traceVerified = true ∧ w.nonCollapseTransitionId ≠ ""

def KnotCompleteInvariantBackedByProof (w : KnotInvariantWitness) : Prop :=
  w.completeForDomain = true → w.completenessWitnessRef.isSome ∧ w.proofWitnessRef.isSome ∧ w.leanCompilerWitnessRef.isSome

theorem knot_equivalence_requires_authority_path
    (w : KnotEquivalenceWitness)
    (h : KnotEquivalenceAuthorized w) :
    HasAuthorityPath w := by
  exact h.left

theorem knot_equivalence_requires_policy
    (w : KnotEquivalenceWitness)
    (h : KnotEquivalenceAuthorized w) :
    HasKnotPolicyDecision w := by
  exact h.right.left

theorem knot_equivalence_requires_non_collapse
    (w : KnotEquivalenceWitness)
    (h : KnotEquivalenceAuthorized w) :
    HasKnotNonCollapseTransition w := by
  exact h.right.right

theorem knot_trace_requires_nonempty_moves
    (w : KnotReidemeisterTraceWitness)
    (h : KnotTraceReplayable w) :
    w.moveRefsNonempty = true := by
  exact h.left

theorem knot_complete_invariant_requires_proof_bundle
    (w : KnotInvariantWitness)
    (h : KnotCompleteInvariantBackedByProof w)
    (hc : w.completeForDomain = true) :
    w.completenessWitnessRef.isSome ∧ w.proofWitnessRef.isSome ∧ w.leanCompilerWitnessRef.isSome := by
  exact h hc

end Duotronic
