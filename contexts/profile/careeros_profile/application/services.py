"""Profile ingestion + enrichment use cases."""

from __future__ import annotations

from uuid import UUID

from careeros_profile.domain.extraction import extract_from_text
from careeros_profile.domain.profile import CandidateProfile, Experience, ExternalLinks
from careeros_profile.ports.profile_ports import (
    GitHubAnalyzer,
    PortfolioFetcher,
    ProfileRepository,
    ResumeParser,
)
from careeros_shared_kernel import ValidationError


class GetOrCreateProfile:
    def __init__(self, *, repository: ProfileRepository) -> None:
        self._repository = repository

    def execute(self, user_id: UUID) -> CandidateProfile:
        existing = self._repository.get(user_id)
        if existing is not None:
            return existing
        profile = CandidateProfile.empty(user_id)
        self._repository.save(profile)
        return profile


class UpsertProfilePreferences:
    def __init__(self, *, repository: ProfileRepository) -> None:
        self._repository = repository

    def execute(
        self,
        user_id: UUID,
        *,
        headline: str = "",
        preferred_locations: list[str] | None = None,
        salary_expectation_min: int | None = None,
        salary_currency: str | None = "INR",
        remote_preference: str = "any",
        github_username: str | None = None,
        linkedin_url: str | None = None,
        portfolio_url: str | None = None,
    ) -> CandidateProfile:
        current = self._repository.get(user_id) or CandidateProfile.empty(user_id)
        updated = current.with_updates(
            headline=headline,
            preferred_locations=tuple(
                dict.fromkeys(s.strip() for s in (preferred_locations or []) if s.strip())
            ),
            salary_expectation_min=salary_expectation_min,
            salary_currency=salary_currency,
            remote_preference=remote_preference,
            links=ExternalLinks(
                github_username=(github_username or "").strip() or None,
                linkedin_url=(linkedin_url or "").strip() or None,
                portfolio_url=(portfolio_url or "").strip() or None,
            ),
        )
        self._repository.save(updated)
        return updated


class IngestResumeText:
    def __init__(self, *, repository: ProfileRepository, parser: ResumeParser) -> None:
        self._repository = repository
        self._parser = parser

    def execute(self, user_id: UUID, raw_text: str) -> CandidateProfile:
        if not raw_text.strip():
            raise ValidationError("Resume text must not be empty")
        parsed = self._parser.parse(raw_text)
        current = self._repository.get(user_id) or CandidateProfile.empty(user_id)
        extraction = extract_from_text(parsed.text)
        skills = tuple(dict.fromkeys([*current.skills, *parsed.skills, *extraction.skills]))
        experiences = extraction.experiences or current.experiences
        updated = current.with_updates(
            resume_text=parsed.text,
            skills=skills,
            experiences=experiences,
            years_experience=parsed.years_experience or extraction.years_experience,
            summary=extraction.summary or current.summary,
        )
        self._repository.save(updated)
        return updated


class IngestLinkedInText:
    """User-provided LinkedIn export/paste — never scraped."""

    def __init__(self, *, repository: ProfileRepository) -> None:
        self._repository = repository

    def execute(self, user_id: UUID, linkedin_text: str) -> CandidateProfile:
        if not linkedin_text.strip():
            raise ValidationError("LinkedIn text must not be empty")
        current = self._repository.get(user_id) or CandidateProfile.empty(user_id)
        extraction = extract_from_text(linkedin_text)
        skills = tuple(dict.fromkeys([*current.skills, *extraction.skills]))
        experiences = extraction.experiences or current.experiences
        updated = current.with_updates(
            linkedin_text=linkedin_text.strip(),
            skills=skills,
            experiences=experiences,
            years_experience=extraction.years_experience or current.years_experience,
            summary=current.summary or extraction.summary,
        )
        self._repository.save(updated)
        return updated


class EnrichFromGitHub:
    def __init__(self, *, repository: ProfileRepository, analyzer: GitHubAnalyzer) -> None:
        self._repository = repository
        self._analyzer = analyzer

    def execute(self, user_id: UUID, username: str) -> CandidateProfile:
        if not username.strip():
            raise ValidationError("GitHub username required")
        analysis = self._analyzer.analyze(username.strip())
        current = self._repository.get(user_id) or CandidateProfile.empty(user_id)
        skills = tuple(dict.fromkeys([*current.skills, *[s.lower() for s in analysis.languages]]))
        updated = current.with_updates(
            links=ExternalLinks(
                github_username=analysis.username,
                linkedin_url=current.links.linkedin_url,
                portfolio_url=current.links.portfolio_url,
            ),
            github_summary=analysis.summary,
            skills=skills,
        )
        self._repository.save(updated)
        return updated


class EnrichFromPortfolio:
    def __init__(self, *, repository: ProfileRepository, fetcher: PortfolioFetcher) -> None:
        self._repository = repository
        self._fetcher = fetcher

    def execute(self, user_id: UUID, url: str) -> CandidateProfile:
        if not url.strip():
            raise ValidationError("Portfolio URL required")
        snap = self._fetcher.fetch(url.strip())
        current = self._repository.get(user_id) or CandidateProfile.empty(user_id)
        skills = tuple(dict.fromkeys([*current.skills, *[k.lower() for k in snap.keywords]]))
        updated = current.with_updates(
            links=ExternalLinks(
                github_username=current.links.github_username,
                linkedin_url=current.links.linkedin_url,
                portfolio_url=snap.url,
            ),
            portfolio_summary=snap.summary,
            skills=skills,
        )
        self._repository.save(updated)
        return updated


def experiences_as_dicts(experiences: tuple[Experience, ...]) -> list[dict[str, object]]:
    return [
        {
            "title": e.title,
            "company": e.company,
            "start_year": e.start_year,
            "end_year": e.end_year,
            "summary": e.summary,
        }
        for e in experiences
    ]
