from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from careeros_application_tracking.domain.application import Application, ApplicationStatus


@runtime_checkable
class ApplicationRepository(Protocol):
    def get(self, application_id: UUID, user_id: UUID) -> Application | None: ...

    def find_active(self, user_id: UUID, opportunity_id: UUID) -> Application | None: ...

    def save(self, application: Application) -> None: ...

    def list_for_user(
        self,
        user_id: UUID,
        *,
        status: ApplicationStatus | None = None,
    ) -> list[Application]: ...
