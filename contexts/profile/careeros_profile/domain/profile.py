"""Unified candidate profile (MVP Career Profile)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from careeros_shared_kernel import ValidationError


@dataclass(frozen=True, slots=True)
class Experience:
    title: str
    company: str
    start_year: int | None
    end_year: int | None
    summary: str

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValidationError("Experience title required")
        if not self.company.strip():
            raise ValidationError("Experience company required")


@dataclass(frozen=True, slots=True)
class ExternalLinks:
    github_username: str | None = None
    linkedin_url: str | None = None
    portfolio_url: str | None = None


@dataclass(frozen=True, slots=True)
class CandidateProfile:
    """Structured candidate model derived from user-provided evidence."""

    user_id: UUID
    version: int
    headline: str
    summary: str
    resume_text: str
    linkedin_text: str
    skills: tuple[str, ...]
    experiences: tuple[Experience, ...]
    years_experience: int | None
    preferred_locations: tuple[str, ...]
    salary_expectation_min: int | None
    salary_currency: str | None
    remote_preference: str
    links: ExternalLinks
    github_summary: str
    portfolio_summary: str
    updated_at: datetime
    id: UUID = field(default_factory=uuid4)

    @classmethod
    def empty(cls, user_id: UUID) -> CandidateProfile:
        return cls(
            user_id=user_id,
            version=1,
            headline="",
            summary="",
            resume_text="",
            linkedin_text="",
            skills=(),
            experiences=(),
            years_experience=None,
            preferred_locations=(),
            salary_expectation_min=None,
            salary_currency="INR",
            remote_preference="any",
            links=ExternalLinks(),
            github_summary="",
            portfolio_summary="",
            updated_at=datetime.now(UTC),
        )

    def with_updates(
        self,
        *,
        headline: str | None = None,
        summary: str | None = None,
        resume_text: str | None = None,
        linkedin_text: str | None = None,
        skills: tuple[str, ...] | None = None,
        experiences: tuple[Experience, ...] | None = None,
        years_experience: int | None = None,
        preferred_locations: tuple[str, ...] | None = None,
        salary_expectation_min: int | None = None,
        salary_currency: str | None = None,
        remote_preference: str | None = None,
        links: ExternalLinks | None = None,
        github_summary: str | None = None,
        portfolio_summary: str | None = None,
        bump_version: bool = True,
    ) -> CandidateProfile:
        return CandidateProfile(
            id=self.id,
            user_id=self.user_id,
            version=self.version + 1 if bump_version else self.version,
            headline=self.headline if headline is None else headline.strip(),
            summary=self.summary if summary is None else summary.strip(),
            resume_text=self.resume_text if resume_text is None else resume_text.strip(),
            linkedin_text=self.linkedin_text if linkedin_text is None else linkedin_text.strip(),
            skills=self.skills if skills is None else skills,
            experiences=self.experiences if experiences is None else experiences,
            years_experience=(
                self.years_experience if years_experience is None else years_experience
            ),
            preferred_locations=(
                self.preferred_locations if preferred_locations is None else preferred_locations
            ),
            salary_expectation_min=(
                self.salary_expectation_min
                if salary_expectation_min is None
                else salary_expectation_min
            ),
            salary_currency=(
                self.salary_currency if salary_currency is None else salary_currency.upper()
            ),
            remote_preference=(
                self.remote_preference if remote_preference is None else remote_preference
            ),
            links=self.links if links is None else links,
            github_summary=(
                self.github_summary if github_summary is None else github_summary.strip()
            ),
            portfolio_summary=(
                self.portfolio_summary if portfolio_summary is None else portfolio_summary.strip()
            ),
            updated_at=datetime.now(UTC),
        )

    def evidence_blob(self) -> str:
        parts = [
            self.headline,
            self.summary,
            self.resume_text,
            self.linkedin_text,
            self.github_summary,
            self.portfolio_summary,
            " ".join(self.skills),
        ]
        for exp in self.experiences:
            parts.append(f"{exp.title} {exp.company} {exp.summary}")
        return "\n".join(p for p in parts if p)
