import Lean

open Lean Meta

namespace WitnessAuthority

/-- Machine-facing result computed from Lean's compiled environment. -/
structure DeclarationInspection where
  declarationFound : Bool
  declarationTypeMatches : Bool
  axiomDependencies : List Name
  deriving Repr

/--
Inspect one compiled declaration without consulting source text or presentation
output. The approved verifier executable elaborates the claimed type in the same
pinned environment, calls this function, then emits the canonical result object
defined by `lean_verifier_result_v1.schema.json`.
-/
def inspectDeclaration
    (env : Environment)
    (declarationName : Name)
    (expectedType : Expr) : MetaM DeclarationInspection := do
  match env.find? declarationName with
  | none =>
      return {
        declarationFound := false
        declarationTypeMatches := false
        axiomDependencies := []
      }
  | some declarationInfo =>
      let typeMatches ← withNewMCtxDepth <| isDefEq declarationInfo.type expectedType
      let dependencies := (collectAxioms env declarationName).toList.mergeSort Name.quickLt
      return {
        declarationFound := true
        declarationTypeMatches := typeMatches
        axiomDependencies := dependencies
      }

/-- `sorry` and `admit` elaborate through `sorryAx` and are never authorized. -/
def containsSorryAx (inspection : DeclarationInspection) : Bool :=
  inspection.axiomDependencies.any fun name =>
    name == ``sorryAx || name.toString.endsWith ".sorryAx"

/-- Axiom authorization is an exact name-set containment check. -/
def axiomsAuthorized
    (inspection : DeclarationInspection)
    (authorized : List Name) : Bool :=
  !containsSorryAx inspection &&
    inspection.axiomDependencies.all fun dependency => authorized.contains dependency

end WitnessAuthority
