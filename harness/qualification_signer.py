#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pq_crypto import (
    generate_signing_key,
    sign_envelope,
    verify_envelope,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if (
        payload.get("schema") != "duotronic-paired-qualification-payload/v1"
        or payload.get("production_eligible") is not False
        or payload.get("authority_profile") != "sandbox-test-only"
    ):
        raise ValueError("qualification payload is not sandbox confined")
    record, secret_key = generate_signing_key("candidate-qualification")
    envelope = sign_envelope(
        payload, record, secret_key, purpose="candidate-qualification"
    )
    verified = verify_envelope(envelope, record)
    output = {
        "schema": "duotronic-signed-paired-qualification/v1",
        "envelope": envelope,
        "public_key": record.as_dict(),
        "signature_verified": verified,
        "private_key_persisted": False,
        "authority_profile": "sandbox-test-only",
        "production_eligible": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if verified else 2


if __name__ == "__main__":
    raise SystemExit(main())
