# Corpus Review: v1.4 Draft to v1.4 Draft 2

**Status:** Internal corpus review and update rationale  
**Version:** corpus-review-v1.4-draft-to-draft-2  
**Document kind:** Review-to-spec integration note  
**Primary purpose:** Record why v1.4 Draft 2 exists and which review items were promoted into source-spec changes.

---

## 1. Summary

v1.4 Draft was coherent and implementation-oriented. Draft 2 does not replace its architecture. It tightens the places where the first draft left governance edges underspecified.

The strongest Draft 1 concepts remain:

1. DPFC owns representational core rules.
2. The Witness Contract owns runtime trust.
3. Bridges require validation, canonicalization, preservation, expected-loss, replay, and policy.
4. Learned profiles start as candidates.
5. Search/social/model outputs are evidence, not truth.
6. Distributed model nodes emit witnesses, not authority.

Draft 2 makes those ideas more enforceable.

---

## 2. Integrated review items

Draft 2 integrates these changes:

1. Unifies profile status names across the Family Registry and Profile Synthesis Registry.
2. States that the Profile Synthesis Registry governs pre-promotion lifecycle and promotion evidence, while the Family Registry records promoted runtime-referenceable families/profiles.
3. Prevents human-authored profiles from bypassing the promotion ladder.
4. Adds a concrete `AutoProfileCandidate` schema and minimum fixture requirements.
5. Defines partial bridge authority and failure reporting.
6. Defines how deleted or unavailable sources affect dependent claim witnesses.
7. Limits non-deterministic node outputs to audit-only or sandbox paths unless replay requirements do not apply and policy explicitly allows use.
8. Allows candidate/research retention metrics to exist without baselines, while requiring baselines before reference/normative promotion.
9. Adds `learning_mode` as a separate L5 policy dimension.
10. Strengthens glyphic-script identity around perceptual hash algorithms and declared collision/variation risks.
11. Strengthens English claim equivalence and modality-preservation rules.
12. Expands starter object shapes.
13. Adds a central glossary.

---

## 3. No fundamental rewrite

Draft 2 is not a conceptual reset. It is a governance-hardening pass.

The corpus is still organized around:

```text
evidence
-> witness
-> canonical identity
-> bridge / profile
-> replay
-> policy
-> runtime use
```

The key Draft 2 improvement is that profile birth, source evidence, node output, and registry promotion are now more explicit and less ambiguous.

---

## 4. Implementation readiness

After Draft 2, the recommended implementation path remains:

1. Roman numeral profile learner;
2. English claim/evidence extractor;
3. source/social evidence wrapper;
4. distributed node witness logger;
5. bridge and normalizer conformance harness;
6. profile synthesis registry;
7. L5 policy gate;
8. glyphic visual segmentation sandbox.
