"""Matching application services."""

from __future__ import annotations

from uuid import UUID

from careeros_matching.domain.match import Match
from careeros_matching.domain.ranking import HeuristicMatchScorer, OpportunitySnapshot
from careeros_matching.domain.seeker_criteria import SeekerCriteria
from careeros_matching.ports.repositories import (
    MatchRepository,
    MatchScorer,
    SeekerCriteriaRepository,
)


class UpsertSeekerCriteria:
    def __init__(self, *, repository: SeekerCriteriaRepository) -> None:
        self._repository = repository

    def execute(self, criteria: SeekerCriteria) -> SeekerCriteria:
        self._repository.save(criteria)
        return criteria


class GetSeekerCriteria:
    def __init__(self, *, repository: SeekerCriteriaRepository) -> None:
        self._repository = repository

    def execute(self, user_id: UUID) -> SeekerCriteria | None:
        return self._repository.get(user_id)


class RecomputeMatches:
    def __init__(
        self,
        *,
        criteria_repo: SeekerCriteriaRepository,
        match_repo: MatchRepository,
        scorer: MatchScorer | None = None,
    ) -> None:
        self._criteria_repo = criteria_repo
        self._match_repo = match_repo
        self._scorer = scorer or HeuristicMatchScorer()

    def execute(
        self,
        user_id: UUID,
        opportunities: list[OpportunitySnapshot],
    ) -> list[Match]:
        criteria = self._criteria_repo.get(user_id)
        if criteria is None:
            self._match_repo.replace_for_user(user_id, [])
            return []
        matches = [self._scorer.score(criteria, opp) for opp in opportunities]
        self._match_repo.replace_for_user(user_id, matches)
        return matches


class ListRecommendations:
    def __init__(self, *, match_repo: MatchRepository) -> None:
        self._match_repo = match_repo

    def execute(
        self,
        user_id: UUID,
        *,
        min_score: float = 0.55,
        limit: int = 50,
    ) -> list[Match]:
        return self._match_repo.list_surfaced(user_id, min_score=min_score, limit=limit)
