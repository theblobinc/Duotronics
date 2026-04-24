# Acoustics, Fourier Analysis, and Spectral Witnesses as a Bounded Duotronic Research Profile v1.0

**Status:** Research profile paper  
**Version:** research-acoustics@v1.0  
**Document kind:** Research/reference paper, not normative core  
**Primary purpose:** Explore how waveform analysis, spectra, partials, missing fundamentals, roughness, masking, and timbre-scale theory can inform witness extraction and retention diagnostics without overclaiming truth.

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


## 1. Research boundary

> **Status tag:** research

This profile treats acoustics as a source of witness-design analogies and optional signal profiles. It does not claim that Fourier spectra are canonical Duotronic witnesses by default. Spectral evidence requires provenance, validation, canonicalization, confidence, and policy gating.

## 2. Central import

> **Status tag:** reference

The useful chain is:

```text
waveform -> spectrum -> partials -> inferred structure -> witness signature -> canonicalization candidate
```

This maps well to the Witness Contract because raw signal evidence is not trusted merely because it is observed.

## 3. Spectral witness signature

> **Status tag:** reference

```yaml
SpectralWitnessSignature:
  schema_version: spectral-witness@v1
  observed_waveform_hash: string
  sample_rate_hz: number
  analysis_window:
    window_size_samples: integer
    hop_size_samples: integer
    window_function: string
  spectrum_profile:
    partials:
      - frequency_hz: number
        amplitude: number
        phase: number | null
        confidence: number
    inharmonicity_score: number | null
    roughness_score: number | null
    masking_score: number | null
  inferred_pitch:
    pitch_hz: number | null
    inference_type: observed_fundamental | missing_fundamental | ambiguous | none
  trust:
    canonicalization_status: raw | canonicalized | rejected
    provenance: string
```

## 4. Fourier provenance rule

> **Status tag:** normative

A Fourier-derived witness must record sample rate, window function, window size, hop size, normalization policy, leakage handling, source hash, and confidence policy. Without provenance, it may remain audit data but must not enter authoritative memory.

## 5. Missing fundamental as derived witness

> **Status tag:** research

A listener or algorithm may infer a fundamental that is not directly present. In witness terms, this is a derived witness, not an observed witness.

```yaml
MissingFundamentalDerivedWitness:
  observed_components_hz: [200, 300, 400, 500]
  inferred_fundamental_hz: 100
  inference_type: missing_fundamental
  trust_status: conditional
  rule: inferred_witness_must_not_be_stored_as_observed_witness
```

## 6. Roughness and partial alignment

> **Status tag:** research

Roughness metrics can inspire retention diagnostics. They show how local interactions among components can produce a stability score. This is useful only if baselines and failure actions are declared.

## 7. Retention metric candidate

> **Status tag:** reference

```yaml
RetentionMetricSpec:
  metric_id: roughness-weighted-partial-alignment@v1
  invariant_kind: partial_alignment
  extractor_id: spectral-partial-extractor@v1
  similarity_id: roughness_weighted_alignment@v1
  transformation: spectral_canonicalization
  baseline_suite:
    - shuffled_partials
    - detuned_partials
    - masked_signal
    - window_leakage_control
  preservation_class: should_preserve
  failure_action: degrade_confidence
```

## 8. Masking boundary

> **Status tag:** research

A spectral component may be physically present but masked by a stronger nearby component. A masked witness must not receive the same confidence as an unmasked witness.

## 9. Signal-to-witness pipeline

> **Status tag:** reference

```text
raw waveform
-> provenance check
-> windowed spectral analysis
-> partial extraction
-> masking/roughness diagnostics
-> inferred structure
-> witness signature
-> canonicalization candidate
-> policy gate
```

## 10. Non-claims

> **Status tag:** normative

This profile does not claim:

1. spectral consonance is semantic truth;
2. Fourier components are canonical witnesses by default;
3. missing fundamentals are observed facts;
4. roughness scores prove correctness;
5. music theory proves Duotronics.

## 11. Useful outcome

> **Status tag:** reference

The acoustics profile gives Duotronics a high-value example of raw evidence becoming structured evidence only through explicit extraction, provenance, inference, and trust boundaries.
