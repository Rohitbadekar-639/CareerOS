"""Bridge Profile → Matching DTO without importing the API package."""

from __future__ import annotations

from careeros_matching.application.sync_from_profile import ProfileSnapshot
from careeros_profile.domain.profile import CandidateProfile


def profile_to_snapshot(profile: CandidateProfile) -> ProfileSnapshot:
    resume_bits = [
        profile.headline,
        profile.summary,
        profile.resume_text,
        profile.linkedin_text,
        profile.github_summary,
        profile.portfolio_summary,
    ]
    for exp in profile.experiences:
        resume_bits.append(f"{exp.title} at {exp.company}. {exp.summary}")
    return ProfileSnapshot(
        user_id=profile.user_id,
        resume_text="\n".join(b for b in resume_bits if b),
        skills=profile.skills,
        years_experience=profile.years_experience,
        preferred_locations=profile.preferred_locations,
        salary_expectation_min=profile.salary_expectation_min,
        salary_currency=profile.salary_currency,
        remote_preference=profile.remote_preference,
    )
