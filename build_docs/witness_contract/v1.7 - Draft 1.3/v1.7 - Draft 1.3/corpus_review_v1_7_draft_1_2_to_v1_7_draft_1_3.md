# Corpus Review: v1.7 Draft 1.2 to v1.7 Draft 1.3

Status: implementation-review candidate, not freeze-ready.

## What Draft 1.2 missed

Draft 1.2 promoted Bayesian and knot-theory witnesses into first-class schema/API/formal surfaces, but schema-required fields drifted behind SQL persistence, active registries still looked Draft 1.2-only, positive fixture coverage was thin, and some validator checks proved malformed SQL paths rather than the intended semantic guards.

## What Draft 1.3 closes

Draft 1.3 aligns schema, SQL, runtime boundary, OpenAPI, fixtures, and validator checks for the first-class Bayesian/knot layer. The redone Draft 1.3 additionally closes the remaining coverage issues by adding active Draft 1.3 registry aliases, positive fixtures for every promoted Bayesian model family, knot encoding family, knot invariant family, and calibration scoring rule, semantic rejection for duplicate Bayesian hypothesis identifiers, and deeper typed knot-encoding semantic validators.

## Deliberately open

The SQL layer is persistence-only for higher-order semantics; semantic acceptance is enforced by validator/kernel conformance before persistence. Lean and TLA remain integration-level formal surfaces unless strict Lake and strict TLC are run in the target environment. Deep mathematical proofs of Jones/Alexander correctness, Reidemeister invariance, Markov equivalence, posterior predictive correctness, and decision-theoretic optimality remain out of scope for this Draft 1.3 review layer.

## Why Draft 1.3 is not frozen

Strict Lake and strict TLC remain freeze blockers. Runtime implementation conformance and human authority review must still be performed. Draft 1.3 is suitable for implementation review and semantic validator hardening, but not final release/freeze.
