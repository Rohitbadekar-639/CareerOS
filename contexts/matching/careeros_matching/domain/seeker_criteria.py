"""SeekerCriteria — MVP stand-in for Career Profile preferences (ADR-0001)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from careeros_shared_kernel import ValidationError


class RemotePreference(StrEnum):
    ANY = "any"
    REMOTE_ONLY = "remote_only"
    HYBRID_OR_ONSITE = "hybrid_or_onsite"


@dataclass(frozen=True, slots=True)
class SeekerCriteria:
    user_id: UUID
    resume_text: str
    skills: tuple[str, ...]
    years_experience: int | None
    preferred_locations: tuple[str, ...]
    salary_expectation_min: int | None
    salary_currency: str | None
    remote_preference: RemotePreference
    updated_at: datetime

    @classmethod
    def create(
        cls,
        user_id: UUID,
        *,
        resume_text: str = "",
        skills: list[str] | tuple[str, ...] | None = None,
        years_experience: int | None = None,
        preferred_locations: list[str] | tuple[str, ...] | None = None,
        salary_expectation_min: int | None = None,
        salary_currency: str | None = "INR",
        remote_preference: RemotePreference = RemotePreference.ANY,
    ) -> SeekerCriteria:
        if years_experience is not None and years_experience < 0:
            raise ValidationError("years_experience must be >= 0")
        if salary_expectation_min is not None and salary_expectation_min < 0:
            raise ValidationError("salary_expectation_min must be >= 0")
        clean_skills = tuple(dict.fromkeys(s.strip().lower() for s in (skills or ()) if s.strip()))
        clean_locs = tuple(
            dict.fromkeys(s.strip() for s in (preferred_locations or ()) if s.strip())
        )
        return cls(
            user_id=user_id,
            resume_text=resume_text.strip(),
            skills=clean_skills,
            years_experience=years_experience,
            preferred_locations=clean_locs,
            salary_expectation_min=salary_expectation_min,
            salary_currency=(salary_currency or "INR").upper(),
            remote_preference=remote_preference,
            updated_at=datetime.now(UTC),
        )
