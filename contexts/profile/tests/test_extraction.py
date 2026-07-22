"""Unit tests for skill/experience extraction."""

from careeros_profile.domain.extraction import extract_from_text


def test_extract_skills_and_years() -> None:
    text = """
    Software Engineer at Acme Corp
    5 years of experience with Python, FastAPI, Postgres and Docker.
    """
    result = extract_from_text(text)
    assert "python" in result.skills
    assert "fastapi" in result.skills
    assert result.years_experience == 5
    assert any(e.company.lower().startswith("acme") for e in result.experiences)
