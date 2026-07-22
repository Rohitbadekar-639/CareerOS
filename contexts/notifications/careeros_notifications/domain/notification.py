"""Notification aggregate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class NotificationKind(StrEnum):
    STRONG_MATCH = "strong_match"
    DAILY_DIGEST = "daily_digest"
    HUNTER_PREP = "hunter_prep"


class NotificationStatus(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    READ = "read"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class Notification:
    id: UUID
    user_id: UUID
    kind: NotificationKind
    title: str
    body: str
    payload: dict[str, object]
    status: NotificationStatus
    created_at: datetime
    read_at: datetime | None = None

    @classmethod
    def create(
        cls,
        *,
        user_id: UUID,
        kind: NotificationKind,
        title: str,
        body: str,
        payload: dict[str, object] | None = None,
    ) -> Notification:
        return cls(
            id=uuid4(),
            user_id=user_id,
            kind=kind,
            title=title.strip(),
            body=body.strip(),
            payload=payload or {},
            status=NotificationStatus.SENT,
            created_at=datetime.now(UTC),
        )

    def mark_read(self) -> Notification:
        return Notification(
            id=self.id,
            user_id=self.user_id,
            kind=self.kind,
            title=self.title,
            body=self.body,
            payload=self.payload,
            status=NotificationStatus.READ,
            created_at=self.created_at,
            read_at=datetime.now(UTC),
        )
