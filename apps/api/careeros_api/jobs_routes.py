"""Job Intelligence HTTP routes — thin translation only."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from psycopg import Connection
from pydantic import BaseModel, Field

from careeros_api.deps import (
    get_app_settings,
    get_db_connection,
    get_user_repository,
    require_verified_identity,
)
from careeros_application_tracking.infrastructure import PostgresApplicationRepository
from careeros_identity.application import EnsureUserFromIdentity
from careeros_identity.ports.auth_provider import VerifiedIdentity
from careeros_identity.ports.user_repository import UserRepository
from careeros_matching.application import (
    CareerCopilot,
    GetSeekerCriteria,
    ListRecommendations,
    RecomputeMatches,
    UpsertSeekerCriteria,
)
from careeros_matching.application.copilot import OpportunityBrief
from careeros_matching.domain.ranking import OpportunitySnapshot
from careeros_matching.domain.seeker_criteria import RemotePreference, SeekerCriteria
from careeros_matching.infrastructure import (
    PostgresMatchRepository,
    PostgresSeekerCriteriaRepository,
)
from careeros_opportunity.application import SearchOpportunities
from careeros_opportunity.domain.value_objects import OpportunityId, SourceKind
from careeros_opportunity.infrastructure import PostgresOpportunityRepository
from careeros_opportunity.ports import OpportunitySearchFilter
from careeros_platform.settings import Settings
from careeros_shared_kernel import ValidationError

jobs_router = APIRouter(prefix="/v1", tags=["jobs"])


class OpportunityResponse(BaseModel):
    id: UUID
    title: str
    company: str
    location: str | None
    is_remote: bool
    apply_url: str
    source_kind: str
    skills: list[str]
    posted_at: str | None = None
    updated_at: str
    description_text: str | None = None


class OpportunityDetailResponse(OpportunityResponse):
    description_text: str
    application_status: str | None = None
    match_score: float | None = None


class CopilotResponse(BaseModel):
    match_score: float | None
    why_match: list[str]
    missing_skills: list[str]
    resume_suggestions: list[str]
    model_version: str


class CoverLetterResponse(BaseModel):
    body: str
    grounding_notes: list[str]
    requires_human_review: bool
    model_version: str
    application_id: UUID | None = None


class OpportunityListResponse(BaseModel):
    items: list[OpportunityResponse]


class SeekerCriteriaRequest(BaseModel):
    resume_text: str = ""
    skills: list[str] = Field(default_factory=list)
    years_experience: int | None = None
    preferred_locations: list[str] = Field(default_factory=list)
    salary_expectation_min: int | None = None
    salary_currency: str | None = "INR"
    remote_preference: RemotePreference = RemotePreference.ANY


class SeekerCriteriaResponse(BaseModel):
    resume_text: str
    skills: list[str]
    years_experience: int | None
    preferred_locations: list[str]
    salary_expectation_min: int | None
    salary_currency: str | None
    remote_preference: str


class RecommendationItem(BaseModel):
    opportunity_id: UUID
    title: str
    company: str
    location: str | None
    is_remote: bool
    apply_url: str
    score: float
    reasons: list[str]
    gaps: list[str]
    model_version: str


class RecommendationListResponse(BaseModel):
    items: list[RecommendationItem]


def _require_user(
    identity: VerifiedIdentity,
    users: UserRepository,
) -> UUID:
    return EnsureUserFromIdentity(users).execute(identity).id.value


def _opp_response(opp: Any, *, include_description: bool = False) -> OpportunityResponse:
    return OpportunityResponse(
        id=opp.id.value,
        title=opp.title,
        company=str(opp.company),
        location=opp.location,
        is_remote=opp.is_remote,
        apply_url=opp.apply_url,
        source_kind=opp.provenance.kind.value,
        skills=list(opp.skills),
        posted_at=opp.posted_at.isoformat() if opp.posted_at else None,
        updated_at=opp.updated_at.isoformat(),
        description_text=opp.description_text if include_description else None,
    )


def _snapshot(opp: Any) -> OpportunitySnapshot:
    salary_min = None
    salary_currency = None
    if opp.compensation is not None:
        salary_min = opp.compensation.min_amount
        salary_currency = opp.compensation.currency
    return OpportunitySnapshot(
        opportunity_id=opp.id.value,
        title=opp.title,
        company=str(opp.company),
        location=opp.location,
        is_remote=opp.is_remote,
        description_text=opp.description_text,
        skills=opp.skills,
        salary_min=salary_min,
        salary_currency=salary_currency,
    )


@jobs_router.get(
    "/opportunities",
    response_model=OpportunityListResponse,
    summary="Search active opportunities",
    operation_id="searchOpportunities",
)
def search_opportunities(
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
    q: Annotated[str | None, Query()] = None,
    location: Annotated[str | None, Query()] = None,
    remote_only: Annotated[bool | None, Query()] = None,
    company: Annotated[str | None, Query()] = None,
    source: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> OpportunityListResponse:
    _require_user(identity, users)
    source_kind = None
    if source:
        try:
            source_kind = SourceKind(source.lower())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid source") from exc
    repo = PostgresOpportunityRepository(conn)
    items = SearchOpportunities(repository=repo).execute(
        OpportunitySearchFilter(
            query=q,
            location=location,
            remote_only=remote_only,
            company=company,
            source_kind=source_kind,
            limit=limit,
            offset=offset,
        )
    )
    return OpportunityListResponse(items=[_opp_response(o) for o in items])


@jobs_router.get(
    "/me/criteria",
    response_model=SeekerCriteriaResponse,
    summary="Get seeker ranking criteria",
    operation_id="getSeekerCriteria",
)
def get_criteria(
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
) -> SeekerCriteriaResponse:
    user_id = _require_user(identity, users)
    criteria = GetSeekerCriteria(repository=PostgresSeekerCriteriaRepository(conn)).execute(user_id)
    if criteria is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Criteria not set")
    return SeekerCriteriaResponse(
        resume_text=criteria.resume_text,
        skills=list(criteria.skills),
        years_experience=criteria.years_experience,
        preferred_locations=list(criteria.preferred_locations),
        salary_expectation_min=criteria.salary_expectation_min,
        salary_currency=criteria.salary_currency,
        remote_preference=criteria.remote_preference.value,
    )


@jobs_router.put(
    "/me/criteria",
    response_model=SeekerCriteriaResponse,
    summary="Upsert seeker ranking criteria and recompute matches",
    operation_id="upsertSeekerCriteria",
)
def put_criteria(
    body: SeekerCriteriaRequest,
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> SeekerCriteriaResponse:
    user_id = _require_user(identity, users)
    criteria = SeekerCriteria.create(
        user_id,
        resume_text=body.resume_text,
        skills=body.skills,
        years_experience=body.years_experience,
        preferred_locations=body.preferred_locations,
        salary_expectation_min=body.salary_expectation_min,
        salary_currency=body.salary_currency,
        remote_preference=body.remote_preference,
    )
    criteria_repo = PostgresSeekerCriteriaRepository(conn)
    UpsertSeekerCriteria(repository=criteria_repo).execute(criteria)

    opp_repo = PostgresOpportunityRepository(conn)
    opportunities = [
        _snapshot(o) for o in opp_repo.list_active(limit=settings.opportunity_active_limit)
    ]
    RecomputeMatches(
        criteria_repo=criteria_repo,
        match_repo=PostgresMatchRepository(conn),
    ).execute(user_id, opportunities)

    return SeekerCriteriaResponse(
        resume_text=criteria.resume_text,
        skills=list(criteria.skills),
        years_experience=criteria.years_experience,
        preferred_locations=list(criteria.preferred_locations),
        salary_expectation_min=criteria.salary_expectation_min,
        salary_currency=criteria.salary_currency,
        remote_preference=criteria.remote_preference.value,
    )


@jobs_router.get(
    "/me/recommendations",
    response_model=RecommendationListResponse,
    summary="Highly relevant job recommendations",
    operation_id="listRecommendations",
)
def list_recommendations(
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> RecommendationListResponse:
    user_id = _require_user(identity, users)
    matches = ListRecommendations(match_repo=PostgresMatchRepository(conn)).execute(
        user_id,
        min_score=settings.match_min_score,
        limit=limit,
    )
    opp_repo = PostgresOpportunityRepository(conn)
    items: list[RecommendationItem] = []
    for match in matches:
        opp = opp_repo.get(OpportunityId(match.opportunity_id))
        if opp is None:
            continue
        items.append(
            RecommendationItem(
                opportunity_id=match.opportunity_id,
                title=opp.title,
                company=str(opp.company),
                location=opp.location,
                is_remote=opp.is_remote,
                apply_url=opp.apply_url,
                score=match.score,
                reasons=list(match.reasons),
                gaps=list(match.gaps),
                model_version=match.model_version,
            )
        )
    return RecommendationListResponse(items=items)


@jobs_router.get(
    "/opportunities/{opportunity_id}",
    response_model=OpportunityDetailResponse,
    summary="Opportunity detail",
    operation_id="getOpportunity",
)
def get_opportunity(
    opportunity_id: UUID,
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
) -> OpportunityDetailResponse:
    user_id = _require_user(identity, users)
    opp = PostgresOpportunityRepository(conn).get(OpportunityId(opportunity_id))
    if opp is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    match = PostgresMatchRepository(conn).get_for_opportunity(user_id, opportunity_id)
    application = PostgresApplicationRepository(conn).find_active(user_id, opportunity_id)
    base = _opp_response(opp, include_description=True)
    return OpportunityDetailResponse(
        **base.model_dump(),
        description_text=opp.description_text,
        application_status=application.status.value if application else None,
        match_score=match.score if match else None,
    )


@jobs_router.get(
    "/opportunities/{opportunity_id}/copilot",
    response_model=CopilotResponse,
    summary="Career Copilot advice for an opportunity",
    operation_id="getOpportunityCopilot",
)
def get_copilot(
    opportunity_id: UUID,
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
) -> CopilotResponse:
    user_id = _require_user(identity, users)
    opp = PostgresOpportunityRepository(conn).get(OpportunityId(opportunity_id))
    if opp is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    criteria = GetSeekerCriteria(repository=PostgresSeekerCriteriaRepository(conn)).execute(user_id)
    match = PostgresMatchRepository(conn).get_for_opportunity(user_id, opportunity_id)
    advice = CareerCopilot().advise(
        criteria=criteria,
        match=match,
        opportunity=OpportunityBrief(
            title=opp.title,
            company=str(opp.company),
            location=opp.location,
            is_remote=opp.is_remote,
            description_text=opp.description_text,
            skills=opp.skills,
        ),
    )
    return CopilotResponse(
        match_score=advice.match_score,
        why_match=list(advice.why_match),
        missing_skills=list(advice.missing_skills),
        resume_suggestions=list(advice.resume_suggestions),
        model_version=advice.model_version,
    )


@jobs_router.post(
    "/opportunities/{opportunity_id}/cover-letter",
    response_model=CoverLetterResponse,
    summary="Generate a grounded cover-letter draft (human review required)",
    operation_id="generateCoverLetter",
)
def generate_cover_letter(
    opportunity_id: UUID,
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
) -> CoverLetterResponse:
    user_id = _require_user(identity, users)
    opp = PostgresOpportunityRepository(conn).get(OpportunityId(opportunity_id))
    if opp is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    criteria = GetSeekerCriteria(repository=PostgresSeekerCriteriaRepository(conn)).execute(user_id)
    if criteria is None:
        raise HTTPException(
            status_code=400,
            detail="Save ranking criteria before generating a cover letter",
        )
    match = PostgresMatchRepository(conn).get_for_opportunity(user_id, opportunity_id)
    draft = CareerCopilot().draft_cover_letter(
        criteria=criteria,
        opportunity=OpportunityBrief(
            title=opp.title,
            company=str(opp.company),
            location=opp.location,
            is_remote=opp.is_remote,
            description_text=opp.description_text,
            skills=opp.skills,
        ),
        match=match,
    )
    from careeros_application_tracking.application import AttachCoverLetterDraft

    try:
        app = AttachCoverLetterDraft(repository=PostgresApplicationRepository(conn)).execute(
            user_id=user_id,
            opportunity_id=opportunity_id,
            draft=draft.body,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CoverLetterResponse(
        body=draft.body,
        grounding_notes=list(draft.grounding_notes),
        requires_human_review=draft.requires_human_review,
        model_version=draft.model_version,
        application_id=app.id,
    )
