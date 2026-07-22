from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from careeros_notifications.domain.notification import Notification


@runtime_checkable
class NotificationRepository(Protocol):
    def save(self, notification: Notification) -> None: ...

    def list_for_user(self, user_id: UUID, *, limit: int = 50) -> list[Notification]: ...

    def get(self, notification_id: UUID, user_id: UUID) -> Notification | None: ...
