"""Reference-impl operation dispatch.

`run_operation(op_name, given) -> dict` is the contract surface that the
harness loader uses to drive every fixture row. External implementations
plug in by exposing a module that defines the same callable; the harness
selects the impl via `--impl <module>` or the `DUOTRONIC_IMPL` env var.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from . import (
    audit,
    canonicalizer,
    dbp,
    dpfc,
    normalizer,
    policy_shield,
    replay,
    retention,
    spectral,
    witness8,
    wsb2,
)
from .registries import (
    FAMILY_REGISTRY,
    GEOMETRY_REGISTRY,
    MIGRATION_REGISTRY,
    NORMALIZER_REGISTRY,
    POLICY_REGISTRY,
    RETENTION_REGISTRY,
    SCHEMA_REGISTRY,
    TRANSPORT_REGISTRY,
)


__all__ = ["run_operation", "OPERATIONS", "register_operation"]


def _family(family_id: str) -> dpfc.Family:
    fam = normalizer.get_family(family_id)
    if fam is None:
        raise KeyError(f"unknown family {family_id}")
    return fam


# ---------------------------------------------------------------------------
# DPFC operations
# ---------------------------------------------------------------------------

def _op_evaluate_family_word(given: Mapping[str, Any]) -> dict[str, Any]:
    family = _family(given["family_id"])
    value = dpfc.evaluate_family_word(list(given["word"]), family)
    return {"value": value, "core_magnitude": f"mu_{value}"}


def _op_family_successor(given: Mapping[str, Any]) -> dict[str, Any]:
    family = _family(given["family_id"])
    return {"successor": dpfc.family_successor(list(given["word"]), family)}


def _op_encode_core_to_family(given: Mapping[str, Any]) -> dict[str, Any]:
    family = _family(given["family_id"])
    word = dpfc.encode_core_to_family(int(given["core_index"]), family)
    return {"word": word}


def _op_family_conversion(given: Mapping[str, Any]) -> dict[str, Any]:
    src = _family(given["source_family"])
    tgt = _family(given["target_family"])
    return dpfc.convert_family(list(given["word"]), src, tgt)


def _op_canonicalize_family_object(given: Mapping[str, Any]) -> dict[str, Any]:
    family = _family(given["family_id"])
    return dpfc.canonicalize_family_object(list(given["word"]), family)


def _op_canonical_storage(given: Mapping[str, Any]) -> dict[str, Any]:
    family = _family(given["family_id"])
    return {"canonical_storage": dpfc.canonical_storage(list(given["word"]), family)}


def _op_exported_nonneg_add_with_correction(given: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "value": dpfc.exported_nonnegative_add_with_correction(
            int(given["left"]), int(given["right"])
        )
    }


def _op_exported_nonneg_add_without_correction(given: Mapping[str, Any]) -> dict[str, Any]:
    """Reference impl returns the deliberately-wrong value AND emits a
    policy-mismatch flag so the suite can verify external impls expose
    the same affine-correction failure mode."""
    wrong = dpfc.exported_nonnegative_add_without_correction(
        int(given["left"]), int(given["right"])
    )
    correct = dpfc.exported_nonnegative_add_with_correction(
        int(given["left"]), int(given["right"])
    )
    return {
        "value": wrong,
        "expected_correct_value": correct,
        "required_correction": correct - wrong,
        "failure_code": "export_policy_mismatch",
        "trusted_arithmetic_use": False,
    }


def _op_detect_export_policy_mismatch(given: Mapping[str, Any]) -> dict[str, Any]:
    return dpfc.detect_export_policy_mismatch(
        dpfc.Mu(int(given["left_core"])),
        dpfc.Mu(int(given["right_core"])),
        int(given["declared_left_export"]),
        int(given["declared_right_export"]),
    )


# ---------------------------------------------------------------------------
# Witness8 / WSB2 / DBP
# ---------------------------------------------------------------------------

def _op_decode_witness8(given: Mapping[str, Any]) -> dict[str, Any]:
    return witness8.decode_witness8(
        given["row"],
        profile_id=given.get("profile_id", "witness8-minsafe@v1"),
        profile_declares_numeric_zero=bool(
            given.get("profile_declares_numeric_zero", False)
        ),
    )


def _op_decode_wsb2(given: Mapping[str, Any]) -> dict[str, Any]:
    return wsb2.decode_wsb2_rows(
        given["payload"],
        profile_declares_numeric_zero=bool(
            given.get("profile_declares_numeric_zero", False)
        ),
    )


def _op_dbp_ingress(given: Mapping[str, Any]) -> dict[str, Any]:
    return dbp.validate_dbp_frame(given["frame"])


def _op_ingress_frame(given: Mapping[str, Any]) -> dict[str, Any]:
    """Composite end-to-end ingress: DBP → (WSB2 | Witness8) → canonicalize."""
    frame = given["frame"]
    transport = dbp.validate_dbp_frame(frame)
    if not transport.get("semantic_decode_allowed"):
        return {"transport": transport, "decoded": None, "canonical": None}
    profile_id = transport.get("profile_id")
    profile = TRANSPORT_REGISTRY.resolve(*profile_id.split("@"))
    payload_kind = frame.get("payload_kind")
    payload = frame.get("payload", {})
    if payload_kind == "wsb2":
        decoded = wsb2.decode_wsb2_rows(
            payload, profile_declares_numeric_zero=profile.declares_numeric_zero
        )
    elif payload_kind == "witness8":
        decoded = witness8.decode_witness8(
            payload.get("row"),
            profile_id=profile_id,
            profile_declares_numeric_zero=profile.declares_numeric_zero,
        )
    else:
        decoded = {"failure_code": "unknown_payload_kind"}
    canonical: dict[str, Any] | None = None
    bundle = frame.get("witness_key_bundle")
    if bundle is not None:
        canonical = canonicalizer.canonicalize_witness_key_bundle(bundle)
    return {"transport": transport, "decoded": decoded, "canonical": canonical}


def _op_canonicalize_witness_key_bundle(given: Mapping[str, Any]) -> dict[str, Any]:
    return canonicalizer.canonicalize_witness_key_bundle(given["bundle"])


# ---------------------------------------------------------------------------
# Normalizer
# ---------------------------------------------------------------------------

def _op_normalize_family_word(given: Mapping[str, Any]) -> dict[str, Any]:
    return normalizer.normalize_family_word(given)


def _op_normalize_reflection_path(given: Mapping[str, Any]) -> dict[str, Any]:
    return normalizer.normalize_reflection_path(given)


def _op_normalize_witness8_row(given: Mapping[str, Any]) -> dict[str, Any]:
    return normalizer.normalize_witness8_row(given)


# ---------------------------------------------------------------------------
# Spectral / EDO
# ---------------------------------------------------------------------------

def _op_infer_missing_fundamental(given: Mapping[str, Any]) -> dict[str, Any]:
    return spectral.infer_missing_fundamental(list(given["components_hz"]))


def _op_transpose_retention(given: Mapping[str, Any]) -> dict[str, Any]:
    return spectral.transpose_retention(
        list(given["values"]),
        int(given["transposition"]),
        int(given["modulus"]),
    )


def _op_collapse_to_12edo(given: Mapping[str, Any]) -> dict[str, Any]:
    return spectral.enharmonic_collapse_policy(
        given.get("source_family", "edo31"),
        given.get("target_family", "edo12"),
        int(given["left_step"]),
        int(given["right_step"]),
    )


def _op_validate_fourier_provenance(given: Mapping[str, Any]) -> dict[str, Any]:
    return spectral.validate_fourier_provenance(given["witness"])


def _op_temperament_error_witness(given: Mapping[str, Any]) -> dict[str, Any]:
    return spectral.temperament_error_witness(given["ratio"], given["target_family"])


def _op_approximate_ratio_in_edo(given: Mapping[str, Any]) -> dict[str, Any]:
    return spectral.approximate_ratio_in_edo(given["ratio"], int(given["steps"]))


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

def _op_resolve_schema(given: Mapping[str, Any]) -> dict[str, Any]:
    entry = SCHEMA_REGISTRY.resolve(given["schema_id"], given["version"])
    return {
        "schema_id": entry.schema_id,
        "version": entry.version,
        "owner": entry.owner,
        "status": entry.status,
    }


def _op_resolve_family(given: Mapping[str, Any]) -> dict[str, Any]:
    e = FAMILY_REGISTRY.resolve(given["family_id"])
    return {
        "family_id": e.family_id,
        "base": e.base,
        "digit_alphabet": list(e.digit_alphabet),
        "is_bijective_base": e.is_bijective_base,
    }


def _op_resolve_geometry(given: Mapping[str, Any]) -> dict[str, Any]:
    e = GEOMETRY_REGISTRY.resolve(given["geometry_id"])
    return {
        "geometry_id": e.geometry_id,
        "family_id": e.family_id,
        "n_sides": e.n_sides,
        "chirality": e.chirality,
    }


def _op_resolve_transport(given: Mapping[str, Any]) -> dict[str, Any]:
    e = TRANSPORT_REGISTRY.resolve(given["profile_id"], given.get("version", "v1"))
    return {
        "profile_id": e.profile_id,
        "version": e.version,
        "declares_numeric_zero": e.declares_numeric_zero,
        "requires_replay_key": e.requires_replay_key,
    }


def _op_resolve_normalizer(given: Mapping[str, Any]) -> dict[str, Any]:
    e = NORMALIZER_REGISTRY.resolve(given["normalizer_id"], given["version"])
    return {
        "normalizer_id": e.normalizer_id,
        "version": e.version,
        "target_family": e.target_family,
        "has_migration_plan": e.has_migration_plan,
    }


def _op_resolve_retention(given: Mapping[str, Any]) -> dict[str, Any]:
    e = RETENTION_REGISTRY.resolve(given["metric_id"])
    return {
        "metric_id": e.metric_id,
        "version": e.version,
        "baseline_required": e.baseline_required,
        "frozen_on_bypass": e.frozen_on_bypass,
    }


def _op_resolve_policy(given: Mapping[str, Any]) -> dict[str, Any]:
    e = POLICY_REGISTRY.resolve(given["event"])
    return {
        "event": e.event,
        "mode": e.mode,
        "freeze_metrics": e.freeze_metrics,
        "trust_status": e.trust_status,
        "escalation_chain": list(e.escalation_chain),
    }


# ---------------------------------------------------------------------------
# Retention
# ---------------------------------------------------------------------------

def _op_freeze_retention_baseline(given: Mapping[str, Any]) -> dict[str, Any]:
    retention.LEDGER.freeze_baseline(
        given["metric_id"],
        value=float(given["value"]),
        sample_count=int(given["sample_count"]),
        profile=given.get("profile", "reference-default"),
    )
    return {"frozen": True, "metric_id": given["metric_id"]}


def _op_record_retention_sample(given: Mapping[str, Any]) -> dict[str, Any]:
    return retention.LEDGER.record_sample(
        metric_id=given["metric_id"],
        value=float(given["value"]),
        policy_mode=given.get("policy_mode", "normal"),
    )


def _op_seed_retention_default_baselines(given: Mapping[str, Any]) -> dict[str, Any]:
    retention.seed_default_baselines()
    return {"seeded": True}


# ---------------------------------------------------------------------------
# Policy / Migration / Replay
# ---------------------------------------------------------------------------

def _op_policy_decide(given: Mapping[str, Any]) -> dict[str, Any]:
    return policy_shield.SHIELD.decide(
        event=given["event"], context=given.get("context", {})
    )


def _op_reset_policy_shield(given: Mapping[str, Any]) -> dict[str, Any]:
    policy_shield.reset_shield()
    return {"reset": True}


def _op_migration_resolve_plan(given: Mapping[str, Any]) -> dict[str, Any]:
    try:
        plan = MIGRATION_REGISTRY.resolve(
            component=given["component"],
            from_version=given["from_version"],
            to_version=given["to_version"],
        )
    except KeyError as exc:
        return {"resolved": False, "failure_code": "missing_migration_plan", "error": str(exc)}
    return {
        "resolved": True,
        "plan_id": plan.plan_id,
        "component": plan.component,
        "from_version": plan.from_version,
        "to_version": plan.to_version,
        "strategy": plan.strategy,
        "requires_replay_pin_update": plan.requires_replay_pin_update,
    }


def _op_register_migration_plan(given: Mapping[str, Any]) -> dict[str, Any]:
    from .registries.migration import MigrationPlan

    plan = MigrationPlan(
        plan_id=given["plan_id"],
        from_version=given["from_version"],
        to_version=given["to_version"],
        component=given["component"],
        strategy=given.get("strategy", "bijective"),
        requires_replay_pin_update=bool(given.get("requires_replay_pin_update", True)),
        notes=given.get("notes", ""),
    )
    MIGRATION_REGISTRY.register(plan)
    return {"registered": True, "plan_id": plan.plan_id}


def _op_replay_compute_normal_form_hash(given: Mapping[str, Any]) -> dict[str, Any]:
    return {"normal_form_hash": replay.normal_form_hash(given["object"])}


def _op_replay_compute_input_hash(given: Mapping[str, Any]) -> dict[str, Any]:
    return {"input_hash": replay.input_hash(given["object"])}


def _op_replay_compare(given: Mapping[str, Any]) -> dict[str, Any]:
    expected = given["expected"]
    identity = replay.ReplayIdentity(**expected)
    return replay.compare_replay(
        identity,
        given["observed"],
        expected_mismatch=bool(given.get("expected_mismatch", False)),
    )


# ---------------------------------------------------------------------------
# Family-conversion + retention report (composite)
# ---------------------------------------------------------------------------

def _op_family_conversion_with_retention_report(given: Mapping[str, Any]) -> dict[str, Any]:
    src = _family(given["source_family"])
    tgt = _family(given["target_family"])
    conversion = dpfc.convert_family(list(given["word"]), src, tgt)
    # convert back to verify core-magnitude preservation
    round_trip = dpfc.convert_family(conversion["target_word"], tgt, src)
    return {
        **conversion,
        "round_trip_word": round_trip["target_word"],
        "round_trip_core_magnitude": round_trip["target_core_magnitude"],
        "core_magnitude_preserved": (
            conversion["source_core_magnitude"]
            == conversion["target_core_magnitude"]
            == round_trip["target_core_magnitude"]
        ),
    }


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

OPERATIONS: dict[str, Callable[[Mapping[str, Any]], dict[str, Any]]] = {
    # DPFC core
    "evaluate_family_word": _op_evaluate_family_word,
    "family_successor": _op_family_successor,
    "encode_core_to_family": _op_encode_core_to_family,
    "family_conversion": _op_family_conversion,
    "canonicalize_family_object": _op_canonicalize_family_object,
    "canonical_storage": _op_canonical_storage,
    "exported_nonnegative_add_with_correction": _op_exported_nonneg_add_with_correction,
    "exported_nonnegative_add_without_correction": _op_exported_nonneg_add_without_correction,
    "detect_export_policy_mismatch": _op_detect_export_policy_mismatch,
    "family_conversion_with_retention_report": _op_family_conversion_with_retention_report,
    # Witness / WSB2 / DBP
    "decode_witness8": _op_decode_witness8,
    "decode_wsb2": _op_decode_wsb2,
    "dbp_ingress": _op_dbp_ingress,
    "ingress_dbp_frame": _op_dbp_ingress,
    "ingress_frame": _op_ingress_frame,
    "canonicalize_witness_key_bundle": _op_canonicalize_witness_key_bundle,
    # Normalizer
    "normalize_family_word": _op_normalize_family_word,
    "normalize_reflection_path": _op_normalize_reflection_path,
    "normalize_witness8_row": _op_normalize_witness8_row,
    # Spectral / EDO
    "infer_missing_fundamental": _op_infer_missing_fundamental,
    "transpose_and_measure_interval_retention": _op_transpose_retention,
    "collapse_to_12edo": _op_collapse_to_12edo,
    "validate_fourier_provenance": _op_validate_fourier_provenance,
    "temperament_error_witness": _op_temperament_error_witness,
    "approximate_ratio_in_edo": _op_approximate_ratio_in_edo,
    # Registries
    "resolve_schema": _op_resolve_schema,
    "resolve_family": _op_resolve_family,
    "resolve_geometry": _op_resolve_geometry,
    "resolve_transport": _op_resolve_transport,
    "resolve_normalizer": _op_resolve_normalizer,
    "resolve_retention": _op_resolve_retention,
    "resolve_policy": _op_resolve_policy,
    # Retention
    "freeze_retention_baseline": _op_freeze_retention_baseline,
    "record_retention_sample": _op_record_retention_sample,
    "seed_retention_default_baselines": _op_seed_retention_default_baselines,
    # Policy
    "policy_decide": _op_policy_decide,
    "reset_policy_shield": _op_reset_policy_shield,
    # Migration
    "migration_resolve_plan": _op_migration_resolve_plan,
    "register_migration_plan": _op_register_migration_plan,
    # Replay
    "replay_compute_normal_form_hash": _op_replay_compute_normal_form_hash,
    "replay_compute_input_hash": _op_replay_compute_input_hash,
    "replay_compare": _op_replay_compare,
}


def register_operation(name: str, fn: Callable[[Mapping[str, Any]], dict[str, Any]]) -> None:
    OPERATIONS[name] = fn


def run_operation(op_name: str, given: Mapping[str, Any]) -> dict[str, Any]:
    if op_name not in OPERATIONS:
        raise KeyError(f"unknown operation: {op_name}")
    return OPERATIONS[op_name](given)
