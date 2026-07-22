"""Postgres connection helpers for request-scoped repositories."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import psycopg
from psycopg import Connection


def open_connection(database_url: str) -> Connection[Any]:
    """Open a psycopg connection (caller owns commit/rollback/close)."""
    return psycopg.connect(database_url, autocommit=False)


def connection_scope(database_url: str) -> Iterator[Connection[Any]]:
    """Yield a connection and commit on success / rollback on error."""
    conn = open_connection(database_url)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
