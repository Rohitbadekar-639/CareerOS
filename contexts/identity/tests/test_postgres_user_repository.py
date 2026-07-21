"""Integration tests for PostgresUserRepository + RLS.

Requires a migrated Postgres. Skips when ``CAREEROS_TEST_DATABASE_URL`` /
``CAREEROS_DATABASE_URL`` is unset or unreachable.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import psycopg
import pytest

from careeros_identity.domain import (
    AuthRef,
    ConsentPurpose,
    ConsentScope,
    EmailAddress,
    User,
    UserStatus,
)
from careeros_identity.infrastructure import PostgresUserRepository

pytestmark = pytest.mark.integration


def _database_url() -> str | None:
    return os.environ.get("CAREEROS_TEST_DATABASE_URL") or os.environ.get("CAREEROS_DATABASE_URL")


def _can_connect(url: str) -> bool:
    try:
        with psycopg.connect(url, connect_timeout=3) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def database_url() -> str:
    url = _database_url()
    if url is None:
        pytest.skip("CAREEROS_TEST_DATABASE_URL / CAREEROS_DATABASE_URL not set")
    if not _can_connect(url):
        pytest.skip(f"Postgres not reachable at {url}")
    return url


@pytest.fixture
def conn(database_url: str) -> Iterator[psycopg.Connection]:
    connection = psycopg.connect(database_url, autocommit=False)
    try:
        row = connection.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'identity' AND table_name = 'users'
            """
        ).fetchone()
        if row is None:
            pytest.skip("identity.users missing — run `pnpm db:migrate` first")

        # Bypass only for truncate (transaction-local), then RLS applies again.
        with connection.transaction():
            connection.execute("SELECT set_config('app.rls_bypass', 'on', true)")
            connection.execute("TRUNCATE identity.consents, identity.users CASCADE")
        yield connection
    finally:
        connection.close()


def _register(email: str, auth_ref: str) -> User:
    return User.register(
        EmailAddress(email),
        AuthRef(auth_ref),
        [ConsentScope(ConsentPurpose.ESSENTIAL_ACCOUNT)],
        email_verified=True,
    )


def test_save_and_get_round_trip(conn: psycopg.Connection) -> None:
    repo = PostgresUserRepository(conn)
    user = _register("one@example.com", "auth-ref-1")
    user.grant_consent(ConsentScope(ConsentPurpose.NOTIFICATIONS))
    user.pull_events()

    repo.save(user)
    conn.commit()

    loaded = repo.get(user.id)
    assert loaded is not None
    assert loaded.id == user.id
    assert str(loaded.email) == "one@example.com"
    assert str(loaded.auth_ref) == "auth-ref-1"
    assert loaded.status is UserStatus.ACTIVE
    assert loaded.has_active_consent(ConsentPurpose.ESSENTIAL_ACCOUNT)
    assert loaded.has_active_consent(ConsentPurpose.NOTIFICATIONS)


def test_get_by_auth_ref(conn: psycopg.Connection) -> None:
    repo = PostgresUserRepository(conn)
    user = _register("two@example.com", "auth-ref-2")
    user.pull_events()
    repo.save(user)
    conn.commit()

    loaded = repo.get_by_auth_ref(AuthRef("auth-ref-2"))
    assert loaded is not None
    assert loaded.id == user.id


def test_rls_hides_other_users_rows(conn: psycopg.Connection) -> None:
    repo = PostgresUserRepository(conn)
    alice = _register("alice@example.com", "auth-alice")
    bob = _register("bob@example.com", "auth-bob")
    alice.pull_events()
    bob.pull_events()
    repo.save(alice)
    repo.save(bob)
    conn.commit()

    # Scoped as Bob under careeros_app: Alice must be invisible.
    with conn.transaction():
        conn.execute("SET LOCAL ROLE careeros_app")
        conn.execute("SELECT set_config('app.rls_bypass', 'off', true)")
        conn.execute("SELECT set_config('app.current_auth_ref', '', true)")
        conn.execute(
            "SELECT set_config('app.current_user_id', %s, true)",
            (str(bob.id.value),),
        )
        row = conn.execute(
            "SELECT id FROM identity.users WHERE id = %s",
            (alice.id.value,),
        ).fetchone()
        assert row is None

    assert repo.get(alice.id) is not None

    with conn.transaction():
        conn.execute("SET LOCAL ROLE careeros_app")
        conn.execute("SELECT set_config('app.rls_bypass', 'off', true)")
        conn.execute(
            "SELECT set_config('app.current_user_id', %s, true)",
            (str(bob.id.value),),
        )
        missing = conn.execute(
            "SELECT email FROM identity.users WHERE id = %s",
            (alice.id.value,),
        ).fetchone()
        assert missing is None


def test_consent_withdraw_persists(conn: psycopg.Connection) -> None:
    repo = PostgresUserRepository(conn)
    user = _register("three@example.com", "auth-ref-3")
    user.grant_consent(ConsentScope(ConsentPurpose.NOTIFICATIONS))
    user.pull_events()
    repo.save(user)
    conn.commit()

    user.withdraw_consent(ConsentPurpose.NOTIFICATIONS)
    user.pull_events()
    repo.save(user)
    conn.commit()

    loaded = repo.get(user.id)
    assert loaded is not None
    assert not loaded.has_active_consent(ConsentPurpose.NOTIFICATIONS)
    assert any(
        c.purpose is ConsentPurpose.NOTIFICATIONS and not c.is_active for c in loaded.consents
    )
