"""Typed application configuration (T9).

Central, typed settings loaded per environment via ``pydantic-settings``.

Precedence (highest first): explicit keyword arguments, process environment
variables (prefixed ``CAREEROS_``), the environment-specific dotenv file
(``.env.<environment>``), then the base ``.env`` file. Missing required values
fail fast at construction with a clear ``ValidationError``.

Secrets are never committed: dotenv files are git-ignored and only real
environment variables carry credentials in staging/production.
"""

import os
from enum import StrEnum
from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX = "CAREEROS_"


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


def _dotenv_chain(environment: str) -> tuple[str, ...]:
    """Base dotenv plus an environment-specific override file.

    Later files win in pydantic-settings, so the environment-specific file
    overrides the shared base.
    """
    return (".env", f".env.{environment}")


class Settings(BaseSettings):
    # No env_file here: raw ``Settings()`` reads only process env vars, which
    # keeps it deterministic. Dotenv layering is applied by ``load_settings``.
    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        extra="ignore",
    )

    # Required: absence fails fast (no default). Holds credentials, so it is
    # sourced only from the environment/secret store, never committed.
    database_url: str

    # Supabase Auth (M1). Local values come from `supabase status` after
    # `supabase start`; see docs/development.md. Service-role keys are not
    # loaded here — they must never reach the browser and are added only when
    # a server use case needs them.
    supabase_url: str
    supabase_anon_key: str
    supabase_jwt_secret: str
    supabase_jwt_audience: str = "authenticated"
    # Optional override when the JWKS host differs from the JWT issuer URL
    # (e.g. Docker API → host.docker.internal while iss stays 127.0.0.1).
    supabase_jwks_url: str | None = None

    # Optional, with safe local defaults.
    app_name: str = "career-os"
    environment: Environment = Environment.DEVELOPMENT
    log_level: str = "INFO"
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # Job Intelligence MVP (ADR-0001). Comma-separated `kind:board_token` pairs.
    # Example: greenhouse:stripe,ashby:notion
    opportunity_boards: str = "greenhouse:stripe,greenhouse:gitlab"
    ingestion_interval_seconds: int = 3600
    match_min_score: float = 0.55
    opportunity_active_limit: int = 400

    @computed_field  # type: ignore[prop-decorator]
    @property
    def supabase_jwt_issuer(self) -> str:
        """JWT issuer claim used by local/hosted Supabase Auth."""
        return f"{self.supabase_url.rstrip('/')}/auth/v1"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def resolved_supabase_jwks_url(self) -> str:
        """JWKS discovery URL for asymmetric Supabase access tokens."""
        if self.supabase_jwks_url and self.supabase_jwks_url.strip():
            return self.supabase_jwks_url.rstrip("/")
        return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"


def load_settings() -> Settings:
    """Build settings for the active environment.

    The environment is read from ``CAREEROS_ENVIRONMENT`` (default
    ``development``) and selects which dotenv override file is layered on top of
    the base ``.env``.
    """
    environment = os.getenv(f"{ENV_PREFIX}ENVIRONMENT", Environment.DEVELOPMENT.value)
    # pydantic-settings accepts ``_env_file`` at runtime, but its mypy plugin
    # omits it from the generated __init__; this is the one place we use it.
    return Settings(_env_file=_dotenv_chain(environment))  # type: ignore[call-arg]


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    return load_settings()
