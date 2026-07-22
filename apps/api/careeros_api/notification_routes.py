"""Notification HTTP routes."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection
from pydantic import BaseModel

from careeros_api.deps import get_db_connection, get_user_repository, require_verified_identity
from careeros_identity.application import EnsureUserFromIdentity
from careeros_identity.ports.auth_provider import VerifiedIdentity
from careeros_identity.ports.user_repository import UserRepository
from careeros_notifications.application import ListNotifications, MarkNotificationRead
from careeros_notifications.infrastructure import PostgresNotificationRepository
from careeros_shared_kernel import NotFoundError

notifications_router = APIRouter(prefix="/v1", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: UUID
    kind: str
    title: str
    body: str
    status: str
    created_at: str
    read_at: str | None = None


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]


def _require_user(identity: VerifiedIdentity, users: UserRepository) -> UUID:
    return EnsureUserFromIdentity(users).execute(identity).id.value


@notifications_router.get(
    "/me/notifications",
    response_model=NotificationListResponse,
    operation_id="listNotifications",
)
def list_notifications(
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
) -> NotificationListResponse:
    user_id = _require_user(identity, users)
    notes = ListNotifications(repository=PostgresNotificationRepository(conn)).execute(user_id)
    return NotificationListResponse(
        items=[
            NotificationResponse(
                id=n.id,
                kind=n.kind.value,
                title=n.title,
                body=n.body,
                status=n.status.value,
                created_at=n.created_at.isoformat(),
                read_at=n.read_at.isoformat() if n.read_at else None,
            )
            for n in notes
        ]
    )


@notifications_router.post(
    "/me/notifications/{notification_id}/read",
    response_model=NotificationResponse,
    operation_id="markNotificationRead",
)
def mark_read(
    notification_id: UUID,
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
) -> NotificationResponse:
    user_id = _require_user(identity, users)
    try:
        note = MarkNotificationRead(repository=PostgresNotificationRepository(conn)).execute(
            user_id=user_id,
            notification_id=notification_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return NotificationResponse(
        id=note.id,
        kind=note.kind.value,
        title=note.title,
        body=note.body,
        status=note.status.value,
        created_at=note.created_at.isoformat(),
        read_at=note.read_at.isoformat() if note.read_at else None,
    )
