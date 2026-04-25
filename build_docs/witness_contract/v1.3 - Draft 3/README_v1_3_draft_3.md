# Duotronic v1.3 Draft 3 Corpus

This bundle is a complete updated corpus based on `v1.3 - Draft 2`.

Draft 2 had a good structure: two root-level main specs and a `refs/` folder for companion source specs and bounded research profiles. Draft 3 keeps that structure and adds the new GCD-jump recurrence material without retheming every companion file.

## Main changed documents

1. `duotronic_witness_contract_v10_10.md` adds GCD-jump sparse witness gates as an optional L2/L2M runtime/research section.
2. `duotronic_polygon_family_calculus_v5_10.md` adds a short DPFC boundary for GCD-jump recurrence adapters and keeps the DW-SSM boundary concise.
3. `refs/duotronic_source_architecture_overview_v1_5.md` updates the corpus map and explains where the GCD-jump profile belongs.
4. `refs/duotronic_lab_integrated_source_corpus_index_v1_4.md` lists the updated corpus.
5. `refs/duotronic_research_profile_gcd_jump_recurrences_v1_0.md` is the new standalone research profile.

## Unchanged companion documents

The companion implementation specs remain at their prior baseline versions unless they have an independent semantic change:

- schema registry v1.2
- family registry v1.2
- normalizer profiles v1.2
- transport profiles v1.2
- retention diagnostics v1.2
- policy shield guide v1.2
- migration guide v1.2
- QCD/acoustics/EDO bounded research profiles v1.2
- selective witness state-space profile v1.0
- lab evidence registry v1.0
- meta runtime contract v0.2

## New recurrence boundary

The GCD-jump profile contributes a sparse witness-gate pattern:

```text
cheap recurrence step -> candidate jump event -> validation -> canonicalization -> policy gate -> optional runtime update
```

It does not redefine DPFC arithmetic and should not be advertised as a faster general prime generator without benchmarks against ordinary prime-generation baselines.
