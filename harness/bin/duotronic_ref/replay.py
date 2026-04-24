"""Replay-identity record (Migration Guide §4 + Witness Contract App P).

Pin every version that affects identity, plus input hash and expected
normal-form hash. Mismatch on any pinned dimension produces an explicit
`replay_mismatch` event that an external comparator can detect.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from typing import Any, Mapping

import cbor2

from harness_lib.schema_versions import ACTIVE_FLOATING_POINT_PROFILE, resolve_schema_snapshot

from . import audit


REPLAY_VERSION_FIELDS = (
    "input_hash",
    "transport_profile_version",
    "schema_versions",
    "family_registry_version",
    "geometry_registry_version",
    "normalizer_versions",
    "serializer_versions",
    "policy_shield_version",
    "retention_metric_versions",
    "floating_point_profile",
    "deterministic_seed",
)


def canonical_cbor(obj: Any) -> bytes:
    """Canonical CBOR: sort dict keys, no float NaN, deterministic order."""
    return cbor2.dumps(_normalise(obj), canonical=True)


def _normalise(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _normalise(obj[k]) for k in sorted(obj, key=str)}
    if isinstance(obj, (list, tuple)):
        return [_normalise(item) for item in obj]
    return obj


def blake2b_hex(payload: bytes) -> str:
    return hashlib.blake2b(payload, digest_size=32).hexdigest()


def normal_form_hash(obj: Any) -> str:
    return blake2b_hex(canonical_cbor(obj))


def input_hash(obj: Any) -> str:
    return blake2b_hex(canonical_cbor(obj))


def _active_transport_profile_version() -> str:
    return "dbp-minsafe@v1"


def _active_family_registry_version() -> str:
    return resolve_schema_snapshot()["family_registry_version"]


def _active_geometry_registry_version() -> str:
    return resolve_schema_snapshot()["geometry_registry_version"]


def _active_policy_shield_version() -> str:
    return resolve_schema_snapshot()["policy_shield_version"]


@dataclass
class ReplayIdentity:
    input_hash: str
    expected_normal_form_hash: str
    transport_profile_version: str = field(default_factory=_active_transport_profile_version)
    schema_versions: dict[str, str] = field(default_factory=dict)
    family_registry_version: str = field(default_factory=_active_family_registry_version)
    geometry_registry_version: str = field(default_factory=_active_geometry_registry_version)
    normalizer_versions: dict[str, str] = field(default_factory=dict)
    serializer_versions: dict[str, str] = field(default_factory=dict)
    policy_shield_version: str = field(default_factory=_active_policy_shield_version)
    retention_metric_versions: dict[str, str] = field(default_factory=dict)
    floating_point_profile: str = ACTIVE_FLOATING_POINT_PROFILE
    deterministic_seed: int | None = 0

    def to_canonical(self) -> bytes:
        return canonical_cbor(asdict(self))

    def hash(self) -> str:
        return blake2b_hex(self.to_canonical())


def compare_replay(
    expected: ReplayIdentity,
    observed: Mapping[str, Any],
    *,
    expected_mismatch: bool = False,
) -> dict[str, Any]:
    """Return a structured replay diff. Mismatches against any pinned field
    surface as `replay_mismatch`; an unmarked mismatch (`expected_mismatch`
    False) is also recorded into the audit ledger so the CI invariants meta-
    test can detect smuggled-in regressions."""
    ours = asdict(expected)
    diffs: dict[str, Any] = {}
    for field_name in REPLAY_VERSION_FIELDS + ("expected_normal_form_hash",):
        ev = ours.get(field_name)
        ov = observed.get(field_name)
        if ev != ov:
            diffs[field_name] = {"expected": ev, "observed": ov}
    if not diffs:
        return {"replay_match": True, "diffs": {}}
    result = {
        "replay_match": False,
        "replay_mismatch": True,
        "diffs": diffs,
        "expected_mismatch": expected_mismatch,
    }
    if expected_mismatch:
        audit.record(audit.EVT_REPLAY_MISMATCH_EXPECTED, diffs=diffs)
    else:
        audit.record(audit.EVT_REPLAY_MISMATCH_UNMARKED, diffs=diffs)
    return result


def run_reference_self_test() -> None:
    h = normal_form_hash({"family_id": "hex6", "digits": ["h1", "h4"]})
    assert isinstance(h, str) and len(h) == 64
    same = normal_form_hash({"digits": ["h1", "h4"], "family_id": "hex6"})
    assert h == same, "canonical hash must be order-independent"
    diff = normal_form_hash({"family_id": "hex6", "digits": ["h1", "h5"]})
    assert h != diff


if __name__ == "__main__":  # pragma: no cover
    run_reference_self_test()
    print("Replay reference self-test passed")
