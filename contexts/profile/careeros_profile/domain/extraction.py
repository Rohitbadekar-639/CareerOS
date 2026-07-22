"""Deterministic skill + experience extraction (grounded, no fabrication)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from careeros_profile.domain.profile import Experience

_SKILL_LEXICON = frozenset(
    {
        "python",
        "java",
        "javascript",
        "typescript",
        "react",
        "nextjs",
        "nodejs",
        "fastapi",
        "django",
        "flask",
        "postgres",
        "postgresql",
        "mysql",
        "mongodb",
        "redis",
        "kafka",
        "aws",
        "gcp",
        "azure",
        "docker",
        "kubernetes",
        "terraform",
        "linux",
        "go",
        "golang",
        "rust",
        "c++",
        "c#",
        "dotnet",
        "spring",
        "graphql",
        "rest",
        "sql",
        "spark",
        "airflow",
        "pandas",
        "numpy",
        "pytorch",
        "tensorflow",
        "llm",
        "langchain",
        "figma",
        "swift",
        "kotlin",
        "android",
        "ios",
        "selenium",
        "pytest",
        "ci/cd",
        "git",
        "github",
        "gitlab",
        "jira",
    }
)

_EXP_LINE = re.compile(
    r"(?P<title>[A-Za-z][A-Za-z0-9 /+.#-]{2,60})\s+(?:at|@|-)\s+"
    r"(?P<company>[A-Za-z0-9 .,&-]{2,60})",
    re.IGNORECASE,
)
_YEARS = re.compile(r"(\d+)\+?\s*(?:\+)?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience|exp)", re.I)


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    skills: tuple[str, ...]
    experiences: tuple[Experience, ...]
    years_experience: int | None
    summary: str


def extract_from_text(text: str) -> ExtractionResult:
    blob = text or ""
    lowered = blob.lower()
    skills = tuple(sorted(s for s in _SKILL_LEXICON if s in lowered))
    experiences: list[Experience] = []
    for match in _EXP_LINE.finditer(blob):
        title = match.group("title").strip(" -|")
        company = match.group("company").strip(" -|")
        if len(title) < 3 or len(company) < 2:
            continue
        experiences.append(
            Experience(
                title=title[:80],
                company=company[:80],
                start_year=None,
                end_year=None,
                summary=match.group(0)[:240],
            )
        )
        if len(experiences) >= 8:
            break
    years = None
    year_match = _YEARS.search(blob)
    if year_match:
        years = min(int(year_match.group(1)), 40)
    summary = " ".join(blob.split())[:400]
    return ExtractionResult(
        skills=skills,
        experiences=tuple(experiences),
        years_experience=years,
        summary=summary,
    )
