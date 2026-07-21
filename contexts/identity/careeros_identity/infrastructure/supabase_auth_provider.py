"""Verify Supabase Auth JWTs (HS256) — adapter for the AuthProvider port.

Uses the project's configured JWT secret / issuer / audience. No network calls;
tokens are verified locally the same way FastAPI middleware will later.
"""

from __future__ import annotations

from typing import Any

import jwt

from careeros_identity.domain.value_objects import AuthRef, EmailAddress
from careeros_identity.ports.auth_provider import VerifiedIdentity
from careeros_shared_kernel import PermissionDeniedError, ValidationError


class SupabaseAuthProvider:
    """AuthProvider adapter for Supabase-issued access tokens."""

    def __init__(
        self,
        *,
        jwt_secret: str,
        jwt_issuer: str,
        jwt_audience: str = "authenticated",
    ) -> None:
        if not jwt_secret.strip():
            raise ValidationError("jwt_secret must not be empty")
        if not jwt_issuer.strip():
            raise ValidationError("jwt_issuer must not be empty")
        self._jwt_secret = jwt_secret
        self._jwt_issuer = jwt_issuer.rstrip("/")
        self._jwt_audience = jwt_audience

    def verify_access_token(self, token: str) -> VerifiedIdentity:
        if not token or not token.strip():
            raise PermissionDeniedError("Missing access token")

        try:
            payload = jwt.decode(
                token.strip(),
                self._jwt_secret,
                algorithms=["HS256"],
                audience=self._jwt_audience,
                issuer=self._jwt_issuer,
            )
        except jwt.PyJWTError as exc:
            raise PermissionDeniedError("Invalid or expired access token") from exc

        return self._to_identity(payload)

    def _to_identity(self, payload: dict[str, Any]) -> VerifiedIdentity:
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.strip():
            raise PermissionDeniedError("Token missing subject")

        email_raw = payload.get("email")
        if not isinstance(email_raw, str) or not email_raw.strip():
            raise PermissionDeniedError("Token missing email")

        email_verified = bool(payload.get("email_verified", False))
        # Supabase sometimes nests verified flag under user_metadata.
        metadata = payload.get("user_metadata")
        if isinstance(metadata, dict) and "email_verified" in metadata:
            email_verified = bool(metadata["email_verified"])

        try:
            return VerifiedIdentity(
                auth_ref=AuthRef(subject),
                email=EmailAddress(email_raw),
                email_verified=email_verified,
            )
        except ValidationError as exc:
            raise PermissionDeniedError("Token contains invalid identity claims") from exc
