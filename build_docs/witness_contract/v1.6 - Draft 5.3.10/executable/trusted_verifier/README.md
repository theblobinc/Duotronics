# Trusted Lean verifier implementation — Draft 5.3.10

This directory contains the two separately governed OCI entry points.

- `compile_lean.py` receives only sealed submitted source, the generated binding,
  and its writable handoff. Every Lean invocation uses
  `-DwarningAsError=true`; warning diagnostics are rejected independently of
  exit status. The generated binding is a first-class `generated_binding`
  member of `compiled_modules`. The handoff records the pinned Lean executable
  digest, working directory, complete environment digest, reconstruction
  policy, and one command digest per canonical module.
- `verify_lean.py` runs only after the host has closed, fsynced, normalized, and
  sealed that handoff. It validates the manifest and artifact closure, invokes
  the trusted inspector, and writes only one private inspection record.

The selected inspector source generation is exactly
`formal/draft5_3_6/lean`. The Lake target, inspector-build Containerfile,
runtime Containerfile, reproducible-build script, this README, and
`INSPECTOR_BUILD_PROTOCOL.md` all use that same root. The target is:

```text
lake build witnessAuthorityInspector
```

The inspector accepts the exact `--handoff /handoff` argument, resolves it,
constructs `/handoff/olean` as its only non-sysroot module search path, and
rejects ambient `LEAN_PATH`.

Before inspection, the trusted consumer independently reconstructs the exact
ordered command list from canonical source/module/output paths, the pinned
Lean executable, `-DwarningAsError=true`, `/work`, and the sealed compilation
environment. Missing, extra, reordered, or self-reported command identities
are rejected before the inspector runs.

## Non-root handoff lifecycle

The governed launcher uses rootless `keep-id`. Both domains use the protected
authority UID/GID mapping, but never run concurrently and never receive the
same writable topology:

1. the compile domain alone receives `/handoff` read-write;
2. the host closes the container, fsyncs all files, rejects links and special
   files, verifies UID/GID and modes, and seals files/directories read-only;
3. the trusted domain receives that handoff read-only and receives a separate
   private inspection directory read-write;
4. the compile domain never receives the request, inspection, result, or key
   mounts.

Compile-domain and inspection-domain evidence are separately typed and bound
to their exact invocation digest, argv digest, mounts, runtime identity,
controls, user mapping, resource observations, and request-wide deadline.
Neither wrapper receives the final compiler-witness signing key.

The runtime image recipe pins its digest externally and verifies exact Python
3.12.13, `cryptography` 46.0.0, Lean executables, active schemas, and inspector
binary before the image can be attested. Digest markers and build outputs stay
fail-closed until the external image and reproducible-build gates complete.
