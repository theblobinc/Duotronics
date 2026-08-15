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
  dependencyClosure : List Name
  axiomDependencies : List Name
  forbiddenAxioms : List Name
  sorryAxPresent : Bool
  unsafeDependencyPresent : Bool
  opaqueDependencyPolicyPassed : Bool
  expectedTypeFingerprint : String
  actualTypeFingerprint : String
  normalizationPolicy : NormalizationPolicy
  deriving Repr

def canonicalNames (names : List Name) : List Name :=
  names.eraseDups.mergeSort Name.quickLt

def containsSorryAxNames (names : List Name) : Bool :=
  names.any fun name => name == ``sorryAx || name.toString.endsWith ".sorryAx"

def declarationUnsafe : ConstantInfo → Bool
  | .defnInfo info => info.safety != DefinitionSafety.safe
  | .opaqueInfo _ => true
  | .thmInfo _ => false
  | .axiomInfo _ => false
  | .quotInfo _ => false
  | .ctorInfo _ => false
  | .inductInfo _ => false
  | .recInfo _ => false

def constantDependencies (info : ConstantInfo) : List Name :=
  let fromType := info.type.getUsedConstants.toList
  let fromValue := match info.value? with
    | some value => value.getUsedConstants.toList
    | none => []
  canonicalNames (fromType ++ fromValue)

partial def dependencyClosure (env : Environment) (roots : List Name) : List Name :=
  let rec visit (pending seen : List Name) : List Name :=
    match pending with
    | [] => canonicalNames seen
    | name :: rest =>
        if seen.contains name then
          visit rest seen
        else
          match env.find? name with
          | none => visit rest (name :: seen)
          | some info => visit (constantDependencies info ++ rest) (name :: seen)
  visit (canonicalNames roots) []

partial def levelFingerprint : Level → String
  | .zero => "z"
  | .succ value => s!"s({levelFingerprint value})"
  | .max left right => s!"max({levelFingerprint left},{levelFingerprint right})"
  | .imax left right => s!"imax({levelFingerprint left},{levelFingerprint right})"
  | .param name => s!"p({name})"
  | .mvar ident => s!"m({reprStr ident})"

partial def expressionFingerprint : Expr → String
  | .bvar index => s!"b({index})"
  | .fvar ident => s!"f({reprStr ident})"
  | .mvar ident => s!"m({reprStr ident})"
  | .sort level => s!"sort({levelFingerprint level})"
  | .const name levels => s!"c({name};{String.intercalate "," (levels.map levelFingerprint)})"
  | .app fn arg => s!"app({expressionFingerprint fn},{expressionFingerprint arg})"
  | .lam name type body info => s!"lam({name};{reprStr info};{expressionFingerprint type};{expressionFingerprint body})"
  | .forallE name type body info => s!"forall({name};{reprStr info};{expressionFingerprint type};{expressionFingerprint body})"
  | .letE name type value body nondep => s!"let({name};{nondep};{expressionFingerprint type};{expressionFingerprint value};{expressionFingerprint body})"
  | .lit literal => s!"lit({reprStr literal})"
  | .mdata _ body => s!"mdata({expressionFingerprint body})"
  | .proj typeName index body => s!"proj({typeName};{index};{expressionFingerprint body})"

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
        dependencyClosure := [],
        sorryAxPresent := false, unsafeDependencyPresent := false,
        opaqueDependencyPolicyPassed := false,
        expectedTypeFingerprint := expressionFingerprint expectedType,
        actualTypeFingerprint := "",
        normalizationPolicy := .isDefEqReducibilityRegularV1
      }
  | some declarationInfo =>
      let typeMatches ← withReducibleAndInstances <| withNewMCtxDepth <|
        isDefEq declarationInfo.type expectedType
      let axiomArray ← collectAxioms declarationName
      let axioms := canonicalNames axiomArray.toList
      let forbidden := axioms.filter fun name => !authorizedAxioms.contains name
      let direct := constantDependencies declarationInfo
      let closure := dependencyClosure env direct
      let unsafePresent := declarationUnsafe declarationInfo || closure.any fun name =>
        match env.find? name with
        | some info => declarationUnsafe info
        | none => true
      let opaquePolicy := closure.all fun name =>
        match env.find? name with
        | some info => !declarationUnsafe info
        | none => false
      return {
        declarationFound := true, declarationTypeMatches := typeMatches,
        expectedType := expectedType, actualType := some declarationInfo.type,
        directDependencies := direct, dependencyClosure := closure,
        axiomDependencies := axioms,
        forbiddenAxioms := forbidden, sorryAxPresent := containsSorryAxNames axioms,
        unsafeDependencyPresent := unsafePresent, opaqueDependencyPolicyPassed := opaquePolicy,
        expectedTypeFingerprint := expressionFingerprint expectedType,
        actualTypeFingerprint := expressionFingerprint declarationInfo.type,
        normalizationPolicy := .isDefEqReducibilityRegularV1
      }

def passesAuthorityPolicy (inspection : DeclarationInspection) : Bool :=
  inspection.declarationFound && inspection.declarationTypeMatches &&
  !inspection.sorryAxPresent && !inspection.unsafeDependencyPresent &&
  inspection.forbiddenAxioms.isEmpty && inspection.opaqueDependencyPolicyPassed

end WitnessAuthority
