"""Ports for profile evidence ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from uuid import UUID

from careeros_profile.domain.profile import CandidateProfile


@dataclass(frozen=True, slots=True)
class ParsedResume:
    text: str
    skills: tuple[str, ...]
    experiences_hint: tuple[str, ...]
    years_experience: int | None


@dataclass(frozen=True, slots=True)
class GitHubAnalysis:
    username: str
    summary: str
    languages: tuple[str, ...]
    top_repos: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    url: str
    summary: str
    keywords: tuple[str, ...]


@runtime_checkable
class ResumeParser(Protocol):
    def parse(self, raw_text: str) -> ParsedResume: ...


@runtime_checkable
class GitHubAnalyzer(Protocol):
    def analyze(self, username: str) -> GitHubAnalysis: ...


@runtime_checkable
class PortfolioFetcher(Protocol):
    def fetch(self, url: str) -> PortfolioSnapshot: ...


@runtime_checkable
class ProfileRepository(Protocol):
    def get(self, user_id: UUID) -> CandidateProfile | None: ...

    def save(self, profile: CandidateProfile) -> None: ...

    def list_user_ids(self) -> list[UUID]: ...
