"""Unit tests for SupabaseAuthProvider (HS256 local; ES256 via injected JWKS)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from jwt.algorithms import ECAlgorithm

from careeros_identity.infrastructure.supabase_auth_provider import SupabaseAuthProvider
from careeros_shared_kernel import PermissionDeniedError, ValidationError

_SECRET = "super-secret-jwt-token-with-at-least-32-characters-long"
_ISSUER = "http://127.0.0.1:54321/auth/v1"
_AUDIENCE = "authenticated"
_KID = "test-es256-kid"


def _provider(**kwargs: object) -> SupabaseAuthProvider:
    return SupabaseAuthProvider(
        jwt_secret=_SECRET,
        jwt_issuer=_ISSUER,
        jwt_audience=_AUDIENCE,
        **kwargs,  # type: ignore[arg-type]
    )


def _hs_token(**claims: object) -> str:
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


class _StaticEs256Jwks:
    def __init__(self, private_key: ec.EllipticCurvePrivateKey) -> None:
        self._private_key = private_key
        self._public_key = private_key.public_key()

    def mint(self, **claims: object) -> str:
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
        return jwt.encode(
            payload,
            self._private_key,
            algorithm="ES256",
            headers={"kid": _KID},
        )

    def get_signing_key_from_jwt(self, token: str) -> object:
        class _Key:
            key = self._public_key

        return _Key()


def test_verify_valid_hs256_token() -> None:
    subject = str(uuid4())
    token = _hs_token(sub=subject, email="Alex@Example.COM")
    identity = _provider().verify_access_token(token)
    assert identity.auth_ref.value == subject
    assert str(identity.email) == "alex@example.com"
    assert identity.email_verified is True


def test_verify_valid_es256_token_via_jwks() -> None:
    jwks = _StaticEs256Jwks(ec.generate_private_key(ec.SECP256R1()))
    subject = str(uuid4())
    token = jwks.mint(sub=subject, email="es256@example.com")
    identity = _provider(jwks_client=jwks).verify_access_token(token)
    assert identity.auth_ref.value == subject
    assert str(identity.email) == "es256@example.com"


def test_reject_es256_without_jwks() -> None:
    jwks = _StaticEs256Jwks(ec.generate_private_key(ec.SECP256R1()))
    token = jwks.mint()
    with pytest.raises(PermissionDeniedError):
        _provider().verify_access_token(token)


def test_reject_missing_token() -> None:
    with pytest.raises(PermissionDeniedError):
        _provider().verify_access_token("")


def test_reject_bad_signature() -> None:
    token = _hs_token()
    other = SupabaseAuthProvider(
        jwt_secret="other-secret-that-is-also-long-enough-32c",
        jwt_issuer=_ISSUER,
        jwt_audience=_AUDIENCE,
    )
    with pytest.raises(PermissionDeniedError):
        other.verify_access_token(token)


def test_reject_wrong_audience() -> None:
    token = _hs_token(aud="anon")
    with pytest.raises(PermissionDeniedError):
        _provider().verify_access_token(token)


def test_reject_expired_token() -> None:
    now = datetime.now(UTC)
    token = _hs_token(iat=now - timedelta(hours=2), exp=now - timedelta(hours=1))
    with pytest.raises(PermissionDeniedError):
        _provider().verify_access_token(token)


def test_reject_jwks_url_and_client_together() -> None:
    with pytest.raises(ValidationError):
        SupabaseAuthProvider(
            jwt_secret=_SECRET,
            jwt_issuer=_ISSUER,
            jwks_url="http://127.0.0.1:54321/auth/v1/.well-known/jwks.json",
            jwks_client=_StaticEs256Jwks(ec.generate_private_key(ec.SECP256R1())),
        )


def test_ec_algorithm_roundtrip_sanity() -> None:
    # Ensures PyJWT[crypto] can serialize EC keys used by JWKS verification.
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = ECAlgorithm.to_jwk(private_key.public_key(), as_dict=True)
    assert jwk["kty"] == "EC"
    assert jwk["crv"] == "P-256"
