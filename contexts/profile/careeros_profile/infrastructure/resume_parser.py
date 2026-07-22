"""Deterministic resume parser adapter."""

from __future__ import annotations

from careeros_profile.domain.extraction import extract_from_text
from careeros_profile.ports.profile_ports import ParsedResume


class HeuristicResumeParser:
    def parse(self, raw_text: str) -> ParsedResume:
        extraction = extract_from_text(raw_text)
        return ParsedResume(
            text=raw_text.strip(),
            skills=extraction.skills,
            experiences_hint=tuple(f"{e.title} at {e.company}" for e in extraction.experiences),
            years_experience=extraction.years_experience,
        )
