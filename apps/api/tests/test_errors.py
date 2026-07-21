from fastapi import FastAPI
from fastapi.testclient import TestClient

from careeros_api.app import create_app
from careeros_api.errors import PROBLEM_CONTENT_TYPE
from careeros_platform.settings import Environment, Settings
from careeros_shared_kernel.errors import NotFoundError


def _test_settings() -> Settings:
    return Settings(
        database_url="postgresql://localhost:5432/careeros_test",
        supabase_url="http://127.0.0.1:54321",
        supabase_anon_key="test-anon-key",
        supabase_jwt_secret="test-jwt-secret-at-least-32-characters-long",
        environment=Environment.DEVELOPMENT,
    )


def _app_with_failing_routes() -> FastAPI:
    app = create_app(_test_settings())

    @app.get("/_boom")
    def _boom() -> dict[str, str]:
        raise RuntimeError("internal secret detail")

    @app.get("/_missing")
    def _missing() -> dict[str, str]:
        raise NotFoundError("profile not found")

    return app


def test_unhandled_error_returns_problem_details_without_stack_trace() -> None:
    client = TestClient(_app_with_failing_routes(), raise_server_exceptions=False)
    response = client.get("/_boom")

    assert response.status_code == 500
    assert response.headers["content-type"].startswith(PROBLEM_CONTENT_TYPE)
    body = response.json()
    assert body["status"] == 500
    assert body["title"] == "Internal Server Error"
    assert body["detail"] == "An unexpected error occurred."
    # The internal exception message must never leak to the client.
    assert "internal secret detail" not in response.text
    assert "Traceback" not in response.text


def test_domain_error_maps_to_problem_details_status() -> None:
    client = TestClient(_app_with_failing_routes(), raise_server_exceptions=False)
    response = client.get("/_missing")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith(PROBLEM_CONTENT_TYPE)
    body = response.json()
    assert body["status"] == 404
    assert body["title"] == "NotFoundError"
    assert body["detail"] == "profile not found"
