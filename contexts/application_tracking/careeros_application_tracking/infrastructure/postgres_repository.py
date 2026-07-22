"""Postgres ApplicationRepository with RLS by user_id."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from psycopg import Connection
from psycopg.rows import dict_row

from careeros_application_tracking.domain.application import Application, ApplicationStatus

_SET_USER = "SELECT set_config('app.current_user_id', %s, true)"
_SET_BYPASS = "SELECT set_config('app.rls_bypass', %s, true)"


class PostgresApplicationRepository:
    def __init__(self, connection: Connection[Any]) -> None:
        self._conn = connection
        self._conn.row_factory = dict_row

    def get(self, application_id: UUID, user_id: UUID) -> Application | None:
        with self._conn.transaction():
            self._scope(user_id)
            row = self._conn.execute(
                "SELECT * FROM application_tracking.applications WHERE id = %s",
                (application_id,),
            ).fetchone()
            return self._from_row(row) if row else None

    def find_active(self, user_id: UUID, opportunity_id: UUID) -> Application | None:
        with self._conn.transaction():
            self._scope(user_id)
            row = self._conn.execute(
                """
                SELECT * FROM application_tracking.applications
                WHERE user_id = %s
                  AND opportunity_id = %s
                  AND status NOT IN ('closed', 'rejected', 'withdrawn')
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (user_id, opportunity_id),
            ).fetchone()
            return self._from_row(row) if row else None

    def save(self, application: Application) -> None:
        with self._conn.transaction():
            self._scope(application.user_id)
            self._conn.execute(
                """
                INSERT INTO application_tracking.applications (
                    id, user_id, opportunity_id, status, notes, cover_letter_draft,
                    created_at, updated_at
                ) VALUES (
                    %(id)s, %(user_id)s, %(opportunity_id)s, %(status)s, %(notes)s,
                    %(cover_letter_draft)s, %(created_at)s, %(updated_at)s
                )
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    notes = EXCLUDED.notes,
                    cover_letter_draft = EXCLUDED.cover_letter_draft,
                    updated_at = EXCLUDED.updated_at
                """,
                {
                    "id": application.id,
                    "user_id": application.user_id,
                    "opportunity_id": application.opportunity_id,
                    "status": application.status.value,
                    "notes": application.notes,
                    "cover_letter_draft": application.cover_letter_draft,
                    "created_at": application.created_at,
                    "updated_at": application.updated_at,
                },
            )

    def list_for_user(
        self,
        user_id: UUID,
        *,
        status: ApplicationStatus | None = None,
    ) -> list[Application]:
        with self._conn.transaction():
            self._scope(user_id)
            if status is None:
                rows = self._conn.execute(
                    """
                    SELECT * FROM application_tracking.applications
                    WHERE user_id = %s
                    ORDER BY updated_at DESC
                    """,
                    (user_id,),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    """
                    SELECT * FROM application_tracking.applications
                    WHERE user_id = %s AND status = %s
                    ORDER BY updated_at DESC
                    """,
                    (user_id, status.value),
                ).fetchall()
            return [self._from_row(row) for row in rows]

    def _assume(self) -> None:
        self._conn.execute("SET LOCAL ROLE careeros_app")

    def _scope(self, user_id: UUID) -> None:
        self._assume()
        self._conn.execute(_SET_BYPASS, ("off",))
        self._conn.execute(_SET_USER, (str(user_id),))

    def _from_row(self, row: dict[str, Any]) -> Application:
        return Application(
            id=row["id"],
            user_id=row["user_id"],
            opportunity_id=row["opportunity_id"],
            status=ApplicationStatus(row["status"]),
            notes=row.get("notes") or "",
            cover_letter_draft=row.get("cover_letter_draft"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
