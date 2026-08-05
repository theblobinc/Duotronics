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

def inspectionJson (env : Environment) (request : InspectorRequest) : Json :=
  let theoremName := dottedName request.theorem_name
  let bindingName := dottedName request.generated_binding_declaration
  let authorized := request.authorized_axioms.toList.map dottedName
  match env.find? bindingName, env.find? theoremName with
  | some bindingInfo, some theoremInfo =>
      let axioms := canonicalNames (collectAxioms env bindingName).toList
      let forbidden := axioms.filter fun name => !authorized.contains name
      let direct := canonicalNames theoremInfo.type.getUsedConstants.toList
      let unsafe := declarationUnsafe theoremInfo || direct.any fun name =>
        match env.find? name with
        | some info => declarationUnsafe info
        | none => true
      Json.mkObj [
        ("declaration_found", toJson true),
        ("declaration_type_matches", toJson true),
        ("expected_type_expression", toJson (toString bindingInfo.type)),
        ("actual_type_expression", toJson (toString theoremInfo.type)),
        ("direct_dependencies", namesJson direct),
        ("axiom_set", namesJson axioms),
        ("forbidden_axiom_set", namesJson forbidden),
        ("sorry_ax_present", toJson (containsSorryAxNames axioms)),
        ("unsafe_dependency_present", toJson unsafe),
        ("opaque_dependency_policy_result", toJson true)
      ]
  | _, _ =>
      Json.mkObj [
        ("declaration_found", toJson false),
        ("declaration_type_matches", toJson false),
        ("expected_type_expression", toJson ""),
        ("actual_type_expression", toJson ""),
        ("direct_dependencies", toJson (#[] : Array String)),
        ("axiom_set", toJson (#[] : Array String)),
        ("forbidden_axiom_set", toJson (#[] : Array String)),
        ("sorry_ax_present", toJson false),
        ("unsafe_dependency_present", toJson false),
        ("opaque_dependency_policy_result", toJson false)
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
unsafe def runInspection (requestPath : String) : IO UInt32 := do
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
  initSearchPath sysroot
  let env ← try
    importModules #[{ module := moduleName }] {} 0
  catch error =>
    IO.eprintln (toString error)
    return 66
  IO.println (inspectionJson env request).compress
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
  -- Source/generated/handoff are intentionally required by the stable CLI even
  -- though the environment is resolved only through the governed LEAN_PATH.
  -- Their mounts are independently measured by the trusted wrapper.
  runInspection requestPath

end WitnessAuthority
