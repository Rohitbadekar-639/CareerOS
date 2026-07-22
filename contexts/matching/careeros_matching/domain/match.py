"""Match aggregate — scored fit between seeker criteria and an opportunity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from careeros_shared_kernel import ValidationError


class MatchStatus(StrEnum):
    COMPUTED = "computed"
    SURFACED = "surfaced"
    SUPPRESSED = "suppressed"
    STALE = "stale"


@dataclass(frozen=True, slots=True)
class Match:
    id: UUID
    user_id: UUID
    opportunity_id: UUID
    score: float
    hard_filter_passed: bool
    reasons: tuple[str, ...]
    gaps: tuple[str, ...]
    model_version: str
    status: MatchStatus
    computed_at: datetime

    @classmethod
    def create(
        cls,
        *,
        user_id: UUID,
        opportunity_id: UUID,
        score: float,
        hard_filter_passed: bool,
        reasons: list[str] | tuple[str, ...],
        gaps: list[str] | tuple[str, ...],
        model_version: str,
        status: MatchStatus = MatchStatus.COMPUTED,
        match_id: UUID | None = None,
    ) -> Match:
        if not 0.0 <= score <= 1.0:
            raise ValidationError("Match score must be between 0 and 1")
        surfaced = (
            MatchStatus.SURFACED if hard_filter_passed and score >= 0.55 else MatchStatus.SUPPRESSED
        )
        return cls(
            id=match_id or uuid4(),
            user_id=user_id,
            opportunity_id=opportunity_id,
            score=score,
            hard_filter_passed=hard_filter_passed,
            reasons=tuple(reasons),
            gaps=tuple(gaps),
            model_version=model_version,
            status=status if status is not MatchStatus.COMPUTED else surfaced,
            computed_at=datetime.now(UTC),
        )
