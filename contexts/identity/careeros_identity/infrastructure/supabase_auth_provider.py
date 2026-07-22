"""Verify Supabase Auth JWTs — adapter for the AuthProvider port.

Local Supabase CLI (and hosted Auth with signing keys) issue user access
tokens as asymmetric JWTs (typically ES256). Those are verified via the
Auth JWKS endpoint. Legacy HS256 tokens signed with the shared JWT secret
remain supported for tests and older projects.
"""

from __future__ import annotations

from typing import Any, Protocol

import jwt
from jwt import PyJWKClient

from careeros_identity.domain.value_objects import AuthRef, EmailAddress
from careeros_identity.ports.auth_provider import VerifiedIdentity
from careeros_shared_kernel import PermissionDeniedError, ValidationError

_ASYMMETRIC_ALGS = frozenset({"ES256", "RS256", "EdDSA"})
_HS_ALGS = frozenset({"HS256"})


class _SigningKeyClient(Protocol):
    def get_signing_key_from_jwt(self, token: str) -> Any: ...


class SupabaseAuthProvider:
    """AuthProvider adapter for Supabase-issued access tokens."""

    def __init__(
        self,
        *,
        jwt_secret: str,
        jwt_issuer: str,
        jwt_audience: str = "authenticated",
        jwks_url: str | None = None,
        jwks_client: _SigningKeyClient | None = None,
    ) -> None:
        if not jwt_secret.strip():
            raise ValidationError("jwt_secret must not be empty")
        if not jwt_issuer.strip():
            raise ValidationError("jwt_issuer must not be empty")
        if jwks_client is not None and jwks_url is not None:
            raise ValidationError("pass jwks_url or jwks_client, not both")

        self._jwt_secret = jwt_secret
        self._jwt_issuer = jwt_issuer.rstrip("/")
        self._jwt_audience = jwt_audience
        self._jwks: _SigningKeyClient | None = jwks_client
        if jwks_url is not None:
            url = jwks_url.strip()
            if not url:
                raise ValidationError("jwks_url must not be empty")
            # Cache keys briefly; Auth rotates signing keys infrequently.
            self._jwks = PyJWKClient(url, cache_keys=True, lifespan=600)

    def verify_access_token(self, token: str) -> VerifiedIdentity:
        if not token or not token.strip():
            raise PermissionDeniedError("Missing access token")

        raw = token.strip()
        try:
            header = jwt.get_unverified_header(raw)
        except jwt.PyJWTError as exc:
            raise PermissionDeniedError("Invalid or expired access token") from exc

        alg = header.get("alg")
        if not isinstance(alg, str):
            raise PermissionDeniedError("Invalid or expired access token")

        try:
            if alg in _HS_ALGS:
                payload = jwt.decode(
                    raw,
                    self._jwt_secret,
                    algorithms=["HS256"],
                    audience=self._jwt_audience,
                    issuer=self._jwt_issuer,
                )
            elif alg in _ASYMMETRIC_ALGS:
                if self._jwks is None:
                    raise PermissionDeniedError("Invalid or expired access token")
                signing_key = self._jwks.get_signing_key_from_jwt(raw)
                payload = jwt.decode(
                    raw,
                    signing_key.key,
                    algorithms=[alg],
                    audience=self._jwt_audience,
                    issuer=self._jwt_issuer,
                )
            else:
                raise PermissionDeniedError("Invalid or expired access token")
        except PermissionDeniedError:
            raise
        except jwt.PyJWTError as exc:
            raise PermissionDeniedError("Invalid or expired access token") from exc
        except Exception as exc:
            # JWKS fetch / key resolution failures surface as generic auth denial.
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
