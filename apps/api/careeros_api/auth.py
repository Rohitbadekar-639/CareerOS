"""HTTP bearer-token extraction for API authentication."""

from __future__ import annotations

from starlette.requests import Request

from careeros_shared_kernel import PermissionDeniedError


def extract_bearer_token(request: Request) -> str:
    """Return the Authorization Bearer token or raise ``PermissionDeniedError``."""
    header = request.headers.get("authorization")
    if header is None or not header.strip():
        raise PermissionDeniedError("Missing Authorization header")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise PermissionDeniedError("Authorization header must be Bearer <token>")
    return token.strip()
