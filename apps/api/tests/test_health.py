from fastapi.testclient import TestClient

from careeros_api.app import create_app
from careeros_platform.settings import Environment, Settings


def _test_settings() -> Settings:
    return Settings(
        database_url="postgresql://localhost:5432/careeros_test",
        supabase_url="http://127.0.0.1:54321",
        supabase_anon_key="test-anon-key",
        supabase_jwt_secret="test-jwt-secret-at-least-32-characters-long",
        environment=Environment.DEVELOPMENT,
    )


def test_healthz_returns_ok() -> None:
    with TestClient(create_app(_test_settings())) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_returns_ok_with_checks() -> None:
    with TestClient(create_app(_test_settings())) as client:
        response = client.get("/readyz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"] == {"self": "ok"}
