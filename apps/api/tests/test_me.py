"""API tests for GET /v1/me authentication."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from careeros_api.app import create_app
from careeros_api.deps import get_db_connection, get_user_repository
from careeros_identity.domain import (
    AuthRef,
    ConsentPurpose,
    ConsentScope,
    EmailAddress,
    User,
)
from careeros_platform.settings import Environment, Settings

_SECRET = "test-jwt-secret-at-least-32-characters-long"
_ISSUER = "http://127.0.0.1:54321/auth/v1"
_AUDIENCE = "authenticated"


def _settings() -> Settings:
    return Settings(
        database_url="postgresql://localhost:5432/careeros_test",
        supabase_url="http://127.0.0.1:54321",
        supabase_anon_key="test-anon-key",
        supabase_jwt_secret=_SECRET,
        supabase_jwt_audience=_AUDIENCE,
        environment=Environment.DEVELOPMENT,
    )


def _token(*, sub: str | None = None, email: str = "user@example.com") -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": sub or str(uuid4()),
        "email": email,
        "email_verified": True,
        "aud": _AUDIENCE,
        "iss": _ISSUER,
        "iat": now,
        "exp": now + timedelta(hours=1),
    }
    return jwt.encode(payload, _SECRET, algorithm="HS256")


class _MemoryUserRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, User] = {}
        self._by_auth: dict[str, User] = {}

    def get(self, user_id: Any) -> User | None:
        return self._by_id.get(str(user_id.value))

    def get_by_auth_ref(self, auth_ref: AuthRef) -> User | None:
        return self._by_auth.get(auth_ref.value)

    def save(self, user: User) -> None:
        self._by_id[str(user.id.value)] = user
        self._by_auth[str(user.auth_ref)] = user


@pytest.fixture
def client() -> Any:
    app = create_app(_settings())
    repo = _MemoryUserRepository()

    def _repo() -> _MemoryUserRepository:
        return repo

    def _conn() -> Any:
        yield None

    app.dependency_overrides[get_user_repository] = _repo
    app.dependency_overrides[get_db_connection] = _conn
    with TestClient(app) as test_client:
        yield test_client, repo
    app.dependency_overrides.clear()


def test_me_requires_bearer(client: Any) -> None:
    test_client, _repo = client
    response = test_client.get("/v1/me")
    assert response.status_code == 401


def test_me_registers_new_user(client: Any) -> None:
    test_client, repo = client
    sub = str(uuid4())
    token = _token(sub=sub, email="new@example.com")
    response = test_client.get("/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "new@example.com"
    assert body["email_verified"] is True
    assert body["role"] == "candidate"
    assert repo.get_by_auth_ref(AuthRef(sub)) is not None


def test_me_returns_existing_user(client: Any) -> None:
    test_client, repo = client
    sub = str(uuid4())
    user = User.register(
        EmailAddress("existing@example.com"),
        AuthRef(sub),
        [ConsentScope(ConsentPurpose.ESSENTIAL_ACCOUNT)],
        email_verified=True,
    )
    user.pull_events()
    repo.save(user)

    token = _token(sub=sub, email="existing@example.com")
    response = test_client.get("/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == str(user.id.value)
    assert response.json()["email"] == "existing@example.com"
