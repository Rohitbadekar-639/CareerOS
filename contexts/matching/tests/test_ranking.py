"""Unit tests for heuristic ranking."""

from uuid import uuid4

from careeros_matching.domain.ranking import HeuristicMatchScorer, OpportunitySnapshot
from careeros_matching.domain.seeker_criteria import RemotePreference, SeekerCriteria


def test_remote_hard_filter_and_skill_overlap() -> None:
    user_id = uuid4()
    criteria = SeekerCriteria.create(
        user_id,
        resume_text="Built FastAPI services in Python",
        skills=["python", "fastapi", "postgres"],
        preferred_locations=["Bengaluru"],
        remote_preference=RemotePreference.REMOTE_ONLY,
    )
    remote_hit = OpportunitySnapshot(
        opportunity_id=uuid4(),
        title="Senior Python Engineer",
        company="Acme",
        location="Remote",
        is_remote=True,
        description_text="FastAPI postgres redis",
        skills=("python", "fastapi", "redis"),
        salary_min=None,
        salary_currency=None,
    )
    onsite_miss = OpportunitySnapshot(
        opportunity_id=uuid4(),
        title="Python Engineer",
        company="Acme",
        location="Mumbai",
        is_remote=False,
        description_text="Python",
        skills=("python",),
        salary_min=None,
        salary_currency=None,
    )
    scorer = HeuristicMatchScorer()
    good = scorer.score(criteria, remote_hit)
    bad = scorer.score(criteria, onsite_miss)
    assert good.hard_filter_passed is True
    assert good.score >= 0.55
    assert good.status.value == "surfaced"
    assert bad.hard_filter_passed is False
    assert bad.status.value == "suppressed"
