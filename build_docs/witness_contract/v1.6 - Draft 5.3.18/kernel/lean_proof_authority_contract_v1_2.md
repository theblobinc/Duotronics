# Lean Proof Authority Contract v1.2

**Applies to:** Witness Contract v1.6 Draft 5.3.3  
**Status:** active kernel profile; permanently unfrozen

The proof-check request selects only a governance-signed compiler-profile
identifier and a pre-ingested source bundle. The authority service—not the
client—selects the OCI runtime, execution image, Lake, actual Lean compiler,
stdlib, dependency closure, verifier binary, sandbox policy, key, and timestamp.

The service rejects symlinks, prebuilt Lean outputs, native plugins, executable
files, and artifacts outside the source bundle. It creates a read-only immutable
snapshot whose digest must equal both source hashes taken around the copy. It
compiles a deterministic direct term-binding module in a networkless,
resource-limited, read-only sandbox.

Only a canonical structured result produced inside the governed image can
confirm declaration existence, elaborated type equality, clean source build,
and the transitive axiom set. Stdout/stderr and source-text scanning are
non-authoritative. Every closure digest and safety Boolean is signed, persisted
append-only, and required by the SQL theorem gate.

Governance-signed lifecycle and supersession events determine key authority.
Historical evaluation uses a signed explicit authority snapshot; wall-clock
views are convenience-only. Portable mock tests are regression evidence and
cannot activate theorem authority.
