# Hermetic Lean verifier protocol — Draft 5.3.3

The approved execution image contains a verifier binary at
`/opt/witness-authority/bin/verify-lean`. It receives a canonical request file,
an immutable submitted-source mount, a deterministic generated term-binding
module, and an empty output directory.

The verifier must build every imported submitted module from source in a fresh
output tree. It must not load `.olean`, native plugins, user configuration,
submitted Lake configuration, network content, or host caches. It resolves the
declaration in Lean's compiled environment, compares its elaborated type with
the claimed type, collects transitive declaration axioms, and writes exactly
one canonical `wc_lean_verifier_result/v1` JSON object.

The result binds the request, claim, theorem, artifact, immutable snapshot,
generated module, Lake executable, actual Lean executable, stdlib tree,
dependency closure, verifier binary, compiler profile, and execution image.
Ordinary stdout and stderr are diagnostics. They are never parsed for theorem
existence, type equality, axiom dependence, or authority.

The corpus specifies this protocol and the fail-closed host runtime. A real
image result is an authority-activation prerequisite and is not claimed by the
portable mock-based regression suite.
