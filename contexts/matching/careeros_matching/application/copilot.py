"""Career Copilot — grounded explanations + draft cover letter (deterministic MVP).

No LLM on the request path. Uses Match reasons/gaps and SeekerCriteria only.
Cover letter drafts are drafts for human review — never auto-sent.
"""

from __future__ import annotations

from dataclasses import dataclass

from careeros_matching.domain.match import Match
from careeros_matching.domain.seeker_criteria import SeekerCriteria


@dataclass(frozen=True, slots=True)
class OpportunityBrief:
    title: str
    company: str
    location: str | None
    is_remote: bool
    description_text: str
    skills: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CopilotAdvice:
    match_score: float | None
    why_match: tuple[str, ...]
    missing_skills: tuple[str, ...]
    resume_suggestions: tuple[str, ...]
    model_version: str


@dataclass(frozen=True, slots=True)
class CoverLetterDraft:
    body: str
    grounding_notes: tuple[str, ...]
    requires_human_review: bool = True
    model_version: str = "grounded-cover-letter-v1"


class CareerCopilot:
    """Deterministic Copilot grounded in Match + SeekerCriteria + Opportunity."""

    def advise(
        self,
        *,
        criteria: SeekerCriteria | None,
        match: Match | None,
        opportunity: OpportunityBrief,
    ) -> CopilotAdvice:
        why = list(match.reasons) if match else []
        gaps = list(match.gaps) if match else []
        missing: list[str] = []
        for gap in gaps:
            if gap.lower().startswith("weak evidence for:"):
                missing.extend(
                    part.strip() for part in gap.split(":", 1)[1].split(",") if part.strip()
                )
            elif "not remote" in gap.lower() or "location" in gap.lower():
                continue
            else:
                missing.append(gap)

        suggestions: list[str] = []
        if criteria is None:
            suggestions.append(
                "Add skills, resume notes, and preferences so ranking can personalize this role."
            )
        else:
            if missing:
                suggestions.append(
                    "Add concrete bullets that demonstrate: " + ", ".join(missing[:6]) + "."
                )
            if opportunity.skills:
                uncovered = [
                    s for s in opportunity.skills[:12] if s.lower() not in set(criteria.skills)
                ]
                if uncovered:
                    suggestions.append(
                        "If true in your experience, mention: " + ", ".join(uncovered[:5]) + "."
                    )
            if not criteria.resume_text.strip():
                suggestions.append(
                    "Paste resume notes so Copilot can ground cover-letter drafts in your words."
                )
            if not suggestions:
                suggestions.append(
                    "Lead with outcomes that match this role's title and stack; keep claims "
                    "only to experience you already listed."
                )

        if not why and match is None:
            why = ["No scored match yet — save ranking criteria to compute fit."]

        return CopilotAdvice(
            match_score=match.score if match else None,
            why_match=tuple(why),
            missing_skills=tuple(dict.fromkeys(missing)),
            resume_suggestions=tuple(suggestions),
            model_version=match.model_version if match else "copilot-advice-v1",
        )

    def draft_cover_letter(
        self,
        *,
        criteria: SeekerCriteria,
        opportunity: OpportunityBrief,
        match: Match | None,
    ) -> CoverLetterDraft:
        skills = ", ".join(criteria.skills[:8]) if criteria.skills else "relevant experience"
        location_line = (
            "remote" if opportunity.is_remote else (opportunity.location or "your location")
        )
        highlights = []
        if match and match.reasons:
            highlights.extend(match.reasons[:2])
        if criteria.resume_text.strip():
            snippet = " ".join(criteria.resume_text.strip().split())[:280]
            highlights.append(f"Background notes: {snippet}")
        highlight_block = "\n".join(f"- {h}" for h in highlights) or (
            f"- Experience aligned to {opportunity.title}"
        )

        body = (
            f"Dear {opportunity.company} Hiring Team,\n\n"
            f"I am writing to express interest in the {opportunity.title} role "
            f"({location_line}). My background includes {skills}, and I am motivated "
            f"by the chance to contribute at {opportunity.company}.\n\n"
            f"Why I am a fit:\n{highlight_block}\n\n"
            f"I would welcome the opportunity to discuss how I can help. "
            f"Thank you for your time and consideration.\n\n"
            f"Sincerely,\n[Your Name]\n"
        )
        notes = [
            "Draft only — review and edit before sending.",
            "Claims are limited to your saved criteria / match explanations.",
            "CareerOS does not auto-submit applications.",
        ]
        return CoverLetterDraft(body=body, grounding_notes=tuple(notes))
