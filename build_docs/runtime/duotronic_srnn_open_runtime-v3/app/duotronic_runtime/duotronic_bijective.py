from __future__ import annotations

"""Duotronic positive-baseline / bijective helpers used by the live WG-RNN runtime.

The core bijective_encode, bijective_decode, encode_baseline and decode_baseline
semantics are adapted directly from the canonical executable reference in
Witness Contract v1.6 Draft 5.3.18:

  build_docs/witness_contract/v1.6 - Draft 5.3.18/
    executable/runtime/positive_baseline.py

Reference SHAKE256-512 at integration time:
  shake256-512:e9814f5785aa3b63921c0b5e228c0e35f171f2c62ef3bccf5f16e324dee97508cbbfeebbb8c603a25ffe9e0da94a5954b5fda6873e3a5966257e35e955432ee8

The runtime keeps ordinary storage indices where interoperability requires them,
but every ordinal/slot/candidate identity can additionally carry a strictly
positive bijective representation. Zero remains an implementation index only;
it is not used as a Duotronic numeral.
"""

from typing import Any, Iterable

REFERENCE_SHAKE256_512 = "shake256-512:0c2fdfff4e60634d0c05c7d2805b3529cefb01b8765558289454e0679739b91e2cc50dfa579900479d1859f173a5fd628217d0429a43ad09c0b5c05334ec6ca3"
REFERENCE_PROFILE = "positive-baseline-reference/1.0"
DEFAULT_ALPHABET = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "A")
DEFAULT_BASELINE = 1


class DuotronicMathError(ValueError):
    """Deterministic refusal with a stable error code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _exact_int(value: Any, label: str) -> int:
    if type(value) is not int:
        raise DuotronicMathError("domain_violation", f"{label} must be an exact integer")
    return value


def _validated_alphabet(alphabet: Iterable[str] | None = None) -> tuple[str, ...]:
    symbols = tuple(alphabet or DEFAULT_ALPHABET)
    if not symbols or len(symbols) != len(set(symbols)) or any(not isinstance(s, str) or not s for s in symbols):
        raise DuotronicMathError("alphabet_invalid", "alphabet must contain unique nonempty symbols")
    return symbols


def bijective_encode(n: int, alphabet: Iterable[str] | None = None) -> tuple[str, ...]:
    """Encode a strictly positive integer in a bijective alphabet.

    This is behavior-compatible with Draft 5.3.18 positive_baseline.py.
    """

    _exact_int(n, "n")
    if n <= 0:
        raise DuotronicMathError("domain_violation", "bijective numerals represent positive integers")
    symbols = _validated_alphabet(alphabet)
    base = len(symbols)
    result: list[str] = []
    while n:
        n, remainder = divmod(n - 1, base)
        result.append(symbols[remainder])
    return tuple(reversed(result))


def bijective_decode(symbols: Iterable[str], alphabet: Iterable[str] | None = None) -> int:
    """Decode a non-empty bijective numeral to a positive integer."""

    encoded = tuple(symbols)
    if not encoded:
        raise DuotronicMathError("domain_violation", "empty sequence is not a positive bijective numeral")
    alphabet_symbols = _validated_alphabet(alphabet)
    digits = {symbol: index + 1 for index, symbol in enumerate(alphabet_symbols)}
    value = 0
    for symbol in encoded:
        if symbol not in digits:
            raise DuotronicMathError("alphabet_invalid", f"symbol is not in alphabet: {symbol!r}")
        value = len(alphabet_symbols) * value + digits[symbol]
    return value


def encode_baseline(payload: int, baseline: int = DEFAULT_BASELINE) -> int:
    """Map an exact integer payload into a positive-baseline codeword."""

    payload_value = _exact_int(payload, "payload")
    baseline_value = _exact_int(baseline, "baseline")
    if baseline_value < 1:
        raise DuotronicMathError("domain_violation", "positive baseline must be >= 1")
    return payload_value + baseline_value


def decode_baseline(codeword: int, baseline: int = DEFAULT_BASELINE) -> int:
    """Remove a positive baseline from an exact integer codeword."""

    codeword_value = _exact_int(codeword, "codeword")
    baseline_value = _exact_int(baseline, "baseline")
    if baseline_value < 1:
        raise DuotronicMathError("domain_violation", "positive baseline must be >= 1")
    return codeword_value - baseline_value


def positive_index_payload(zero_based_index: int, *, baseline: int = DEFAULT_BASELINE) -> dict[str, Any]:
    """Represent a zero-based interoperability index in the Duotronic domain.

    The external/storage index is preserved for compatibility. Its Duotronic
    codeword is ``index + baseline`` and is therefore strictly positive.
    """

    index = _exact_int(zero_based_index, "zero_based_index")
    if index < 0:
        raise DuotronicMathError("domain_violation", "zero_based_index must be >= 0")
    codeword = encode_baseline(index, baseline)
    return {
        "storage_index": index,
        "baseline": baseline,
        "codeword": codeword,
        "bijective": "".join(bijective_encode(codeword)),
        "alphabet": list(DEFAULT_ALPHABET),
        "profile": "positive-baseline-1",
        "reference_shake256_512": REFERENCE_SHAKE256_512,
    }


def positive_ordinal_payload(ordinal: int) -> dict[str, Any]:
    """Represent an already-positive ordinal without introducing a zero symbol."""

    value = _exact_int(ordinal, "ordinal")
    if value <= 0:
        raise DuotronicMathError("domain_violation", "ordinal must be > 0")
    return {
        "ordinal": value,
        "bijective": "".join(bijective_encode(value)),
        "alphabet": list(DEFAULT_ALPHABET),
        "profile": "bijective-positive-ordinal-v1",
        "reference_shake256_512": REFERENCE_SHAKE256_512,
    }


def bounded_score_codeword(score: float, *, scale: int = 1000, baseline: int = DEFAULT_BASELINE) -> dict[str, Any]:
    """Encode a normalized score as a deterministic positive integer codeword.

    Floating-point scores remain ordinary evaluation metadata. The integer
    projection is used only for deterministic WG-RNN/witness ordering and does
    not claim mathematical equivalence between the continuous and discrete
    representations.
    """

    value = max(0.0, min(1.0, float(score)))
    payload = int(round(value * max(1, int(scale))))
    codeword = encode_baseline(payload, baseline)
    return {
        "score": value,
        "scale": int(scale),
        "payload": payload,
        "baseline": baseline,
        "codeword": codeword,
        "bijective": "".join(bijective_encode(codeword)),
        "profile": "positive-baseline-score-projection-v1",
        "reference_shake256_512": REFERENCE_SHAKE256_512,
    }
