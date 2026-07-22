"""Ports for Matching & Fit."""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from careeros_matching.domain.match import Match
from careeros_matching.domain.seeker_criteria import SeekerCriteria


@runtime_checkable
class SeekerCriteriaRepository(Protocol):
    def get(self, user_id: UUID) -> SeekerCriteria | None: ...

    def save(self, criteria: SeekerCriteria) -> None: ...


@runtime_checkable
class MatchRepository(Protocol):
    def replace_for_user(self, user_id: UUID, matches: list[Match]) -> None: ...

    def get_for_opportunity(self, user_id: UUID, opportunity_id: UUID) -> Match | None: ...

    def list_surfaced(
        self,
        user_id: UUID,
        *,
        min_score: float = 0.55,
        limit: int = 50,
    ) -> list[Match]: ...


@runtime_checkable
class MatchScorer(Protocol):
    def score(self, criteria: SeekerCriteria, opportunity: object) -> Match: ...
