"""Application aggregate — one pursuit per user x opportunity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from careeros_shared_kernel import ConflictError, ValidationError


class ApplicationStatus(StrEnum):
    INTERESTED = "interested"  # saved
    PREPARED = "prepared"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    CLOSED = "closed"


_ACTIVE = frozenset(
    {
        ApplicationStatus.INTERESTED,
        ApplicationStatus.PREPARED,
        ApplicationStatus.APPLIED,
        ApplicationStatus.INTERVIEWING,
        ApplicationStatus.OFFER,
    }
)

_TRANSITIONS: dict[ApplicationStatus, frozenset[ApplicationStatus]] = {
    ApplicationStatus.INTERESTED: frozenset(
        {
            ApplicationStatus.PREPARED,
            ApplicationStatus.APPLIED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.PREPARED: frozenset(
        {
            ApplicationStatus.APPLIED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.APPLIED: frozenset(
        {
            ApplicationStatus.INTERVIEWING,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
            ApplicationStatus.OFFER,
        }
    ),
    ApplicationStatus.INTERVIEWING: frozenset(
        {
            ApplicationStatus.OFFER,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.OFFER: frozenset(
        {
            ApplicationStatus.CLOSED,
            ApplicationStatus.WITHDRAWN,
            ApplicationStatus.REJECTED,
        }
    ),
    ApplicationStatus.REJECTED: frozenset({ApplicationStatus.CLOSED}),
    ApplicationStatus.WITHDRAWN: frozenset({ApplicationStatus.CLOSED}),
    ApplicationStatus.CLOSED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class Application:
    id: UUID
    user_id: UUID
    opportunity_id: UUID
    status: ApplicationStatus
    notes: str
    cover_letter_draft: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def save_interest(
        cls,
        *,
        user_id: UUID,
        opportunity_id: UUID,
        application_id: UUID | None = None,
    ) -> Application:
        now = datetime.now(UTC)
        return cls(
            id=application_id or uuid4(),
            user_id=user_id,
            opportunity_id=opportunity_id,
            status=ApplicationStatus.INTERESTED,
            notes="",
            cover_letter_draft=None,
            created_at=now,
            updated_at=now,
        )

    def transition_to(self, status: ApplicationStatus) -> Application:
        allowed = _TRANSITIONS.get(self.status, frozenset())
        if status not in allowed:
            raise ConflictError(f"Cannot move from {self.status.value} to {status.value}")
        return Application(
            id=self.id,
            user_id=self.user_id,
            opportunity_id=self.opportunity_id,
            status=status,
            notes=self.notes,
            cover_letter_draft=self.cover_letter_draft,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    def mark_applied(self) -> Application:
        if self.status is ApplicationStatus.APPLIED:
            return self
        if self.status in (ApplicationStatus.INTERESTED, ApplicationStatus.PREPARED):
            return self.transition_to(ApplicationStatus.APPLIED)
        raise ConflictError(f"Cannot apply from status {self.status.value}")

    def with_cover_letter_draft(self, draft: str) -> Application:
        text = draft.strip()
        if not text:
            raise ValidationError("Cover letter draft must not be empty")
        return Application(
            id=self.id,
            user_id=self.user_id,
            opportunity_id=self.opportunity_id,
            status=self.status
            if self.status is not ApplicationStatus.INTERESTED
            else ApplicationStatus.PREPARED,
            notes=self.notes,
            cover_letter_draft=text,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    @property
    def is_active(self) -> bool:
        return self.status in _ACTIVE
