import pytest
from pydantic import ValidationError

from careeros_platform.settings import (
    Environment,
    Settings,
    get_settings,
    load_settings,
)


def test_missing_required_var_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CAREEROS_DATABASE_URL", raising=False)
    with pytest.raises(ValidationError) as exc_info:
        # Intentionally omit the required var to assert fail-fast behaviour.
        Settings()  # type: ignore[call-arg]
    assert "database_url" in str(exc_info.value)


def test_valid_env_loads(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAREEROS_DATABASE_URL", "postgresql://localhost:5432/careeros")
    # database_url is supplied via the environment variable set above.
    settings = Settings()  # type: ignore[call-arg]
    assert settings.database_url == "postgresql://localhost:5432/careeros"
    assert settings.environment is Environment.DEVELOPMENT
    assert settings.app_name == "career-os"


def test_explicit_values_take_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAREEROS_DATABASE_URL", "postgresql://env/db")
    settings = Settings(database_url="postgresql://explicit/db")
    assert settings.database_url == "postgresql://explicit/db"


def test_environment_selects_dotenv_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAREEROS_ENVIRONMENT", Environment.STAGING.value)
    monkeypatch.setenv("CAREEROS_DATABASE_URL", "postgresql://staging/db")
    settings = load_settings()
    assert settings.database_url == "postgresql://staging/db"


def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAREEROS_DATABASE_URL", "postgresql://localhost/db")
    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()
    assert first is second
