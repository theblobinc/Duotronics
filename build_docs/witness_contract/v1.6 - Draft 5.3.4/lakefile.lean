import Lake
open Lake DSL

package duotronic_formal where
  version := v!"5.3.4"
  keywords := #["evidence", "witness", "kernel", "proof"]

@[default_target]
lean_lib Duotronic where
  roots := #[`Duotronic]
