"""DPFC v5.8 reference implementation.

Ported faithfully from Appendix H of `duotronic_polygon_family_calculus_v5_6.md`,
extended with the §28 reference algorithms and the µ_n core type, Φ_F / Φ_F^{-1}
bridges. This module is the SUT used by default; external implementations can
replace it via the `DUOTRONIC_IMPL` env var.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class Family:
    family_id: str
    schema_version: str
    alphabet: tuple[str, ...]
    kind: str = "polygon"
    status: str = "experimental"
    geometry_id: str | None = None
    normalizer_id: str | None = None
    external_zero_bridge: str | None = None

    @property
    def modulus(self) -> int:
        return len(self.alphabet)

    def ordinal(self, digit: str) -> int:
        try:
            return self.alphabet.index(digit) + 1
        except ValueError as exc:  # pragma: no cover - exercised through tests
            raise ValueError(
                f"unknown digit {digit!r} for family {self.family_id}"
            ) from exc

    def digit(self, ordinal: int) -> str:
        if ordinal < 1 or ordinal > self.modulus:
            raise ValueError(f"ordinal {ordinal} outside 1..{self.modulus}")
        return self.alphabet[ordinal - 1]


# Baseline registered families (Family Registry §5)
HEX6 = Family(
    family_id="hex6",
    schema_version="dpfc-family@v5.8",
    alphabet=("h1", "h2", "h3", "h4", "h5", "h6"),
    kind="polygon",
    status="normative_reference",
    geometry_id="regular-hexagon@v1",
    normalizer_id="simple-bijective-word-normalizer@v1",
)
REFL3 = Family(
    family_id="refl3",
    schema_version="dpfc-family@v5.8",
    alphabet=("r1", "r2", "r3"),
    kind="reflection",
    status="research_valid",
    geometry_id="reflection-triangle@v1",
    normalizer_id="reflection-path-normalizer@v1",
)
EDO31 = Family(
    family_id="edo31",
    schema_version="dpfc-family@v5.8",
    alphabet=tuple(f"e{i}" for i in range(1, 32)),
    kind="edo",
    status="research_valid",
    geometry_id="circle-of-diesis@v1",
    normalizer_id="simple-bijective-word-normalizer@v1",
    external_zero_bridge="external_step_k_maps_to_e_k_plus_1",
)


@dataclass(frozen=True)
class Mu:
    """Native one-based core magnitude index (DPFC §5.1).

    `mu_n` is the abstract structural position; it is never numeric zero.
    """

    n: int

    def __post_init__(self) -> None:
        if self.n < 1:
            raise ValueError("core magnitude index must be at least 1 (mu_1, mu_2, ...)")

    def __repr__(self) -> str:  # pragma: no cover
        return f"mu_{self.n}"

    @property
    def label(self) -> str:
        return f"mu_{self.n}"


def parse_mu(value: Any) -> Mu:
    if isinstance(value, Mu):
        return value
    if isinstance(value, int):
        return Mu(value)
    if isinstance(value, str):
        if value.startswith("mu_"):
            return Mu(int(value[3:]))
    raise ValueError(f"unrecognised core magnitude {value!r}")


def evaluate_family_word(word: list[str], family: Family) -> int:
    """DPFC §28.2 — bijective positional evaluation."""
    if not word:
        raise ValueError("native family numerals must be nonempty")
    value = 0
    for digit in word:
        value = value * family.modulus + family.ordinal(digit)
    return value


def Phi_F(word: list[str], family: Family) -> Mu:
    """Family-to-core bridge Φ_F: native word → core magnitude µ_n."""
    return Mu(evaluate_family_word(word, family))


def encode_core_to_family(n: int, family: Family) -> list[str]:
    """DPFC §28.1 — inverse encoding (bijective base-b)."""
    if n < 1:
        raise ValueError("core magnitude index must be at least one")
    q = n
    out: list[str] = []
    while q > 0:
        r = ((q - 1) % family.modulus) + 1
        out.insert(0, family.digit(r))
        q = (q - r) // family.modulus
    return out


def Phi_F_inverse(mu: Mu, family: Family) -> list[str]:
    return encode_core_to_family(mu.n, family)


def inverse_encode(n: int, family: Family) -> list[str]:
    return encode_core_to_family(n, family)


def family_successor(word: list[str], family: Family) -> list[str]:
    """DPFC §10.1 — bijective carry successor."""
    if not word:
        raise ValueError("native family numerals must be nonempty")
    out = list(word)
    pos = len(out) - 1
    while pos >= 0:
        ordinal = family.ordinal(out[pos])
        if ordinal < family.modulus:
            out[pos] = family.digit(ordinal + 1)
            return out
        out[pos] = family.digit(1)
        pos -= 1
    return [family.digit(1)] + out


def core_successor(mu: Mu) -> Mu:
    return Mu(mu.n + 1)


def core_realized_step_add(left: Mu, right: Mu) -> Mu:
    """DPFC §5.3 — n_a ⊕_µ n_b = n_a + n_b (positive index addition)."""
    return Mu(left.n + right.n)


def core_realized_step_mul(left: Mu, right: Mu) -> Mu:
    """DPFC §5.4 — n_a ⊗_µ n_b = n_a · n_b (positive index multiplication)."""
    return Mu(left.n * right.n)


def nonneg_export(mu: Mu) -> int:
    """DPFC §5.6 — E_U(µ_n) = n - 1 (nonneg export image)."""
    return mu.n - 1


def exported_nonnegative_add_with_correction(left: int, right: int) -> int:
    """DPFC §5.7 — E_U(µ_a ⊕_µ µ_b) = E_U(µ_a) + E_U(µ_b) + 1."""
    return nonneg_export(Mu(left)) + nonneg_export(Mu(right)) + 1


def exported_nonnegative_add_without_correction(left: int, right: int) -> int:
    """The deliberately wrong addition that must be flagged as policy mismatch."""
    return nonneg_export(Mu(left)) + nonneg_export(Mu(right))


def canonical_storage(word: list[str], family: Family) -> str:
    ordinals = " ".join(str(family.ordinal(digit)) for digit in word)
    return f"family:{family.family_id} schema_version:{family.schema_version} digits:{ordinals}"


def canonicalize_family_object(word: list[str], family: Family) -> dict[str, Any]:
    mu = Phi_F(word, family)
    return {
        "family_id": family.family_id,
        "schema_version": family.schema_version,
        "digit_ordinals": [family.ordinal(d) for d in word],
        "core_magnitude": mu.label,
        "canonical_storage": canonical_storage(word, family),
    }


def convert_family(
    word: list[str], source: Family, target: Family
) -> dict[str, Any]:
    """DPFC §11 — inter-family conversion preserving core magnitude."""
    mu = Phi_F(word, source)
    target_word = Phi_F_inverse(mu, target)
    target_mu = Phi_F(target_word, target)
    return {
        "source_core_magnitude": mu.label,
        "target_word": target_word,
        "target_core_magnitude": target_mu.label,
        "must_preserve": ["core_magnitude"],
        "expected_loss": [
            "source_family_identity_unless_metadata_channel_enabled"
        ],
    }


def detect_export_policy_mismatch(
    left_mu: Mu,
    right_mu: Mu,
    declared_left_export: int,
    declared_right_export: int,
) -> dict[str, Any]:
    """DPFC §5.7 — Detect when nonneg export arithmetic is applied without
    affine correction (App F failure case)."""
    expected_left = nonneg_export(left_mu)
    expected_right = nonneg_export(right_mu)
    if (
        declared_left_export != expected_left
        or declared_right_export != expected_right
    ):
        return {
            "failure_code": "export_label_mismatch",
            "trusted_arithmetic_use": False,
        }
    incorrect = declared_left_export + declared_right_export
    correct = exported_nonnegative_add_with_correction(left_mu.n, right_mu.n)
    return {
        "incorrect_downstream_result": incorrect,
        "correct_exported_result": correct,
        "required_correction": correct - incorrect,
        "failure_code": "export_policy_mismatch",
        "trusted_arithmetic_use": False,
    }


def run_reference_self_test() -> None:
    assert evaluate_family_word(["h1", "h4"], HEX6) == 10
    assert family_successor(["h1", "h4"], HEX6) == ["h1", "h5"]
    assert family_successor(["h6"], HEX6) == ["h1", "h1"]
    assert family_successor(["h1", "h6"], HEX6) == ["h2", "h1"]
    assert encode_core_to_family(10, REFL3) == ["r3", "r1"]
    assert convert_family(["h1", "h4"], HEX6, REFL3)["target_word"] == ["r3", "r1"]
    assert exported_nonnegative_add_with_correction(2, 3) == 4
    assert nonneg_export(Mu(1)) == 0
    assert Phi_F_inverse(Phi_F(["h1", "h4"], HEX6), HEX6) == ["h1", "h4"]


if __name__ == "__main__":  # pragma: no cover
    run_reference_self_test()
    print("DPFC v5.8 reference self-test passed")
