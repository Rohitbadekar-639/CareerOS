"""Notification domain tests."""

from uuid import uuid4

from careeros_notifications.domain.notification import Notification, NotificationKind


def test_create_and_mark_read() -> None:
    note = Notification.create(
        user_id=uuid4(),
        kind=NotificationKind.DAILY_DIGEST,
        title="Digest",
        body="Hello",
    )
    assert note.status.value == "sent"
    read = note.mark_read()
    assert read.status.value == "read"
    assert read.read_at is not None
