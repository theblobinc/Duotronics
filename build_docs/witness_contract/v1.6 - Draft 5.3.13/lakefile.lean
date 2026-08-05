import Lake
open Lake DSL

package duotronic_formal where
  version := v!"5.3.13"
  keywords := #["evidence", "witness", "kernel", "proof"]

@[default_target]
lean_lib Duotronic where
  roots := #[`Duotronic]

lean_lib WitnessAuthority where
  srcDir := "formal/draft5_3_6/lean"
  roots := #[`WitnessAuthority.Verifier]

lean_exe witnessAuthorityInspector where
  srcDir := "formal/draft5_3_6/lean"
  root := `WitnessAuthority.InspectorMain
