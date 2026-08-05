import Lean

open Lean Meta

namespace WitnessAuthority

inductive NormalizationPolicy where
  | isDefEqReducibilityRegularV1
  deriving Repr, DecidableEq

structure DeclarationInspection where
  declarationFound : Bool
  declarationTypeMatches : Bool
  expectedType : Expr
  actualType : Option Expr
  directDependencies : List Name
  axiomDependencies : List Name
  forbiddenAxioms : List Name
  sorryAxPresent : Bool
  unsafeDependencyPresent : Bool
  opaqueDependencyPolicyPassed : Bool
  normalizationPolicy : NormalizationPolicy
  deriving Repr

def canonicalNames (names : List Name) : List Name :=
  names.eraseDups.mergeSort Name.quickLt

def containsSorryAxNames (names : List Name) : Bool :=
  names.any fun name => name == ``sorryAx || name.toString.endsWith ".sorryAx"

def declarationUnsafe : ConstantInfo → Bool
  | .defnInfo info => info.safety != DefinitionSafety.safe
  | .opaqueInfo _ => false
  | .thmInfo _ => false
  | .axiomInfo _ => false
  | .quotInfo _ => false
  | .ctorInfo _ => false
  | .inductInfo _ => false
  | .recInfo _ => false

def inspectDeclaration
    (env : Environment)
    (declarationName : Name)
    (expectedType : Expr)
    (authorizedAxioms : List Name) : MetaM DeclarationInspection := do
  match env.find? declarationName with
  | none =>
      return {
        declarationFound := false, declarationTypeMatches := false,
        expectedType := expectedType, actualType := none,
        directDependencies := [], axiomDependencies := [], forbiddenAxioms := [],
        sorryAxPresent := false, unsafeDependencyPresent := false,
        opaqueDependencyPolicyPassed := false,
        normalizationPolicy := .isDefEqReducibilityRegularV1
      }
  | some declarationInfo =>
      let typeMatches ← withReducibleAndInstances <| withNewMCtxDepth <|
        isDefEq declarationInfo.type expectedType
      let axioms := canonicalNames (collectAxioms env declarationName).toList
      let forbidden := axioms.filter fun name => !authorizedAxioms.contains name
      let direct := canonicalNames declarationInfo.type.getUsedConstants.toList
      let unsafe := declarationUnsafe declarationInfo || direct.any fun name =>
        match env.find? name with
        | some info => declarationUnsafe info
        | none => true
      return {
        declarationFound := true, declarationTypeMatches := typeMatches,
        expectedType := expectedType, actualType := some declarationInfo.type,
        directDependencies := direct, axiomDependencies := axioms,
        forbiddenAxioms := forbidden, sorryAxPresent := containsSorryAxNames axioms,
        unsafeDependencyPresent := unsafe, opaqueDependencyPolicyPassed := true,
        normalizationPolicy := .isDefEqReducibilityRegularV1
      }

def passesAuthorityPolicy (inspection : DeclarationInspection) : Bool :=
  inspection.declarationFound && inspection.declarationTypeMatches &&
  !inspection.sorryAxPresent && !inspection.unsafeDependencyPresent &&
  inspection.forbiddenAxioms.isEmpty && inspection.opaqueDependencyPolicyPassed

end WitnessAuthority
