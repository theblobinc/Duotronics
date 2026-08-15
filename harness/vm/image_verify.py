#!/usr/bin/env python3
"""Verify a VM base image with the project's SHAKE256-512 identifier profile."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: image_verify.py IMAGE EXPECTED_HEX", file=sys.stderr)
        return 64
    image = Path(sys.argv[1])
    expected = sys.argv[2].lower()
    if not re.fullmatch(r"[0-9a-f]{128}", expected):
        print("expected digest must be 128 lowercase hex characters", file=sys.stderr)
        return 65
    digest = hashlib.shake_256()
    with image.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    actual = digest.hexdigest(64)
    print(actual)
    return 0 if actual == expected else 66


if __name__ == "__main__":
    raise SystemExit(main())
