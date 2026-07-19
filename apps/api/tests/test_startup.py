from fastapi import FastAPI
from fastapi.testclient import TestClient

from careeros_api.app import create_app
from careeros_platform.settings import Environment, Settings


def test_create_app_returns_fastapi_instance() -> None:
    app = create_app(Settings(environment=Environment.DEVELOPMENT))
    assert isinstance(app, FastAPI)


def test_app_starts_and_serves_openapi() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/openapi.json")
    assert response.status_code == 200
