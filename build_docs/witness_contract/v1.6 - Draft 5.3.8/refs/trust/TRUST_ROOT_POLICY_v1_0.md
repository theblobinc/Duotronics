# External Trust Root Policy v1.0

Package-local hashes provide integrity relative to a trusted copy. They do not prove who produced the package because an attacker who can replace the package can also recompute its hashes.

Draft 5.3.1 is intentionally `unsigned_not_frozen`. A frozen successor must:

1. hash the final checksum manifest and canonical descriptor;
2. sign those digests with a governance key held outside the release package;
3. publish the public key fingerprint through an independently controlled channel;
4. identify the signature algorithm, key identifier, signing principal, and time;
5. include revocation and rotation instructions; and
6. verify the signature before any package-local hash is trusted.

Private signing material must never be committed to the corpus. Test keys must be marked non-production and cannot satisfy the freeze gate.
