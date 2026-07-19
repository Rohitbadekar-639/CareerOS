"""Minimal typed application settings.

This is a deliberately small slice of the full T9 configuration module,
created only because T6 (the api skeleton) must wire to typed settings and the
locked architecture (Technical Architecture §2) places configuration in
`shared/platform`. The complete T9 scope (per-environment file loading,
fail-fast on missing required vars, secret-store integration) is NOT
implemented here and remains owned by T9.
"""

from enum import StrEnum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CAREEROS_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "career-os"
    environment: Environment = Environment.DEVELOPMENT
    log_level: str = "INFO"
    api_host: str = "127.0.0.1"
    api_port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()
