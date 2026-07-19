from fastapi import FastAPI
from fastapi.testclient import TestClient

from careeros_api.app import create_app
from careeros_platform.settings import Environment, Settings


def _test_settings() -> Settings:
    return Settings(
        database_url="postgresql://localhost:5432/careeros_test",
        environment=Environment.DEVELOPMENT,
    )


def test_create_app_returns_fastapi_instance() -> None:
    app = create_app(_test_settings())
    assert isinstance(app, FastAPI)


def test_app_starts_and_serves_openapi() -> None:
    with TestClient(create_app(_test_settings())) as client:
        response = client.get("/openapi.json")
    assert response.status_code == 200
