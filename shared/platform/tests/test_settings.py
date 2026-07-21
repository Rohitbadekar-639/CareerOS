import pytest
from pydantic import ValidationError

from careeros_platform.settings import (
    Environment,
    Settings,
    get_settings,
    load_settings,
)

_LOCAL_SUPABASE = {
    "supabase_url": "http://127.0.0.1:54321",
    "supabase_anon_key": "test-anon-key",
    "supabase_jwt_secret": "test-jwt-secret-at-least-32-characters-long",
}


def test_missing_required_var_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CAREEROS_DATABASE_URL", raising=False)
    monkeypatch.delenv("CAREEROS_SUPABASE_URL", raising=False)
    monkeypatch.delenv("CAREEROS_SUPABASE_ANON_KEY", raising=False)
    monkeypatch.delenv("CAREEROS_SUPABASE_JWT_SECRET", raising=False)
    with pytest.raises(ValidationError) as exc_info:
        # Intentionally omit required vars to assert fail-fast behaviour.
        Settings()  # type: ignore[call-arg]
    message = str(exc_info.value)
    assert "database_url" in message


def test_missing_supabase_settings_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAREEROS_DATABASE_URL", "postgresql://localhost:5432/careeros")
    monkeypatch.delenv("CAREEROS_SUPABASE_URL", raising=False)
    monkeypatch.delenv("CAREEROS_SUPABASE_ANON_KEY", raising=False)
    monkeypatch.delenv("CAREEROS_SUPABASE_JWT_SECRET", raising=False)
    with pytest.raises(ValidationError) as exc_info:
        Settings()  # type: ignore[call-arg]
    message = str(exc_info.value)
    assert (
        "supabase_url" in message
        or "supabase_anon_key" in message
        or "supabase_jwt_secret" in message
    )


def test_valid_env_loads(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAREEROS_DATABASE_URL", "postgresql://localhost:5432/careeros")
    monkeypatch.setenv("CAREEROS_SUPABASE_URL", _LOCAL_SUPABASE["supabase_url"])
    monkeypatch.setenv("CAREEROS_SUPABASE_ANON_KEY", _LOCAL_SUPABASE["supabase_anon_key"])
    monkeypatch.setenv("CAREEROS_SUPABASE_JWT_SECRET", _LOCAL_SUPABASE["supabase_jwt_secret"])
    settings = Settings()  # type: ignore[call-arg]
    assert settings.database_url == "postgresql://localhost:5432/careeros"
    assert settings.supabase_url == _LOCAL_SUPABASE["supabase_url"]
    assert settings.supabase_anon_key == _LOCAL_SUPABASE["supabase_anon_key"]
    assert settings.supabase_jwt_secret == _LOCAL_SUPABASE["supabase_jwt_secret"]
    assert settings.supabase_jwt_audience == "authenticated"
    assert settings.supabase_jwt_issuer == "http://127.0.0.1:54321/auth/v1"
    assert settings.environment is Environment.DEVELOPMENT
    assert settings.app_name == "career-os"


def test_explicit_values_take_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAREEROS_DATABASE_URL", "postgresql://env/db")
    monkeypatch.setenv("CAREEROS_SUPABASE_URL", "http://env.example")
    monkeypatch.setenv("CAREEROS_SUPABASE_ANON_KEY", "env-anon")
    monkeypatch.setenv("CAREEROS_SUPABASE_JWT_SECRET", "env-jwt-secret")
    settings = Settings(
        database_url="postgresql://explicit/db",
        supabase_url=_LOCAL_SUPABASE["supabase_url"],
        supabase_anon_key=_LOCAL_SUPABASE["supabase_anon_key"],
        supabase_jwt_secret=_LOCAL_SUPABASE["supabase_jwt_secret"],
    )
    assert settings.database_url == "postgresql://explicit/db"
    assert settings.supabase_url == _LOCAL_SUPABASE["supabase_url"]


def test_environment_selects_dotenv_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAREEROS_ENVIRONMENT", Environment.STAGING.value)
    monkeypatch.setenv("CAREEROS_DATABASE_URL", "postgresql://staging/db")
    monkeypatch.setenv("CAREEROS_SUPABASE_URL", _LOCAL_SUPABASE["supabase_url"])
    monkeypatch.setenv("CAREEROS_SUPABASE_ANON_KEY", _LOCAL_SUPABASE["supabase_anon_key"])
    monkeypatch.setenv("CAREEROS_SUPABASE_JWT_SECRET", _LOCAL_SUPABASE["supabase_jwt_secret"])
    settings = load_settings()
    assert settings.database_url == "postgresql://staging/db"


def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAREEROS_DATABASE_URL", "postgresql://localhost/db")
    monkeypatch.setenv("CAREEROS_SUPABASE_URL", _LOCAL_SUPABASE["supabase_url"])
    monkeypatch.setenv("CAREEROS_SUPABASE_ANON_KEY", _LOCAL_SUPABASE["supabase_anon_key"])
    monkeypatch.setenv("CAREEROS_SUPABASE_JWT_SECRET", _LOCAL_SUPABASE["supabase_jwt_secret"])
    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()
    assert first is second
