"""Postgres NotificationRepository with RLS."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from psycopg import Connection
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from careeros_notifications.domain.notification import (
    Notification,
    NotificationKind,
    NotificationStatus,
)

_SET_USER = "SELECT set_config('app.current_user_id', %s, true)"
_SET_BYPASS = "SELECT set_config('app.rls_bypass', %s, true)"


class PostgresNotificationRepository:
    def __init__(self, connection: Connection[Any]) -> None:
        self._conn = connection
        self._conn.row_factory = dict_row

    def save(self, notification: Notification) -> None:
        with self._conn.transaction():
            self._scope(notification.user_id)
            self._conn.execute(
                """
                INSERT INTO notifications.notifications (
                    id, user_id, kind, title, body, payload, status, created_at, read_at
                ) VALUES (
                    %(id)s, %(user_id)s, %(kind)s, %(title)s, %(body)s, %(payload)s,
                    %(status)s, %(created_at)s, %(read_at)s
                )
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    read_at = EXCLUDED.read_at
                """,
                {
                    "id": notification.id,
                    "user_id": notification.user_id,
                    "kind": notification.kind.value,
                    "title": notification.title,
                    "body": notification.body,
                    "payload": Jsonb(notification.payload),
                    "status": notification.status.value,
                    "created_at": notification.created_at,
                    "read_at": notification.read_at,
                },
            )

    def list_for_user(self, user_id: UUID, *, limit: int = 50) -> list[Notification]:
        with self._conn.transaction():
            self._scope(user_id)
            rows = self._conn.execute(
                """
                SELECT * FROM notifications.notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            ).fetchall()
            return [self._from_row(row) for row in rows]

    def get(self, notification_id: UUID, user_id: UUID) -> Notification | None:
        with self._conn.transaction():
            self._scope(user_id)
            row = self._conn.execute(
                "SELECT * FROM notifications.notifications WHERE id = %s",
                (notification_id,),
            ).fetchone()
            return self._from_row(row) if row else None

    def _scope(self, user_id: UUID) -> None:
        self._conn.execute("SET LOCAL ROLE careeros_app")
        self._conn.execute(_SET_BYPASS, ("off",))
        self._conn.execute(_SET_USER, (str(user_id),))

    def _from_row(self, row: dict[str, Any]) -> Notification:
        payload = row.get("payload") or {}
        if isinstance(payload, str):
            payload = json.loads(payload)
        return Notification(
            id=row["id"],
            user_id=row["user_id"],
            kind=NotificationKind(row["kind"]),
            title=row["title"],
            body=row["body"],
            payload=dict(payload) if isinstance(payload, dict) else {},
            status=NotificationStatus(row["status"]),
            created_at=row["created_at"],
            read_at=row.get("read_at"),
        )
