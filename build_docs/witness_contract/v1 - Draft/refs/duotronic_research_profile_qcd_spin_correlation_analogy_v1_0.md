# QCD Spin-Correlation Measurement as a Bounded Duotronic Analogy Profile v1.0

**Status:** Analogy/research profile paper  
**Version:** research-qcd-analogy@v1.0  
**Document kind:** Bounded analogy paper, not physics claim and not normative core  
**Primary purpose:** Extract method-level lessons from the STAR spin-correlation measurement for Duotronic witness retention, decoherence-style diagnostics, and hidden-to-observable transition reasoning without claiming that Duotronics models QCD.

> Drafting note. This document follows the one-based Duotronic style for public headings, claim labels, and checklist labels. External domains, wire formats, host languages, and physical sciences may still contain ordinary zero where their own standards require it. The Duotronic rule is not that zero is forbidden; the rule is that absence, origin, invalidity, numeric zero, raw witness evidence, canonical identity, and transport encoding must not be silently collapsed.

---

## Document status tag key

> **Status tag:** reference

Every major section carries one primary status tag. If a section needs secondary classification, use `Related tags:` on a separate line.

| Tag | Meaning | Promotion rule |
|---|---|---|
| `normative` | Binding rule for the active source document. | Conforming implementations must follow it. |
| `reference` | Examples, schemas, fixtures, algorithms, explanations, and implementation aids. | Useful for implementation; not a new semantic rule unless cited by a normative section. |
| `research` | Experimental metric, profile, analogy, or benchmark candidate. | Must remain opt-in until promoted by evidence. |
| `future` | Useful planned work not active yet. | Must not be treated as live authority. |
| `analogy` | Outside-domain comparison or inspiration. | Must not be treated as proof or runtime authority. |


## 1. Boundary statement

> **Status tag:** analogy

This paper is an analogy profile. It does not claim that DPFC models quantum chromodynamics, virtual particles, confinement, quark condensates, entanglement, or hadronization. It imports only method-level patterns:

1. hidden correlated source;
2. transition through a complex medium;
3. observable final-state proxy;
4. correlation measurement;
5. baseline comparison;
6. loss of correlation with separation.

## 2. Source-paper method pattern

> **Status tag:** reference

The STAR measurement studies whether spin-correlated strange quark-antiquark pairs can leave a measurable correlation in final-state Lambda hyperon pairs. The paper reports a relative polarization signal and observes that the correlation vanishes for widely separated hyperon pairs. For Duotronics, the useful pattern is not the physics result; it is the measurement design.

## 3. Duotronic analogy map

> **Status tag:** analogy

| QCD measurement concept | Duotronic analogy | Boundary |
|---|---|---|
| virtual correlated pair | hidden source correlation | analogy only |
| hadronization | transformation through runtime/transport/canonicalization | analogy only |
| Lambda pair | observable witness pair | analogy only |
| spin correlation | retained invariant | analogy only |
| angular separation | transformation distance / context separation | analogy only |
| decoherence | retention loss or diagnostic collapse | analogy only |

## 4. Retention diagnostic pattern

> **Status tag:** research

The useful Duotronic abstraction is:

```text
hidden structure
-> transformation
-> observable proxy
-> correlation measurement
-> baseline comparison
-> distance/separation dependence
```

This can inspire retained-correlation diagnostics for family conversion, replay, transport, or witness lookup.

## 5. Baseline requirement

> **Status tag:** normative

Any Duotronic metric inspired by the QCD analogy must include baselines. The source-paper method compares against control channels and simulations; a Duotronic analog must compare against shuffled, malformed, long-separation, random-family, or schema-mismatch baselines.

## 6. Example Duotronic metric

> **Status tag:** reference

```yaml
RetentionMetricSpec:
  metric_id: hidden-to-observable-correlation-retention@v1
  invariant_kind: paired_witness_correlation
  extractor_id: pairwise-witness-extractor@v1
  similarity_id: separation_conditioned_correlation@v1
  transformation: transport_or_canonicalization
  baseline_suite:
    - shuffled_pairs
    - long_separation_pairs
    - unrelated_family_pairs
    - malformed_pairs
  preservation_class: should_preserve
  failure_action: observe_only
```

## 7. What not to import

> **Status tag:** normative

Duotronic documents MUST NOT say:

1. Duotronics proves virtual particles;
2. DPFC is QCD;
3. witness retention is quantum coherence;
4. retention loss is physical decoherence;
5. polygon families are particle multiplets;
6. analogy profiles are implementation authority.

## 8. Useful outcome

> **Status tag:** reference

The QCD profile is useful because it shows a disciplined way to reason from hidden correlation to final-state observable, with controls and separation-dependent loss. That helps Duotronics design better retention diagnostics, but it remains bounded as analogy/research.

## 9. Claim-class assignment

> **Status tag:** normative

All QCD-inspired statements in this profile are C5 analogy or C4 metric-design hypotheses unless a separate external-domain evidence document is created. They are not C2 proofs or C3 runtime requirements.
