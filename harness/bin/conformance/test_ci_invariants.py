"""CI invariants meta-test (Witness Contract App S §S.3).

After the rest of the suite runs, this meta-test inspects the audit
ledger for any forbidden CI-rule violations and fails the build if it
finds anything. Forbidden events:

  - failed_frame_to_trusted_memory
  - absence_zero_collision_accepted
  - replay_mismatch_unmarked        (only forbidden when no test marked
                                     it as `expected_mismatch=True`)
  - retention_no_baseline           (allowed only if a test deliberately
                                     unfroze the baseline)

This test re-runs the dispatch surface with a representative end-to-end
scenario so the ledger is meaningful for both the reference impl and any
external impl.
"""

from __future__ import annotations

from typing import Any

import pytest

from duotronic_ref import audit


@pytest.mark.normative
def test_no_forbidden_ledger_events_after_clean_e2e(run_operation: Any) -> None:
    audit.LEDGER.clear()
    # Drive a full clean ingress → canonicalize → record sample.
    transport = run_operation(
        "dbp_ingress",
        {
            "frame": {
                "shape_valid": True,
                "profile_id": "dbp-minsafe@v1",
                "integrity_check": "passed",
                "payload_kind": "witness8",
            }
        },
    )
    assert transport["semantic_decode_allowed"] is True

    canonical = run_operation(
        "canonicalize_witness_key_bundle",
        {
            "bundle": {
                "family_id": "hex6",
                "family_schema_version": "dpfc-family@v5.6",
                "digits": ["h1", "h4"],
            }
        },
    )
    assert canonical["lookup_allowed"] is True

    sample = run_operation(
        "record_retention_sample",
        {"metric_id": "shuffled_lookup_retention", "value": 1.0, "policy_mode": "normal"},
    )
    assert sample["accepted"] is True

    forbidden_kinds = (
        audit.EVT_FAILED_FRAME_TO_TRUSTED_MEMORY,
        audit.EVT_ABSENCE_ZERO_COLLISION_ACCEPTED,
        audit.EVT_REPLAY_MISMATCH_UNMARKED,
        audit.EVT_RETENTION_NO_BASELINE,
    )
    for kind in forbidden_kinds:
        events = audit.LEDGER.events(kind)
        assert not events, (
            f"CI invariant violated: forbidden audit event {kind!r}: {events}"
        )


@pytest.mark.normative
def test_absence_zero_separation_helper_emits_audit_when_violated(run_operation: Any) -> None:
    """Direct unit-style check that the assertion helper records the audit
    event AND raises when an impl tries to collapse absence onto numeric
    zero. This is the load-bearing safety net for the negative-injection
    test described in the build plan."""
    from duotronic_ref import witness8

    audit.LEDGER.clear()
    fake_decoded = {
        "decode_status": "token_free_absent",
        "numeric_zero_inferred": True,
    }
    with pytest.raises(AssertionError):
        witness8.assert_absence_zero_separation(fake_decoded)
    assert audit.LEDGER.events(audit.EVT_ABSENCE_ZERO_COLLISION_ACCEPTED), (
        "negative-injection canary must surface an audit event"
    )


@pytest.mark.normative
@pytest.mark.migration
def test_every_non_baseline_normalizer_version_has_migration_plan(run_operation: Any) -> None:
    """CI invariant (Migration Guide §3): an identity-affecting component
    that ships a version > v1 must have a corresponding migration plan
    registered. Without it, a normalizer @v2 in the registry is a build
    failure — this is the load-bearing safety net for negative-injection
    test #2."""
    from duotronic_ref.registries.normalizer import NORMALIZER_REGISTRY

    offenders: list[str] = []
    for entry in NORMALIZER_REGISTRY.all():
        if entry.version == "v1":
            continue
        # find prior version (vN-1) — by string compare on the suffix int
        try:
            n = int(entry.version.lstrip("v"))
        except ValueError:
            offenders.append(f"{entry.normalizer_id}@{entry.version}: unparseable version")
            continue
        from_version = f"{entry.normalizer_id}@v{n - 1}"
        to_version = f"{entry.normalizer_id}@v{n}"
        out = run_operation(
            "migration_resolve_plan",
            {
                "component": "normalizer",
                "from_version": from_version,
                "to_version": to_version,
            },
        )
        if not out.get("resolved"):
            offenders.append(f"{from_version} -> {to_version}: {out.get('failure_code')}")
    assert not offenders, (
        "normalizer versions registered without migration plans: " + "; ".join(offenders)
    )
