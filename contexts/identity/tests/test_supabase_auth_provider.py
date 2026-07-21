"""Unit tests for SupabaseAuthProvider (no network / no database)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from careeros_identity.infrastructure.supabase_auth_provider import SupabaseAuthProvider
from careeros_shared_kernel import PermissionDeniedError

_SECRET = "super-secret-jwt-token-with-at-least-32-characters-long"
_ISSUER = "http://127.0.0.1:54321/auth/v1"
_AUDIENCE = "authenticated"


def _provider() -> SupabaseAuthProvider:
    return SupabaseAuthProvider(
        jwt_secret=_SECRET,
        jwt_issuer=_ISSUER,
        jwt_audience=_AUDIENCE,
    )


def _token(**claims: object) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(uuid4()),
        "email": "candidate@example.com",
        "email_verified": True,
        "aud": _AUDIENCE,
        "iss": _ISSUER,
        "iat": now,
        "exp": now + timedelta(hours=1),
        **claims,
    }
    return jwt.encode(payload, _SECRET, algorithm="HS256")


def test_verify_valid_token() -> None:
    subject = str(uuid4())
    token = _token(sub=subject, email="Alex@Example.COM")
    identity = _provider().verify_access_token(token)
    assert identity.auth_ref.value == subject
    assert str(identity.email) == "alex@example.com"
    assert identity.email_verified is True


def test_reject_missing_token() -> None:
    with pytest.raises(PermissionDeniedError):
        _provider().verify_access_token("")


def test_reject_bad_signature() -> None:
    token = _token()
    other = SupabaseAuthProvider(
        jwt_secret="other-secret-that-is-also-long-enough-32c",
        jwt_issuer=_ISSUER,
        jwt_audience=_AUDIENCE,
    )
    with pytest.raises(PermissionDeniedError):
        other.verify_access_token(token)


def test_reject_wrong_audience() -> None:
    token = _token(aud="anon")
    with pytest.raises(PermissionDeniedError):
        _provider().verify_access_token(token)


def test_reject_expired_token() -> None:
    now = datetime.now(UTC)
    token = _token(iat=now - timedelta(hours=2), exp=now - timedelta(hours=1))
    with pytest.raises(PermissionDeniedError):
        _provider().verify_access_token(token)
