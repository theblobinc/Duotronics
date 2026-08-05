import Lean
import WitnessAuthority.Verifier

open Lean

namespace WitnessAuthority

def cliVersion : String := "witness-authority-inspector/1.0.0"

structure InspectorRequest where
  theorem_name : String
  generated_binding_module_path : String
  generated_binding_declaration : String
  authorized_axioms : Array String
  deriving FromJson

def dottedName (value : String) : Name :=
  value.splitOn "." |>.foldl (fun current part => Name.str current part) Name.anonymous

def moduleNameFromPath (value : String) : Except String Name := do
  if !value.endsWith ".lean" then
    throw "generated binding path must end in .lean"
  let withoutSuffix := value.dropRight 5
  if withoutSuffix.isEmpty || withoutSuffix.startsWith "/" || withoutSuffix.contains '\\' then
    throw "generated binding path is not a normalized module path"
  let parts := withoutSuffix.splitOn "/"
  if parts.any (fun part => part.isEmpty || part == "." || part == "..") then
    throw "generated binding path contains an unsafe component"
  return parts.foldl (fun current part => Name.str current part) Name.anonymous

def namesJson (names : List Name) : Json :=
  toJson (canonicalNames names |>.map Name.toString |>.toArray)

def inspectionJson (env : Environment) (request : InspectorRequest) : MetaM Json := do
  let theoremName := dottedName request.theorem_name
  let bindingName := dottedName request.generated_binding_declaration
  let authorized := request.authorized_axioms.toList.map dottedName
  match env.find? bindingName with
  | none =>
      return Json.mkObj [
        ("declaration_found", toJson false),
        ("declaration_type_matches", toJson false),
        ("expected_type_expression_fingerprint", toJson "missing_binding"),
        ("actual_type_expression_fingerprint", toJson "missing_declaration"),
        ("direct_dependencies", toJson (#[] : Array String)),
        ("dependency_closure", toJson (#[] : Array String)),
        ("axiom_set", toJson (#[] : Array String)),
        ("forbidden_axiom_set", toJson (#[] : Array String)),
        ("sorry_ax_present", toJson false),
        ("unsafe_dependency_present", toJson true),
        ("opaque_dependency_policy_result", toJson "not_evaluated")
      ]
  | some bindingInfo =>
      let inspection ← inspectDeclaration env theoremName bindingInfo.type authorized
      return Json.mkObj [
        ("declaration_found", toJson inspection.declarationFound),
        ("declaration_type_matches", toJson inspection.declarationTypeMatches),
        ("expected_type_expression_fingerprint", toJson inspection.expectedTypeFingerprint),
        ("actual_type_expression_fingerprint", toJson inspection.actualTypeFingerprint),
        ("direct_dependencies", namesJson inspection.directDependencies),
        ("dependency_closure", namesJson inspection.dependencyClosure),
        ("axiom_set", namesJson inspection.axiomDependencies),
        ("forbidden_axiom_set", namesJson inspection.forbiddenAxioms),
        ("sorry_ax_present", toJson inspection.sorryAxPresent),
        ("unsafe_dependency_present", toJson inspection.unsafeDependencyPresent),
        ("opaque_dependency_policy_result", toJson (if inspection.opaqueDependencyPolicyPassed then "passed" else "failed"))
      ]

def argumentValue (args : List String) (flag : String) : Except String String :=
  match args.dropWhile (fun value => value != flag) with
  | _ :: value :: _ => pure value
  | _ => throw s!"missing required inspector argument {flag}"

/--
Load the exact compiled generated binding module from the governed Lean search
path and inspect both the generated `BoundClaim` and submitted theorem in that
same environment. No source-text declaration search or stdout interpretation
participates in the result.
-/
unsafe def runInspection (requestPath handoffRoot : String) : IO UInt32 := do
  if handoffRoot != "/handoff" then
    IO.eprintln "handoff root must be the governed /handoff mount"
    return 64
  if let some ambientLeanPath ← IO.getEnv "LEAN_PATH" then
    if !ambientLeanPath.isEmpty then
      IO.eprintln "ambient LEAN_PATH is forbidden"
      return 64
  let handoffPath := System.FilePath.mk handoffRoot
  let handoffReal ← IO.FS.realPath handoffPath
  let governedReal ← IO.FS.realPath (System.FilePath.mk "/handoff")
  if handoffReal != governedReal then
    IO.eprintln "handoff root does not resolve to the governed mount"
    return 64
  let handoffOLean := handoffReal / "olean"
  unless (← handoffOLean.dirExists) do
    IO.eprintln "sealed handoff olean search root is absent"
    return 64
  let source ← IO.FS.readFile requestPath
  let json ← match Json.parse source with
    | .ok value => pure value
    | .error error => IO.eprintln error; return 65
  let request ← match fromJson? json with
    | .ok value => pure value
    | .error error => IO.eprintln error; return 65
  let moduleName ← match moduleNameFromPath request.generated_binding_module_path with
    | .ok value => pure value
    | .error error => IO.eprintln error; return 65
  let sysroot ← findSysroot
  initSearchPath sysroot [handoffOLean]
  let env ← try
    importModules #[{ module := moduleName }] {} 0
  catch error =>
    IO.eprintln (toString error)
    return 66
  let inspected ← Meta.MetaM.toIO (inspectionJson env request) {} { env := env } {} {}
  IO.println inspected.1.compress
  return 0

unsafe def main (args : List String) : IO UInt32 := do
  if args == ["--version"] then
    IO.println cliVersion
    return 0
  let allowed := ["--request", "--source", "--generated", "--handoff"]
  if args.length != allowed.length * 2 || allowed.any (fun flag => !args.contains flag) then
    IO.eprintln "expected exactly --request, --source, --generated, and --handoff"
    return 64
  let requestPath ← match argumentValue args "--request" with
    | .ok value => pure value
    | .error error => IO.eprintln error; return 64
  let handoffRoot ← match argumentValue args "--handoff" with
    | .ok value => pure value
    | .error error => IO.eprintln error; return 64
  -- Source and generated remain required so their sealed mounts stay bound to
  -- the stable CLI. Module resolution is constructed only from --handoff and
  -- the Lean sysroot; ambient LEAN_PATH never participates.
  runInspection requestPath handoffRoot

end WitnessAuthority
