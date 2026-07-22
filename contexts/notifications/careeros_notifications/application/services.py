"""Notification application services."""

from __future__ import annotations

from uuid import UUID

from careeros_notifications.domain.notification import Notification, NotificationKind
from careeros_notifications.ports.repositories import NotificationRepository
from careeros_shared_kernel import NotFoundError


class PublishNotification:
    def __init__(self, *, repository: NotificationRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        user_id: UUID,
        kind: NotificationKind,
        title: str,
        body: str,
        payload: dict[str, object] | None = None,
    ) -> Notification:
        note = Notification.create(
            user_id=user_id,
            kind=kind,
            title=title,
            body=body,
            payload=payload,
        )
        self._repository.save(note)
        return note


class ListNotifications:
    def __init__(self, *, repository: NotificationRepository) -> None:
        self._repository = repository

    def execute(self, user_id: UUID, *, limit: int = 50) -> list[Notification]:
        return self._repository.list_for_user(user_id, limit=limit)


class MarkNotificationRead:
    def __init__(self, *, repository: NotificationRepository) -> None:
        self._repository = repository

    def execute(self, *, user_id: UUID, notification_id: UUID) -> Notification:
        note = self._repository.get(notification_id, user_id)
        if note is None:
            raise NotFoundError("Notification not found")
        updated = note.mark_read()
        self._repository.save(updated)
        return updated
