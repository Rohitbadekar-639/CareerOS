"""Unit tests for Career Copilot."""

from uuid import uuid4

from careeros_matching.application.copilot import CareerCopilot, OpportunityBrief
from careeros_matching.domain.match import Match
from careeros_matching.domain.seeker_criteria import SeekerCriteria


def test_copilot_advice_and_cover_letter() -> None:
    user_id = uuid4()
    criteria = SeekerCriteria.create(
        user_id,
        resume_text="Built APIs in Python",
        skills=["python", "fastapi"],
    )
    match = Match.create(
        user_id=user_id,
        opportunity_id=uuid4(),
        score=0.8,
        hard_filter_passed=True,
        reasons=["Skills overlap: python, fastapi"],
        gaps=["Weak evidence for: kubernetes"],
        model_version="heuristic-match-v1",
    )
    brief = OpportunityBrief(
        title="Backend Engineer",
        company="Acme",
        location="Remote",
        is_remote=True,
        description_text="Python FastAPI",
        skills=("python", "fastapi", "kubernetes"),
    )
    copilot = CareerCopilot()
    advice = copilot.advise(criteria=criteria, match=match, opportunity=brief)
    assert advice.match_score == 0.8
    assert any("python" in r.lower() for r in advice.why_match)
    assert "kubernetes" in " ".join(advice.resume_suggestions).lower() or advice.missing_skills
    draft = copilot.draft_cover_letter(criteria=criteria, opportunity=brief, match=match)
    assert "Acme" in draft.body
    assert draft.requires_human_review is True
