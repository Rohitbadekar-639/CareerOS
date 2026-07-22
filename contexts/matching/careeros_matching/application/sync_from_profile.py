"""Project a ProfileSnapshot DTO into SeekerCriteria (ACL into Matching)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from careeros_matching.domain.seeker_criteria import RemotePreference, SeekerCriteria
from careeros_matching.ports.repositories import SeekerCriteriaRepository


@dataclass(frozen=True, slots=True)
class ProfileSnapshot:
    """DTO filled by API/worker from the Profile context — no cross-table reads."""

    user_id: UUID
    resume_text: str
    skills: tuple[str, ...]
    years_experience: int | None
    preferred_locations: tuple[str, ...]
    salary_expectation_min: int | None
    salary_currency: str | None
    remote_preference: str


def criteria_from_snapshot(snapshot: ProfileSnapshot) -> SeekerCriteria:
    try:
        remote = RemotePreference(snapshot.remote_preference)
    except ValueError:
        remote = RemotePreference.ANY
    return SeekerCriteria.create(
        snapshot.user_id,
        resume_text=snapshot.resume_text,
        skills=list(snapshot.skills),
        years_experience=snapshot.years_experience,
        preferred_locations=list(snapshot.preferred_locations),
        salary_expectation_min=snapshot.salary_expectation_min,
        salary_currency=snapshot.salary_currency,
        remote_preference=remote,
    )


def sync_snapshot_to_matching(
    snapshot: ProfileSnapshot,
    *,
    criteria_repo: SeekerCriteriaRepository,
) -> SeekerCriteria:
    criteria = criteria_from_snapshot(snapshot)
    criteria_repo.save(criteria)
    return criteria
