import Lake
open Lake DSL

package duotronic_formal where
  version := v!"1.7.0"
  keywords := #["evidence", "witness", "kernel", "proof", "bayesian", "knot-theory"]

@[default_target]
lean_lib Duotronic where
  roots := #[`Duotronic]
