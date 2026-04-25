# Corpus Review: v1.3 Draft 2 to Draft 3

## Structure review

Draft 2 is structurally sound. The root contains the two main specifications:

1. DPFC;
2. Witness Contract.

The `refs/` folder contains companion source specs, bounded research profiles, the corpus index, and the release manifest. That is the right shape because it prevents every research profile from becoming part of the normative core.

## What needed improvement

The next documentation topic, GCD-jump recurrences, should not be added across every companion file. It is a narrow runtime/research profile. It belongs in:

1. the Witness Contract, because it affects L2/L2M recurrence and sparse witness gates;
2. DPFC only as a boundary note, because it uses external GCD arithmetic and must not redefine DPFC;
3. the Source Architecture Overview, because the overview maps the corpus;
4. the corpus index;
5. a standalone research profile.

## Draft 3 decision

Draft 3 adds a new profile, `duotronic_research_profile_gcd_jump_recurrences_v1_0.md`, and updates only the owning documents. Companion specs remain unchanged.

## Safety boundary

A GCD jump is a candidate event, not authority. It must still pass validation, canonicalization, and policy gating before it can affect authoritative recurrent state, lookup memory, or persistent storage.
