# Standalone Complete Corpus Rule — v1.6 Draft 5.2

Every Draft 5.2 distribution must be complete, standalone, and implementation-ready.

## Rule

A Draft 5.2 corpus zip must contain:

1. all carried-forward Draft 5.1 files,
2. all Draft 5.2 authority and theory contracts,
3. all Draft 5.2 runtime contracts,
4. all Draft 5.2 schemas,
5. all Draft 5.2 formal model stubs,
6. all Draft 5.2 validation and test documents,
7. a manifest, package inventory, checksum file, and reconciliation audit.

## No patch-only releases

Draft 5.2 must not be distributed as a delta-only package. Any implementation team must be able to inspect the zip alone and understand:

- the old NLA/authority substrate,
- the new formal evidence language,
- how the four pillars map to SRNN server implementation,
- what must be enforced at runtime,
- and what tests prove conformance.

## Supersession

Draft 5.2 supersedes Draft 5.1 only for the language, formalization, composition, replay-assumption, pragmatic authority, and non-collapse layers. It does not remove Draft 5.1 safety gates.
