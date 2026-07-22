"""FastAPI dependency wiring for identity auth + persistence."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from psycopg import Connection

from careeros_api.auth import extract_bearer_token
from careeros_identity.infrastructure import PostgresUserRepository, SupabaseAuthProvider
from careeros_identity.ports.auth_provider import AuthProvider, VerifiedIdentity
from careeros_identity.ports.user_repository import UserRepository
from careeros_platform.db import open_connection
from careeros_platform.settings import Settings, get_settings
from careeros_shared_kernel import PermissionDeniedError


def get_app_settings(request: Request) -> Settings:
    settings = getattr(request.app.state, "settings", None)
    if isinstance(settings, Settings):
        return settings
    return get_settings()


def get_auth_provider(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> AuthProvider:
    return SupabaseAuthProvider(
        jwt_secret=settings.supabase_jwt_secret,
        jwt_issuer=settings.supabase_jwt_issuer,
        jwt_audience=settings.supabase_jwt_audience,
        jwks_url=settings.resolved_supabase_jwks_url,
    )


def get_db_connection(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> Iterator[Connection[Any]]:
    conn = open_connection(settings.database_url)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_user_repository(
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
) -> UserRepository:
    return PostgresUserRepository(conn)


def require_verified_identity(
    request: Request,
    auth: Annotated[AuthProvider, Depends(get_auth_provider)],
) -> VerifiedIdentity:
    try:
        token = extract_bearer_token(request)
        return auth.verify_access_token(token)
    except PermissionDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
