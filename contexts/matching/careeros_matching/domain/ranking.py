"""Deterministic ranking against an OpportunitySnapshot DTO."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from careeros_matching.domain.match import Match, MatchStatus
from careeros_matching.domain.seeker_criteria import RemotePreference, SeekerCriteria


@dataclass(frozen=True, slots=True)
class OpportunitySnapshot:
    """Published-contract-shaped DTO — filled by worker/API, not by joining tables."""

    opportunity_id: UUID
    title: str
    company: str
    location: str | None
    is_remote: bool
    description_text: str
    skills: tuple[str, ...]
    salary_min: int | None
    salary_currency: str | None


MODEL_VERSION = "heuristic-match-v1"


class HeuristicMatchScorer:
    """Explainable, grounded scoring — no LLM."""

    def score(self, criteria: SeekerCriteria, opportunity: OpportunitySnapshot) -> Match:
        reasons: list[str] = []
        gaps: list[str] = []
        hard_ok = True

        if criteria.remote_preference is RemotePreference.REMOTE_ONLY and not opportunity.is_remote:
            hard_ok = False
            gaps.append("Role is not remote")
        if (
            criteria.remote_preference is RemotePreference.HYBRID_OR_ONSITE
            and opportunity.is_remote
            and not (opportunity.location or "").strip()
        ):
            # Prefer non-remote-only listings when seeker wants hybrid/onsite.
            pass

        if criteria.preferred_locations and not opportunity.is_remote:
            loc = (opportunity.location or "").lower()
            if not any(pref.lower() in loc for pref in criteria.preferred_locations):
                hard_ok = False
                gaps.append("Location does not match preferred locations")

        if (
            criteria.salary_expectation_min is not None
            and opportunity.salary_min is not None
            and opportunity.salary_currency
            and criteria.salary_currency
            and opportunity.salary_currency.upper() == criteria.salary_currency.upper()
            and opportunity.salary_min < criteria.salary_expectation_min
        ):
            hard_ok = False
            gaps.append("Listed compensation below expectation")

        seeker_skills = set(criteria.skills)
        resume_tokens = {
            t.lower() for t in criteria.resume_text.replace(",", " ").split() if len(t) >= 3
        }
        opp_skills = {s.lower() for s in opportunity.skills}
        opp_text = f"{opportunity.title} {opportunity.description_text}".lower()

        overlap = seeker_skills & opp_skills
        soft_overlap = {s for s in seeker_skills if s in opp_text} | {
            t for t in resume_tokens if t in opp_text and len(t) >= 4
        }
        skill_hits = overlap | soft_overlap
        if skill_hits:
            reasons.append(f"Skills overlap: {', '.join(sorted(skill_hits)[:8])}")
        missing = sorted(seeker_skills - skill_hits)[:5]
        if missing:
            gaps.append(f"Weak evidence for: {', '.join(missing)}")

        skill_score = 0.0
        if seeker_skills:
            skill_score = len(skill_hits) / max(len(seeker_skills), 1)
        elif soft_overlap:
            skill_score = min(0.4, 0.05 * len(soft_overlap))

        title_bonus = 0.15 if any(s in opportunity.title.lower() for s in seeker_skills) else 0.0
        remote_bonus = (
            0.1
            if criteria.remote_preference is RemotePreference.REMOTE_ONLY and opportunity.is_remote
            else 0.0
        )
        score = min(1.0, skill_score * 0.75 + title_bonus + remote_bonus)
        if not hard_ok:
            score = min(score, 0.35)

        if criteria.years_experience is not None and criteria.years_experience >= 2:
            reasons.append(f"Candidate experience signal: ~{criteria.years_experience} years")

        if opportunity.is_remote and criteria.remote_preference is not (
            RemotePreference.HYBRID_OR_ONSITE
        ):
            reasons.append("Remote-friendly role")
        if not reasons and hard_ok:
            reasons.append("Passed hard filters; limited skill evidence in listing")

        return Match.create(
            user_id=criteria.user_id,
            opportunity_id=opportunity.opportunity_id,
            score=round(score, 4),
            hard_filter_passed=hard_ok,
            reasons=reasons,
            gaps=gaps,
            model_version=MODEL_VERSION,
            status=MatchStatus.COMPUTED,
        )
