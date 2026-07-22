"""Application tracking HTTP routes — save, apply, tracker."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import Connection
from pydantic import BaseModel

from careeros_api.deps import (
    get_db_connection,
    get_user_repository,
    require_verified_identity,
)
from careeros_application_tracking.application import (
    ListApplications,
    MarkApplied,
    SaveOpportunity,
    UpdateApplicationStatus,
)
from careeros_application_tracking.domain.application import ApplicationStatus
from careeros_application_tracking.infrastructure import PostgresApplicationRepository
from careeros_identity.application import EnsureUserFromIdentity
from careeros_identity.ports.auth_provider import VerifiedIdentity
from careeros_identity.ports.user_repository import UserRepository
from careeros_opportunity.domain.value_objects import OpportunityId
from careeros_opportunity.infrastructure import PostgresOpportunityRepository
from careeros_shared_kernel import ConflictError, NotFoundError

applications_router = APIRouter(prefix="/v1", tags=["applications"])


class ApplicationResponse(BaseModel):
    id: UUID
    opportunity_id: UUID
    status: str
    notes: str
    cover_letter_draft: str | None
    created_at: str
    updated_at: str
    title: str | None = None
    company: str | None = None
    apply_url: str | None = None
    location: str | None = None
    is_remote: bool | None = None


class ApplicationListResponse(BaseModel):
    items: list[ApplicationResponse]


class StatusUpdateRequest(BaseModel):
    status: ApplicationStatus


def _require_user(identity: VerifiedIdentity, users: UserRepository) -> UUID:
    return EnsureUserFromIdentity(users).execute(identity).id.value


def _app_response(app: Any, opp: Any | None = None) -> ApplicationResponse:
    return ApplicationResponse(
        id=app.id,
        opportunity_id=app.opportunity_id,
        status=app.status.value,
        notes=app.notes,
        cover_letter_draft=app.cover_letter_draft,
        created_at=app.created_at.isoformat(),
        updated_at=app.updated_at.isoformat(),
        title=opp.title if opp else None,
        company=str(opp.company) if opp else None,
        apply_url=opp.apply_url if opp else None,
        location=opp.location if opp else None,
        is_remote=opp.is_remote if opp else None,
    )


@applications_router.post(
    "/opportunities/{opportunity_id}/save",
    response_model=ApplicationResponse,
    summary="Save / mark interested",
    operation_id="saveOpportunity",
)
def save_opportunity(
    opportunity_id: UUID,
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
) -> ApplicationResponse:
    user_id = _require_user(identity, users)
    opp = PostgresOpportunityRepository(conn).get(OpportunityId(opportunity_id))
    if opp is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    app = SaveOpportunity(repository=PostgresApplicationRepository(conn)).execute(
        user_id=user_id,
        opportunity_id=opportunity_id,
    )
    return _app_response(app, opp)


@applications_router.post(
    "/opportunities/{opportunity_id}/apply",
    response_model=ApplicationResponse,
    summary="Confirm applied (user-confirmed; no auto-submit)",
    operation_id="markOpportunityApplied",
)
def mark_applied(
    opportunity_id: UUID,
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
) -> ApplicationResponse:
    user_id = _require_user(identity, users)
    opp = PostgresOpportunityRepository(conn).get(OpportunityId(opportunity_id))
    if opp is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    try:
        app = MarkApplied(repository=PostgresApplicationRepository(conn)).execute(
            user_id=user_id,
            opportunity_id=opportunity_id,
        )
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _app_response(app, opp)


@applications_router.get(
    "/me/applications",
    response_model=ApplicationListResponse,
    summary="Application tracker",
    operation_id="listApplications",
)
def list_applications(
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
) -> ApplicationListResponse:
    user_id = _require_user(identity, users)
    status = None
    if status_filter:
        try:
            status = ApplicationStatus(status_filter)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid status") from exc
    apps = ListApplications(repository=PostgresApplicationRepository(conn)).execute(
        user_id,
        status=status,
    )
    opp_repo = PostgresOpportunityRepository(conn)
    items: list[ApplicationResponse] = []
    for app in apps:
        opp = opp_repo.get(OpportunityId(app.opportunity_id))
        items.append(_app_response(app, opp))
    return ApplicationListResponse(items=items)


@applications_router.patch(
    "/me/applications/{application_id}",
    response_model=ApplicationResponse,
    summary="Update application pipeline status",
    operation_id="updateApplicationStatus",
)
def patch_application(
    application_id: UUID,
    body: StatusUpdateRequest,
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
) -> ApplicationResponse:
    user_id = _require_user(identity, users)
    try:
        app = UpdateApplicationStatus(repository=PostgresApplicationRepository(conn)).execute(
            user_id=user_id,
            application_id=application_id,
            status=body.status,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    opp = PostgresOpportunityRepository(conn).get(OpportunityId(app.opportunity_id))
    return _app_response(app, opp)
