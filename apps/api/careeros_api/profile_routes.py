"""Profile intelligence HTTP routes."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection
from pydantic import BaseModel, Field

from careeros_api.deps import (
    get_app_settings,
    get_db_connection,
    get_user_repository,
    require_verified_identity,
)
from careeros_api.profile_sync import profile_to_snapshot
from careeros_identity.application import EnsureUserFromIdentity
from careeros_identity.ports.auth_provider import VerifiedIdentity
from careeros_identity.ports.user_repository import UserRepository
from careeros_matching.application import RecomputeMatches, sync_snapshot_to_matching
from careeros_matching.domain.ranking import OpportunitySnapshot
from careeros_matching.infrastructure import (
    PostgresMatchRepository,
    PostgresSeekerCriteriaRepository,
)
from careeros_opportunity.infrastructure import PostgresOpportunityRepository
from careeros_platform.settings import Settings
from careeros_profile.application import (
    EnrichFromGitHub,
    EnrichFromPortfolio,
    GetOrCreateProfile,
    IngestLinkedInText,
    IngestResumeText,
    UpsertProfilePreferences,
)
from careeros_profile.infrastructure import (
    HeuristicResumeParser,
    HttpGitHubAnalyzer,
    HttpPortfolioFetcher,
    PostgresProfileRepository,
)
from careeros_shared_kernel import ValidationError

profile_router = APIRouter(prefix="/v1", tags=["profile"])


class ExperienceOut(BaseModel):
    title: str
    company: str
    start_year: int | None = None
    end_year: int | None = None
    summary: str = ""


class ProfileResponse(BaseModel):
    version: int
    headline: str
    summary: str
    resume_text: str
    linkedin_text: str
    skills: list[str]
    experiences: list[ExperienceOut]
    years_experience: int | None
    preferred_locations: list[str]
    salary_expectation_min: int | None
    salary_currency: str | None
    remote_preference: str
    github_username: str | None
    linkedin_url: str | None
    portfolio_url: str | None
    github_summary: str
    portfolio_summary: str


class ProfilePreferencesRequest(BaseModel):
    headline: str = ""
    preferred_locations: list[str] = Field(default_factory=list)
    salary_expectation_min: int | None = None
    salary_currency: str | None = "INR"
    remote_preference: str = "any"
    github_username: str | None = None
    linkedin_url: str | None = None
    portfolio_url: str | None = None


class TextBody(BaseModel):
    text: str


class UsernameBody(BaseModel):
    username: str


class UrlBody(BaseModel):
    url: str


def _require_user(identity: VerifiedIdentity, users: UserRepository) -> UUID:
    return EnsureUserFromIdentity(users).execute(identity).id.value


def _response(profile: Any) -> ProfileResponse:
    return ProfileResponse(
        version=profile.version,
        headline=profile.headline,
        summary=profile.summary,
        resume_text=profile.resume_text,
        linkedin_text=profile.linkedin_text,
        skills=list(profile.skills),
        experiences=[
            ExperienceOut(
                title=e.title,
                company=e.company,
                start_year=e.start_year,
                end_year=e.end_year,
                summary=e.summary,
            )
            for e in profile.experiences
        ],
        years_experience=profile.years_experience,
        preferred_locations=list(profile.preferred_locations),
        salary_expectation_min=profile.salary_expectation_min,
        salary_currency=profile.salary_currency,
        remote_preference=profile.remote_preference,
        github_username=profile.links.github_username,
        linkedin_url=profile.links.linkedin_url,
        portfolio_url=profile.links.portfolio_url,
        github_summary=profile.github_summary,
        portfolio_summary=profile.portfolio_summary,
    )


def _sync_and_rematch(conn: Connection[Any], profile: Any, settings: Settings) -> None:
    criteria_repo = PostgresSeekerCriteriaRepository(conn)
    sync_snapshot_to_matching(profile_to_snapshot(profile), criteria_repo=criteria_repo)
    opp_repo = PostgresOpportunityRepository(conn)
    snapshots = []
    for opp in opp_repo.list_active(limit=settings.opportunity_active_limit):
        salary_min = opp.compensation.min_amount if opp.compensation else None
        salary_currency = opp.compensation.currency if opp.compensation else None
        snapshots.append(
            OpportunitySnapshot(
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
        )
    RecomputeMatches(
        criteria_repo=criteria_repo,
        match_repo=PostgresMatchRepository(conn),
    ).execute(profile.user_id, snapshots)


@profile_router.get("/me/profile", response_model=ProfileResponse, operation_id="getProfile")
def get_profile(
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
) -> ProfileResponse:
    user_id = _require_user(identity, users)
    profile = GetOrCreateProfile(repository=PostgresProfileRepository(conn)).execute(user_id)
    return _response(profile)


@profile_router.put("/me/profile", response_model=ProfileResponse, operation_id="upsertProfile")
def put_profile(
    body: ProfilePreferencesRequest,
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> ProfileResponse:
    user_id = _require_user(identity, users)
    profile = UpsertProfilePreferences(repository=PostgresProfileRepository(conn)).execute(
        user_id,
        headline=body.headline,
        preferred_locations=body.preferred_locations,
        salary_expectation_min=body.salary_expectation_min,
        salary_currency=body.salary_currency,
        remote_preference=body.remote_preference,
        github_username=body.github_username,
        linkedin_url=body.linkedin_url,
        portfolio_url=body.portfolio_url,
    )
    _sync_and_rematch(conn, profile, settings)
    return _response(profile)


@profile_router.post(
    "/me/profile/resume",
    response_model=ProfileResponse,
    operation_id="ingestResumeText",
)
def ingest_resume(
    body: TextBody,
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> ProfileResponse:
    user_id = _require_user(identity, users)
    try:
        profile = IngestResumeText(
            repository=PostgresProfileRepository(conn),
            parser=HeuristicResumeParser(),
        ).execute(user_id, body.text)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _sync_and_rematch(conn, profile, settings)
    return _response(profile)


@profile_router.post(
    "/me/profile/linkedin",
    response_model=ProfileResponse,
    operation_id="ingestLinkedInText",
)
def ingest_linkedin(
    body: TextBody,
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> ProfileResponse:
    user_id = _require_user(identity, users)
    try:
        profile = IngestLinkedInText(repository=PostgresProfileRepository(conn)).execute(
            user_id,
            body.text,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _sync_and_rematch(conn, profile, settings)
    return _response(profile)


@profile_router.post(
    "/me/profile/github",
    response_model=ProfileResponse,
    operation_id="enrichGitHub",
)
def enrich_github(
    body: UsernameBody,
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> ProfileResponse:
    user_id = _require_user(identity, users)
    try:
        profile = EnrichFromGitHub(
            repository=PostgresProfileRepository(conn),
            analyzer=HttpGitHubAnalyzer(),
        ).execute(user_id, body.username)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"GitHub enrichment failed: {exc}") from exc
    _sync_and_rematch(conn, profile, settings)
    return _response(profile)


@profile_router.post(
    "/me/profile/portfolio",
    response_model=ProfileResponse,
    operation_id="enrichPortfolio",
)
def enrich_portfolio(
    body: UrlBody,
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    conn: Annotated[Connection[Any], Depends(get_db_connection)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> ProfileResponse:
    user_id = _require_user(identity, users)
    try:
        profile = EnrichFromPortfolio(
            repository=PostgresProfileRepository(conn),
            fetcher=HttpPortfolioFetcher(),
        ).execute(user_id, body.url)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Portfolio fetch failed: {exc}") from exc
    _sync_and_rematch(conn, profile, settings)
    return _response(profile)
