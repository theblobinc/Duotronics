# Roman Numerals as a Duotronic Auto-Learned Symbolic Numeric Profile v0.1

**Status:** Reference candidate profile  
**Version:** roman-numeral-profile@v0.1  
**Document kind:** Reference profile for auto-profile learning, bridge testing, and normalizer validation  
**Primary purpose:** Provide a simple, testable example of how the Duotronic engine can learn a symbolic numeric representation, generate witnesses, synthesize a profile, canonicalize surface forms, bridge into a numeric/core representation, and preserve absence/zero boundaries.

---

## 1. Research boundary

This profile is a reference candidate for internal testing. It is not a claim about all historical Roman numeral practices.

The purpose is to test the profile-learning pipeline on a bounded symbolic numeric system.

---

## 2. Object space

A Roman numeral object is a text surface form composed of Roman numeral symbols.

Reference symbol inventory:

```text
I V X L C D M
```

The profile may support two modes:

1. `canonical_mode`: accepts only canonical subtractive notation.
2. `loose_historical_mode`: accepts declared variants and normalizes them with expected loss.

The default for runtime tests should be `canonical_mode`.

---

## 3. Absence and zero policy

Roman numerals in this reference profile have no native zero.

The empty string is not zero. It is:

1. rejected by default; or
2. interpreted as structural absence only if the outer container declares that empty input means absence.

Malformed Roman symbols are invalid, not absence.

---

## 4. Candidate learning behavior

An auto-profile learner should discover or propose:

1. symbol inventory;
2. relative symbol values;
3. additive composition;
4. subtractive pairs;
5. repetition limits;
6. canonical spelling;
7. invalid ordering;
8. malformed characters;
9. range constraints;
10. bridge to an external integer or DPFC core import policy.

---

## 5. Candidate witness example

```yaml
CandidateWitness:
  witness_id: roman:witness:XLIV
  surface_form: XLIV
  proposed_segments: [XL, IV]
  proposed_value: 44
  proposed_rules:
    - X_before_L_subtractive
    - I_before_V_subtractive
  ambiguity: low
  trust_status: candidate
```

---

## 6. Normalizer

A reference normalizer should:

1. trim outer whitespace if declared nonsemantic;
2. uppercase symbols;
3. reject unknown symbols;
4. validate ordering;
5. validate repetition;
6. reduce accepted loose variants only in loose mode;
7. emit canonical subtractive form;
8. emit value under declared external integer bridge;
9. preserve original surface as witness history, not canonical identity.

---

## 7. Bridge

Possible bridge path:

```text
Roman surface
-> canonical Roman object
-> external positive integer
-> DPFC import policy
-> target family
```

The profile must declare whether the external integer is interpreted by positive-index policy or nonnegative export/import policy.

---

## 8. Failure cases

```text
IIII        loose or invalid depending on mode
IC          invalid subtractive form
VX          invalid order
AIV         malformed
empty       absence only if outer container declares it
0           invalid Roman symbol, not Roman zero
```

---

## 9. Fixture set

Minimum fixtures:

1. valid canonical examples: `I`, `II`, `III`, `IV`, `V`, `IX`, `XL`, `XC`, `CD`, `CM`, `MCMXCIV`;
2. invalid examples: `IC`, `VX`, `IL`, `MMMMMMMM` if range limit applies;
3. zero/absence examples: empty string, `0`, null container;
4. round-trip examples;
5. target-family conversion examples.

---

## 10. Promotion target

This profile should first become a `research_profile`, then a `sandbox_runtime_profile`, then a `reference_profile` only after deterministic parsing, bridge tests, and replay pass.
