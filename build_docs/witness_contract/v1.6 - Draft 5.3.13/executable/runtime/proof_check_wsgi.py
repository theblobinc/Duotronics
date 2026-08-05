#!/usr/bin/env python3
"""Authenticated synchronous WSGI adapter for the proof-check operation."""

from __future__ import annotations

import json
from typing import Callable, Iterable

from proof_authority import AuthorityFailure, canonical_bytes, canonical_json_loads
from proof_check_service import ProofCheckApplication

MAX_REQUEST_BYTES = 1024 * 1024
AUTHENTICATED_PRINCIPAL_ENVIRON_KEY = "witness.authenticated_principal_id"


class ProofCheckWSGI:
    def __init__(self, application: ProofCheckApplication):
        self.application = application

    def __call__(self, environ: dict, start_response: Callable) -> Iterable[bytes]:
        if environ.get("REQUEST_METHOD") != "POST" or environ.get("PATH_INFO") != "/v2/proof-checks":
            return self._respond(start_response, "404 Not Found", {"error": "route_not_found"})
        if environ.get("CONTENT_TYPE", "").split(";", 1)[0].strip() != "application/json":
            return self._respond(start_response, "415 Unsupported Media Type", {"error": "application_json_required"})
        try:
            length = int(environ.get("CONTENT_LENGTH") or "0")
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise ValueError("invalid request length")
            data = environ["wsgi.input"].read(length + 1)
            if len(data) != length or len(data) > MAX_REQUEST_BYTES:
                raise ValueError("request body length mismatch")
            request = canonical_json_loads(data.decode("utf-8"))
            if environ.get("HTTP_IDEMPOTENCY_KEY") != request.get("idempotency_key"):
                raise ValueError("Idempotency-Key header must equal body idempotency_key")
            principal_id = environ.get(AUTHENTICATED_PRINCIPAL_ENVIRON_KEY)
            if not isinstance(principal_id, str) or not principal_id:
                raise AuthorityFailure("governance_authorization_invalid", "verified middleware principal is required")
            result = self.application.handle(request, authenticated_principal_id=principal_id)
            return self._respond(start_response, "200 OK", result)
        except AuthorityFailure as error:
            if error.code == "cache_key_rotation_requires_new_idempotency_key":
                status = "409 Conflict"
            elif error.code == "cache_audit_publication_failed":
                status = "503 Service Unavailable"
            else:
                status = "403 Forbidden" if error.code in {"policy_decision_invalid", "governance_authorization_invalid"} else "422 Unprocessable Entity"
            return self._respond(start_response, status, {"error": error.code, "message": str(error)})
        except TimeoutError as error:
            return self._respond(start_response, "504 Gateway Timeout", {"error": "idempotency_wait_timeout", "message": str(error)})
        except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
            return self._respond(start_response, "400 Bad Request", {"error": "invalid_request", "message": str(error)})

    @staticmethod
    def _respond(start_response: Callable, status: str, value: dict) -> list[bytes]:
        body = canonical_bytes(value)
        start_response(status, [("Content-Type", "application/json"), ("Content-Length", str(len(body))), ("Cache-Control", "no-store")])
        return [body]


__all__ = ["AUTHENTICATED_PRINCIPAL_ENVIRON_KEY", "ProofCheckWSGI"]
