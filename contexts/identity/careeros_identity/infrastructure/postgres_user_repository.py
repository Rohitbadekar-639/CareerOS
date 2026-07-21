"""Postgres adapter for UserRepository with session-scoped RLS."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from psycopg import Connection
from psycopg.errors import UniqueViolation
from psycopg.rows import dict_row

from careeros_identity.domain.consent import Consent
from careeros_identity.domain.lifecycle import UserRole, UserStatus
from careeros_identity.domain.user import User
from careeros_identity.domain.value_objects import (
    AuthRef,
    ConsentId,
    ConsentPurpose,
    ConsentScope,
    EmailAddress,
    UserId,
)
from careeros_shared_kernel import ConflictError

_SET_USER = "SELECT set_config('app.current_user_id', %s, true)"
_SET_AUTH_REF = "SELECT set_config('app.current_auth_ref', %s, true)"
_SET_BYPASS = "SELECT set_config('app.rls_bypass', %s, true)"


class PostgresUserRepository:
    """Persists the User aggregate under Postgres RLS.

    Session GUCs (transaction-local via ``set_config(..., true)``):
    - ``app.current_user_id`` — own-row access for get/save
    - ``app.current_auth_ref`` — constrained lookup by external subject
    - ``app.rls_bypass=on`` — admin/test only (not used by normal get/save)
    """

    def __init__(self, connection: Connection[Any]) -> None:
        self._conn = connection
        self._conn.row_factory = dict_row

    def get(self, user_id: UserId) -> User | None:
        with self._conn.transaction():
            self._assume_app_role()
            self._scope_user(user_id)
            return self._load_user(user_id)

    def get_by_auth_ref(self, auth_ref: AuthRef) -> User | None:
        with self._conn.transaction():
            self._assume_app_role()
            self._clear_scope()
            self._conn.execute(_SET_AUTH_REF, (auth_ref.value,))
            row = self._conn.execute(
                """
                SELECT id
                FROM identity.users
                WHERE auth_ref = %s
                """,
                (auth_ref.value,),
            ).fetchone()
            if row is None:
                return None
            user_id = UserId(row["id"])
            self._scope_user(user_id)
            return self._load_user(user_id)

    def save(self, user: User) -> None:
        with self._conn.transaction():
            self._assume_app_role()
            self._scope_user(user.id)
            try:
                self._upsert_user(user)
                self._upsert_consents(user)
            except UniqueViolation as exc:
                raise ConflictError("User persistence conflict") from exc

    def _assume_app_role(self) -> None:
        """Run under careeros_app so FORCE RLS applies (superusers bypass RLS)."""
        self._conn.execute("SET LOCAL ROLE careeros_app")

    def _scope_user(self, user_id: UserId) -> None:
        self._conn.execute(_SET_BYPASS, ("off",))
        self._conn.execute(_SET_AUTH_REF, ("",))
        self._conn.execute(_SET_USER, (str(user_id.value),))

    def _clear_scope(self) -> None:
        self._conn.execute(_SET_BYPASS, ("off",))
        self._conn.execute(_SET_USER, ("",))
        self._conn.execute(_SET_AUTH_REF, ("",))

    def _load_user(self, user_id: UserId) -> User | None:
        user_row = self._conn.execute(
            """
            SELECT id, email, auth_ref, status, role, email_verified, legal_hold,
                   tenant_id, registered_at
            FROM identity.users
            WHERE id = %s
            """,
            (user_id.value,),
        ).fetchone()
        if user_row is None:
            return None

        consent_rows = self._conn.execute(
            """
            SELECT id, purpose, granted_at, withdrawn_at
            FROM identity.consents
            WHERE user_id = %s
            ORDER BY granted_at ASC
            """,
            (user_id.value,),
        ).fetchall()

        consents = [
            Consent(
                ConsentId(row["id"]),
                ConsentScope(ConsentPurpose(row["purpose"])),
                granted_at=_as_utc(row["granted_at"]),
                withdrawn_at=_as_utc(row["withdrawn_at"])
                if row["withdrawn_at"] is not None
                else None,
            )
            for row in consent_rows
        ]

        return User(
            UserId(user_row["id"]),
            EmailAddress(user_row["email"]),
            AuthRef(user_row["auth_ref"]),
            status=UserStatus(user_row["status"]),
            role=UserRole(user_row["role"]),
            email_verified=bool(user_row["email_verified"]),
            legal_hold=bool(user_row["legal_hold"]),
            consents=consents,
            tenant_id=user_row["tenant_id"],
            registered_at=_as_utc(user_row["registered_at"]),
        )

    def _upsert_user(self, user: User) -> None:
        self._conn.execute(
            """
            INSERT INTO identity.users (
                id, email, auth_ref, status, role, email_verified, legal_hold,
                tenant_id, registered_at
            ) VALUES (
                %(id)s, %(email)s, %(auth_ref)s, %(status)s, %(role)s,
                %(email_verified)s, %(legal_hold)s, %(tenant_id)s, %(registered_at)s
            )
            ON CONFLICT (id) DO UPDATE SET
                email = EXCLUDED.email,
                auth_ref = EXCLUDED.auth_ref,
                status = EXCLUDED.status,
                role = EXCLUDED.role,
                email_verified = EXCLUDED.email_verified,
                legal_hold = EXCLUDED.legal_hold,
                tenant_id = EXCLUDED.tenant_id,
                registered_at = EXCLUDED.registered_at
            """,
            {
                "id": user.id.value,
                "email": str(user.email),
                "auth_ref": str(user.auth_ref),
                "status": user.status.value,
                "role": user.role.value,
                "email_verified": user.email_verified,
                "legal_hold": user.legal_hold,
                "tenant_id": user.tenant_id,
                "registered_at": user.registered_at,
            },
        )

    def _upsert_consents(self, user: User) -> None:
        for consent in user.consents:
            self._conn.execute(
                """
                INSERT INTO identity.consents (
                    id, user_id, purpose, granted_at, withdrawn_at
                ) VALUES (
                    %(id)s, %(user_id)s, %(purpose)s, %(granted_at)s, %(withdrawn_at)s
                )
                ON CONFLICT (id) DO UPDATE SET
                    purpose = EXCLUDED.purpose,
                    granted_at = EXCLUDED.granted_at,
                    withdrawn_at = EXCLUDED.withdrawn_at
                """,
                {
                    "id": consent.id.value,
                    "user_id": user.id.value,
                    "purpose": consent.purpose.value,
                    "granted_at": consent.granted_at,
                    "withdrawn_at": consent.withdrawn_at,
                },
            )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value
