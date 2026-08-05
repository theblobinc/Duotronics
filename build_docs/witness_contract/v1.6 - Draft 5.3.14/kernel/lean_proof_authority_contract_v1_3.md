# Lean Proof Authority Contract v1.3

**Applies to:** Witness Contract v1.6 Draft 5.3.4  
**Status:** normative fail-closed kernel contract

A Lean compiler witness may report `passed/proved` only when all of the
following are true:

1. the submitted artifact locator was normalized and confined to its bundle;
2. the entire source was copied into a sealed, content-addressed snapshot;
3. every artifact and metadata hash came from that sealed snapshot;
4. the deterministic generated term-binding module was separately sealed;
5. submitted code had no mount for the verifier request or final result;
6. the trusted verifier structurally resolved the declaration and compared its
   type under the declared normalization policy;
7. dependency and axiom closures were collected programmatically;
8. `sorryAx`, forbidden axioms, unsafe declarations, native injection, stale
   build output, and unresolved declarations were absent;
9. the trusted result carried an authorized verifier-result signature;
10. the result bound the exact snapshot, artifact, generated input, verifier,
    Lean, Lake, stdlib, dependencies, image, OCI runtime, and effective sandbox;
11. the snapshot remained unchanged after execution;
12. the compiler witness bound a valid authority snapshot and ledger cutoff;
13. the final witness was signed by the effective witness key; and
14. all deployment release gates required for theorem authority were active.

Failure or uncertainty at any step produces a nonpassing witness and cannot be
repaired by caller assertions, policy approval, repetition, or unsigned status
mutation.
