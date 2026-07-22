"""Application tracking use cases."""

from __future__ import annotations

from uuid import UUID

from careeros_application_tracking.domain.application import Application, ApplicationStatus
from careeros_application_tracking.ports.repositories import ApplicationRepository
from careeros_shared_kernel import NotFoundError


class SaveOpportunity:
    def __init__(self, *, repository: ApplicationRepository) -> None:
        self._repository = repository

    def execute(self, *, user_id: UUID, opportunity_id: UUID) -> Application:
        existing = self._repository.find_active(user_id, opportunity_id)
        if existing is not None:
            return existing
        app = Application.save_interest(user_id=user_id, opportunity_id=opportunity_id)
        self._repository.save(app)
        return app


class MarkApplied:
    def __init__(self, *, repository: ApplicationRepository) -> None:
        self._repository = repository

    def execute(self, *, user_id: UUID, opportunity_id: UUID) -> Application:
        existing = self._repository.find_active(user_id, opportunity_id)
        if existing is None:
            existing = Application.save_interest(user_id=user_id, opportunity_id=opportunity_id)
        updated = existing.mark_applied()
        self._repository.save(updated)
        return updated


class UpdateApplicationStatus:
    def __init__(self, *, repository: ApplicationRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
        status: ApplicationStatus,
    ) -> Application:
        app = self._repository.get(application_id, user_id)
        if app is None:
            raise NotFoundError("Application not found")
        updated = app.transition_to(status)
        self._repository.save(updated)
        return updated


class AttachCoverLetterDraft:
    def __init__(self, *, repository: ApplicationRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        user_id: UUID,
        opportunity_id: UUID,
        draft: str,
    ) -> Application:
        existing = self._repository.find_active(user_id, opportunity_id)
        if existing is None:
            existing = Application.save_interest(user_id=user_id, opportunity_id=opportunity_id)
        updated = existing.with_cover_letter_draft(draft)
        self._repository.save(updated)
        return updated


class ListApplications:
    def __init__(self, *, repository: ApplicationRepository) -> None:
        self._repository = repository

    def execute(
        self,
        user_id: UUID,
        *,
        status: ApplicationStatus | None = None,
    ) -> list[Application]:
        return self._repository.list_for_user(user_id, status=status)
