# Release notes - v1.6 Draft 5.3.17

5.3.17 is a standalone post-quantum migration corpus built from the complete 5.3.16 lineage. It is not a patch or overlay release.

Changes:

- replaced the legacy classical cryptographic profile throughout the active contract;
- introduced SHAKE256-512 authority identities and domain-separated Merkle trees;
- introduced ML-DSA-87 attestation envelopes;
- introduced ML-KEM-1024 recipient encapsulation and AES-256-GCM-SIV protected payloads;
- separated semantic, envelope, and attestation identities;
- made meta-object edges canonical typed objects with indexed directional relations;
- formalized object witnesses, recurrent witness state, and non-authoritative binary retrieval sidecars;
- added algorithm registries and critical-extension behavior for future contract upgrades;
- added an explicit mixed-version migration policy and runtime checklist;
- added portable schema, vector, manifest, and forbidden-primitive validation.
- retained all 1,968 baseline files, preserving overwritten 5.3.16 entry surfaces in history;
- migrated every text file that named the retired profile, including runtime code, SQL, schemas, fixtures, validators, tests, formal support files, manifests, and documentation;
- added a fail-closed standardized provider adapter and pinned runtime dependency profile;
- regenerated a whole-corpus schema registry, content map, inventory, provenance record, and path-bound manifest.

This artifact is complete as a development contract. It does not claim operational authority: external gates, production key ceremonies, provider attestations, formal toolchain runs, and runtime migration remain outstanding.
