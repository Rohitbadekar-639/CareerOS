"""Profile → Matching ACL sync."""

from uuid import uuid4

from careeros_matching.application.sync_from_profile import (
    ProfileSnapshot,
    criteria_from_snapshot,
)


def test_criteria_from_snapshot_maps_skills_and_remote() -> None:
    snapshot = ProfileSnapshot(
        user_id=uuid4(),
        resume_text="Python engineer",
        skills=("python", "fastapi"),
        years_experience=4,
        preferred_locations=("Bengaluru",),
        salary_expectation_min=2_000_000,
        salary_currency="INR",
        remote_preference="remote_only",
    )
    criteria = criteria_from_snapshot(snapshot)
    assert criteria.skills == ("python", "fastapi")
    assert criteria.years_experience == 4
    assert criteria.remote_preference.value == "remote_only"
    assert "Python" in criteria.resume_text
